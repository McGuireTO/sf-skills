---
name: data360-connection-create
description: "Use this skill when users want to execute Data Cloud Connection operations via the Data 360 MCP facade. Trigger when users mention data360/connection, shared, cdp, mcp, connect, api, shared-cdp-mcp-connect-api."
metadata:
  version: "1.0"
---

# Managing Data360/connection

## When to Use This Skill

Execute Data Cloud Connection operations via the Data 360 MCP facade.

## Workflow

Each step lists an `operation` id. Call describe(<operation>) BEFORE dispatching to get that tool's parameter schema and, where available, a worked example. `paramsJson` decodes to the operation's requestBody schema VERBATIM, including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap or omit it. The only envelope the step handles for you is `{toolName, paramsJson}` (its `invocation` already wraps it); do not POST the operation path directly. If the tool's error suggests `payload_examples`, ignore it — that tool isn't available here; call describe(<operation>) instead.

## Critical Constraints

**Destructive operations — require explicit user confirmation:**

- **`connection-delete`** — Permanently delete a Data Cloud connection by its connectionId. This is destructive and irreversible: it disconnects the connection (for a Salesforce CRM Home Org connection this removes the Home Org connection) and cannot be undone. Only call this when the user has explicitly confirmed they want to delete the connection. Find the connectionId with d360_connection_list or d360_connection_get.
  - Rollback: No automatic rollback.
- **`connection-user-delete`** — Delete a specific user's per-user connection from a shell connection. Removes the user's individual credentials without affecting other users or the shell connection.
  - Rollback: No automatic rollback.

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `connection-activate` | write | implemented | `execute_connection-activate` | — |
| `connection-command-execute` | write | implemented | `execute_connection-command-execute` | — |
| `connection-command-execute-existing` | write | implemented | `execute_connection-command-execute-existing` | — |
| `connection-create-ingestion-api` | write | implemented | `execute_connection-create-ingestion-api` | — |
| `connection-create-sfdc` | write | implemented | `execute_connection-create-sfdc` | — |
| `connection-create-sfmc` | write | implemented | `execute_connection-create-sfmc` | — |
| `connection-create-streaming-app` | write | implemented | `execute_connection-create-streaming-app` | — |
| `connection-databases-get` | read | implemented | `execute_connection-databases-get` | — |
| `connection-db-schemas-list` | read | implemented | `execute_connection-db-schemas-list` | — |
| `connection-delete` | delete | implemented | `execute_connection-delete` | — |
| `connection-dependencies-list` | read | implemented | `execute_connection-dependencies-list` | — |
| `connection-endpoints` | read | implemented | `execute_connection-endpoints` | — |
| `connection-get` | read | implemented | `execute_connection-get` | — |
| `connection-list` | read | implemented | `execute_connection-list` | — |
| `connection-list-sfmc` | read | implemented | `execute_connection-list-sfmc` | — |
| `connection-nodes-get` | read | implemented | `execute_connection-nodes-get` | — |
| `connection-object-fields-describe` | read | implemented | `execute_connection-object-fields-describe` | — |
| `connection-object-fields-describe-sfmc` | read | implemented | `execute_connection-object-fields-describe-sfmc` | — |
| `connection-objects-list` | read | implemented | `execute_connection-objects-list` | — |
| `connection-objects-list-sfmc` | read | implemented | `execute_connection-objects-list-sfmc` | — |
| `connection-preview` | read | implemented | `execute_connection-preview` | — |
| `connection-readiness-check-sfmc` | read | implemented | `execute_connection-readiness-check-sfmc` | — |
| `connection-reauthenticate-sfdc` | write | implemented | `execute_connection-reauthenticate-sfdc` | — |
| `connection-schema-get` | read | implemented | `execute_connection-schema-get` | — |
| `connection-schema-put-ingestion-api` | write | implemented | `execute_connection-schema-put-ingestion-api` | — |
| `connection-schema-put-streaming-app` | write | implemented | `execute_connection-schema-put-streaming-app` | — |
| `connection-schema-test` | read | implemented | `execute_connection-schema-test` | — |
| `connection-schema-update` | write | implemented | `execute_connection-schema-update` | — |
| `connection-sitemap-get` | read | implemented | `execute_connection-sitemap-get` | — |
| `connection-sitemap-update` | write | implemented | `execute_connection-sitemap-update` | — |
| `connection-test-existing` | read | implemented | `execute_connection-test-existing` | — |
| `connection-update-sfdc` | write | implemented | `execute_connection-update-sfdc` | — |
| `connection-update-sfmc` | write | implemented | `execute_connection-update-sfmc` | — |
| `connection-update-streaming-app` | write | implemented | `execute_connection-update-streaming-app` | — |
| `connection-user-create` | write | implemented | `execute_connection-user-create` | — |
| `connection-user-delete` | delete | implemented | `execute_connection-user-delete` | — |
| `connection-user-get` | read | implemented | `execute_connection-user-get` | — |
| `connection-user-list` | read | implemented | `execute_connection-user-list` | — |
| `connection-user-update` | write | implemented | `execute_connection-user-update` | — |
| `connector-list` | read | implemented | `execute_connector-list` | — |
| `connector-metadata` | read | implemented | `execute_connector-metadata` | — |

### Read operations

#### `connection-databases-get`

List databases available in a connection. Use for database-aware connectors (Snowflake, MySQL, PostgreSQL) to discover accessible databases before querying schemas or tables.

**Call:** `execute_connection-databases-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_connection_databases_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_connection-databases-get) for the param schema and, where available, a worked example.

#### `connection-db-schemas-list`

List database schemas available in a Data Cloud connection. Use this for connectors that expose hierarchical schemas (e.g., Snowflake, JDBC) before listing tables/objects.

**Call:** `execute_connection-db-schemas-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_connection_db_schemas_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_connection-db-schemas-list) for the param schema and, where available, a worked example.

#### `connection-dependencies-list`

List the 1-level Data Cloud component dependencies (data streams and data action targets) of a connection. Requires connectionId; optionally filter by componentType (DataStream or DataActionTarget) and page with limit/offset. Find the connectionId with d360_connection_list or d360_connection_get. Currently supported for Salesforce CRM (SalesforceDotCom) Home Org connections.

**Call:** `execute_connection-dependencies-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_connection_dependencies_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_connection-dependencies-list) for the param schema and, where available, a worked example.

#### `connection-endpoints`

Download the Ingestion API endpoints YAML for a connection. Use this to discover the per-DLO push endpoints that streaming/batch ingestion clients should target.

**Call:** `execute_connection-endpoints`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_connection_endpoints (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_connection-endpoints) for the param schema and, where available, a worked example.

#### `connection-get`

Get a Data Cloud connection by its connectionId. Returns connector type and full configuration metadata.

**Call:** `execute_connection-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_connection_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_connection-get) for the param schema and, where available, a worked example.

#### `connection-list`

List Data Cloud connections filtered by connectorType (required). 

**Call:** `execute_connection-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_connection_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_connection-list) for the param schema and, where available, a worked example.

#### `connection-list-sfmc`

List Salesforce Marketing Cloud (SFMC) Data Cloud connections in the running org. Pins connectorType=SalesforceMarketingCloud on the underlying list endpoint so the agent does not need to know the discriminator; only paging is exposed. The response is filtered by the platform to MC EDCs and includes BU lists, BU-to-dataspace mappings, profileBuMappings, and a mid-auth authorizationUrl when the connection is still completing OAuth.

**Call:** `execute_connection-list-sfmc`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_connection_list_sfmc (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_connection-list-sfmc) for the param schema and, where available, a worked example.

#### `connection-nodes-get`

List nodes (folders, sites, organizational units) in a connection. Use for hierarchical data sources (Google Drive, SharePoint) to discover structure before accessing content.

**Call:** `execute_connection-nodes-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_connection_nodes_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_connection-nodes-get) for the param schema and, where available, a worked example.

#### `connection-object-fields-describe`

Describe the fields exposed by a specific object/resource in a Data Cloud connection. Use this after d360_connection_objects_list when configuring a data stream's source schema. For a Salesforce CRM (SalesforceDotCom) connection, pass an empty getFieldsInput ({}) to list all fields, or narrow with getFieldsInput.filters.filtersByProperty (e.g. name='name', filterOperator='SubstrOp', values=['Billing']); getFieldsInput.advancedAttributes is only for schema-aware connectors like Snowflake.

**Call:** `execute_connection-object-fields-describe`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_connection_object_fields_describe (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_connection-object-fields-describe) for the param schema and, where available, a worked example.

#### `connection-object-fields-describe-sfmc`

Describe the fields of an object in a Salesforce Marketing Cloud (SFMC) connection. subType is mandatory and must be either SalesforceMarketingCloudStandard (resourceName is a bundle stream name like 'EmailEngagementSend' returned by d360_connection_objects_list_sfmc with subType=SalesforceMarketingCloudStandard) or SalesforceMarketingCloudDataExtension (resourceName is the DE's customObjectId or customObjectName). mid is also required and identifies the target Marketing Cloud Business Unit. EID is resolved server-side from the connection and is NOT a tool parameter. The tool guards that the target connection is of type SalesforceMarketingCloud.

**Call:** `execute_connection-object-fields-describe-sfmc`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_connection_object_fields_describe_sfmc (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_connection-object-fields-describe-sfmc) for the param schema and, where available, a worked example.

#### `connection-objects-list`

List discoverable objects (tables/entities) in a Data Cloud connection. Use this to find candidate sources before creating a data stream. For schema-aware connectors, narrow with d360_connection_db_schemas_list first. For a Salesforce CRM (SalesforceDotCom) connection, pass an empty objectInput ({}) to list all objects, or narrow with objectInput.filters.filtersByProperty (e.g. name='name', filterOperator='SubstrOp', values=['Account']); objectInput.advancedAttributes is only for schema-aware connectors like Snowflake.

**Call:** `execute_connection-objects-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_connection_objects_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_connection-objects-list) for the param schema and, where available, a worked example.

#### `connection-objects-list-sfmc`

List objects available in a Salesforce Marketing Cloud (SFMC) connection. The subType filter is mandatory and must be one of: SalesforceMarketingCloudStandard (canonical bundle streams — e.g. Subscriber, EmailEngagementSend, EmailEngagementOpen, EmailEngagementClick, EmailEngagementBounce); SalesforceMarketingCloudDataExtension (custom DEs in a specific Marketing Cloud Business Unit — 'name' LIKE filter and 'mid' are additionally required); SalesforceMarketingCloudBusinessUnit (list every BU under the connection's EID); SalesforceMarketingCloudBundle (list available channels/bundles like COMMON, EMAIL, MOBILE_CONNECT, MOBILE_PUSH, WHATSAPP for ingestion). The tool guards that the target connection is of type SalesforceMarketingCloud. OUTPUT SHAPE (per subType — read this before piping results into another tool): (1) For subType=SalesforceMarketingCloudBusinessUnit: each returned row's 'businessUnitId' field IS THE MID (numeric string, e.g. '524004881'). Use this exact 'businessUnitId' value verbatim wherever another SFMC tool expects a 'mid' — including d360_connection_update_sfmc (addIngestionBusinessUnits / removeIngestionBusinessUnits / addActivationBusinessUnits / removeActivationBusinessUnits / addBusinessUnitsToDataSpaces / removeBusinessUnitsToDataSpaces), d360_datastream_create_sfmc_standard (mid param), d360_datastream_create_sfmc_data_extension (mid param), and d360_datastream_create_sfmc_bundle (mids param). Do NOT confuse 'businessUnitId' with a Salesforce record Id — it is the raw MID. (2) For subType=SalesforceMarketingCloudDataExtension: each row carries the DE's customObjectId (opaque MC id) AND customObjectName (human-readable) — both are required inputs on d360_datastream_create_sfmc_data_extension. (3) For subType=SalesforceMarketingCloudStandard: each row carries 'name' (feed into sourceObjectName on d360_datastream_create_sfmc_standard) and 'bundleName' (the channel, e.g. EMAIL / MOBILE_CONNECT / COMMON — feed into bundleType on d360_datastream_create_sfmc_bundle). (4) For subType=SalesforceMarketingCloudBundle: rows expose the bundle/channel names (COMMON, EMAIL, MOBILE_CONNECT, MOBILE_PUSH, WHATSAPP) — feed into bundleType on d360_datastream_create_sfmc_bundle.

**Call:** `execute_connection-objects-list-sfmc`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_connection_objects_list_sfmc (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_connection-objects-list-sfmc) for the param schema and, where available, a worked example.

#### `connection-preview`

Preview sample data from a connection object/table. Returns rows to help verify data structure and content before creating a data stream.

**Call:** `execute_connection-preview`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_connection_preview (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_connection-preview) for the param schema and, where available, a worked example.

#### `connection-readiness-check-sfmc`

One-shot readiness report for a Salesforce Marketing Cloud (SFMC) connection: is it authenticated, reachable right now, and configured well enough to create data streams? Combines connection-state discovery (from d360_connection_get) with a LIVE probe (testExistingConnection — Cost=Expensive) and returns a machine-readable verdict plus actionable next steps. Supply exactly one of connectionId (preferred) or connectionName. USAGE GUIDANCE: this tool is intended for setup/onboarding flows and troubleshooting — do NOT call it before every d360_datastream_create_* invocation. The live probe hits the Marketing Cloud admin service and is not free. When it fails, the tool reports readiness=AUTH_STALE_OR_UNREACHABLE with the underlying error message; the caller may choose to retry after a short delay (5-10s) to rule out a transient MC-side issue before concluding the connection needs OAuth reconnect. Set includeAvailableBUs=true to opt into an extra objects_list call that surfaces MIDs which exist under the EID but are not yet ingestion-enabled (useful for 'why can't I stream from this BU?' investigations); default false to keep the tool at 2 API calls. The tool guards that the target connection is of type SalesforceMarketingCloud.

**Call:** `execute_connection-readiness-check-sfmc`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_connection_readiness_check_sfmc (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_connection-readiness-check-sfmc) for the param schema and, where available, a worked example.

#### `connection-schema-get`

Get the schema definition for a connection. Returns the list of objects, fields, and metadata the connection exposes for data ingestion.

**Call:** `execute_connection-schema-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_connection_schema_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_connection-schema-get) for the param schema and, where available, a worked example.

#### `connection-schema-test`

Test the schema definition for a connection. Validates that the configured schema can be successfully retrieved from the external data source.

**Call:** `execute_connection-schema-test`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_connection_schema_test (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_connection-schema-test) for the param schema and, where available, a worked example.

#### `connection-sitemap-get`

Get the sitemap for a connection. Returns the mapping configuration between source objects and Data Cloud landing objects.

**Call:** `execute_connection-sitemap-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_connection_sitemap_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_connection-sitemap-get) for the param schema and, where available, a worked example.

#### `connection-test-existing`

Test an existing Data Cloud connection by ID to verify it can authenticate and reach its source system. For Salesforce CRM (SalesforceDotCom) connections this verifies authentication and trust to the source org. Requires connectionId; optionally pass process=true to also run post-test processing (advanced, defaults to false). Find the connectionId with d360_connection_list or d360_connection_get. Distinct from d360_connection_test, which tests an unsaved connection input before it is created.

**Call:** `execute_connection-test-existing`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_connection_test_existing (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_connection-test-existing) for the param schema and, where available, a worked example.

#### `connection-user-get`

Get a specific user's per-user connection details for a shell connection. Returns the user's individual credentials and connection status.

**Call:** `execute_connection-user-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_connection_user_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_connection-user-get) for the param schema and, where available, a worked example.

#### `connection-user-list`

List all per-user connections for a shell connection. Each user's individual credentials are stored in separate per-user connection records.

**Call:** `execute_connection-user-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_connection_user_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_connection-user-list) for the param schema and, where available, a worked example.

#### `connector-list`

List all available CDP connectors. Optionally filter by Name, Label, Features, or ReleaseLevel, order by Name or Label, and control field detail level with fieldGroup (SMALL, MEDIUM, BIG).

**Call:** `execute_connector-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_connector_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_connector-list) for the param schema and, where available, a worked example.

#### `connector-metadata`

Get metadata/schema for a specific connector type.

**Call:** `execute_connector-metadata`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_connector_metadata (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_connector-metadata) for the param schema and, where available, a worked example.

### Write operations

#### `connection-activate`

Activate a disconnected Data Cloud connection by connectionId (sandbox only). 

**Call:** `execute_connection-activate`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_connection_activate (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_connection-activate) for the param schema and, where available, a worked example.

#### `connection-command-execute`

Execute connector-specific commands without creating a connection. Use for operations like listing databases, testing queries, or discovery that don't require persisting a connection.

**Call:** `execute_connection-command-execute`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_connection_command_execute (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_connection-command-execute) for the param schema and, where available, a worked example.

#### `connection-command-execute-existing`

Execute connector-specific commands on an existing saved connection. Use for operations like querying data, listing tables, or running connector-specific actions.

**Call:** `execute_connection-command-execute-existing`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_connection_command_execute_existing (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_connection-command-execute-existing) for the param schema and, where available, a worked example.

#### `connection-create-ingestion-api`

Create a Data Cloud Ingestion API connection -- a connection that lets an external system push (ingest) data into Data Cloud over the Ingestion API (REST), either in bulk (file upload) or streaming (small JSON payloads). connectorType (IngestApi) is auto-set. Only a human-readable label is required. The optional alias, when supplied, is used in place of the connector name for data stream deployments and must be exactly 3 alphanumeric characters and unique across Ingestion API connectors. After creation, define the object/field schema with 'd360_connection_schema_put_ingestion_api' (inspect the current schema first with 'd360_connection_schema_get'); use 'd360_connection_list' with connectorType=IngestApi to find the connection's record id.

**Call:** `execute_connection-create-ingestion-api`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_connection_create_ingestion_api (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_connection-create-ingestion-api) for the param schema and, where available, a worked example.

#### `connection-create-sfdc`

Create the Home Org CRM (SalesforceDotCom) Data Cloud connection. Credential-less and takes no required parameters: the connection always targets this org, so organizationId defaults to the running org's ID when omitted (the backing API rejects any other org, and ignores name/label). Use d360_connection_list with connectorType=SalesforceDotCom to review the existing CRM connection first.

**Call:** `execute_connection-create-sfdc`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_connection_create_sfdc (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_connection-create-sfdc) for the param schema and, where available, a worked example.

#### `connection-create-sfmc`

Create a Salesforce Marketing Cloud (SFMC) Data Cloud connection. NO credentials are supplied in this payload: the response contains a short-lived authorizationUrl that the agent MUST relay verbatim to the user so they can complete the OAuth handoff in a browser. Until OAuth completes, the connection stays in Disconnected status. Only name and label are required; connectorType is pinned to SalesforceMarketingCloud automatically. After OAuth completes, manage business units and bundle ingestion with d360_connection_update_sfmc.

**Call:** `execute_connection-create-sfmc`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_connection_create_sfmc (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_connection-create-sfmc) for the param schema and, where available, a worked example.

#### `connection-create-streaming-app`

Create a Data Cloud Streaming App connection -- a web, mobile, or server-to-server app that streams events into Data Cloud. connectorType (StreamingApp) is auto-set. STEP 1 -- establish the streamingAppType first. It is required and must be exactly one of: MobileApp (a mobile app, e.g. iOS/Android), WebApp (a website, including Google Analytics), or ServerApp (a server-to-server integration). STEP 2 -- only AFTER the streamingAppType is known, and only if the user has not already supplied one, prompt for the optional streamingAppSubType (see its description for the values valid for each type). Do NOT ask for a subtype before the type is established; omit it for a plain connection of the given type. After creation, define the event schema with 'd360_connection_schema_put_streaming_app'.

**Call:** `execute_connection-create-streaming-app`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_connection_create_streaming_app (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_connection-create-streaming-app) for the param schema and, where available, a worked example.

#### `connection-reauthenticate-sfdc`

Re-authenticate a Salesforce CRM (SalesforceDotCom) Home Org Data Cloud connection, re-establishing Data Cloud's trust with the org and returning a NeedsReAuthentication connection to Connected. Requires only the connectionId (from d360_connection_list with connectorType=SalesforceDotCom or d360_connection_get). Supported for Home Org connections only; an already-Connected connection is an idempotent no-op. To rename a connection instead, use d360_connection_update_sfdc.

**Call:** `execute_connection-reauthenticate-sfdc`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_connection_reauthenticate_sfdc (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_connection-reauthenticate-sfdc) for the param schema and, where available, a worked example.

#### `connection-schema-put-ingestion-api`

Create or update the object schema for a Data Cloud Ingestion API connection (a source that pushes data into Data Cloud over the Ingestion API, in bulk or streaming). The schema defines the objects and their fields that the connection can ingest. PREREQUISITE: call 'd360_connection_list' with connectorType=IngestApi to find the connection, and pass its record id as connectionId. schemaType (IngestApi) is auto-set. IMPORTANT: this is an UPSERT against the connection's existing schema -- existing objects cannot be dropped and existing fields cannot be removed, so include ALL previously-defined objects and fields. Call 'd360_connection_schema_get' first to retrieve the current schema before editing.

**Call:** `execute_connection-schema-put-ingestion-api`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_connection_schema_put_ingestion_api (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_connection-schema-put-ingestion-api) for the param schema and, where available, a worked example.

#### `connection-schema-put-streaming-app`

Create or update the event schema for a Data Cloud Streaming App connection (web, mobile, or server-side app). The schema defines the events and their fields that the connection can ingest. PREREQUISITE: call 'd360_connection_list' with connectorType=StreamingApp to find the connection, and pass its record id as connectionId. schemaType (StreamingApp) is auto-set. IMPORTANT: this is an UPSERT against the connection's existing schema -- existing events cannot be dropped and existing fields cannot be removed, so include ALL previously-defined events and fields. Newly-added fields on an existing event cannot be isDataRequired=true. Call 'd360_connection_schema_get' first to retrieve the current schema before editing.

**Call:** `execute_connection-schema-put-streaming-app`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_connection_schema_put_streaming_app (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_connection-schema-put-streaming-app) for the param schema and, where available, a worked example.

#### `connection-schema-update`

Create or update the schema definition for a connection. Define which objects and fields from the external source should be available for data streams.

**Call:** `execute_connection-schema-update`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_connection_schema_update (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_connection-schema-update) for the param schema and, where available, a worked example.

#### `connection-sitemap-update`

Create or update the sitemap for a connection. Defines how source objects map to Data Cloud landing objects for ingestion.

**Call:** `execute_connection-sitemap-update`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_connection_sitemap_update (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_connection-sitemap-update) for the param schema and, where available, a worked example.

#### `connection-update-sfdc`

Update (rename) the display label of a Salesforce CRM (SalesforceDotCom) Data Cloud connection. Requires the connectionId and the new label. Find the connectionId first with d360_connection_list (connectorType=SalesforceDotCom) or d360_connection_get. The label must be non-empty and at most 80 characters. Renaming is not supported for Remote Data Cloud (Data Cloud One) connections.

**Call:** `execute_connection-update-sfdc`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_connection_update_sfdc (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_connection-update-sfdc) for the param schema and, where available, a worked example.

#### `connection-update-sfmc`

Update a Salesforce Marketing Cloud (SFMC) Data Cloud connection by connectionId. Use to add/remove Marketing Cloud Business Units (BUs) for ingestion or activation, add/remove BU-to-dataspace mappings, or enable bundle ingestion / profile BU mappings. At least one operation must be supplied. Each 'mid' value in every BU-related field may be either (a) a child BU MID under the connection's EID, or (b) the connection's own enterprise ID (EID) — configuring the enterprise-level itself is a valid scenario for ingestion, activation, and BU-to-dataspace mapping. The server rejects any value that is neither a child BU MID nor the EID with 'Invalid values for Business Unit Ids (mid): [...]'. To discover valid child MIDs call d360_connection_objects_list_sfmc with subType=SalesforceMarketingCloudBusinessUnit; the EID itself is available on the connection record via d360_connection_get. IMPORTANT: enableBundleIngestion and createProfileBuMappings are ONE-WAY enables — they cannot be reversed via this API once set to true; confirm with the user before sending either. The tool guards that the target connection is of type SalesforceMarketingCloud and returns a structured error envelope otherwise.

**Call:** `execute_connection-update-sfmc`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_connection_update_sfmc (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_connection-update-sfmc) for the param schema and, where available, a worked example.

#### `connection-update-streaming-app`

Partially update (PATCH) a Data Cloud Streaming App connection's module configurations (web, mobile, or server-side app). connectorType (StreamingApp) is auto-set. PREREQUISITE: call 'd360_connection_list' with connectorType=StreamingApp to find the connection, and pass its record id as connectionId. This is a field-level UPSERT keyed by module name: only the attributes you provide are changed, omitted attributes keep their existing values, and modules you do not list are left untouched (modules are never removed). Each module name must be a supported Streaming App module type. NOTE: module configuration must be enabled for the org; otherwise the call fails with NOT_IMPLEMENTED.

**Call:** `execute_connection-update-streaming-app`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_connection_update_streaming_app (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_connection-update-streaming-app) for the param schema and, where available, a worked example.

#### `connection-user-create`

Create a per-user connection for a shell connection. Shell connections allow multiple users to authenticate with their own credentials to the same external data source.

**Call:** `execute_connection-user-create`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_connection_user_create (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_connection-user-create) for the param schema and, where available, a worked example.

#### `connection-user-update`

Update a per-user connection's credentials or configuration. Each user maintains their own authentication to the shared shell connection.

**Call:** `execute_connection-user-update`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_connection_user_update (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_connection-user-update) for the param schema and, where available, a worked example.

### Destructive operations

#### `connection-delete`

Permanently delete a Data Cloud connection by its connectionId. This is destructive and irreversible: it disconnects the connection (for a Salesforce CRM Home Org connection this removes the Home Org connection) and cannot be undone. Only call this when the user has explicitly confirmed they want to delete the connection. Find the connectionId with d360_connection_list or d360_connection_get.

**Call:** `execute_connection-delete`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_connection_delete (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_connection-delete) for the param schema and, where available, a worked example.

#### `connection-user-delete`

Delete a specific user's per-user connection from a shell connection. Removes the user's individual credentials without affecting other users or the shell connection.

**Call:** `execute_connection-user-delete`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_connection_user_delete (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_connection-user-delete) for the param schema and, where available, a worked example.
