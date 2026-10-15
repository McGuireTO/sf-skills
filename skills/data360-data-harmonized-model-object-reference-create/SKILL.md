---
name: data360-data-harmonized-model-object-reference-create
description: "Use this skill when users want to execute Data Cloud DataHarmonizedModelObjRef operations via the Data 360 MCP facade. Trigger when users mention data360/data, harmonized, model, obj, ref, shared, cdp, mcp, connect, api, shared-cdp-mcp-connect-api."
metadata:
  version: "1.0"
---

# Managing Data360/data Harmonized Model Obj Ref

## When to Use This Skill

Execute Data Cloud DataHarmonizedModelObjRef operations via the Data 360 MCP facade.

## Workflow

Each step lists an `operation` id. Call describe(<operation>) BEFORE dispatching to get that tool's parameter schema and, where available, a worked example. `paramsJson` decodes to the operation's requestBody schema VERBATIM, including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap or omit it. The only envelope the step handles for you is `{toolName, paramsJson}` (its `invocation` already wraps it); do not POST the operation path directly. If the tool's error suggests `payload_examples`, ignore it — that tool isn't available here; call describe(<operation>) instead.

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `ek-dhmor-create` | write | implemented | `execute_ek-dhmor-create` | — |

### Write operations

#### `ek-dhmor-create`

create/get a Data Harmonized Model Object Reference bridging harmonized content to a DMO.

**Call:** `execute_ek-dhmor-create`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_ek_dhmor_create (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_ek-dhmor-create) for the param schema and, where available, a worked example.
