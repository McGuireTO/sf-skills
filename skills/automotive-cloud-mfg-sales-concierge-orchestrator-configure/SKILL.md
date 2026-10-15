---
name: automotive-cloud-mfg-sales-concierge-orchestrator-configure
description: "Enable the foundational Manufacturing Cloud org preferences (feature toggles) and assign the supporting permission sets that the Salesforce Industries Sales Concierge agent depends on — entirely headless and API-first, driven only through the Headless 360 MCP server's dispatch tool. This is \"Act 0\" (Enable the Foundation) of the Industries Sales Concierge steel thread and it is SETUP ONLY. It first enables the Agentforce platform prerequisites (Einstein GPT Platform → Agent Platform → Einstein Copilot) via Connect API, then turns on Criteria-Based Search & Filter via Aura controller, Appraisal Management and Partner Lead Management via Connect API, Quotes Without Opportunity via Metadata API; it hands the two legally-gated preferences — MFG Agents and Manufacturing Generative AI — off to the user to enable in the Setup UI (both preferences have legal terms-and-conditions consent popups that have no headless path), STOPS AND WAITS for user confirmation, then resumes; and it assigns the Agentforce-platform and Manufacturing foundation permission sets to the target user via the sObject REST API. TRIGGER when the user wants to enable the Manufacturing Cloud foundation, set up Industries Sales Concierge prerequisites, enable the Agentforce / Einstein GPT platform prerequisites, turn on the Manufacturing org preferences, or assign the Manufacturing foundation permission sets. DO NOT TRIGGER when the user wants to create business data, run Data Pipelines jobs, deploy the Agentforce agent, create partner lead records, or create quote records — those are later Acts served by separate skills, not this setup-only foundation skill."
metadata:
  version: "1.0"
---

# Enable Industries Sales Concierge Foundation (Act 0)

Enable the foundational **Manufacturing Cloud** org preferences and assign the supporting
permission sets that the **Industries Sales Concierge** agent depends on — directly in a live org,
**headlessly and API-first, using only the Headless 360 MCP server's `dispatch` tool**.

This is **Act 0 — "Enable the Foundation"** of the Industries Sales Concierge steel thread. Its job
is narrow and deliberate: **enable the Agentforce platform prerequisites via Connect API (Einstein
GPT Platform, Agent Platform, Einstein Copilot — in that mandatory order), then enable the
remaining Manufacturing foundation preferences via Connect API, Aura controller, and Metadata API,
hand the two legally-gated preferences — MFG Agents and Manufacturing Generative AI — to the user
to enable in the Setup UI (STOP and WAIT for user confirmation, then resume), and assign the
supporting permission sets** — so the later Acts (create data, run Data Pipelines, deploy the agent)
start from a working foundation.

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
- **Connect API surface:** `PATCH /services/data/v<apiVersion>/setup/org/preferences/<preferenceName>`
  with body `{"desiredState": "true"}` enables a preference. `GET` at the same path returns
  `{"isPreferenceEnabled": true|false}`.
- **Aura controller surface:** The CBSF preference uses a headless Aura controller route at
  `/headless/invoke/platform/criteria-based-search-and-filter/set-criteria-based-search-and-filter-pref`.
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
  For GET (read), the body is simply `{"type": "<SettingsTypeName>", "fullName": "<FullName>"}` —
  no `xmlRep` needed for reads. Because a Metadata write is a **full-record replace**, always
  **read the current component before writing** and include only the fields you intend to set in
  the `xmlRep`, so you don't reset omitted fields to defaults.
- **Native REST surfaces** (sObject, SOQL `query`) pass straight through `dispatch` at their
  fully-qualified `/services/data/v<apiVersion>/...` paths.

> **Absolute rules (from the Headless 360 factory):**
> - **`sf` CLI must NEVER appear as a step here.** Hosted-MCP customers have no shell.
> - **No browser / no manual Setup click — with exactly two deliberate, documented exceptions:** the
>   MFG Agents and Manufacturing Generative AI legal-consent preferences (see step 7), which have no
>   headless path at all. Every other step is fully headless. If a non-handoff step cannot be
>   completed by `dispatch`, STOP and report the exact failing response — do not reach for a
>   browser workaround.

---

## Be interactive — narrate, ask, and handle termination gracefully

This skill runs against a live org, so keep the user in the loop the whole way:

- **Narrate every step before and after you do it** — what you're about to call, then what came back.
- **Ask when a real decision is needed** — which org, which target user, and the MFG Agents +
  Generative-AI UI handoff pause (step 7), where you must **wait for the user to confirm** before
  resuming.
- **Handle errors and terminations gracefully.** On any failure, report the exact API response
  (status + body), say which preference it affected, then offer: retry, skip-and-continue, or stop.

---

## Scope — SETUP ONLY

- **In scope**
  - Enabling Manufacturing Cloud org preferences via three surfaces: Connect API PATCH, Aura
    controller, and Metadata API PUT.
  - Handing the `MfgAgentsEnabled` and `ManufacturingGenAIPref` preferences off to the user to
    enable in the Setup UI (both are legally gated — see step 7), then resuming.
  - Verifying the required Permission Set **Licenses** (read-only) and assigning the derived
    **permission sets** to a target user via the sObject REST API.

- **Out of scope** (delegate — do NOT attempt here)
  - Creating business data of any kind (accounts, assets, leads, partner lead management records,
    quote records).
  - Running Data Pipelines (DPE) jobs — a later Act.
  - Deploying the Agentforce agent, its topics, or actions.
  - Provisioning the underlying Permission Set **Licenses** — those are org entitlements granted by
    license and cannot be created via API; this skill reads and reports them, then assigns the derived
    permission sets.
  - **OmniStudio in any form — explicitly out of scope for this steel thread.**
  - **Named credentials**, integration procedures, FlexCards, the messaging channel, ASA, and MIAW —
    all out of scope for this steel thread.
  - **DPE clone and activation** — a separate skill, integrated later.
  - **Act 6** in its entirety, and any verification of the deployed agent's actions.

---

## Required Inputs

- **Target org** — the org the MCP server is connected to. Confirm with the user before mutating.
- **Target user** for permission-set assignment — defaults to the authenticated user. Ask only if
  the user wants to provision a different user.
- **Desired scope** — default is the full Sales Concierge foundation (all preferences below).

**Do not hardcode** org IDs, instance URLs, access tokens, user IDs, permission-set IDs, or the API
version. Resolve them all at runtime through `dispatch`.

---

## The 9 preferences this skill enables

| # | Org Preference | Method | Surface / Endpoint | Notes |
|---|---|---|---|---|
| 1 | `EinsteinGPTPlatformEnabled` | PATCH | `/services/data/v<apiVersion>/setup/org/preferences/EinsteinGPTPlatformEnabled` | **Connect API.** Agentforce platform prerequisite — enable FIRST. Body: `{"desiredState": "true"}`. |
| 2 | `AgentPlatformEnabled` | PATCH | `/services/data/v<apiVersion>/setup/org/preferences/AgentPlatformEnabled` | **Connect API.** Agentforce platform prerequisite — enable after #1. Body: `{"desiredState": "true"}`. |
| 3 | `EinsteinGPTCopilotEnabled` | PATCH | `/services/data/v<apiVersion>/setup/org/preferences/EinsteinGPTCopilotEnabled` | **Connect API.** Agentforce platform prerequisite — enable after #2. Body: `{"desiredState": "true"}`. |
| 4 | `CriteriaBasedSearchAndFilterEnabled` | PATCH | `/headless/invoke/platform/criteria-based-search-and-filter/set-criteria-based-search-and-filter-pref` | **Aura controller.** CBSF master gate — enables the Criteria-Based Search and Filter feature. Body: `{"enable": true}`. |
| 5 | `AppraisalManagementEnabled` | PATCH | `/services/data/v<apiVersion>/setup/org/preferences/AppraisalManagementEnabled` | **Connect API.** Master appraisal-management toggle. Body: `{"desiredState": "true"}`. |
| 6 | `MfgPartnerLeadMgmtEnabled` | PATCH | `/services/data/v<apiVersion>/setup/org/preferences/MfgPartnerLeadMgmtEnabled` | **Connect API.** Partner lead management. Body: `{"desiredState": "true"}`. |
| 7 | `QuotesWithoutOppEnabled` | PUT | `/services/data/v<apiVersion>/headless/metadata` | **Metadata API.** `QuoteSettings` / `Quote` / `enableQuotesWithoutOppEnabled`. Quotes without opportunity — commerce dependency for the Create-Quote action (later Act). |
| 8 | **`MfgAgentsEnabled`** | — | **Setup UI (user handoff — see step 7)** | **Legally gated.** Enabling it triggers a legal terms-and-conditions consent popup in the Setup UI that has **no headless path**. The skill **pauses and asks the user to enable it in the UI** alongside Manufacturing Generative AI (#9), waits for user confirmation, then resumes. |
| 9 | **`ManufacturingGenAIPref`** | — | **Setup UI (user handoff — see step 7)** | **Legally gated.** Enabling it triggers a legal terms-and-conditions consent popup in the Setup UI that has **no headless path** — it is opted out of the Metadata API for legal reasons (`mdApiOptOutReason="LEGAL"`). The skill **pauses and asks the user to enable it in the UI**, waits for user confirmation, then resumes. |

### Enablement order (load-bearing)

```text
#1 → #2 → #3 → #4 → #5 → #6 → then #7, #8, #9 in any order
```

- **#1 before #2:** Agent Platform requires Einstein GPT Platform on.
- **#2 before #3:** Einstein Copilot requires Agent Platform on.

### Verify reads for each surface

| Surface | Verify endpoint | Expected success response |
|---|---|---|
| Connect API (#1–#3, #5, #6) | `GET /services/data/v<apiVersion>/setup/org/preferences/<preferenceName>` | `{"isPreferenceEnabled": true}` |
| Aura controller (#4) | `GET /headless/invoke/platform/criteria-based-search-and-filter` | `{"status": "SUCCESS", "isPrefEnabled": true}` |
| Metadata API (#7) | `GET /services/data/v<apiVersion>/headless/metadata?type=QuoteSettings&fullName=Quote` | XML body containing `<enableQuotesWithoutOppEnabled>true</enableQuotesWithoutOppEnabled>` |

### The Industries Sales Concierge access-check chain

The Industries Sales Concierge agent's org-access gate requires ALL of the following features
to be active simultaneously:

- Criteria-Based Search and Filter (`CriteriaBasedSearchAndFilterEnabled`)
- MFG Agents (`MfgAgentsEnabled` — enabled via UI handoff in step 7)
- Partner Lead Management (`MfgPartnerLeadMgmtEnabled`)

If any leaf is false after the writes and UI handoffs, the agent's access check fails.

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

### 2. Write-then-verify pattern (applies to ALL preference writes in steps 3–5)

For each preference on Connect API, Aura controller, or Metadata API, apply this pattern:

1. **Write** — PATCH (Connect API / Aura) or PUT (Metadata API) to enable the preference.
2. **Verify** — GET at the verify endpoint to confirm the preference is now enabled.

If a write "succeeds" but the verify reads back as not enabled, that preference is almost certainly
gated behind a missing Permission Set License — note it and continue; step 8 verifies the PSLs.

### 3. Enable the Agentforce platform prerequisites — Connect API, in order

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
| Third | `EinsteinGPTCopilotEnabled` | Only after `AgentPlatformEnabled` verifies `true`. **Silent-failure mode:** PATCH succeeds but verify reads `false` when the `EinsteinGPTCopilot` org permission (Einstein Copilot add-on license) is missing — report as license-level blocker and **continue** (Manufacturing prefs do not depend on this). |

### 4. Enable the Manufacturing foundation preferences

**#4 — CriteriaBasedSearchAndFilterEnabled (Aura controller):**
Enable the CBSF org preference via the Aura controller headless route.

```text
# Write:
dispatch("PATCH", "/headless/invoke/platform/criteria-based-search-and-filter/set-criteria-based-search-and-filter-pref",
  body={"enable": true})

# Verify:
dispatch("GET", "/headless/invoke/platform/criteria-based-search-and-filter")
# → {"status": "SUCCESS", "isPrefEnabled": true}
```

**#5, #6 — AppraisalManagementEnabled, MfgPartnerLeadMgmtEnabled (Connect API):**
Continue with the same Connect API write-then-verify pattern from step 3:

| Order | Preference Name | Notes |
|---|---|---|
| First | `AppraisalManagementEnabled` | Master appraisal-management toggle. |
| Any | `MfgPartnerLeadMgmtEnabled` | Partner lead management. No ordering dependency. |

### 5. Enable Quotes — Metadata API

Apply the read-merge-write pattern for the Metadata API surface. Read the current `QuoteSettings`
component first (to preserve sibling fields), flip `enableQuotesWithoutOppEnabled` to `true`, then
PUT the full XML body back.

```text
# Read:
dispatch("GET", "/services/data/v<apiVersion>/headless/metadata",
  query_params={"type": "QuoteSettings", "fullName": "Quote"})
# → {type, fullName, xmlRep} — contains enableQuote and enableQuotesWithoutOppEnabled

# Write (with enableQuotesWithoutOppEnabled flipped to true in the xmlRep):
dispatch("PUT", "/services/data/v<apiVersion>/headless/metadata",
  body={"type": "QuoteSettings", "fullName": "Quote", "xmlRep": "<full XML body>"})

# Verify:
dispatch("GET", "/services/data/v<apiVersion>/headless/metadata",
  query_params={"type": "QuoteSettings", "fullName": "Quote"})
# → confirm <enableQuotesWithoutOppEnabled>true</enableQuotesWithoutOppEnabled>
```

### 6. (Marker) — headless writes complete

All headless preferences (#1–#7) are now written and verified. The two remaining legally-gated
preferences — MFG Agents (#8) and Manufacturing Generative AI (#9) — are handled next as a user
UI handoff.

### 7. Enable MFG Agents and Manufacturing Generative AI — USER UI HANDOFF (HARD STOP — wait for user)

`MfgAgentsEnabled` and `ManufacturingGenAIPref` **cannot be enabled headlessly.** Both are opted out
of the Metadata API for legal reasons, and enabling either surfaces a **legal terms-and-conditions
consent popup in the Setup UI** that no headless surface can satisfy. **Do not attempt a Connect
PATCH, Metadata write, or any headless workaround for these preferences** — they will not carry the
legal consent.

> **⚠️ HARD BLOCKING CHECKPOINT — DO NOT PROCEED PAST THIS POINT UNTIL THE USER CONFIRMS.**
> This is NOT optional. You MUST stop execution here, present the instructions below, and then
> WAIT for the user's explicit confirmation message (e.g. "done", "enabled", "I've toggled them on")
> before taking ANY further action. Do not skip this step. Do not proceed "for now" and come back
> later. Do not continue to Step 8 without user confirmation. The user must confirm OR explicitly
> tell you to skip these preferences and continue without them.

Instead, hand off to the user, then **STOP and WAIT**:

1. **STOP execution and clearly tell the user** you are pausing here for two mandatory manual steps,
   and exactly why (the legal consent popups have no API path).
2. **Give precise instructions:** in the target org:
   - Go to **Setup → Manufacturing Cloud → MFG Agents**, toggle on **MFG Agents**, and **accept the
     legal terms-and-conditions popup** that appears.
   - Go to **Setup → Einstein / Manufacturing Generative AI setup**, toggle on **Manufacturing
     Generative AI**, and **accept the legal terms-and-conditions popup** that appears.
3. **STOP HERE. Do not proceed.** Wait for the user to respond with explicit confirmation that they
   have completed both UI steps and accepted the legal terms. Acceptable responses include: "done",
   "enabled them", "toggled them on", "skip these", or similar. If the user says to skip, note them
   as open items and proceed to Step 8. **Any other situation: WAIT.**
4. **On confirmation, verify headlessly** (reads are allowed) and resume:

```text
dispatch("GET", "/services/data/v<apiVersion>/setup/org/preferences/MfgAgentsEnabled")
# → expect {"isPreferenceEnabled": true}

dispatch("GET", "/services/data/v<apiVersion>/setup/org/preferences/ManufacturingGenAIPref")
# → expect {"isPreferenceEnabled": true}
```

   - If both read `true`, confirm to the user and continue to step 8.
   - If either still reads `false`, tell the user which toggle/consent didn't take, ask them to
     re-check the relevant Setup page and re-accept the popup, and re-verify. Offer to continue with
     the rest of the foundation and leave the failing preference(s) as open items if they prefer —
     the permission-set assignments in step 8 do not depend on them.

### 8. Assign the foundation permission sets (sObject REST, API-first)

Salesforce licensing for a feature is two calls — missing either one silently breaks things with no error:

1. **`PermissionSetLicenseAssign`** — consumes a seat from a `PermissionSetLicense` bucket (bookkeeping only, grants no access by itself).
2. **`PermissionSetAssignment`** — assigns the actual `PermissionSet` (the CRUD/FLS/user-permission grants) to the user. **This is the call that actually grants access.**

Assign **both** the PSL and its paired PermissionSet for each feature below. A `DUPLICATE_VALUE` on
either write means it is already assigned — treat as success and continue.

**8a. Verify PSL presence (resolve by exact DeveloperName).**

```text
dispatch("GET", "/services/data/v<apiVersion>/query", query_params={
  "q": "SELECT Id, DeveloperName, MasterLabel FROM PermissionSetLicense WHERE DeveloperName IN ('EinsteinGPTCopilotPsl','EinsteinGPTPromptTemplatesPsl','ManufacturingFoundationUserPsl','CriteriaBasedSearchAndFilterPsl','ManufacturingPartnerLeadMgmtPsl','IndustriesServiceExcellencePsl')"
})
```

PSL → capability map (verified against a live Manufacturing Cloud central org, 2026-08-21):

| # | PSL DeveloperName | Label | Capability it gates |
|---|---|---|---|
| 1 | `EinsteinGPTCopilotPsl` | Agentforce (Default) | Agentforce agent runtime — backs CopilotSalesforceUser + CopilotSalesforceAdmin |
| 2 | `EinsteinGPTPromptTemplatesPsl` | Einstein Prompt Templates | Prompt template invocation |
| 3 | `ManufacturingFoundationUserPsl` | Manufacturing Foundation User | Base Manufacturing objects |
| 4 | `CriteriaBasedSearchAndFilterPsl` | Criteria-Based Search and Filter | CBSF objects |
| 5 | `ManufacturingPartnerLeadMgmtPsl` | Partner Lead Management | Partner lead management |
| 6 | `IndustriesServiceExcellencePsl` | Industry Service Excellence | Industries base |

Any PSL not found in the org means the license is not provisioned — report it as the likely cause of
a related preference staying off; it needs a license/entitlement grant (out of headless scope).

**8b. Assign PSL seats** — for each PSL above, consume a seat:

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
  "q": "SELECT Id, Name, Label FROM PermissionSet WHERE Name IN ('CopilotSalesforceUser','CopilotSalesforceAdmin','EinsteinGPTPromptTemplateUser','ManufacturingFoundationUserPsl','CriteriaBasedSearchAndFilterPsl','ManufacturingPartnerLeadMgmtPsl','IndustriesServiceExcellence')"
})
```

PermissionSet → PSL map (verified against a live central org, 2026-08-21):

| # | PermissionSet Name | Label | Backing PSL |
|---|---|---|---|
| 1 | `CopilotSalesforceUser` | Access Agentforce Default Agent | EinsteinGPTCopilotPsl |
| 2 | `CopilotSalesforceAdmin` | Agentforce Default Admin | EinsteinGPTCopilotPsl |
| 3 | `EinsteinGPTPromptTemplateUser` | Prompt Template User | EinsteinGPTPromptTemplatesPsl |
| 4 | `ManufacturingFoundationUserPsl` | Manufacturing Foundation User | ManufacturingFoundationUserPsl |
| 5 | `CriteriaBasedSearchAndFilterPsl` | Criteria-Based Search and Filter | CriteriaBasedSearchAndFilterPsl |
| 6 | `ManufacturingPartnerLeadMgmtPsl` | Partner Lead Management | ManufacturingPartnerLeadMgmtPsl |
| 7 | `IndustriesServiceExcellence` | Industry Service Excellence | IndustriesServiceExcellencePsl |

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

A `DUPLICATE_VALUE` / already-assigned error is benign — treat as success and continue.

**8f. Verify the assignments landed** — read back BOTH PSL seats AND PermissionSets:

```text
dispatch("GET", "/services/data/v<apiVersion>/query", query_params={
  "q": "SELECT Id, PermissionSetLicenseId, PermissionSetLicense.DeveloperName FROM PermissionSetLicenseAssign WHERE AssigneeId = '<userId>'"
})
```

Confirm all 6 PSL seats from the table in 8a are assigned. Report any that are missing.

```text
dispatch("GET", "/services/data/v<apiVersion>/query", query_params={
  "q": "SELECT PermissionSetId, PermissionSet.Name FROM PermissionSetAssignment WHERE AssigneeId = '<userId>'"
})
```

Confirm all 7 PermissionSets from the table in 8c are present. Report any that are missing.

**Notes (from the live org):**
- Agent/Copilot access (`Einstein_Copilot_User` / `AgentForce_User`) is delivered by the Agentforce
  package, not this foundation — it belongs to a later Act. Do not block on it.
- Not every org has every permission set — assign the ones that resolve; report any that don't.

---

## Rules / Constraints

| Constraint | Rationale |
|---|---|
| `dispatch` only — no `sf` CLI, no `curl`, no browser | Hosted-MCP customers have no shell. |
| MFG Agents and GenAI are the two deliberate UI handoffs — HARD STOP | Both are legally opted out of every headless surface and require accepting consent popups; there is no API path. Pause, instruct, WAIT for user confirmation, verify, resume. |
| No hardcoded org IDs, instance URLs, tokens, user IDs, permission-set IDs, or API versions | Portable across orgs; resolve at runtime. |
| Enable Einstein GPT (#1) before Agent Platform (#2) before Copilot (#3) | Hard ordering dependency. |
| Verify after every write | A write can "succeed" while a gated field stays false. |
| The preference table is the source of truth | Enable ONLY the 9 preferences listed. Do NOT attempt additional preferences. |
| Stay inside setup scope | This is Act 0. Never create data, run pipelines, or deploy the agent. |

---

## Troubleshooting

### Connect API failures

| Symptom | Cause | Resolution |
|---|---|---|
| PATCH returns error | Preference gated behind a missing PSL | Verify PSLs in step 8a; report missing PSL. |
| Verify reads `false` after successful write | Silent-failure — underlying permission/license missing | Report the specific PSL blocker and continue. |
| 404 Not Found | Preference name incorrect or not registered on this org version | Verify the exact preference name from the table. |

### Aura controller failures (CBSF)

| Symptom | Cause | Resolution |
|---|---|---|
| PATCH returns error or 404 | Route not available on this org | Verify the headless invoke route exists; report the exact error. |
| Verify reads `isPrefEnabled: false` | Feature gated behind a missing PSL | Verify `CriteriaBasedSearchAndFilterPsl` is provisioned. |

### Metadata API failures (Quotes)

| Symptom | Cause | Resolution |
|---|---|---|
| `Invalid field` | Field name wrong for this API version | Re-check against table; if correct, feature is PSL-gated. |
| Write succeeds but verify shows field `false` | Preference gated behind a missing PSL | Report PSL blocker. |
| `INSUFFICIENT_ACCESS` | Connected user lacks Customize Application | Report; must use an admin. |

### MFG Agents + Generative AI preferences (UI handoff)

| Symptom | Cause | Resolution |
|---|---|---|
| User asks why these aren't automated | Legal consent popups; opted out of headless surfaces | Explain: enabling them requires accepting legal terms in the Setup UI, which no API can do. These are the two intended manual steps. |
| GET still `{"isPreferenceEnabled": false}` after the user says they enabled it | Toggle/consent didn't take | Ask the user to re-open the Setup page, re-toggle, and re-accept the popup; re-verify. Offer to continue and leave the failing preference as an open item. |

### Permission-set assignment failures

| Symptom | Cause | Headless fallback |
|---|---|---|
| POST → `DUPLICATE_VALUE` | User already has the set | Benign — treat as success, continue. |
| Query returns fewer sets than requested | Some sets not present in the org | Assign the ones that resolved; report the missing labels (package not installed). |
| PSL query returns fewer rows than expected | Not all PSLs provisioned | Report each missing PSL and the preference it blocks. |

If none of these resolves an issue, STOP and report the exact API response (status + body) — do not
fall back to a browser or manual Setup step (except the documented MFG Agents + GenAI handoffs).

---

## Output Expectations

Report, in order:
1. **Org & user** — the connected org, target user, and resolved API version.
2. **Per-preference results** — for each of the 9 preferences: skipped (already on), newly enabled
   (wrote + verified), or still off (name the blocker).
3. **Actions taken** — Connect API writes, Aura controller write, Metadata write, MFG Agents + GenAI
   handoff outcome, permission-set assignments.
4. **Gaps** — any preference still off and the blocker (PSL/license), and MFG Agents / GenAI if the
   user left them as open items.
5. **Next step** — the foundation is ready; hand back to the orchestrator for the next Act.

---

## Cross-Skill Integration

This skill is **Act 0** and is designed to be invoked by the **MFG Sales Concierge Foundation
Orchestrator** (its parent). It does the setup only; every downstream capability is a later Act the
orchestrator runs after this one succeeds.

| Need | Belongs to |
|---|---|
| Enable CBSF-specific data/config beyond the toggle | later Act — "cbsf enablement" |
| Run Data Pipelines (DPE) jobs | later Act — "dpe enablement" |
| Deploy the Agentforce agent metadata (GenAiAgent/topics/actions) | later Act — `create-mfg-sales-concierge-agent` |
| Create partner lead management data | later Act — partner lead configure |
| Create quote setup data | later Act — quote configure |
