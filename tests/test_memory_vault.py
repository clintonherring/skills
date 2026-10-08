#!/usr/bin/env python3
"""Tests for scripts/memory_vault.py."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable
SCRIPT = ROOT / "scripts" / "memory_vault.py"


class MemoryVaultTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="vault-"))
        self.env = os.environ.copy()
        # Point user vault at tmp; project/team use repo paths — use isolated copy via cwd tricks
        self.env["AGENT_MEMORY_USER_ROOT"] = str(self.tmp / "user")

    def run_vault(self, *args: str, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [PY, str(SCRIPT), *args],
            input=input_text,
            text=True,
            capture_output=True,
            cwd=str(ROOT),
            env=self.env,
            check=False,
        )

    def test_save_search_read_roundtrip(self) -> None:
        body = "The migration tests pass; rollout is still pending."
        proc = self.run_vault(
            "save",
            "--title",
            "Auth migration status",
            "--kind",
            "context",
            "--scope",
            "project",
            "--tag",
            "auth",
            "--stdin",
            input_text=body,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        mid = proc.stdout.strip().splitlines()[0]
        self.assertTrue(mid.startswith("mem_"))

        search = self.run_vault("search", "migration")
        self.assertEqual(search.returncode, 0)
        self.assertIn(mid, search.stdout)

        read = self.run_vault("read", mid)
        self.assertEqual(read.returncode, 0)
        self.assertIn(body, read.stdout)
        self.assertIn("ecc.memory.v1", read.stdout)

        # cleanup created project file
        path = ROOT / "memory" / "vault" / "project" / f"{mid}.md"
        if path.exists():
            path.unlink()

    def test_rejects_secrets(self) -> None:
        proc = self.run_vault(
            "save",
            "--title",
            "Bad",
            "--stdin",
            input_text="api_key=SUPERSECRETVALUE123456",
        )
        self.assertNotEqual(proc.returncode, 0)

    def test_create_only(self) -> None:
        body = "Unique body for create-only test xyzzy"
        first = self.run_vault(
            "save",
            "--title",
            "Once",
            "--id",
            "mem_createonlytest001",
            "--stdin",
            input_text=body,
        )
        self.assertEqual(first.returncode, 0, first.stderr)
        second = self.run_vault(
            "save",
            "--title",
            "Twice",
            "--id",
            "mem_createonlytest001",
            "--stdin",
            input_text=body + "2",
        )
        self.assertNotEqual(second.returncode, 0)
        path = ROOT / "memory" / "vault" / "project" / "mem_createonlytest001.md"
        if path.exists():
            path.unlink()

    def test_doctor(self) -> None:
        proc = self.run_vault("doctor")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_handoff(self) -> None:
        proc = self.run_vault(
            "handoff",
            "--from",
            "cursor",
            "--target",
            "cursor",
            "--title",
            "Finish rollout",
            input_text="## Objective\nShip it\n## Next\nDeploy canary\n",
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        mid = proc.stdout.strip().splitlines()[0]
        path = ROOT / "memory" / "vault" / "project" / f"{mid}.md"
        self.assertTrue(path.is_file())
        text = path.read_text(encoding="utf-8")
        self.assertIn("kind: handoff", text)
        path.unlink()


if __name__ == "__main__":
    unittest.main()
