---
name: fsc-digital-origination-coordinate
description: "Master end-to-end orchestrator for standing up Financial Services Cloud (FSC) Digital Origination (formerly Digital Lending) in a live org — the single entry point that runs the WHOLE setup journey across all six capability areas in strict dependency order and reports one consolidated result. \"Set up Digital Origination end to end\", \"run the full Digital Origination setup\", \"configure Digital Origination from scratch\", \"set up digital lending completely\", \"do the whole DOP setup\", \"stand up loan origination end to end\", or \"run every Digital Origination setup step in order\" means running all six acts through their existing sibling skills: Act 1 Initial Setup (Discovery Framework + KYC + Digital Origination + Import/Export + Sample-Template enablement + Manage User Access), Act 2 Product Catalog Management (catalog, products, classifications, attributes), Act 3 Pricing (permissions, rate data, BRE decision tables, pricing procedure), Act 4 Sample Template Deployment (deploy + activate the FSC_DL Discovery Framework template), Act 5 Business Rules Engine (Disclosures & Consent, Document Upload, STP eligibility decision matrices), and Act 6 Stage Management (Stage-field transitions + Compliant Data Sharing). Currently runs in AUTONOMOUS mode — the full six-act journey runs unattended, without pausing for input, using each sibling skill's documented sample/example values as the inputs and Product Configurator as the fixed pricing engine. Digital Origination is the renamed Digital Lending feature; the underlying config, org preferences, license, and permission set still carry the DigitalLending name. TRIGGER when the admin wants the whole ordered origination build rather than one specific capability. DO NOT TRIGGER when the admin asks for exactly one capability (\"set up the pricing\", \"deploy the sample template\", \"just turn on Digital Origination\", \"set up stage management\") — route straight to that act's sibling skill instead; and DO NOT TRIGGER for the Initial-Setup-only turn-on journey (\"run Digital Origination Initial Setup\") — that is Act 1's sibling `digital-origination-initial-setup` on its own."
metadata:
  version: "1.0"
---

# Digital Origination master setup orchestrator

## ⚠️ Step 0 (MANDATORY, runs before ANYTHING else) — Load execution guardrails

**Before Preflight, before any read, before any dispatch, invoke the sub-skill
`fsc-mandalorians/digital-origination-execution-guardrails` and read its SKILL.md end-to-end.**
That sub-skill returns eight rules (full-content-never-previews, render-verbatim, gate-in-order,
never-fabricate, evidence-not-assumption, retry-and-re-read, cite-SOR-anchor, if-in-doubt-re-read)
that override default agent behavior for the rest of this run. It is a small, side-effect-free
priming skill; it exists precisely because embedding these rules in this orchestrator's own
`agent_guidance` risks losing them to MCP `describe`-preview truncation.

**Non-negotiable:** if you have not loaded the guardrails skill in this run, stop and load it now —
regardless of which act the admin asks for, regardless of autonomous vs interactive mode. A run
started without Step 0 is a rule-1 / rule-3 violation of the very rules the skill sets. All
downstream text in THIS orchestrator (autonomous-mode language included) is read UNDER those eight
rules; where anything below appears to conflict with a guardrail, the guardrail wins.

Orchestrate the **complete** setup of **Digital Origination** — whose underlying APIs and setup
artifacts still use the **Digital Lending** name — from a licensed-but-unconfigured FSC org to a
working origination configuration. This is the top-level entry point that sequences the six
constituent capability areas in a fixed, dependency-respecting order and reports one consolidated
result.

**This skill owns sequencing, shared-runtime resolution, and gate-on-outcome only.** It does not
duplicate the implementation contracts maintained by its six sibling skills — each act is its own
already-published top-level `fsc-mandalorians/*` skill, delegated to in order. Act N runs only after
every act it depends on has reached its end state.

## ⚠️ Naming: Digital Origination IS Digital Lending (read first)

Digital Origination is the renamed Digital Lending feature. The product name is **Digital
Origination** (and the Setup surface is "Digital Origination Initial Setup"), but the org
preferences, license, permission set, Discovery Framework feature ids, and every backing API still
carry the **DigitalLending** name (`digitalLendingPref`, `DigitalLendingAdminUser`, the FSC_DL sample
template, `LendingProductConfigContext`, etc.). Both names refer to the same thing throughout this
journey. Do not treat a `DigitalLending*` identifier as stale or wrong.

## Run mode — AUTONOMOUS (unattended) is the active default

**This orchestrator currently runs in AUTONOMOUS mode: run the entire journey end to end without
pausing for input or confirmation, using the documented sample/example values from each act's sibling
skill as the concrete inputs, and continue through every act to the end.** This is a deliberate,
temporary override of the children's "never infer customer inputs / always confirm" discipline,
chosen so the full six-act journey can be validated in one unattended pass on a test org. A later
revision will flip this back to interactive/manual mode.

Autonomous-mode rules (these override the staged-run rule, the confirmation gates, and the
"never infer" invariant wherever they conflict — for this mode only):

1. **Do not stop to ask the admin anything *after the run starts*.** No approve/reject gates, no
   "continue to the next act?" prompts, no request for business inputs once underway. Run Act 1 → Act
   6 straight through. **The only sanctioned pause *during the run* is the up-front plan-and-confirm
   gate** (see "Pre-run plan & confirmation gate" below): before Act 1, present the ordered step list
   with rough timings and get a single go-ahead. After that go-ahead, the "never pause" rule holds
   absolutely for the rest of the journey. (One further pause is allowed *after* the run has fully
   completed and the consolidated summary is rendered — the single post-setup verification offer; see
   "Post-setup verification offer." It is not a mid-run pause.)
2. **Use the sample/example values each sibling skill documents as the actual inputs.** The
   personal-loan catalog + products + attributes (Act 2), the example base rates / credit-score tiers
   / term tiers / effective dates (Act 3), the FSC_DL template + activate the deployed OmniScripts/IPs
   (Act 4), the Disclosures & Consent + Document Upload + STP example matrices (Act 5), and the
   example stage picklist values / transition map / per-stage access policy / consent text (Act 6).
   Where a sibling gives more than one example, take the first/primary one.
3. **Pricing engine is fixed to Product Configurator** (the documented default and the proven path).
   Do not deliberate — Act 3 takes the Product Configurator branch, not Salesforce Pricing.
4. **BRE (Act 5) sets up all three features** — Disclosures & Consent, Document Upload, and STP
   eligibility — with their example matrices, since no admin is present to narrow the request.
5. **Activate opt-in artifacts autonomously.** Where a sibling would normally ask which subset to
   activate (e.g. Act 4's deployed OmniScripts / IPs / DataRaptors), activate the full set the sample
   template ships, and report exactly what was activated.
6. **Never fabricate a value that isn't an org fact or a documented example.** Autonomous ≠
   inventing. If a required input is neither an example in the skill nor readable from the org,
   record it as a gap and continue; do not guess a raw value.
7. **A genuinely headless-impossible step does not stop the run.** If a step has no headless write at
   all (a legal-consent UI-only toggle), attempt every headless avenue first; if truly impossible,
   record it as an explicit gap in `act_ledger` and CONTINUE to the next act rather than halting.
   (Contrast with a hard dependency failure — see Run Order gate-on-outcome — which still stops a
   dependent act.)

Everything below (Preflight, ordering, dependency gates, definition of done, consolidated report)
still applies; autonomous mode changes only *whether the orchestrator pauses* and *where its inputs
come from*, not the order or the correctness checks.

## Scope & definition of done — READ THIS FIRST

**Every ask runs the orchestrator Preflight gates first** (resolve target org and acting admin,
validate the true external prerequisites). Only once `preflight_ok` holds does routing proceed. **In
autonomous mode the orchestrator then presents the pre-run plan & confirmation gate once (the ordered
step list with rough timings — see below), and on the admin's go-ahead runs all six acts, in order,
Act 1 → Act 6, without pausing again.**

**You are NOT done until every act in scope has reached its own end state and read back as
configured.** Each act is idempotent and self-verifying; this orchestrator advances only on a
sibling's own fresh read-back evidence, never on an assumed result. If a true prerequisite (edition,
license, add-on) is unmet, the Preflight gate reports which one explicitly and **stops** — those are
the customer's or Salesforce's provisioning decisions, not something any act can fix.

**This orchestrator writes nothing itself.** Every write is performed by the delegated sibling that
owns it. The orchestrator resolves the shared runtime once, routes, gates, and consolidates.

## Session state (track across the conversation)

- `guardrails_loaded` — bool; the Step 0 execution-guardrails sub-skill has been invoked and its
  SKILL.md read end-to-end into this run's context. Must be `true` before **anything else** runs
  (Preflight included). A resumed session that already has this flag `true` can skip the Step 0
  re-invocation; a fresh session always starts with `guardrails_loaded=false` and MUST load it
  first. Contrast with `preflight_ok` (org+admin+license floor) — guardrails come before Preflight.
- `target_org_alias` — the org being configured. In autonomous mode this is the already-connected
  org (taken, not asked). Set during Preflight gate 1.
- `acting_admin` — resolved `userId` / `username` for the admin performing setup. Set during Preflight
  gate 1 and passed to every act so no act re-resolves it.
- `api_version` — resolved once in Preflight and passed down.
- `preflight_ok` — bool; both orchestrator preflight gates passed. Must be `true` before **any** act
  runs.
- `plan_confirmed` — bool; the admin gave the single up-front go-ahead at the pre-run plan &
  confirmation gate. Must be `true` before Act 1 runs; the run does not start without it.
- `pricing_engine` — `product-configurator` (default) or `salesforce-pricing`; captured before Act 3
  so the pricing sibling takes the right engine branch.
- `bre_features` — which of Disclosures & Consent / Document Upload / STP the admin wants in Act 5
  (they are independent; set up only the requested ones).
- `act_ledger` — the running record of the whole run, one entry per act, that the final consolidated
  summary is rendered from. Each entry captures: the act's status (`✅ done / ⚠️ partial (gap
  reported) / 🔒 blocked / ⬜ not-started`), **what the sibling created or changed** (records created
  with their ids/API names/counts, permission sets assigned, preferences flipped, matrices/procedures
  activated), **which sub-steps ran and their success/failure**, and any **gaps or manual checkpoints**
  the act reported. Append to it as each act reports back — never collapse an act to its status glyph
  alone; the record-level detail is what the end-of-run summary itemizes.
- `pending_checkpoint` — anything a sibling paused on awaiting the admin (a guided-Setup checkpoint, a
  legally-gated UI toggle, an approve/reject on staged values).
- `demo_offered` / `demo_accepted` — bool; after the consolidated summary the orchestrator makes the
  single post-setup offer to create sample data and demonstrate the setup (see "Post-setup verification
  offer"), and records whether the admin accepted. Only set after all in-scope acts have reported.
- `sample_data_handle` — the `run_tag` + record ids returned by
  `digital-origination-sample-data-setup`, threaded into `digital-origination-demo-run` so the demo
  drives the records the seed created (and the teardown deletes exactly them).

## Preflight — orchestrator-level gates (hold before any act)

**Preflight runs AFTER Step 0 (guardrails) but before any act.** The guardrails skill must already
have been loaded before Preflight begins — Preflight itself is executed under those rules
(especially rule 5: evidence, not assumption — every Preflight check is a live read, not a
memoized value).

**These two gates then run first, no matter which act the admin's ask routes to.** They are not part
of any single act — they are the floor the whole journey stands on. Run them before routing, and
re-satisfy them (a fresh auth, a fresh org-state read) at the start of any resumed session; never
carry a stale result forward.

1. **Resolve the shared runtime.** Use the connected/target org alias (in autonomous mode, take the
   already-connected org — do not pause to ask which org). Resolve `api_version` (`GET
   /services/data/`) and `acting_admin` (`GET /services/data/v<apiVersion>/chatter/users/me`) via
   `dispatch` / `dispatch`. If the identity call fails with an auth error, STOP and report that the
   MCP connection needs re-authentication (an auth failure is the one thing autonomous mode cannot
   work around). Capture `username`, `userId`, `apiVersion` and pass them to every act.

2. **Validate true prerequisites (check only — cannot be fixed by this skill).** Surface each as an
   explicit ✅/❌ line with the value you queried, even when all pass: Lightning Experience edition
   (Enterprise / Unlimited / Developer), the Financial Services Cloud + Digital Lending license
   family present and Active, and admin access to the org. Any unmet item → report which one,
   redirect, **stop**. Act 1 (`digital-origination-initial-setup`) owns the authoritative detail of
   this prerequisite check; this gate is the fast floor — defer to Act 1 for the full validation.

## Pre-run plan & confirmation gate (runs once, after Preflight, before Act 1)

**Immediately after both Preflight gates pass and before delegating to Act 1, present the full run
plan and get one explicit go-ahead.** This is the single sanctioned pause of the whole journey — it
exists so the admin knows what is about to run and roughly how long it takes before a ~2–3 hour
unattended sequence begins. Once the admin confirms, autonomous mode's "never pause" rule holds for
the entire remainder of the run.

Show the ordered act list with **the records / config each act will create** (a high-level record
summary, not field detail) and a rough time estimate for each, the total estimate, and the target org
/ acting admin resolved in Preflight. Then ask a single yes/no: **"Proceed with the full Digital
Origination setup on `<target_org_alias>`?"**

> **Digital Origination — full setup plan** (target org `<target_org_alias>`, admin `<acting_admin>`)
>
> | # | Act | Records / config this act will create | Rough time |
> |---|---|---|---|
> | 1 | Initial Setup | Discovery Framework + Know Your Customer features enabled; a Digital Lending admin permission-set clone created + assigned; Digital Origination, Import/Export, and Sample Templates org preferences turned on; Manage User Access completed | ~10 min |
> | 2 | Product Catalog (PCM) | 1 product catalog, its categories/subcategories, 1 Home Loan product, the LoanTerm picklist, 5 product attribute definitions, 1 Home Loans classification (with attribute defaults), and the product↔classification / product↔category bindings; PCM permission sets assigned | ~10 min |
> | 3 | Pricing | pricing permission sets + `CorePricingPreference`; Product List Rate, credit-score-tier, and term rate-data records; 3 BRE pricing decision tables; the `NGPDefaultRecipe` mapping; and 1 pricing procedure (Product Configurator engine) — the longest act | ~60–90 min |
> | 4 | Sample Template Deployment | the FSC_DL Discovery Framework sample template deployed + its AssessmentTemplate materialized; the deployed OmniScripts / IntegrationProcedures / DataRaptors activated | ~5–10 min |
> | 5 | Business Rules Engine | 3 decision matrices — Disclosures & Consent, Document Upload, and STP eligibility — created, populated, and activated, with their Discovery Framework wiring | ~15–20 min |
> | 6 | Stage Management | the Stage-field restriction on `ApplicationFormProduct`, Compliant Data Sharing (CDS) with its CDS Apex + autolaunched Flow, 3 stage decision matrices, 1 stage definition, and the stage transitions | ~20–25 min |
> | | **Total** | | **~2–3 hours** |
>
> This lists the records/config each act creates so you know what will change — it does not enumerate
> the field values that go into them. Timings are rough estimates from a reference run; actual
> duration varies with org state, async deploy/activation polling, and which acts are already partially
> configured (idempotent re-runs are faster).
>
> **Smart defaults applied** — to reach a working setup fast without a per-act interview, autonomous mode
> applies these values (each is a documented default the admin can override by asking):
>
> | Setting | Default value we apply |
> |---|---|
> | Product | **Home Loan** (classification & category **Home Loans**) |
> | Loan amount range | **1,000 – 100,000** (`MinLoanAmount` 1,000, `MaxLoanAmount` 100,000; org's default currency) |
> | Loan term options | **180 / 240 / 360 months** (15 / 20 / 30-year home-loan terms) |
> | Offer valid period | **30 days** |
> | Intake OmniScript | **`ApplicantIntakeSecured`** (Home Loan is secured) — `ApplicantIntake` for an unsecured product |
> | Pricing basis | Base **List Rate 5% (Percent)** (fixed default), then **credit-score-adjusted** + **term-adjusted** (3 decision tables: `ProductListRateDT`, `CreditScoreBasedAdjustmentDT`, `TermBasedAdjustmentDT`); engine = **Product Configurator** |
> | Sample template | **`FSC_DL`** ("Digital Lending" Discovery Framework sample template) |
> | Stage flow | **Intake → Submitted → In Review → Underwriter/Auto Approved → Customer Approved → Contract Generation → Signature Complete** (+ Need More Info / Rejected / Book to Core branches) |
> | Roles & access | participants **banker / underwriter / applicant**; CDS via perm set **`FSCCDSUser`** + groups **`Agent_Group`** / **`Underwriter_Group`**; admin gets a **`DigitalLending`** clone with `DigitalLendingAdminUser` |
> | BRE decision matrices | **`IsSTPApplication`** (STP eligibility), **Disclosures & Consent**, **`LendingDocumentTypes`** (document upload) |
> | STP credit cutoff | auto-approve at **740+**, minimum qualifying **620** (proven live on fsc-dop7; a configured matrix row, not a fixed constant) |
>
> **Proceed with the full setup on `<target_org_alias>`?** (yes / no) — or reply **"show details"** to
> see the full record-and-data breakdown first.

- **Only proceed on an explicit yes.** On no / no answer, stop cleanly without running any act.
- **This gate is confirmation only — it does not ask for business inputs.** Inputs still come from
  each sibling's documented examples per autonomous rule 2; the gate never turns into a per-act
  interview.
- **Two levels of detail: the Smart-defaults table above is the brief; the "Detailed record & data
  reference" section below is the deep dive.** After showing the plan + Smart-defaults table, the admin
  can ask for the full detail (e.g. "show details", "what exactly gets created", "deep info on the
  records"). **On that request, render the "Detailed record & data reference" section below verbatim**
  — it is static, self-contained content, so quote it directly rather than re-deriving values from each
  sibling skill (which risks drift). Then return to the yes/no. Do not volunteer the detailed section
  unprompted, and do not let the question turn the gate into a per-act interview. If the admin asks
  about only one act, render just that act's row group from the detailed section.
- **This is the only pause.** Do not re-confirm between acts. A resumed session re-runs Preflight and
  re-shows this gate once (state may have changed), then runs straight through again.

## Detailed record & data reference (render verbatim only when the admin asks for detail)

**This section is static reference content.** Render it (or the relevant act's part) verbatim when the
admin asks "show details" / "what exactly gets created" / "deep info on the records" at the pre-run gate.
It lists the concrete records each act creates and the actual field values the smart defaults apply — the
same values the sibling skills use, consolidated here so the answer is stable and does not vary by model
run. Values marked *(admin-supplied)* have no fixed default and are taken from the admin's own data;
values marked *(proven fsc-dop7)* were verified live and are the applied defaults.

### Act 1 — Initial Setup
- **Features enabled:** Discovery Framework, Know Your Customer.
- **Org preferences turned on:** `digitalLendingPref`, Import/Export, Sample Templates
  (`enableDiscoveryFrwrkSampleTemplate`), `CorePricingPreference`, `DiscoveryFrameworkMetadata`.
- **Permission sets / license:** a custom **clone of the `DigitalLending`** permission set carrying the
  `DigitalLendingAdminUser` system permission, assigned to the acting admin; requires the
  `DigitalLending` + `DigitalLendingPsl` license family Active.

### Act 2 — Product Catalog (PCM)
- **1 product:** `Home Loan`.
- **1 product classification:** `Home Loans` (Code `Home Loans`), assigned to the `Home Loans`
  category; the product is *Based On* this classification.
- **5 attribute definitions:** `MinLoanAmount`, `MaxLoanAmount`, `LoanTerm`, `OfferValidPeriod`,
  `OmniScriptName`.
- **Attribute default values:** `MinLoanAmount = 1000`, `MaxLoanAmount = 100000`, `OfferValidPeriod = 30`,
  `OmniScriptName = ApplicantIntakeSecured` (secured — Home Loan) / `ApplicantIntake` (unsecured).
- **`LoanTerm` picklist values:** `180 Months`, `240 Months`, `360 Months`.

### Act 3 — Pricing
- **3 decision tables:** `ProductListRateDT` (output **List Rate**, Percent), `CreditScoreBasedAdjustmentDT`
  (credit-score-tier adjustment), `TermBasedAdjustmentDT` (term adjustment).
- **Rate data:** one base List Rate record per product with effective start/end dates and the
  **List Rate defaulted to 5% (Percent)** *(fixed default — not admin-gated; override only if the
  admin supplies a specific rate)*; credit-score-tier and term adjustment rows.
- **Pricing wiring:** context `LendingProductConfigContext` (`LendingProductConfigContext__stdctx`),
  mapping `LendingProductConfigMapping`, recipe `NGPDefaultRecipe`; 1 pricing procedure (an
  ExpressionSet, engine **Product Configurator**).

### Act 4 — Sample Template Deployment
- **Template:** `FSC_DL` (label "Digital Lending", module `ui-industries-digitallending-components`)
  deployed; its `AssessmentTemplate` materialized.
- **Activated:** the deployed OmniScripts / IntegrationProcedures / DataRaptors — including the STP
  OmniScript `DigitalLendingDFIsSTPApplication` (verified/activated, not created here).

### Act 5 — Business Rules Engine (3 decision matrices)
- **`IsSTPApplication`** — input `CreditScore` (NumberRange) → output `IsSTP` (Boolean). Rows:
  **0–739 → `false`, 740–9999 → `true`** *(proven fsc-dop7; the cutoff is a configured row)*.
- **Disclosures & Consent** — inputs `ProductId` / `ApplicantType` / `Level` (Text) → `DataUsePurpose`
  (Text). Example row: ApplicantType `Primary Applicant`, Level `ApplicationFormProduct`. Consent/disclosure
  text is *(admin-supplied)*; locale `en_US`.
- **`LendingDocumentTypes`** — inputs `productId` / `applicantType` / `level` (Text) → `docTypeLabel`
  (Text). Document-type labels are *(admin-supplied)*.

### Act 6 — Stage Management
- **1 stage definition:** `Digital Lending Stage Management` (API/Flow `Digital_Lending_Stage_Management`),
  on `ApplicationFormProduct.Stage`.
- **Stage values (14, proven fsc-dop7):** Intake, Submitted, In Review, Need More Info, Underwriter
  Approved, Customer Approved, Auto Approved, Customer Rejected, Underwriter Rejected, Auto Rejected,
  Contract Generation, Awaiting Signature, Signature Complete, Book to Core.
- **Transition map (allowed moves, proven fsc-dop7):** Intake → {Submitted, Auto Rejected}; Submitted →
  {In Review, Need More Info, Auto Approved, Auto Rejected}; In Review → {Need More Info, Underwriter
  Approved, Underwriter Rejected}; Underwriter Approved → {Customer Approved, Customer Rejected}; Auto
  Approved → {Customer Approved, Customer Rejected, Contract Generation}; Customer Approved → Contract
  Generation; Contract Generation → Signature Complete.
- **Compliant Data Sharing:** perm set `FSCCDSUser` (+ `FSCCDSConfigUser`); participant groups
  `Agent_Group` and `Underwriter_Group` (`Group.Type = 'Participant'`); 9 participant roles (No Access /
  Read Write / Read Only across `ApplicationForm` / `ApplicationFormProduct` / `PartyProfile`); CDS Apex
  + autolaunched Flow (`StepType = AutoTask`).
- **3 stage decision matrices:** `HomeLoan_CDS_Config` (stage → participant access:
  `Underwriter_Access`, `Applicant_Agent_Access`), `AFPStage_To_ApplicantVisibleStatus` (stage →
  applicant-visible status), `AFPStage_To_AFStage` (product stage → parent form stage) — all keyed on
  `ApplicationFormProductStage`.

### Post-setup verification (only if the admin opts in after setup)
- **Sample records created** (all tagged `DL_Test_<run_tag>`): 1 `ApplicationForm`
  (`UsageType = 'LoanOrigination'`, marker in `Title`); 1 `ApplicationFormProduct` (the Home Loan
  product, `Stage = Intake`); 1 `ApplicationFormProductProposal` (`Amount`, `Term`, `InterestRate`);
  3 `PartyProfile` participants (banker / underwriter / applicant, the applicant carrying `CreditScore`).
- **Scenario credit scores:** golden path **680** (`IsSTP=false`, manual), STP auto-approve **780**
  (`IsSTP=true`), disqualification **590** (`IsSTP=false`). Seeded on `PartyProfile.CreditScore`.
- **Tests run:** an allowed stage transition (Intake → Submitted) + disallowed-move check; the 3 BRE
  matrix lookups; the price simulation (returns a rate). Then an offer to delete the tagged records.

## Entry point — route on the admin's actual ask

**Default rule (autonomous mode):** after Preflight passes, run the full six-act journey Act 1 → Act
6 in order, without pausing. The routing table below documents how the orchestrator behaves when it is
later switched back to interactive mode; **while autonomous mode is active, the top row governs and
the staged-run rule is suspended.**

| Signal | Where to start |
|---|---|
| **"Set up Digital Origination end to end" / "the whole DOP setup" / "from scratch" / "everything" / no narrowing qualifier (autonomous default)** | **Run Preflight, then Act 1 → Act 6 in order, unattended.** Not done until every act's end state holds. |
| _(interactive mode only)_ A "first"-type qualifier — "just get the org ready first", "run initial setup first" | Run Preflight, then Act 1 ONLY; report Act 1's end state and ask before continuing. **Suspended in autonomous mode.** |
| _(interactive mode only)_ One named capability — "set up the pricing", "deploy the sample template", "set up the BREs", "set up stage management" | Do NOT run the whole journey. Route straight to that act's sibling, after verifying its upstream acts' end states hold. |
| "The org's already set up through Act N" | Run Preflight to confirm, verify Acts 1…N end states are met (idempotent no-ops), then resume at Act N+1. |

### Staged-run rule — sequencing qualifiers stop after each act (interactive mode only)

When interactive mode is active and the ask carries a sequencing qualifier like **"first"**, **"before
…"**, or **"just get the org ready"**, treat it as a request to run **one act at a time**: complete
the act, report its end state, then ask whether to continue. **This rule is suspended while autonomous
mode is active** — the journey runs straight through regardless of qualifiers.

## The journey (delegation map)

This orchestrator **chains a sequence of peer skills** — each act is its own already-published
top-level `fsc-mandalorians/*` skill, delegated to in order. Act N runs only after every act it
depends on has reached its end state.

```text
Step 0. Execution guardrails (MANDATORY priming — sub-skill, read-only)
 │
Preflight (org + admin + license floor)
 │
1. Initial Setup ─────────────► foundation: DF + KYC + Digital Origination + Import/Export
 │                               + Sample-Template enablement + Manage User Access
 ├───────────────┐
2. Product Catalog Management   (needs Act 1)
 │
3. Pricing                      (needs Act 1 + Act 2)
 │
4. Sample Template Deployment   (needs Act 1's Sample-Template enablement)
 │
5. Business Rules Engine        (needs Act 1)
 │
6. Stage Management             (needs Act 1 + Act 5 (BRE) + Compliant Data Sharing)
 │
End-of-run consolidated summary (per-act: created/changed, pass/fail, gaps)
```

| Act | Capability | What it does | Peer skill (delegate target) | Depends on |
|---|---|---|---|---|
| **0** | **Execution guardrails (MANDATORY priming)** | Load the eight execution guardrails (full-content/no-previews, render-verbatim, gate-in-order, never-fabricate, evidence-not-assumption, retry-and-re-read, cite-SOR-anchor, if-in-doubt-re-read) into the run's context. Read-only priming; no dispatches, no writes, no records. Must run before Preflight. | `fsc-mandalorians/digital-origination-execution-guardrails` | — (runs first) |
| **1** | **Initial Setup** | Turn on the two prerequisite Discovery Framework features (Discovery Framework, Know Your Customer), prepare + assign the admin-capable Digital Lending permission-set clone, turn on Digital Origination, enable Import or Export, enable Discovery Framework **Sample Templates**, and complete Manage User Access. Validates true prerequisites (edition/license/add-ons). | `fsc-mandalorians/digital-origination-initial-setup` | Preflight |
| **2** | **Product Catalog Management (PCM)** | Assign PCM permission sets; create the Digital Lending catalog, categories/subcategories, the Home Loan product, the LoanTerm picklist, the five product attributes, the Home Loans classification with attribute defaults, and the product↔classification / product↔category bindings. | `fsc-mandalorians/digital-origination-product-setup` | Act 1 |
| **3** | **Pricing** | Pricing permissions + `CorePricingPreference`; Product List Rate / credit-score / term rate data; the three BRE pricing decision tables + `NGPDefaultRecipe` mapping; the selected pricing engine (Product Configurator default, or Salesforce Pricing); the pricing procedure. | `fsc-mandalorians/digital-origination-pricing-setup` | Act 1, Act 2 |
| **4** | **Sample Template Deployment** | Deploy the `FSC_DL` Discovery Framework sample template via async Metadata API, poll to completion, materialize the AssessmentTemplate, enumerate the deployed OmniScripts / IntegrationProcedures / DataRaptors, and activate the admin-selected subset (never auto-activate everything). | `fsc-mandalorians/digital-origination-sample-template-deployment` | Act 1 (Sample-Template enablement) |
| **5** | **Business Rules Engine** | Set up the requested decision-matrix BRE features — Disclosures & Consent, Document Upload, and applicant-eligibility STP — via the shared decision-matrix create/activate mechanic. Independent features; build only the ones requested. | `fsc-mandalorians/digital-origination-bre-setup` | Act 1 |
| **6** | **Stage Management** | Restrict the `Stage` field on `ApplicationFormProduct` to defined transitions and drive Compliant Data Sharing (CDS) so participants gain/lose access per stage — permissions, CDS, the CDS Apex + autolaunched Flow, the three stage decision matrices, the stage definition, and the stage transitions. | `fsc-mandalorians/digital-origination-stage-management-setup` | Act 1, Act 5 (BRE), CDS |

## Run Order (how the orchestrator executes)

Execute the acts strictly top-to-bottom in the delegation-map order. For each act:

0. **Step 0 — Load execution guardrails (MANDATORY, runs first, no exceptions).** Invoke
   `fsc-mandalorians/digital-origination-execution-guardrails` and read its SKILL.md end-to-end
   into the main-loop context. The eight rules it returns govern every subsequent step in this
   run. Do NOT proceed to Preflight until the rules are loaded. This step is idempotent and
   side-effect-free — it neither reads nor writes org state; skip it only if the guardrails are
   already in the current run's context (a resumed session that already loaded them counts).

1. **Preflight once, then confirm the plan, up front.** Resolve the target org (the connected org in
   autonomous mode), acting admin, and API version (see Preflight). Then present the pre-run plan &
   confirmation gate (ordered step list + rough timings) and get the single go-ahead before Act 1.
   Pass the resolved context to every act so none re-resolves it.
2. **Verify the act's upstream end states hold** before delegating (e.g. don't start Act 3 pricing
   until Act 1 and Act 2 report done). If an upstream end state is missing, run (or resume) that act
   first.
3. **Delegate to the act's sibling skill.** Hand off and let the sibling own its own workflow,
   verification, and reporting. Do **not** re-implement an act's mechanics here — the sibling is the
   single source of truth for how that capability is set up. Follow the sibling's instructions
   exactly, **except that in autonomous mode you do not honor its interactive pauses**: where a
   sibling would pause for an approve/reject gate, an activation-subset choice, or a "continue?"
   prompt, proceed autonomously using the documented example values / full activation set (per the
   autonomous-mode rules). The one exception is a step with genuinely no headless path (a
   legally-gated UI-only toggle) — attempt every headless avenue, then record it as a gap and
   continue rather than halting.
4. **Gate on the act's outcome before continuing.**
   - **Success** (end state read back as configured) → proceed to the next act.
   - **Partial with a reported gap** (e.g. a license-gated preference reads back `false` after write,
     or a sibling reports a manual checkpoint that could not be completed headlessly) → record the
     gap in `act_ledger` and decide: continue only if no downstream act depends on the missing piece;
     otherwise treat as blocked.
   - **Blocked** (a prerequisite the act cannot satisfy AND that a downstream act depends on) → **STOP
     the ordered run.** Do not start a dependent act on top of an incomplete foundation. Report
     exactly what blocked it, with the failing response, and what later acts now cannot rely on.
   - **Hard failure** → STOP, report, do not continue.
5. **Record what the act did in `act_ledger`.** Capture the sibling's fresh read-back detail — records
   created (ids / API names / counts), permission sets assigned, preferences flipped, matrices /
   procedures / templates activated, which sub-steps succeeded or failed, and any reported gap or
   manual checkpoint — not just the ✅/⚠️/🔒 status. This is the raw material the end-of-run
   consolidated summary is rendered from, so capture it as the act reports, while the detail is fresh.

After the last act in scope reports back (or the run stops on a block), **render the end-of-run
consolidated summary** from `act_ledger` (see "End-of-run consolidated summary" below). Then, if the
run completed every in-scope act (not stopped on a block), make the single **post-setup verification
offer** (see "Post-setup verification offer") — one yes/no to create `DL_Test_` sample data and
demonstrate the setup — before returning.

Because every act is idempotent, re-running the orchestrator after fixing a blocker is always safe —
already-enabled preferences, already-assigned permission sets, and already-created records are
no-ops.

## End-of-run consolidated summary (the final output)

**Every run — full or partial, success or stopped — ends by rendering one consolidated summary from
`act_ledger`.** This is the audit trail an unattended ~2–3 hour run leaves behind: the admin was not
watching, so the summary is how they learn what actually happened in their org. Render it as the last
thing the orchestrator does, before returning.

The summary is **not** a re-statement of the plan — it reports **what actually ran**, act by act,
from the fresh read-back evidence captured in `act_ledger`. For each act in scope, show:

- **Status** — ✅ done / ⚠️ partial (gap reported) / 🔒 blocked / ⬜ not-started.
- **What was created / changed** — the concrete records and config: records created (name / API name /
  id and counts — e.g. catalog, products, attributes, decision matrices, stage transitions),
  permission sets assigned, org preferences flipped, and procedures / matrices / templates /
  OmniScripts activated. Name them; don't say "the products were created."
- **Sub-steps: succeeded vs failed** — which parts of the act completed and which did not.
- **Gaps / manual checkpoints** — anything headless-impossible, license-gated, or left for the admin
  (a UI-only toggle, an activation the admin must finish), stated explicitly.

Lead with a one-line **overall verdict** (e.g. "5 of 6 acts complete; Act 6 blocked on CDS provisioning
— see below"), then the per-act breakdown, then a **collected list of every gap and manual
checkpoint** so nothing is buried. Suggested shape:

> ### Digital Origination setup — run summary (org `<target_org_alias>`, admin `<acting_admin>`)
> **Overall:** _e.g._ 5 / 6 acts complete; Act 6 partial (1 gap). ⚠️
>
> | Act | Status | Created / changed | Failed sub-steps | Gaps / checkpoints |
> |---|---|---|---|---|
> | 1 Initial Setup | ✅ | DF + KYC features on; `DigitalLendingAdminUser` clone assigned; Digital Origination + Import/Export + Sample Templates on | — | — |
> | 2 Product Catalog | ✅ | catalog `…`, category `…`, product `Home Loan` (id `…`), LoanTerm picklist, 5 attributes, classification `…` | — | — |
> | … | … | … | … | … |
>
> **Gaps & manual checkpoints (action required):**
> - _e.g._ Act 6 — CDS entity not provisioned on this org; stage transitions created but not activated. …

**Rules for the summary:**
- **Report faithfully.** A partial or blocked run is reported as partial or blocked — never dressed up
  as complete (this is Definition-of-done item 7, made concrete). If a step failed, say so with what it
  was.
- **It renders from `act_ledger` only** — it never re-derives state by re-querying the org or
  re-running an act. If an act never ran (⬜), say so rather than omitting it.
- **A stopped run still gets a summary.** When the orchestrator halts on a block, render the summary up
  to and including the blocking act, so the admin sees what was built before the stop.

## Post-setup verification offer (runs once, after the consolidated summary)

**After the end-of-run consolidated summary is rendered — and only when every in-scope act has reported
back (a full or partial-but-not-blocked run) — make ONE offer to prove the setup works by creating a few
sample records and demonstrating them.** This is a sanctioned pause: the six-act journey is already
complete, so autonomous mode's "never pause mid-run" rule no longer applies. Do not make this offer if
the run stopped on a hard block or an unmet true prerequisite — there is nothing to demonstrate yet.

**Render a clear summary FIRST — the admin should see exactly what will be created and what each test
proves before deciding — then ask a single yes/no.** Present it as two short sections (the records, then
the tests), not one dense paragraph, so the admin can weigh it at a glance:

> "**Setup is complete.** Before you go, I can verify it actually works end to end by creating a small,
> clearly-tagged set of sample records and running them through what we just built. Here's exactly what
> that would do:
>
> **Sample records I'd create** (all tagged `DL_Test_<run_tag>` so I can find and delete exactly them):
>
> | Record | Why it's needed |
> |---|---|
> | 1 × Application Form | the parent loan application |
> | 1 × Application Form Product | the record Stage Management acts on (seeded at the first stage, e.g. Intake) |
> | 1 × Proposal | carries the loan amount / term / interest rate the pricing sim reads |
> | 3 × Participant (Party Profile) | banker, underwriter, and applicant — the applicant carries the credit score the BRE reads |
>
> **Tests I'd run against them:**
> 1. **Stage Management** — move the loan along an *allowed* transition (Intake → Submitted) and show the
>    before → after change; then confirm a *disallowed* move (Submitted → Intake) isn't a defined
>    transition. (Note: enforcement + the CDS recompute fire through the guided UI, not a raw API write —
>    I'll prove the restriction from the transition map and report honestly what the headless path does.)
> 2. **Business Rules Engine** — run all three decision-matrix lookups (STP eligibility by credit score,
>    document types, disclosures & consent) and show each returns a real decision, not an empty result.
> 3. **Pricing** — run the price simulation for the sample loan and show it returns a rate matching the
>    list rate we configured.
>
> Nothing here re-runs or changes your setup — it only creates these sample records (plus one
> demonstrative stage change), and when I'm done I'll offer to delete them so your org stays clean.
>
> **Want me to create the sample data and run these tests, or leave it for now?** (run / leave)"

- **On leave / no / no answer:** stop cleanly. Setup is already done and reported; do not create any records.
- **On run / yes:** run the two verification siblings **in sequence, straight through** — this is a single
  data-then-demo pass, not two separate gates:
  1. **`digital-origination-sample-data-setup`** — creates the minimal `DL_Test_`-tagged record graph
     (idempotent; reuses an existing tagged graph). Capture its returned `run_tag` + record ids into
     `sample_data_handle`.
  2. **`digital-origination-demo-run`** — drives that handle through the three demonstrations
     (Stage Management first — the record-observable one — then BRE, then pricing), narrating before →
     after for the stage transition and attributing each change to the matrix/transition that drove it.
     It polls the async CDS Flow to completion before reading the "after," and it ends by offering
     teardown (default yes — delete only records carrying the `run_tag`).
- **This offer only creates sample transactional records and one demonstrative stage PATCH (plus the
  optional teardown deletes).** It never re-runs a setup act and never touches setup artifacts — the
  `run_tag` marker is the boundary between demo data and configuration.
- **The two verification siblings are also standalone-runnable** for a later "show me the setup working"
  ask; the orchestrator only sequences them behind this one offer.

## Narrowed requests

| User request | Route |
|---|---|
| Turn on Digital Origination / run Initial Setup only | Act 1 — `digital-origination-initial-setup` |
| Create the loan product catalog / products / classifications | Act 2 — `digital-origination-product-setup` |
| Set up lending pricing / decision tables / pricing procedure | Act 3 — `digital-origination-pricing-setup` |
| Deploy / activate the FSC_DL sample template | Act 4 — `digital-origination-sample-template-deployment` |
| Set up the Disclosures & Consent / Document Upload / STP BREs | Act 5 — `digital-origination-bre-setup` |
| Set up stage management / stage transitions / CDS | Act 6 — `digital-origination-stage-management-setup` |
| Create sample / test records to try the setup | Verification — `digital-origination-sample-data-setup` |
| Demonstrate the setup / show it working / run the stage transition on a test loan | Verification — `digital-origination-demo-run` (creates the sample data first if absent) |

For a narrowed request, validate that its upstream acts' end states exist. Do not silently run the
entire journey when the admin explicitly asks for one part; and do not run a downstream act on an
unmet upstream (offer to run the missing upstream first).

## Shared invariants

- **Read before write; reuse before create.** Each act's sibling reuses matching artifacts by API
  name and verified shape; this orchestrator never re-does a completed act's writes.
- **Inputs come from the documented examples (autonomous mode).** Products, rates, tiers, effective
  dates, credit cutoffs, document types, consent/disclosure text, stage values, transition maps, and
  access policies are taken from each sibling's documented sample/example values, and users default to
  the resolved `acting_admin`. (In interactive mode this inverts to "never infer — the admin supplies
  or approves each.") Autonomous ≠ fabricate: never invent a value that is neither a documented
  example nor an org fact.
- **Resolve the shared runtime once, pass it down.** No act should re-resolve or hardcode org / user
  / API version.
- **Advance only on fresh read-back evidence.** Treat asynchronous states as in progress, not
  success — always poll async deploys/activations to a terminal state before advancing. In autonomous
  mode, a checkpoint that has no headless path is recorded as a gap and the run continues; it is never
  a pause.
- **Stop on block, never cascade a failure.** A dependent act must not start on an incomplete
  upstream. A true dependency failure still halts the ordered run and reports — this holds even in
  autonomous mode (a headless-impossible *non-blocking* step is recorded as a gap and skipped; a
  *blocking* dependency failure still stops the dependent act).
- **Headless / API-first.** Prefer the platform dispatch tool over CLI/UI, matching every sibling's
  own discipline; surface the documented UI handoffs (legally-gated toggles) as explicit HARD STOPS.

## Definition of done

The full journey is complete only when, for every act in scope:

1. **Act 1** — the two prerequisite features are on, the admin permission-set clone is assigned,
   Digital Origination and Import/Export are on, Sample Templates are enabled, and Manage User Access
   is complete — all read back as configured.
2. **Act 2** — catalog + at least one category exist; the Home Loan product, LoanTerm picklist,
   five attribute definitions, and the Home Loans classification with defaults exist; product
   `Based On` and category assignment are set.
3. **Act 3** — pricing permissions + `CorePricingPreference` verified; rate data present; the three
   pricing decision tables active and refreshed; `NGPDefaultRecipe` mapped without losing existing
   mappings; the selected engine configured; the pricing procedure active and pointed to by the
   recipe.
4. **Act 4** — the `FSC_DL` template deployed (async deploy completed), AssessmentTemplate
   materialized, and the admin-selected OmniScripts / IPs / DataRaptors activated.
5. **Act 5** — each requested BRE feature's decision matrix created, populated, and activated, and
   its Discovery Framework wiring in place.
6. **Act 6** — the `Stage` field on `ApplicationFormProduct` restricted to the defined transitions,
   the CDS Apex + autolaunched Flow bound, the three stage decision matrices active, and the stage
   definition + transitions created and verified.
7. **The end-of-run consolidated summary is rendered** (see "End-of-run consolidated summary") — a
   per-act breakdown of what was created/changed, which sub-steps succeeded or failed, and every
   manual checkpoint or unresolved gap, collected so nothing is buried. A partial run is never reported
   as complete.

## Companion references (the six delegated siblings + the priming sub-skill)

Each is a self-contained top-level skill that owns its own grounded contracts, references, and
verification. This orchestrator only sequences them.

- `fsc-mandalorians/digital-origination-execution-guardrails` — Step 0, MANDATORY priming
  sub-skill. Loads the eight execution guardrails that override default agent behavior for the
  rest of the run. Read-only; no dispatches, no writes. Called first, before Preflight, before
  any act — no exceptions.
- `fsc-mandalorians/digital-origination-initial-setup` — Act 1, the foundation turn-on journey.
- `fsc-mandalorians/digital-origination-product-setup` — Act 2, product-catalog data.
- `fsc-mandalorians/digital-origination-pricing-setup` — Act 3, pricing orchestrator (its own nested
  pricing sub-skills).
- `fsc-mandalorians/digital-origination-sample-template-deployment` — Act 4, FSC_DL sample-template
  deploy + activate.
- `fsc-mandalorians/digital-origination-bre-setup` — Act 5, BRE orchestrator (its own nested BRE
  sub-skills).
- `fsc-mandalorians/digital-origination-stage-management-setup` — Act 6, Stage Management orchestrator
  (its own nested stage sub-skills).

The two **verification** siblings the post-setup offer runs (not setup acts — they create sample data
and demonstrate the finished build):

- `fsc-mandalorians/digital-origination-sample-data-setup` — creates the minimal `DL_Test_`-tagged loan
  application graph the demo drives.
- `fsc-mandalorians/digital-origination-demo-run` — drives that data through Stage Management, the BREs,
  and pricing, narrating before → after, then offers teardown.

## Adding a new act (contributor note)

To extend this master orchestrator with another capability:

1. Author (or reuse) the capability as its own top-level `fsc-mandalorians/*` skill.
2. Add a row to the delegation-map table and insert it at the correct dependency position in the Run
   Order, with its `Depends on` recorded.
3. Re-run the skill-onboarding harness on this parent `SKILL.md`. The harness reads the delegation
   map and emits one `purpose: delegate` step per sibling (`delegates_to: fsc-mandalorians/<child-id>`,
   with `depends_on` reflecting the ordered gating) into this orchestrator's generated SOR — you do
   not hand-wire the parent-to-child edges.

<!-- skill-validate: ignore-start -->
<!-- codey:operations start -->
## Operations Reference

Operations this skill uses — routing and dependency reference.

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `preflight-resolve-runtime` | verify | — | `GET /services/data/` | — |
| `preflight-validate-prerequisites` | verify | — | `GET /services/data/v{api_version}/query` | `preflight-resolve-runtime` |
| `delegate-digital-origination-initial-setup` | delegate | — | → `fsc-mandalorians/digital-origination-initial-setup` | `preflight-validate-prerequisites` |
| `delegate-digital-origination-product-setup` | delegate | — | → `fsc-mandalorians/digital-origination-product-setup` | `delegate-digital-origination-initial-setup` |
| `delegate-digital-origination-pricing-setup` | delegate | — | → `fsc-mandalorians/digital-origination-pricing-setup` | `delegate-digital-origination-initial-setup`, `delegate-digital-origination-product-setup` |
| `delegate-digital-origination-sample-template-deployment` | delegate | — | → `fsc-mandalorians/digital-origination-sample-template-deployment` | `delegate-digital-origination-initial-setup` |
| `delegate-digital-origination-bre-setup` | delegate | — | → `fsc-mandalorians/digital-origination-bre-setup` | `delegate-digital-origination-initial-setup` |
| `delegate-digital-origination-stage-management-setup` | delegate | — | → `fsc-mandalorians/digital-origination-stage-management-setup` | `delegate-digital-origination-initial-setup`, `delegate-digital-origination-bre-setup` |
<!-- codey:operations end -->
<!-- skill-validate: ignore-end -->
