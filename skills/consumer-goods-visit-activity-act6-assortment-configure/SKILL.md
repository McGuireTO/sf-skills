---
name: consumer-goods-visit-activity-act6-assortment-configure
description: "Act 6 of 9: Enables assortment-based product surveying so merchandisers see only the products listed for each store at survey time. Configures ShouldIncludeAssortments on the Assessment Task Definition (from Act 3) and verifies that sample stores have assortments that will resolve at runtime. Product-level questions (from Act 4) instantiate once per listed product per store. Depends on Act 3 (activity) and Act 4 (product-level questions). Part of the 9-Act Retail Execution steel thread."
metadata:
  version: "1.0"
  cliTools:
  - tool:
    - "sf"
    semver: ">=2.0.0"
---

# Act 6: Make the Activity Assortment-Based

**Part of:** [9-Act Retail Execution Steel Thread](../../README.md)  
**Depends on:** [Act 3 - Activity Definition](../act3-activity-definition/SKILL.md), [Act 4 - Add Questions](../act4-add-questions/SKILL.md)  
**Enables:** [Act 7 - Account Scoping](../act7-account-scoping/SKILL.md)

**Act 6 makes product-level questions dynamic and store-specific. You MUST complete Act 3 (activity exists) and Act 4 (at least one product-level question is linked) before starting this act — assortment mode only matters when product-level questions are present.**

---

## Goal

Enable dynamic, store-specific product surveying by linking the activity to each store's assortment. When merchandisers open a visit, product-level questions (e.g., "Facings Count") instantiate **once per listed product for that specific store** — no manual per-store product list required.

**Builder's intent:** "Don't make me attach 50 products by hand — show each merchandiser only the products actually listed for the store they're visiting."

**What you'll create:**
1. `ShouldIncludeAssortments = true` on the Assessment Task Definition (from Act 3)
2. A verification that at least one sample store has a resolvable assortment

The store→assortment association is established by a **batch process ahead of time**, not at activity creation time and not live when the visit opens — this act only flips the setting; a batch job pre-associates each store with its listed products, and that's what determines the product list per store.

---

## What this Act does

This Act bridges the gap between static product lists (which require manual maintenance per store) and dynamic store-specific surveys. By enabling `ShouldIncludeAssortments`, the activity becomes aware of each store's current product mix through the Trade Org hierarchy resolution system. It performs THREE operations:

1. **Enables `ShouldIncludeAssortments`** on the Assessment Task Definition via PATCH (idempotent if Act 3 already set it `true`).
2. **Verifies the setting** by reading back the ATD via GET.
3. **Confirms assortment resolution** for a sample store (read-only) — so you catch the silent "zero products" failure before declaring success.

**Business scenario:** A field merchandiser visits Store 001. The activity includes a "Facings Count" question. Without assortments, you'd need to manually attach 50 products to the activity definition. With assortments enabled, the system:
1. Queries the active assortments
2. Instantiates the facings question once per listed product (12 products for Store 001, 18 for Store 002, etc.)
3. Merchandiser sees a dynamic survey with only the products relevant to the store they're visiting

---

## When to use

**Invoke this skill when:**
- You've completed Act 3 (activity) and Act 4 (questions, including at least one product-level question)
- Product-level questions should repeat per store-specific product rather than a hand-maintained list
- The user asks about "assortment-based activity", "store-specific products", "consider listing", or "dynamic product survey"

**Trigger phrases:**
- "Make the activity assortment-based"
- "Enable dynamic product surveying"
- "Act 6" or "assortments"

**Skip this Act when:**
- The activity has no product-level questions (assortment mode has nothing to act on)
- You genuinely want a static, hand-attached product list (a different flow, not part of the 9-Act thread)

---

## Prerequisites

| Act | Artifact | Required For |
|-----|----------|--------------|
| Act 3 | Assessment Task Definition (ATD) | The `Id` to PATCH (`0Z4xx00000000o1CAA` in examples) |
| Act 4 | Product-level question linked | Assortment mode only surveys product-level questions (e.g., Facings Count) |

**Object permissions** — the running user needs Read + Edit on `AssessmentTaskDefinition` and field-level Write on `ShouldIncludeAssortments`:
```sql
SELECT Parent.Name, SobjectType, PermissionsRead, PermissionsEdit
FROM ObjectPermissions
WHERE SobjectType = 'AssessmentTaskDefinition'
  AND PermissionsEdit = true
```

**Assortments must already exist** — this Act **assumes** assortments exist at the Trade Org hierarchy level for target stores. Creating assortments is NOT part of this Act; it's upstream data management. **If no assortment resolves for a store, the survey will show zero products — a silent failure, not an API error.**

---

## Inputs

| Variable | Description | Source | Example |
|---|---|---|---|
| `ORG_ALIAS` | Target org alias for `sf` CLI commands | Auth session | `my-re-org` |
| `ACTIVITY_ID` | Assessment Task Definition to make assortment-based | Act 3 | `0Z4xx00000000o1CAA` |
| `SAMPLE_STORE_ID` | A representative store/RetailStore to verify assortment resolution | Master data | `001xx000000ABCD` |

### Key Concepts (reference before executing)

**Assortment-based surveying** — the activity draws each store's product list from a store→assortment association that a batch process establishes ahead of time, instead of carrying a static product list. Critical points:

- **ShouldIncludeAssortments** — the single field that turns on assortment mode. Boolean on the Assessment Task Definition. May already be `true` from Act 3; the PATCH is idempotent.
- **Association is pre-computed by a batch process, not resolved live** — a batch job associates each store with the products listed for it ahead of time. When the merchandiser opens the visit, that association already exists.
- **Product-level vs visit-level questions** — only questions with `AssessmentContext: "Product"` (from Act 4) repeat per listed product; visit-level questions ("Display Up?") still ask once.
- **Silent zero-products failure** — if no assortment resolves for a store, the activity works with no error, but the merchandiser sees zero products. Always run the sample-store verification.

---

## Step-by-step procedure

### Step 1: Enable ShouldIncludeAssortments

Update the Assessment Task Definition to enable assortment-based mode:

```http
PATCH /services/data/v68.0/sobjects/AssessmentTaskDefinition/0Z4xx00000000o1CAA
Content-Type: application/json

{
  "ShouldIncludeAssortments": true
}
```

**Note:** If the field was already set to `true` during Act 3 creation, this PATCH is idempotent. If it was `false` or `null`, this updates it.

**Response:**
- `204 No Content` → success
- `400 Bad Request` → field validation failure (e.g., invalid object ID)
- `404 Not Found` → Assessment Task Definition doesn't exist

### Step 2: Verify the Setting

Read back the Assessment Task Definition to confirm the change — query by the `ACTIVITY_ID` carried from Act 3 (never by name):

```bash
sf data query \
  --query "SELECT Id, Name, ShouldIncludeAssortments, IsActive FROM AssessmentTaskDefinition WHERE Id = '$ACTIVITY_ID'" \
  --target-org <org-alias>
```

**Expected response:**
```json
{
  "totalSize": 1,
  "records": [
    {
      "Id": "0Z4xx00000000o1CAA",
      "Name": "Promo Compliance Check",
      "ShouldIncludeAssortments": true,
      "IsActive": true
    }
  ]
}
```

If `ShouldIncludeAssortments` is `false` or `null` after the PATCH, investigate:
- Field-level security may block the update (check user's permission set)
- Validation rule on the object may reject the change
- Org configuration may have custom requirements

### Runtime Behavior (Not Part of This Act's API Calls)

Understanding what happens at survey time helps verify this Act worked correctly:

**The association is pre-computed by a batch process — not resolved live when the visit opens.** A batch job walks the Trade Org hierarchy and **already associates** each store with the products listed for it, ahead of time. By the time a merchandiser opens the visit, the store's product list is a settled association, not a lookup that runs on demand.

**When merchandiser opens the visit:**
1. **Association already in place** — the batch process has already linked the store to the active products listed for it.
2. **Question instantiation** — for each product-level question in the activity definition, one instance is created per already-associated product.
3. **Survey rendering** — merchandiser sees:
   - "Facings Count" for Product A
   - "Facings Count" for Product B
   - ...one instance per listed product

**Key point:** The store→assortment association is established by a **batch process ahead of time**, not resolved dynamically at visit open. This Act only enables the setting (`ShouldIncludeAssortments = true`); the batch association and the listed products are what actually drive which products appear.

---

### Success Criteria

- ✓ PATCH request returned `204 No Content`
- ✓ Read-back query shows `"ShouldIncludeAssortments": true`
- ✓ Activity still shows `IsActive: true` (no validation rules broke the update)
---

## End state

After completing Act 6:

- ✅ **`ShouldIncludeAssortments = true`** on the Assessment Task Definition.
- ✅ **Setting verified** via GET request.
- ✅ **Activity is now product-aware and store-specific** — product-level questions expand per store using the batch-computed store→assortment association.

**At this point:**
- Act 6 flips the assortment setting only — no products are attached to the activity directly.
- No accounts are scoped yet — Act 7 (optional) limits which stores get the activity.
- No visits exist yet — those are planned in Act 8.

**You are NOT done with the full setup** — this is Act 6 of 9. Proceed to Act 7 (Account Scoping).

---

## Gotchas and common errors

### 1. Field-Level Security May Block the Update
**Problem:** If the running user doesn't have Edit permission on `AssessmentTaskDefinition.ShouldIncludeAssortments`, the PATCH returns `400 Bad Request` or `403 Forbidden`.  
**Fix:** Grant the user a permission set with `Edit` on Assessment Task Definition and field-level access to `ShouldIncludeAssortments`.

## Notes: best practices & architecture

**The product list comes from a pre-computed association, not the activity.** The activity carries no product list; it carries an intent (`ShouldIncludeAssortments = true`). A batch process associates each store with its listed products ahead of time, and the visit draws on that association. This is what makes one activity definition serve stores with wildly different product mixes.

**API reference:**

*Update Assessment Task Definition* — `PATCH /services/data/v68.0/sobjects/AssessmentTaskDefinition/{id}` with `{ "ShouldIncludeAssortments": true }`. Auth: OAuth 2.0 Bearer token with `api` scope. Requires Read + Edit on `AssessmentTaskDefinition` and field-level Write on `ShouldIncludeAssortments`.

*Read Assessment Task Definition* — `GET /services/data/v68.0/sobjects/AssessmentTaskDefinition/{id}`. Response shape:
```json
{
  "attributes": {
    "type": "AssessmentTaskDefinition",
    "url": "/services/data/v68.0/sobjects/AssessmentTaskDefinition/0Z4xx00000000o1CAA"
  },
  "Id": "0Z4xx00000000o1CAA",
  "Name": "Promo Compliance Check",
  "ShouldIncludeAssortments": true,
  "Status": "Active",
  "ActiveFrom": "2026-07-01",
  "ActiveTo": "2026-12-31"
}
```

**Where assortment mode sits in the lifecycle:**

```text
Activity (AssessmentTaskDefinition)          ← Act 3: the concrete activity
Questions-on-activity (ATID)                 ← Act 4: product-level + visit-level questions
   ↓ (ShouldIncludeAssortments = true)
Assortment-based activity                    ← Act 6 (this act): product questions expand per store
   ↓ (store→assortment association batch-computed ahead of time)
Account scoping (Act 7) → Visits (Act 8) → Verification (Act 9)
```

---

## Session state to track & handoff

> **Internal only — never print this to the user.** These variables (including `act6_complete`) are orchestration bookkeeping. Track them silently to drive the gate below; do **not** echo raw variable names, IDs, or the gate flag into the conversation. When the Act finishes, tell the user only a short plain-language confirmation (e.g., "✅ Act 6 done — assortment-based product surveys are enabled").

Pass these forward to Act 7:

- `activity_id` — the `AssessmentTaskDefinition` Id with `ShouldIncludeAssortments = true` (carried from Act 3).
- `assortment_verified` — boolean; whether Step 3 confirmed at least one sample store resolves products.
- `act6_complete` — boolean; set to `true` after the Validation checks pass.

**Do NOT proceed to Act 7 until `act6_complete = true`.**

---

## Next Act

Proceed to **Act 7: Account Scoping** (`../act7-account-scoping/SKILL.md`), which defines which stores (Accounts) are eligible for this activity by creating Account–Assessment Task Definition junction records (`AsmtTskDefAcct`). Act 7 is optional — skip it if the activity applies org-wide. Downstream: Act 8 (Plan Visits & Attach), Act 9 (Verification).

---

## References

- **Act 3:** [Activity Definition](../act3-activity-definition/SKILL.md) ← Prerequisite (provides the activity Id)
- **Act 4:** [Add Questions](../act4-add-questions/SKILL.md) ← Prerequisite (product-level questions to survey)
- **Act 7:** [Account Scoping](../act7-account-scoping/SKILL.md) ← Next step
- **9-Act Steel Thread README:** [../../README.md](../../README.md) ← Full flow
- **Retail Execution Data Model** — Trade Org hierarchy and assortment resolution (internal documentation)
- **Core Successor Mapping (M2C)** — managed-to-core field mapping guide ("Consider Listing" → `ShouldIncludeAssortments`)
