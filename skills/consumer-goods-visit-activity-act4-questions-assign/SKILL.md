---
name: consumer-goods-visit-activity-act4-questions-assign
description: "Act 4 of 9: Links questions to the activity with display order for Retail Execution. This is the PRIMARY, enforceable linking step — template-level links from Act 2 do NOT auto-flow to the activity, so every question must be explicitly linked here. Handles TWO kinds of questions: GENERIC questions reused from the Act 2 template, and NEW activity-specific questions created at this stage. Creates AssessmentTaskIndDefinition (ATID) junction records that bind each Assessment Indicator Definition (question) to the Assessment Task Definition (activity, from Act 3), setting DisplayOrder and IsMandatory. Use when the user wants to \"add questions to the activity\", \"link assessment indicators\", \"put questions on the activity\", \"add a question just for this activity\", \"set up question display order\", or \"configure activity questions\". Depends on Act 2 (template questions) and Act 3 (activity). Part of the 9-Act Retail Execution steel thread."
metadata:
  version: "1.0"
  cliTools:
  - tool:
    - "sf"
    semver: ">=2.0.0"
---

# Act 4: Add Questions to the Activity

**Part of:** [9-Act Retail Execution Steel Thread](../../README.md)  
**Depends on:** [Act 2 - Template and Questions](../act2-template-and-questions/SKILL.md), [Act 3 - Activity Definition](../act3-activity-definition/SKILL.md)  
**Enables:** [Act 5 - Standard Activity](../act5-standard-activity/SKILL.md) (auto-runs only when Act 1 created a new Visit Spec; otherwise the thread proceeds to Act 6)

**Act 4 is the bridge between the questions you defined (Act 2) and the activity container (Act 3). You MUST complete Act 2 (questions exist) and Act 3 (activity exists) before starting this act — the question links reference both.**

---

## Goal

Link Assessment Indicator Definitions (questions) to the Assessment Task Definition (activity) with display order and mandatory flags — so merchandisers see the right questions, in the right sequence, when they complete the activity.

**Builder's intent:** "Put my questions on this activity, in order — the generic ones from my template, plus any extra questions that only apply to this one activity."

**Two kinds of questions land on the activity here:**
- **Generic (reused)** — the Assessment Indicator Definitions created and linked to the *template* in Act 2. They do NOT arrive on the activity automatically (verified: creating an ATD from a template with template-indicator links yields **zero** activity-level links). You reuse them by explicitly linking each one to the activity here.
- **Activity-specific (new)** — questions that apply only to this one activity. You create the Assessment Indicator Definition *now* (Act 2 never made it), then link it to the activity the same way.

Both kinds become real on the activity through the **same** junction record (`AssessmentTaskIndDefinition`). The only difference is whether the underlying question already exists (generic) or you create it in this Act (activity-specific).

**What you'll create:**
1. (Activity-specific only) Zero or more new `AssessmentIndicatorDefinition` (AID) records — one per brand-new question
2. One `AssessmentTaskIndDefinition` (ATID) record per question — generic *and* activity-specific — linking it to the activity with a `DisplayOrder`

The same generic question can be reused across many activities with different ordering — this is how you build a reusable question library. Activity-specific questions are the escape hatch for one-off needs the template didn't anticipate.

---

## What this Act does

This is the **primary, enforceable linking step**. Template-level links from Act 2 (`AsmtTaskDefTemplateIndDef`) describe the template's *generic* question set but do NOT propagate to activities — an activity created from that template starts with **zero** questions until you link them here. This Act:

1. **(Activity-specific questions only) Creates new `AssessmentIndicatorDefinition` (AID) records** for questions that apply solely to this activity and were never part of the Act 2 template. The new AID **must** carry the same `InternalOrganizationUnitId` as the activity (see the IOU-match rule below), or it cannot be linked.
2. **Creates `AssessmentTaskIndDefinition` (ATID) records** — one per question, for **both** the generic (reused-from-template) questions and any activity-specific questions. Think of ATID as the "questions-on-this-activity" junction. Each ATID record:
   - **Links one question to one activity** via foreign keys (`AssessmentIndDefinitionId` → question, `AssessmentTaskDefinitionId` → activity).
   - **Sets display order** — determines the sequence merchandisers see questions in (1-indexed).
   - **Configures the mandatory flag** — whether the question must be answered to complete the visit.
3. **Enables question reuse** — the same generic question (AID) can appear on multiple activities with different ordering.
4. **Verifies** the links resolve and appear in the correct order (no gaps, no duplicates).

### The IOU-match rule (applies to every link)

A question can only be linked to an activity when the question's `InternalOrganizationUnitId` **equals** the activity's `InternalOrganizationUnitId`. If they differ, the link is rejected with:

> *"Select an Assessment Indicator Definition with an Internal Organization Unit that matches the Assessment Task Definition's Internal Organization Unit."*

- **Generic questions** created in Act 2 already carry the Act 1 IOU, and the Act 3 activity carries that same IOU — so they link cleanly.
- **Activity-specific questions** you create here MUST be created with that same IOU (`INTERNAL_ORG_UNIT_ID`, carried from Act 1/Act 3). Create it without the IOU and the link in Step 3 will fail.

---

## When to use

**Invoke this skill when:**
- You've completed Act 2 (questions/Assessment Indicator Definitions) and Act 3 (activity/Assessment Task Definition)
- You need to attach questions to an activity and control the order merchandisers answer them
- The user asks about "add questions to the activity", "link assessment indicators", "put questions on the activity", "set up question display order", or "configure activity questions"

**Trigger phrases:**
- "Put my questions on this activity, in order"
- "Add the questions to the activity"
- "Link the indicators to the activity"
- "Act 4" or "add questions"

---

## Prerequisites

| Act | Artifact | Required For |
|-----|----------|--------------|
| Act 2 | Assessment Indicator Definitions (AIDs) — the generic questions | `AssessmentIndDefinitionId` for each **reused** question |
| Act 3 | Assessment Task Definition (ATD) | `AssessmentTaskDefinitionId` for the activity |
| Act 1/3 | Internal Organization Unit id | Must match on every AID you link (and on any activity-specific AID you create here) |

**Object permissions** — the running user needs Create on `AssessmentTaskIndDefinition` (always), and Create on `AssessmentIndicatorDefinition` (only if you'll add activity-specific questions here):
```sql
SELECT Parent.Name, SobjectType, PermissionsRead, PermissionsCreate
FROM ObjectPermissions
WHERE SobjectType IN ('AssessmentTaskIndDefinition', 'AssessmentIndicatorDefinition')
  AND PermissionsCreate = true
```
If `AssessmentTaskIndDefinition` doesn't return with `PermissionsCreate = true`, the user cannot create the links. If you plan to add activity-specific questions, `AssessmentIndicatorDefinition` must also come back `true`.

**Record IDs to have in hand:**
- `AssessmentIndDefinitionId` for each **generic** question you're reusing (from Act 2)
- `AssessmentTaskDefinitionId` for the activity (from Act 3)
- `InternalOrganizationUnitId` (from Act 1/Act 3) — required to create any activity-specific question so it matches the activity's IOU

---

## Inputs

| Variable | Description | Source | Example |
|---|---|---|---|
| `ORG_ALIAS` | Target org alias for `sf` CLI commands | Auth session | `my-re-org` |
| `ACTIVITY_ID` | Assessment Task Definition the questions attach to | Act 3 | `0Z4xx00000000o1CAA` |
| `INTERNAL_ORG_UNIT_ID` | IOU the activity carries — every linked AID must match it | Act 1/3 | `0gJxx0000000001EAA` |
| `INDICATOR_ID_1` | First **generic** question reused from the template (e.g., "Display Up?") | Act 2 | `0euxx00000001SLAAY` |
| `INDICATOR_ID_2` | Second **generic** question reused from the template (e.g., "Facings Count") | Act 2 | `0euxx00000001SLBBY` |
| `NEW_INDICATOR_ID_*` | **Activity-specific** question(s) created in this Act (Step 2), if any | Act 4 | `0euxx00000001SLCCY` |

### Key Concepts (reference before executing)

**Two question types — same junction, different origin.** Everything on the activity is an `AssessmentIndicatorDefinition` (AID) joined via an `AssessmentTaskIndDefinition` (ATID). What differs is where the AID came from:

| | Generic (reused) | Activity-specific (new) |
|---|---|---|
| **Where the AID is created** | Act 2 (linked to the *template*) | Act 4 — here (Step 2) |
| **Reusable across activities?** | Yes — the template's shared library | No — belongs to this one activity |
| **Arrives on the activity how?** | You link it here (template links do NOT auto-flow) | You create it, then link it here |
| **IOU** | Already has the Act 1 IOU | You must set it to match the activity |
| **Use when** | The question is common to every activity built from this template | The question only makes sense for this specific activity/promotion |

Both still need an explicit ATID at the activity level — that link, not the template link, is the enforceable contract for what merchandisers actually answer.

**AssessmentTaskIndDefinition (ATID)** — the junction object linking a question (AID) to an activity (ATD). Critical fields:

- **AssessmentTaskDefinitionId** — the activity this question appears on (from Act 3). **Required.**
- **AssessmentIndDefinitionId** — the question being added (generic from Act 2, or activity-specific from Step 2). **Required.**
- **DisplayOrder** — sequence position, **1-indexed** (starts at 1, NOT 0). **Required.** The most common mistake is starting at 0, which causes unexpected ordering.
- **IsMandatory** — whether the merchandiser must answer to complete the visit. Defaults to `false`. Use `true` sparingly — only for truly required data, since it blocks visit completion.
- **The link is directional** — ATID references the activity and the question, but the activity and question objects don't know about ATID.
- **Question reuse** — the same `AssessmentIndDefinitionId` can appear on multiple activities with different `DisplayOrder` values (build a question library). Activity-specific questions, by convention, aren't reused elsewhere.
- **IOU must match** — the AID's `InternalOrganizationUnitId` must equal the activity's, or the link is rejected. Generic AIDs already match; activity-specific AIDs must be created with the matching IOU.
- **Deletion cascades** — deleting an AID (question) deletes all ATID records linking it; deleting an ATD (activity) deletes all ATID records on it. The other side survives, minus the link.

---

## Step-by-step procedure

### Step 1: Confirm Carried-Forward IDs (generic questions + activity + IOU)

This Act consumes IDs that already exist — don't re-query them by name. Carry them forward:

- `ACTIVITY_ID` — the Assessment Task Definition from **Act 3** (referenced as `AssessmentTaskDefinitionId`).
- `INTERNAL_ORG_UNIT_ID` — the IOU on the activity, from **Act 1/Act 3**. Any question you link must carry this same IOU.
- `INDICATOR_ID_1`, `INDICATOR_ID_2`, … — one captured id per **generic** question from **Act 2** (referenced as `AssessmentIndDefinitionId`). Carry forward as many as you created — these are the template's shared questions you're reusing.

```bash
ACTIVITY_ID="0Z4xx00000000o1CAA"          # from Act 3
INTERNAL_ORG_UNIT_ID="0gJxx0000000001EAA"  # from Act 1/Act 3 — every linked AID must match this
INDICATOR_ID_1="0euxx00000001SLAAY"        # from Act 2 ("Display Up?", generic)
INDICATOR_ID_2="0euxx00000001SLBBY"        # from Act 2 ("Facings Count", generic)
```

Optionally confirm the generic questions still exist and check their `AssessmentContext`:

```bash
sf data query \
  --query "SELECT Id, Name, AssessmentContext, InternalOrganizationUnitId FROM AssessmentIndicatorDefinition WHERE Id IN ('$INDICATOR_ID_1','$INDICATOR_ID_2')" \
  --target-org <org-alias>
```

Confirm each row's `InternalOrganizationUnitId` equals `$INTERNAL_ORG_UNIT_ID`. If a generic question has a different IOU than the activity, it can't be linked (see the IOU-match rule) — recreate it under the matching IOU.

### Step 2: (Optional) Create Activity-Specific Questions

**First, ask the user which they want** — don't assume. Pose it explicitly:

> "Do you want to add any questions that apply **only to this activity**, or just reuse the generic questions from your template? [Reuse only / Add activity-specific too]"

- If **reuse only** → skip this entire step and go to Step 3 with just the generic `INDICATOR_ID_*` ids from Step 1.
- If **add activity-specific too** → ask **"How many activity-specific questions?"** and for **each** one collect a name, `DataType`, and `AssessmentContext` (exactly as Act 2 gathers question details). There is **no fixed count** — create as many (or as few) as the user asks for. Then run the create call below once per question.

Do this when the activity needs a question the Act 2 template never defined — one that applies **only** to this activity.

```bash
sf data create record --sobject AssessmentIndicatorDefinition \
  --values "Name='Promo Endcap Photo' Description='Photo of the promotional endcap for this campaign' DataType=String IsActive=true AssessmentContext=Store InternalOrganizationUnitId=$INTERNAL_ORG_UNIT_ID" \
  --target-org <org-alias>
```

> **Quote multi-word values.** Any field value containing spaces (`Name`, `Description`) must be wrapped in single quotes inside `--values`, or the CLI splits on the space and drops the field (`REQUIRED_FIELD_MISSING`).

Capture the returned id — you'll link it in Step 3 alongside the generic ones:

```bash
NEW_INDICATOR_ID_1="0euxx00000001SLCCY"   # activity-specific, created just now
```

- `DataType` is **immutable** after creation — pick it deliberately (`Boolean`, `String`, `Number`, `DateTime`, `Percentage`, `Decimal`, `Picklist`, `Multi-Select Picklist`).
- `AssessmentContext` is `Store`, `InStore`, or `StoreInStore` (there is **no** "Product" value). `Store` = answered once per visit; `StoreInStore` = also per merchandising section.
- Repeat this create once per activity-specific question, capturing `NEW_INDICATOR_ID_2`, `NEW_INDICATOR_ID_3`, ….

### Step 3: Link Every Question to the Activity

Create one `AssessmentTaskIndDefinition` (ATID) per question — **both** the generic ids from Step 1 and any activity-specific ids from Step 2 — assigning each a 1-indexed `DisplayOrder`. Interleave them in whatever order merchandisers should see them; ATID doesn't care whether the underlying AID is generic or activity-specific.

**Link the first generic question ("Display Up?"):**
```bash
POST /services/data/v68.0/sobjects/AssessmentTaskIndDefinition
Content-Type: application/json

{
  "IsMandatory": false,
  "AssessmentIndDefinitionId": "0euxx00000001SLAAY",
  "AssessmentTaskDefinitionId": "0Z4xx00000000o1CAA",
  "DisplayOrder": 1
}
```

**Response:**
```json
{
  "id": "0dtxx00000001SAAAY",
  "success": true,
  "errors": []
}
```

**Link the second generic question ("Facings Count"):**
```bash
POST /services/data/v68.0/sobjects/AssessmentTaskIndDefinition
Content-Type: application/json

{
  "IsMandatory": false,
  "AssessmentIndDefinitionId": "0euxx00000001SLBBY",
  "AssessmentTaskDefinitionId": "0Z4xx00000000o1CAA",
  "DisplayOrder": 2
}
```

**Link an activity-specific question (from Step 2), if any:**
```bash
POST /services/data/v68.0/sobjects/AssessmentTaskIndDefinition
Content-Type: application/json

{
  "IsMandatory": false,
  "AssessmentIndDefinitionId": "0euxx00000001SLCCY",
  "AssessmentTaskDefinitionId": "0Z4xx00000000o1CAA",
  "DisplayOrder": 3
}
```

**What these do:**
- Each POST adds one question to the activity at the given `DisplayOrder` (1, 2, 3, …).
- Generic and activity-specific links are identical in shape — only the `AssessmentIndDefinitionId` source differs.
- If any POST returns *"Select an Assessment Indicator Definition with an Internal Organization Unit that matches…"*, that AID's IOU ≠ the activity's IOU — fix the AID (recreate it with `$INTERNAL_ORG_UNIT_ID`) before retrying.

### Step 4: Verify Links

Query all questions on the activity by the `ACTIVITY_ID` captured in Act 3 — filter on the `AssessmentTaskDefinitionId` foreign key:

```bash
sf data query \
  --query "SELECT Id FROM AssessmentTaskIndDefinition WHERE AssessmentTaskDefinitionId = '$ACTIVITY_ID'" \
  --target-org <org-alias>
```

Expected result — one `Id` row per linked question, generic and activity-specific alike (three in the worked example: two generic + one activity-specific):

| Id |
|---|
| 0dtxx00000001SA001 |
| 0dtxx00000001SA002 |
| 0dtxx00000001SA003 |

### Step 5: Verify with Indicator Details (Optional Deep Check)

Join query to see question names and contexts. The parent relationship name is **`AssessmentIndDefinition`** (the relationship name on the `AssessmentIndDefinitionId` field — NOT the object name `AssessmentIndicatorDefinition`):

```bash
sf data query \
  --query "SELECT Id, AssessmentIndDefinition.Name, AssessmentIndDefinition.AssessmentContext, DisplayOrder FROM AssessmentTaskIndDefinition WHERE AssessmentTaskDefinitionId = '$ACTIVITY_ID' ORDER BY DisplayOrder" \
  --target-org <org-alias>
```

Expected result (`AssessmentContext` returns the stored API value — `Store`, `InStore`, or `StoreInStore`). The generic and activity-specific questions are indistinguishable in this view — both are just linked AIDs:

| ATID.Id | AID.Name | AID.AssessmentContext | DisplayOrder |
|---|---|---|---|
| 0dtxx00000001SA001 | Display Up? (generic) | Store | 1 |
| 0dtxx00000001SA002 | Facings Count (generic) | StoreInStore | 2 |
| 0dtxx00000001SA003 | Promo Endcap Photo (activity-specific) | Store | 3 |

---

## Validation

Confirm every ATID record exists and the questions appear in the correct order (Step 4 / Step 5 queries return these values).

### Success Criteria

- ✓ One `AssessmentTaskIndDefinition` record exists per question you linked — generic (from Act 2) **and** activity-specific (created in Step 2)
- ✓ Every activity-specific AID created in Step 2 carries `InternalOrganizationUnitId = ACTIVITY_ID`'s IOU (otherwise the link would have been rejected)
- ✓ `DisplayOrder` sequence is contiguous starting at 1 (no gaps)
- ✓ `AssessmentTaskDefinitionId` matches your Act 3 activity ID on every row
- ✓ `AssessmentIndDefinitionId` values match your Act 2 (generic) and Step 2 (activity-specific) question IDs
- ✓ `IsMandatory` flags set per your requirements (`false` in this example)
- ✓ Foreign keys resolve — both references point to existing records
- ✓ Verification query returns one row per question in correct order (no duplicates)

---

## End state

After completing Act 4:

- ✅ **(If any) Activity-specific `AssessmentIndicatorDefinition` records created** — new questions unique to this activity, each carrying the activity's IOU.
- ✅ **One `AssessmentTaskIndDefinition` record per question created** — generic questions reused from the Act 2 template and any activity-specific questions, all explicitly linked at the activity level.
- ✅ **Display order set** — e.g., "Display Up?" (order 1), "Facings Count" (order 2), "Promo Endcap Photo" (order 3).
- ✅ **The activity now has its full, enforceable question set attached** and knows the sequence to present them (template links alone would have left it empty).
- ✅ **The ATID Ids (and any new AID Ids) are captured** for later verification (Act 9).

**At this point:**
- Act 4 is the primary linking step — the activity's questions are now real and enforceable.
- The activity does NOT yet know **which products** to ask about.
- No accounts are scoped and no visits exist yet — those happen in Acts 7–8.

**You are NOT done with the full setup** — this is Act 4 of 9. Proceed to Act 5 (Standard Activity) — which auto-runs only when Act 1 created a new Visit Spec, and is otherwise skipped straight to Act 6 (Assortments).

---

## Gotchas and common errors

### 1. DisplayOrder Starts at 1
**Not zero-indexed.** First question is `DisplayOrder: 1`, second is `2`, etc. Common mistake: starting at 0 causes unexpected ordering.

### 2. IsMandatory Blocks Visit Completion
Setting `IsMandatory: true` means:
- Merchandiser **cannot complete the visit** until the question is answered
- Use sparingly — only for truly required data
- Our example uses `false` for both questions (optional)

### 3. The Link is Directional
`AssessmentTaskIndDefinition` references:
- **AssessmentTaskDefinitionId** → the activity (Act 3)
- **AssessmentIndDefinitionId** → the question (generic from Act 2, or activity-specific from Step 2)

The relationship is one-way: ATID joins them, but the activity and question objects don't know about ATID.

### 4. IOU Mismatch Blocks the Link
**Error:** *"Select an Assessment Indicator Definition with an Internal Organization Unit that matches the Assessment Task Definition's Internal Organization Unit."*
**Cause:** the AID's `InternalOrganizationUnitId` ≠ the activity's. Most common with an **activity-specific** question created in Step 2 without the IOU, or a generic AID that was created under a different IOU.
**Fix:** create (or recreate) the AID with `InternalOrganizationUnitId = $INTERNAL_ORG_UNIT_ID` — the same IOU the activity carries — then link it.

### Troubleshooting

**Error: "Required fields are missing"**  
Cause: one of the three required fields is missing (`AssessmentTaskDefinitionId`, `AssessmentIndDefinitionId`, `DisplayOrder`).  
Fix: ensure all three fields are in your POST body.

**Error: "Invalid foreign key relationship"**  
Cause: one of the IDs doesn't exist — `AssessmentTaskDefinitionId` not found → Act 3 didn't complete; `AssessmentIndDefinitionId` not found → the generic question (Act 2) or activity-specific question (Step 2) wasn't created.  
Fix: query to verify the IDs exist:
```bash
# Verify activity exists
SELECT Id FROM AssessmentTaskDefinition WHERE Id = '0Z4xx00000000o1CAA'

# Verify question exists
SELECT Id FROM AssessmentIndicatorDefinition WHERE Id = '0euxx00000001SLAAY'
```

**Questions Appear in Wrong Order**  
Cause: DisplayOrder values are out of sequence (e.g., 1, 3 instead of 1, 2).  
Fix: update the DisplayOrder on existing ATID records:
```bash
PATCH /services/data/v68.0/sobjects/AssessmentTaskIndDefinition/{ATID_Id}
Content-Type: application/json

{
  "DisplayOrder": 2
}
```

---

## Notes: best practices & architecture

**Generic vs activity-specific — decide before you link.** For each question the user wants, ask: *is this common to every activity built from the template (generic — reuse the Act 2 AID) or unique to this one activity (activity-specific — create a new AID in Step 2)?* When in doubt, prefer generic — a reused question keeps the library small and lets a single edit propagate. Reach for activity-specific only when the question genuinely doesn't belong on the shared template.

**Template links never substitute for activity links.** The `AsmtTaskDefTemplateIndDef` records from Act 2 describe the template's default question set but do NOT populate an activity — verified: a fresh ATD created from a template with template-indicator links has **zero** `AssessmentTaskIndDefinition` records. Act 4 is where questions actually land on the activity, for both types.

**Create ATID records sequentially** — one POST per question rather than batching. It's easier to debug and to capture each returned Id.

**Verify after each POST** — run the verification query after each link to catch errors immediately rather than at the end.

**Where the question links sit in the lifecycle:**

```text
Generic questions (AssessmentIndicatorDefinition / AID)   ← Act 2: linked to the TEMPLATE (shared library)
Activity-specific questions (AssessmentIndicatorDefinition) ← Act 4 Step 2: new, unique to this activity
Activity (AssessmentTaskDefinition / ATD)                 ← Act 3: the concrete activity
   ↓ (both kinds joined to the activity by ATID — Act 4)
Questions-on-activity (AssessmentTaskIndDefinition / ATID) ← Act 4 (this act): the enforceable question contract
   ↓ 
Standard Activity (Act 5, conditional) → Assortment (Act 6) → Account scoping (Act 7) → Visits (Act 8) → Verification (Act 9)
```

Act 4 is the enforceable contract that says "these questions, in this order, appear on this activity" — regardless of whether each question came from the shared template or was created here. Section-level (`StoreInStore`) questions gain their per-section repetition only after Act 6 attaches an assortment.

**Builder's intent translation** — when a builder says *"Put my template questions on this activity, plus one extra just for this promo"*, Claude interprets:
1. "my template questions" → link the existing generic AIDs (Act 2) via new `AssessmentTaskIndDefinition` records
2. "one extra just for this promo" → create a new activity-specific `AssessmentIndicatorDefinition` (Step 2) with the activity's IOU, then link it
3. "on this activity" → use the `AssessmentTaskDefinitionId` from Act 3 on every link
4. "in order" → set `DisplayOrder` values starting at 1, interleaving both kinds

The builder doesn't need to know the junction object is called `AssessmentTaskIndDefinition`, that template links don't auto-flow, that an activity-specific AID must share the activity's IOU, or that display order starts at 1 — Claude handles the API translation and guides through the gotchas.

---

## Session state to track & handoff

> **Internal only — never print this to the user.** These variables (including `act4_complete`) are orchestration bookkeeping. Track them silently to drive the gate below; do **not** echo raw variable names, IDs, or the gate flag into the conversation. When the Act finishes, tell the user only a short plain-language confirmation (e.g., "✅ Act 4 done — your extra questions are added").

Pass these forward to Act 5 (and Act 9 verification):

- `atid_ids` — the `Id`s of the `AssessmentTaskIndDefinition` records created (e.g., `[0dtxx00000001SA001, 0dtxx00000001SA002, 0dtxx00000001SA003]`), covering both generic and activity-specific links. **Required for Act 9** (verification queries questions through this junction).
- `activity_specific_indicator_ids` — the `Id`s of any new AIDs created in Step 2 (empty if none). Distinguishes them from the reused generic AIDs carried from Act 2.
- `activity_id` — carried from Act 3 (`AssessmentTaskDefinitionId` used on each link).
- `internal_org_unit_id` — carried from Act 1/Act 3; the IOU every linked AID shares.
- `question_contexts` — which questions are `Store` (once per visit) vs `StoreInStore` (also per merchandising section) — drives Act 6 assortment behavior.
- `act4_complete` — boolean; set to `true` after the Validation checks pass.

**Do NOT proceed to Act 5 (or, when skipped, Act 6) until `act4_complete = true`.**

---

## Next Act

Proceed to **Act 5: Standard Activity** (`../act5-standard-activity/SKILL.md`) — this auto-runs only when Act 1 *created* a new Visit Spec (it builds the standard activity with the Facings/Pricing/Distribution KPI questions the offline product survey requires); it is skipped when the spec was reused. Either way the thread then reaches **Act 6: Assortment-Based Configuration** (`../act6-assortment-based/SKILL.md`), which makes the activity assortment-based by linking it to a Product List. Downstream: Act 6 (Assortments), Act 7 (Account Scoping), Act 8 (Plan Visits & Attach), Act 9 (Verification).

---

## References

- **Act 2:** [Template and Questions](../act2-template-and-questions/SKILL.md) ← Prerequisite (created the generic questions and linked them to the template)
- **Act 3:** [Activity Definition](../act3-activity-definition/SKILL.md) ← Prerequisite (created the activity container)
- **Act 5:** [Standard Activity](../act5-standard-activity/SKILL.md) ← Next step (auto-runs only if Act 1 created a new Visit Spec)
- **Act 6:** [Assortment-Based Configuration](../act6-assortment-based/SKILL.md)
- **Act 9:** [Verification](../act9-verification/SKILL.md) ← End-to-end test including question answering
- **9-Act Steel Thread README:** [../../README.md](../../README.md) ← Full flow
- **Object Reference:** Salesforce `AssessmentTaskIndDefinition` object documentation (API v68.0, Winter '25+)
