---
name: data360-engagement-signal-get
description: "Use this skill when users want to execute Data Cloud IEngagementSignal operations via the Data 360 MCP facade. Trigger when users mention data360/engagement, signal, shared, cdp, mcp, connect, api, shared-cdp-mcp-connect-api."
metadata:
  version: "1.0"
---

# Querying Data360/engagement Signal

## When to Use This Skill

Execute Data Cloud IEngagementSignal operations via the Data 360 MCP facade.

## Workflow

Each step lists an `operation` id. Call describe(<operation>) BEFORE dispatching to get that tool's parameter schema and, where available, a worked example. `paramsJson` decodes to the operation's requestBody schema VERBATIM, including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap or omit it. The only envelope the step handles for you is `{toolName, paramsJson}` (its `invocation` already wraps it); do not POST the operation path directly. If the tool's error suggests `payload_examples`, ignore it — that tool isn't available here; call describe(<operation>) instead.

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `personalization-engagement-signals-list` | read | implemented | `execute_personalization-engagement-signals-list` | — |

### Read operations

#### `personalization-engagement-signals-list`

List engagement signals configured for a personalization data graph. Returns signal types (click, view, purchase, add-to-cart, etc.) that feed into recommender attribution and objective optimization. Use this to discover which user interactions are tracked before configuring a recommender.

**Call:** `execute_personalization-engagement-signals-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_personalization_engagement_signals_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_personalization-engagement-signals-list) for the param schema and, where available, a worked example.
