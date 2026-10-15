---
name: fsc-stage-management-permissions-assign
parent: "digital-origination-stage-management-setup"
purpose: "Assign the Stage Management and Digital Lending permission sets, turn on the Stage Management feature, and confirm Context Service is enabled."
description: "Assign and verify the permission-set access required to configure and run Stage Management for Digital Lending, turn on the Stage Management feature, and confirm Context Service is enabled so the stage decision matrices can be evaluated. Handles the Digital Lending, Stage Management Design User, and Stage Management User access documented by the help articles. Reuses the approved PermSets SOR and standard assignment APIs, is idempotent on rerun, and never assigns access to inferred users or service accounts."
metadata:
  version: "1.0"
---

# Digital Origination Stage Management permissions

Prepare a specifically identified admin or runtime user for Stage Management, turn the feature on, and
confirm Context Service is enabled so the stage decision matrices evaluate. This sibling manages access
and two org-level enablements; it does not create matrices, records, CDS objects, or stage definitions.

## Inputs

- Explicit target-org alias
- Explicit target user ID or username
- Role: design-time admin (configure Stage Management), runtime user (progress records), or both

Never select all active users. Never target Automated Process, integration, guest, or service users.

## Required access matrix

The help articles state the same permission surface. Resolve exact API names from the target org; labels
can differ by release.

| Role | Required product-supplied access |
|---|---|
| Set up Digital Lending | Digital Lending permission set |
| Configure Stage Management (design time) | Stage Management Design User |
| Run Stage Management for end users (runtime) | Stage Management User |

Do not manufacture a custom replacement for a missing product-supplied set. Report a missing entitlement
or package artifact as a blocker.

## Reusable operations

Use the **Permission Sets** entity SOR (find it with `discover`, then `describe` it for these operations):

- `get-permission-set-details` — Tooling read of a permission set and its `Permissions*` fields.
- `assign-users` — create `PermissionSetAssignment` using AssigneeId and PermissionSetId.
- `unassign-users` — rollback an assignment created by this run.
- `edit-assignment-expiration` — update an explicitly requested expiration.

For any permission-set-license required by the selected sets, query and create
`PermissionSetLicenseAssign` through standard sObject REST. Assign a missing license before its
permission set.

## Turn on Stage Management (headless — proven)

The Stage Management feature is the org preference **`IndustriesStageMgmtPref`**, and it is set through
the **generic Setup-Connect Org Preferences API** — there is no per-feature controller and no UI-only
step. (The `IndustriesStageDefinitions` SOR's "no public setter" note is wrong; the toggle IS this
generic OrgPreference, the same mechanism ITSM/CLM/Inventory settings use.)

```text
GET   /services/data/vXX.0/setup/org/preferences/IndustriesStageMgmtPref     -> {"isPreferenceEnabled": <bool>}
PATCH /services/data/vXX.0/setup/org/preferences/IndustriesStageMgmtPref     body {"desiredState": true}   -> {"isPreferenceEnabled": true}
```

Enabling `IndustriesStageMgmtPref` provisions the eight Stage Management entities (`StageDefinition`,
`StageValue`, `StageTransition`, `StageCriteria`, `StageCondition`, `StgFulfillmentStepDefGrp`,
`StgFulfillmentStepDef`, `StgFulfillmentStepDpndDef`) into the org's data dictionary. Before it is on,
those sObjects do not exist (`describe` 404s, absent from `EntityDefinition`) and `hasAccess` is false.

**Steps:**

1. GET the preference. If already `true`, skip (idempotent).
2. PATCH `{"desiredState": true}` and confirm the response echoes `isPreferenceEnabled: true`.
3. **Verify the feature actually provisioned** — do NOT trust the pref read-back alone. Call
   `fetchInitialStageManagementData` (POST the dispatcher envelope, see below) and confirm
   `hasAccess: true` and `ApplicationFormProduct` appears in `supportedEntities`. Optionally
   `GET /sobjects/StageDefinition/describe` and confirm it returns `createable: true` instead of 404.

Note on the dispatcher envelope for the Aura-backed reads/writes (`fetchInitialStageManagementData`,
`create-stage-mgmt-def-and-fetch-records`, etc.): POST to the `/headless/invoke/...` path with body
`{"className":"<className>","action":"<methodName>","params":{...}}`. The **fully-qualified** class name
is required — a short name returns 501 "Controller not available". Do not hardcode it: take the exact
`className` from the operation's route metadata (the resolved dispatch route for the op you are calling
already carries it), so the envelope always matches the deployed controller.

Enabling a feature is an org-wide change — report it and enable only after confirming the target org is
the intended one. There is a companion pref `RulesReEvalForInactiveSD` (rules re-evaluation for inactive
stage definitions) settable the same way if the admin wants it; leave it default unless asked.

## Context Service enablement

The stage decision matrices are Business Rules Engine decision matrices, which evaluate behind the
Context Service feature family (`ContextResourceFamily`). When the gate is off, matrix evaluation returns
HTTP 403 `FUNCTIONALITY_NOT_ENABLED`.

Enable it headlessly via the Context Service Connect API — the `preferenceName` must be exactly
`contextServiceEnabled`, and `uniqueIdentifier` is the 18-char Org Id:

```text
PUT /connect/contextservice/access/contextServiceEnabled/{orgId}  {"isEnabled":true}
```

If the family-level gate itself is not yet on, the PUT cannot reach the resource; stop at the Setup
checkpoint **Context Service Settings → enable Context Definitions**
(`/lightning/setup/ContextServiceSettings/home`) and resume after the admin confirms. Verify by calling
the cheapest live endpoint (a decision-matrix read or a `GET /connect/context-definitions`) rather than
trusting the preference read-back, which can lag.

## Workflow

1. Confirm org and target user. Query `User` and report username, profile, active state, and user type.
2. Query `PermissionSet` by both `Name` and `Label` for every required access item. Capture Id,
   LicenseId, NamespacePrefix, and IsOwnedByProfile.
3. If more than one candidate matches, stop and ask; do not guess.
4. Query any required `PermissionSetLicense` and existing `PermissionSetLicenseAssign`. Assign a missing
   license before its permission set.
5. Query existing `PermissionSetAssignment` records for the target user and candidate set IDs.
6. Create only missing assignments. Treat `DUPLICATE_VALUE` as already assigned, then re-query.
7. Re-read the assigned permission sets and assignments and verify each is attached to the intended user.
8. Turn on Stage Management headlessly by PATCHing `IndustriesStageMgmtPref` to `desiredState:true`, then
   verify the feature provisioned via `fetchInitialStageManagementData` (`hasAccess:true`) — not the pref
   read-back alone.
9. Confirm Context Service is enabled; if not, enable it as above and re-verify with a live endpoint.

## Failure and rollback rules

- Missing permission set or license: report the exact missing API/label and stop dependent steps.
- License-limit failure: do not remove another user's license; report the limit.
- Assignment failure: preserve successful pre-existing assignments; remove only assignments created by
  this run and only when the user requests rollback.
- Never edit a standard managed permission set.

## Output contract

Return a table with target user, role, permission-set API name/ID, license ID if applicable, prior
state, action, and verified final state; the Stage Management feature enablement result; and the Context
Service enablement result. Separate blockers from optional runtime-user access.

## Definition of done

Every required design-time or runtime assignment for the explicitly selected role is present and verified
in fresh queries, Stage Management reads on (`IndustriesStageMgmtPref` enabled AND
`fetchInitialStageManagementData` returns `hasAccess:true` with the eight entities provisioned), and
Context Service reads enabled (or a Setup checkpoint is reported). No unrelated user or assignment was
changed.
