---
name: experience-community-flexi-page-list-create
description: "Use this skill when users want to browse and manage FlexiPage records that drive Experience Cloud (Communities) Builder pages — the records whose Type sits in the FlexiPageType.Container=COMMUNITIES subset (CommObjectPage, CommRecordPage, CommLoginPage, CommThemeLayoutPage, CommSearchResultPage, etc.). Trigger when users mention community, flexi, page, list, community flexi page list."
metadata:
  version: "1.0"
---

# Managing Community Flexi Page List

## When to Use This Skill

Browse and manage FlexiPage records that drive Experience Cloud (Communities) Builder pages — the records whose Type sits in the FlexiPageType.Container=COMMUNITIES subset (CommObjectPage, CommRecordPage, CommLoginPage, CommThemeLayoutPage, CommSearchResultPage, etc.). The Aloha Setup page at view_url renders this list filtered server-side; for programmatic CRUD use the Tooling sObject FlexiPage (read-flexi-page-list, read-flexi-page, write-flexi-page). Page-content edits are authored in the Lightning App Builder, not by direct sObject PATCH on the record's Metadata field. Org gates: Experience Cloud sites enabled, Experience Cloud pages enabled; user gates: view Experience Cloud pages (read), create Experience Cloud pages (write).

## Critical Constraints

**Preconditions:**

- Networks (Experience Sites / Communities) feature must be enabled on the org. (check: `Experience Cloud sites enabled || Experience Cloud sites enabled`)
- FlexiPage feature must be enabled for Communities on the org. (check: `Experience Cloud pages enabled`)
- Org must NOT be a Help-Center-Networks-only org (the page is hidden in that mode). (check: `!Help Center networks-only mode`)
- User must hold View Setup to load the page; Customize Application (or equivalent) is needed for write/delete row actions and Tooling FlexiPage CRUD. (check: `UserPermissions.ViewSetup; view Experience Cloud pages; create Experience Cloud pages (writes)`)

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `view_CommunityFlexiPageList_1` | read | — | `CommunityFlexiPageList.view` | — |
| `read-flexi-page-list` | read | — | `GET /services/data/v66.0/tooling/query` | — |
| `read-flexi-page` | read | — | `GET /services/data/v66.0/tooling/sobjects/FlexiPage/{id}` | `read-flexi-page-list` |
| `write-flexi-page` | write | — | `POST /services/data/v66.0/tooling/sobjects/FlexiPage` | — |

### Read operations

#### `view_CommunityFlexiPageList_1`

Open the Aloha Setup list view at view_url (PlatformTools > FeatureSettings > Networks). Renders FlexiPage records with FlexiPageType.Container=COMMUNITIES, with row-level Edit (App Builder) and Delete actions. For programmatic record access use steps read-flexi-page-list, read-flexi-page, write-flexi-page.

**Call:** `CommunityFlexiPageList.view`

#### `read-flexi-page-list`

List Community FlexiPage records via Tooling SOQL filtered to FlexiPageType.Container=COMMUNITIES. Sibling FlexiPageList SOR's list_FlexiPage_1 is the unfiltered analog.

**Call:** `GET /services/data/v66.0/tooling/query`

**Output:** QueryResult.records[] of FlexiPage rows: Id, DeveloperName, MasterLabel, Type, NamespacePrefix, LastModifiedDate. The agent should call Tooling.describe(FlexiPage).Type for the authoritative community subset rather than relying on this step's hard-coded WHERE list, since the Container=COMMUNITIES set evolves across releases. Note LastModifiedById is not a valid FlexiPage column on the Tooling entity — resolve the actor via a follow-up SOQL against User if needed.

#### `read-flexi-page`

Read a single FlexiPage record by Id via the Tooling sObject API. Apply this once the agent has an Id from read-flexi-page-list or another source.

**Call:** `GET /services/data/v66.0/tooling/sobjects/FlexiPage/{id}`

**Depends on:** `read-flexi-page-list`

**Output:** Tooling FlexiPage record. GET without ?fields returns the full record: Id, FullName, DeveloperName, MasterLabel, Type, Description, NamespacePrefix, ManageableState, ParentFlexiPage, EntityDefinitionId, LastModifiedDate, LastModifiedById, CreatedDate, SystemModstamp, plus the load-bearing Metadata sub-object. Metadata carries masterLabel, type, sobjectType, description, events[], flexiPageRegions[], parentFlexiPage, platformActionlist, quickActionList, template, and urls. flexiPageRegions[] elements carry name, type (Region), mode, appendable, prependable, replaceable, and itemInstances[] (each with a componentInstance authored via the Lightning App Builder — do not construct these from prose). template.name references an existing platform-bundled template (for example one:utilityBarTemplateDesktop on UtilityBar records, or flexipage:defaultTemplate on Community pages). To project a smaller payload, append ?fields=Id,MasterLabel,Type,...

### Write operations

#### `write-flexi-page`

Create or update a Community-context FlexiPage record via the Tooling sObject API. On POST the wire contract requires a top-level FullName and a Metadata sub-object; Metadata must carry masterLabel, type (a FlexiPageType value in the COMMUNITIES subset — for example CommObjectPage or CommRecordPage), a non-empty flexiPageRegions[] array, and template.name referencing an existing platform-bundled template. sobjectType is set on record-page-type variants (for example CommObjectPage with sobjectType Account). PATCH also requires the Metadata sub-object — sending just top-level scalar field updates without Metadata returns 400 REQUIRED_FIELD_MISSING. The item-instance component graph inside flexiPageRegions[] is authored in the Lightning App Builder after this step provisions the record — do not synthesize componentInstance bodies from prose.

**Call:** `POST /services/data/v66.0/tooling/sobjects/FlexiPage`

**Output:** Tooling sObject create response — { id, success, errors[] } — on POST, and an empty 204 on PATCH. On create, only the shell record is provisioned; the flexiPageRegions[].itemInstances[] component graph is authored later in the Lightning App Builder. Verify the record shape post-write by calling read-flexi-page with the returned Id.

**Rollback:** Delete the created FlexiPage via DELETE /services/data/v66.0/tooling/sobjects/FlexiPage/{id}. Confirmed reachable — DELETE on a non-existent Id returns 404 NOT_FOUND with a well-formed error body, so the surface exists and is idempotent from the caller's perspective. No separate rollback step is emitted because deletion is not a first-class customer workflow for this SOR — it is the undo verb for a mistaken create.

**Notes:** patch_semantics: PATCH requires the full Metadata sub-object. Sending a partial Metadata does not merge with the persisted body — always read the current record first, mutate in-memory, and PATCH the full Metadata to avoid dropping fields.; fullname_immutability: FullName is set once on POST and is the record's stable developer-name identifier. Renaming requires deleting and recreating.; invalid_type_returns_500: An invalid FlexiPage type value (a string outside the FlexiPageType enum) returns 500 UNKNOWN_EXCEPTION rather than a validated 400 — this is a Core defect surface, not a documented contract. Agents constructing type values should pick from the community subset enumerated in agent_description.; empty_region_array_rejected: Metadata.flexiPageRegions must be a non-empty array. An empty [] is rejected with 400 "Required field is missing: flexiPageRegions" even though the key is present.; template_name_must_exist: Metadata.template.name must reference an existing platform-bundled template FullName. Templates are not created via this SOR.
