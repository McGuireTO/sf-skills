---
name: data360-harmonized-unstructured-dmo-create
description: "Use this skill when users want to execute Data Cloud HarmonizedUnstructuredDmo operations via the Data 360 MCP facade. Trigger when users mention data360/harmonized, unstructured, dmo, shared, cdp, mcp, connect, api, shared-cdp-mcp-connect-api."
metadata:
  version: "1.0"
---

# Managing Data360/harmonized Unstructured Dmo

## When to Use This Skill

Execute Data Cloud HarmonizedUnstructuredDmo operations via the Data 360 MCP facade.

## Workflow

Each step lists an `operation` id. Call describe(<operation>) BEFORE dispatching to get that tool's parameter schema and, where available, a worked example. `paramsJson` decodes to the operation's requestBody schema VERBATIM, including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap or omit it. The only envelope the step handles for you is `{toolName, paramsJson}` (its `invocation` already wraps it); do not POST the operation path directly. If the tool's error suggests `payload_examples`, ignore it — that tool isn't available here; call describe(<operation>) instead.

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `ek-harmonization-config-create` | write | implemented | `execute_ek-harmonization-config-create` | — |
| `ek-harmonization-config-list` | read | implemented | `execute_ek-harmonization-config-list` | — |
| `ek-harmonization-trigger` | write | implemented | `execute_ek-harmonization-trigger` | — |
| `ek-harmonized-content-get` | read | implemented | `execute_ek-harmonized-content-get` | — |
| `ek-knowledge-harmonization-config-create` | write | implemented | `execute_ek-knowledge-harmonization-config-create` | — |

### Read operations

#### `ek-harmonization-config-list`

lists all unstructured harmonization configs (HUDMOs) in the org; use to discover configApiName/processingId to feed d360_ek_harmonization_status or d360_ek_harmonization_trigger.

**Call:** `execute_ek-harmonization-config-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_ek_harmonization_config_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_ek-harmonization-config-list) for the param schema and, where available, a worked example.

#### `ek-harmonized-content-get`

fetch harmonized unstructured DMO (HUDMO) content for a record by hudmoName + recordId.

**Call:** `execute_ek-harmonized-content-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_ek_harmonized_content_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_ek-harmonized-content-get) for the param schema and, where available, a worked example.

### Write operations

#### `ek-harmonization-config-create`

creates the unstructured harmonization config (HUDLO+HUDMO) and runs harmonization synchronously; on completion poll d360_ek_harmonization_status by configApiName/processingId — do NOT retry create.

**Call:** `execute_ek-harmonization-config-create`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_ek_harmonization_config_create (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_ek-harmonization-config-create) for the param schema and, where available, a worked example.

#### `ek-harmonization-trigger`

RECOVERY ONLY — re-trigger harmonization for an existing config; not a normal forward step.

**Call:** `execute_ek-harmonization-trigger`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_ek_harmonization_trigger (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_ek-harmonization-trigger) for the param schema and, where available, a worked example.

#### `ek-knowledge-harmonization-config-create`

creates the structured Knowledge Article harmonization config (HDLO+HDMO, optional attachment DLO/DMO) and runs harmonization synchronously; on completion poll d360_ek_harmonization_status by configApiName/processingId — do NOT retry create.

**Call:** `execute_ek-knowledge-harmonization-config-create`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_ek_knowledge_harmonization_config_create (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_ek-knowledge-harmonization-config-create) for the param schema and, where available, a worked example.
