---
name: flow-element-wait
license: LICENSE.txt has complete terms
description: "Use this skill when the user asks about the Wait or Pause element in a flow, including resume conditions (time-based, date-based, duration-based, platform event, or wait-until-event), scheduled pause behavior, or any question about pausing a flow and resuming it later. TRIGGER when: user asks to pause a flow, wait for a time or event, or configure a Wait element. DO NOT TRIGGER when the user needs a scheduled trigger on the Start element (use flow-element-start)."
metadata:
  version: "1.0"
  related-skills: flow-conditions
---

# Wait / Pause Element

## Overview

The Wait element pauses a flow interview and resumes it later when one or more resume conditions are met. It is only available in flows that support asynchronous execution (primarily autolaunched flows and record-triggered flows). The element stores outputs from whichever condition fires and routes execution down the corresponding path.

## When to Use

Use a Wait element when the flow needs to:
- Pause until a specific date/time in the future
- Pause for a fixed number of minutes, hours, days, weeks, or months
- Pause until a platform event is received
- Pause until a customer interaction event occurs (email open/click, SMS response, WhatsApp response, etc.)
- Implement a multi-step timed sequence inside an autolaunched or record-triggered flow

Wait elements are NOT available in screen flows or other synchronous flow types. To check programmatically, call `dispatch_readonly(method: "GET", url: "/services/data/vXX.0/flowbuilder/schema/flow-capabilities", queryParams: { processType, triggerType })` and confirm `Wait` appears in `.elements` — that list is filtered by the full `(processType, triggerType)` pair, so it is the authoritative availability signal. Do **not** rely on `GET /services/data/vXX.0/flowbuilder/schema/trigger-types` detail-mode `.isPauseSupported`: that field is computed from `triggerType` alone (a different signal from the `(processType, triggerType)` pause check).

## Do NOT emit the base (classic) `Wait` — use a subtype

The general palette-authorable rule is `shared/anti-patterns.md` item 29 (never
emit an element with no `configComponent`). Below is how it applies to the Wait
family.

**Do not generate a Wait element without an `elementSubtype` by default** (see the
narrow exception below for explicitly-requested classic Waits). The base `Wait`
type (the multi-branch "classic" Wait with `defaultConnector` + `faultConnector`
+ `eventType`-based `waitEvents` such as `AlarmEvent`/`DateRefAlarmEvent`/platform
events) is **metadata-valid but not authorable in the canvas palette**. It passes
API save-time validation, so a raw metadata save succeeds, but Flow Builder never
offers a palette tile for it — the saved element renders as an orphaned/odd node
the user cannot recreate or cleanly edit in the UI.

How to tell the difference from `GET /services/data/vXX.0/flowbuilder/schema/flow-capabilities` (read `.elements`): the base `Wait` entry
has `"isElementSubtype": false`, `"attributes": null`, and **no `configComponent`,
`icon`, or `label`**. Only entries that carry a `configComponent` (an editor
component) are palette-authorable. For the Wait family those are the three
subtypes below.

**Default to one of the three canvas-authorable subtypes** (`WaitDuration`,
`WaitDate`, `WaitUntilEvent`). There is no fourth, canvas-authorable classic Wait
variant — do not present "classic Wait" as a distinct option to the user, and do
not proactively construct it via metadata even though the org will accept it.

**Narrow exception — an explicitly requested classic Wait.** The prohibition is a
default, not an absolute. Author a classic Wait (no `elementSubtype`) ONLY when the
user explicitly asks for behavior that no canvas subtype can express — namely
multi-branch **"by Criteria"** resumption (variant 01) or a **date relative to a
record field** (`DateRefAlarmEvent`, variant 04). In that case, build it per the
worked, activatable examples in the "Classic Wait Events REQUIRE `inputParameters`"
section below (every time-based branch needs its full five `inputParameters`), and
tell the user it will render as a non-palette node in the canvas. Do NOT reach for
a classic Wait for any request a subtype already covers (a fixed delay → duration,
an absolute date → date, an engagement event → until-event).

## Wait Subtypes

The element uses an `elementSubtype` field to distinguish between the simplified and classic variants:

| Subtype | UI Name | Notes |
|---|---|---|
| (none) | Classic Wait | **DO NOT AUTHOR by default** (see "Do NOT emit" section above for the rule + narrow exception). Multiple resume conditions (branches), supports platform events and time events; includes a default path and a fault path |
| `WaitDuration` | Duration | Single branch; offset 1-365 in minutes, hours, days, weeks, or months; no fault connector |
| `WaitDate` | Specific Date | Single branch; absolute date + time; no fault connector |
| `WaitAttribute` | Attribute (internal) | **DO NOT AUTHOR** — internal/platform-only, no palette tile (like classic Wait). Documented for reading existing flows. Pauses until `$Record.LastModifiedDate`; simplified; no fault connector |
| `WaitUntilEvent` | Wait Until Event | Exactly two branches: one "Event Received" path and one "Timeout" path; no fault connector |

**`elementSubtype` takes exactly these values: `WaitDuration`, `WaitDate`, `WaitAttribute`, `WaitUntilEvent`.** Never write an upper-case form such as `WAIT_DURATION`, `WAIT_DATE` or `WAIT_UNTIL_EVENT`: the org rejects the flow with `Error parsing file: 'WAIT_DURATION' is not a valid value for the enum 'ElementSubtypeEnumProxy'`.

Simplified subtypes (`WaitDuration`, `WaitDate`, `WaitAttribute`, `WaitUntilEvent`) do NOT have a fault connector or a *configurable* default connector in the UI.

**But `defaultConnectorLabel` is still REQUIRED on the metadata for simplified subtypes.** Even though the UI exposes no default-connector option for them, the server rejects the save with `Required field is missing: defaultConnectorLabel` if the field is absent. Always emit `"defaultConnectorLabel": "Default"` on every `WaitDuration` / `WaitDate` / `WaitUntilEvent` element. This is a metadata-only requirement; you still do not emit a `defaultConnector` for these subtypes.

## Required Properties

| Property | Description | Constraints |
|---|---|---|
| Label | Display name for the Wait element | Required; any text |
| API Name | Developer name used in formulas and Apex | Required; alphanumeric + underscores; must be unique in the flow |
| Resume condition (at least one) | At least one wait event must be defined | Required unless using a simplified subtype that auto-creates its events |

## Optional Properties

| Property | Description | Default |
|---|---|---|
| Description | Internal notes about the element | Empty |
| Default Path label | Label for the default connector (classic Wait only) | "All Other Conditions" |
| Time Zone | Time zone for absolute-time resume conditions (inherited from the Start element's time zone) | Inherited from Start element |
| Max Batch Size (org perm required) | Maximum number of interviews to resume in a single batch | None (org default applies) |

## Resume Condition Types

### Absolute Time (`AlarmEvent`) — the default for "resume at a datetime"

Resumes at a specific date and time, optionally offset from a base time. **This is the correct event type whenever you already have a datetime value** — a flow variable, a formula, a literal, or a single `$Record` **DateTime** field (e.g. `$Record.SLA_Deadline__c`). The bound field/resource must be `DateTime`, not `Date`: `AlarmTime` requires a datetime, so a Date-only field like `Opportunity.CloseDate` is rejected. To resume relative to a Date-only field, use the `WaitDate` pattern instead (see below).

- The base datetime is bound through a **single `AlarmTime` inputParameter** whose value is an `elementReference` (or a datetime literal) — NOT a set of separate SObject / RecordId / Date-field fields. Do not split it into `TimeField` + `SObject` + `RecordId`; that is the `DateRefAlarmEvent` shape and the server rejects it on an `AlarmEvent` wait event.
- **Offset Number**: Integer; how many units before or after the base time. Offset unit must be `Hours` or `Days` only (not weeks or months).
- **Offset Unit**: `Hours` or `Days`. Blank means "exactly at the base time".
- If no offset is specified the flow resumes exactly at the base datetime value.

Worked example: `examples/alarmEvent-absolute-time.json` — a single `AlarmEvent` wait event binding the base datetime through one `AlarmTime` inputParameter (elementReference to a DateTime field, `$Record.SLA_Deadline__c`), no split TimeField/SObject/RecordId.

### Direct Record Time (`DateRefAlarmEvent`) — only when you must resolve a field on a *different* record

Resumes relative to a datetime field on a specific record identified by ID. Use this ONLY when the datetime lives on a record you must look up by ID (not the triggering `$Record`, and not a value you already hold). For a datetime you already have or that sits on `$Record`, use `AlarmEvent` above instead. This is variant 04 ("Wait Until Date–Record"). It is a **classic** Wait event (no `elementSubtype`), so it carries five required `inputParameters` — see the copy-pasteable worked example in the Metadata Shape section below.

- **SObject** (Salesforce Object): Required — `inputParameters` name `TimeTableColumnEnumOrId` (stringValue).
- **Date/Time Field**: Required — `TimeFieldColumnEnumOrId` (stringValue).
- **Record ID**: Required — `EntityObjectId` (elementReference to the record Id).
- **Offset**: `TimeOffset` (numberValue) + `TimeOffsetUnit` (stringValue, Hours or Days).

Omitting `TimeTableColumnEnumOrId` (Object Type) is what makes a classic Wait
draft-save but refuse to activate (`WARNING_BLOCK_ACTIVATION`). Always emit all five.

### Platform Event

Resumes when a specific platform event is received.

- **Event Type**: Required. The API name of the platform event object.
- **Filter conditions**: Optional conditions on event fields to narrow which event instances trigger resumption.
- **Output parameters**: Optional. Captures field values from the received event.

### Duration (`WaitDuration` subtype)

A simplified single-branch wait for a fixed duration.

- **Offset**: Integer between 1 and 365 (inclusive). Required. **Zero is rejected** — a `WaitDuration` event with `offset: 0` saves but blocks activation with `WAITEVENT_INVALID_VALUE`: *"The offset field can't be '0'. Enter a number between 1 and 365."* There is no zero-duration `WaitDuration`.
- **Offset Unit**: `Days`, `Hours`, `Weeks`, `Minutes`, or `Months`. Required. (`Minutes` is valid — e.g. "wait 5 minutes" → `offset: 5, offsetUnit: "Minutes"`. The `FlowScheduledPathOffsetUnit` enum in `metadata/metadata.wsdl` is the source of truth: `Hours`, `Days`, `Minutes`, `Months`, `Weeks`.)
- No time zone, no conditions, no fault path.
- **The outgoing connector goes on the single `waitEvents` entry** (`waitEvents[0].connector`).
  The Wait itself has no `connector` field. In a `.flow-meta.xml`, a `<connector>` directly under
  `<waits>` fails the deploy with `Error parsing file: Element
  {http://soap.sforce.com/2006/04/metadata}connector invalid at this location in type FlowWait`.

#### Resume-at-time-of-day option (`resumeTime` on a `WaitDuration` event)

Set `resumeTime` (an `xsd:time`, e.g. `"12:00:00.000"`) on the wait event to gate resumption to a time of day. Semantics: wait at least `offset` `offsetUnit`, then resume at the next `resumeTime` — "resume at noon" → `offset: 1, offsetUnit: "Days", resumeTime: "12:00:00.000"`, **not** a same-instant next-noon.

- The `offset ≥ 1` rule above **still applies** — you cannot express "the very next noon" with `offset: 0`. The minimum wait is 1 unit; pick the `offsetUnit` that fits the intent (`Days` for a daily noon).
- `resumeTime` uses the flow's time zone (`metadata.timeZoneSidKey`, inherited via the Wait's `timeZoneId`). Emit `timeZoneSidKey` by **trigger type**, not `processType`:
  - **Plain `AutoLaunchedFlow` (no trigger): `timeZoneSidKey` is NOT settable** — the server rejects it with `PROCESSTYPE_ELEMENT_CONFIG_NOT_SUPPORTED`: *"Because this flow has a processType of AutoLaunchedFlow, elements and resources in this flow can't reference the TimeZoneSidKey field."* The time zone is implicit (org/running-user default); omit `metadata.timeZoneSidKey` entirely.
  - **Segment-triggered flow (`processType: AutoLaunchedFlow` with `triggerType: Segment` — see `../start/segment-triggered.md`): `timeZoneSidKey` is REQUIRED.** Omitting it blocks activation with `INVALID_TIME_ZONE`: *"You must specify a value for the timeZoneSidKey parameter with the Segment flow trigger type."* When the user hasn't named a timezone, do NOT ask — set it to the **org default** (e.g. `America/Los_Angeles` on SDB105; confirm by reading an existing active flow in the org).
  - A record-triggered flow *can* also carry it.
  - Net: the same `resumeTime: "12:00:00.000"` ("noon") payload is correct in all cases; only whether you emit `timeZoneSidKey` alongside it changes with trigger type.
- `resumeDate` is NOT set on a `WaitDuration` event — an absolute calendar date is the `WaitDate` subtype instead.

### Specific Date (`WaitDate` subtype)

A simplified single-branch wait until a date. The resume date is supplied one of **two mutually exclusive ways** — an explicit literal date, or a reference to a date field ("Get from Attribute"):

- **Explicit date** — set `resumeDate` (ISO date only, e.g. `"2027-05-28"`) **and** `resumeTime` (an `xsd:time` **string**, e.g. `"00:00:00.000"`). Both are required in this mode.
- **Date attribute reference** (FEROV) — set `resumeDateReference` to any FEROV that resolves to a **Date** field. When set, `resumeDateReference` **supersedes** `resumeDate`/`resumeTime`, and **`resumeTime` is optional — omit it** (the "Date value required" validator is satisfied by the reference alone). This is the "Get from Attribute" option in the Wait Until Date editor.
  - The reference is **not restricted to a direct `$Record.<field>`.** Any FEROV that lands on a Date field is accepted, including a **traversed lookup** — e.g. in an audience/List-triggered flow the member's source-record fields are reached through `$Input.ReferenceRecord.<field>`, so `resumeDateReference: "$Input.ReferenceRecord.Birthdate"` is valid (LookupTraversal must be an available `flowFeature`). Confirm the referenced field is `dataType: "Date"` via `list_fields_for_entity` — a non-Date field trips the "Invalid date field" activation error.
- **Offset** (optional) — `offset` (integer) + `offsetUnit` shift the resume relative to the resolved date. **For the `WaitDate` subtype the offset unit is NOT limited to Hours/Days** — `Days` and `Weeks` are both confirmed accepted on save (e.g. "32 weeks after the contact's birthdate" → `resumeDateReference: "$Input.ReferenceRecord.Birthdate"`, `offset: 32`, `offsetUnit: "Weeks"`, no `resumeTime`). Do **not** convert weeks to days to satisfy an Hours/Days rule — that restriction (validators.md "Offset unit must be Hours or Days") applies to the **classic** `AlarmEvent`/`DateRefAlarmEvent` event offsets, not to this simplified subtype.

**On SAVE, `resumeTime` must be a JSON time string and `resumeDate` a `"YYYY-MM-DD"` date string — NOT the server's read-back forms.** When you *retrieve* an existing flow, the server hands these back in read-back shape: `resumeTime` as a `{ "timeInMillis": N }` object (e.g. `{ "timeInMillis": 43200000 }`) and `resumeDate` as a bare **epoch-millis integer** (e.g. `1811462400000`) — the *same* shape as the Start element's `schedule.startDate`/`schedule.endDate`, since `resumeDate` and the schedule dates are the identical `xsd:date` type. That is the **read-back form only**. Echoing `resumeTime`'s object straight back on save is rejected (observed: `No suitable constructor found for type [...] com.sforce.ws.types.Time: can not instantiate from JSON object`); echoing `resumeDate`'s integer is likewise rejected. Convert first: `{timeInMillis:43200000}` → `"12:00:00.000"`, `{timeInMillis:0}` → `"00:00:00.000"`, and the epoch-millis `resumeDate` → its **UTC** date-only string via `floor(epochMillis / 86400000)` (`1811462400000` → `"2027-05-28"`) — never local-time formatting, which can silently land a day early. This is the same failure class as the Start element's Scheduled-trigger `schedule.startTime`/`schedule.endTime`/`schedule.startDate`/`schedule.endDate` (`../start/start.md`) — see the canonical writeup, full field list, and date-math in `shared/anti-patterns.md` item 39.

### Wait Until Event (`WaitUntilEvent` subtype)

Pauses until a customer engagement event occurs, with a required timeout path.

> **Always use this subtype for engagement/automation events — never a classic Wait.** To wait on an email event (open/link-click/bounce), an SMS event (response/link-click/delivery-failure), or a Journey Builder contact event (entered/exited/met-goal), the element MUST have `elementSubtype: "WaitUntilEvent"`. Do NOT approximate it with a classic Wait whose timeout branch is an `AlarmEvent`/`DateRefAlarmEvent` — engagement events are not platform events, carry no `eventType`, and cannot be bound on a classic wait event, so such a flow never resumes on the engagement. If you find yourself reaching for `AlarmEvent` to satisfy an "event" request, stop and switch to `WaitUntilEvent`.

> **Adding this subtype to an *existing* flow is a breaking change — Stop-and-Ask first.** Hosting a WaitUntilEvent forces the start trigger to `IndivRelatedRecord`/`Segment` (see `../start/start.md`), so retrofitting one onto a trigger-less flow silently breaks its current Apex/API/subflow invokers. Confirm the trigger change with the user; never rewrite the start element on your own.

**Always has exactly two branches:**
1. **Event Received path** – fires when the engagement event occurs.
2. **Timeout path** – fires if the event does not occur within the specified window.

**Timeout path configuration:**
- **Offset**: Integer between 1 and 365. Required.
- **Offset Unit**: `Days`, `Hours`, or `Weeks`. Required.

**Event types supported on the Event Received path (requires `WaitForAutomationEvents` org permission):**

The event is bound via **two paired fields** on the WaitUntilEvent `waitEvent`: `automationEventType` (the event's type) and `automationEventName` (its qualified name). Two distinct layers govern which values are legal, and they do **not** agree — know which one applies:

1. **Save-validation layer (the type enum).** `automationEventType` must be a member of the `InvocableActionType` enum — the authoritative list is the `InvocableActionType` simpleType in `metadata/metadata.wsdl` / `designerApi.wsdl` (the `trgrOn*` members). A value not in that enum fails on save with `not one of the declared Enum instance names`. This enum is a **superset** and includes email-response, all three WhatsApp events, and RCS response:

   | Event | `automationEventType` value |
   |---|---|
   | Email opened | `trgrOnEmailOpenEngagement` |
   | Email link clicked | `trgrOnEmailLinkClickEngagement` |
   | Email bounced | `trgrOnEmailBounceEngagement` |
   | Email response (reply) | `trgrOnEmailResponseEngagement` |
   | SMS link clicked | `trgrOnSmsLinkClickEngagement` |
   | SMS delivery failure | `trgrOnSmsDeliveryFailureEngagement` |
   | SMS response | `trgrOnSmsResponseEngagement` |
   | WhatsApp link clicked | `trgrOnWhatsAppLinkClickEngmt` |
   | WhatsApp delivery failure | `trgrOnWhatsAppDlvrFailureEngmt` |
   | WhatsApp response | `trgrOnWhatsAppResponseEngmt` |
   | RCS response | `trgrOnRcsResponseEngagement` |

2. **Runtime-availability layer (the org's provisioned Event Library).** An `automationEventType` that passes the enum check still resumes only if the **org has that event provisioned**. The Event Library actually offered by an org is a subset of the enum, discovered at runtime — do **not** assume the full enum is available. Query the org's actual subset with **`GET /services/data/vXX.0/flowbuilder/action/invocable-events`**. Call it with **`processType: "AutoLaunchedFlow"` and `triggerType: "Segment"`** (the Connect OAS param names — NOT `flowProcessType`/`flowTriggerType`). Read rows from `invocableActions[]`; each descriptor's `type` is the value for `automationEventType`. Do NOT copy the descriptor's bare `name` into `automationEventName` — build it from the type per the table below (`default__` + `automationEventType`, except SMS Response). The response also carries `pagination.totalSize` and `pagination.hasMore` when an explicit `limit` truncates the list. A 403 means the caller cannot view Flow or Journey Builder; an absent SMS event means the org or user lacks that event's provisioning or permission.

   > **Discovery vs. start trigger — keep these distinct.** The tool's `triggerType` here selects only *which catalog the tool returns*; it is NOT the flow's own trigger. For **event discovery**, use `Segment` (or omit `triggerType`) to get the engagement-only list — not `IndivRelatedRecord`, which returns the same events plus ~130 unrelated SObject entities that are not valid Wait Until Event sources. Separately, the flow you author still needs `triggerType: IndivRelatedRecord` (or `Segment`) as its **start** trigger to host the WaitUntilEvent element — see `../start/start.md`. The provisioned set is org-dependent; the table below is one org's baseline, not the enum.

| UI label | `automationEventType` | `automationEventName` |
|---|---|---|
| Email Open | `trgrOnEmailOpenEngagement` | `default__trgrOnEmailOpenEngagement` |
| Email Link Click | `trgrOnEmailLinkClickEngagement` | `default__trgrOnEmailLinkClickEngagement` |
| Email Bounce | `trgrOnEmailBounceEngagement` | `default__trgrOnEmailBounceEngagement` |
| SMS Response | `trgrOnSmsResponseEngagement` | `trgrOnSmsResponseEngagement` |
| SMS Link Click | `trgrOnSmsLinkClickEngagement` | `default__trgrOnSmsLinkClickEngagement` |
| SMS Delivery Failure | `trgrOnSmsDeliveryFailureEngagement` | `default__trgrOnSmsDeliveryFailureEngagement` |
| Journey Builder Contact Entered | `enteredJourneyBuilder` | `default__enteredJourneyBuilder` |
| Journey Builder Contact Exited | `exitedJourneyBuilder` | `default__exitedJourneyBuilder` |
| Journey Builder Contact Met Goal | `metJourneyBuilderGoal` | `default__metJourneyBuilderGoal` |

- `automationEventName` is `default__` + `automationEventType`, **except SMS Response**, whose name equals its type with no `default__` prefix.
- The engagement id does NOT go in `eventType` (that field is for classic platform-event waits). Do not emit the old `…InvocableEvent` PascalCase constants — they are not valid enum values.
- **Do not promise SMS reply data.** Core 264 describes `trgrOnSmsResponseEngagement` with no output parameters, and its event-field resolver currently returns no fields. Emit `outputParameters: []`. Use the event only to resume a branch when a response arrives.

**Input parameters for Wait Until Event:**
- The Journey Builder events take an `mceJourneyInput` input parameter whose `stringValue` is the target MCE Journey's id.
- The **messaging engagement and response events** — every email, SMS, WhatsApp, and RCS event (open, link-click, bounce, delivery-failure, and response) — **require an `associatedContent` input parameter**. It is a required STRING input; a missing or empty value blocks activation with `Required parameter 'associatedContent' is missing or empty`. `automationEventType`/`automationEventName` alone are NOT sufficient for these events. (The three Journey Builder events do NOT require `associatedContent`.)
  - **`associatedContent` must reference the upstream send/message action element in the same flow** — the actionCall that sent the email/SMS/WhatsApp/RCS you are waiting on (e.g. `Send_Marketing_Email`, `Send_SMS_Message`). Bind it by `elementReference` to that action element, NOT to a String variable holding a content/template id: `"inputParameters": [{ "name": "associatedContent", "value": { "elementReference": "Send_SMS_Message" } }]`. The wait monitors engagements *against that specific send*, so the reference must resolve to the send-action element — which is why the flow must FIRST contain the send step and the wait must come after it. (A raw content-id String may satisfy the not-empty activation gate, but it does not correctly bind the wait to the send being monitored and is wrong.)
  - **This is the Wait Until Event shape only.** An event-triggered **exit rule** on the same event takes the email's ManagedContent Id (`20Y…`) as a `stringValue` instead; an element reference fails activation there (`../exit-rule/exit-rule.md` § Event-Triggered Variant).
- The **link-click events** (`trgrOnEmailLinkClickEngagement`, `trgrOnSmsLinkClickEngagement`, `trgrOnWhatsAppLinkClickEngmt`) require a **second** STRING input, **`specificLink`** — the link to monitor — *in addition to* `associatedContent`. Omitting it saves fine but blocks activation with `ACTIONCALL_MISSING_REQUIRED_PARAM` ("Enter a value for the specificLink input parameter"). Two ways to set it:
  - **Any link** → the literal sentinel `{ "stringValue": "ANY" }`. This is the "Any Link" option (source: `messagingEventEditor.ts` `const ANY_LINK = { value: 'ANY' }`). Prefer it whenever the email's links are **dynamic or contain merge fields** — Salesforce docs state specific-link matching is unsupported for those.
  - **A specific link** → the exact link URL/value as it appears in the content, `{ "stringValue": "<link>" }`.
  - **Do not try to enumerate the links headlessly.** `GET /services/data/vXX.0/flowbuilder/action/invocable-action-parameter-enum-values` returns `{ "parameters": [] }` for `specificLink` outside the live builder (the picklist is resolved from the content's tracked links at runtime). Use `dispatch_readonly(method: "GET", url: "/services/data/vXX.0/flowbuilder/action/invocable-action-details", queryParams: { actionType, actionName })` to confirm the required params, then bind `"ANY"` (or a known URL) directly.

**Output parameters for Wait Until Event:**
- Call `dispatch_readonly(method: "GET", url: "/services/data/vXX.0/flowbuilder/action/invocable-action-details")` with the selected event descriptor's `type` as `actionType` and `name` as `actionName`, then read its outputs before emitting any mapping. For the SMS Response event in Core 264, emit `outputParameters: []`; no reply-text output is declared.
- If the user asks to capture SMS reply text, explain that this event can branch on receipt but the current Flow event contract does not expose the text. Do not invent an output name or variable mapping.

## Validation Rules and Constraints

- **A Wait element must define at least one wait event** — an empty Wait element (classic type with no resume conditions) is an activation error.
- **Each wait event must specify its event type** — a wait event with a blank or missing event type is an activation error.
- **Relative date/time wait events** must reference a valid Date or DateTime field on a valid SObject. The offset value must be between 1 and 365 (inclusive).
- **Resume date must not be in the past** at the time of evaluation — the server emits a warning (not a hard error) when a scheduled resume time has already passed.
- The wait element's API name must be unique among all element names and wait event names in the same flow.
- Wait event API names are also validated for uniqueness against each other and the parent wait element.
- `defaultConnectorLabel` must not be blank — required on **both** classic Wait and every simplified subtype (`WaitDuration`/`WaitDate`/`WaitUntilEvent`); a missing label fails the save with `Required field is missing: defaultConnectorLabel`.
- Duration subtype: offset must be a number between 1 and 365 (inclusive). Offset unit must not be blank.
- Date subtype: `resumeDate` must be a valid date; `resumeTime` must be provided.
- Wait Until Event timeout path: offset must be a number between 1 and 365. Offset unit must not be blank.
- **Connect BOTH Wait Until Event branches.** Each of the two wait events (the event branch and the timeout branch) needs its own `connector.targetReference`. A timeout branch with no connector is a silent dead end — the flow reaches the timeout and simply stops, which is almost never intended. Route the timeout branch to a real "no response / gave up" path.
- Wait Until Event on a messaging engagement/response event (email, SMS, WhatsApp, RCS): the `associatedContent` input parameter is **required** — see "Input parameters for Wait Until Event" above for the rule and activation error.
- Wait Until Event on a **link-click** event (email/SMS/WhatsApp link click): the `specificLink` input parameter is **also required** (in addition to `associatedContent`); missing it blocks activation with `ACTIONCALL_MISSING_REQUIRED_PARAM`. Use `{"stringValue":"ANY"}` for "any link". See "Input parameters for Wait Until Event".
- Absolute time: the base time input parameter is required. Offset unit, if provided, must be `Hours` or `Days` (weeks and months are not valid for this event type).
- Direct Record Time: SObject and date/time field are required. Record ID is required.
- Platform event: event type must be non-blank and must resolve to a valid platform event API name.
- Filter conditions: when condition logic is not "No Conditions", all three properties (field, operator, value) of each condition must be filled.
- **DO NOT author `maxBatchSize` on a Wait element or its wait events in an `AutoLaunchedFlow`.** The server rejects the save with `ERROR_BLOCK_SAVE`: *"AutoLaunchedFlow can't have maxBatchSize attributes on the Wait element."* Omit the field entirely. (It is only accepted when the org has the `FlowResumeCustomBatchSize` permission enabled.) When you *retrieve* a saved WaitUntilEvent flow the server may hand `maxBatchSize` back on the wait events as a read-back artifact (often `0`) — that is the read-back form only; **do not echo it back on save**, or the save fails. This mirrors the `resumeTime`/`resumeDate` object round-trip caveat above.
- Time zone is nulled out automatically for `WaitUntilEvent` subtypes — those use a different timing mechanism.
- The time zone is inherited from the Start element's `timeZoneSidKey` if not explicitly set on the Wait element.
- Offset values entered with locale-specific decimal separators (e.g., French "2,0") are normalized to integers automatically.
- **Zero-duration offset as a transaction boundary — NOT a `WaitDuration`.** This applies to the Start element's *scheduled path* `offsetNumber` (a `FlowScheduledPath` field), NOT to a Wait event's `offset`. A scheduled path with `offsetNumber = 0` acts as a transaction boundary in autolaunched flows, committing open DML and resetting governor limits between iterations (the autolaunched-flow equivalent of the CommitTransaction Local Action in screen flows). It carries a performance cost due to async re-entry — only use it when governor limits are actually being hit, not as a default pattern. Do NOT confuse this with a `WaitDuration` event: **a `WaitDuration` `offset` of `0` is rejected** and blocks activation (`WAITEVENT_INVALID_VALUE`) — see the Duration subtype section above (offset must be 1–365). There is no zero-duration `WaitDuration`.

## Common Patterns

**Timed delay in a record-triggered flow**: Use `WaitDuration` (e.g., 3 days) after an update to send a follow-up notification without building date math.

**Pause until a future date stored on a record**: Use `WaitDate` with `resumeDateReference` pointing to any Date-typed FEROV — a field on `$Record` (e.g., `$Record.CloseDate`) or a traversed lookup (e.g., `$Input.ReferenceRecord.Birthdate`). `resumeTime` is optional here (omit it unless explicitly required); add an optional `offset`/`offsetUnit` (`Minutes`, `Hours`, `Days`, `Weeks`, or `Months`) to resume a fixed span after that date — e.g., `offset: 4, offsetUnit: "Hours"` for "4 hours after". A negative offset indicates an offset in the past.

**Email engagement tracking**: Use `WaitUntilEvent` with an email click or open event type. Connect the Event Received path to the success branch and the Timeout path to a "no response" branch.

**Multiple resume conditions in classic Wait**: Each wait event becomes a separate output branch. Add conditions to narrow which event instance triggers each branch (e.g., wait for platform event where `Order__c = {!recordId}`).

**Chaining waits**: Connect the output of one Wait element to another Wait element to create a multi-step timed sequence.

## Aura/Server Functions

- `getIsPauseSupported` — checks whether the Pause/Wait element is available for the current flow process type and trigger type
- `getFlowEntries` — retrieves available flow type entries (used to determine if Wait is applicable for the current context)

---

## Metadata Shape

### Top-Level Wait Fields

| Key | Type | Required | Notes |
|---|---|---|---|
| `name` | string | yes | dev-name |
| `label` | string | yes | display label |
| `defaultConnectorLabel` | string | yes | label for the "no event matched" / timeout branch. **Required on ALL waits incl. simplified subtypes** — emit `"Default"` even on `WaitDuration`/`WaitDate`/`WaitUntilEvent` or the save is rejected (`Required field is missing: defaultConnectorLabel`). |
| `defaultConnector` | Connector | classic only | the no-event-matched outgoing path on classic Wait — do NOT emit for simplified subtypes. For `WaitUntilEvent` the timeout path is a `waitEvents` entry, not a default connector |
| `faultConnector` | Connector | classic only | waits can throw at runtime; classic Wait only — NOT present on any simplified subtype, including `WaitUntilEvent` |
| `waitEvents` | array | yes | one per resumption condition; for `WaitUntilEvent` there are exactly two (the event branch and the timeout branch) |
| `timeZoneId` | string | no | nullable; inherited from Start element if not set. Nulled out for `WaitUntilEvent` |
| `elementSubtype` | string | conditional | `WaitDuration`, `WaitDate`, `WaitAttribute`, or `WaitUntilEvent` |

Note: there is **no top-level `connector`** on Wait — every resumption path is via `waitEvents[i].connector`.

### waitEvents Structure

Each entry in `waitEvents[]`:

| Key | Type | Required | Notes |
|---|---|---|---|
| `name` | string | yes | unique within the wait element |
| `label` | string | yes | |
| `connector` | Connector | yes | where this resumption path leads |
| `conditions` | array | yes | `Condition[]`; `[]` when `conditionLogic === "no_conditions"` |
| `conditionLogic` | string | conditional | omitted (not `"no_conditions"`) when no conditions |
| `eventType` | string | conditional | classic wait events only (platform-event API name). NOT used by `WaitUntilEvent` — that binds via `automationEventType`/`automationEventName` instead |
| `automationEventType` / `automationEventName` | string | conditional | `WaitUntilEvent` event branch only; see event table above |
| `offset` / `offsetUnit` | number / string | conditional | on simplified-subtype branches (`WaitUntilEvent` timeout branch: 1–365 + `Days`/`Hours`/`Weeks`; event branch `offset: 0`) |
| `inputParameters` | array | conditional | Use the selected invocable event's live contract. Messaging events require `associatedContent`; Journey Builder events require `mceJourneyInput`. |
| `outputParameters` | array | conditional | captures event payload field values on resumption |

### Subtype-Specific Extras

| `elementSubtype` | Extra Event Fields | Notes |
|---|---|---|
| `WaitDuration` | `offset`, `offsetUnit` (`Minutes`/`Hours`/`Days`/`Weeks`/`Months`) | `inputParameters` and `outputParameters` forced to `[]` |
| `WaitDate` | Either `resumeDate` + `resumeTime` (literal) **or** `resumeDateReference` (FEROV to a Date field; `resumeTime` optional and normally omitted with it — any Date-typed reference incl. a traversed lookup like `$Input.ReferenceRecord.Birthdate`). Optional `offset` + `offsetUnit` (`Minutes`/`Hours`/`Days`/`Weeks`/`Months` confirmed accepted — **not** limited to Hours/Days). | `inputParameters` and `outputParameters` forced to `[]` |
| `WaitAttribute` | `resumeDateReference` (e.g., `"$Record.LastModifiedDate"`) | `inputParameters` and `outputParameters` forced to `[]` |
| `WaitUntilEvent` | Two `waitEvents`. **Event branch:** `automationEventType`, `automationEventName` (see event table above), `offset: 0`, and — **Journey Builder contact events only** — `recordTriggerType` (`"Create"`/`"Update"`/…). `recordTriggerType` is NOT required for messaging engagement events; omitting it on an Email Link Click event saved clean with no warnings. **Timeout branch:** `offset` (1–365), `offsetUnit` (`Days`/`Hours`/`Weeks`), and NO event fields. | Event branch uses normal `inputParameters`: `mceJourneyInput` for Journey Builder events; `associatedContent` for messaging events, **plus `specificLink` for the link-click events** (`{"stringValue":"ANY"}` for any link — see "Input parameters" above). Emit `outputParameters: []` for SMS Response because Core 264 declares no event outputs. Timeout branch has empty `inputParameters`/`outputParameters`. |

For the non-`WaitUntilEvent` simplified subtypes (`WaitDuration`, `WaitDate`, `WaitAttribute`), `inputParameters` and `outputParameters` must be emitted as `[]`.

**WaitUntilEvent two-branch example:** `examples/waitUntilEvent-two-branch.json` — a real configured flow whose event branch waits on Journey Builder Contact Entered and whose timeout branch uses a 1-week offset. It applies the subtype-table and validation rules above (two connected branches, `elementSubtype`/`defaultConnectorLabel`, no `maxBatchSize`); use the JSON as the shape anchor.

### conditionLogic Sentinel Rule

When condition logic is "No Conditions": emit `conditions: []` and **omit** `conditionLogic` entirely. Never pass `"no_conditions"` to the server.

### Required-on-Save Rules

- Classic Wait only: `defaultConnector.targetReference` and `faultConnector.targetReference` must resolve.
- Per event: `connector.targetReference` must resolve.
- `defaultConnectorLabel` must not be blank — on classic Wait **and** every simplified subtype incl. `WaitUntilEvent` (see Required Properties above).
- At least one `waitEvents` entry is required (empty Wait is an activation error). `WaitUntilEvent` requires exactly two (event + timeout).
- Wait Until Event on a messaging engagement/response event (email, SMS, WhatsApp, RCS): `associatedContent` input parameter is required (see the Wait Until Event section).

### Save-Time Rejections

- `Element type Wait is not allowed in trigger type RecordBeforeSave`
- `WaitEvent '<name>' has no connector`
- `Event type '<eventType>' not found`
- `Error parsing file: '<VALUE>' is not a valid value for the enum 'ElementSubtypeEnumProxy'` → an upper-case `elementSubtype` such as `WAIT_DURATION`; write `WaitDuration` / `WaitDate` / `WaitUntilEvent`

### Fault Connector Mandate

Waits can throw at runtime. Always emit a `faultConnector`. (Simplified subtypes like `WaitDuration`, `WaitDate`, `WaitAttribute`, and `WaitUntilEvent` do NOT have a fault connector — only the classic multi-event Wait does.) **Marketing flows are the exception:** in a marketing flow, emit a classic Wait's `faultConnector` only if the user asks for error handling (the marketing trigger types are listed in `shared/fault-paths/fault-paths.md` § Marketing Flows — Fault Paths Only When Asked).

---

## Classic Wait Events REQUIRE `inputParameters` (activation gate)

> **Classic Wait is default-prohibited** — author it only in the narrow
> exception (multi-branch "by Criteria" or record-relative `DateRefAlarmEvent`),
> per the "Do NOT emit the base (classic) `Wait`" section near the top. The shapes
> below apply when reading an existing classic Wait OR building that exception:
> emit every required `inputParameter` or the flow saves but never activates.
>
> **This is the #1 cause of a classic Wait saving but refusing to activate.**

A classic (no-subtype) time-based `waitEvent` is NOT complete just because it has a
`connector` and an `eventType`. Each time-based event carries **required `inputParameters`**,
and if you omit them the flow **draft-saves fine but throws one `WARNING_BLOCK_ACTIVATION`
per branch** — `"Enter a value for the Object Type input parameter"` — so it can never
activate. Emitting the full `inputParameters` block below is what makes a classic Wait
*activatable*, not just *saveable*.

Fetch the authoritative parameter list for a classic platform event with
`dispatch_readonly(method: "GET", url: "/services/data/vXX.0/flowbuilder/platform/event-types/<EventApiName>/parameters")`. Discover its API name
with `dispatch_readonly(method: "GET", url: "/services/data/vXX.0/flowbuilder/platform/event-types", queryParams: { eventType: "Runtime" })`; if its category is unknown, repeat
the discovery call with `eventType: "Setup"` and `eventType: "ManagedSetup"`. The two
common time-based shapes are fixed and given below verbatim. Do NOT loop on reads/greps —
construct the payload directly from these.

### `DateRefAlarmEvent` — resume relative to a date field on a record (variant 04, "Date–Record")

Five `inputParameters`, all required. This exact shape is confirmed against active core
metadata (`LsFinclAsst/CheckAppealStsAndTkActn`):

| `name` | value kind | Meaning | Example |
|---|---|---|---|
| `TimeTableColumnEnumOrId` | `stringValue` | **Object Type** — the SObject API name whose record supplies the base date. *(This is the parameter whose absence produces the activation warning.)* | `"Case"` |
| `TimeFieldColumnEnumOrId` | `stringValue` | **Time Field** — the Date/DateTime field on that object | `"ClosedDate"` |
| `EntityObjectId` | `elementReference` | **Record Id** — a reference to the Id of the specific record | `"Get_Case.Id"` |
| `TimeOffset` | `numberValue` | Offset amount (may be `0`; negative = before the base date) | `30` |
| `TimeOffsetUnit` | `stringValue` | `Days` or `Hours` | `"Days"` |

Copy-pasteable single-branch classic Wait (Date–Record):

```json
{
  "name": "Wait_Until_30_Days_After_Close",
  "label": "Wait Until 30 Days After Close",
  "locationX": 350,
  "locationY": 400,
  "defaultConnectorLabel": "Other (Default)",
  "defaultConnector": { "targetReference": "End_No_Event" },
  "faultConnector": { "targetReference": "Handle_Fault" },
  "waitEvents": [
    {
      "name": "Resume_After_Close",
      "label": "Resume After Close",
      "conditionLogic": "and",
      "conditions": [],
      "connector": { "targetReference": "Send_Followup" },
      "eventType": "DateRefAlarmEvent",
      "inputParameters": [
        { "name": "TimeTableColumnEnumOrId", "value": { "stringValue": "Case" } },
        { "name": "TimeFieldColumnEnumOrId", "value": { "stringValue": "ClosedDate" } },
        { "name": "EntityObjectId", "value": { "elementReference": "Get_Case.Id" } },
        { "name": "TimeOffset", "value": { "numberValue": 30 } },
        { "name": "TimeOffsetUnit", "value": { "stringValue": "Days" } }
      ],
      "outputParameters": []
    }
  ]
}
```

### `AlarmEvent` — resume at a base datetime value (absolute time)

One required `inputParameter`. The base time comes from `AlarmTime`; the optional
`TimeOffset`/`TimeOffsetUnit` (Hours/Days only) shift it.

| `name` | value kind | Meaning |
|---|---|---|
| `AlarmTime` | `elementReference` | base datetime (a DateTime field or variable), e.g. `"Get_Case.ClosedDate"` |
| `TimeOffset` | `numberValue` | optional offset amount |
| `TimeOffsetUnit` | `stringValue` | optional; `Hours` or `Days` only |

### Multi-branch classic Wait "by Criteria" (variant 01)

The "Criteria" variant is a classic Wait with **two or more `waitEvents`**, each with its own
`conditionLogic` + `conditions` (resume conditions), `eventType`, and the same required
`inputParameters` as above. Every time-based branch still needs its `inputParameters` block —
missing the Object Type on any branch blocks activation for the whole flow.

```json
{
  "name": "Wait_For_Case_Milestones",
  "label": "Wait For Case Milestones",
  "locationX": 350,
  "locationY": 400,
  "defaultConnectorLabel": "All Other Conditions",
  "defaultConnector": { "targetReference": "End_No_Event" },
  "faultConnector": { "targetReference": "Handle_Fault" },
  "waitEvents": [
    {
      "name": "One_Day_Before_Close",
      "label": "1 Day Before Close",
      "conditionLogic": "and",
      "conditions": [
        {
          "leftValueReference": "Get_Case.Status",
          "operator": "EqualTo",
          "rightValue": { "stringValue": "Escalated" }
        }
      ],
      "connector": { "targetReference": "Send_Reminder" },
      "eventType": "DateRefAlarmEvent",
      "inputParameters": [
        { "name": "TimeTableColumnEnumOrId", "value": { "stringValue": "Case" } },
        { "name": "TimeFieldColumnEnumOrId", "value": { "stringValue": "ClosedDate" } },
        { "name": "EntityObjectId", "value": { "elementReference": "Get_Case.Id" } },
        { "name": "TimeOffset", "value": { "numberValue": -1 } },
        { "name": "TimeOffsetUnit", "value": { "stringValue": "Days" } }
      ],
      "outputParameters": []
    },
    {
      "name": "One_Day_After_Close",
      "label": "1 Day After Close",
      "conditionLogic": "and",
      "conditions": [],
      "connector": { "targetReference": "Send_Survey" },
      "eventType": "DateRefAlarmEvent",
      "inputParameters": [
        { "name": "TimeTableColumnEnumOrId", "value": { "stringValue": "Case" } },
        { "name": "TimeFieldColumnEnumOrId", "value": { "stringValue": "ClosedDate" } },
        { "name": "EntityObjectId", "value": { "elementReference": "Get_Case.Id" } },
        { "name": "TimeOffset", "value": { "numberValue": 1 } },
        { "name": "TimeOffsetUnit", "value": { "stringValue": "Days" } }
      ],
      "outputParameters": []
    }
  ]
}
```

Notes that keep a classic Wait activatable:
- **Every time-based branch needs its full `inputParameters` block** (esp. `TimeTableColumnEnumOrId`). This is the fix for the `WARNING_BLOCK_ACTIVATION` regression.
- `defaultConnectorLabel` must be non-blank; both `defaultConnector` and `faultConnector` targets must resolve.
- Branches with no resume condition emit `conditions: []` and keep `conditionLogic: "and"` (or omit `conditionLogic` — never send `"no_conditions"`).
- `outputParameters: []` unless you are capturing event payload fields.
- A Wait is async-only: use an **Autolaunched** (or record-triggered) flow, never a screen flow or a `RecordBeforeSave` trigger.
