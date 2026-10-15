---
name: flow-element-start
license: LICENSE.txt has complete terms
description: "Start element — configure the trigger type, object scope, entry conditions, and scheduled paths that fire a flow. Covers record triggers (before/after save, before delete), scheduled flows, platform events, autolaunched flows, and screen flows. Key decision: before-save (synchronous, no cross-record DML) vs. after-save (async, can update other records). TRIGGER when: user configures a flow's trigger, entry criteria, scheduled paths, or run-as mode. DO NOT TRIGGER when the user needs a Wait/Pause element for mid-flow delays (use flow-element-wait)."
metadata:
  version: "1.0"
  related-skills: flow-flow-properties, flow-shared-record-filter
---

# Start Element

## Reference File Index

| File | Purpose |
|---|---|
| `../../shared/flow-type-resolver/flow-type-resolver.md` | Canonical flow-type resolution — picking `processType`/`triggerType`/`recordTriggerType`/`runInMode` from the characteristics of what is being automated, plus the literal-"autolaunched" guidance (an explicit *"autolaunched flow"* is no-trigger — do not infer a record, `Scheduled`, or audience trigger from intent- or timing-language *unless* the user also explicitly asks for that trigger, e.g. "schedule-triggered", "runs daily at 3 AM"). Load when choosing a flow's type/trigger. (`../../shared/decision-tree.md` is a thin pointer to it.) |
| `examples/autolaunched.json` | Autolaunched / no-trigger Start example |
| `examples/beforeSave.json` | Before Save record-triggered Start example |
| `examples/recordTriggered.json` | After Save record-triggered Start example |
| `examples/scheduled.json` | Scheduled trigger Start example |
| `examples/filterFormula-dateRange.json` | **Record-triggered** flow with `filterFormula` using date arithmetic — demonstrates correct date-range filtering (see [[flow.shared.formula-expression]] §1.1 for why `ADDDAYS()` is not available). `filterFormula` is record-triggered-only; NOT valid on Scheduled flows |
| `examples/platformEvent.json` | Platform event trigger Start example |
| `examples/segment-weekly-schedule.json` | Segment-triggered weekly run-schedule example |
| `audience-common.md` | Shared build contract for ALL audience triggers (Segment, List, CampaignMember, RecordQuery) — run schedule, top-level `timeZoneSidKey`, top-level `dataSpace`, optional `dataGraph`, re-entry (`entryType`), save-and-activate gates, builder round-trip defaults. Load FIRST for any audience trigger, then the per-trigger file below |
| `segment-triggered.md` | Segment (Audience) flow build guide — MUST load (after `audience-common.md`) before configuring a Segment flow (segment binding chain, eligibility gate, `publishSegment`, outreach actions, `$Record` member context) |
| `list-campaignmember.md` | List (Actionable List) + CampaignMember (Campaign) build guide — MUST load (after `audience-common.md`) before configuring either (the `start.listAction` binding, audience-selection gate, `$Input` member handles, examples) |
| `recordquery.md` | RecordQuery (all records of an SObject matching a filter) build guide — MUST load (after `audience-common.md`) before configuring it (the `start.object` + optional `start.filters` binding, `CRM_OBJECT_SELECTION_REQUIRED` gate, direct `$Input.<field>` record context, example) |
| `automation-event-triggered.md` | Automation Event (OOTB email-engagement) flow build guide — MUST load before configuring an `AutomationEvent` flow (start `eventName`/`eventType`, the OOTB email-event catalog, and the trigger-vs-wait disambiguation) |
| `form-submission-triggered.md` | Form-Triggered (Marketing form submission) flow build guide — MUST load before configuring a `FormSubmissionEvent` flow (form discovery → content FQN for start `form`, `$Form.<field>` names, one-form-per-flow rule, and the prohibition on `AutomationEvent` + `trgrOnFormSubmission`) |
| `examples/formSubmission.json` | Form-Triggered start — `form` bound to a form's content FQN, plus a Create Records element mapping `$Form` answers |
| `data-cloud-data-change-triggered.md` | Data Cloud-Triggered (single DMO record change) flow build guide — MUST load before configuring a `DataCloudDataChange` flow (DMO discovery chain, start `object`/`recordTriggerType` shape, `$Record.<dmoField>` context, writable-SObject write rule, and the data-graph/core-record/AutomationEvent disambiguation) |
| `examples/automationEvent-emailOpen.json` | Automation Event start — email-open trigger with the required `associatedContent` start input |
| `examples/automationEvent-emailClick.json` | Automation Event start — email link-click trigger with `associatedContent` + `specificLink` start inputs |
| `examples/negative-triggerTypeNone.json` | INVALID: `triggerType: "None"` must never be emitted |
| `examples/negative-filterLogicNoConditions.json` | INVALID: `filterLogic: "no_conditions"` must never be emitted |
| `examples/negative-scheduledMissingFilterLogic.json` | INVALID: Scheduled flow missing required `filterLogic` |
| `examples/negative-scheduledFilterFormula.json` | INVALID: Scheduled flow using `filterFormula` / `formula_evaluates_to_true` — formula entry criteria is record-triggered-only; use literal `filters[]` + a body Decision instead |
| `examples/negative-valueDataType.json` | INVALID: `valueDataType` in filter value (UI-layer only) |
| `examples/negative-platformEventWithObject.json` | INVALID: PlatformEvent using `eventName`/`eventType` — must use `object` field |
| `examples/negative-priorInEntryCriteria-doesRequire.json` | INVALID: `$Record__Prior` in Start entry criteria while `doesRequireRecordChangedToMeetCriteria: true` — `FORMULA_EXPRESSION_INVALID` |

## Overview

Start element defines trigger type, which determines available system variables and element constraints.

## Picking the flow type — use the flow-type-resolver reference

**Flow-type classification (which `processType` / `triggerType` / `recordTriggerType` /
`runInMode` to build from a request's intent) is owned by the flow-type-resolver reference
(`../../shared/flow-type-resolver/flow-type-resolver.md`) — the single source of truth.** Load it
to resolve the tuple before configuring the Start element; do not re-derive the choice here. The
**authoritative supported set** — the full enumeration of every supported
`(processType × triggerType × recordTriggerType)` tuple, including the finer Flow Builder picker
labels (Before Save / After Save / Before Delete, carried as `uiLabel`), the audience triggers
(`Segment` / `List` / `CampaignMember` / `RecordQuery`), and the Orchestration / Approval
variants — is that reference's `taxonomy.json` → `supportedTuples`, validated against the org by
its `eval/verify_supported_types.py`.

Once the resolver returns a tuple, use the **Reference File Index** above to load the
per-trigger build guide (`audience-common.md` + `segment-triggered.md` /
`list-campaignmember.md` / `recordquery.md` for audiences; `automation-event-triggered.md`
for `AutomationEvent`; `form-submission-triggered.md` for `FormSubmissionEvent`; the Engagement / Journey section + `../wait/wait.md` for
`IndivRelatedRecord`) and follow it for the Start-element shape.

> **"Autolaunched" is literal:** an explicit *"autolaunched flow"* request is **no-trigger**
> — do not infer a record or `Scheduled` trigger from intent- or timing-language.
> **Exception:** when the user *also* explicitly asks for a trigger — "schedule-triggered",
> "runs daily at 3 AM", "on create/update", "fire when the record is saved" — build that
> trigger (a *"schedule-triggered autolaunched flow"* is `Scheduled`, not no-trigger). An
> On-Demand Flow stays `OnDemandNoTrigger` even if it says "autolaunched"
> ([On-Demand](#on-demand-ondemandnotrigger)). Full
> rule, examples, and body-modeling pattern: `../../shared/flow-type-resolver/flow-type-resolver.md`.

> **A marketing flow that fires on a Lead, Contact or Prospect change is `IndivRelatedRecord`,
> not `RecordAfterSave`.** This covers an "automation event" flow that triggers on a CRM record
> change ("when Lead Status is Nurturing") and sends a marketing message, sends to a journey or
> waits on a journey or engagement event. A "CRM Triggered Flow" request follows the resolver:
> `IndivRelatedRecord` when it says "marketing", otherwise ask the user.
> Flow Builder lists it under Automation Event-Triggered Flow as "Prospect, Lead, Contact or
> Related Record Change". Build it with `start.triggerType: "IndivRelatedRecord"`, the record
> as `start.object`, and `$Input.<field>` (not `$Record`) for that record's fields. A
> `RecordAfterSave` start can't hold these actions: the org rejects even a Draft save with
> `You can't use the Send to Journey action type in flows with the Autolaunched Flow process
> type.` (or `…the Send Email Message action type…`). `AutomationEvent` is a different trigger:
> it starts only on an email or SMS engagement event (`automation-event-triggered.md`).

## Before Save — Critical Architectural Constraint

**THE silent failure mode.** The flow saves successfully; forbidden elements fail silently at runtime.

### RecordBeforeSave — Forbidden Elements:
- `recordCreates`, `recordUpdates`, `recordDeletes` (DML on other objects)
- `recordLookups` (Get Records — SOQL not allowed)
- Action Calls to external services (callouts)
- Send Email actions

### CORRECT — Direct field update pattern (what Before Save is for):
```json
{
  "name": "Set_Description",
  "assignmentItems": [{
    "assignToReference": "$Record.Description",
    "operator": "Assign",
    "value": { "stringValue": "Auto-populated by flow" }
  }]
}
```
Assignments to `$Record.<FieldName>` are committed when the record saves — no `recordUpdates` needed or allowed. Also permitted: Decisions, formula evaluations, assignments to flow variables.

| Need | Use |
|---|---|
| Set a field on the triggering record | `RecordBeforeSave` + Assignment to `$Record.<Field>` |
| Create a related record | `RecordAfterSave` + `recordCreates` |
| Update other records | `RecordAfterSave` + `recordUpdates` |
| Query related data | `RecordAfterSave` + `recordLookups` |

## Trigger Types

### Record-Triggered (Before Save)
- **triggerType**: `RecordBeforeSave`
- Runs synchronously before record is saved; can only update fields on `$Record` — see [Before Save Constraint](#before-save--critical-architectural-constraint)
- Supports `Create`, `Update`, `CreateAndUpdate` as `recordTriggerType`
- `$Record` = new/updated values; `$Record__Prior` = prior values (Update/CreateAndUpdate only)
- No scheduled paths; `doesRequireRecordChangedToMeetCriteria` available for Update/CreateAndUpdate

### Record-Triggered (After Save)
- **triggerType**: `RecordAfterSave`
- Runs asynchronously after record is saved; can DML, send emails, call external services
- Supports `Create`, `Update`, `Delete`, `CreateAndUpdate` as `recordTriggerType`
- `$Record` = saved values; `$Record__Prior` available for Update/CreateAndUpdate
- Scheduled paths available for AfterSave only — see [Scheduled Paths](#scheduled-paths)
- Multiple flows on same object/event: execution order controlled by `triggerOrder` (flow-root property, see `flow-properties.md`)

### Record-Triggered (Before Delete)
- **triggerType**: `RecordBeforeDelete`; `recordTriggerType` auto-set to `Delete`
- `$Record` = record being deleted (read-only); no scheduled paths; no `doesRequireRecordChangedToMeetCriteria`

### Scheduled (Time-Based)
- **triggerType**: `Scheduled`
- Runs on a schedule. **A Scheduled flow supports only `frequency` `Once`, `Daily`, or `Weekly`** — `Hourly`/`Monthly`/`Yearly`/`Weekdays`/`OnActivate` are NOT valid for `Scheduled` and are rejected.
- Requires: `object`, `startDate`, `startTime`, `frequency`; `filterLogic` required (cannot be "No Conditions")
- `$Record` = each record matching filter at run time
- Optional: `endDate`/`endTime`, `maxBatchSize` (API v63+)
- **Do NOT set `frequencyNumber`, `daysOfWeekToRun`, `dayOfMonthToRun`, or `timeZoneSidKey` on a Scheduled flow** — those are "enhanced scheduling" fields gated to the Segment (Audience) trigger; the validator rejects them here (`timeZoneSidKey` → `UNSUPPORTED_FIELD_FOR_PROCESS_TYPE`). For a weekly/monthly *marketing* cadence, use a Segment flow, not a Scheduled flow.
- **On SAVE, `schedule.startTime`/`schedule.endTime`/`schedule.startDate`/`schedule.endDate` must be wire strings, NOT the server's read-back form.** A retrieve hands these back as `schedule.startTime`/`schedule.endTime`: `{ "timeInMillis": N }` objects, and `schedule.startDate`/`schedule.endDate`: epoch-millis integers — that is the **read-back form only**. Echoing those objects/integers straight back on save is rejected (`ILLEGAL_QUERY_PARAMETER_VALUE` observed). Convert first: `{ "timeInMillis": 32400000 }` → `"09:00:00.000"`; for a date, take the **UTC** calendar day (`floor(epochMillis / 86400000)`), never a local-zone render — these are midnight-UTC instants, so local formatting in a negative-UTC offset silently lands a day early (e.g. `1773532800000` → `"2026-03-15"` in UTC but `"2026-03-14"` in US Pacific). See `../wait/wait.md` (the same rule for `resumeTime`/`resumeDate`) and `shared/anti-patterns.md` item 39 for the worked midnight-boundary example.
- **Entry criteria: literal `filters[]` rows only.** `filterFormula` / `filterLogic: "formula_evaluates_to_true"` is record-triggered-only — on a Scheduled flow it saves as `InvalidDraft` and warns `FORMULA_EXPRESSION_INVALID` (even a trivial `1 = 1`). `filters[]` also reject `elementReference`; use literal typed values or `IsNull`. To select by a formula, field-to-field comparison, or `$Flow.CurrentDate` (e.g. "birthday is today"): narrow with literal `filters[]`, then evaluate the expression in a Boolean **Formula resource** compared `EqualTo true` in a **Decision** (non-matches → end), or precompute a formula field and filter on it literally.

### Platform Event-Triggered
- **triggerType**: `PlatformEvent`
- Use `object` = event API name (e.g., `"Payment_Page_Change__e"`) — do NOT use `eventName` or `eventType` (those cause save failure)
- `$Record` = platform event fields; no scheduled paths
- **Fault handling:** `customErrors` is NOT valid here (`TRIGGER_TYPE_ELEMENT_NOT_SUPPORTED`, same as Autolaunched) — a DML/action `faultConnector` must target a `Log_Error` actionCall or a `$Flow.FaultMessage` Assignment instead. For observability, prefer a persisted/notified handler — a bare in-memory Assignment leaves the error invisible in this headless flow (advisory; see `shared/fault-paths/fault-paths.md` § Observable vs. In-Memory-Only Fault Handling). See `elements/custom-error/custom-error.md` and `shared/anti-patterns.md` #2.

### Autolaunched (No Trigger)
- **triggerType**: must be absent — the key must not appear in the JSON at all. Do NOT emit `"triggerType": "None"` or `"triggerType": ""` — both are invalid (see negative-triggerTypeNone.json).
- Called from Apex, REST API, Process Builder, another flow (subflow), or scheduled job
- A marketing send (`sendEmailMessage` / `sendSmsMessage` / `sendToJourney`) launched by an app or the API is not this type; see [On-Demand](#on-demand-ondemandnotrigger).
- No object, no filters; run-in mode configurable — see [Run-As User Context](#run-as-user-context)
- Input/output variables declared in `metadata.variables[]` with `isInput: true` / `isOutput: true` — NOT on Start:
  ```json
  { "name": "inputAccountId", "dataType": "String", "isInput": true, "isOutput": false }
  ```
- Forbidden: `screens[]` — save-time error: "Element type Screen is not supported for process type AutoLaunchedFlow"
- Forbidden: `customErrors[]` anywhere in the flow (via `faultConnector`, a regular `connector`, or unconnected) — Custom Error elements require a record-triggered `triggerType` (`RecordBeforeSave`/`RecordAfterSave`); an Autolaunched Flow's fault paths must target a `Log_Error` actionCall or a `$Flow.FaultMessage` Assignment instead (for observability, prefer a persisted/notified handler — advisory, see `shared/fault-paths/fault-paths.md` § Observable vs. In-Memory-Only Fault Handling). Save-time error: `TRIGGER_TYPE_ELEMENT_NOT_SUPPORTED` — "A flow can't include Custom Error elements when TriggerType is set to None". See `elements/custom-error/custom-error.md`.

### Screen Flow
- **processType**: `Flow` + **triggerType**: absent (key omitted); runs interactively in user's browser
- No object, no filters, no scheduled paths; run-in mode configurable — see [Run-As User Context](#run-as-user-context)

### Automation Event-Triggered
- **triggerType**: `AutomationEvent` (OOTB engagement events); **processType**: `AutoLaunchedFlow`. `AdminAutomationEvent` and `ApiEventTrigger` are separate admin/API variants — do not resolve marketer intent to them.
- The flow FIRES when a core email-engagement event occurs (email open, link click, bounce, response). The event is set on the start via **`eventName` + `eventType`** (both carry the same trigger string) — NOT `actionName`/`actionType`. `$Event` is available once they are set. Optional entry `conditions`/`conditionLogic` (default: No Conditions).
- **You MUST load `automation-event-triggered.md` before configuring an `AutomationEvent` flow** — it carries the OOTB email-event catalog and the required start shape; none of it is derivable.
- **A valid (activatable) AutomationEvent flow also needs required start `inputs[]` (`associatedContent`; plus `specificLink` for link-click) and a flow-level `dataSpace`** — without them the flow saves but is `InvalidDraft`. This is the one AutoLaunched case where start `inputs[]` ARE populated; see `automation-event-triggered.md`.
- **Form Submission is NOT an `AutomationEvent` event.** The builder lists it in the Automation Event picker, but a form-submission flow saves as `triggerType: FormSubmissionEvent` — see [Form-Triggered](#form-triggered-marketing-form-submission). Never emit `AutomationEvent` + `trgrOnFormSubmission`.
- **Do NOT confuse with a mid-flow wait:** a flow that runs first and PAUSES until an engagement event uses `triggerType: IndivRelatedRecord` (or `Segment`) + a `WaitUntilEvent` element, whose event is set via `automationEventName`/`automationEventType` — see [Engagement / Journey-Triggered](#engagement--journey-triggered-indivrelatedrecord--required-for-mid-flow-wait-until-event). And do NOT confuse with `PlatformEvent` (a `__e` message, set via `object`).

### Data Cloud-Triggered (Single DMO Record Change)
- **triggerType**: `DataCloudDataChange`; **processType**: `AutoLaunchedFlow`. The flow FIRES when a single Data Cloud DMO record is created or updated.
- The DMO is set on the start via **`object`** (a `ssot__*__dlm` API name resolved from discovery), and **`recordTriggerType`** is `Create`, `CreateAndUpdate`, or `Update` (no `Delete`). `$Record` = the changed DMO record (read-only), referenced downstream as `$Record.<dmoField>`.
- **You MUST load `data-cloud-data-change-triggered.md` before configuring a `DataCloudDataChange` flow** — it carries the DMO discovery chain, the start shape, the writable-SObject write rule (DMOs are read/trigger-only), and the disambiguation from a data-graph trigger, from core record triggers, and from `AutomationEvent`; none of it is derivable.
- Requires a Data Cloud-provisioned org and API version 59.0+. Do NOT confuse with `DataGraphDataChange` (multi-object data graph, org-gated — see below), the core-SObject record triggers (`RecordAfterSave`/`RecordBeforeSave`/`RecordBeforeDelete`), or `AutomationEvent` (email engagement).

### Activation-Triggered (Data Cloud Activation Payload)
- **triggerType**: `Activation`; **processType**: `AutoLaunchedFlow`. The flow FIRES when a Data Cloud **activation** runs, once per activated member. The activation is set on the start (`activation` set) and its payload is exposed as **`$ActivationData`**, populated from the activation's `activationRecordSchema`.
- **`$ActivationData` is the canonical, authoritative data source for an `Activation` flow — read AND write through it.** Because `object` is also set on the start (e.g. `Account`), the builder ALSO exposes `$Record` ("Triggering Account"). **`$Record` is NOT the activation payload** — it is the underlying core record — and must NOT be the default read/write target. Defaulting to `$Record` produces a semantically wrong flow (it reads/updates the triggering record, not the activated member). `$ActivationData` supersedes `$Record` here; use `$Record` only when the request explicitly needs the core record.
- **`$ActivationData` attribute names come from the activation's `activationRecordSchema`, NOT the SObject field names** — they frequently differ (e.g. the attribute is `$ActivationData.AccountType`, not `$ActivationData.Type`). Discover the actual attribute names from the activation's `activationRecordSchema` before referencing them; do not assume they match the core object's fields.
- **Write path — update by `Id = $ActivationData.Id`, never `inputReference: "$Record"`.** To update the activated member, use Get/Update filtered on `Id Equals $ActivationData.Id` (or assign fields resolved from `$ActivationData`). An in-place `$Record` update writes the triggering core record, not the activation payload.
- **Expected advisory:** a pure-`$ActivationData` update (filter by `Id = $ActivationData.Id`) trips `TRIGGERED_FLOW_REDUNDANT_QUERY` on save. This warning is **acceptable and inherent** to the correct pattern — do NOT "resolve" it by switching to an in-place `$Record` update. The flow still saves and activates.
- Requires a Data Cloud-provisioned org with activations configured. Do NOT confuse with `DataCloudDataChange` (single DMO record change, uses `$Record`) or the audience triggers (`List`/`CampaignMember`/`RecordQuery` use `$Input`; `Segment` uses `$Record`, see `segment-triggered.md`).

#### Minimal worked example — `Activation` flow reading and writing `$ActivationData`
Request: "When an Account is activated, if the account type is Prospect, append 'prospect' to the Description."
- **Decision** reads the activation payload: `$ActivationData.AccountType Equals "Prospect"` (the `activationRecordSchema` attribute — NOT `$ActivationData.Type`, and NOT `$Record.Type`).
- **Get Records** on `Account` filtered `Id Equals $ActivationData.Id` (retrieves the activated member; expect the `TRIGGERED_FLOW_REDUNDANT_QUERY` advisory).
- **Assignment** builds the new Description from `$ActivationData` / the retrieved record.
- **Update Records** targets the record from Get (filtered by `Id = $ActivationData.Id`) — NOT `inputReference: "$Record"`.

### Form-Triggered (Marketing Form Submission)
- **triggerType**: `FormSubmissionEvent`; **processType**: `AutoLaunchedFlow`. The flow FIRES, headless, each time someone submits a Marketing form (a Form Builder form stored as Managed Content, `sfdc_cms__form`).
- The form is set on the start via **`form`** = the form's content FQN (`marketing--<ContentSpaceApiName>.sfdc_cms__form--<ContentKey>`, resolved from discovery — never guessed). No `eventName`/`eventType`, no start `inputs[]`; `actionName`/`actionType` are cleared on save. The submitted answers are `$Form.<field>`.
- **You MUST load `form-submission-triggered.md` before configuring a `FormSubmissionEvent` flow** — it carries the form discovery chain, the start shape, the `$Form` field names, and the one-form-per-flow rule; none of it is derivable.
- **HARD PROHIBITION:** never author a form-submission flow as `triggerType: AutomationEvent` + `eventName`/`eventType` `trgrOnFormSubmission`. Flow Builder lists Form Submission under the Automation Event picker, but it saves the flow as `FormSubmissionEvent`; the `AutomationEvent` shape is rejected (invalid event name, `InvalidDraft`).
- Do NOT confuse with a **Screen Flow** — a form the user steps through inside the flow is `processType: Flow`, not this trigger.

### Data Graph / Other
- `DataGraphDataChange`: requires `triggeringDataGraph` + `triggeringDataModelObjectPath`; `$Event` available

### Audience-Triggered flows (`Segment` / `List` / `CampaignMember` / `RecordQuery`)

All four share Core's `BaseAudienceTriggerTypeHandler` and enter an audience's members when the flow runs, on `processType: "AutoLaunchedFlow"`. They share one contract (run schedule, top-level `timeZoneSidKey`, top-level `dataSpace`, optional `dataGraph`, re-entry, save-and-activate gates) documented once in **`audience-common.md`** — **load it first for any of the four**, then load the per-trigger binding file below. None of these fields is derivable — do NOT guess them.

- **`Segment`** — targets a marketing segment/audience for outreach (email campaigns, drip sequences, re-engagement, nurture journeys) on a schedule or on activation. Do NOT use `Scheduled` or `RecordAfterSave` for segment-based marketing. A request to create a **broadcast** flow that fans out a dynamic segment now is `BroadcastNoTrigger`, not `Segment`. **MUST load `segment-triggered.md`** for the segment name→ID→DMO binding chain, the `segmentOnApiName` eligibility gate, `publishSegment`, outreach actions, and the `$Record` member context. Do not load `segment-triggered.md` for `BroadcastNoTrigger`.
- **`List` (Actionable List) / `CampaignMember` (Campaign)** — **MUST load `list-campaignmember.md`** for the `start.listAction` binding (List puts the `0wo…` ID in `actionName`; CampaignMember uses the `runCampaign` action with the `701…` ID in the `campaignId` input parameter), the audience-selection gate, and the record context (`$Input.ReferenceRecord` / `$Input.campaignMember`).
- **`RecordQuery` (all records of one SObject matching a filter)** — **MUST load `recordquery.md`** for the `start.object` (+ optional `start.filters`, **no** `listAction`) binding, the `CRM_OBJECT_SELECTION_REQUIRED` gate, and the direct `$Input.<field>` record context.

### Engagement / Journey-Triggered (`IndivRelatedRecord`) — required for mid-flow Wait Until Event
- **triggerType**: `IndivRelatedRecord`; **processType**: `AutoLaunchedFlow`; opened with **`builderType: JourneyBuilder`**.
- **Also called a CRM Triggered Flow.** A "CRM Triggered Flow" ("CRM Triggered", "CRM Trigger") request that says "marketing" is this trigger. Without "marketing", the resolver first asks whether the user wants this marketing Automation Event flow or a core Record-Triggered Flow. Flow Builder lists this type under Automation Event-Triggered Flow as "Prospect, Lead, Contact or Related Record Change". It runs when a Contact, Lead, Prospect, or related record changes and can send a marketing email (`sendEmailMessage`) with no mid-flow wait. Before writing the send, load `../action-call/action-call.md` § Send Email Message (E360): the email's content, sender and consent subscription are literal Ids that you look up by name, not a Get Records lookup in the flow. Record-change wording in such a request ("every time a Contact is updated") sets `object` and `recordTriggerType` below; it does not make the flow a core record-triggered flow. The resolver rule is in `../../shared/flow-type-resolver/flow-type-resolver.md`.
- This is the trigger a flow needs when it pauses on a customer **engagement event** via a mid-flow `WaitUntilEvent` Wait element (email open/click/bounce, SMS response/click/delivery-failure, or a Journey Builder contact event). A plain no-trigger `AutoLaunchedFlow` **cannot** host a `WaitUntilEvent` element — the save is rejected with `ELEMENT_SUBTYPE_NOT_SUPPORTED_FOR_PROCESSTYPE` ("the WaitUntilEvent flow element subtype isn't supported with the AutoLaunchedFlow process type"). `IndivRelatedRecord` (or `Segment`) clears that gate. See `../wait/wait.md` for the Wait Until Event element shape.
- **Required Start fields** (from a real retrieved engagement flow):
  - `object` — the individual-related object the engagement is scoped to (e.g. `Lead`). **Must be set**; leaving it blank blocks activation.
  - `recordTriggerType` — `Create`, `Update`, or `CreateAndUpdate`.
  - `filters` / `filterLogic` — entry criteria on that object (e.g. `IsDeleted = false`); use the no_conditions omission rule when there are none.
- **Record context — reference the triggering record as `$Input`, never `$Record`.** The triggering individual-related record is exposed as the bare **`$Input`** SObject (its object = the Start `object` above, e.g. `Lead`). Reference its fields as `$Input.<FieldApiName>` (e.g. `$Input.Status`) in decision conditions, filters, assignments, and record-update input references. Do **NOT** use `$Record`: for this trigger `$Record` is reserved for the Unified-Individual context and does not carry the triggering related record — yet the builder still offers `$Record` and a flow referencing it passes save-time validation, so the mistake is silent (no save error). Note the bare whole-record reference `{!$Input}` can trip a save error ("You can't use the variable "$input" without referencing a field"), so always reference a field; related-record traversal such as `$Input.Contact__r` is a known platform gap.
- **Expected advisory:** an Update Records filtered on `Id Equals $Input.Id` trips `TRIGGERED_FLOW_REDUNDANT_QUERY` on save. This warning is **acceptable and inherent** to the `$Input` rule above — do NOT "resolve" it by switching to `$Record`. The flow still saves.
- **Set `dataSpace` on the top-level flow object — required to activate.** Omitting it saves a draft but blocks activation with `DATA_SPACE_REQUIRED_FOR_FLOW_TYPE` ("Specify a data space in this automation's properties."). Set it on the FIRST save, not reactively after the warning. Resolve it through Data 360 for this `IndivRelatedRecord` context. This is the top-level flow field, NOT a Start field. Follow `audience-common.md` § [Set the data space](audience-common.md#set-the-data-space) for the shared data-space resolution (including the Send-to-Journey business-unit rule).
- **Do NOT set `timeZoneSidKey`** on the Start for this trigger unless a downstream element requires it — like a plain AutoLaunchedFlow, engagement flows use implicit timing (the WaitUntilEvent path nulls out `timeZoneId`; see `../wait/wait.md`).
- Journey Builder contact events additionally need the Wait event's `mceJourneyInput` (the MCE Journey id) — that lives on the Wait element, not the Start; see `../wait/wait.md`.
- This trigger is only meaningful in a journey/engagement-provisioned org (the `WaitForAutomationEvents` permission + a provisioned Event Library). To discover the org's available engagement events at runtime, see the discovery guidance in `../wait/wait.md` (use `GET /services/data/vXX.0/flowbuilder/action/invocable-events` with `triggerType: "Segment"` (the OAS param name, not `flowTriggerType`); that discovery `triggerType` is independent of this Start's own `triggerType`).

### Broadcast (dynamic segment fan-out)
- **triggerType**: `BroadcastNoTrigger`; **processType**: `AutoLaunchedFlow`. This is a broadcast flow. It is not a Segment-triggered flow, even when the audience is a dynamic segment. Do NOT load `segment-triggered.md`. Do NOT apply that file's Individual-only eligibility gate, and do NOT require a run schedule, `timeZoneSidKey`, or `start.object`.
- The segment may be built on any DMO the org already uses for broadcast, including Account (`ssot__Account__dlm`) and Unified Individual (`UnifiedIndividual__dlm`). Resolve the segment the same way as a name lookup: `d360_segment_get` when the prompt gives the API name, otherwise `d360_segment_list` and match `displayName`. Use the resolved `apiName`. Do not invent a segment and do not substitute a different one.
- **The audience is `start.fanOutAction`, not a canvas `actionCalls` element and not `start.object`.** The fan-out has no name, no label, and no connector. `actionType` is `cdpJitSegment`. `actionName` and `nameSegment` are the segment API name (for example `Account_Dyn_Seg`), never the string `cdpJitSegment`. Describing `actionName=cdpJitSegment` returns an empty descriptor; describe `actionName=<segment api name>`. Do not substitute `cdpSendToActivation` or `cdpPublishSegment`.
- **Run type** is `start.isAsync`. `false` is Sync. Omit it only when the user did not ask; the platform treats a missing value as sync. Do not ask for a schedule.
- Set top-level `dataSpace` from the segment (`default` when the segment is in the default data space). A start whose connector goes straight to End is a valid draft when the user did not ask for a body element.
- **Per-member fields are `$Input.<segmentOnApiName>.<fieldApiName>`**, stored as an `elementReference`, not a string literal. Example: `$Input.UnifiedIndividual__dlm.ssot__FirstName__c`. Confirm the field exists on that DMO before wiring it. `$Input` is one fan-out row, the current segment member.

#### Minimal worked example
Request: "Create a broadcast flow on the dynamic segment Account Dyn Seg. Add a Create Contact whose First Name comes from that segment member. Save it as a draft."
- Resolve `Account Dyn Seg` to its API name and `segmentOnApiName`.
- `metadata.start.triggerType` = `BroadcastNoTrigger`, `isAsync` = `false`, no `object`.
- `metadata.start.fanOutAction` = `{ "actionType": "cdpJitSegment", "actionName": "<segment api name>", "nameSegment": "<segment api name>" }`.
- Create Records on Contact. First Name `elementReference` = `$Input.<segmentOnApiName>.<firstName field>`.
- Start connector targets that Create Records element, which connects to End.

### On-Demand (`OnDemandNoTrigger`)
An On-Demand Flow is a marketing flow that an app or integration starts through the API, one person at a time. Use it when the request names an On-Demand Flow, or asks for a marketing send (`sendEmailMessage`, `sendSmsMessage`, `sendToJourney`) that an app or the API triggers for a specific person. Without a marketing send, a flow that "runs on demand" stays no-trigger (`triggerType` omitted); the rule is in `../../shared/flow-type-resolver/flow-type-resolver.md`.
- **triggerType**: `OnDemandNoTrigger`; **processType**: `AutoLaunchedFlow`. No `object`, no `filters`, no schedule. Do NOT load `segment-triggered.md`.
- **Top-level `dataSpace` is required.** Resolve it as in `audience-common.md` § [Set the data space](audience-common.md#set-the-data-space). Without it, activation fails: `Specify a data space in this automation's properties.`
- **Check the action catalog for this context.** Call `dispatch_readonly(method: "GET", url: "/services/data/vXX.0/flowbuilder/action/invocable-actions", queryParams: { processType: "AutoLaunchedFlow", triggerType: "OnDemandNoTrigger", dataSpace: "<data space>" })` and require the send action in the result. A no-trigger flow's catalog does not offer the E360 send actions, and saving one there fails, for example: `You can't use the Send SMS Message action type in flows with the Autolaunched Flow process type.`
- **The recipient is not an action parameter.** The caller supplies the person in the launch request (`IndividualId`, `EmailAddress`, `TelephoneNumber`), and the send actions use that. A send needs no flow variable for the recipient, so do not add one. Declare your own `isInput` variables only for the other values the caller passes (for example a flag that drives a Decision). To read the person's fields in the body, add a `start.dataGraph` (below); do not invent an `IndividualId` variable.
- **Person fields: `start.dataGraph` + `$SelectedIndividual`.** Resolve the graph as in `audience-common.md` § [Set the data graph](audience-common.md#set-the-data-graph) and check that its backing DMO (`dgObject.developerName`) is Unified Individual or Individual; any other fails: `This flow type requires that the primary data model object (DMO) of the specified data graph be UnifiedIndividual or Individual.` Then read the person's fields as `$SelectedIndividual.<field>` (for example `$SelectedIndividual.ssot__FirstName__c`), for example in Decisions and Exit Rules. Without a `dataGraph`, `$SelectedIndividual` fails: `The "$SelectedIndividual.<field>" element doesn't exist.` Use `$SelectedIndividual`, not `$Record`: `$Record.<field>` also saves when a data graph is set, but its runtime value in an On-Demand Flow is not verified.
- **Exit Rules are allowed**, both condition-based and event-triggered (`../exit-rule/exit-rule.md`).
- **Output variables are not returned to the API caller.** The launch response's `outputValues` is empty even when the flow sets an `isOutput` variable. If the user asks for an On-Demand Flow that returns values, keep it `OnDemandNoTrigger` (never switch to a plain autolaunched flow for this), declare the `isOutput` variables they ask for, and say that an On-Demand launch does not return them in the plan summary (before approval) and in your final reply. If they need the values back, ask how they want them delivered; don't add a delivery step they haven't agreed to.
- **It can't be a subflow.** A Subflow element that references an On-Demand Flow fails to save. No Screen elements (it is an `AutoLaunchedFlow`). If the user wants an E360 send inside a subflow, no shape works: a no-trigger flow can't host the send, and an On-Demand Flow can't be a subflow. Say so and offer an On-Demand Flow the app calls directly, or a core action such as `emailSimple` in the subflow.
- It is a marketing flow: add a fault path only when the user asks for error handling (`../../shared/fault-paths/fault-paths.md` § Marketing Flows — Fault Paths Only When Asked).
- Apps launch it with `POST /services/data/vXX.0/actions/custom/flow/<FlowApiName>` and body `{ "inputs": [ { "IndividualId": "…", "TelephoneNumber": "…" } ] }`: pass the contact point the send uses (`EmailAddress` for an email, `TelephoneNumber` for an SMS). The flow must be Active before an app can launch it. The running user needs access to this flow (a permission set or profile that grants the flow), not just Run Flows; otherwise the call fails with `The running user doesn't have the required access to run the flow.` Building the flow does not call this endpoint; mention the access step in your final reply.

Fragment of `metadata` (the rest of the flow is normal):
```json
{
  "processType": "AutoLaunchedFlow",
  "dataSpace": "default",
  "start": {
    "locationX": 0, "locationY": 0,
    "triggerType": "OnDemandNoTrigger",
    "connector": { "targetReference": "Send_Welcome_SMS" }
  }
}
```

### Other Trigger Types
- `ExternalSystemChange`, `EnterpriseScaleExternalSystemChange`, `Capability` — these are specialized trigger types for external system integrations and UMA flows. Each has distinct requirements not covered here. (For `DataCloudDataChange`, see [Data Cloud-Triggered](#data-cloud-triggered-single-dmo-record-change) above and `data-cloud-data-change-triggered.md`; for `Activation`, see [Activation-Triggered](#activation-triggered-data-cloud-activation-payload) above — it defaults to `$ActivationData`, NOT `$Record`; for `BroadcastNoTrigger`, see [Broadcast](#broadcast-dynamic-segment-fan-out) above; for `OnDemandNoTrigger`, see [On-Demand](#on-demand-ondemandnotrigger) above.)

## Required Properties

| Property | Constraints |
|---|---|
| `triggerType` | Must be valid for the flow's `processType` |
| `object` | Required for `RecordBeforeSave`, `RecordAfterSave`, `RecordBeforeDelete`, `Scheduled`; valid SObject API name |
| `recordTriggerType` | Required for record-triggered flows; auto-set to `Delete` for `RecordBeforeDelete` |
| `startDate` + `frequency` | Required for Scheduled flows |
| `eventName` + `eventType` | Required for `AutomationEvent` (both carry the same trigger string) — see `automation-event-triggered.md` |
| `associatedContent` (+ `specificLink` for link-click) | Required start `inputs[]` for `AutomationEvent` flows — see `automation-event-triggered.md` |
| `form` | Required for `FormSubmissionEvent` — the form's Managed Content FQN, resolved via discovery — see `form-submission-triggered.md` |

## Optional Properties

| Property | Default | Notes |
|---|---|---|
| `filters` / `filterLogic` | No Conditions | Entry criteria — see [Filter Logic](#filter-logic--entry-criteria) |
| `filterFormula` | None | Alternative to filter rows; mutually exclusive with `filters[]` |
| `doesRequireRecordChangedToMeetCriteria` | false | Only valid for Update and CreateAndUpdate. Do NOT combine with a `$Record__Prior` reference in `filters`/`filterFormula` — invalidates the Start (`FORMULA_EXPRESSION_INVALID`); see Validation Rules |
| `flowRunAsUser` | Running user | User context for scheduled flow execution |
| `maxBatchSize` | Platform default | Only when `CustomBatchSize` feature enabled |
| `endDate` / `endTime` | None | When recurring scheduled flow stops |
| `frequencyNumber` | 1 | **Audience triggers only (Segment/List/CampaignMember/RecordQuery); rejected on Scheduled flows.** See `audience-common.md` § [Run schedule](audience-common.md#run-schedule). |
| `conditions` / `conditionLogic` | No Conditions | Automation event flows only |

## Filter Logic / Entry Criteria

**Critical — `no_conditions` omission rule**: When filter logic is "No Conditions" — emit `filters: []` and **omit `filterLogic` entirely**. Do NOT emit `"filterLogic": "no_conditions"` — it is a UI-only sentinel the server strips on save (not a hard rejection), but emit the omitted form rather than relying on clean-up. See `shared/anti-patterns.md` #12.

- `No Conditions` — every qualifying record triggers the flow
- `All Conditions Are Met (AND)` / `Any Condition Is Met (OR)` — standard filter row evaluation
- `Custom logic` — combine with AND/OR expression (e.g., `1 AND (2 OR 3)`)
- `Formula Evaluates to True` — formula expression replaces all filter rows

For **scheduled flows**: `filterLogic` required — cannot be "No Conditions" (save error if missing).

## recordTriggerType Values

| Value | Meaning |
|---|---|
| `Create` | New record created |
| `Update` | Existing record updated |
| `CreateAndUpdate` | Record created or updated |
| `Delete` | Record deleted (`RecordBeforeDelete` only) |

## System Variables Available

Rows are evaluated top-down and the FIRST matching row wins. `Activation` is the exception — it matches both the `object`-is-set row and its own row, and the `Activation` row is **authoritative** (see the note below the table).

| Condition | Variable |
|---|---|
| `Activation` trigger + `activation` set | **`$ActivationData`** — authoritative; use over `$Record` (see note below) |
| `IndivRelatedRecord` trigger (`object` + `recordTriggerType` set; Journey Builder) | **`$Input`** — the triggering individual-related record; **NOT `$Record`** (see note below) |
| `Segment` trigger (`object` = the segment's DMO) | `$Record`: the current segment member, `$Record.<field>`, never the bare field name (see `segment-triggered.md`) |
| `BroadcastNoTrigger`, `RecordQuery`, `List`, or `CampaignMember` trigger | `$Input` (Broadcast: `$Input.<segmentOnApiName>.<field>`; see [Broadcast](#broadcast-dynamic-segment-fan-out)) |
| `object` is set, record-triggered (NOT `Activation` or `IndivRelatedRecord` — most cases) | `$Record` |
| `DataCloudDataChange` (`object` = a DMO) | `$Record` (the changed DMO record; NOT `$Event`) |
| (`RecordBeforeSave` or `RecordAfterSave`) + `recordTriggerType` = Update or CreateAndUpdate | `$Record__Prior` |
| `FormSubmissionEvent` trigger + `form` set | `$Form` — the submitted answers, `$Form.<field>` (field names from the form; NOT `$Event` or `$Record`) |
| Automation event + `eventName`/`eventType` set | `$Event` |
| `OnDemandNoTrigger` + `dataGraph` set | `$SelectedIndividual` (the person the caller passed; the data graph must be rooted on Unified Individual or Individual; see [On-Demand](#on-demand-ondemandnotrigger)) |

> **`Activation` trigger — `$ActivationData` wins over `$Record`.** An `Activation` flow sets `object` too, so the builder also exposes `$Record` ("Triggering <Object>"). This overlap is **not** symmetric: `$ActivationData` is the canonical activation payload and the default read/write target; `$Record` is the underlying core record and must **not** be the default. Attribute names come from the activation's `activationRecordSchema` (e.g. `$ActivationData.AccountType`, not `$ActivationData.Type`). Full guidance and a worked example: [Activation-Triggered](#activation-triggered-data-cloud-activation-payload).

> **`IndivRelatedRecord` trigger — `$Input`, not `$Record`.** An Individual Related Record-Triggered (Engagement/Journey) flow sets `object` + `recordTriggerType`, so the builder *also* offers `$Record` ("Triggering <Object>") and a flow referencing it still passes save-time validation — but at runtime `$Record` is reserved for the Unified-Individual context and does **not** carry the triggering record. The triggering individual-related record is the bare **`$Input`** SObject (its object = the Start `object`, e.g. `Lead`); reference fields as `$Input.<FieldApiName>` (e.g. `$Input.Status`). Full guidance and the bare-reference gotcha: [Engagement / Journey-Triggered](#engagement--journey-triggered-indivrelatedrecord--required-for-mid-flow-wait-until-event).

Reference as `elementReference` literal strings: `"$Record"`, `"$Record__Prior"`, `"$ActivationData"`.

| `recordTriggerType` | `$Record` | `$Record__Prior` |
|---|---|---|
| `Create` | Available | NOT available — save error: "element doesn't exist" |
| `Update` | Available (new values) | Available (pre-update values) |
| `CreateAndUpdate` | Available (new values) | Available (pre-update values for updates) |
| `Delete` | Available (read-only) | NOT available |

## Scheduled Paths

Only available for `AutoLaunchedFlow` + `RecordAfterSave`.
- **`Create`**: always available once object is selected
- **`Update` / `CreateAndUpdate`**: require `doesRequireRecordChangedToMeetCriteria: true` + at least one filter

The `start.connector` = Immediate path (synchronous). `scheduledPaths[]` = time-delayed async branches.

### scheduledPaths Metadata Shape

`scheduledPaths` is an array directly inside the `start` object.

| Field | Type | Notes |
|---|---|---|
| `label` | string | Omitted for `AsyncAfterCommit` and `ApprovalRecall` path types |
| `name` | string | API name; unique within flow |
| `offsetNumber` | number | Positive = after; negative = before |
| `offsetUnit` | string | `"Minutes"`, `"Hours"`, `"Days"`, `"Weeks"`, `"Months"` — NOT `"DaysAfter"` / `"DaysBefore"` (UI strings, not valid metadata) |
| `timeSource` | string | `"RecordTriggerEvent"` or `"RecordField"` |
| `recordField` | string | Required when `timeSource: "RecordField"`; field API name (e.g., `"CloseDate"`); omit otherwise |
| `pathType` | string or null | `null` = standard; `"AsyncAfterCommit"` = async after commit; `"ApprovalRecall"` = requires org permission |
| `connector` | Connector | Edge to first element in this path; required |
| `maxBatchSize` | number | Range 1–200; omit when not needed |

```json
"start": {
  "triggerType": "RecordAfterSave",
  "object": "Opportunity",
  "recordTriggerType": "Create",
  "scheduledPaths": [
    {
      "label": "Follow Up 3 Days After Create",
      "name": "Follow_Up_3_Days_After_Create",
      "offsetNumber": 3,
      "offsetUnit": "Days",
      "timeSource": "RecordTriggerEvent",
      "connector": { "targetReference": "Send_Follow_Up_Email", "isGoTo": false },
      "pathType": null
    }
  ],
  "connector": { "targetReference": "Immediate_Action", "isGoTo": false }
}
```

## Run-As User Context

Configured at **flow root** (`metadata.runInMode`) — NOT on the Start element. The UI picker surfaces this only for autolaunched no-trigger flows, but metadata writing accepts it for any flow type and it is runtime-effective on screen flows as well.

| Mode | Behavior |
|---|---|
| `SystemModeWithoutSharing` | Runs as system; ignores sharing rules — use for background jobs, cross-user data access |
| `SystemModeWithSharing` | Runs as system; respects sharing rules |
| *(not set)* | Runs as invoking user — use for subflows from Screen Flows, user-context operations |

Orchestration, Evaluation, Auto Approval Evaluation, and Approval Workflow flows default to `SystemModeWithoutSharing` on creation.

## Validation Rules and Constraints

- `triggerType` blank → save error
- `object` blank for record-triggered or scheduled → save error
- `recordTriggerType` blank for record-triggered → save error
- `filterFormula` blank when filter mode is formula → save error
- `filterLogic` blank or null for scheduled flows → save error
- `filterFormula` + `filters[]` both present → save error: "Cannot specify both filters and filterFormula"
- `doesRequireRecordChangedToMeetCriteria` auto-set to `false` when `recordTriggerType` is not `Update` or `CreateAndUpdate`
- `maxBatchSize` only persisted when `CustomBatchSize` feature enabled; scheduled flows require API runtime v63+
- `$Record__Prior` reference in a Create flow → save error: "element doesn't exist"
- DML elements in a Before Save flow → runtime failure (saves fine, fails silently when triggered)
- `elementReference` value in record-triggered or Scheduled Start `filters[]` → blocks activation: `RECORDFILTER_NON_PRIMITIVE` — only literal typed values allowed
- **Workaround for reference-based Start filtering — record-triggered ONLY**: use `filterFormula` with `filterLogic: "formula_evaluates_to_true"` — formulas can evaluate `$Flow.CurrentDate`, `$Record.Field`, etc.
- **This workaround does NOT apply to `triggerType: Scheduled`.** Scheduled flows reject `filterFormula` outright (`FORMULA_EXPRESSION_INVALID`, `InvalidDraft`) — formula entry criteria is record-triggered-only. For a Scheduled flow that needs formula/reference-based selection, use literal `filters[]` + a body Decision, or a precomputed formula field on the object. See the Scheduled section above.
- **`$Record__Prior` in entry criteria + `doesRequireRecordChangedToMeetCriteria: true` → blocks activation** (`FORMULA_EXPRESSION_INVALID`, saves as InvalidDraft with `isSuccess: true` — inspect `warnings`). Full rule, detection, and fix: [[flow.shared.anti-patterns]] #33.
- A mid-flow `WaitUntilEvent` element requires `triggerType: IndivRelatedRecord` (or `Segment`); a no-trigger `AutoLaunchedFlow` rejects it with `ELEMENT_SUBTYPE_NOT_SUPPORTED_FOR_PROCESSTYPE`. For `IndivRelatedRecord`, `object` + `recordTriggerType` are required — a blank `object` blocks activation.

## Common Patterns

- **Run only on meaningful field changes**: `recordTriggerType: Update` + filter conditions on fields of interest + `doesRequireRecordChangedToMeetCriteria: true`
- **Trigger on a prior-vs-new comparison** (e.g. "new Amount > 20% over old Amount", "Stage moved backward"): `recordTriggerType: Update`, `doesRequireRecordChangedToMeetCriteria` **omitted/`false`**, entry criteria left broad (or `filterFormula` referencing `$Record__Prior` with the flag off), then a **Decision** element in the body does the `$Record__Prior.Field` vs `$Record.Field` comparison. Setting the flag `true` here breaks the Start — see Validation Rules.
- **Process all open cases daily**: `triggerType: Scheduled`, `object: Case`, `frequency: Daily`, filter `Status != Closed`
- **Follow-up email 3 days after create**: `RecordAfterSave` + `Create` + scheduled path `offsetNumber: 3`, `offsetUnit: "Days"`, `timeSource: "RecordTriggerEvent"`
- **Platform event handler**: `triggerType: PlatformEvent`, `object` = event API name (e.g., `"Payment_Page_Change__e"`), access fields via `$Record`
- **Autolaunched from Apex with elevated access**: triggerType absent, `AutoLaunchedFlow`, `runInMode: SystemModeWithoutSharing` at flow root
- **Screen flow with elevated access**: `processType: Flow`, triggerType absent, `runInMode: SystemModeWithoutSharing` at flow root — bypasses record sharing for all users
- **Stamp a default field value before save**: `RecordBeforeSave` + Assignment to `$Record.<FieldName>` — no `recordUpdates` needed

## AI Agent Guidelines

### Pre-Generation Checks

1. Determine `processType` BEFORE writing Start — all Start fields depend on it.
2. For record-triggered flows: verify `object` is a valid SObject API name and `recordTriggerType` is set; use full enum strings (`RecordBeforeSave`, `RecordAfterSave`, `RecordBeforeDelete`) — short forms (`BeforeSave`, `AfterSave`, `BeforeDelete`) are invalid.
3. For Before Save (`RecordBeforeSave`): confirm the flow body has NO `recordCreates`, `recordUpdates`, `recordDeletes`, or `recordLookups` — these save fine but fail silently at runtime.
4. For Scheduled flows: include `filterLogic` (save error if missing) and emit the full `schedule` block (`frequency`, `startDate`, `startTime`) — omit the block entirely if `frequency` is unset.
5. For scheduled paths (AfterSave): verify `recordTriggerType` is `Update` or `CreateAndUpdate` + `doesRequireRecordChangedToMeetCriteria: true` + at least one filter.
6. `doesRequireRecordChangedToMeetCriteria` is only valid for `Update` or `CreateAndUpdate`; omit for `Create` and `Delete`. When the entry criteria compares against prior values (`$Record__Prior.*` in `filters`/`filterFormula` — e.g. "new Amount > old Amount"), do NOT set the flag `true`: it invalidates the Start with `FORMULA_EXPRESSION_INVALID`. Move the prior-vs-new comparison into a body Decision, or leave the flag `false`.
7. Use `filterFormula` OR `filters[]`, never both (save error).
8. For PlatformEvent: use `object` = event API name — do NOT emit `eventName` or `eventType` (they cause save failure: `Can not construct instance of com.sforce.soap.tooling.wsc.InvocableActionType`).
9. For Autolaunched (no trigger): omit `triggerType` entirely — NEVER emit `"triggerType": "None"`; it is a serialization error; place `runInMode` at `metadata.runInMode`, not on Start.
10. For a marketing flow (its `triggerType` is on the list in `shared/fault-paths/fault-paths.md` § Marketing Flows — Fault Paths Only When Asked): add no `faultConnector` or error-handling branch unless the user asks for error handling, and don't ask about it or offer it in the plan. A flow with no `triggerType` (item 9) is not a marketing flow.

## Aura/Server Functions

- `getTriggerTypeInfo` — configuration for a trigger type for dynamic Start element setup
- `getFlowEntries` — available flow types and supported trigger type options
- `getIsPauseSupported` — whether Wait/Pause element is available for current process type + trigger type
- `getIsReadModeEnabled` — whether read mode (flow insights) is available
- `getFrpQuickAccess` — flow-level quick access options for record-triggered flows (FRP feature)

## Metadata Shape

`metadata.start` is a **singleton object** (not an array). Include only fields relevant to the `triggerType`.

`label`, `name`, and `description` are NOT valid on the Start element.

### Common fields (all trigger types)

| Field | Type | Required | Notes |
|---|---|---|---|
| `triggerType` | string | conditional | Required for record-triggered, scheduled, and event flows. Must be absent (key not present) for autolaunched/screen flows — NEVER use `"None"` or `""`. Valid values: `"RecordBeforeSave"`, `"RecordAfterSave"`, `"RecordBeforeDelete"`, `"Scheduled"`, `"PlatformEvent"` |
| `connector` | Connector | yes | Edge from Start → first downstream element |
| `locationX` / `locationY` | number | yes | Canvas position |

### Record-triggered fields (`RecordBeforeSave`, `RecordAfterSave`, `RecordBeforeDelete`)

| Field | Type | Required | Notes |
|---|---|---|---|
| `object` | string | yes | sObject API name |
| `recordTriggerType` | string | yes | `Create`, `Update`, `CreateAndUpdate`, or `Delete` |
| `doesRequireRecordChangedToMeetCriteria` | boolean | conditional | Only for Update/CreateAndUpdate; forced `false` when filterLogic is no_conditions |
| `filters` | array | yes | RecordFilter objects; `[]` valid — omit `filterLogic` when empty |
| `filterLogic` | string | conditional | `"and"`, `"or"`, expression, or `"formula_evaluates_to_true"`; omitted when no conditions |
| `filterFormula` | string | conditional | Only when `filterLogic: "formula_evaluates_to_true"` |
| `scheduledPaths` | array | no | AfterSave only — see [Scheduled Paths](#scheduled-paths) |
| `isAsync` | boolean | conditional | `true` only for AfterSave flows running async after DB commit; omit for standard AfterSave; set by UI automatically — do not emit manually |

### Scheduled fields (`triggerType: Scheduled`)

| Field | Type | Required | Notes |
|---|---|---|---|
| `schedule` | object | yes | `{ frequency, startDate, startTime, endDate?, endTime? }` — omit entire block if `frequency` unset. On save, `startTime`/`endTime`/`startDate`/`endDate` must be wire strings (`"HH:mm:ss.SSS"` / `"YYYY-MM-DD"`), never the retrieve read-back form (`{timeInMillis}` / epoch millis) — see the Scheduled section above and `shared/anti-patterns.md` item 39. |
| `object` | string | conditional | sObject API name (record-batch scheduled flows) |
| `filters` / `filterLogic` | — | conditional | As record-triggered; `filterLogic` required for scheduled flows |
| `flowRunAsUser` | string | no | User impersonation; omit when not needed |
| `maxBatchSize` | number | no | Only when `isCustomBatchSizeSupported` is true |

`schedule.frequency` for `Scheduled` flows must be one of `Once`, `Daily`, or `Weekly`. Enhanced-scheduling fields (`frequencyNumber`, `daysOfWeekToRun`, `dayOfMonthToRun`) are Segment-only — see the Scheduled section above.

### PlatformEvent fields (`triggerType: PlatformEvent`)

| Field | Type | Required | Notes |
|---|---|---|---|
| `object` | string | yes | Event API name (e.g., `Payment_Page_Change__e`) — verify with `dispatch_readonly(method: "GET", url: "/services/data/vXX.0/flowbuilder/platform/event-types", queryParams: { eventType: "Runtime" })`; if its category is unknown, also query `Setup` and `ManagedSetup` explicitly |
| `inputs` | array | conditional | InputParameter objects bound to event-payload fields |
| `versionString` | string | no | Default `""` |
| `filters` / `filterLogic` | — | no | Filter the event payload |

**INVALID fields** (cause save failure): `eventName`, `eventType` — do NOT emit these for PlatformEvent flows. Use `object` instead.

### Capability fields (`triggerType: Capability`)


| Field | Type | Required | Notes |
|---|---|---|---|
| `capabilityTypes` | array | yes | `[{ capability: string, inputs: [{ name, dataType, isCollection?, sobjectType? }] }]` |

`capabilityTypes[i].inputs[j].dataType` is a data type value (`"String"`, `"Number"`, `"SObject"`, `"Apex"`, …) — **not** a value-field `*DataType`.

### RecordFilter Shape

See [[flow.shared.record-filter]] for the full field/operator/value shape, operator reference, value types, and filterLogic co-presence contract.

**Start-specific**: **record-triggered** `start` elements support `filterFormula` as an alternative to `filters[]`; `filterFormula` / `filterLogic: "formula_evaluates_to_true"` is **INVALID on `triggerType: Scheduled`** (yields `FORMULA_EXPRESSION_INVALID` + `InvalidDraft` — see the `filterFormula` vs `filters` note below). Both record-triggered and Scheduled Start elements reject `elementReference` in `filters[]`. See the restriction callout in [[flow.shared.record-filter]] for details, the Scheduled fallback (literal `filters[]` + body Decision), and workarounds.

See [[flow.shared.record-filter]] §filterLogic Co-Presence Contract for the full rule: omit `filterLogic` when `filters: []`, never emit the literal string `"no_conditions"`.


### `filterFormula` vs `filters` — mutually exclusive

- **Standard**: `filters[]` + `filterLogic` (`"and"`, `"or"`, or expression)
- **Formula**: `filterLogic: "formula_evaluates_to_true"` + `filterFormula: "<expression>"` — no_conditions omission rule does NOT apply in formula mode. **Formula mode is record-triggered-only — it is INVALID on `triggerType: Scheduled`** (Scheduled supports literal `filters[]` only; a `filterFormula` there yields `FORMULA_EXPRESSION_INVALID` + `InvalidDraft`).

### filterFormula Reference Syntax

`filterFormula` is a formula expression — use `{!reference}` syntax for system variables and flow resources, same as Formula resources and inline formulas. See `examples/filterFormula-dateRange.json` for a worked example with date arithmetic, and [[flow.shared.formula-expression]] §3 for full merge-field syntax rules.

### RecordBeforeSave — minimal example

See `examples/beforeSave.json`. `filterLogic` omitted — no entry conditions (no_conditions omission rule).
