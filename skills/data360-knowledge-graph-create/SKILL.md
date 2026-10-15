---
name: data360-knowledge-graph-create
description: "Use this skill when users want to execute Data Cloud KnowledgeGraph operations via the Data 360 MCP facade. Trigger when users mention data360/knowledge, graph, shared, cdp, mcp, connect, api, shared-cdp-mcp-connect-api."
metadata:
  version: "1.0"
---

# Managing Data360/knowledge Graph

## When to Use This Skill

Execute Data Cloud KnowledgeGraph operations via the Data 360 MCP facade.

## Workflow

Each step lists an `operation` id. Call describe(<operation>) BEFORE dispatching to get that tool's parameter schema and, where available, a worked example. `paramsJson` decodes to the operation's requestBody schema VERBATIM, including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap or omit it. The only envelope the step handles for you is `{toolName, paramsJson}` (its `invocation` already wraps it); do not POST the operation path directly. If the tool's error suggests `payload_examples`, ignore it — that tool isn't available here; call describe(<operation>) instead.

## Critical Constraints

**Destructive operations — require explicit user confirmation:**

- **`knowledge-graph-delete`** — Delete a Knowledge Graph by name or ID. This permanently removes the graph 
  - Rollback: No automatic rollback.
- **`knowledge-graph-extraction-delete`** — Delete a Knowledge Graph extraction definition by name. This permanently 
  - Rollback: No automatic rollback.

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `knowledge-graph-build` | write | implemented | `execute_knowledge-graph-build` | — |
| `knowledge-graph-build-status` | read | implemented | `execute_knowledge-graph-build-status` | — |
| `knowledge-graph-create` | write | implemented | `execute_knowledge-graph-create` | — |
| `knowledge-graph-delete` | delete | implemented | `execute_knowledge-graph-delete` | — |
| `knowledge-graph-extraction-create` | write | implemented | `execute_knowledge-graph-extraction-create` | — |
| `knowledge-graph-extraction-delete` | delete | implemented | `execute_knowledge-graph-extraction-delete` | — |
| `knowledge-graph-extraction-get` | read | implemented | `execute_knowledge-graph-extraction-get` | — |
| `knowledge-graph-extraction-list` | read | implemented | `execute_knowledge-graph-extraction-list` | — |
| `knowledge-graph-extraction-update` | write | implemented | `execute_knowledge-graph-extraction-update` | — |
| `knowledge-graph-get` | read | implemented | `execute_knowledge-graph-get` | — |
| `knowledge-graph-list` | read | implemented | `execute_knowledge-graph-list` | — |
| `knowledge-graph-presign-urls` | read | implemented | `execute_knowledge-graph-presign-urls` | — |
| `knowledge-graph-replace` | write | implemented | `execute_knowledge-graph-replace` | — |
| `knowledge-graph-suggest-smart-config` | read | implemented | `execute_knowledge-graph-suggest-smart-config` | — |
| `knowledge-graph-suggest-smart-config-status` | read | implemented | `execute_knowledge-graph-suggest-smart-config-status` | — |
| `knowledge-graph-update` | write | implemented | `execute_knowledge-graph-update` | — |

### Read operations

#### `knowledge-graph-build-status`

KG Playground, step 6 poll: get the status of the current playground (REALTIME) 

**Call:** `execute_knowledge-graph-build-status`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_knowledge_graph_build_status (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_knowledge-graph-build-status) for the param schema and, where available, a worked example.

#### `knowledge-graph-extraction-get`

Get a Knowledge Graph extraction definition by name. 

**Call:** `execute_knowledge-graph-extraction-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_knowledge_graph_extraction_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_knowledge-graph-extraction-get) for the param schema and, where available, a worked example.

#### `knowledge-graph-extraction-list`

List Knowledge Graph extraction definitions, with paging (limit, offset). 

**Call:** `execute_knowledge-graph-extraction-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_knowledge_graph_extraction_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_knowledge-graph-extraction-list) for the param schema and, where available, a worked example.

#### `knowledge-graph-get`

Get a Knowledge Graph by name or ID, including the resolved (suffixed) 

**Call:** `execute_knowledge-graph-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_knowledge_graph_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_knowledge-graph-get) for the param schema and, where available, a worked example.

#### `knowledge-graph-list`

List Knowledge Graphs in the org, with paging (limit, offset). 

**Call:** `execute_knowledge-graph-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_knowledge_graph_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_knowledge-graph-list) for the param schema and, where available, a worked example.

#### `knowledge-graph-presign-urls`

KG Playground, step 1 (REALTIME/playground graphs only): request presigned upload 

**Call:** `execute_knowledge-graph-presign-urls`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_knowledge_graph_presign_urls (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_knowledge-graph-presign-urls) for the param schema and, where available, a worked example.

#### `knowledge-graph-suggest-smart-config`

KG Playground, step 4 (submit): kick off an async AI recommendation that returns an 

**Call:** `execute_knowledge-graph-suggest-smart-config`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_knowledge_graph_suggest_smart_config (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_knowledge-graph-suggest-smart-config) for the param schema and, where available, a worked example.

#### `knowledge-graph-suggest-smart-config-status`

KG Playground, step 4 poll: get the status/result of the current 

**Call:** `execute_knowledge-graph-suggest-smart-config-status`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_knowledge_graph_suggest_smart_config_status (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_knowledge-graph-suggest-smart-config-status) for the param schema and, where available, a worked example.

### Write operations

#### `knowledge-graph-build`

KG Playground, step 6 (final playground step): trigger an async build of a 

**Call:** `execute_knowledge-graph-build`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_knowledge_graph_build (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_knowledge-graph-build) for the param schema and, where available, a worked example.

#### `knowledge-graph-create`

Create a Data Cloud Knowledge Graph in a data space. FIRST ASK THE USER: 

**Call:** `execute_knowledge-graph-create`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_knowledge_graph_create (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_knowledge-graph-create) for the param schema and, where available, a worked example.

#### `knowledge-graph-extraction-create`

Create an extraction (LLM mining job) that pulls entities and relationships 

**Call:** `execute_knowledge-graph-extraction-create`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_knowledge_graph_extraction_create (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_knowledge-graph-extraction-create) for the param schema and, where available, a worked example.

#### `knowledge-graph-extraction-update`

Update (full replace) an existing Knowledge Graph extraction definition by name. 

**Call:** `execute_knowledge-graph-extraction-update`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_knowledge_graph_extraction_update (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_knowledge-graph-extraction-update) for the param schema and, where available, a worked example.

#### `knowledge-graph-replace`

Replace (full update) an existing Knowledge Graph by name or ID. PUT 

**Call:** `execute_knowledge-graph-replace`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_knowledge_graph_replace (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_knowledge-graph-replace) for the param schema and, where available, a worked example.

#### `knowledge-graph-update`

Update an existing Knowledge Graph by name or ID (partial update of its 

**Call:** `execute_knowledge-graph-update`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_knowledge_graph_update (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_knowledge-graph-update) for the param schema and, where available, a worked example.

### Destructive operations

#### `knowledge-graph-delete`

Delete a Knowledge Graph by name or ID. This permanently removes the graph 

**Call:** `execute_knowledge-graph-delete`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_knowledge_graph_delete (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_knowledge-graph-delete) for the param schema and, where available, a worked example.

#### `knowledge-graph-extraction-delete`

Delete a Knowledge Graph extraction definition by name. This permanently 

**Call:** `execute_knowledge-graph-extraction-delete`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_knowledge_graph_extraction_delete (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_knowledge-graph-extraction-delete) for the param schema and, where available, a worked example.
