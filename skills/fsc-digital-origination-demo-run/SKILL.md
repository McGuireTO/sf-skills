---
name: fsc-digital-origination-demo-run
description: "Demonstrate that a completed Digital Origination (Digital Lending) setup actually works, by driving the `DL_Test_`-tagged sample records created by `digital-origination-sample-data-setup` through the configuration the six setup acts stood up — and narrating the before/after so the admin SEES the effect. Runs three demonstrations against one sample loan application: (1) Stage Management, the headline — read the Compliant Data Sharing participant access before, PATCH the ApplicationFormProduct Stage along an allowed transition, poll the autolaunched CDS Flow to completion, re-read, and show the access / applicant-visible-status / parent Application-Form stage that changed because of the decision matrices; then show a disallowed transition is BLOCKED, proving the transition restriction; (2) the Business Rules Engine — run each of the three decision-matrix lookups with the sample applicant's inputs and show each returns a decision; (3) Pricing — run the price simulation with the sample loan and show it returns a rate. Ends by offering to tear down the tagged sample records (default yes). \"Demonstrate the Digital Origination setup\", \"show me the setup working\", \"run the stage transition on my test loan\", \"prove the BREs / pricing fire\", or \"test the setup with the sample data\" route here. Read-mostly: its only writes are the demonstrative stage PATCH and the optional teardown deletes — it never re-runs a setup act. Digital Origination is the renamed Digital Lending feature; the objects and APIs still carry the DigitalLending name."
metadata:
  version: "1.0"
  cliTools:
  - tool:
    - "sf"
    semver: ">=2.0.0"
---

# Digital Origination — demonstration run

Prove the setup works by driving the sample data through it and **narrating what changed and why**.
This runs after `digital-origination-sample-data-setup` has seeded the `DL_Test_`-tagged record graph;
it demonstrates the three capabilities whose effects are observable, then offers to clean up.

The value of this skill is the **before → action → after** narration: the admin didn't watch a ~2–3
hour unattended build, so seeing a real loan application move through the machinery — with the access
and statuses visibly flipping *because of the matrices and transitions they configured* — is the proof
that the setup is live.

## ⚠️ Naming: Digital Origination IS Digital Lending (read first)

Same as the rest of the family: the labels say "Digital Origination," the objects and APIs
(`ApplicationFormProduct.Stage`, the `HomeLoan_CDS_Config` decision matrix, the
`Digital_Lending_Stage_Management` Flow, `LendingProductConfigContext`) still carry the DigitalLending
name. Use the API names against the org.

## Prerequisites

1. **The sample data exists** — the `run_tag` handle from `digital-origination-sample-data-setup`: the
   `ApplicationFormProduct` id (the transition target), its current `Stage`, the proposal inputs, and the
   participant ids. If it was not passed in, query for the tagged graph; if none exists, route back to
   `digital-origination-sample-data-setup` and stop (do not demonstrate against nothing).
2. **The setup being demonstrated is complete** — Stage Management (active stage definition, transitions,
   CDS Flow + Apex, the three decision matrices), the BRE matrices, and pricing (an active pricing
   procedure bound to the recipe). This skill demonstrates them; it does not configure them.
3. **Target org alias and acting admin resolved** (passed down; do not re-resolve).

## The three demonstrations

Run them in this order. Stage Management is first because it is the headline — the one capability whose
effect is observable *on a record*.

### Demo 1 — Stage Management (the headline: a live, record-observable transition)

This is the demonstration that proves the transition-and-access model works. Do all four steps and show
the diff — do not summarize; the point is the visible change.

1. **Read access BEFORE.** For the sample `ApplicationFormProduct` at its current `Stage` (e.g. Intake),
   read and print the current Compliant Data Sharing participant access for each role — the banker has
   Read/Write at Intake, the underwriter has none. Also read the current applicant-visible-status and the
   parent Application-Form stage. This is the baseline.
2. **Do an ALLOWED transition.** `PATCH … /sobjects/ApplicationFormProduct/<id>` setting `Stage` to the
   next stage along a **defined** transition (e.g. Intake → Submitted — a move that exists in the
   transition map). This is the single demonstrative write.
3. **Poll for the recompute — and know when it will NOT fire headlessly.** In the product UI the `Stage`
   change fires the `Digital_Lending_Stage_Management` autolaunched Flow, which runs the CDS Apex and
   reads the three decision matrices. Treat any `PATCH` 2xx as *in progress*, not *done*, and poll for the
   recomputed access / status before reading the "after." **But observed live (fsc-dop7): a bare
   `sObject` REST `PATCH` of `Stage` does NOT trigger the autolaunched Flow — the applicant-visible-status
   and parent form stage do not recompute on their own.** The Flow fires through the guided OmniScript /
   UI stage-change action, not a raw field write. So: poll a bounded number of attempts; if the recompute
   does not land (it typically will not on a headless PATCH), do **not** wait indefinitely and do **not**
   report it as fired — fall back to the matrix-output proof in the note below and say plainly that the
   Flow-driven recompute runs through the UI path, not the raw PATCH.
4. **Read access AFTER and show the diff.** Re-read the participant access, the applicant-visible-status,
   and the parent Application-Form stage, and print the **before → after** change explicitly, attributing
   each change to the artifact that drove it:
   - who gained/lost access — *from the `HomeLoan_CDS_Config` matrix*,
   - the new applicant-visible status — *from `AFPStage_To_ApplicantVisibleStatus`*,
   - the new parent form stage — *from `AFPStage_To_AFStage`*.
5. **Show the DISALLOWED transition — and where the restriction lives.** Attempt a move that is **not**
   in the transition map (e.g. Submitted → Intake). In the guided UI this is rejected, proving the `Stage`
   field is restricted to the transitions the setup defined; a UI rejection is the *expected, successful*
   proof. **But observed live (fsc-dop7): a bare `sObject` REST `PATCH` of the disallowed move is NOT
   rejected — the raw REST layer does not enforce the transition map** (consistent with the Flow not
   firing on a raw PATCH: enforcement, like the recompute, runs through the guided OmniScript / UI
   stage-change action). Report this faithfully — do **not** dress a raw PATCH that succeeded up as a
   "blocked" proof. When you only have raw REST, prove the restriction the way the setup encodes it:
   the transition map (`StageTransition` rows: which `FromStageValueId → ToStageValueId` pairs exist) has
   no Submitted → Intake row, so the guided path would reject it. Restore the record to the allowed
   end-state (e.g. `Submitted`) after the check.

> **Note on the CDS read surface:** read participant access through whatever the org exposes for reading
> CDS grants for a record + participant (a fresh sObject/read of the participant access, or the CDS read
> the stage-management setup verified). If no headless read of the recomputed access is available on this
> org, fall back to showing the two matrix outputs that drive it (the applicant-visible-status and parent
> form stage, which the BRE lookup CAN return) and say so — the transition + the matrix outputs still
> prove the chain fired; be explicit that the participant-access read was substituted.

### Demo 2 — Business Rules Engine (the three decision matrices return a decision)

For each of the three BRE decision matrices the setup activated, run a live lookup with the sample
applicant's inputs and show it returns an output (not the "no output for the specified input parameters"
error):

- `POST /connect/business-rules/decision-matrices/<MatrixName>` with body
  `{"inputs":[{"input":[{"name":<col>,"value":<val>}]}]}`, using the sample proposal's inputs (credit
  score, product/applicant type, level) as the values.
- Run all three: **Disclosures & Consent**, **Document Upload**, and **STP eligibility**. Print each
  matrix's returned decision (e.g. STP `IsSTPApplication` true/false for the sample credit score, the
  document-type label, the data-use-purpose).
- Match the input casing to the column `apiName` exactly — a camelCase input against a PascalCase column
  silently returns "no output." If a matrix returns no output, report it as a gap (the setup's matrix may
  need a row for these inputs) rather than dressing it up as a hit.

#### Credit-score outcome scenarios (STP eligibility — our thresholds)

The `IsSTPApplication` lookup is stateless — it returns a decision for whatever credit score you pass,
independent of the seeded record's stage — so demonstrate the **outcome differences the setup encodes**
by running it for the documented scenario scores. This is the headless-provable slice of the reference
validation script's borrower scenarios: the decision-time branch differs even though we cannot headlessly
walk each application to its terminal stage (see the raw-PATCH limitation in Demo 1). The STP cutoff is a
**configured matrix row, not a fixed constant** — do not hardcode it; the boundary below reflects what the
live `IsSTPApplication` matrix returned on fsc-dop7 (probed score-by-score: **739 → `false`, 740 →
`true`**), so the cutoff on that org is **740**, and the minimum qualifying score is **620**. On any org,
**verify the boundary against the matrix** (probe around the expected score) rather than trusting a
documented number — a matrix rebuilt with a different row moves it:

| Scenario | `CreditScore` input | Expected `IsSTP` | What it proves |
|---|---|---|---|
| Golden path (manual) | 680 | `false` | Qualifies but below the STP cutoff → would go to manual underwriting |
| STP auto-approve | 780 | `true` | At/above the STP cutoff → straight-through auto-approval |
| Disqualification | 590 | `false` | Below the 620 minimum qualifying score |
| Cutoff boundary | 739 / 740 | `false` / `true` | Confirms the live fsc-dop7 cutoff row is `0–739 = False`, `740+ = True` (probe to confirm on other orgs) |

- First run the lookup for **the credit score actually seeded on the sample proposal** and confirm it
  matches the expected decision the seeder handed off. Then optionally run the other scenario scores to
  show the branch — narrate each as "at score X the application would {auto-approve / go to manual
  underwriting / be disqualified}."
- Be precise about what this proves: the **decision-matrix branch** fires correctly per credit score.
  Do **not** claim the application auto-advanced to Approved/Rejected on a raw PATCH — that stage
  automation runs through the guided UI path (Demo 1), not the headless REST layer. The `IsSTP` decision
  is the honest, headless-provable evidence of the STP rule.

### Demo 3 — Pricing (the price simulation returns a rate)

Run the Evaluate Price simulation for the sample loan and show it returns a rate driven by the pricing
procedure the setup bound:

- Generate the canonical simulation payload with
  `GET /connect/core-pricing/simulationInputVariablesWithData?contextDefinitionId=LendingProductConfigContext__stdctx&contextMappingId=LendingProductConfigMapping&expressionSetVersionId=<active 9QM version>&entityId=<the sample ApplicationForm id>` — do not hand-guess the `jsonDataString`.
- `POST /connect/core-pricing/pricing` (Evaluate Price) with all four required inputs:
  `pricingProcedureId` (the **ExpressionSetDefinition** `9QA…` id — verified live on fsc-dop7:
  passing the `9QM…` version id or the `9QL…` ExpressionSet id both fail with `SF-Pricing-00004
  "couldn't find the pricing procedure"`; only the `9QA…` ESD id resolves), `contextDefinitionId`
  (`LendingProductConfigContext__stdctx`), `contextMappingId` (bare `LendingProductConfigMapping` — the
  slash-path form fails), and the generated `jsonDataString`.
- Print the returned rate (e.g. `pricingResult.InterestRate[0].value`) and its `Completed` status, and
  tie it back to the ProductListRate the pricing setup configured (the demo hit should match the
  configured list rate for the sample product).

## Teardown (offer after the demos — default yes)

After the demonstrations, **ask whether to delete the sample records**, defaulting to yes so the org is
left clean:

> "Demo complete. Shall I delete the `DL_Test_` sample records I created (the loan application, its
> product, proposal, and the participant records)? (yes / no — default yes)"

- On **yes** (or no answer): delete every record carrying the `run_tag`, in reverse dependency order
  (proposal → application-form-product → application-form; participant records), and report exactly what
  was deleted. Only delete records that carry the `run_tag` — never touch setup artifacts (matrices, the
  stage definition, the Flow, permission sets) or any record without the marker.
- On **no**: leave the records and tell the admin the `run_tag` so they can find and inspect them in the
  UI, and clean them up later.

**Teardown deletes sample data only.** It never removes anything the six setup acts created — the marker
is the boundary. If a delete fails (a record is referenced), report it and continue with the rest rather
than aborting.

> **Deletion mechanics (observed live).** Use `sf data delete record --sobject <obj> --record-id <id>`
> for each delete — a raw `sf api request rest --method DELETE …` fails with `No 'mode' found in 'body'`
> (the REST helper demands a body mode on DELETE). Always **re-query each id after deleting** to confirm
> `rows=0`; a delete tool that reports success is not proof the row is gone until the read-back confirms
> it.

## Reporting discipline (applies throughout)

- **Show before → after, not just after.** The demonstration's value is the visible change; always print
  the baseline and the post-transition state side by side.
- **Advance only on fresh read-back.** The stage transition fires an async Flow — poll to a terminal
  state before reading the "after"; a bare 2xx is in progress, not proof.
- **Attribute each change to the artifact that drove it** (which matrix, which transition), so the admin
  connects the effect to the setup step that produced it.
- **Report faithfully.** A disallowed transition blocked *in the guided UI* is the expected proof; a raw
  REST `PATCH` that silently succeeds is NOT a block — report it as raw-layer non-enforcement and prove
  the restriction from the `StageTransition` map instead. Likewise, a recompute that does not fire on a
  headless PATCH, a matrix that returns no output, a missing pricing procedure, or an unavailable CDS read
  is a gap reported plainly — never a demonstration dressed up as working when it did not fire.

## Standalone vs orchestrated

- **Orchestrated** (the common path): the `digital-origination-setup-orchestrator` offers the
  data-and-demo step once, after the six-act consolidated summary; on the admin's yes it runs
  `digital-origination-sample-data-setup` then this skill straight through, then teardown.
- **Standalone:** invoked directly ("demonstrate the setup", "run the stage transition on my test
  loan"). Resolve or create the sample data first (route to `digital-origination-sample-data-setup` if
  the tagged graph is absent), then run the three demos and offer teardown.

<!-- skill-validate: ignore-start -->
<!-- codey:operations start -->
## Operations Reference

Operations this skill uses — routing and dependency reference.

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `preflight-sample-data-exists` | validate | — | `SOQL SELECT Id,Title FROM ApplicationForm WHERE Title LIKE 'DLTEST_%'` | — |
| `preflight-context-service` | validate | — | `GET /services/data/v67.0/connect/context-definitions` | `preflight-sample-data-exists` |
| `demo-1-read-participant-access-before` | read | — | `SOQL over CDS participant grants + AVS + parent form stage` | `preflight-sample-data-exists` |
| `demo-1-patch-stage-allowed` | write | — | `PATCH /services/data/v67.0/sobjects/ApplicationFormProduct/{id}` | `demo-1-read-participant-access-before` |
| `demo-1-read-participant-access-after` | verify | — | `SOQL re-read of participant grants + AVS + parent form stage` | `demo-1-patch-stage-allowed` |
| `demo-1-verify-transition-map` | verify | — | `SOQL SELECT FromStageValueId,ToStageValueId FROM StageTransition` | `demo-1-read-participant-access-after` |
| `demo-2-bre-lookup-homeloan-cds-config` | read | — | `POST /services/data/v67.0/connect/business-rules/decision-matrices/HomeLoan_CDS_Config` | `preflight-sample-data-exists` |
| `demo-2-bre-lookup-afpstage-to-avs` | read | — | `POST /services/data/v67.0/connect/business-rules/decision-matrices/AFPStage_To_ApplicantVisibleStatus` | `demo-2-bre-lookup-homeloan-cds-config` |
| `demo-2-bre-lookup-afpstage-to-afstage` | read | — | `POST /services/data/v67.0/connect/business-rules/decision-matrices/AFPStage_To_AFStage` | `demo-2-bre-lookup-afpstage-to-avs` |
| `demo-3-pricing-simulation-inputs` | read | — | `GET /services/data/v67.0/connect/core-pricing/simulationInputVariablesWithData` | `preflight-context-service`, `preflight-sample-data-exists` |
| `demo-3-pricing-evaluate` | read | — | `POST /services/data/v67.0/connect/core-pricing/pricing` | `demo-3-pricing-simulation-inputs` |
| `teardown-delete-sample` | delete | — | `sf data delete record --sobject <obj> --record-id <id> (per record)` | `demo-3-pricing-evaluate` |
| `teardown-verify-rows-zero` | verify | — | `SOQL SELECT COUNT(Id) FROM ApplicationForm WHERE Title LIKE 'DLTEST_%' (per object)` | `teardown-delete-sample` |
<!-- codey:operations end -->
<!-- skill-validate: ignore-end -->
