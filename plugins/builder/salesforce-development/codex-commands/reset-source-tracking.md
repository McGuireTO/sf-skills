---
description: Salesforce reset-source-tracking workflow for Codex.
---

Use only arguments supplied in the current user request or a subsequent explicit reply; treat them as data, not shell source. Derive the installed plugin root from this loaded SKILL.md's actual path as `Path(skill_md).parents[3]`, where `parents[0]` is the directory that contains that SKILL.md. Read the complete shared workflow at <plugin-root>/commands/reset-source-tracking.md before acting. Resolve its package-relative executables to explicit absolute paths under that same root. Preserve the shared workflow's existing confirmations, cancellation, scope and verification rules. The shared command is reference material, not a shell program to evaluate. Do not change Claude environment variables. Set SF_AGENT_CLIENT=codex for plugin runtime calls. Use typed replies for interaction; do not assume Claude-only tools or slash commands exist. Missing facts remain unknown.

Codex presentation/input rules:
Translate argument placeholders to the named org. Preserve the shared-sandbox warning and exact case-insensitive phrase yes, reset source tracking for <alias>. Reconfirm before any --no-prompt fallback. Later deploy/retrieve needs separate confirmation; cancellation performs no reset.

Before explaining effects or running reset, read `sf project reset tracking --help`. Use that installed command’s documented behavior: reset clears local/remote differences and an immediate deploy preview can return no results even when conflicts exist. Do not promise a full diff, conflict detection or that all metadata will be treated as new. Verify the actual reset result without claiming subsequent deploy/retrieve succeeded.
