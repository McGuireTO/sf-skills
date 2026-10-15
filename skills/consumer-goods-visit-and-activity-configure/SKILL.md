---
name: consumer-goods-visit-and-activity-configure
description: "\"Set up retail execution\" / \"configure visit and activity\" with no narrowing qualifier means running UP TO NINE ACTS in order — Act 1 (Visit Specification), Act 2 (Template + Generic Questions), Act 3 (Activity, no questions yet), Act 4 (Link Questions to Activity - PRIMARY linking step: reuse generic + add activity-specific), Act 5 (Standard Activity - only when Act 1 created a NEW Visit Spec; a standard activity with the Facing/PriceSurvey/Distribution KPI questions the offline product survey requires), Act 6 (Assortments), Act 7 (Account Scoping), Act 8 (Plan Visits & Attach Activity - REQUIRED), and Act 9 (Verification - optional proof beat). Guided end-to-end admin setup of Retail Execution visit-and-activity workflows: Visit Spec creation/reuse, template with generic question structure, activity creation, linking questions to the activity (reused generic questions plus activity-specific ones), a standard activity for newly created Visit Specs, assortment-based product surveying, account-level scoping, visit planning with activity attachment, and end-to-end verification. Triggers on \"set up retail execution\", \"configure visit and activity\", \"create activity with questions\", \"enable assortments\", \"scope to accounts\", \"attach activity to visits\", \"plan visits\", \"verify setup\"."
metadata:
  version: "1.0"
  cliTools:
  - tool:
    - "sf"
    semver: ">=2.0.0"
---

# Visit and Activity Setup (Acts 1-9)

**Setting up Retail Execution visit-and-activity means running up to NINE acts in order — Act 1 (Visit Specification), Act 2 (Template + Generic Questions), Act 3 (Activity), Act 4 (Link Questions to Activity — PRIMARY linking step), Act 5 (Standard Activity — only when Act 1 created a NEW Visit Spec), Act 6 (Assortments), Act 7 (Account Scoping), Act 8 (Plan Visits & Attach Activity - REQUIRED), and Act 9 (Verification - OPTIONAL proof beat).** This is the full end-to-end setup journey; Act 4 is where questions become real on the activity (reused generic + activity-specific), Act 5 gives a newly created Visit Spec its standard activity, Act 8 is the minimum required completion point, Act 9 is the final verification.

This skill is an **orchestrator** that guides an admin through setting up a complete Retail Execution activity workflow, delegating to atomic sub-skills for each act.

## Scope

"Set up retail execution" with no narrowing qualifier means running **up to nine acts** in order — Visit Specification, Template + Generic Questions, Activity, Link Questions to Activity (the primary linking step — reuse generic + add activity-specific), Standard Activity (only when Act 1 created a new Visit Spec), Assortments, Account Scoping, Plan Visits & Attach Activity (REQUIRED), and optional Verification (proof beat).

**Definition of done:** Act 8 complete (visits planned and activity attached). Act 9 is optional verification to prove the complete chain works.

## Preflight: Org & user gates (run ONCE, before Act 1)

These are org-/user-level preconditions for the *entire* steel thread, not per-act checks — verify them **once, up front, before delegating to Act 1**. Run them **in this order and STOP on the first that fails** (a missing org pref or user permission blocks everything downstream). Do not proceed to Act 1 until both pass.

### Gate 1 — User has the Retail Execution user permission

The running user needs the RE user permission (`PermissionsRunRetailExecution`, surfaced in the UI as "Run Retail Execution") for visit planning/execution to behave correctly. Check whether the current user has it assigned via any Permission Set using the `Count()` pattern:

```apex
// Run via: sf apex run --target-org <org-alias>
String userId = UserInfo.getUserId();
String userPermission = 'PermissionsRunRetailExecution';
Integer permissionSets = Database.countQuery(
  'SELECT Count() FROM PermissionSet WHERE ' + userPermission +
  ' = true AND Id IN (SELECT PermissionSetId FROM PermissionSetAssignment WHERE AssigneeId = :userId)'
);
System.debug('RE permission-bearing permission sets assigned to user: ' + permissionSets);
```

**If the count is `0`, STOP and report:** **"The current user lacks the Retail Execution user permission. Assign a Permission Set that grants `Run Retail Execution` (`PermissionsRunRetailExecution`), then re-run."** A count `>= 1` confirms the user holds the permission through at least one assigned Permission Set.

### Gate 2 — Retail Execution is enabled for the org (org pref check)

The Visit Specification and all downstream RE objects only exist once Retail Execution is turned on. This is the `enableRetailExecution` flag on the `RetailExecutionSettings` metadata type — it is **not** SOQL-queryable, so retrieve the settings metadata and inspect the flag:

```bash
sf project retrieve start \
  --metadata Settings:RetailExecution \
  --target-org <org-alias>
```

Then open the retrieved `force-app/main/default/settings/RetailExecution.settings-meta.xml` and confirm:

```xml
<enableRetailExecution>true</enableRetailExecution>
```

**If `enableRetailExecution` is `false` (or the setting is absent), STOP and report:** **"Retail Execution is not enabled in this org. Enable it under Setup → Retail Execution Settings (or deploy `RetailExecutionSettings` with `enableRetailExecution=true`), then re-run."** Do NOT proceed to Act 1 against a disabled org — the Visit Specification create will fail or produce an unusable spec.

> Note: `RetailExecutionSettings` also exposes `enableProductHierarchy` and `enableVisitSharing`. Those are optional; only `enableRetailExecution` gates the steel thread.

## Before any writes: State the plan

Before creating any objects, output a single-line plan:

```text
📋 Acts to run: 1 (Visit Spec) → 2 (Template + 2 generic questions) → 3 (Activity) → 4 (Link questions: reuse generic + add activity-specific) → 5 (Standard Activity: only if the Visit Spec is new) → 6 (Assortments: Yes/No) → 7 (Scoping) → 8 (Plan Visits & Attach) → 9 (Verification: Yes/No)
```

## Orchestration Pattern

This skill does NOT execute API calls directly. Each act delegates to an atomic sub-skill. Full detail in `source/skills/actN-.../SKILL.md`.

### Act 1: Visit Specification

**End state:** Visit Specification exists (created or reused) with `UsageType: "Retail"`. Capture whether it was **created vs reused** (`visitSpecIsNew`) — Act 5 branches on it.

**Form:** Present reuse/create choice + name if creating.

**Delegate to:** `source/skills/act1-visit-specification/SKILL.md`

**Builder's intent**: "Set up the store-visit type every activity will attach to — and never create a duplicate, because duplicate specs cause activity-attachment mismatches and orphaned visits."

### Act 2: Template + Questions

**End state:** ATDT + 2 generic AIDs + 2 ATDTIDs exist.

**Form:** Template name, question 1 (name, DataType, context), question 2 (name, DataType, context).

**Delegate to:** `source/skills/act2-template-and-questions/SKILL.md`

**Builder's intent**: "I want reusable questions and a template that marks an activity as one-off, event-driven rather than a recurring standard task."

### Act 3: Activity Definition

**End state:** ATD exists, references ATDT from Act 2, linked to Visit Spec from Act 1. **No questions linked yet** — that's Act 4.

**Form:** Activity name, date range (ValidFrom/ValidTo).

**Delegate to:** `source/skills/act3-activity-definition/SKILL.md`

**Builder's intent**: "We're running a two-week promotion. I need a one-off activity for it, tied to our store-visit type, that only lives for those two weeks."

### Act 4: Link Questions to Activity

**End state:** ATID records exist linking questions to the activity — the activity had zero questions before this step (template links do NOT auto-flow).

**Form (two parts):**
1. **Reuse generic questions** — show the template's questions (from Act 2), ask which to link, capture DisplayOrder + IsMandatory per link.
2. **Add activity-specific questions?** [Yes/No] — if yes, for each: name, DataType, context, DisplayOrder, IsMandatory. Create the new AID with the activity's IOU, then link it.

**Delegate to:** `source/skills/act4-add-questions/SKILL.md`

**Builder's intent**: "Put my template questions on this activity, in order — plus any extra questions just for this one activity — and let me mark which ones are mandatory."

**Not optional:** without Act 4 the activity has no questions. (Adding *only* activity-specific questions, or reusing *only* generic ones, are both valid — but at least one question must be linked.)

### Act 5: Standard Activity

**Runs AUTOMATICALLY — never a manual step.** This Act is orchestrator-triggered on `visitSpecIsNew = true`; the user does **not** (and should not) ask for a standard activity. It fires **only when Act 1 created a NEW Visit Spec**. A brand-new Visit Spec has no standard activity, and the offline app resolves a visit's standard activity through its Visit Spec — so the Act 9 product-survey verification fails until one exists. **Skipped automatically** when the Visit Spec was reused.

**End state:** A standard `AssessmentTaskDefinition` (`IsStandardTask = true` — the only structural difference from the Act 3 activity) bound to the Act 1 Visit Spec and **time-scoped to the SAME `ValidFrom`/`ValidTo` window as the Act 3 activity**, carrying at least 3 questions whose `AssessmentKpi` covers **Facing**, **PriceSurvey**, and **Distribution**. (Or: skipped, when the spec was reused.)

**Form:** No trigger prompt — the automatic gate is `visitSpecIsNew = true`. When it fires, the only user input is the standard template **name** (ask by name, resolve to Id) and, if creating fresh questions, the KPI question details. Then either copy the template's KPI questions or create new ones covering Facing/PriceSurvey/Distribution. Reuse the Act 3 `ValidFrom`/`ValidTo` for the standard activity.

**Delegate to:** `source/skills/act5-standard-activity/SKILL.md`

**Builder's intent**: "A brand-new store-visit type needs the baseline standard activity with Facing, PriceSurvey, and Distribution questions, or the product survey has nothing to show and fails."

**Skip if:** Act 1 reused an existing Visit Spec (`visitSpecIsNew = false`).

### Act 6: Assortments

**End state:** ATD.ShouldIncludeAssortments updated to true.

**Form:** "Enable assortment-based product surveys? [Yes/No]"

**Delegate to:** `source/skills/act6-assortment-based/SKILL.md`

**Builder's intent**: "Show merchandisers only the products listed for the store they're actually in — a different product set per store, resolved at visit-open time."

**Skip if:** User says "No".

### Act 7: Account Scoping

**End state:** AsmtTskDefAcct records created — one per scoped account.

**Form:** "Which accounts should receive this activity?"

**Delegate to:** `source/skills/act7-account-scoping/SKILL.md`

**Builder's intent**: "This promo is only in our West region stores. Don't push it to every account — just those 40 locations."

### Act 8: Plan Visits & Attach Activity (REQUIRED)

**End state:** Assessment Tasks created from Activity Definition and attached to visits (existing or newly created).

**Form:** "Do visits already exist for these accounts in the window? [Yes, attach to existing / No, create new / Check first]"

**Delegate to:** `source/skills/act8-plan-and-attach/SKILL.md`

**Builder's intent**: "Now put it on a visit. If a visit already exists for these stores in the window, attach it. If not, create one for the right time frame. This attaching step is where it usually goes wrong."

**Skip if:** User explicitly opts out (not recommended - activity won't be usable without visits).

### Act 9: Verify the Merchandiser Gets the Activity (OPTIONAL)

**End state:** End-to-end verification complete — merchandiser has visit with activity, questions, and store-specific products. Ready to execute in mobile app.

**Form:** "Run verification? [Yes - prove the chain works / No - skip verification]"

**Delegate to:** `source/skills/act9-verification/SKILL.md`

**Builder's intent**: "Prove it. Show me a rep's visit actually carries the promo activity, with its questions and that store's products, inside the window, assigned to them."

**Skip if:** 
- Already verified manually in Salesforce UI
- Confident in Acts 1-8 execution
- Testing in mobile app directly

**Agent Implementation:** When executing this skill, you MUST invoke the atomic sub-skills via their file paths. Do NOT implement the API calls inline.

---

## Data Model Understanding

**Two-Level Question Architecture:**

### Level 1: Template (ATDT) - Generic Questions
- **Act 2 creates**: ATDT + generic AID + ATDTID
- Generic questions define the reusable structure/types activities draw from
- Attached to template via ATDTID
- Reusable across multiple activities

### Level 2: Activity (ATD) - The Concrete Instance
- **Act 3 creates**: ATD only (references template, sets validity window) — **no questions, no links**
- Creating an ATD from a template does NOT copy the template's questions onto it (verified: a fresh ATD has zero activity-level links)

### Level 3: Activity Questions (ATID) - Where Questions Become Real
- **Act 4 creates**: the `AssessmentTaskIndDefinition` (ATID) links — the PRIMARY, enforceable linking step
- Handles **two kinds of questions**:
  - **Generic (reused)** — the AIDs from Act 2's template, linked to the activity here
  - **Activity-specific (new)** — brand-new AIDs created in Act 4 for this one activity (must share the activity's IOU)

### Standard activity (ATD, IsStandardTask = true) - Act 5
- **Act 5 creates** (only for a newly created Visit Spec): a standard `AssessmentTaskDefinition` with `IsStandardTask = true`, bound to the Act 1 Visit Spec, plus its own ATID links to the three KPI questions (`AssessmentKpi` = Facing, PriceSurvey, Distribution)
- The offline product survey resolves this standard activity via the visit's Visit Spec; without it, a new spec's product survey fails

**The Flow:**
```text
Act 2: Template + Generic Questions (via ATDTID)      ← reusable library
       ↓
Act 3: Activity only (from template, validity window) ← no questions yet
       ↓
Act 4: Link questions to activity (via ATID)          ← PRIMARY LINKING STEP
       ├─ reuse generic questions from the template
       └─ (optionally) create + link activity-specific questions
       ↓
Act 5: Standard activity for a NEW Visit Spec         ← Facing/PriceSurvey/Distribution
       (IsStandardTask = true, bound to the Visit Spec; skipped if spec reused)
```

**Key Point:** Act 3 creates the activity container only. **Act 4 is where questions become real on the activity** — reusing the template's generic questions and/or adding activity-specific ones. Template links do NOT auto-flow to the activity. **Act 5** additionally ensures a newly created Visit Spec has its standard activity with the required KPI questions.

---

## What this skill does

Executes Acts 1-9:

**Act 1: Visit Specification**
- User provides name, searches for existing
- If not found: creates with user parameters
- Captures whether the spec was created (new) or reused (`visitSpecIsNew`) — gates Act 5
- Output: Visit Spec ID

**Act 2: Template Configuration + Generic Questions**
- User provides template name, searches for existing
- Creates template with generic question definitions
- **Creates generic AIDs (question structure/types)**
- **Creates ATDTID (links generic questions to template)**
- Template with generic questions is reusable
- Output: Template ID + Generic Question IDs

**Act 3: Activity Definition**
- Creates ATD (activity) from template, bound to the Visit Spec (Act 1)
- Sets the validity window (ValidFrom/ValidTo) and activates it
- **No questions are linked here** — the activity starts empty
- Output: Activity ID

**Act 4: Link Questions to Activity** ✨ **PRIMARY LINKING STEP**
- The activity has no questions until this step; template links do NOT auto-flow
- **Reuse generic questions** — link the AIDs created on the template in Act 2 to the activity
- **Add activity-specific questions (optional)** — create new AIDs unique to this activity (with the activity's IOU), then link them
- User sets DisplayOrder and IsMandatory per link
- Every AID linked must share the activity's `InternalOrganizationUnitId`
- Output: ATID IDs + any new activity-specific Question IDs

**Act 5: Standard Activity (automatic, only for a newly created Visit Spec)**
- Runs **automatically** when `visitSpecIsNew = true` (orchestrator-triggered, never user-requested); skipped when the spec was reused
- Asks the user for the **name** of an existing standard template (`AsmtTskDefTmpl`, `IsStandardTask = true`) and resolves it to an Id
- Creates a standard `AssessmentTaskDefinition` (`IsStandardTask = true`) bound to the Act 1 Visit Spec, **reusing the Act 3 `ValidFrom`/`ValidTo` window**
- Copies the template's KPI questions or creates new ones, then links ≥3 covering `AssessmentKpi` = Facing, PriceSurvey, Distribution
- Output: Standard Activity ID + KPI question IDs (or "skipped")

**Act 6: Enable Assortment-Based Surveying**
- User chooses to enable/disable assortments
- Updates ATD.ShouldIncludeAssortments
- Output: Assortment status

**Act 7: Account Scoping**
- User provides a specific list of accounts (by name or Id)
- Resolves the listed accounts to Ids and confirms each belongs to the activity's IOU
- Creates AsmtTskDefAcct junction records (activity → accounts)
- Output: Scoping count (N accounts scoped)

**Act 8: Plan Visits & Attach Activity (REQUIRED)**
- Checks for existing visits for the scoped accounts in the validity window
- Attaches the activity to existing visits, or creates new visits and attaches
- Creates Assessment Tasks from the Activity Definition
- Output: Visits planned + activity attached count

**Act 9: Verification (Optional)**
- Proves the end-to-end chain: a rep's visit carries the activity, its questions, and store-specific products, inside the window, assigned to them
- Output: Verification result

---

## Interactive Conversational Flow

### Form-Based Experience

Each Act gets its own form, presented one at a time. User fills in the form, the skill executes that Act, then moves to the next Act's form.

```text
🎯 Welcome! Let's set up your Retail Execution activity.

I'll walk you through up to 9 Acts, one at a time. For each Act, I'll show you a 
form with all the information I need. Fill in the blanks, I'll execute that Act, 
show you the result, then we move to the next one together. I won't skip ahead or 
run the rest on autopilot.

Ready? Let's start with Act 1.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 ACT 1: Visit Specification

This creates the visit type that activities will use.

Fill in these details:

┌─────────────────────────────────────────────────────────
│ Visit Spec Name: _________________________________
│                  (e.g., "Store Visit", "Audit Visit")
│
│ Valid From: ____________ (YYYY-MM-DD, e.g. 2026-07-01)
│
│ Valid To:   ____________ (YYYY-MM-DD, e.g. 2027-06-30,
│             or "No end date" for an evergreen spec)
│
│ Duration: _________ (default: 30)
│
│ Duration Type: [Minute / Hour] (default: Minute)
│                (unit for the Duration above — 30 + Minute = 30-minute visit)
│
│ Capture start/end times? [Yes / No] (default: Yes)
│
│ Usage Type: [Retail / Service / Other] (default: Retail)
└─────────────────────────────────────────────────────────

[Submit Act 1]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⏳ Executing Act 1...
   - Searching for existing Visit Spec "Store Visit"...
   
   🔍 Found an existing "Store Visit" spec.
   
   Reuse this or create new?
   [Reuse] / [Create New]

✅ Act 1 Complete: Using Visit Spec "Store Visit".

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 ACT 2: Template Configuration + Generic Questions

This creates a reusable template with generic question definitions.

Fill in these details:

┌─────────────────────────────────────────────────────────
│ TEMPLATE CONFIGURATION
│ ─────────────────────────
│ Template Name: _____________________________________
│                (e.g., "Compliance Template")
│
│ Activity Type:
│   [ ] Event-driven (time-boxed promo, with date range)
│   [ ] Recurring (ongoing, like weekly checks)
│
│ Include specific accounts? [Yes / No] (default: Yes)
│
│ Include assortments? [Yes / No] (default: Yes)
│
│ ─────────────────────────
│ GENERIC QUESTION DEFINITIONS (for template)
│ ─────────────────────────
│ How many generic questions? _____
│
│ ┌─── Generic Question 1 ────────────────────────────
│ │ Name: _______________________________________
│ │ Data Type: [Boolean / Number / Text / Date]
│ │ Assessment Context: [Store / Store and Merchandising Section]
│ └───────────────────────────────────────────────────
│
│ ┌─── Generic Question 2 ────────────────────────────
│ │ Name: _______________________________________
│ │ Data Type: [Boolean / Number / Text / Date]
│ │ Assessment Context: [Store / Store and Merchandising Section]
│ └───────────────────────────────────────────────────
│
│ [+ Add more questions if needed]
└─────────────────────────────────────────────────────────

[Submit Act 2]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⏳ Executing Act 2...
   - Searching for existing template "Compliance Template"...
   ❌ Not found. Creating new template...
   
   - Creating generic question 1: "Display Setup Correct?"... ✅
   - Linking it to the template... ✅
   
   - Creating generic question 2: "Facings Count"... ✅
   - Linking it to the template... ✅
   
✅ Act 2 Complete: Template "Compliance Template" with 2 generic questions.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 ACT 3: Activity Definition

This creates the activity container. Questions are linked in Act 4.

Fill in these details:

┌─────────────────────────────────────────────────────────
│ ACTIVITY DETAILS                                         │
│ ─────────────────                                        │
│ Activity Name: ______________________________________    │
│                (e.g., "Q1 Promotion Compliance")         │
│
│ Date Range (for event-driven):
│   Start Date: ____________ (YYYY-MM-DD, e.g. 2026-03-01)
│   End Date:   ____________ (YYYY-MM-DD, e.g. 2026-03-14)
└─────────────────────────────────────────────────────────

[Submit Act 3]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⏳ Executing Act 3...
   - Creating activity "Q1 Promotion Compliance"... ✅

✅ Act 3 Complete: Activity "Q1 Promotion Compliance" created (no questions yet).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 ACT 4: Link Questions to the Activity (PRIMARY LINKING STEP)

The activity has no questions yet — the template's questions do NOT flow to it
automatically. Two kinds of questions can land here:
  • Generic — reuse the questions from your Act 2 template (shared, reusable)
  • Activity-specific — new questions unique to THIS activity only

┌─────────────────────────────────────────────────────────
│ PART A — REUSE GENERIC QUESTIONS (from the template)     │
│ ─────────────────────────────                            │
│ Template "Compliance Template" has these questions:      │
│   [ ] Display Setup Correct?  (Boolean, Store)           │
│   [ ] Facings Count           (Number, Store & Merch. Section) │
│ Tick the ones to put on this activity, then set:         │
│   Display Order: _____ (1 = first)   Mandatory? [Yes/No] │
│ ─────────────────────────────                            │
│ PART B — ADD ACTIVITY-SPECIFIC QUESTIONS (optional)      │
│ ─────────────────────────────                            │
│ Add questions unique to this activity? [Yes / No]        │
│ If Yes, per question:                                    │
│ ┌─── New Question ──────────────────────────────────┐   │
│ │ Name: _______________________________________     │
│ │ Data Type: [Boolean / Number / Text / Date]      │
│ │ Assessment Context: [Store / Store and Merchandising Section] │
│ │ Display Order: _____   Mandatory? [Yes / No]     │
│ └───────────────────────────────────────────────────┘   │
│ (Created with the activity's IOU so it can be linked.)   │
└─────────────────────────────────────────────────────────

[Submit Act 4]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⏳ Executing Act 4...
   - Linking generic question "Display Setup Correct?" (order 1, mandatory)... ✅
   - Linking generic question "Facings Count" (order 2, optional)... ✅
   - Creating activity-specific question "Product Available?"... ✅
   - Linking it to the activity (order 3, mandatory)... ✅

✅ Act 4 Complete: 3 questions on activity (2 reused from template, 1 activity-specific)!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 ACT 5: Standard Activity (AUTOMATIC — only if the Visit Spec is new)

Fires AUTOMATICALLY when Act 1 created a NEW Visit Spec — the user never asks for
it. A new Visit Spec has no standard activity, so the offline product survey
(Act 9) would fail. Skipped automatically when the Visit Spec was reused.

┌─────────────────────────────────────────────────────────
│ Auto-gate: was the Visit Spec newly created in Act 1?    │
│   • Reused → skip Act 5 (existing spec already has one)  │
│   • New    → auto-create the standard activity below     │
│                                                          │
│ Standard Template — ask by NAME (not Id):                │
│   Standard template name: __________________________     │
│   (resolved to an Id; this Act does NOT create it)       │
│                                                          │
│ Validity window: reuses the Act 3 ValidFrom/ValidTo      │
│                                                          │
│ KPI questions (must cover all three):                    │
│   [ ] Facing      [ ] PriceSurvey     [ ] Distribution  │
│   Copy from the standard template, or create new?        │
│   [ Copy from template / Create new ]                    │
└─────────────────────────────────────────────────────────

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⏳ Executing Act 5...
   - Visit Spec is new → creating the standard activity (IsStandardTask=true)...
   - Bound to Visit Spec "Store Visit"... ✅
   - Linking KPI questions: Facing ✅  PriceSurvey ✅  Distribution ✅
   - Verified all three KPIs present.

✅ Act 5 Complete: Standard activity ready with Facing, PriceSurvey, Distribution.
   (Or, when reused: "✅ Act 5 Skipped: Visit Spec was reused.")

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 ACT 6: Enable Assortments

Enable dynamic, store-specific product surveying?

What this does:
  ✓ Product-level questions repeat for each product
  ✓ Product list determined by store's assortment at visit time
  ✓ Different stores see different products automatically

Example: Store A has 12 products, Store B has 18 products.
         "Facings Count" question appears 12 times for Store A,
         18 times for Store B.

┌─────────────────────────────────────────────────────────
│ Enable assortment-based product surveying?               │
│
│   [ ] Yes - Enable dynamic product lists                 │
│   [ ] No  - Keep questions fixed (no per-product repeat) │
└─────────────────────────────────────────────────────────

[Submit Act 6]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⏳ Executing Act 6...
   - Updating activity to enable assortments...
   
✅ Act 6 Complete: Assortments enabled!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 ACT 7: Account Scoping

Scope this activity to a specific set of stores.

┌─────────────────────────────────────────────────────────
│ Which accounts should receive this activity?             │
│
│   List them (by name or Id):                             │
│   Accounts: _____________________________________        │
│             (e.g., "Store 101, Store 102, Store 103"     │
│              or their 001… Ids)                          │
└─────────────────────────────────────────────────────────

[Submit Act 7]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⏳ Executing Act 7...
   - Resolving the accounts you listed to their Ids...
   - Confirming each belongs to the activity's org unit... ✅
   - Scoping the activity to those accounts... ✅

✅ Act 7 Complete: Activity scoped to 3 stores (Store 101, 102, 103).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 ACT 8: Plan Visits & Attach Activity (REQUIRED)

Put the activity on visits. If visits already exist for these stores in the
window, attach to them; otherwise create new ones.

┌─────────────────────────────────────────────────────────
│ Do visits already exist for these accounts in the window?│
│
│   [ ] Yes — attach the activity to existing visits       │
│   [ ] No  — create new visits, then attach               │
│   [ ] Check first — look, then decide                    │
│
│ If creating new visits:                                  │
│   Visit date(s): ____________ (within 2026-03-01…03-14)  │
└─────────────────────────────────────────────────────────

[Submit Act 8]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⏳ Executing Act 8...
   - Checking for existing visits for the 3 stores in the window...
   - Found 1 existing visit; creating 2 new ones... ✅
   - Attaching the activity (Assessment Tasks) to all 3 visits... ✅

✅ Act 8 Complete: Activity attached to 3 visits.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 ACT 9: Verify the Merchandiser Gets the Activity (Optional)

Prove the whole chain works end-to-end before reps hit the field.

┌─────────────────────────────────────────────────────────
│ Run verification?                                        │
│
│   [ ] Yes — prove the chain works                        │
│   [ ] No  — skip (already verified / testing in mobile)  │
└─────────────────────────────────────────────────────────

[Submit Act 9]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⏳ Executing Act 9...
   - Picking a sample rep and their visit...
   - Confirming the visit carries the activity... ✅
   - Confirming the activity's questions are present... ✅
   - Confirming store-specific products resolve from the assortment... ✅
   - Confirming the visit falls inside the window and is assigned... ✅

✅ Act 9 Complete: Verified — the rep's visit carries the activity, its
   questions, and that store's products, inside the window.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎉 ALL ACTS COMPLETE!

Your Retail Execution activity is ready:

┌─────────────────────────────────────────────────────────
│ Activity: Q1 Promotion Compliance                        │
│
│ Configuration:                                           │
│   • Visit Spec: Store Visit                              │
│   • Template: Compliance Template                        │
│   • Date Range: 2026-03-01 to 2026-03-14                │
│   • Questions: 2 (1 mandatory)                           │
│   • Standard activity: created (Facing/PriceSurvey/Distribution) │
│   • Assortments: Enabled                                 │
│   • Scoping: 3 stores (Store 101, 102, 103)              │
│   • Visits: attached to 3 visits                         │
│   • Verified: Yes                                        │
│
│ Questions:                                               │
│   1. Display Setup Correct? (mandatory, Store context)   │
│   2. Facings Count (optional, Store and Merch. Section)  │
└─────────────────────────────────────────────────────────

Ready for use in Retail Execution mobile app! ✅
```

> **Note:** The summary refers to records by their human names only. Raw record IDs are tracked internally (see "Never print session state" in Key Rules) — do not surface them in the completion message.

---

## Agent Implementation: How to Execute the Orchestrator

**CRITICAL:** This skill is an ORCHESTRATOR. Do NOT implement API calls inline. Instead, delegate to atomic sub-skills.

### Execution Pattern

For each Act:

1. **Present the complete form** - Show ALL blanks for that Act in one message using the box-drawing format above
2. **Wait for user to fill all blanks** - User provides all values together
3. **Parse the response** - Extract all field values from the user's response
4. **Invoke the atomic sub-skill** - Call the appropriate Act sub-skill file with gathered parameters
5. **Capture outputs** - Save visitSpecId, templateId, activityId, etc. from the sub-skill response **into internal state only** — do not print them
6. **Show completion status** - Display a short plain-language success message that names records by their human name (e.g., "✅ Act 3 done — *Q1 Promotion Compliance* is live"). **Never** include raw record IDs or the `actN_complete` flag (see Key Rule 7)

### How to Invoke Atomic Sub-Skills

Use the Read tool to load each atomic skill, then execute it. **Use repository-relative paths** — resolved against this orchestrator skill's own directory (`.../retail-execution/visit-and-activity-setup/`).

```python
# Example for Act 1 — path relative to this skill's directory
Read('source/skills/act1-visit-specification/SKILL.md')
# Parse the skill instructions
# Execute the API calls as specified in that skill
# Return visitSpecId and visitSpecIsNew

# Example for Act 2
Read('source/skills/act2-template-and-questions/SKILL.md')
# Execute with visitSpecId from Act 1
# Return templateId, questionIds

# And so on for Acts 3-9 (source/skills/act<N>-.../SKILL.md)
```

**DO NOT** re-implement the API calls in this orchestrator. Each atomic skill contains the correct API endpoints, field names, and logic. The per-act forms to present are shown in the "Interactive Conversational Flow" section above.

### Key Rules

1. **Never ask one field at a time** - Always present the complete form for an Act
2. **Use AskUserQuestion tool** - Present form as question text with options where applicable
3. **Parse grouped responses** - User will provide all values together, extract each field
4. **Validate before executing** - Check all required fields are provided
5. **Show visual progress** - Use the box-drawing format from the examples above
6. **Always go step-by-step — never offer to "run straight through"** - Run exactly one Act per turn, then STOP. Present that Act's form, execute it after the user submits, show the result, and wait for the user before starting the next Act. Do **not** auto-apply the form defaults on the user's behalf: defaults are *pre-filled suggestions in the form* the user still confirms or overrides. The `actN_complete` gate (see each sub-skill's "Session state to track & handoff") is the checkpoint — advance to Act N+1 only after the user has reviewed Act N's result.
7. **Never print session state to the user** - The `actN_complete` flags, handoff variables, and raw record IDs (visitSpecId, templateId, activityId, ATID/ATDTID ids, etc.) are **internal orchestration bookkeeping**. Track them silently across Acts; do **not** echo the state YAML, variable names, gate flags, or ID lists into the conversation. When an Act completes, confirm it to the user in **plain language** ("✅ Act 3 done — your activity is created and live"), not with a record-ID dump. Reference records by their human name ("the *Q1 Promotion Compliance* activity"), never by their raw Id.

---

## Data Flow Diagram

```text
Act 1: Create Visit Spec
       └─ Output: visitSpecId, visitSpecIsNew (created vs reused)

Act 2: Create Template + Questions
       ├─ Create ATDT (template) ← configuration
       │  └─ Output: templateId
       │
       ├─ Create AIDs (questions) ← attached to template
       │  └─ Output: questionIds[]
       │
       └─ Create ATDTIDs (junction) ← links AIDs to ATDT
          └─ Output: atdtidIds[]

Act 3: Create Activity
       └─ Create ATD (activity) ← references templateId, inherits questions
          └─ Output: activityId

Act 4: Link Template Questions to Activity (PRIMARY LINKING STEP)
       └─ Create ATIDs (junction) ← links template's AIDs to ATD
          ├─ Sets DisplayOrder per activity
          ├─ Sets IsMandatory per activity
          └─ Output: atidIds[]

Act 5: Standard Activity (AUTO — only if visitSpecIsNew = true)
       ├─ Ask for standard ATDT by NAME (IsStandardTask = true) → resolve Id
       ├─ Create standard ATD (IsStandardTask = true) ← bound to visitSpecId,
       │    reuses Act 3 ValidFrom/ValidTo
       └─ Link ≥3 KPI questions (AssessmentKpi: Facing, PriceSurvey, Distribution)
          └─ Output: standardActivityId, standardKpiQuestions[]  (or: skipped)

Act 6: Enable Assortments
       └─ Update ATD.ShouldIncludeAssortments

Act 7: Account Scoping
       └─ Create AsmtTskDefAcct (junction) ← links activity to specific accounts
          └─ Output: scoping count (N accounts)

Act 8: Plan Visits & Attach Activity (REQUIRED)
       ├─ Check/create visits for scoped accounts in the window
       └─ Create Assessment Tasks from ATD ← attach activity to visits
          └─ Output: visits planned + activity attached

Act 9: Verification (Optional)
       └─ Prove the chain: visit carries activity, questions, store products,
          in window, assigned to a rep
          └─ Output: verification result
```

---

## Key Corrections

### Architecture Summary

```text
Act 2: Create template (ATDT) + questions (AID) + template-question links (ATDTID)
Act 3: Create activity (ATD) - references template
Act 4: Link template questions to activity (ATID) - PRIMARY LINKING STEP
Act 5: Standard activity (ATD, IsStandardTask=true) for a NEW Visit Spec - Facing/PriceSurvey/Distribution
```

---

## Example Conversational Session

```text
🤖 Let's set up your Retail Execution activity.

📋 ACT 1: Visit Specification
Q: Visit Spec name?
A: Compliance Visit

Q: Found existing "Compliance Visit". Reuse?
A: Yes

✅ Visit Spec "Compliance Visit" ready. (reused — Act 5 will be skipped)

📋 ACT 2: Template Configuration
Q: Template name?
A: Standard Compliance Template

Q: Found existing. Reuse?
A: Yes

✅ Template "Standard Compliance Template" ready (event-driven).

📋 ACT 3: Activity Definition
Q: Activity name?
A: March Planogram Compliance

Q: Start date?
A: 2026-03-01

Q: End date?
A: 2026-03-31

✅ Activity "March Planogram Compliance" created (no questions yet).

📋 ACT 4: Link Questions to the Activity (PRIMARY LINKING STEP)

🔸 Your template "Standard Compliance Template" carries 2 generic questions.
   These aren't on the activity yet — let's link the ones you want, and add
   any questions unique to this activity.

Q: Which template (generic) questions should appear on this activity?
   [1] Display Setup Correct?  (Boolean, Store)
   [2] Number of Facings       (Number, Store and Merchandising Section)
A: Both

--- Generic question 1: Display Setup Correct? ---
Q: Display order? (1 = first)
A: 1
Q: Mandatory? [Yes/No]
A: Yes
✅ Linked template question "Display Setup Correct?" to the activity (order 1, mandatory).

--- Generic question 2: Number of Facings ---
Q: Display order?
A: 2
Q: Mandatory?
A: No
✅ Linked template question "Number of Facings" to the activity (order 2, optional).

Q: Add any activity-specific questions — ones that apply only to THIS activity,
   not the shared template? [Yes/No]
A: Yes

Q: How many?
A: 1

--- Activity-specific question 1 ---
Q: Name?
A: Price Correct?
Q: Data type? [Boolean/Number/Text/Date/Picklist]
A: Boolean
Q: Context? [Store / Store and Merchandising Section]
A: Store and Merchandising Section
Q: Display order?
A: 3
Q: Mandatory? [Yes/No]
A: Yes
✅ Created activity-specific question "Price Correct?" and linked it (order 3, mandatory).

✅ Questions on activity: 3 (2 reused from template, 1 activity-specific).

📋 ACT 5: Standard Activity (AUTOMATIC — only if the Visit Spec is new)
(No prompt — the orchestrator auto-evaluates visitSpecIsNew; the user is not asked.)
Auto-gate: The Visit Spec was reused in Act 1 → Act 5 does not run.

✅ Act 5 skipped (Visit Spec was reused).
   [If the Visit Spec had been newly created, Act 5 would run automatically: ask
    for a standard template by NAME (IsStandardTask=true), then build a standard
    activity (reusing the Act 3 ValidFrom/ValidTo window) with the Facing,
    PriceSurvey, and Distribution KPI questions.]

📋 ACT 6: Enable Assortments
Q: Enable assortment-based product surveying?
A: Yes

✅ Assortments enabled.

📋 ACT 7: Account Scoping
Q: Which stores should receive this activity? (by name or Id)
A: Store 101, Store 102, Store 103

✅ Scoped to 3 stores (Store 101, 102, 103).

📋 ACT 8: Plan Visits & Attach Activity (REQUIRED)
Q: Do visits already exist for these stores in the window?
   [Yes, attach to existing / No, create new / Check first]
A: Check first

🔍 Found 1 existing visit; 2 stores have none in the window.
Q: Create the missing 2 visits and attach to all 3?
A: Yes

✅ Activity attached to 3 visits (1 existing, 2 newly created).

📋 ACT 9: Verify the Merchandiser Gets the Activity (Optional)
Q: Run verification? [Yes / No]
A: Yes

✅ Verified — a rep's visit carries the activity, its questions, and that
   store's products, inside the window, assigned to them.

🎉 Complete! Activity "March Planogram Compliance" is ready:
  - Visit Spec: Compliance Visit
  - Questions: 3 (2 mandatory)
  - Date range: 2026-03-01 to 2026-03-31
  - Assortments: Enabled
  - Scoping: 3 stores (Store 101, 102, 103)
  - Visits: attached to 3 visits
  - Verified: Yes
```

---

## Agent Guidance

### State Management

> **Internal only — never print this to the user** (see Key Rule 7). This is the bookkeeping the orchestrator carries across Acts to drive the `actN_complete` gates and pass IDs between sub-skills. It is not conversation output.

```yaml
state:
  act1:
    visitSpecId: ""
    visitSpecName: ""
    visitSpecIsNew: false  # true when Act 1 CREATED the spec; gates Act 5
  act2:
    templateId: ""
    templateName: ""
    isStandardTask: false
    questions: []  # [{id, name, dataType, context, atdtidId}]
  act3:
    activityId: ""
    activityName: ""
    validFrom: ""
    validTo: ""
  act4:
    links: []  # [{atidId, questionId, displayOrder, isMandatory, source}] source: "generic" | "activity-specific"
    activitySpecificQuestionIds: []  # new AIDs created in Act 4
  act5:                        # AUTOMATIC — runs only when act1.visitSpecIsNew=true
    standardActivityId: ""     # standard AssessmentTaskDefinition (IsStandardTask=true); empty when skipped
    standardAtdtName: ""       # user supplies the template NAME (not Id)
    standardAtdtId: ""         # resolved from standardAtdtName (IsStandardTask=true)
    standardKpiQuestions: []   # [{id, assessmentKPI}] covering Facing, PriceSurvey, Distribution
    # validFrom/validTo reused from act3 (standard activity is time-scoped to the same window)
    skipped: false             # true when visitSpecIsNew=false (spec reused)
  act6:
    assortmentsEnabled: false
  act7:
    scopedAccountIds: []  # accounts scoped
    scopingCount: 0
  act8:
    visitIds: []  # visits planned or reused
    attachedCount: 0
  act9:
    verified: false
```

### Act 2: Template + Questions

```yaml
After creating template:
  Prompt: "How many questions for this template?"
  
  For each question:
    - Create AID (AssessmentIndicatorDefinition)
    - Create ATDTID (AsmtTaskDefTemplateIndDef)
    - Links question to template
  
  state.act2.questions = [...all template questions]
```

### Act 4: Primary Linking Step (two question types)

```yaml
Act 4 links questions to the activity — the PRIMARY, enforceable step.
Handles BOTH generic (reused) and activity-specific (new) questions.

Part A — Generic questions (reuse from template):
  - Query the template's questions via ATDTID (state.act2.questions)
  - Show all available generic questions from the template
  - Ask which to link to this activity
  - For each selected:
    - User sets DisplayOrder + IsMandatory
    - Create ATID (AssessmentTaskIndDefinition), source = "generic"

Part B — Activity-specific questions (new, this activity only):
  - Ask: "Add questions unique to this activity?" [Yes/No]
  - For each: create a new AID (AssessmentIndicatorDefinition) with
    InternalOrganizationUnitId = the activity's IOU (REQUIRED — the link
    fails if the AID's IOU != the activity's IOU), Description is required
    - Capture into state.act4.activitySpecificQuestionIds
    - User sets DisplayOrder + IsMandatory
    - Create ATID, source = "activity-specific"

  state.act4.links = [...all ATIDs created, both sources]
```

**Contrast to convey to the user:** generic = shared across activities, edit-once-propagates; activity-specific = one-off, unique to this activity. Prefer generic unless the question genuinely doesn't belong on the shared template.

### Act 5: Standard Activity (conditional on visitSpecIsNew)

```yaml
Act 5 runs AUTOMATICALLY (orchestrator-triggered, never user-requested) and ONLY
when state.act1.visitSpecIsNew == true. The user does not ask for it.

If visitSpecIsNew == false (spec reused):
  - Skip automatically. Set state.act5.skipped = true. Tell the user in plain language.

If visitSpecIsNew == true (spec created):
  - Ask the user for the NAME of an existing standard template (AsmtTskDefTmpl,
    IsStandardTask=true) and resolve the name to an Id (query WHERE Name=... AND
    IsStandardTask=true). This Act does NOT create the template — STOP with a
    clear message if none exists.
  - Create the standard activity: AssessmentTaskDefinition with
    IsStandardTask = true (the only structural difference from the Act 3 activity),
    AsmtTskDefTmplId = the standard template, VisitSpecId = state.act1.visitSpecId,
    InternalOrganizationUnitId = the Act 1 IOU, and ValidFrom/ValidTo REUSED from
    the Act 3 activity (state.act3.validFrom/validTo) — the standard activity is
    time-scoped to the same window.
    - Capture state.act5.standardActivityId
  - Questions: either copy from the standard template
    (AsmtTaskDefTemplateIndDef → reuse those AIDs) or create new
    AssessmentIndicatorDefinition records with AssessmentKpi set (and
    AssessmentContext = StoreInStore). Then link each via
    AssessmentTaskIndDefinition (field: AssessmentIndDefinitionId).
  - Enforce KPI coverage: the linked set MUST cover AssessmentKpi = Facing,
    PriceSurvey, AND Distribution. If any is missing, create/link the missing
    question(s) before completing.
    - Capture state.act5.standardKpiQuestions
```

**Why Act 5 exists:** the offline app resolves a visit's standard activity through its Visit Spec. A brand-new Visit Spec has none, so the Act 9 product-survey verification fails until this standard activity (with the three KPI questions) exists.

---

## Success Criteria

- ✅ User-provided parameters throughout (no hardcoded values)
- ✅ Existing records searched before creating
- ✅ **Generic questions (AID) created in Act 2 and attached to template (ATDTID)**
- ✅ **Act 3 creates activity only (references template) — no questions/links**
- ✅ **Act 4 creates ATID records** linking generic questions to the activity
- ✅ **Act 4 supports activity-specific questions** — new AIDs created there (with the activity's IOU) and linked
- ✅ Act 4 is the PRIMARY linking step (not optional) — template links do NOT auto-flow
- ✅ **Act 5 creates a standard activity (IsStandardTask=true) for a newly created Visit Spec**, with KPI questions covering Facing, PriceSurvey, and Distribution (skipped when the spec was reused)
- ✅ Every linked AID shares the activity's `InternalOrganizationUnitId`
- ✅ All foreign key references valid
- ✅ Display orders user-controlled per activity

---

## Key Architecture Points

1. **Template (ATDT) contains the questions**
   - Act 2 creates template + questions (AID) + links (ATDTID)
   - Questions are attached to template, reusable across activities

2. **Activity (ATD) references the template**
   - Act 3 creates activity only
   - Activity does NOT inherit the template's questions — a fresh ATD has zero activity-level links (verified)

3. **Act 4 is the PRIMARY linking step — two question types**
   - **Generic (reused):** links Act 2's template questions to the activity
   - **Activity-specific (new):** creates new AIDs unique to this activity (with the activity's IOU) and links them
   - Both become real via the same ATID junction; user sets DisplayOrder and IsMandatory per link
   - This is where questions become active on the activity

4. **Act 5 is the standard-activity step for a NEW Visit Spec**
   - `IsStandardTask = true` is the only structural difference from the Act 3 activity
   - Bound to the Act 1 Visit Spec; carries the Facing/PriceSurvey/Distribution KPI questions the offline product survey requires
   - Skipped when Act 1 reused an existing spec

5. **IOU-match rule**
   - Every linked AID's `InternalOrganizationUnitId` must equal the activity's, or the link is rejected
   - Generic AIDs already match (created under the Act 1 IOU); activity-specific AIDs must be created with that same IOU

6. **Template reusability**
   - Multiple activities can use the same template's generic questions
   - Each activity can have different DisplayOrder and IsMandatory settings, plus its own activity-specific questions
   - Questions stay consistent across activities (defined once in template)

---

This architecture allows template reuse while letting each activity customize question order and mandatory flags!

<!-- skill-validate: ignore-start -->
<!-- codey:operations start -->
## Operations Reference

Operations this skill uses — routing and dependency reference.

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `act1-visit-spec-create` | write | — | `POST /services/data/v67.0/sobjects/VisitSpec` | — |
| `act2-atdt-create` | write | — | `POST /services/data/v67.0/sobjects/AsmtTskDefTmpl` | `act1-visit-spec-create` |
| `act2-aid-create` | write | — | `POST /services/data/v67.0/sobjects/AssessmentIndicatorDefinition` | `act1-visit-spec-create` |
| `act2-atdtid-link` | write | — | `POST /services/data/v67.0/sobjects/AsmtTaskDefTemplateIndDef` | `act2-atdt-create`, `act2-aid-create` |
| `act3-atd-create` | write | — | `POST /services/data/v67.0/sobjects/AssessmentTaskDefinition` | `act1-visit-spec-create`, `act2-atdt-create` |
| `act4-atid-link` | write | — | `POST /services/data/v67.0/sobjects/AssessmentTaskIndDefinition` | `act3-atd-create`, `act2-aid-create` |
| `act5-standard-activity-create` | write | — | `POST /services/data/v67.0/sobjects/AssessmentTaskDefinition` | `act1-visit-spec-create`, `act3-atd-create` |
| `act5-assortments-toggle` | write | — | `PATCH /services/data/v67.0/sobjects/AssessmentTaskDefinition/{Id}` | `act3-atd-create` |
| `act6-account-scope-bulk` | write | — | `POST /services/data/v67.0/composite/sobjects` | `act3-atd-create` |
| `act7-prepare-tasks` | write | — | `POST /services/data/v67.0/connect/industries/retail/prepare-assessment-task` | `act3-atd-create`, `act6-account-scope-bulk` |
| `act7-verify-tasks` | write | — | `POST /services/data/v67.0/connect/industries/visit/assessment-task-visit-planning/visits` | `act7-prepare-tasks` |
| `act8-store-check` | verify | — | `GET /services/data/v67.0/connect/industries/retail/visit-execution/store-check` | `act7-verify-tasks` |
| `act8-product-survey` | verify | — | `GET /services/data/v67.0/connect/industries/retail/visit-execution/product-survey` | `act7-verify-tasks` |
| `delegate-visit-and-activity-setup-act1-visit-specification` | delegate | — | → `retail-execution/visit-and-activity-setup-act1-visit-specification` | — |
| `delegate-visit-and-activity-setup-act2-template-and-questions` | delegate | — | → `retail-execution/visit-and-activity-setup-act2-template-and-questions` | — |
| `delegate-visit-and-activity-setup-act3-activity-definition` | delegate | — | → `retail-execution/visit-and-activity-setup-act3-activity-definition` | — |
| `delegate-visit-and-activity-setup-act4-add-questions` | delegate | — | → `retail-execution/visit-and-activity-setup-act4-add-questions` | — |
| `delegate-visit-and-activity-setup-act5-standard-activity` | delegate | — | → `retail-execution/visit-and-activity-setup-act5-standard-activity` | — |
| `delegate-visit-and-activity-setup-act6-assortment-based` | delegate | — | → `retail-execution/visit-and-activity-setup-act6-assortment-based` | — |
| `delegate-visit-and-activity-setup-act7-account-scoping` | delegate | — | → `retail-execution/visit-and-activity-setup-act7-account-scoping` | — |
| `delegate-visit-and-activity-setup-act8-plan-and-attach` | delegate | — | → `retail-execution/visit-and-activity-setup-act8-plan-and-attach` | — |
| `delegate-visit-and-activity-setup-act9-verification` | delegate | — | → `retail-execution/visit-and-activity-setup-act9-verification` | — |
<!-- codey:operations end -->
<!-- skill-validate: ignore-end -->
