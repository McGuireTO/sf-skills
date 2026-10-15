---
name: fsc-digital-origination-bre-stp-eligibility-configure
parent: "digital-origination-bre-setup"
purpose: "Set up the IsSTPApplication decision matrix that auto-approves or rejects a loan by credit score, and verify the OmniScript that consumes it."
description: "Set up Straight-Through Processing for Digital Lending applicant eligibility: a Business Rules Engine decision matrix named IsSTPApplication that returns whether a loan application qualifies for automatic approval based on the applicant's credit score. Drives the shared decision-matrix-foundation sibling for the matrix, enforces the exact name the preconfigured DigitalLendingDFIsSTPApplication OmniScript expects, and verifies that OmniScript references the matrix. Treats the OmniScript as a delivered artifact it verifies, not one it creates."
metadata:
  version: "1.0"
---

# Digital Origination STP applicant eligibility

Automate loan approval by credit score. A decision matrix named `IsSTPApplication` returns whether an
application qualifies for straight-through processing; the preconfigured `DigitalLendingDFIsSTPApplication`
OmniScript reads that result to show the applicant a confirm-offer or submitted-offer page. This
sibling owns the matrix and the verification that the OmniScript is wired to it. It does not create the
OmniScript.

The delivered OmniScript is `DigitalLendingDFIsSTPApplication` (type `DigitalLendingDF`, subType
`IsSTPApplication`, language `English`; unique key `DigitalLendingDF_IsSTPApplication_English_1`), with an
Angular/agent-console variant `DigitalLendingDFIsSTPApplicationAAE`. Inside it, the decision-matrix
**action element is named exactly `IsSTPApplication`** — that element name, not the OmniScript name, is
what the matrix name must match.

Source: Salesforce Help "Applicant Eligibility Check by Using Business Rules Engine for Digital
Lending" — the sub-topics "Approve or Reject a Loan Automatically" and "Verify the
DigitalLendingDFIsSTPApplication OmniScript".

## Required inputs

- Target-org alias and acting admin.
- The credit-score cutoff for automatic approval (the example approves at 740 and above, rejects 0–739).
  The cutoff is a customer decision; the example value is not a default.

## Decision matrix contract

Drive nested `decision-matrix-foundation` to create and activate a decision matrix with the exact name
`IsSTPApplication`:

| Column header (apiName) | columnType | dataType |
|---|---|---|
| `CreditScore` | `Input` | `NumberRange` |
| `IsSTP` | `Output` | `Boolean` |

Row contract (example values — replace with the customer's cutoff):

| CreditScore | IsSTP |
|---|---|
| `min 0, max 739` | `false` |
| `min 740, max 9999` | `true` |

Use the exact `CalculationMatrixColumn` enum tokens (`NumberRange`, `Boolean`) — not the English
labels.

**Runtime-critical (org-verified): the matrix needs `CalculationMatrix.Type="Standard"`, and its rows are
direct `CalculationMatrixRow` inserts keyed by an MD5-hash `Name`.** The one thing that stops an
`IsSTPApplication` matrix from evaluating is a null `Type` on the `CalculationMatrix` — its derived
`MatrixType` then reads null and the BRE lookup throws "Unsupported Matrix type null", surfaced as
*"there isn't any output for the specified input parameters."* Set `Type="Standard"` right after creating
the matrix. Rows are inserted directly as `CalculationMatrixRow` sObjects (the Connect
`post-decision-matrix-rows` write 500s on the verified org); each row's `Name` MUST be the engine's MD5
hash of the input columns (for `CreditScore`, `md5("CreditScore" + boundary)`), and its `InputData`
carries the **band-boundary value as a string** (`{"CreditScore":"0"}`, `{"CreditScore":"740"}` — not a
`{"min","max"}` object). The `NumberRange` **bands are defined once on the column's `RangeValues`** (a
comma-separated boundary list, e.g. `0,740,10000`) at column-creation time — it cannot be edited once the
version is enabled or the matrix has more than one version. Rows can only be written while the version is
a **draft** (`IsEnabled=false`). Pick a sensible top boundary (e.g. 10000). Delegate the whole
Type+column+row+activate sequence to `decision-matrix-foundation`, which owns this ordering and the hash
algorithm.

**Name is a hard contract.** The matrix name MUST be exactly `IsSTPApplication`, because it must match
the decision-matrix action element name inside the `DigitalLendingDFIsSTPApplication` OmniScript. A
differently named matrix will not drive the applicant's confirm-offer / submitted-offer pages. Do not
create a variant name.

## OmniScript verification and activation

The `DigitalLendingDFIsSTPApplication` OmniScript is **delivered by a Discovery Framework template, not
created by this sibling.** Verify and activate it:

1. Confirm the `DigitalLendingDFIsSTPApplication` OmniScript exists in the target org (App Launcher →
   OmniStudio → OmniScripts, or a read of the `OmniProcess` by name / by
   `type='DigitalLendingDF' AND subType='IsSTPApplication'`).
2. Confirm it contains a decision-matrix **action element** named `IsSTPApplication` — the same name as
   the matrix created above. This is a static read of `OmniProcessElement.PropertySetConfig`
   (`"matrixName":"IsSTPApplication"`), which is present regardless of the OmniScript's active state.
3. **Activate it if it is inactive.** Template deploys land the OmniScript `IsActive=false`, version 1.
   Activate by setting `OmniProcess.IsActive=true` (the field is directly updateable) and read it back to
   confirm `isActive:true` with `propertySetConfig` preserved. Only an active version is loadable at
   runtime.

**Blocker, not a build.** If the OmniScript is absent, stop and report a blocker: the
`DigitalLendingDFIsSTPApplication` OmniScript must be deployed from the Discovery Framework / Digital
Lending sample template, which is owned outside this skill (see `digital-origination-initial-setup` for
enabling sample templates; materializing the OmniScripts requires deploying the template package).
Report exactly what is missing and which artifact provides it; do not attempt to author the OmniScript
here. The matrix build above still completes independently and its result is reported.

If the OmniScript exists but references a different action-element name, report the mismatch and the
required name (`IsSTPApplication`) rather than silently renaming either side.

## Idempotency and rollback

- Reuse an exact-match `IsSTPApplication` matrix rather than creating a duplicate; on a shape mismatch
  present the diff and stop.
- Rollback removes only rows added by this run, and only after confirming the OmniScript does not
  depend on them.
- Never modify or delete the delivered OmniScript.

## Output contract

Return the `IsSTPApplication` matrix ID/version, active status, verified columns and rows, the live BRE
lookup result proving the matrix evaluates (a credit score above the cutoff returns `IsSTP=true`, below
returns `false`), and the OmniScript verification result (present, active, and references
`IsSTPApplication`, or the specific blocker/mismatch).

## Definition of done

The `IsSTPApplication` matrix is Active with the approval/rejection rows **and returns a decision from a
live `POST /connect/business-rules/decision-matrices/IsSTPApplication` lookup** (not merely readable via
the builder GET), and the `DigitalLendingDFIsSTPApplication` OmniScript is verified to reference it and is
Active — or the missing-OmniScript blocker is reported explicitly. A partial run is never reported as
complete.
