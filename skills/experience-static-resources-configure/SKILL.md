---
name: experience-static-resources-configure
description: "Use this skill when users want to tooling sObject CRUD for StaticResource (UDD setup entity; Data API does not expose setup-entity records). Trigger when users mention static, resources, static resources."
metadata:
  version: "1.0"
---

# Managing Static Resources

## When to Use This Skill

Tooling sObject CRUD for StaticResource (UDD setup entity; Data API does not expose setup-entity records). Holds binary or text assets (CSS, JS, images, archive bundles) addressable from Visualforce / LWC / Aura / community sites; CacheControl Public|Private gates cross-org/anonymous fetchability of the served URL. Tooling sObject is the canonical programmatic CRUD surface; Metadata API SOAP type StaticResource is the deploy/retrieve transport, not per-record CRUD. Image-only domain helpers under platform.interaction-builder (createImageStaticResource / getImageStaticResources) narrow content-type and orderBy. Customize Application user permission required to write.

## Critical Constraints

**Preconditions:**

- Caller needs the Customize Application user permission to write StaticResource records (standard gate for setup-entity writes; Tooling sObject CRUD enforces it). (check: `PermissionsCustomizeApplication`)
- API access on Tooling — UDD setup entity, Data API does not expose the StaticResource sObject.

**Destructive operations — require explicit user confirmation:**

- **`delete_StaticResource_1`** — Delete a StaticResource record by Id via the Tooling/sObject API. The {id} path parameter is the record Id.
  - Rollback: No automatic rollback.

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `list_StaticResource_1` | read | — | `query.StaticResource` | — |
| `get_StaticResource_1` | read | — | `sobjects/StaticResource/{id}` | — |
| `create_StaticResource_1` | write | — | `sobjects/StaticResource` | — |
| `update_StaticResource_1` | write | — | `sobjects/StaticResource/{id}` | — |
| `delete_StaticResource_1` | delete | — | `sobjects/StaticResource/{id}` | — |

### Read operations

#### `list_StaticResource_1`

SOQL list via Tooling. {q} is the SOQL string, e.g. SELECT Id, Name, NamespacePrefix, ContentType, BodyLength, CacheControl, Description FROM StaticResource.

**Call:** `query.StaticResource`

#### `get_StaticResource_1`

GET single StaticResource by Id via Tooling sObject. Returns the record envelope plus FullName and Metadata (cacheControl, contentType, description — the deploy-shape mirror).

**Call:** `sobjects/StaticResource/{id}`

### Write operations

#### `create_StaticResource_1`

POST new StaticResource via Tooling sObject — Name, Body (base64 binary/text), ContentType (MIME), CacheControl (Public|Private gates served-URL public fetchability), Description. Image-only alternate platform.interaction-builder.createImageStaticResource defaults cacheControl=PRIVATE and surfaces DuplicateDeveloperNameException.

**Call:** `sobjects/StaticResource`

#### `update_StaticResource_1`

Update a StaticResource record by Id via the Tooling/sObject API. The {id} path parameter is the record Id; body fields replace existing values.

**Call:** `sobjects/StaticResource/{id}`

### Destructive operations

#### `delete_StaticResource_1`

Delete a StaticResource record by Id via the Tooling/sObject API. The {id} path parameter is the record Id.

**Call:** `sobjects/StaticResource/{id}`
