#!/usr/bin/env python3
"""Sync memory files with NocoDB Agent Memory base (one-way each direction)."""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent


class NocoClient:
    def __init__(self, base_url: str, token: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token

    def request(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
        retries: int = 3,
    ) -> Any:
        url = f"{self.base_url}{path}"
        data = None if body is None else json.dumps(body).encode("utf-8")
        headers = {
            "xc-token": self.token,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        last_err: Exception | None = None
        for attempt in range(retries):
            req = urllib.request.Request(url, data=data, headers=headers, method=method)
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    raw = resp.read().decode("utf-8")
                    return json.loads(raw) if raw.strip() else {}
            except urllib.error.HTTPError as exc:
                last_err = exc
                if exc.code == 429 and attempt + 1 < retries:
                    time.sleep(2 ** attempt)
                    continue
                # NocoDB v2 often returns 422 when offset is past the end.
                if exc.code == 422 and method == "GET":
                    return {"list": []}
                detail = exc.read().decode("utf-8", errors="replace")[:500]
                raise RuntimeError(f"HTTP {exc.code} {path}: {detail}") from exc
            except urllib.error.URLError as exc:
                last_err = exc
                if attempt + 1 < retries:
                    time.sleep(2 ** attempt)
                    continue
                raise
        raise RuntimeError(str(last_err))

    def list_records(self, table_id: str, limit: int = 200) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        offset = 0
        while True:
            q = urllib.parse.urlencode({"limit": limit, "offset": offset})
            page = self.request("GET", f"/tables/{table_id}/records?{q}")
            rows = page.get("list") if isinstance(page, dict) else None
            if rows is None and isinstance(page, list):
                rows = page
            rows = rows or []
            if not rows:
                break
            out.extend(rows)
            if len(rows) < limit:
                break
            offset += limit
        return out

    def create_records(self, table_id: str, rows: list[dict[str, Any]]) -> Any:
        # NocoDB v2 bulk create accepts a JSON array of row objects.
        return self.request("POST", f"/tables/{table_id}/records", rows)

    def get_table_meta(self, table_id: str) -> Any:
        # Prefer columns endpoint shapes used by NocoDB v2.
        try:
            return self.request("GET", f"/meta/tables/{table_id}")
        except RuntimeError:
            return self.request("GET", f"/tables/{table_id}")


def load_cfg() -> dict[str, Any]:
    with (ROOT / "memory.config.json").open(encoding="utf-8") as fh:
        return json.load(fh)


def env_from_cfg(cfg: dict[str, Any]) -> tuple[str, str, str, str]:
    n = cfg.get("nocodb", {})
    base = os.environ.get(n.get("base_url_env", "NOCODB_BASE_URL"), "")
    token = os.environ.get(n.get("token_env", "NOCODB_TOKEN"), "")
    facts = os.environ.get(n.get("facts_table_env", "NOCODB_FACTS_TABLE"), "")
    decisions = os.environ.get(n.get("decisions_table_env", "NOCODB_DECISIONS_TABLE"), "")
    return base, token, facts, decisions


def require_client(cfg: dict[str, Any]) -> tuple[NocoClient, str, str]:
    base, token, facts, decisions = env_from_cfg(cfg)
    missing = [
        name
        for name, val in (
            ("NOCODB_BASE_URL", base),
            ("NOCODB_TOKEN", token),
            ("NOCODB_FACTS_TABLE", facts),
            ("NOCODB_DECISIONS_TABLE", decisions),
        )
        if not val
    ]
    if missing:
        raise SystemExit(f"Missing env: {', '.join(missing)}")
    return NocoClient(base, token), facts, decisions


def expected_columns() -> dict[str, list[str]]:
    path = ROOT / "nocodb" / "tables.csv"
    by_table: dict[str, list[str]] = {}
    with path.open(encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            by_table.setdefault(row["table"], []).append(row["column"])
    return by_table


def cmd_check(cfg: dict[str, Any]) -> int:
    client, facts_id, decisions_id = require_client(cfg)
    expected = expected_columns()
    print("Expected columns from nocodb/tables.csv:")
    for table, cols in expected.items():
        print(f"  {table}: {', '.join(cols)}")
    for label, tid in (("facts", facts_id), ("decisions", decisions_id)):
        meta = client.get_table_meta(tid)
        cols = []
        if isinstance(meta, dict):
            columns = meta.get("columns") or meta.get("fields") or []
            for col in columns:
                if isinstance(col, dict):
                    cols.append(str(col.get("title") or col.get("column_name") or col.get("name") or ""))
        print(f"\nLive table {label} ({tid}) columns:")
        for c in cols:
            print(f"  - {c}")
        missing = [c for c in expected.get(label, []) if c not in cols]
        if missing:
            print(f"  MISSING (writes to these will silently blank): {missing}")
        else:
            print("  matches contract")
    return 0


def facts_to_markdown(rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Durable facts",
        "",
        "<!-- Generated by scripts/nocodb_sync.py pull-facts. Edit in NocoDB. -->",
        "",
        "| Key | Value | Updated |",
        "| --- | --- | --- |",
    ]
    for row in rows:
        key = str(row.get("Key") or row.get("key") or "").replace("|", "\\|")
        value = str(row.get("Value") or row.get("value") or "").replace("|", "\\|").replace("\n", " ")
        updated = str(row.get("Updated") or row.get("updated") or "")
        if not key:
            continue
        lines.append(f"| {key} | {value} | {updated} |")
    lines.append("")
    return "\n".join(lines)


def cmd_pull_facts(cfg: dict[str, Any]) -> int:
    client, facts_id, _ = require_client(cfg)
    rows = client.list_records(facts_id)
    path = ROOT / cfg["files"]["facts"]
    path.write_text(facts_to_markdown(rows), encoding="utf-8")
    print(f"Wrote {len(rows)} facts → {path}")
    return 0


def parse_decisions_md(text: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 3:
            continue
        if cells[0].lower() == "date" or set(cells[0]) <= {"-", ":"}:
            continue
        rows.append(
            {
                "Date": cells[0],
                "Decision": cells[1],
                "Rationale": cells[2] if len(cells) > 2 else "",
            }
        )
    return rows


def cmd_push_decisions(cfg: dict[str, Any]) -> int:
    client, _, decisions_id = require_client(cfg)
    path = ROOT / cfg["files"]["decisions"]
    rows = parse_decisions_md(path.read_text(encoding="utf-8"))
    payload = [
        {
            "Date": r["Date"],
            "Decision": r["Decision"],
            "Rationale": r["Rationale"],
            "Project": "clintonherring/skills",
        }
        for r in rows
    ]
    if not payload:
        print("No decision rows to push")
        return 0
    # NocoDB v2 accepts a bare array for bulk create.
    client.create_records(decisions_id, payload)
    print(f"Pushed {len(payload)} decisions → {decisions_id}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="NocoDB Agent Memory sync")
    parser.add_argument(
        "command",
        choices=("check", "pull-facts", "push-decisions"),
        help="check columns | pull facts cache | push decisions",
    )
    # Allow injecting a stand-in client in tests via monkeypatching NocoClient.
    args = parser.parse_args()
    cfg = load_cfg()
    if args.command == "check":
        return cmd_check(cfg)
    if args.command == "pull-facts":
        return cmd_pull_facts(cfg)
    return cmd_push_decisions(cfg)


if __name__ == "__main__":
    raise SystemExit(main())
