---
name: data360-data-model-object-create
description: "Use this skill when users want to execute Data Cloud DataModelObject operations via the Data 360 MCP facade. Trigger when users mention data360/data, model, object, shared, cdp, mcp, connect, api, shared-cdp-mcp-connect-api."
metadata:
  version: "1.0"
---

# Managing Data360/data Model Object

## When to Use This Skill

Execute Data Cloud DataModelObject operations via the Data 360 MCP facade.

## Workflow

Each step lists an `operation` id. Call describe(<operation>) BEFORE dispatching to get that tool's parameter schema and, where available, a worked example. `paramsJson` decodes to the operation's requestBody schema VERBATIM, including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap or omit it. The only envelope the step handles for you is `{toolName, paramsJson}` (its `invocation` already wraps it); do not POST the operation path directly. If the tool's error suggests `payload_examples`, ignore it — that tool isn't available here; call describe(<operation>) instead.

## Critical Constraints

**Destructive operations — require explicit user confirmation:**

- **`dmo-delete`** — Delete a Data Model Object.
  - Rollback: No automatic rollback.
- **`dmo-relationship-delete`** — Delete a DMO relationship by name. Only Custom relationships can 
  - Rollback: No automatic rollback.

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `dmo-create` | write | implemented | `execute_dmo-create` | — |
| `dmo-delete` | delete | implemented | `execute_dmo-delete` | — |
| `dmo-get` | read | implemented | `execute_dmo-get` | — |
| `dmo-list` | read | implemented | `execute_dmo-list` | — |
| `dmo-relationship-create` | write | implemented | `execute_dmo-relationship-create` | — |
| `dmo-relationship-delete` | delete | implemented | `execute_dmo-relationship-delete` | — |
| `dmo-relationship-list` | read | implemented | `execute_dmo-relationship-list` | — |
| `dmo-update` | write | implemented | `execute_dmo-update` | — |

### Read operations

#### `dmo-get`

Get a specific Data Model Object by name with all field definitions. 

**Call:** `execute_dmo-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_dmo_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_dmo-get) for the param schema and, where available, a worked example.

#### `dmo-list`

List the Data Model Objects (DMOs) in this org, excluding the standard/canonical DMOs (those are listed by d360_data_model_objects_list). Returns customer-created and derived DMOs — custom, SQL/transform, segment membership, calculated insight, and so on. Supports pagination and ordering, plus optional filters on data space, category, and enablement.

**Call:** `execute_dmo-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_dmo_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_dmo-list) for the param schema and, where available, a worked example.

#### `dmo-relationship-list`

List the relationships where the provided Data Model Object (DMO) is the source or 

**Call:** `execute_dmo-relationship-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_dmo_relationship_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_dmo-relationship-list) for the param schema and, where available, a worked example.

### Write operations

#### `dmo-create`

Create a new Data Model Object. 

**Call:** `execute_dmo-create`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_dmo_create (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_dmo-create) for the param schema and, where available, a worked example.

#### `dmo-relationship-create`

Create one or more relationships on a Data Model Object (DMO). The DMO must be 

**Call:** `execute_dmo-relationship-create`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_dmo_relationship_create (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_dmo-relationship-create) for the param schema and, where available, a worked example.

#### `dmo-update`

Update an existing Data Model Object.

**Call:** `execute_dmo-update`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_dmo_update (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_dmo-update) for the param schema and, where available, a worked example.

### Destructive operations

#### `dmo-delete`

Delete a Data Model Object.

**Call:** `execute_dmo-delete`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_dmo_delete (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_dmo-delete) for the param schema and, where available, a worked example.

#### `dmo-relationship-delete`

Delete a DMO relationship by name. Only Custom relationships can 

**Call:** `execute_dmo-relationship-delete`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_dmo_relationship_delete (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_dmo-relationship-delete) for the param schema and, where available, a worked example.
