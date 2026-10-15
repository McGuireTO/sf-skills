---
name: data360-semantic-calculated-measurement-mcp-configure
description: "Use this skill when users want to execute Data Cloud SemanticCalculatedMeasurement operations via the Data 360 MCP facade. Trigger when users mention data360/semantic, calculated, measurement, shared, cdp, mcp, connect, api, shared-cdp-mcp-connect-api."
metadata:
  version: "1.0"
---

# Managing Data360/semantic Calculated Measurement

## When to Use This Skill

Execute Data Cloud SemanticCalculatedMeasurement operations via the Data 360 MCP facade.

## Workflow

Each step lists an `operation` id. Call describe(<operation>) BEFORE dispatching to get that tool's parameter schema and, where available, a worked example. `paramsJson` decodes to the operation's requestBody schema VERBATIM, including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap or omit it. The only envelope the step handles for you is `{toolName, paramsJson}` (its `invocation` already wraps it); do not POST the operation path directly. If the tool's error suggests `payload_examples`, ignore it — that tool isn't available here; call describe(<operation>) instead.

## Critical Constraints

**Destructive operations — require explicit user confirmation:**

- **`sdm-calc-measure-delete`** — Delete a calculated measurement from a semantic model.
  - Rollback: No automatic rollback.

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `sdm-calc-measure-create` | write | implemented | `execute_sdm-calc-measure-create` | — |
| `sdm-calc-measure-delete` | delete | implemented | `execute_sdm-calc-measure-delete` | — |
| `sdm-calc-measure-get` | read | implemented | `execute_sdm-calc-measure-get` | — |
| `sdm-calc-measure-update` | write | implemented | `execute_sdm-calc-measure-update` | — |
| `sdm-calc-measures-list` | read | implemented | `execute_sdm-calc-measures-list` | — |

### Read operations

#### `sdm-calc-measure-get`

Get a calculated measurement from a semantic model.

**Call:** `execute_sdm-calc-measure-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_sdm_calc_measure_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_sdm-calc-measure-get) for the param schema and, where available, a worked example.

#### `sdm-calc-measures-list`

List calculated measurements in a semantic model.

**Call:** `execute_sdm-calc-measures-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_sdm_calc_measures_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_sdm-calc-measures-list) for the param schema and, where available, a worked example.

### Write operations

#### `sdm-calc-measure-create`

Create a calculated measurement in a semantic model. Body: { label, expression, dataType: 'Number', aggregationType: 'UserAgg' }. IMPORTANT: aggregationType 'UserAgg' is REQUIRED for any formula containing aggregation functions (SUM, COUNT, AVG, etc.). Formula syntax uses [DataObject].[Field] references. Use IIF(condition, true_val, false_val) for inline conditionals.

**Call:** `execute_sdm-calc-measure-create`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_sdm_calc_measure_create (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_sdm-calc-measure-create) for the param schema and, where available, a worked example.

#### `sdm-calc-measure-update`

Update a calculated measurement in a semantic model.

**Call:** `execute_sdm-calc-measure-update`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_sdm_calc_measure_update (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_sdm-calc-measure-update) for the param schema and, where available, a worked example.

### Destructive operations

#### `sdm-calc-measure-delete`

Delete a calculated measurement from a semantic model.

**Call:** `execute_sdm-calc-measure-delete`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_sdm_calc_measure_delete (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_sdm-calc-measure-delete) for the param schema and, where available, a worked example.
