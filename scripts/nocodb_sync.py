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
from datetime import datetime, timezone
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

    def update_records(self, table_id: str, rows: list[dict[str, Any]]) -> Any:
        # NocoDB v2 bulk update: PATCH with objects that include Id.
        return self.request("PATCH", f"/tables/{table_id}/records", rows)

    def get_table_meta(self, table_id: str) -> Any:
        # Prefer columns endpoint shapes used by NocoDB v2.
        try:
            return self.request("GET", f"/meta/tables/{table_id}")
        except RuntimeError:
            return self.request("GET", f"/tables/{table_id}")


def load_cfg() -> dict[str, Any]:
    with (ROOT / "memory.config.json").open(encoding="utf-8") as fh:
        return json.load(fh)


def env_from_cfg(cfg: dict[str, Any]) -> tuple[str, str, str, str, str]:
    n = cfg.get("nocodb", {})
    base = os.environ.get(n.get("base_url_env", "NOCODB_BASE_URL"), "")
    token = os.environ.get(n.get("token_env", "NOCODB_TOKEN"), "")
    facts = os.environ.get(n.get("facts_table_env", "NOCODB_FACTS_TABLE"), "")
    decisions = os.environ.get(n.get("decisions_table_env", "NOCODB_DECISIONS_TABLE"), "")
    now = os.environ.get(n.get("now_table_env", "NOCODB_NOW_TABLE"), "") or str(
        n.get("now_table") or ""
    )
    return base, token, facts, decisions, now


def require_client(cfg: dict[str, Any]) -> tuple[NocoClient, str, str]:
    base, token, facts, decisions, _now = env_from_cfg(cfg)
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


def require_now_table(cfg: dict[str, Any]) -> tuple[NocoClient, str]:
    base, token, _facts, _decisions, now = env_from_cfg(cfg)
    missing = [
        name
        for name, val in (
            ("NOCODB_BASE_URL", base),
            ("NOCODB_TOKEN", token),
            ("NOCODB_NOW_TABLE or nocodb.now_table", now),
        )
        if not val
    ]
    if missing:
        raise SystemExit(f"Missing env/config: {', '.join(missing)}")
    return NocoClient(base, token), now


def expected_columns() -> dict[str, list[str]]:
    path = ROOT / "nocodb" / "tables.csv"
    by_table: dict[str, list[str]] = {}
    with path.open(encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            by_table.setdefault(row["table"], []).append(row["column"])
    return by_table


def _print_table_contract(client: NocoClient, label: str, tid: str, expected: dict[str, list[str]]) -> None:
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


def cmd_check(cfg: dict[str, Any]) -> int:
    client, facts_id, decisions_id = require_client(cfg)
    expected = expected_columns()
    print("Expected columns from nocodb/tables.csv:")
    for table, cols in expected.items():
        print(f"  {table}: {', '.join(cols)}")
    for label, tid in (("facts", facts_id), ("decisions", decisions_id)):
        _print_table_contract(client, label, tid, expected)
    _base, _token, _facts, _decisions, now_id = env_from_cfg(cfg)
    if now_id:
        _print_table_contract(client, "now", now_id, expected)
    else:
        print("\nnow table: not configured (set NOCODB_NOW_TABLE or nocodb.now_table)")
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
    print(f"Wrote {len(rows)} facts -> {path}")
    return 0


DEFAULT_PROJECT = "clintonherring/skills"


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


def decision_project(cfg: dict[str, Any]) -> str:
    return str(cfg.get("nocodb", {}).get("project") or DEFAULT_PROJECT)


def decision_identity(row: dict[str, Any], project: str) -> tuple[str, str, str]:
    return (
        str(row.get("Date") or "").strip(),
        str(row.get("Decision") or "").strip(),
        str(row.get("Project") or project).strip(),
    )


def remote_record_id(row: dict[str, Any]) -> str | int | None:
    if row.get("Id") is not None:
        return row["Id"]
    if row.get("id") is not None:
        return row["id"]
    return None


def cmd_push_decisions(cfg: dict[str, Any]) -> int:
    client, _, decisions_id = require_client(cfg)
    path = ROOT / cfg["files"]["decisions"]
    project = decision_project(cfg)
    local_rows = [
        {
            "Date": r["Date"],
            "Decision": r["Decision"],
            "Rationale": r["Rationale"],
            "Project": project,
        }
        for r in parse_decisions_md(path.read_text(encoding="utf-8"))
    ]
    if not local_rows:
        print("No decision rows to push")
        return 0

    existing = client.list_records(decisions_id)
    by_key: dict[tuple[str, str, str], dict[str, Any]] = {}
    for remote in existing:
        key = decision_identity(remote, project)
        # Prefer the earliest Id when duplicates already exist remotely.
        if key not in by_key:
            by_key[key] = remote

    to_create: list[dict[str, Any]] = []
    to_update: list[dict[str, Any]] = []
    for row in local_rows:
        key = decision_identity(row, project)
        remote = by_key.get(key)
        if remote is None:
            to_create.append(row)
            continue
        remote_rationale = str(remote.get("Rationale") or "")
        if remote_rationale != row["Rationale"]:
            rid = remote_record_id(remote)
            if rid is None:
                continue
            to_update.append(
                {
                    "Id": rid,
                    "Date": row["Date"],
                    "Decision": row["Decision"],
                    "Rationale": row["Rationale"],
                    "Project": project,
                }
            )

    if to_create:
        client.create_records(decisions_id, to_create)
    if to_update:
        client.update_records(decisions_id, to_update)
    print(
        f"Upserted decisions -> {decisions_id} "
        f"(created={len(to_create)} updated={len(to_update)} unchanged={len(local_rows) - len(to_create) - len(to_update)})"
    )
    return 0


def cmd_push_now(cfg: dict[str, Any], *, source: str = "desktop") -> int:
    """Upsert one NOW snapshot row per project (high-churn intent for Cloud Agents)."""
    client, now_id = require_now_table(cfg)
    path = ROOT / cfg["files"]["now"]
    if not path.is_file():
        print(f"No NOW file at {path}")
        return 0
    content = path.read_text(encoding="utf-8")
    project = decision_project(cfg)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    existing = client.list_records(now_id)
    match = next(
        (row for row in existing if str(row.get("Project") or "").strip() == project),
        None,
    )
    payload = {
        "Project": project,
        "Content": content,
        "Updated": stamp,
        "Source": source,
    }
    if match is None:
        client.create_records(now_id, [payload])
        print(f"Created NOW snapshot -> {now_id} project={project}")
        return 0
    rid = remote_record_id(match)
    if rid is None:
        raise SystemExit("Remote NOW row missing Id")
    if str(match.get("Content") or "") == content:
        print(f"NOW snapshot unchanged -> {now_id} project={project}")
        return 0
    client.update_records(now_id, [{"Id": rid, **payload}])
    print(f"Updated NOW snapshot -> {now_id} project={project}")
    return 0


def cmd_pull_now(cfg: dict[str, Any]) -> int:
    """Write Noco NOW snapshot for this project into memory/NOW.md (Cloud session start)."""
    client, now_id = require_now_table(cfg)
    project = decision_project(cfg)
    existing = client.list_records(now_id)
    match = next(
        (row for row in existing if str(row.get("Project") or "").strip() == project),
        None,
    )
    if match is None:
        print(f"No NOW snapshot in Noco for project={project}")
        return 1
    content = str(match.get("Content") or "")
    if not content.strip():
        print("Remote NOW snapshot is empty")
        return 1
    path = ROOT / cfg["files"]["now"]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"Wrote NOW snapshot -> {path} (source={match.get('Source')})")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="NocoDB Agent Memory sync")
    parser.add_argument(
        "command",
        choices=("check", "pull-facts", "push-decisions", "push-now", "pull-now"),
        help="check | pull-facts | push-decisions | push-now | pull-now",
    )
    parser.add_argument(
        "--source",
        default="desktop",
        help="Source label for push-now (desktop|cloud|manual)",
    )
    # Allow injecting a stand-in client in tests via monkeypatching NocoClient.
    args = parser.parse_args()
    cfg = load_cfg()
    if args.command == "check":
        return cmd_check(cfg)
    if args.command == "pull-facts":
        return cmd_pull_facts(cfg)
    if args.command == "push-decisions":
        return cmd_push_decisions(cfg)
    if args.command == "push-now":
        return cmd_push_now(cfg, source=str(args.source or "desktop"))
    return cmd_pull_now(cfg)


if __name__ == "__main__":
    raise SystemExit(main())
