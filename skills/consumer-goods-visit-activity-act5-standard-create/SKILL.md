---
name: consumer-goods-visit-activity-act5-standard-create
description: "Act 5 of 9: Create the STANDARD activity for a newly created Visit Specification. A standard activity is an Assessment Task Definition with `IsStandardTask = true` (the only difference from the non-standard activity built in Act 3) that carries at least three KPI questions — `AssessmentKpi` = Facing, PriceSurvey, and Distribution. The offline Retail Execution app resolves a visit's standard activity through the visit's Visit Specification; a brand-new Visit Spec has none, so the Act 9 product-survey verification fails until one exists. This Act runs AUTOMATICALLY (orchestrator-triggered, never a manual user request) whenever Act 1 created a new Visit Spec (`visit_spec_is_new = true`); it is skipped automatically when the spec was reused. The standard activity is time-scoped to the SAME validity window (`ValidFrom`/`ValidTo`) as the non-standard activity from Act 3 — `IsStandardTask = true` remains its only structural difference."
metadata:
  version: "1.0"
  cliTools:
  - tool:
    - "sf"
    semver: ">=2.0.0"
---

# Act 5: Standard Activity

**Part of:** [9-Act Retail Execution Steel Thread](../../README.md)  
**Depends on:** [Act 1 - Visit Specification](../act1-visit-specification/SKILL.md) (provides `visit_spec_id`, `internal_org_unit_id`, and the `visit_spec_is_new` flag), and the question patterns established in [Act 3](../act3-activity-definition/SKILL.md) / [Act 4](../act4-add-questions/SKILL.md)  
**Enables:** [Act 6 - Assortment-Based Activity](../act6-assortment-based/SKILL.md)

**Act 5 exists because the offline app requires a *standard activity* on every visit's Visit Specification.** When Act 1 creates a NEW Visit Spec, nothing else in the steel thread builds a standard activity for it, so the product survey has no baseline KPI questions to render and the Act 9 verification fails. This Act closes that gap.

---

## Goal

For a **newly created** Visit Specification, create one **standard activity** — an `AssessmentTaskDefinition` with `IsStandardTask = true` — bound to that Visit Spec, carrying **at least three questions** whose `AssessmentKpi` values cover **Facing**, **PriceSurvey**, and **Distribution**.

**Builder's intent:** "A new store-visit type needs a standard activity with the three baseline KPI questions, or the offline product survey has nothing to show and fails. Reused visit types already have theirs — don't touch them."

**What you'll create (only when `visit_spec_is_new = true`):**
1. One standard `AssessmentTaskDefinition` (`IsStandardTask = true`), built from a user-named standard template, bound to the Act 1 Visit Spec, and **time-scoped to the same `ValidFrom`/`ValidTo` window as the Act 3 activity**.
2. Three (or more) `AssessmentTaskIndDefinition` links attaching KPI questions (Facing, PriceSurvey, Distribution) to that standard activity.

> **This Act is automatic.** The orchestrator fires it on Act 1's `visit_spec_is_new = true` signal — the user never asks for the standard activity to be created. The only user inputs are the standard template **name** and (if creating fresh questions) the KPI question details.

---

## Gate: is the Visit Specification new?

**This Act is conditional. Read `visit_spec_is_new` from the Act 1 session state before doing anything.**

- **`visit_spec_is_new = false` (spec was reused):** Do NOT create a standard activity. Tell the user, in plain language: "The Visit Specification was reused, so its standard activity is assumed to already exist — skipping Act 5." Mark `act5_complete = true` (skipped) and hand off to Act 6.
- **`visit_spec_is_new = true` (spec was created in Act 1):** Proceed. Tell the user: "This is a **new Visit Spec**, so we need to create a new **standard activity** (`IsStandardTask = true`) with the three baseline KPI questions (Facing, PriceSurvey, Distribution) — otherwise the product survey verification in Act 9 will fail."

> `IsStandardTask = true` is the **only** structural difference between this standard activity and the non-standard activity created in Act 3. Everything else about the ATD create call is the same.

---

## When to use

**This Act is orchestrator-triggered, not user-requested.** It runs **automatically** the moment Act 1 reports a newly created Visit Specification (`visit_spec_is_new = true`) — the user does not (and should not) ask for the standard activity to be created. It is skipped **automatically** when Act 1 reused an existing spec.

**No trigger phrase is required** — the automatic gate is the `visit_spec_is_new = true` signal from Act 1. (If a user *does* volunteer "the product survey has no questions / is failing", run this same Act — but do not wait for such a prompt.)

---

## Prerequisites

Before running this Act, verify — **in this order, and STOP on the first that fails**:

- **`visit_spec_is_new = true`.** If it is `false`, apply the skip path above and do not continue.
- **`visit_spec_id` and `internal_org_unit_id`** are known from Act 1, and **`valid_from` / `valid_to`** are known from Act 3 (the standard activity binds to the Visit Spec + IOU and reuses Act 3's validity window, exactly like the Act 3 activity).
- **A standard Assessment Task Definition Template exists** — an `AsmtTskDefTmpl` with `IsStandardTask = true`. **This Act does NOT create one.** You will ask the user for its **name** and resolve it to an `Id` (see Step 2). If the org has none, STOP and report that a standard template must be created first (via Act 2's template step with `IsStandardTask = true`, or by an admin) before Act 5 can run.
- **Object permissions** for `AssessmentTaskDefinition` (Create), `AssessmentIndicatorDefinition` (Create — only if creating new questions), and `AssessmentTaskIndDefinition` (Create).

---

## Inputs

| Variable | Description | Source | Example |
|---|---|---|---|
| `ORG_ALIAS` | Target org alias for `sf` CLI commands | Auth session | `re-org` |
| `VISIT_SPEC_ID` | The Visit Spec created in Act 1 | Act 1 session state | `0gOxx0000000001EAA` |
| `INTERNAL_ORG_UNIT_ID` | IOU used across the thread | Act 1 session state | `0gJxx0000000001EAA` |
| `VALID_FROM` / `VALID_TO` | Validity window — **reuse the Act 3 activity's window** | Act 3 session state | `2026-03-01` / `2026-03-14` |
| `STANDARD_ATDT_NAME` | Name of an existing standard template (`AsmtTskDefTmpl`, `IsStandardTask = true`) | **User-supplied (Step 2)** | `Standard Store Template` |
| `STANDARD_ATDT_ID` | Id resolved from `STANDARD_ATDT_NAME` | **Query result (Step 2)** | `0pTxx0000000001EAA` |

### Key concepts (reference before executing)

**Standard activity (`AssessmentTaskDefinition`, `IsStandardTask = true`)** — the baseline activity the offline app resolves for a visit *through its Visit Specification*. In this workflow it is **time-scoped to the same `ValidFrom`/`ValidTo` window as the Act 3 activity** (reuse Act 3's dates). `IsStandardTask = true` is the only structural difference from the Act 3 (non-standard) activity.

**`AssessmentKpi` (on `AssessmentIndicatorDefinition`)** — the KPI classification of a question. The offline product survey requires coverage of all three picklist values **`Facing`**, **`PriceSurvey`**, and **`Distribution`**. This is the field that makes a question count toward the standard-activity requirement. (When creating questions, also set `AssessmentContext = StoreInStore`.)

**Questions do NOT auto-flow from the template.** Just like Act 4, linking a template's indicator (`AsmtTaskDefTemplateIndDef`) does not put the question on the activity. You must create an `AssessmentTaskIndDefinition` link per question directly against the standard ATD.

---

## Step-by-step procedure

### Step 1: Confirm the gate

Re-check `visit_spec_is_new`. If `false`, apply the skip path and stop. Otherwise announce the plan (create a standard activity with the 3 KPI questions) and continue.

### Step 2: Ask the user for the standard template by NAME, then resolve its Id

Ask the user for the **name** of an existing **standard** Assessment Task Definition Template (`AsmtTskDefTmpl`, `IsStandardTask = true`) — **ask by name, not by Id.** Then resolve that name to an `Id` yourself:

```bash
sf data query \
  --query "SELECT Id, Name, IsStandardTask, IsActive, InternalOrganizationUnitId FROM AsmtTskDefTmpl WHERE Name = '<STANDARD_ATDT_NAME>' AND IsStandardTask = true AND InternalOrganizationUnitId = '<INTERNAL_ORG_UNIT_ID>'" \
  --target-org <org-alias>
```

- **Exactly one row** → capture its `Id` as `STANDARD_ATDT_ID` and continue.
- **More than one row** → the name is ambiguous; show the user the matches and have them pick, then capture that `Id`.
- **Zero rows** → no standard template by that name for this IOU. Offer to list the available standard templates so the user can give the right name:

  ```bash
  sf data query \
    --query "SELECT Id, Name, IsActive FROM AsmtTskDefTmpl WHERE IsStandardTask = true AND InternalOrganizationUnitId = '<INTERNAL_ORG_UNIT_ID>' ORDER BY CreatedDate DESC" \
    --target-org <org-alias>
  ```

  - If the list has entries, ask the user for the correct **name** and re-resolve.
  - **If there are no standard templates at all**, STOP and report: **"No standard Assessment Task Definition Template (`IsStandardTask = true`) exists for this Internal Organization Unit. Create one first (Act 2's template step with `IsStandardTask = true`), then re-run Act 5."** Do NOT create the template here.

### Step 3: Create the standard activity (AssessmentTaskDefinition, IsStandardTask = true)

This mirrors the Act 3 activity-create call, with `IsStandardTask = true` and the standard template:

```bash
sf data create record \
  --sobject AssessmentTaskDefinition \
  --values "Name='Standard Store Activity' IsActive=true Description='Standard activity carrying the baseline KPI questions for every visit on this Visit Spec' AsmtTskDefTmplId=<STANDARD_ATDT_ID> IsStandardTask=true ShouldIncludeAssortments=true VisitSpecId=<VISIT_SPEC_ID> TaskType=ConductInStoreSurveys InternalOrganizationUnitId=<INTERNAL_ORG_UNIT_ID>" \
  --target-org <org-alias>
```

**Field notes:**
- `IsStandardTask = true` — **the defining field.** This is the sole structural difference from the Act 3 (non-standard) activity.
- `ShouldIncludeAssortments = true` — enable the **Assortment flag** on the standard activity so it picks up the visit's assortment. This is a Boolean on `AssessmentTaskDefinition`.
- `AsmtTskDefTmplId` — the `STANDARD_ATDT_ID` from Step 2.
- `VisitSpecId` — **must be the Act 1 `VISIT_SPEC_ID`.** The offline app resolves the standard activity through the visit's Visit Spec, so this binding is what makes the activity apply to the new spec's visits.
- `InternalOrganizationUnitId` — must match the Act 1 IOU (and the IOU of every question linked in Step 5).
- `Description` — required by a validation rule (same as Act 3).
- `TaskType` — a valid picklist value (e.g. `ConductInStoreSurveys`).

Capture the returned `Id` as `STANDARD_ACTIVITY_ID`.

### Step 4: Choose the KPI questions — copy from the template or create new

You need three questions covering `AssessmentKpi` = **Facing**, **PriceSurvey**, **Distribution**. Offer the user two paths (exactly as Act 3 / Act 4 handle questions):

**Path A — copy the questions from the standard template.** Read the template's indicator links, then reuse those `AssessmentIndicatorDefinition` records:

```bash
sf data query \
  --query "SELECT AssessmentIndDefId, AssessmentIndDef.Name, AssessmentIndDef.AssessmentKpi FROM AsmtTaskDefTemplateIndDef WHERE AsmtTskDefTmplId = '<STANDARD_ATDT_ID>'" \
  --target-org <org-alias>
```

Collect the `AssessmentIndDefId` values and their `AssessmentKpi`. These AIDs are re-linked to the standard activity in Step 5 (linking a template's question does NOT flow it to the activity — you must link explicitly).

**Path B — create new KPI questions.** Create one `AssessmentIndicatorDefinition` per missing KPI, setting `AssessmentKpi` explicitly:

```bash
sf data create record \
  --sobject AssessmentIndicatorDefinition \
  --values "Name='Facings count' DataType=Number Description='Number of product facings on shelf' AssessmentKpi=Facing AssessmentContext=StoreInStore InternalOrganizationUnitId=<INTERNAL_ORG_UNIT_ID> IsActive=true" \
  --target-org <org-alias>
```

Repeat for `AssessmentKpi=PriceSurvey` and `AssessmentKpi=Distribution`. Field reminders (from Act 2 / Act 4): `Description` is required by a validation rule; `DataType` is immutable after create and its valid values are `Number|Boolean|Percentage|DateTime|String|Decimal|Picklist|Multi-Select Picklist` (use `String`, not "Text"); `AssessmentContext` must be `StoreInStore`; each AID's `InternalOrganizationUnitId` **must match** the standard activity's IOU.

### Step 5: Link each question to the standard activity

For each chosen AID, create an `AssessmentTaskIndDefinition` link against the standard activity (one per question), exactly as Act 4 does:

```bash
sf data create record \
  --sobject AssessmentTaskIndDefinition \
  --values "AssessmentTaskDefinitionId=<STANDARD_ACTIVITY_ID> AssessmentIndDefinitionId=<AID_ID> DisplayOrder=1 IsMandatory=true" \
  --target-org <org-alias>
```

**Field notes:**
- `DisplayOrder` is 1-indexed; increment per question (1, 2, 3).
- Every linked AID's IOU must equal the standard activity's IOU, or the link returns `FIELD_CUSTOM_VALIDATION_EXCEPTION` ("Select an Assessment Indicator Definition with an Internal Organization Unit that matches the Assessment Task Definition's Internal Organization Unit").

### Step 6: Enforce KPI coverage (Facing, PriceSurvey, Distribution)

Confirm the standard activity now has questions covering **all three** required KPIs:

```bash
sf data query \
  --query "SELECT AssessmentIndDefinitionId, AssessmentIndDefinition.Name, AssessmentIndDefinition.AssessmentKpi FROM AssessmentTaskIndDefinition WHERE AssessmentTaskDefinitionId = '<STANDARD_ACTIVITY_ID>'" \
  --target-org <org-alias>
```

- **If all three `AssessmentKpi` values (Facing, PriceSurvey, Distribution) are present**, the standard activity is complete — continue.
- **If any KPI is missing**, do NOT mark the Act done. Tell the user which KPI(s) are missing and loop back to Step 4 (Path A or B) to create/link the missing question(s). The offline product survey requires all three; an incomplete set still fails Act 9.

---

## Validation

**Expect, after Step 6:**
- One `AssessmentTaskDefinition` with `IsStandardTask = true`, `VisitSpecId = <Act 1 spec>`, and the Act 1 IOU. ✅
- At least three `AssessmentTaskIndDefinition` links whose AIDs' `AssessmentKpi` values cover Facing, PriceSurvey, and Distribution. ✅

### Success Criteria
- ✓ A standard activity (`IsStandardTask = true`) exists on the new Visit Spec.
- ✓ The Assortment flag is enabled (`ShouldIncludeAssortments = true`).
- ✓ Facing, PriceSurvey, and Distribution KPI questions are all linked to it.
- ✓ Every linked AID shares the activity's IOU.

---

## End state

After completing Act 5 (create path):
- ✅ The newly created Visit Spec has a **standard activity** carrying the three baseline KPI questions, so the Act 9 product-survey verification can succeed.

After the skip path (reused spec):
- ✅ No standard activity was created; the existing spec's standard activity is assumed present.

**You are NOT done with the full setup** — this is Act 5 of 9. Proceed to Act 6 (Assortment-Based Activity).

---

## Gotchas and common errors

### 1. Using `IsStandard` instead of `IsStandardTask`
There is no `IsStandard` field on `AssessmentTaskDefinition` or `AsmtTskDefTmpl`. The field that marks a template/activity as standard is **`IsStandardTask`** (Boolean). Set `IsStandardTask = true` on the activity (and use a template whose `IsStandardTask = true`).

### 2. Product survey still fails after Act 5
Most often a missing KPI. The offline app requires **all three** of Facing, PriceSurvey, and Distribution. Re-run the Step 6 coverage query — if only two KPIs are linked, add the third. Also confirm `VisitSpecId` on the standard activity matches the visit's Visit Spec exactly.

### 3. Copying template questions doesn't attach them
`AsmtTaskDefTemplateIndDef` links live on the *template*, not the activity. You must create an `AssessmentTaskIndDefinition` per question against the standard activity (Step 5). "Copy" here means reuse the AID `Id`s, then link them explicitly.

### 4. IOU mismatch on the question link
If an AID's IOU differs from the standard activity's IOU, the `AssessmentTaskIndDefinition` create fails with `FIELD_CUSTOM_VALIDATION_EXCEPTION`. Create/choose KPI questions on the same IOU as the Act 1 Visit Spec.

---

## Session state to track & handoff

> **Internal only — never print this to the user.** Track silently; when the Act finishes, give a short plain-language confirmation (e.g., "✅ Act 5 done — standard activity with Facing/PriceSurvey/Distribution is ready" or "✅ Act 5 skipped — Visit Spec was reused").

Maintain after Act 5:
- `standard_activity_id` — `Id` of the created standard `AssessmentTaskDefinition` (unset on the skip path).
- `standard_atdt_id` — the standard template `Id` used.
- `standard_kpi_questions` — the AID ids/KPIs linked (Facing, PriceSurvey, Distribution).
- `act5_complete` — boolean; `true` after Step 6 passes, or `true` (skipped) when `visit_spec_is_new = false`.

**Do NOT block Act 6 on the create path when the spec was reused** — the skip path completes Act 5 immediately.

---

## Out of scope / deferred (for this Act)

- **Creating the standard template** — Act 5 asks for an existing standard `AsmtTskDefTmpl`; it does not create one.
- **Account scoping** — happens in Act 7. The standard activity attaches to visits via the Visit Spec, not via per-account scoping here.
- **Visit planning / generation** — Act 8.
- **Product-survey verification** — Act 9 (which this Act unblocks).

---

## Next Act

Proceed to **Act 6: Assortment-Based Activity** (`../act6-assortment-based/SKILL.md`).

---

## References

- **Act 1 (Visit Specification)** — source of `visit_spec_id` and the `visit_spec_is_new` flag that gates this Act.
- **Act 3 (Activity Definition)** — the non-standard activity create pattern this Act mirrors (with `IsStandardTask = true`).
- **Act 4 (Add Questions)** — the `AssessmentTaskIndDefinition` question-linking pattern this Act reuses.
- **Act 9 (Verification)** — the product-survey beat that requires this standard activity.
