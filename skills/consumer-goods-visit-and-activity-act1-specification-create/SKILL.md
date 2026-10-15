---
name: consumer-goods-visit-and-activity-act1-specification-create
description: "Act 1 of 9: Set up the Visit Specification for Retail Execution. Creates (or reuses) a Visit Specification with UsageType \"Retail\" that activities will attach to in later acts. This is the foundational step — activities MUST reference a valid Visit Specification to be eligible for visit planning and execution. NEVER duplicate — always check if a suitable Visit Specification already exists before creating a new one (duplicate specs cause activity attachment mismatches and orphaned visits)."
metadata:
  version: "1.0"
  cliTools:
  - tool:
    - "sf"
    semver: ">=2.0.0"
---

# Act 1: Visit Specification Setup

**Part of:** [9-Act Retail Execution Steel Thread](../../README.md)  
**Depends on:** — (foundational; this is the first act)  
**Enables:** [Act 2 - Template and Questions](../act2-template-and-questions/SKILL.md)

**Act 1 is the foundational step for the 9-Act Retail Execution visit-and-activity steel thread. You MUST complete this act before proceeding to Act 2 (Template and Questions), as all subsequent activities require a valid Visit Specification to attach to.**

---

## Goal

Create (or reuse) a **Visit Specification** with `UsageType = "Retail"` — the store-visit type that every activity attaches to in later acts.

**Builder's intent:** "Set up the store-visit type every activity will attach to — and never create a duplicate, because duplicate specs cause activity-attachment mismatches and orphaned visits."

**What you'll create:**
1. One Visit Specification (`VisitSpec`) configured for Retail Execution — or a reused existing one

---

## What this Act does

Before any activities can be configured, a **Visit Specification** must exist in the org. This Act:

1. **Checks if a suitable Visit Specification already exists** — specifically one with `UsageType = "Retail"` that matches the intended store visit pattern (CRITICAL: never create duplicates — they cause activity attachment failures where activities reference the wrong spec or visits become orphaned).
2. **Creates a new Visit Specification** if none exists — via the standard sObject REST API (`POST /services/data/v68.0/sobjects/VisitSpec`).
3. **Configures it for Retail Execution** — sets `UsageType = "Retail"` (mandatory for RE activity matching), default duration (30 minutes recommended), and enables start/end time capture for visit tracking.
4. **Verifies the Visit Specification is active** — confirms it can be queried and referenced by subsequent acts.

The Visit Specification's `Id` becomes the reference key (`VisitSpecId`) for Assessment Task Definitions (Act 3), which in turn attach to Visit Plans and Visit assignments (Act 8).

---

## When to use

**Invoke this skill when:**
- You're starting a new Retail Execution visit-and-activity setup (this is the first act)
- You need a store-visit type for activities to attach to
- The user asks about "visit specification", "visit type", or "store visit setup"

**Trigger phrases:**
- "Set up the visit specification"
- "Create a store visit type"
- "Act 1" or "visit spec setup"

---

## Prerequisites

> **Org & user gates run in the orchestrator, not here.** The two org-/user-level preconditions for the whole steel thread — the Retail Execution user permission (`PermissionsRunRetailExecution`) and the org pref (`enableRetailExecution`) — are checked ONCE in the orchestrator's "Preflight: Org & user gates" section before Act 1 is invoked. If you are running Act 1 standalone (outside the orchestrator), confirm both are satisfied first. This Act assumes they already passed.

Before running this Act, verify — **in this order, and STOP on the first that fails**:

- **Obtain the target Internal Organization Unit (IOU) from the user** — the Visit Specification is bound to exactly one `InternalOrganizationUnit` (the `InternalOrganizationUnitId` field is mandatory). Do NOT guess or silently pick the first one. Instead:
  1. **List all IOUs** and present them to the user as a choice:
     ```bash
     sf data query \
       --query "SELECT Id, OrganizationName, Type, ParentOrganizationId FROM InternalOrganizationUnit ORDER BY OrganizationName" \
       --target-org <org-alias>
     ```
  2. **If the query returns zero rows, STOP and throw an error** — do not attempt to create the Visit Specification and do not create an IOU on the user's behalf. Report clearly: **"No Internal Organization Units (IOUs) exist in this org. A Visit Specification requires a valid `InternalOrganizationUnitId`. Create an IOU first, then re-run Act 1."**
  3. **Confirm the chosen IOU record is readable by the running user.** Object-level Read (checked below) is not enough — row-level sharing can still hide a specific record, and binding a VisitSpec to an IOU the user can't see leads to downstream visibility gaps. Verify record-level access with `UserRecordAccess`:
     ```bash
     sf data query \
       --query "SELECT RecordId, HasReadAccess, MaxAccessLevel FROM UserRecordAccess WHERE UserId = '<current-user-id>' AND RecordId = '<INTERNAL_ORG_UNIT_ID>'" \
       --target-org <org-alias>
     ```
     **If `HasReadAccess` is `false` (or no row returns), STOP and report:** **"The chosen Internal Organization Unit is not readable by the current user. Grant access (sharing rule / role hierarchy / manual share), then re-run Act 1."** Proceed only when `HasReadAccess = true`.

- **Obtain the validity window (`ValidFrom` / `ValidTo`) from the user** — the Visit Specification carries a validity window that Step 2's reuse check and every downstream act depend on. **Take both dates explicitly from the user; do NOT hardcode or silently default them.** Ask for a `ValidFrom` and a `ValidTo` (both `YYYY-MM-DD`). If the user wants the spec to be evergreen, that must be their **explicit** choice — confirm "no end date" with them and only then omit `ValidTo`. Do not assume evergreen, and do not invent a fiscal-year or rolling-12-month range on their behalf.

- **Object permissions for VisitSpec** — Check that the user has Create permissions:
  ```sql
  SELECT Parent.Name, Parent.Profile.Name, SobjectType, 
         PermissionsRead, PermissionsCreate, PermissionsEdit, PermissionsDelete 
  FROM ObjectPermissions 
  WHERE SobjectType = 'VisitSpec' 
    AND PermissionsCreate = true
  ```
  If no rows are returned with `PermissionsCreate = true`, the user cannot create VisitSpec records.

- **Object permissions for InternalOrganizationUnit** — Check Read access:
  ```sql
  SELECT Parent.Name, SobjectType, PermissionsRead
  FROM ObjectPermissions 
  WHERE SobjectType = 'InternalOrganizationUnit' 
    AND PermissionsRead = true
  ```

- **Setup data loaded** — at minimum:
  - Accounts representing stores (standard Account records)
  - Internal Organization Unit
  - Users assigned to appropriate territories/roles

- **API version v68.0 or later** (recommended for full RE feature parity). (Retail Execution feature enablement is covered by the org-pref check above.)

---

## Inputs

| Variable | Description | Source | Example |
|---|---|---|---|
| `ORG_ALIAS` | Target org alias for `sf` CLI commands | Auth session | `my-re-org` |
| `INTERNAL_ORG_UNIT_ID` | Internal Organization Unit the spec applies to (mandatory field) | Setup data | `0gJxx0000000001EAA` |
| `VALID_FROM` | Start of the Visit Specification's validity window | **User-supplied (Prerequisites)** | `2026-07-01` |
| `VALID_TO` | End of the validity window — or an explicit "no end date" chosen by the user | **User-supplied (Prerequisites)** | `2027-06-30` |

### Key Concepts (reference before executing)

**Visit Specification (VisitSpec)** — the reusable "visit type" that activities attach to and that visit planning matches against. Critical fields:

- **UsageType**: Must be `"Retail"` for Retail Execution activity matching. Other values ("FieldService", "Service") belong to different visit models and will not match RE activities.
- **InternalOrganizationUnitId**: **Mandatory.** Binds the spec to the Internal Organization Unit.
- **DefaultDrtn + DurationType**: Set the default visit length (e.g., `30` + `"Minute"`). Interpreted together — `DefaultDrtn` is the numeric value and `DurationType` is the unit it's read in:
  - `DurationType = "Minute"` → `DefaultDrtn = 30` means 30 minutes (recommended for store visits).
  - `DurationType = "Hour"` → `DefaultDrtn = 1` means 1 hour.
  - Set both fields together — a mismatched unit (e.g. `"Hour"` when you meant minutes) yields wildly wrong visit durations.
- **One spec per visit pattern *per IOU***: Never duplicate *within the same `InternalOrganizationUnitId`*. A second spec with the same/similar name bound to the *same* IOU splits activity attachments and orphans visits. The same name reused across *different* IOUs is fine and expected — a "Store Visit" spec on each IOU serves the same purpose per unit; uniqueness only matters within a single IOU.

---

## Step-by-step procedure

### Step 1: Authenticate to the org

Confirm the target org alias and authenticate:

```bash
sf org display --target-org <org-alias>
```

Verify the org's API version (recommended: v68.0 or later for full RE feature parity).

### Step 2: Check for existing Visit Specifications

**CRITICAL: Always check before creating.** Query for existing Visit Specifications with `UsageType = "Retail"` **scoped to the chosen IOU** (`INTERNAL_ORG_UNIT_ID` from Prerequisites) — a spec is only a reuse candidate if it matches on *both* `UsageType` **and** `InternalOrganizationUnitId`:

```bash
sf data query \
  --query "SELECT Id, Name, UsageType, DefaultDrtn, DurationType, IsAccountRequired, ShouldCaptureStartEndTime, InternalOrganizationUnitId, ValidFrom, ValidTo FROM VisitSpec WHERE UsageType = 'Retail' AND InternalOrganizationUnitId = '<INTERNAL_ORG_UNIT_ID>' ORDER BY CreatedDate DESC" \
  --target-org <org-alias>
```

**Check validity before reusing.** A Visit Specification carries a validity window (`ValidFrom` / `ValidTo`). An existing spec is only a reuse candidate if it is **currently valid** — i.e. `ValidFrom` is on/before today **and** `ValidTo` is null or on/after today. An expired (or not-yet-effective) spec must NOT be reused: visits planned against it won't generate, and activities attached to it silently drop out of scope.

**Decision point:**
- **If a suitable AND currently-valid Visit Specification exists** (`UsageType = "Retail"` **AND** `InternalOrganizationUnitId` = the chosen IOU **AND** today falls within `ValidFrom`–`ValidTo` — e.g., Name = "Store Visit"), **reuse it** — capture its `Id`, record it as an **existing** spec (`visit_spec_is_new = false`), and skip to Step 4 (verification). Do NOT create a duplicate. (Act 5 — Standard Activity — reads `visit_spec_is_new`: a reused spec is assumed to already carry its standard activity, so Act 5 is skipped for it.)
- **If no suitable Visit Specification exists for the chosen IOU**, proceed to Step 3. A spec with `UsageType = "Retail"` bound to a *different* IOU does NOT count as a match — activities scoped to this IOU need a spec on this IOU.
- **If a matching spec exists but is expired or not yet effective** (today is outside its `ValidFrom`–`ValidTo` window), do NOT reuse it. Either extend its `ValidTo` (if it has no downstream conflicts) via an update, or create a fresh spec in Step 3 with a current validity window. Note the expired spec's `Id` so you don't accidentally attach activities to it later.

**Why this matters:** Duplicate Visit Specifications with the same or similar names cause:
- Activity definitions attaching to the wrong spec
- Visit Plans that don't match the intended activities
- Orphaned visits when merchandisers execute against a spec that has no activities defined

### Step 3: Create the Visit Specification (if none exists)

Create the spec using the `InternalOrganizationUnitId` the user already provided (and whose record access you verified in Prerequisites).

**Create the Visit Specification via the `sf` CLI:**

```bash
sf data create record \
  --sobject VisitSpec \
  --values "Name='Store Visit' InternalOrganizationUnitId=0gJxx0000000001EAA Description='Standard store visit type for merchandiser activities' ValidFrom=<VALID_FROM> ValidTo=<VALID_TO> UsageType=Retail IsAccountRequired=true DefaultDrtn=30 DurationType=Minute ShouldCaptureStartEndTime=true" \
  --target-org <org-alias>
```

**Field notes:**
- `Name`: The label shown in the UI. Keep it simple and recognizable (e.g., "Store Visit"). This becomes the match key for visit planning in Act 8. Quote it (`Name='Store Visit'`) because it contains a space.
- `InternalOrganizationUnitId`: **Required.** The Internal Org unit this spec applies to. Replace `0gJxx0000000001EAA` with the `Id` the user provided in Prerequisites.
- `UsageType`: **Must be "Retail"** for RE activities to match. Do not use "FieldService" or other values — they belong to different visit models.
- `DefaultDrtn` + `DurationType`: Recommended 30 minutes (`Minute`). Adjust based on typical store visit duration.
- `IsAccountRequired`: Set `true` — retail visits are always account-scoped (store-specific).
- `ShouldCaptureStartEndTime`: Set `true` — enables time tracking for visit execution (used in reporting and KPI calculations).
- `ValidFrom` / `ValidTo`: **The validity window the user supplied in Prerequisites.** Substitute `<VALID_FROM>` / `<VALID_TO>` with their exact dates — do NOT hardcode a range or default it. Only omit `ValidTo` when the user explicitly chose "no end date" (evergreen). This window gates Step 2's reuse check and every downstream act, so it must reflect the user's stated intent, not an assumed default.

Capture the returned `Id` (e.g., `0gOxx0000000001EAA`) — you'll need it for verification and for referencing in Act 3. Record this as a **newly created** spec (`visit_spec_is_new = true`) — Act 5 (Standard Activity) uses this flag to know it must create a standard activity for the brand-new Visit Spec (a new spec has no standard activity yet, which would otherwise make the Act 9 product-survey verification fail).

### Step 4: Verify the Visit Specification

Re-query the Visit Specification to confirm it was created/exists correctly:

```bash
sf data query \
  --query "SELECT Id FROM VisitSpec WHERE Id = '0gOxx0000000001EAA'" \
  --target-org <org-alias>
```

### Step 5: Record the Visit Specification Id for downstream Acts

Store the Visit Specification `Id` in a session variable or note it for Act 3 (Activity Definition):

```bash
# Example: export for use in subsequent commands
export VISIT_SPEC_ID="0gOxx0000000001EAA"
```

You'll reference this `Id` as `VisitSpecId` when creating Assessment Task Definitions (Act 3).

---

## Validation

Confirm the Visit Specification exists and is configured correctly (Step 4 query returns these values).

**Expect:**
- `UsageType = "Retail"` ✅
- `DefaultDrtn = 30` (or your configured value) ✅
- `DurationType = "Minute"` (or your configured value) ✅
- `IsAccountRequired = true` ✅
- `ShouldCaptureStartEndTime = true` ✅
- `InternalOrganizationUnitId` set ✅

### Success Criteria

- ✓ One `VisitSpec` record exists with `UsageType = "Retail"` and a valid `InternalOrganizationUnitId`
- ✓ Spec is active / within its `ValidFrom`–`ValidTo` window (if set)
- ✓ No duplicate Visit Specifications were created (reused an existing one if applicable)
- ✓ The Visit Specification `Id` is captured for Act 3

---

## End state

After completing Act 1:

- ✅ **A Visit Specification exists** with `Name = "Store Visit"` (or your chosen name), `UsageType = "Retail"`, and a valid `InternalOrganizationUnitId`.
- ✅ **The Visit Specification is active** — can be queried and is within its `ValidFrom` / `ValidTo` date range (if set).
- ✅ **The Visit Specification Id is captured** and ready to be referenced in Act 3 (Assessment Task Definitions).
- ✅ **No duplicate Visit Specifications were created** — reused an existing one if applicable.

**At this point:**
- Act 1 only sets up the visit container.
- No activities are attached yet — that happens in Act 3.
- No visits are planned or assigned yet — that happens in Act 8.

**You are NOT done with the full setup** — this is Act 1 of 9. Proceed to Act 2 (Template and Questions) to configure the assessment framework.

---

## Gotchas and common errors

### 1. Duplicate Visit Specifications cause activity attachment failures

**Symptom:** You create a new Visit Specification with `Name = "Store Visit"` for a given IOU, but a prior one with the same `Name`, `UsageType = "Retail"`, and *same* `InternalOrganizationUnitId` already exists (perhaps created by a different admin or in an earlier test run). Later, when you create Assessment Task Definitions (Act 3), some reference the old spec and some reference the new one. Result: visits generated from one spec have no activities, and vice versa.

**Fix:** ALWAYS query first (Step 2), matching on all three of `Name`, `UsageType`, **and** `InternalOrganizationUnitId` — the duplicate that causes this is a spec with the same name and usage type bound to the *same* IOU. If such a spec already exists (and is currently valid), reuse it — do not create a new one unless absolutely necessary (e.g., the existing spec has incompatible settings, is expired, or is for a different usage type). Note: the same `Name` on a *different* IOU is not a duplicate — uniqueness only matters within a single IOU.


### 2. `UsageType` is not "Retail"

**Symptom:** The Visit Specification is created, but later activities (Assessment Task Definitions) with `UsageType = "Retail"` don't match/attach to visits created from this spec.

**Root cause:** `UsageType` was set to something other than "Retail" (e.g., "FieldService", "Service", or left blank).

**Fix:** RE activities REQUIRE `UsageType = "Retail"` for the visit matching logic to work. Always set this field to "Retail" explicitly. If you accidentally created a spec with the wrong `UsageType`, create a new spec with the correct `UsageType` and update all downstream references to point to it.

### 3. `REQUIRED_FIELD_MISSING` error on create

**Symptom:** The create command fails with `"errorCode": "REQUIRED_FIELD_MISSING", "message": "Required fields are missing: [InternalOrganizationUnitId]"`.

**Root cause:** You didn't provide `InternalOrganizationUnitId` in the payload, or it's `null`.

**Fix:** Query for a valid `InternalOrganizationUnit.Id` (see Step 3) and include it in the payload. This field is mandatory for Visit Specifications.

---

## Notes: best practices & architecture

**Reuse over recreate.** The Visit Specification is a long-lived container. One well-named spec per visit pattern (e.g., "Store Visit") is reused across every activity and template. Duplicates are the single most common source of downstream attachment bugs — always query first.

**Where the spec sits in the lifecycle:**

```text
Visit Specification (VisitSpec)          ← Act 1 (this act): the visit type / container
   ↓ (referenced by VisitSpecId)
Activity Definition (AssessmentTaskDefinition)  ← Act 3: activities that attach to the spec
   ↓
Visit Plan / Visit (AssessmentTask)      ← Act 8: planned & generated field visits
```

Act 1 provides the foundation the entire steel thread builds on; every later act assumes this spec exists and is referenced consistently.

---

## Session state to track & handoff

> **Internal only — never print this to the user.** These variables (including `act1_complete`) are orchestration bookkeeping. Track them silently to drive the gate below; do **not** echo raw variable names, IDs, or the gate flag into the conversation. When the Act finishes, tell the user only a short plain-language confirmation (e.g., "✅ Act 1 done — your Visit Specification is ready").

For orchestrating the full 9-Act steel thread, maintain these session variables after Act 1:

- `visit_spec_id` — the `Id` of the Visit Specification created/reused (e.g., `0gOxx0000000001EAA`). **Required for Act 3** (Assessment Task Definitions reference this as `VisitSpecId`).
- `visit_spec_name` — the `Name` of the Visit Specification (e.g., "Store Visit"). **Required for Act 8**.
- `visit_spec_is_new` — boolean; `true` when this Act **created** the spec (Step 3), `false` when it **reused** an existing one (Step 2). **Required for Act 5** (Standard Activity): Act 5 only creates a standard activity when `visit_spec_is_new = true`, and is skipped when the spec was reused.
- `internal_org_unit_id` — the `InternalOrganizationUnitId` used (for reference in scoping queries).
- `act1_complete` — boolean; set to `true` after Step 4 verification passes.

**Do NOT proceed to Act 2 until `act1_complete = true`.** The subsequent acts assume a valid Visit Specification exists.

---

## Out of scope / deferred (for this Act)

These are NOT part of Act 1, but are called out here to set expectations:

- **Visit Planning** — happens in Act 8 (Visit Plan and Attachment).
- **Activity Definition** — happens in Act 3 (Assessment Task Definitions that reference this Visit Specification).
- **Visit Assignment/Generation** — happens in Act 8 (Plan Visits & Attach).
- **Mobile execution** — the Retail Execution mobile app consumes visits generated from this spec, but the app setup is external to this skill.
- **Scheduling and routing optimization** — advanced features that depend on the basic visit model being in place (this Act provides that foundation).

---

## Next Act

Proceed to **Act 2: Template and Questions** (`../act2-template-and-questions/SKILL.md`), which configures the questions (Assessment Indicator Definitions) and the non-standard activity template required for activity authoring.

---

## References

- **Retail Execution Developer Guide** — `VisitSpec` object reference and field definitions.
- **Visit Specifications in the UI** — Setup → Retail Execution → Visit Specifications.
- **Act 3 (Activity Definition)** — where `VisitSpecId` is referenced to attach activities to this visit type.
- **Act 8 (Visit Plan and Attachment)** — where Visit Plans are created that reference this Visit Specification by name and attach the activities configured in Acts 3–7.
