---
name: industries-fsc-visa-fulfillment-setup-configure
description: "Use this skill when users want to enable Visa Resolve Online (VROL) integration for FSC dispute management (OrgPreferences.VROLIntegration). Trigger when users mention fsc, visa, fulfillment, setup, fsc visa fulfillment setup."
metadata:
  version: "1.0"
  accessCheck: "IndustriesDisputeManagement.userHasAccessToDisputeManagement"
---

# Managing Fsc Visa Fulfillment Setup

## When to Use This Skill

Enable Visa Resolve Online (VROL) integration for FSC dispute management
(OrgPreferences.VROLIntegration). Step 1 reads two booleans:
isVisaFulfillmentAccessible (Dispute Management feature license) and
isVisaFulfillmentEnabled (the org preference) — check accessible first.
Step 2 ENABLES the preference (enabled=true) and is refused unless the
caller is a Setup admin and the org has Dispute Management. Enabling is
ONE-WAY: it is irreversible and permanently locks after a UI confirmation
modal — disabling is not a supported capability (enabled=false is accepted
on the wire only as a constraint; see agent_guidance). Both ops are
aura-routed via /headless/invoke/industries/industries-dispute-management/visa-fulfillment-settings/*.
AURA-IS-CANONICAL: public Connect/Tooling preference paths drop the
feature-license gate and cannot reconstruct the accessibility flag;
Metadata API has no IndustriesDisputeManagementSettings type.

## Workflow

Enabling Visa Resolve Online (VROL) integration is a ONE-WAY operation. Once
OrgPreferences.VROLIntegration is set to true it is permanently locked: the Setup UI
disables the toggle after enable and there is no supported path to turn it back off.
Before enabling, the Setup UI presents a confirmation modal the admin must accept,
precisely because the action is irreversible — treat enabling as requiring deliberate,
confirmed intent, and surface that irreversibility to the user before proceeding.

Disabling is NOT a supported capability. Although the save endpoint technically accepts
enabled=false on the wire, that is a system constraint, not an available action: do not
present disabling to users as something this skill can do, and never call save with
enabled=false as a rollback — there is no rollback once the setting is enabled.

## Critical Constraints

**Preconditions:**

- (precondition) (check: `Dispute Management access`)

**Operational rules:**

- AURA-IS-CANONICAL: the public Connect setup.connect.api.{get,update}Preference and
Tooling OrgPreferenceSetting paths drop the Dispute Management feature-license gate
this Aura controller enforces, and the read DTO's isVisaFulfillmentAccessible flag
is not exposed as an org preference, so the two-key state cannot be reconstructed
from a generic preference read. The Aura controller remains canonical. Metadata API
has no IndustriesDisputeManagementSettings type.

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `getVisaFulfillmentSettings_1` | read | implemented | `GET /headless/invoke/industries/industries-dispute-management/visa-fulfillment-settings/get-visa-fulfillment-settings` | — |
| `saveVisaFulfillmentPreference_2` | write | implemented | `PATCH /headless/invoke/industries/industries-dispute-management/visa-fulfillment-settings/save-visa-fulfillment-preference` | `getVisaFulfillmentSettings_1` |

### Read operations

#### `getVisaFulfillmentSettings_1`

Reads two booleans for the org: isVisaFulfillmentAccessible (whether Dispute
Management is available) and isVisaFulfillmentEnabled (whether
OrgPreferences.VROLIntegration is on). Check accessible first — do not call
save when accessible is false; the write is refused without Dispute Management
access. AURA-IS-CANONICAL: a public Connect or Tooling org-preference read
returns only the enabled boolean; the accessibility flag is not an org
preference, so the two-key state cannot be reconstructed from a generic
preference read. Metadata API has no IndustriesDisputeManagementSettings type.

**Call:** `GET /headless/invoke/industries/industries-dispute-management/visa-fulfillment-settings/get-visa-fulfillment-settings`   — status: `implemented`

### Write operations

#### `saveVisaFulfillmentPreference_2`

Enables Visa Resolve Online integration by writing OrgPreferences.VROLIntegration=true.
This is a ONE-WAY, irreversible operation: the Setup UI shows a confirmation modal
before enabling and permanently locks the toggle afterward, so there is no supported
way to disable it once set. Disabling is NOT a capability of this step — although
the endpoint accepts enabled=false on the wire, treat that only as a system constraint:
never call it to roll back, and never present disable to users. Refused unless the
caller is a Setup admin and the org has Dispute Management. AURA-IS-CANONICAL: public
Connect and Tooling org-preference paths drop the explicit feature-license gate this
Aura controller enforces — contract-fidelity violation. Metadata API has no
IndustriesDisputeManagementSettings type.

**Call:** `PATCH /headless/invoke/industries/industries-dispute-management/visa-fulfillment-settings/save-visa-fulfillment-preference`   — status: `implemented`

**Inputs:**

- `enabled` *(`boolean`)*

**Depends on:** `getVisaFulfillmentSettings_1`
