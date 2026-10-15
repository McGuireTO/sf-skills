---
name: data360-secondary-index-mcp-configure
description: "Use this skill when users want to execute Data Cloud SecondaryIndex operations via the Data 360 MCP facade. Trigger when users mention data360/secondary, index, shared, cdp, mcp, connect, api, shared-cdp-mcp-connect-api."
metadata:
  version: "1.0"
---

# Managing Data360/secondary Index

## When to Use This Skill

Execute Data Cloud SecondaryIndex operations via the Data 360 MCP facade.

## Workflow

Each step lists an `operation` id. Call describe(<operation>) BEFORE dispatching to get that tool's parameter schema and, where available, a worked example. `paramsJson` decodes to the operation's requestBody schema VERBATIM, including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap or omit it. The only envelope the step handles for you is `{toolName, paramsJson}` (its `invocation` already wraps it); do not POST the operation path directly. If the tool's error suggests `payload_examples`, ignore it — that tool isn't available here; call describe(<operation>) instead.

## Critical Constraints

**Destructive operations — require explicit user confirmation:**

- **`secondary-index-delete`** — Delete a secondary index by its developer name or Salesforce ID. This removes the index configuration and associated platform entities.
  - Rollback: No automatic rollback.

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `secondary-index-create` | write | implemented | `execute_secondary-index-create` | — |
| `secondary-index-delete` | delete | implemented | `execute_secondary-index-delete` | — |
| `secondary-index-get` | read | implemented | `execute_secondary-index-get` | — |
| `secondary-index-list` | read | implemented | `execute_secondary-index-list` | — |
| `secondary-index-run-history` | read | implemented | `execute_secondary-index-run-history` | — |
| `secondary-index-schedule-get` | read | implemented | `execute_secondary-index-schedule-get` | — |
| `secondary-index-schedule-update` | write | implemented | `execute_secondary-index-schedule-update` | — |
| `secondary-index-status` | read | implemented | `execute_secondary-index-status` | — |

### Read operations

#### `secondary-index-get`

Retrieve a specific secondary index by its developer name or Salesforce ID. Returns detailed configuration including fields, source object, and related entities.

**Call:** `execute_secondary-index-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_secondary_index_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_secondary-index-get) for the param schema and, where available, a worked example.

#### `secondary-index-list`

List all secondary indexes configured in the org with optional filtering, sorting and pagination. Use d360_secondary_index_get to fetch a specific one by developer name or id.

**Call:** `execute_secondary-index-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_secondary_index_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_secondary-index-list) for the param schema and, where available, a worked example.

#### `secondary-index-run-history`

Retrieve the run history for a secondary index by its developer name or ID. Shows execution results, timestamps, and status of past index builds.

**Call:** `execute_secondary-index-run-history`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_secondary_index_run_history (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_secondary-index-run-history) for the param schema and, where available, a worked example.

#### `secondary-index-schedule-get`

Get the schedule configuration for a secondary index by its developer name or ID. Returns frequency, timing, and recurrence settings.

**Call:** `execute_secondary-index-schedule-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_secondary_index_schedule_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_secondary-index-schedule-get) for the param schema and, where available, a worked example.

#### `secondary-index-status`

Get the aggregated status of a secondary index and its related platform entities by developer name or ID. Returns health, runtime status, and related entity states.

**Call:** `execute_secondary-index-status`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_secondary_index_status (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_secondary-index-status) for the param schema and, where available, a worked example.

### Write operations

#### `secondary-index-create`

Create a new secondary index. Specify the source object, fields to index, and related entity configurations.

**Call:** `execute_secondary-index-create`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_secondary_index_create (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_secondary-index-create) for the param schema and, where available, a worked example.

#### `secondary-index-schedule-update`

Update the schedule configuration for a secondary index. Modify frequency, timing, and recurrence settings for automated index builds.

**Call:** `execute_secondary-index-schedule-update`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_secondary_index_schedule_update (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_secondary-index-schedule-update) for the param schema and, where available, a worked example.

### Destructive operations

#### `secondary-index-delete`

Delete a secondary index by its developer name or Salesforce ID. This removes the index configuration and associated platform entities.

**Call:** `execute_secondary-index-delete`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_secondary_index_delete (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_secondary-index-delete) for the param schema and, where available, a worked example.
