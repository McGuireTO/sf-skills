---
name: industries-custom-object-settings-configure
description: "Use this skill when users want to manage two Compliant Data Sharing rules for deleting a custom object's sharing permission: `CdsDeleteCOPEditOnParentPref` (require Edit access on the parent record before the permission can be deleted) and `CdsDeleteCOPByParentOwnerPref` (let the parent record's owner delete it). Trigger when users mention custom, object, settings, custom object settings."
metadata:
  version: "1.0"
  accessCheck: "IndustriesCompliantDataSharing.userHasIndustriesConfigCompliantDataSharing && (UserPermissions.CustomizeApplication || UserPermissions.ModifyAllData)"
---

# Managing Custom Object Settings

## When to Use This Skill

Manage two Compliant Data Sharing rules for deleting a custom object's sharing permission: `CdsDeleteCOPEditOnParentPref` (require Edit access on the parent record before the permission can be deleted) and `CdsDeleteCOPByParentOwnerPref` (let the parent record's owner delete it). Reads the current values and toggles either one. Setup administrator access required.

## Workflow

Read the current settings first, then toggle.

### Phase 1: Call getAccessCheckValues_1 to read the current state. It...

Call getAccessCheckValues_1 to read the current state. It returns three flags: `CdsDeleteCOPEditOnParentPref` and `CdsDeleteCOPByParentOwnerPref` (the current on/off state of each deletion rule) and `OrgHasCDSCustomObjects` (whether Compliant Data Sharing is available in the org and support for custom objects is enabled).

### Phase 2: Prerequisite — Compliant Data Sharing support for custom...

Prerequisite — Compliant Data Sharing support for custom objects must be enabled before these settings can be saved. Check `OrgHasCDSCustomObjects` from step 1. If it is false, custom-object support is not enabled: an admin must first enable it on the Object Enablement Settings page by turning on the Custom Object entry. (Programmatically, that is the ObjectEnablementSettings skill — call updateEntityPreference with parentEntityName "Custom Object" and isEnabled true.) Until that is done, savePref_2 is rejected.

### Phase 3: When OrgHasCDSCustomObjects is true, call savePref_2 with pref...

When `OrgHasCDSCustomObjects` is true, call savePref_2 with `pref` set to one of the two rule names above and `enabled` set to the desired on/off value. Any other `pref` name is rejected.

### Phase 4: Call verify-savePref_2 to confirm the change took effect...

Call verify-savePref_2 to confirm the change took effect — savePref returns no body, so re-reading is the only confirmation.

## Critical Constraints

**Preconditions:**

- You must have Setup administrator access. Without it, the settings are not returned and cannot be saved. (check: `Setup administrator access`)
- Your org must have access to configure Compliant Data Sharing. (check: `Compliant Data Sharing configuration access`)
- Saving a setting additionally requires Compliant Data Sharing support for custom objects to be enabled. Enable it on the Object Enablement Settings page by turning on the Custom Object entry — the read step's `OrgHasCDSCustomObjects` flag tells you whether this is already satisfied. (check: `Compliant Data Sharing support for custom objects enabled`)

## Verification Checklist

After every write operation, confirm the effect by re-reading state:

- After `savePref_2`: call `verify-savePref_2` (`GET /headless/invoke/industries/industries-compliant-datasharing/custom-object-settings/get-access-check-values`)

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `getAccessCheckValues_1` | read | implemented | `GET /headless/invoke/industries/industries-compliant-datasharing/custom-object-settings/get-access-check-values` | — |
| `savePref_2` | write | implemented | `PATCH /headless/invoke/industries/industries-compliant-datasharing/custom-object-settings/save-pref` | `getAccessCheckValues_1` |
| `verify-savePref_2` | verify | implemented | `GET /headless/invoke/industries/industries-compliant-datasharing/custom-object-settings/get-access-check-values` | `savePref_2` |

### Read operations

#### `getAccessCheckValues_1`

Reads the current Compliant Data Sharing custom-object settings. Returns three flags keyed by name: `CdsDeleteCOPEditOnParentPref` and `CdsDeleteCOPByParentOwnerPref` (the current on/off state of each deletion rule) and `OrgHasCDSCustomObjects` (whether Compliant Data Sharing is available in the org and support for custom objects is enabled — this must be true before either rule can be saved). Compliant Data Sharing configuration access and Setup administrator access are required; a caller without the required access receives an access error instead of the flags.

**Call:** `GET /headless/invoke/industries/industries-compliant-datasharing/custom-object-settings/get-access-check-values`   — status: `implemented`

**Output:** Three boolean flags keyed by name: `CdsDeleteCOPEditOnParentPref`, `CdsDeleteCOPByParentOwnerPref`, and `OrgHasCDSCustomObjects`. Returns an access error when the caller lacks Compliant Data Sharing configuration access or Setup administrator access.

### Write operations

#### `savePref_2`

Saves one Compliant Data Sharing deletion rule. Set `pref` to either `CdsDeleteCOPEditOnParentPref` (require Edit access on the parent record before a custom object's sharing permission can be deleted) or `CdsDeleteCOPByParentOwnerPref` (allow the parent record's owner to delete the sharing permission) — no other value is accepted. Set `enabled` to the desired on/off value. Saving requires Compliant Data Sharing configuration access and Setup administrator access, and the org must have Compliant Data Sharing support for custom objects enabled (see `OrgHasCDSCustomObjects` from the read step; enable the Custom Object entry on the Object Enablement Settings page if it is false). Returns no body; use the verify step to confirm.

**Call:** `PATCH /headless/invoke/industries/industries-compliant-datasharing/custom-object-settings/save-pref`   — status: `implemented`

**Inputs:**

- `pref` *(`String`)*
- `enabled` *(`boolean`)*

**Depends on:** `getAccessCheckValues_1`

### Verify operations

#### `verify-savePref_2`

Re-reads the settings and confirms the flag matching the `pref` you saved now equals the `enabled` value you sent. Because saving returns no body, this read-back is the only way to confirm the change persisted.

**Call:** `GET /headless/invoke/industries/industries-compliant-datasharing/custom-object-settings/get-access-check-values`   — status: `implemented`

**Depends on:** `savePref_2`
