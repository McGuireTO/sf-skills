---
name: industries-brokerage-settings-configure
description: "Use this skill when users want to single-toggle Setup page for the `InsBrokerageEnabled` org preference (master switch for Salesforce Insurance Brokerage Management). Trigger when users mention brokerage, settings, brokerage settings."
metadata:
  version: "1.0"
---

# Managing Brokerage Settings

## When to Use This Skill

Single-toggle Setup page for the `InsBrokerageEnabled` org preference (master switch for Salesforce Insurance Brokerage Management). Read state via `setup.connect.api.checkPreference` (GET); flip via `setup.connect.api.updatePreference` (PATCH, body `{desiredState: boolean}`); both keyed by path param `preferenceName=InsBrokerageEnabled`. Enabling seeds default brokerage commission/setup metadata records as a server-side side effect; the toggle is not intended to be flipped back to false once enabled. Preconditions: org has `OrgPermissions.InsuranceBrokerage` (or `InsuranceBrokeragePilot`); writer holds `CustomizeApplication && ModifyAllData` or sysadmin.

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `isOrgPreferenceEnabled_wire_2` | read | — | `checkPreference` | — |
| `setOrgPreferences_1` | write | — | `updatePreference` | `isOrgPreferenceEnabled_wire_2` |

### Read operations

#### `isOrgPreferenceEnabled_wire_2`

Wire adapter that checks whether the InsBrokerageEnabled org preference is currently enabled. The result populates the toggle's initial position on page load and is also re-evaluated after a write to confirm success or failure.

**Call:** `checkPreference`

### Write operations

#### `setOrgPreferences_1`

Flip the InsBrokerageEnabled org preference to the opposite of its current value. Invoked when the admin clicks the Brokerage Preferences toggle. After the write completes, the wire re-fires and the component compares old vs new values to determine success or failure.

**Call:** `updatePreference`

**Depends on:** `isOrgPreferenceEnabled_wire_2`
