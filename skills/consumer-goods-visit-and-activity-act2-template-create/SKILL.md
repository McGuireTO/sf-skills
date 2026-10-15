---
name: consumer-goods-visit-and-activity-act2-template-create
description: "Act 2 of 9: Set up questions and the activity template for Retail Execution. Creates one or more Assessment Indicator Definitions (reusable questions — the user chooses how many, and per question picks the AssessmentContext: \"Store\" or \"Store and Merchandising Section\") and one non-standard Activity Template (AsmtTskDefTmpl) with IsStandardTask=false to mark activities as event-driven, time-boxed rather than recurring standard tasks. Depends on Act 1 (a valid Visit Specification and InternalOrganizationUnitId must exist). DataType is immutable after creation — validate before creating. Template settings (ShouldIncludeAssortments, ShouldIncludeSpecAcct, UsageType, IsStandardTask) cascade to activities created from it in Act 3."
metadata:
  version: "1.0"
  cliTools:
  - tool:
    - "sf"
    semver: ">=2.0.0"
---

# Act 2: Set Up Questions and Activity Template

**Part of:** [9-Act Retail Execution Steel Thread](../../README.md)  
**Depends on:** [Act 1 - Visit Specification Setup](../act1-visit-specification/SKILL.md)  
**Enables:** [Act 3 - Activity Definition](../act3-activity-definition/SKILL.md)

**Act 2 builds the reusable assessment framework the activity in Act 3 is created from. You MUST complete Act 1 (a valid Visit Specification and InternalOrganizationUnitId exist) before starting this act.**

---

## Goal

Create the reusable question infrastructure for Retail Execution activities: **Assessment Indicator Definitions** (questions) and a **non-standard activity template** that marks activities as event-driven rather than recurring standard tasks.

**Builder's intent:** "I want reusable questions and a template that marks an activity as one-off, event-driven rather than a recurring standard task."

**What you'll create:**
1. One or more Assessment Indicator Definitions (questions)
2. One non-standard Activity Template
3. Links between template and questions

---

## What this Act does

The activity in Act 3 is instantiated from a template and carries questions. This Act builds both, so Act 3 has something to reference. It:

1. **Creates the Assessment Indicator Definitions (AIDs)** — reusable questions. **Ask the user how many questions they need and for each one's name, DataType, and AssessmentContext** — the walkthrough below uses two (a `Boolean` "Display Up?" and a `Number` "Facings Count") purely as a worked example; create as many (or as few) as the user wants by repeating Steps 1-2. Each AID requires a `Description` (a mandatory field on the object). **For `Picklist` / `Multi-Select Picklist` questions, also creates the choice records (`AssessmentIndDefinedValue`)** — one per option the user lists (Step 2b).
2. **Creates the non-standard Activity Template (AsmtTskDefTmpl)** — with `IsStandardTask = false` (the event-driven/time-boxed marker), plus `IsActive = true`, `ShouldIncludeAssortments = true`, `ShouldIncludeSpecAcct = true`, and `UsageType = "Retail"`.
3. **Links the indicators to the template (AsmtTaskDefTemplateIndDef)** — required *if* questions were created in step 1 (one link per question); skip entirely if no questions were specified. When present, this defines the template's generic question set. Activity-level links in Act 4 are the enforceable per-activity contract (template links do NOT auto-flow to activities).
4. **Verifies** every AID created is `IsActive = true`, the template carries `IsStandardTask = false`, and the template settings that cascade to activities are set correctly.

Template settings (`IsStandardTask`, `ShouldIncludeAssortments`, `ShouldIncludeSpecAcct`, `UsageType`) **cascade to activities created from it in Act 3**. `DataType` on the indicators is **immutable after creation** (`AssessmentContext` can be changed later, but pick it deliberately) — validate before creating.

---

## When to use

**Invoke this skill when:**
- You've completed Act 1 (Visit Specification exists)
- You need to create questions for store visits or product assessments
- You're setting up an event-driven (non-recurring) activity template
- The user asks about "assessment indicators", "questions", "activity templates", or "non-standard tasks"

**Trigger phrases:**
- "Create questions for retail execution"
- "Set up assessment indicators"
- "Make a non-standard activity template"
- "Configure event-driven activity template"
- "Act 2" or "template and questions setup"

---

## Prerequisites

Before starting this Act, ensure:

1. **Act 1 Complete:**
   - Visit Specification created with Id (e.g., `0o7xx0000000001EAA`)
   - InternalOrganizationUnitId known (e.g., `0gJxx0000000001EAA`)

2. **Object Permissions:**

   Check user has Create permissions for required objects:

   ```sql
   SELECT Parent.Name, Parent.Profile.Name, SobjectType, 
          PermissionsRead, PermissionsCreate, PermissionsEdit 
   FROM ObjectPermissions 
   WHERE SobjectType IN ('AssessmentIndicatorDefinition', 'AsmtTskDefTmpl', 'AsmtTaskDefTemplateIndDef')
     AND PermissionsCreate = true
   ```

   All three objects must have `PermissionsCreate = true` for the user's profile/permission set.

   **If any question is a `Picklist` (`DataType`), you also need Create on `AssessmentIndDefinedValue`** — the picklist values are stored as child `AssessmentIndDefinedValue` records, not on the AID itself. Include it in the check only when a picklist-type question is in scope:

   ```sql
   SELECT Parent.Name, Parent.Profile.Name, SobjectType, 
          PermissionsRead, PermissionsCreate, PermissionsEdit 
   FROM ObjectPermissions 
   WHERE SobjectType = 'AssessmentIndDefinedValue'
     AND PermissionsCreate = true
   ```

   `AssessmentIndDefinedValue` must return `PermissionsCreate = true` before you create any picklist question, or the value-population step will fail.

3. **Retail Execution feature enabled:** Setup → Feature Settings → Retail Execution, and API version v54.0 or later (examples use v68.0).

---

## Inputs

| Variable | Description | Source | Example |
|---|---|---|---|
| `ORG_ALIAS` | Target org alias for `sf` CLI commands | Auth session | `my-re-org` |
| `INTERNAL_ORG_UNIT_ID` | Internal Organization Unit that scopes the indicators and template | Act 1 | `0gJxx0000000001EAA` |
| `DEFAULT_ACTIVITY_DRTN` | Default activity length (numeric), read together with `ACTIVITY_DURATION_TYPE` | User | `30` |
| `ACTIVITY_DURATION_TYPE` | Unit for the duration — `Minute` or `Hour` | User (default `Minute`) | `Minute` |
| `DISPLAY_ORDER` | Sort position of the template in the Activity list (integer) | User (default `1`) | `1` |

```bash
INTERNAL_ORG_UNIT_ID="0gJxx0000000001EAA"  # From Act 1
DEFAULT_ACTIVITY_DRTN=30                    # numeric value
ACTIVITY_DURATION_TYPE="Minute"            # "Minute" or "Hour"
DISPLAY_ORDER=1                            # template sort position
```

### Key Concepts (reference before executing)

**Number of questions is up to the user.** This Act creates one AID per question. The steps below walk through two as an example, but there is no fixed count — ask the user how many questions they want, then repeat the create-a-question step once per question.

**Assessment Indicator Definitions (AIDs)** — questions reusable across multiple activities. Two critical fields:

- **AssessmentContext**: Determines granularity. Two choices to offer the user (API value → what it means):
  - `"Store"` (UI label "Store"): Visit-level questions, answered once per visit (e.g., "Display Up?", "Facings Count").
  - `"StoreInStore"` (UI label "Store and Merchandising Section"): Questions answered at both the store level and per merchandising section within the store.
  - (A third value, `"InStore"` / "Merchandising Section", exists but is out of scope for this steel thread.)
- **DataType**: `Boolean`, `String`, `Number`, `DateTime`, `Percentage`, `Decimal`, `Currency`, `Picklist`, `Multi-Select Picklist`. **Immutable after creation** — pick the right one up front.

**Ask the user which context each question uses — "Store" or "Store and Merchandising Section".** `AssessmentContext` can be changed after creation, but choose it deliberately; `DataType` cannot.

**Activity Template (AsmtTskDefTmpl)** — a reusable blueprint for creating activities. `IsStandardTask` is the classification pivot:

- **IsStandardTask = true**: Recurring, scheduled tasks (e.g., weekly shelf checks)
- **IsStandardTask = false**: **Event-driven, time-boxed activities** (our use case)

Other critical fields:
- `ShouldIncludeAssortments`: `true` enables assortment-based product surveys
- `ShouldIncludeSpecAcct`: `true` enables account scoping (which stores)
- `UsageType`: `"Retail"` for Retail Execution context
- **DefaultActivityDrtn + ActivityDurationType**: Set the default activity length (e.g., `30` + `"Minute"`). Interpreted together — `DefaultActivityDrtn` is the numeric value and `ActivityDurationType` is the unit it's read in:
  - `ActivityDurationType = "Minute"` → `DefaultActivityDrtn = 30` means 30 minutes.
  - `ActivityDurationType = "Hour"` → `DefaultActivityDrtn = 1` means 1 hour.
  - Set both fields together — a mismatched unit (e.g. `"Hour"` when you meant minutes) yields wildly wrong activity durations. Ask the user for both; default to `Minute` if they don't specify a unit.
- **DisplayOrder**: Integer sort position of the template in the Activity list (default `1`).

**Template-to-Indicator Links (AsmtTaskDefTemplateIndDef)** — junction object linking templates to questions.

---

## Step-by-step procedure

> **First, decide how many questions.** Ask the user how many questions the activity needs, and for each: a name, a DataType (`Boolean`, `String`, `Number`, `DateTime`, `Percentage`, `Decimal`, `Currency`, `Picklist`, `Multi-Select Picklist`), and an AssessmentContext — **"Store"** or **"Store and Merchandising Section"**. **For any `Picklist` / `Multi-Select Picklist` question, also ask for its list of choices** — those become `AssessmentIndDefinedValue` records in Step 2b. Then run the create-a-question step (below) once per question. Steps 1 and 2 show two questions as a worked example — create exactly as many as the user asked for.

### Step 1: Create the First Store-Level Question

Create the "Display Up?" boolean question (visit-level) — example of the first question.

**API Call:**
```http
POST /services/data/v68.0/sobjects/AssessmentIndicatorDefinition
Content-Type: application/json

{
  "Name": "Display Up?",
  "Description": "Is the promotional display set up correctly?",
  "DataType": "Boolean",
  "IsActive": true,
  "AssessmentContext": "Store",
  "InternalOrganizationUnitId": "0gJxx0000000001EAA"
}
```

**Save this value:**
```bash
INDICATOR_ID_1="0l0xx0000000001EAA"
```

**What this creates:** A yes/no question answered once per store visit. Field reps will see this question at the visit level before diving into product-specific tasks.

> `Description` is **required** on `AssessmentIndicatorDefinition` — omitting it returns `REQUIRED_FIELD_MISSING: [Description]`. `AssessmentContext` here is `"Store"` (label "Store"); use `"StoreInStore"` (label "Store and Merchandising Section") if the user chose that for this question.

**Expected result:** Response returns `"success": true` with an `id`; save it as `INDICATOR_ID_1`.
```json
{
  "id": "0l0xx0000000001EAA",
  "success": true,
  "errors": []
}
```

### Step 2: Create Additional Store-Level Questions (repeat per question)

Repeat this create call once for each remaining question the user wants — capturing each returned id as `INDICATOR_ID_2`, `INDICATOR_ID_3`, … (each with its own `Description`, `DataType`, and `AssessmentContext`). If the user only wants one question, skip this step. The example creates a second question, "Facings Count" (store-level). `Number` is used here only as an example — the DataType is **not mandated**; pick whichever fits the question (`Boolean`, `String`, `Number`, `DateTime`, `Percentage`, `Decimal`, `Currency`, `Picklist`, `Multi-Select Picklist`).

**API Call:**
```http
POST /services/data/v68.0/sobjects/AssessmentIndicatorDefinition
Content-Type: application/json

{
  "Name": "Facings Count",
  "Description": "Number of product facings visible on the shelf.",
  "DataType": "Number",
  "IsActive": true,
  "AssessmentContext": "Store",
  "InternalOrganizationUnitId": "0gJxx0000000001EAA"
}
```

**Save this value:**
```bash
INDICATOR_ID_2="0l0xx0000000002EAA"
```

**What this creates:** A second store-level question answered once per visit. `DataType: "Number"` makes "Facings Count" a numeric field, but any supported DataType works — choose it to match the question you're asking.

**Expected result:** Response returns `"success": true` with an `id`; save it as `INDICATOR_ID_2`.
```json
{
  "id": "0l0xx0000000002EAA",
  "success": true,
  "errors": []
}
```

### Step 2b: Add Picklist Values (only for `Picklist` / `Multi-Select Picklist` questions)

**Skip this step for every non-picklist question.** For a `Picklist` or `Multi-Select Picklist` question, the AID itself holds no choices — the selectable options live in child `AssessmentIndDefinedValue` records. A picklist question with zero values is unusable (field reps see an empty dropdown), so this step is **required** for those questions.

**Ask the user for the list of choices** for each picklist question (e.g. for a "Shelf Condition" question: `Excellent`, `Good`, `Poor`). Then create one `AssessmentIndDefinedValue` per choice, each pointing at that question's `AssessmentIndicatorDefinition` Id.

**API Call (repeat once per value):**
```http
POST /services/data/v68.0/sobjects/AssessmentIndDefinedValue
Content-Type: application/json

{
  "AssessmentIndicatorDefinitionId": "0l0xx0000000003EAA",
  "Value": "Excellent",
  "SequenceNumber": 1,
  "IsDefault": false
}
```

- `AssessmentIndicatorDefinitionId` → **required.** The `INDICATOR_ID_n` of the picklist question these values belong to.
- `Value` → **required.** The choice as shown to the field rep (this is the label field — the object has no `Name` field). Create one record per choice the user gave.
- `SequenceNumber` → **required.** The order the choices appear in the dropdown (1, 2, 3, …). (There is no `DisplayOrder` field on this object.)
- `IsDefault` → **required.** `true` for the choice pre-selected by default, `false` otherwise. Set at most one value to `true` per question.

**Expected result:** Each call returns `"success": true` with an `id`. After creating all values, the picklist question has one `AssessmentIndDefinedValue` child per choice.

> The four fields above (`AssessmentIndicatorDefinitionId`, `Value`, `SequenceNumber`, `IsDefault`) are all **required** on create — none can be omitted. Confirm them against the target org with `sf sobject describe --sobject AssessmentIndDefinedValue` before running, as field API names can vary by org/version.

### Step 3: Create Non-Standard Activity Template

Create the event-driven activity template.

**API Call:**
```http
POST /services/data/v68.0/sobjects/AsmtTskDefTmpl
Content-Type: application/json

{
  "Name": "Non-Standard Activity Template",
  "InternalOrganizationUnitId": "0gJxx0000000001EAA",
  "Description": "Template for event-driven, time-boxed activities",
  "DisplayOrder": 1,
  "IsActive": true,
  "IsStandardTask": false,
  "ShouldIncludeSpecAcct": true,
  "ShouldIncludeAssortments": true,
  "UsageType": "Retail",
  "DefaultActivityDrtn": 30,
  "ActivityDurationType": "Minute"
}
```

**Save this value:**
```bash
ACTIVITY_TEMPLATE_ID="0oBxx0000000001EAA"
```

**Critical fields explained:**
- `IsStandardTask: false` → Activities created from this template are **event-driven** (one-off, time-boxed)
- `ShouldIncludeAssortments: true` → Activities can reference product lists
- `ShouldIncludeSpecAcct: true` → Activities can be scoped to specific accounts (stores)
- `UsageType: "Retail"` → Template appears in Retail Execution context
- `DefaultActivityDrtn: 30` + `ActivityDurationType: "Minute"` → Default activity length, read as a pair. Use the user's values (`DEFAULT_ACTIVITY_DRTN` / `ACTIVITY_DURATION_TYPE`); `ActivityDurationType` is `"Minute"` or `"Hour"`, defaulting to `Minute`.
- `DisplayOrder: 1` → Sort position of the template in the Activity list (use `DISPLAY_ORDER`)

**Expected result:** Response returns `"success": true` with an `id`; save it as `ACTIVITY_TEMPLATE_ID`.
```json
{
  "id": "0oBxx0000000001EAA",
  "success": true,
  "errors": []
}
```

### Step 4: Link Indicators to Template (only if questions were created)

**Skip this step entirely if you created no questions in Steps 1-2** — a template with no generic questions is valid (Act 4 can still add activity-specific questions directly to the activity).

If you did create questions, they are the *generic* questions for this template, and they only belong to the template once linked — create **one `AsmtTaskDefTemplateIndDef` record per question you created**. (Act 4 later adds the *activity-level* links, which are the enforceable per-activity contract — these template links do NOT auto-flow to activities; the template links here just define the template's generic question set that Act 4 reuses.) The two calls below correspond to the two example questions; add one call per additional question.

**Link Store Indicator:**
```http
POST /services/data/v68.0/sobjects/AsmtTaskDefTemplateIndDef
Content-Type: application/json

{
  "AsmtTskDefTmplId": "0oBxx0000000001EAA",
  "AssessmentIndDefId": "0l0xx0000000001EAA"
}
```

**Link Store Numeric Indicator:**
```http
POST /services/data/v68.0/sobjects/AsmtTaskDefTemplateIndDef
Content-Type: application/json

{
  "AsmtTskDefTmplId": "0oBxx0000000001EAA",
  "AssessmentIndDefId": "0l0xx0000000002EAA"
}
```

**Note:** These links define the template's generic question set. Activities created from this template still need their own explicit activity-level indicator links (**Act 4**) — those are the enforceable per-activity contract. The template links here do NOT propagate to the activity automatically; Act 4 reuses these generic questions by linking each one to the activity.

**Expected result:** One `AsmtTaskDefTemplateIndDef` record per question created, each returning `"success": true` (the worked example creates two). If no questions were created, there are no links — that's expected.

---

## Validation

Confirm successful setup with these checks.

### 1. Query Assessment Indicator Definitions

Skip this check if you created no questions. Otherwise, query the questions you created by the Ids captured in Steps 1-2 (`INDICATOR_ID_1`, `INDICATOR_ID_2`, …):

```bash
# All questions created in this Act, by their captured Ids
sf data query \
  --query "SELECT Id FROM AssessmentIndicatorDefinition WHERE Id IN ('$INDICATOR_ID_1','$INDICATOR_ID_2')" \
  --target-org <org-alias>
```

**Expected:** Every question you created comes back — one `Id` row per question.

### 2. Query Activity Template

```bash
sf data query \
  --query "SELECT Id FROM AsmtTskDefTmpl WHERE Id = '$ACTIVITY_TEMPLATE_ID'" \
  --target-org <org-alias>
```

**Expected:** Exactly one `Id` row — the template exists.

### 3. Verify Template-Indicator Links

Skip this check if you created no questions (there are no links to verify). Otherwise:

```bash
sf data query \
  --query "SELECT Id FROM AsmtTaskDefTemplateIndDef WHERE AsmtTskDefTmplId = '$ACTIVITY_TEMPLATE_ID'" \
  --target-org <org-alias>
```

**Expected:** One record per question you linked (in the worked example, two).

### Success Criteria

- ✓ One `AssessmentIndicatorDefinition` record exists per question the user asked for (the worked example creates two — "Display Up?" Boolean and "Facings Count" Number)
- ✓ One `AsmtTskDefTmpl` record exists ("Non-Standard Activity Template")
- ✓ `IsStandardTask = false` on the template
- ✓ Every indicator active (`IsActive = true`)
- ✓ Template active (`IsActive = true`)
- ✓ Template settings enable assortments and account scoping (`ShouldIncludeAssortments = true`, `ShouldIncludeSpecAcct = true`, `UsageType = "Retail"`)
- ✓ One `AsmtTaskDefTemplateIndDef` link exists per question created (Step 4 — required only if questions were created; none needed if no questions were specified)

---

## End state

After completing Act 2:

- ✅ **Assessment Indicator Definitions exist** — as many as the user asked for (possibly none), each `IsActive = true`. The worked example creates two: "Display Up?" (`Boolean`, Store context) and "Facings Count" (`Number`, Store context).
- ✅ **One non-standard Activity Template exists** — `IsStandardTask = false`, `ShouldIncludeAssortments = true`, `ShouldIncludeSpecAcct = true`, `UsageType = "Retail"`, `IsActive = true`.
- ✅ **Template-indicator links exist for each question created** — one `AsmtTaskDefTemplateIndDef` record per question (Step 4); if no questions were created, the template simply carries no generic question set (valid — Act 4 can add activity-specific questions later).
- ✅ **The template Id and every indicator Id are captured** and ready for Act 3.

**At this point:**
- Act 2 only builds the reusable blueprint (template) and question library.
- No concrete activity exists yet — that happens in Act 3.
- Questions are not yet enforceably attached to an activity — that happens in Act 4 (activity-level links).

**You are NOT done with the full setup** — this is Act 2 of 9. Proceed to Act 3 (Activity Definition) to create the concrete, time-boxed activity from this template.

---

## Gotchas and common errors

### 1. "Template not appearing in Activity creation UI"

**Symptom:** Template created successfully but doesn't show in dropdown.

**Cause:** `IsActive: false` or `UsageType` mismatch.

**Fix:**
```bash
# Update template to active
sf data update record \
  --sobject AsmtTskDefTmpl \
  --record-id "$ACTIVITY_TEMPLATE_ID" \
  --values "IsActive=true UsageType=Retail" \
  --target-org <org-alias>
```

### 2. DataType is Immutable (AssessmentContext is not)

**Symptom:** Need to change `DataType` after creation.

**Cause:** `DataType` is **not updateable** after indicator creation — a PATCH returns `INVALID_FIELD_FOR_INSERT_UPDATE: [DataType]`. (`AssessmentContext`, by contrast, *can* be updated after creation — but still choose it deliberately.)

**Fix:** Create a new indicator with the correct `DataType`:
```json
{
  "Name": "Updated Question Name",
  "Description": "Corrected question.",
  "AssessmentContext": "Store",
  "DataType": "Number"
}
```

Then deactivate the old indicator: `{"IsActive": false}` and update activities to use the new indicator ID.

**Prevention:** Validate `DataType` before creation (it can't be fixed afterward).

---

## Notes: best practices & architecture

**1. AssessmentContext: Ask the user per question**

Two contexts are in scope, and the user chooses per question:
- **"Store"** (API `Store`) — answered once per visit. Use for visit-level observations (e.g., "Store cleanliness rating", "Display up?", "Facings count").
- **"Store and Merchandising Section"** (API `StoreInStore`) — answered at both the store level and per merchandising section within the store. Use when the question needs section-level granularity in addition to the store-level answer.

Pick the context deliberately at creation. It *can* be updated later, but `DataType` cannot — so validate DataType up front.

**2. IsStandardTask=false is the Event-Driven Marker**

Standard tasks (`IsStandardTask=true`):
- Recurring, scheduled (e.g., "Check shelf every Monday")
- Generate visits automatically
- Not time-boxed

Non-standard tasks (`IsStandardTask=false`):
- **Event-driven**, one-off (e.g., "New product launch promotion")
- Manually triggered or time-boxed
- Our use case for the 9-Act flow

Setting `IsStandardTask=false` is how you classify activities as event-driven. This cascades to activities created from this template.

**3. Template Settings Cascade to Activities**

| Template Field | Effect on Activities |
|---|---|
| `ShouldIncludeAssortments: true` | Activities can link to AssessmentTaskOrders (product lists) |
| `ShouldIncludeSpecAcct: true` | Activities can be scoped to specific accounts (stores) |
| `UsageType: "Retail"` | Activities appear in Retail Execution context |
| `IsStandardTask: false` | Activities are event-driven, non-recurring |

Choose template settings carefully. Changing the template doesn't update existing activities.

**4. Indicator Links: Template vs Activity Level**

At template level (Step 4): The generic questions created in this Act only belong to the template once linked — this defines the template's generic question set.

At activity level (Act 4): explicit links required via `AssessmentTaskIndDefinition`, determines which questions appear during the visit. Template links do NOT auto-flow here — Act 4 must link each question to the activity.

Best practice: Define the generic set at the template level here, then in Act 4 reuse them on the activity (plus any activity-specific questions). Activity-level links are the enforceable contract.

**5. Why separate Indicator Definitions from Activities?**

Reusability: The same "Facings Count" question can be used across multiple activities (new product launch, seasonal promo), multiple templates (standard shelf checks, event-driven audits), and multiple internal org units (different regions).

Centralized updates: Change the indicator definition, and all activities referencing it inherit the update (e.g., rename "Facings Count" to "Shelf Facings").

**Template vs Activity Lifecycle**

```text
Template (AsmtTskDefTmpl) → Blueprint
   ↓ (IsStandardTask, ShouldIncludeAssortments, etc.)
Activity (AssessmentTaskDefinition) → Concrete instance
   ↓ (Linked to Visit Spec, Account, Assortment)
Visit (AssessmentTask) → Field execution
```

Act 2 creates the blueprint. Act 3 creates the concrete instance.

---

## Session state to track & handoff

> **Internal only — never print this to the user.** These variables (including `act2_complete`) are orchestration bookkeeping. Track them silently to drive the gate below; do **not** echo raw variable names, IDs, or the gate flag into the conversation. When the Act finishes, tell the user only a short plain-language confirmation (e.g., "✅ Act 2 done — your template and questions are ready").

Pass these forward to Act 3:

- `ACTIVITY_TEMPLATE_ID` — from Step 3. **Required for Act 3** (the activity is created from this template via `AsmtTskDefTmplId`).
- `INDICATOR_ID_1`, `INDICATOR_ID_2`, … — one captured id per question created in Steps 1-2. **Required for Act 4** (activity-level question links reuse these generic questions). Carry forward as many as you created.
- `VISIT_SPEC_ID` — carried from Act 1 (the activity references it via `VisitSpecId`).
- `act2_complete` — boolean; set to `true` after the Validation checks pass.

**Do NOT proceed to Act 3 until `act2_complete = true`.** The activity in Act 3 is created from this template (`AsmtTskDefTmplId`) and references its questions.

You can now create **event-driven activities** from this template (Act 3). The questions are reusable across multiple activities.

---

## Next Act

Proceed to **Act 3: Activity Definition** (`../act3-activity-definition/SKILL.md`). In Act 3, you'll:
1. Create an `AssessmentTaskDefinition` (concrete activity) from this template
2. Link the activity to the Visit Specification (Act 1)
3. Set the validity window and activate the activity

Then **Act 4** links the questions to the activity (mandatory at activity level) — reusing these generic questions and adding any activity-specific ones — before assortment scoping in Act 6.

---

## References

**API Documentation**
- [AssessmentIndicatorDefinition Object](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_assessmentindicatordefinition.htm)
- [AsmtTskDefTmpl Object](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_asmttskdeftmpl.htm)
- [AsmtTaskDefTemplateIndDef Object](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_asmttaskdeftemplateinddef.htm)

**Related Acts**
- [Act 1: Visit Specification Setup](../act1-visit-specification/SKILL.md) ← Prerequisites
- [Act 3: Activity Definition](../act3-activity-definition/SKILL.md) ← Next step
- [9-Act Steel Thread README](../../README.md) ← Full flow
