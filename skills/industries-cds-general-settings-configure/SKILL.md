---
name: industries-cds-general-settings-configure
description: "Use this skill when users want to compliant Data Sharing (CDS) general settings: read or change the org-wide policy for what happens when a Salesforce user who holds CDS participant records, or belongs to a CDS participant group, is deactivated. Trigger when users mention cdsgeneral, settings, cdsgeneral settings."
metadata:
  version: "1.0"
---

# Managing Cds General Settings

## When to Use This Skill

Compliant Data Sharing (CDS) general settings: read or change the org-wide policy for what happens when a Salesforce user who holds CDS participant records, or belongs to a CDS participant group, is deactivated. Either block the user deactivation until that participant access is removed, or allow it and have the user's participant records deactivated automatically. This is the CDS user-offboarding policy; sibling CDS setup pages cover object enablement, participant roles, and participant groups.

## Workflow

This page exposes one org-wide preference plus a retry hook.

## Critical Constraints

**Preconditions:**

- Org has IndustriesCompliantDataSharing enabled (OrgPermissions.CompliantDataSharing). Parent gate for the entire CDS setup tree — without it the setup node is not visible. (check: `Compliant Data Sharing enabled`)
- Caller has UserPermissions.ConfigCompliantDataSharing + UserPermissions.ViewSetup, OR is sysadmin (CustomizeApplication + ModifyAllData). Per-method @ServiceComponentAccessGuard on every controller method. (check: `Compliant Data Sharing config access`)
- Class-level @ServiceComponentAccessGuard layered before per-method gate — userHasIndustriesConfigCompliantDataSharing AND (ViewSetup OR sysadmin). Applied on every method dispatched into this controller. (check: `Manage Object Enablement Settings`)
- Compliant Data Sharing must be enabled for at least one object (Setup > Compliant Data Sharing > Object Enablement Settings) before the user-deactivation preference has any effect. Without it the preference is still readable and writable, but no deactivation is ever refused, so a successful write changes nothing observable. (check: `Compliant Data Sharing enabled for at least one object`)
- The participant-group half of the deactivation block - refusing to deactivate a user because they belong to a participant group - additionally requires the Groups org permission. Without it, only participant records are checked. (check: `Groups org permission for participant-group checks`)
- Choosing SetParticipantRecordsToInactiveOnDeactivateUser requires the admin who later performs the user deactivation to hold EDIT field-level security on the IsActive field of every participant entity. Verified against a live org: this is granted by neither the System Administrator profile nor the FSC Sales permission set and must be added explicitly. Without it the deactivation is refused with "you don't have permission to update field IsActive of <entity>", which resembles the participant-record block but has a different cause and fix. (check: `Edit field-level security on participant IsActive`)

**Operational rules:**

- THE PREFERENCE has two values, and the option labels an admin sees in the UI are easy to misread, so rely on this description instead. PreventDeactivateUserWithParticipantRecords (the default) BLOCKS user deactivation: if the user holds any participant record, or belongs to any participant group, the deactivation is refused and the error points at the offending record or group. Nothing is deleted; the admin must remove the participant records and group memberships first, then deactivate. SetParticipantRecordsToInactiveOnDeactivateUser ALLOWS the deactivation and then deactivates that user's participant records automatically in an asynchronous follow-up job.
- INERT UNLESS ENABLED PER OBJECT. The blocking behavior only engages when Compliant Data Sharing is turned on for at least one object. On an org where no object has it enabled, this preference can be written and read back successfully while changing nothing observable. Do not report a successful write as a behavior change without confirming object enablement. The participant-group half of the block additionally requires the Groups org permission.
- ORDERING. Read the current value first; the read operation stands alone and does not require a prior write. Write, then read back to confirm the new value persisted.
- HUMAN GATE THE API SKIPS. In the UI, changing this preference raises an "Are you sure you want to change the user deactivation behavior?" confirmation that the admin must accept. That gate is client-side only, so an API write applies immediately with no confirmation. Surface the consequence to the user and get their intent before writing.
- WITHDRAWN OPERATION - DO NOT OFFER IT. The controller behind this page also exposes a bulk participant-record deactivation call, intended as the retry path for a failed asynchronous cleanup job. It is withdrawn and not callable here, because it fails with HTTP 500 on every invocation and the product's own admin retry link fails identically. Do not describe it as available, and do not offer to retry a failed cleanup from this page - there is currently no supported way to do that.
- ERROR CONTRACT. The preference write returns HTTP 500 for input that is permanently wrong rather than a 4xx: an unrecognised preference value surfaces as 500. Do not treat a 500 from this page as a transient fault worth retrying - read the message and correct the request instead. Some messages carry internal implementation text rather than admin-facing guidance, so relay their substance to the user rather than the raw string.

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `update-cds-participant-record-on-deactivate-user-org-value` | write | proposed | `PATCH /headless/invoke/platform/cdsgeneral-settings/update-cdsparticipant-record-on-deactivate-user-org-value` | — |
| `verify-update-cds-participant-record-on-deactivate-user-org-value` | read | proposed | `GET /headless/invoke/platform/cdsgeneral-settings/get-cdsparticipant-record-on-deactivate-user-org-value` | — |

### Read operations

#### `verify-update-cds-participant-record-on-deactivate-user-org-value`

Read the current org-wide user-deactivation behavior for Compliant Data Sharing participant records. Returns one of PreventDeactivateUserWithParticipantRecords (the default) or SetParticipantRecordsToInactiveOnDeactivateUser. Safe to call on its own as a baseline read before changing the setting, and again afterwards to confirm the new value persisted - it takes no inputs and has no prerequisite step.

**Call:** `GET /headless/invoke/platform/cdsgeneral-settings/get-cdsparticipant-record-on-deactivate-user-org-value`   — status: `proposed`

**Output:** The current value of the org-wide preference, as a string. Either PreventDeactivateUserWithParticipantRecords (the default - user deactivation is refused while the user holds participant records or belongs to a participant group) or SetParticipantRecordsToInactiveOnDeactivateUser (deactivation proceeds and the user's participant records are deactivated asynchronously).

### Write operations

#### `update-cds-participant-record-on-deactivate-user-org-value`

Set the org-wide user-deactivation behavior for Compliant Data Sharing participant records. Accepts PreventDeactivateUserWithParticipantRecords (refuse to deactivate a user who holds participant records or belongs to a participant group) or SetParticipantRecordsToInactiveOnDeactivateUser (allow the deactivation and deactivate that user's participant records via an asynchronous follow-up job). Echoes the saved value back. The setting takes effect only on orgs where Compliant Data Sharing is enabled for at least one object. In the UI this change is gated behind a confirmation dialog that this API call does not apply.

**Call:** `PATCH /headless/invoke/platform/cdsgeneral-settings/update-cdsparticipant-record-on-deactivate-user-org-value`   — status: `proposed`

**Inputs:**

- `selectedValue` *(`String`)* — Value for the selected value field.
