#!/usr/bin/env python3
"""Create Agent Memory tables in an existing NocoDB base (best-effort v2 meta API)."""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent

TYPE_MAP = {
    "SingleLineText": "SingleLineText",
    "LongText": "LongText",
    "Date": "Date",
    "DateTime": "DateTime",
}


def request(base_url: str, token: str, method: str, path: str, body: Any = None) -> Any:
    url = f"{base_url.rstrip('/')}{path}"
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "xc-token": token,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw.strip() else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:800]
        raise SystemExit(f"HTTP {exc.code} {path}: {detail}") from exc


def load_contract() -> dict[str, list[dict[str, str]]]:
    by_table: dict[str, list[dict[str, str]]] = {}
    with (ROOT / "nocodb" / "tables.csv").open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            by_table.setdefault(row["table"], []).append(row)
    return by_table


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Bootstrap Agent Memory tables into a NocoDB base"
    )
    parser.add_argument(
        "--base-id",
        default=os.environ.get("NOCODB_BASE_ID", ""),
        help="Existing NocoDB base/project id (or set NOCODB_BASE_ID)",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    base_url = os.environ.get("NOCODB_BASE_URL", "")
    token = os.environ.get("NOCODB_TOKEN", "")
    if not base_url or not token:
        print(
            "Set NOCODB_BASE_URL and NOCODB_TOKEN.\n"
            "Create an empty base named 'Agent Memory' in the NocoDB UI, then pass --base-id.",
            file=sys.stderr,
        )
        return 1
    if not args.base_id:
        print(
            "Missing --base-id / NOCODB_BASE_ID.\n"
            "NocoDB's public API creates tables inside an existing base; create the "
            "'Agent Memory' base in the UI first, copy its id, then re-run.",
            file=sys.stderr,
        )
        return 1

    contract = load_contract()
    created: dict[str, str] = {}
    for table, columns in contract.items():
        payload = {
            "table_name": table,
            "title": table,
            "columns": [
                {
                    "column_name": col["column"],
                    "title": col["column"],
                    "uidt": TYPE_MAP.get(col["type"], "SingleLineText"),
                }
                for col in columns
            ],
        }
        print(f"Create table {table} with {len(columns)} columns…")
        if args.dry_run:
            print(json.dumps(payload, indent=2))
            continue
        # Meta path used by NocoDB v2: POST /api/v2/meta/bases/{baseId}/tables
        result = request(
            base_url,
            token,
            "POST",
            f"/meta/bases/{args.base_id}/tables",
            payload,
        )
        tid = str(result.get("id") or result.get("table_id") or "")
        created[table] = tid
        print(f"  id={tid or '(see response)'}")
        if not tid:
            print(json.dumps(result, indent=2)[:500])

    if created and not args.dry_run:
        print("\nExport these for your shell / Cloud Agent env:")
        if created.get("facts"):
            print(f"export NOCODB_FACTS_TABLE='{created['facts']}'")
        if created.get("decisions"):
            print(f"export NOCODB_DECISIONS_TABLE='{created['decisions']}'")
        print("Then: python3 scripts/nocodb_sync.py check")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
