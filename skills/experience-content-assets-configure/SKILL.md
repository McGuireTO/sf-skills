---
name: experience-content-assets-configure
description: "Use this skill when users want to manage ContentAsset records end-to-end via Tooling sObject CRUD + Connect assetize-file. Trigger when users mention content, assets, content assets."
metadata:
  version: "1.0"
---

# Managing Content Assets

## When to Use This Skill

Manage ContentAsset records end-to-end via Tooling sObject CRUD + Connect assetize-file. ContentAssets are file-backed asset records with a stable DeveloperName (Setup UI column "Unique Name") + MasterLabel (UI column "Label"), a Language, and IsVisibleByExternalUsers gate. The Setup page /lightning/setup/ContentAssets/home is a read-only Aloha-era list with no New/Edit/Delete row actions — this skill exceeds UI parity by exposing all six verbs: list (SOQL enumeration), read (get by Id), create-shell (Tooling POST with 4 top-level fields, no file linkage), create-file-backed (Connect postAssetizeFile wrapping an already-uploaded ContentDocument — the canonical create-with-file path today), update (Tooling PATCH on MasterLabel / Language / IsVisibleByExternalUsers), and delete. The ContentDocumentId FK derived from the underlying file is non-editable; the file itself cannot be swapped on an existing asset. Setting IsVisibleByExternalUsers=true additionally requires the org-level external-asset permission.

## Critical Constraints

**Preconditions:**

- Content Assets is enabled at the org level (feature gate).
- Caller has the Content Assets read+create permission (per-action gates separate read/create from edit/delete).
- Setting IsVisibleByExternalUsers requires the org-level external-asset permission in addition to edit access.

**Destructive operations — require explicit user confirmation:**

- **`delete_ContentAsset_1`** — Delete a ContentAsset by Id via the Tooling sObject API. Removes the ContentAsset record; the underlying ContentDocument may persist depending on org retention settings. Use list_ContentAsset_1 (SOQL) or get_ContentAsset_1 to resolve DeveloperName → Id first.
  - Rollback: No automatic rollback.

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `list_ContentAsset_1` | read | — | `query.ContentAsset` | — |
| `get_ContentAsset_1` | read | — | `sobjects/ContentAsset/{id}` | — |
| `create_ContentAsset_1` | write | — | `sobjects/ContentAsset` | — |
| `update_ContentAsset_1` | write | — | `sobjects/ContentAsset/{id}` | `create_ContentAsset_1` |
| `delete_ContentAsset_1` | delete | — | `sobjects/ContentAsset/{id}` | `create_ContentAsset_1` |
| `postAssetizeFile_1` | write | — | `/services/data/v67.0/connect/files/{fileId}/asset` | — |

### Read operations

#### `list_ContentAsset_1`

Enumerate ContentAsset records via SOQL through the Tooling API. Selectable columns include Id, DeveloperName, MasterLabel, Language, IsVisibleByExternalUsers, NamespacePrefix, SystemModstamp. This is the discover/list/filter surface; use get_ContentAsset_1 (by-Id deep-read) once the caller knows the Id to round-trip into an update. The {q} input is the full SOQL string the agent supplies.

**Call:** `query.ContentAsset`

#### `get_ContentAsset_1`

Deep-read one ContentAsset by Id via the Tooling sObject API. Returns the typed record body (DeveloperName, MasterLabel, Language, IsVisibleByExternalUsers, NamespacePrefix, SystemModstamp, and ContentDocumentId — the FK to the underlying file). Pair with list_ContentAsset_1 (SOQL) to enumerate by DeveloperName + look up an Id, then round-trip into update_ContentAsset_1.

**Call:** `sobjects/ContentAsset/{id}`

### Write operations

#### `create_ContentAsset_1`

Create a SHELL ContentAsset record via the Tooling sObject API — a ContentAsset with no file attached. Tooling POST accepts only DeveloperName, MasterLabel, Language, and IsVisibleByExternalUsers; there is no createable column for file linkage on this surface. For a file-backed ContentAsset (the common case), use postAssetizeFile_1 instead — it wraps an already-uploaded ContentDocument, wires sharing + external visibility, and returns the fileAsset in one call. Setting IsVisibleByExternalUsers=true additionally requires the org-level external-asset permission.

**Call:** `sobjects/ContentAsset`

#### `update_ContentAsset_1`

Update an existing ContentAsset by Id via the Tooling sObject API. Body fields replace existing values. Editable columns include MasterLabel, Language, IsVisibleByExternalUsers. DeveloperName is the stable identity key and the ContentDocumentId FK is non-editable — the underlying file cannot be swapped on an existing asset. Toggling IsVisibleByExternalUsers to true requires the org-level external-asset permission.

**Call:** `sobjects/ContentAsset/{id}`

**Depends on:** `create_ContentAsset_1`

#### `postAssetizeFile_1`

Convert an already-uploaded file (ContentDocument, Id prefix 069) into a ContentAsset in one call. Wires the asset's DeveloperName + MasterLabel, sets external visibility, and applies initial sharing. Returns the enriched FileDetailRepresentation with a nested fileAsset block carrying the new asset's Id, name, and masterLabel. Use this instead of create_ContentAsset_1 when the file already exists — this path avoids constructing a Tooling shell record with no file linkage.

**Call:** `/services/data/v67.0/connect/files/{fileId}/asset`

### Destructive operations

#### `delete_ContentAsset_1`

Delete a ContentAsset by Id via the Tooling sObject API. Removes the ContentAsset record; the underlying ContentDocument may persist depending on org retention settings. Use list_ContentAsset_1 (SOQL) or get_ContentAsset_1 to resolve DeveloperName → Id first.

**Call:** `sobjects/ContentAsset/{id}`

**Depends on:** `create_ContentAsset_1`
