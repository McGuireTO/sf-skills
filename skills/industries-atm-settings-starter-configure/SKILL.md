---
name: industries-atm-settings-starter-configure
description: "Use this skill when users want to manage Advanced Therapy Management Settings Starter (Health Cloud Starter-license variant of AdvancedTherapyManagementSettings — same ATM Flow Event Preference toggle, a second Setup mount over the same AdminSetupController + atmSetupToggleFlowEventPref action from this setup page. Trigger when users mention advanced, therapy, management, settings, starter, advanced therapy management settings starter."
metadata:
  version: "1.0"
---

# Managing Advanced Therapy Management Settings Starter

## When to Use This Skill

Setup page entry point for Advanced Therapy Management Settings Starter (Health Cloud Starter-license variant of AdvancedTherapyManagementSettings — same ATM Flow Event Preference toggle, a second Setup mount over the same AdminSetupController + atmSetupToggleFlowEventPref action, on the advanced-therapy-management-settings-starter dispatcher path). The action writes the org preference "disable ATM flow orchestration event". The naming is inverted: by DEFAULT the preference is OFF and flow orchestration events for Advanced Therapy Management are ENABLED (required for entry condition-based orchestrator flows to resume normally). Enabling the preference (the "ACTIVE" toggle state) DISABLES those flow events — so an agent must NOT assume ACTIVE means "events are active." Two distinct invocations exist, and BOTH go through the parameterized step (parameterized-execute-admin-setup-step-action), NOT the plain execute-admin-setup-step-action step (which maps to a no-arg execute() that is a no-op for this action and changes nothing): (1) READ current state — paramKeys=[type], paramValues=[GET_STATUS] — returns a boolean result (result=true ⇒ the disable preference is ON ⇒ flow events are currently DISABLED; result=false ⇒ events ENABLED). Side-effect free; callable standalone without toggling first. (2) WRITE — paramKeys=[inputState], paramValues=[true] or [false] — inputState=true sets the disable preference ON (DISABLES flow events, response custom.toggleStatus=ACTIVE); inputState=false sets it OFF (re-ENABLES events, custom.toggleStatus=INACTIVE). custom.toggleStatus is returned by the WRITE only; the GET_STATUS read returns the boolean result, not custom.toggleStatus. Config is read via get-admin-setup-data (fileName=AdvancedTherapyManagementSetup).

## Critical Constraints

**Preconditions:**

- User must have Industries AccessSetup access (enforced by @ServiceComponentAccessGuard(View Setup permission) on the Aura controller and by the underlying setup-framework Apex layer the Connect API delegates to). (check: `View Setup permission`)
- Org must have HealthCloud Multi-Step Scheduling enabled (one of the OR-list feature gates on the Connect operation's org-access-check; ATM Settings Starter is the LifeSciences-tree-placed Multi-Step Scheduling configuration entry point). (check: `Multi-Step Scheduling enabled`)
- Wizard config resource AdvancedTherapyManagementSetup.json must be present in core/ui-industries-common-components/resources/setupConfig/ (jar-shipped; not org-deployable). The Aura component hard-codes featureConfigFileName=AdvancedTherapyManagementSetup.json so the agent must pass that exact value as fileName.

**Operational rules:**

- IMPORTANT — both the status read and the toggle go through parameterized-execute-admin-setup-step-action. The plain execute-admin-setup-step-action step is a no-op for this action (backing no-arg execute() returns false and writes nothing); never use it to toggle.
To check current state (e.g. "are ATM Starter flow-orchestration events disabled?"): call parameterized-execute-admin-setup-step-action with actionName=atmSetupToggleFlowEventPref, paramKeys=[type], paramValues=[GET_STATUS]. Side-effect-free. The response's boolean result=true means the disable preference is ON ⇒ flow orchestration events are currently DISABLED; result=false means events are ENABLED (the default) and entry condition-based orchestrator flows can resume normally. (This read returns the boolean result, not custom.toggleStatus.)
To change the setting: call parameterized-execute-admin-setup-step-action with actionName=atmSetupToggleFlowEventPref, paramKeys=[inputState], and paramValues=[true] to DISABLE flow events (sets the disable preference ON; response custom.toggleStatus=ACTIVE) or paramValues=[false] to ENABLE them (response custom.toggleStatus=INACTIVE). Optionally read config first (get-admin-setup-data, fileName=AdvancedTherapyManagementSetup) to confirm action.name, then verify the new state with the GET_STATUS call above.
Access: the write requires the Advanced Therapy Orchestration org capability plus Customize Application / System Administrator; page access is gated by View Setup permission.

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `get-admin-setup-data` | read | proposed | `GET /connect/industries/adminSetup/{fileName}` | — |
| `execute-admin-setup-step-action` | write | proposed | `PATCH /headless/invoke/platform/advanced-therapy-management-settings-starter/execute-admin-setup-step-action` | — |
| `parameterized-execute-admin-setup-step-action` | write | proposed | `PATCH /headless/invoke/platform/advanced-therapy-management-settings-starter/parameterized-execute-admin-setup-step-action` | — |

### Read operations

#### `get-admin-setup-data`

Loads ATM wizard config; pass fileName=AdvancedTherapyManagementSetup. Returns AdminSetupRepresentation with configurations[].steps[].action.{name,type}; agent reads action.name=atmSetupToggleFlowEventPref from group 4 (the only AdminExecute) to drive the toggle steps.

**Call:** `GET /connect/industries/adminSetup/{fileName}`   — status: `proposed`

**Inputs:**

- `fileName` *(`String`)*

**Output:** AdminSetupRepresentation: isSuccess (boolean), errors (array of ErrorRepresentation), featureName (string echoing the loaded config's title key), configurations (array of AdminSetupGroupRepresentation, each with groupName/groupOrder/groupAccessCheck/timeToComplete/groupStatus and steps[] of AdminSetupStepRepresentation carrying name/order/dependency/action{name,type,resource,target}/actionResponse/helpUrl/preValidation/stepAccessCheck/stepCompletionCheck/stepStatus), disableReset (boolean — true for this wizard).

### Write operations

#### `execute-admin-setup-step-action`

Execute admin setup step action.

**Call:** `PATCH /headless/invoke/platform/advanced-therapy-management-settings-starter/execute-admin-setup-step-action`   — status: `proposed`

**Inputs:**

- `actionName` *(`String`)* — Name of the action.

#### `parameterized-execute-admin-setup-step-action`

Parameterized execute admin setup step action.

**Call:** `PATCH /headless/invoke/platform/advanced-therapy-management-settings-starter/parameterized-execute-admin-setup-step-action`   — status: `proposed`

**Inputs:**

- `actionName` *(`String`)* — Name of the action.
- `params` *(`Map<String, String>`)* — Value for params.
