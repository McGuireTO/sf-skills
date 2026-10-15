---
name: flow-element-exit-rule
license: LICENSE.txt has complete terms
description: "Use this skill when a user wants to create, configure, or troubleshoot an Exit Rule (FlowExitRule) in a Salesforce Flow — a condition that ends a flow interview early for an individual. TRIGGER when: user asks to exit, stop, or remove an individual from a flow/journey/segment/on-demand/digital-form/data-graph-change/activation flow based on a condition or automation event, or configure an Exit Rule. DO NOT TRIGGER for record-triggered or default-trigger flows — Exit Rule is not valid there; use flow-element-decision or an entry filter instead."
metadata:
  version: "1.0"
  related-skills: flow-conditions, flow-element-start-segment-triggered
---

# Exit Rule

## Reference File Index

| File | Purpose |
|---|---|
| `validators.md` | Save/activation constraints derived from platform validators |
| `examples/basic.json` | One condition-based exit rule |
| `examples/event-email-link-click.json` | One event-triggered exit rule (email link click) |

## Overview

An Exit Rule ends a flow interview early for an individual when its conditions match. It has no canvas position — it is not a `Start → Exit Rule → End` chain. It lives in the top-level `metadata.exitRules[]` array, evaluated alongside the flow's Start, not dropped between elements.

## When to Use

Use Exit Rule when an individual should stop mid-journey based on a condition (opted out, unsubscribed, already converted). Do not use it to branch flow logic mid-flow — use Decision for that. Do not use it on record-triggered or default-trigger flows — save fails or the rule is silently ineligible.

## Valid Flow Types

Exit Rule is allowed ONLY in:
- `AutoLaunchedFlow` with `triggerType`: `Segment`, `DataGraphDataChange`, `FormSubmissionEvent`, `Activation`, `BroadcastNoTrigger`, `OnDemandNoTrigger`, or `MarketingSobject`. In a Segment flow, reference member fields as `$Record.<field>` (`../start/segment-triggered.md`). In an On-Demand flow, reference the person's fields as `$SelectedIndividual.<field>`, which needs a `start.dataGraph` (`../start/start.md` § On-Demand).
- `DigitalForm`
- `Journey` (deprecated process type)

It is blocked on the default trigger type and every custom process type (Prompt, FSCLending, Appointments, Evaluation, UserProvisioning, ContactRequestFlows, ActionableEventManagement, UnifiedScheduling, RecommendationStrategy) and on record-triggered flows. If the user asks for an Exit Rule on one of these, tell them it isn't supported and suggest a Decision element or an entry filter on Start instead — do not force the save.

## Metadata Shape (FlowExitRule)

Extends `FlowElement`, not `FlowNode` — no `locationX`/`locationY`. Serializes to `metadata.exitRules[]` (sibling of `metadata.start`, not nested inside it).

| Key | Type | Required | Notes |
|---|---|---|---|
| `name` | string | yes | Dev-name; unique within the flow (inherited from `FlowElement`) |
| `label` | string | yes | Display label |
| `ruleOrder` | int | yes | Evaluation order among multiple exit rules on the same flow; lower runs first |
| `conditions` | [Condition](../../shared/conditions/conditions.md)[] | yes\* | At least one condition — zero conditions blocks activation (flow still saves). \*Required for condition-based variant; omit for event-triggered variant (see below) |
| `logicalOperator` | string | yes | `"and"` or `"or"` only — custom-logic expressions (e.g. `"1 AND (2 OR 3)"`) are NOT supported here, unlike Decision's `conditionLogic`. **Required even with exactly one condition** — omitting it fails save with a null-field error |
| `automationEventName` | string | no | Event-triggered variant only |
| `automationEventType` | InvocableActionType | no | Event-triggered variant only |
| `inputParameters` | FlowExitEventInputParameter[] | no | `{ name, value }`; event-triggered variant only |
| `outputParameters` | FlowExitEventOutputParameter[] | no | `{ name, assignToReference }`; event-triggered variant only |

Condition shape matches [FlowCondition](../../shared/conditions/conditions.md). Look up field/entity/operator values with `GET /services/data/vXX.0/flowbuilder/platform/entities`, `GET /services/data/vXX.0/flowbuilder/platform/entity/{apiName}/fields`, `GET /services/data/vXX.0/flowbuilder/schema/flow-capabilities` (read `.operators`).

## Event-Triggered Variant

Set `automationEventName`/`automationEventType` to exit when an invocable automation event fires, instead of a condition match — omit `conditions` entirely; setting both blocks activation. Discover candidates with `dispatch_readonly(method: "GET", url: "/services/data/vXX.0/flowbuilder/action/invocable-events", queryParams: { processType })`, then bind the selected descriptor's `name` to `automationEventName` and `type` to `automationEventType`. Call `dispatch_readonly(method: "GET", url: "/services/data/vXX.0/flowbuilder/action/invocable-action-details", queryParams: { actionType: type, actionName: name })` before setting `inputParameters`/`outputParameters`. `GET /services/data/vXX.0/flowbuilder/platform/event-types` is the platform-event catalog and does not provide the `InvocableActionType` required here.

**Input values.** Each `inputParameters` entry is `{ "name": …, "value": { "stringValue": … } }`: the value is always wrapped in a typed value object, never bare text. For the email engagement events:

| Input | Value |
|---|---|
| `associatedContent` | The email's **ManagedContent Id** (`20Y…`) as a `stringValue`. Not the content FQN (`marketing--…sfdc_cms__email--…`), not the bare content key (`MC…`), and not an element reference to the send. Look it up with SOQL: `SELECT Id FROM ManagedContent WHERE Name = '<email title>' AND ContentTypeFullyQualifiedName = 'sfdc_cms__email'` (or `WHERE ContentKey = '<MC… key>'`). |
| `specificLink` | Required for link click. `ANY` = any link in the email. |

Exit when the individual clicks any link in an email: `examples/event-email-link-click.json`.

This is a different shape from the same event on a Wait Until Event, where `associatedContent` is an element reference to the send (`../wait/wait.md`). On an exit rule, an element reference fails activation.

## Example

See `examples/basic.json`. Each entry is one item of `exitRules[]` — not the whole flow. Multiple rules: give each a distinct `ruleOrder` (1, 2, …) and its own `conditions`/`logicalOperator` — rules don't share condition state.

## Common Failures

- **`Unrecognized field "conditionLogic" (Class FlowExitRule), not marked as ignorable`** → wrong field name. Use `logicalOperator`.
- **`The field logicalOperator can't be "null".`** → `logicalOperator` omitted. Set it even for one condition.
- **`FLOW_EXITRULE_WITH_NO_CONDITION`** → `conditions[]` is empty. Blocks activation (flow still saves). Exit Rule requires at least one condition for the condition-based variant; there is no unconditional exit — use a Decision default path instead if that's the intent.
- **`The field associatedContent can't be "<automationEventName>". Enter a different value and try again.`** → an event exit rule's `associatedContent` is not a ManagedContent Id `stringValue` (bare text, the content FQN or bare content key, or an element reference). The message names the event, not the bad value. Use the `20Y…` Id as a `stringValue`.
- **`The "<field>" element doesn't exist. Remove references to the element in all conditions.`** → a condition uses a bare field name or a DMO-qualified name. In a Segment flow write `$Record.<field>` (`../start/segment-triggered.md`); in an On-Demand flow write `$SelectedIndividual.<field>` and set `start.dataGraph` (`../start/start.md` § On-Demand).
- **`Enter a value for the specificLink input parameter.`** → a link-click exit rule without `specificLink`. Set it (`ANY` for any link).
- **`TRIGGER_TYPE_CONTEXT_OBJECT_NOT_SUPPORTED`** or a silently ineligible rule → flow's process/trigger type isn't in the valid list above. Do not retry with a different trigger type or process type as a workaround. State the constraint again in your final response to the user, even if you flagged it earlier in the conversation — never let the flow save with the exit rule dropped or replaced without saying so in the last message.
- **`WARNING_BLOCK_ACTIVATION` on a condition field reference** → `leftValueReference` doesn't resolve against the flow's bound DMO/Individual object. Confirm the field exists on the object the flow is bound to (via `GET /services/data/vXX.0/flowbuilder/platform/entity/{apiName}/fields`) — a field that's valid on `Account`/`Contact` may not exist on the Individual/DMO object a segment flow is scoped to.
