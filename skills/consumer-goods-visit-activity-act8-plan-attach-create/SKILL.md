---
name: consumer-goods-visit-activity-act8-plan-attach-create
description: "Act 8 of 9: Plans visits and attaches the Activity Definition to those visits via Assessment Task records. Uses Connect APIs (prepare-assessment-task for bulk task create, assessment-task-visit-planning/visits for visit creation). Handles the full prerequisite chain including the critical AccountTeamMemberPeriod junction records — without which the API returns success but creates zero tasks. Depends on Act 3 (activity) and, if scoped, Act 7 (account scoping). Part of the 9-Act Retail Execution steel thread."
metadata:
  version: "1.0"
  cliTools:
  - tool:
    - "sf"
    semver: ">=2.0.0"
---

# Act 8: Plan Visits & Attach Activity

**Part of:** [9-Act Retail Execution Steel Thread](../../README.md)  
**Depends on:** [Act 3 - Activity Definition](../act3-activity-definition/SKILL.md), [Act 7 - Account Scoping](../act7-account-scoping/SKILL.md) (if scoped)  
**Enables:** [Act 9 - Verification](../act9-verification/SKILL.md)

**Act 8 is where the activity becomes usable — it creates Assessment Tasks and attaches them to visits, making the activity executable by field reps in the mobile app. You MUST complete Act 3 (activity exists) and, if scoping, Act 7 before starting this act.**

---

## Goal

Plan visits and attach the Activity Definition to those visits via Assessment Task records — so field reps can execute the activity in the Retail Execution mobile app for every scoped account.

**Builder's intent:** "Put it on a visit. If a visit exists, attach it. If not, create one. This attaching step is where it usually goes wrong."

**What you'll create:**
1. `AssessmentTask` (job) records via the `prepare-assessment-task` Connect API — one per scoped account × covering assignment.
2. `Visit` records via the `assessment-task-visit-planning/visits` Connect API — created from those task Ids; the response returns the authoritative `visitIds`.

**What you'll verify (NOT create):** `AccountTeamMemberPeriod` records — the merchandiser-to-account assignments that tell the Connect API which user-account-date combinations should get tasks. These are operational data that must already exist in the org. **If they're missing, surface it as a gap — do NOT fabricate them.**

**Definition of done:** Assessment Tasks prepared for all scoped accounts and every account has a visit (`visitIds`) — tasks are linked to an existing visit when one satisfies the matching criteria, and a new visit is created when none does. Activity is ready for field reps to execute in the Retail Execution mobile app.

---

## What this Act does

At this point Acts 1–7 have produced: Visit Specification (`visitSpecId`), Template + questions (`templateId`), Activity Definition + questions (`activityId`), assortments, and account scoping (`scopedAccountIds[]` or org-wide). Act 8 turns that configuration into executable field work:

1. **Verifies the full prerequisite chain** (object permissions + data prerequisites).
2. **Verifies `AccountTeamMemberPeriod` records exist** — the critical junction that tells the Connect API which user-account-date combinations should get tasks. **These are pre-existing operational assignments; if they're missing, the API returns success but creates 0 tasks — surface that as a gap rather than creating the records.**
3. **Calls `prepare-assessment-task`** (Connect API) — bulk-creates Assessment Task (job) records.
4. **Calls `assessment-task-visit-planning/visits`** (Connect API) — creates the Visit records from those task Ids and returns `visitIds`.

**Builder's mental model:** "Put it on a visit. If a visit exists, attach it. If not, create one." The attaching step is where setups usually fail — almost always because `AccountTeamMemberPeriod` assignments don't exist yet for these merchandisers.

---

## When to use

**Invoke this skill when:**
- Acts 1–3 and Act 7 are complete, and you're ready to make the activity executable
- You want bulk visit-task matching across many accounts
- The user asks about "plan visits for assessment tasks", "attach the activity", "create assessment tasks", or "make the activity executable"

**Trigger phrases:**
- "Attach the activity to visits"
- "Plan the visits and push the activity to field reps"
- "Create the assessment tasks"
- "Act 8" or "plan and attach"

**Connect API — use when:**
- All 8 data prerequisites are fully configured
- Bulk operation across many accounts (50+)
- You want automatic visit-task matching
- You have `AccountTeamMemberPeriod` records in place

**Connect API — don't use when:**
- Partial setup (missing any prerequisite)
- You need fine-grained control over task names
- `AccountTeamMemberPeriod` is not configured

---

## Prerequisites

| Act | Artifact | Required For |
|-----|----------|--------------|
| Act 1 | Visit Specification + InternalOrganizationUnit | `visitSpecId`, IOU on the activity |
| Act 3 | Assessment Task Definition (active, with IOU/VisitSpecId/validity) | `activityId` to prepare tasks for |
| Act 7 | Account scoping (`AsmtTskDefAcct`) | Which accounts get tasks (or org-wide) |

**Object permissions** — check the user has access to the required objects:
```sql
SELECT Parent.Name, Parent.Profile.Name, SobjectType,
       PermissionsRead, PermissionsCreate, PermissionsEdit
FROM ObjectPermissions
WHERE SobjectType IN ('AssessmentTask', 'Visit')
  AND PermissionsCreate = true
```
Visit, AssessmentTask need at least `PermissionsRead = true`.

**The full 8 data prerequisites (ALL required — missing ANY ONE = API returns success but creates 0 tasks):**

1. ✅ **AssessmentTaskDefinition** (Activity) with `IsActive = true`, `InternalOrganizationUnitId` set, `VisitSpecId` set, `ValidFrom`/`ValidTo` dates, `ShouldIncludeSpecAcct = true` — from Acts 1–3
2. ✅ **AsmtTskDefAcct** (account scoping) — links activity to specific accounts — from Act 7
3. ✅ **VisitSpec** with InternalOrganizationUnit — from Act 1
4. ✅ **InternalOrganizationUnit** exists — from Act 1
5. ✅ **Location** records — for `Visit.PlaceId`
6. ✅ **AccountTeamMemberPeriod** ⭐ **THE CRITICAL ONE** — links User to Account for a specific date period. **Without this, the API returns success but creates 0 tasks.**

---

## Inputs

Received from previous Acts (orchestrator integration):
```yaml
activityId: "0Z4..."           # from Act 3
activityName: "Q1 Promotion Compliance"  # from Act 3
visitSpecId: "1cb..."          # from Act 1
validFrom: "2026-03-01"        # from Act 3
validTo: "2026-03-14"          # from Act 3
iouId: "0gJ..."                # from Act 1/2/3
scopedAccountIds: ["001...", "001..."]  # from Act 6, or [] for org-wide
```

**Expected output** (returned to orchestrator):
```yaml
tasksCreated: 40         # upsertedTaskCount from prepare-assessment-task
visitsCreated: 12        # visitCount from assessment-task-visit-planning/visits
duplicateVisitsSkipped: 0  # duplicateVisitCount (a visit already existed for that slot)
visitIds: ["0Z5..."]     # authoritative list of created visits — handed to Act 8
```

### Key Concepts (reference before executing)

**Act 8 uses TWO Connect APIs:**
- **prepare-assessment-task** — bulk-creates Assessment Task (job) records
- **assessment-task-visit-planning/visits** — creates the Visit records from those task Ids (synchronous; returns `visitIds`)

Critical points:

- **AccountTeamMemberPeriod is mandatory** — the #1 cause of "success but 0 tasks". The Connect API uses it to determine which user-account-visit combinations should have assessment tasks created. `UsageType` = `"Trade"` (only available value); the `StartDate`/`EndDate` must cover the activity's `ValidFrom`/`ValidTo` range.
- **currentDate must be within ValidFrom/ValidTo** — the `prepare-assessment-task` call's `currentDate` must fall inside the activity's validity window.
- **A Location named exactly `Default Location` must exist** — the visit-creation API anchors the visits it creates to it as the fallback place. Without it the call errors: "We couldn't find a default location record. Make sure a location named Default Location exists in your org."
- **`visitScheduleDate` must be within ValidFrom/ValidTo** and today-or-future.
- **Silent-zero contract** — the prepare API returns `isSuccess: true` even when it creates nothing; always check `upsertedTaskCount`. Note visit creation is a separate call (Step 4).

---

## Step-by-step procedure

### Step 1: Verify all 8 prerequisites are met

Before calling the Connect API, confirm ALL eight data prerequisites exist (see the Prerequisites section). **If any prerequisite is missing, the API returns `isSuccess: true` but `upsertedTaskCount: 0`.**

### Step 2: Verify AccountTeamMemberPeriod records exist (CRITICAL)

`AccountTeamMemberPeriod` links a merchandiser (User) to an Account for a date period — it's the org's operational assignment data, created when merchandisers are assigned their territories/accounts. **Act 8 does NOT create these records.** It verifies they already exist and cover the activity's validity window.

For each scoped account-user combination that should have tasks, confirm a record exists covering `ValidFrom`/`ValidTo`:

```bash
sf data query \
  --query "SELECT AccountId, UserId, StartDate, EndDate FROM AccountTeamMemberPeriod WHERE AccountId IN ('001...','001...') AND UsageType = 'Trade' AND StartDate <= 2026-03-01 AND EndDate >= 2026-03-31" \
  --target-org <org-alias>
```

**Why this matters:** The Connect API uses `AccountTeamMemberPeriod` to determine which user-account-visit combinations should have Assessment Tasks created. Without a covering record, the API silently creates 0 tasks.

**If records are missing:** do NOT fabricate them. Merchandiser-account assignments are owned upstream (territory management / account team setup). Surface the missing assignments as a gap — list the account-user combinations that lack a covering `AccountTeamMemberPeriod` and stop, so the right owner can create them. Attaching tasks to accounts no one is assigned to would produce orphaned work.

```text
⏳ Verifying AccountTeamMemberPeriod coverage...
   ✅ 40/40 scoped accounts have a covering assignment
```

### Step 3: Call prepare-assessment-task Connect API

```bash
POST /services/data/v68.0/connect/industries/retail/prepare-assessment-task
{
  "assessmentTaskDefinitionId": "0Z4...",
  "currentDate": "2026-03-05"     # Must be within ValidFrom/ValidTo
}
```

**Response:**
```json
{
  "deletedTaskCount": 0,
  "failedCount": 0,
  "failedRecords": [],
  "isSuccess": true,
  "upsertedTaskCount": 40
}
```

**What the API does:**
1. **Validates** all prerequisites are in place
2. **Creates AssessmentTasks** — one per scoped account (AsmtTskDefAcct) × covering `AccountTeamMemberPeriod` for `currentDate`. NOTE: overlapping AccountTeamMemberPeriod rows for the same account produce **duplicate** tasks.
3. **Sets Name** from Activity Definition and **Status** to "Incomplete"
4. **Does NOT create or attach visits** — `ParentId` is left null. Visit creation is Step 4 (`assessment-task-visit-planning/visits`).

```text
⏳ Calling Connect API to prepare assessment tasks...
   ✅ API call successful!
   📊 40 Assessment Tasks created and attached
   🗑️  0 Tasks deleted
   ❌ 0 Failed
```

### Step 4: Create visits via assessment-task-visit-planning/visits

**Purpose:** Create the Visit records the tasks belong to. `prepare-assessment-task` (Step 3) only creates the `AssessmentTask` job records — it does NOT create visits. **This** is the API that turns those jobs into Visits.

**Prerequisite:** a Location named exactly **`Default Location`** must exist in the org (the API anchors the created visits to it). Without it the call fails with "We couldn't find a default location record. Make sure a location named Default Location exists in your org."

```bash
POST /services/data/v68.0/connect/industries/visit/assessment-task-visit-planning/visits
{
  "visitScheduleDate": "2026-08-23",          # Within ValidFrom/ValidTo; today or future
  "internalOrgUnitId": "0gJ...",
  "assessmentTaskIds": ["0eg...", "0eg..."]   # the task Ids created in Step 3
}
```

**Response:**
```json
{
  "visitCount": 1,
  "visitIds": ["0Z5..."],
  "duplicateVisitCount": 0,
  "failedVisitCount": 0,
  "responseStatus": "SUCCESS"
}
```

**Read the counts, not just the status:**
- `visitCount` — visits created by this call.
- `visitIds` — **the authoritative list of created visits. Hand THESE to Act 8**.
- `duplicateVisitCount` — visits skipped because one already existed for that account/date. Dedup only spans this single call — a background planning job can also create a visit for the same slot, so re-running or mixing with the UI can still leave duplicate visits.
- `failedVisitCount` / `responseStatus` — surface any failures.

### Step 5: Verify the visits were created

Confirm with a SOQL query on the returned Ids:
```bash
sf data query --target-org <org> \
  --query "SELECT Id, AccountId, Status FROM Visit WHERE Id IN ('0Z5...')"
```
Expect one row per Id in `visitIds`.

---

## Validation

Confirm Assessment Tasks were created and attached (Step 3 `upsertedTaskCount` > 0, Step 4 query returns the tasks).

### Success Criteria

- ✓ `prepare-assessment-task` returned `isSuccess: true` **AND** `upsertedTaskCount` matches the expected account/visit count (NOT 0)
- ✓ `failedCount: 0` (or failures reviewed and resolved)
- ✓ `assessment-task-visit-planning/visits` returned `responseStatus: SUCCESS` with `visitCount > 0` and a `visitIds` array
- ✓ A SOQL query on `visitIds` returns one Visit per Id (`PlaceId = Default Location`)
- ✓ `AccountTeamMemberPeriod` records were confirmed to exist (pre-existing, not created here) for every scoped account-user combination, covering the validity window
- ✓ Tasks are visible to the assigned merchandisers for the target date

---

## End state

After completing Act 8:

- ✅ **`AccountTeamMemberPeriod` coverage confirmed** for each account-user combination (verified pre-existing, not created here).
- ✅ **Assessment Tasks created** via `prepare-assessment-task`.
- ✅ **Visits created and verified** via `assessment-task-visit-planning/visits` (`visitIds` in the response, confirmed by SOQL).
- ✅ **The activity is executable** by field reps in the Retail Execution mobile app for the scoped accounts.

**At this point:**
- Act 8 attaches the activity to the visits that currently exist / were created for this window.
- End-to-end validation (a merchandiser opening a visit and answering questions) is confirmed in Act 9 (Verification).

**You are NOT done with the full setup** — this is Act 8 of 9. Proceed to Act 9 (Verification).

---

## Gotchas and common errors

### Connect API Zero Tasks Issue (most common)
- ✅ API returns `isSuccess: true`
- ❌ But `upsertedTaskCount: 0`
- 🔍 **Cause:** Missing `AccountTeamMemberPeriod` records
- 🔧 **Fix:** Confirm a covering `AccountTeamMemberPeriod` exists for each user-account-date combo (Step 2). These are pre-existing assignments — if absent, surface a gap for the assignment owner rather than creating them here.

### Troubleshooting: "prepare-assessment-task returns 0 tasks"
Causes, in order of likelihood:
1. ❌ **AccountTeamMemberPeriod missing** (most common) — Check: `SELECT COUNT() FROM AccountTeamMemberPeriod WHERE AccountId IN (...) AND UserId = '...'`; Fix: these are pre-existing merchandiser-account assignments — surface the missing combinations as a gap for the assignment owner (do NOT fabricate them)
2. ❌ **Date mismatch** — Check: `currentDate` is within the activity's ValidFrom/ValidTo AND Visit `PlannedVisitStartTime` is in range; Fix: align the dates
3. ❌ **InternalOrganizationUnit not set** — Check: activity definition AND VisitSpec both have `InternalOrganizationUnitId`; Fix: set IOU on both (from Acts 1–3)
4. ❌ **Account scoping missing** — Check: `SELECT COUNT() FROM AsmtTskDefAcct WHERE AssessmentTaskDefinitionId = '...'`; Fix: run Act 7 to create scoping records

### Troubleshooting: "assessment-task-visit-planning/visits creates 0 visits or errors"
1. ❌ No `Default Location` — create a Location named exactly `Default Location` (the fallback place the API anchors visits to). Error: "We couldn't find a default location record..."
2. ❌ `visitScheduleDate` outside the activity's ValidFrom/ValidTo, or in the past — use a today-or-future date inside the window
3. ❌ Empty/invalid `assessmentTaskIds` — pass the task Ids returned by Step 3 (`prepare-assessment-task`)
4. ❌ Check `internalOrgUnitId` matches the `InternalOrganizationUnitId` from Act 1

---

## Notes: best practices & architecture

**AccountTeamMemberPeriod is the linchpin.** The single most important lesson of this act: the prepare API's silent-success contract means a missing team-member-period looks identical to success. These records are pre-existing operational assignments (owned by territory/account-team setup) — verify their coverage first, surface any gaps to the assignment owner, and only call prepare-assessment-task once coverage is confirmed. Act 7 does not create them.

**Verify, don't trust the success flag.** `isSuccess: true` (prepare) and `responseStatus: SUCCESS` (visits) are each necessary but not sufficient — always read `upsertedTaskCount` and `visitCount`/`visitIds`, then confirm the Visits with a SOQL query.

**Connect API vs standard sObject API.** The Connect API is for bulk, automatic visit-task matching once all 8 prerequisites are in place. When debugging, drop to the standard sObject API for per-record visibility (task names, ParentId links) — the Connect API abstracts these away.

**API reference summary:**

| Operation | Method | Endpoint | Request Body |
|---|---|---|---|
| Prepare tasks (bulk) | POST | `/connect/industries/retail/prepare-assessment-task` | `{assessmentTaskDefinitionId, currentDate}` |
| Create visits | POST | `/connect/industries/visit/assessment-task-visit-planning/visits` | `{visitScheduleDate, internalOrgUnitId, assessmentTaskIds[]}` |
| Verify team member period | GET (SOQL) | `AccountTeamMemberPeriod` | `AccountId, UserId, UsageType, StartDate, EndDate` (confirm coverage; do not create) |

**Where attachment sits in the lifecycle:**

```text
Activity (AssessmentTaskDefinition)          ← Act 3: the concrete activity
Account scoping (AsmtTskDefAcct)             ← Act 7: which stores are eligible
   ↓ (AccountTeamMemberPeriod links users to accounts for the window)
Plan Visits & Attach (this act)              ← Act 8: AssessmentTasks created & attached to visits
   ↓
Verification (Act 9)
```

**Agent implementation flow:** receive inputs from prior Acts → present the form (user-assignment confirmation) → Step 1 verify prerequisites → Step 2 verify AccountTeamMemberPeriod coverage (surface a gap if missing) → Step 3 call prepare-assessment-task → Step 4 call assessment-task-visit-planning/visits to create the visits → Step 5 verify the returned `visitIds` via SOQL → return `tasksCreated: N` / `visitIds` to orchestrator → display completion summary. Typical progress narration:

```text
⏳ Executing Act 8...
   - Verifying prerequisites...             ✅ All prerequisites met
   - Verifying AccountTeamMemberPeriod coverage... ✅ 40/40 accounts assigned
   - Confirming Default Location exists...   ✅ found
   - Preparing assessment tasks...           ✅ 40 Assessment Tasks created
   - Creating visits from those tasks...     ✅ 12 Visits created (visitIds returned)
✅ Act 8 Complete: tasks prepared and visits created!
```

---

## Session state to track & handoff

> **Internal only — never print this to the user.** These variables (including `act8_complete`) are orchestration bookkeeping. Track them silently to drive the gate below; do **not** echo raw variable names, IDs, or the gate flag into the conversation. When the Act finishes, tell the user only a short plain-language confirmation (e.g., "✅ Act 8 done — visits are planned and the activity is attached").

Pass these forward to Act 9:

- `tasks_created` — count of `AssessmentTask` records created and attached (must be > 0).
- `visits_created` / `visits_reused` — how many visits were newly created vs reused.
- `visit_ids` — the visit Ids **created in Step 4**, taken directly from the `visits` API response `visitIds`. **Act 9 iterates these exact Ids** — it must not re-discover visits with a SOQL query, so this list is required, not optional.
- `account_team_member_period_ids` — the `AccountTeamMemberPeriod` records verified to cover the scoped accounts.
- `activity_id` / `visit_spec_id` / `iou_id` — carried from Acts 1–3.
- `act8_complete` — boolean; set to `true` after the Validation checks pass (`upsertedTaskCount` > 0 and verified).

**Do NOT proceed to Act 9 until `act8_complete = true`.**

---

## Next Act

Proceed to **Act 9: Verification** (`../act9-verification/SKILL.md`), which confirms end-to-end that a merchandiser can open a visit and answer the activity's questions.

---

## References

- **Act 1:** [Visit Specification Setup](../act1-visit-specification/SKILL.md) ← Provides `visitSpecId` + IOU
- **Act 3:** [Activity Definition](../act3-activity-definition/SKILL.md) ← Provides `activityId` + validity window
- **Act 7:** [Account Scoping](../act7-account-scoping/SKILL.md) ← Provides `AsmtTskDefAcct` scoping (if used)
- **Act 9:** [Verification](../act9-verification/SKILL.md) ← End-to-end field validation
- **9-Act Steel Thread README:** [../../README.md](../../README.md) ← Full flow
