---
name: flow-element-start-form-submission-triggered
license: LICENSE.txt has complete terms
description: "Load when building a Form-Triggered flow — triggerType `FormSubmissionEvent`, processType `AutoLaunchedFlow` — that FIRES each time someone submits a Marketing form (a Form Builder form stored as Managed Content, `sfdc_cms__form`). Covers discovering the form at runtime (ManagedContent SOQL + the content-FQN endpoint), the start-element shape (`form` = the form's content FQN), reading the submitted answers via `$Form.<field>`, the one-form-per-flow rule, and the HARD PROHIBITION on authoring it as `AutomationEvent` + `trgrOnFormSubmission` (Flow Builder lists Form Submission under Automation Event, but the saved trigger type is `FormSubmissionEvent`). Also the line vs a Screen flow (a form the user steps through). DO NOT load for any other trigger type."
metadata:
  version: "1.0"
  related-skills: flow-element-start, flow-flow-properties
---

# Form-Triggered (Marketing Form Submission)

Load this when `triggerType` is `FormSubmissionEvent`. It is the complete build guide for the form-submission start element; the base `start.md` carries only the routing stub.

The whole flow FIRES, headless, once per submission of a Marketing form. The submitted answers are available in the flow body as `$Form.<field>`.

- **triggerType**: `FormSubmissionEvent`. Author **`processType: "AutoLaunchedFlow"`**.
- The form is chosen ON the start via the **`form`** field — the form's Managed Content FQN. There is no `eventName`/`eventType` and no start `inputs[]` on this trigger.
- Requires a Marketing-provisioned org with at least one Form Builder form. If the trigger type is unavailable or the org has no form, STOP and tell the user — do NOT fall back to another trigger type, and never fabricate a form value.

## HARD PROHIBITION — never `AutomationEvent` + `trgrOnFormSubmission`

Flow Builder lists **Form Submission** inside the **Automation Event** trigger picker, and event discovery scoped to the Automation Event trigger (`GET /services/data/vXX.0/flowbuilder/action/invocable-events` with `triggerType: "AutomationEvent"`) returns a `trgrOnFormSubmission` row labeled "Form Submission". **Do not build on that row.** When a user picks Form Submission in the builder, the builder rewrites the flow to `triggerType: FormSubmissionEvent`; it never saves `AutomationEvent` + `trgrOnFormSubmission`.

If you author that shape anyway, the platform rejects it:

- The event name is invalid (`FLOW_INVALID_EVENT_NAME`, "Invalid event name trgrOnFormSubmission."); on save the server rewrites `eventName` to `"nullNotFound"`.
- The flow saves as **`InvalidDraft`** (cannot be activated).
- `$Form.<field>` references stop resolving (the start is no longer bound to a form).
- The event's describe marks a `Form` input as required, but the validator then rejects that input (`FLOW_START_INPUT_INVALID_INPUT`, "Flows with event type Form Submission don't support the Form field"). The describe for this event is not a reliable guide — use this file instead.

So: a form-submission request is ALWAYS `triggerType: FormSubmissionEvent`, even when the user says "Automation Event" or names the Form Submission event. When they used Automation Event wording, tell them in one line why the saved trigger type is `FormSubmissionEvent`.

## Do NOT confuse with two look-alikes

**Choosing between these is a flow-type classification decision — owned by the
flow-type-resolver reference (`../../shared/flow-type-resolver/flow-type-resolver.md`).** Resolve there, not here. Once the type is resolved, this is where the trigger is set for each:

| Request | Type | Where it is set |
|---|---|---|
| The flow runs AFTER someone submits an existing Marketing form (this guide) | `FormSubmissionEvent` | `form` on the **start** |
| The flow IS the form — a user steps through screens and enters values | Screen Flow (`processType: Flow`, no trigger) | `screens[]` in the flow body |
| The flow fires on an email engagement (open / link click / bounce / response) | `AutomationEvent` — see `automation-event-triggered.md` | `eventName`/`eventType` on the **start** |

A plain record trigger on the object the form writes to (e.g. `RecordAfterSave` on `Lead` create) is also not a substitute: use `FormSubmissionEvent` when the user describes the form submission itself as the starting event.

## Discover the form — don't guess it

1. **List the org's forms.** `dispatch_readonly({ url: "/services/data/vXX.0/query", method: "GET", queryParams: { q: "SELECT Id, Name, ContentKey, AuthoredManagedContentSpaceId FROM ManagedContent WHERE ContentTypeFullyQualifiedName = 'sfdc_cms__form'" } })` → `records[]`, each `{Id (20Y…), Name, ContentKey, AuthoredManagedContentSpaceId}`. Match the form the user named against `Name`; select one exact match automatically, ask the user to choose when several match or the request does not identify one, and STOP when none exist (the user must create the form in Form Builder first).
2. **Resolve its FQN.** `dispatch_readonly({ url: "/services/data/vXX.0/flowbuilder/messaging/content-fqn", method: "GET", queryParams: { managedContentId: "<the 20Y… Id>" } })` → `{ contentFqn, managedContentId }`. Bind the returned `contentFqn` to `start.form`. It has the shape `marketing--<ContentSpaceApiName>.sfdc_cms__form--<ContentKey>` (e.g. `marketing--Default_Content_Workspace.sfdc_cms__form--<CONTENT_KEY>`). Never hand-assemble it, and never bind the bare `ContentKey`, the `20Y…` Id, or the form title.
3. **Read the form's field names.** `dispatch_readonly({ url: "/services/data/vXX.0/connect/cms/contents/<the 20Y… Id>", method: "GET" })` → `contentBody`. Each form input in the block tree carries `sfdc_cms:formInputNameProperty` (e.g. `Email`, `FirstName`, `Company`) — that value is the field you reference as `$Form.<name>`. The input's `sfdc_cms:fieldReference` shows which object field the form maps it to (e.g. `{!<provider>.Email}` on `Lead`). Reference only names that exist in the form.

## Start element shape

| Field | Value |
|---|---|
| `triggerType` | `"FormSubmissionEvent"` |
| `form` | the `contentFqn` from discovery step 2 |
| `eventName` / `eventType` / `inputs[]` | omit — this trigger has none (`actionName`/`actionType` are cleared on save) |
| `processType` (flow root) | `"AutoLaunchedFlow"` |
| `dataSpace` (flow root) | a Data Space developer name that resolves on the org (commonly `"default"`). Active form flows carry it; set it on the first save. |

```json
{
  "processType": "AutoLaunchedFlow",
  "dataSpace": "default",
  "start": {
    "locationX": 0, "locationY": 0,
    "triggerType": "FormSubmissionEvent",
    "form": "marketing--Default_Content_Workspace.sfdc_cms__form--<CONTENT_KEY>",
    "connector": { "targetReference": "<first element>", "isGoTo": false }
  }
}
```

See `examples/formSubmission.json` for a start plus a Create Records element that maps the submitted answers.

## Read the submitted answers — `$Form.<field>`

- Reference each answer as **`$Form.<formInputNameProperty>`** (e.g. `elementReference: "$Form.Email"`) in assignments, decisions, and record create/update input assignments.
- Do NOT use `$Event.<field>` or `$Record` — neither carries the submission.
- A system-variable listing may not show `$Form`; the validator still resolves it against the bound form. A name the form does not contain fails with "The "<Name>" field doesn't exist in your form content. Use an existing field or add the field to the form in Form Builder." — fix the name from discovery step 3; do not invent fields.

## Save-time rules

- **One form, one flow.** A form can drive only one flow. Binding a form that another flow (or another draft version) already uses is an unsaveable error (`FORM_ALREADY_IN_USE_BY_FLOW` / `FORM_ALREADY_IN_USE_BY_DRAFT_VERSION`). If you hit it, STOP and tell the user which form is taken; do not silently switch to a different form.
- **The form must exist.** A `form` value that does not resolve to Managed Content is an unsaveable error (`FORM_CONTENT_NOT_FOUND`). This is why discovery step 2 is mandatory.
- **A draft form is enough to save.** The form does not have to be published for the flow to save as `Draft`; check with the user before activating against an unpublished form.
- **No fault paths unless asked.** A form-submission flow is a marketing flow: add a `faultConnector` or error-handling branch only when the user asks for error handling. See `../../shared/fault-paths/fault-paths.md` § Marketing Flows — Fault Paths Only When Asked.
