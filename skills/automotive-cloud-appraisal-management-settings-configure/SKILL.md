---
name: automotive-cloud-appraisal-management-settings-configure
description: "Use this skill when users want to toggle two industry-cloud org preferences via the SetupApiFamily Connect API: parent AppraisalManagementEnabled and child AutomotiveComponentsForAppraisalMgmtEnabled. Trigger when users mention appraisal, management, settings, appraisal management settings."
metadata:
  version: "1.0"
---

# Managing Appraisal Management Settings

## When to Use This Skill

Toggle two industry-cloud org preferences via the SetupApiFamily Connect API: parent AppraisalManagementEnabled and child AutomotiveComponentsForAppraisalMgmtEnabled. Reads + writes are per-pref single-call. Child write is conventionally gated on parent=true AND Automotive Cloud enabled or orgHasAutomotiveDealerEssentials (LWC-rendered, server allows write regardless). Setup-node access requires Customize Application or System Administrator.

## Workflow

Read isOrgPreferenceEnabled_wire_3 (per-pref iteration over orgPreferences), then setOrgPreferences_1 (parent) and/or setOrgPreferences_2 (child) — independent server-side. Verify-* steps re-read via checkPreference. Child write conventionally requires parent=true + IndustriesAutomotive perm; server accepts regardless. 403 = caller lacks Customize Application.

## Critical Constraints

**Preconditions:**

- Org has the Appraisal Management access license/perm — gates the Setup node's visibility and accessibility. Without it the AppraisalManagementSettings page is not reachable. (check: `Appraisal Management access`)
- Caller has Customize Application permission or is a System Administrator. Derived from the manifest's Customize Application permission access predicate; unauthorized callers get 403 from checkPreference and updatePreference on this Setup family. (check: `Customize Application permission`)
- Conditional on the child setOrgPreferences_2 step: org has Automotive Cloud enabled or Automotive Dealer Essentials access. The LWC hides the child toggle without one of these (appraisalManagementPref.js line 51); the Connect endpoint itself accepts the write regardless, but persisting the child pref while the parent feature lacks Automotive coverage is unconventional and may have no UI surface. (check: `Automotive Cloud enabled OR Automotive Dealer Essentials access`)
- Conditional on the child setOrgPreferences_2 step: parent AppraisalManagementEnabled is already true. The LWC only renders the child toggle when the parent pref reads back true (showAutoComponentsChildPrefComp gate, appraisalManagementPref.js line 51).

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `isOrgPreferenceEnabled_wire_3` | read | — | `/services/data/v66.0/setup/org/preferences/{preferenceName}` | — |
| `setOrgPreferences_1` | write | — | `/services/data/v66.0/setup/org/preferences/{preferenceName}` | `isOrgPreferenceEnabled_wire_3` |
| `setOrgPreferences_2` | write | — | `/services/data/v66.0/setup/org/preferences/{preferenceName}` | `isOrgPreferenceEnabled_wire_3`, `setOrgPreferences_1` |

### Read operations

#### `isOrgPreferenceEnabled_wire_3`

Calls checkPreference once per inputs.orgPreferences entry. Returns isPreferenceEnabled (boolean) per call; agent assembles a name->boolean map locally. 403 if caller lacks Customize Application; 404 on unknown preferenceName.

**Call:** `/services/data/v66.0/setup/org/preferences/{preferenceName}`

**Output:** Per call: PreferenceCheckOutputRepresentation {isPreferenceEnabled: boolean} where true means the named org pref is enabled. The agent calls checkPreference once per entry in inputs.orgPreferences and assembles a name->boolean map locally.

### Write operations

#### `setOrgPreferences_1`

PATCH preferenceName=AppraisalManagementEnabled, body {desiredState: boolean}. Response echoes isPreferenceEnabled (in-line verify). Disabling parent hides child UI toggle but does not auto-disable it. 403 lacks Customize Application.

**Call:** `/services/data/v66.0/setup/org/preferences/{preferenceName}`

**Depends on:** `isOrgPreferenceEnabled_wire_3`

**Output:** PreferenceCheckOutputRepresentation with isPreferenceEnabled boolean — server echo of the post-write state. Agents can use this echo as an in-line verify, or re-read via the isOrgPreferenceEnabled_wire_3 step for an explicit confirmation.

#### `setOrgPreferences_2`

PATCH preferenceName=AutomotiveComponentsForAppraisalMgmtEnabled, body {desiredState: boolean}. Response echoes isPreferenceEnabled (in-line verify). Conventionally requires parent AppraisalManagementEnabled=true and Automotive Cloud/Dealer Essentials access; server accepts write regardless. 403 = caller lacks Customize Application.

**Call:** `/services/data/v66.0/setup/org/preferences/{preferenceName}`

**Depends on:** `isOrgPreferenceEnabled_wire_3`, `setOrgPreferences_1`

**Output:** PreferenceCheckOutputRepresentation with isPreferenceEnabled boolean — server echo of the post-write state. Verified working: PATCH returns 200 with {isPreferenceEnabled: true/false} regardless of Automotive license state.
