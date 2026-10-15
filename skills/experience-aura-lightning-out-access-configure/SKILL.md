---
name: experience-aura-lightning-out-access-configure
description: "Use this skill when users want to manage the AuraLightningOutAccess org preference, which gates whether Aura components can be served through Lightning Out (the cross-org embed surface for Aura). Trigger when users mention aura, lightning, out, access, aura lightning out access."
metadata:
  version: "1.0"
  accessCheck: "OrgPermissions.AuraLightningOutPermission"
---

# Managing Aura Lightning Out Access

## When to Use This Skill

Manage the AuraLightningOutAccess org preference, which gates whether Aura components can be served through Lightning Out (the cross-org embed surface for Aura). Two operations: read the current boolean state, then flip it on/off. The PATCH response echoes the new state, so the caller does not need a follow-up read to confirm persistence. Caller must hold the AuraLightningOutPermission org permission (UDD access check Lightning Out settings access).

## Workflow

Org-wide preference gating whether Aura components can be served through Lightning Out (the cross-org Aura embed surface). Canonical flow: read the current boolean via the GET step, then PATCH the desired value; the write response echoes the post-update isPreferenceEnabled, so no follow-up read is needed. Writes require the AuraLightningOutPermission org permission — without it the PATCH returns 401 INSUFFICIENT_ACCESS "Cannot update preference value!" (distinct from an OAuth/token failure, which differs by errorCode). Reads are ungated. Send desiredState as the boolean; an empty body returns 400 "Invalid desiredState passed!".

## Critical Constraints

**Preconditions:**

- Caller must hold the AuraLightningOutPermission org permission; the setup page's UDD access check userCanAccessAuraLightningOutSettings gates read/write of this preference. (check: `OrgPermissions.AuraLightningOutPermission`)

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `isOrgPreferenceEnabled_wire_2` | read | — | `checkPreference` | — |
| `setOrgPreferences_1` | write | — | `updatePreference` | `isOrgPreferenceEnabled_wire_2` |

### Read operations

#### `isOrgPreferenceEnabled_wire_2`

Read whether the AuraLightningOutAccess org preference is currently enabled. Response field isPreferenceEnabled is the boolean.

**Call:** `checkPreference`

**Output:** PreferenceCheckOutputRepresentation with one field: isPreferenceEnabled (boolean) — true when AuraLightningOutAccess is currently enabled for the org, false otherwise.

### Write operations

#### `setOrgPreferences_1`

Set the AuraLightningOutAccess org preference to the new boolean value. Response echoes the post-update isPreferenceEnabled, confirming persistence without an extra read.

**Call:** `updatePreference`

**Depends on:** `isOrgPreferenceEnabled_wire_2`

**Output:** PreferenceCheckOutputRepresentation echoing the new state: isPreferenceEnabled (boolean) is the value of AuraLightningOutAccess after the update — equals desiredState on success.

**Notes:** error_contracts: [{'status': 400, 'errorCode': 'BAD_REQUEST', 'message_pattern': 'Invalid desiredState passed!', 'when': 'Request body is empty or omits the desiredState field.', 'body_shape': '[{"errorCode":"BAD_REQUEST","message":"Invalid desiredState passed!"}]'}, {'status': 401, 'errorCode': 'INSUFFICIENT_ACCESS', 'message_pattern': 'Cannot update preference value!', 'when': 'Caller lacks the AuraLightningOutPermission org permission. Distinguish from an OAuth-token failure by the errorCode + message combination (a bad token would return AUTH_ERROR or 401 with a different message).', 'body_shape': '[{"errorCode":"INSUFFICIENT_ACCESS","message":"Cannot update preference value!"}]'}, {'status': 405, 'errorCode': 'METHOD_NOT_ALLOWED', 'when': 'A verb other than GET, HEAD, or PATCH is used against this path.', 'body_shape': '[{"errorCode":"METHOD_NOT_ALLOWED","message":"HTTP Method ... not allowed. Allowed are GET,HEAD,PATCH"}]'}]
