#!/usr/bin/env python3
"""Lightweight ecc.memory.v1 vault — save/search/read/handoff/doctor (stdlib only).

Adapted from affaan-m/ECC Memory Vault (MIT). Does not require ecc-universal.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
SECRET_RE = re.compile(
    r"(?i)(-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|"
    r"\b(api[_-]?key|secret|password|token)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{16,})"
)
ID_RE = re.compile(r"^mem_[a-z0-9][a-z0-9_-]{2,127}$")
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def user_vault_root() -> Path:
    override = os.environ.get("AGENT_MEMORY_USER_ROOT")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".cursor" / "agent-memory" / "vault"


def scope_dir(scope: str) -> Path:
    if scope == "user":
        return user_vault_root()
    if scope == "project":
        return ROOT / "memory" / "vault" / "project"
    if scope == "team":
        return ROOT / "memory" / "vault" / "team"
    raise SystemExit(f"Unknown scope: {scope}")


def make_id(title: str, body: str) -> str:
    digest = hashlib.sha256(f"{title}\n{body}\n{utc_now()}".encode()).hexdigest()[:16]
    return f"mem_{digest}"


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}, text
    raw = text[4:end]
    body = text[end + 5 :]
    meta: dict[str, Any] = {}
    for line in raw.splitlines():
        if not line.strip() or line.strip().startswith("#") or ":" not in line:
            continue
        key, val = line.split(":", 1)
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key in ("tags", "links", "targetHarnesses"):
            inner = val.strip("[]").strip()
            meta[key] = [p.strip() for p in inner.split(",") if p.strip()] if inner else []
        else:
            meta[key] = val
    return meta, body.lstrip("\n")


def render_doc(meta: dict[str, Any], body: str) -> str:
    def fmt_list(items: list[str]) -> str:
        return "[" + ", ".join(items) + "]"

    lines = [
        "---",
        f"schema: {meta['schema']}",
        f"id: {meta['id']}",
        f'title: "{meta["title"]}"',
        f"kind: {meta['kind']}",
        f"scope: {meta['scope']}",
        f"trust: {meta['trust']}",
        f"status: {meta['status']}",
        f"sourceHarness: {meta['sourceHarness']}",
        f"targetHarnesses: {fmt_list(meta['targetHarnesses'])}",
        f"tags: {fmt_list(meta.get('tags') or [])}",
        f"links: {fmt_list(meta.get('links') or [])}",
        f"createdAt: {meta['createdAt']}",
        f"updatedAt: {meta['updatedAt']}",
        "---",
        "",
        body.rstrip() + "\n",
    ]
    return "\n".join(lines)


def load_doc(path: Path) -> dict[str, Any] | None:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    meta, body = parse_frontmatter(text)
    if meta.get("schema") != "ecc.memory.v1" or not meta.get("id"):
        return None
    meta["body"] = body
    meta["path"] = str(path)
    return meta


def iter_docs(scopes: list[str], *, active_only: bool = True) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for scope in scopes:
        root = scope_dir(scope)
        if not root.is_dir():
            continue
        for path in sorted(root.glob("mem_*.md")):
            if path.is_symlink():
                continue
            doc = load_doc(path)
            if not doc:
                continue
            if active_only and doc.get("status", "active") != "active":
                continue
            out.append(doc)
    return out


def cmd_init(_: argparse.Namespace) -> int:
    for scope in ("project", "team"):
        d = scope_dir(scope)
        d.mkdir(parents=True, exist_ok=True)
        print(f"OK {d}")
    user = user_vault_root()
    user.mkdir(parents=True, exist_ok=True)
    print(f"OK {user} (user)")
    return 0


def cmd_save(args: argparse.Namespace) -> int:
    if args.stdin:
        body = sys.stdin.read()
    elif args.body_file:
        body = Path(args.body_file).read_text(encoding="utf-8")
    else:
        raise SystemExit("Provide --stdin or --body-file (never pass secrets on argv)")
    body = body.strip()
    if not body:
        raise SystemExit("Empty body")
    if SECRET_RE.search(body) or SECRET_RE.search(args.title):
        raise SystemExit("Refusing to save: body/title looks like it contains a secret")

    mid = args.id or make_id(args.title, body)
    if not ID_RE.match(mid):
        raise SystemExit(f"Invalid id: {mid}")
    targets = [t.strip() for t in (args.target or "all").split(",") if t.strip()]
    for t in targets:
        if not SLUG_RE.match(t):
            raise SystemExit(f"Invalid target harness: {t}")
    tags = list(args.tag or [])
    links = list(args.link or [])
    now = utc_now()
    meta = {
        "schema": "ecc.memory.v1",
        "id": mid,
        "title": args.title,
        "kind": args.kind,
        "scope": args.scope,
        "trust": "unreviewed",
        "status": "active",
        "sourceHarness": args.source_harness,
        "targetHarnesses": targets,
        "tags": tags,
        "links": links,
        "createdAt": now,
        "updatedAt": now,
    }
    dest_dir = scope_dir(args.scope)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{mid}.md"
    if dest.exists():
        raise SystemExit(f"Create-only: {dest} already exists")
    dest.write_text(render_doc(meta, body), encoding="utf-8")
    print(mid)
    print(dest)
    return 0


def cmd_handoff(args: argparse.Namespace) -> int:
    body = Path(args.body_file).read_text(encoding="utf-8") if args.body_file else sys.stdin.read()
    if SECRET_RE.search(body):
        raise SystemExit("Refusing handoff: body looks like it contains a secret")
    mid = make_id(args.title, body)
    now = utc_now()
    meta = {
        "schema": "ecc.memory.v1",
        "id": mid,
        "title": args.title,
        "kind": "handoff",
        "scope": args.scope,
        "trust": "unreviewed",
        "status": "active",
        "sourceHarness": args.from_harness,
        "targetHarnesses": [args.target],
        "tags": list(args.tag or []),
        "links": list(args.link or []),
        "createdAt": now,
        "updatedAt": now,
    }
    dest_dir = scope_dir(args.scope)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{mid}.md"
    dest.write_text(render_doc(meta, body.strip()), encoding="utf-8")
    print(mid)
    print(dest)
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    scopes = ["project", "team"]
    if args.scope == "user":
        scopes = ["user"]
    elif args.scope:
        scopes = [args.scope]
    q = args.query.lower()
    hits = []
    for doc in iter_docs(scopes, active_only=True):
        blob = f"{doc.get('title','')} {' '.join(doc.get('tags') or [])} {doc.get('body','')}".lower()
        if q in blob:
            if args.target_harness and args.target_harness != "all":
                targets = doc.get("targetHarnesses") or []
                if "all" not in targets and args.target_harness not in targets:
                    continue
            hits.append(doc)
    for doc in hits[: args.limit]:
        print(f"{doc['id']}\t{doc.get('kind')}\t{doc.get('scope')}\t{doc.get('title')}")
    if not hits:
        print("(no matches)")
    return 0


def cmd_read(args: argparse.Namespace) -> int:
    scopes = ["project", "team", "user"]
    for doc in iter_docs(scopes, active_only=False):
        if doc["id"] == args.id:
            print(Path(doc["path"]).read_text(encoding="utf-8"))
            return 0
    raise SystemExit(f"Not found: {args.id}")


def cmd_doctor(_: argparse.Namespace) -> int:
    problems = 0
    for scope in ("project", "team", "user"):
        root = scope_dir(scope)
        if not root.exists():
            print(f"WARN missing scope dir: {root}")
            continue
        print(f"OK scope {scope}: {root}")
        for path in sorted(root.glob("*.md")):
            if path.name in ("README.md",):
                continue
            if path.is_symlink():
                print(f"FAIL symlink skipped: {path}")
                problems += 1
                continue
            doc = load_doc(path)
            if not doc:
                print(f"FAIL unreadable/invalid: {path}")
                problems += 1
                continue
            if not ID_RE.match(str(doc.get("id", ""))):
                print(f"FAIL bad id in {path}")
                problems += 1
            if doc.get("trust") != "unreviewed":
                print(f"WARN unexpected trust in {path}: {doc.get('trust')}")
    print("doctor: ok" if problems == 0 else f"doctor: {problems} problem(s)")
    return 1 if problems else 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="ecc.memory.v1 vault (stdlib)")
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("init").set_defaults(func=cmd_init)

    s = sub.add_parser("save")
    s.add_argument("--title", required=True)
    s.add_argument("--kind", default="context", choices=[
        "context", "decision", "fact", "handoff", "lesson", "note", "preference", "runbook"
    ])
    s.add_argument("--scope", default="project", choices=["project", "team", "user"])
    s.add_argument("--source-harness", default="cursor")
    s.add_argument("--target", default="all", help="Comma-separated harnesses or 'all'")
    s.add_argument("--tag", action="append", default=[])
    s.add_argument("--link", action="append", default=[])
    s.add_argument("--id")
    s.add_argument("--stdin", action="store_true")
    s.add_argument("--body-file")
    s.set_defaults(func=cmd_save)

    h = sub.add_parser("handoff")
    h.add_argument("--from", dest="from_harness", required=True)
    h.add_argument("--target", required=True)
    h.add_argument("--title", required=True)
    h.add_argument("--scope", default="project", choices=["project", "team", "user"])
    h.add_argument("--body-file")
    h.add_argument("--tag", action="append", default=[])
    h.add_argument("--link", action="append", default=[])
    h.set_defaults(func=cmd_handoff)

    q = sub.add_parser("search")
    q.add_argument("query")
    q.add_argument("--scope", choices=["project", "team", "user"])
    q.add_argument("--target-harness")
    q.add_argument("--limit", type=int, default=20)
    q.set_defaults(func=cmd_search)

    r = sub.add_parser("read")
    r.add_argument("id")
    r.set_defaults(func=cmd_read)

    sub.add_parser("doctor").set_defaults(func=cmd_doctor)
    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
