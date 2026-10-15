---
name: fsc-actionable-segmentation-settings-configure
description: "Use this skill when users want to manages Actionable Segmentation (FSC Actionable List) admin settings. Trigger when users mention actionable, segmentation, settings, actionable segmentation settings."
metadata:
  version: "1.0"
  accessCheck: "(ActionableList.userHasActionableListAccess) || (SetupUtil.isSetupAdmin)"
---

# Managing Actionable Segmentation Settings

## When to Use This Skill

Manages Actionable Segmentation (FSC Actionable List) admin settings. Three concept clusters: (1) two org prefs `listPref` (master feature toggle) and `adminConfigAccess` (admin-config edit perm) read together as a map and toggled individually; (2) install + status of the bundled CRM Analytics (Wave) application that backs the feature; (3) admin-list-view ops on `ActionableListDefinition` (ALD) records — toggle IsActive, upsert dataset columns and member statuses with server-enforced caps + uniqueness, and a canDelete + delete pair. `BatchCalcJobDefinition` lookup by anchor entity supports the ALD editor.

## Workflow

Enable the feature via save-pref(listPref=true), then install-wave-application; poll get-actionable-list-folder-status until it returns `CompletedStatus` (`InProgressStatus` while still running; `NotAvailable` before it starts). ALD edits need an existing ALD id (creation lives on industries-actionablelist-connect-api). Always call can-delete-actionable-list-definition before delete-actionable-list-definition.

## Critical Constraints

**Preconditions:**

- User must have ActionableList ActionableListAccess access. (check: `Actionable List access`)
- Caller must be a Setup admin. The backing bean gates BOTH the read (getActionableListAllConfigurations) and the write (savePref) with `!isSetupAdmin() && ORG_HAS_ACTIONABLE_LIST → NoAccessException`, so once ActionableList is enabled on the org a non-admin cannot read the config map or toggle any pref. Skill-wide, not step-scoped. (check: `Setup administrator access`)

**Destructive operations — require explicit user confirmation:**

- **`delete-actionable-list-definition`** — Delete the ActionableListDefinition; cascades to its dataset columns and member statuses. Pair with can-delete-actionable-list-definition to gate the call and avoid orphaning ActionableList rows.
  - Rollback: No automatic rollback.

## Verification Checklist

After every write operation, confirm the effect by re-reading state:

- After `save-pref`: call `verify-save-pref` (`GET /headless/invoke/platform/actionable-segmentation-settings`)
- After `install-wave-application`: call `verify-install-wave-application` (`GET /headless/invoke/platform/actionable-segmentation-settings/get-actionable-list-folder-status`)

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `get-all-configurations` | read | proposed | `GET /headless/invoke/platform/actionable-segmentation-settings` | — |
| `get-datatable-data-types` | read | proposed | `GET /headless/invoke/platform/actionable-segmentation-settings/get-datatable-data-types` | — |
| `save-pref` | write | implemented | `PATCH /headless/invoke/platform/actionable-segmentation-settings/save-pref` | — |
| `get-actionable-list-folder-status` | read | proposed | `GET /headless/invoke/platform/actionable-segmentation-settings/get-actionable-list-folder-status` | — |
| `install-wave-application` | write | proposed | `PATCH /headless/invoke/platform/actionable-segmentation-settings/install-wave-application` | — |
| `update-actionable-list-member-status` | write | proposed | `PATCH /headless/invoke/platform/actionable-segmentation-settings/update-actionable-list-member-status` | — |
| `update-dataset-columns` | write | proposed | `PATCH /headless/invoke/platform/actionable-segmentation-settings/update-dataset-columns` | — |
| `toggle-actionable-list-definition` | write | proposed | `PATCH /headless/invoke/platform/actionable-segmentation-settings/toggle-actionable-list-definition` | — |
| `can-delete-actionable-list-definition` | read | proposed | `GET /headless/invoke/platform/actionable-segmentation-settings/can-delete-actionable-list-definition` | — |
| `delete-actionable-list-definition` | delete | proposed | `DELETE /headless/invoke/platform/actionable-segmentation-settings/delete-actionable-list-definition` | — |
| `get-batch-calc-job-definitions` | read | proposed | `GET /headless/invoke/platform/actionable-segmentation-settings/get-batch-calc-job-definitions` | — |
| `verify-save-pref` | verify | — | `GET /headless/invoke/platform/actionable-segmentation-settings` | `save-pref` |
| `verify-install-wave-application` | verify | — | `GET /headless/invoke/platform/actionable-segmentation-settings/get-actionable-list-folder-status` | `install-wave-application` |

### Read operations

#### `get-all-configurations`

Returns Map<String,Boolean> with `listPref` (master toggle) and `adminConfigAccess` (admin-config edit perm). Throws NoAccessException for non-Setup-admins when listPref is on. AURA-IS-CANONICAL — feature-scoped 2-key projection of org prefs.

**Call:** `GET /headless/invoke/platform/actionable-segmentation-settings`   — status: `proposed`

#### `get-datatable-data-types`

Returns supported column types as Map<name,apiValue>: Boolean, Currency, Date, DateTime, Email, Location, Number, Percent, Phone, Text (default), Url. AURA-IS-CANONICAL — wraps internal Java enum, no public describe surface.

**Call:** `GET /headless/invoke/platform/actionable-segmentation-settings/get-datatable-data-types`   — status: `proposed`

#### `get-actionable-list-folder-status`

Returns the bundled CRM Analytics (Wave) app install status, or null when caller lacks View Setup. Fixed 3-value enum: `CompletedStatus` (install finished successfully), `InProgressStatus` (install still running), `NotAvailable` (no install present / not started). AURA-IS-CANONICAL — controller hides the canonical Wave folder name; raw `/wave/folders/{id}` requires the agent to know it.

**Call:** `GET /headless/invoke/platform/actionable-segmentation-settings/get-actionable-list-folder-status`   — status: `proposed`

#### `can-delete-actionable-list-definition`

Returns true when no ActionableList rows reference the given ALD (delete would not orphan). Call before delete-actionable-list-definition. AURA-IS-CANONICAL — wraps orphan-check semantics that may evolve; raw SOQL count bakes the current implementation in.

**Call:** `GET /headless/invoke/platform/actionable-segmentation-settings/can-delete-actionable-list-definition`   — status: `proposed`

**Inputs:**

- `actionableListDefinitionId` *(`String`)*

#### `get-batch-calc-job-definitions`

Lists BatchCalcJobDefinition records whose AnchorEntity matches the given object API name. Powers the ALD editor's calc-job picker. AURA-IS-CANONICAL — BatchCalcJobDefinition is industries-internal; sObject substitution plausible but unverified.

**Call:** `GET /headless/invoke/platform/actionable-segmentation-settings/get-batch-calc-job-definitions`   — status: `proposed`

**Inputs:**

- `anchorEntity` *(`String`)*

### Write operations

#### `save-pref`

Writes one org pref. `pref` is restricted to {listPref, adminConfigAccess}; any other name is ignored. Server-enforced gating inside savePref: a non-Setup-admin caller (with ActionableList enabled) gets NoAccessException; a Setup-admin caller must additionally have Data Pipelines/Insights enabled (InsightsAccessCheck.ORG_HAS_DATA_PIPELINES_APP AND ORG_HAS_DATA_PIPELINES_APP_ENABLED — else AuraHandledException "DataPipeLineNotEnabledError") and Data Processing Engine enabled (CalcserviceAccessCheck.ORG_HAS_CALCSERVICE — else "DPENotEnabledError"). AURA-IS-CANONICAL — the pref allowlist + admin cross-feature gate are not reconstructable via a raw pref / Metadata-API write.

**Call:** `PATCH /headless/invoke/platform/actionable-segmentation-settings/save-pref`   — status: `implemented`

**Inputs:**

- `pref` *(`String`)* — Value for the pref field.
- `enabled` *(`boolean`)* — Whether d is enabled.

#### `install-wave-application`

Triggers install of the bundled CRM Analytics (Wave) app required for Actionable Segmentation. Setup-admin only. Idempotent at the service layer. AURA-IS-CANONICAL — controller hides the canonical templateApiName; sibling SORs RevenueInsightsSetup / ServiceUnifiedAnalytics wrap the install per-feature for the same reason.

**Call:** `PATCH /headless/invoke/platform/actionable-segmentation-settings/install-wave-application`   — status: `proposed`

#### `update-actionable-list-member-status`

Upserts ActionableListMemberStatus rows on one ALD. inputJson is `{memberStatus:[{id?, statusIcon, status}]}`; entries without id created, with id modified, duplicate `status` rejected server-side. Returns ALL member statuses (max 100). AURA-IS-CANONICAL — batch + uniqueness not reconstructable via per-row sObject PATCH.

**Call:** `PATCH /headless/invoke/platform/actionable-segmentation-settings/update-actionable-list-member-status`   — status: `proposed`

**Inputs:**

- `actionableListDefinitionId` *(`String`)* — Id of the actionable list definition.
- `inputJson` *(`String`)* — Value for the input json field.

#### `update-dataset-columns`

Upserts ActionableListDatasetColumn rows on one ALD. inputJson is `{datasetColumn:[{id, sourceFieldName, objectName, isDefault, dataDomain, dataType, isTypeAheadSearchEnabled}]}`. Server enforces MAX_DEF_ALDC_IN_ALD cap on default-flagged columns and rejects renaming the anchor object's Id column. AURA-IS-CANONICAL.

**Call:** `PATCH /headless/invoke/platform/actionable-segmentation-settings/update-dataset-columns`   — status: `proposed`

**Inputs:**

- `actionableListDefinitionId` *(`String`)* — Id of the actionable list definition.
- `inputJson` *(`String`)* — Value for the input json field.

#### `toggle-actionable-list-definition`

Sets IsActive on the named ALD and returns the updated record (id + recordLink + named fields). AURA-IS-CANONICAL — Connect API has no PATCH on ALD; raw sObject PATCH returns 204, losing the controller's record-projection response.

**Call:** `PATCH /headless/invoke/platform/actionable-segmentation-settings/toggle-actionable-list-definition`   — status: `proposed`

**Inputs:**

- `actionableListDefinitionId` *(`String`)* — Id of the actionable list definition.
- `isActive` *(`boolean`)* — Whether active is enabled.

### Verify operations

#### `verify-save-pref`

Read back the org-pref map via getActionableListAllConfigurations to confirm save-pref took effect; check the targeted key (`listPref` or `adminConfigAccess`) equals the value that was written.

**Call:** `GET /headless/invoke/platform/actionable-segmentation-settings`

**Depends on:** `save-pref`

#### `verify-install-wave-application`

Read the Wave folder install status via getActionableListFolderStatus to confirm install-wave-application kicked off and to poll until it reports `CompletedStatus` (`InProgressStatus` while the install is still running; `NotAvailable` before it starts).

**Call:** `GET /headless/invoke/platform/actionable-segmentation-settings/get-actionable-list-folder-status`

**Depends on:** `install-wave-application`

### Destructive operations

#### `delete-actionable-list-definition`

Delete the ActionableListDefinition; cascades to its dataset columns and member statuses. Pair with can-delete-actionable-list-definition to gate the call and avoid orphaning ActionableList rows.

**Call:** `DELETE /headless/invoke/platform/actionable-segmentation-settings/delete-actionable-list-definition`   — status: `proposed`

**Inputs:**

- `actionableListDefinitionId` *(`String`)*
