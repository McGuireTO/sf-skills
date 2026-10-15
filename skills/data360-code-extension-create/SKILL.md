---
name: data360-code-extension-create
description: "Use this skill when users want to execute Data Cloud CodeExtension operations via the Data 360 MCP facade. Trigger when users mention data360/code, extension, shared, cdp, mcp, connect, api, shared-cdp-mcp-connect-api."
metadata:
  version: "1.0"
---

# Managing Data360/code Extension

## When to Use This Skill

Execute Data Cloud CodeExtension operations via the Data 360 MCP facade.

## Workflow

Each step lists an `operation` id. Call describe(<operation>) BEFORE dispatching to get that tool's parameter schema and, where available, a worked example. `paramsJson` decodes to the operation's requestBody schema VERBATIM, including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap or omit it. The only envelope the step handles for you is `{toolName, paramsJson}` (its `invocation` already wraps it); do not POST the operation path directly. If the tool's error suggests `payload_examples`, ignore it — that tool isn't available here; call describe(<operation>) instead.

## Critical Constraints

**Destructive operations — require explicit user confirmation:**

- **`code-extension-delete`** — Delete a Code Extension (BYOC) deployment by record id or developer name. Only accepted when status is Active or Deleting; the API returns 400 otherwise.
  - Rollback: No automatic rollback.

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `code-extension-create` | write | implemented | `execute_code-extension-create` | — |
| `code-extension-delete` | delete | implemented | `execute_code-extension-delete` | — |
| `code-extension-execution-get` | read | implemented | `execute_code-extension-execution-get` | — |
| `code-extension-executions-list` | read | implemented | `execute_code-extension-executions-list` | — |
| `code-extension-get` | read | implemented | `execute_code-extension-get` | — |
| `code-extension-list` | read | implemented | `execute_code-extension-list` | — |
| `code-extension-update` | write | implemented | `execute_code-extension-update` | — |

### Read operations

#### `code-extension-execution-get`

Get details of a single Code Extension (BYOC) execution: status, rowsRead, rowsWritten, durationInSeconds, computeType, errorCode, errorMessage. SCRIPT-ONLY: Function deployments return 405.

**Call:** `execute_code-extension-execution-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_code_extension_execution_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_code-extension-execution-get) for the param schema and, where available, a worked example.

#### `code-extension-executions-list`

List paginated executions of a Code Extension (BYOC) deployment. SCRIPT-ONLY: Function deployments return 405. Pagination: limit (1-200), offset, orderBy (e.g. 'StartTime DESC'). Use d360_code_extension_execution_get for one.

**Call:** `execute_code-extension-executions-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_code_extension_executions_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_code-extension-executions-list) for the param schema and, where available, a worked example.

#### `code-extension-get`

Get a Code Extension (BYOC) deployment by record id (1LX...) or developer name. Returns the deployment definition, codeType, computeType, and deploymentStatus (Initializing -> Scanning -> Deployed | Error).

**Call:** `execute_code-extension-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_code_extension_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_code-extension-get) for the param schema and, where available, a worked example.

#### `code-extension-list`

List Code Extension (BYOC) deployments — customer-owned Python deployed to Data 360. Optional filters: codeType (Script|Function), functionInvokeOption (UnstructuredChunking|BatchTransformCustomNode), deploymentStatus (Initializing|Scanning|Error|Deployed), label (case-insensitive substring). Pagination: limit (1-200), offset, orderBy (e.g. 'CreatedDate DESC'). Use d360_code_extension_get to fetch one by id or developer name.

**Call:** `execute_code-extension-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_code_extension_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_code-extension-list) for the param schema and, where available, a worked example.

### Write operations

#### `code-extension-create`

Create a Code Extension (BYOC) deployment. Returns the created deployment, including a short-lived presigned S3 fileUploadUrl (~15 min TTL) that the caller uploads their code package zip to via HTTP PUT. Required fields: name (developer name; unique), label, version, codeType (Script|Function). Optional: description, computeType (defaults to Cpu_s), functionInvokeOptions (Function deployments only), alwaysReady (Function keep-warm flag), displayFileName (min-version 262). After the zip upload lands, the off-core byoc-service scans it and transitions deploymentStatus Initializing -> Scanning -> Deployed | Error; poll d360_code_extension_get.

**Call:** `execute_code-extension-create`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_code_extension_create (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_code-extension-create) for the param schema and, where available, a worked example.

#### `code-extension-update`

Partially update a Code Extension (BYOC) deployment. Only accepted when deploymentStatus=Deployed; the API returns 400 otherwise. Updatable fields: description, version, computeType, and (Function deployments only) functionInvokeOptions.

**Call:** `execute_code-extension-update`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_code_extension_update (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_code-extension-update) for the param schema and, where available, a worked example.

### Destructive operations

#### `code-extension-delete`

Delete a Code Extension (BYOC) deployment by record id or developer name. Only accepted when status is Active or Deleting; the API returns 400 otherwise.

**Call:** `execute_code-extension-delete`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_code_extension_delete (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_code-extension-delete) for the param schema and, where available, a worked example.
