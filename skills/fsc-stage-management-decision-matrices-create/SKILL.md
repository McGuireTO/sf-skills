---
name: fsc-stage-management-decision-matrices-create
parent: "digital-origination-stage-management-setup"
purpose: "Create and activate the three stage-management decision matrices that map an application form product stage to CDS access, applicant visible status, and application form stage."
description: "Create and activate the three Business Rules Engine decision matrices that drive Compliant Data Sharing for Stage Management: HomeLoan_CDS_Config (stage to participant access levels), AFPStage_To_ApplicantVisibleStatus (stage to the applicant-facing visible status), and AFPStage_To_AFStage (application form product stage to the parent application form stage). All three are Standard decision matrices keyed on the ApplicationFormProductStage input with Text columns. Reuses the shared digital-origination-bre-setup decision-matrix-foundation machinery (a CalculationMatrix sObject with Type set to Standard, MD5-hash rows, and activate-dmversion). Never invents the customer's stage values or access policy."
metadata:
  version: "1.0"
---

# Digital Origination Stage Management — decision matrices

Build the three decision matrices the CDS Apex reads on every stage transition. Each is keyed on the new
`ApplicationFormProductStage` value and returns the decisions that drive access and status. This sibling
owns the three matrices' column and row contracts; it delegates the actual create/populate/activate
mechanics to the shared decision-matrix foundation.

Source: Salesforce Help "Create Decision Matrix for Digital Lending" (stage management). Prerequisite:
Business Rules Engine is set up and Context Service is enabled (the `permissions` sibling confirms this).

## Reuse the shared foundation — do not re-derive the mechanics

These are the same Business Rules Engine decision matrices `digital-origination-bre-setup` builds. Delegate
the create/columns/rows/activate lifecycle to the shared sibling SOR
`fsc-mandalorians/digital-origination-bre-setup-decision-matrix-foundation`, which owns the org-verified
recipe:

- The matrix is a **`CalculationMatrix`** sObject (key prefix `0lI`), **not** `DecisionMatrixDefinition`.
- Immediately after insert, PATCH **`Type = "Standard"`** — a null `Type` makes the derived version
  `MatrixType` null and the runtime lookup throws "Unsupported Matrix type null" (surfaced as "no output
  for the specified input").
- Columns via the BRE Taurus Connect API (`post-decision-matrix-columns`), which auto-creates version 1.
  All columns here are `Text` — no `NumberRange` banding is needed.
- Rows by direct `CalculationMatrixRow` sObject insert with the engine's MD5-hash `Name` (over the input
  columns only), into a draft version (`IsEnabled=false`).
- Activate via `activate-dmversion`, then prove with a live
  `POST /connect/business-rules/decision-matrices/{Name}` lookup that returns the expected output.

Pass each matrix's exact Name, its column contract, and its rows to the foundation sibling. All three
matrices share the single input column `ApplicationFormProductStage` (`Input`, `Text`).

## Matrix 1 — `HomeLoan_CDS_Config`

Maps a stage to the participant access each side gets. Columns:

| Column (apiName) | columnType | dataType |
|---|---|---|
| `ApplicationFormProductStage` | `Input` | `Text` |
| `Underwriter_Access` | `Output` | `Text` |
| `Applicant_Agent_Access` | `Output` | `Text` |

Rows: one per stage the admin defined. Each output cell is a comma-separated list of participant-role API
names (must match the roles the `compliant-data-sharing` sibling created), e.g. `Applicant_Agent_Access`
= `ApplicationFormRW, ApplicationFormProductRW, PartyProfileRW` and `Underwriter_Access` =
`ApplicationFormNoAccess, ApplicationFormProductNoAccess, PartyProfileNoAccess` at Intake. The article's
example (bankers RW / underwriters NoAccess at Intake; the reverse at Contract Generation; underwriters
NoAccess at Auto Approved/Auto Rejected) is illustrative — use the admin's approved access policy.

## Matrix 2 — `AFPStage_To_ApplicantVisibleStatus`

Maps a stage to the applicant-facing status shown on the record. Columns:

| Column (apiName) | columnType | dataType |
|---|---|---|
| `ApplicationFormProductStage` | `Input` | `Text` |
| `ApplicantVisibleStatus` | `Output` | `Text` |

Rows map each stage to its applicant-visible label (article examples: Book to Core → Loan Booked; the
Rejected stages → Rejected; the Approved stages → Approved; In Review → In Review; Submitted →
Submitted). Use the admin's values.

## Matrix 3 — `AFPStage_To_AFStage`

Maps the application-form-product stage to the parent application-form stage. Columns:

| Column (apiName) | columnType | dataType |
|---|---|---|
| `ApplicationFormProductStage` | `Input` | `Text` |
| `ApplicationFormStage` | `Output` | `Text` |

Rows roll product stages up to the coarser form stages (article examples: Signature Complete / Awaiting
Signature / Contract Generation → Closing; the Approved/Rejected stages → Decision; Need More Info / In
Review / Submitted → Submitted; Intake → Intake; Book to Core → Book to Core). Use the admin's values.

## Ordering and idempotency

- The input token in every row's `InputData` is the stage string (`{"ApplicationFormProductStage":"Intake"}`);
  the MD5-hash `Name` is computed over that input column only (delegated to the foundation sibling).
- Build all three matrices; each is independent but all share the same input column name.
- Reuse an exact-match matrix (same Name, columns, and rows) rather than creating a duplicate. On a shape
  mismatch, present the diff and stop.
- The output tokens must line up with the artifacts they name — the role lists in `HomeLoan_CDS_Config`
  must be roles the `compliant-data-sharing` sibling created, and the stage/status values must match the
  `ApplicationFormProduct.Stage` picklist and the applicant-status field. Cross-check before activating.

## Output contract

For each of the three matrices return the Name, `CalculationMatrix` Id (`0lI…`),
`CalculationMatrixVersion` Id (`0lN…`), the active window (StartDateTime set, EndDateTime null), the
verified columns and rows, and a live BRE lookup result proving the matrix evaluates for a representative
stage.

## Definition of done

All three matrices (`HomeLoan_CDS_Config`, `AFPStage_To_ApplicantVisibleStatus`, `AFPStage_To_AFStage`)
exist as `CalculationMatrix` records with `Type="Standard"`, carry the admin's stage rows, read active on
a fresh read, and each returns its expected output from a live BRE lookup. A matrix that is Active but
whose lookup returns "no output" is NOT done. A partial run is never reported as complete.
