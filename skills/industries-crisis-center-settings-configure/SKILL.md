---
name: industries-crisis-center-settings-configure
description: "Use this skill when users want to read or toggle the Crisis Center org access preference for Health Cloud. Trigger when users mention crisis, center, settings, crisis center settings."
metadata:
  version: "1.0"
  accessCheck: "(IndustriesSettingAccessCheck.USER_PERMISSION_CRISIS_CENTER_USER_ACCESS) || (UngroupedSettingAccessCheck.USER_PERMISSION_CUSTOMIZE_APPLICATION) || (setupUtil.hasViewSetup)"
---

# Managing Crisis Center Settings

## When to Use This Skill

Read or toggle the Crisis Center org access preference for Health Cloud. Requires View Setup, Customize Application and the Crisis Center user permission, and the org must have the Crisis Center license. Enabling also publishes a product-usage telemetry event that no Metadata or Tooling write reproduces.

## Workflow

Read the current boolean, toggle it with the boolean `value`, then re-read to confirm, because the toggle returns no body. A localized no-access error means one of the four gates (View Setup, Customize Application, the Crisis Center user permission, the Crisis Center license) is off, not a bad payload.

## Critical Constraints

**Preconditions:**

- Org has the Health Cloud Crisis Center license enabled. Without it, both the read and the toggle return an access error. (check: `Crisis Center license`)
- Caller has View Setup access. (check: `setupUtil.hasViewSetup`)
- Caller has the Customize Application user permission. (check: `UngroupedSettingAccessCheck.USER_PERMISSION_CUSTOMIZE_APPLICATION`)
- Caller has the Crisis Center user permission. (check: `IndustriesSettingAccessCheck.USER_PERMISSION_CRISIS_CENTER_USER_ACCESS`)

## Verification Checklist

After every write operation, confirm the effect by re-reading state:

- After `handleCrisisCenterToggle_2`: call `verify-crisis-center-org-pref` (`GET /headless/invoke/industries/industries-healthcare/crisis-center-setup-page/get-crisis-center-org-pref`)

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `getCrisisCenterOrgPref_1` | read | implemented | `GET /headless/invoke/industries/industries-healthcare/crisis-center-setup-page/get-crisis-center-org-pref` | — |
| `handleCrisisCenterToggle_2` | write | implemented | `PATCH /headless/invoke/industries/industries-healthcare/crisis-center-setup-page/handle-crisis-center-toggle` | `getCrisisCenterOrgPref_1` |
| `verify-crisis-center-org-pref` | verify | implemented | `GET /headless/invoke/industries/industries-healthcare/crisis-center-setup-page/get-crisis-center-org-pref` | `handleCrisisCenterToggle_2` |

### Read operations

#### `getCrisisCenterOrgPref_1`

Returns whether the Crisis Center org access preference is enabled. Fails with a localized no-access error when the caller lacks View Setup, Customize Application or the Crisis Center user permission, or the org lacks the Crisis Center license.

**Call:** `GET /headless/invoke/industries/industries-healthcare/crisis-center-setup-page/get-crisis-center-org-pref`   — status: `implemented`

**Output:** Boolean; true when the Crisis Center org access preference is enabled.

**Notes:** verification_note: No public Connect, Tooling, Metadata or sObject API exposes this preference (live probes of the Setup Connect preference API and Tooling OrgPreferenceSettings both failed), so the controller read is the only surface.

### Write operations

#### `handleCrisisCenterToggle_2`

Sets the Crisis Center org access preference to the boolean `value`. Same access gate as the read; a failed save returns the first save error. When `value` is true the controller also publishes a product-usage telemetry event. Returns no body.

**Call:** `PATCH /headless/invoke/industries/industries-healthcare/crisis-center-setup-page/handle-crisis-center-toggle`   — status: `implemented`

**Inputs:**

- `value` *(`boolean`)*

**Depends on:** `getCrisisCenterOrgPref_1`

**Notes:** verification_note: The license gate, the Crisis Center user-permission gate and the enable-only telemetry event are controller-only behaviour; no Metadata, Tooling or sObject write reproduces them, so the controller toggle is the canonical write.

### Verify operations

#### `verify-crisis-center-org-pref`

Re-read the preference with getCrisisCenterOrgPref after handleCrisisCenterToggle; both read and write the same org preference, so the returned boolean must match the requested value.

**Call:** `GET /headless/invoke/industries/industries-healthcare/crisis-center-setup-page/get-crisis-center-org-pref`   — status: `implemented`

**Depends on:** `handleCrisisCenterToggle_2`

**Output:** Boolean equal to the value passed to handleCrisisCenterToggle on success.
