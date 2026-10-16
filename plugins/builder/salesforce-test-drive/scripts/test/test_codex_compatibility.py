#!/usr/bin/env python3
"""Contract tests for the Codex projection of salesforce-test-drive.

Offline and static: they pin the manifest, the command adapter and the host rules against the
unchanged Claude contract. They do not start Codex, call a model or touch an org.
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def flat(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def builder_root() -> Path:
    return ROOT.parent


def load(path: str) -> dict:
    return json.loads(read(path))


ENGINE = flat(read("references/engine.md"))
HOST = flat(read("references/codex-host.md"))
ADAPTER = read("codex-commands/start.md")
CATALOG = load("catalog/test-drives.json")


class ManifestTests(unittest.TestCase):
    def test_codex_manifest_matches_claude_identity(self):
        codex, claude = load(".codex-plugin/plugin.json"), load(".claude-plugin/plugin.json")
        for key in ("name", "version", "license", "homepage", "repository"):
            self.assertEqual(claude[key], codex[key], key)

    def test_codex_manifest_only_selects_command_adapters(self):
        codex = load(".codex-plugin/plugin.json")
        self.assertEqual("./codex-commands/", codex["commands"])
        for key in ("hooks", "mcpServers", "skills"):
            self.assertNotIn(key, codex)

    def test_claude_surface_is_unchanged(self):
        claude = load(".claude-plugin/plugin.json")
        self.assertEqual("./commands/", claude["commands"])
        self.assertEqual(["salesforce-development"], claude["dependencies"])
        self.assertFalse((ROOT / "hooks").exists(), "Claude would auto-load a hooks directory")
        self.assertEqual(["start.md"], sorted(p.name for p in (ROOT / "commands").iterdir()))
        command = read("commands/start.md")
        self.assertIn("${CLAUDE_PLUGIN_ROOT}", command)
        self.assertIn("AskUserQuestion", command)


class AdapterTests(unittest.TestCase):
    def test_single_adapter_for_the_single_command(self):
        self.assertEqual(["start.md"], sorted(p.name for p in (ROOT / "codex-commands").iterdir()))

    def test_adapter_stays_small(self):
        # Keeps the always-loaded adapter small; the detail lives in references/.
        self.assertLess(len(ADAPTER.encode("utf-8")), 2500)

    def test_adapter_is_codex_clean(self):
        for forbidden in ("$ARGUMENTS", "CLAUDE_PLUGIN_ROOT", "AskUserQuestion", "allowed-tools"):
            self.assertNotIn(forbidden, ADAPTER)

    def test_adapter_plugin_root_derivation_matches_the_real_layout(self):
        # The adapter derives the plugin root as Path(<SKILL.md>).parents[3] from the
        # command file's installed path: <root>/codex-commands/start.md projected as a
        # skill resolves three levels up from the SKILL.md. Pin the layout it depends on.
        self.assertEqual(ROOT, (ROOT / "codex-commands" / "start.md").parents[1])
        for rel in ("references/codex-host.md", "references/engine.md"):
            self.assertTrue((ROOT / rel).is_file(), rel)

    def test_adapter_delegates_to_shared_engine_and_host_rules(self):
        self.assertIn("parents[3]", ADAPTER)
        self.assertLess(ADAPTER.index("references/codex-host.md"), ADAPTER.index("references/engine.md"))
        self.assertIn("SF_AGENT_CLIENT=codex", ADAPTER)
        self.assertIn("--instrument", ADAPTER)


class HostRulesTests(unittest.TestCase):
    def test_preserved_contract_surfaces_still_exist_in_the_engine(self):
        for needle in (
            "test-drive-mark start <driveId>", "test-drive-mark done",
            "SELECTED_DRIVE", "Not now — exit", "plugin-install", "COMPANION_SKILLS_INVOCABLE",
            "never confirm on their behalf",
        ):
            self.assertIn(needle, ENGINE, needle)

    def test_host_rules_cover_every_codex_lifecycle_gap(self):
        for needle in (
            "<PLUGIN_ROOT>/../../salesforce-development", ".codex-plugin/plugin.json",
            "SF_AGENT_CLIENT=codex", "--client codex", "test-drive-mark start", "test-drive-mark done",
            "numbered", "Not now — exit", "codex plugin add salesforce-development@salesforce --json",
            "new Codex session", "SF_TARGET_ORG", "confirm production deploy to <alias>",
            "--instrument",
        ):
            self.assertIn(needle, HOST, needle)

    def test_host_rules_do_not_imply_deployment_or_user_consent(self):
        self.assertIn("Never confirm anything for the user", HOST)
        self.assertIn("no deployment unless", HOST)

    def test_claude_reload_and_install_commands_are_replaced_not_instructed(self):
        self.assertIn("`/reload-plugins` does not exist", HOST)
        self.assertIn("replace the engine's `/plugin …` lines", HOST)
        self.assertNotIn("run `/reload-plugins`", HOST)

    def test_resume_nudge_is_host_worded_not_a_known_limitation(self):
        self.assertIn("resume test drive <id>", HOST)
        self.assertNotIn("Known limitation", HOST)

    def test_post_install_handoff_overrides_engine_reload_step(self):
        self.assertIn("replaces Step 4 point 4's reload handoff in full", HOST)
        self.assertIn("is installed. Start a new Codex session, then ask it to resume test drive", HOST)
        self.assertIn("Never mention `/reload-plugins`, `/salesforce-test-drive:start` or a Claude Code restart", HOST)

    def test_install_command_is_not_improvised(self):
        self.assertIn("never pass `--session-id` or another `--client`", HOST)

    def test_every_required_plugin_has_a_codex_manifest(self):
        # A drive may only require plugins that Salesforce Development can install on Codex.
        builder = ROOT.parent
        for drive in CATALOG["testDrives"]:
            for plugin in drive["requires"].get("plugins", []):
                with self.subTest(drive=drive["id"], plugin=plugin):
                    self.assertTrue((builder / plugin / ".codex-plugin" / "plugin.json").is_file())

    def test_test_drive_is_not_withheld_from_codex_recommendations(self):
        sf_context = (builder_root() / "salesforce-development/scripts/sf_context.py").read_text(encoding="utf-8")
        self.assertRegex(sf_context, r"_CODEX_UNVERIFIED_WORKFLOW_PLUGINS: frozenset = frozenset\(\)")

    def test_generic_install_rule_for_other_plugins(self):
        self.assertIn("plugin-install <pluginId> --client codex", HOST)
        self.assertIn("Every required plugin", HOST)

    def test_no_org_menu_pick_provisions_before_the_requirements_gate(self):
        i = HOST.index("Menu mode with no default org")
        rule = HOST[i:i + 400]
        self.assertLess(rule.index("run Step 2"), rule.index("continue to Step 4"))
        self.assertLess(rule.index("sf org display"), rule.index("continue to Step 4"))

    def test_companion_without_codex_manifest_does_not_loop(self):
        self.assertIn("do not suggest reinstalling", HOST)


class CatalogTests(unittest.TestCase):
    def test_every_prompt_exists_and_ids_are_unique(self):
        ids = [d["id"] for d in CATALOG["testDrives"]]
        self.assertEqual(len(ids), len(set(ids)))
        for drive in CATALOG["testDrives"]:
            self.assertTrue((ROOT / "prompts" / drive["promptPath"]).is_file(), drive["id"])


if __name__ == "__main__":
    unittest.main()
