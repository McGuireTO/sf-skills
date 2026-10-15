---
name: industries-clinical-data-model-settings-starter-configure
description: "Use this skill when users want to manages two Health Cloud org preferences via the Clinical Data Model Settings Starter setup page (HC-Starter license variant of sibling SOR ClinicalDataModelSettings): ORG_PREFERENCE_CLINICAL_DATA_MODEL (clinical data model) and ORG_PREFERENCE_ADVERSE_EVENTS (adverse event data m. Trigger when users mention clinical, data, model, settings, starter, clinical data model settings starter."
metadata:
  version: "1.0"
  accessCheck: "(HealthCloudAccessCheck.ORG_HAS_HEALTH_CLOUD || HealthCloudAccessCheck.ORG_HAS_HEALTH_CLOUD_STARTER) || (IndustriesLifeSciencesUddSettingAccessCheck.ORG_PERMISSION_ADVERSE_EVENTS)"
---

# Managing Clinical Data Model Settings Starter

## When to Use This Skill

Manages two Health Cloud org preferences via the Clinical Data Model Settings Starter setup page (HC-Starter license variant of sibling SOR ClinicalDataModelSettings): ORG_PREFERENCE_CLINICAL_DATA_MODEL (clinical data model) and ORG_PREFERENCE_ADVERSE_EVENTS (adverse event data model). All four operations route through /headless/invoke/platform/clinical-data-model-settings-starter/* — same backing endpoint as the non-Starter SOR; the URL prefix differentiates the setup-tree node. Reads return each pref's current boolean state; writes toggle each independently. Writes require an org licensed for Health Cloud OR Health Cloud Starter plus Customize Application/SysAdmin; the adverse-event toggle additionally requires the ORG_PERMISSION_ADVERSE_EVENTS feature flag. Enabling the clinical-data-model preference emits a LifeSciences telemetry event (CLINICAL_DM, clinicalDataModel.enabled).

## Workflow

Two independent prefs, no inter-pref ordering. To inspect: call get-clinical-data-model-org-pref and get-adverse-event-data-model-org-pref. To change either: call its handle-*-toggle write, then its verify read-back. License (HC|HC-Starter) + Customize Application/SysAdmin required for all writes; the adverse-event write additionally requires ORG_PERMISSION_ADVERSE_EVENTS.

## Critical Constraints

**Preconditions:**

- Caller must hold Customize Application OR System Administrator (Customize Application permission); required by both writes and the adverse-event read. (check: `Customize Application permission`)
- Org must be licensed for Health Cloud OR Health Cloud Starter; both writes throw NoAccessException via checkAccessAndThrowException when neither license is present. The non-Starter setup-page variant (ClinicalDataModelSettings) lives in a sibling SOR backed by the same controller. (check: `HealthCloudAccessCheck.ORG_HAS_HEALTH_CLOUD || HealthCloudAccessCheck.ORG_HAS_HEALTH_CLOUD_STARTER`)
- The Adverse Event Data Model toggle additionally requires the ORG_PERMISSION_ADVERSE_EVENTS feature flag enabled in the org (controller checkAdverseEventAccessAndThrowException). Does NOT affect the clinical-data-model toggle. (check: `IndustriesLifeSciencesUddSettingAccessCheck.ORG_PERMISSION_ADVERSE_EVENTS`)

## Verification Checklist

After every write operation, confirm the effect by re-reading state:

- After `handle-clinical-data-model-pref-toggle`: call `verify-handle-clinical-data-model-pref-toggle` (`GET /headless/invoke/platform/clinical-data-model-settings-starter`)
- After `handle-adverse-model-pref-toggle`: call `verify-handle-adverse-model-pref-toggle` (`GET /headless/invoke/platform/clinical-data-model-settings-starter/get-adverse-event-data-model-org-pref`)

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `get-clinical-data-model-org-pref` | read | proposed | `GET /headless/invoke/platform/clinical-data-model-settings-starter` | — |
| `get-adverse-event-data-model-org-pref` | read | proposed | `GET /headless/invoke/platform/clinical-data-model-settings-starter/get-adverse-event-data-model-org-pref` | — |
| `handle-clinical-data-model-pref-toggle` | write | proposed | `PATCH /headless/invoke/platform/clinical-data-model-settings-starter/handle-clinical-data-model-pref-toggle` | — |
| `verify-handle-clinical-data-model-pref-toggle` | verify | — | `GET /headless/invoke/platform/clinical-data-model-settings-starter` | `handle-clinical-data-model-pref-toggle` |
| `handle-adverse-model-pref-toggle` | write | proposed | `PATCH /headless/invoke/platform/clinical-data-model-settings-starter/handle-adverse-model-pref-toggle` | — |
| `verify-handle-adverse-model-pref-toggle` | verify | — | `GET /headless/invoke/platform/clinical-data-model-settings-starter/get-adverse-event-data-model-org-pref` | `handle-adverse-model-pref-toggle` |

### Read operations

#### `get-clinical-data-model-org-pref`

Returns boolean — whether ORG_PREFERENCE_CLINICAL_DATA_MODEL is enabled org-wide. No access guard on this read; any authenticated caller can observe the state.

**Call:** `GET /headless/invoke/platform/clinical-data-model-settings-starter`   — status: `proposed`

**Output:** boolean — true when ORG_PREFERENCE_CLINICAL_DATA_MODEL is enabled in the org; false otherwise.

#### `get-adverse-event-data-model-org-pref`

Returns boolean — whether ORG_PREFERENCE_ADVERSE_EVENTS is enabled org-wide. Gated by Customize Application permission; no license check on this read.

**Call:** `GET /headless/invoke/platform/clinical-data-model-settings-starter/get-adverse-event-data-model-org-pref`   — status: `proposed`

**Output:** boolean — true when ORG_PREFERENCE_ADVERSE_EVENTS (IndustriesLifeSciencesUddSettingAccessCheck.ORG_PREFERENCE_ADVERSE_EVENTS) is enabled in the org; false otherwise.

### Write operations

#### `handle-clinical-data-model-pref-toggle`

Persists the new boolean state of ORG_PREFERENCE_CLINICAL_DATA_MODEL. Void return on success; throws NoAccessException without HC|HC-Starter license + Customize Application/SysAdmin. Enable (value=true) emits a LifeSciences telemetry event (CLINICAL_DM, clinicalDataModel.enabled).

**Call:** `PATCH /headless/invoke/platform/clinical-data-model-settings-starter/handle-clinical-data-model-pref-toggle`   — status: `proposed`

**Inputs:**

- `value` *(`boolean`)* — Toggle the value preference on or off.

#### `handle-adverse-model-pref-toggle`

Persists the new boolean state of ORG_PREFERENCE_ADVERSE_EVENTS. Void return on success; throws NoAccessException without HC|HC-Starter license + ORG_PERMISSION_ADVERSE_EVENTS feature flag + Customize Application/SysAdmin. No telemetry side-effect.

**Call:** `PATCH /headless/invoke/platform/clinical-data-model-settings-starter/handle-adverse-model-pref-toggle`   — status: `proposed`

**Inputs:**

- `value` *(`boolean`)* — Toggle the value preference on or off.

### Verify operations

#### `verify-handle-clinical-data-model-pref-toggle`

Verify the effect of handle-clinical-data-model-pref-toggle: read back the current value via the companion read to confirm the write took effect.

**Call:** `GET /headless/invoke/platform/clinical-data-model-settings-starter`

**Depends on:** `handle-clinical-data-model-pref-toggle`

#### `verify-handle-adverse-model-pref-toggle`

Verify the effect of handle-adverse-model-pref-toggle by reading back via getAdverseEventDataModelOrgPref; the read returns the same ORG_PREFERENCE_ADVERSE_EVENTS the toggle just set.

**Call:** `GET /headless/invoke/platform/clinical-data-model-settings-starter/get-adverse-event-data-model-org-pref`

**Depends on:** `handle-adverse-model-pref-toggle`
