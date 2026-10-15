---
name: industries-case-management-intelligence-settings-configure
description: "Use this skill when users want to nonProfit Cloud Case Management Intelligence guided-setup wizard. Trigger when users mention case, mgmt, intelligence, settings, case mgmt intelligence settings."
metadata:
  version: "1.0"
  accessCheck: "Industries.userCanAccessSetup"
---

# Querying Case Mgmt Intelligence Settings

## When to Use This Skill

NonProfit Cloud Case Management Intelligence guided-setup wizard. get-admin-setup-data loads the wizard layout (configurations/groups/ordered-steps with server-evaluated stepStatus + per-step action descriptors) via fileName=CaseMgmtIntelligenceSetup.json. All three original controller methods substitute the Aura admin-setup operation with industries-healthcare-connect-api Connect endpoints (Aura is a thin pass-through). Note: execute-admin-setup-step-action and parameterized-execute-admin-setup-step-action are rejected for headless dispatch -- see navigate-case-mgmt-intelligence-setup. This node's own setupConfig declares no executor-backed action (4 steps: Manual, ButtonNavigate, LaunchComponent, ButtonNavigate), and the generic caller-supplied-actionName dispatcher those two steps use reaches a cross-feature executor that grants the Data Cloud Salesforce Connector permission set -- the same underlying grant this wizard's own LaunchComponent step auto-fires on mount, with no accept-click of its own and no enforced step-ordering precondition of its own either (the underlying wizard step's own configuration declares no dependency or preValidation). Gated at the Connect wire tier by a broad ~14-way Industries org-feature OR-list (HealthCloud-related checks and Public Sector Cloud LPI among them, plus several other Industries clouds -- not limited to Nonprofit Cloud or FSC-specific features).

## Workflow

Only get-admin-setup-data is executable for headless dispatch. Read it first to learn current stepStatus. Both write steps (execute-admin-setup-step-action, parameterized-execute-admin-setup-step-action) are rejected -- this node's own setupConfig has no executor-backed action, and the generic dispatcher reaches a cross-feature grant (see navigate-case-mgmt-intelligence-setup and the rejected steps' reason fields). Use navigate-case-mgmt-intelligence-setup to route the admin to the Setup page to drive the wizard (including its LaunchComponent step) themselves.

## Critical Constraints

**Preconditions:**

- View Setup permission (user must have Industries AccessSetup access) (check: `View Setup permission`)

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `get-admin-setup-data` | read | proposed | `GET /connect/industries/adminSetup/{fileName}` | — |
| `navigate-case-mgmt-intelligence-setup` | read | — | `CaseMgmtIntelligenceSettings.setup` | — |

### Read operations

#### `get-admin-setup-data`

Load the wizard. fileName=CaseMgmtIntelligenceSetup.json (only valid value for this node). Returns AdminSetupRepresentation: featureName, ordered configurations[] (groups with ordered steps; each carries action descriptor, server-evaluated stepStatus, stepCompletionCheck, helpUrl), errors[], disableReset, isSuccess.

**Call:** `GET /connect/industries/adminSetup/{fileName}`   — status: `proposed`

**Inputs:**

- `fileName` *(`String`)*

**Notes:** error_contracts: 404 NOT_FOUND when the caller's org lacks a matching Industries-family org-feature — the Connect org-feature check is a broad ~14-way OR-list (HealthCloud-related checks and Public Sector Cloud LPI among them, plus several other Industries clouds — not limited to Nonprofit Cloud or FSC-specific features) that gates this read at the wire tier. Verified: probe against an org with no matching OR-list feature returned 404. 500 INVALID_INPUT when fileName != CaseMgmtIntelligenceSetup.json. Path segment must include the trailing .json literal as-is (no URL-encoding needed; probe with the literal .json in the path segment returns 404 (feature-gated), which is a routing hit, not a URL-layer intercept).

#### `navigate-case-mgmt-intelligence-setup`

Routes a human admin to the Case Mgmt Intelligence Settings Setup page to drive the wizard themselves. Replaces execute-admin-setup-step-action and parameterized-execute-admin-setup-step-action for headless dispatch: this node's own setupConfig has no executor-backed action, and the generic dispatcher those steps use reaches a cross-feature executor that grants the Data Cloud Salesforce Connector permission set -- the same underlying grant this wizard's own LaunchComponent step auto-fires on mount, not gated by an accept-click or by any enforced step-ordering precondition of its own (the underlying wizard step's own configuration declares no dependency or preValidation) -- the only practical gate is that a human has to open the Setup page and reach the step at all. An agent should navigate the admin here and let them drive the wizard themselves, not dispatch step actions on their behalf. get-admin-setup-data remains fully executable for reading wizard layout and stepStatus.

**Call:** `CaseMgmtIntelligenceSettings.setup`
