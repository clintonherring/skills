#!/usr/bin/env python3
"""postToolUse / postToolUseFailure: reinject memory after compaction flag."""

from __future__ import annotations

import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _lib import (  # noqa: E402
    build_restore_bundle,
    clear_flag,
    conversation_id,
    emit,
    has_flag,
    load_config,
    read_stdin_json,
    repo_root,
)


def main() -> int:
    try:
        payload = read_stdin_json()
        root = repo_root()
        cfg = load_config(root)
        conv = conversation_id(payload)
        if not has_flag(root, cfg, conv, "needs_restore"):
            emit({})
            return 0
        bundle = build_restore_bundle(root, cfg)
        clear_flag(root, cfg, conv, "needs_restore")
        if not bundle:
            emit({})
            return 0
        emit({"additional_context": bundle})
    except Exception:
        traceback.print_exc(file=sys.stderr)
        emit({})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
