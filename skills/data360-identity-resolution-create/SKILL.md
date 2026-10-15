---
name: data360-identity-resolution-create
description: "Use this skill when users want to execute Data Cloud IdentityResolution operations via the Data 360 MCP facade. Trigger when users mention data360/identity, resolution, shared, cdp, mcp, connect, api, shared-cdp-mcp-connect-api."
metadata:
  version: "1.0"
---

# Managing Data360/identity Resolution

## When to Use This Skill

Execute Data Cloud IdentityResolution operations via the Data 360 MCP facade.

## Workflow

Each step lists an `operation` id. Call describe(<operation>) BEFORE dispatching to get that tool's parameter schema and, where available, a worked example. `paramsJson` decodes to the operation's requestBody schema VERBATIM, including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap or omit it. The only envelope the step handles for you is `{toolName, paramsJson}` (its `invocation` already wraps it); do not POST the operation path directly. If the tool's error suggests `payload_examples`, ignore it — that tool isn't available here; call describe(<operation>) instead.

## Critical Constraints

**Destructive operations — require explicit user confirmation:**

- **`ir-delete`** — Delete an identity resolution ruleset by id. Existing unified profiles remain until the unification DMO is also removed.
  - Rollback: No automatic rollback.

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `ir-create` | write | implemented | `execute_ir-create` | — |
| `ir-delete` | delete | implemented | `execute_ir-delete` | — |
| `ir-get` | read | implemented | `execute_ir-get` | — |
| `ir-list` | read | implemented | `execute_ir-list` | — |
| `ir-publish` | write | implemented | `execute_ir-publish` | — |
| `ir-run` | write | implemented | `execute_ir-run` | — |
| `ir-update` | write | implemented | `execute_ir-update` | — |

### Read operations

#### `ir-get`

Get a specific identity resolution ruleset by id. Returns full match rules, source DMOs, and unification target.

**Call:** `execute_ir-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_ir_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_ir-get) for the param schema and, where available, a worked example.

#### `ir-list`

List all identity resolution rulesets configured in the org. Use d360_ir_get to fetch a specific one by id.

**Call:** `execute_ir-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_ir_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_ir-list) for the param schema and, where available, a worked example.

### Write operations

#### `ir-create`

Create a new identity resolution ruleset. Specify match rules, source DMOs, and unification target DMO. Use d360_ir_publish followed by d360_ir_run to materialize unified profiles.

**Call:** `execute_ir-create`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_ir_create (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_ir-create) for the param schema and, where available, a worked example.

#### `ir-publish`

Publish an identity resolution ruleset by id. Promotes the draft to active so it can be executed via d360_ir_run.

**Call:** `execute_ir-publish`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_ir_publish (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_ir-publish) for the param schema and, where available, a worked example.

#### `ir-run`

Trigger an on-demand run of a published identity resolution ruleset by id. Materializes unified profile records into the unification target DMO.

**Call:** `execute_ir-run`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_ir_run (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_ir-run) for the param schema and, where available, a worked example.

#### `ir-update`

Update an existing identity resolution ruleset by id. Use to modify match rules, source DMOs, or unification target. Republish (d360_ir_publish) and rerun (d360_ir_run) to materialize changes.

**Call:** `execute_ir-update`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_ir_update (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_ir-update) for the param schema and, where available, a worked example.

### Destructive operations

#### `ir-delete`

Delete an identity resolution ruleset by id. Existing unified profiles remain until the unification DMO is also removed.

**Call:** `execute_ir-delete`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_ir_delete (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_ir-delete) for the param schema and, where available, a worked example.
