---
name: data360-semantic-data-object-mcp-configure
description: "Use this skill when users want to execute Data Cloud SemanticDataObject operations via the Data 360 MCP facade. Trigger when users mention data360/semantic, data, object, shared, cdp, mcp, connect, api, shared-cdp-mcp-connect-api."
metadata:
  version: "1.0"
---

# Managing Data360/semantic Data Object

## When to Use This Skill

Execute Data Cloud SemanticDataObject operations via the Data 360 MCP facade.

## Workflow

Each step lists an `operation` id. Call describe(<operation>) BEFORE dispatching to get that tool's parameter schema and, where available, a worked example. `paramsJson` decodes to the operation's requestBody schema VERBATIM, including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap or omit it. The only envelope the step handles for you is `{toolName, paramsJson}` (its `invocation` already wraps it); do not POST the operation path directly. If the tool's error suggests `payload_examples`, ignore it — that tool isn't available here; call describe(<operation>) instead.

## Critical Constraints

**Destructive operations — require explicit user confirmation:**

- **`sdm-data-object-delete`** — Delete a data object from a semantic model.
  - Rollback: No automatic rollback.

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `sdm-data-object-create` | write | implemented | `execute_sdm-data-object-create` | — |
| `sdm-data-object-delete` | delete | implemented | `execute_sdm-data-object-delete` | — |
| `sdm-data-object-get` | read | implemented | `execute_sdm-data-object-get` | — |
| `sdm-data-object-update` | write | implemented | `execute_sdm-data-object-update` | — |
| `sdm-data-objects-list` | read | implemented | `execute_sdm-data-objects-list` | — |

### Read operations

#### `sdm-data-object-get`

Get a data object from a semantic model.

**Call:** `execute_sdm-data-object-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_sdm_data_object_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_sdm-data-object-get) for the param schema and, where available, a worked example.

#### `sdm-data-objects-list`

List data objects in a semantic model.

**Call:** `execute_sdm-data-objects-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_sdm_data_objects_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_sdm-data-objects-list) for the param schema and, where available, a worked example.

### Write operations

#### `sdm-data-object-create`

Add an existing Data Cloud Object as a new Semantic Data Object to a specific Semantic Model. Required body: { dataObjectName, label, dataObjectType, shouldIncludeAllFields }. dataObjectType values: 'Dmo' for DMOs, 'Dlo' for DLOs, 'Cio' for Calculated Insights (NOT 'CalculatedInsight'). Use shouldIncludeAllFields: true to auto-include all fields as dimensions/measurements.

**Call:** `execute_sdm-data-object-create`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_sdm_data_object_create (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_sdm-data-object-create) for the param schema and, where available, a worked example.

#### `sdm-data-object-update`

Update a data object in a semantic model.

**Call:** `execute_sdm-data-object-update`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_sdm_data_object_update (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_sdm-data-object-update) for the param schema and, where available, a worked example.

### Destructive operations

#### `sdm-data-object-delete`

Delete a data object from a semantic model.

**Call:** `execute_sdm-data-object-delete`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_sdm_data_object_delete (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_sdm-data-object-delete) for the param schema and, where available, a worked example.
