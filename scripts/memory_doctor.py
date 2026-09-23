#!/usr/bin/env python3
"""Diagnose agent-memory kit health. Exit 0 always unless --strict."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / ".cursor" / "hooks"))

from _lib import build_restore_bundle, load_config, repo_root, state_dir  # noqa: E402


def ok(msg: str) -> None:
    print(f"OK   {msg}")


def warn(msg: str) -> None:
    print(f"WARN {msg}")


def bad(msg: str) -> None:
    print(f"FAIL {msg}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnose agent-memory kit")
    parser.add_argument("--strict", action="store_true", help="Exit 1 on FAIL")
    args = parser.parse_args()
    root = repo_root()
    failures = 0

    cfg_path = root / "memory.config.json"
    if not cfg_path.is_file():
        bad(f"missing {cfg_path}")
        failures += 1
        cfg = {}
    else:
        try:
            cfg = load_config(root)
            ok(f"config {cfg_path}")
        except Exception as exc:
            bad(f"config parse: {exc}")
            failures += 1
            cfg = {}

    hooks = root / ".cursor" / "hooks.json"
    if hooks.is_file():
        try:
            data = json.loads(hooks.read_text(encoding="utf-8"))
            events = data.get("hooks", {})
            for name in ("preCompact", "postToolUse", "afterFileEdit", "stop"):
                if name in events:
                    ok(f"hook registered: {name}")
                else:
                    bad(f"hook missing: {name}")
                    failures += 1
        except Exception as exc:
            bad(f"hooks.json: {exc}")
            failures += 1
    else:
        bad("missing .cursor/hooks.json")
        failures += 1

    for rel in (
        ".cursor/hooks/pre_compact.py",
        ".cursor/hooks/post_tool_use.py",
        ".cursor/hooks/after_file_edit.py",
        ".cursor/hooks/stop.py",
        ".cursor/rules/agent-memory.mdc",
        ".cursor/skills/agent-memory/SKILL.md",
        "memory/NOW.md",
        "memory/facts.md",
        "memory/decisions.md",
    ):
        path = root / rel
        if path.is_file():
            ok(rel)
        else:
            bad(f"missing {rel}")
            failures += 1

    # Smoke-run each hook with empty / minimal JSON
    for script, stdin in (
        ("pre_compact.py", '{"conversation_id":"doctor","trigger":"manual"}'),
        ("post_tool_use.py", '{"conversation_id":"doctor","tool_name":"Shell"}'),
        ("after_file_edit.py", '{"conversation_id":"doctor","file_path":"/tmp/x"}'),
        ("stop.py", '{"conversation_id":"doctor","status":"completed","loop_count":0}'),
    ):
        path = root / ".cursor" / "hooks" / script
        if not path.is_file():
            continue
        try:
            proc = subprocess.run(
                [sys.executable, str(path)],
                input=stdin.encode(),
                capture_output=True,
                timeout=10,
                check=False,
            )
            if proc.returncode != 0:
                bad(f"{script} exit {proc.returncode}: {proc.stderr.decode()[:200]}")
                failures += 1
            else:
                json.loads(proc.stdout.decode() or "{}")
                ok(f"{script} smoke")
        except Exception as exc:
            bad(f"{script} smoke: {exc}")
            failures += 1

    if cfg:
        bundle = build_restore_bundle(root, cfg)
        if bundle:
            ok(f"restore bundle {len(bundle)} chars")
        else:
            warn("restore bundle empty")
        sd = state_dir(root, cfg)
        flags = list(sd.glob("*"))
        if flags:
            warn(f"{len(flags)} state flag(s) in {sd}")
        else:
            ok(f"state dir clean ({sd})")

    nocodb = cfg.get("nocodb", {}) if cfg else {}
    for key in ("base_url_env", "token_env", "facts_table_env", "decisions_table_env"):
        env_name = nocodb.get(key)
        if not env_name:
            warn(f"config nocodb.{key} unset")
            continue
        import os

        if os.environ.get(env_name):
            ok(f"env {env_name} set")
        else:
            warn(f"env {env_name} not set (NocoDB sync disabled)")

    print()
    if failures:
        print(f"{failures} failure(s)")
        return 1 if args.strict else 0
    print("doctor: all required checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
