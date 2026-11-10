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
        if path.endswith("/meta/tables/now_tbl") or path.endswith("/tables/now_tbl"):
            self._send(
                200,
                {
                    "columns": [
                        {"title": "Project"},
                        {"title": "Content"},
                        {"title": "Updated"},
                        {"title": "Source"},
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
        if "/tables/now_tbl/records" in path:
            self._send(200, {"list": StandIn.store.get("now", [])})
            return
        self._send(404, {"msg": "missing"})

    def do_POST(self) -> None:  # noqa: N802
        if not self._auth():
            self._send(401, {"msg": "unauthorized"})
            return
        body = self._read_json()
        for key, store_key in (
            ("decisions_tbl", "decisions"),
            ("now_tbl", "now"),
        ):
            if f"/tables/{key}/records" in self.path:
                rows = body if isinstance(body, list) else body.get("records", [])
                existing = StandIn.store.setdefault(store_key, [])
                next_id = StandIn.store.get("next_id", 1)
                for row in rows:
                    item = dict(row)
                    if "Id" not in item and "id" not in item:
                        item["Id"] = next_id
                        next_id += 1
                    existing.append(item)
                StandIn.store["next_id"] = next_id
                self._send(200, {"list": rows})
                return
        self._send(404, {"msg": "missing"})

    def do_PATCH(self) -> None:  # noqa: N802
        if not self._auth():
            self._send(401, {"msg": "unauthorized"})
            return
        body = self._read_json()
        for key, store_key in (
            ("decisions_tbl", "decisions"),
            ("now_tbl", "now"),
        ):
            if f"/tables/{key}/records" in self.path:
                rows = body if isinstance(body, list) else body.get("records", [])
                existing = StandIn.store.setdefault(store_key, [])
                by_id = {str(r.get("Id") or r.get("id")): r for r in existing}
                for row in rows:
                    rid = str(row.get("Id") or row.get("id") or "")
                    if rid in by_id:
                        by_id[rid].update(row)
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
        os.environ["NOCODB_NOW_TABLE"] = "now_tbl"
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

    def test_push_decisions_upserts_no_duplicates(self) -> None:
        import nocodb_sync

        decisions_path = ROOT / "memory" / "decisions.md"
        backup = decisions_path.read_text(encoding="utf-8")
        self.addCleanup(decisions_path.write_text, backup, "utf-8")
        decisions_path.write_text(
            """# Recent decisions

| Date | Decision | Rationale |
| --- | --- | --- |
| 2026-10-08 | Unique upsert decision | First rationale |
""",
            encoding="utf-8",
        )
        cfg = nocodb_sync.load_cfg()
        self.assertEqual(nocodb_sync.cmd_push_decisions(cfg), 0)
        self.assertEqual(len(StandIn.store.get("decisions", [])), 1)

        # Second push with same identity must not create another row.
        self.assertEqual(nocodb_sync.cmd_push_decisions(cfg), 0)
        self.assertEqual(len(StandIn.store.get("decisions", [])), 1)

        # Rationale change updates in place.
        decisions_path.write_text(
            """# Recent decisions

| Date | Decision | Rationale |
| --- | --- | --- |
| 2026-10-08 | Unique upsert decision | Updated rationale |
""",
            encoding="utf-8",
        )
        self.assertEqual(nocodb_sync.cmd_push_decisions(cfg), 0)
        rows = StandIn.store.get("decisions", [])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].get("Rationale"), "Updated rationale")

    def test_push_now_upserts_one_row_per_project(self) -> None:
        import nocodb_sync

        now_path = ROOT / "memory" / "NOW.md"
        backup = now_path.read_text(encoding="utf-8")
        self.addCleanup(now_path.write_text, backup, "utf-8")
        now_path.write_text("# NOW\n\nSnapshot A\n", encoding="utf-8")
        cfg = nocodb_sync.load_cfg()
        self.assertEqual(nocodb_sync.cmd_push_now(cfg, source="test"), 0)
        self.assertEqual(len(StandIn.store.get("now", [])), 1)
        self.assertEqual(nocodb_sync.cmd_push_now(cfg, source="test"), 0)
        self.assertEqual(len(StandIn.store.get("now", [])), 1)
        now_path.write_text("# NOW\n\nSnapshot B\n", encoding="utf-8")
        self.assertEqual(nocodb_sync.cmd_push_now(cfg, source="test"), 0)
        rows = StandIn.store.get("now", [])
        self.assertEqual(len(rows), 1)
        self.assertIn("Snapshot B", rows[0].get("Content", ""))

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
