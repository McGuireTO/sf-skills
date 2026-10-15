---
name: flow-type-resolver
description: "Resolve the Salesforce flow type for a natural-language automation request. Given a prompt, returns the canonical (processType x triggerType [x recordTriggerType, runInMode]) tuple plus a friendly label, a confidence, the one clarifying question that would flip an ambiguous answer, and ranked alternatives. A feature of automation-flow-coordinate: loaded by its resolve-type recipe (classification-only 'what kind of flow is this?' requests) and by author.md Phase 2 before drafting a flow. This is the single source of truth for flow-type classification — do not re-derive the taxonomy elsewhere."
metadata:
  version: "1.2"
  related-skills: flow-flow-properties
---

# Flow Type Resolver

The single source of truth for turning an automation request into a Salesforce flow type.
"Flow type" is not a flat enum — it is a **tuple**: `processType` × `triggerType`
(× `recordTriggerType`, `runInMode`). The friendly names in the Flow Builder picker
("Record-Triggered Flow", "Autolaunched Orchestration", …) are labels over that tuple.

The canonical matrix, enums, characteristics, bad pairs, the recognized out-of-scope
process types (`unsupportedProcessTypes`), and the finer Flow Builder picker labels (the
advisory `uiLabel` on record-triggered `supportedTuples` entries) all live in
**`taxonomy.json`** (next to this file). This document explains the reasoning engine; it
does not re-tabulate the matrix. The **authoritative supported set** — the full enumeration of the
`(processType × triggerType × recordTriggerType)` tuples Project Codey supports — is
`taxonomy.json`'s `supportedTuples`; the `categories` are the coarse resolver view over it.
Any tuple you resolve must be one of those `supportedTuples` entries. That set is validated
against the live org by `eval/verify_supported_types.py` (see Scope and guardrails). This is a
feature of `automation-flow-coordinate`: its `resolve-type` recipe (classification-only
requests) and `author.md` Phase 2 load this reference for flow-type classification; per-trigger
build detail (Segment/List/CampaignMember/RecordQuery binding, AutomationEvent discovery,
scheduled paths, before/after-save constraints) stays in coordinate's own element files
(`../../elements/start/...`) — this reference only answers "which tuple", not "how do I build it".

## Output contract

Emit a `FlowTypeResolution`:

```jsonc
{
  "tuple": { "processType": "...", "triggerType": "...?", "recordTriggerType": "...?", "runInMode": "...?" },
  "label": "Record-Triggered Orchestration",   // derived from taxonomy.json
  "confidence": "high" | "medium" | "low",
  "decidingClarification": "…the one question that would flip the answer, when ambiguous",
  "mustAsk": true | false,   // true only when a rule below says the user has to choose
  "alternatives": [ { "tuple": {…}, "label": "…", "why": "…" } ]   // ranked, best-first
}
```

`confidence` and `decidingClarification` derive from how close the characteristic axes were
to tipping the family (see below). Emit `decidingClarification` only when confidence is not
`high`.

`mustAsk` is `false` unless a rule below sets it. When it is `true`, the `tuple` is only the
leaning answer: the caller asks `decidingClarification` before drafting and builds the type the
user picks. Today only the "CRM Triggered Flow" rule sets it.

## Resolution engine — characteristics first, then trigger

Flow type is a function of the **characteristics of *what is being automated***, resolved
along two independent dimensions and then composed:

**Dimension A — the process family (the *what*).** Read three characteristic axes:

- **Process vs. Task** — a single unit of work, or a coordinated multi-stage business process?
- **Long-running vs. Short-running** — completes in one session/transaction, or spans time,
  waits for humans/events, and resumes?
- **Single-user vs. Collaboration** — one actor, or coordination across multiple
  users/teams/approvers across stages?

Combine them by **dominant signal, not strict conjunction**: promote to an Orchestration
family when the request *leans* toward Process (clearly multi-stage + long-running), even if
one axis (e.g. user count) is ambiguous. Secondary factors — complexity, cognitive overload,
manageability — are tie-breakers: when a would-be single flow's process spans enough
stages/actors/waiting that one monolithic flow would be hard to build or manage, promote it.

- Task · short · single, interactive → **Screen Flow** (`Flow`)
- Task · short · single, headless → **Autolaunched** (`AutoLaunchedFlow`)
- Process · long-running · multi-user, **interactive stages** → **Orchestration** (`Orchestrator`)
- Process · long-running · **geared toward getting approvals** → **Approval Orchestration** (`ApprovalWorkflow`)

**Background steps do not demote.** Orchestrations (and Approval Orchestrations) routinely
contain background/headless steps that run autolaunched sub-flows. Automated,
non-interactive work *inside* a process is NOT evidence of a plain Autolaunched flow — it is
a normal constituent of an orchestration. Classify the whole thing as Autolaunched only when
the ENTIRE automation is a single short headless task.

**Orchestrator vs. ApprovalWorkflow.** Orchestrations coordinate multi-user *interactive*
work across stages. Approval Orchestrations are specifically geared toward *obtaining
approvals* — evidenced by approval state objects (Approval Requests, Approval Work Items) and
approver actions (Recall / Approve / Reject). One approval step among many interactive stages
is NOT enough; the process must be fundamentally about sign-off routing. If a request needs
both rich interaction AND formal approvals and the dominant intent is unclear, pick the
leaning family and surface the tension via `decidingClarification`.

**Dimension B — the invocation (*how it STARTS*), composed with the family.** This axis is
what separates an Autolaunched type from its Record-Triggered / Scheduled / audience
counterpart within the *same* family, so decide it deliberately — do not let it default to
record-triggered:

- **Automatic triggers:** starts on a record change → `triggerType: RecordAfterSave` (+
  `recordTriggerType` Create / Update / CreateAndUpdate; use `RecordBeforeSave` only for a
  Task-family before-save flow, never for an Orchestration) — except a request that names a
  **CRM Triggered Flow**, which is `IndivRelatedRecord` when it says "marketing" and is
  otherwise asked, even on a record change (see "CRM Triggered Flow" below). On a schedule →
  `Scheduled`. On a
  platform event → `PlatformEvent`. On an email-engagement event (open/click/bounce/response)
  → `AutomationEvent`. A marketing "automation event" flow that instead triggers on a Lead,
  Contact or Prospect change ("when Lead Status is Nurturing", then send to a journey) is the
  "Prospect, Lead, Contact or Related Record Change" entry → `IndivRelatedRecord`, not
  `AutomationEvent` or `RecordAfterSave`. When someone **submits a Marketing form** → `FormSubmissionEvent` (Flow
  Builder shows it as Automation Event → Form Submission, but it saves as its own trigger type —
  never `AutomationEvent`; see below). On a marketing/audience source → `Segment` (Data Cloud segment), `List`
  (Actionable List), `CampaignMember` (Campaign members), or `RecordQuery` (all records of an
  object matching a filter) — pick the specific one the request names. On a **Data Cloud DMO
  record change** (a `ssot__*__dlm` object created/updated) → `DataCloudDataChange` (+
  `recordTriggerType` Create / Update / CreateAndUpdate; no `Delete`) — org-gated, needs a Data
  Cloud-provisioned org (API version 59.0+). A `__dlm` target is a Data Cloud DMO, never a core SObject;
  a change across a multi-object *data graph* is the separate org-gated `DataGraphDataChange`.
- **Explicit start (no trigger):** launched by a user who steps through it, or called on demand
  from a button / Apex / an API / a subflow, or submitted for approval → `None` (an
  Autolaunched\* type).
- **On-Demand marketing flow:** the request names the **On-Demand Flow** type, or an app / the API
  starts a **marketing send** for one specific person (`sendEmailMessage`, `sendSmsMessage`,
  `sendToJourney`, or another send that the `OnDemandNoTrigger` action catalog lists) →
  `OnDemandNoTrigger`: `processType` `AutoLaunchedFlow` **and** `start.triggerType`
  `OnDemandNoTrigger`, plus a top-level `dataSpace`. Without that `triggerType` the flow is a
  plain autolaunched flow, not an On-Demand one, even when it is named "On-Demand". This wins over the
  explicit-start rule above **only** in those two cases. A no-trigger flow's action catalog does
  not offer those send actions (for example: `You can't use the Send SMS Message action type in
  flows with the Autolaunched Flow process type.`).
  - **A send tied to a consent subscription is a marketing send.** An email or text the user
    sends "with consent from" a communication subscription is `sendEmailMessage` /
    `sendSmsMessage`, the E360 sends that take a subscription. An Email Alert (`emailAlert`) or
    core Send Email (`emailSimple`) has no subscription input, so never map such a request to
    either. Decide the send action before the flow type.
  - **The send action decides, not the launch channel.** An API-launched flow with an E360 send is
    `OnDemandNoTrigger`; an API-launched flow without one is `None`. A core Send Email
    (`emailSimple`), a subflow, or an Apex/REST-invoked utility flow stays `None`.
  - **"On demand" alone is not this type.** "Runs on demand", or an on-demand flow that Apex, a
    button or another flow calls, with no marketing send, means "runs when called": the
    explicit-start rule above → `None`. Route to `OnDemandNoTrigger` only when the flow does a
    marketing send, or when the user names the On-Demand Flow type itself (for example "an
    On-Demand Flow, not a regular autolaunched flow").

  Read `../../elements/start/start.md` § On-Demand before writing the Start: it has the build detail.

**A mentioned record is NOT a record trigger.** Decide invocation by *who or what starts the
automation*, independent of any record the prompt names. "A Contract that reached the renewal
stage" or "a Closed Won Opportunity" is record *context*, not a trigger. A record trigger means
the flow fires **automatically the moment the record is created/updated/deleted** — look for
"when/whenever a record is created/updated", "on save", "as soon as". If instead a person or
another process **explicitly starts** it — "a user can kick off / begin / initiate", "from a
button", "on demand", "submit for approval", "called from Apex / a subflow" — the invocation is
`None` (Autolaunched\*), *even though a record is involved*. When the prompt describes a record
state but names an explicit human/process starter, prefer the Autolaunched\* family and, if it
is genuinely ambiguous, surface the tension via `decidingClarification`.

**Fire-on-event vs. run-then-wait.** "Send this when the email is opened/clicked" is
`triggerType: AutomationEvent` (fires the whole flow on the event). A flow that *runs first on
a record/segment and then pauses mid-flow* until that same kind of event is a completely
different shape — a normal trigger plus a `WaitUntilEvent` element. Don't conflate the two;
see the matching `badPairs` entry in `taxonomy.json`.

**Form submission — `FormSubmissionEvent`, never `AutomationEvent`.** A flow that runs when
someone submits a Marketing form ("when someone submits our webinar registration form", "on
form submit", "when a prospect fills out our Contact Us form") resolves to
`processType: AutoLaunchedFlow` + `triggerType: FormSubmissionEvent`. Flow Builder lists Form
Submission inside the Automation Event picker, and event discovery scoped to the Automation
Event trigger returns a `trgrOnFormSubmission` row, but selecting it saves the flow as
`FormSubmissionEvent`. **HARD PROHIBITION:** never resolve or author a form-submission flow as
`triggerType: AutomationEvent` with `eventName`/`eventType` `trgrOnFormSubmission`, even when
the user says "Automation Event" or names the Form Submission event — the platform rejects that
shape (invalid event name, `InvalidDraft`). Resolve to `FormSubmissionEvent` and, when the user
used Automation Event wording, say why in one line (the builder files Form Submission under
Automation Event, but the saved trigger type is `FormSubmissionEvent`). See the matching
`badPairs` entry in `taxonomy.json`.

**Submitted form vs. a form the user fills in.** The word "form" alone does not decide the
type. If the flow **reacts after** someone submits a form (headless, once per submission, the
answers arrive in `$Form`), it is `FormSubmissionEvent`. If the flow **is** the form — a user
steps through it, enters values, or is guided screen by screen ("build a form that walks an
agent through…", "collect input from the user") — it is a **Screen Flow** (`Flow`). When a
request is genuinely unclear (e.g. "a flow for our signup form"), surface it via
`decidingClarification`: "Should the flow run after someone submits an existing Marketing form,
or should the flow itself be the form the user fills in?"

**"For an individual" — record trigger vs. Individual Related Record.** A request to build a flow
"for an individual" (or "for a person/contact/lead/prospect") is ambiguous and is **not**, on its
own, a signal for `IndivRelatedRecord`. A plain record-triggered flow on the Individual/Contact/Lead
sObject fires on that record's own save; an **Individual Related Record-Triggered Flow**
(`triggerType: IndivRelatedRecord`, Engagement/Journey) is a distinct type that fires on a
contact/lead/prospect-related record and can host mid-flow engagement waits. Route to
`IndivRelatedRecord` only when the request names the type ("Individual Related Record-Triggered
Flow", "individual-related record", or a "CRM Triggered Flow" that says "marketing" — see below)
or describes engagement/journey behavior (pauses on an engagement event, wait-until-event, journey
builder contact event). When the request pairs "for an individual" with plain record-trigger
language ("when created/updated", "on save") and no engagement/journey signal and no CRM
Triggered name, resolve it as a normal record-triggered flow — but if the person may have meant
the engagement type, surface the tension via `decidingClarification` (e.g. "a standard
record-triggered flow on the Individual/Contact/Lead object, or an Individual Related
Record-Triggered engagement/journey flow?").

**"CRM Triggered Flow" — "marketing" decides, otherwise ask.** "CRM Triggered Flow" (also "CRM
Triggered", "CRM Trigger") is an informal name for the Individual Related Record type, which Flow
Builder lists under Automation Event-Triggered Flow as "Prospect, Lead, Contact or Related Record
Change". People also say it for a core Record-Triggered Flow on a CRM object, so the name alone
does not decide the type. When a request names a CRM Triggered Flow:

1. **It says "marketing"** (for example "a marketing CRM Triggered Flow", "send our marketing
   email"). Resolve to `processType: AutoLaunchedFlow` + `triggerType: IndivRelatedRecord` with
   `high` confidence and no clarifying question, **even when the rest of the request uses
   record-change wording** ("every time a Contact is updated", "when a Lead is created"). That
   wording sets the Start `object` and `recordTriggerType`; it does not make the flow a core
   Record-Triggered Flow.
2. **It does not say "marketing".** Ask before building. Return `IndivRelatedRecord` as the
   leaning `tuple` with `medium` confidence and `mustAsk: true`, list the core Record-Triggered
   Flow (`RecordAfterSave`, with the request's object and `recordTriggerType`) as the first
   alternative, and set `decidingClarification` to: "Should this be a marketing Automation Event
   flow (Prospect, Lead, Contact or Related Record Change), or a Record-Triggered Flow?" Build
   the type the user picks. Record-change wording does not settle it, and neither does "send an
   email" on its own.

Either way, never resolve the name to the Data Cloud-triggered `DataCloudDataChange` (that fires
on a Data Cloud DMO, not a CRM record). If the user picks the Record-Triggered Flow, it cannot run
the marketing Send Email Message action (`sendEmailMessage`): the save is rejected with
`ACTIONCALL_NOT_SUPPORTED_FOR_PROCESSTYPE`, so an email in that flow uses the core Send Email
action. The Individual Related Record flow does not need a mid-flow wait to be this type. Build
detail (`builderType: JourneyBuilder`, the triggering record as `$Input`, the required
`dataSpace`) is in `../../elements/start/start.md`'s Engagement / Journey section.

Composing A×B is what makes Record-Triggered Orchestration etc. reachable. `runInMode`
defaults per `taxonomy.json` (orchestrations/approvals default to `SystemModeWithoutSharing`).

**Literal "autolaunched" override.** When a request *explicitly contains the word
"autolaunched"*, build a **no-trigger** flow (omit `triggerType`) — invoked on demand, from
Apex/API, or a subflow — and do NOT infer a record, `Scheduled`, or audience trigger from
intent- or timing-language ("for each Opportunity that reaches Closed Won", "when X is
created", "every day at 9am"). Model that intent inside the flow body instead. Only promote to
a triggered type if the user ALSO explicitly asks for that trigger. When "autolaunched" is
absent, this override does not apply — record-transition language is the normal, correct
signal for a record-triggered flow. The **On-Demand marketing flow** rule above wins over this
override: an On-Demand Flow request, or a marketing send that an app or the API starts for one
person, is `OnDemandNoTrigger` even when it also says "autolaunched". Say why in one line.

**Validate against the bad pairs** in `taxonomy.json` before finalizing; if the composed
tuple matches one, apply its redesign.

## Producing the resolution

1. Score the three axes from the prompt; pick the leaning family (dominant signal).
2. Apply the literal-"autolaunched" override if the word is present.
3. Pick the trigger dimension; compose the tuple; set `runInMode` from `taxonomy.json`
   defaults.
4. Run the bad-pairs gate; redesign if matched.
5. Derive `label` from the matching `taxonomy.json` category.
6. Set `confidence`: `high` when all axes agree and the trigger is explicit; `medium`/`low`
   as axes conflict or the trigger is inferred. When not `high`, write the single
   `decidingClarification` that would move the answer, and list ranked `alternatives`.
7. Set `mustAsk: true` only when a rule above requires the user's choice (today, a CRM
   Triggered Flow request that does not say "marketing"); otherwise `false`.

## Scope and guardrails

- **Prompt-only — EVOLVE-blind.** This reference maps a request to a tuple; it never receives the loaded flow. A confident, high-confidence result here is **not** license to change an existing flow's type. When a flow is already loaded (EVOLVE), the caller must compare this resolved `processType` against the loaded flow's `processType` and decline on divergence — that check is `author.md` Phase 2's job (its EVOLVE processType lock), not this resolver's.
- **Supported types only — stop if unavailable.** Resolve only to a tuple present in
  `taxonomy.json`'s `supportedTuples` (the authoritative supported set). Some supported types are
  **org-gated** — they need a feature or provisioning the base org may lack — and each is
  modeled as a first-class **feature** in `taxonomy.json`'s `orgGating.features` (declaring how to
  detect provisioning and what to tell the user when it is absent). A gated tuple references its
  feature by id via `orgGated: <featureId>`:
  - **`DataCloudDataChange`** is gated on Data Cloud provisioning (feature `data-cloud`,
    `detectBy: triggerType` — it exists only on a Data Cloud-provisioned org, API version 59.0+; the
    separate `DataGraphDataChange` maps to the same feature).

  `Orchestrator`, `ApprovalWorkflow`, and `EvaluationFlow` are **not** org-gated — they ride an
  always-on org perm, so they are ordinary supported types the validator checks normally.

  When the org does not expose a gated feature, **stop and surface the feature's clean
  "org not provisioned for `<feature>`" outcome** (from its `notProvisioned` note) rather than
  falling back — e.g. never silently substitute a core record trigger for `DataCloudDataChange`.
  **Non-gated tuples are unaffected** (a non-gated `processType` missing from the org's supported
  list is still a hard stop — the org may lack a required feature flag). The supported set is kept
  honest by **`eval/verify_supported_types.py`**, an org-check that confirms every `supportedTuples`
  entry is valid in the org (`processType` in list-process-types, `triggerType` in list-trigger-types
  for that processType; no-trigger valid by absence; an org-gated tuple is skipped as informational —
  carrying its `notProvisioned` note — when the org lacks the feature, and validated normally when
  the org exposes it). Run it after any change to `supportedTuples`:
  `set -a; . test-agent/.env; set +a; python3 eval/verify_supported_types.py`.
- **Confirm elevated run mode.** When the resolved tuple carries a non-`DefaultMode`
  `runInMode` — whether you elected it or the family defaults to `SystemModeWithoutSharing`
  (orchestrations and approvals do) — explicitly confirm with the user that elevated,
  sharing-bypassing permissions are intended before finalizing. See
  `../flow-properties/flow-properties.md`.
- **Per-trigger build detail lives elsewhere.** Once this reference has picked `Segment` /
  `List` / `CampaignMember` / `RecordQuery` / `AutomationEvent` / `FormSubmissionEvent` /
  `DataCloudDataChange`, hand off to coordinate's `../../elements/start/audience-common.md` +
  `../../elements/start/segment-triggered.md` / `list-campaignmember.md` / `recordquery.md` /
  `automation-event-triggered.md` / `form-submission-triggered.md` /
  `data-cloud-data-change-triggered.md` for the actual
  binding and Start-element shape — this reference does not re-document those.
  `BroadcastNoTrigger` → `../../elements/start/start.md` § Broadcast; `OnDemandNoTrigger` →
  `../../elements/start/start.md` § On-Demand.
- **Out of scope — hand off.** Field Service (`FieldServiceMobile` / `FieldServiceWeb`),
  CPQ, and other industry-specific process types are not resolved here; for the recognized
  out-of-scope process types see `taxonomy.json`'s `unsupportedProcessTypes` block. (CPQ is
  a feature family, not a single `processType`, so it stays as prose here rather than an
  entry there.)

## How this feature is loaded within `automation-flow-coordinate`

This reference is not a standalone skill — it is loaded by path from coordinate's recipes and
elements:

- `../../recipes/resolve-type/resolve-type.md` — the classification-only recipe. Loads this
  reference to answer "what kind of flow is this?" and emit the `FlowTypeResolution`, then
  offers to continue into authoring.
- `../decision-tree.md` is a thin pointer to this reference.
- `../../elements/start/start.md`'s "autolaunched is literal" note and Reference File Index
  point here for the classification rule; it keeps only per-trigger build detail.
- `../../recipes/author/author.md`'s Phase 2 "pick processType/triggerType" step and its EVOLVE
  "change trigger type" row load this reference to (re-)pick the tuple before drafting or
  restructuring a flow.

Do not copy the matrix or rules into any consumer — extend `taxonomy.json` and this file.
