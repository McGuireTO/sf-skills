---
name: data360-data-streams-create
description: "Use this skill when users want to execute Data Cloud DataStreams operations via the Data 360 MCP facade. Trigger when users mention data360/data, streams, shared, cdp, mcp, connect, api, shared-cdp-mcp-connect-api."
metadata:
  version: "1.0"
---

# Managing Data360/data Streams

## When to Use This Skill

Execute Data Cloud DataStreams operations via the Data 360 MCP facade.

## Workflow

Each step lists an `operation` id. Call describe(<operation>) BEFORE dispatching to get that tool's parameter schema and, where available, a worked example. `paramsJson` decodes to the operation's requestBody schema VERBATIM, including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap or omit it. The only envelope the step handles for you is `{toolName, paramsJson}` (its `invocation` already wraps it); do not POST the operation path directly. If the tool's error suggests `payload_examples`, ignore it — that tool isn't available here; call describe(<operation>) instead. A Connection is usually a prerequisite for creating a data stream; see the data360/connection SOR.

## Critical Constraints

**Destructive operations — require explicit user confirmation:**

- **`datastream-delete`** — Delete a data stream by recordIdOrDeveloperName. Set shouldDeleteDataLakeObject=true to also remove the underlying DLO; otherwise the DLO is preserved. Deletion is asynchronous: on success the stream enters a DELETING state and may still appear in get/list for a while before it is fully removed -- this is expected, not a failure, and re-issuing delete on an already-deleting stream returns 'already deleted'. A stream cannot be deleted while it is still PROCESSING (e.g. a freshly created stream mid initial run) -- wait until it is ACTIVE.
  - Rollback: No automatic rollback.

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `datastream-activate` | write | implemented | `execute_datastream-activate` | — |
| `datastream-create` | write | implemented | `execute_datastream-create` | — |
| `datastream-create-aws-s3` | write | implemented | `execute_datastream-create-aws-s3` | — |
| `datastream-create-ingestion-api` | write | implemented | `execute_datastream-create-ingestion-api` | — |
| `datastream-create-sfdc` | write | implemented | `execute_datastream-create-sfdc` | — |
| `datastream-create-sfmc-bundle` | write | implemented | `execute_datastream-create-sfmc-bundle` | — |
| `datastream-create-sfmc-data-extension` | write | implemented | `execute_datastream-create-sfmc-data-extension` | — |
| `datastream-create-sfmc-standard` | write | implemented | `execute_datastream-create-sfmc-standard` | — |
| `datastream-create-snowflake` | write | implemented | `execute_datastream-create-snowflake` | — |
| `datastream-create-streaming-app` | write | implemented | `execute_datastream-create-streaming-app` | — |
| `datastream-create-third-party-connectors` | write | implemented | `execute_datastream-create-third-party-connectors` | — |
| `datastream-delete` | delete | implemented | `execute_datastream-delete` | — |
| `datastream-dependencies-list` | read | implemented | `execute_datastream-dependencies-list` | — |
| `datastream-get` | read | implemented | `execute_datastream-get` | — |
| `datastream-list` | read | implemented | `execute_datastream-list` | — |
| `datastream-patch-ingestion-api` | write | implemented | `execute_datastream-patch-ingestion-api` | — |
| `datastream-patch-streaming-app` | write | implemented | `execute_datastream-patch-streaming-app` | — |
| `datastream-refresh-history-list` | read | implemented | `execute_datastream-refresh-history-list` | — |
| `datastream-retry` | write | implemented | `execute_datastream-retry` | — |
| `datastream-run` | write | implemented | `execute_datastream-run` | — |
| `datastream-source-fields-list` | read | implemented | `execute_datastream-source-fields-list` | — |
| `datastream-update` | write | implemented | `execute_datastream-update` | — |
| `datastream-update-aws-s3` | write | implemented | `execute_datastream-update-aws-s3` | — |
| `datastream-update-sfdc` | write | implemented | `execute_datastream-update-sfdc` | — |
| `datastream-update-sfmc` | write | implemented | `execute_datastream-update-sfmc` | — |
| `datastream-update-snowflake` | write | implemented | `execute_datastream-update-snowflake` | — |

### Read operations

#### `datastream-dependencies-list`

List entities that depend on a data stream. Use as a pre-flight check before deleting the data stream.

**Call:** `execute_datastream-dependencies-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_datastream_dependencies_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_datastream-dependencies-list) for the param schema and, where available, a worked example.

#### `datastream-get`

Get a single data stream by recordIdOrDeveloperName. Returns full configuration including source schema, target DLO, refresh schedule/status, and field mappings. Field mappings are always included: each mapping has a targetFieldName plus either a sourceFieldName (a directly mapped source field) or a formula (a formula field's expression). Note: a formula field's expression is READ here under the 'formula' key, but WRITTEN via 'transformationFormula' on d360_datastream_update.

**Call:** `execute_datastream-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_datastream_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_datastream-get) for the param schema and, where available, a worked example.

#### `datastream-list`

List data streams. WARNING: each entry is large because it embeds the full source and target DLO field schema, so request a small page. Use limit (default 10, min 1, max 200) and page with offset, reading totalSize and nextPageUrl in the response. To find specific streams cheaply, narrow server-side with filter (connector type), connectionName, or sourceObjectName instead of paging the whole org. IMPORTANT: 'filter' accepts ONLY these short codes, case-sensitive: 'EVENTS' (StreamingApp), 'SFDC' (SalesforceDotCom), 'MC' (SalesforceMarketingCloud — returns both MC bundle and MCDE streams), 'AE' (AccountEngagement), 'INGESTAPI'. Passing the full connectorType wire name (for example 'SalesforceMarketingCloud') matches nothing and returns an unfiltered page silently. Pass multiple codes as a comma-separated list. Leave includeMappings off (the default) unless you need DLO-DMO field mappings, as it makes each entry even larger. For one stream's full configuration, call d360_datastream_get by recordIdOrDeveloperName rather than enlarging the page.

**Call:** `execute_datastream-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_datastream_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_datastream-list) for the param schema and, where available, a worked example.

#### `datastream-refresh-history-list`

List paginated refresh history for a data stream.

**Call:** `execute_datastream-refresh-history-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_datastream_refresh_history_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_datastream-refresh-history-list) for the param schema and, where available, a worked example.

#### `datastream-source-fields-list`

List the source fields for a data stream, with optional status filtering and pagination.

**Call:** `execute_datastream-source-fields-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_datastream_source_fields_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_datastream-source-fields-list) for the param schema and, where available, a worked example.

### Write operations

#### `datastream-activate`

Activate a single data stream in NEEDS_ACTIVATION status by recordIdOrDeveloperName 

**Call:** `execute_datastream-activate`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_datastream_activate (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_datastream-activate) for the param schema and, where available, a worked example.

#### `datastream-create`

Create a new data stream (generic). 

**Call:** `execute_datastream-create`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_datastream_create (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_datastream-create) for the param schema and, where available, a worked example.

#### `datastream-create-aws-s3`

Create a data stream from an AWS S3 file. PREREQUISITE: Before calling this tool, call 'd360_connection_list' with connectorType=AwsS3 and present the user with the available connections so they can select the connection to use. datastreamType (CONNECTORSFRAMEWORK) and connectorType (DataConnector) are auto-set. Provide name, label, connectionName, advancedAttributes (fileType, importDirectory, fileName, delimiter, headerlessRetrievalEnabled), DLO definition with fields, and refreshMode. Take the file name from the user and use d360_connection_object_fields_describe tool with {  "advancedAttributes": {}} payload to get the schema and fields of the file. Map that describe output into 'fields': each describe entry's 'name' becomes the field 'label' (the source column), and you choose the target DLO field 'name'; carry over the type as 'dataType' and add 'isPrimaryKey' (the describe call returns no primary key, so pick one). Supported dataType values are: Text, Number, Date, DateTime, Boolean, Email, Phone, Url, Percent (aliases: VARCHAR->Text, FLOAT->Number, TIMESTAMP->DateTime). Currency and other types are not supported. Before creating, this tool validates that the S3 file exists and that every field 'label' is a real column in the file; if the file is missing or a label is unknown it returns an error and creates nothing.

**Call:** `execute_datastream-create-aws-s3`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_datastream_create_aws_s3 (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_datastream-create-aws-s3) for the param schema and, where available, a worked example.

#### `datastream-create-ingestion-api`

Create an Ingestion API data stream from an existing Ingestion API connection. PREREQUISITE: Before calling this tool, call 'd360_connection_list' with connectorType=IngestApi and present the user with the available connections so they can select the connection to use. ALWAYS use the connection's developer name as the connectionName parameter. connectorType (IngestApi) is auto-set. The schema is defined on the connection, so you do NOT pass full field definitions -- you pass the single event name to ingest (Ingestion API data streams have EXACTLY ONE event) and, for a new DLO, which schema field is the primary key. Provide EITHER a new Data Lake Object (dloName, dloLabel, category, and primaryKeyField*) OR an existing one (existingDloName) -- never both. For an existing DLO, refreshMode is REQUIRED. Ingestion API supports only UPSERT or PARTIAL_UPDATE refresh modes; Engagement streams allow only UPSERT.

**Call:** `execute_datastream-create-ingestion-api`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_datastream_create_ingestion_api (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_datastream-create-ingestion-api) for the param schema and, where available, a worked example.

#### `datastream-create-sfdc`

Create a data stream from a Salesforce CRM object. PREREQUISITE: Before calling this tool, call 'd360_connection_list' with connectorType=SalesforceDotCom and present the user with the organizationId, alias, and connectorType from the output so they can select the connection to use. ALWAYS use the connection's alias as the connectionAliasOrOrganizationId parameter. Only fall back to organizationId if alias is not present. The dataStreamName and dloName are auto-derived as '{sourceObject}_{connectionAliasOrOrganizationId}' unless explicitly overridden. IMPORTANT: Event/transactional objects (Case, CaseComment, Task, Event, ActivityHistory) MUST use category='Engagement' with eventDateTimeFieldName (e.g. 'CreatedDate'). Profile objects (Contact, Account, Lead) use category='Profile'. OPTIONAL fullRefreshIntervalDays controls how often a periodic full refresh runs for the CRM stream: NONE (default), DAYS_10, DAYS_25, or DAYS_50. Set it to a non-NONE value to schedule a configurable full refresh; leave it unset/NONE to keep the org default. OPTIONAL sourceRecordsFilter is a SOQL WHERE clause (without the 'WHERE' keyword, e.g. "Industry = 'Technology'") applied to the CRM source records during ingestion; omit it to ingest all records. Requires the CdpSfdcDataStreamFiltering org permission (PILOT). OPTIONAL formulaFields adds formula (calculated) fields to the stream's DLO at creation time. Unlike file-based connectors, you do NOT enumerate source fields for CRM -- only the formula fields you want added. Each entry needs name (target field name), formula (the transformation expression, e.g. "UPPER(Name)"), and returnType (one of Text, Number, Date, DateTime, Email, Phone, Url, Percent, Boolean, Currency).

**Call:** `execute_datastream-create-sfdc`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_datastream_create_sfdc (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_datastream-create-sfdc) for the param schema and, where available, a worked example.

#### `datastream-create-sfmc-bundle`

Create ALL Salesforce Marketing Cloud (SFMC) standard bundle data streams for one bundle/channel (COMMON, EMAIL, MOBILE_CONNECT, MOBILE_PUSH, or WHATSAPP) across the connection's Marketing Cloud Business Units (BUs) that are enabled for ingestion — in one call. For a specific channel (EMAIL, MOBILE_CONNECT, MOBILE_PUSH, WHATSAPP) the tool ALWAYS also includes the connection's COMMON streams (Campaign, Journey, JourneyActivity, Subscriber, …), matching the Setup UI. Request bundleType=COMMON to deploy only the shared streams. EXCEPTION — 'Journey Activity Run' is an OPTIONAL add-on and is NEVER deployed implicitly: it is held back unless the caller sets includeJourneyActivityRun=true. When it is eligible but held back, the response reports journeyActivityRunAvailable=true so you can confirm with the user before re-invoking with the opt-in. Each stream is created at its correct scope: enterprise-level streams are created ONCE with mid = eid for the whole connection, while Business-Unit-specific streams are created once per target BU MID — so the planned/created/skipped/failed entries are NOT a simple mids × streams product, and totalPlanned reflects the actual (mid, streamName) work-list. Supply exactly one of connectionId (preferred) or connectionName. By default fans out over every BU already enabled for ingestion on the connection (discovered from the connection record; may include the connection's own EID as an ingestion target, which is a valid configuration). Pass 'mids' to restrict to a subset; every supplied MID must be in the ingestion-enabled set on THIS connection. The tool distinguishes two failure shapes on unknown MIDs: MIDs that exist under the EID but are not yet ingestion-enabled are returned in 'notEnabledForIngestionMids[]' (use d360_connection_update_sfmc with addIngestionBusinessUnits to enable them first — enabling the EID itself is valid); MIDs that neither match the EID nor any child BU under it are returned in 'notInEidMids[]' (usually a typo). Both cases fail-fast before any stream is created. Before creating, the tool pre-fetches the streams already deployed on this connection/EID and skips them, so the plan and counts reflect only what will actually be created (matching the Setup UI). Set dryRun=true to preview: the response returns planned[] and totalPlanned (the streams that WOULD be created) plus alreadyExistsStreams[] and alreadyExists (the streams skipped as already-deployed), without creating anything. Response envelope carries three per-stream buckets: created[] (newly created, with dataStreamId), skipped[] (already existed on the connection — reason: 'already exists'; pre-filtered by the existing-stream fetch, plus any duplicate detected at create time), and failed[] (real errors — bad payload, gate closed, etc.). Making the tool re-runnable: on a second invocation, previously-created streams show up in skipped[] not failed[], so success=(failed[] is empty) stays true. Per-stream failures never abort the batch by default; set continueOnError=false to abort on the first real failure ('already exists' is a soft skip and never triggers abort). PREREQUISITE: The MC connection must be authenticated (post-OAuth) and have at least one BU enabled for ingestion; both are enforced upfront. DATASPACE PREREQUISITE — enabling BUs for ingestion is NOT sufficient: every BU this bundle deploys against must ALSO be mapped to at least one dataspace via d360_connection_update_sfmc (addBusinessUnitsToDataSpaces=[{mid, dataspaceName}]) or those streams fail server-side with 'This Business Unit <mid> is not mapped to any dataspaces'. Which MID each stream needs mapped depends on stream scope: BU-specific streams deploy per BU MID (each target MID must be mapped), while enterprise-level (COMMON/most EMAIL) streams deploy once at mid=eid (the EID ITSELF must be mapped to a dataspace — a child-BU mapping does not cover it). This tool takes NO dataspace parameter — dataspace placement comes from the connection's BU->dataspace mapping, not from the call. A request like 'create the bundle in dataspace abc' cannot be honored here; first map the relevant BUs/EID to 'abc' via d360_connection_update_sfmc. (Only d360_datastream_create_sfmc_data_extension accepts an explicit dataspace.) Run d360_connection_status_sfmc first — its gaps.midsWithoutDataspace lists ingestion-enabled MIDs still missing a mapping. Stream-eligibility filters (MCR, SMS 1.0 vs 2.0, Push 1.0 vs 2.0, PushClick gate, EnterpriseProfileAttribute) are inherited from the platform via the connection's Standard-object listing — no logic is duplicated in this tool. LONG-RUNNING: This tool loops synchronously over every planned (mid, streamName) unit, invoking d360_datastream_create_sfmc_standard per stream. Each per-stream deployment typically takes 3-10 minutes server-side, so a full bundle can run 30+ minutes wall-clock. Configure the MCP client with a very long request timeout (60+ minutes) or run this tool with dryRun=true first to size the fan-out, then invoke it in a job/background context that can tolerate long waits. If the client times out mid-batch, streams that already succeeded remain created; a follow-up invocation will bucket them as skipped[] (reason 'already exists') rather than re-creating, so re-running is safe.

**Call:** `execute_datastream-create-sfmc-bundle`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_datastream_create_sfmc_bundle (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_datastream-create-sfmc-bundle) for the param schema and, where available, a worked example.

#### `datastream-create-sfmc-data-extension`

Create a data stream from a Salesforce Marketing Cloud data extension (DE). PREREQUISITES: (1) Call 'd360_connection_list_sfmc' to discover the MC connection EID. (2) Call 'd360_connection_objects_list_sfmc' with subType=SalesforceMarketingCloudBusinessUnit to confirm the Marketing Cloud Business Unit's MID. (3) Call 'd360_connection_objects_list_sfmc' with subType=SalesforceMarketingCloudDataExtension (with the discovered MID and a name LIKE filter) to discover the customObjectId and customObjectName. Unlike the standard tool, the caller supplies the full DLO definition (fields), mappings, and refresh configuration. connectorType and subType are set automatically. Mappings may include a transformationFormula with targetFieldReturntype for derived fields. Supported dataType / targetFieldReturntype values: Text, Number, Date, DateTime, Boolean, Email, Phone, Url, Percent, Currency. The target Business Unit (identified by MID) must be enabled for ingestion on the connection; otherwise create fails server-side. MC data streams cannot be created with isEnabled=false. When refreshMode=UPSERT, set mcDataExtractMode to an incremental value AND supply mcDeltaExtractField (the tool enforces this). LONG-RUNNING: MC data extension deployment is synchronous under this Connect API and typically takes 3-10 minutes (DLO + DTO + DataStreamDefinition + field mappings + key-qualifier setup). Configure the MCP client with at least a 15-minute request timeout for this call. If the client times out before the server finishes, DO NOT retry immediately — the deployment may still be in progress server-side and a retry can produce a duplicate-SetupEntityAccess error. Instead, poll 'd360_datastream_get' with the developer name you supplied (the 'name' param) until it returns the stream; only retry the create if the stream is still absent after ~15 minutes.

**Call:** `execute_datastream-create-sfmc-data-extension`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_datastream_create_sfmc_data_extension (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_datastream-create-sfmc-data-extension) for the param schema and, where available, a worked example.

#### `datastream-create-sfmc-standard`

Create a data stream from a Salesforce Marketing Cloud standard bundle object (e.g. 'Subscriber', 'EmailEngagementSend', 'EmailEngagementOpen', 'EmailEngagementClick', 'EmailEngagementBounce'). The data stream definition (name, label, fields, mappings, refresh schedule) is derived automatically by the platform from the bundle object, so only eid, mid, and sourceObjectName are needed. PREREQUISITES: (1) Call 'd360_connection_list_sfmc' to discover the MC connection EID. (2) Call 'd360_connection_objects_list_sfmc' with subType=SalesforceMarketingCloudBusinessUnit to confirm the target Marketing Cloud Business Unit's MID. (3) Call 'd360_connection_objects_list_sfmc' with subType=SalesforceMarketingCloudStandard to discover valid sourceObjectName values for this connection (each result carries name = the stream, and bundleName = its channel like EMAIL / MOBILE_CONNECT / COMMON). 'EnterpriseProfileAttribute' is not supported. DATASPACE PREREQUISITE — enabling the BU for ingestion is NOT sufficient on its own: the target Business Unit (identified by MID) must ALSO be mapped to at least one dataspace via d360_connection_update_sfmc (addBusinessUnitsToDataSpaces=[{mid, dataspaceName}]); an ingestion-enabled BU with no dataspace mapping fails server-side with 'This Business Unit <mid> is not mapped to any dataspaces'. Note this tool takes NO dataspace parameter — the stream's dataspace is derived from the BU->dataspace mapping on the connection, NOT chosen at create time. A request like 'create this standard stream in dataspace abc' cannot be honored here; to place the data in dataspace 'abc' you must first map the BU (or the EID, for enterprise-level streams) to 'abc' via d360_connection_update_sfmc. Only d360_datastream_create_sfmc_data_extension (custom DE streams) accepts an explicit dataspace. MC data streams cannot be created with isEnabled=false. LONG-RUNNING: MC bundle deployment is synchronous under this Connect API and typically takes 3-10 minutes (DLO + DTO + DataStreamDefinition + field mappings + key-qualifier setup). Configure the MCP client with at least a 15-minute request timeout for this call. If the client times out before the server finishes, DO NOT retry immediately — the deployment may still be in progress server-side and a retry can produce a duplicate-SetupEntityAccess error. Instead, poll 'd360_datastream_get' with the expected developer name 'sfmc_<snake_case_source_object>_<mid>' (e.g. sourceObjectName='EmailEngagementBounce' + mid='524000862' -> 'sfmc_email_engagement_bounce_524000862') until it returns the stream; only retry the create if the stream is still absent after ~15 minutes.

**Call:** `execute_datastream-create-sfmc-standard`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_datastream_create_sfmc_standard (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_datastream-create-sfmc-standard) for the param schema and, where available, a worked example.

#### `datastream-create-snowflake`

Create a Snowflake-backed data stream using an existing Snowflake connection. Automatically builds sourceFields, mappings, advancedAttributes (database/schema/object), and dataLakeObjectInfo from the provided fields. Use 'label' for the Snowflake source column name and 'name' for the target DLO field name; the target DLO field name is lowercased to match Data Cloud conventions. To create an accelerated (zero-copy) Direct Access stream, set isAccelerationEnabled=true and provide a zero-copy 'frequency' (NONE, MINUTES_15, MINUTES_30, or HOURLY).

**Call:** `execute_datastream-create-snowflake`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_datastream_create_snowflake (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_datastream-create-snowflake) for the param schema and, where available, a worked example.

#### `datastream-create-streaming-app`

Create a streaming app (events) data stream from an existing Streaming App connection (web, mobile, or server-side app). PREREQUISITE: Before calling this tool, call 'd360_connection_list' with connectorType=StreamingApp and present the user with the available connections so they can select the connection to use. ALWAYS use the connection's developer name as the connectionName parameter. connectorType (StreamingApp) is auto-set. Unlike file/warehouse data streams, the schema is defined on the connection, so you do NOT pass field definitions -- you pass the list of event names to ingest. IMPORTANT: category='Other' is only valid for streamingAppType='ServerApp'. For WebApp and MobileApp connections, only one 'Engagement' data stream can exist per connection; ServerApp connections can have multiple 'Engagement' data streams.

**Call:** `execute_datastream-create-streaming-app`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_datastream_create_streaming_app (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_datastream-create-streaming-app) for the param schema and, where available, a worked example.

#### `datastream-create-third-party-connectors`

Create a data stream for a third-party connector (e.g. Airtable, HubSpot, Marketo, Google Ads, or any other connector). PREREQUISITE: Call 'd360_connection_list' to find the connection, then 'd360_connection_objects_list' and 'd360_connection_object_fields_describe' to discover available objects and their fields. Automatically builds sourceFields, mappings, dataLakeObjectInfo, and advancedAttributes. datastreamType=CONNECTORSFRAMEWORK and connectorType=DataConnector are set automatically.

**Call:** `execute_datastream-create-third-party-connectors`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_datastream_create_third_party_connectors (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_datastream-create-third-party-connectors) for the param schema and, where available, a worked example.

#### `datastream-patch-ingestion-api`

Patch an existing Ingestion API data stream. Two INDEPENDENT operations are supported and may be combined in a single call: (1) syncSchema=true pulls in new source fields that have appeared on the connection; (2) mappings adds new formula/transformation fields to the DLO. Provide at least ONE of the two. PREREQUISITE: identify the target data stream first (e.g. via 'd360_datastream_list') and pass its record id or developer name as recordIdOrDeveloperName. connectorType (IngestApi) is auto-set. Each mapping needs targetFieldName, targetFieldReturntype, and exactly ONE of sourceFieldLabel or transformationFormula.

**Call:** `execute_datastream-patch-ingestion-api`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_datastream_patch_ingestion_api (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_datastream-patch-ingestion-api) for the param schema and, where available, a worked example.

#### `datastream-patch-streaming-app`

Patch an existing streaming app (events) data stream. Use this to either sync the data stream's schema with the latest schema on its connection, OR add new events to an existing Engagement data stream -- exactly ONE of those two operations per call. PREREQUISITE: identify the target data stream first (e.g. via 'd360_datastream_list') and pass its record id or developer name as recordIdOrDeveloperName. connectorType (StreamingApp) is auto-set. IMPORTANT: provide EITHER syncSchema=true OR a non-empty addEvents list, never both and never neither. To change source-field transformations/formula fields instead, use d360_datastream_update.

**Call:** `execute_datastream-patch-streaming-app`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_datastream_patch_streaming_app (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_datastream-patch-streaming-app) for the param schema and, where available, a worked example.

#### `datastream-retry`

Retry a data stream that is in ERROR status.

**Call:** `execute_datastream-retry`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_datastream_retry (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_datastream-retry) for the param schema and, where available, a worked example.

#### `datastream-run`

Trigger an on-demand ingestion run of a data stream by recordIdOrDeveloperName. Set processAllRecords=true for a FULL REFRESH (re-ingests ALL source records); omit it or set false for an INCREMENTAL run (default -- only records new or changed since the last run). Set interactive=true for synchronous low-latency execution.

**Call:** `execute_datastream-run`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_datastream_run (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_datastream-run) for the param schema and, where available, a worked example.

#### `datastream-update`

Update an existing data stream by recordIdOrDeveloperName. Use to change refresh schedule, source schema, transformations, or labels without recreating the stream. Field operations that are easy to miss: (1) sourceFields is add-only -- listing a field adds it (each added field needs name AND dataType), but omitting a field does NOT remove it. (2) To stop ingesting / remove a field, send a mappings entry with the targetFieldName set and an empty transformationFormula (and no source field) -- this disables the field and drops it from the stream's sourceFields. (3) To ADD a formula field, send a mappings entry with the targetFieldName set, a non-empty transformationFormula (the expression, e.g. \

**Call:** `execute_datastream-update`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_datastream_update (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_datastream-update) for the param schema and, where available, a worked example.

#### `datastream-update-aws-s3`

Update an existing AWS S3-backed data stream. Sends a SPARSE PATCH: only the arguments you supply are updated; omitted arguments are left untouched. Identify the stream by its record id or developer name. Updatable: label, connectionName (renames the underlying connection), S3 advancedAttributes (fileName, importDirectory, fileType, delimiter, headerlessRetrievalEnabled), fields (rebuilds sourceFields + mappings), refreshMode (TOTAL_REPLACE or UPSERT), and isEnabled (true activates, false deactivates). At least one updatable argument is required.

**Call:** `execute_datastream-update-aws-s3`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_datastream_update_aws_s3 (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_datastream-update-aws-s3) for the param schema and, where available, a worked example.

#### `datastream-update-sfdc`

Update an existing Salesforce CRM (SalesforceDotCom) data stream. This is the CRM-specific counterpart to the generic d360_datastream_update: it exposes ONLY the fields that are actually patchable on a CRM stream, so you never have to guess which of the generic tool's fields apply to CRM. PREREQUISITE: the target must be a SalesforceDotCom stream in Active, Error, or Inactive status (a stream still PROCESSING cannot be patched). Supply only the fields you want to change; omitted fields are left untouched. enableDeletionDlo toggles the Deletion DLO (delete-history retention) for the stream. sourceRecordsFilter sets a SOQL WHERE clause (without the 'WHERE' keyword) applied to source records; pass an empty string to clear it. Requires the CdpSfdcDataStreamFiltering org permission (PILOT). fullRefreshIntervalDays changes the periodic full-refresh interval: NONE, DAYS_10, DAYS_25, or DAYS_50. formulaFields ADDS/UPDATES or REMOVES formula (calculated) fields: an entry with a non-empty formula adds or updates the field (needs name, formula, returnType); an entry whose formula is empty REMOVES that field. label changes the data stream's display label.

**Call:** `execute_datastream-update-sfdc`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_datastream_update_sfdc (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_datastream-update-sfdc) for the param schema and, where available, a worked example.

#### `datastream-update-sfmc`

Update a Salesforce Marketing Cloud Data Extension (MCDE) data stream by recordIdOrDeveloperName. Only MCDE streams are supported — MC bundle streams (dataStreamType=MC) and MCIS streams are NOT patchable and are rejected upfront. The MCDE patch surface is narrow: you may add new source fields (sourceFields) and set/disable mappings. To DISABLE a field, send a mapping with an empty transformationFormula for that targetFieldName. To set/update a formula, send a non-empty transformationFormula (and targetFieldReturntype for derived fields). isEnabled and refreshConfig are NOT patchable for MCDE and are rejected upfront. EID/MID are resolved server-side from the EDC — agents do NOT supply them.

**Call:** `execute_datastream-update-sfmc`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_datastream_update_sfmc (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_datastream-update-sfmc) for the param schema and, where available, a worked example.

#### `datastream-update-snowflake`

Update an existing Snowflake-backed data stream. Sends a SPARSE PATCH: only the arguments you supply are updated; omitted arguments are left untouched. Identify the stream by its record id or developer name. Updatable: label, connectionName (renames the underlying connection), Snowflake advancedAttributes (database, schema, object, incrementalColumn), fields (rebuilds sourceFields + mappings), refreshMode (TOTAL_REPLACE or UPSERT), and isEnabled (true activates, false deactivates). At least one updatable argument is required. Note: the PATCH advancedAttribute keys are lowercase (database/schema/object), unlike the create tool.

**Call:** `execute_datastream-update-snowflake`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_datastream_update_snowflake (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_datastream-update-snowflake) for the param schema and, where available, a worked example.

### Destructive operations

#### `datastream-delete`

Delete a data stream by recordIdOrDeveloperName. Set shouldDeleteDataLakeObject=true to also remove the underlying DLO; otherwise the DLO is preserved. Deletion is asynchronous: on success the stream enters a DELETING state and may still appear in get/list for a while before it is fully removed -- this is expected, not a failure, and re-issuing delete on an already-deleting stream returns 'already deleted'. A stream cannot be deleted while it is still PROCESSING (e.g. a freshly created stream mid initial run) -- wait until it is ACTIVE.

**Call:** `execute_datastream-delete`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_datastream_delete (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_datastream-delete) for the param schema and, where available, a worked example.
