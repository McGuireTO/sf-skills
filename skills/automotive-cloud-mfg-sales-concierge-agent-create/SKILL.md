---
name: automotive-cloud-mfg-sales-concierge-agent-create
description: "Create and activate the Industries Sales Concierge agent from the pre-installed NextGen Authoring (NGA) template in a live org — entirely headless and API-first, driven only through the Headless 360 MCP server's dispatch tool. This is \"Act 1\" (Create & Activate the Agent) of the Industries Sales Concierge steel thread. It resolves the IndustriesSalesConcierge NGA template script, creates an NGA bundle from it, publishes the bundle (materializing the BotDefinition + BotVersion), activates the bundle version, and verifies the runtime BotVersion reached Active status. TRIGGER when the user wants to \"create the Industries Sales Concierge agent\", \"deploy the manufacturing agent\", \"activate the industries sales concierge agent\", \"create the Industries Sales Concierge agent\", or otherwise asks to stand up the agent from the NGA template. DO NOT TRIGGER when the user wants to enable org preferences or assign permission sets (that's Act 0), create business data, run Data Pipelines jobs, or configure messaging channels — those are separate Acts served by other skills."
metadata:
  version: "1.0"
---

# Create & Activate Industries Sales Concierge Agent (Act 1)

Create the **Industries Sales Concierge** agent from the pre-installed **NextGen Authoring (NGA)**
template, publish and **activate** the agent — directly in a live org, **headlessly and API-first,
using only the Headless 360 MCP server's `dispatch` tool**.

This is **Act 1 — "Create & Activate the Agent"** of the Industries Sales Concierge steel thread.
It runs **after Act 0** (Enable the Foundation) has completed successfully — Act 0 turns on the
Agentforce platform prerequisites and Manufacturing Cloud org preferences that this Act depends on.

The NGA template `IndSalesConcierge__IndustriesSalesConcierge` (type: `AgentforceEmployeeAgent`)
ships with the Manufacturing Cloud package. It contains the full agent definition in afscript
format — the router, topics, and the **IndustriesSalesConcierge** subagent with its actions
pre-configured. The template is resolved by name, then the script is used to create an NGA bundle
which is published and activated through the **native NextGen Authoring Connect API**.

---

## The command surface — `dispatch` ONLY (no sf CLI, no curl, no browser)

Every call this skill makes is a single MCP tool call:

```text
dispatch(method, path, body?, query_params?)
```

- The MCP server resolves the org, instance URL, and bearer token on its own. **Do not** ask for or
  handle tokens, instance URLs, org IDs, or API versions as inputs — `dispatch` supplies them.
- Use the API version resolved by the orchestrator's preflight (passed down as shared runtime context).

> **Absolute rules (inherited from the Headless 360 factory):**
> - **`sf` CLI must NEVER appear as a step here.** Hosted-MCP customers have no shell.
> - **No browser / no manual Setup click.** Every step in this Act is fully headless.

---

## Prerequisites (verified by the orchestrator before invoking this Act)

This Act assumes the orchestrator has already:
1. Resolved the shared runtime (org, userId, apiVersion) in its preflight.
2. Completed Act 0 successfully — specifically:
   - `EinsteinGPTPlatformEnabled` = true (pref #1)
   - `AgentPlatformEnabled` = true (pref #2)
   - `EinsteinGPTCopilotEnabled` = true (pref #3, or reported as license-level gap)
   - `IndManufacturingEnabled` = true (pref #4)
   - `MfgAgentsEnabled` = true (pref #5)
   - `ManufacturingGenAIPref` = true (the UI-only pref — gated on legal consent)
   - Foundation permission sets assigned (including Agentforce Default Agent access)
3. NextGen Authoring is provisioned in the org (NGA license active).

If any Agentforce platform prerequisite is missing, this Act will fail. The orchestrator gates on
Act 0 success before invoking Act 1.

---

## Scope — AGENT CREATION & ACTIVATION ONLY (NextGen Authoring path)

- **In scope**
  - Probing NGA enablement (the `/nextgen-authoring/bundles` endpoint must return 200).
  - Resolving the `IndSalesConcierge__IndustriesSalesConcierge` template's `agentScript` via the
    agent-authoring catalog (`get-agent-templates`).
  - Checking name idempotency (is a bundle with this name already created?).
  - Creating an NGA bundle + draft version from the resolved script.
  - Publishing the bundle version (materializes BotDefinition + BotVersion).
  - Activating the bundle version (promotes BotVersion to Active).
  - Verifying the runtime `BotVersion.Status == "Active"`.

- **Out of scope** (delegate — do NOT attempt here)
  - Enabling org preferences or assigning permission sets (Act 0).
  - Creating business data (accounts, products, opportunities, etc.).
  - Configuring messaging channels, Experience Cloud sites, or deployment surfaces.
  - Running Data Pipelines jobs.
  - Modifying the agent's topics, actions, or instructions post-creation (the template is complete).
  - Using the legacy Copilot Builder `createCopilotFromTemplate` path (that is NOT NextGen Authoring).

---

## Required Inputs

All provided by the orchestrator's shared runtime context:

- **`<apiVersion>`** — the org's max API version (from orchestrator preflight step 1). NGA requires v64+.
- **`<userId>`** — the authenticated user's Id (from orchestrator preflight).

Template name is fixed: **`IndSalesConcierge__IndustriesSalesConcierge`** (the fully-qualified NGA
template name).

---

## The template's actions are resolved at runtime

Unlike a hand-maintained action list, the `IndustriesSalesConcierge` agent template's actions
(flows, standard invocable actions, prompt-response actions) live inside the `.agent` afscript
resolved in Step 3 — they are **not** enumerated here. Do not hardcode an expected action set for
this Act; the template script is the single source of truth for what the agent can do, and it may
evolve independently of this skill. After activation, the verify step confirms the agent reached
Active status — it does not (and should not) assert on the specific action inventory.

---

## Workflow — NextGen Authoring: resolve → create → publish → activate → verify

Follow in order. Report progress per step.

### Step 1. Resolve API version

```text
dispatch("GET", "/services/data/")
```

Take `max(versions[].version)` → `{v}`. NGA requires v64 floor; use the org's newest version.

### Step 2. Probe NGA enablement

```text
dispatch("GET", "/services/data/v<apiVersion>/nextgen-authoring/bundles")
```

- **200** = NGA is live and the user has read access. Proceed.
- **403** = NGA is NOT provisioned or the user lacks `userCanAccessAuthoringBundle`. **STOP.**
  Report that NextGen Authoring is not enabled in this org; this is a blocker.

This also lists any already-created bundles — check if `IndustriesSalesConcierge` already exists.

### Step 3. Resolve template script (the one off-native step)

The native NextGen Authoring API has no template catalog. Template name → agentScript resolution
goes through the headless agent-authoring dispatch route:

```text
dispatch("GET", "/headless/invoke/platform/agent-authoring/get-agent-templates")
```

The dispatcher auto-resolves the route and returns the unwrapped response directly.

**Response:** array of template entries. Each has `{devName, namespace, name (FQN = namespace__devName),
agentType, agentScript, templateLabel, templateDescription, iconUrl, ...}`.

**Match logic:** find the entry where `name` is EXACTLY equal to
`IndSalesConcierge__IndustriesSalesConcierge` (strict equality — NOT `startsWith`, NOT `includes`,
NOT substring match). There may be multiple templates with similar prefixes; you MUST match on
exact string equality only. If exact FQN match yields no result, fall back to exact `devName` ==
`IndustriesSalesConcierge` (again, strict equality — not partial match).

**Capture:** the matching entry's `agentScript` (the full afscript — typically ~60KB+).

**If no template found:** STOP. Report that the `IndSalesConcierge__IndustriesSalesConcierge` NGA
template is not installed in this org. The Manufacturing Cloud package may not be deployed or the
`ManufacturingGenAIPref` preference is off.

### Step 4. Check name idempotency

Before creating, check if a bundle with this name already exists:

```text
dispatch("GET", "/services/data/v<apiVersion>/nextgen-authoring/bundles/names")
```

Check if `IndustriesSalesConcierge` (or whatever `apiName` you intend to use) is already taken.

**If already exists:** The agent was already created in a prior run. Query for its bundle version
and check its status — if already Active, report success and skip to verify. If in DRAFT state,
proceed to publish + activate.

### Step 5. Create NGA bundle from template script

**CRITICAL — rewrite `config.developer_name` and `config.agent_label` in the agentScript** to a
run-scoped unique value before creating. The collision key for `publish` is the script's internal
`developer_name`, NOT the bundle `apiName`. If a BotDefinition with the same `developer_name`
already exists, publish will fail with `400 DUPLICATE_VALUE`.

For the Industries Sales Concierge, use:
- `config.developer_name`: `IndustriesSalesConcierge` (or a run-scoped variant if re-running)
- `config.agent_label`: `Industries Sales Concierge`

**DO NOT change `config.agent_template`** — that is the template-lineage pointer and must stay as-is.

```text
dispatch("POST", "/services/data/v<apiVersion>/nextgen-authoring/bundles",
  body={
    "apiName": "IndustriesSalesConcierge",
    "label": "Industries Sales Concierge",
    "assets": [
      {
        "resourceName": "definition.agent",
        "resourceType": "agentDefinition",
        "resourceContent": "<the resolved agentScript from Step 3>",
        "resourceAuthoringFormat": "afscript",
        "authoringFormatVersion": "v1.0"
      }
    ]
  })
```

**Response:** `{bundleId, id (= bundleVersionId), apiName, label, versionStatus: "DRAFT", ...}`.

Capture **`bundleId`** and **`bundleVersionId`** (the `id` field). Thread these through remaining steps.

**Error handling:**
- Auth/permission errors → user lacks `userCanEditAuthoringBundle`. Report the exact error.
- 500 on large script → fallback: create-empty bundle then PATCH `updateBundleVersion` to attach
  the asset separately.

### Step 6. Publish the bundle version

```text
dispatch("POST", "/services/data/v<apiVersion>/nextgen-authoring/bundle-versions/<bundleVersionId>/publish")
```

**Response** carries:
- `publishedBotId` — the materialized BotDefinition Id
- `publishedBotVersionId` — the materialized BotVersion Id
- `versionStatus: "Published"`

Capture **`publishedBotId`** and **`publishedBotVersionId`** for verification.

**Error handling:**
- `400 DUPLICATE_VALUE: BotDefinition duplicates value on record with id: <developer_name>` →
  the script's `config.developer_name` collides with an existing BotDefinition. Either the agent
  already exists (check and proceed to activate the existing one) or use a unique developer_name.
- Permission errors → user lacks `userCanEditAuthoringBundle`.

### Step 7. Activate the bundle version

```text
dispatch("POST", "/services/data/v<apiVersion>/nextgen-authoring/bundle-versions/<bundleVersionId>/activate")
```

**Returns HTTP 204** (empty body). Activation is **async** — do NOT expect the status to flip
immediately.

**CRITICAL — activation is NOT blind-retry-safe.** A second activate POST while the first is still
in flight returns 500 UNKNOWN_EXCEPTION. On timeout, **read status back before retrying** — never
blind-retry.

### Step 8. Verify activation

Two-level verification:

**8a. Accepted-checkpoint (async activation queued):**

```text
dispatch("GET", "/services/data/v<apiVersion>/nextgen-authoring/bundle-versions/<bundleVersionId>")
```

Assert `targetStatus == "ACTIVE"`. This confirms the activation was accepted.
Note: `versionStatus` may still show `"PUBLISHED"` — that is normal (it does NOT update to ACTIVE
synchronously). Check `targetStatus`, not `versionStatus`.

**8b. Authoritative Active proof (runtime record):**

```text
dispatch("GET", "/services/data/v<apiVersion>/query",
  query_params={"q": "SELECT Id, Status FROM BotVersion WHERE Id = '<publishedBotVersionId>'"})
```

Assert `Status == "Active"`.

If not Active yet, wait 5-10 seconds and re-query (activation is async). Up to 3 retries with
increasing delays (5s, 10s, 15s).

---

## Findings — encode as invariants

1. **Enablement gate (step 2).** 403 on the read probe = NGA not provisioned → flag, don't retry.
2. **Name→script is the only off-native step and keys on the FQN.** Native NGA Connect has no
   template catalog. Match `templateName` against `namespace__devName`.
3. **Publish is a distinct step before activate.** create → publish → activate. Activating a
   DRAFT/unpublished version fails.
4. **Activation is async AND not blind-retry-safe.** Returns 204; a 2nd activate while the first
   is in flight returns 500. Read status back before retrying.
5. **Verify via the RUNTIME record, not authoring versionStatus.** Use `targetStatus == "ACTIVE"`
   for the accepted-checkpoint and runtime `BotVersion.Status == "Active"` for the hard pass.
6. **`validateAgentJson` is a known false-negative — do NOT gate publish on it.**
7. **Idempotency's collision key is the script's `config.developer_name`, NOT the bundle apiName.**
   `createBundleWithVersion` auto-suffixes a colliding apiName, but publish materializes a
   BotDefinition keyed on developer_name. On collision, publish fails with DUPLICATE_VALUE.
8. **The ~60KB+ script must round-trip inline.** There is no name→instantiate server API; create
   takes the full agentScript inline in the request body.

---

## Rules / Constraints

| Constraint | Rationale |
|---|---|
| `dispatch` only — no `sf` CLI, no `curl`, no browser | Hosted-MCP customers have no shell. |
| Use the **NextGen Authoring Connect API** (`/nextgen-authoring/...`) | This is the canonical NGA path; do NOT use the legacy Copilot Builder `createCopilotFromTemplate`. |
| Template is `IndSalesConcierge__IndustriesSalesConcierge` (FQN) | This is the NextGen template shipped in Core; NOT the legacy copilot template. |
| Publish BEFORE activate | Create → Publish → Activate is the mandatory sequence. |
| Never blind-retry activate | Activation is async; read status back before retrying. |
| No hardcoded IDs | Resolve bundleId, bundleVersionId, publishedBotId, publishedBotVersionId at runtime. |
| Do not modify the agent post-creation | The template afscript is the source of truth. |
| Do not delete the agent | Leave it in place for validation by the admin. |

---

## Output Expectations

Report, in order:
1. **NGA enablement** — confirmed NextGen Authoring is provisioned (step 2 returned 200).
2. **Template resolution** — the `IndSalesConcierge__IndustriesSalesConcierge` template's agentScript
   resolved successfully (size in chars).
3. **Bundle creation** — `bundleId`, `bundleVersionId`, `apiName`, `versionStatus: DRAFT`.
4. **Publish** — `publishedBotId`, `publishedBotVersionId`, `versionStatus: Published`.
5. **Activation** — activation accepted (204), `targetStatus: ACTIVE`.
6. **Verification** — runtime `BotVersion.Status == "Active"` confirmed.
7. **Summary** — the Industries Sales Concierge agent is live. Provide:
   - `bundleId`, `bundleVersionId` (NGA identifiers)
   - `publishedBotId` (BotDefinition Id / copilotId)
   - `publishedBotVersionId` (BotVersion Id)
   - `apiName` / `DeveloperName`
8. **Next step** — hand back to the orchestrator for the next Act.

---

## Troubleshooting

| Symptom | Cause | Resolution |
|---|---|---|
| Step 2 returns 403 | NGA not provisioned or user lacks NGA perms | Verify NGA license is provisioned and user has Agent Authoring permissions. |
| Template not found in `get-agent-templates` | Manufacturing Cloud package not deployed, or `ManufacturingGenAIPref` is off | Verify Act 0 completed; check the UI-only GenAI preference. |
| `createBundleWithVersion` 500 on large script | Intermittent server issue with large payloads | Fallback: create-empty then PATCH `updateBundleVersion` to attach asset. |
| Publish fails with `DUPLICATE_VALUE: BotDefinition duplicates value` | A BotDefinition with same `developer_name` already exists | Check existing agent; if Active, report success. If stale, use a unique developer_name. |
| Activate returns 500 UNKNOWN_EXCEPTION | Double-activate race condition | Read `getBundleVersion` status; if `targetStatus == "ACTIVE"`, the first activate succeeded. |
| `BotVersion.Status` not Active after activate 204 | Activation is async | Wait 5-15s and re-query. Up to 3 retries. |
| `validateAgentJson` reports errors on valid script | Known false-negative (YAML parser vs afscript) | Ignore validate failures; proceed to publish (the real compiler). |

---

## Cross-Skill Integration

This skill is **Act 1** and is designed to be invoked by the **MFG Sales Concierge Foundation
Orchestrator** (its parent) after Act 0 succeeds.

| Need | Belongs to |
|---|---|
| Enable org preferences + assign permission sets | Act 0 — `enable-mfg-sales-concierge-foundation` |
| Configure messaging channels / deployment surfaces | later Act — channel deployment |
| Create business data (accounts, products, opportunities) | later Act — data setup |
| Run Data Pipelines jobs | later Act — DPE enablement |

<!-- skill-validate: ignore-start -->
<!-- codey:operations start -->
## Operations Reference

Operations this skill uses — routing and dependency reference.

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `nga-01-resolve-api-version` | read | — | `GET /services/data/` | — |
| `nga-02-probe-nga-enabled` | validate | — | `GET /services/data/v{apiVersion}/nextgen-authoring/bundles` | `nga-01-resolve-api-version` |
| `nga-03-resolve-template-script` | read | — | `GET /headless/invoke/platform/agent-authoring/get-agent-templates` | `nga-02-probe-nga-enabled` |
| `nga-04-check-idempotency` | read | — | `GET /services/data/v{apiVersion}/nextgen-authoring/bundles` | `nga-03-resolve-template-script` |
| `nga-05-create-bundle-from-template` | write | — | `POST /services/data/v{apiVersion}/nextgen-authoring/bundles` | `nga-04-check-idempotency` |
| `nga-06-publish-bundle-version` | write | — | `POST /services/data/v{apiVersion}/nextgen-authoring/bundle-versions/{bundleVersionId}/publish` | `nga-05-create-bundle-from-template` |
| `nga-07-activate-bundle-version` | write | — | `POST /services/data/v{apiVersion}/nextgen-authoring/bundle-versions/{bundleVersionId}/activate` | `nga-06-publish-bundle-version` |
| `nga-08a-verify-authoring-checkpoint` | verify | — | `GET /services/data/v{apiVersion}/nextgen-authoring/bundle-versions/{bundleVersionId}` | `nga-07-activate-bundle-version` |
| `nga-08b-verify-runtime-botversion` | verify | — | `GET /services/data/v{apiVersion}/query` | `nga-08a-verify-authoring-checkpoint` |
<!-- codey:operations end -->
<!-- skill-validate: ignore-end -->
