---
name: industries-advanced-therapy-management-settings-configure
description: "Use this skill when users want to reads the ATM setup wizard config and toggles the single registered ATM Flow Event Preference action (atmSetupToggleFlowEventPref), which writes the org preference \"disable ATM flow orchestration event\". Trigger when users mention advanced, therapy, management, settings, advanced therapy management settings."
metadata:
  version: "1.0"
  accessCheck: "Industries.userCanAccessSetup"
---

# Managing Advanced Therapy Management Settings

## When to Use This Skill

Reads the ATM setup wizard config and toggles the single registered ATM Flow Event Preference action (atmSetupToggleFlowEventPref), which writes the org preference "disable ATM flow orchestration event". The naming is inverted: by DEFAULT the preference is OFF and flow orchestration events for Advanced Therapy Management are ENABLED (required for entry condition-based orchestrator flows to resume normally). Enabling the preference (the "ACTIVE" toggle state) DISABLES those flow events — so an agent must NOT assume ACTIVE means "events are active." Two distinct invocations exist, and BOTH go through the parameterized step (parameterized-execute-admin-setup-step-action), NOT the plain execute-admin-setup-step-action step (which maps to a no-arg execute() that is a no-op for this action and changes nothing): (1) READ current state — paramKeys=[type], paramValues=[GET_STATUS] — returns a boolean result (result=true ⇒ the disable preference is ON ⇒ flow events are currently DISABLED; result=false ⇒ events ENABLED). This read is side-effect-free and can be called standalone without toggling first. (2) WRITE — paramKeys=[inputState], paramValues=[true] or [false] — inputState=true sets the disable preference ON (DISABLES flow events, response custom.toggleStatus=ACTIVE); inputState=false sets it OFF (re-ENABLES events, custom.toggleStatus=INACTIVE). custom.toggleStatus is returned by the WRITE only; the GET_STATUS read returns the boolean result, not custom.toggleStatus. Config is read via the public GET /connect/industries/adminSetup/{fileName}; the parameterized action invocation runs on the Setup dispatcher (Aura) /headless/invoke controller (paramKeys[]/paramValues[] arrays).

## Critical Constraints

**Preconditions:**

- User must have Industries AccessSetup access (check: `View Setup permission`)

**Operational rules:**

- IMPORTANT — both the status read and the toggle go through parameterized-execute-admin-setup-step-action. The plain execute-admin-setup-step-action step is a no-op for this action (backing no-arg execute() returns false and writes nothing); never use it to toggle.
To check current state (e.g. "are ATM flow-orchestration events disabled?"): call parameterized-execute-admin-setup-step-action with actionName=atmSetupToggleFlowEventPref, paramKeys=[type], paramValues=[GET_STATUS]. This is side-effect-free — no need to read config or toggle first. The response's boolean result=true means the disable preference is ON ⇒ flow orchestration events are currently DISABLED; result=false means events are ENABLED (the default) and entry condition-based orchestrator flows can resume normally. (This read returns the boolean result, not custom.toggleStatus.)
To change the setting: call parameterized-execute-admin-setup-step-action with actionName=atmSetupToggleFlowEventPref, paramKeys=[inputState], and paramValues=[true] to DISABLE flow events (sets the disable preference ON; response custom.toggleStatus=ACTIVE) or paramValues=[false] to ENABLE them (response custom.toggleStatus=INACTIVE). Optionally read config first (get-admin-setup-data, fileName=AdvancedTherapyManagementSetup) to confirm action.name, then verify the new state with the GET_STATUS call above.
Access: the write requires the Advanced Therapy Orchestration org capability plus Customize Application / System Administrator; page access is gated by View Setup permission.

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `get-admin-setup-data` | read | proposed | `GET /connect/industries/adminSetup/{fileName}` | — |
| `execute-admin-setup-step-action` | write | proposed | `PATCH /headless/invoke/platform/advanced-therapy-management-settings/execute-admin-setup-step-action` | — |
| `parameterized-execute-admin-setup-step-action` | write | proposed | `PATCH /headless/invoke/platform/advanced-therapy-management-settings/parameterized-execute-admin-setup-step-action` | — |

### Read operations

#### `get-admin-setup-data`

Loads ATM wizard config. Pass fileName=AdvancedTherapyManagementSetup. Returns AdminSetupRepresentation with configurations[].steps[] carrying action.name and stepCompletionCheck the agent traverses to dispatch toggles.

**Call:** `GET /connect/industries/adminSetup/{fileName}`   — status: `proposed`

**Inputs:**

- `fileName` *(`String`)*

### Write operations

#### `execute-admin-setup-step-action`

Execute admin setup step action.

**Call:** `PATCH /headless/invoke/platform/advanced-therapy-management-settings/execute-admin-setup-step-action`   — status: `proposed`

**Inputs:**

- `actionName` *(`String`)* — Name of the action.

#### `parameterized-execute-admin-setup-step-action`

Parameterized execute admin setup step action.

**Call:** `PATCH /headless/invoke/platform/advanced-therapy-management-settings/parameterized-execute-admin-setup-step-action`   — status: `proposed`

**Inputs:**

- `actionName` *(`String`)* — Name of the action.
- `params` *(`Map<String, String>`)* — Value for params.
