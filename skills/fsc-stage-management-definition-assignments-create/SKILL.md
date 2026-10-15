---
name: fsc-stage-management-definition-assignments-create
parent: "digital-origination-stage-management-setup"
purpose: "Create and activate a Stage Definition Assignment rule group that binds the reference object (+ optional record type) to the active default stage definition, with optional priority-ordered criteria rules that route records to different definitions."
description: "REQUIRED final step of the Digital Lending stage-management journey. After the stage definition and transitions are active, always create and activate a StgAssignmentRuleGrp that binds the reference object (ApplicationFormProduct) — optionally scoped to a record type — to the active StageDefinition as its default, so record-to-definition resolution runs through the assignment layer rather than an implicit direct binding. Do it directly; do not ask whether it is needed and do not skip it. When the admin supplies a multi-definition routing spec, additionally add the priority-ordered criteria rules that route matching records to a different definition. Authored against the IndustriesStageAssignmentDefinition StageAssignmentSetupController Aura ops and org-verified end-to-end on a live org. Never invents the customer's routing rules; never overwrites a pre-existing group that already points at a different definition."
metadata:
  version: "1.0"
---

# Digital Origination Stage Management — stage definition assignments

Assign **which** stage definition governs a record. A *Stage Definition Assignment* is a rule group
(`StgAssignmentRuleGrp`) that binds a reference object (optionally scoped to a record type) to a
**default** stage definition, plus optional priority-ordered **criteria rules** (`StgAssignmentRule`)
that route records to a *different* definition when their field values match. It is the runtime
dispatcher that sits in front of the `StageDefinition`(s) for the same object.

> **This step is REQUIRED and runs as the final step of the Digital Lending journey.** Create and
> activate the assignment group directly — do not ask whether it is needed and do not skip it. In the
> single-definition case the group binds `ApplicationFormProduct` to the one active `StageDefinition`
> (the case the other six siblings build); this is additive and does not change how that definition
> behaves — activating a group never modifies the underlying `StageDefinition` (org-verified). When the
> admin has supplied a multi-definition routing spec, the same step also adds the criteria rules that
> route matching records to a different definition.

Source: Salesforce Help "Stage Management for Digital Lending" (stage definition assignment sub-articles)
and the corpus SOR `itsm-arka/IndustriesStageAssignmentDefinition` (`StageAssignmentSetupController`).

## What this step does

Run it as the final step, directly, every time the journey completes stage transitions:

1. Bind the reference object (`ApplicationFormProduct`, plus a record type if the admin scoped one) to
   the active `StageDefinition` as the group's **default**, then activate the group.
2. If — and only if — the admin supplied a routing spec for **two or more** definitions competing on the
   same object (+ record type), add the priority-ordered criteria rules from that spec. Absent a routing
   spec, a single default definition is the correct, complete result.

Do not gate this behind a "do you need it?" question. The only inputs you must not invent are the
customer's criteria rules — apply the admin's routing spec if one was given, otherwise stop at the
default-definition binding.

## Feature gate — read-only, no customer enable lever

Stage Definition Assignments are gated by the **`StageMgmtAssignGroup`** org permission, which Salesforce
**auto-backfills** for any org already entitled to `IndustriesStageManagement`. Because Step 1 of this
family turns Stage Management on, the gate is already `true` by the time this step runs — proceed and
create directly. Read the current state only to confirm, and do NOT try to turn it on:

- Call `StageManagementSetupController.fetchInitialStageManagementData` (the base controller) and read
  **`isStageManagementAssignmentsEnabled`**; in the normal flow it is `true`.
- `StageMgmtAssignGroup` is a **provisioned org permission** (owner ITSM Arka, `minApiVersion` 256). It is
  **not** an org preference, **not** a Metadata `Settings` field, and **not** PermissionSet-grantable —
  there is **no supported headless lever** to enable it. In the rare case it reads `false` (an org that is
  not entitled to `IndustriesStageManagement`, which would already have blocked the earlier siblings),
  report it as an **org-provisioning precondition/gap** — do not attempt to enable it and do not fabricate
  a step for it. (Contrast `IndustriesStageMgmtPref`, which the `permissions` sibling *can* flip via the
  OrgPreferences API — this perm is different.)

## Prerequisites this step depends on

- An **active** `StageDefinition` (`1DL…`) for the target reference object, from the `stage-definition` +
  `stage-transitions` siblings. The assignment group's default (and each rule's target) references a real
  definition **by its 18-char Id**, so the definition must exist first.
- The reference object must be in the `supportedEntities` allowlist returned by
  `fetchInitialStageManagementData` (ApplicationFormProduct is supported).
- If scoping to a record type: the `ReferenceObjectRecordTypeId` (a `RecordType` Id) on that object.

## Transport — Aura controller ops over `/headless/invoke` (dispatcher / MCP-dispatchable)

Every operation below is a `StageAssignmentSetupController` Aura action resolved by the dispatcher. The
wire call is `POST /services/data/vXX.0/headless/invoke` with an envelope
{`"className": "...StageAssignmentSetupController", "action": "<op>", "params_schema": [ {name,type}… ],
"body": { <param>: <value>… }`}; the response is `{status_code, body}` (unwrap the inner status). This is
exactly what MCP `dispatch` builds, and it is org-verified over plain REST.

**GOTCHA — `params_schema` is REQUIRED for every parameterized op.** A no-arg read
(`fetchInitialStageManagementData`) resolves with just `{className, action}`, but create / update / delete
MUST include `params_schema` listing every param, or the proxy returns
`{errorCode: "NOT_IMPLEMENTED", message: "Controller not available"}` — which looks like "the op doesn't
exist" but actually means "no method matched the (absent) arg schema". With `params_schema` present, the
values go in `body` keyed by param name.

| Op | action | Key params (all `body`, with `params_schema`) |
|---|---|---|
| Read feature flag + existing defs | `fetchInitialStageManagementData` (base controller) | none |
| List supported entities | `fetchInitialStageManagementData` (assignment controller) | none |
| Create rule group | `createStgAssignmentRuleGrp` | `name`, `devName`, `description`, `referenceObject`, `referenceObjectRecordTypeId`, `defaultStageDefinition` |
| Activate / deactivate / edit group | `updateStgAssignmentRuleGrp` | `recordId`, `name`, `description`, `isActive` (Boolean), `defaultStageDef` |
| Add criteria rules | `createStageAssignmentRuleCriteriaAndConditions` | `stgAssignmentRuleGrpId`, `stgAssignmentRuleRequests` (List) |
| Edit criteria rules | `updateStageAssignmentRuleCriteriaAndConditions` | `stgAssignmentRuleGrpId`, `stgAssignmentRuleRequests` (List) |
| Delete one rule entry | `deleteRuleEntry` | `stgAssignmentRuleGrpId`, `stgAssignmentRuleId` |
| Delete the group | `deleteStgAssignmentRuleGrp` | `recordId` |

**Field-value contract (org-verified — do not repeat these mistakes):**

- **`defaultStageDefinition` (create) / `defaultStageDef` (update) is the StageDefinition *Id* (`1DL…`),
  NOT its DeveloperName.** Passing the developer name returns
  `CONTROLLER_ERROR "Stage Definition ID: id value of incorrect type: <devName>"` and creates nothing.
  Note the param name differs between create (`defaultStageDefinition`) and update (`defaultStageDef`).
- **A group is created INACTIVE** (`IsActive:false`). There is no activate flag on create; activation is a
  separate `updateStgAssignmentRuleGrp {isActive:true}`. This is why create is inert until you explicitly
  activate — and why create+delete is safe on a live org.
- **Activating a group does NOT modify the underlying `StageDefinition`** (org-verified: the live
  definition stayed active with an unchanged count while a group bound to it was activated). Activate only
  after the group (and any intended criteria rules) is fully built.
- **Read/verify via the Tooling API at v64.0+**, never the Data API and never v63.0. `StgAssignmentRuleGrp`
  is a Tooling-family setup entity (`keyPrefix 1S9`, `minApiVersion` 256): a v63.0 SOQL/Tooling query
  returns `sObject type 'StgAssignmentRuleGrp' is not supported` (a **version artifact**, not proof of
  absence), and the plain Data API never supports it. Query at v64.0+:
  `SELECT Id, DeveloperName, MasterLabel, ReferenceObject, ReferenceObjectRecordTypeId, StageDefinitionId, IsActive FROM StgAssignmentRuleGrp`.
  The controller has no "list groups" op, so the Tooling query is the read/idempotency path.

## Workflow

### Step 1 — Preflight: confirm the feature and capture the active definition

Read `isStageManagementAssignmentsEnabled` via the base `fetchInitialStageManagementData`. In the normal
flow it is `true` (Step 1 of this family already turned Stage Management on, and the gate auto-backfills).
Capture the active `StageDefinition` Id(s) (`1DL…`) for the target reference object — that Id is the
group's default. Only in the rare `false` case (an org not entitled to Stage Management) report the
`StageMgmtAssignGroup` provisioning precondition and stop; there is no headless enable path.

### Step 2 — Resolve existing rule groups (idempotency)

Tooling-query (v64.0+) `StgAssignmentRuleGrp` filtered on the target `ReferenceObject` (and
`ReferenceObjectRecordTypeId` if scoped). If a matching group already exists with the intended default
definition, reuse it — do not create a duplicate. If a group already exists but points at a *different*
default definition, do not overwrite it — leave the existing (working) group in place and report the
divergence in the output contract, since silently repointing it could break a routing setup already in
use.

### Step 3 — Create the rule group

When no matching group exists, `createStgAssignmentRuleGrp` with `name`, `devName`, `description`,
`referenceObject` (e.g. `ApplicationFormProduct`), `referenceObjectRecordTypeId` (a RecordType Id or
`null`), and `defaultStageDefinition` = the StageDefinition **Id** (`1DL…`, not the developer name). The
group is created inactive.

### Step 4 — (Data-driven) Add priority-ordered criteria rules

Add criteria rules when — and only when — the admin supplied a multi-definition routing spec (records must
route to a *different* definition based on field values): call
`createStageAssignmentRuleCriteriaAndConditions` with `stgAssignmentRuleGrpId` and a
`stgAssignmentRuleRequests` list — each entry a rule with its target stage definition, priority, and
field/value criteria + conditions (the rule that matches highest priority wins; unmatched records fall
through to the group's default). Never invent the customer's criteria — apply only the admin's routing
spec. Absent a routing spec, the default-definition binding alone is the complete result.

### Step 5 — Activate the group (do this LAST)

Once the group and any criteria rules are built, `updateStgAssignmentRuleGrp {recordId, isActive:true, …}`
(carry `name`/`description`/`defaultStageDef` = the def **Id**). Verify the group reads `IsActive=true`,
and re-confirm the target `StageDefinition`(s) are still active and unchanged.

### Step 6 — Confirm

Tooling-query the group back (v64.0+): `IsActive=true`, correct `ReferenceObject`,
`ReferenceObjectRecordTypeId`, and `StageDefinitionId`; and each criteria rule present with its intended
priority/target. Confirm the underlying `StageDefinition`(s) still read active with unchanged counts.

## Idempotency and rollback

- Reuse an existing group/rule that matches the admin's spec by reference object (+ record type); do not
  duplicate. If a pre-existing group points at a different definition, leave it untouched and report it —
  never silently overwrite a working routing setup.
- Rollback removes only what this run created and only after confirming no active application depends on
  the assignment routing: deactivate first (`updateStgAssignmentRuleGrp {isActive:false}`), then delete
  the group via `deleteStgAssignmentRuleGrp {recordId}` (org-verified; the Tooling
  `DELETE /services/data/v67.0/tooling/sobjects/StgAssignmentRuleGrp/{1S9id}` is an equivalent fallback).
  Individual criteria rules are removed with `deleteRuleEntry {stgAssignmentRuleGrpId, stgAssignmentRuleId}`.

## Output contract

Return the created/reused rule group (Id, developer name, reference object, record type, default
StageDefinition Id, active state), any criteria rules with their priorities and target definitions, and a
fresh Tooling read confirming the group is active and bound — plus confirmation that the underlying
`StageDefinition`(s) remain active and unchanged. If a pre-existing group pointed at a different
definition and was left in place, report that divergence explicitly.

## Definition of done

`isStageManagementAssignmentsEnabled` is `true`; a `StgAssignmentRuleGrp` for the target reference object
(+ record type) exists with the intended default StageDefinition **Id**, reads `IsActive=true` on a fresh
Tooling query (v64.0+), and every referenced `StageDefinition` remains active; and, when the admin
supplied a multi-definition routing spec, its criteria rules are present with their priorities and target
definitions. In the rare case the feature reads `false`, this step stops at the provisioning precondition
and reports it — it does not attempt to enable `StageMgmtAssignGroup`. A partial run (a created-but-inactive
group, or a group missing an admin-specified rule) is never reported as complete.
