---
name: data360-data-lake-object-create
description: "Use this skill when users want to execute Data Cloud DataLakeObject operations via the Data 360 MCP facade. Trigger when users mention data360/data, lake, object, shared, cdp, mcp, connect, api, shared-cdp-mcp-connect-api."
metadata:
  version: "1.0"
---

# Managing Data360/data Lake Object

## When to Use This Skill

Execute Data Cloud DataLakeObject operations via the Data 360 MCP facade.

## Workflow

Each step lists an `operation` id. Call describe(<operation>) BEFORE dispatching to get that tool's parameter schema and, where available, a worked example. `paramsJson` decodes to the operation's requestBody schema VERBATIM, including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap or omit it. The only envelope the step handles for you is `{toolName, paramsJson}` (its `invocation` already wraps it); do not POST the operation path directly. If the tool's error suggests `payload_examples`, ignore it — that tool isn't available here; call describe(<operation>) instead.

## Critical Constraints

**Destructive operations — require explicit user confirmation:**

- **`dlo-delete`** — Delete a Data Lake Object. Use this to remove a DLO and its data from the data lake. Ensure no mappings or data streams reference it before deleting.
  - Rollback: No automatic rollback.
- **`dlo-field-delete`** — Delete a field from a Data Lake Object.
  - Rollback: No automatic rollback.
- **`dlo-kq-remove`** — Remove the Key Qualifier designation from a Data Lake Object field. The field itself is not deleted — only the Key Qualifier designation is cleared.
  - Rollback: No automatic rollback.

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `dlo-create` | write | implemented | `execute_dlo-create` | — |
| `dlo-delete` | delete | implemented | `execute_dlo-delete` | — |
| `dlo-dependencies-list` | read | implemented | `execute_dlo-dependencies-list` | — |
| `dlo-field-delete` | delete | implemented | `execute_dlo-field-delete` | — |
| `dlo-get` | read | implemented | `execute_dlo-get` | — |
| `dlo-kq-dependencies-list` | read | implemented | `execute_dlo-kq-dependencies-list` | — |
| `dlo-kq-get` | read | implemented | `execute_dlo-kq-get` | — |
| `dlo-kq-list` | read | implemented | `execute_dlo-kq-list` | — |
| `dlo-kq-remove` | delete | implemented | `execute_dlo-kq-remove` | — |
| `dlo-kq-retry` | write | implemented | `execute_dlo-kq-retry` | — |
| `dlo-kq-upsert` | write | implemented | `execute_dlo-kq-upsert` | — |
| `dlo-list` | read | implemented | `execute_dlo-list` | — |
| `dlo-refresh-history-list` | read | implemented | `execute_dlo-refresh-history-list` | — |
| `dlo-retry` | write | implemented | `execute_dlo-retry` | — |
| `dlo-update` | write | implemented | `execute_dlo-update` | — |

### Read operations

#### `dlo-dependencies-list`

List entities that depend on a Data Lake Object. Use as a pre-flight check before deleting the Data Lake Object.

**Call:** `execute_dlo-dependencies-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_dlo_dependencies_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_dlo-dependencies-list) for the param schema and, where available, a worked example.

#### `dlo-get`

Get ONE DLO with all field definitions by API name. PREREQUISITE for creating mappings - returns exact field API names needed for sourceFieldName values. Pair with d360_dmo_get for target field names.

**Call:** `execute_dlo-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_dlo_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_dlo-get) for the param schema and, where available, a worked example.

#### `dlo-kq-dependencies-list`

List entities that depend on a specific Key Qualifier of a Data Lake Object. Use as a pre-flight check before removing the Key Qualifier.

**Call:** `execute_dlo-kq-dependencies-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_dlo_kq_dependencies_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_dlo-kq-dependencies-list) for the param schema and, where available, a worked example.

#### `dlo-kq-get`

Get a single Key Qualifier designation on a Data Lake Object by its record id or developer name.

**Call:** `execute_dlo-kq-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_dlo_kq_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_dlo-kq-get) for the param schema and, where available, a worked example.

#### `dlo-kq-list`

List all Key Qualifier designations configured on a Data Lake Object.

**Call:** `execute_dlo-kq-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_dlo_kq_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_dlo-kq-list) for the param schema and, where available, a worked example.

#### `dlo-list`

List all Data Lake Objects (DLOs) - raw ingested data sources. Essential for discovering DLO names and field API names before creating mappings.

**Call:** `execute_dlo-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_dlo_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_dlo-list) for the param schema and, where available, a worked example.

#### `dlo-refresh-history-list`

List the most recent 50 refresh history records for a Data Lake Object, ordered by refresh start time descending.

**Call:** `execute_dlo-refresh-history-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_dlo_refresh_history_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_dlo-refresh-history-list) for the param schema and, where available, a worked example.

### Write operations

#### `dlo-create`

Create a new Data Lake Object. Typically created automatically via data stream ingestion, but can be created manually for custom use cases. Specify fields, types, and category.

**Call:** `execute_dlo-create`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_dlo_create (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_dlo-create) for the param schema and, where available, a worked example.

#### `dlo-kq-retry`

Retry a Key Qualifier that is in ERROR status on a Data Lake Object.

**Call:** `execute_dlo-kq-retry`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_dlo_kq_retry (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_dlo-kq-retry) for the param schema and, where available, a worked example.

#### `dlo-kq-upsert`

Add or update the Key Qualifier designation on a Data Lake Object field. Only the Constant type is accepted.

**Call:** `execute_dlo-kq-upsert`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_dlo_kq_upsert (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_dlo-kq-upsert) for the param schema and, where available, a worked example.

#### `dlo-retry`

Retry a Data Lake Object that is in ERROR status.

**Call:** `execute_dlo-retry`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_dlo_retry (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_dlo-retry) for the param schema and, where available, a worked example.

#### `dlo-update`

Update an existing Data Lake Object. Use this to modify a DLO's schema - add or change fields, update labels, or adjust field types.

**Call:** `execute_dlo-update`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_dlo_update (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_dlo-update) for the param schema and, where available, a worked example.

### Destructive operations

#### `dlo-delete`

Delete a Data Lake Object. Use this to remove a DLO and its data from the data lake. Ensure no mappings or data streams reference it before deleting.

**Call:** `execute_dlo-delete`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_dlo_delete (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_dlo-delete) for the param schema and, where available, a worked example.

#### `dlo-field-delete`

Delete a field from a Data Lake Object.

**Call:** `execute_dlo-field-delete`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_dlo_field_delete (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_dlo-field-delete) for the param schema and, where available, a worked example.

#### `dlo-kq-remove`

Remove the Key Qualifier designation from a Data Lake Object field. The field itself is not deleted — only the Key Qualifier designation is cleared.

**Call:** `execute_dlo-kq-remove`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_dlo_kq_remove (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_dlo-kq-remove) for the param schema and, where available, a worked example.
