---
name: automotive-cloud-sales-concierge-foundation-configure
description: "Enable the foundational Automotive Cloud org preferences (feature toggles) and assign the supporting permission sets that the Salesforce Automotive Sales Concierge agent depends on — entirely headless and API-first, driven only through the Headless 360 MCP server's dispatch tool. This is \"Act 0\" (Enable the Foundation) of the Automotive Sales Concierge steel thread and it is SETUP ONLY. It first delegates to AutomotiveFoundationSettings to enable the Automotive Cloud master toggle and Automotive Scheduler, then enables the Agentforce platform prerequisites (Einstein GPT Platform → Agent Platform → Einstein Copilot) via Connect API, then turns on Appraisal Management, Appraisal Components, Partner Lead Management via Connect API, Quotes via Metadata API; it hands the legally-gated Automotive Generative AI and Automotive Agents preferences off to the user to enable in the Setup UI (both have legal terms-and-conditions consent popups that have no headless path), STOPS AND WAITS for user confirmation, then resumes; and it assigns the Agentforce-platform and Automotive foundation permission sets to the target user via the sObject REST API. TRIGGER when the user wants to enable the Automotive Cloud foundation, set up Automotive Sales Concierge prerequisites, enable the Agentforce / Einstein GPT platform prerequisites, turn on the Automotive org preferences, or assign the Automotive foundation permission sets. DO NOT TRIGGER when the user wants to create business data, run Data Pipelines jobs, deploy the Agentforce agent, create Scheduler booking records, or create appraisal records — those are later Acts served by separate skills, not this setup-only foundation skill."
metadata:
  version: "1.0"
---

# Enable Automotive Sales Concierge Foundation (Act 0)

Enable the foundational **Automotive Cloud** org preferences and assign the supporting permission
sets that the **Automotive Sales Concierge** agent depends on — directly in a live org,
**headlessly and API-first, using only the Headless 360 MCP server's `dispatch` tool**.

This is **Act 0 — "Enable the Foundation"** of the Automotive Sales Concierge steel thread. Its job
is narrow and deliberate: **delegate to AutomotiveFoundationSettings to enable Automotive Cloud and
Scheduler, then enable the Agentforce platform prerequisites via Connect API (Einstein GPT Platform,
Agent Platform, Einstein Copilot — in that mandatory order), then enable the remaining Automotive
org preferences via Connect API and Metadata API, hand the two legally-gated preferences (Automotive
Generative AI and Automotive Agents) to the user to enable in the Setup UI (STOP and WAIT for user confirmation, then
resume), and assign the supporting permission sets** — so the later Acts (create data, run Data
Pipelines, deploy the agent) start from a working foundation.

This skill **mutates a live org**. Everything it does runs through `dispatch`.

---

## The command surface — `dispatch` ONLY (no sf CLI, no curl, no browser)

Every call this skill makes is a single MCP tool call:

```text
dispatch(method, path, body?, query_params?)
```

- The MCP server resolves the org, instance URL, and bearer token on its own. **Do not** ask for or
  handle tokens, instance URLs, org IDs, or API versions as inputs to a call — `dispatch` supplies
  them. Discover the API version once (below) only so you can build versioned REST paths.
- **Delegation:** Preferences #1 and #2 are delegated to the `AutomotiveFoundationSettings` SOR —
  see step 3. This skill does not call any endpoints for those preferences directly.
- **Connect API surface:** `PATCH /services/data/v<apiVersion>/setup/org/preferences/<preferenceName>`
  with body `{"desiredState": "true"}` enables a preference. `GET` at the same path returns
  `{"isPreferenceEnabled": true|false}`.
- **Metadata surface:** `PUT /services/data/v<apiVersion>/headless/metadata` with an `xmlRep` body.
  `GET` with query params `type` + `fullName` reads the current component. Always use the
  fully-qualified path (`/services/data/v<apiVersion>/headless/metadata`), never bare
  `/headless/metadata`.
- **Metadata PUT body format — `xmlRep` is mandatory.** The endpoint does NOT accept a
  `"metadata": {key: value}` shorthand. Every PUT must supply the full Metadata API XML
  representation in the `xmlRep` field:
  ```json
  {
    "type": "<SettingsTypeName>",
    "fullName": "<FullName>",
    "xmlRep": "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<SettingsTypeName xmlns=\"http://soap.sforce.com/2006/04/metadata\">\n    <fieldName>value</fieldName>\n</SettingsTypeName>"
  }
  ```
- **Native REST surfaces** (sObject, SOQL `query`) pass straight through `dispatch` at their
  fully-qualified `/services/data/v<apiVersion>/...` paths.

> **Absolute rules (from the Headless 360 factory):**
> - **`sf` CLI must NEVER appear as a step here.** Hosted-MCP customers have no shell.
> - **No browser / no manual Setup click — with exactly one deliberate, documented exception:** the
>   Automotive Generative AI and Automotive Agents legal-consent preferences (see step 7), which have no headless path at all.

---

## Be interactive — narrate, ask, and handle termination gracefully

This skill runs against a live org, so keep the user in the loop the whole way:

- **Narrate every step before and after you do it** — what you're about to call, then what came back.
- **Ask when a real decision is needed** — which org, which target user, and the Generative-AI UI
  handoff pause (step 7), where you must **wait for the user to confirm** before resuming.
- **Handle errors and terminations gracefully.** On any failure, report the exact API response
  (status + body), say which preference it affected, then offer: retry, skip-and-continue, or stop.

---

## Scope — SETUP ONLY

- **In scope**
  - Enabling Automotive Cloud org preferences via three surfaces: delegation to
    AutomotiveFoundationSettings, Connect API PATCH, and Metadata API PUT.
  - Handing the `IndustriesAutomotiveGenerativeAIEnabled` and `AutomotiveAgentsEnabled` preferences
    off to the user to enable in the Setup UI (legally gated — see step 7), then resuming.
  - Verifying the required Permission Set **Licenses** (read-only) and assigning the derived
    **permission sets** to a target user via the sObject REST API.
  - Confirming the `ManageAppraisalsAndValuations` user permission resolved after the foundation
    permission set is assigned.

- **Out of scope** (delegate — do NOT attempt here)
  - Creating business data of any kind.
  - Running Data Pipelines (DPE) jobs.
  - Deploying the Agentforce agent, its topics, or actions.
  - Provisioning Permission Set **Licenses** — those are org entitlements granted by license.
  - OmniStudio in any form.
  - Named credentials, integration procedures, FlexCards, messaging channel, ASA, MIAW.
  - DPE clone and activation.

---

## Required Inputs

- **Target org** — the org the MCP server is connected to. Confirm with the user before mutating.
- **Target user** for permission-set assignment — defaults to the authenticated user. Ask only if
  the user wants to provision a different user.
- **Desired scope** — default is the full Sales Concierge foundation (all preferences below).

**Do not hardcode** org IDs, instance URLs, access tokens, user IDs, permission-set IDs, or the API
version. Resolve them all at runtime through `dispatch`.

---

## The 12 preferences this skill enables

| # | Org Preference | Method | Surface / Endpoint | Notes |
|---|---|---|---|---|
| 1 | `IndustriesAutomotiveEnabled` | — | Delegate to `AutomotiveFoundationSettings` SOR | Master Automotive Cloud toggle. Must be enabled first. |
| 2 | `IndustriesAutomotiveSchedulerEnabled` | — | Delegate to `AutomotiveFoundationSettings` SOR | Requires #1 on first. |
| 3 | `CriteriaBasedSearchAndFilterEnabled` | PATCH | `/headless/invoke/platform/criteria-based-search-and-filter/set-criteria-based-search-and-filter-pref` | **Aura controller.** CBSF master gate — enables the Criteria-Based Search and Filter feature. Body: `{"enable": true}`. Enable after #2. |
| 4 | `EinsteinGPTPlatformEnabled` | PATCH | `/services/data/v<apiVersion>/setup/org/preferences/EinsteinGPTPlatformEnabled` | **Connect API.** Agentforce platform prerequisite — enable FIRST among Connect prefs. Body: `{"desiredState": "true"}`. |
| 5 | `AgentPlatformEnabled` | PATCH | `/services/data/v<apiVersion>/setup/org/preferences/AgentPlatformEnabled` | **Connect API.** Agentforce platform prerequisite — enable after #4. Body: `{"desiredState": "true"}`. |
| 6 | `EinsteinGPTCopilotEnabled` | PATCH | `/services/data/v<apiVersion>/setup/org/preferences/EinsteinGPTCopilotEnabled` | **Connect API.** Agentforce platform prerequisite — enable after #5. Body: `{"desiredState": "true"}`. |
| 7 | `AppraisalManagementEnabled` | PATCH | `/services/data/v<apiVersion>/setup/org/preferences/AppraisalManagementEnabled` | **Connect API.** Master appraisal-management toggle — enable BEFORE #8. Body: `{"desiredState": "true"}`. |
| 8 | `AutomotiveComponentsForAppraisalMgmtEnabled` | PATCH | `/services/data/v<apiVersion>/setup/org/preferences/AutomotiveComponentsForAppraisalMgmtEnabled` | **Connect API.** Appraisal components — enable AFTER #7. Body: `{"desiredState": "true"}`. |
| 9 | `MfgPartnerLeadMgmtEnabled` | PATCH | `/services/data/v<apiVersion>/setup/org/preferences/MfgPartnerLeadMgmtEnabled` | **Connect API.** Partner lead management. Body: `{"desiredState": "true"}`. Any order after #8. |
| 10 | `QuotesEnabled` | PUT | `/services/data/v<apiVersion>/headless/metadata` | **Metadata API.** `QuoteSettings` / `Quote` / `enableQuote`. Any order after #8. |
| 11 | **`IndustriesAutomotiveGenerativeAIEnabled`** | — | **Setup UI (user handoff)** | **Legally gated.** No headless surface. STOP and WAIT for user. Any order after #8. |
| 12 | **`AutomotiveAgentsEnabled`** | — | **Setup UI (user handoff)** | **Legally gated.** Child pref to Automotive Generative AI — enable together with #11 in the same UI handoff. STOP and WAIT for user. |

### Enablement order (load-bearing)

```text
#1 → #2 → #3 → #4 → #5 → #6 → #7 → #8 → then #9, #10, #11+#12 in any order
```

- **#1 before #2:** Scheduler requires the Foundation master toggle on.
- **#2 before #3:** CBSF requires Automotive Cloud on (Foundation master gate).
- **#4 before #5:** Agent Platform requires Einstein GPT Platform on.
- **#5 before #6:** Einstein Copilot requires Agent Platform on.
- **#7 before #8:** Appraisal Management (master toggle) must be on before Automotive Appraisal
  Components can enable.
- **#11 + #12 together:** Both are legally gated UI handoffs — enable in a single user handoff step.
  Automotive Agents is a child pref to Automotive Generative AI.

### Verify reads for each surface

| Surface | Verify endpoint | Expected success response |
|---|---|---|
| Delegation (#1, #2) | Handled by `AutomotiveFoundationSettings` SOR | Preference reads as enabled |
| Aura controller (#3) | `GET /headless/invoke/platform/criteria-based-search-and-filter` | `{"status": "SUCCESS", "isPrefEnabled": true}` |
| Connect API (#4–#9) | `GET /services/data/v<apiVersion>/setup/org/preferences/<preferenceName>` | `{"isPreferenceEnabled": true}` |
| Metadata API (#10) | `GET /services/data/v<apiVersion>/headless/metadata?type=QuoteSettings&fullName=Quote` | XML body containing `<enableQuote>true</enableQuote>` |
| UI handoff (#11, #12) | `GET /services/data/v<apiVersion>/setup/org/preferences/<preferenceName>` | `{"isPreferenceEnabled": true}` for both `IndustriesAutomotiveGenerativeAIEnabled` and `AutomotiveAgentsEnabled` |

### The Sales Concierge access-check chain

The Employee Sales Concierge agent's org-access gate requires ALL of the following features
to be active simultaneously:

- Automotive Scheduler (`IndustriesAutomotiveSchedulerEnabled` + Lightning Scheduler PSL)
- Automotive Cloud (`IndustriesAutomotiveEnabled`)
- Criteria-Based Search and Filter (`CriteriaBasedSearchAndFilterEnabled`)
- Agents for Automotive (`AutomotiveAgentsEnabled`)
- Appraisal Management (`AppraisalManagementEnabled`)
- Partner Lead Management (`MfgPartnerLeadMgmtEnabled`)

If any leaf is false after the writes, the agent's access check fails.

---

## Workflow

Follow in order. Every mutation is followed by a verify read. Report progress per step.

### 1. Preflight — confirm the connected org and resolve runtime facts

Discover the API version (used to build every versioned REST path) and the authenticated user, all
through `dispatch`:

```text
dispatch("GET", "/services/data/")
# → array of {label, url, version}; take the highest version as <apiVersion>.

dispatch("GET", "/services/data/v<apiVersion>/chatter/users/me")
# → the current user (id, username). Capture id → <userId>, username → <username>.
```

Tell the user which org and user this run targets and confirm before mutating.

### 2. Write-then-verify pattern (applies to ALL preference writes in steps 3–6)

For each preference on Connect API or Metadata API, apply this pattern:

1. **Write** — PATCH (Connect API) or PUT (Metadata API) to enable the preference.
2. **Verify** — GET at the verify endpoint to confirm the preference is now enabled.

If a write "succeeds" but the verify reads back as not enabled, that preference is almost certainly
gated behind a missing Permission Set License — note it and continue; step 8 verifies the PSLs.

### 3. Enable Automotive Foundation and Scheduler — delegate to AutomotiveFoundationSettings

Delegate to the `AutomotiveFoundationSettings` SOR to enable these two preferences. That SOR owns
the enablement API surface and documents the exact call pattern, request/response shapes, and
error handling. Enable Foundation first, then Scheduler (Scheduler requires Foundation on).

**#1 — IndustriesAutomotiveEnabled (Automotive Cloud master toggle):**
Delegate to `AutomotiveFoundationSettings` to enable the automotive-foundation-pref.
Verify it reads as enabled before proceeding.

**#2 — IndustriesAutomotiveSchedulerEnabled (only after #1 is verified true):**
Delegate to `AutomotiveFoundationSettings` to enable the automotive-scheduler-pref.
If the Scheduler-for-Automotive license is not provisioned, report as license-level blocker
and continue.

**#3 — CriteriaBasedSearchAndFilterEnabled (only after #2 is verified true):**
Enable the CBSF org preference via the Aura controller headless route. This uses the same
route that the `CriteriaBasedSearchAndFilter` SOR uses directly — no delegation needed.

```text
# Write:
dispatch("PATCH", "/headless/invoke/platform/criteria-based-search-and-filter/set-criteria-based-search-and-filter-pref",
  body={"enable": true})

# Verify:
dispatch("GET", "/headless/invoke/platform/criteria-based-search-and-filter")
# → {"status": "SUCCESS", "isPrefEnabled": true}
```

### 4. Enable the Agentforce platform prerequisites — Connect API, in order

These three must be enabled sequentially. Each uses the write-then-verify pattern:

```text
# Write:
dispatch("PATCH", "/services/data/v<apiVersion>/setup/org/preferences/<preferenceName>",
  body={"desiredState": "true"})

# Verify:
dispatch("GET", "/services/data/v<apiVersion>/setup/org/preferences/<preferenceName>")
# → {"isPreferenceEnabled": true}
```

| Order | Preference Name | Notes |
|---|---|---|
| First | `EinsteinGPTPlatformEnabled` | Master Einstein GPT switch. If verify reads `false` after write, the `EinsteinGPTPlatformAddOn` PSL is missing — license-level blocker. |
| Second | `AgentPlatformEnabled` | Only after `EinsteinGPTPlatformEnabled` verifies `true`. |
| Third | `EinsteinGPTCopilotEnabled` | Only after `AgentPlatformEnabled` verifies `true`. **Silent-failure mode:** PATCH succeeds but verify reads `false` when the `EinsteinGPTCopilot` org permission (Einstein Copilot add-on license) is missing — report as license-level blocker and **continue** (Automotive prefs do not depend on this). |

### 5. Enable the remaining Automotive preferences — Connect API

Continue with the same Connect API write-then-verify pattern from step 4, in this order:

| Order | Preference Name | Notes |
|---|---|---|
| First | `AppraisalManagementEnabled` | Master appraisal-management toggle — must verify true before next. |
| Second | `AutomotiveComponentsForAppraisalMgmtEnabled` | Appraisal components — requires `AppraisalManagementEnabled` on. |
| Any | `MfgPartnerLeadMgmtEnabled` | Partner lead management. No ordering dependency. |

### 6. Enable Quotes — Metadata API

Apply the write-then-verify pattern for the Metadata API surface. The PUT body must include
`type`, `fullName`, and `xmlRep` (the full Metadata API XML representation with
`<enableQuote>true</enableQuote>` set). Refer to the Metadata PUT body format documented in the
command surface section above.

```text
# Write:
dispatch("PUT", "/services/data/v<apiVersion>/headless/metadata",
  body={"type": "QuoteSettings", "fullName": "Quote", "xmlRep": "<full XML body>"})

# Verify:
dispatch("GET", "/services/data/v<apiVersion>/headless/metadata",
  query_params={"type": "QuoteSettings", "fullName": "Quote"})
# → confirm <enableQuote>true</enableQuote>
```

### 7. Enable Automotive Generative AI AND Automotive Agents — USER UI HANDOFF (HARD STOP — wait for user)

Both `IndustriesAutomotiveGenerativeAIEnabled` and `AutomotiveAgentsEnabled` **cannot be enabled
headlessly.** Both are opted out of headless surfaces for legal reasons — enabling each surfaces a
**legal terms-and-conditions consent popup in the Setup UI** that has no headless path. Automotive
Agents is a child preference to Automotive Generative AI, so both must be enabled together in the
same UI handoff.

> **HARD BLOCKING CHECKPOINT — DO NOT PROCEED PAST THIS POINT UNTIL THE USER CONFIRMS.**
> This is NOT optional. You MUST stop execution here, present the instructions below, and then
> WAIT for the user's explicit confirmation before taking ANY further action.

1. **STOP execution and tell the user** you are pausing for two mandatory manual toggles, and why.
2. **Give precise instructions:** in the target org:
   - Go to **Setup → Einstein / Automotive Generative AI setup**, toggle on **Automotive Generative
     AI**, and **accept the legal terms-and-conditions popup** that appears.
   - Then toggle on **Automotive Agents** (on the same page or under Automotive Agents setup) and
     **accept its legal terms-and-conditions popup**.
3. **STOP HERE. Do not proceed.** Wait for the user to respond with explicit confirmation (e.g.
   "done", "enabled both", "skip"). If the user says to skip, note it as an open item and
   proceed to Step 8.
4. **On confirmation, verify both headlessly:**

```text
dispatch("GET", "/services/data/v<apiVersion>/setup/org/preferences/IndustriesAutomotiveGenerativeAIEnabled")
# → {"isPreferenceEnabled": true}

dispatch("GET", "/services/data/v<apiVersion>/setup/org/preferences/AutomotiveAgentsEnabled")
# → {"isPreferenceEnabled": true}
```

### 8. Assign the foundation permission sets (sObject REST, API-first)

Salesforce licensing for a feature is two calls:

1. **`PermissionSetLicenseAssign`** — consumes a seat from a `PermissionSetLicense` bucket.
2. **`PermissionSetAssignment`** — assigns the actual `PermissionSet` to the user.

Assign **both** the PSL and its paired PermissionSet for each feature below. A `DUPLICATE_VALUE` on
either write means it is already assigned — treat as success and continue.

**8a. Verify PSL presence (resolve by exact DeveloperName).**

```text
dispatch("GET", "/services/data/v<apiVersion>/query", query_params={
  "q": "SELECT Id, DeveloperName, MasterLabel FROM PermissionSetLicense WHERE DeveloperName IN ('EinsteinGPTCopilotPsl','EinsteinGPTPromptTemplatesPsl','AgentforcePlatformUserPsl','EinsteinForAutomotivePsl','AutomotiveFoundationUserPsl','AutomotiveSchedulerPsl','CriteriaBasedSearchAndFilterPsl','ManufacturingPartnerLeadMgmtPsl','IndustriesServiceExcellencePsl','LightningSchedulerPsl','LightningSchedulerGreeterPsl')"
})
```

PSL → capability map:

| # | PSL DeveloperName | Label | Capability it gates |
|---|---|---|---|
| 1 | `EinsteinGPTCopilotPsl` | Agentforce (Default) | Agentforce agent runtime |
| 2 | `EinsteinGPTPromptTemplatesPsl` | Einstein Prompt Templates | Prompt template invocation |
| 3 | `AgentforcePlatformUserPsl` | Agentforce Platform User | Agentforce platform base (PSL seat only — no paired PermissionSet) |
| 4 | `EinsteinForAutomotivePsl` | Einstein for Automotive | Automotive GenAI / Einstein access |
| 5 | `AutomotiveFoundationUserPsl` | Automotive Foundation User | Base Automotive objects + ManageAppraisalsAndValuations |
| 6 | `AutomotiveSchedulerPsl` | Automotive Scheduler | Scheduler objects |
| 7 | `CriteriaBasedSearchAndFilterPsl` | Criteria-Based Search and Filter | CBSF objects |
| 8 | `ManufacturingPartnerLeadMgmtPsl` | Partner Lead Management | Partner lead management |
| 9 | `IndustriesServiceExcellencePsl` | Industry Service Excellence | Industries base |
| 10 | `LightningSchedulerPsl` | Salesforce Scheduler | Lightning Scheduler base (PSL seat only — no paired PermissionSet) |
| 11 | `LightningSchedulerGreeterPsl` | Salesforce Scheduler Greeter | Scheduler Greeter |

Any PSL not found means the license is not provisioned — report as a blocker.

**8b. Assign PSL seats** — for each PSL above:

```text
dispatch("GET", "/services/data/v<apiVersion>/query", query_params={
  "q": "SELECT Id FROM PermissionSetLicense WHERE DeveloperName = '<pslDeveloperName>'"
})
dispatch("POST", "/services/data/v<apiVersion>/sobjects/PermissionSetLicenseAssign",
  body={"AssigneeId": "<userId>", "PermissionSetLicenseId": "<pslId>"})
```

`DUPLICATE_VALUE` = already assigned = success.

**8c. Resolve and assign PermissionSets by exact Name.**

```text
dispatch("GET", "/services/data/v<apiVersion>/query", query_params={
  "q": "SELECT Id, Name, Label FROM PermissionSet WHERE Name IN ('CopilotSalesforceUser','CopilotSalesforceAdmin','EinsteinGPTPromptTemplateUser','EinsteinForAutomotivePsl','AutomotiveFoundationUserPsl','AutomotiveSchedulerPsl','CriteriaBasedSearchAndFilterPsl','ManufacturingPartnerLeadMgmtPsl','IndustriesServiceExcellence','LightningSchedulerGreeterPermissionSet')"
})
```

PermissionSet → PSL map:

| # | PermissionSet Name | Label | Backing PSL |
|---|---|---|---|
| 1 | `CopilotSalesforceUser` | Access Agentforce Default Agent | EinsteinGPTCopilotPsl |
| 2 | `CopilotSalesforceAdmin` | Agentforce Default Admin | EinsteinGPTCopilotPsl |
| 3 | `EinsteinGPTPromptTemplateUser` | Prompt Template User | EinsteinGPTPromptTemplatesPsl |
| 4 | `EinsteinForAutomotivePsl` | Einstein for Automotive | EinsteinForAutomotivePsl |
| 5 | `AutomotiveFoundationUserPsl` | Automotive Foundation User | AutomotiveFoundationUserPsl |
| 6 | `AutomotiveSchedulerPsl` | Automotive Scheduler | AutomotiveSchedulerPsl |
| 7 | `CriteriaBasedSearchAndFilterPsl` | Criteria-Based Search and Filter | CriteriaBasedSearchAndFilterPsl |
| 8 | `ManufacturingPartnerLeadMgmtPsl` | Partner Lead Management | ManufacturingPartnerLeadMgmtPsl |
| 9 | `IndustriesServiceExcellence` | Industry Service Excellence | IndustriesServiceExcellencePsl |
| 10 | `LightningSchedulerGreeterPermissionSet` | Salesforce Scheduler Greeter | LightningSchedulerGreeterPsl |

**8d. The target user Id** is `<userId>` from step 1 (default = authenticated user). If provisioning a
different user, resolve their Id:

```text
dispatch("GET", "/services/data/v<apiVersion>/query", query_params={
  "q": "SELECT Id, Username FROM User WHERE Username = '<username>'"
})
```

**8e. Assign each PermissionSet to the target user:**

```text
dispatch("POST", "/services/data/v<apiVersion>/sobjects/PermissionSetAssignment",
  body={"AssigneeId": "<userId>", "PermissionSetId": "<permissionSetId>"})
```

`DUPLICATE_VALUE` = already assigned = success.

**8f. Verify the assignments landed** — read back BOTH PSL seats AND PermissionSets:

```text
dispatch("GET", "/services/data/v<apiVersion>/query", query_params={
  "q": "SELECT Id, PermissionSetLicenseId, PermissionSetLicense.DeveloperName FROM PermissionSetLicenseAssign WHERE AssigneeId = '<userId>'"
})
```

Confirm all 11 PSL seats are assigned. Report any missing.

```text
dispatch("GET", "/services/data/v<apiVersion>/query", query_params={
  "q": "SELECT PermissionSetId, PermissionSet.Name FROM PermissionSetAssignment WHERE AssigneeId = '<userId>'"
})
```

Confirm all 10 PermissionSets are present. Report any missing.

**8g. Verify the `ManageAppraisalsAndValuations` user permission resolved.**

```text
dispatch("GET", "/services/data/v<apiVersion>/query", query_params={
  "q": "SELECT PermissionSet.Name FROM PermissionSetAssignment WHERE AssigneeId = '<userId>' AND PermissionSet.PermissionsManageAppraisalsAndValuations = true"
})
```

- **If a row returns** → the permission is granted. Done.
- **If zero rows** → create a minimal permission set that carries it:

```text
dispatch("POST", "/services/data/v<apiVersion>/headless/metadata", body={
  "type": "PermissionSet", "fullName": "Automotive_Manage_Appraisals",
  "metadata": {
    "label": "Automotive Manage Appraisals",
    "hasActivationRequired": false,
    "userPermissions": [{"enabled": true, "name": "ManageAppraisalsAndValuations"}]
  }
})
# then resolve its Id and assign it:
dispatch("GET", "/services/data/v<apiVersion>/query", query_params={
  "q": "SELECT Id FROM PermissionSet WHERE Name = 'Automotive_Manage_Appraisals'"
})
dispatch("POST", "/services/data/v<apiVersion>/sobjects/PermissionSetAssignment",
  body={"AssigneeId": "<userId>", "PermissionSetId": "<newPsId>"})
```

**8h. Report Scheduler-object CRUD readiness (report-only — no grant here).**

```text
dispatch("GET", "/services/data/v<apiVersion>/query", query_params={
  "q": "SELECT SobjectType, PermissionsCreate, PermissionsEdit, PermissionsDelete FROM ObjectPermissions WHERE ParentId IN (SELECT PermissionSetId FROM PermissionSetAssignment WHERE AssigneeId = '<userId>') AND SobjectType IN ('OperatingHours','TimeSlot','ServiceTerritory','ServiceTerritoryMember','ServiceResource','WorkTypeGroup','WorkType','WorkTypeGroupMember','ServiceTerritoryWorkType')"
})
```

- **System Admin** → report "Scheduler objects: CRUD OK (admin)".
- **Non-admin lacking Create** → report as a readiness note for Act 3.
- This step never mutates anything.

---

## Rules / Constraints

| Constraint | Rationale |
|---|---|
| `dispatch` only — no `sf` CLI, no `curl`, no browser | Hosted-MCP customers have no shell. |
| The GenAI + Automotive Agents preferences are the single, deliberate UI handoff — HARD STOP | Both legally opted out of every headless surface. Pause, instruct, WAIT for user confirmation, verify both, resume. |
| No hardcoded org IDs, instance URLs, tokens, user IDs, permission-set IDs, or API versions | Portable across orgs; resolve at runtime. |
| Enable Foundation (#1) before Scheduler (#2) | Scheduler requires Foundation on. |
| Enable Einstein GPT (#4) before Agent Platform (#5) before Copilot (#6) | Hard ordering dependency. |
| Enable AppraisalManagement (#7) before AutomotiveComponentsForAppraisalMgmt (#8) | Master toggle before components. |
| Verify after every write | A write can "succeed" while a gated field stays false. |
| The preference table is the source of truth | Enable ONLY the 12 preferences listed. Do NOT attempt additional preferences. |
| Stay inside setup scope | This is Act 0. Never create data, run pipelines, or deploy the agent. |

---

## Troubleshooting

### Delegation failures (prefs #1, #2)

If the `AutomotiveFoundationSettings` delegation fails, report the error from that SOR and offer
retry/skip/stop. Common causes: Foundation not on when enabling Scheduler, or the
Scheduler-for-Automotive license not provisioned (license-level blocker).

### Connect API failures

| Symptom | Cause | Resolution |
|---|---|---|
| PATCH returns error | Preference gated behind a missing PSL | Verify PSLs in step 8a; report missing PSL. |
| Verify reads `false` after successful write | Silent-failure — underlying permission/license missing | Report the specific PSL blocker and continue. |
| 404 Not Found | Preference name incorrect or not registered on this org version | Verify the exact preference name from the table. |

### Metadata API failures

| Symptom | Cause | Resolution |
|---|---|---|
| `Invalid field` | Field name wrong for this API version | Re-check against table; if correct, feature is PSL-gated. |
| Write succeeds but verify shows field `false` | Preference gated behind a missing PSL | Report PSL blocker. |
| `INSUFFICIENT_ACCESS` | Connected user lacks Customize Application | Report; must use an admin. |

### Generative AI + Automotive Agents preferences (UI handoff)

| Symptom | Cause | Resolution |
|---|---|---|
| User asks why these aren't automated | Legal consent popup; no API path | Explain: legal terms require UI acceptance for both. |
| Verify reads `false` after user says enabled | Toggle/consent didn't take, or Automotive Cloud (#1) missing | Confirm #1 is on; ask user to re-toggle and re-accept both. |

### Permission-set assignment failures

| Symptom | Cause | Resolution |
|---|---|---|
| `DUPLICATE_VALUE` | Already assigned | Benign — success. |
| Query returns fewer sets than requested | Some sets not in this org | Assign resolved ones; report missing. |

---

## Output Expectations

Report, in order:
1. **Org & user** — the connected org, target user, and resolved API version.
2. **Per-preference results** — for each of the 12 preferences: skipped (already on), newly enabled
   (wrote + verified), or still off (name the blocker).
3. **Actions taken** — delegation results, Connect API writes, Metadata writes, GenAI + Automotive Agents handoff outcome,
   permission-set assignments.
4. **Gaps** — any preference still off and the blocker (PSL/license).
5. **Scheduler-object CRUD readiness** — from step 8h.
6. **Next step** — the foundation is ready; hand back to the orchestrator for the next Act.

---

## Cross-Skill Integration

This skill is **Act 0** and is designed to be invoked by the **Automotive Sales Concierge Foundation
Orchestrator** (its parent).

| Need | Belongs to |
|---|---|
| AutomotiveFoundationSettings pref enablement (prefs #1, #2) | Delegated to `AutomotiveFoundationSettings` SOR (mfg-knights) |
| Run Data Pipelines (DPE) jobs | later Act |
| Deploy the Agentforce agent metadata | later Act |
| Create Scheduler booking data | later Act |
| Create appraisal setup data | later Act |

<!-- skill-validate: ignore-start -->
<!-- codey:operations start -->
## Operations Reference

Operations this skill uses — routing and dependency reference.

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `preflight-api-version` | read | — | `GET /services/data/` | — |
| `preflight-user` | read | — | `GET /services/data/${apiVersion}/query` | `preflight-api-version` |
| `check-required-psls` | read | — | `GET /services/data/${apiVersion}/query` | `preflight-api-version` |
| `set-automotive-cloud-master` | write | — | `PATCH /headless/invoke/platform/automotive-foundation-settings/set-automotive-foundation-pref` | `preflight-api-version` |
| `set-automotive-scheduler` | write | — | `PATCH /headless/invoke/platform/automotive-foundation-settings/set-automotive-scheduler-pref` | `set-automotive-cloud-master` |
| `set-criteria-based-search-and-filter-pref` | write | — | `PATCH /headless/invoke/platform/criteria-based-search-and-filter/set-criteria-based-search-and-filter-pref` | `set-automotive-scheduler` |
| `set-einstein-gpt-platform` | write | — | `PATCH /services/data/${apiVersion}/setup/org/preferences/EinsteinGPTPlatformEnabled` | `set-criteria-based-search-and-filter-pref` |
| `set-agent-platform` | write | — | `PATCH /services/data/${apiVersion}/setup/org/preferences/AgentPlatformEnabled` | `set-einstein-gpt-platform` |
| `set-einstein-copilot` | write | — | `PATCH /services/data/${apiVersion}/setup/org/preferences/EinsteinGPTCopilotEnabled` | `set-agent-platform` |
| `set-appraisal-management` | write | — | `PATCH /services/data/${apiVersion}/setup/org/preferences/AppraisalManagementEnabled` | `set-einstein-copilot` |
| `set-automotive-appraisal-components` | write | — | `PATCH /services/data/${apiVersion}/setup/org/preferences/AutomotiveComponentsForAppraisalMgmtEnabled` | `set-appraisal-management` |
| `set-mfg-partner-lead-mgmt` | write | — | `PATCH /services/data/${apiVersion}/setup/org/preferences/MfgPartnerLeadMgmtEnabled` | `set-automotive-appraisal-components` |
| `enable-quote-settings` | write | — | `PUT /services/data/${apiVersion}/headless/metadata` | `set-mfg-partner-lead-mgmt` |
| `enable-automotive-genai-prefs` | delegate | — | `GET /services/data/${apiVersion}/setup/org/preferences/IndustriesAutomotiveGenerativeAIEnabled` | `enable-quote-settings` |
| `assign-psl-seats` | write | — | `POST /services/data/${apiVersion}/composite/sobjects` | `preflight-user`, `check-required-psls`, `enable-automotive-genai-prefs` |
| `assign-perm-sets` | write | — | `POST /services/data/${apiVersion}/composite/sobjects` | `assign-psl-seats` |
| `verify-user-assignments` | verify | — | `GET /services/data/${apiVersion}/query` | `assign-perm-sets` |
<!-- codey:operations end -->
<!-- skill-validate: ignore-end -->
