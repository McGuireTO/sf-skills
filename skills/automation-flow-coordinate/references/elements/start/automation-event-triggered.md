---
name: flow-element-start-automation-event-triggered
license: LICENSE.txt has complete terms
description: "Load when building an Automation Event-triggered flow — triggerType `AutomationEvent`, processType `AutoLaunchedFlow` — that FIRES when an email-engagement event occurs (email open, link click, bounce, or response). Covers discovering the event at runtime (`GET /services/data/vXX.0/flowbuilder/action/invocable-events` + describe), the start-element shape (`eventName`/`eventType`), the inputs that make the flow activatable, and the hard line between an event-TRIGGERED flow (this) vs a flow that WAITS mid-flow on an engagement event (IndivRelatedRecord + WaitUntilEvent) vs a PlatformEvent flow. NOT for Marketing form submission — Flow Builder lists Form Submission under Automation Event, but it is triggerType `FormSubmissionEvent` (load `form-submission-triggered.md`). DO NOT load for any other trigger type."
metadata:
  version: "1.0"
  related-skills: flow-element-start, flow-flow-properties
---

# Automation Event-Triggered (OOTB Email-Engagement Flow)

Load this when `triggerType` is `AutomationEvent`. It is the complete build guide for the Automation Event start element; the base `start.md` carries only the routing stub.

The whole flow FIRES when an email-engagement event occurs for an individual — an email is opened, a link is clicked, the email bounces, or the recipient responds.

- **triggerType**: `AutomationEvent`. Author **`processType: "AutoLaunchedFlow"`** (headless). Do not substitute `Journey` based on the builder surface name.
- The event is chosen ON the start element via **`eventName` + `eventType`** — NOT `actionName`/`actionType`, which match neither element (a mid-flow Wait Until Event uses its own `automationEventName`/`automationEventType`, and the start uses `eventName`/`eventType` — see the disambiguation below).
- Requires a Marketing/engagement-provisioned org: the Automation Event trigger and its events are license-gated and do not exist on a plain org. If the trigger type or an event is unavailable, STOP and tell the user the org is not provisioned — do NOT fall back to another trigger type.

## Discover the event — don't hard-code it

Automation Events run on the same invocable-action framework as Action Call actions, so you discover them the same way you discover actions: list what the org offers, then describe the one you pick. Treat discovery as the source of truth for the event's trigger string and its inputs; the event-specific notes later in this file cover only the handful of things discovery does NOT tell you.

> **One shared discovery endpoint — read this before using it.** `invocable-events` is the org's single event-discovery endpoint, and its API description is written around the Wait-Until-Event case ("the events a Wait Until Event element can wait on"). It nonetheless enumerates the SAME engagement/automation event catalog that the AutomationEvent **start** trigger fires on — there is no separate start-trigger discovery endpoint. The only difference is how the discovered event is referenced downstream: an AutomationEvent **start** uses the BARE `trgrOn…` value in `eventName`/`eventType` (this guide), whereas a mid-flow Wait Until Event uses the `default__`-prefixed form in `automationEventName`/`automationEventType` (see `../wait/wait.md`). So discover the event here, then put the **bare** value on the start.

1. **List the available events.** Call `dispatch_readonly(method: "GET", url: "/services/data/vXX.0/flowbuilder/action/invocable-events", queryParams: { processType: "AutoLaunchedFlow" })` to enumerate the engagement/automation events the org actually exposes. Read the descriptors from the response `invocableActions[]` — each row's `name` is the event's exact trigger string (its `type` echoes the same value). Match the user's intent (opened / link clicked / bounced / responded) to a row and take its exact `name`. Do NOT guess or hard-code the string — use what discovery returns. (Optional query params to narrow the list: `triggerType`, `builderType`, `dataSpace`, `actionType`, `namePattern`, `limit`.)
2. **Set the trigger identity from it.** Put that exact string in BOTH `eventName` and `eventType` (they always carry the identical value — see Start element shape).
3. **Describe the chosen event to learn its inputs.** Call `dispatch_readonly(method: "GET", url: "/services/data/vXX.0/flowbuilder/action/invocable-action-details", queryParams: { actionType: "<the row's type>", actionName: "<the row's name>" })` for the event. The describe output lists its input parameters and marks which are required (`isRequired`). For the email-engagement events this is where `associatedContent` (and, for link click, `specificLink`) come back as required inputs — read them from describe rather than assuming. See "Fill the required inputs" below for the values these inputs expect.

If `GET /services/data/vXX.0/flowbuilder/action/invocable-events` returns nothing or the intended event is missing, the org is not engagement-provisioned — STOP and tell the user (see the provisioning note above).

> **Form Submission is not built here.** When discovery is scoped to `triggerType: "AutomationEvent"`, it also returns a `trgrOnFormSubmission` row labeled "Form Submission". Never put it in `eventName`/`eventType` — that shape is rejected (invalid event name, `InvalidDraft`). A flow that runs when someone submits a Marketing form is `triggerType: FormSubmissionEvent`; STOP here and load `form-submission-triggered.md`.

## Do NOT confuse with the look-alikes

**Choosing between these is a flow-type classification decision — owned by the
flow-type-resolver reference (`../../shared/flow-type-resolver/flow-type-resolver.md`).**
Fire-on-event vs. run-then-wait is its `taxonomy.json`
fire-on-event-vs-run-then-wait bad pair, and the `AutomationEvent` / `IndivRelatedRecord`
(+ `Segment`) / `PlatformEvent` types are its categories; resolve there, not here. Once the
type is resolved, this is the build detail — **where the event is set** for each:

| Trigger type | Where the event is set |
|---|---|
| `AutomationEvent` start (this guide) — flow FIRES when an email is opened/clicked/bounced/responded-to | `eventName`/`eventType` on the **start** |
| `IndivRelatedRecord` (or `Segment`) + a `WaitUntilEvent` element — flow runs first, then PAUSES until the engagement event (see `start.md` and `../wait/wait.md`) | `automationEventName`/`automationEventType` on the **wait** element |
| `PlatformEvent` start — react to a Platform Event (`__e`) message | `object` = event API name (never `eventName`/`eventType`) |
| `FormSubmissionEvent` start — flow FIRES when someone submits a Marketing form (listed under Automation Event in Flow Builder, but NOT an `AutomationEvent`; see `form-submission-triggered.md`) | `form` = the form's content FQN on the **start** (never `eventName`/`eventType`) |

Do NOT resolve marketer intent to **`AdminAutomationEvent`** — that is a separate admin variant, not the OOTB engagement trigger.

## Start element shape

| Field | Value |
|---|---|
| `triggerType` | `"AutomationEvent"` |
| `eventName` | the event's exact trigger string — from discovery (see above) |
| `eventType` | the SAME trigger string as `eventName` (both fields carry the identical value in every saved Automation Event flow) |
| `processType` (flow root) | `"AutoLaunchedFlow"` |

**Required:** start `inputs[]` (`associatedContent`, plus `specificLink` for link-click) and a flow-level `dataSpace` — see [Fill the required inputs](#fill-the-required-inputs--start-inputs--data-space) below; without them the flow saves but comes back `InvalidDraft`. Optional: entry `conditions`/`conditionLogic` (default: No Conditions). `$Event` is available in the flow body once `eventName`/`eventType` are set.

```json
"start": {
  "locationX": 0, "locationY": 0,
  "triggerType": "AutomationEvent",
  "eventName": "trgrOnEmailOpenEngagement",
  "eventType": "trgrOnEmailOpenEngagement",
  "connector": { "targetReference": "<first element>", "isGoTo": false }
}
```

*Note: the snippet above shows the trigger-identity fields only (the event string is illustrative — use the one `GET /services/data/vXX.0/flowbuilder/action/invocable-events` returns). A valid, activatable flow also needs the start `inputs[]` and flow-level `dataSpace` described under "Fill the required inputs" below.*

## Fill the required inputs — start inputs + data space

An Automation Event start SAVES even when incomplete, but the saved flow comes back **`InvalidDraft`** (cannot be activated) unless it ALSO supplies the fields below. **Saving is not validating** — emit all of these on the first save so the generated flow is activatable, not merely persistable. Discovery (describe) tells you WHICH inputs the event requires; the notes here tell you what VALUES to put in them and add the one field discovery can't surface (`dataSpace`).

| Field | Where | Required for | Value |
|---|---|---|---|
| `associatedContent` | start **input parameter** (STRING) | all email-engagement events | Id of the Managed Content whose engagement is monitored (the email/message content) |
| `specificLink` | start **input parameter** (STRING) | **email link click only** | the link to watch, or `"ANY"` to match any link |
| `dataSpace` | **flow-level** field (NOT a start input, so it does NOT appear in describe) | all email-engagement events | a Data Space developer name that resolves on the org (commonly `"default"`) |

**Populate start `inputs[]` here — the one AutoLaunched exception.** AutomationEvent engagement flows are AutoLaunched, yet they REQUIRE start input parameters; do NOT drop them under the general "no start inputs on AutoLaunched flows" guidance. The shape is the standard start `inputs[]` (`name` + `value`), same as a PlatformEvent start:

```json
"start": {
  "triggerType": "AutomationEvent",
  "eventName": "trgrOnEmailLinkClickEngagement",
  "eventType": "trgrOnEmailLinkClickEngagement",
  "inputs": [
    { "name": "associatedContent", "value": { "stringValue": "<Managed Content Id>" } },
    { "name": "specificLink", "value": { "stringValue": "ANY" } }
  ],
  "connector": { "targetReference": "<first element>", "isGoTo": false }
}
```

The data space is a **flow-root** field, not a start field, and is NOT one of the event's discoverable inputs — set it yourself:

```json
{ "processType": "AutoLaunchedFlow", "dataSpace": "default", "start": { "...": "..." } }
```

- **`associatedContent`** is required for all email-engagement events; its value is a Managed Content record Id that exists on the org.
- **`specificLink`** is required ONLY for the email link-click event; the other events do not take it. Use `"ANY"` to fire on any link.
- **`dataSpace`** must resolve to a Data Space on the target org (`"default"` is the common value). Set it on the first save — omitting it blocks activation with `DATA_SPACE_REQUIRED_FOR_FLOW_TYPE`.
- These require an engagement/content-provisioned org (see the provisioning note above): the Managed Content record and the Data Space must actually exist, or the flow saves as `InvalidDraft` (missing content) or fails to save at all (no Data Space backend).
- **No fault paths unless asked.** An `AutomationEvent` flow is a marketing flow: add a `faultConnector` or error-handling branch only when the user asks for error handling. A bounce event is an engagement trigger, not a request for error handling. See `../../shared/fault-paths/fault-paths.md` § Marketing Flows — Fault Paths Only When Asked.

## Special treatment — what discovery does NOT tell you

Discovery gives you the event's trigger string and its required inputs. These few things it does not surface, so they stay called out here:

- **Version floors (functional prerequisite):** email open / link click / bounce require API version 254+; response requires 260+. If the flow's API version is below the floor for the chosen event, that event is unavailable — describe won't flag this, so check the flow's API version.
- **`associatedContent` value differs by surface:** on an Automation Event *start* (this guide) it is a Managed Content Id passed as a `stringValue` (see the snippet above); on a *mid-flow* Wait Until Event it is an element reference — see `../wait/wait.md`. Do not carry one shape into the other.

For reference, the OOTB core email-engagement events you will typically see returned by `GET /services/data/vXX.0/flowbuilder/action/invocable-events` (discovery is authoritative — always use the exact string it returns):

| User intent | trigger string |
|---|---|
| Email is **opened** | `trgrOnEmailOpenEngagement` |
| A **link** in the email is **clicked** | `trgrOnEmailLinkClickEngagement` (the "Link" variant — not `trgrOnEmailClickEngagement`) |
| Email **bounces** | `trgrOnEmailBounceEngagement` |
| Recipient **responds** to the email | `trgrOnEmailResponseEngagement` |

## Out of scope — MCE email click (STOP and ask)

`trgrOnMceEmailClickEngagement` (Marketing Cloud Engagement email link click) is NOT part of the OOTB core-email flavor. It requires MCE provisioning and pairs only with a `SEND_TO_MCE_EMAIL` send, never the core Send Email. If the user asks for an MCE email-engagement trigger, STOP and confirm the org has MCE provisioning before proceeding — do NOT emit `trgrOnMceEmailClickEngagement` on a core-email flow.
