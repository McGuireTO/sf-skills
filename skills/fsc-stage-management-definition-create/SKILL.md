---
name: fsc-stage-management-definition-create
parent: "digital-origination-stage-management-setup"
purpose: "Create and activate the Digital Lending stage definition on the Application Form Product Stage field."
description: "Create the stage definition that Stage Management for Digital Lending governs: a StageDefinition record (key prefix 1DL) named Digital Lending Stage Management, with Reference Object set to Application Form Product and Reference Object Field set to Stage. This is the definition the Stage Management Builder loads via its stateDefId parameter and that the stage transitions attach to. Reuses the corpus IndustriesStageDefinitions setup operations and the stage-management builder wizard SOR. Resolves an existing definition by exact name before creating one and confirms it with a fresh read."
metadata:
  version: "1.0"
---

# Digital Origination Stage Management — stage definition

Create the stage definition that restricts the `Stage` field on `ApplicationFormProduct`. This is the
`StageDefinition` record (key prefix `1DL`) the Stage Management Builder opens via its `stateDefId`
parameter (e.g. `builder_industries_stagemgmt/stageManagementBuilder.app?stateDefId=1DL...`). This sibling
owns creating the definition shell **and its stage values (inactive)**; the `stage-transitions` sibling
adds the transitions and rules and performs the **final activation** (activation only succeeds after
≥1 transition exists — see that sibling).

Source: Salesforce Help "Create a Stage Definition for Digital Lending".

## Inputs

- Target-org alias and acting admin.
- Definition Name (the article uses `Digital Lending Stage Management`).
- Reference Object = `ApplicationFormProduct`.
- Reference Object Field = `Stage`.

The `Stage` field must already carry the admin's picklist values (Intake, Submitted, In Review, the
Approved/Rejected stages, Contract Generation, etc.) before transitions can reference them. Confirm the
picklist is non-empty first.

**`Intake` is the entry stage — always create it.** Every `ApplicationFormProduct` starts life at
`Intake` (it is the seeded starting `Stage` on the sample record, and the first stage in the default
flow), so an `Intake` `StageValue` MUST exist regardless of how the admin customizes the later stages.
Create it first (the lowest-sequence `StageValue`); the `stage-transitions` sibling then defines the
move out of it (`Intake → Submitted`) as the entry transition.

## Naming note: StageDefinition vs StateDefinition

The public/API entity is **`StageDefinition`** (key prefix `1DL`), but the builder app and its LWCs refer
to it internally as **`StateDefinition`** — the URL parameter is `stateDefId` and the internal field is
`definitionId`. They are the same record. Address it as a `StageDefinition` in queries; expect
`stateDefId` in builder deep-links.

## Reusable operations

Use the **Industries Stage Definitions** setup SOR (find it with `discover`, then `describe` it),
backed by the Stage Management setup controller via the Headless360 dispatcher:

- `check-pick-list-non-empty` — confirm the `Stage` field on `ApplicationFormProduct` has picklist values
  before creating the definition.
- `fetch-all-stage-definition-versions` / `fetch-initial-stage-management-data` — resolve an existing
  definition by name (reuse rather than duplicate).
- `create-stage-mgmt-def-and-fetch-records` — create the stage definition (Name, Reference Object,
  Reference Object Field) and read back the created record.
- `update-stage-definition` / `update-stage-mgmt-def` — adjust the definition if it exists but differs.
- `fetch-stage-values` — read the stage values the definition exposes.

The builder wizard SOR `builders/fsc-rolex/ui-industries-stage-mgmt-components`
(`wizard-ui-industries-stage-mgmt-components`) provides the builder-canvas operations
(`util-create-stage-def-options`, `util-stage-def-modal`, `util-template-stage-def-modal`,
`util-stage-mapping-body`) if the definition is created through the builder UI flow rather than the
setup controller directly.

## Workflow

1. Confirm the `Stage` picklist on `ApplicationFormProduct` is non-empty (`check-pick-list-non-empty`).
   If empty, stop and report a blocker — transitions need the stage values.
2. Resolve an existing `Digital Lending Stage Management` definition by name. If found with the right
   reference object and field, reuse it; on a mismatch, present the diff and stop.
3. Create the definition with **Name (MasterLabel)** `Digital Lending Stage Management` and
   **`DeveloperName` `Digital_Lending_Stage_Management` (REQUIRED — the create rejects a missing
   developer name)**, Reference Object `ApplicationFormProduct`, Reference Object Field `Stage`
   (`create-stage-mgmt-def-and-fetch-records`). That setup op pins `UsageType = STAGE_MANAGEMENT` for
   you. The `StageDefinition` also accepts a direct sObject REST POST (org-verified) if the controller
   op is unavailable — key prefix `1DL`; on the raw POST you MUST supply `DeveloperName` and set
   `UsageType = 'STAGE_MANAGEMENT'` yourself. **Do NOT set `IsActive` at create — activation is the
   last step and is owned by `stage-transitions` (it only succeeds after ≥1 transition exists).**
4. **Create the `StageValue` records** — one per stage the admin defined — via direct sObject REST POST
   to `StageValue`: `StageDefinitionId` (REQ, the `1DL…` id) + `Value` (the stage string, matching the
   `ApplicationFormProduct.Stage` picklist). These `StageValue` ids (`1DE…`) are what the
   `stage-transitions` sibling references as `FromStageValueId`/`ToStageValueId`, so they must exist
   before transitions. (org-verified: 12 StageValues created this way on fsc-dop8.)
5. Re-read the created `StageDefinition` and its `StageValue`s and confirm the Id (`1DL…`), reference
   object, field, active status, and stage-value count.
6. Hand the `StageDefinition` Id **and the `StageValue` id-per-stage map** to the `stage-transitions`
   sibling.

## Idempotency and rollback

- Reuse an exact-match definition (same name, reference object, field); do not create a duplicate.
- On a shape mismatch, present current vs requested and stop.
- Do not delete a definition that already carries transitions or that an active application depends on
  without explicit approval.

## Output contract

Return the `StageDefinition` Id (`1DL…`), Name, Reference Object, Reference Object Field, active status,
and the created `StageValue` id-per-stage map (`1DE…` per stage string). The `StageDefinition` Id is the
`stateDefId` for the builder deep-link; the `StageValue` map is the handoff to `stage-transitions`
(source/target ids for each transition).

## Definition of done

The `Digital Lending Stage Management` stage definition exists exactly once as a `StageDefinition` on
`ApplicationFormProduct` / `Stage`, reads back with the correct reference object and field on a fresh
query, and a `StageValue` record exists for each of the admin's stages (fresh-read count matches). A
manual builder checkpoint left incomplete means this sibling is partial.
