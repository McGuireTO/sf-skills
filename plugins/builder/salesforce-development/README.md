# salesforce-development

**AI-powered Salesforce platform development in Claude Code**

The foundation plugin for building apps and agents on the Salesforce Platform. When you open Claude Code in a Salesforce DX project, this plugin auto-detects your environment, injects org context, and provides AI assistance through validated skills, the Salesforce CLI, and Salesforce hosted MCP servers. The plugin uses this three-tier capability resolution: Skills (primary) → Salesforce CLI (secondary) → Salesforce MCP (last resort). Simply use natural language to describe what you want to build — no need to memorize any slash commands.

## Quick Start

This quick start describes the required software you must install, how to authorize your Salesforce org, and how to install this plugin from Anthropic's official Claude Code plugin marketplace.

1. **Install prerequisites:**
   - [Claude Code](https://claude.ai/code) — requires Claude Code 2.1.222 or later
   - [Node.js LTS](https://nodejs.org). The bundled language servers run under `node`.
   - [Salesforce CLI](https://developer.salesforce.com/tools/salesforcecli). The MCP host and deploy hooks shell out to `sf`.
   - Python 3.8+. The org-detection, deploy-safety, and agent-validation hooks use Python under the hood.

2. Authorize your Salesforce org. From a terminal or command window, use the `org login web` Salesforce CLI command which opens a browser where you log into your org with your authentication credentials:
   ```bash
   sf org login web --alias my-org --set-default
   ```

3. In Claude Code, install the plugin from the official `claude-plugins-official` marketplace (pre-registered, no `marketplace add` needed):
   ```text
   /plugin install salesforce-development@claude-plugins-official
   ```
   Alternatively, install from the Salesforce-hosted marketplace:
   ```text
   /plugin marketplace add forcedotcom/sf-skills
   /plugin install salesforce-development@salesforce
   ```

4. (Optional) Validate your environment:
   ```text
   /salesforce-development:setup
   ```

You're all set. Open a Salesforce DX project and start describing what you need.

## Example Prompts

Once you're all set up, use natural language to describe what you want to do; there's no need to memorize any slash commands:

- "Create an Apex service class to handle Account territory assignments."
- "Generate a custom object `Project__c` with fields for Name, Status, Due Date, and Owner."
- "Deploy the current changes to my sandbox."
- "Write test class for AccountTerritoryService and run it."
- "Validate a deployment to production."
- "Build a permission set that grants read access to Accounts and Contacts."
- “What can I do here?”

## Verify, Update, and Uninstall the Plugin

- **Verify:** `/plugin` lists `salesforce-development`. `/salesforce-development:status` shows the org/project banner. `"${CLAUDE_PLUGIN_ROOT}"/bin/lsp-doctor` checks the bundled language-server host.
- **Update:** if you installed from `claude-plugins-official`, updates happen automatically; to update manually run `/plugin update salesforce-development@claude-plugins-official`. If you installed from the `salesforce` marketplace, run `/plugin marketplace update salesforce` then `/plugin update salesforce-development@salesforce`.
- **Uninstall:** `/plugin uninstall salesforce-development@claude-plugins-official` (or `@salesforce`, matching however you installed it). If you added the `salesforce` marketplace, also run `/plugin marketplace remove salesforce`.

## What's Included

### 37 Skills

| Area | Skills |
|------|--------|
| **Discovery** | `platform-capability-search` — Public-channel overview of 102 released and 40 foundation capabilities (29 overlap; 113 visible), domain drilldown, skill detail with hash provenance, compact machine index, pinned one-step enable guidance, and explicitly on-demand cached org-feature detection |
| **Environment** | `platform-environment-validate` — Prerequisite scan (Salesforce CLI, Code Analyzer, Node, NPM, Git, MCP, source tracking) with guided installation and update |
| **Project and org lifecycle** | `dx-project-create` — Scaffold a new Salesforce DX project from scratch (template → generate → relocate → auth → default → source tracking); `dx-org-manage` — Create scratch orgs, take org snapshots, open orgs in the browser |
| **Apex** | `platform-apex-generate`, `platform-apex-anonymous-run` (anonymous Apex + debug-log capture), `platform-apex-test-generate`, `platform-apex-test-run`, `platform-apex-logs-debug` |
| **Automation** | `automation-flow-generate` — Screen, Autolaunched, Record-Triggered, and Scheduled Flows |
| **Declarative metadata** | `platform-custom-object-generate`, `platform-custom-field-generate`, `platform-custom-metadata-type-generate`, `platform-custom-setting-generate`, `platform-custom-application-generate`, `platform-custom-tab-generate`, `platform-custom-report-type-generate`, `platform-list-view-generate`, `platform-value-set-generate`, `platform-validation-rule-generate`, `platform-flexipage-generate`, `platform-lightning-app-coordinate` |
| **Data and API context** | `platform-data-manage` — Create, update, delete, import, export, seed, and clean up org records; `platform-soql-query` — SOQL/SOSL authoring, optimization, and query-plan analysis; `platform-data-and-tooling-api-context-get` — Standard-object and Tooling API field/schema reference |
| **Deploy and retrieve** | `platform-metadata-deploy`, `platform-metadata-retrieve`, `platform-manifest-generate` (build `package.xml` / `destructiveChanges.xml`), `platform-metadata-api-context-get`, `platform-deploy-validate`, `platform-quick-deploy`, `platform-destructive-deploy` |
| **Security** | `platform-permission-set-generate`, `platform-sharing-owd-configure`, `platform-sharing-rules-generate` |
| **Reporting** | `platform-report-generate` |
| **LSP** | `platform-lsp-integrate` — Contract and fallbacks for the bundled language-server tools |

### What Else Is in the Box

- **Agents** — `salesforce-dev`, the primary Salesforce development agent (activates automatically in Salesforce projects — `sfdx-project.json` present — and routes requests skills-first, then SF CLI, then direct API as a last resort). Code-analysis and Well-Architected review — the `dx-code-analyzer-*` skills, `platform-architecture-analyze`, and the read-only `architecture-review` agent — now live in the separate **salesforce-code-quality** plugin.
- **Slash commands** — `/salesforce-development:discover` (computed public-channel capability overview/drilldown, `plugins <text>` for on-demand uninstalled-plugin matching, and optional on-demand `features [--target-org <alias>] [--refresh] [--json]`), `:plugin-install` (one-confirmation install for a trusted same-session marketplace recommendation; source confirmation for anything else), `:plugin-recommendations` (view or change how readily uninstalled plugins get proposed), `:telemetry`, `:setup`, `:status`, `:org`, `:login`, `:logout`, `:set-default`, `:project`, `:reset-source-tracking`, `:welcome`, `:feedback` (manual-only — see [Feedback](#-feedback) below).
- **MCP servers** — `salesforce-api-context` and `salesforce-metadata-experts` (API/metadata guidance), and `salesforce-lsp`, a local host that lazily spawns the **Apex** and **SOQL** language servers and exposes their semantic capabilities as MCP tools. See the `platform-lsp-integrate` skill for the tool contract.
- **Hooks** — org-context detection on session start; a production deploy-safety gate and an Apex pre-deploy diagnostics gate on `sf project deploy`; and skills-first advisories that, when no installed skill matches, also propose an uninstalled plugin whose curated description does.

Your progress through **Connect → Project → Build → Test → Deploy → Observe** is tracked from real, successful actions in your project — never assumed. Run `/salesforce-development:discover journey inspect` to review it, or `journey reset` to clear it.

## 💬 Feedback

Run `/salesforce-development:feedback` any time to tell us how things are going. It's a manual-only
command (it never shows up in the model's own suggestions) that asks a single 1-5 satisfaction
question right in chat and records it as a local telemetry event — the only thing that leaves your
machine is that numeric rating, tagged the same coarse way as every other telemetry event.

## More Information

- **[Configuration reference](./docs/configuration.md)** — ambient UI modes and deploy/delete guard rails.
- **[Changelog](https://github.com/forcedotcom/sf-skills/blob/main/plugins/builder/salesforce-development/CHANGELOG.md)** — what's new in each release.
- To skip Claude Code's permission prompts for the CLI commands this plugin runs (`sf`, `node`, `npm`, read-only `git`), add the equivalent allow-rules to your DX project's `.claude/settings.json`. See [Settings](https://code.claude.com/docs/en/settings#permission-settings) in the Claude Code docs. This plugin doesn't ship a `settings.json` of its own.
- Third-party code bundled with this plugin (such as the vendored Apex language server and a few esbuild-bundled MCP dependencies) is attributed in [`NOTICE`](./NOTICE).

## Codex lifecycle support

### Install, enable and uninstall

Register a local checkout with `codex plugin marketplace add <repository-checkout> --json`, then
install with `codex plugin add salesforce-development@salesforce --json`; repeating that add
command refreshes the installed files. Enable or disable the plugin through the Codex setting
`plugins."salesforce-development@salesforce".enabled`, and uninstall with
`codex plugin remove salesforce-development@salesforce --json`. Start a new Codex session after
any of these changes. The package declares its Codex hooks separately from the Claude manifest;
review and trust them through Codex `/hooks` before relying on their safety checks.

Every builder plugin carries a `.codex-plugin/plugin.json`, so Codex can recommend it and install
it through the guarded Salesforce Development flow (never a raw
`codex plugin add`: the guarded flow keeps the source/trust check, installs one named plugin at a
time, and requires a new Codex session). This includes `salesforce-test-drive`, whose native
Codex adapter supports recommendation and guarded installation. Claude-only hooks and agents in
those plugins (for example the `agentforce-adlc` guardrails and validator hooks) are not carried
over to Codex. Installation and a native Codex surface are not evidence that every end-to-end
workflow is verified in Codex; temporarily withhold a host-incompatible plugin by adding it to
`_CODEX_UNVERIFIED_WORKFLOW_PLUGINS` in `scripts/sf_context.py`.

### Invoking commands on Codex

Codex does not support `/plugin:command` slash commands. It converts each command in a plugin's
`codex-commands/` into a skill when the plugin is installed, so ask for the workflow in plain
language (for example, "run the Salesforce Development status workflow") or pick it from the `$`
skill list. This needs a Codex build that includes command migration (0.145.0 or later), and
a plugin installed or updated after that build. Messages the plugin generates on Codex use this
wording instead of `/salesforce-development:<name>`.

### Environment variables

| Variable | Effect |
|---|---|
| `SF_TARGET_ORG` / `SFDX_TARGET_ORG` | The org the MCP servers and the deploy gate use. When both are set they must agree. Unset, the MCP launcher uses the project's own `.sf/config.json` `target-org` (or `.sfdx/sfdx-config.json` `defaultusername`) (`.sf/config.json` wins when both name an org) and refuses to start when there is none; run `sf config set target-org <alias>` in the project or set the variable in the MCP server's environment. |
| `SF_PLUGIN_UI_MODE` | `full`, `plain` or `off`; selects the presentation mode ahead of the other settings. Safety and routing guidance stay active when it is `off`. |
| `SF_AGENT_CLIENT` | Set to `codex` on plugin runtime commands run from the shell (for example `scripts/sf-context feedback-record <1-5>`) so they use the Codex session identity. |
| `SFDX_FEEDBACK` | `1` enables the end-of-turn numeric feedback nudge; it never asks for typed comments. |

### Behavior and known limits

- SessionStart shows a local-only banner (project facts and the configured org alias, no org, git
  or MCP probe); ask for Salesforce status for live details. A resumed session reuses its banner.
- The shell hook verifies the target org and applies the production and destructive-deployment
  checks. Run one literal deploy/delete per shell call, from the session's working directory,
  without inline `cd`, `export`, `env`, variable assignments or `sf config set`. A deploy or
  delete run through `eval`, `source`, a nested shell, command or process substitution, a
  here-string, `xargs`, `find -exec`, `env -S`, an interpreter's `-c`/`-e` code or a variable
  in command position is denied; `npx sf` and one-shot wrappers such as `stdbuf` are read through to the
  CLI call. Any other command that looks like a deploy or delete but has no literal `sf` call
  (an unlisted wrapper, or an `echo`/`grep`/heredoc that only mentions one) is denied too, as is a
  deploy or delete inside a loop, function body or `watch`. A script
  written earlier and then run is not inspected. Non-production destructive
  deploys are advised, not blocked.
- A production deploy proceeds only after your whole reply is
  `confirm production deploy to <alias>` (optionally starting with `yes,`). The confirmation covers one deploy to that org in the
  current session and expires after ten minutes. It names the org (matched exactly, including case), not the command, and a deploy
  to another org (including a sandbox alias you confirmed) or one denied by a later check does not
  use it up. A `--dry-run` deploy to
  production counts as a production deploy. Inline override markers in the command are ignored.
- Shell post-hooks carry no exit status, so the adapter records no shell success, deploy/test
  journey evidence or skill invocation. Telemetry records no skill events. SessionEnd hands
  buffers to the detached sender; an interrupted shutdown can leave a buffer for a later session
  to recover.
- Hook callbacks run `python3` and the bash deploy gate, so they need a POSIX host. If the hook itself fails, a shell command that could deploy or delete is denied and other tool
  calls proceed with a warning. Callback startup failures and host timeouts are outside the adapter's
  fail-closed guarantee. Remote API-context and metadata MCP servers need
  credential access inside the host sandbox; CLI and packaged context-file fallbacks remain.
- Codex command adapters reference the packaged shared workflows. The feedback command surface
  does not collect a rating. Login checks installed CLI support before offering device-code
  login. Login, logout, defaults and source-tracking reset keep their confirmation and
  cancellation steps.

### Changes visible in Claude Code

- `/salesforce-development:discover` and the `platform-capability-search` skill name the
  `--client codex` form of the discovery command.
- The deploy gate reads the target org with the same parser as its command check (a mid-word `#`
  is not a comment, heredoc bodies are read, and an unreadable target flag is denied). It checks
  every deploy or delete in the command, and denies one that spans more than one org. The
  production override counts only as a leading `CONFIRM_PROD=1` on each deploy command itself or
  its `--I-CONFIRM-PROD` argument. The default org honors `SF_TARGET_ORG` / `SFDX_TARGET_ORG`.
- `SF_PLUGIN_UI_MODE` selects the presentation mode ahead of the other settings.
