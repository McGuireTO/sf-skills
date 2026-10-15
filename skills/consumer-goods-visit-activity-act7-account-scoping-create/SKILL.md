---
name: consumer-goods-visit-activity-act7-account-scoping-create
description: "Act 7 of 9: Limits which stores/accounts receive a merchandising activity by creating AsmtTskDefAcct (Assessment Task Definition Account) junction records — one per scoped account. Without this Act the activity applies org-wide to all accounts matching the Visit Specification; with scoping, only explicitly linked accounts get the activity. Depends on Act 3 (Assessment Task Definition). Part of the 9-Act Retail Execution steel thread."
metadata:
  version: "1.0"
  cliTools:
  - tool:
    - "sf"
    semver: ">=2.0.0"
---

# Act 7: Scope Activity to Accounts

**Part of:** [9-Act Retail Execution Steel Thread](../../README.md)  
**Depends on:** [Act 3 - Activity Definition](../act3-activity-definition/SKILL.md)  
**Enables:** [Act 8 - Plan Visits & Attach](../act8-plan-and-attach/SKILL.md)

**Act 7. It limits which stores get the activity. You MUST complete Act 3 (activity exists) before starting this act — scoping records reference the Assessment Task Definition.**

---

## Goal

Limit which stores/accounts receive a merchandising activity by creating `AsmtTskDefAcct` (Assessment Task Definition Account) junction records. Without this Act, the activity applies org-wide to ALL accounts matching the Visit Specification. With scoping, only explicitly linked accounts get the activity.

**Builder's intent:** "This promo is only in our West region stores. Don't push it to every account — just those 40 locations."

**What you'll create:**
1. One `AsmtTskDefAcct` record per scoped account (bulk-inserted via Composite API)

Scoping is **additive**: each record grants eligibility, it doesn't exclude others. Scoping does NOT create visits — it only limits which accounts can receive the activity when visits are created/attached.

---

## What this Act does

Limits which stores/accounts receive a merchandising activity by creating `AsmtTskDefAcct` records. Each record is a junction object linking:
- **AssessmentTaskDefinitionId**: the activity (from Act 3)
- **AccountId**: one specific store/location

1. **Gets the accounts to scope to from the user** — the user chooses which stores get the activity (by Id or by name).
2. **Resolves the chosen accounts to Ids** via SOQL and verifies the count.
3. **Bulk-inserts `AsmtTskDefAcct` records** — one per account, via the Composite API (200/request limit).
4. **Verifies scoping** — confirms the record count matches, no duplicates, correct accounts.

**Scoping vs Visit Creation (critical distinction):**
- **Act 7 (this Act):** says "these accounts are eligible for this activity"
- **Act 8 (Plan Visits & Attach):** actually creates visits at those accounts and attaches the activity
- Scoping doesn't create visits — it just limits which accounts can receive the activity when visits are created/attached.

---

## When to use

**Invoke this skill when (use scoping when):**
- Activity applies to a subset of stores (region, territory, account tier)
- Different activities target different account segments

**Trigger phrases:**
- "Only roll this out to the West region stores"
- "Scope the activity to these accounts"
- "Limit the promo to a subset of stores"
- "Act 7" or "account scoping"

---

## Prerequisites

| Act | Artifact | Required For |
|-----|----------|--------------|
| Act 3 | Assessment Task Definition (ATD) | The `AssessmentTaskDefinitionId` (`0Z4...`) to scope |

**Accounts exist** — the stores/locations the user wants to scope to already exist in Salesforce (so they can be resolved to Ids).

**Object permissions** — the running user needs:
- **Create + Read on `AsmtTskDefAcct`** — to insert scoping records (Step 3–4) and read them back (Step 5).
- **Read on `Account`** — to resolve chosen stores to Ids (Step 2). Without it, name→Id resolution silently returns zero rows.

Check all of them in one query:
```sql
SELECT Parent.Name, SobjectType, PermissionsRead, PermissionsCreate
FROM ObjectPermissions
WHERE SobjectType IN ('AsmtTskDefAcct','Account')
```
Confirm the running user's permission sets/profile grant: `AsmtTskDefAcct` with `PermissionsCreate = true` **and** `PermissionsRead = true`; `Account` with `PermissionsRead = true`.

---

## Inputs

| Variable | Description | Source | Example |
|---|---|---|---|
| `ORG_ALIAS` | Target org alias for `sf` CLI commands | Auth session | `my-re-org` |
| `ACTIVITY_ID` | Assessment Task Definition to scope | Act 3 | `0Z4xx00000000o1CAA` |
| `CHOSEN_ACCOUNTS` | The accounts (stores) the user chose to scope to — by Id or by name | User | `Store 101, Store 102` / `001xx...` |
| `ACCOUNT_IDS` | The resolved list of account IDs to link | Step 2 query | `['001xx...', '001xx...']` |

### Key Concepts (reference before executing)

**AsmtTskDefAcct (Assessment Task Definition Account)** — a pure junction object linking an activity to a store. Critical points:

- **AssessmentTaskDefinitionId** (reference, required) — the activity from Act 3. Always the same for all records in one scoping operation.
- **AccountId** (reference, required) — one store/location per record.
- **No additional fields** — no name, description, or dates. It's purely a link.
- **Additive** — creating multiple records is the union of scoped accounts; each grants eligibility, none excludes.
- **Prospective, not retroactive** — scoping limits future assignments. Adding/removing a scoping record does NOT create or delete existing visits/tasks.
- **Must overlap with Visit Spec criteria** — an account gets the activity only if it satisfies BOTH the scoping (Act 7) and the Visit Specification's criteria (Act 1).

---

## Step-by-step procedure

### Step 1: Get the accounts to scope to from the user

**Ask the user which accounts (stores) should receive the activity.** There is no fixed rule or criteria engine here — scoping is a deliberate, user-chosen list of accounts. The user supplies them however is convenient:

- **By account Id** — the explicit list of Account Ids to scope to.
- **By account name** — names you resolve to Ids in Step 2.

**Example:** the user says "scope this to Store 101, Store 102, and Store 103" (or hands you their Ids directly).

### Step 2: Resolve the chosen accounts to IDs

You need the `AccountId` for each account the user chose. If they gave Ids, confirm each exists; if they gave names, resolve them to Ids.

```bash
# By name — resolve each chosen store to its Id
sf data query \
  --query "SELECT Id, Name FROM Account WHERE Name IN ('Store 101','Store 102','Store 103')" \
  --target-org <org-alias>
```

```bash
# By Id — confirm the Ids the user gave actually exist
sf data query \
  --query "SELECT Id, Name FROM Account WHERE Id IN ('001xx0000006i2SAAQ','001xx0000006i2TBAQ')" \
  --target-org <org-alias>
```

**Check which accounts are already associated with this activity** — a `(AssessmentTaskDefinitionId, AccountId)` pair is unique, so re-inserting an existing one fails with `DUPLICATE_VALUE`. Query the existing scoping records and filter them out **before** building the payload (idempotent insert):
```bash
sf data query \
  --query "SELECT Id, AccountId FROM AsmtTskDefAcct WHERE AssessmentTaskDefinitionId = '$ACTIVITY_ID' AND AccountId IN ('001xx0000006i2SAAQ','001xx0000006i2TBAQ','001xx0000006i2UCAQ')" \
  --target-org <org-alias>
```
Any `AccountId` returned already has an `AsmtTskDefAcct` for this activity — **do not add it again.** Remove those from `ACCOUNT_IDS` so the payload contains only new accounts.

**Key checks:**
- Every account the user named resolved to exactly one Id — if a name matched zero or multiple accounts, confirm the right one with the user before proceeding.
- Accounts already associated with this activity are filtered out of the insert payload (only genuinely new accounts remain).
- The resolved account count matches what the user expects (asked for 3 stores → got 3 Ids).
- Capture the resolved Ids as `ACCOUNT_IDS` for the bulk insert in Step 3.

### Step 3: Prepare bulk insert payload

For scale (dozens to thousands of accounts), use the Composite API to insert all `AsmtTskDefAcct` records in one request.

**Template:**
```json
{
  "allOrNone": false,
  "records": [
    {
      "attributes": {"type": "AsmtTskDefAcct"},
      "AssessmentTaskDefinitionId": "0Z4xx00000000o1CAA",
      "AccountId": "001xx0000006i2SAAQ"
    },
    {
      "attributes": {"type": "AsmtTskDefAcct"},
      "AssessmentTaskDefinitionId": "0Z4xx00000000o1CAA",
      "AccountId": "001xx0000006i2TBAQ"
    }
    // ... one record per account
  ]
}
```

**Field notes:**
- `AssessmentTaskDefinitionId`: Your Act 3 activity ID (always the same for all records in this scoping operation)
- `AccountId`: One per target store (varies per record)
- `attributes.type`: Must be `"AsmtTskDefAcct"` (exact spelling)
- `allOrNone: false`: Continue on individual failures (e.g., one account deleted mid-operation); review failures in response

### Step 4: Bulk insert scoping records

**Request:**
```http
POST /services/data/v68.0/composite/sobjects
Content-Type: application/json
Authorization: Bearer <session_token>

{
  "allOrNone": false,
  "records": [
    // ... your prepared records from Step 3
  ]
}
```

**Success response:**
```json
[
  {"id": "0Z5xx000000001aCAA", "success": true},
  {"id": "0Z5xx000000001bCAA", "success": true},
  // ... one per record
]
```

**Partial failure response:**
```json
[
  {"id": "0Z5xx000000001aCAA", "success": true},
  {
    "success": false,
    "errors": [
      {
        "statusCode": "INVALID_FIELD",
        "message": "Account ID: id value of incorrect type: 001xx0000006INVALID",
        "fields": ["AccountId"]
      }
    ]
  }
]
```

**Handling failures:**
- Review `"success": false` entries
- Common causes: deleted account, invalid ID format, duplicate scoping record
- Retry failed records after fixing (don't re-insert successful ones)

**Batch limits:**
- Composite API limit: 200 records per request
- For >200 accounts: split into batches of 200, insert sequentially or parallelize with care
- For >10,000 accounts: consider Bulk API 2.0 (async, higher throughput)

### Step 5: Verify scoping

Query the created `AsmtTskDefAcct` records to confirm scoping.

```bash
sf data query \
  --query "SELECT Id, AccountId FROM AsmtTskDefAcct WHERE AssessmentTaskDefinitionId = '$ACTIVITY_ID'" \
  --target-org <org-alias>
```

**Expected result:** one `AsmtTskDefAcct` record per account the user chose — the returned `AccountId` set matches `ACCOUNT_IDS`.
```json
{
  "totalSize": 3,
  "records": [
    {"Id": "0Z5xx000000001aCAA", "AccountId": "001xx0000006i2SAAQ", "Account": {"Name": "Store 101"}},
    {"Id": "0Z5xx000000001bCAA", "AccountId": "001xx0000006i2TBAQ", "Account": {"Name": "Store 102"}},
    {"Id": "0Z5xx000000001cCAA", "AccountId": "001xx0000006i2UCAQ", "Account": {"Name": "Store 103"}}
  ]
}
```

---

## Validation

Confirm the scoping records exist and match the intended account set (Step 5 query + verification scenarios).

### Success Criteria

- ✓ The user's chosen accounts captured and resolved to Ids (Step 1–2)
- ✓ Accounts already associated with this activity were filtered out before insert (no duplicate `AsmtTskDefAcct` created)
- ✓ Resolved account count matches what the user expects (e.g., asked for 3 stores → 3 Ids)
- ✓ Composite API request successful (Step 4) with no failures (or failures resolved)
- ✓ Verification query confirms correct record count (Step 5: one `AsmtTskDefAcct` per chosen account)
- ✓ The returned `AccountId` set matches `ACCOUNT_IDS` exactly; no duplicate AccountIds
- ✓ Spot-check: an account the user did NOT choose has NO scoping record

---

## End state

After completing Act 7:

- ✅ **`AsmtTskDefAcct` records created** — one per scoped account (e.g., 40 West stores → 40 records).
- ✅ **Scoping verified** — record count matches, no duplicates, excluded accounts confirmed absent.
- ✅ **The activity is now limited** to the scoped accounts (union of all linked accounts).

**At this point:**
- Act 7 only declares eligibility — it does NOT create visits.
- No visits exist yet — Act 8 (Plan Visits & Attach) creates visits at eligible accounts and attaches the activity.
- The scoping is prospective — it affects future visit creation/attachment, not any existing visits.

**You are NOT done with the full setup** — this is Act 7 of 9. Proceed to Act 8 (Plan Visits & Attach).

---

## Gotchas and common errors

### 1. Scoping records created, but activity still appears everywhere
**Cause 1:** Activity was already attached org-wide before scoping (Act 8 attachment ran before Act 7).  
**Fix:** Scoping is prospective — it doesn't retract existing attachments. Delete/deactivate unwanted `AssessmentTask` records, or start fresh.

**Cause 2:** Multiple activities exist; you scoped one but not others.  
**Fix:** Verify `AssessmentTaskDefinitionId` matches the activity you're testing. Query all activities to see if another is org-wide.

### 2. Scoped accounts not receiving activity
**Cause 1:** The Visit Specification's criteria exclude the chosen accounts — an account gets the activity only if it satisfies BOTH the Act 7 scoping (it's in the chosen list) and the Act 1 Visit Specification.  
**Fix:** Confirm each chosen account also satisfies the Visit Specification (Act 1). An account scoped here but excluded by the Visit Spec still won't receive the activity.

**Cause 2:** No visits created at scoped accounts yet.  
**Fix:** Run Act 8 (Plan Visits & Attach) for the scoped accounts. Scoping doesn't create visits — it only limits eligibility.

**Cause 3:** Field-level security blocks merchandiser from seeing accounts.  
**Fix:** Grant Read access to the Account object for the merchandiser profile.

### 3. Can't create AsmtTskDefAcct records — "insufficient privileges"
**Cause:** User lacks Create permission on `AsmtTskDefAcct`.  
**Fix (Salesforce Admin):**
1. Setup → Profiles → [Merchandiser Profile]
2. Object Settings → Assessment Task Definition Account
3. Enable "Create" permission
4. Save

---

## Notes: best practices & architecture

**Idempotent scoping.** Because of the (activity, account) unique constraint, always query existing scoping records before inserting and link only the missing accounts. This makes campaign expansion safe to re-run.

**Additive scoping patterns:**
- **Adding more accounts** — to scope additional stores later, insert records for them too (union). The scoped set is the union of all `AsmtTskDefAcct` records for the activity.
- **Mid-campaign expansion** — when the user chooses more accounts to add, resolve them to Ids, insert `AsmtTskDefAcct` records with the same `AssessmentTaskDefinitionId`, then run Act 8 for the new accounts. Existing scoping remains intact — purely additive.

**Execution order:**
- **Strict:** Act 3 (create activity) → Act 7 (scope accounts).
- **Flexible:** Act 7 is independent of Act 1 (Visit Spec) — run in either order. Act 7 should run BEFORE Act 8 attachment (scoping is prospective). Running Act 7 before Act 8 visit creation simplifies validation.

**When to revisit this Act:** campaign expansion (add regions/accounts), account maintenance (stores close/open), scoping rule changes ("West only" → "West + Southwest"), or activity reuse in a new campaign with different scoping.

**Composite API limits:** 200 records/request (hard limit); daily API limits apply (Setup → System Overview → API Usage); Bulk API 2.0 for >10,000 accounts.

**Where scoping sits in the lifecycle:**

```text
Activity (AssessmentTaskDefinition)          ← Act 3: the concrete activity
   ↓ (AsmtTskDefAcct junction, one per account)
Account scoping (this act)                   ← Act 7: which stores are eligible
   ↓ (must overlap with Visit Spec criteria)
Plan Visits & Attach (Act 8)                 ← creates visits at eligible accounts, attaches activity
   ↓
Verification (Act 9)
```

Scoping limits which accounts get activities, NOT which get visits. Act 8 checks `AsmtTskDefAcct` to determine eligible accounts and only attaches the activity to visits at scoped accounts.

---

## Session state to track & handoff

> **Internal only — never print this to the user.** These variables (including `act7_complete`) are orchestration bookkeeping. Track them silently to drive the gate below; do **not** echo raw variable names, IDs, or the gate flag into the conversation. When the Act finishes, tell the user only a short plain-language confirmation (e.g., "✅ Act 7 done — the activity is scoped to your chosen accounts").

Pass these forward to Act 8:

- `activity_id` — the `AssessmentTaskDefinitionId` scoped (carried from Act 3).
- `scoped_account_ids` — the list of `AccountId`s linked via `AsmtTskDefAcct` (Act 8 attaches the activity only to visits at these accounts).
- `scoping_rationale` — which accounts are scoped and why (region/tier/territory), plus date applied — for auditability.
- `act7_complete` — boolean; set to `true` after the Validation checks pass.

**Do NOT proceed to Act 8 until `act7_complete = true`.**

---

## Next Act

Proceed to **Act 8: Plan Visits & Attach** (`../act8-plan-and-attach/SKILL.md`), which creates visits at the eligible accounts and attaches this activity to them. Act 8 checks the `AsmtTskDefAcct` scoping records to determine which accounts get the activity. Downstream: Act 9 (Verification).

---

## References

- **Act 1:** [Visit Specification Setup](../act1-visit-specification/SKILL.md) ← Defines the visit criteria the chosen accounts must also satisfy
- **Act 3:** [Activity Definition](../act3-activity-definition/SKILL.md) ← Prerequisite (provides the activity ID)
- **Act 8:** [Plan Visits & Attach](../act8-plan-and-attach/SKILL.md) ← Next step (creates visits, attaches activity; respects scoping)
- **Act 9:** [Verification](../act9-verification/SKILL.md) ← End-to-end test of the full visit
- **9-Act Steel Thread README:** [../../README.md](../../README.md) ← Full flow
- **Object Reference:** Salesforce `AsmtTskDefAcct` (Assessment Task Definition Account) object documentation
