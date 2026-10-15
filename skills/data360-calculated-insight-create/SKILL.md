---
name: data360-calculated-insight-create
description: "Use this skill when users want to execute Data Cloud CalculatedInsight operations via the Data 360 MCP facade. Trigger when users mention data360/calculated, insight, shared, cdp, mcp, connect, api, shared-cdp-mcp-connect-api."
metadata:
  version: "1.0"
---

# Managing Data360/calculated Insight

## When to Use This Skill

Execute Data Cloud CalculatedInsight operations via the Data 360 MCP facade.

## Workflow

Each step lists an `operation` id. Call describe(<operation>) BEFORE dispatching to get that tool's parameter schema and, where available, a worked example. `paramsJson` decodes to the operation's requestBody schema VERBATIM, including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap or omit it. The only envelope the step handles for you is `{toolName, paramsJson}` (its `invocation` already wraps it); do not POST the operation path directly. If the tool's error suggests `payload_examples`, ignore it — that tool isn't available here; call describe(<operation>) instead.

## Critical Constraints

**Destructive operations — require explicit user confirmation:**

- **`ci-delete`** — Delete a calculated insight by apiName. Removes the CI definition and downstream queries against it will fail.
  - Rollback: No automatic rollback.

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `ci-create` | write | implemented | `execute_ci-create` | — |
| `ci-delete` | delete | implemented | `execute_ci-delete` | — |
| `ci-disable` | write | implemented | `execute_ci-disable` | — |
| `ci-enable` | write | implemented | `execute_ci-enable` | — |
| `ci-get` | read | implemented | `execute_ci-get` | — |
| `ci-list` | read | implemented | `execute_ci-list` | — |
| `ci-run` | write | implemented | `execute_ci-run` | — |
| `ci-run-status` | read | implemented | `execute_ci-run-status` | — |
| `ci-update` | write | implemented | `execute_ci-update` | — |
| `ci-validate` | read | implemented | `execute_ci-validate` | — |

### Read operations

#### `ci-get`

Get a specific calculated insight by its apiName. Returns the full definition including dimensions, measures, and SQL.

**Call:** `execute_ci-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_ci_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_ci-get) for the param schema and, where available, a worked example.

#### `ci-list`

List calculated insights. Optionally filter by definitionType (one of CalculatedMetric, StreamingMetric, ExternalMetric, GraphMetric, HistoryMetric) 

**Call:** `execute_ci-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_ci_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_ci-list) for the param schema and, where available, a worked example.

#### `ci-run-status`

Get the latest run status of a calculated insight by apiName. Use after d360_ci_run to poll for completion or failure.

**Call:** `execute_ci-run-status`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_ci_run_status (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_ci-run-status) for the param schema and, where available, a worked example.

#### `ci-validate`

Validate a calculated insight SQL definition before creation or update; returns syntax/semantics errors without persisting the CI. 

**Call:** `execute_ci-validate`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_ci_validate (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_ci-validate) for the param schema and, where available, a worked example.

### Write operations

#### `ci-create`

Create a new calculated insight (CI). The 'input' object fields are: apiName (developer name), displayName, 

**Call:** `execute_ci-create`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_ci_create (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_ci-create) for the param schema and, where available, a worked example.

#### `ci-disable`

Disable a calculated insight by apiName. Stops scheduled runs; existing materialized data remains until the CI is re-enabled or deleted.

**Call:** `execute_ci-disable`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_ci_disable (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_ci-disable) for the param schema and, where available, a worked example.

#### `ci-enable`

Enable a calculated insight by apiName so it runs on its scheduled cadence and is queryable. 

**Call:** `execute_ci-enable`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_ci_enable (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_ci-enable) for the param schema and, where available, a worked example.

#### `ci-run`

Trigger an on-demand run of a calculated insight by apiName. Use d360_ci_run_status to poll completion.

**Call:** `execute_ci-run`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_ci_run (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_ci-run) for the param schema and, where available, a worked example.

#### `ci-update`

Update an existing calculated insight by apiName. Use to revise SQL, dimensions, measures, or metadata. Also the path to publish a DRAFT CI: call with draft=false. 

**Call:** `execute_ci-update`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_ci_update (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_ci-update) for the param schema and, where available, a worked example.

### Destructive operations

#### `ci-delete`

Delete a calculated insight by apiName. Removes the CI definition and downstream queries against it will fail.

**Call:** `execute_ci-delete`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_ci_delete (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_ci-delete) for the param schema and, where available, a worked example.
