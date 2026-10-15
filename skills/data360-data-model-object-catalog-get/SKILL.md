---
name: data360-data-model-object-catalog-get
description: "Use this skill when users want to execute Data Cloud DataModelObjectCatalog operations via the Data 360 MCP facade. Trigger when users mention data360/data, model, object, catalog, shared, cdp, mcp, connect, api, shared-cdp-mcp-connect-api."
metadata:
  version: "1.0"
---

# Querying Data360/data Model Object Catalog

## When to Use This Skill

Execute Data Cloud DataModelObjectCatalog operations via the Data 360 MCP facade.

## Workflow

Each step lists an `operation` id. Call describe(<operation>) BEFORE dispatching to get that tool's parameter schema and, where available, a worked example. `paramsJson` decodes to the operation's requestBody schema VERBATIM, including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap or omit it. The only envelope the step handles for you is `{toolName, paramsJson}` (its `invocation` already wraps it); do not POST the operation path directly. If the tool's error suggests `payload_examples`, ignore it — that tool isn't available here; call describe(<operation>) instead.

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `data-model-object-get` | read | implemented | `execute_data-model-object-get` | — |
| `data-model-objects-list` | read | implemented | `execute_data-model-objects-list` | — |

### Read operations

#### `data-model-object-get`

Get a single standard Data Cloud data model object (model / object / DMO) by its name. Returns the model's name, label, type, description, and its fields (each with name, label, and type). Use d360_data_model_objects_list to discover available model names.

**Call:** `execute_data-model-object-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_model_object_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-model-object-get) for the param schema and, where available, a worked example.

#### `data-model-objects-list`

List the standard Data Cloud data model objects (models / objects / DMOs) available to map to. Supports pagination and ordering, plus an optional search that matches on either the model name or its label (case-insensitive, minimum 3 characters). Returns each model's name, label, type, and description; call d360_data_model_object_get for a model's fields.

**Call:** `execute_data-model-objects-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_model_objects_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-model-objects-list) for the param schema and, where available, a worked example.
