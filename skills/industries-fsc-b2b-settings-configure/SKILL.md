---
name: industries-fsc-b2b-settings-configure
description: "Use this skill when users want to read-and-toggle for FSC B2B + FSC Account Plan org preferences (Industries cloud). Trigger when users mention fscb2bsettings."
metadata:
  version: "1.0"
  accessCheck: "(IndustriesAccessCheck.ORG_HAS_B2B) || (setupUtil.isSetupAdmin)"
---

# Querying Fscb2 B Settings

## When to Use This Skill

Read-and-toggle for FSC B2B + FSC Account Plan org preferences (Industries cloud). Read returns a 4-key map {IsFSCB2BPrefEnabled, userHasAccess, isAccountPlanEnabled, isFSCAccountPlanPrefEnabled} where userHasAccess composes Setup-admin AND ORG_HAS_B2B. Write toggles exactly one of two prefs: FSCB2BPref or FSCAccountPlanEnabled; any other value raises IllegalStateException. Both methods require the View B2B Settings access guard.

## Workflow

Order: call getAccessCheckValues first to read the four-key access map, then gate any write on userHasAccess=true (composes Setup-admin AND ORG_HAS_B2B). handlePrefEnable toggles exactly ONE org preference per call: pref must be "FSCB2BPref" or "FSCAccountPlanEnabled" (case-sensitive) — any other value raises IllegalStateException; value is the boolean target state. Both methods require the View B2B Settings access guard and ORG_HAS_B2B feature; without them calls fail with NoAccessException regardless of user permission. Verified live against a live org: getAccessCheckValues returned the 4-key map and handlePrefEnable(FSCB2BPref) round-tripped the toggle (HTTP 200).

## Critical Constraints

**Preconditions:**

- Industries B2B feature must be enabled on the org (IndustriesAccessCheck.ORG_HAS_B2B). Enforced at runtime by validateAccess(); calls fail with NoAccessException when ORG_HAS_B2B is off, regardless of user permission. (check: `IndustriesAccessCheck.ORG_HAS_B2B`)
- Caller must be a Setup admin (setupUtil.isSetupAdmin()). validateAccess() throws NoAccessException when this fails. (check: `setupUtil.isSetupAdmin`)
- Caller must hold the View B2B Settings access access guard. Enforced declaratively by @ServiceComponentAccessGuard on both methods. (check: `View B2B Settings access`)

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `getAccessCheckValues_2` | read | implemented | `GET /headless/invoke/platform/fsc/assessment-settings/get-access-check-values` | — |
| `handlePrefEnable_1` | read | implemented | `PATCH /headless/invoke/platform/fsc/assessment-settings/handle-pref-enable` | `getAccessCheckValues_2` |

### Read operations

#### `getAccessCheckValues_2`

Read four access-check booleans gating the FSC B2B Settings page UI: IsFSCB2BPrefEnabled (ORG_HAS_B2BENABLED), userHasAccess (Setup-admin AND ORG_HAS_B2B), isAccountPlanEnabled (Account Plan enabled), isFSCAccountPlanPrefEnabled (ORG_HAS_FSCACCOUNT_PLAN_ENABLED). userHasAccess controls whether toggle UI is editable. No public Connect/Tooling/Metadata alternative — 4-key composed shape is value-add.

**Call:** `GET /headless/invoke/platform/fsc/assessment-settings/get-access-check-values`   — status: `implemented`

**Output:** Map<String,Boolean> with exactly four keys: IsFSCB2BPrefEnabled, userHasAccess, isAccountPlanEnabled, isFSCAccountPlanPrefEnabled. userHasAccess=true only when caller is Setup admin AND ORG_HAS_B2B is enabled; clients use it to gate edit controls.

#### `handlePrefEnable_1`

Toggle exactly one of two FSC org preferences. pref must be FSCB2BPref (writes ORG_PREFERENCE_FSCB2BPREF) or FSCAccountPlanEnabled (writes ORG_PREFERENCE_FSCACCOUNT_PLAN_ENABLED); any other value raises IllegalStateException. Save failure surfaces as AuraHandledException. Requires View B2B Settings access + Setup admin + ORG_HAS_B2B. No public Metadata API field for these prefs (IndustriesSettings WSDL omits them); Tooling OrganizationSettingsDetail substitution would drop the pref allowlist + access-guard composition (contract-fidelity gate).

**Call:** `PATCH /headless/invoke/platform/fsc/assessment-settings/handle-pref-enable`   — status: `implemented`

**Inputs:**

- `pref` *(`String`)*
- `value` *(`boolean`)*

**Depends on:** `getAccessCheckValues_2`

**Output:** Empty body on success (HTTP 200 indicates the named org preference was successfully written). Save failure surfaces as AuraHandledException with the SaveResult error message; pref outside {FSCB2BPref, FSCAccountPlanEnabled} raises IllegalStateException.
