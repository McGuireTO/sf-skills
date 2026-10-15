---
name: experience-apex-pages-configure
description: "Use this skill when users want to manage Visualforce Apex Pages (key prefix `066`) via the Tooling sObject API. Trigger when users mention apex, pages, apex pages."
metadata:
  version: "1.0"
  accessCheck: "UserPermissions.ViewSetup"
---

# Managing Apex Pages

## When to Use This Skill

Manage Visualforce Apex Pages (key prefix `066`) via the Tooling sObject API. UDD
`sobjectFamily="TOOLING"` blocks standard sObject CRUD; Metadata API CRUD is
documented-broken on FullName (BI-EDS udd/216/ApexPage.entity.xml line 22). Tooling
sObject is the only working programmatic surface.

- List: `GET /services/data/v66.0/tooling/query?q=SELECT ... FROM ApexPage` —
  filterable on Name, MasterLabel, NamespacePrefix, ApiVersion, ControllerType.
- Read one: `GET /services/data/v66.0/tooling/sobjects/ApexPage/{id}` — returns
  full record incl. Markup, Metadata (ApexPageDescriptor), NamespacePrefix.
- Create: `POST /services/data/v66.0/tooling/sobjects/ApexPage` with required
  body `{Name, MasterLabel, ApiVersion, Markup}`.

Required-on-create: `Name` (DeveloperName, ≤80), `MasterLabel` (≤80), `ApiVersion`
(DOUBLE, scale=1), `Markup` (CLOB, ≤1,048,576 chars). `ControllerType` is the
`ApexPageControllerType` enum (Standard | Custom | Extension) — first-class on
create when binding the page to a controller. Update (PATCH) and delete
(DELETE) on `/sobjects/ApexPage/{id}` exist in the Tooling REST contract but
are dropped from this SOR by the producer-merge layer; see `notes.coverage_gap`.

## Workflow

Workflow: list_ApexPage_1 (SOQL filter to find a page by Name / MasterLabel /
ControllerType) → get_ApexPage_1 by Id (returns full Markup + Metadata) →
create_ApexPage_1 with required `{Name, MasterLabel, ApiVersion, Markup}`.
Read steps are independent — call get_ApexPage_1 directly when the Id is
already known.

## Critical Constraints

**Preconditions:**

- Org must have Apex Pages enabled (`Apex Pages enabled` feature gate). Without this org-level setting the Tooling REST surface returns no rows / refuses writes regardless of user permissions. (check: `Apex Pages enabled`)
- Read access requires `OrgPermissions.AuthorApexPages` plus `UserPermissions.ViewSetup` (the Tooling per-API-access tuple on the ApexPage entity). (check: `UserPermissions.ViewSetup`)
- Create / update / delete requires `Customize Application permission` (entity `editAccess` on ApexPage). (check: `Customize Application permission`)

**Destructive operations — require explicit user confirmation:**

- **`delete_ApexPage_1`** — Delete a ApexPage record by Id via the Tooling/sObject API. The {id} path parameter is the record Id.
  - Rollback: No automatic rollback.

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `list_ApexPage_1` | read | — | `query.ApexPage` | — |
| `get_ApexPage_1` | read | — | `sobjects/ApexPage/{id}` | — |
| `create_ApexPage_1` | write | — | `sobjects/ApexPage` | — |
| `update_ApexPage_1` | write | — | `sobjects/ApexPage/{id}` | — |
| `delete_ApexPage_1` | delete | — | `sobjects/ApexPage/{id}` | — |

### Read operations

#### `list_ApexPage_1`

SOQL over ApexPage via Tooling. Filter on Name (DeveloperName), MasterLabel, NamespacePrefix, ApiVersion, ControllerType. Markup is large (≤1MB) — project explicitly when needed. Paginate via nextRecordsUrl when totalSize > 2000.

**Call:** `query.ApexPage`

**Output:** Tooling QueryResult: {totalSize: int, done: bool, nextRecordsUrl: string|null, records: [{Id (066…), Name, MasterLabel, ApiVersion, ControllerType, NamespacePrefix, ManageableState, CreatedDate, LastModifiedDate, ...projected}]}. done=false → call nextRecordsUrl to continue paging.

#### `get_ApexPage_1`

Get one ApexPage by Id (key prefix 066). Returns the full record including Markup (≤1MB CLOB), MasterLabel, ApiVersion (DOUBLE), ControllerType (`ApexPageControllerType` enum: Standard | Custom | Extension), Metadata (ApexPageDescriptor), NamespacePrefix. 404 NOT_FOUND when the Id is unknown.

**Call:** `sobjects/ApexPage/{id}`

**Output:** Full ApexPage record: {Id (066…), Name (DeveloperName, ≤80), MasterLabel (≤80), ApiVersion (DOUBLE), Markup (CLOB ≤1,048,576 chars), ControllerType (ApexPageControllerType enum: Standard|Custom|Extension), ControllerKey, NamespacePrefix, ManageableState, IsAvailableInTouch (bool), CreatedDate, LastModifiedDate, SystemModstamp, Metadata (ApexPageDescriptor — Tooling-only), FullName (Tooling-only)}.

### Write operations

#### `create_ApexPage_1`

POST a new ApexPage. Required body fields: `Name` (DeveloperName, ≤80), `MasterLabel` (≤80), `ApiVersion` (DOUBLE), `Markup` (CLOB ≤1,048,576). Optional: `ControllerType` (ApexPageControllerType enum), `ControllerKey`, `Description`. Returns Tooling SaveResult `{id, success, errors[]}` plus a Location header pointing at `/sobjects/ApexPage/{id}`.

**Call:** `sobjects/ApexPage`

**Output:** Tooling SaveResult: {id: string (066…, the new ApexPage Id), success: bool, errors: [{statusCode, message, fields[]}]}. On success the response Location header carries `/services/data/v66.0/tooling/sobjects/ApexPage/{id}`. On REQUIRED_FIELD_MISSING / DUPLICATE_DEVELOPER_NAME / INVALID_FIELD, errors[] is populated and success=false.

#### `update_ApexPage_1`

Update a ApexPage record by Id via the Tooling/sObject API. The {id} path parameter is the record Id; body fields replace existing values.

**Call:** `sobjects/ApexPage/{id}`

### Destructive operations

#### `delete_ApexPage_1`

Delete a ApexPage record by Id via the Tooling/sObject API. The {id} path parameter is the record Id.

**Call:** `sobjects/ApexPage/{id}`
