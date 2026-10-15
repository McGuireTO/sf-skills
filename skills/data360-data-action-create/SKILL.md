---
name: data360-data-action-create
description: "Use this skill when users want to execute Data Cloud DataAction operations via the Data 360 MCP facade. Trigger when users mention data360/data, action, shared, cdp, mcp, connect, api, shared-cdp-mcp-connect-api."
metadata:
  version: "1.0"
---

# Managing Data360/data Action

## When to Use This Skill

Execute Data Cloud DataAction operations via the Data 360 MCP facade.

## Workflow

Each step lists an `operation` id. Call describe(<operation>) BEFORE dispatching to get that tool's parameter schema and, where available, a worked example. `paramsJson` decodes to the operation's requestBody schema VERBATIM, including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap or omit it. The only envelope the step handles for you is `{toolName, paramsJson}` (its `invocation` already wraps it); do not POST the operation path directly. If the tool's error suggests `payload_examples`, ignore it — that tool isn't available here; call describe(<operation>) instead.

## Critical Constraints

**Destructive operations — require explicit user confirmation:**

- **`data-action-delete`** — Delete a data action by developer name.
  - Rollback: No automatic rollback.

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `data-action-create` | write | implemented | `execute_data-action-create` | — |
| `data-action-create-search-index` | write | implemented | `execute_data-action-create-search-index` | — |
| `data-action-create-with-dmo-enrichment` | write | implemented | `execute_data-action-create-with-dmo-enrichment` | — |
| `data-action-delete` | delete | implemented | `execute_data-action-delete` | — |
| `data-action-get` | read | implemented | `execute_data-action-get` | — |
| `data-action-list` | read | implemented | `execute_data-action-list` | — |
| `data-action-metrics-get` | read | implemented | `execute_data-action-metrics-get` | — |
| `data-action-update` | write | implemented | `execute_data-action-update` | — |

### Read operations

#### `data-action-get`

Get a data action by developer name.

**Call:** `execute_data-action-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_action_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-action-get) for the param schema and, where available, a worked example.

#### `data-action-list`

List data actions with pagination, ordering, and optional dataspace filter.

**Call:** `execute_data-action-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_action_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-action-list) for the param schema and, where available, a worked example.

#### `data-action-metrics-get`

Get aggregate event metrics (records processed, produced, published, and 

**Call:** `execute_data-action-metrics-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_action_metrics_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-action-metrics-get) for the param schema and, where available, a worked example.

### Write operations

#### `data-action-create`

Create a data action. Must reference an existing data action target.

**Call:** `execute_data-action-create`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_action_create (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-action-create) for the param schema and, where available, a worked example.

#### `data-action-create-search-index`

Create a data action that notifies target(s) as a search index processes its source records: each record/file the index processes generates an event. The source is the search index's index DMO (pass it as dmoApiName), plus a searchConfig block referencing the search index. 'search index' is not a source type — the source is still a DMO (the index DMO). Use d360_search_index_list to find searchIndexApiName; only vector-type search indexes are supported. Events are limited to CREATE/UPDATE (as records are processed); DELETE is not supported.

**Call:** `execute_data-action-create-search-index`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_action_create_search_index (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-action-create-search-index) for the param schema and, where available, a worked example.

#### `data-action-create-with-dmo-enrichment`

Create a data action on a DMO source enriched by joining to a related DMO, so the related object's fields can be used in conditions and projected fields. Provide relationshipEdges (the join — only 1:1 or N:1 relationships are supported; find a DMO's relationships with d360_dmo_relationship_list) and projectedFields (fields to pull in). sourceSubscriptions (create/update/delete rules) is required; conditions are optional. For a plain source with no enrichment, or a Calculated Insight source, use d360_data_action_create.

**Call:** `execute_data-action-create-with-dmo-enrichment`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_action_create_with_dmo_enrichment (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-action-create-with-dmo-enrichment) for the param schema and, where available, a worked example.

#### `data-action-update`

Update a data action by developer name. Supports updating dataActionStatus to enable/disable the action.

**Call:** `execute_data-action-update`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_action_update (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-action-update) for the param schema and, where available, a worked example.

### Destructive operations

#### `data-action-delete`

Delete a data action by developer name.

**Call:** `execute_data-action-delete`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_action_delete (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-action-delete) for the param schema and, where available, a worked example.
