"""Shared helpers: locate config.json and the person's data folder. Stdlib only."""
import json
from pathlib import Path

CONFIG_PATH = Path.home() / ".job-post-resume-writer" / "config.json"


def load_config():
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def data_dir():
    cfg = load_config()
    d = cfg.get("data_dir")
    return Path(d).expanduser() if d else None


def default_facts():
    d = data_dir()
    return d / "facts.md" if d else None


def default_voice():
    d = data_dir()
    return d / "voice.md" if d else None
