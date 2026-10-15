---
name: consumer-goods-visit-and-activity-act3-definition-create
description: "Act 3 of 9: Creates an event-driven, time-limited Assessment Task Definition (ATD) from the non-standard template. Sets the validity window (ValidFrom/ValidTo) so the activity auto-expires, references the Visit Specification from Act 1 (VisitSpecId), and inherits the non-standard classification (IsStandardTask=false) from the Act 2 template. Depends on Act 1 (Visit Specification) and Act 2 (Activity Template). Part of the 9-Act Retail Execution steel thread."
metadata:
  version: "1.0"
  cliTools:
  - tool:
    - "sf"
    semver: ">=2.0.0"
---

# Act 3: Define Non-Standard Activity (Assessment Task Definition)

**Part of:** [9-Act Retail Execution Steel Thread](../../README.md)  
**Depends on:** [Act 1 - Visit Specification Setup](../act1-visit-specification/SKILL.md), [Act 2 - Template and Questions](../act2-template-and-questions/SKILL.md)  
**Enables:** [Act 4 - Add Questions](../act4-add-questions/SKILL.md)

**Act 3 creates the concrete activity merchandisers complete during store visits. You MUST complete Act 1 (Visit Specification) and Act 2 (non-standard Activity Template) before starting this act — the activity references both.**

---

## Goal

Create an event-driven, time-limited **Assessment Task Definition** (ATD) from the non-standard template — the actual activity merchandisers will complete during store visits (here, a two-week promotional compliance check).

**Builder's intent:** "We're running a two-week promotion. I need a one-off activity for it, tied to our store-visit type, that only lives for those two weeks."

**What you'll create:**
1. One `AssessmentTaskDefinition` (ATD) — event-driven, validity-window-bound, referencing the Act 1 Visit Spec and Act 2 template

Activities outside the validity window won't be served to field users — the platform automatically enforces temporal boundaries.

---

## What this Act does

1. **Creates the Assessment Task Definition (ATD)** from the non-standard template (`AsmtTskDefTmplId` from Act 2).
2. **Sets the validity window** (`ValidFrom`/`ValidTo`) — the activity auto-expires outside the window.
3. **References the Visit Specification** from Act 1 (`VisitSpecId`) — binds the activity to the visit type.
4. **Classifies as non-standard** (`IsStandardTask = false`, inherited from the template; explicit is safer).
5. **Configures the task type** (`TaskType` — one of the valid picklist values, e.g. `PromotionCheck` for a promo activity, or `Other`) and **activates** the activity (`IsActive = true`).
6. **Verifies** the query returns exactly one record with the expected fields (no duplicates).

---

## When to use

**Invoke this skill when:**
- You've completed Act 1 (Visit Specification) and Act 2 (non-standard template)
- You need a concrete, time-boxed activity for a promotion, seasonal campaign, or one-off audit
- The user asks about "create an activity", "assessment task definition", "event-driven activity", or "promo compliance activity"

**Trigger phrases:**
- "Create the activity"
- "Define the promo compliance activity"
- "Set up an event-driven activity with a date range"
- "Act 3" or "activity definition"

---

## Prerequisites

| Act | Artifact | Required For |
|-----|----------|--------------|
| Act 1 | Visit Specification (VisitSpec) | `VisitSpecId` field — binds activity to visit type |
| Act 2 | Assessment Task Definition Template | `AsmtTskDefTmplId` field — inherits non-standard classification |

**Object permissions** — the running user needs **Create** on `AssessmentTaskDefinition` (the object this Act creates) and **Read** on the two Act 2 objects this Act references: `AsmtTskDefTmpl` (ATDT — read via `AsmtTskDefTmplId`) and `AsmtTaskDefTemplateIndDef` (ATDTID — the template-indicator links). Confirm they're granted through the user's profile or an assigned permission set:

```sql
SELECT Parent.Name, Parent.Profile.Name, SobjectType,
       PermissionsRead, PermissionsCreate, PermissionsEdit
FROM ObjectPermissions
WHERE (SobjectType = 'AssessmentTaskDefinition' AND PermissionsCreate = true)
   OR (SobjectType IN ('AsmtTskDefTmpl', 'AsmtTaskDefTemplateIndDef') AND PermissionsRead = true)
```

Expect three things to hold for the running user's profile or one of their assigned permission sets:
- `AssessmentTaskDefinition` with `PermissionsCreate = true` — without it the user can't create the activity.
- `AsmtTskDefTmpl` with `PermissionsRead = true` — needed to read the template referenced by `AsmtTskDefTmplId`.
- `AsmtTaskDefTemplateIndDef` with `PermissionsRead = true` — needed to read the template-indicator links.

If any of the three is missing, grant the corresponding object permission before proceeding.

---

## Inputs

| Variable | Description | Source | Example |
|---|---|---|---|
| `ORG_ALIAS` | Target org alias for `sf` CLI commands | Auth session | `my-re-org` |
| `VISIT_SPEC_ID` | Visit Specification the activity binds to | Act 1 | `1cbxx0000000001AAA` |
| `ACTIVITY_TEMPLATE_ID` | Non-standard template the activity is created from | Act 2 | `1cDxx0000000001EAA` |
| `INTERNAL_ORG_UNIT_ID` | Internal Org Unit for scoping (must exist) | Setup data | `0gJxx0000000001EAA` |
| `VALID_FROM` / `VALID_TO` | Validity window in ISO date format (`yyyy-MM-dd`) | User | `2026-03-01` / `2026-03-14` |
| `PROMOTION_ID` / `PROMOTION_NAME` | **Promotional activities only** — the Promotion this activity is tied to. Pass the Id directly, or a name to resolve to an Id in Step 1b. | User | `0c8xx0000000001AAA` / `March Endcap Promo` |

### Key Concepts (reference before executing)

**Assessment Task Definition (ATD)** — the concrete activity instance, created from a template and bound to a Visit Spec. Critical fields:

- **ValidFrom / ValidTo (validity window)** — ISO date format (`yyyy-MM-dd`, NOT datetime). The platform hides the activity from field users outside this range. In this workflow **both** this event-driven activity and the standard activity created in Act 5 use the **same** validity window (Act 5 reuses this activity's `ValidFrom`/`ValidTo`).
- **VisitSpecId** — MUST match the Act 1 Visit Specification. This is the binding contract ("this activity belongs to this visit type"); a mismatch breaks Act 8's visit-activity attachment.
- **AsmtTskDefTmplId** — MUST point to a template with `IsStandardTask=false`. The template is the classification source of truth; a standard template makes this ATD standard (wrong path).
- **IsStandardTask** — `false` = event-driven, validity-window-bound. Inherited from the template, but set explicitly as defense.
- **InternalOrganizationUnitId** — the referenced record must exist or field users get "activity not found".
- **PromotionId** — *only for promotional activities* (e.g. `TaskType = "PromotionCheck"`). Ties the activity to a specific `Promotion` record. The user passes either the Promotion Id or a promotion name; if they give a name, resolve it to an Id (Step 1b) before creating the ATD. Omit the field entirely for non-promotional activities.

---

## Step-by-step procedure

### Step 1: Confirm Carried-Forward IDs

This Act consumes three IDs that already exist — don't re-query them by name. Carry them forward:

- `VISIT_SPEC_ID` — the Visit Specification from **Act 1** (bound via `VisitSpecId`).
- `ACTIVITY_TEMPLATE_ID` — the non-standard Activity Template from **Act 2** (referenced as `AsmtTskDefTmplId`).
- `INTERNAL_ORG_UNIT_ID` — the Internal Org Unit from **Act 1** (referenced as `InternalOrganizationUnitId`).

```bash
VISIT_SPEC_ID="1cbxx0000000001AAA"        # from Act 1
ACTIVITY_TEMPLATE_ID="1cDxx0000000001EAA"  # from Act 2
INTERNAL_ORG_UNIT_ID="0gJxx0000000001EAA"  # from Act 1
```

Optionally confirm the template is still non-standard before building on it (a standard template makes this ATD standard — the wrong path):

```bash
sf data query \
  --query "SELECT Id, IsStandardTask FROM AsmtTskDefTmpl WHERE Id = '$ACTIVITY_TEMPLATE_ID'" \
  --target-org <org-alias>
# Expect IsStandardTask = false
```

### Step 1b: Resolve the Promotion (promotional activities only)

**Skip this step for non-promotional activities.** If the user is setting up a promotional activity (e.g. `TaskType = "PromotionCheck"`), they must supply the promotion — either its `PROMOTION_ID` or a promotion name.

- **If they gave an Id (`PROMOTION_ID`)** — confirm it exists, then use it as-is:

  ```bash
  sf data query \
    --query "SELECT Id, Name FROM Promotion WHERE Id = '$PROMOTION_ID'" \
    --target-org <org-alias>
  # Expect exactly one row; if zero, the Id is wrong — stop and re-confirm with the user.
  ```

- **If they gave a name (`PROMOTION_NAME`)** — resolve it to an Id:

  ```bash
  sf data query \
    --query "SELECT Id, Name FROM Promotion WHERE Name = '$PROMOTION_NAME'" \
    --target-org <org-alias>
  ```

  - **Zero rows** → no such promotion; stop and ask the user for the correct name or Id.
  - **Exactly one row** → capture its `Id` as `PROMOTION_ID`.
  - **More than one row** → the name is ambiguous; show the user the matches and have them pick the right `Id`.

Carry the resolved `PROMOTION_ID` into Step 2's payload. For non-promotional activities, leave `PromotionId` out of the payload entirely.

### Step 2: Create Assessment Task Definition
```bash
POST /services/data/v68.0/sobjects/AssessmentTaskDefinition
Content-Type: application/json

{
  "Name": "Promo Compliance Check",
  "IsActive": true,
  "Description": "Two-week promotion compliance activity for March campaign",
  "AsmtTskDefTmplId": "1cDxx0000000001EAA",
  "IsStandardTask": false,
  "ValidFrom": "2026-03-01",
  "ValidTo": "2026-03-14",
  "VisitSpecId": "1cbxx0000000001AAA",
  "ShouldIncludeSpecAcct": true,
  "ShouldIncludeAssortments": true,
  "TaskType": "PromotionCheck",
  "PromotionId": "0c8xx0000000001AAA",
  "InternalOrganizationUnitId": "0gJxx0000000001EAA"
}
```

> `PromotionId` is included here because this worked example is a **promotional** activity (`TaskType = "PromotionCheck"`) — use the `PROMOTION_ID` resolved in Step 1b. **Omit this field entirely** for non-promotional activities.

**Response:**
```json
{
  "id": "0Z4xx0000000001EAA",
  "success": true,
  "errors": []
}
```

**Save this value** — capture the returned `id` as `ACTIVITY_ID`; Step 3 and every downstream Act reference it by Id (never by name):
```bash
ACTIVITY_ID="0Z4xx0000000001EAA"
```

**Field Explanations:**

| Field | Type | Required | Purpose |
|-------|------|----------|---------|
| `Name` | String(80) | ✅ | Activity name shown to merchandisers |
| `IsActive` | Boolean | ✅ | Must be true for activity to be served |
| `Description` | String(255) | ✅ | Business context for the activity. Required on create — omitting it returns `REQUIRED_FIELD_MISSING: [Description]` (a validation rule; the field describes as nillable). |
| `AsmtTskDefTmplId` | Reference | ✅ | Points to Act 2 template — inherits `IsStandardTask=false` |
| `IsStandardTask` | Boolean | ✅ | **MUST be false** for event-driven activities. Inherited from template but explicit is safer. |
| `ValidFrom` | Date | ✅ | Start of validity window (ISO format: yyyy-MM-dd) |
| `ValidTo` | Date | ✅ | End of validity window. Activity won't be served outside this range. |
| `VisitSpecId` | Reference | ✅ | Points to Act 1 Visit Spec — binds activity to visit type. **MUST match** for Act 8 attachment to work. |
| `ShouldIncludeSpecAcct` | Boolean | ⚪ | Include accounts from Visit Spec's ActionPlanAssignedTargets |
| `ShouldIncludeAssortments` | Boolean | ⚪ | Include product assortments for scoped activities |
| `TaskType` | Picklist | ✅ | Valid values: `InventoryCheck`, `PlanogramCheck`, `PromotionCheck`, `ConductInStoreSurveys`, `PlaceOrder`, `Other`, `SafetyCheck`, `VehicleCheck`, `AssetAudit`, `PictureAudit`, `AccountTask`. Use `PromotionCheck` for a promo-compliance activity; `Other` when none fit. |
| `PromotionId` | Reference | ⚪ | **Promotional activities only.** The `Promotion` this activity is tied to — use the `PROMOTION_ID` resolved in Step 1b (from a passed Id or name). Omit for non-promotional activities. |
| `InternalOrganizationUnitId` | Reference | ✅ | Internal Org Unit — must match for proper scoping |

### Step 3: Verify Creation

Query the activity by the `ACTIVITY_ID` captured in Step 2:

```bash
sf data query \
  --query "SELECT Id FROM AssessmentTaskDefinition WHERE Id = '$ACTIVITY_ID'" \
  --target-org <org-alias>
```

**Expected Response:** Exactly one `Id` row — the activity exists.
```json
{
  "totalSize": 1,
  "records": [
    { "Id": "0Z4xx0000000001EAA" }
  ]
}
```

---

## Validation

Confirm the Assessment Task Definition exists and is configured correctly (Step 3 query returns these values).

### Success Criteria

- ✓ `IsStandardTask = false` (non-standard classification)
- ✓ `ValidFrom` and `ValidTo` are set and correct (ISO date format)
- ✓ `VisitSpecId` matches Act 1's Visit Specification ID
- ✓ `AsmtTskDefTmplId` matches Act 2's Template ID
- ✓ `IsActive = true` (activity is live)
- ✓ `InternalOrganizationUnitId` references an existing `InternalOrganizationUnit` record
- ✓ Query returns exactly 1 record (no duplicates)

---

## End state

After completing Act 3:

- ✅ **Assessment Task Definition created**, classified as event-driven (`IsStandardTask = false`).
- ✅ **Validity window set** (March 1-14, 2026 in the example) and active.
- ✅ **Visit Specification referenced** (`VisitSpecId` matches Act 1 — binds to the store visit type).
- ✅ **Template referenced** (`AsmtTskDefTmplId` matches Act 2 — non-standard classification inherited).
- ✅ **The activity Id is captured** and ready for Act 4.

**At this point:**
- Act 3 creates the activity container only.
- No questions are linked to the activity yet — that happens in Act 4 (activity-level `AssessmentTaskIndDefinition` links, the enforceable contract).
- No accounts are scoped and no visits exist yet — those happen in Acts 7–8.

**You are NOT done with the full setup** — this is Act 3 of 9. Proceed to Act 4 (Add Questions).

---

## Gotchas and common errors

### 1. Validity Window Format
**Problem:** Passing a datetime (`ValidFrom: "2026-03-01T00:00:00Z"`) instead of a plain date.  
**Behavior:** `ValidFrom`/`ValidTo` are `Date` fields. A datetime string does **not** error — the platform silently coerces it, discarding the time component and storing just the date (`2026-03-01`). This holds via both the `sf` CLI and the raw REST API.  
**Fix:** Always pass a plain ISO date without a time component: `"2026-03-01"`. Don't rely on the coercion — send the date the field expects.

### 2. Standard Template Used by Mistake
**Problem:** `AsmtTskDefTmplId` points to template with `IsStandardTask=true`  
**Symptom:** Activity classified as standard, validity window ignored  
**Fix:** Query template first, verify `IsStandardTask=false`

### 3. InternalOrganizationUnitId Invalid
**Problem:** Org unit id is wrong or the record doesn't exist  
**Error:** `INVALID_CROSS_REFERENCE_KEY`  
**Fix:** Query `SELECT Id, OrganizationName FROM InternalOrganizationUnit WHERE Id = '<id>'` and confirm one row returns before using it. (`InternalOrganizationUnit` has no active/status field.)

---

## Notes: best practices & architecture

**Explicit over inherited.** `IsStandardTask` is inherited from the Act 2 template, but set it explicitly on the ATD as well — it's the classification pivot for the whole activity, and an explicit value protects against a mis-selected template.

**Validity window is the event-driven mechanism.** For promotional/seasonal activities, `ValidFrom`/`ValidTo` is what makes the activity auto-appear and auto-expire. The platform enforces this at serve time — no manual activation/deactivation needed.

**Where the activity sits in the lifecycle:**

```text
Visit Specification (VisitSpec)          ← Act 1: the visit type
Activity Template (AsmtTskDefTmpl)        ← Act 2: the reusable blueprint
   ↓ (created from template, bound to spec)
Activity Definition (AssessmentTaskDefinition)  ← Act 3 (this act): the concrete instance
   ↓ (questions linked via ATID)
Questions on activity                     ← Act 4: the enforceable question contract
   ↓
Visit (AssessmentTask)                    ← Act 8: field execution
```

Act 3 creates the concrete instance. It references the template's classification and the spec's visit type, but questions become active on the activity only in Act 4.

---

## Session state to track & handoff

> **Internal only — never print this to the user.** These variables (including `act3_complete`) are orchestration bookkeeping. Track them silently to drive the gate below; do **not** echo raw variable names, IDs, or the gate flag into the conversation. When the Act finishes, tell the user only a short plain-language confirmation (e.g., "✅ Act 3 done — your activity is created and live").

Pass these forward to Act 4:

- `activity_id` — the `Id` of the `AssessmentTaskDefinition` created (e.g., `0Z4xx0000000001EAA`). **Required for Act 4** (question links reference this as `AssessmentTaskDefinitionId`).
- `activity_name` — the `Name` of the activity (use a unique name to avoid ambiguous later queries).
- `valid_from` / `valid_to` — the validity window (Act 8 matches visits against this range).
- `visit_spec_id` — carried from Act 1 (bound via `VisitSpecId`).
- `act3_complete` — boolean; set to `true` after the Validation checks pass.

**Do NOT proceed to Act 4 until `act3_complete = true`.**

---

## Next Act

Proceed to **Act 4: Add Questions** (`../act4-add-questions/SKILL.md`), which creates the `AssessmentTaskIndDefinition` records that link questions to this activity (the enforceable question contract). Downstream: Act 5 (Standard Activity — auto-runs only if Act 1 created a new Visit Spec), Act 6 (Assortments), Act 7 (Account Scoping), Act 8 (Plan Visits & Attach).

---

## References

- **Act 1:** [Visit Specification Setup](../act1-visit-specification/SKILL.md) ← Prerequisite (provides `VisitSpecId`)
- **Act 2:** [Template and Questions](../act2-template-and-questions/SKILL.md) ← Prerequisite (provides `AsmtTskDefTmplId`)
- **Act 4:** [Add Questions](../act4-add-questions/SKILL.md) ← Next step
- **9-Act Steel Thread README:** [../../README.md](../../README.md) ← Full flow
- **Object Reference:** Salesforce `AssessmentTaskDefinition` object documentation
