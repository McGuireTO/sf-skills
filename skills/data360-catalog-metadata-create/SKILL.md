---
name: data360-catalog-metadata-create
description: "Use this skill when users want to execute Data Cloud CatalogMetadata operations via the Data 360 MCP facade. Trigger when users mention data360/catalog, metadata, shared, cdp, mcp, connect, api, shared-cdp-mcp-connect-api."
metadata:
  version: "1.0"
---

# Managing Data360/catalog Metadata

## When to Use This Skill

Execute Data Cloud CatalogMetadata operations via the Data 360 MCP facade.

## Workflow

Each step lists an `operation` id. Call describe(<operation>) BEFORE dispatching to get that tool's parameter schema and, where available, a worked example. `paramsJson` decodes to the operation's requestBody schema VERBATIM, including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap or omit it. The only envelope the step handles for you is `{toolName, paramsJson}` (its `invocation` already wraps it); do not POST the operation path directly. If the tool's error suggests `payload_examples`, ignore it — that tool isn't available here; call describe(<operation>) instead.

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `catalog-metadata-bulk-fetch` | read | implemented | `execute_catalog-metadata-bulk-fetch` | — |
| `catalog-metadata-children-bulk-fetch` | read | implemented | `execute_catalog-metadata-children-bulk-fetch` | — |
| `catalog-metadata-children-list` | read | implemented | `execute_catalog-metadata-children-list` | — |
| `catalog-metadata-get` | read | implemented | `execute_catalog-metadata-get` | — |
| `catalog-metadata-last-extraction-get` | read | implemented | `execute_catalog-metadata-last-extraction-get` | — |
| `catalog-metadata-lookup` | read | implemented | `execute_catalog-metadata-lookup` | — |
| `catalog-metadata-refresh-status-get` | read | implemented | `execute_catalog-metadata-refresh-status-get` | — |
| `catalog-metadata-relationship-children-get` | read | implemented | `execute_catalog-metadata-relationship-children-get` | — |
| `catalog-metadata-relationships-get` | read | implemented | `execute_catalog-metadata-relationships-get` | — |
| `catalog-metadata-relationships-lookup` | read | implemented | `execute_catalog-metadata-relationships-lookup` | — |
| `catalog-metadata-search` | read | implemented | `execute_catalog-metadata-search` | — |
| `catalog-metadata-trigger-full-extraction` | write | implemented | `execute_catalog-metadata-trigger-full-extraction` | — |
| `catalog-metadata-type-describe` | read | implemented | `execute_catalog-metadata-type-describe` | — |
| `catalog-metadata-type-list` | read | implemented | `execute_catalog-metadata-type-list` | — |

### Read operations

#### `catalog-metadata-bulk-fetch`

Bulk fetch metadata records by their opaque identifiers (1-100), more efficient than repeated d360_catalog_metadata_get calls; identifiers not found are silently omitted. Call d360_catalog_metadata_search or d360_catalog_metadata_lookup to obtain the identifiers.

**Call:** `execute_catalog-metadata-bulk-fetch`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_catalog_metadata_bulk_fetch (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_catalog-metadata-bulk-fetch) for the param schema and, where available, a worked example.

#### `catalog-metadata-children-bulk-fetch`

Bulk fetch children of metadata records grouped by parent identifier (1-100 parents), more efficient than repeated d360_catalog_metadata_children_list calls; parents not found are silently omitted. Call d360_catalog_metadata_search or d360_catalog_metadata_lookup to obtain the parent identifiers.

**Call:** `execute_catalog-metadata-children-bulk-fetch`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_catalog_metadata_children_bulk_fetch (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_catalog-metadata-children-bulk-fetch) for the param schema and, where available, a worked example.

#### `catalog-metadata-children-list`

List child metadata records (fields) for a given parent metadata asset. Confirms the exact __c field API names (and their types) that a segment, calculated-insight, or data-transform SQL statement may reference, so creation tools do not reject columns that do not exist in metadata. Call d360_catalog_metadata_lookup or d360_catalog_metadata_search to obtain the parent identifier. Returns the child records for the supplied parent identifier.

**Call:** `execute_catalog-metadata-children-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_catalog_metadata_children_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_catalog-metadata-children-list) for the param schema and, where available, a worked example.

#### `catalog-metadata-get`

Get the full metadata profile for a single entity or field by its opaque identifier, including its exact API name, fields, and key/key-qualifier details needed to author segment, calculated-insight, or data-transform SQL. Call d360_catalog_metadata_lookup or d360_catalog_metadata_search to obtain the identifier from a human-readable name.

**Call:** `execute_catalog-metadata-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_catalog_metadata_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_catalog-metadata-get) for the param schema and, where available, a worked example.

#### `catalog-metadata-last-extraction-get`

Get information about the last metadata extraction, including last extraction timestamp, next scheduled extraction, whether an extraction is in progress, and last refresh time.

**Call:** `execute_catalog-metadata-last-extraction-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_catalog_metadata_last_extraction_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_catalog-metadata-last-extraction-get) for the param schema and, where available, a worked example.

#### `catalog-metadata-lookup`

Look up metadata records by human-readable composite key (metadataType + API name). Confirms that the entity or field exists and resolves it to the opaque identifier required by the identifier-based tools (d360_catalog_metadata_get, d360_catalog_metadata_relationships_get, d360_catalog_metadata_bulk_fetch); a no-match result means the name does not exist and must not be passed to a creation tool. Call d360_catalog_metadata_type_list to know the valid metadataType and metadataSubType values. Returns matching records; use metadataSubType or parentIdentifier to disambiguate.

**Call:** `execute_catalog-metadata-lookup`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_catalog_metadata_lookup (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_catalog-metadata-lookup) for the param schema and, where available, a worked example.

#### `catalog-metadata-refresh-status-get`

Get the current refresh status of the metadata.

**Call:** `execute_catalog-metadata-refresh-status-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_catalog_metadata_refresh_status_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_catalog-metadata-refresh-status-get) for the param schema and, where available, a worked example.

#### `catalog-metadata-relationship-children-get`

Get the field-level plumbing of a single relationship edge, including field-to-field edges and the metadata of every referenced field. Call d360_catalog_metadata_relationships_get or d360_catalog_metadata_relationships_lookup to obtain the edge identifier.

**Call:** `execute_catalog-metadata-relationship-children-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_catalog_metadata_relationship_children_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_catalog-metadata-relationship-children-get) for the param schema and, where available, a worked example.

#### `catalog-metadata-relationships-get`

Traverse the relationship subgraph from a metadata asset by identifier, up to the requested upstream/downstream depths. Grounds joins before authoring any segment or calculated-insight SQL join — segment and CI joins must correspond to a relationship declared in the DMO graph or creation fails with 'No relationship exists between the provided keys', and the returned edges expose the valid join keys and key qualifiers to use. Returns the root, neighbor nodes, and connecting edges; set includeFieldDetails=true to inline field-level edges. Call d360_catalog_metadata_lookup or d360_catalog_metadata_search to obtain the identifier, or use d360_catalog_metadata_relationships_lookup when only a human-readable name is known.

**Call:** `execute_catalog-metadata-relationships-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_catalog_metadata_relationships_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_catalog-metadata-relationships-get) for the param schema and, where available, a worked example.

#### `catalog-metadata-relationships-lookup`

Resolve a metadata asset by human-readable composite key (metadataType + API name), then traverse its relationship subgraph. Grounds joins before authoring any segment or calculated-insight SQL join — segment and CI joins must correspond to a relationship declared in the DMO graph or creation fails with 'No relationship exists between the provided keys', and the returned edges expose the valid join keys and key qualifiers. Applies when the opaque identifier is not known (otherwise use d360_catalog_metadata_relationships_get); call d360_catalog_metadata_type_list to know the valid metadataType and metadataSubType values.

**Call:** `execute_catalog-metadata-relationships-lookup`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_catalog_metadata_relationships_lookup (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_catalog-metadata-relationships-lookup) for the param schema and, where available, a worked example.

#### `catalog-metadata-search`

Semantic-searches Data Cloud metadata by free text to resolve entities and fields to their exact API names, types, and dataspace before creating or editing an asset. Always scope with a filter: first call d360_catalog_metadata_type_list for the right metadataType (and subType) — don't guess, as DMOs and other objects aren't under an obvious type name — then pass them in filters, an array of {field, values} where field is 'metadataType' or 'subType'. An unfiltered query also returns Salesforce setup-metadata noise. To confirm a single already-known name, use d360_catalog_metadata_lookup instead.

**Call:** `execute_catalog-metadata-search`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_catalog_metadata_search (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_catalog-metadata-search) for the param schema and, where available, a worked example.

#### `catalog-metadata-type-describe`

Describes a single metadata type, returning its full JSON Schema document including subtypes and property schemas. Call d360_catalog_metadata_type_list to obtain the valid type names accepted by typeName.

**Call:** `execute_catalog-metadata-type-describe`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_catalog_metadata_type_describe (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_catalog-metadata-type-describe) for the param schema and, where available, a worked example.

#### `catalog-metadata-type-list`

List all available metadata types with their subtypes. Returns the valid metadataType and metadataSubType values that the other metadata tools require as inputs; this is the starting point for metadata discovery before any create or modify operation on a Data Cloud asset.

**Call:** `execute_catalog-metadata-type-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_catalog_metadata_type_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_catalog-metadata-type-list) for the param schema and, where available, a worked example.

### Write operations

#### `catalog-metadata-trigger-full-extraction`

Trigger a full (Day 0) extraction to refresh the metadata. EXPENSIVE — this is a long-running background job that can take significant time to complete, so do not invoke it unless absolutely necessary. Only run when the user has explicitly asked for a metadata refresh; never trigger it automatically as part of another task. Always confirm with the user before running. Returns whether the extraction was successfully triggered; poll d360_catalog_metadata_refresh_status_get and d360_catalog_metadata_last_extraction_get to track progress.

**Call:** `execute_catalog-metadata-trigger-full-extraction`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_catalog_metadata_trigger_full_extraction (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_catalog-metadata-trigger-full-extraction) for the param schema and, where available, a worked example.
