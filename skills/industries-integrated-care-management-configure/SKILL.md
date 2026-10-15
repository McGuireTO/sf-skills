---
name: industries-integrated-care-management-configure
description: "Use this skill when users want to setup for Integrated Care Management (Health Cloud). Trigger when users mention integrated, care, management, settings, integrated care management settings."
metadata:
  version: "1.0"
  accessCheck: "Industries.userCanAccessSetup"
---

# Managing Integrated Care Management Settings

## When to Use This Skill

Setup for Integrated Care Management (Health Cloud). Two complementary paths. (1) Industries AdminSetup framework: GET /connect/industries/adminSetup/{fileName} discovers access-filtered configurations[].steps[] with action.name values, and POST /connect/industries/executeAdminSetupStepAction invokes them (paramKeys/paramValues parallel arrays for the parameterized variant); reads gate on Industries AccessSetup. (2) Direct org-preference toggles applied in a STRICT order — Enhanced Care Plans (CarePlansPreference) FIRST because it provisions the ICM Console app, then Integrated Care Management (Automatic Sharing for Goal Assignment Records), Automatic Sharing for Care Task Records, Care Gap Detection, and optionally MCG. Each toggle is enabled by deploying a MINIMAL IndustriesSettings via the file-based Metadata-CRUD surface (one enable* field) and read back via a Tooling IndustriesSettings query of the matching Is*Enabled field. The internal CarePlanBenefitSettings / IntegratedCareManagement / CareManagement controllers behind the /headless dispatcher document the underlying handlers but are internal-gated (POST-only, not customer-reachable).

## Workflow

Enable ICM in strict order. Enhanced Care Plans (enableCarePlansPreference) MUST succeed first — it provisions the ICM Console app that the later toggles depend on. Enable each toggle by deploying a MINIMAL IndustriesSettings via the file-based Metadata-CRUD surface (one enable* field per toggle; a full retrieve→deploy fails on feature-coupled prefs), then verify with a Tooling IndustriesSettings read of the matching Is*Enabled field before advancing to the next. Toggle 2 (Integrated Care Management / goal-assignment record sharing) is backed internally by the Integrated Care Management setup operations.handleToggleIntegratedCareManagement; toggles 3-5 (Care Task record sharing, Care Gap Detection, MCG) by the generic care-management operation.setPreference(orgPref, value) — these controllers run behind the internal H360 /headless dispatcher and are documented as controller_method but are not a customer transport; MCG is optional. Alternatively drive the same settings through the AdminSetup framework: call get-admin-setup-data first to discover valid action.name values, then execute-admin-setup-step-action (no params) or parameterized-execute-admin-setup-step-action.

## Critical Constraints

**Preconditions:**

- User must have Industries AccessSetup access (check: `View Setup permission`)
- The org must have Health Cloud with Care Management provisioned; ICM is a Health Cloud Care Management capability. (check: `Health Cloud provisioned`)
- The running user needs Industries setup access (View Setup / AccessSetup) to read and write these Care Management preferences. (check: `Care Management setup access`)
- Enhanced Care Plans (enableCarePlansPreference) must be enabled before the Integrated Care Management master toggle — enabling it provisions the ICM Console app the later toggles depend on. (check: `Enhanced Care Plans before ICM master`)

## Verification Checklist

After every write operation, confirm the effect by re-reading state:

- After `parameterized-execute-admin-setup-step-action`: call `verify-parameterized-execute-admin-setup-step-action` (`GET /connect/industries/adminSetup/{fileName}`)
- After `execute-admin-setup-step-action`: call `verify-execute-admin-setup-step-action` (`GET /connect/industries/adminSetup/{fileName}`)
- After (write): call `verify-enable-care-plans-preference`
- After (write): call `verify-enable-integrated-care-management`
- After (write): call `verify-enable-care-task-sharing`
- After (write): call `verify-enable-care-gap-detection`
- After (write): call `verify-enable-mcg`

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `get-admin-setup-data` | read | proposed | `GET /connect/industries/adminSetup/{fileName}` | — |
| `execute-admin-setup-step-action` | write | proposed | `PATCH /headless/invoke/platform/integrated-care-management-settings/execute-admin-setup-step-action` | — |
| `parameterized-execute-admin-setup-step-action` | write | proposed | `PATCH /headless/invoke/platform/integrated-care-management-settings/parameterized-execute-admin-setup-step-action` | — |
| `verify-parameterized-execute-admin-setup-step-action` | verify | proposed | `GET /connect/industries/adminSetup/{fileName}` | `parameterized-execute-admin-setup-step-action` |
| `verify-execute-admin-setup-step-action` | verify | implemented | `GET /connect/industries/adminSetup/{fileName}` | `execute-admin-setup-step-action` |
| `verify-enable-care-plans-preference` | verify | implemented | `IndustriesSettings.query` | — |
| `verify-enable-integrated-care-management` | verify | implemented | `IndustriesSettings.query` | — |
| `verify-enable-care-task-sharing` | verify | implemented | `IndustriesSettings.query` | — |
| `verify-enable-care-gap-detection` | verify | implemented | `IndustriesSettings.query` | — |
| `verify-enable-mcg` | verify | implemented | `IndustriesSettings.query` | — |

### Read operations

#### `get-admin-setup-data`

Loads the wizard's group/step graph. fileName is a path parameter naming a JSON descriptor under setupConfig/; response (AdminSetupRepresentation) carries access-filtered configurations[].steps[].action.name (the actionName for execute paths) and per-step stepStatus.

**Call:** `GET /connect/industries/adminSetup/{fileName}`   — status: `proposed`

**Inputs:**

- `fileName` *(`String`)*

### Write operations

#### `execute-admin-setup-step-action`

Execute admin setup step action.

**Call:** `PATCH /headless/invoke/platform/integrated-care-management-settings/execute-admin-setup-step-action`   — status: `proposed`

**Inputs:**

- `actionName` *(`String`)* — Name of the action.

#### `parameterized-execute-admin-setup-step-action`

Parameterized execute admin setup step action.

**Call:** `PATCH /headless/invoke/platform/integrated-care-management-settings/parameterized-execute-admin-setup-step-action`   — status: `proposed`

**Inputs:**

- `actionName` *(`String`)* — Name of the action.
- `params` *(`Map<String, String>`)* — Value for params.

### Verify operations

#### `verify-parameterized-execute-admin-setup-step-action`

Re-fetch the wizard graph after a parameterized step action runs and confirm the affected step.stepStatus advanced. Match by configurations[].steps[].action.name = <actionName>.

**Call:** `GET /connect/industries/adminSetup/{fileName}`   — status: `proposed`

**Inputs:**

- `fileName` *(`String`)* — Same fileName used in the original get-admin-setup-data call.

**Depends on:** `parameterized-execute-admin-setup-step-action`

#### `verify-execute-admin-setup-step-action`

Verify the effect of execute-admin-setup-step-action by re-reading the AdminSetup configuration for the same fileName; the dispatched step's completion check reflects in the returned configurations[].steps[] state.

**Call:** `GET /connect/industries/adminSetup/{fileName}`   — status: `implemented`

**Depends on:** `execute-admin-setup-step-action`

#### `verify-enable-care-plans-preference`

Verify Enhanced Care Plans is on via a Tooling IndustriesSettings query of IsCarePlansPreferenceEnabled (field confirmed against a live HC org). The internal is-care-plan-preference-enabled dispatcher (GET /headless/invoke/platform/care-plan-settings/is-care-plan-preference-enabled) is POST-only and internal-gated — not a customer read surface — so Tooling is the read-back path.

**Call:** `IndustriesSettings.query`   — status: `implemented`

**Inputs:**

- `q` *(`String`)*

#### `verify-enable-integrated-care-management`

Verify the Integrated Care Management master preference is on via a Tooling IndustriesSettings query of IsIntegratedCareManagementSettingEnabled (field confirmed against a live HC org). The internal get-integrated-care-management-pref dispatcher (GET /headless/invoke/industries/industries-healthcare/integrated-care-management/get-integrated-care-management-pref) is POST-only and internal-gated — not a customer read surface — so Tooling is the read-back path.

**Call:** `IndustriesSettings.query`   — status: `implemented`

**Inputs:**

- `q` *(`String`)*

#### `verify-enable-care-task-sharing`

Verify Care Task record sharing is enabled via a Tooling IndustriesSettings query of IsCareTaskSharingSettingEnabled (field confirmed against a live HC org). The internal generic get-preference dispatcher (GET /headless/invoke/industries/industries-healthcare/care-management/get-preference) is POST-only and internal-gated — not a customer read surface — so Tooling is the read-back path.

**Call:** `IndustriesSettings.query`   — status: `implemented`

**Inputs:**

- `q` *(`String`)*

#### `verify-enable-care-gap-detection`

Verify Care Gap Detection is enabled via a Tooling IndustriesSettings query of IsCareGapPrefSettingEnabled (field confirmed against a live HC org). The internal generic get-preference dispatcher (GET /headless/invoke/industries/industries-healthcare/care-management/get-preference) is POST-only and internal-gated — not a customer read surface — so Tooling is the read-back path.

**Call:** `IndustriesSettings.query`   — status: `implemented`

**Inputs:**

- `q` *(`String`)*

#### `verify-enable-mcg`

Verify the MCG preference state via a Tooling IndustriesSettings query of IsMcgSettingEnabled (field confirmed against a live HC org). The internal generic get-preference dispatcher (GET /headless/invoke/industries/industries-healthcare/care-management/get-preference) is POST-only and internal-gated — not a customer read surface — so Tooling is the read-back path.

**Call:** `IndustriesSettings.query`   — status: `implemented`

**Inputs:**

- `q` *(`String`)*

## Notes

- **related_sors:** {'node': 'psc-lpi/CarePlanSettings', 'relationship': 'shared-capability', 'reason': 'Enhanced Care Plans is the first ICM sub-feature and is configured in depth by the Public Sector CarePlanSettings node (CarePlanBenefitSettingsController). ICM enables it first (enableCarePlansPreference) to provision the ICM Console; for the full Care Plans preference surface (group membership, benefit verification, etc.) consult that node.'}
