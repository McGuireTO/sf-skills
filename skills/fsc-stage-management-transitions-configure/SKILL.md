---
name: fsc-stage-management-transitions-configure
parent: "digital-origination-stage-management-setup"
purpose: "Build the stage transition map and transition rules that run the Digital Lending Stage Management flow, then activate the transitions."
description: "Set up the stage transitions for Digital Lending: within the stage definition, define the allowed transitions between application form product stages (Intake to Submitted, In Review to Underwriter Approved, and so on), add a transition rule to each with a step definition of Step Type AutoTask whose FlowDefinitionName is the Digital Lending Stage Management flow (RunAsUser is optional and omitted), and activate the transitions. This is the step that makes the stage field enforce the allowed moves and fire the CDS flow after each change. Created via direct StageTransition / StgFulfillmentStepDefGrp / StgFulfillmentStepDef sObject REST, and never invents the customer's transition map."
metadata:
  version: "1.0"
---

# Digital Origination Stage Management — stage transitions

Define the allowed moves between stages and wire each to the CDS Flow. This is the step that makes the
`Stage` field enforce valid transitions and that triggers the `Digital Lending Stage Management` Flow
after each change so CDS re-computes access. This sibling operates inside the stage definition created by
`stage-definition` and depends on the Flow created by `apex-and-flow`.

Source: Salesforce Help "Set Up Stage Transitions for Digital Lending".

## Prerequisites this sibling depends on

- The `StageDefinition` (`1DL…`) from the `stage-definition` sibling, on `ApplicationFormProduct` / `Stage`.
- The active `Digital Lending Stage Management` autolaunched Flow from the `apex-and-flow` sibling — the
  transition rule step definitions bind to it by exact name.
- The three decision matrices active (the Flow's Apex reads them at runtime).

## Inputs

- Target-org alias and acting admin.
- The transition map — which stage may move to which. The article's personal-loan example:

  | From stage | Allowed transitions to |
  |---|---|
  | Intake | Submitted, Auto Rejected |
  | Submitted | In Review, Need More Info, Auto Approved, Auto Rejected |
  | In Review | Need More Info, UW Approved, UW Rejected |
  | UW Approved | Customer Approved, Customer Rejected |
  | Auto Approve | Customer Approved, Customer Rejected, Contract Generation |
  | Customer Approved | Contract Generation |
  | Contract Generation | Signature Complete |

  Use the admin's transition map — the example is illustrative, not a default. The **one exception is the
  entry transition `Intake → Submitted`**: because `Intake` is the entry stage every application starts in
  (see `stage-definition`) and activation requires at least one transition, always define
  `Intake → Submitted` as the baseline first transition, then layer the admin's remaining moves on top of
  it. Do not activate the stage definition until this entry transition exists.

## Reusable operations — proven headless sObject path

**The transitions and rules are created directly via sObject REST POST — no builder UI, dispatcher
envelope, or Connect API is needed.** (org-verified on fsc-dop8, v63.0). All four Stage Management
records accept plain `POST /services/data/vXX.0/sobjects/<Entity>`:

- **`StageTransition`** — `StageDefinitionId` (REQ), `FromStageValueId` (REQ), `ToStageValueId` (REQ),
  `Description`. The `From`/`To` ids are `StageValue` ids (`1DE…`) created by the `stage-definition`
  sibling. A transition is what blocks invalid moves — an undefined move (e.g. Submitted → Intake) is
  simply prevented.
- **`StgFulfillmentStepDefGrp`** — one group per transition: `StageDefinitionId` (REQ),
  `ContextReferenceId` (REQ, = the `StageTransition` id — this is what binds the rule to the transition),
  `StgFulfillmentStepDefGrpName`.
- **`StgFulfillmentStepDef`** — the rule that runs the Flow: `StgFulfillmentStepDefGrpId` (REQ),
  `StgFulfillmentStepDefName` (REQ), `StgFulfillmentStepDefApiName` (REQ), `StepType`,
  `FlowDefinitionName`.

**Field-value contract (three org-verified findings — do not repeat the earlier mistakes):**

- **`StepType = "AutoTask"`** — NOT "AutoLaunched Flow". "AutoLaunched Flow" is the *UI label*; the
  sObject picklist value for a Flow-backed step is `AutoTask` (full picklist:
  AutoTask/Callout/ManualTask/Milestone/Pause/StagedAssetize).
- **`FlowDefinitionName` is the Flow's *API name*** — `Digital_Lending_Stage_Management` (underscored),
  not the display name `Digital Lending Stage Management`.
- **`RunAsUser` is OPTIONAL — omit it.** Every string value ("Admin", "AdminUser", "RunAsAdmin",
  "Admin User") returns `400 INVALID_INPUT "Specify a valid value for Run As User"`. Omitting the field
  creates the record cleanly. The UI's "Run As User = Admin User" is a UI-only convenience, not required
  for the sObject write.
- There is **no `SequenceNumber` column** on `StgFulfillmentStepDef` ("No such column").

The Stage Management Builder
(`builder_industries_stagemgmt/stageManagementBuilder.app?stateDefId=<1DL id>`, wizard SOR
`builders/fsc-rolex/ui-industries-stage-mgmt-components`) remains available as a **UI fallback** if a
future org rejects the direct sObject writes, but the direct path above is proven and preferred.

## Workflow

### Step 1 — Create transitions

For each allowed move in the admin's transition map, POST a `StageTransition` with the source/target
`StageValue` ids (`FromStageValueId`/`ToStageValueId`), the `StageDefinitionId`, and a `Description`.
Only create the moves in the map — an undefined move is what blocks an invalid transition.

### Step 2 — Add transition rules (group + step per transition)

For each transition that should recompute CDS access, create the two-record rule:

1. POST a **`StgFulfillmentStepDefGrp`** with `ContextReferenceId` = the `StageTransition` id, the
   `StageDefinitionId`, and a group name.
2. POST a **`StgFulfillmentStepDef`** into that group: `StgFulfillmentStepDefGrpId` = the group id,
   `StepType = "AutoTask"`, `FlowDefinitionName = "Digital_Lending_Stage_Management"` (the Flow's API
   name from `apex-and-flow`), plus `StgFulfillmentStepDefName` + `StgFulfillmentStepDefApiName`.
   **Do not set `RunAsUser`** (it 400s on every value).

### Step 3 — Activate the stage definition (do this LAST, after ≥1 transition exists)

Now that at least one transition exists, activate the `StageDefinition`. **This is the ONLY point
activation succeeds (org-verified):** `IsActive=true` set at create time is rejected, and set before any
`StageTransition` exists it throws `FIELD_INTEGRITY_EXCEPTION`. Activate via the
`IndustriesStageDefinitions` setup op that toggles publish state (the Aura/SOAP path pins
`UsageType=STAGE_MANAGEMENT`); a raw `PATCH /sobjects/StageDefinition/<1DL id> {"IsActive": true}` also
works once ≥1 transition is present. This is why `stage-definition` deliberately leaves the definition
inactive and hands activation to this sibling.

### Step 4 — Confirm active

Re-read the definition and count: every intended transition has a group (matched by
`ContextReferenceId`) and a step bound to `Digital_Lending_Stage_Management`. Confirm the stage
definition/version reads `IsActive=true` on a fresh query.

## Idempotency and rollback

- Reuse existing transitions and rules that match the admin's map; do not duplicate a transition or a rule.
- On a mismatch (an extra or missing transition, or a rule pointing at a different Flow), present the diff
  and stop.
- Rollback removes only transitions/rules created by this run and only after confirming no active
  application depends on the transition path.

## Output contract

Return the created transitions (source → targets with their `StageTransition` ids), each transition's
`StgFulfillmentStepDefGrp` id, and each `StgFulfillmentStepDef` with its name, `StepType` (`AutoTask`),
and bound `FlowDefinitionName` (`Digital_Lending_Stage_Management`), plus a fresh read confirming the
stage definition/version is active and the group/step counts match the transition count.

## Definition of done

The transition map matches the admin's specification, every intended transition has a
`StgFulfillmentStepDefGrp` (bound by `ContextReferenceId`) and a `StgFulfillmentStepDef` whose
`StepType=AutoTask` step runs the `Digital_Lending_Stage_Management` Flow, and the transitions read back
on a fresh query with matching counts. Invalid moves are provably blocked (not defined). If the direct
sObject path is rejected and the builder-UI fallback is left incomplete, this sibling is partial; a
partial run is never reported as complete.
