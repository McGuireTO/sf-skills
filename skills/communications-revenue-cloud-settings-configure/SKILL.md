---
name: communications-revenue-cloud-settings-configure
description: "Use this skill when users want to manage Revenue Cloud for Communications (Industries Communications Sales) org preferences. Trigger when users mention revenue, cloudfor, communications, settings, revenue cloudfor communications settings."
metadata:
  version: "1.0"
  accessCheck: "(OrgPermissions.CMEMultiRecipient && UserPermissions.CMESales) || (OrgPermissions.MultiRecipient || OrgPermissions.CMEMultiRecipient)"
---

# Managing Revenue Cloudfor Communications Settings

## When to Use This Skill

Manage Revenue Cloud for Communications (Industries Communications Sales) org preferences. Read returns Map<String,Boolean> with keys multiLocationEnabled / multiSubscriberEnabled, reflecting OrgPreferences.MultiLocationFeatureOrgPref and OrgPreferences.MultiSubscriberFeatureOrgPref. Two write operations flip those preferences independently. Access guarded by multi-recipient feature access (read + multi-location write) or userCanUseCMEFeatures (multi-subscriber write); admin caller needs Customize Application + the relevant org permission (MultiRecipient/CMEMultiRecipient/CMESales). No Connect/Tooling/Metadata alternative exists.

## Critical Constraints

**Preconditions:**

- Caller user must have Customize Application permission (admin permission required to edit org preferences via the UDD `editAccess`). (check: `Customize Application permission`)
- Org must have OrgPermissions.MultiRecipient or OrgPermissions.CMEMultiRecipient enabled — required for the read and Multi-Location write (UDD orgAccess) and gating for multi-recipient feature access. (check: `OrgPermissions.MultiRecipient || OrgPermissions.CMEMultiRecipient`)
- For Multi-Subscriber write only: org must have OrgPermissions.CMEMultiRecipient AND user must have UserPermissions.CMESales — gates Communications Media Enterprise features access access guard on setMultiSubscriberEnabled. (check: `OrgPermissions.CMEMultiRecipient && UserPermissions.CMESales`)

## Verification Checklist

After every write operation, confirm the effect by re-reading state:

- After `write-multi-location-enabled`, `write-multi-subscriber-enabled`: call `verify-comms-org-preferences` (`GET /headless/invoke/industries/industries-communications-sales/get-comms-org-preferences`)

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `getCommsOrgPreferences_1` | read | implemented | `GET /headless/invoke/industries/industries-communications-sales/get-comms-org-preferences` | — |
| `write-multi-location-enabled` | write | implemented | `PATCH /headless/invoke/industries/industries-communications-sales/set-multi-location-enabled` | — |
| `write-multi-subscriber-enabled` | write | implemented | `PATCH /headless/invoke/industries/industries-communications-sales/set-multi-subscriber-enabled` | — |
| `verify-comms-org-preferences` | verify | implemented | `GET /headless/invoke/industries/industries-communications-sales/get-comms-org-preferences` | `write-multi-location-enabled`, `write-multi-subscriber-enabled` |

### Read operations

#### `getCommsOrgPreferences_1`

Read the two Industries Communications Sales OrgPreferences. Returns Map<String,Boolean> with keys multiLocationEnabled (OrgPreferences.MultiLocationFeatureOrgPref) and multiSubscriberEnabled (OrgPreferences.MultiSubscriberFeatureOrgPref). Caller must satisfy multi-recipient feature access.

**Call:** `GET /headless/invoke/industries/industries-communications-sales/get-comms-org-preferences`   — status: `implemented`

**Output:** Map<String,Boolean> with two keys: multiLocationEnabled (mirrors OrgPreferences.MultiLocationFeatureOrgPref) and multiSubscriberEnabled (mirrors OrgPreferences.MultiSubscriberFeatureOrgPref).

### Write operations

#### `write-multi-location-enabled`

Set OrgPreferences.MultiLocationFeatureOrgPref to enable or disable Location-based quoting and ordering. Body: {value: boolean}. Returns true on success. Access guarded by multi-recipient feature access; requires OrgPermissions.MultiRecipient || OrgPermissions.CMEMultiRecipient + Customize Application permission.

**Call:** `PATCH /headless/invoke/industries/industries-communications-sales/set-multi-location-enabled`   — status: `implemented`

#### `write-multi-subscriber-enabled`

Set OrgPreferences.MultiSubscriberFeatureOrgPref to enable or disable Subscriber-based quoting and ordering. Body: {value: boolean}. Returns true on success. Access guarded by Communications Media Enterprise features access (the broader CME entitlement, distinct from the multi-recipient guard on read/multi-location-write); requires OrgPermissions.CMEMultiRecipient + UserPermissions.CMESales + Customize Application permission.

**Call:** `PATCH /headless/invoke/industries/industries-communications-sales/set-multi-subscriber-enabled`   — status: `implemented`

### Verify operations

#### `verify-comms-org-preferences`

Re-read getCommsOrgPreferences after write-multi-location-enabled and/or write-multi-subscriber-enabled. The returned multiLocationEnabled / multiSubscriberEnabled values reflect the just-written OrgPreferences and confirm the writes took effect.

**Call:** `GET /headless/invoke/industries/industries-communications-sales/get-comms-org-preferences`   — status: `implemented`

**Depends on:** `write-multi-location-enabled`, `write-multi-subscriber-enabled`
