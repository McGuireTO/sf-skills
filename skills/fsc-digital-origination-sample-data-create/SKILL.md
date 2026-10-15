---
name: fsc-digital-origination-sample-data-create
description: "Create a minimal, clearly-tagged set of sample records so an admin can SEE the Digital Origination (Digital Lending) setup working end to end — the record graph the sibling `digital-origination-demo-run` skill drives to demonstrate Stage Management, the Business Rules Engine decision matrices, and pricing. Stands up one loan application (an ApplicationForm + ApplicationFormProduct seeded at the first stage + an ApplicationFormProductProposal with a loan amount / term / credit score, plus the PartyProfile participant records CDS grants access to) so a live stage transition, a BRE lookup, and a price simulation all have real inputs. Every record it creates is tagged with a shared run marker (a `DL_Test_` prefix where the Name is writable, and the run tag in a Description / external-id field where it is not) so the demo can find them and the teardown can delete exactly them. \"Create Digital Origination sample data\", \"make some test records to try the setup\", \"seed demo loan data\", \"give me records to test stage management / pricing / the BREs\", or \"set up sample data so I can see it work\" route here. Idempotent and resumable — it queries by the run marker first and creates only the records that are missing. This skill WRITES only the sample transactional records; it never re-runs any of the six setup acts. Digital Origination is the renamed Digital Lending feature; the underlying objects, org preferences, and APIs still carry the DigitalLending name."
metadata:
  version: "1.0"
---

# Digital Origination — sample data setup

Create the **smallest record graph that proves the setup works**, so an admin who just finished the
six-act Digital Origination build can watch a real loan application move through the machinery they
configured. This skill only creates transactional sample records; it does not enable features, assign
permission sets, or re-run any setup act — those are done by the time this runs.

Its output is consumed by the sibling `digital-origination-demo-run` skill, which drives these records
to demonstrate Stage Management (the headline — a live, record-observable stage transition), the
Business Rules Engine decision matrices, and pricing.

## ⚠️ Naming: Digital Origination IS Digital Lending (read first)

Digital Origination is the renamed Digital Lending feature. The customer-facing labels say "Digital
Origination," but the objects and APIs you write against here — `ApplicationForm`,
`ApplicationFormProduct`, `ApplicationFormProductProposal`, `PartyProfile`, the CDS participant records,
the `LendingProductConfigContext` pricing context — still carry the `DigitalLending` lineage. Use the
API names against the org; say "Digital Origination" to the admin.

## Prerequisites (verify, do not fix here)

This skill assumes the setup is already done. Verify — and if a prerequisite is missing, report it and
stop rather than trying to create data on an unconfigured org:

1. **Digital Origination Initial Setup is complete** — `ApplicationForm`, `ApplicationFormProduct`, and
   `PartyProfile` are in use (Act 1).
2. **A Home Loan product exists** (Act 2) — its `Product2` id is the `ProductId` the sample
   `ApplicationFormProduct` and the price simulation reference. Query it by name; never invent a product id.
3. **Stage Management is set up** (Act 6) — the `Digital_Lending_Stage_Management` `StageDefinition`
   (`1DL…`) is active on `ApplicationFormProduct` / `Stage`, its `StageValue`s (`1DE…`) exist, and its
   transitions + the CDS Flow are in place. The demo needs the seeded record's initial `Stage` to be a
   real `StageValue`.
4. **Target org alias and acting admin are resolved** (passed down from the orchestrator; do not
   re-resolve or hardcode).

If this skill is invoked standalone and any of the above is missing, report exactly which one and route
back to the owning act — do not fabricate the missing artifact.

## The run marker (how every sample record is tagged)

**Every record this skill creates carries one shared, discoverable marker so the demo can find them and
the teardown can delete exactly them — and nothing else.** Resolve the marker once at the start of the
run and thread it through every write:

- **`run_tag`** — a single short token for this batch, e.g. `DLTEST` plus a per-run suffix
  (`DLTEST_<suffix>`). Do not use a timestamp you fabricate — derive the suffix from an org fact you
  already read (for example the acting admin's short id) or ask the orchestrator to supply it, so the
  value is stable across a resumed run.
- **Where the marker lives per object:**
  - Where the object's `Name` is **writable**, prefix it: `DL_Test_<thing>_<run_tag>` (e.g. a
    participant `PartyProfile` name).
  - Where `Name` is **not writable** — notably **`ApplicationForm` (`Name` is not writable, auto-assigned;
    `UsageType` is required on create)** — put the `run_tag` in a writable free-text field instead. On
    `ApplicationForm` that field is **`Title`**. Record which field carries the marker for each object so
    the demo and teardown query the right field.
  - **Observed live (fsc-dop7):** `ApplicationForm.Title` **is writable and accepts the marker cleanly
    (201)** — it is the run-marker carrier for the parent application. `ApplicationForm` has **no
    `Description` / `ApplicationSummary` / `Purpose` column** — a POST naming any of them fails
    `400 INVALID_FIELD` (column-absence, not FLS), so do not use them. `UsageType` is **business-rule
    required** even though `describe.nillable=true` (an empty POST fails `400 INVALID_INPUT: Select a usage
    type`) — always send `UsageType='LoanOrigination'`. Discover the graph with
    `WHERE Title LIKE 'DLTEST_%'`.

**Read before write.** Before creating anything, query for records already carrying this `run_tag` and
create only the ones missing. A re-run must be a no-op on what already exists (idempotent + resumable) —
this matters because a full seed is a handful of sequential sObject writes and a partial/timed-out run
must be safe to resume.

## The sample record graph (minimal — one application, enough inputs for all three demos)

Create exactly this graph. It is deliberately minimal: **one** loan application, seeded so a single
stage transition, one BRE lookup per matrix, and one price simulation all have the inputs they need.

```text
ApplicationForm (UsageType='LoanOrigination', run_tag in Title)
 └─ ApplicationFormProduct  (ProductId = the Act-2 Home Loan product; Stage = the first StageValue.Value, e.g. Intake)
     └─ ApplicationFormProductProposal (Amount, Term, InterestRate — the pricing + eligibility inputs)
PartyProfile participant records (banker, underwriter, applicant) — the subjects CDS grants/revokes access to
```

### 1 — `ApplicationForm` (the parent application)

- `POST /services/data/v<apiVersion>/sobjects/ApplicationForm` with **`UsageType = 'LoanOrigination'`
  (business-rule required on create)** and the `run_tag` in **`Title`** (writable; verified live). Do
  **not** set `Name` (not writable, auto-assigned) and do **not** send `Description` / `ApplicationSummary`
  / `Purpose` — `ApplicationForm` has no such column and the POST fails `400 INVALID_FIELD`.
- Re-read to capture the id (`13X…`).

### 2 — `ApplicationFormProduct` (the record Stage Management acts on)

- `POST … /sobjects/ApplicationFormProduct` with `ApplicationFormId` = the parent, `ProductId` = the
  **queried** Home Loan `Product2` id (never a guessed id), and **`Stage` = the `StageValue.Value`
  of the first stage** on the active stage definition (e.g. `Intake` — the identifier column is `Value`,
  not `MasterLabel` / `DeveloperName` / `ApiName`). Carry the `run_tag` in a writable free-text field.
- **Describe the object first** to confirm which fields (`Stage`, `Name`, a description field) are
  writable on this org before choosing where the marker lives; do not assume.
- Re-read to capture the id (`13Z…`) and confirm `Stage` read back as the seeded starting stage. This id
  is the one the demo will `PATCH` to trigger a transition.

### 3 — `ApplicationFormProductProposal` (the pricing + eligibility inputs)

- `POST … /sobjects/ApplicationFormProductProposal` with `ApplicationFormProductId` = the AFP, and the
  loan terms the downstream demos key on: `Amount`, `Term`, and the interest/credit input. **The interest
  field is `InterestRate`** (verified live — `AFPPInterestRate` fails `400 INVALID_FIELD`; `InterestRate`
  returns 201). Use the **documented example values** from the pricing and BRE siblings (e.g. the
  credit-score tier and term the matrices were built around), so the BRE lookups and the price sim return
  a real decision rather than an empty result.
- These are the values the `simulationInputVariablesWithData` helper will serialize for the price
  simulation and that the BRE decision matrices key on. Do not fabricate values that no matrix row or
  rate tier covers — pick example inputs the setup's matrices/rates actually have a row for, so the demo
  shows a hit, not a miss.

#### Credit-score scenario inputs (seed one documented value — our data)

The `IsSTPApplication` matrix and the qualification floor are keyed on a **credit score**, and it is what
makes one application demonstrate a *different outcome* than another. **Verified live on fsc-dop7: the
credit score lives on `PartyProfile.CreditScore` (the applicant participant), NOT on the proposal** — the
proposal has no credit-score field (its createable numerics are `Amount` / `Term` / `InterestRate`). So
seed the credit input on the **applicant `PartyProfile`** to one of these **documented scenario values**
(never an arbitrary number) so the demo's BRE lookup lands on a known decision. The STP cutoff is a
**configured matrix row, not a fixed constant** — on fsc-dop7 the live matrix flipped at **740** (probed:
739 → `false`, 740 → `true`), and the minimum qualifying score is **620**. Treat 740 as this org's proven
value, not a universal one; on another org, probe the matrix to confirm the boundary:

| Scenario | Credit score to seed | `IsSTPApplication` decision | Meaning |
|---|---|---|---|
| Golden path (manual) | **680** | `IsSTP = false` | Qualifies (≥620) but below the STP cutoff → manual underwriting |
| STP auto-approve | **780** | `IsSTP = true` | At/above the STP cutoff (740 on fsc-dop7) → straight-through auto-approval |
| Disqualification | **590** | `IsSTP = false` | Below the 620 minimum → does not qualify |

Default to the **golden-path 680** for the single seeded application unless the admin/orchestrator asks
for a specific scenario. Record which scenario value was seeded in the hand-off so `digital-origination-demo-run`
knows which decision to expect from the `IsSTPApplication` lookup. To demonstrate a *different* scenario,
re-seed the applicant `PartyProfile`'s `CreditScore` to that row's value (or update the existing party) —
one application graph is enough; the outcome is driven by the credit input, not by seeding multiple graphs.

### 4 — Participant records (`PartyProfile` + roles) for CDS

- Create the minimal participant `PartyProfile` records for the **banker**, **underwriter**, and
  **applicant** roles — the subjects Compliant Data Sharing grants or revokes access to as the stage
  changes. Name them with the `DL_Test_` prefix + `run_tag` where `Name` is writable.
- These must line up with the participant roles/groups the Stage Management CDS setup created
  (`Agent_Group`, `Underwriter_Group`, and the applicant role) so that when the demo moves the stage,
  there is a real participant whose access visibly changes. **Reuse** the existing participant roles by
  their exact API names — do not create new roles here; only create the sample party records that fill
  them.

## Verify & report (what "done" means for this skill)

Re-read every created record and report the graph back with ids, so the demo has a verified handle on
each:

- `ApplicationForm` id + the field carrying `run_tag`.
- `ApplicationFormProduct` id + its current `Stage` (must read back as the seeded starting stage).
- `ApplicationFormProductProposal` id + the `Amount` / `Term` / credit input it carries.
- The participant `PartyProfile` ids and which role each fills.
- The single `run_tag` value — this is the handle the demo and teardown use.

Report faithfully: if a record could not be created (a field is not writable on this org, a required
lookup is missing), say which one and why, and report a **partial** seed — never claim the graph exists
when it does not. A partial seed still hands back whatever was created so the demo can run what it can.

## Idempotency & safety

- **Read before write; reuse by `run_tag`.** A re-run creates only the missing records; an existing
  tagged graph is a no-op.
- **Resumable.** Query the tagged graph first each run so a timed-out or interrupted seed resumes cleanly
  (a handful of sequential sObject writes; keep the create loop query-first).
- **Never fabricate ids or product references.** The `ProductId` and the participant role API names are
  queried from the org; the loan/credit inputs come from the documented example values the setup was
  built around.
- **This skill only creates the sample transactional records.** It never enables a feature, assigns a
  permission set, or re-runs a setup act.

## Hand-off to the demo

On success, hand `digital-origination-demo-run` the resolved handle: the `run_tag`, the
`ApplicationFormProduct` id (the transition target), the current `Stage`, the proposal inputs
(**including which credit-score scenario value was seeded — 680 / 780 / 590 — and its expected
`IsSTPApplication` decision**), and the participant ids. The demo drives these; the teardown (owned by
the demo) deletes everything carrying the `run_tag`.

<!-- skill-validate: ignore-start -->
<!-- codey:operations start -->
## Operations Reference

Operations this skill uses — routing and dependency reference.

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `verify-prerequisites` | read | — | `GET /services/data/v63.0/query` | — |
| `resolve-run-tag-and-check-existing` | read | — | `GET /services/data/v63.0/query` | `verify-prerequisites` |
| `create-application-form` | write | — | `POST /services/data/v63.0/sobjects/ApplicationForm` | `resolve-run-tag-and-check-existing` |
| `create-application-form-product` | write | — | `POST /services/data/v63.0/sobjects/ApplicationFormProduct` | `create-application-form` |
| `create-application-form-product-proposal` | write | — | `POST /services/data/v63.0/sobjects/ApplicationFormProductProposal` | `create-application-form-product` |
| `create-participant-party-profiles` | write | — | `POST /services/data/v63.0/sobjects/PartyProfile` | `create-application-form-product-proposal` |
| `verify-sample-data-graph` | verify | — | `GET /services/data/v63.0/query` | `create-participant-party-profiles` |
<!-- codey:operations end -->
<!-- skill-validate: ignore-end -->
