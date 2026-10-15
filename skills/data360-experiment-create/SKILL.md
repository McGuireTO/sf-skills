---
name: data360-experiment-create
description: "Use this skill when users want to execute Data Cloud IExperimentService operations via the Data 360 MCP facade. Trigger when users mention data360/experiment, shared, cdp, mcp, connect, api, shared-cdp-mcp-connect-api."
metadata:
  version: "1.0"
---

# Managing Data360/experiment

## When to Use This Skill

Execute Data Cloud IExperimentService operations via the Data 360 MCP facade.

## Workflow

Each step lists an `operation` id. Call describe(<operation>) BEFORE dispatching to get that tool's parameter schema and, where available, a worked example. `paramsJson` decodes to the operation's requestBody schema VERBATIM, including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap or omit it. The only envelope the step handles for you is `{toolName, paramsJson}` (its `invocation` already wraps it); do not POST the operation path directly. If the tool's error suggests `payload_examples`, ignore it — that tool isn't available here; call describe(<operation>) instead.

## Critical Constraints

**Destructive operations — require explicit user confirmation:**

- **`personalization-setup-experiment-delete`** — Delete an A/B/n experiment by its ID or name.
  - Rollback: No automatic rollback.

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `personalization-setup-experiment-create` | write | implemented | `execute_personalization-setup-experiment-create` | — |
| `personalization-setup-experiment-delete` | delete | implemented | `execute_personalization-setup-experiment-delete` | — |
| `personalization-setup-experiment-get` | read | implemented | `execute_personalization-setup-experiment-get` | — |
| `personalization-setup-experiment-update` | write | implemented | `execute_personalization-setup-experiment-update` | — |

### Read operations

#### `personalization-setup-experiment-get`

Get a specific A/B/n experiment by its ID or name. Returns the full experiment definition 

**Call:** `execute_personalization-setup-experiment-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_personalization_setup_experiment_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_personalization-setup-experiment-get) for the param schema and, where available, a worked example.

### Write operations

#### `personalization-setup-experiment-create`

Create a new A/B/n experiment for personalization. Specify cohorts with allocation weights, 

**Call:** `execute_personalization-setup-experiment-create`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_personalization_setup_experiment_create (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_personalization-setup-experiment-create) for the param schema and, where available, a worked example.

#### `personalization-setup-experiment-update`

Update an A/B/n experiment by its ID or name. Use the action parameter to perform a 

**Call:** `execute_personalization-setup-experiment-update`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_personalization_setup_experiment_update (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_personalization-setup-experiment-update) for the param schema and, where available, a worked example.

### Destructive operations

#### `personalization-setup-experiment-delete`

Delete an A/B/n experiment by its ID or name.

**Call:** `execute_personalization-setup-experiment-delete`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_personalization_setup_experiment_delete (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_personalization-setup-experiment-delete) for the param schema and, where available, a worked example.
