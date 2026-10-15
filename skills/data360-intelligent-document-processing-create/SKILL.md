---
name: data360-intelligent-document-processing-create
description: "Use this skill when users want to execute Data Cloud IntelligentDocumentProcessing operations via the Data 360 MCP facade. Trigger when users mention data360/intelligent, document, processing, shared, cdp, mcp, connect, api, shared-cdp-mcp-connect-api."
metadata:
  version: "1.0"
---

# Managing Data360/intelligent Document Processing

## When to Use This Skill

Execute Data Cloud IntelligentDocumentProcessing operations via the Data 360 MCP facade.

## Workflow

Each step lists an `operation` id. Call describe(<operation>) BEFORE dispatching to get that tool's parameter schema and, where available, a worked example. `paramsJson` decodes to the operation's requestBody schema VERBATIM, including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap or omit it. The only envelope the step handles for you is `{toolName, paramsJson}` (its `invocation` already wraps it); do not POST the operation path directly. If the tool's error suggests `payload_examples`, ignore it — that tool isn't available here; call describe(<operation>) instead.

## Critical Constraints

**Destructive operations — require explicit user confirmation:**

- **`document-ai-configuration-delete`** — Delete a Document AI configuration (internally named IDP configuration) by its ID or API name. This permanently removes the configuration and its associated schema and rules.
  - Rollback: No automatic rollback.

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `document-ai-configuration-create` | write | implemented | `execute_document-ai-configuration-create` | — |
| `document-ai-configuration-delete` | delete | implemented | `execute_document-ai-configuration-delete` | — |
| `document-ai-configuration-get` | read | implemented | `execute_document-ai-configuration-get` | — |
| `document-ai-configuration-list` | read | implemented | `execute_document-ai-configuration-list` | — |
| `document-ai-configuration-process` | write | implemented | `execute_document-ai-configuration-process` | — |
| `document-ai-configuration-update` | write | implemented | `execute_document-ai-configuration-update` | — |
| `document-ai-data-extract` | read | implemented | `execute_document-ai-data-extract` | — |
| `document-ai-global-config-get` | read | implemented | `execute_document-ai-global-config-get` | — |
| `document-ai-schema-detect` | read | implemented | `execute_document-ai-schema-detect` | — |
| `document-ai-schema-generate` | write | implemented | `execute_document-ai-schema-generate` | — |

### Read operations

#### `document-ai-configuration-get`

Get the details of a specific Document AI configuration (internally named IDP configuration) by its ID or API name. Returns configuration details including schema, data model objects, and processing rules.

**Call:** `execute_document-ai-configuration-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_document_ai_configuration_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_document-ai-configuration-get) for the param schema and, where available, a worked example.

#### `document-ai-configuration-list`

List all Document AI configurations (internally named IDP configurations) with optional filtering by activation status, search text, and pagination support. Returns configuration details including labels, API names, and status.

**Call:** `execute_document-ai-configuration-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_document_ai_configuration_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_document-ai-configuration-list) for the param schema and, where available, a worked example.

#### `document-ai-data-extract`

Extract structured data from documents by providing a json schema or Document AI configuration. Supports targeted page-range extraction and confidence scores for the extracted data. Returns extracted field values and metadata.

**Call:** `execute_document-ai-data-extract`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_document_ai_data_extract (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_document-ai-data-extract) for the param schema and, where available, a worked example.

#### `document-ai-global-config-get`

Get the global configuration settings for Document AI (internally named IDP). Returns system-wide Document AI settings including enabled features, quotas, and default parameters.

**Call:** `execute_document-ai-global-config-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_document_ai_global_config_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_document-ai-global-config-get) for the param schema and, where available, a worked example.

#### `document-ai-schema-detect`

Classify a document against existing Document AI schema configurations (internally named IDP schema configurations) and return the best matching configuration along with a confidence score. This operation identifies which existing schema configuration applies to the provided document and does not generate a new schema. To create a new schema, use d360_document_ai_schema_generate. Required inputs: schemaConfigurations (api names of existing configurations), mlModel, files, and mode. Threshold is optional, defaults if omitted, and must be between 0.0 and 1.0.

**Call:** `execute_document-ai-schema-detect`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_document_ai_schema_detect (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_document-ai-schema-detect) for the param schema and, where available, a worked example.

### Write operations

#### `document-ai-configuration-create`

Create a new Document AI configuration (internally named IDP configuration) with schema, data model objects, and processing rules. Specify the source and filter data model objects, ML model, and activation status. Returns the created configuration details. Before calling this tool, the agent MUST: (a) call d360_document_ai_global_config_get to fetch the list of supported models, present that list to the user, and ask which mlModel to use — do not guess or hard-code an mlModel value; and (b) enumerate the supported unstructured DMOs (UDMOs) by calling d360_dmo_list with dataObjectCategory=DirectoryTable, then present that list to the user and ask which UDMO to bind the configuration to (or whether to leave it unbound). Then explicitly ask the user: (1) whether to bind the configuration to a sourceDmoDeveloperName from the enumerated UDMO list (for batch/scheduled processing of files in an existing unstructured DMO) or leave it unbound (for standalone/on-demand extraction)—this choice cannot be changed later; (2) which file/content types the configuration should accept, and provide them as MIME types in fileConfig.fileTypes (for example, application/pdf, image/png, image/jpeg); and (3) whether they want to specify custom output DLO and field names. If yes, collect the required names and pass them in extractedDloConfig. If no, omit extractedDloConfig so the output DLO and field names are automatically derived from the schema.

**Call:** `execute_document-ai-configuration-create`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_document_ai_configuration_create (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_document-ai-configuration-create) for the param schema and, where available, a worked example.

#### `document-ai-configuration-process`

Process (full refresh) a Document AI configuration (internally named IDP configuration) by its ID or API name. This triggers a full reprocessing of all documents associated with the configuration. Returns empty on success.

**Call:** `execute_document-ai-configuration-process`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_document_ai_configuration_process (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_document-ai-configuration-process) for the param schema and, where available, a worked example.

#### `document-ai-configuration-update`

Update a Document AI configuration (internally named IDP configuration) by its ID or API name. Allows modification of configuration details, schema, and processing rules. Returns the updated configuration.

**Call:** `execute_document-ai-configuration-update`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_document_ai_configuration_update (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_document-ai-configuration-update) for the param schema and, where available, a worked example.

#### `document-ai-schema-generate`

Generate a Document AI schema (internally named IDP schema) by analyzing sample documents. Provide document content, optional user description, and context. Returns a generated schema with field definitions.

**Call:** `execute_document-ai-schema-generate`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_document_ai_schema_generate (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_document-ai-schema-generate) for the param schema and, where available, a worked example.

### Destructive operations

#### `document-ai-configuration-delete`

Delete a Document AI configuration (internally named IDP configuration) by its ID or API name. This permanently removes the configuration and its associated schema and rules.

**Call:** `execute_document-ai-configuration-delete`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_document_ai_configuration_delete (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_document-ai-configuration-delete) for the param schema and, where available, a worked example.
