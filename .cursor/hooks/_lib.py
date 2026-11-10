#!/usr/bin/env python3
"""Shared helpers for agent-memory hooks and scripts."""

from __future__ import annotations

import json
import os
import subprocess
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


def relative_posix(path: str, root: Path) -> str:
    try:
        return str(Path(path).resolve().relative_to(root.resolve())).replace("\\", "/")
    except Exception:
        return path.replace("\\", "/")


def is_decisions_path(path: str, root: Path, cfg: dict[str, Any] | None = None) -> bool:
    cfg = cfg or load_config(root)
    decisions_rel = str(cfg.get("files", {}).get("decisions", "memory/decisions.md")).replace("\\", "/")
    rel = relative_posix(path, root)
    return rel == decisions_rel or rel.endswith("/" + decisions_rel)


def is_now_path(path: str, root: Path, cfg: dict[str, Any] | None = None) -> bool:
    cfg = cfg or load_config(root)
    now_rel = str(cfg.get("files", {}).get("now", "memory/NOW.md")).replace("\\", "/")
    rel = relative_posix(path, root)
    return rel == now_rel or rel.endswith("/" + now_rel)


def nocodb_env_ready(cfg: dict[str, Any]) -> bool:
    n = cfg.get("nocodb", {})
    required = (
        n.get("base_url_env", "NOCODB_BASE_URL"),
        n.get("token_env", "NOCODB_TOKEN"),
        n.get("facts_table_env", "NOCODB_FACTS_TABLE"),
        n.get("decisions_table_env", "NOCODB_DECISIONS_TABLE"),
    )
    return all(bool(os.environ.get(str(name) or "")) for name in required)


def nocodb_now_ready(cfg: dict[str, Any]) -> bool:
    n = cfg.get("nocodb", {})
    base_ok = bool(os.environ.get(str(n.get("base_url_env", "NOCODB_BASE_URL") or "")))
    token_ok = bool(os.environ.get(str(n.get("token_env", "NOCODB_TOKEN") or "")))
    now_env = os.environ.get(str(n.get("now_table_env", "NOCODB_NOW_TABLE") or ""), "")
    now_cfg = str(n.get("now_table") or "")
    return base_ok and token_ok and bool(now_env or now_cfg)


def _run_nocodb_cmd(
    root: Path,
    cfg: dict[str, Any],
    command: str,
    *,
    reason: str,
    extra_args: list[str] | None = None,
) -> bool:
    script = root / "scripts" / "nocodb_sync.py"
    if not script.is_file():
        return False
    timeout = float(cfg.get("nocodb", {}).get("push_timeout_sec") or 20)
    cmd = [sys.executable, str(script), command, *(extra_args or [])]
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        if proc.returncode != 0:
            msg = (proc.stderr or proc.stdout or "").strip()[:300]
            if msg:
                print(f"nocodb {command} failed ({reason}): {msg}", file=sys.stderr)
            return False
        return True
    except Exception as exc:  # noqa: BLE001 — hooks must fail open
        print(f"nocodb {command} error ({reason}): {exc}", file=sys.stderr)
        return False


def try_push_decisions(
    root: Path | None = None,
    cfg: dict[str, Any] | None = None,
    *,
    reason: str = "",
) -> bool:
    """Best-effort upsert of decisions.md → NocoDB. Never raises; returns True on success."""
    root = root or repo_root()
    cfg = cfg or load_config(root)
    if cfg.get("nocodb", {}).get("auto_push_decisions", True) is False:
        return False
    if not nocodb_env_ready(cfg):
        return False
    return _run_nocodb_cmd(root, cfg, "push-decisions", reason=reason)


def try_push_now(
    root: Path | None = None,
    cfg: dict[str, Any] | None = None,
    *,
    reason: str = "",
    source: str = "desktop",
) -> bool:
    """Best-effort NOW.md snapshot → NocoDB. Never raises; returns True on success."""
    root = root or repo_root()
    cfg = cfg or load_config(root)
    if cfg.get("nocodb", {}).get("auto_push_now", True) is False:
        return False
    if not nocodb_now_ready(cfg):
        return False
    return _run_nocodb_cmd(
        root,
        cfg,
        "push-now",
        reason=reason,
        extra_args=["--source", source],
    )
