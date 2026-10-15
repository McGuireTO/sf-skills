---
name: data360-activation-external-platform-get
description: "Use this skill when users want to execute Data Cloud ActivationExternalPlatform operations via the Data 360 MCP facade. Trigger when users mention data360/activation, external, platform, shared, cdp, mcp, connect, api, shared-cdp-mcp-connect-api."
metadata:
  version: "1.0"
---

# Querying Data360/activation External Platform

## When to Use This Skill

Execute Data Cloud ActivationExternalPlatform operations via the Data 360 MCP facade.

## Workflow

Each step lists an `operation` id. Call describe(<operation>) BEFORE dispatching to get that tool's parameter schema and, where available, a worked example. `paramsJson` decodes to the operation's requestBody schema VERBATIM, including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap or omit it. The only envelope the step handles for you is `{toolName, paramsJson}` (its `invocation` already wraps it); do not POST the operation path directly. If the tool's error suggests `payload_examples`, ignore it — that tool isn't available here; call describe(<operation>) instead.

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `activation-external-platform-get` | read | implemented | `execute_activation-external-platform-get` | — |
| `activation-external-platforms-list` | read | implemented | `execute_activation-external-platforms-list` | — |

### Read operations

#### `activation-external-platform-get`

Get a specific activation external platform by record Id or developer name. Optionally scope the returned attribute configuration to a standard event / action source.

**Call:** `execute_activation-external-platform-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_activation_external_platform_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_activation-external-platform-get) for the param schema and, where available, a worked example.

#### `activation-external-platforms-list`

List all available activation external platforms (destination systems for data activation). 

**Call:** `execute_activation-external-platforms-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_activation_external_platforms_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_activation-external-platforms-list) for the param schema and, where available, a worked example.
