---
name: data360-data-graph-create
description: "Use this skill when users want to execute Data Cloud DataGraph operations via the Data 360 MCP facade. Trigger when users mention data360/data, graph, shared, cdp, mcp, connect, api, shared-cdp-mcp-connect-api."
metadata:
  version: "1.0"
---

# Managing Data360/data Graph

## When to Use This Skill

Execute Data Cloud DataGraph operations via the Data 360 MCP facade.

## Workflow

Each step lists an `operation` id. Call describe(<operation>) BEFORE dispatching to get that tool's parameter schema and, where available, a worked example. `paramsJson` decodes to the operation's requestBody schema VERBATIM, including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap or omit it. The only envelope the step handles for you is `{toolName, paramsJson}` (its `invocation` already wraps it); do not POST the operation path directly. If the tool's error suggests `payload_examples`, ignore it — that tool isn't available here; call describe(<operation>) instead.

## Critical Constraints

**Destructive operations — require explicit user confirmation:**

- **`data-graph-delete`** — Delete a Data Graph by its dataGraphName. This permanently removes the graph definition; ensure no dependent segments, calculated insights, or activations reference it before deleting.
  - Rollback: No automatic rollback.

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `data-graph-create` | write | implemented | `execute_data-graph-create` | — |
| `data-graph-delete` | delete | implemented | `execute_data-graph-delete` | — |
| `data-graph-get` | read | implemented | `execute_data-graph-get` | — |
| `data-graph-update` | write | implemented | `execute_data-graph-update` | — |

### Read operations

#### `data-graph-get`

Get a Data Graph by its dataGraphName. Returns the graph definition, and optionally calculated insight (CI) and segment usage details via includeCIDetails/includeSegmentDetails.

**Call:** `execute_data-graph-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_graph_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-graph-get) for the param schema and, where available, a worked example.

### Write operations

#### `data-graph-create`

Create a Data Graph from a primary DMO and its related objects/fields for low-latency lookup. Use d360_data_graph_get afterwards to verify the resulting definition.

**Call:** `execute_data-graph-create`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_graph_create (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-graph-create) for the param schema and, where available, a worked example.

#### `data-graph-update`

Update (edit) an existing Data Graph by dataGraphName. Provide the full input definition to redefine the graph, or set editScheduleOnly to true to only update its refresh schedule. Use d360_data_graph_get first to review the current definition.

**Call:** `execute_data-graph-update`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_graph_update (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-graph-update) for the param schema and, where available, a worked example.

### Destructive operations

#### `data-graph-delete`

Delete a Data Graph by its dataGraphName. This permanently removes the graph definition; ensure no dependent segments, calculated insights, or activations reference it before deleting.

**Call:** `execute_data-graph-delete`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_graph_delete (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-graph-delete) for the param schema and, where available, a worked example.
