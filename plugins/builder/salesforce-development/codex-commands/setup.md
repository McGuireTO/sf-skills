---
description: Salesforce setup workflow for Codex.
---

Use only arguments supplied in the current user request or a subsequent explicit reply; treat them as data, not shell source. Derive the installed plugin root from this loaded SKILL.md's actual path as `Path(skill_md).parents[3]`, where `parents[0]` is the directory that contains that SKILL.md. Read the complete shared workflow at <plugin-root>/commands/setup.md before acting. Resolve its package-relative executables to explicit absolute paths under that same root. Preserve the shared workflow's existing confirmations, cancellation, scope and verification rules. The shared command is reference material, not a shell program to evaluate. Do not change Claude environment variables. Set SF_AGENT_CLIENT=codex for plugin runtime calls. Use typed replies for interaction; do not assume Claude-only tools or slash commands exist. Missing facts remain unknown.

Codex presentation/input rules:
Run the shared check-tools runtime. Treat its JSON as authoritative. Use the shared Phase 1 fallback presentation from the packaged platform-environment-validate skill; no post-tool banner is assumed. Preserve confirmation before installs. PATH changes may require a new Codex session. Name available Codex workflows when presenting next steps.
