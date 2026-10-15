---
name: data360-data-clean-room-create
description: "Use this skill when users want to execute Data Cloud DataCleanRoom operations via the Data 360 MCP facade. Trigger when users mention data360/data, clean, room, shared, cdp, mcp, connect, api, shared-cdp-mcp-connect-api."
metadata:
  version: "1.0"
---

# Managing Data360/data Clean Room

## When to Use This Skill

Execute Data Cloud DataCleanRoom operations via the Data 360 MCP facade.

## Workflow

Each step lists an `operation` id. Call describe(<operation>) BEFORE dispatching to get that tool's parameter schema and, where available, a worked example. `paramsJson` decodes to the operation's requestBody schema VERBATIM, including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap or omit it. The only envelope the step handles for you is `{toolName, paramsJson}` (its `invocation` already wraps it); do not POST the operation path directly. If the tool's error suggests `payload_examples`, ignore it — that tool isn't available here; call describe(<operation>) instead.

## Critical Constraints

**Destructive operations — require explicit user confirmation:**

- **`dcr-delete-specification`** — Delete a Data Clean Room data specification by ID or API name. Irreversible. 
  - Rollback: No automatic rollback.
- **`dcr-reject-invitation`** — Reject an invitation to join a Data Clean Room collaboration. 
  - Rollback: No automatic rollback.

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `dcr-create-collaboration` | write | implemented | `execute_dcr-create-collaboration` | — |
| `dcr-create-provider` | write | implemented | `execute_dcr-create-provider` | — |
| `dcr-create-specification` | write | implemented | `execute_dcr-create-specification` | — |
| `dcr-delete-specification` | delete | implemented | `execute_dcr-delete-specification` | — |
| `dcr-disable-collaboration` | write | implemented | `execute_dcr-disable-collaboration` | — |
| `dcr-get-provider` | read | implemented | `execute_dcr-get-provider` | — |
| `dcr-list-collaboration-results` | read | implemented | `execute_dcr-list-collaboration-results` | — |
| `dcr-list-collaborations` | read | implemented | `execute_dcr-list-collaborations` | — |
| `dcr-list-collaborations-for-usecase` | read | implemented | `execute_dcr-list-collaborations-for-usecase` | — |
| `dcr-list-providers` | read | implemented | `execute_dcr-list-providers` | — |
| `dcr-list-query-jobs` | read | implemented | `execute_dcr-list-query-jobs` | — |
| `dcr-list-specifications` | read | implemented | `execute_dcr-list-specifications` | — |
| `dcr-list-templates` | read | implemented | `execute_dcr-list-templates` | — |
| `dcr-list-templates-for-provider` | read | implemented | `execute_dcr-list-templates-for-provider` | — |
| `dcr-list-usecases` | read | implemented | `execute_dcr-list-usecases` | — |
| `dcr-refresh-collaboration-metadata` | read | implemented | `execute_dcr-refresh-collaboration-metadata` | — |
| `dcr-reject-invitation` | delete | implemented | `execute_dcr-reject-invitation` | — |
| `dcr-run-query` | write | implemented | `execute_dcr-run-query` | — |

### Read operations

#### `dcr-get-provider`

Get a Data Clean Room provider by record ID or developer name. 

**Call:** `execute_dcr-get-provider`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_dcr_get_provider (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_dcr-get-provider) for the param schema and, where available, a worked example.

#### `dcr-list-collaboration-results`

Get the result DMOs created as a result of a Data Clean Room collaboration. 

**Call:** `execute_dcr-list-collaboration-results`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_dcr_list_collaboration_results (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_dcr-list-collaboration-results) for the param schema and, where available, a worked example.

#### `dcr-list-collaborations`

List Data Clean Room collaborations, paginated. 

**Call:** `execute_dcr-list-collaborations`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_dcr_list_collaborations (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_dcr-list-collaborations) for the param schema and, where available, a worked example.

#### `dcr-list-collaborations-for-usecase`

List Data Clean Room collaborations filtered by use case template type, paginated. 

**Call:** `execute_dcr-list-collaborations-for-usecase`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_dcr_list_collaborations_for_usecase (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_dcr-list-collaborations-for-usecase) for the param schema and, where available, a worked example.

#### `dcr-list-providers`

List Data Clean Room providers, paginated. 

**Call:** `execute_dcr-list-providers`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_dcr_list_providers (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_dcr-list-providers) for the param schema and, where available, a worked example.

#### `dcr-list-query-jobs`

List Data Clean Room query jobs for a collaboration, paginated. 

**Call:** `execute_dcr-list-query-jobs`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_dcr_list_query_jobs (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_dcr-list-query-jobs) for the param schema and, where available, a worked example.

#### `dcr-list-specifications`

List Data Clean Room data specifications, paginated. 

**Call:** `execute_dcr-list-specifications`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_dcr_list_specifications (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_dcr-list-specifications) for the param schema and, where available, a worked example.

#### `dcr-list-templates`

List all Data Clean Room templates available in this org, paginated. 

**Call:** `execute_dcr-list-templates`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_dcr_list_templates (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_dcr-list-templates) for the param schema and, where available, a worked example.

#### `dcr-list-templates-for-provider`

List Data Clean Room templates offered by a specific provider, paginated. 

**Call:** `execute_dcr-list-templates-for-provider`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_dcr_list_templates_for_provider (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_dcr-list-templates-for-provider) for the param schema and, where available, a worked example.

#### `dcr-list-usecases`

List Data Clean Room use cases with their associated template versions, paginated. 

**Call:** `execute_dcr-list-usecases`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_dcr_list_usecases (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_dcr-list-usecases) for the param schema and, where available, a worked example.

#### `dcr-refresh-collaboration-metadata`

Refresh the schema for a Data Clean Room collaboration's result objects. 

**Call:** `execute_dcr-refresh-collaboration-metadata`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_dcr_refresh_collaboration_metadata (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_dcr-refresh-collaboration-metadata) for the param schema and, where available, a worked example.

### Write operations

#### `dcr-create-collaboration`

Create a new Data Clean Room collaboration between this org and a provider. 

**Call:** `execute_dcr-create-collaboration`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_dcr_create_collaboration (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_dcr-create-collaboration) for the param schema and, where available, a worked example.

#### `dcr-create-provider`

Create a new Data Clean Room provider. 

**Call:** `execute_dcr-create-provider`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_dcr_create_provider (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_dcr-create-provider) for the param schema and, where available, a worked example.

#### `dcr-create-specification`

Create a new Data Clean Room data specification that maps this org's data to a template. 

**Call:** `execute_dcr-create-specification`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_dcr_create_specification (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_dcr-create-specification) for the param schema and, where available, a worked example.

#### `dcr-disable-collaboration`

Disable an active Data Clean Room collaboration. 

**Call:** `execute_dcr-disable-collaboration`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_dcr_disable_collaboration (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_dcr-disable-collaboration) for the param schema and, where available, a worked example.

#### `dcr-run-query`

Run a Data Clean Room query job against a collaboration. 

**Call:** `execute_dcr-run-query`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_dcr_run_query (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_dcr-run-query) for the param schema and, where available, a worked example.

### Destructive operations

#### `dcr-delete-specification`

Delete a Data Clean Room data specification by ID or API name. Irreversible. 

**Call:** `execute_dcr-delete-specification`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_dcr_delete_specification (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_dcr-delete-specification) for the param schema and, where available, a worked example.

#### `dcr-reject-invitation`

Reject an invitation to join a Data Clean Room collaboration. 

**Call:** `execute_dcr-reject-invitation`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_dcr_reject_invitation (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_dcr-reject-invitation) for the param schema and, where available, a worked example.
