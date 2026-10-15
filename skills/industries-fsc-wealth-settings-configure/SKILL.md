---
name: industries-fsc-wealth-settings-configure
description: "Use this skill when users want to toggle FSC (Financial Services Cloud) Wealth Management org preferences and read the access-check map that gates the Setup page. Trigger when users mention fsc, wealth, settings, fsc wealth settings."
metadata:
  version: "1.0"
  accessCheck: "(WealthManagement.isAdminUser) || (WealthManagement.isAdminWithRBLUsingCalc)"
---

# Managing Fsc Wealth Settings

## When to Use This Skill

Toggle FSC (Financial Services Cloud) Wealth Management org preferences and read the access-check map that gates the Setup page. The controller accepts an 8-pref allowlist via the `pref` parameter — `RBLUsingCalc`, `RecordRollup`, `TransformRBLtoDPE`, `SlackForCib`, `IndustriesKycPref`, `TearSheetPref`, `IndustriesOnboarding`, `DigitalLendingReadOnly` — unknown names throw. Two write paths: `handle-pref-enable` is the generic toggle, gated on the FSC org permission for all prefs except `IndustriesKycPref` and `DigitalLendingReadOnly`; `handle-rblpref-enable` is enable-only and additionally runs the calc-engine RBL rule conversion as part of the toggle, returning per-rule conversion outcomes. `get-access-check-values` returns a 16-key map combining preferences, permissions, and the setup-admin flag — call it before a write to determine which prefs the current admin can mutate.

## Workflow

Workflow: (1) Call `get-access-check-values` first to read the access map — most write attempts fail without `IsFinancialServicesPermEnabled` (skipped only for `IndustriesKycPref`/`DigitalLendingReadOnly`). The map is necessary but NOT sufficient: a true permission key does not guarantee a write is accepted — `handle-rblpref-enable` is separately guarded by `isAdminWithRBLUsingCalc`, which is not exposed as its own map key, so `IsRBLUsingCalcPermEnabled:true` can still yield ACCESS_DENIED (verified against a live org). (2a) For non-RBL prefs, call `handle-pref-enable` with the canonical pref name + `value:true`. This path is effectively ENABLE-ONLY for org prefs: `value:true` returns 200 and flips the corresponding `Is*PrefEnabled` flag, but `value:false` returns CONTROLLER_ERROR (`There was an error enabling or disabling a setting: OrgPreferences.<Pref>`) — confirmed for TearSheetPref and IndustriesKycPref against a live org. Treat these toggles as one-way enablement; do not rely on this surface to turn a pref back off. (2b) For `RBLUsingCalc`, prefer `handle-rblpref-enable` — enable-only (`value=false` raises) and additionally converts existing RBL rules through the calc-engine, returning `result.totalRulesCount` + `result.failedRulesErrorMap` so the agent can surface conversion failures; requires the `isAdminWithRBLUsingCalc` guard (see caveat above). (3) Re-read `get-access-check-values` after a write to confirm the corresponding `Is*PrefEnabled` flag flipped (verify chains added below).

## Critical Constraints

**Preconditions:**

- User must have WealthManagement isAdminUser access (check: `Wealth Management admin access`)
- User must have WealthManagement isAdminWithRBLUsingCalc access (check: `Wealth Management admin access`)

## Verification Checklist

After every write operation, confirm the effect by re-reading state:

- After `handle-pref-enable`: call `verify-handle-pref-enable` (`GET /headless/invoke/platform/fsc-wealth-settings`)
- After `handle-rblpref-enable`: call `verify-handle-rblpref-enable` (`GET /headless/invoke/platform/fsc-wealth-settings`)

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `handle-pref-enable` | write | implemented | `PATCH /headless/invoke/platform/fsc-wealth-settings/handle-pref-enable` | — |
| `handle-rblpref-enable` | write | implemented | `PATCH /headless/invoke/platform/fsc-wealth-settings/handle-rblpref-enable` | — |
| `get-access-check-values` | read | implemented | `GET /headless/invoke/platform/fsc-wealth-settings` | — |
| `verify-handle-pref-enable` | verify | — | `GET /headless/invoke/platform/fsc-wealth-settings` | `handle-pref-enable` |
| `verify-handle-rblpref-enable` | verify | — | `GET /headless/invoke/platform/fsc-wealth-settings` | `handle-rblpref-enable` |

### Read operations

#### `get-access-check-values`

Read the 16-key access-check map driving FSC Wealth Setup gating. Returns a `Map<String, Boolean>` mixing org preferences (e.g. `IsRBLUsingCalcPreferenceEnabled`, `isTransformRBLtoDPEEnabled`, `isIndustriesKycPrefEnabled`, `isTearSheetPrefEnabled`, `isIndustriesOnboardingPrefEnabled`, `isReadOnlyRecordsEnabled`), org permissions (e.g. `IsFinancialServicesPermEnabled`, `IsRBLUsingCalcPermEnabled`, `isIndustriesKycPermEnabled`, `isTearSheetPermEnabled`, `isDigitalLendingEnabled`, `isDigitalLendingAdminUserPermEnabled`, `isIndustriesOnboardingEnabled`), and a `userHasAccess` setup-admin flag. Use this read to decide which prefs `handle-pref-enable` / `handle-rblpref-enable` can write — but note the map is NECESSARY-BUT-NOT-SUFFICIENT: a true permission key does not guarantee a write is accepted. Verified against a live org, `IsRBLUsingCalcPermEnabled:true` (with `userHasAccess:true` and `IsFinancialServicesPermEnabled:true`) still returned ACCESS_DENIED from `handle-rblpref-enable`, which is separately guarded by `isAdminWithRBLUsingCalc` — a capability this map does NOT expose as its own key. No public alternative aggregates preferences AND permissions AND setup-admin in one call — `setup.connect.api.checkPreference` only covers preferences, missing 8 of the 16 keys.

**Call:** `GET /headless/invoke/platform/fsc-wealth-settings`   — status: `implemented`

**Output:** Map<String, Boolean> with 16 keys: preferences (`IsRBLUsingCalcPreferenceEnabled`, `isTransformRBLtoDPEEnabled`, `isIndustriesKycPrefEnabled`, `isTearSheetPrefEnabled`, `isIndustriesOnboardingPrefEnabled`, `isReadOnlyRecordsEnabled`), permissions (`IsRBLUsingCalcPrefEnabled` reflecting ORG_HAS_RBLUSING_CALC_PREF, `IsRecordRollupPrefEnabled` reflecting ORG_HAS_RECORD_ROLLUP_PREF, `IsRBLUsingCalcPermEnabled`, `IsFinancialServicesPermEnabled`, `isIndustriesKycPermEnabled`, `isTearSheetPermEnabled`, `isIndustriesOnboardingEnabled`, `isDigitalLendingEnabled`, `isDigitalLendingAdminUserPermEnabled`), and one `userHasAccess` setup-admin flag computed.

### Write operations

#### `handle-pref-enable`

Toggle one of 8 allowlisted FSC Wealth prefs (`RBLUsingCalc`, `RecordRollup`, `TransformRBLtoDPE`, `SlackForCib`, `IndustriesKycPref`, `TearSheetPref`, `IndustriesOnboarding`, `DigitalLendingReadOnly`); unknown names raise IllegalStateException (surfaced on the wire as CONTROLLER_ERROR). For all prefs except `IndustriesKycPref` and `DigitalLendingReadOnly` the controller enforces `IndustriesFSCAccessCheck.ORG_HAS_FINANCIAL_SERVICES` server-side. `RBLUsingCalc` in a non-FSC org is routed through the settings `operation.modify().setBoolean(...)` instead of `permAndPrefUtil.setOrgPref`. `IndustriesKycPref` toggles emit FSC telemetry. No public Connect/Tooling/Metadata alternative reproduces the FSC feature gate, the RBLUsingCalc-without-FSC routing, or the telemetry side-effect — Aura controller is canonical. Verified against a live org: this path is effectively ENABLE-ONLY for org preferences — `value:true` returns HTTP 200 and the matching `Is*PrefEnabled` flag flips on read-back, but `value:false` returns CONTROLLER_ERROR (`There was an error enabling or disabling a setting: OrgPreferences.<Pref>`), confirmed for both `TearSheetPref` (FSC-gated) and `IndustriesKycPref` (not FSC-gated). Treat these toggles as one-way enablement; do not rely on this surface to turn a pref back off.

**Call:** `PATCH /headless/invoke/platform/fsc-wealth-settings/handle-pref-enable`   — status: `implemented`

**Inputs:**

- `pref` *(`String`)* — Value for the pref field.
- `value` *(`boolean`)* — Toggle the value preference on or off.

#### `handle-rblpref-enable`

Enable an RBL preference (typically `RBLUsingCalc`) and run the calc-engine RBL rule conversion as an atomic side-effect of the toggle. Enable-only: `value=false` raises IllegalStateException. Returns `RblRulesConversionOutputRepresentation` carrying `result.conversionStatus`, `result.totalRulesCount`, `result.failedRulesErrorMap` (per-rule errors), `result.packageNameSpace`, and `result.calcJobDefinitions`. The pref is only flipped on if at least one rule converts; conversion exception triggers an inline pref rollback. Gated by Wealth Management admin access. No public alternative reproduces the calc-engine conversion side-effect or the typed conversion-result return — Aura controller is canonical.

**Call:** `PATCH /headless/invoke/platform/fsc-wealth-settings/handle-rblpref-enable`   — status: `implemented`

**Inputs:**

- `pref` *(`String`)* — Value for the pref field.
- `value` *(`boolean`)* — Toggle the value preference on or off.

**Output:** RblRulesConversionOutputRepresentation. Carries `result.conversionStatus` (boolean — true when all eligible rules converted), `result.totalRulesCount` (int), `result.failedRulesErrorMap` (map of rule-id → error message for failed rules), `result.packageNameSpace` (string — managed-package namespace; empty for org-default), and `result.calcJobDefinitions` (map of CalcJobDefinition records keyed by job-definition name).

### Verify operations

#### `verify-handle-pref-enable`

Read back via `get-access-check-values` to confirm the just-written pref took effect. The access-check map exposes `IsRBLUsingCalcPreferenceEnabled` (for `RBLUsingCalc`), `isTransformRBLtoDPEEnabled`, `isIndustriesKycPrefEnabled`, `isTearSheetPrefEnabled`, `isIndustriesOnboardingPrefEnabled`, `isReadOnlyRecordsEnabled` — match the write's `pref` to the corresponding `Is*PrefEnabled` key. Note: `RecordRollup` and `SlackForCib` have no direct read-back key in this map; for those, no verify is available.

**Call:** `GET /headless/invoke/platform/fsc-wealth-settings`

**Depends on:** `handle-pref-enable`

#### `verify-handle-rblpref-enable`

Read back via `get-access-check-values` to confirm the RBL pref enable took effect. `IsRBLUsingCalcPreferenceEnabled` reflects `RBLUsingCalc`; `isTransformRBLtoDPEEnabled` reflects `TransformRBLtoDPE`. The verify confirms the pref state but does NOT re-validate calc-engine rule conversion — inspect the write's response (`result.failedRulesErrorMap`, `result.totalRulesCount`) for that.

**Call:** `GET /headless/invoke/platform/fsc-wealth-settings`

**Depends on:** `handle-rblpref-enable`
