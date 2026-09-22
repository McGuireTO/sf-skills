#!/usr/bin/env python3
"""Offline gate tests for this plugin's public-release verifier.

Auto-discovered and run by scripts/run-plugin-gate-tests.ts (`npm run test:gates`),
which invokes `python3 <file>` directly — so this suite is self-contained
(no shared _test_support import) and self-runs via unittest.main().

The verifier is the release-time fail-closed gate: two workflow steps in
release-to-public.yml iterate PLUGIN_ALLOWLIST (which now includes
salesforce-code-quality) and invoke each plugin's own copy of this script before
its tree is copied into the public marketplace repo. These tests pin the two
invariants it enforces — tree safety (no links/special/transient/oversized
entries) and plugin.json identity (name == directory) — plus that this plugin's
real, checked-in tree passes the gate.
"""
from __future__ import annotations

import sys

# Import the verifier WITHOUT leaving a scripts/__pycache__ behind: this test
# loads the module by path (below), and the real plugin tree it later asserts is
# publishable includes that very scripts/ dir. A stray import-time __pycache__
# would make test_real_checked_in_tree_passes_the_gate fail against its own side
# effect (the verifier only sets sys.dont_write_bytecode when run as __main__, so
# we must set it here before the import happens). Must precede the import below.
sys.dont_write_bytecode = True

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = PLUGIN_ROOT / "scripts" / "verify-public-plugin-release.py"


def _load_verifier():
    spec = importlib.util.spec_from_file_location("verify_public_plugin_release", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _make_plugin_tree(root: Path, name: str) -> Path:
    """Write a minimal, valid publishable plugin tree and return its root."""
    plugin_dir = root / name
    (plugin_dir / ".claude-plugin").mkdir(parents=True)
    (plugin_dir / ".claude-plugin" / "plugin.json").write_text(
        json.dumps({"name": name, "version": "0.1.0", "skills": "./skills/"}),
        encoding="utf-8",
    )
    skill_dir = plugin_dir / "skills" / "dx-code-analyzer-run"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# dx-code-analyzer-run\n", encoding="utf-8")
    return plugin_dir


class VerifyPublicPluginReleaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load_verifier()

    def test_real_checked_in_tree_passes_the_gate(self):
        # The actual plugin tree that ships to the public marketplace must clear
        # its own release gate — otherwise the allowlisted release step fails.
        evidence = self.mod.verify(PLUGIN_ROOT)
        self.assertGreater(evidence["files"], 0)

    def test_valid_synthetic_tree_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            plugin_dir = _make_plugin_tree(Path(tmp), "salesforce-code-quality")
            evidence = self.mod.verify(plugin_dir)
            self.assertGreater(evidence["files"], 0)

    def test_plugin_json_name_mismatch_fails_closed(self):
        # plugin.json identity guard: the manifest name must equal the directory
        # basename before the tree is published under that identity.
        with tempfile.TemporaryDirectory() as tmp:
            plugin_dir = _make_plugin_tree(Path(tmp), "salesforce-code-quality")
            manifest = plugin_dir / ".claude-plugin" / "plugin.json"
            manifest.write_text(json.dumps({"name": "something-else"}), encoding="utf-8")
            with self.assertRaises(self.mod.ReleaseGateError):
                self.mod.verify(plugin_dir)

    def test_transient_directory_is_rejected(self):
        # A stray __pycache__ (or .sf/.pytest_cache) must never be copied verbatim
        # into the public repo.
        with tempfile.TemporaryDirectory() as tmp:
            plugin_dir = _make_plugin_tree(Path(tmp), "salesforce-code-quality")
            (plugin_dir / "__pycache__").mkdir()
            (plugin_dir / "__pycache__" / "junk.pyc").write_text("x", encoding="utf-8")
            with self.assertRaises(self.mod.ReleaseGateError):
                self.mod.verify(plugin_dir)

    def test_symlink_is_rejected(self):
        # Only regular files and directories are publishable; a symlink (or any
        # special file) fails closed rather than being followed.
        with tempfile.TemporaryDirectory() as tmp:
            plugin_dir = _make_plugin_tree(Path(tmp), "salesforce-code-quality")
            link = plugin_dir / "skills" / "dx-code-analyzer-run" / "evil-link"
            os.symlink(plugin_dir / ".claude-plugin" / "plugin.json", link)
            with self.assertRaises(self.mod.ReleaseGateError):
                self.mod.verify(plugin_dir)


if __name__ == "__main__":
    unittest.main()
