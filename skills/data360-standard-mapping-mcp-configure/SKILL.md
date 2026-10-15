---
name: data360-standard-mapping-mcp-configure
description: "Use this skill when users want to execute Data Cloud StandardMapping operations via the Data 360 MCP facade. Trigger when users mention data360/standard, mapping, shared, cdp, mcp, connect, api, shared-cdp-mcp-connect-api."
metadata:
  version: "1.0"
---

# Managing Data360/standard Mapping

## When to Use This Skill

Execute Data Cloud StandardMapping operations via the Data 360 MCP facade.

## Workflow

Each step lists an `operation` id. Call describe(<operation>) BEFORE dispatching to get that tool's parameter schema and, where available, a worked example. `paramsJson` decodes to the operation's requestBody schema VERBATIM, including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap or omit it. The only envelope the step handles for you is `{toolName, paramsJson}` (its `invocation` already wraps it); do not POST the operation path directly. If the tool's error suggests `payload_examples`, ignore it — that tool isn't available here; call describe(<operation>) instead.

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `create-standard-mapping` | write | implemented | `execute_create-standard-mapping` | — |

### Write operations

#### `create-standard-mapping`

Create the standard Data Cloud mapping for a single DLO of an opinionated standard Salesforce object. Given one DLO developer name, checks whether it is opinionated and, if so, triggers its standard mapping deployment. Returns success=true with the mapped DLO developer name when the mapping was created, or success=false when the DLO was not mapped.

**Call:** `execute_create-standard-mapping`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_create_standard_mapping (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_create-standard-mapping) for the param schema and, where available, a worked example.
