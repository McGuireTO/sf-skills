---
name: data360-semantic-calculated-dimension-mcp-configure
description: "Use this skill when users want to execute Data Cloud SemanticCalculatedDimension operations via the Data 360 MCP facade. Trigger when users mention data360/semantic, calculated, dimension, shared, cdp, mcp, connect, api, shared-cdp-mcp-connect-api."
metadata:
  version: "1.0"
---

# Managing Data360/semantic Calculated Dimension

## When to Use This Skill

Execute Data Cloud SemanticCalculatedDimension operations via the Data 360 MCP facade.

## Workflow

Each step lists an `operation` id. Call describe(<operation>) BEFORE dispatching to get that tool's parameter schema and, where available, a worked example. `paramsJson` decodes to the operation's requestBody schema VERBATIM, including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap or omit it. The only envelope the step handles for you is `{toolName, paramsJson}` (its `invocation` already wraps it); do not POST the operation path directly. If the tool's error suggests `payload_examples`, ignore it — that tool isn't available here; call describe(<operation>) instead.

## Critical Constraints

**Destructive operations — require explicit user confirmation:**

- **`sdm-calc-dim-delete`** — Delete a calculated dimension from a semantic model.
  - Rollback: No automatic rollback.

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `sdm-calc-dim-create` | write | implemented | `execute_sdm-calc-dim-create` | — |
| `sdm-calc-dim-delete` | delete | implemented | `execute_sdm-calc-dim-delete` | — |
| `sdm-calc-dim-get` | read | implemented | `execute_sdm-calc-dim-get` | — |
| `sdm-calc-dim-update` | write | implemented | `execute_sdm-calc-dim-update` | — |
| `sdm-calc-dims-list` | read | implemented | `execute_sdm-calc-dims-list` | — |

### Read operations

#### `sdm-calc-dim-get`

Get a calculated dimension from a semantic model.

**Call:** `execute_sdm-calc-dim-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_sdm_calc_dim_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_sdm-calc-dim-get) for the param schema and, where available, a worked example.

#### `sdm-calc-dims-list`

List calculated dimensions in a semantic model.

**Call:** `execute_sdm-calc-dims-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_sdm_calc_dims_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_sdm-calc-dims-list) for the param schema and, where available, a worked example.

### Write operations

#### `sdm-calc-dim-create`

Create a calculated dimension in a semantic model. Body: { label, expression, dataType: 'Text'|'Number'|'DateTime' }. Formula syntax uses [DataObject].[Field] references (NOT {field}). Use IF/ELSEIF/ELSE/END for conditionals (not CASE WHEN). Example: IF [MyObj].[field1] > 10 THEN 'High' ELSE 'Low' END

**Call:** `execute_sdm-calc-dim-create`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_sdm_calc_dim_create (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_sdm-calc-dim-create) for the param schema and, where available, a worked example.

#### `sdm-calc-dim-update`

Update a calculated dimension in a semantic model.

**Call:** `execute_sdm-calc-dim-update`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_sdm_calc_dim_update (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_sdm-calc-dim-update) for the param schema and, where available, a worked example.

### Destructive operations

#### `sdm-calc-dim-delete`

Delete a calculated dimension from a semantic model.

**Call:** `execute_sdm-calc-dim-delete`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_sdm_calc_dim_delete (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_sdm-calc-dim-delete) for the param schema and, where available, a worked example.
