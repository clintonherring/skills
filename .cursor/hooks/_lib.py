#!/usr/bin/env python3
"""Shared helpers for agent-memory hooks and scripts."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any


def repo_root() -> Path:
    """Walk up from this file (or cwd) to find memory.config.json."""
    here = Path(__file__).resolve()
    for candidate in [here.parent.parent.parent, Path.cwd(), *Path.cwd().parents]:
        if (candidate / "memory.config.json").is_file():
            return candidate
    return Path.cwd()


def load_config(root: Path | None = None) -> dict[str, Any]:
    root = root or repo_root()
    path = root / "memory.config.json"
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def read_stdin_json() -> dict[str, Any]:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def emit(payload: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(payload))
    sys.stdout.flush()


def state_dir(root: Path | None = None, cfg: dict[str, Any] | None = None) -> Path:
    root = root or repo_root()
    cfg = cfg or load_config(root)
    path = root / cfg.get("state_dir", ".cursor/memory-state")
    path.mkdir(parents=True, exist_ok=True)
    return path


def conversation_id(payload: dict[str, Any]) -> str:
    return (
        str(payload.get("conversation_id") or "")
        or str(payload.get("session_id") or "")
        or "unknown"
    )


def flag_path(root: Path, cfg: dict[str, Any], conv_id: str, name: str) -> Path:
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in conv_id)[:120]
    return state_dir(root, cfg) / f"{name}-{safe}"


def set_flag(root: Path, cfg: dict[str, Any], conv_id: str, name: str, content: str = "1") -> None:
    path = flag_path(root, cfg, conv_id, name)
    path.write_text(content, encoding="utf-8")


def clear_flag(root: Path, cfg: dict[str, Any], conv_id: str, name: str) -> None:
    path = flag_path(root, cfg, conv_id, name)
    if path.exists():
        path.unlink()


def has_flag(root: Path, cfg: dict[str, Any], conv_id: str, name: str) -> bool:
    return flag_path(root, cfg, conv_id, name).is_file()


def read_text(path: Path, max_chars: int | None = None) -> str:
    if not path.is_file():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace")
    if max_chars is not None and len(text) > max_chars:
        return text[: max_chars - 20] + "\n…[truncated]\n"
    return text


def active_task_state(root: Path) -> str:
    active = root / "tasks" / "ACTIVE"
    if not active.is_file():
        return ""
    slug = active.read_text(encoding="utf-8", errors="replace").strip().splitlines()
    if not slug:
        return ""
    name = slug[0].strip()
    if not name or "/" in name or "\\" in name or name.startswith("."):
        return f"(invalid ACTIVE slug: {name!r})"
    state = root / "tasks" / name / "state.md"
    if not state.is_file():
        return f"(ACTIVE={name}; no tasks/{name}/state.md)"
    return f"### Task `{name}`\n\n{read_text(state)}"


def estimate_tokens(text: str, chars_per_token: float) -> int:
    if not text:
        return 0
    return max(1, int(len(text) / max(chars_per_token, 1)))


def build_restore_bundle(root: Path | None = None, cfg: dict[str, Any] | None = None) -> str:
    root = root or repo_root()
    cfg = cfg or load_config(root)
    files = cfg.get("files", {})
    budget = int(cfg.get("budget_tokens", 3000))
    cpt = float(cfg.get("chars_per_token", 4))
    budget_chars = int(budget * cpt)

    sections: list[tuple[str, str]] = []
    now_path = root / files.get("now", "memory/NOW.md")
    facts_path = root / files.get("facts", "memory/facts.md")
    decisions_path = root / files.get("decisions", "memory/decisions.md")

    now = read_text(now_path)
    if now:
        sections.append(("NOW (current intent)", now))

    task = active_task_state(root)
    if task:
        sections.append(("Active task state", task))

    facts = read_text(facts_path)
    if facts:
        sections.append(("Durable facts", facts))

    decisions = read_text(decisions_path)
    if decisions:
        sections.append(("Recent decisions", decisions))

    if not sections:
        return ""

    parts: list[str] = ["## Restored project memory", ""]
    used = estimate_tokens("\n".join(parts), cpt) * cpt  # rough char budget tracking
    used = len("\n".join(parts))

    for title, body in sections:
        header = f"### {title}\n\n"
        footer = "\n"
        room = budget_chars - used - len(header) - len(footer)
        if room < 40:
            parts.append(f"### {title}\n\n…[omitted; budget exhausted]\n")
            break
        body = body.strip()
        if len(body) > room:
            body = body[: max(0, room - 15)].rstrip() + "\n…[truncated]"
        block = f"{header}{body}{footer}"
        parts.append(block)
        used += len(block)
        if used >= budget_chars:
            break

    return "\n".join(parts).rstrip() + "\n"


def workspace_roots(payload: dict[str, Any]) -> list[Path]:
    roots = payload.get("workspace_roots") or []
    out: list[Path] = []
    if isinstance(roots, list):
        for item in roots:
            try:
                out.append(Path(str(item)))
            except (TypeError, ValueError):
                continue
    if not out:
        out.append(repo_root())
    return out
