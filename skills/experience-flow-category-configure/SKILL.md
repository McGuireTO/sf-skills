---
name: experience-flow-category-configure
description: "Use this skill when users want to manage Flow Categories — Metadata API type (since v42) that bundles flows under a developer-name-keyed grouping for Setup-page browsing in Lightning Bolt experiences. Trigger when users mention flow, category, flow category."
metadata:
  version: "1.0"
---

# Managing Flow Category

## When to Use This Skill

Manage Flow Categories — Metadata API type (since v42) that bundles flows under a developer-name-keyed grouping for Setup-page browsing in Lightning Bolt experiences. Each FlowCategory carries DeveloperName, MasterLabel, optional Description, and a flowCategoryItems[] list whose entries each name a flow developer name. Persistence is reachable via /headless/metadata deploy/delete/retrieve on the FlowCategory type; the underlying operation is THIN over Tooling sObject FlowCategory CRUD. Use this SOR to read a category, list its flows, create/update/delete a category, and validate developer-name uniqueness before save.

## Workflow

Validate uniqueness (is-developer-name-unique) before create; then save-flow-category (Metadata deploy upserts by FullName=DeveloperName; isUpdate=true requires the record Id in the flowCategory map). verify-save-flow-category retrieves the FullName to confirm. delete-flow-category is independent. get-flows reads flowCategoryItems[].flow from the same retrieve.

## Critical Constraints

**Destructive operations — require explicit user confirmation:**

- **`delete-flow-category`** — Delete a FlowCategory by FullName via /headless/metadata destructiveChanges deploy on the FlowCategory type. Returns no data on success (treat 200/204 as success). Removes the category record and its flowCategoryItems children atomically.
  - Rollback: No automatic rollback.

## Verification Checklist

After every write operation, confirm the effect by re-reading state:

- After `delete-flow-category`: call `verify-delete-flow-category` (`/headless/metadata`)

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `save-flow-category` | write | proposed | `/headless/metadata` | — |
| `delete-flow-category` | delete | proposed | `DELETE /headless/invoke/platform/flow-category/delete-flow-category` | — |
| `verify-delete-flow-category` | verify | — | `/headless/metadata` | `delete-flow-category` |
| `get-flows` | read | implemented | `/headless/metadata` | — |
| `verify-save-flow-category` | read | proposed | `/headless/metadata` | `save-flow-category` |
| `is-developer-name-unique` | read | implemented | `GET /headless/invoke/platform/flow-category/is-developer-name-unique` | — |

### Read operations

#### `get-flows`

Retrieve FlowCategory by FullName via /headless/metadata; read flowCategoryItems[].flow — each entry names a flow developer name in the category. Aura's UI reformat is presentational; Metadata payload carries the data.

**Call:** `/headless/metadata`   — status: `implemented`

**Inputs:**

- `flowCategoryId` *(`String`)*

#### `verify-save-flow-category`

Retrieve the FlowCategory by FullName via /headless/metadata after save. A non-empty members result with the saved DeveloperName, MasterLabel, Description, and flowCategoryItems echoes the deploy and confirms it took effect.

**Call:** `/headless/metadata`   — status: `proposed`

**Inputs:**

- `id` *(`String`)*

**Depends on:** `save-flow-category`

#### `is-developer-name-unique`

Returns true when no FlowCategory has the supplied developerName. Call before save-flow-category on create to validate a candidate DeveloperName. Disposition: AURA-IS-CANONICAL (Tooling-coverage evidence not vendored; see /notes/coverage_gap).

**Call:** `GET /headless/invoke/platform/flow-category/is-developer-name-unique`   — status: `implemented`

**Inputs:**

- `developerName` *(`String`)*

### Write operations

#### `save-flow-category`

Deploy FlowCategory via /headless/metadata. Body XML: DeveloperName, MasterLabel, optional Description, flowCategoryItems[].flow. Same op handles create + update — FullName=DeveloperName keys upsert; isUpdate=true requires record Id.

**Call:** `/headless/metadata`   — status: `proposed`

**Inputs:**

- `flowCategory` *(`Map<String, Object>`)* — Value for flow category.
- `isUpdate` *(`boolean`)* — Whether update is enabled.

### Verify operations

#### `verify-delete-flow-category`

Retrieve the FlowCategory by FullName via /headless/metadata after delete. An empty members result confirms the destructiveChanges deploy landed; a non-empty result means the delete did not take effect.

**Call:** `/headless/metadata`

**Inputs:**

- `id` *(`String`)*

**Depends on:** `delete-flow-category`

### Destructive operations

#### `delete-flow-category`

Delete a FlowCategory by FullName via /headless/metadata destructiveChanges deploy on the FlowCategory type. Returns no data on success (treat 200/204 as success). Removes the category record and its flowCategoryItems children atomically.

**Call:** `DELETE /headless/invoke/platform/flow-category/delete-flow-category`   — status: `proposed`

**Inputs:**

- `id` *(`String`)*
