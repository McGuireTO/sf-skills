---
name: consumer-goods-visit-activity-act9-proof-validate
description: "Act 9 of 9: THE PROOF BEAT - verifies the end-to-end chain worked: each visit created in Act 8 carries the activity, its store-level questions, and its store's products. Uses Connect APIs (store-check, product-survey) per visitId — iterating the visits from Act 8. Depends on Act 8. Final act of the 9-Act Retail Execution steel thread."
metadata:
  version: "1.0"
  cliTools:
  - tool:
    - "sf"
    semver: ">=2.0.0"
---

# Act 9: Verify the Merchandiser Gets the Activity (THE PROOF BEAT)

**Part of:** [9-Act Retail Execution Steel Thread](../../README.md)  
**Depends on:** [Act 8 - Plan Visits & Attach](../act8-plan-and-attach/SKILL.md)  
**Enables:** Mobile execution (steel thread complete)

**Act 9 is the FINAL act — the proof beat for the whole setup. You MUST have completed Act 8 (plan visits & attach) first — at least one visit must exist with the activity attached. Skip only if you'll verify manually later; but if Act 9 passes, the merchandiser can execute the visit in the mobile app with full context.**

---

## Goal

Prove the chain works end-to-end: from Visit Specification (Act 1) through Activity Definition (Act 3), Questions (Act 4), Assortments (Act 6), Scoping (Act 7), to Visit Planning & Attachment (Act 8). For each visit created in Act 8, verify the visit actually carries the activity, with its store-level questions and that store's products, inside the validity window.

**Builder's intent:** "Prove it. Show me a rep's visit actually carries the promo activity, with its questions and that store's products, inside the window."

**What you'll create:**
1. Nothing — this Act is **read-only**. It runs verification calls (Connect APIs) and produces a pass/fail verification report.

**Definition of done:** End-to-end verification complete — each Act 8 visit carries the activity, its store-level questions, and store-specific products, inside the validity window. Ready to execute in the Retail Execution mobile app.

---

## What this Act does

This is **Act 9** (FINAL) of the visit-and-activity-setup orchestration — the **PROOF BEAT** that verifies the entire chain composed correctly. Iterating **per visit created in Act 8** (whose Ids are already in memory from Act 8 — do NOT re-discover them with a SOQL query), it confirms for each visit:

1. **The activity is attached** — `store-check` returns the visit context with the activity on `taskDefinitions[]`.
2. **Store-level questions are present** — the visit-level questions where `assessmentContext = "Store"`.
3. **Product rows carry the assessment** — `product-survey` returns the store's products, and at least one product carries an assessment task (`taskDefinitions[]`) with its corresponding AIDs; the product-level indicators where `assessmentContext = "StoreInStore"` are present.
4. **Validity window is honored** — the visit's `plannedVisitStartTime` is within the activity's `validFrom`/`validTo` (both already in memory from Act 3).

It uses **two Connect APIs**, both keyed on `visitId`: `store-check` (visit context + activity attachment + store-level questions) and `product-survey` (store-specific product rows + product-level indicators).

**Builder's mental model:** "Prove it. Show me a rep's visit actually carries the promo activity, with its questions and that store's products, inside the window."

---

## When to use

**Invoke this skill when:**
- You've completed Act 8 (plan visits & attach) and want to prove the setup works.
- Before handing off to field merchandisers — the final gate before mobile execution.
- The user asks to "verify", "prove it works", "check the merchandiser gets the activity", or "run the proof beat".

**Trigger phrases:**
- "Prove the whole thing works"
- "Verify the merchandiser gets the activity"
- "Run the end-to-end check"
- "Act 9" or "verification" or "proof beat"

**Skip this Act when:**
- You'll verify manually later (e.g., directly in the mobile app).
- You only ran a partial setup and aren't ready to prove the full chain.

---

## Prerequisites

| Act | Artifact | Required For |
|-----|----------|--------------|
| Act 8 | At least one visit with the activity attached (visit Ids in memory) | There must be something to verify |
| Act 3 | Activity validity window (`validFrom`/`validTo` in memory) | Validity-window check |
| Act 4 | Merchandiser name + user Id already known | Reporting only — no SOQL lookup |

**The merchandiser is already known.** The merchandiser's name and user Id are carried in memory from the prior acts — Act 9 does NOT look them up by email or user Id, and does NOT query visits by user. Verification runs **per `visitId`**, iterating the visits Act 8 created.

**Activity validity window includes the visit dates** — if a visit's `plannedVisitStartTime` falls outside the activity's `validFrom`/`validTo`, the activity won't show for that visit. Adjust the validity window in Act 3 or re-plan the visit in Act 8.

**Standard survey activities must exist for the SAME Internal Org Unit** — `product-survey` requires the org's standard survey activities (Facing, Price Survey, Distribution) to be configured **on the activity's own IOU**. These are discovered through a **standard template** — an `AsmtTskDefTmpl` with `IsStandardTask = true` scoped to that IOU — with a standard product-check `AssessmentTaskDefinition` (`IsStandardTask = true`) beneath it whose `StoreInStore` indicators carry `AssessmentKpi = Facing` / `PriceSurvey` / `Distribution`. **A standard template configured on a *different* IOU does not count** — the API resolves them per-IOU. If they're absent for this IOU, `product-survey` returns:

```json
[{"errorCode": "RESOURCE_NOT_FOUND",
  "message": "Facing, price survey, and distribution are required standard survey activities. Ask your Salesforce admin to configure them."}]
```

This is an **org/admin provisioning prerequisite owned upstream** (not something Acts 1–8 create). If you hit this error, surface it as a gap for the Salesforce admin — name the IOU that lacks a standard survey template and stop the product-survey check for that visit. Do **not** fabricate the standard template/activities to work around it.

---

## Inputs

Received from previous Acts (orchestrator integration):
```yaml
activityName: "Q1 Promotion Compliance"  # from Act 3
validFrom: "2026-03-01"                   # from Act 3
validTo: "2026-03-14"                     # from Act 3
visitIds: ["0Z5...", "0Z5..."]           # from Act 8 — the visits to verify
merchandiserName: "..."                    # from prior acts (reporting only)
merchandiserUserId: "005..."               # from prior acts (reporting only)
```

**Expected output** (returned to orchestrator):
```yaml
verificationPassed: true
visitsVerified: 2              # count of Act 8 visits that passed
activityAttached: true         # activity on every verified visit
storeQuestionsPresent: true    # assessmentContext = "Store" indicators present
productAssessmentPresent: true # ≥1 product carries an assessment task + AIDs
validityWindowHonored: true
```

### Key Concepts (reference before executing)

**End-to-end verification** — a read-only, per-`visitId` sweep that confirms every prior Act composed correctly. Critical points:

- **Two Connect APIs, both keyed on `visitId`:**
  - **store-check** — `GET /services/data/v68.0/connect/industries/retail/visit-execution/store-check?visitId=...` — returns the visit context, the activity attachment on `taskDefinitions[]`, and the store-level questions. Verify the indicators where `assessmentContext = "Store"`.
  - **product-survey** — `GET /services/data/v68.0/connect/industries/retail/visit-execution/product-survey?visitId=...` — returns the store's product rows. Verify the indicators where `assessmentContext = "StoreInStore"`, and confirm at least one product carries an assessment task (`taskDefinitions[]`) with its corresponding AIDs.
- **`assessmentContext` scopes what to verify** — store-level questions carry `assessmentContext = "Store"` (verified on `store-check`); product-level indicators carry `assessmentContext = "StoreInStore"` (verified on `product-survey`). Verify only the context that belongs to each call.
- **Product detail is NOT validated** — there is no source of truth for exact product names or counts, so do NOT assert specific SKUs, counts, or per-store differences. The only product assertion is presence: at least one product carries an assessment task with its AIDs.
- **All calls are read-only** — no create/update/delete, no MDAPI/metadata.

**Connect API response shapes (v68.0):**

*store-check* — returns the visit context and a `metadata` roll-up (task/indicator counts). When a **store-level** activity (`assessmentContext = "Store"`) is attached, its questions surface under `taskDefinitions[].indicatorDefinitions[]`; when none is attached, `taskDefinitions[]` is empty and `metadata.totalTaskDefinitions` is `0`:
```json
{
  "accountId": "001...",
  "internalOrganizationUnitId": "0gJ...",
  "metadata": {
    "answeredIndicatorDefinitions": 0,
    "mandatoryIndicatorDefinitions": 0,
    "totalIndicatorDefinitions": 1,
    "totalTaskDefinitions": 1
  },
  "plannedVisitStartTime": "2026-03-03T09:00:00.000Z",
  "plannedVisitEndTime": "2026-03-03T19:00:00.000Z",
  "responseStatus": null,
  "taskDefinitions": [
    {
      "assessmentTaskDefinitionId": "0Z4...",
      "description": "Promo Compliance Check",
      "indicatorDefinitions": [
        {
          "assessmentIndDefinitionId": "0eu...",
          "assessmentTaskIndDefinitionId": "0dt...",
          "assessmentKpi": "Display Up?",
          "assessmentContext": "Store",
          "dataType": "Boolean",
          "displayOrder": 1
        }
      ]
    }
  ],
  "visitDate": "2026-03-03",
  "visitId": "0Z5...",
  "visitSpecId": "1cb...",
  "visitSpecName": "visit execution"
}
```

> The populated `taskDefinitions[]`/`indicatorDefinitions[]` block above is the **expected shape** when a store-level activity is attached; its field names mirror product-survey's (below), differing only in `assessmentContext = "Store"`. If no store-context activity is attached, store-check returns `"taskDefinitions": []` with `totalTaskDefinitions: 0` — that is a data state (nothing to verify at the store level), not an API failure.

*product-survey* — returns the visit context, a `metadata` roll-up with `totalProducts`, and a `products[]` array; each product carries `taskDefinitions[].indicatorDefinitions[]` (the product-level KPI questions, `assessmentContext = "StoreInStore"`) with their AIDs. This block is an **actual org payload** (v68.0), trimmed to the fields that matter for verification:
```json
{
  "accountId": "001...",
  "internalOrganizationUnitId": "0gJ...",
  "metadata": {
    "answeredIndicatorDefinitions": 0,
    "totalIndicatorDefinitions": 3,
    "totalProducts": 4,
    "totalTaskDefinitions": 1
  },
  "products": [
    {
      "productId": "01t...",
      "productCategory": "Beverages",
      "productSource": "Assortment",
      "computedFields": { "Product2.Name": "Product1" },
      "taskDefinitions": [
        {
          "assessmentTaskDefinitionId": "0Z4LT00000002OR0AY",
          "assessmentTaskId": null,
          "description": "ATD Product Check Standard",
          "displayOrder": 0,
          "isStandardTask": true,
          "taskType": "InventoryCheck",
          "indicatorDefinitions": [
            {
              "assessmentIndDefinitionId": "0euLT00000006vAYAQ",
              "assessmentTaskIndDefinitionId": "0dtLT000000S6XDYA0",
              "assessmentKpi": "Facing",
              "assessmentContext": "StoreInStore",
              "dataType": "String",
              "displayOrder": 1
            }
            // ... Distribution, PriceSurvey (same shape, assessmentContext = "StoreInStore")
          ]
        }
      ]
    }
    // ... more products (Coca Cola, Limca, Pepsi — productSource "Planned" or "Assortment")
  ],
  "visitId": "0Z5...",
  "visitSpecId": "1cb..."
}
```

The AIDs on each indicator are `assessmentTaskDefinitionId` (the ATD), `assessmentIndDefinitionId`, and `assessmentTaskIndDefinitionId` — whichever the payload carries. Note `assessmentTaskId` is `null` here (the ATD/indicator *definitions* are surfaced, not per-run `AssessmentTask` records).

---

## Step-by-step procedure

### Step 1: Authenticate

Confirm you're pointed at the right org:

```bash
sf org display --target-org <org-alias>
```

The merchandiser's name and user Id are already in memory from the prior acts. The visit Ids to verify come from Act 8 (in memory). Iterate over each `visitId` and run Steps 2–4 per visit.

### Step 2: Verify the activity + store-level questions via store-check

For each Act 8 `visitId`, call `store-check`:

```bash
GET /services/data/v68.0/connect/industries/retail/visit-execution/store-check?visitId=0Z5xx0000000000AAA
```

From the response (see the shape in Key Concepts):
- Confirm the **activity is attached** — `taskDefinitions[]` is non-empty (or `metadata.totalTaskDefinitions ≥ 1`) and an entry's `description` matches the activity name from Act 3.
- Confirm the **store-level questions are present** — under `taskDefinitions[].indicatorDefinitions[]`, verify the indicators where **`assessmentContext = "Store"`** (e.g., "Display Up?"). Verify only the `"Store"` context here.

**Verification checklist (per visit):**
- [ ] `store-check` returns the visit context
- [ ] Activity is attached (`taskDefinitions[]` non-empty; `description` matches the Act 3 activity)
- [ ] At least one indicator with `assessmentContext = "Store"` is present

### Step 3: Verify products + assessment via product-survey

For the same `visitId`, call `product-survey`:

```bash
GET /services/data/v68.0/connect/industries/retail/visit-execution/product-survey?visitId=0Z5xx0000000000AAA
```

From the response:
- Confirm **at least one product carries the assessment** — some entry in `products[]` has a non-empty `taskDefinitions[]`, and that task carries its corresponding AIDs: the ATD (`assessmentTaskDefinitionId`), the indicator definition (`assessmentIndDefinitionId`), and the task-indicator definition (`assessmentTaskIndDefinitionId`). These are the *definition* IDs; `assessmentTaskId` is `null` until the per-run `AssessmentTask` is created during mobile execution — so verify the definition AIDs, not `assessmentTaskId`.
- Confirm the **product-level indicators** where **`assessmentContext = "StoreInStore"`** are present under those `taskDefinitions[].indicatorDefinitions[]`. Verify only the `"StoreInStore"` context here.
- **Do NOT** validate specific product names, counts, or per-store differences — there is no source of truth for product detail. Presence of the assessment + its definition AIDs is the assertion.

**Verification checklist (per visit):**
- [ ] `product-survey` returns product rows (`metadata.totalProducts` > 0)
- [ ] At least one product carries an assessment task (`taskDefinitions[]`) with its definition AIDs
- [ ] At least one indicator with `assessmentContext = "StoreInStore"` is present

### Step 4: Verify the validity window is honored

Using the `plannedVisitStartTime` returned by `store-check` (Step 2) and the activity's `validFrom`/`validTo` (already in memory from Act 3), confirm the visit falls inside the window — no query required:

- `plannedVisitStartTime >= validFrom`
- `plannedVisitStartTime <= validTo`

**Verification checklist (per visit):**
- [ ] `plannedVisitStartTime` is within `validFrom`/`validTo`

Repeat Steps 2–4 for every visit Id carried from Act 8.

---

## Validation

Confirm the checks pass for every Act 8 visit, using the two Connect APIs.

### Success Criteria

Act 9 is complete when, for each visit created in Act 8, ALL of the following are verified:

1. ✓ **Activity is attached** — `store-check` returns the visit with the activity on `taskDefinitions[]` (matching the Act 3 activity).
2. ✓ **Store-level questions are present** — at least one `store-check` indicator with `assessmentContext = "Store"`.
3. ✓ **Product assessment is present** — `product-survey` returns product rows and at least one product carries an assessment task (`taskDefinitions[]`) with its corresponding AIDs, plus at least one indicator with `assessmentContext = "StoreInStore"`.
4. ✓ **Validity window is honored** — the visit's `plannedVisitStartTime` is within the activity's `validFrom`/`validTo`.

**Failure patterns (surface as gaps)** — if any of these are true for a visit, Act 9 has NOT passed for that visit:

| Condition | Gap Type | Surface As |
|-----------|----------|------------|
| Activity not attached to visit | **Critical** | "Activity '<activity name>' not attached to visit <visitId>. Verify Visit Spec match (Act 1, Act 3) and validity window (Act 3, Act 8)." |
| No store-level questions (`assessmentContext = "Store"`) | **Critical** | "No store-level questions on visit <visitId>. Return to Act 4 and add the visit-level question(s)." |
| No product assessment (no product carries a task/AIDs, or no `StoreInStore` indicators) | **High** | "No product-level assessment for visit <visitId>. Verify the store's assortment (Act 6) and that the activity includes assortments (Act 3)." |
| `product-survey` returns `RESOURCE_NOT_FOUND` — "Facing, price survey, and distribution are required standard survey activities" | **High** (org prerequisite) | "The activity's Internal Org Unit <iouId> has no standard survey template. Ask your Salesforce admin to configure the standard survey activities (Facing/PriceSurvey/Distribution) for THIS IOU — a template on another IOU does not apply. Do not fabricate them." |
| Visit outside validity window | **Critical** | "Visit <visitId> plannedVisitStartTime is outside the activity validFrom/validTo range. Extend the window (Act 3) or re-plan the visit (Act 8)." |

---

## End state

After completing Act 9, for each Act 8 visit:

- ✅ **Visit carries the activity** — verified via `store-check` `taskDefinitions[]`.
- ✅ **Store-level questions present** — indicators with `assessmentContext = "Store"` (e.g., "Display Up?").
- ✅ **Product assessment present** — at least one product carries an assessment task with its AIDs, and product-level indicators with `assessmentContext = "StoreInStore"` are present.
- ✅ **Visit is within the validity window** — `plannedVisitStartTime` is between `validFrom` and `validTo`.

```text
✅ Act 9 Complete: End-to-end verification passed!

Summary (per Act 8 visit):
  • Activity: "Promo Compliance Check" attached to every verified visit
  • Store-level questions: present (assessmentContext = "Store")
  • Product assessment: present (≥1 product carries a task + AIDs; StoreInStore indicators present)
  • Validity Window: honored (visits within validFrom/validTo)

🎉 THE STEEL THREAD IS COMPLETE!
```

**Finish line:** The merchandiser can now open the Retail Execution mobile app, see the visit in their schedule, tap into it, and find the activity with its questions and products ready to capture data.

**This IS the last Act — the full 9-Act setup is DONE.**

**Out of scope / deferred** (set expectations — NOT part of Act 9):
- **Mobile app execution** — Act 9 only verifies the data is in place; tapping buttons in the app is out of scope.
- **Data capture and sync** — the app writes captured answers (`AssessmentIndValue`) during execution; Act 9 doesn't create these.
- **Reporting and analytics** — reports/dashboards on completion rates, answer distributions, and product compliance are a separate workstream.
- **Assignment** — merchandiser-to-account assignment (`AccountTeamMemberPeriod`) is owned upstream and verified in Act 8; Act 9 does not re-check it.
- **Product-detail validation** — exact product names, counts, and per-store differences are not asserted (no source of truth).

---

## Notes: best practices & architecture

**This Act is read-only — no create/update/delete, no MDAPI/metadata.** The proof beat observes; it never mutates.

**Verification runs per `visitId` through the two Connect APIs** (`store-check`, `product-survey`). Iterate the visit Ids from Act 8 — do NOT re-discover visits with a SOQL query, and do NOT look up the merchandiser (name and user Id are already in memory from the prior acts).

**`assessmentContext` scopes each check.** Verify `assessmentContext = "Store"` indicators on `store-check`, and `assessmentContext = "StoreInStore"` indicators on `product-survey`. Confirm at least one product carries an assessment task with its AIDs; do not assert product names or counts.

**Where verification sits in the lifecycle:**
```text
Plan Visits & Attach (Act 8)  →  Verification (this act)  →  Mobile execution (out of scope)
                                       ↑ read-only proof beat        AssessmentIndValue / sync
```

**Agent implementation flow:** take the visit Ids from Act 8 → for each `visitId`, call `store-check` (confirm activity attachment + `assessmentContext = "Store"` questions) → call `product-survey` (confirm ≥1 product carries an assessment task + AIDs and `assessmentContext = "StoreInStore"` indicators) → check the validity window from the returned `plannedVisitStartTime` against `validFrom`/`validTo` in memory → return `verificationPassed`, `visitsVerified`, and any failures to the orchestrator. Typical progress narration:

```text
⏳ Executing Act 9 verification...
   - Verifying visit 0Z5...AAA via store-check...   ✅ Activity attached, "Store" question present
   - Verifying products via product-survey...        ✅ Assessment present (StoreInStore indicators + AIDs)
   - Checking validity window...                      ✅ Within validFrom/validTo
   - Verifying visit 0Z5...BBB via store-check...     ✅ Activity attached, "Store" question present
✅ Act 9 Complete: Verification passed! Ready to execute in mobile app.
```

---

## Session state to track & handoff

> **Internal only — never print this to the user.** These variables (including `act9_complete`) are orchestration bookkeeping. Track them silently; do **not** echo raw variable names, IDs, or the gate flag into the conversation. When verification finishes, tell the user only a short plain-language confirmation (e.g., "✅ Act 9 done — verified end-to-end; each visit carries the activity, its questions, and store products").

This is the final Act — there is no downstream Act to hand off to, but maintain these for orchestration bookkeeping and audit:

- `verified_visit_ids` — the Act 8 visit Ids that passed verification.
- `activity_attached` — boolean; the activity is on every verified visit.
- `store_questions_present` — boolean; `assessmentContext = "Store"` indicators present.
- `product_assessment_present` — boolean; ≥1 product carries an assessment task + AIDs and `assessmentContext = "StoreInStore"` indicators present.
- `validity_window_honored` — boolean; every visit's `plannedVisitStartTime` is within `validFrom`/`validTo`.
- `act9_complete` — boolean; set to `true` after all verification checks pass for every Act 8 visit.

**If `act9_complete = true`, the steel thread is DONE.** The merchandiser can execute the visit in the mobile app.

---

## References

- **Act 1:** [Visit Specification](../act1-visit-specification/SKILL.md) ← The foundational Visit Specification all visits reference
- **Act 3:** [Activity Definition](../act3-activity-definition/SKILL.md) ← Where the activity's `validFrom`/`validTo` and `VisitSpecId` are set
- **Act 4:** [Add Questions](../act4-add-questions/SKILL.md) ← Where questions are added to the activity
- **Act 6:** [Assortment-Based Configuration](../act6-assortment-based/SKILL.md) ← Where store-specific assortments are configured
- **Act 8:** [Plan Visits & Attach](../act8-plan-and-attach/SKILL.md) ← Attachment path + assignment (prerequisite)
- **9-Act Steel Thread README:** [../../README.md](../../README.md) ← Full flow
- **Connect APIs:** `/connect/industries/retail/visit-execution/store-check` and `/product-survey` (v68.0+, if published)
- **Salesforce Object Reference:** `Visit`, `AssessmentTask`, `AssessmentTaskDefinition`, `AssessmentTaskIndDefinition`
