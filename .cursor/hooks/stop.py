#!/usr/bin/env python3
"""stop: once per dirty stretch, ask for a memory checkpoint."""

from __future__ import annotations

import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _lib import (  # noqa: E402
    clear_flag,
    conversation_id,
    emit,
    has_flag,
    load_config,
    read_stdin_json,
    repo_root,
    set_flag,
)


def main() -> int:
    try:
        payload = read_stdin_json()
        root = repo_root()
        cfg = load_config(root)
        conv = conversation_id(payload)
        status = payload.get("status", "completed")
        if status != "completed":
            emit({})
            return 0
        if not has_flag(root, cfg, conv, "dirty_edits"):
            emit({})
            return 0
        if has_flag(root, cfg, conv, "nag_sent"):
            emit({})
            return 0
        set_flag(root, cfg, conv, "nag_sent")
        clear_flag(root, cfg, conv, "dirty_edits")
        emit(
            {
                "followup_message": (
                    "Memory checkpoint: update `memory/NOW.md` (and promote durable "
                    "items to `memory/facts.md` / `memory/decisions.md` if needed) "
                    "before this session's context is compacted."
                )
            }
        )
    except Exception:
        traceback.print_exc(file=sys.stderr)
        emit({})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
