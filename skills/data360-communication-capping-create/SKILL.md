---
name: data360-communication-capping-create
description: "Use this skill when users want to execute Data Cloud CommunicationCapping operations via the Data 360 MCP facade. Trigger when users mention data360/communication, capping, shared, cdp, mcp, connect, api, shared-cdp-mcp-connect-api."
metadata:
  version: "1.0"
---

# Managing Data360/communication Capping

## When to Use This Skill

Execute Data Cloud CommunicationCapping operations via the Data 360 MCP facade.

## Workflow

Each step lists an `operation` id. Call describe(<operation>) BEFORE dispatching to get that tool's parameter schema and, where available, a worked example. `paramsJson` decodes to the operation's requestBody schema VERBATIM, including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap or omit it. The only envelope the step handles for you is `{toolName, paramsJson}` (its `invocation` already wraps it); do not POST the operation path directly. If the tool's error suggests `payload_examples`, ignore it — that tool isn't available here; call describe(<operation>) instead.

## Critical Constraints

**Destructive operations — require explicit user confirmation:**

- **`communication-capping-activation-target-delete`** — Delete all dimension metadata associated with a specific activation target by its ID.
  - Rollback: No automatic rollback.
- **`communication-capping-rule-delete`** — Delete a specific communication capping rule by its ID or developer name.
  - Rollback: No automatic rollback.

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `communication-capping-activation-target-delete` | delete | implemented | `execute_communication-capping-activation-target-delete` | — |
| `communication-capping-activation-target-get` | read | implemented | `execute_communication-capping-activation-target-get` | — |
| `communication-capping-activation-target-map-dimension` | write | implemented | `execute_communication-capping-activation-target-map-dimension` | — |
| `communication-capping-activation-targets-list` | read | implemented | `execute_communication-capping-activation-targets-list` | — |
| `communication-capping-create` | write | implemented | `execute_communication-capping-create` | — |
| `communication-capping-dimension-create` | write | implemented | `execute_communication-capping-dimension-create` | — |
| `communication-capping-dimension-swap-priority` | write | implemented | `execute_communication-capping-dimension-swap-priority` | — |
| `communication-capping-dimension-update` | write | implemented | `execute_communication-capping-dimension-update` | — |
| `communication-capping-dimensions-get` | read | implemented | `execute_communication-capping-dimensions-get` | — |
| `communication-capping-disable` | write | implemented | `execute_communication-capping-disable` | — |
| `communication-capping-enable` | write | implemented | `execute_communication-capping-enable` | — |
| `communication-capping-get` | read | implemented | `execute_communication-capping-get` | — |
| `communication-capping-rule-create` | write | implemented | `execute_communication-capping-rule-create` | — |
| `communication-capping-rule-delete` | delete | implemented | `execute_communication-capping-rule-delete` | — |
| `communication-capping-rule-update` | write | implemented | `execute_communication-capping-rule-update` | — |
| `communication-capping-rules-list` | read | implemented | `execute_communication-capping-rules-list` | — |
| `communication-capping-update` | write | implemented | `execute_communication-capping-update` | — |

### Read operations

#### `communication-capping-activation-target-get`

Get dimension metadata associated with a specific activation target by its ID.

**Call:** `execute_communication-capping-activation-target-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_communication_capping_activation_target_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_communication-capping-activation-target-get) for the param schema and, where available, a worked example.

#### `communication-capping-activation-targets-list`

List activation targets for a communication capping configuration by ID. Supports pagination (offset, limit) and ordering by field and direction.

**Call:** `execute_communication-capping-activation-targets-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_communication_capping_activation_targets_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_communication-capping-activation-targets-list) for the param schema and, where available, a worked example.

#### `communication-capping-dimensions-get`

Get dimension information for a communication capping configuration. Filter by ccId (communication capping ID) or dataSpaceId.

**Call:** `execute_communication-capping-dimensions-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_communication_capping_dimensions_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_communication-capping-dimensions-get) for the param schema and, where available, a worked example.

#### `communication-capping-get`

Get a specific communication capping configuration by its ID.

**Call:** `execute_communication-capping-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_communication_capping_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_communication-capping-get) for the param schema and, where available, a worked example.

#### `communication-capping-rules-list`

List communication capping rules for a given configuration ID. Supports pagination (offset, limit) and ordering by field and direction.

**Call:** `execute_communication-capping-rules-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_communication_capping_rules_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_communication-capping-rules-list) for the param schema and, where available, a worked example.

### Write operations

#### `communication-capping-activation-target-map-dimension`

Map dimension metadata to a communication capping activation target by activation target ID. Provide the target name and list of dimension/dimension-value associations.

**Call:** `execute_communication-capping-activation-target-map-dimension`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_communication_capping_activation_target_map_dimension (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_communication-capping-activation-target-map-dimension) for the param schema and, where available, a worked example.

#### `communication-capping-create`

Create a new communication capping configuration. Provide a name, optional description, data space associations, and related dimensions.

**Call:** `execute_communication-capping-create`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_communication_capping_create (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_communication-capping-create) for the param schema and, where available, a worked example.

#### `communication-capping-dimension-create`

Create a new dimension for communication capping. Specify name, apiName, functionType, dimensionName, hierarchyOrder, and optional dimension values.

**Call:** `execute_communication-capping-dimension-create`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_communication_capping_dimension_create (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_communication-capping-dimension-create) for the param schema and, where available, a worked example.

#### `communication-capping-dimension-swap-priority`

Reorder the priority of communication capping dimensions by submitting an ordered list of dimension objects.

**Call:** `execute_communication-capping-dimension-swap-priority`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_communication_capping_dimension_swap_priority (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_communication-capping-dimension-swap-priority) for the param schema and, where available, a worked example.

#### `communication-capping-dimension-update`

Update an existing communication capping dimension by its dimensionId. Update name, apiName, functionType, dimensionName, hierarchyOrder, or dimension values.

**Call:** `execute_communication-capping-dimension-update`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_communication_capping_dimension_update (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_communication-capping-dimension-update) for the param schema and, where available, a worked example.

#### `communication-capping-disable`

Disable a communication capping configuration by its ID. Stops the capping from being applied.

**Call:** `execute_communication-capping-disable`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_communication_capping_disable (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_communication-capping-disable) for the param schema and, where available, a worked example.

#### `communication-capping-enable`

Enable a communication capping configuration by its ID. Activates the capping so it is applied to communications.

**Call:** `execute_communication-capping-enable`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_communication_capping_enable (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_communication-capping-enable) for the param schema and, where available, a worked example.

#### `communication-capping-rule-create`

Create a new communication capping rule under a given configuration ID. Provide startDate, endDate, limits, apiName, and optional dimension associations.

**Call:** `execute_communication-capping-rule-create`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_communication_capping_rule_create (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_communication-capping-rule-create) for the param schema and, where available, a worked example.

#### `communication-capping-rule-update`

Update a specific communication capping rule by configuration ID and rule ID or developer name. Update dates, limits, apiName, or dimension associations.

**Call:** `execute_communication-capping-rule-update`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_communication_capping_rule_update (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_communication-capping-rule-update) for the param schema and, where available, a worked example.

#### `communication-capping-update`

Update a communication capping configuration by its ID. Update name, description, data space associations, or related dimensions.

**Call:** `execute_communication-capping-update`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_communication_capping_update (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_communication-capping-update) for the param schema and, where available, a worked example.

### Destructive operations

#### `communication-capping-activation-target-delete`

Delete all dimension metadata associated with a specific activation target by its ID.

**Call:** `execute_communication-capping-activation-target-delete`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_communication_capping_activation_target_delete (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_communication-capping-activation-target-delete) for the param schema and, where available, a worked example.

#### `communication-capping-rule-delete`

Delete a specific communication capping rule by its ID or developer name.

**Call:** `execute_communication-capping-rule-delete`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_communication_capping_rule_delete (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_communication-capping-rule-delete) for the param schema and, where available, a worked example.
