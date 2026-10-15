---
name: data360-data-model-object-mapping-create
description: "Use this skill when users want to execute Data Cloud DataModelObjectMapping operations via the Data 360 MCP facade. Trigger when users mention data360/data, model, object, mapping, shared, cdp, mcp, connect, api, shared-cdp-mcp-connect-api."
metadata:
  version: "1.0"
---

# Managing Data360/data Model Object Mapping

## When to Use This Skill

Execute Data Cloud DataModelObjectMapping operations via the Data 360 MCP facade.

## Workflow

Each step lists an `operation` id. Call describe(<operation>) BEFORE dispatching to get that tool's parameter schema and, where available, a worked example. `paramsJson` decodes to the operation's requestBody schema VERBATIM, including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap or omit it. The only envelope the step handles for you is `{toolName, paramsJson}` (its `invocation` already wraps it); do not POST the operation path directly. If the tool's error suggests `payload_examples`, ignore it — that tool isn't available here; call describe(<operation>) instead.

## Critical Constraints

**Destructive operations — require explicit user confirmation:**

- **`dmo-field-mapping-delete`** — Delete a single field mapping from an existing object mapping (e.g. MailingCity__c_fieldmap_ssot__CityId__c) without deleting the entire object mapping.
  - Rollback: No automatic rollback.
- **`dmo-mapping-delete`** — Delete a DMO mapping by its developer name. Removes the DLO-to-DMO field mapping; the data stream and DMO still exist but data will no longer flow into the target DMO from that source.
  - Rollback: No automatic rollback.

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `dmo-field-mapping-add` | write | implemented | `execute_dmo-field-mapping-add` | — |
| `dmo-field-mapping-delete` | delete | implemented | `execute_dmo-field-mapping-delete` | — |
| `dmo-mapping-create` | write | implemented | `execute_dmo-mapping-create` | — |
| `dmo-mapping-delete` | delete | implemented | `execute_dmo-mapping-delete` | — |
| `dmo-mapping-get` | read | implemented | `execute_dmo-mapping-get` | — |
| `dmo-mapping-list` | read | implemented | `execute_dmo-mapping-list` | — |

### Read operations

#### `dmo-mapping-get`

Get a specific DMO mapping by its developer name (e.g. Account_std_map_Account_1000000000000). Returns the field-level mapping between a DLO and DMO.

**Call:** `execute_dmo-mapping-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_dmo_mapping_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_dmo-mapping-get) for the param schema and, where available, a worked example.

#### `dmo-mapping-list`

List DMO mappings filtered by DMO developer name or CRM source object name. Provide either dmoDeveloperName or sourceObjectName (at least one is required).

**Call:** `execute_dmo-mapping-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_dmo_mapping_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_dmo-mapping-list) for the param schema and, where available, a worked example.

### Write operations

#### `dmo-field-mapping-add`

Add field mappings to an existing object mapping between a DLO and DMO without recreating the entire object mapping.

**Call:** `execute_dmo-field-mapping-add`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_dmo_field_mapping_add (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_dmo-field-mapping-add) for the param schema and, where available, a worked example.

#### `dmo-mapping-create`

Create a single DMO mapping (one source-to-DMO mapping per call). DLO field names include a __c suffix (e.g., customer_id__c). Use d360_dlo_get for source field names and d360_dmo_get for target field names. For Engagement DLOs, the event date field MUST be included in the mapping and source/target field types must match exactly.

**Call:** `execute_dmo-mapping-create`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_dmo_mapping_create (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_dmo-mapping-create) for the param schema and, where available, a worked example.

### Destructive operations

#### `dmo-field-mapping-delete`

Delete a single field mapping from an existing object mapping (e.g. MailingCity__c_fieldmap_ssot__CityId__c) without deleting the entire object mapping.

**Call:** `execute_dmo-field-mapping-delete`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_dmo_field_mapping_delete (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_dmo-field-mapping-delete) for the param schema and, where available, a worked example.

#### `dmo-mapping-delete`

Delete a DMO mapping by its developer name. Removes the DLO-to-DMO field mapping; the data stream and DMO still exist but data will no longer flow into the target DMO from that source.

**Call:** `execute_dmo-mapping-delete`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_dmo_mapping_delete (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_dmo-mapping-delete) for the param schema and, where available, a worked example.
