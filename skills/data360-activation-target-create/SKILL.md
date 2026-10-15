---
name: data360-activation-target-create
description: "Use this skill when users want to execute Data Cloud ActivationTarget operations via the Data 360 MCP facade. Trigger when users mention data360/activation, target, shared, cdp, mcp, connect, api, shared-cdp-mcp-connect-api."
metadata:
  version: "1.0"
---

# Managing Data360/activation Target

## When to Use This Skill

Execute Data Cloud ActivationTarget operations via the Data 360 MCP facade.

## Workflow

Each step lists an `operation` id. Call describe(<operation>) BEFORE dispatching to get that tool's parameter schema and, where available, a worked example. `paramsJson` decodes to the operation's requestBody schema VERBATIM, including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap or omit it. The only envelope the step handles for you is `{toolName, paramsJson}` (its `invocation` already wraps it); do not POST the operation path directly. If the tool's error suggests `payload_examples`, ignore it — that tool isn't available here; call describe(<operation>) instead.

## Critical Constraints

**Destructive operations — require explicit user confirmation:**

- **`activation-target-delete`** — Delete an activation target by ID.
  - Rollback: No automatic rollback.

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `activation-target-create` | write | implemented | `execute_activation-target-create` | — |
| `activation-target-delete` | delete | implemented | `execute_activation-target-delete` | — |
| `activation-target-get` | read | implemented | `execute_activation-target-get` | — |
| `activation-target-list` | read | implemented | `execute_activation-target-list` | — |
| `activation-target-update` | write | implemented | `execute_activation-target-update` | — |

### Read operations

#### `activation-target-get`

Get an activation target by ID.

**Call:** `execute_activation-target-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_activation_target_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_activation-target-get) for the param schema and, where available, a worked example.

#### `activation-target-list`

List activation targets. Optionally paginate with batchSize and offset, filter with filters, and sort with orderBy.

**Call:** `execute_activation-target-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_activation_target_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_activation-target-list) for the param schema and, where available, a worked example.

### Write operations

#### `activation-target-create`

Create an activation target. connector binds polymorphically on platformType and must 

**Call:** `execute_activation-target-create`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_activation_target_create (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_activation-target-create) for the param schema and, where available, a worked example.

#### `activation-target-update`

Update an activation target by ID with partial fields.

**Call:** `execute_activation-target-update`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_activation_target_update (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_activation-target-update) for the param schema and, where available, a worked example.

### Destructive operations

#### `activation-target-delete`

Delete an activation target by ID.

**Call:** `execute_activation-target-delete`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_activation_target_delete (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_activation-target-delete) for the param schema and, where available, a worked example.
