# Codex host rules

Read by the Codex adapter (`codex-commands/start.md`) before `engine.md`. These rules replace only
the host-specific mechanics below and win over the engine text on Codex; everything else in the
engine applies as written: catalog-driven menu or direct launch, explicit org readiness, the
requirements gate, instrumentation, and no deployment unless the build step is reached and the user
has approved it.

Read `engine.md` in successive ranges until the last line and confirm you reached the end; long
tool output can be truncated.

## 1. Plugin requirements

Every required plugin that ships a Codex manifest is eligible for the guarded Salesforce
Development install flow in section 5. A recommendation or successful installation makes the
plugin available for a new session; it does not prove that every composite workflow in that plugin
is verified end to end. Apply the requirements gate normally once the drive is known. Do not hide a
drive from the menu merely because it names `agentforce-adlc`, `experience-cms`, or
`service-engagement`.

## 2. Roots and the companion

- `PLUGIN_ROOT` comes from the adapter. Codex installs each plugin to
  `<cache>/<marketplace>/<plugin>/<version>/`, so `<PLUGIN_ROOT>/../salesforce-development` is **not**
  the companion. Resolve `COMPANION_ROOT` as the version directory under
  `<PLUGIN_ROOT>/../../salesforce-development/` (or, in a repository checkout, the sibling
  `<PLUGIN_ROOT>/../salesforce-development`) that holds both `scripts/sf-context` and
  `.codex-plugin/plugin.json`; if several versions qualify, take the highest `version`.
  Everywhere the engine writes `<PLUGIN_ROOT>/../salesforce-development`, use `COMPANION_ROOT`.
- For any other plugin id, Step 4's presence probe checks the sibling
  `<PLUGIN_ROOT>/../<id>/.codex-plugin/plugin.json` first, then each version directory under
  `<PLUGIN_ROOT>/../../<id>/` for `.codex-plugin/plugin.json`, in place of the engine's
  `.claude-plugin/plugin.json` path.
- Run every companion script with `SF_AGENT_CLIENT=codex` (for example
  `SF_AGENT_CLIENT=codex "<COMPANION_ROOT>/scripts/sf-context" check-tools`).
- Companion not installed: replace the engine's `/plugin …` lines with
  `codex plugin add salesforce-development@salesforce --json`, then tell the user to start a new
  Codex session and re-run the Test Drive start workflow.
- Companion installed but with no `.codex-plugin/plugin.json`: its installed version has no Codex
  lifecycle support. Say so and stop; do not suggest reinstalling.
- Wherever the engine tells the user to re-run `/salesforce-test-drive:start` or restart Claude
  Code, say instead: start a new Codex session and ask it to run the Test Drive start workflow
  (with the drive id, if one was chosen).

## 3. Interaction and tools

- No `AskUserQuestion`, `Skill` or `Task` tool is assumed. Present the Step 3 menu as a numbered
  list with a final `Not now — exit`, and always stop for the typed reply, even for a one-entry
  catalog. Never auto-select.
- A skill counts as invocable (`COMPANION_SKILLS_INVOCABLE`, `PLUGIN_SKILLS_INVOCABLE[…]`) only if
  it appears in this session's skill inventory; do not probe by calling it. When not invocable,
  use the engine's script fallbacks (Step 0.5's `check-tools`) or the "state the requirement and
  let the user confirm" path.

## 4. Org readiness and deploys

- Menu mode with no default org: after the user picks a drive and before Step 4, run Step 2 for that
  drive's `provisioningTier` (Tier 3 signup, connect and set the default org, verify it with
  `sf org display`), then continue to Step 4. Step 4 assumes an authenticated org.
- The engine's default-org handling (`sf org display`, `sf config set target-org … --global`) is
  unchanged and is what CLI calls use. The Salesforce Development MCP servers do **not** read a
  global default: they need `SF_TARGET_ORG` / `SFDX_TARGET_ORG` in their environment or the DX
  project's own `target-org`. Tell the user this once after the org is settled; CLI and packaged
  fallbacks remain available without it.
- Never confirm anything for the user. A production deploy proceeds only on the user's own whole
  reply `confirm production deploy to <alias>`. That gate is enforced by the companion's Codex
  hooks, so it applies when those hooks are trusted and enabled (`/hooks`). Where Step 5 narrates
  the deploy-pause heads-up, say that reply is what unblocks it, in place of "one-time safety
  confirmation".

## 5. Plugin install and activation

- For every required plugin, Step 4's install surface is
  `SF_AGENT_CLIENT=codex "<COMPANION_ROOT>/scripts/sf-context" plugin-install <pluginId> --client codex`.
  Pass exactly `--client codex`; never pass `--session-id` or another `--client`. Relay the
  runtime's proposal and nonce verbatim, accept only the user's own typed confirmation, and install
  exactly one plugin.
- `/reload-plugins` does not exist: after an install, the user starts a new Codex session and
  resubmits the Test Drive request.
- This replaces Step 4 point 4's reload handoff in full, for a plugin just installed and for one
  already on disk but not in this session's skill inventory. Stop and say exactly: "`<pluginId>` is
  installed. Start a new Codex session, then ask it to resume test drive `<driveId>`." Never mention
  `/reload-plugins`, `/salesforce-test-drive:start` or a Claude Code restart on Codex, and do not
  continue into Step 5 in the same session.

## 6. Resume marker

The marker calls are the engine's, with `SF_AGENT_CLIENT=codex` and `COMPANION_ROOT`:
`… test-drive-mark start <driveId>` at launch and `… test-drive-mark done` at handoff. They only
run when a drive actually launches. The marker is shared per project across hosts. On Codex the companion's resume nudge asks the
user to "ask Codex to resume test drive <id>" and to start a new session if that is not
recognized; when the user says that, run the Test Drive start workflow with that drive id.

## 7. Instrumentation

`--instrument` is unchanged: the model keeps the session log, counters and redaction. Codex hook
payloads carry no skill-activation signal and shell post-hooks no exit status, so counts come
from the model's own record of its calls, not from host telemetry.
