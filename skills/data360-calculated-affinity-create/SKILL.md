---
name: data360-calculated-affinity-create
description: "Use this skill when users want to execute Data Cloud ICalculatedAffinityService operations via the Data 360 MCP facade. Trigger when users mention data360/calculated, affinity, shared, cdp, mcp, connect, api, shared-cdp-mcp-connect-api."
metadata:
  version: "1.0"
---

# Managing Data360/calculated Affinity

## When to Use This Skill

Execute Data Cloud ICalculatedAffinityService operations via the Data 360 MCP facade.

## Workflow

Each step lists an `operation` id. Call describe(<operation>) BEFORE dispatching to get that tool's parameter schema and, where available, a worked example. `paramsJson` decodes to the operation's requestBody schema VERBATIM, including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap or omit it. The only envelope the step handles for you is `{toolName, paramsJson}` (its `invocation` already wraps it); do not POST the operation path directly. If the tool's error suggests `payload_examples`, ignore it — that tool isn't available here; call describe(<operation>) instead.

## Critical Constraints

**Destructive operations — require explicit user confirmation:**

- **`calculated-affinity-delete`** — Delete a Calculated Affinity definition by ID or API name. This permanently removes the affinity model and its configuration. Use this to clean up an affinity model that is no longer needed.
  - Rollback: No automatic rollback.

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `calculated-affinity-create` | write | implemented | `execute_calculated-affinity-create` | — |
| `calculated-affinity-delete` | delete | implemented | `execute_calculated-affinity-delete` | — |
| `calculated-affinity-get` | read | implemented | `execute_calculated-affinity-get` | — |
| `calculated-affinity-list` | read | implemented | `execute_calculated-affinity-list` | — |

### Read operations

#### `calculated-affinity-get`

Get a single Calculated Affinity definition by ID or API name. Returns its configuration for scoring how strongly a profile is associated with a given item or category. Use this to inspect an existing affinity model before updating or deleting it.

**Call:** `execute_calculated-affinity-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_calculated_affinity_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_calculated-affinity-get) for the param schema and, where available, a worked example.

#### `calculated-affinity-list`

List Calculated Affinity definitions configured in the org. Use this to discover which affinity models exist before creating, updating, or deleting one.

**Call:** `execute_calculated-affinity-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_calculated_affinity_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_calculated-affinity-list) for the param schema and, where available, a worked example.

### Write operations

#### `calculated-affinity-create`

Create a new Calculated Affinity definition. Defines how strongly a profile is scored against a given item or category, feeding into recommendations and personalization. Use this to set up a new affinity model.

**Call:** `execute_calculated-affinity-create`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_calculated_affinity_create (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_calculated-affinity-create) for the param schema and, where available, a worked example.

### Destructive operations

#### `calculated-affinity-delete`

Delete a Calculated Affinity definition by ID or API name. This permanently removes the affinity model and its configuration. Use this to clean up an affinity model that is no longer needed.

**Call:** `execute_calculated-affinity-delete`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_calculated_affinity_delete (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_calculated-affinity-delete) for the param schema and, where available, a worked example.
