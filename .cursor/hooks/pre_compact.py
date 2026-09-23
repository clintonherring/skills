#!/usr/bin/env python3
"""preCompact: observational only — set restore flag for postToolUse."""

from __future__ import annotations

import sys
import traceback
from pathlib import Path

# Allow importing sibling _lib when Cursor invokes this script by path.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _lib import (  # noqa: E402
    conversation_id,
    emit,
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
        set_flag(root, cfg, conv, "needs_restore")
        trigger = payload.get("trigger", "auto")
        pct = payload.get("context_usage_percent")
        msg = f"Agent memory: compaction ({trigger}"
        if pct is not None:
            msg += f", ~{pct}% context"
        msg += "). Will reinject NOW/facts on the next tool call."
        emit({"user_message": msg})
    except Exception:
        # Fail open — never block compaction.
        traceback.print_exc(file=sys.stderr)
        emit({})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
