---
name: industries-catalog-process-preprocessor-configure
description: "Use this skill when users want to cHILD of the create-unified-catalog-service-process orchestrator — one configuration pass over a service process that ALREADY EXISTS. Trigger when users mention configure, unified, catalog, service, process, preprocessor, automation, connect, api, service-automation-connect-api."
metadata:
  version: "1.0"
  accessCheck: "IndustriesEpc.orgHasUnifiedCatalog"
---

# Managing Configure Unified Catalog Service Process Preprocessor

## When to Use This Skill

CHILD of the create-unified-catalog-service-process orchestrator — one configuration pass over a service process that ALREADY EXISTS. Run standalone against an existing process (supply its catalogItemId), or as the phase that orchestrator routes to; for a NEW end-to-end process start at create-unified-catalog-service-process, which asks the creation fork FIRST.
Use this when an admin wants to set (or remove) the Apex preprocessor on a service process that ALREADY EXISTS — e.g. "add a preprocessor that rejects duplicate laptop requests". DONE when the chosen class reads back as the ONE preProcessors entry on the verify GET with the anchor still intact. Org-gated on Unified Catalog. This references an EXISTING Apex class; it does not author or compile one. SINGLE-VALUED: a process has at most ONE preprocessor. To SET when none exists, send the class as operationType:"Create". To CHANGE the existing one, REPLACE — send the current class as operationType:"Delete" (carrying its junction id) AND the new class as operationType:"Create" in the same bind. To REMOVE, send the current class as operationType:"Delete" carrying its junction id. NEVER send a Create while a preprocessor is already attached without also Deleting it: the API accepts the second Create (200) but the extra junction is INVALID — it never renders in the UI and is not honoured. A Delete WITHOUT its junction id does not error: it silently creates a stray entry instead of removing anything, so the junction id is mandatory on every Delete. DETACH-TRAP handling and the single-valued replace rule are in agent_guidance and step assertions.

## Critical Constraints

**Preconditions:**

- Org must have Unified Catalog enabled.
 (check: `Unified Product Catalog enabled`)
- HARD CONSTRAINT — the service process must ALREADY EXIST and its catalogItemId (== productId) must be known before this workflow runs. The first step (resolve-catalog-item) GETs the item to confirm it exists and is usedFor=ServiceProcess before any write; a 404 there means the id is wrong or the process was never created — the process must be created first, then re-run here with its catalogItemId.
 (check: `process_exists_with_known_catalog_item_id`)
- HARD CONSTRAINT — the preprocessor to set MUST be a real ApexClass Id taken from the list step (list-apex-classes) for THIS org. Never guess or hand-construct a class id. List the eligible classes, let the user pick ONE, and bind that exact id.
 (check: `preprocessor_is_a_real_listed_apex_class`)
- HARD CONSTRAINT — a service process is SINGLE-VALUED for preprocessors: at most ONE. The Connect API UNDER-ENFORCES this — sending a second class as operationType:"Create" while one is already attached is accepted (200) and persists a second junction, but that row is INVALID (never renders in the UI, not honoured). So the bind rule is REPLACE, not add:
  - SET (none attached): send the new class as {preProcessorsID, operationType:"Create"}.
  - CHANGE (one attached): send the existing class as {id:<its 127-prefix junction id>,
    preProcessorsID, operationType:"Delete"} AND the new class as {preProcessorsID,
    operationType:"Create"} in the SAME bind.
  - REMOVE: send the existing class as {id, preProcessorsID, operationType:"Delete"}.
NEVER send a Create while a preprocessor is already attached without also Deleting it. A Delete WITHOUT its junction id does NOT error — it silently ADDS a stray entry instead of removing anything, so the junction id (preProcessors[].id from resolve-catalog-item, a 127-prefix id) is mandatory on every Delete. Confirm the final set (exactly one, the intended class) on the verify GET.
 (check: `bind_replaces_single_preprocessor`)
- HARD CONSTRAINT — patchCatalogItemGet overwrites the item's scalar identity: the bind MUST re-send the item's identity fields (targetObject, name, usedFor, isActive). Omitting targetObject CLEARS the anchor — it reads back absent on the next GET, not reset to a default, even after it was set at create time. The intakeForm block is ALSO a full overwrite: sending it with only {id, operationType:Update} preserves the container but WIPES the bound surface (intakeFormId + type disappear). When the item has an intake surface, the bind MUST re-send intakeForm.intakeFormId AND intakeForm.type alongside the container id, not just the id. The bind PATCH always carries the four identity fields and re-sends the FULL intakeForm (id + intakeFormId + type) when one exists; the verify GET confirms the anchor and intake surface are intact.
 (check: `bind_patch_resends_anchor_identity_fields`)

**Operational rules:**

- MUST-DO CONTRACT (read before executing — each rule is enforced by the named precondition/step; do NOT skip because the detail is further down):
  1. CONFIRM the process exists first — run resolve-catalog-item (GET) and capture its
     identity fields (name, usedFor, isActive, targetObject), its current intakeForm.id,
     and its CURRENT preProcessors[] — each entry is {id, preProcessorsID}; the junction id
     (127-prefix) is required to REMOVE that preprocessor later. A 404 means the
     catalogItemId is wrong; do NOT proceed.
     [precondition: process_exists_with_known_catalog_item_id]
  2. LIST the org's Apex classes via list-apex-classes, present the COMPLETE set as numbered
     text (Name, ApexClass Id), and let the user pick ONE.
     [precondition: preprocessor_is_a_real_listed_apex_class]
  3. BIND via patchCatalogItemGet — SINGLE-VALUED, so REPLACE rather than add. If NONE is
     attached, send the chosen class as operationType:"Create" (its preProcessorsID only). If
     ONE is already attached and you are CHANGING it, send the existing class as
     operationType:"Delete" (carrying its 127-prefix junction id from resolve-catalog-item) AND
     the new class as operationType:"Create" in the SAME bind. To REMOVE, send the existing
     class as operationType:"Delete" carrying its junction id. NEVER send a Create while a
     preprocessor is already attached without also Deleting it — the API accepts it (200) but
     the extra junction is INVALID (never shows in the UI, not honoured). A
     Delete missing the junction id silently ADDS a stray entry rather than removing; carry the
     127-prefix id.
     [precondition: bind_replaces_single_preprocessor]
  4. The bind PATCH is a FULL overwrite of the ITEM's scalar identity — ALWAYS re-send
     targetObject + name + usedFor + isActive. The intakeForm block is ALSO a full overwrite:
     when the item has an intake surface, re-send the FULL block — intakeForm.id AND
     intakeForm.intakeFormId AND intakeForm.type (operationType:Update). Sending only {id}
     preserves the container but WIPES the bound surface. Omit intakeForm only
     when the item has no surface. Otherwise the anchor clears (reads back absent) and/or the intake surface
     detaches. (The identity overwrite and the preProcessors delta are independent: the scalars
     are replaced, the preprocessor list is a delta.)
     [precondition: bind_patch_resends_anchor_identity_fields]
  5. VERIFY: GET the item and confirm preProcessors contains EXACTLY ONE entry — the intended
     class — with no second/stray junction, AND targetObject is unchanged.
     [step: verify-preprocessors]
- ASK MODALITY: for the Apex-class list (unbounded), list the COMPLETE set as numbered text (Name, ApexClass Id) and let the user type ONE selection; PRESENT smartly — match a named target locally, list a small set in full, and narrow a large one (typed name or a recent top slice) rather than dumping every row. The list is a paged SOQL query — page through nextRecordsUrl to completeness before asking. The list is org-specific — take it from this call, never a fixed list.
TIMING: resolve → list → bind → verify. There is one write path. SET, CHANGE, and REMOVE all flow through the preProcessors[] delta on the bind — SET sends one Create, CHANGE sends a Delete (of the existing, carrying its junction id) PLUS a Create (of the new) together, REMOVE sends one Delete carrying the junction id.

## Verification Checklist

After every write operation, confirm the effect by re-reading state:

- After `resolve-catalog-item`, `bind-preprocessors`: call `verify-preprocessors` (`GET /connect/service-automation/catalog/catalog-item/{catalogItemId}`)

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `resolve-catalog-item` | read | implemented | `GET /connect/service-automation/catalog/catalog-item/{catalogItemId}` | — |
| `list-apex-classes` | read | implemented | `queryApexClasses` | `resolve-catalog-item` |
| `bind-preprocessors` | write | implemented | `PATCH /connect/service-automation/catalog/catalog-item/{catalogItemId}` | `resolve-catalog-item`, `list-apex-classes` |
| `verify-preprocessors` | verify | implemented | `GET /connect/service-automation/catalog/catalog-item/{catalogItemId}` | `resolve-catalog-item`, `bind-preprocessors` |

### Read operations

#### `resolve-catalog-item`

CONFIRM + CAPTURE — GET the existing service process to prove it exists and to capture the identity fields the later bind must re-send AND the CURRENT preProcessors[]. Each preProcessors entry is {id, preProcessorsID}: the id (127-prefix junction id) is what a later Delete must carry to remove that preprocessor; the preProcessorsID (an ApexClass 01p id) tells you which classes are already attached. Fails fast (404) if the catalogItemId is wrong or the process was never created. Capture name, usedFor, isActive, targetObject (the anchor), the current intake surface (intakeForm.id AND intakeForm.intakeFormId + intakeForm.type — the bound Flow/OmniScript, NOT just the container id) and the current preProcessors.


**Call:** `GET /connect/service-automation/catalog/catalog-item/{catalogItemId}`   — status: `implemented`

**Inputs:**

- `catalogItemId` *(`String`)* — The catalogItemId (== productId) of the EXISTING service process. If the user does not have it, the process must be created first before this workflow can run.

#### `list-apex-classes`

LIST — the org's Apex classes via SOQL over ApexClass. Present the COMPLETE set as numbered text (Name, ApexClass Id) and let the user pick ONE; page via nextRecordsUrl — never cap or truncate. TARGETED LOOKUP: when the user has already NAMED the class, append AND Name LIKE '%<name>%' to the SOQL WHERE (alongside Status='Active') to fetch just the matches in ONE call instead of paging the whole list; fall back to the full listing only when no name was given or the filter returns nothing. The list is org-specific — take it from this call, never a fixed list. ID TO BIND: bind the ApexClass Id (01p-prefix). preProcessors.preProcessorsID expects that id.


**Call:** `queryApexClasses`   — status: `implemented`

**Inputs:**

- `q` *(`string`)*

**Depends on:** `resolve-catalog-item`

### Write operations

#### `bind-preprocessors`

SET BIND — change the process's single preprocessor via patchCatalogItemGet. SINGLE-VALUED / REPLACE: a process has at most ONE preprocessor. To SET when none is attached, send the chosen class as {preProcessorsID, operationType:"Create"}. To CHANGE the existing one, send the current class as {id:<its 127-prefix junction id from resolve-catalog-item>, preProcessorsID, operationType:"Delete"} AND the new class as {preProcessorsID, operationType:"Create"} in the SAME preProcessors[] array. To REMOVE, send only the current class as {id, preProcessorsID, operationType:"Delete"}. NEVER send a Create while a preprocessor is already attached without also Deleting it — the API accepts the second Create (200) and persists it, but that extra junction is INVALID: it never renders in the UI and is not honoured. A Delete WITHOUT the junction id does NOT error — it silently ADDS a stray entry instead of removing, so carry the id from resolve-catalog-item.existing_preprocessors. DETACH TRAP: this PATCH is a full overwrite of the ITEM's scalar identity — it MUST also re-send the item's identity fields (targetObject, name, usedFor, isActive), sourced from resolve-catalog-item. The intakeForm block is ALSO a full overwrite: when the item has an intake surface, re-send the FULL block — intakeForm.id (container) AND intakeForm.intakeFormId (the bound Flow/OmniScript) AND intakeForm.type, all from resolve-catalog-item, with operationType:"Update". Sending only {id, operationType:Update} preserves the container but WIPES the bound surface (intakeFormId + type vanish). Omit the intakeForm block only if resolve-catalog-item returned no intake_surface_id. Omitting targetObject CLEARS the anchor (it reads back absent on the next GET, not reset to a default). (The scalar identity is replaced; the preProcessors list is a delta — the two behave independently in the same PATCH.)


**Call:** `PATCH /connect/service-automation/catalog/catalog-item/{catalogItemId}`   — status: `implemented`

**Inputs:**

- `catalogItemId` *(`String`)* — The catalogItemId (== productId) of the process to set the preprocessor on.
- `preProcessors` *(`Array`)* — The preProcessors[] delta for a SINGLE-VALUED preprocessor — REPLACE, not add. SET (none attached): [{preProcessorsID, operationType:"Create"}], where preProcessorsID is the chosen id from list-apex-classes.class_ids (01p-prefix ApexClass id, never hand-constructed). CHANGE (one attached): send BOTH in one array — the existing class as {id, preProcessorsID, operationType:"Delete"} (id = its 127-prefix junction id from resolve-catalog-item.existing_preprocessors) AND the new class as {preProcessorsID, operationType:"Create"}. REMOVE: [{id, preProcessorsID, operationType:"Delete"}]. NEVER send a bare Create while a preprocessor is already attached — the API accepts it (200) but the extra junction is INVALID (invisible in the UI, not honoured). A Delete missing the junction id silently adds a stray entry instead of removing.

  - **Source:** output of `list-apex-classes`, `resolve-catalog-item`
- `intakeContainerId` *(`String`)* — The existing intake container id (intakeForm.id) from resolve-catalog-item, carried forward as intakeForm.id (with operationType:"Update"). NOTE the container id alone is NOT enough — the intakeForm block is a full overwrite, so intakeSurfaceId + intakeSurfaceType below must also be re-sent or the bound surface is wiped. Omit the whole intakeForm block only when resolve-catalog-item returned no intake_surface_id.

  - **Source:** output of `resolve-catalog-item`
- `intakeSurfaceId` *(`String`)* — The bound intake surface id (intakeForm.intakeFormId — the Flow/OmniScript definition id) from resolve-catalog-item. MUST be re-sent alongside the container id: sending intakeForm with only {id} wipes the surface. Present only when the item has a surface.

  - **Source:** output of `resolve-catalog-item`
- `intakeSurfaceType` *(`String`)* — The bound intake surface type (intakeForm.type — "Flow" or "OmniScript") from resolve-catalog-item. Re-sent with intakeSurfaceId to preserve the bound surface.

  - **Source:** output of `resolve-catalog-item`
- `targetObject` *(`String`)* — The anchor object (a closed set — Case, Incident, or ServiceRequest) — re-sent on this identity-overwrite PATCH or the anchor CLEARS — it reads back absent on the next GET, not reset to a default (DETACH TRAP). Take the value from resolve-catalog-item, never a fixed assumption.

  - **Source:** output of `resolve-catalog-item`
- `name` *(`String`)* — The process name — re-sent to preserve identity on this identity-overwrite PATCH.
- `usedFor` *(`String`)* — The usedFor value (ServiceProcess) — re-sent to preserve identity.
- `isActive` *(`Boolean`)* — The isActive flag — re-sent to preserve identity.

**Depends on:** `resolve-catalog-item`, `list-apex-classes`

**Rollback:** To undo, re-invoke patchCatalogItemGet with the class added here as operationType:"Delete" carrying its junction id (read it back from the bind response or a fresh GET); if this bind REPLACED a prior preprocessor, also re-Create the prior class to restore it. Always re-send the anchor identity fields AND the full intakeForm block (id + intakeFormId + type when a surface exists) — the rollback PATCH is the same full-overwrite, so anchor-only re-send would wipe the surface. The catalog-item resource has no DELETE method.

### Verify operations

#### `verify-preprocessors`

Read the process back and confirm the intended preprocessor is the sole entry (or none after a REMOVE) and the anchor held.


**Call:** `GET /connect/service-automation/catalog/catalog-item/{catalogItemId}`   — status: `implemented`

**Inputs:**

- `catalogItemId` *(`String`)* — The catalogItemId (== productId) of the process to verify.

**Depends on:** `resolve-catalog-item`, `bind-preprocessors`
