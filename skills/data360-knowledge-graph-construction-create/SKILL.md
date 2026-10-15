---
name: data360-knowledge-graph-construction-create
description: "Use this skill when users want to execute Data Cloud KnowledgeGraphConstruction operations via the Data 360 MCP facade. Trigger when users mention data360/knowledge, graph, construction, shared, cdp, mcp, connect, api, shared-cdp-mcp-connect-api."
metadata:
  version: "1.0"
---

# Managing Data360/knowledge Graph Construction

## When to Use This Skill

Execute Data Cloud KnowledgeGraphConstruction operations via the Data 360 MCP facade.

## Workflow

Each step lists an `operation` id. Call describe(<operation>) BEFORE dispatching to get that tool's parameter schema and, where available, a worked example. `paramsJson` decodes to the operation's requestBody schema VERBATIM, including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap or omit it. The only envelope the step handles for you is `{toolName, paramsJson}` (its `invocation` already wraps it); do not POST the operation path directly. If the tool's error suggests `payload_examples`, ignore it — that tool isn't available here; call describe(<operation>) instead.

## Critical Constraints

**Destructive operations — require explicit user confirmation:**

- **`knowledge-graph-construction-delete`** — Delete a Knowledge Graph construction config by name or ID. This permanently 
  - Rollback: No automatic rollback.

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `knowledge-graph-construction-create` | write | implemented | `execute_knowledge-graph-construction-create` | — |
| `knowledge-graph-construction-delete` | delete | implemented | `execute_knowledge-graph-construction-delete` | — |
| `knowledge-graph-construction-get` | read | implemented | `execute_knowledge-graph-construction-get` | — |
| `knowledge-graph-construction-list` | read | implemented | `execute_knowledge-graph-construction-list` | — |
| `knowledge-graph-construction-update` | write | implemented | `execute_knowledge-graph-construction-update` | — |

### Read operations

#### `knowledge-graph-construction-get`

Get a Knowledge Graph construction config by name or ID, including 

**Call:** `execute_knowledge-graph-construction-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_knowledge_graph_construction_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_knowledge-graph-construction-get) for the param schema and, where available, a worked example.

#### `knowledge-graph-construction-list`

List construction configs for a Knowledge Graph. 

**Call:** `execute_knowledge-graph-construction-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_knowledge_graph_construction_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_knowledge-graph-construction-list) for the param schema and, where available, a worked example.

### Write operations

#### `knowledge-graph-construction-create`

Create the construction (build) config for a Knowledge Graph: semantic 

**Call:** `execute_knowledge-graph-construction-create`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_knowledge_graph_construction_create (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_knowledge-graph-construction-create) for the param schema and, where available, a worked example.

#### `knowledge-graph-construction-update`

Update (full replace) an existing Knowledge Graph construction config by name or ID. 

**Call:** `execute_knowledge-graph-construction-update`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_knowledge_graph_construction_update (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_knowledge-graph-construction-update) for the param schema and, where available, a worked example.

### Destructive operations

#### `knowledge-graph-construction-delete`

Delete a Knowledge Graph construction config by name or ID. This permanently 

**Call:** `execute_knowledge-graph-construction-delete`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_knowledge_graph_construction_delete (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_knowledge-graph-construction-delete) for the param schema and, where available, a worked example.
