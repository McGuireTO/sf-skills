---
name: automotive-cloud-dealer-essentials-configure
description: "Use this skill when users want to toggle two Automotive org preferences via SetupMetadata batch ops: `DealerEssentialsForAutomotiveEnabled` (master) and `IndustriesAutomotiveSchedulerEnabled` (subordinate). Trigger when users mention dealer, essentials, automotive, settings, dealer essentials for automotive settings."
metadata:
  version: "1.0"
---

# Managing Dealer Essentials For Automotive Settings

## When to Use This Skill

Toggle two Automotive org preferences via SetupMetadata batch ops: `DealerEssentialsForAutomotiveEnabled` (master) and `IndustriesAutomotiveSchedulerEnabled` (subordinate). Read: `GET .../is-org-preference-enabled?orgPreferences=[...]` → `Map<String, Boolean>`. Write: `PATCH .../set-org-preference` body `{orgPreferences: {<api-name>: <bool>}}` (multi-pref atomic). Server-gated by View Setup; master/subordinate gating is UI-only — server permits the scheduler write regardless of master state.

## Critical Constraints

**Preconditions:**

- View Setup required — a class-level `View Setup permission` access guard gates both ops. (check: `View Setup permission`)
- Org must hold the Automotive Cloud / Industries Automotive license that exposes `DealerEssentialsForAutomotiveEnabled`; without it the prefs persist but feature surfaces stay dark.

## Verification Checklist

After every write operation, confirm the effect by re-reading state:

- After `setOrgPreferences_1`, `write-org-preference`: call `verify-is-org-preference-enabled` (`GET /headless/invoke/platform/setup/setup-metadata/is-org-preference-enabled`)

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `isOrgPreferenceEnabled_wire_3` | read | — | `checkPreference` | — |
| `setOrgPreferences_1` | write | — | `updatePreference` | `isOrgPreferenceEnabled_wire_3` |
| `write-org-preference` | write | — | `PATCH /headless/invoke/platform/setup/setup-metadata/set-org-preference` | `isOrgPreferenceEnabled_wire_3`, `setOrgPreferences_1` |
| `verify-is-org-preference-enabled` | verify | — | `GET /headless/invoke/platform/setup/setup-metadata/is-org-preference-enabled` | `setOrgPreferences_1`, `write-org-preference` |

### Read operations

#### `isOrgPreferenceEnabled_wire_3`

Batch-read both Automotive org preferences (`DealerEssentialsForAutomotiveEnabled`, `IndustriesAutomotiveSchedulerEnabled`) via SetupMetadata `isOrgPreferenceEnabled`. Returns `Map<String, Boolean>` keyed by api-name. Requires View Setup.

**Call:** `checkPreference`

**Output:** `Map<String, Boolean>` keyed by each requested org-preference api-name; value is the current enabled state under the SetupMetadata permission frame. Unknown api-names are silently omitted from the result map.

### Write operations

#### `setOrgPreferences_1`

Write `DealerEssentialsForAutomotiveEnabled` via SetupMetadata `setOrgPreference` (PATCH; void return). Body shape `{orgPreferences: {DealerEssentialsForAutomotiveEnabled: <bool>}}`. Endpoint accepts multiple prefs in one call. Requires View Setup.

**Call:** `updatePreference`

**Depends on:** `isOrgPreferenceEnabled_wire_3`

#### `write-org-preference`

Write `IndustriesAutomotiveSchedulerEnabled` via SetupMetadata `setOrgPreference` (PATCH; void). Body `{orgPreferences: {IndustriesAutomotiveSchedulerEnabled: <bool>}}`. Requires View Setup. No server-side master/subordinate gating.

**Call:** `PATCH /headless/invoke/platform/setup/setup-metadata/set-org-preference`

**Depends on:** `isOrgPreferenceEnabled_wire_3`, `setOrgPreferences_1`

### Verify operations

#### `verify-is-org-preference-enabled`

Read-back via SetupMetadata `isOrgPreferenceEnabled` to confirm the preceding writes took effect. Same endpoint as page-load read; one call covers both prefs.

**Call:** `GET /headless/invoke/platform/setup/setup-metadata/is-org-preference-enabled`

**Depends on:** `setOrgPreferences_1`, `write-org-preference`

**Output:** `Map<String, Boolean>` confirming each pref's persisted state matches the value just written.
