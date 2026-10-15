---
name: data360-semantic-model-mcp-configure
description: "Use this skill when users want to execute Data Cloud SemanticModel operations via the Data 360 MCP facade. Trigger when users mention data360/semantic, model, shared, cdp, mcp, connect, api, shared-cdp-mcp-connect-api."
metadata:
  version: "1.0"
---

# Managing Data360/semantic Model

## When to Use This Skill

Execute Data Cloud SemanticModel operations via the Data 360 MCP facade.

## Workflow

Each step lists an `operation` id. Call describe(<operation>) BEFORE dispatching to get that tool's parameter schema and, where available, a worked example. `paramsJson` decodes to the operation's requestBody schema VERBATIM, including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap or omit it. The only envelope the step handles for you is `{toolName, paramsJson}` (its `invocation` already wraps it); do not POST the operation path directly. If the tool's error suggests `payload_examples`, ignore it — that tool isn't available here; call describe(<operation>) instead.

## Critical Constraints

**Destructive operations — require explicit user confirmation:**

- **`sdm-delete`** — Delete a semantic data model.
  - Rollback: No automatic rollback.

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `sdm-clone` | write | implemented | `execute_sdm-clone` | — |
| `sdm-create` | write | implemented | `execute_sdm-create` | — |
| `sdm-delete` | delete | implemented | `execute_sdm-delete` | — |
| `sdm-get` | read | implemented | `execute_sdm-get` | — |
| `sdm-list` | read | implemented | `execute_sdm-list` | — |
| `sdm-update` | write | implemented | `execute_sdm-update` | — |
| `sdm-validate` | read | implemented | `execute_sdm-validate` | — |

### Read operations

#### `sdm-get`

Get a semantic data model by API name or ID.

**Call:** `execute_sdm-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_sdm_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_sdm-get) for the param schema and, where available, a worked example.

#### `sdm-list`

List semantic data models in the org. All parameters are optional; with no filters returns all models the caller can see. 

**Call:** `execute_sdm-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_sdm_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_sdm-list) for the param schema and, where available, a worked example.

#### `sdm-validate`

Validate a semantic data model.

**Call:** `execute_sdm-validate`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_sdm_validate (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_sdm-validate) for the param schema and, where available, a worked example.

### Write operations

#### `sdm-clone`

Clone a semantic data model.

**Call:** `execute_sdm-clone`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_sdm_clone (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_sdm-clone) for the param schema and, where available, a worked example.

#### `sdm-create`

Create a semantic data model shell. Body: { apiName, label, description, dataspace (REQUIRED in body) }. Then add data objects, relationships, calc dims/measures via separate tools. DEPENDENCY: All CIs/DMOs must exist before adding as data objects.

**Call:** `execute_sdm-create`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_sdm_create (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_sdm-create) for the param schema and, where available, a worked example.

#### `sdm-update`

Updates specific entity fields in the Semantic Model object without affecting child dependencies or relationships.

**Call:** `execute_sdm-update`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_sdm_update (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_sdm-update) for the param schema and, where available, a worked example.

### Destructive operations

#### `sdm-delete`

Delete a semantic data model.

**Call:** `execute_sdm-delete`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_sdm_delete (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_sdm-delete) for the param schema and, where available, a worked example.
