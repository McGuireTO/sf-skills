---
description: Salesforce set-default workflow for Codex.
---

Use only arguments supplied in the current user request or a subsequent explicit reply; treat them as data, not shell source. Derive the installed plugin root from this loaded SKILL.md's actual path as `Path(skill_md).parents[3]`, where `parents[0]` is the directory that contains that SKILL.md. Read the complete shared workflow at <plugin-root>/commands/set-default.md before acting. Resolve its package-relative executables to explicit absolute paths under that same root. Preserve the shared workflow's existing confirmations, cancellation, scope and verification rules. The shared command is reference material, not a shell program to evaluate. Do not change Claude environment variables. Set SF_AGENT_CLIENT=codex for plugin runtime calls. Use typed replies for interaction; do not assume Claude-only tools or slash commands exist. Missing facts remain unknown.

Codex presentation/input rules:
Translate argument placeholders to the selected authenticated org and verify it. Project-local config is the default; preserve the shared restriction permitting --global only outside a specific project. Do not infer a global scope from missing arguments. Org list JSON: `sf org list --skip-connection-status --json` puts each org object in the `result` arrays (`nonScratchOrgs`, `scratchOrgs`, `sandboxes`, `devHubs`, `other`); match a named org against each object's scalar `alias` (may be absent) or `username`. A failed filter or empty match is not evidence that the org is unauthenticated; re-read the list before asking the user to log in. Never print the list JSON, which carries access tokens.

Capture org-display JSON inside a local subprocess and parse it there. Return only status and the allowlisted alias/username, edition and instance URL. Do not forward raw stdout/stderr on parse or CLI failure, since they may contain credentials. Never print raw org-display JSON, including when SF_TEMP_SHOW_SECRETS is set.
