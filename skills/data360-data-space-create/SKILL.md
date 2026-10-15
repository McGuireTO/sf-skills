---
name: data360-data-space-create
description: "Use this skill when users want to execute Data Cloud DataSpace operations via the Data 360 MCP facade. Trigger when users mention data360/data, space, shared, cdp, mcp, connect, api, shared-cdp-mcp-connect-api."
metadata:
  version: "1.0"
---

# Managing Data360/data Space

## When to Use This Skill

Execute Data Cloud DataSpace operations via the Data 360 MCP facade.

## Workflow

Each step lists an `operation` id. Call describe(<operation>) BEFORE dispatching to get that tool's parameter schema and, where available, a worked example. `paramsJson` decodes to the operation's requestBody schema VERBATIM, including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap or omit it. The only envelope the step handles for you is `{toolName, paramsJson}` (its `invocation` already wraps it); do not POST the operation path directly. If the tool's error suggests `payload_examples`, ignore it — that tool isn't available here; call describe(<operation>) instead.

## Critical Constraints

**Destructive operations — require explicit user confirmation:**

- **`dataspace-delete`** — Delete a data space by ID or developer name (idOrName, e.g. 'North_America'). This is destructive — it removes the data space definition. The default data space cannot be deleted, and deletion may be rejected if members or dependent assets are still linked.
  - Rollback: No automatic rollback.
- **`dataspace-member-remove`** — Remove one or more members (DLOs/DMOs) from a data space by data space idOrName and dataSpaceMemberObjectName. Unlinks the member from the dataspace without deleting the underlying entity.
  - Rollback: No automatic rollback.

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `dataspace-create` | write | implemented | `execute_dataspace-create` | — |
| `dataspace-delete` | delete | implemented | `execute_dataspace-delete` | — |
| `dataspace-get` | read | implemented | `execute_dataspace-get` | — |
| `dataspace-list` | read | implemented | `execute_dataspace-list` | — |
| `dataspace-member-add` | write | implemented | `execute_dataspace-member-add` | — |
| `dataspace-member-get` | read | implemented | `execute_dataspace-member-get` | — |
| `dataspace-member-list` | read | implemented | `execute_dataspace-member-list` | — |
| `dataspace-member-remove` | delete | implemented | `execute_dataspace-member-remove` | — |
| `dataspace-member-retry` | write | implemented | `execute_dataspace-member-retry` | — |
| `dataspace-retry` | write | implemented | `execute_dataspace-retry` | — |
| `dataspace-update` | write | implemented | `execute_dataspace-update` | — |

### Read operations

#### `dataspace-get`

Get a specific data space by ID or developer name (idOrName). Returns name, label, filter definitions, prefix, and metadata.

**Call:** `execute_dataspace-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_dataspace_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_dataspace-get) for the param schema and, where available, a worked example.

#### `dataspace-list`

List all data spaces in the org. All parameters are optional; supports pagination (batchSize/offset) and ordering. A data space is an isolated workspace for segregating Data Cloud assets; most operations require a dataspace name (e.g. 'default').

**Call:** `execute_dataspace-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_dataspace_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_dataspace-list) for the param schema and, where available, a worked example.

#### `dataspace-member-get`

Get a single data space member (DLO/DMO) by data space idOrName and dataSpaceMemberObjectName. Returns the member entity reference and any dataspace-specific filter applied to it.

**Call:** `execute_dataspace-member-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_dataspace_member_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_dataspace-member-get) for the param schema and, where available, a worked example.

#### `dataspace-member-list`

List all members (DLOs/DMOs) of a data space by idOrName. Supports pagination (batchSize with either offset or an opaque continuationToken for keyset paging) and ordering. Use to discover what entities are linked to a given dataspace.

**Call:** `execute_dataspace-member-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_dataspace_member_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_dataspace-member-list) for the param schema and, where available, a worked example.

### Write operations

#### `dataspace-create`

Create a new data space. Provide name, label, and optional filter definitions. Use to isolate a set of DLOs/DMOs/segments from other workloads in the same org.

**Call:** `execute_dataspace-create`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_dataspace_create (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_dataspace-create) for the param schema and, where available, a worked example.

#### `dataspace-member-add`

Upsert (add or update) one or more members in a data space by idOrName. Use to link DLOs/DMOs to a dataspace and optionally apply per-member filter criteria.

**Call:** `execute_dataspace-member-add`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_dataspace_member_add (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_dataspace-member-add) for the param schema and, where available, a worked example.

#### `dataspace-member-retry`

Retry off-core sync for a data space member (DLO/DMO) in an error state, addressed by data space idOrName and dataSpaceMemberObjectName (the DLO/DMO developer name, e.g. 'Individual__dll' for the Individual DLO). Use when the member failed to propagate to off-core metadata services and needs to be re-synced.

**Call:** `execute_dataspace-member-retry`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_dataspace_member_retry (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_dataspace-member-retry) for the param schema and, where available, a worked example.

#### `dataspace-retry`

Retry off-core sync for a data space in an error state, addressed by ID or developer name (idOrName, e.g. 'North_America'). Use when the data space failed to propagate to off-core metadata services and needs to be re-synced.

**Call:** `execute_dataspace-retry`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_dataspace_retry (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_dataspace-retry) for the param schema and, where available, a worked example.

#### `dataspace-update`

Update an existing data space by ID or developer name. Only label and description can be updated; prefix is immutable once the data space exists.

**Call:** `execute_dataspace-update`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_dataspace_update (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_dataspace-update) for the param schema and, where available, a worked example.

### Destructive operations

#### `dataspace-delete`

Delete a data space by ID or developer name (idOrName, e.g. 'North_America'). This is destructive — it removes the data space definition. The default data space cannot be deleted, and deletion may be rejected if members or dependent assets are still linked.

**Call:** `execute_dataspace-delete`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_dataspace_delete (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_dataspace-delete) for the param schema and, where available, a worked example.

#### `dataspace-member-remove`

Remove one or more members (DLOs/DMOs) from a data space by data space idOrName and dataSpaceMemberObjectName. Unlinks the member from the dataspace without deleting the underlying entity.

**Call:** `execute_dataspace-member-remove`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_dataspace_member_remove (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_dataspace-member-remove) for the param schema and, where available, a worked example.
