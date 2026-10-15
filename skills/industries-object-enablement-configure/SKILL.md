---
name: industries-object-enablement-configure
description: "Use this skill when users want to manage Financial Services Cloud Compliant Data Sharing at the object level. Trigger when users mention object, enablement, settings, object enablement settings."
metadata:
  version: "1.0"
  accessCheck: "IndustriesCompliantDataSharing.userCanManageObjectEnablementSettings"
---

# Managing Object Enablement Settings

## When to Use This Skill

Manage Financial Services Cloud Compliant Data Sharing at the object level.
See which objects support Compliant Data Sharing and whether it is turned on
for each, turn it on or off per object, and control whether external community
(site) users are allowed to be participants (an org-wide setting).

Two operations:
  - List the objects that support Compliant Data Sharing, with each object's
    current settings. Only objects returned here can be updated.
  - Update one object at a time: turn its Compliant Data Sharing on or off, or
    change whether external community users can be participants.

Good to know:
  - The two settings are linked. Turning on external community-user
    participation also turns on the object's Compliant Data Sharing if it
    isn't already on; turning off an object's Compliant Data Sharing also
    turns off external community-user participation.
  - Some changes are rejected. You can't turn off an object's Compliant Data
    Sharing while it still has participant roles, and you can't turn off
    external community-user participation while active community users are
    participants. The update response flags which rule blocked the change.
  - The update response reflects the object's settings after the change, so no
    separate read-back is needed.

Managing these settings requires permission to manage Object Enablement
Settings for Compliant Data Sharing.

## Workflow

Start by listing the objects and their current settings — this tells you which objects support Compliant Data Sharing and the current state of each. Only the objects returned here can be updated. To change a setting, call the update step with the object's parentEntityName from the list and the desired isEnabled value. By default this turns the object's Compliant Data Sharing on or off; to instead control whether external community (site) users can be participants, set isSiteUserParticipantsOrgPreference to true. The two settings are linked, so turning on external community-user participation also turns on the object's Compliant Data Sharing, and turning off an object's Compliant Data Sharing also turns off external community-user participation. The update response reflects the object's settings after the change, so you don't need to re-list to confirm. If a change is rejected, check the two flags on the response: one means the object still has participant roles (so its Compliant Data Sharing can't be turned off), the other means active community users are still participants (so external community-user participation can't be turned off).

## Critical Constraints

**Preconditions:**

- (precondition) (check: `Manage Object Enablement Settings`)

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `getEntityPreferences_1` | read | implemented | `GET /headless/invoke/industries/industries-compliant-datasharing/entity-pref-selector/get-entity-preferences` | — |
| `updateEntityPreference_2` | write | implemented | `PATCH /headless/invoke/industries/industries-compliant-datasharing/entity-pref-selector/update-entity-preference` | `getEntityPreferences_1` |

### Read operations

#### `getEntityPreferences_1`

List the objects that support Compliant Data Sharing, along with each object's current settings. Only objects returned here can be updated in the next step. Each item includes parentEntityName (the object's API name — pass this to the update step), parentEntityLabel (the object's label), and three current-state flags: isParticipantEntityOrgPreferenceEnabled (whether Compliant Data Sharing is on for the object), isSiteUserParticipantsOrgPreferenceEnabled (whether external community (site) users are allowed to be participants — an org-wide setting), and registrationSupportsSiteUsers (whether the object supports external community-user participants). Objects are sorted by label, and a generic "Custom Object" entry always appears last.

**Call:** `GET /headless/invoke/industries/industries-compliant-datasharing/entity-pref-selector/get-entity-preferences`   — status: `implemented`

**Output:** A list of the objects that support Compliant Data Sharing. Each item has: parentEntityName (string — the object's API name; pass to the update step), parentEntityLabel (string — the object's label), isParticipantEntityOrgPreferenceEnabled (boolean — whether Compliant Data Sharing is on for the object), isSiteUserParticipantsOrgPreferenceEnabled (boolean — whether external community-user participation is on org-wide), and registrationSupportsSiteUsers (boolean — whether the object supports external community-user participants; always false on the trailing "Custom Object" entry).

### Write operations

#### `updateEntityPreference_2`

Turn Compliant Data Sharing on or off for a single object, or change whether external community (site) users can be participants — one setting per call. Choose which setting to change with isSiteUserParticipantsOrgPreference: leave it false to change the object's Compliant Data Sharing (isEnabled), or set it true to change external community-user participation instead. The two settings are linked: turning on external community-user participation also turns on the object's Compliant Data Sharing if it isn't already on, and turning off an object's Compliant Data Sharing also turns off external community-user participation. Some changes can be rejected: you can't turn off an object's Compliant Data Sharing while it still has participant roles, and you can't turn off external community-user participation while active community users are participants. The response reports whether the change succeeded and reflects the object's updated setting.

**Call:** `PATCH /headless/invoke/industries/industries-compliant-datasharing/entity-pref-selector/update-entity-preference`   — status: `implemented`

**Inputs:**

- `parentEntityName` *(`String`)*
- `isEnabled` *(`boolean`)*
- `isSiteUserParticipantsOrgPreference` *(`boolean`)*

**Depends on:** `getEntityPreferences_1`

**Output:** Reports the result for the object. Always includes parentEntityName (the object you updated) and isSuccess. On success, updatedEntityPreference holds the object's settings after the change (same shape as an item from the list step), so no separate read-back is needed. On failure, two flags explain a rejected change: isParticipantEntityOrgPreferenceDisableValidationError is true when turning off Compliant Data Sharing was blocked because the object still has participant roles, and isSiteUserParticipantsOrgPreferenceDisableValidationError is true when turning off external community-user participation was blocked because active community users are still participants. If neither flag is set on a failure, the change wasn't allowed — for example the object doesn't support Compliant Data Sharing, or it doesn't support external community-user participants.
