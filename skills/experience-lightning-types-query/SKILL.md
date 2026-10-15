---
name: experience-lightning-types-query
description: "Use this skill when users want to use this skill when an admin or developer wants to discover what Lightning Types exist in their org (Standard out-of-the-box types, Custom types created via Metadata API, or Managed types from installed packages), or to retrieve the detailed schema + editor/renderer configuration. Trigger when users mention lightning, types, lightning types."
metadata:
  version: "1.0"
  accessCheck: "OrgPermissions.LightningTypeBundle"
---

# Querying Lightning Types

## When to Use This Skill

Use this skill when an admin or developer wants to discover what Lightning Types exist in their org (Standard out-of-the-box types, Custom types created via Metadata API, or Managed types from installed packages), or to retrieve the detailed schema + editor/renderer configuration of a specific type by its fully qualified name (FQN). Typical flow: list types (filter by category, source, or config target as needed) → pick a type from the response → fetch its detail by FQN. Both operations are read-only — there are no Connect API endpoints for creating, updating, or deleting Lightning Types in this family (Custom Type authoring still flows through the Metadata API, which is out of scope for this skill).

## Workflow

list-lightning-types → (optional) filter further → get-lightning-type-detail.
Discovery first: list-lightning-types returns paginated summaries (namespacePrefix, developerName, title, description, source, detailUrl). Use pageSize 1-250 (default 25, max 250) to control batch size and page (0-based) to advance. If you need only Custom or Managed types, set excludeStandardTypes=true — Standard types are the OOTB type catalog and are usually the bulk of results. Filter to types intended for a specific surface via editorConfigTarget / rendererConfigTarget (e.g., LightningCommunity, ExperienceBuilder, PromptBuilder). Filter by underlying category with category=Apex or category=Object when the caller cares about type backing.
Detail lookup: get-lightning-type-detail takes the FQN (namespacePrefix__developerName, e.g. lightning__booleanType, setup_discovery__considerationType, c__myCustomType) and returns the full schema + editor/renderer configurations for the requested target. By default configs come back expanded (computed propertyRenderers + layout, with OOTB config generation); pass expandConfigs=false to inspect what is actually configured (useful when debugging CLT Setup UI overrides). Pass includeSubSchemaDefinitions=true to inline referenced subschemas under $defs so the response is self-contained.
No write APIs in this family. Custom Type creation/update/deletion goes through the Metadata API (CustomLightningType metadata type) — not covered here.
Common gotchas: the API returns 403 FUNCTIONALITY_NOT_ENABLED if the org does not have OrgPermissions.LightningTypeBundle (default-enabled but can be disabled in some orgs). pageSize outside [1, 250] returns 400 INVALID_PAGING_OPTION. An unknown editorConfigTarget / rendererConfigTarget enum value returns 400 ILLEGAL_QUERY_PARAMETER_VALUE — the precise accepted set is enumerated in the inputs below and is broader in v66 than in the DRB. An FQN that does not exist returns 404 NOT_FOUND.

## Critical Constraints

**Preconditions:**

- Org must have the LightningTypeBundle permission enabled (default-enabled) (check: `OrgPermissions.LightningTypeBundle`)
- API must be available at v66.0 or later (Connect API was introduced in 254/v63 and has evolved through v66; SOR is authored against v66 wire shape) (check: `ApiVersion >= 63.0`)

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `list-lightning-types` | read | implemented | `getLightningTypeCollection` | — |
| `get-lightning-type-detail` | read | implemented | `getLightningType` | `list-lightning-types` |

### Read operations

#### `list-lightning-types`

Fetch a paginated list of Lightning Types in the org. Returns a LightningTypeCollectionRepresentation with `count`, `lightningTypes[]` (summary entries), and `currentPageUrl` / `nextPageUrl` / `previousPageUrl` for navigation. Each summary entry contains namespacePrefix, developerName, title, description, source (Standard / Custom / Managed), and detailUrl for drilling into the full type. Custom types additionally carry id, createdDate, createdBy, updatedDate, updatedBy.


**Call:** `getLightningTypeCollection`   — status: `implemented`

**Inputs:**

- `category` *(`String`)* — Filter by underlying schema category. Valid values: 'Apex' (for @apexClassType-backed types), 'Object' (for lightning__objectType-backed types). Omit to include all categories. NOTE: enum is title-case in v66 ('Apex' / 'Object'), not the lowercase form shown in the DRB summary.

- `editorConfigTarget` *(`String`)* — Return only types that have an editor configuration for the given target. Accepted values are broader in v66 than in the DRB (the DRB lists 6; v66 has 12).

- `rendererConfigTarget` *(`String`)* — Return only types that have a renderer configuration for the given target. Accepted values are broader in v66 than in the DRB (the DRB lists 7; v66 has 16).

- `excludeStandardTypes` *(`Boolean`)* — When true, omit Standard (OOTB) types from the response — useful to retrieve only Custom and Managed types. NOT documented in the DRB but live in v66.

- `fullyQualifiedNames` *(`List<String>`)* — Comma-separated list of FQNs (namespacePrefix__developerName) to fetch a specific subset. Each FQN element follows the pattern `<namespacePrefix>__<developerName>`, e.g. `lightning__booleanType,c__myCustomType`.

- `language` *(`String`)* — Locale code (e.g. `fr`, `en_AU`, `en_US`) controlling the language of the returned title and description. If omitted, the logged-in user's language is used; ENGLISH is the fallback when translations don't exist.

- `page` *(`Integer`)* — 0-based page index. Default 0 returns the first page.
- `pageSize` *(`Integer`)* — Items per page. Valid range is 1-250 inclusive (default 25). Values outside this range return 400 INVALID_PAGING_OPTION.

#### `get-lightning-type-detail`

Fetch the full / detailed information about a single Lightning Type by its fully qualified name. Returns a LightningTypeDetailRepresentation containing the JSON Schema definition (`schema`), the editor configuration (`editorConfig`) and renderer configuration (`rendererConfig`) for the requested target, and source metadata (createdBy, updatedBy, etc., for Custom types).


**Call:** `getLightningType`   — status: `implemented`

**Inputs:**

- `fullyQualifiedName` *(`String`)* — The fully qualified name in `namespacePrefix__developerName` form, e.g. `lightning__booleanType` (Standard), `setup_discovery__considerationType` (Standard), `c__myCustomType` (Custom in default namespace). Typically threaded from a list-lightning-types response — pick a `lightningTypes[i].namespacePrefix` + `developerName` and join with `__`. An unknown FQN returns 404 NOT_FOUND.

- `editorConfigTarget` *(`String`)* — Editor configuration target. If unspecified, the Default editor configuration is returned. Accepted values match the LightningModelTypesEditorConfigEnum (12 values; see list-lightning-types step inputs for the full set).

- `rendererConfigTarget` *(`String`)* — Renderer configuration target. If unspecified, the Default renderer configuration is returned. Accepted values match the LightningModelTypesRendererConfigEnum (16 values).

- `includeSubSchemaDefinitions` *(`Boolean`)* — When true, the response inlines all referenced external sub-schema definitions under a `$defs` block in the schema, replacing `sfdc_cms:type`-style refs with `$ref: #/$defs/...` internal refs. Use when you want a self-contained schema for offline analysis. Default false keeps the response compact.

- `expandConfigs` *(`Boolean`)* — Default true returns "expanded" editor / renderer configs (OOTB config generation, computed propertyRenderers, computed layout including override expansion). Set false to return configs as stored — primary use case is letting users inspect what's actually configured in the CLT Setup UI. (Since v258 in the DRB; live on v66.)

- `applyDefaults` *(`Boolean`)* — Boolean toggle present in v66 (not in the DRB). Spec description is sparse — agent should treat as advanced/experimental. Likely controls whether default values from the schema are applied to the response. Omit unless an explicit need exists.

- `language` *(`String`)* — Locale code controlling the language of returned labels (title / description / property labels). Falls back to the user's language, then ENGLISH.


**Depends on:** `list-lightning-types`

**Output:** $.description

## Notes

- **related_apis:** GET /connect/lightning-types/references/{id} — returns references to a Lightning Type by 18-char Id (different controller — shared.lightning.model); not authored here, but see operation_id shared.lightning.model.connect.api.getLightningTypeReferences for callers needing reference inspection., GET /connect/lightning-model/candidate-types — vocabulary-driven type candidate lookup; complementary discovery API on a different controller., POST /connect/lightning-model/type-bundles — write API for upserting Lightning Type bundles; lives on shared-lightning-model-connect-api, different controller, not part of this skill's read-only family.
- **out_of_scope:** Custom Type creation, update, and deletion (still flows through the Metadata API CustomLightningType metadata type)., Lightning Object Types and Lightning Type bundles (handled by shared-lightning-model-connect-api, not this family).
