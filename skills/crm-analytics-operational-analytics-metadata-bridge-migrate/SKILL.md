---
name: crm-analytics-operational-analytics-metadata-bridge-migrate
description: "Use this skill when users want to oA->Tableau Next metadata bridge wizard. Trigger when users mention operational, analytics, metadata, bridge, operational analytics metadata bridge."
metadata:
  version: "1.0"
  accessCheck: "Insights.userCanUseOaMetadataBridge"
---

# Managing Operational Analytics Metadata Bridge

## When to Use This Skill

OA->Tableau Next metadata bridge wizard. Migrates legacy Operational
Analytics report-based dashboards into Tableau Next semantic data
models. Lists in-flight and completed AnalyticsInteropMigrDef records
(filter source=Oa - the Crma variant belongs to a sibling admin
surface), drills into one job by id, lists Tableau Next workspaces
and the org's Data Cloud connection, fetches DLO field metadata, and
atomically generates a target DMO plus DLO->DMO field mapping from a
dloConfig payload. Bulk status poll returns modeling state for many
DMOs in one call. First-class concepts: the migration-job source
enum {Crma, Oa} scopes lookups; the status enum {None,
DataObjectsAndFieldsDiscovered, OaReportTypesSelected,
DataLakeObjectLineageSaved, DataModelObjectLineageSaved,
CrmaDashboardsSelected, CrmaRecipesSelected, Completed, Failed}
tracks wizard progress. Update paths on the migration-job record
require echoing the current definitionVersion (optimistic locking).

## Workflow

Reads are independent (no ordering between get-active-interop-process,
get-interop-migration-history, get-interop-migration-job-by-id,
get-workspaces, get-connection-name, get-dlo-details,
get-bulk-dmo-status, get-semantic-models-for-dataspace,
get-all-semantic-model-api-names-for-dataspace). The atomic write
generate-dmo-with-mapping is initiated with a dloConfig payload;
verify-generate-dmo-with-mapping reads back via get-bulk-dmo-status
using the new DMO's developer name to confirm the deploy reached a
terminal modeling state.

Workflow - a typical OA->Tableau Next migration: (1) list active jobs
to check for an in-flight record; (2) list history for completed
migrations context; (3) fetch workspaces + Data Cloud connection to
populate wizard pickers; (4) fetch DLO field metadata for the source
DLO; (5) optionally pre-check semantic-model name collisions via
get-all-semantic-model-api-names-for-dataspace; (6) submit the
dloConfig to generate-dmo-with-mapping (or the bulk variant for
multiple DMOs in one transaction); (7) poll get-bulk-dmo-status until
the target DMO reaches Completed.

Out-of-band admin surface: POST /wave/interop/migration-jobs creates
an AnalyticsInteropMigrDef record standalone (POST response body is
7 fields: id, name, label, dataspaceApiName, definitionVersion:1,
source, status; GET on the created id returns the full 9-field record
including server-assigned createdDate and lastModifiedDate); PATCH
updates one, requiring
the caller to echo the current definitionVersion - server increments
on write (optimistic locking); DELETE removes the record. These
aren't part of the wizard's happy path but are the canonical Connect
surface for admin tools that manage AnalyticsInteropMigrDef records
directly.

Access guard: every cached controller signature (releases 262 and
264) gates all methods on Insights.userCanUseOaMetadataBridge. The
legacy Analytics Metadata Bridge access appears in NO
cached signature - the factory precondition originally named it in
error (now corrected). Callers should gate on
userCanUseOaMetadataBridge.

## Critical Constraints

**Preconditions:**

- User must have Insights UseOaMetadataBridge access (check: `Insights.userCanUseOaMetadataBridge`)

## Verification Checklist

After every write operation, confirm the effect by re-reading state:

- After `generate-dmo-with-mapping`: call `verify-generate-dmo-with-mapping` (`GET /headless/invoke/platform/operational-analytics-metadata-bridge/get-bulk-dmostatus`)

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `get-active-interop-process` | read | proposed | `GET /services/data/v66.0/wave/interop/migration-jobs` | — |
| `get-interop-migration-history` | read | proposed | `GET /services/data/v66.0/wave/interop/migration-jobs` | — |
| `get-interop-migration-job-by-id` | read | proposed | `GET /services/data/v66.0/wave/interop/migration-jobs/{interopMigrationJobId}` | — |
| `get-workspaces` | read | implemented | `GET /services/data/v66.0/tableau/workspaces` | — |
| `get-connection-name` | read | proposed | `GET /services/data/v66.0/ssot/connections` | — |
| `generate-dmo-with-mapping` | write | proposed | `PATCH /headless/invoke/platform/operational-analytics-metadata-bridge/generate-dmo-with-mapping` | — |
| `get-dlo-details` | read | proposed | `GET /services/data/v66.0/ssot/data-lake-objects/{recordIdOrDeveloperName}` | — |
| `get-bulk-dmo-status` | read | implemented | `GET /headless/invoke/platform/operational-analytics-metadata-bridge/get-bulk-dmostatus` | — |
| `verify-generate-dmo-with-mapping` | verify | proposed | `GET /headless/invoke/platform/operational-analytics-metadata-bridge/get-bulk-dmostatus` | `generate-dmo-with-mapping` |
| `get-semantic-models-for-dataspace` | read | proposed | `GET /headless/invoke/platform/operational-analytics-metadata-bridge/get-semantic-models-for-dataspace` | — |
| `get-all-semantic-model-api-names-for-dataspace` | read | proposed | `GET /headless/invoke/platform/operational-analytics-metadata-bridge/get-all-semantic-model-api-names-for-dataspace` | — |
| `generate-dmos-with-mapping-bulk` | write | proposed | `PATCH /headless/invoke/platform/operational-analytics-metadata-bridge/generate-dmos-with-mapping-bulk` | — |

### Read operations

#### `get-active-interop-process`

List interop migration jobs filtered by source=Oa; caller selects the latest entry with status=Started to recover the active OA migration. Connect representation per the InteropMigrationJob schema.

**Call:** `GET /services/data/v66.0/wave/interop/migration-jobs`   — status: `proposed`

#### `get-interop-migration-history`

List interop migration jobs filtered by source=Oa; caller filters to status=Completed and sorts by createdDate desc to recover the OA migration history.

**Call:** `GET /services/data/v66.0/wave/interop/migration-jobs`   — status: `proposed`

#### `get-interop-migration-job-by-id`

Read one interop migration job by its record id; returns the InteropMigrationJob representation with id, dataspaceApiName, definitionVersion, status, source, errorInfo, and the per-source selection lineage fields.

**Call:** `GET /services/data/v66.0/wave/interop/migration-jobs/{interopMigrationJobId}`   — status: `proposed`

**Inputs:**

- `jobId` *(`String`)*

#### `get-workspaces`

List Tableau Next workspaces visible to the running user, populating the OA bridge wizard's workspace picker. Optional limit/offset for pagination; returns workspaces array of {id, name, label}.

**Call:** `GET /services/data/v66.0/tableau/workspaces`   — status: `implemented`

#### `get-connection-name`

List Data Cloud connection records. connectorType is a REQUIRED query parameter - a request without it returns 400 ILLEGAL_QUERY_PARAMETER_VALUE ("ConnectorType must be provided"). The OA bridge passes connectorType=SalesforceDotCom; the server returns only that connector's connection metadata (server-side filtered, not caller-side), recovering the running org's Data Cloud connection used by the wizard.

**Call:** `GET /services/data/v66.0/ssot/connections`   — status: `proposed`

#### `get-dlo-details`

Read one Data Lake Object by record id or developer name; returns the DLO record with label, category, and field metadata used by the OA bridge wizard's mapping panel.

**Call:** `GET /services/data/v66.0/ssot/data-lake-objects/{recordIdOrDeveloperName}`   — status: `proposed`

**Inputs:**

- `dloApiName` *(`String`)*

#### `get-bulk-dmo-status`

Bulk-poll modeling status; List<String> of DMO developer names -> name->status map. AURA-IS-CANONICAL - no Connect/Tooling endpoint accepts a name list; substitution forces N round-trips and loses batch semantics. FACTORY GAP (live-confirmed on epic-orgfarm): this route is currently UN-INVOKABLE via the dispatcher - a headless Aura GET whose only param is a List<String> query param returns 400 REQUEST_ERROR "Invalid request", because the invoke envelope's query_params is a string-valued map and cannot carry a list. No-param and single-String-param headless GETs on the same org return 200, isolating the failure to the List<String> query encoding. This also breaks the verify-generate-dmo-with-mapping read-back step.

**Call:** `GET /headless/invoke/platform/operational-analytics-metadata-bridge/get-bulk-dmostatus`   — status: `implemented`

**Inputs:**

- `dmoDeveloperNames` *(`List<String>`)*

#### `get-semantic-models-for-dataspace`

List semantic data models scoped to one dataspace. The OA bridge wizard
calls this to populate the DMO picker per dataspace before generating
a new mapping. No public Connect / Tooling / Metadata alternative
surfaces the dataspace-scoped list shape.

**Call:** `GET /headless/invoke/platform/operational-analytics-metadata-bridge/get-semantic-models-for-dataspace`   — status: `proposed`

**Inputs:**

- `dataspaceApiName` *(`String`)* — API name of the target dataspace (default is `default`). Scopes the
returned semantic-model list to only models defined in this dataspace.

#### `get-all-semantic-model-api-names-for-dataspace`

List semantic model api names in one dataspace. The OA bridge wizard
uses this to check for duplicate name collisions before creating a
new DMO in that dataspace. Lighter-weight than the full semantic-model
list read; returns names only.

**Call:** `GET /headless/invoke/platform/operational-analytics-metadata-bridge/get-all-semantic-model-api-names-for-dataspace`   — status: `proposed`

**Inputs:**

- `dataspaceApiName` *(`String`)* — API name of the target dataspace. Scopes the returned name list to
models defined in this dataspace.

### Write operations

#### `generate-dmo-with-mapping`

Atomic DLO->DMO materialization: resolve the source DLO, create the target custom DMO when missing, and apply the field mapping in one autoCommit multi-wrapper. AURA-IS-CANONICAL - chained cdp-connect-api calls would lose autoCommit atomicity across the CdpDataLakeObject/DataModelObject/Mapping/DataSpace wrappers. The dloConfig body map (live-verified against the controller's own validation errors on epic-orgfarm) requires: dloApiName (source DLO API name, e.g. "ProvisionedFeature__dll"); dloFieldNames (List<String> of source DLO field API names to carry - REQUIRED, "Data Lake Object information must include field names"); dmoDeveloperName (target DMO developer name; the controller appends "__dlm", so "ProvisionedFeature_OA" -> "ProvisionedFeature_OA__dlm"); dataspaceApiName (default "default"); and mappingFields (list of source->target field entries, per-entry shape {sourceFieldName, targetFieldName} - structurally accepted and reached the createDMO step on epic-orgfarm). NOTE: the harness-inferred key "dlmDeveloperName" is WRONG - the controller reads "dloApiName" and 500s ("Data Lake Object information must include API name") on the wrong key.

**Call:** `PATCH /headless/invoke/platform/operational-analytics-metadata-bridge/generate-dmo-with-mapping`   — status: `proposed`

**Inputs:**

- `dloConfig` *(`Map<String, Object>`)* — Value for dlo config.

#### `generate-dmos-with-mapping-bulk`

Bulk variant of generate-dmo-with-mapping: accepts a list of dloConfig
entries plus a correlationId and atomically creates all DMOs and their
DLO field mappings in one call. AURA-IS-CANONICAL - the batch shape
+ atomic autoCommit across multiple DLO/DMO/Mapping/DataSpace wrappers
has no Connect/Tooling equivalent.

**Call:** `PATCH /headless/invoke/platform/operational-analytics-metadata-bridge/generate-dmos-with-mapping-bulk`   — status: `proposed`

**Inputs:**

- `dloConfigs` *(`List<Map<String, Object>>`)* — List of per-DMO dloConfig entries; each entry follows the SAME generate-dmo-with-mapping dloConfig contract: dloApiName (source DLO API name, e.g. "ProvisionedFeature__dll"); dloFieldNames (List<String> of source DLO field API names to carry - REQUIRED); dmoDeveloperName (target DMO developer name; the controller appends "__dlm"); dataspaceApiName (default "default"); and mappingFields (per-entry {sourceFieldName, targetFieldName}). NOTE: the harness-inferred key "dlmDeveloperName" is WRONG - the controller reads "dloApiName" and 500s ("Data Lake Object information must include API name") on the wrong key, exactly as documented on the singular generate-dmo-with-mapping step. All entries are processed inside one autoCommit transaction; partial success is not surfaced.
- `correlationId` *(`String`)* — Client-supplied correlation identifier for the bulk operation.
Downstream progress tracking (via get-bulk-dmo-status) uses the
resulting DMO developer names, not this id; supply a stable value
per bulk submission for observability.

### Verify operations

#### `verify-generate-dmo-with-mapping`

Read back via get-bulk-dmo-status with the new DMO developer name; the returned map's modeling-status entry confirms the deploy reached the platform.

**Call:** `GET /headless/invoke/platform/operational-analytics-metadata-bridge/get-bulk-dmostatus`   — status: `proposed`

**Inputs:**

- `dmoDeveloperNames` *(`List<String>`)*

**Depends on:** `generate-dmo-with-mapping`

## Notes

- **wire_contract_findings:** {'description': 'GET /wave/interop/migration-jobs?source=<invalid> returns 503 with\nerrorCode 239 ("The specified enum type has no constant with the\nspecified name: <value>"). Query-filter enum validation is\ncase-sensitive and rejects unknown values with a server-error shape\n(not a 400).', 'affected_step': 'get-active-interop-process'}, {'description': 'POST /wave/interop/migration-jobs body {source: <invalid>, ...}\nreturns 400 POST_BODY_PARSE_ERROR ("Invalid value for Invalid\ninteroperability migration source: <value>"). Body enum validation\nproduces a different error shape than the query-filter case above.', 'affected_step': 'get-active-interop-process'}, {'description': 'GET /wave/interop/migration-jobs/{invalid-id} returns 404 errorCode\n135 ("Failed to load AnalyticsInteropMigrDef for Id=<id>"). Distinct\nfrom the 118 mandatory-field code.', 'affected_step': 'get-interop-migration-job-by-id'}, {'description': 'PATCH /wave/interop/migration-jobs/{id} without definitionVersion in\nthe body returns 400 errorCode 118 ("definitionVersion is a\nmandatory field"). PATCH is not true partial merge - the caller\nmust fetch the current record and echo definitionVersion on every\nupdate. On success, the server increments definitionVersion by 1\n(optimistic-locking semantics; a stale echo will conflict).', 'affected_step': 'get-interop-migration-job-by-id'}, {'description': 'POST /wave/interop/migration-jobs body accepts a strict subset of\nthe response fields: only {source, dataspaceApiName, status} are\nwritable inputs. Including id, name, label, definitionVersion,\ncreatedDate, or lastModifiedDate in the request body returns 400\nJSON_PARSER_ERROR "Unrecognized field <field>" (short-circuits\nbefore enum validation). Server auto-assigns id, name, label\n(name defaults to AnalyticsInteropMigrDef_<random>; label mirrors\nname), definitionVersion (starts at 1), createdDate,\nlastModifiedDate.', 'affected_step': 'get-active-interop-process'}, {'description': 'PATCH /wave/interop/migration-jobs/{id} rejects `name` and `label`\nas unrecognized input fields (400 JSON_PARSER_ERROR). These are\nimmutable post-create - only `status`, `definitionVersion` (echo),\nand per-source selection lineage fields are mutable. Agents\ndriving update workflows should not attempt to rename records.', 'affected_step': 'get-interop-migration-job-by-id'}, {'description': 'PATCH body `status` field has a stricter accepted-value set than\nthe response schema exposes. Long-form values like\nDataObjectsAndFieldsDiscovered return 503 errorCode 239 ("No enum\nconstant AnalyticsInteropMigrDefStatusEnum.<abbrev>") where the\nserver has translated the input to an internal abbreviation\nbefore enum lookup. The short abbreviation itself (e.g., DOAFD)\nreturns 400 POST_BODY_PARSE_ERROR "Invalid value for status".\nConfirmed accepted: None. Agents should treat the write-side\nstatus enum as a distinct, less permissive set than the response\nschema - probe or use `get-interop-migration-job-by-id` to\ndiscover an accepted value before PATCH-transitioning state.', 'affected_step': 'get-interop-migration-job-by-id'}, {'description': 'definitionVersion does not increment strictly by +1 per successful\nPATCH. After POST (v1), a successful PATCH may return v3 or higher\neven when no prior successful PATCH occurred - validation-error\npaths (400/503) can still bump the internal version counter, or\nthe successful PATCH itself may bump by more than one. Agents MUST\nround-trip a GET after any successful write to recover the current\nversion before the next PATCH; do not assume +1 arithmetic.', 'affected_step': 'get-interop-migration-job-by-id'}
