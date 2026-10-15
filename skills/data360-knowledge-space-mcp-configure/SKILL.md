---
name: data360-knowledge-space-mcp-configure
description: "Use this skill when users want to execute Data Cloud KnowledgeSpace operations via the Data 360 MCP facade. Trigger when users mention data360/knowledge, space, shared, cdp, mcp, connect, api, shared-cdp-mcp-connect-api."
metadata:
  version: "1.0"
---

# Managing Data360/knowledge Space

## When to Use This Skill

Execute Data Cloud KnowledgeSpace operations via the Data 360 MCP facade.

## Workflow

Each step lists an `operation` id. Call describe(<operation>) BEFORE dispatching to get that tool's parameter schema and, where available, a worked example. `paramsJson` decodes to the operation's requestBody schema VERBATIM, including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap or omit it. The only envelope the step handles for you is `{toolName, paramsJson}` (its `invocation` already wraps it); do not POST the operation path directly. If the tool's error suggests `payload_examples`, ignore it — that tool isn't available here; call describe(<operation>) instead.

## Critical Constraints

**Destructive operations — require explicit user confirmation:**

- **`knowledge-space-config-delete`** — Delete a Notebook AI (Knowledge Space) configuration by name or ID.
  - Rollback: No automatic rollback.
- **`knowledge-space-delete`** — Delete a Notebook AI (Knowledge Space) by API name or ID.
  - Rollback: No automatic rollback.
- **`knowledge-space-library-remove`** — Remove a Notebook AI (Knowledge Space) library based on the provided parameters. Returns the removed library confirmation.
  - Rollback: No automatic rollback.
- **`knowledge-space-remove-files`** — Remove files from knowledge space. Deletes specified files and removes them from the search index.
  - Rollback: No automatic rollback.
- **`knowledge-space-session-delete`** — Delete a Notebook AI (Knowledge Space) session by session ID. Permanently removes the session and its conversation history.
  - Rollback: No automatic rollback.

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `knowledge-space-config-create` | write | implemented | `execute_knowledge-space-config-create` | — |
| `knowledge-space-config-delete` | delete | implemented | `execute_knowledge-space-config-delete` | — |
| `knowledge-space-config-get` | read | implemented | `execute_knowledge-space-config-get` | — |
| `knowledge-space-config-list` | read | implemented | `execute_knowledge-space-config-list` | — |
| `knowledge-space-create` | write | implemented | `execute_knowledge-space-create` | — |
| `knowledge-space-deep-research-add-source` | write | implemented | `execute_knowledge-space-deep-research-add-source` | — |
| `knowledge-space-deep-research-cancel` | write | implemented | `execute_knowledge-space-deep-research-cancel` | — |
| `knowledge-space-deep-research-create` | write | implemented | `execute_knowledge-space-deep-research-create` | — |
| `knowledge-space-deep-research-get` | read | implemented | `execute_knowledge-space-deep-research-get` | — |
| `knowledge-space-deep-research-plan-patch` | write | implemented | `execute_knowledge-space-deep-research-plan-patch` | — |
| `knowledge-space-deep-research-report-get` | read | implemented | `execute_knowledge-space-deep-research-report-get` | — |
| `knowledge-space-deep-research-run` | write | implemented | `execute_knowledge-space-deep-research-run` | — |
| `knowledge-space-deep-research-thinking-events-get` | read | implemented | `execute_knowledge-space-deep-research-thinking-events-get` | — |
| `knowledge-space-deep-research-update` | write | implemented | `execute_knowledge-space-deep-research-update` | — |
| `knowledge-space-delete` | delete | implemented | `execute_knowledge-space-delete` | — |
| `knowledge-space-details-get` | read | implemented | `execute_knowledge-space-details-get` | — |
| `knowledge-space-file-summary-get` | read | implemented | `execute_knowledge-space-file-summary-get` | — |
| `knowledge-space-files-status-get` | read | implemented | `execute_knowledge-space-files-status-get` | — |
| `knowledge-space-get` | read | implemented | `execute_knowledge-space-get` | — |
| `knowledge-space-get-import-knowledge` | read | implemented | `execute_knowledge-space-get-import-knowledge` | — |
| `knowledge-space-import-knowledge` | write | implemented | `execute_knowledge-space-import-knowledge` | — |
| `knowledge-space-index-files` | write | implemented | `execute_knowledge-space-index-files` | — |
| `knowledge-space-library-create` | write | implemented | `execute_knowledge-space-library-create` | — |
| `knowledge-space-library-get` | read | implemented | `execute_knowledge-space-library-get` | — |
| `knowledge-space-library-remove` | delete | implemented | `execute_knowledge-space-library-remove` | — |
| `knowledge-space-library-search` | read | implemented | `execute_knowledge-space-library-search` | — |
| `knowledge-space-library-update` | write | implemented | `execute_knowledge-space-library-update` | — |
| `knowledge-space-list` | read | implemented | `execute_knowledge-space-list` | — |
| `knowledge-space-presigned-urls-get` | read | implemented | `execute_knowledge-space-presigned-urls-get` | — |
| `knowledge-space-provision` | write | implemented | `execute_knowledge-space-provision` | — |
| `knowledge-space-remove-files` | delete | implemented | `execute_knowledge-space-remove-files` | — |
| `knowledge-space-research-template-create` | write | implemented | `execute_knowledge-space-research-template-create` | — |
| `knowledge-space-research-template-list` | read | implemented | `execute_knowledge-space-research-template-list` | — |
| `knowledge-space-session-conversation-get` | read | implemented | `execute_knowledge-space-session-conversation-get` | — |
| `knowledge-space-session-create` | write | implemented | `execute_knowledge-space-session-create` | — |
| `knowledge-space-session-delete` | delete | implemented | `execute_knowledge-space-session-delete` | — |
| `knowledge-space-session-get` | read | implemented | `execute_knowledge-space-session-get` | — |
| `knowledge-space-session-list` | read | implemented | `execute_knowledge-space-session-list` | — |
| `knowledge-space-update` | write | implemented | `execute_knowledge-space-update` | — |

### Read operations

#### `knowledge-space-config-get`

Get a specific Notebook AI (Knowledge Space) configuration by name or ID. Returns the config details, settings, and metadata.

**Call:** `execute_knowledge-space-config-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_knowledge_space_config_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_knowledge-space-config-get) for the param schema and, where available, a worked example.

#### `knowledge-space-config-list`

List all knowledge space configurations in the current org. Returns all knowledge space config records with their settings and metadata.

**Call:** `execute_knowledge-space-config-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_knowledge_space_config_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_knowledge-space-config-list) for the param schema and, where available, a worked example.

#### `knowledge-space-deep-research-get`

Get the status, progress, and details of a Notebook AI (Knowledge Space) deep research job by research ID. Returns current execution state, plan steps, and results if completed.

**Call:** `execute_knowledge-space-deep-research-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_knowledge_space_deep_research_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_knowledge-space-deep-research-get) for the param schema and, where available, a worked example.

#### `knowledge-space-deep-research-report-get`

Get the completed Notebook AI (Knowledge Space) deep research report by research ID. Returns the full research findings, analysis, and conclusions in the specified format.

**Call:** `execute_knowledge-space-deep-research-report-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_knowledge_space_deep_research_report_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_knowledge-space-deep-research-report-get) for the param schema and, where available, a worked example.

#### `knowledge-space-deep-research-thinking-events-get`

Get Notebook AI (Knowledge Space) deep research thinking events, optionally filtered by sequence number. Returns a list of thinking events with sequence numbers and current status for polling/streaming progress.

**Call:** `execute_knowledge-space-deep-research-thinking-events-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_knowledge_space_deep_research_thinking_events_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_knowledge-space-deep-research-thinking-events-get) for the param schema and, where available, a worked example.

#### `knowledge-space-details-get`

Get detailed information about a specific Notebook AI (Knowledge Space) by API name or ID. Returns comprehensive notebook details including configuration and metadata.

**Call:** `execute_knowledge-space-details-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_knowledge_space_details_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_knowledge-space-details-get) for the param schema and, where available, a worked example.

#### `knowledge-space-file-summary-get`

Get summary of file chunks in knowledge space. Returns all chunks with metadata for specified files.

**Call:** `execute_knowledge-space-file-summary-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_knowledge_space_file_summary_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_knowledge-space-file-summary-get) for the param schema and, where available, a worked example.

#### `knowledge-space-files-status-get`

Get status of knowledge space files by file IDs. Returns processing status, indexing state, and metadata for specified files.

**Call:** `execute_knowledge-space-files-status-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_knowledge_space_files_status_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_knowledge-space-files-status-get) for the param schema and, where available, a worked example.

#### `knowledge-space-get`

Get a specific Notebook AI (Knowledge Space) by API name or ID. Returns the notebook details, configuration, and metadata.

**Call:** `execute_knowledge-space-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_knowledge_space_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_knowledge-space-get) for the param schema and, where available, a worked example.

#### `knowledge-space-get-import-knowledge`

Get available knowledge for import based on filters. Returns knowledge records matching import criteria before actual import.

**Call:** `execute_knowledge-space-get-import-knowledge`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_knowledge_space_get_import_knowledge (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_knowledge-space-get-import-knowledge) for the param schema and, where available, a worked example.

#### `knowledge-space-library-get`

Get detailed information about a specific Notebook AI (Knowledge Space) library by ID. Returns the library details, configuration, and metadata.

**Call:** `execute_knowledge-space-library-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_knowledge_space_library_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_knowledge-space-library-get) for the param schema and, where available, a worked example.

#### `knowledge-space-library-search`

Search and filter knowledge space libraries based on criteria. Returns matching libraries with metadata.

**Call:** `execute_knowledge-space-library-search`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_knowledge_space_library_search (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_knowledge-space-library-search) for the param schema and, where available, a worked example.

#### `knowledge-space-list`

List all knowledge spaces in the current org. Returns all knowledge space records with their details and metadata.

**Call:** `execute_knowledge-space-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_knowledge_space_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_knowledge-space-list) for the param schema and, where available, a worked example.

#### `knowledge-space-presigned-urls-get`

Get presigned URLs for uploading knowledge files to a library. Returns temporary upload URLs for secure file uploads.

**Call:** `execute_knowledge-space-presigned-urls-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_knowledge_space_presigned_urls_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_knowledge-space-presigned-urls-get) for the param schema and, where available, a worked example.

#### `knowledge-space-research-template-list`

Get all available research templates. Returns all template definitions with their configurations.

**Call:** `execute_knowledge-space-research-template-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_knowledge_space_research_template_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_knowledge-space-research-template-list) for the param schema and, where available, a worked example.

#### `knowledge-space-session-conversation-get`

Get conversation messages for a Notebook AI (Knowledge Space) session. Returns all messages and interactions in the session.

**Call:** `execute_knowledge-space-session-conversation-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_knowledge_space_session_conversation_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_knowledge-space-session-conversation-get) for the param schema and, where available, a worked example.

#### `knowledge-space-session-get`

Get details of a specific Notebook AI (Knowledge Space) session by session ID. Returns session metadata and status.

**Call:** `execute_knowledge-space-session-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_knowledge_space_session_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_knowledge-space-session-get) for the param schema and, where available, a worked example.

#### `knowledge-space-session-list`

List all sessions for a specific Notebook AI (Knowledge Space) with optional limit. Returns all session records.

**Call:** `execute_knowledge-space-session-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_knowledge_space_session_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_knowledge-space-session-list) for the param schema and, where available, a worked example.

### Write operations

#### `knowledge-space-config-create`

Create a new knowledge space configuration with the provided settings. Returns the created knowledge space config details.

**Call:** `execute_knowledge-space-config-create`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_knowledge_space_config_create (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_knowledge-space-config-create) for the param schema and, where available, a worked example.

#### `knowledge-space-create`

Create a new knowledge space with the provided configuration. Returns the created knowledge space with its details and metadata.

**Call:** `execute_knowledge-space-create`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_knowledge_space_create (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_knowledge-space-create) for the param schema and, where available, a worked example.

#### `knowledge-space-deep-research-add-source`

Add a completed Notebook AI (Knowledge Space) deep research report as a data source to a knowledge space. The report is added to the GENERATED_RESOURCES library (creating it if needed) and indexed for future searches.

**Call:** `execute_knowledge-space-deep-research-add-source`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_knowledge_space_deep_research_add_source (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_knowledge-space-deep-research-add-source) for the param schema and, where available, a worked example.

#### `knowledge-space-deep-research-cancel`

Cancel a running Notebook AI (Knowledge Space) deep research job. Optionally request a partial report of findings so far. Returns the updated research status.

**Call:** `execute_knowledge-space-deep-research-cancel`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_knowledge_space_deep_research_cancel (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_knowledge-space-deep-research-cancel) for the param schema and, where available, a worked example.

#### `knowledge-space-deep-research-create`

Create a new Notebook AI (Knowledge Space) deep research plan with query and configuration. Returns the research ID and initial status.

**Call:** `execute_knowledge-space-deep-research-create`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_knowledge_space_deep_research_create (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_knowledge-space-deep-research-create) for the param schema and, where available, a worked example.

#### `knowledge-space-deep-research-plan-patch`

Update a Notebook AI (Knowledge Space) deep research plan before execution. Modify instructions, add/remove steps, or refine the research approach. Must be done before running the research.

**Call:** `execute_knowledge-space-deep-research-plan-patch`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_knowledge_space_deep_research_plan_patch (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_knowledge-space-deep-research-plan-patch) for the param schema and, where available, a worked example.

#### `knowledge-space-deep-research-run`

Run/execute a Notebook AI (Knowledge Space) deep research job that was previously created. Requires the research ID. Returns the updated research status and execution details.

**Call:** `execute_knowledge-space-deep-research-run`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_knowledge_space_deep_research_run (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_knowledge-space-deep-research-run) for the param schema and, where available, a worked example.

#### `knowledge-space-deep-research-update`

Update Notebook AI (Knowledge Space) deep research configuration including query, data sources, output format, locale, or provide edit instructions. Returns updated research configuration and status.

**Call:** `execute_knowledge-space-deep-research-update`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_knowledge_space_deep_research_update (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_knowledge-space-deep-research-update) for the param schema and, where available, a worked example.

#### `knowledge-space-import-knowledge`

Import knowledge into knowledge space based on modal input. Processes and indexes knowledge content from specified source.

**Call:** `execute_knowledge-space-import-knowledge`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_knowledge_space_import_knowledge (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_knowledge-space-import-knowledge) for the param schema and, where available, a worked example.

#### `knowledge-space-index-files`

Index files for knowledge space. Processes and indexes uploaded files to make them searchable.

**Call:** `execute_knowledge-space-index-files`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_knowledge_space_index_files (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_knowledge-space-index-files) for the param schema and, where available, a worked example.

#### `knowledge-space-library-create`

Create a new knowledge space library with the provided configuration. Returns the created library with its details and metadata.

**Call:** `execute_knowledge-space-library-create`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_knowledge_space_library_create (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_knowledge-space-library-create) for the param schema and, where available, a worked example.

#### `knowledge-space-library-update`

Update a Notebook AI (Knowledge Space) library by ID. Returns the updated library with its details and metadata.

**Call:** `execute_knowledge-space-library-update`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_knowledge_space_library_update (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_knowledge-space-library-update) for the param schema and, where available, a worked example.

#### `knowledge-space-provision`

Provision a knowledge space with required infrastructure and configuration. Sets up storage, indexing, and necessary resources.

**Call:** `execute_knowledge-space-provision`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_knowledge_space_provision (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_knowledge-space-provision) for the param schema and, where available, a worked example.

#### `knowledge-space-research-template-create`

Create a new research template with name, file path, description, and type. Templates define research methodologies and workflows.

**Call:** `execute_knowledge-space-research-template-create`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_knowledge_space_research_template_create (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_knowledge-space-research-template-create) for the param schema and, where available, a worked example.

#### `knowledge-space-session-create`

Create a new Notebook AI (Knowledge Space) session for a specific notebook. Returns the created session details.

**Call:** `execute_knowledge-space-session-create`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_knowledge_space_session_create (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_knowledge-space-session-create) for the param schema and, where available, a worked example.

#### `knowledge-space-update`

Update a Notebook AI (Knowledge Space) by API name or ID. Returns the updated notebook with its details and metadata.

**Call:** `execute_knowledge-space-update`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_knowledge_space_update (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_knowledge-space-update) for the param schema and, where available, a worked example.

### Destructive operations

#### `knowledge-space-config-delete`

Delete a Notebook AI (Knowledge Space) configuration by name or ID.

**Call:** `execute_knowledge-space-config-delete`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_knowledge_space_config_delete (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_knowledge-space-config-delete) for the param schema and, where available, a worked example.

#### `knowledge-space-delete`

Delete a Notebook AI (Knowledge Space) by API name or ID.

**Call:** `execute_knowledge-space-delete`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_knowledge_space_delete (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_knowledge-space-delete) for the param schema and, where available, a worked example.

#### `knowledge-space-library-remove`

Remove a Notebook AI (Knowledge Space) library based on the provided parameters. Returns the removed library confirmation.

**Call:** `execute_knowledge-space-library-remove`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_knowledge_space_library_remove (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_knowledge-space-library-remove) for the param schema and, where available, a worked example.

#### `knowledge-space-remove-files`

Remove files from knowledge space. Deletes specified files and removes them from the search index.

**Call:** `execute_knowledge-space-remove-files`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_knowledge_space_remove_files (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_knowledge-space-remove-files) for the param schema and, where available, a worked example.

#### `knowledge-space-session-delete`

Delete a Notebook AI (Knowledge Space) session by session ID. Permanently removes the session and its conversation history.

**Call:** `execute_knowledge-space-session-delete`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_knowledge_space_session_delete (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_knowledge-space-session-delete) for the param schema and, where available, a worked example.
