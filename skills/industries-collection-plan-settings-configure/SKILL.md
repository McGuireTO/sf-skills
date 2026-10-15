---
name: industries-collection-plan-settings-configure
description: "Use this skill when users want to configure org-level FSC Collection Plan preferences and the Promise-to-Pay (PTP) count. Trigger when users mention collection, plan, settings, collection plan settings."
metadata:
  version: "1.0"
  accessCheck: "IndustriesCollectionAccessCheck.ORG_HAS_COLLECTION"
---

# Managing Collection Plan Settings

## When to Use This Skill

Configure org-level FSC Collection Plan preferences and the Promise-to-Pay (PTP) count. Toggles one of six Collection preferences by exact string id: CollectionContactCardPref, CollectionTimeline, CollectionRiskScoringCFE, CollectionDbBasedOps, CollectionAsaAgentPref, CollDialerCampaignPref; passing an unrecognized id is rejected. PTP writes (save-promise-count, save-promise-count-with-change-info) set the org-wide Promise-to-Pay count setting; the with-change-info variant returns {success, isChanged} for the confirmation-modal flow. Reads: get-access-check-values (six per-preference enablement booleans + userHasAccess / userHasCPAgentAccess / userHasCPASAAgentAccess role gates), get-ptp-value (current count, 0 when unset), can-enable-collections-agent-data-cloud-pref (composite probe — true only when CDP/Genie is provisioned AND five DMOs exist; required before turning on CollectionAsaAgentPref). All ops are gated by setup-admin access and the org's FSC Collections-feature provisioning check.

## Workflow

Read-then-write. Call get-access-check-values first to confirm userHasAccess and current Is*Enabled state. Before enabling CollectionAsaAgentPref, call can-enable-collections-agent-data-cloud-pref and require brwrCntctPref:true. After every write, run the corresponding verify step.

## Critical Constraints

**Preconditions:**

- User must have IndustriesCollection AccessToCollectionIsAdmin access (admin Customize Application). (check: `Collections admin access`)
- Org must have the FSC Collections feature provisioned. Each write is rejected when the caller is not a setup admin or the Collections feature isn't provisioned. (check: `the org's FSC Collections-feature provisioning check`)
- Before calling handle-pref-enable with pref=CollectionAsaAgentPref and value=true, call can-enable-collections-agent-data-cloud-pref and require brwrCntctPref=true (CDP or Genie provisioned AND all 5 DMOs resolve). Verified live against a test org during factory-review: handlePrefEnable does NOT enforce this gate server-side — it accepts and persists the toggle even when brwrCntctPref is false. This precondition is UI-only; an agent MUST check it before writing this specific pref. (check: `Data Cloud eligibility before enabling CollectionAsaAgentPref`)

## Verification Checklist

After every write operation, confirm the effect by re-reading state:

- After `save-promise-count`: call `verify-save-promise-count` (`GET /headless/invoke/platform/collection-plan-settings/get-ptpvalue`)
- After `save-promise-count-with-change-info`: call `verify-save-promise-count-with-change-info` (`GET /headless/invoke/platform/collection-plan-settings/get-ptpvalue`)

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `handle-pref-enable` | write | implemented | `PATCH /headless/invoke/platform/collection-plan-settings/handle-pref-enable` | — |
| `get-access-check-values` | read | implemented | `GET /headless/invoke/platform/collection-plan-settings` | — |
| `save-promise-count-with-change-info` | write | implemented | `PATCH /headless/invoke/platform/collection-plan-settings/save-promise-count-with-change-info` | — |
| `save-promise-count` | write | implemented | `PATCH /headless/invoke/platform/collection-plan-settings/save-promise-count` | — |
| `can-enable-collections-agent-data-cloud-pref` | read | implemented | `GET /headless/invoke/platform/collection-plan-settings/can-enable-collections-agent-data-cloud-pref` | — |
| `get-ptp-value` | read | implemented | `GET /headless/invoke/platform/collection-plan-settings/get-ptpvalue` | — |
| `verify-save-promise-count` | verify | implemented | `GET /headless/invoke/platform/collection-plan-settings/get-ptpvalue` | `save-promise-count` |
| `verify-save-promise-count-with-change-info` | verify | implemented | `GET /headless/invoke/platform/collection-plan-settings/get-ptpvalue` | `save-promise-count-with-change-info` |

### Read operations

#### `get-access-check-values`

Read six Is*Enabled pref flags (IsCollectionTimelineEnabled, IsCollectionRiskScoringCFEEnabled, IsCollectionDbBasedOpsEnabled, IsCollectionASAAgentEnabled, IsCollectionDialerCampaignEnabled, IsCollectionPersonAccountControlPrefEnabled) plus userHasAccess / userHasCPAgentAccess / userHasCPASAAgentAccess role gates for Setup-page toggle visibility. Aura is canonical — no public alternative.

**Call:** `GET /headless/invoke/platform/collection-plan-settings`   — status: `implemented`

**Output:** Map<String,Boolean> with 9 keys: 6 per-preference enablement booleans (one per Collection preference toggle) plus three role-gate booleans — userHasAccess (setup admin with Collections provisioned), userHasCPAgentAccess (setup admin with Collections-agent access provisioned), userHasCPASAAgentAccess (userHasAccess plus universal credit metering enabled).

#### `can-enable-collections-agent-data-cloud-pref`

Probe Data Cloud eligibility for CollectionAsaAgentPref. Returns {brwrCntctPref:<bool>}; true iff (CDP OR Genie) provisioned AND all five DMOs resolve (UnifiedLinkssotIndividualColl, Individual, ContactPointAddress, ContactPointEmail, ContactPointPhone). Required before enabling the pref. Aura is canonical — no public alternative.

**Call:** `GET /headless/invoke/platform/collection-plan-settings/can-enable-collections-agent-data-cloud-pref`   — status: `implemented`

**Output:** Map<String,Boolean> with single key brwrCntctPref. true when (CDP OR Genie Platform) provisioned AND all 5 DMOs (UnifiedLinkssotIndividualColl__dlm, Individual, ContactPointAddress, ContactPointEmail, ContactPointPhone) resolve via namespace-aware lookup. Drives the dCAccessForCollAgent UI gate.

#### `get-ptp-value`

Read the current org-wide Promise-to-Pay count setting; returns Integer, 0 when the value is unset. Aura is canonical — no Tooling/Metadata surface for this setting.

**Call:** `GET /headless/invoke/platform/collection-plan-settings/get-ptpvalue`   — status: `implemented`

**Output:** Integer — current org-wide Promise-to-Pay count setting. Returns 0 when no value has been set.

### Write operations

#### `handle-pref-enable`

Toggle one of six org prefs by exact id (CollectionContactCardPref, CollectionTimeline, CollectionRiskScoringCFE, CollectionDbBasedOps, CollectionAsaAgentPref, CollDialerCampaignPref); void return; AuraHandledException on save failure, IllegalStateException on unknown pref. Aura is canonical — no public alternative.

**Call:** `PATCH /headless/invoke/platform/collection-plan-settings/handle-pref-enable`   — status: `implemented`

**Inputs:**

- `pref` *(`String`)* — Value for the pref field.
- `value` *(`boolean`)* — Toggle the value preference on or off.

**Output:** Empty body on success (200, void). On save-failure, AuraHandledException carries the SaveResult error message.

#### `save-promise-count-with-change-info`

Write the org-wide Promise-to-Pay count setting from a positive-Integer string; returns {success:true, isChanged:<bool>} where isChanged=true iff value differs from prior. Drives the confirmation-modal flow. Aura is canonical — no public alternative.

**Call:** `PATCH /headless/invoke/platform/collection-plan-settings/save-promise-count-with-change-info`   — status: `implemented`

**Inputs:**

- `count` *(`String`)* — Value for the count field.

**Output:** Map<String,Object> {success: true on persist, isChanged: true when newValue differs from prior getPTPValue, false otherwise}. ServiceException on parse-error or non-positive value.

#### `save-promise-count`

Write the org-wide Promise-to-Pay count setting from a positive-Integer string; returns boolean success. No change-detection — prefer save-promise-count-with-change-info when the agent must distinguish noops from real updates. Aura is canonical — no public alternative.

**Call:** `PATCH /headless/invoke/platform/collection-plan-settings/save-promise-count`   — status: `implemented`

**Inputs:**

- `count` *(`String`)* — Value for the count field.

**Output:** boolean — true on successful persist of the org-wide Promise-to-Pay count setting. ServiceException on parse-error or non-positive value.

### Verify operations

#### `verify-save-promise-count`

Read back via getPTPValue; confirm the returned Integer equals the count just persisted by save-promise-count.

**Call:** `GET /headless/invoke/platform/collection-plan-settings/get-ptpvalue`   — status: `implemented`

**Depends on:** `save-promise-count`

#### `verify-save-promise-count-with-change-info`

Read back via getPTPValue; confirm the returned Integer equals the count just persisted by save-promise-count-with-change-info.

**Call:** `GET /headless/invoke/platform/collection-plan-settings/get-ptpvalue`   — status: `implemented`

**Depends on:** `save-promise-count-with-change-info`
