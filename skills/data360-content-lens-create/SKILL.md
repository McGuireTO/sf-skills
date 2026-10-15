---
name: data360-content-lens-create
description: "Use this skill when users want to execute Data Cloud ContentLens operations via the Data 360 MCP facade. Trigger when users mention data360/content, lens, shared, cdp, mcp, connect, api, shared-cdp-mcp-connect-api."
metadata:
  version: "1.0"
---

# Managing Data360/content Lens

## When to Use This Skill

Execute Data Cloud ContentLens operations via the Data 360 MCP facade.

## Workflow

Each step lists an `operation` id. Call describe(<operation>) BEFORE dispatching to get that tool's parameter schema and, where available, a worked example. `paramsJson` decodes to the operation's requestBody schema VERBATIM, including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap or omit it. The only envelope the step handles for you is `{toolName, paramsJson}` (its `invocation` already wraps it); do not POST the operation path directly. If the tool's error suggests `payload_examples`, ignore it — that tool isn't available here; call describe(<operation>) instead.

## Critical Constraints

**Destructive operations — require explicit user confirmation:**

- **`intelligent-context-delete`** — Delete an intelligent context by API name. Removes the definition record, its associated source records, and the backing index DMO along with its DLO mappings.
  - Rollback: No automatic rollback.

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `intelligent-context-agent-session-conversation-get` | read | implemented | `execute_intelligent-context-agent-session-conversation-get` | — |
| `intelligent-context-chunks-get` | read | implemented | `execute_intelligent-context-chunks-get` | — |
| `intelligent-context-create` | write | implemented | `execute_intelligent-context-create` | — |
| `intelligent-context-delete` | delete | implemented | `execute_intelligent-context-delete` | — |
| `intelligent-context-generate-config` | write | implemented | `execute_intelligent-context-generate-config` | — |
| `intelligent-context-get` | read | implemented | `execute_intelligent-context-get` | — |
| `intelligent-context-list` | read | implemented | `execute_intelligent-context-list` | — |
| `intelligent-context-metadata-fields-list` | read | implemented | `execute_intelligent-context-metadata-fields-list` | — |
| `intelligent-context-metadata-fields-upsert` | write | implemented | `execute_intelligent-context-metadata-fields-upsert` | — |
| `intelligent-context-presigned-urls-get` | read | implemented | `execute_intelligent-context-presigned-urls-get` | — |
| `intelligent-context-publish` | write | implemented | `execute_intelligent-context-publish` | — |
| `intelligent-context-status-get` | read | implemented | `execute_intelligent-context-status-get` | — |
| `intelligent-context-update` | write | implemented | `execute_intelligent-context-update` | — |

### Read operations

#### `intelligent-context-agent-session-conversation-get`

Get the conversation message history for the agent session associated with an intelligent context. The session id is resolved server-side from the intelligent context's associated agent session; callers only supply the intelligent context API name.

**Call:** `execute_intelligent-context-agent-session-conversation-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_intelligent_context_agent_session_conversation_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_intelligent-context-agent-session-conversation-get) for the param schema and, where available, a worked example.

#### `intelligent-context-chunks-get`

Get chunks belonging to an intelligent context, scoped by API name and by the file names and/or DMO record ids provided in the request. Scope files by the same file names passed to d360_intelligent_context_update, not by content or chunk ids. Supports an optional chunk-text filter. Returns the intelligent context's current processing status; when the status is READY, also queries the underlying processing service for the matching chunks and returns them along with the status. When the status is not READY, only the status is returned.

**Call:** `execute_intelligent-context-chunks-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_intelligent_context_chunks_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_intelligent-context-chunks-get) for the param schema and, where available, a worked example.

#### `intelligent-context-get`

Get a single intelligent context definition by API name, including its configuration and metadata.

**Call:** `execute_intelligent-context-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_intelligent_context_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_intelligent-context-get) for the param schema and, where available, a worked example.

#### `intelligent-context-list`

List intelligent context definitions in the org. Supports limit/offset paging and an optional name-based search filter. Returns summary metadata for each definition.

**Call:** `execute_intelligent-context-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_intelligent_context_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_intelligent-context-list) for the param schema and, where available, a worked example.

#### `intelligent-context-metadata-fields-list`

List metadata fields defined on an intelligent context. Supports limit/offset paging.

**Call:** `execute_intelligent-context-metadata-fields-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_intelligent_context_metadata_fields_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_intelligent-context-metadata-fields-list) for the param schema and, where available, a worked example.

#### `intelligent-context-presigned-urls-get`

Generate presigned upload URLs for the requested file names under an intelligent context's SFDrive upload location. Validates the file count against the per-intelligent-context maximum and validates that each file's extension is supported. Pass every file the user supplied in one fileNames list, keeping each original name and extension; mixed types in one request are supported (pdf, pptx, docx, html, txt, and other types the server accepts). Do not rename files to .pdf or split mixed uploads across multiple intelligent contexts unless the user asks. For each file, resolves its MIME type, obtains a PUT-only presigned URL, and returns the URL along with the fully qualified upload path. This endpoint only issues URLs; it does not transfer file contents. Each returned URL must be consumed by the caller via an HTTP PUT of the file bytes to complete the upload. Uploading the bytes does not by itself register the file with the intelligent context: after each PUT succeeds, associate the file by calling d360_intelligent_context_update with files[], copying fileName, fullyQualifiedFilePath, and mimeType verbatim from this response.

**Call:** `execute_intelligent-context-presigned-urls-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_intelligent_context_presigned_urls_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_intelligent-context-presigned-urls-get) for the param schema and, where available, a worked example.

#### `intelligent-context-status-get`

Get the current processing status of an intelligent context by API name. Reads status from the underlying processing service and returns the intelligent context's position in the asynchronous processing lifecycle (in-progress, terminal success, or terminal failure states). Suitable for polling to observe when processing completes.

**Call:** `execute_intelligent-context-status-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_intelligent_context_status_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_intelligent-context-status-get) for the param schema and, where available, a worked example.

### Write operations

#### `intelligent-context-create`

Create a new intelligent context definition. Required fields on createContentLensDefRecord: name (API name, unique in the org; every later intelligent-context tool passes this as intelligentContextName), label, dataSpaceName (dataspace API name, typically 'default'), indexDmoName, and indexDmoLabel. Set indexDmoName to the same value as name — do not append '__dlm'; the platform adds that suffix. description is optional. Provisions the backing vector DMO/DLO and mapping and persists the definition in DRAFT. Does not upload files or start indexing.

**Call:** `execute_intelligent-context-create`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_intelligent_context_create (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_intelligent-context-create) for the param schema and, where available, a worked example.

#### `intelligent-context-generate-config`

Generate a suggested search-index configuration for an existing intelligent context by delegating the provided user instructions to the configuration-generation service. The intelligent context's sources must already have reached the generation service before calling this, because the recommendation is derived from the stored documents. For a file-based intelligent context, call d360_intelligent_context_update with files[] and a searchIndexConfig in the same patch first — sources are forwarded only when the patch bumps the definition version, which requires searchIndexConfig to be present, and a searchIndexConfig of empty lists is sufficient on an intelligent context that has no configuration yet. Uploading bytes to a presigned URL, or patching files[] on its own, is not sufficient, and generation fails when no sources have reached the service. When associated files have different extensions, the returned chunkingConfiguration.fileLevelConfiguration.perFileExtensions contains one object per distinct extension (for example pdf, pptx, docx, html, txt). Copy that entire list on update CALL 2; do not keep only the pdf entry. preProcessingConfigurations may list only pdf (LLM infographics) even when other files exist — do not invent preprocessing for omitted extensions. Returns the intelligent context API name and the generated searchIndexConfig. The returned searchIndexConfig is not persisted by this endpoint; it must be applied to the intelligent context via d360_intelligent_context_update before it takes effect on the intelligent context's processing.

**Call:** `execute_intelligent-context-generate-config`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_intelligent_context_generate_config (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_intelligent-context-generate-config) for the param schema and, where available, a worked example.

#### `intelligent-context-metadata-fields-upsert`

Upsert metadata fields on an intelligent context. Accepts a list of field definitions and their per-file (or per-record) values; creates fields that do not yet exist and updates fields and values that do. Returns the resulting metadata field configuration for the intelligent context.

**Call:** `execute_intelligent-context-metadata-fields-upsert`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_intelligent_context_metadata_fields_upsert (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_intelligent-context-metadata-fields-upsert) for the param schema and, where available, a worked example.

#### `intelligent-context-publish`

Publish a READY intelligent context: create the Semantic Search (SI) and set status to PUBLISHED. 

**Call:** `execute_intelligent-context-publish`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_intelligent_context_publish (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_intelligent-context-publish) for the param schema and, where available, a worked example.

#### `intelligent-context-update`

Patch an intelligent context definition by API name. For a file-based intelligent context this tool is called twice with different payloads. CALL 1 associates already-uploaded files: send files[] together with a placeholder searchIndexConfig that contains only empty lists (parsingConfigurations, preProcessingConfigurations, prefilterColumnMappings, transformConfigurations, vectorEmbeddingFileRelatedFields, vectorEmbeddingRelatedFields). The placeholder is required: associated files are forwarded to the processing service only when the patch bumps the definition version, and the version is bumped only when searchIndexConfig is present. A files[]-only patch records the files in the org and leaves d360_intelligent_context_generate_config reporting that the intelligent context has no files. Copy fileName, fullyQualifiedFilePath, and mimeType from d360_intelligent_context_presigned_urls_get after HTTP PUT of the file bytes. files[] may mix supported extensions in one intelligent context (pdf, pptx, docx, html, txt, and other types the presign endpoint accepted); keep every original fileName and do not rename files to .pdf. CALL 2 starts indexing: after d360_intelligent_context_generate_config, resend that same mixed files[] with the returned searchIndexConfig. Copy generate_config values verbatim (searchType, typically HYBRID; every chunkingConfiguration.fileLevelConfiguration.perFileExtensions entry, one per distinct uploaded extension; vectorEmbeddingConfiguration including embeddingModel.id; preProcessingConfigurations including long LLM prompts, which often apply only to pdf; citations/decorators when present; and any empty lists the response includes). Do not collapse mixed files to a pdf-only chunking config or invent preprocessing for extensions generate_config omitted. searchType alone is not sufficient. Do not resend the CALL 1 empty-list placeholder after a real configuration exists. Poll d360_intelligent_context_status_get until READY before retrieving chunks. sourceDmo is the structured alternative to files[]; do not send both. To publish, call d360_intelligent_context_publish with publishContentLensPayload; do not set searchIndexPublished on this tool.

**Call:** `execute_intelligent-context-update`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_intelligent_context_update (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_intelligent-context-update) for the param schema and, where available, a worked example.

### Destructive operations

#### `intelligent-context-delete`

Delete an intelligent context by API name. Removes the definition record, its associated source records, and the backing index DMO along with its DLO mappings.

**Call:** `execute_intelligent-context-delete`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_intelligent_context_delete (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_intelligent-context-delete) for the param schema and, where available, a worked example.
