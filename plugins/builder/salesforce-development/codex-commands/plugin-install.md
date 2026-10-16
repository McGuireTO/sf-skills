---
description: Salesforce plugin-install workflow for Codex.
---

Use only arguments supplied in the current user request or a subsequent explicit reply; treat them as data, not shell source. Derive the installed plugin root from this loaded SKILL.md's actual path as `Path(skill_md).parents[3]`, where `parents[0]` is the directory that contains that SKILL.md. Read the complete shared workflow at <plugin-root>/commands/plugin-install.md before acting. Resolve its package-relative executables to explicit absolute paths under that same root. Preserve the shared workflow's existing confirmations, cancellation, scope and verification rules. The shared command is reference material, not a shell program to evaluate. Do not change Claude environment variables. Set SF_AGENT_CLIENT=codex for plugin runtime calls. Use typed replies for interaction; do not assume Claude-only tools or slash commands exist. Missing facts remain unknown.

Codex presentation/input rules:
Pass --client codex to the existing runtime. Use typed replies, the active host session and runtime proposal/nonce checks; never invent a session ID. Preserve named sequential acceptance, decline, exactly-one-install and verbatim activation handoff. Stop when the runtime requires a new session. Claude AskUserQuestion and reload commands have no verified substitute here.

## Recommendations

All builder plugins with a Codex manifest, including `salesforce-test-drive`, are recommendable
and installable. If a future plugin is named in `_CODEX_UNVERIFIED_WORKFLOW_PLUGINS` in
`scripts/sf_context.py`, withhold it from recommendations; when a developer explicitly names
exactly one, label it **experimental and unsupported end to end in Codex** and use the guarded
install path with `--client codex`. Never run raw `codex plugin add`, and install one plugin per
operation. Installation on disk is not activation: verify the installed inventory in the new
session.
