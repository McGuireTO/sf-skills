---
name: industries-data-cloud-integration-configure
description: "Use this skill when users want to industries admin-setup wizard backing the Nonprofit Cloud Fundraising 'Data Cloud Integration' setup page, known to customers as \"Fundraising Intelligence Settings\". Trigger when users mention data, cloud, integration, data cloud integration."
metadata:
  version: "1.0"
---

# Managing Data Cloud Integration

## When to Use This Skill

Industries admin-setup wizard backing the Nonprofit Cloud Fundraising 'Data Cloud Integration' setup page, known to customers as "Fundraising Intelligence Settings". Generic AdminSetupController with three @AuraEnabled methods. The GET reads a setupConfig JSON (resolved relative to ui-industries-common-components/resources/setupConfig/) keyed by fileName and returns AdminSetupRepresentation: ordered groups containing dependency-ordered steps with action/actionResponse descriptors plus stepAccessCheck, preValidation, and stepCompletionCheck identifiers. The two PATCHes invoke server-side AdminSetupStepActionExecutor Spring beans by name; one accepts a String-to-String params map, the other does not. The setupConfig JSON is the source of truth for the step graph and the runtime registry of executable action names. No public Connect, Tooling, Metadata, or sObject equivalent exists for this surface — action names resolve at runtime to feature-specific beans, so substitution would lose both the dispatcher's access-guard and the per-step PermissionParser evaluation. Workflow: GET first to discover available step actions, then PATCH each in dependency order.

## Workflow

Call get-admin-setup-data first (with the page's fileName) to discover the current setupConfig's action names, dependency graph, and per-step access state. Then dispatch each step via execute-admin-setup-step-action when no caller inputs are required, or parameterized-execute-admin-setup-step-action when the step expects a String-to-String params map. Action names are runtime-resolved Spring bean names; do not invent them — read them from the GET response.

## Critical Constraints

**Preconditions:**

- User must have Industries AccessSetup access (controller-level guard on executeAdminSetupStepAction). (check: `View Setup permission`)
- Org must have the Nonprofit Cloud Fundraising / Nonprofit Intelligence feature enabled. (check: `Nonprofit Intelligence access`)
- Running user must be configured as a Fundraising admin. (check: `Fundraising Admin role`)
- API version must be v248 or later (setup-manifest 'since' for this node). (check: `None`)

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `get-admin-setup-data` | read | proposed | `GET /headless/invoke/platform/data-cloud-integration` | — |
| `execute-admin-setup-step-action` | write | proposed | `PATCH /headless/invoke/platform/data-cloud-integration/execute-admin-setup-step-action` | `get-admin-setup-data` |
| `parameterized-execute-admin-setup-step-action` | write | proposed | `PATCH /headless/invoke/platform/data-cloud-integration/parameterized-execute-admin-setup-step-action` | `get-admin-setup-data` |

### Read operations

#### `get-admin-setup-data`

Reads the setupConfig JSON named by fileName (resolved relative to ui-industries-common-components/resources/setupConfig/) and returns AdminSetupRepresentation. AURA-IS-CANONICAL — no public Connect/Tooling/Metadata/sObject alternative; setupConfig descriptors are Java resource files, not CRUD-able entities. Read-only; per-step stepAccessCheck/groupAccessCheck filters apply server-side.

**Call:** `GET /headless/invoke/platform/data-cloud-integration`   — status: `proposed`

**Inputs:**

- `fileName` *(`String`)*

**Output:** AdminSetupRepresentation: isSuccess (boolean), errors (ErrorRepresentation list — populated on parse/validation failure; only errorMessage carries content from the get path), featureName (echoes fileName), configurations (ordered AdminSetupGroupRepresentation list, filtered + renumbered by per-user groupAccessCheck — each group bundles dependency-ordered AdminSetupStepRepresentation steps carrying name, order, dependency indices, action+actionResponse descriptors, helpUrl/helpUrlLabel, preValidation/validationMessage, stepAccessCheck, stepCompletionCheck, ignoreStepProgress), disableReset (boolean — when true the wizard hides the reset control).

**Notes:** setup_config_filename: For this node, fileName resolves to FundraisingIntelligenceSetup.json, confirmed via source and a live headless GET. Customer-facing page name: "Fundraising Intelligence Settings".; genie_gating: 4 of the 10 steps in FundraisingIntelligenceSetup.json (3 groups of 2/7/1; 7 ButtonNavigate, 1 Manual, 2 LaunchComponent) carry a stepAccessCheck gated on "Data Cloud platform enabled". A live headless GET confirmed these steps are filtered out of the returned step graph server-side when the org lacks Genie Platform — observed in both license states (6 steps unlicensed → 10 once licensed, matching the UI) — the gate is runtime-enforced, not a UI-only toggle.; completion_status_fidelity_gap: The GET returns each step's stepCompletionCheck bean name but not its evaluated result — step objects carry no completed field and groupStatus is null. The Setup UI runs those validators (green checks / % complete) but the headless path does not, and no operation exposes running them. The skill is structure-aware but not progress-aware: an agent can list and route steps but can't report which are already done. Suggested to the owning team: return evaluated completion status in the GET, or add an operation to run the completion-check beans.

### Write operations

#### `execute-admin-setup-step-action`

Invokes the server-side AdminSetupStepActionExecutor Spring bean named by actionName (must match an action.name from a prior getAdminSetupData response). Gated by the controller-level View Setup permission access guard. Returns AdminSetupStepActionResultRepresentation. AURA-IS-CANONICAL — no public alternative because action names resolve at runtime to feature-specific beans, and substitution would drop the controller's access-guard.

**Call:** `PATCH /headless/invoke/platform/data-cloud-integration/execute-admin-setup-step-action`   — status: `proposed`

**Inputs:**

- `actionName` *(`String`)* — Name of the action.

**Depends on:** `get-admin-setup-data`

**Output:** AdminSetupStepActionResultRepresentation: result (boolean — true when the resolved AdminSetupStepActionExecutor bean reported success; thrown exceptions surface as AuraHandledException and never reach result=false), error (ErrorRepresentation, populated only on recoverable executor-reported failures), custom (string-keyed map — always null on this no-args path, populated only by the parameterized variant).

**Notes:** executor_allowlist_risk: This is a generic dispatcher that executes an AdminSetupStepActionExecutor Spring bean by caller-supplied actionName. Safe today because every action in FundraisingIntelligenceSetup.json is ButtonNavigate/Manual/LaunchComponent — no action currently maps to a mutating install/authorize bean. A live PATCH probe with a config action name returned 200 {"custom":{},"error":{}}, a benign no-op (no bean resolved, nothing mutated). Recommend an explicit allowlist of executable action names; re-review if the setupConfig ever registers an executor-backed install/authorize action.

#### `parameterized-execute-admin-setup-step-action`

Like execute-admin-setup-step-action but forwards a String-to-String params map to the executor bean — use when the step requires caller-supplied inputs. NOT decorated with the controller-level View Setup permission guard; access is enforced via the loaded setupConfig's stepAccessCheck (PermissionParser evaluation per group/step). Returns AdminSetupStepActionResultRepresentation with handler-defined custom map. AURA-IS-CANONICAL — runtime-bean dispatch + stepAccessCheck enforcement have no system-API analog.

**Call:** `PATCH /headless/invoke/platform/data-cloud-integration/parameterized-execute-admin-setup-step-action`   — status: `proposed`

**Inputs:**

- `actionName` *(`String`)* — Name of the action.
- `params` *(`Map<String, String>`)* — Value for params.

**Depends on:** `get-admin-setup-data`

**Output:** AdminSetupStepActionResultRepresentation: result (boolean — true on executor success; thrown exceptions become AuraHandledException), error (ErrorRepresentation on recoverable failure), custom (executor-bean-defined string-keyed output map — populated by the parameterized executor, distinct from the no-args variant which leaves it null).

**Notes:** executor_allowlist_risk: This is a generic dispatcher that executes an AdminSetupStepActionExecutor Spring bean by caller-supplied actionName. Safe today because every action in FundraisingIntelligenceSetup.json is ButtonNavigate/Manual/LaunchComponent — no action currently maps to a mutating install/authorize bean. Recommend an explicit allowlist of executable action names; re-review if the setupConfig ever registers an executor-backed install/authorize action.; access_guard_gap: Unlike its sibling execute-admin-setup-step-action, this method carries no controller-level View Setup access guard of its own. It relies entirely on the setupConfig's per-step stepAccessCheck for access control. Not a rejection reason — no mutating bean is wired today — but flagged as a latent risk to revisit if that changes.
