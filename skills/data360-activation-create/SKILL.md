---
name: data360-activation-create
description: "Use this skill when users want to execute Data Cloud Activation operations via the Data 360 MCP facade. Trigger when users mention data360/activation, shared, cdp, mcp, connect, api, shared-cdp-mcp-connect-api."
metadata:
  version: "1.0"
---

# Managing Data360/activation

## When to Use This Skill

Execute Data Cloud Activation operations via the Data 360 MCP facade.

## Workflow

Each step lists an `operation` id. Call describe(<operation>) BEFORE dispatching to get that tool's parameter schema and, where available, a worked example. `paramsJson` decodes to the operation's requestBody schema VERBATIM, including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap or omit it. The only envelope the step handles for you is `{toolName, paramsJson}` (its `invocation` already wraps it); do not POST the operation path directly. If the tool's error suggests `payload_examples`, ignore it — that tool isn't available here; call describe(<operation>) instead.

## Critical Constraints

**Destructive operations — require explicit user confirmation:**

- **`activation-delete`** — Delete an activation by ID.
  - Rollback: No automatic rollback.

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `activation-create` | write | implemented | `execute_activation-create` | — |
| `activation-delete` | delete | implemented | `execute_activation-delete` | — |
| `activation-get` | read | implemented | `execute_activation-get` | — |
| `activation-list` | read | implemented | `execute_activation-list` | — |
| `activation-publish` | write | implemented | `execute_activation-publish` | — |
| `activation-update` | write | implemented | `execute_activation-update` | — |

### Read operations

#### `activation-get`

Get the details of a specific activation by ID.

**Call:** `execute_activation-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_activation_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_activation-get) for the param schema and, where available, a worked example.

#### `activation-list`

List all activations. Optionally paginate with batchSize and offset, filter with filters, and sort with orderBy.

**Call:** `execute_activation-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_activation_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_activation-list) for the param schema and, where available, a worked example.

### Write operations

#### `activation-create`

Create an activation. Required fields: name, refreshType (exactly FULL_REFRESH or 

**Call:** `execute_activation-create`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_activation_create (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_activation-create) for the param schema and, where available, a worked example.

#### `activation-publish`

Publish an activation on-demand by activation ID. Triggers immediate ad-hoc execution of the activation, 

**Call:** `execute_activation-publish`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_activation_publish (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_activation-publish) for the param schema and, where available, a worked example.

#### `activation-update`

Update an activation by ID. Replaces the activation definition with the provided input.

**Call:** `execute_activation-update`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_activation_update (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_activation-update) for the param schema and, where available, a worked example.

### Destructive operations

#### `activation-delete`

Delete an activation by ID.

**Call:** `execute_activation-delete`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_activation_delete (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_activation-delete) for the param schema and, where available, a worked example.
