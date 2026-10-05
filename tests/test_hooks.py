#!/usr/bin/env python3
"""Hook lifecycle tests — no network, subprocess each hook."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOOKS = ROOT / ".cursor" / "hooks"
PY = sys.executable


def run_hook(script: str, payload: dict, cwd: Path | None = None) -> dict:
    proc = subprocess.run(
        [PY, str(HOOKS / script)],
        input=json.dumps(payload).encode(),
        capture_output=True,
        cwd=str(cwd or ROOT),
        check=False,
    )
    assert proc.returncode == 0, proc.stderr.decode()
    out = proc.stdout.decode().strip() or "{}"
    return json.loads(out)


class HookLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="memkit-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        # Isolate state dir inside tmp by copying minimal kit.
        for rel in (
            "memory.config.json",
            "memory/NOW.md",
            "memory/facts.md",
            "memory/decisions.md",
            ".cursor/hooks/_lib.py",
            ".cursor/hooks/pre_compact.py",
            ".cursor/hooks/post_tool_use.py",
            ".cursor/hooks/after_file_edit.py",
            ".cursor/hooks/stop.py",
        ):
            src = ROOT / rel
            dst = self.tmp / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        cfg = json.loads((self.tmp / "memory.config.json").read_text(encoding="utf-8"))
        cfg["state_dir"] = str(self.tmp / "state")
        (self.tmp / "memory.config.json").write_text(json.dumps(cfg), encoding="utf-8")
        # Point hooks at this tmp tree: _lib.repo_root walks to memory.config.json
        self.hooks = self.tmp / ".cursor" / "hooks"

    def _run(self, script: str, payload: dict) -> dict:
        proc = subprocess.run(
            [PY, str(self.hooks / script)],
            input=json.dumps(payload).encode(),
            capture_output=True,
            cwd=str(self.tmp),
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr.decode())
        return json.loads(proc.stdout.decode().strip() or "{}")

    def test_compaction_restore_lifecycle(self) -> None:
        conv = "conv-alpha"
        pre = self._run(
            "pre_compact.py",
            {
                "conversation_id": conv,
                "trigger": "auto",
                "context_usage_percent": 90,
            },
        )
        self.assertIn("compaction", pre.get("user_message", "").lower())
        flag = self.tmp / "state" / f"needs_restore-{conv}"
        self.assertTrue(flag.is_file())

        post = self._run(
            "post_tool_use.py",
            {"conversation_id": conv, "tool_name": "Shell"},
        )
        ctx = post.get("additional_context", "")
        self.assertIn("Restored project memory", ctx)
        self.assertIn("NOW", ctx)
        self.assertFalse(flag.exists())

        # Second postToolUse should be silent
        post2 = self._run(
            "post_tool_use.py",
            {"conversation_id": conv, "tool_name": "Shell"},
        )
        self.assertEqual(post2, {})

    def test_conversation_isolation(self) -> None:
        self._run("pre_compact.py", {"conversation_id": "a", "trigger": "manual"})
        out_b = self._run("post_tool_use.py", {"conversation_id": "b", "tool_name": "Read"})
        self.assertEqual(out_b, {})
        out_a = self._run("post_tool_use.py", {"conversation_id": "a", "tool_name": "Read"})
        self.assertIn("Restored project memory", out_a.get("additional_context", ""))

    def test_bundle_ordering_prefers_now(self) -> None:
        sys.path.insert(0, str(self.hooks))
        from _lib import build_restore_bundle, load_config  # type: ignore

        cfg = load_config(self.tmp)
        cfg["budget_tokens"] = 40  # tiny — only room for NOW-ish
        cfg["chars_per_token"] = 4
        (self.tmp / "memory" / "NOW.md").write_text("# NOW\nUNIQUE_NOW_MARKER\n", encoding="utf-8")
        (self.tmp / "memory" / "facts.md").write_text(
            "# facts\n" + ("FACTLINE\n" * 200), encoding="utf-8"
        )
        bundle = build_restore_bundle(self.tmp, cfg)
        self.assertIn("UNIQUE_NOW_MARKER", bundle)
        # Facts may be truncated/omitted but NOW must appear before facts heading content loss
        now_idx = bundle.find("UNIQUE_NOW_MARKER")
        fact_idx = bundle.find("FACTLINE")
        if fact_idx != -1:
            self.assertLess(now_idx, fact_idx)

    def test_budget_limit(self) -> None:
        sys.path.insert(0, str(self.hooks))
        from _lib import build_restore_bundle, estimate_tokens, load_config  # type: ignore

        cfg = load_config(self.tmp)
        cfg["budget_tokens"] = 100
        cfg["chars_per_token"] = 4
        (self.tmp / "memory" / "facts.md").write_text("X" * 5000, encoding="utf-8")
        bundle = build_restore_bundle(self.tmp, cfg)
        self.assertLessEqual(estimate_tokens(bundle, 4), 120)

    def test_nag_suppression(self) -> None:
        conv = "nag-1"
        # Dirty edit on non-memory file
        self._run(
            "after_file_edit.py",
            {
                "conversation_id": conv,
                "file_path": str(self.tmp / "src" / "app.py"),
            },
        )
        stop1 = self._run(
            "stop.py",
            {"conversation_id": conv, "status": "completed", "loop_count": 0},
        )
        self.assertIn("checkpoint", stop1.get("followup_message", "").lower())
        stop2 = self._run(
            "stop.py",
            {"conversation_id": conv, "status": "completed", "loop_count": 1},
        )
        self.assertEqual(stop2, {})

    def test_memory_edit_does_not_dirty(self) -> None:
        conv = "clean-1"
        self._run(
            "after_file_edit.py",
            {
                "conversation_id": conv,
                "file_path": str(self.tmp / "memory" / "NOW.md"),
            },
        )
        stop = self._run(
            "stop.py",
            {"conversation_id": conv, "status": "completed", "loop_count": 0},
        )
        self.assertEqual(stop, {})

    def test_malformed_stdin(self) -> None:
        proc = subprocess.run(
            [PY, str(self.hooks / "pre_compact.py")],
            input=b"not-json",
            capture_output=True,
            cwd=str(self.tmp),
            check=False,
        )
        self.assertEqual(proc.returncode, 0)
        json.loads(proc.stdout.decode() or "{}")

    def test_dangling_active(self) -> None:
        (self.tmp / "tasks").mkdir(parents=True, exist_ok=True)
        (self.tmp / "tasks" / "ACTIVE").write_text("missing-slug\n", encoding="utf-8")
        sys.path.insert(0, str(self.hooks))
        from _lib import active_task_state  # type: ignore

        text = active_task_state(self.tmp)
        self.assertIn("no tasks/missing-slug/state.md", text)

    def test_active_task_included(self) -> None:
        (self.tmp / "tasks" / "demo").mkdir(parents=True, exist_ok=True)
        (self.tmp / "tasks" / "ACTIVE").write_text("demo\n", encoding="utf-8")
        (self.tmp / "tasks" / "demo" / "state.md").write_text(
            "# state\nTASK_STATE_MARKER\n", encoding="utf-8"
        )
        self._run("pre_compact.py", {"conversation_id": "t1", "trigger": "auto"})
        out = self._run("post_tool_use.py", {"conversation_id": "t1", "tool_name": "Write"})
        self.assertIn("TASK_STATE_MARKER", out.get("additional_context", ""))


class LiveRepoSmoke(unittest.TestCase):
    def test_doctor_runs(self) -> None:
        proc = subprocess.run(
            [PY, str(ROOT / "scripts" / "memory_doctor.py")],
            capture_output=True,
            cwd=str(ROOT),
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout.decode() + proc.stderr.decode())
        self.assertIn("doctor:", proc.stdout.decode())


if __name__ == "__main__":
    unittest.main()
