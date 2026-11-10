#!/usr/bin/env python3
"""afterFileEdit: mark conversation dirty until a memory checkpoint."""

from __future__ import annotations

import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _lib import (  # noqa: E402
    clear_flag,
    conversation_id,
    emit,
    is_decisions_path,
    is_now_path,
    load_config,
    read_stdin_json,
    repo_root,
    set_flag,
    try_push_decisions,
    try_push_now,
)


MEMORY_PREFIXES = (
    "memory/",
    "tasks/",
    ".cursor/memory-state/",
    "memory.config.json",
)


def is_memory_path(path: str, root: Path) -> bool:
    try:
        rel = str(Path(path).resolve().relative_to(root.resolve())).replace("\\", "/")
    except Exception:
        rel = path.replace("\\", "/")
    return any(rel == p or rel.startswith(p) for p in MEMORY_PREFIXES)


def main() -> int:
    try:
        payload = read_stdin_json()
        root = repo_root()
        cfg = load_config(root)
        path = str(payload.get("file_path") or "")
        if path and not is_memory_path(path, root):
            set_flag(root, cfg, conversation_id(payload), "dirty_edits")
        conv = conversation_id(payload)
        if path and is_decisions_path(path, root, cfg):
            set_flag(root, cfg, conv, "decisions_touched")
            if try_push_decisions(root, cfg, reason="afterFileEdit"):
                clear_flag(root, cfg, conv, "decisions_touched")
        if path and is_now_path(path, root, cfg):
            set_flag(root, cfg, conv, "now_touched")
            if try_push_now(root, cfg, reason="afterFileEdit", source="desktop"):
                clear_flag(root, cfg, conv, "now_touched")
        emit({})
    except Exception:
        traceback.print_exc(file=sys.stderr)
        emit({})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
