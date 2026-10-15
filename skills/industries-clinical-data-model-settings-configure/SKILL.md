---
name: industries-clinical-data-model-settings-configure
description: "Use this skill when users want to manages two Health Cloud org preferences via the Clinical Data Settings setup page: ORG_PREFERENCE_CLINICAL_DATA_MODEL (clinical data model) and ORG_PREFERENCE_ADVERSE_EVENTS (adverse event data model). Trigger when users mention clinical, data, model, settings, clinical data model settings."
metadata:
  version: "1.0"
  accessCheck: "(HealthCloudAccessCheck.ORG_HAS_HEALTH_CLOUD || HealthCloudAccessCheck.ORG_HAS_HEALTH_CLOUD_STARTER) || (IndustriesLifeSciencesUddSettingAccessCheck.ORG_PERMISSION_ADVERSE_EVENTS)"
---

# Managing Clinical Data Model Settings

## When to Use This Skill

Manages two Health Cloud org preferences via the Clinical Data Settings setup page: ORG_PREFERENCE_CLINICAL_DATA_MODEL (clinical data model) and ORG_PREFERENCE_ADVERSE_EVENTS (adverse event data model). All four operations route through the platform Aura controller (exposed via /headless/invoke/platform/clinical-data-model-settings/*). The page reads each preference's current boolean state and toggles each independently. Writes require an org licensed for Health Cloud OR Health Cloud Starter plus Customize Application/SysAdmin; the adverse-event toggle additionally requires the ORG_PERMISSION_ADVERSE_EVENTS feature flag. Enabling the clinical-data-model preference emits a LifeSciences telemetry event (CLINICAL_DM, clinicalDataModel.enabled). The HC Starter license variant lives in sibling SOR ClinicalDataModelSettingsStarter.

## Workflow

Two independent prefs, no inter-pref ordering. To inspect: call get-clinical-data-model-org-pref and get-adverse-event-data-model-org-pref. To change either: call its toggle write, then its verify read-back. License (HC|HC-Starter) + Customize Application/SysAdmin required for all writes.

## Critical Constraints

**Preconditions:**

- Caller must hold Customize Application OR System Administrator (Customize Application permission); required by both writes and the adverse-event read. (check: `Customize Application permission`)
- Org must be licensed for Health Cloud OR Health Cloud Starter; both writes throw NoAccessException when neither license is present (controller checkAccessAndThrowException, lines 75-79). The HC Starter license variant has its own SOR (ClinicalDataModelSettingsStarter). (check: `HealthCloudAccessCheck.ORG_HAS_HEALTH_CLOUD || HealthCloudAccessCheck.ORG_HAS_HEALTH_CLOUD_STARTER`)
- Toggling the Adverse Event Data Model preference additionally requires the ORG_PERMISSION_ADVERSE_EVENTS feature flag enabled in the org. Does NOT affect the clinical-data-model toggle (controller checkAdverseEventAccessAndThrowException, lines 84-90). (check: `IndustriesLifeSciencesUddSettingAccessCheck.ORG_PERMISSION_ADVERSE_EVENTS`)

## Verification Checklist

After every write operation, confirm the effect by re-reading state:

- After `toggle-clinical-data-model-pref`: call `verify-toggle-clinical-data-model-pref` (`GET /headless/invoke/platform/clinical-data-model-settings`)
- After `toggle-adverse-model-pref`: call `verify-toggle-adverse-model-pref` (`GET /headless/invoke/platform/clinical-data-model-settings/get-adverse-event-data-model-org-pref`)

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `get-clinical-data-model-org-pref` | read | proposed | `GET /headless/invoke/platform/clinical-data-model-settings` | — |
| `get-adverse-event-data-model-org-pref` | read | proposed | `GET /headless/invoke/platform/clinical-data-model-settings/get-adverse-event-data-model-org-pref` | — |
| `toggle-clinical-data-model-pref` | write | proposed | `PATCH /headless/invoke/platform/clinical-data-model-settings/handle-clinical-data-model-pref-toggle` | — |
| `verify-toggle-clinical-data-model-pref` | verify | — | `GET /headless/invoke/platform/clinical-data-model-settings` | `toggle-clinical-data-model-pref` |
| `toggle-adverse-model-pref` | write | proposed | `PATCH /headless/invoke/platform/clinical-data-model-settings/handle-adverse-model-pref-toggle` | — |
| `verify-toggle-adverse-model-pref` | verify | — | `GET /headless/invoke/platform/clinical-data-model-settings/get-adverse-event-data-model-org-pref` | `toggle-adverse-model-pref` |

### Read operations

#### `get-clinical-data-model-org-pref`

Returns boolean — whether ORG_PREFERENCE_CLINICAL_DATA_MODEL is enabled org-wide. No access guard on this read; any authenticated caller can observe the state.

**Call:** `GET /headless/invoke/platform/clinical-data-model-settings`   — status: `proposed`

**Output:** boolean — true when ORG_PREFERENCE_CLINICAL_DATA_MODEL is enabled in the org; false otherwise.

#### `get-adverse-event-data-model-org-pref`

Returns boolean — whether ORG_PREFERENCE_ADVERSE_EVENTS is enabled org-wide. Gated by Customize Application permission; no license check on this read.

**Call:** `GET /headless/invoke/platform/clinical-data-model-settings/get-adverse-event-data-model-org-pref`   — status: `proposed`

**Output:** boolean — true when ORG_PREFERENCE_ADVERSE_EVENTS is enabled in the org; false otherwise.

### Write operations

#### `toggle-clinical-data-model-pref`

Persists the new boolean state of ORG_PREFERENCE_CLINICAL_DATA_MODEL. Void return on success; throws NoAccessException without HC|HC-Starter license + Customize Application/SysAdmin. Enable emits a LifeSciences telemetry event (CLINICAL_DM, clinicalDataModel.enabled).

**Call:** `PATCH /headless/invoke/platform/clinical-data-model-settings/handle-clinical-data-model-pref-toggle`   — status: `proposed`

**Inputs:**

- `value` *(`boolean`)* — Desired boolean state of ORG_PREFERENCE_CLINICAL_DATA_MODEL. Send
strict JSON boolean `true` to enable, `false` to disable. The
dispatcher applies Boolean.parseBoolean — case-insensitive string
"true" also coerces to true; anything else coerces to false and
silently disables the preference. Prefer the strict boolean form.

**Notes:** error_contracts: {'wrong_verb': 'PATCH is the only accepted verb on this endpoint. POST / PUT / DELETE\nreturn 404 NOT_FOUND from the dispatcher. Do not attempt a POST create.', 'silent_coercion': 'The controller uses a Java primitive boolean binding — the dispatcher\ncalls Boolean.parseBoolean on the JSON value. Case-insensitive string\n"true" / "TRUE" IS coerced to true (verified iter 2: PATCH `{"value":\n"true"}` from a false state produced a true read-back). Every other\nshape — missing value key (empty {}), numeric 0/1, null, or any other\nstring — coerces to false and DISABLES the preference. Always send\nstrict JSON `{"value": true}` or `{"value": false}` to avoid ambiguity.\nChain the paired read to confirm the applied value.', 'extra_fields': 'Extra top-level fields in the body are silently ignored. Safe but\nnot useful — no schema validation error is raised.'}; response_shape: Successful PATCH returns HTTP 200 with an empty JSON object {}. The
response does not echo the applied value. To confirm the write took
effect, chain the verify-toggle-clinical-data-model-pref read step.; side_effects: Enabling this preference emits a LifeSciences telemetry event
(CLINICAL_DM, clinicalDataModel.enabled). Repeated enable calls emit
repeated telemetry — prefer idempotent gating by reading first.

#### `toggle-adverse-model-pref`

Persists the new boolean state of ORG_PREFERENCE_ADVERSE_EVENTS. Void return on success; throws NoAccessException without HC|HC-Starter license + ORG_PERMISSION_ADVERSE_EVENTS feature flag + Customize Application/SysAdmin. No telemetry side-effect.

**Call:** `PATCH /headless/invoke/platform/clinical-data-model-settings/handle-adverse-model-pref-toggle`   — status: `proposed`

**Inputs:**

- `value` *(`boolean`)* — Desired boolean state of ORG_PREFERENCE_ADVERSE_EVENTS. Send strict
JSON boolean `true` to enable, `false` to disable. The dispatcher
applies Boolean.parseBoolean — case-insensitive string "true" also
coerces to true; anything else coerces to false and silently disables
the preference.

**Notes:** error_contracts: {'wrong_verb': 'PATCH is the only accepted verb on this endpoint. POST / PUT / DELETE\nreturn 404 NOT_FOUND from the dispatcher.', 'silent_coercion': 'The controller uses a Java primitive boolean binding — the dispatcher\ncalls Boolean.parseBoolean on the JSON value. Case-insensitive string\n"true" / "TRUE" IS coerced to true. Every other shape — missing value\nkey (empty {}), numeric 0/1, null, or any other string — coerces to\nfalse and DISABLES the preference. Always send strict JSON\n`{"value": true}` or `{"value": false}` to avoid ambiguity. Chain the\npaired read (get-adverse-event-data-model-org-pref) to confirm the\napplied value.', 'extra_fields': 'Extra top-level fields in the body are silently ignored.'}; response_shape: Successful PATCH returns HTTP 200 with an empty JSON object {}. The
response does not echo the applied value. Chain the paired
verify-toggle-adverse-model-pref read step to confirm.; independence: This preference is fully independent of ORG_PREFERENCE_CLINICAL_DATA_MODEL.
Toggling adverse-events does not affect the clinical-data-model state
and vice versa; the two toggles can be issued in either order.

### Verify operations

#### `verify-toggle-clinical-data-model-pref`

Verify the effect of toggle-clinical-data-model-pref: read back the current value via the companion read to confirm the write took effect.

**Call:** `GET /headless/invoke/platform/clinical-data-model-settings`

**Depends on:** `toggle-clinical-data-model-pref`

**Output:** Boolean read-back of ORG_PREFERENCE_CLINICAL_DATA_MODEL. Should
match the value just written by toggle-clinical-data-model-pref;
any mismatch means the write did not take effect (typically the
body was silently coerced — see the paired toggle step's
error_contracts.silent_coercion).

#### `verify-toggle-adverse-model-pref`

Verify the effect of toggle-adverse-model-pref by reading back via getAdverseEventDataModelOrgPref; the read returns the same ORG_PREFERENCE_ADVERSE_EVENTS the toggle just set.

**Call:** `GET /headless/invoke/platform/clinical-data-model-settings/get-adverse-event-data-model-org-pref`

**Depends on:** `toggle-adverse-model-pref`

**Output:** Boolean read-back of ORG_PREFERENCE_ADVERSE_EVENTS. Should match the
value just written by toggle-adverse-model-pref; a mismatch means the
write coerced (see the paired toggle step's
error_contracts.silent_coercion).
