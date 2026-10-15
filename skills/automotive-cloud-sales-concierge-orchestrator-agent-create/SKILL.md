---
name: automotive-cloud-sales-concierge-orchestrator-agent-create
description: "Create and activate the Automotive Sales Concierge agent from the pre-installed NextGen Authoring (NGA) template in a live org — entirely headless and API-first, driven only through the Headless 360 MCP server's dispatch tool. This is \"Act 1\" (Create & Activate the Agent) of the Automotive Sales Concierge steel thread. It resolves the AutomotiveSalesConcierge NGA template script, creates an NGA bundle from it, publishes the bundle (materializing the BotDefinition + BotVersion), activates the bundle version, and verifies the runtime BotVersion reached Active status. TRIGGER when the user wants to \"create the Automotive Sales Concierge agent\", \"deploy the automotive agent\", \"activate the sales concierge agent\", \"create the Industries Sales Assistance agent with the Automotive Sales Concierge subagent\", or otherwise asks to stand up the agent from the NGA template. DO NOT TRIGGER when the user wants to enable org preferences or assign permission sets (that's Act 0), create business data, run Data Pipelines jobs, or configure messaging channels — those are separate Acts served by other skills."
metadata:
  version: "1.0"
---

# Create & Activate Automotive Sales Concierge Agent (Act 1)

Create the **Automotive Sales Concierge** agent from the pre-installed **NextGen Authoring (NGA)**
template, publish and **activate** the agent — directly in a live org, **headlessly and API-first,
using only the Headless 360 MCP server's `dispatch` tool**.

This is **Act 1 — "Create & Activate the Agent"** of the Automotive Sales Concierge steel thread.
It runs **after Act 0** (Enable the Foundation) has completed successfully — Act 0 turns on the
Agentforce platform prerequisites and Automotive Cloud org preferences that this Act depends on.

The NGA template `AutoGenAi__AutomotiveSalesConcierge` (type: `AgentforceEmployeeAgent`) ships with
the Automotive Cloud package. It contains the full agent definition in afscript format — the router,
topics, and the **AutomotiveSalesConcierge** subagent with all 13 flow/standard actions
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
   - `IndustriesAutomotiveEnabled` = true (pref #4)
   - `AutomotiveAgentsEnabled` = true (pref #6)
   - `IndustriesAutomotiveGenerativeAIEnabled` = true (the UI-only pref — gated on legal consent)
   - Foundation permission sets assigned (including Agentforce Default Agent access)
3. NextGen Authoring is provisioned in the org (NGA license active).

If any Agentforce platform prerequisite is missing, this Act will fail. The orchestrator gates on
Act 0 success before invoking Act 1.

---

## Scope — AGENT CREATION & ACTIVATION ONLY (NextGen Authoring path)

- **In scope**
  - Probing NGA enablement (the `/nextgen-authoring/bundles` endpoint must return 200).
  - Resolving the `AutoGenAi__AutomotiveSalesConcierge` template's `agentScript` via the
    agent-authoring catalog (`get-agent-templates`).
  - Checking name idempotency (is a bundle with this name already created?).
  - Creating an NGA bundle + draft version from the resolved script.
  - Publishing the bundle version (materializes BotDefinition + BotVersion).
  - Activating the bundle version (promotes BotVersion to Active).
  - Verifying the runtime `BotVersion.Status == "Active"`.

- **Out of scope** (delegate — do NOT attempt here)
  - Enabling org preferences or assigning permission sets (Act 0).
  - Creating business data (accounts, vehicles, opportunities, etc.).
  - Configuring messaging channels, Experience Cloud sites, or deployment surfaces.
  - Running Data Pipelines jobs.
  - Modifying the agent's topics, actions, or instructions post-creation (the template is complete).
  - Using the legacy Copilot Builder `createCopilotFromTemplate` path (that is NOT NextGen Authoring).

---

## Required Inputs

All provided by the orchestrator's shared runtime context:

- **`<apiVersion>`** — the org's max API version (from orchestrator preflight step 1). NGA requires v64+.
- **`<userId>`** — the authenticated user's Id (from orchestrator preflight).

Template name is fixed: **`AutoGenAi__AutomotiveSalesConcierge`** (the fully-qualified NGA template name).

---

## The 13 expected actions in the template

The `AutomotiveSalesConcierge` agent template (defined in the `.agent` afscript file) includes
these actions. After activation, the verify step confirms the agent reached Active status:

| # | Action Name | Target | Purpose |
|---|---|---|---|
| 1 | SearchVehicleDefinitions | `flow://AutoGenAi__SearchVehicleDefinitions` | Search vehicle definitions by NLP query |
| 2 | GetDealersForSrchCriteria | `flow://AutoGenAi__GetDealersForSrchCriteria` | Find dealers by location/criteria |
| 3 | CreaOppAndPrefSell | `flow://IndSalesConcierge__CreaOppAndPrefSell` | Create opportunity + preferred seller |
| 4 | CreateQuoteFromOppt | `flow://IndSalesConcierge__CreateQuoteFromOppt` | Create quote from opportunity |
| 5 | GetAvailableAppointmentSlots | `standardInvocableAction://getAvailableAppointmentSlots` | Get test drive time slots |
| 6 | ScheduleAutomotiveAppointment | `standardInvocableAction://scheduleSvcApptActnblEvntOrch` | Book test drive appointment |
| 7 | GetVehiclesForCustomer | `flow://AutoGenAi__GetVehiclesForACustomer` | Get customer's existing vehicles |
| 8 | CreateVehicleAppraisal | `flow://IndAppraisals__CreateVehicleAppraisal` | Initiate trade-in appraisal |
| 9 | SummarizeCustomerAccount | `generatePromptResponse://AutoGenAi__SummarizeCustomerAccount` | Summarize customer account |
| 10 | QueryRecords | `standardInvocableAction://queryRecords` | SOQL via natural language |
| 11 | SummarizeRecord | `standardInvocableAction://getRecordSummarizationPrompt` | Summarize any record |
| 12 | DraftOrReviseEmail | `standardInvocableAction://getDraftOrReviseEmailPrompt` | Draft/revise emails |
| 13 | SrchPrdctAndParts | `flow://IndSalesConcierge__SrchPrdctAndParts` | Search accessories/related parts |

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

This also lists any already-created bundles — check if `AutomotiveSalesConcierge` already exists.

### Step 3. Resolve template script (the one off-native step)

The native NextGen Authoring API has no template catalog. Template name → agentScript resolution
goes through the headless agent-authoring dispatch route:

```text
dispatch("GET", "/headless/invoke/platform/agent-authoring/get-agent-templates")
```

The dispatcher auto-resolves the route and returns the unwrapped response directly.

**Response:** array of template entries. Each has `{devName, namespace, name (FQN = namespace__devName),
agentType, agentScript, templateLabel, templateDescription, iconUrl, ...}`.

**Match logic:** find the entry where `name` is EXACTLY equal to `AutoGenAi__AutomotiveSalesConcierge`
(strict equality — NOT `startsWith`, NOT `includes`, NOT substring match). There are multiple
templates with similar prefixes (e.g. `AutoGenAi__AutomotiveSalesConciergeCrossChannel`); you MUST
match on exact string equality only. If exact FQN match yields no result, fall back to exact
`devName` == `AutomotiveSalesConcierge` (again, strict equality — not partial match).

**Capture:** the matching entry's `agentScript` (the full afscript — typically ~60KB+).

**If no template found:** STOP. Report that the `AutoGenAi__AutomotiveSalesConcierge` NGA template
is not installed in this org. The Automotive Cloud package may not be deployed or the
`IndustriesAutomotiveGenerativeAIEnabled` preference is off.

### Step 4. Check name idempotency

Before creating, check if a bundle with this name already exists:

```text
dispatch("GET", "/services/data/v<apiVersion>/nextgen-authoring/bundles/names")
```

Check if `AutomotiveSalesConcierge` (or whatever `apiName` you intend to use) is already taken.

**If already exists:** The agent was already created in a prior run. Query for its bundle version
and check its status — if already Active, report success and skip to verify. If in DRAFT state,
proceed to publish + activate.

### Step 5. Create NGA bundle from template script

**CRITICAL — rewrite `config.developer_name` and `config.agent_label` in the agentScript** to a
run-scoped unique value before creating. The collision key for `publish` is the script's internal
`developer_name`, NOT the bundle `apiName`. If a BotDefinition with the same `developer_name`
already exists, publish will fail with `400 DUPLICATE_VALUE`.

For the Automotive Sales Concierge, use:
- `config.developer_name`: `AutomotiveSalesConcierge` (or a run-scoped variant if re-running)
- `config.agent_label`: `Automotive Sales Concierge`

**DO NOT change `config.agent_template`** — that is the template-lineage pointer and must stay as-is.

```text
dispatch("POST", "/services/data/v<apiVersion>/nextgen-authoring/bundles",
  body={
    "apiName": "AutomotiveSalesConcierge",
    "label": "Automotive Sales Concierge",
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
| Template is `AutoGenAi__AutomotiveSalesConcierge` (FQN) | This is the NextGen template shipped in Core; NOT the legacy `IndSalesConcierge__IndustriesSalesAssistance` copilot template. |
| Publish BEFORE activate | Create → Publish → Activate is the mandatory sequence. |
| Never blind-retry activate | Activation is async; read status back before retrying. |
| No hardcoded IDs | Resolve bundleId, bundleVersionId, publishedBotId, publishedBotVersionId at runtime. |
| Do not modify the agent post-creation | The template afscript is the source of truth. |
| Do not delete the agent | Leave it in place for validation by the admin. |

---

## Output Expectations

Report, in order:
1. **NGA enablement** — confirmed NextGen Authoring is provisioned (step 2 returned 200).
2. **Template resolution** — the `AutoGenAi__AutomotiveSalesConcierge` template's agentScript
   resolved successfully (size in chars).
3. **Bundle creation** — `bundleId`, `bundleVersionId`, `apiName`, `versionStatus: DRAFT`.
4. **Publish** — `publishedBotId`, `publishedBotVersionId`, `versionStatus: Published`.
5. **Activation** — activation accepted (204), `targetStatus: ACTIVE`.
6. **Verification** — runtime `BotVersion.Status == "Active"` confirmed.
7. **Summary** — the Automotive Sales Concierge agent is live. Provide:
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
| Template not found in `get-agent-templates` | Automotive Cloud package not deployed, or `IndustriesAutomotiveGenerativeAIEnabled` pref is off | Verify Act 0 completed; check the UI-only GenAI preference. |
| `createBundleWithVersion` 500 on large script | Intermittent server issue with large payloads | Fallback: create-empty then PATCH `updateBundleVersion` to attach asset. |
| Publish fails with `DUPLICATE_VALUE: BotDefinition duplicates value` | A BotDefinition with same `developer_name` already exists | Check existing agent; if Active, report success. If stale, use a unique developer_name. |
| Activate returns 500 UNKNOWN_EXCEPTION | Double-activate race condition | Read `getBundleVersion` status; if `targetStatus == "ACTIVE"`, the first activate succeeded. |
| `BotVersion.Status` not Active after activate 204 | Activation is async | Wait 5-15s and re-query. Up to 3 retries. |
| `validateAgentJson` reports errors on valid script | Known false-negative (YAML parser vs afscript) | Ignore validate failures; proceed to publish (the real compiler). |

---

## Cross-Skill Integration

This skill is **Act 1** and is designed to be invoked by the **Automotive Sales Concierge Foundation
Orchestrator** (its parent) after Act 0 succeeds.

| Need | Belongs to |
|---|---|
| Enable org preferences + assign permission sets | Act 0 — `enable-automotive-sales-concierge-foundation` |
| Configure messaging channels / deployment surfaces | later Act — channel deployment |
| Create business data (accounts, vehicles, opportunities) | later Act — data setup |
| Run Data Pipelines jobs | later Act — DPE enablement |
