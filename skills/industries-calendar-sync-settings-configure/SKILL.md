---
name: industries-calendar-sync-settings-configure
description: "Use this skill when users want to read or set the Visit Calendar Sync org preference (VisitCalendarSyncEnabled) for Salesforce Industries Visit — the org flag that surfaces scheduled Visit records on user calendars. Trigger when users mention calendar, sync, settings, calendar sync settings."
metadata:
  version: "1.0"
---

# Querying Calendar Sync Settings

## When to Use This Skill

Read or set the Visit Calendar Sync org preference (VisitCalendarSyncEnabled) for
Salesforce Industries Visit — the org
flag that surfaces scheduled Visit records on user calendars. The read returns a
bare boolean; the toggle takes a `value` boolean.
NOT exposed on the generic Setup Connect API org-preferences endpoint. Caller
needs the View Setup and Configuration permission; the org must have Industries
Visit AND Visit Calendar enabled.

## Critical Constraints

**Preconditions:**

- Org must have Salesforce Industries Visit enabled (OrgPermissions.IndustriesVisit).
Without it the preference is not registered and the feature is unavailable. (check: `IndustriesVisit org permission`)
- Org must ALSO have the Visit Calendar feature enabled
(OrgPermissions.VisitCalendar). VisitCalendarSyncEnabled declares
required="OrgPermissions.IndustriesVisit,OrgPermissions.VisitCalendar" in
IndustriesVisitUdd.settings.xml — both org perms are needed. (check: `VisitCalendar org permission`)
- Caller must hold the View Setup and Configuration permission. Both operations
enforce it and return an access error otherwise. (check: `View Setup and Configuration`)

## Verification Checklist

After every write operation, confirm the effect by re-reading state:

- After `handleVisitCalendarSyncToggle_2`: call `verify-handleVisitCalendarSyncToggle_2` (`GET /headless/invoke/industries/industries-visit/visit-calendar-sync-settings/get-visit-calendar-sync-org-pref`)

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `getVisitCalendarSyncOrgPref_1` | read | implemented | `GET /headless/invoke/industries/industries-visit/visit-calendar-sync-settings/get-visit-calendar-sync-org-pref` | — |
| `handleVisitCalendarSyncToggle_2` | read | implemented | `PATCH /headless/invoke/industries/industries-visit/visit-calendar-sync-settings/handle-visit-calendar-sync-toggle` | `getVisitCalendarSyncOrgPref_1` |
| `verify-handleVisitCalendarSyncToggle_2` | verify | — | `GET /headless/invoke/industries/industries-visit/visit-calendar-sync-settings/get-visit-calendar-sync-org-pref` | `handleVisitCalendarSyncToggle_2` |

### Read operations

#### `getVisitCalendarSyncOrgPref_1`

Read the Visit Calendar Sync org preference (VisitCalendarSyncEnabled).
Returns a bare boolean (true when enabled). Requires the View Setup and
Configuration permission (access denied otherwise).

**Call:** `GET /headless/invoke/industries/industries-visit/visit-calendar-sync-settings/get-visit-calendar-sync-org-pref`   — status: `implemented`

**Output:** Bare boolean. true when the Visit Calendar Sync org preference
(VisitCalendarSyncEnabled) is enabled for the org, false otherwise. Not wrapped
— the Aura action returns the raw boolean (confirmed live: returnValue=false).

#### `handleVisitCalendarSyncToggle_2`

Enable or disable the Visit Calendar Sync org preference. Body param
`value` (boolean). Returns void on success; raises an error carrying the
save-failure message on write failure, or an access error when the caller
lacks the View Setup and Configuration permission.

**Call:** `PATCH /headless/invoke/industries/industries-visit/visit-calendar-sync-settings/handle-visit-calendar-sync-toggle`   — status: `implemented`

**Inputs:**

- `value` *(`boolean`)*

**Depends on:** `getVisitCalendarSyncOrgPref_1`

### Verify operations

#### `verify-handleVisitCalendarSyncToggle_2`

Re-read the Visit Calendar Sync org preference after the toggle; the returned
boolean should equal the `value` sent to handleVisitCalendarSyncToggle_2.

**Call:** `GET /headless/invoke/industries/industries-visit/visit-calendar-sync-settings/get-visit-calendar-sync-org-pref`

**Depends on:** `handleVisitCalendarSyncToggle_2`
