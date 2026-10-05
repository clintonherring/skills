#!/usr/bin/env python3
"""NocoDB sync tests against a local stand-in HTTP server."""

from __future__ import annotations

import json
import os
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent.parent
sys_path_inserted = False


class StandIn(BaseHTTPRequestHandler):
    """Minimal NocoDB v2 quirks: 422 past end, 429 once, token auth, column meta."""

    store: dict[str, Any] = {}

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        return

    def _auth(self) -> bool:
        return self.headers.get("xc-token") == "test-token"

    def _read_json(self) -> Any:
        length = int(self.headers.get("Content-Length") or 0)
        if not length:
            return None
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def _send(self, code: int, body: Any) -> None:
        raw = json.dumps(body).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:  # noqa: N802
        if not self._auth():
            self._send(401, {"msg": "unauthorized"})
            return
        path = urlparse(self.path).path
        qs = parse_qs(urlparse(self.path).query)
        if path.endswith("/meta/tables/facts_tbl") or path.endswith("/tables/facts_tbl"):
            self._send(
                200,
                {
                    "columns": [
                        {"title": "Key"},
                        {"title": "Value"},
                        {"title": "Updated"},
                        {"title": "Source"},
                    ]
                },
            )
            return
        if path.endswith("/meta/tables/decisions_tbl") or path.endswith("/tables/decisions_tbl"):
            self._send(
                200,
                {
                    "columns": [
                        {"title": "Decision"},
                        {"title": "Rationale"},
                        {"title": "Date"},
                        {"title": "ConversationId"},
                        {"title": "Project"},
                    ]
                },
            )
            return
        if "/tables/facts_tbl/records" in path:
            offset = int((qs.get("offset") or ["0"])[0])
            if offset > 0:
                self._send(422, {"msg": "offset past end"})
                return
            # First facts list call may 429 once
            if not StandIn.store.get("facts_ok"):
                StandIn.store["facts_ok"] = True
                self._send(429, {"msg": "rate limit"})
                return
            self._send(
                200,
                {
                    "list": [
                        {
                            "Key": "repo",
                            "Value": "skills",
                            "Updated": "2026-09-23",
                            "Source": "test",
                        }
                    ]
                },
            )
            return
        if "/tables/decisions_tbl/records" in path:
            self._send(200, {"list": StandIn.store.get("decisions", [])})
            return
        self._send(404, {"msg": "missing"})

    def do_POST(self) -> None:  # noqa: N802
        if not self._auth():
            self._send(401, {"msg": "unauthorized"})
            return
        body = self._read_json()
        if "/tables/decisions_tbl/records" in self.path:
            rows = body if isinstance(body, list) else body.get("records", [])
            StandIn.store.setdefault("decisions", []).extend(rows)
            self._send(200, {"list": rows})
            return
        self._send(404, {"msg": "missing"})


class NocoSyncTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        StandIn.store = {}
        cls.httpd = HTTPServer(("127.0.0.1", 0), StandIn)
        cls.port = cls.httpd.server_address[1]
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.httpd.shutdown()

    def setUp(self) -> None:
        global sys_path_inserted
        import sys

        if not sys_path_inserted:
            sys.path.insert(0, str(ROOT / "scripts"))
            sys_path_inserted = True
        os.environ["NOCODB_BASE_URL"] = f"http://127.0.0.1:{self.port}"
        os.environ["NOCODB_TOKEN"] = "test-token"
        os.environ["NOCODB_FACTS_TABLE"] = "facts_tbl"
        os.environ["NOCODB_DECISIONS_TABLE"] = "decisions_tbl"
        StandIn.store = {}

    def test_check_columns(self) -> None:
        import nocodb_sync

        cfg = nocodb_sync.load_cfg()
        self.assertEqual(nocodb_sync.cmd_check(cfg), 0)

    def test_pull_facts_retries_429(self) -> None:
        import nocodb_sync

        facts_path = ROOT / "memory" / "facts.md"
        backup = facts_path.read_text(encoding="utf-8")
        self.addCleanup(facts_path.write_text, backup, "utf-8")
        cfg = nocodb_sync.load_cfg()
        self.assertEqual(nocodb_sync.cmd_pull_facts(cfg), 0)
        text = facts_path.read_text(encoding="utf-8")
        self.assertIn("skills", text)
        self.assertIn("repo", text)

    def test_push_decisions(self) -> None:
        import nocodb_sync

        cfg = nocodb_sync.load_cfg()
        self.assertEqual(nocodb_sync.cmd_push_decisions(cfg), 0)
        self.assertTrue(StandIn.store.get("decisions"))

    def test_token_required(self) -> None:
        import nocodb_sync

        os.environ["NOCODB_TOKEN"] = "wrong"
        client = nocodb_sync.NocoClient(os.environ["NOCODB_BASE_URL"], "wrong")
        with self.assertRaises(RuntimeError):
            client.list_records("facts_tbl")

    def test_parse_decisions(self) -> None:
        import nocodb_sync

        md = """# Recent decisions

| Date | Decision | Rationale |
| --- | --- | --- |
| 2026-01-01 | Use files | Reviewable |
"""
        rows = nocodb_sync.parse_decisions_md(md)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["Decision"], "Use files")


if __name__ == "__main__":
    unittest.main()
