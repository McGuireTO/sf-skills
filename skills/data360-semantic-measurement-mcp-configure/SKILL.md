---
name: data360-semantic-measurement-mcp-configure
description: "Use this skill when users want to execute Data Cloud SemanticMeasurement operations via the Data 360 MCP facade. Trigger when users mention data360/semantic, measurement, shared, cdp, mcp, connect, api, shared-cdp-mcp-connect-api."
metadata:
  version: "1.0"
---

# Querying Data360/semantic Measurement

## When to Use This Skill

Execute Data Cloud SemanticMeasurement operations via the Data 360 MCP facade.

## Workflow

Each step lists an `operation` id. Call describe(<operation>) BEFORE dispatching to get that tool's parameter schema and, where available, a worked example. `paramsJson` decodes to the operation's requestBody schema VERBATIM, including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap or omit it. The only envelope the step handles for you is `{toolName, paramsJson}` (its `invocation` already wraps it); do not POST the operation path directly. If the tool's error suggests `payload_examples`, ignore it — that tool isn't available here; call describe(<operation>) instead.

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `sdm-measurements-list` | read | implemented | `execute_sdm-measurements-list` | — |

### Read operations

#### `sdm-measurements-list`

List measurements for a data object in a semantic model.

**Call:** `execute_sdm-measurements-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_sdm_measurements_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_sdm-measurements-list) for the param schema and, where available, a worked example.
