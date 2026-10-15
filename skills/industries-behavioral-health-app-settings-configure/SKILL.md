---
name: industries-behavioral-health-app-settings-configure
description: "Use this skill when users want to read or toggle the org-level Behavioral Health App preference (ORG_PREFERENCE_BEHAVIORAL_HEALTH_APP_PREF) for Health Cloud — Setup > Platform Tools > Feature Settings > Health Cloud > Behavioral Health App Settings. Trigger when users mention behavioral, health, app, settings, behavioral health app settings."
metadata:
  version: "1.0"
  accessCheck: "(UngroupedSettingAccessCheck.USER_PERMISSION_VIEW_SETUP) && (UngroupedSettingAccessCheck.USER_PERMISSION_CUSTOMIZE_APPLICATION) && (IndustriesSettingAccessCheck.ORG_PERMISSION_BEHAVIORAL_HEALTH_APP)"
---

# Managing Behavioral Health App Settings

## When to Use This Skill

Read or toggle the org-level Behavioral Health App preference (ORG_PREFERENCE_BEHAVIORAL_HEALTH_APP_PREF) for Health Cloud — Setup > Platform Tools > Feature Settings > Health Cloud > Behavioral Health App Settings. Two operations on a single boolean: GET returns the current state, PATCH writes a new value. Both gated server-side by Customize Application + ViewSetup + the BehavioralHealthApp org permission (Health Cloud feature license); failure throws localized NoAccessException. Toggle additionally publishes a featurePref.enable / featurePref.disable PFT telemetry event for the Behavioral Health product feature taxonomy.

## Critical Constraints

**Preconditions:**

- Caller must hold the Customize Application user permission (UngroupedSettingAccessCheck.USER_PERMISSION_CUSTOMIZE_APPLICATION); Behavioral Health setup access requires it on both read and toggle, throwing AuraHandledException with localized 'Global_Setup.NoAccessException' otherwise. (check: `USER_PERMISSION_CUSTOMIZE_APPLICATION`)
- Org must have the BehavioralHealthApp org permission enabled (the Health Cloud feature license — StandardPermissionSet_force.BehavioralHealthApp); IndustriesSettingAccessCheck.ORG_PERMISSION_BEHAVIORAL_HEALTH_APP gates both methods. Without it the controller throws AuraHandledException; a Metadata API deploy of IndustriesSettings.enableBehavioralHealthAppPref also fails because the persistence layer enforces the same license. (check: `IndustriesSettingAccessCheck.ORG_PERMISSION_BEHAVIORAL_HEALTH_APP`)
- Caller must have View Setup access (setupUtil.hasViewSetup()); without it both controller methods throw AuraHandledException before any pref read or write. (check: `setupUtil.hasViewSetup`)

## Verification Checklist

After every write operation, confirm the effect by re-reading state:

- After `toggleBehavioralHealthAppOrgPref_2`: call `verifyBehavioralHealthAppOrgPref_3` (`GET /headless/invoke/platform/behavioral-health-app-settings`)

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `getBehavioralHealthAppOrgPref_1` | read | implemented | `GET /headless/invoke/platform/behavioral-health-app-settings` | — |
| `toggleBehavioralHealthAppOrgPref_2` | write | implemented | `PATCH /headless/invoke/platform/behavioral-health-app-settings/toggle-behavioral-health-app-org-pref` | `getBehavioralHealthAppOrgPref_1` |
| `verifyBehavioralHealthAppOrgPref_3` | verify | implemented | `GET /headless/invoke/platform/behavioral-health-app-settings` | `toggleBehavioralHealthAppOrgPref_2` |

### Read operations

#### `getBehavioralHealthAppOrgPref_1`

Reads ORG_PREFERENCE_BEHAVIORAL_HEALTH_APP_PREF. Gated by ViewSetup + Customize Application + BehavioralHealthApp org permission; denial throws AuraHandledException('Global_Setup.NoAccessException').

**Call:** `GET /headless/invoke/platform/behavioral-health-app-settings`   — status: `implemented`

### Write operations

#### `toggleBehavioralHealthAppOrgPref_2`

Writes ORG_PREFERENCE_BEHAVIORAL_HEALTH_APP_PREF; publishes featurePref.enable/disable PFT event for BEHAVIORAL_HEALTH_PRODUCT_FEATURE_ID. Same gate as read. SaveResult error → ServiceException. Returns void; re-call GET to read back.

**Call:** `PATCH /headless/invoke/platform/behavioral-health-app-settings/toggle-behavioral-health-app-org-pref`   — status: `implemented`

**Inputs:**

- `value` *(`boolean`)*

**Depends on:** `getBehavioralHealthAppOrgPref_1`

### Verify operations

#### `verifyBehavioralHealthAppOrgPref_3`

Read-back via getBehavioralHealthAppOrgPref to confirm toggleBehavioralHealthAppOrgPref_2 persisted. Returns boolean — the same ORG_PREFERENCE_BEHAVIORAL_HEALTH_APP_PREF the toggle wrote; it should equal the value passed to the toggle.

**Call:** `GET /headless/invoke/platform/behavioral-health-app-settings`   — status: `implemented`

**Depends on:** `toggleBehavioralHealthAppOrgPref_2`
