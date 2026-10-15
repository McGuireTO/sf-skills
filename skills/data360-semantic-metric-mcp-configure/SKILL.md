---
name: data360-semantic-metric-mcp-configure
description: "Use this skill when users want to execute Data Cloud SemanticMetric operations via the Data 360 MCP facade. Trigger when users mention data360/semantic, metric, shared, cdp, mcp, connect, api, shared-cdp-mcp-connect-api."
metadata:
  version: "1.0"
---

# Managing Data360/semantic Metric

## When to Use This Skill

Execute Data Cloud SemanticMetric operations via the Data 360 MCP facade.

## Workflow

Each step lists an `operation` id. Call describe(<operation>) BEFORE dispatching to get that tool's parameter schema and, where available, a worked example. `paramsJson` decodes to the operation's requestBody schema VERBATIM, including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap or omit it. The only envelope the step handles for you is `{toolName, paramsJson}` (its `invocation` already wraps it); do not POST the operation path directly. If the tool's error suggests `payload_examples`, ignore it — that tool isn't available here; call describe(<operation>) instead.

## Critical Constraints

**Destructive operations — require explicit user confirmation:**

- **`sdm-metric-delete`** — Delete a metric from a semantic model.
  - Rollback: No automatic rollback.

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `sdm-metric-create` | write | implemented | `execute_sdm-metric-create` | — |
| `sdm-metric-delete` | delete | implemented | `execute_sdm-metric-delete` | — |
| `sdm-metric-get` | read | implemented | `execute_sdm-metric-get` | — |
| `sdm-metric-update` | write | implemented | `execute_sdm-metric-update` | — |
| `sdm-metrics-list` | read | implemented | `execute_sdm-metrics-list` | — |

### Read operations

#### `sdm-metric-get`

Get a metric from a semantic model.

**Call:** `execute_sdm-metric-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_sdm_metric_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_sdm-metric-get) for the param schema and, where available, a worked example.

#### `sdm-metrics-list`

List metrics in a semantic model.

**Call:** `execute_sdm-metrics-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_sdm_metrics_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_sdm-metrics-list) for the param schema and, where available, a worked example.

### Write operations

#### `sdm-metric-create`

Create a metric in a semantic model.

**Call:** `execute_sdm-metric-create`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_sdm_metric_create (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_sdm-metric-create) for the param schema and, where available, a worked example.

#### `sdm-metric-update`

Update a metric in a semantic model.

**Call:** `execute_sdm-metric-update`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_sdm_metric_update (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_sdm-metric-update) for the param schema and, where available, a worked example.

### Destructive operations

#### `sdm-metric-delete`

Delete a metric from a semantic model.

**Call:** `execute_sdm-metric-delete`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_sdm_metric_delete (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_sdm-metric-delete) for the param schema and, where available, a worked example.
