---
name: flow-element-forward-to-bot-or-agent
license: LICENSE.txt has complete terms
description: "Load when authoring a Forward to Bot/Agent element (`forwardToBotOrAgent` action call) in a marketing flow. Covers the mandatory WaitUntilEvent companion, the cross-element link via `associatedWaitConfiguration`, channel and event-type scoping, processType constraints (NOT Journey), and when to add a fault path. TRIGGER on: 'forward to bot', 'forward to agent', 'forwardToBotOrAgent', 'route replies to agent', 'conversational agent handoff', 'route inbound replies', 'send replies to bot'. DO NOT load for any other action call type."
metadata:
  version: "1.0"
  related-skills: flow-element-action-call, flow-element-wait
---

# Forward to Bot/Agent

`forwardToBotOrAgent` covers two distinct use cases. Identify the correct one before authoring anything.

## Which mode do you need?

| Mode | When to use | `modeSelector` wire value | WaitUntilEvent needed? |
|---|---|---|---|
| **Outreach Initiation (BEA)** | BEA sends the first email to a set of contactable records | `"InitiateConversation"` | **No** |
| **Reply Routing** | Agent handles a customer's inbound reply to an upstream send | `"ManageReplies"` | **Yes** |

- **"Forward to a Buyer Engagement Agent", "route contacts to BEA", "send email outreach via an agent"** → **Outreach Initiation**. Jump to [Outreach Initiation (BEA)](#outreach-initiation-bea). Skip "The Mandatory Pair" entirely.
- **"Route replies to an agent", "handle customer responses"** → **Reply Routing**. The action must always follow an upstream send action and a matching WaitUntilEvent. Do not author it in isolation.

## Reference File Index

| File | Purpose |
|---|---|
| `examples/bea-outreach-initiation.json` | Outreach Initiation (BEA) forwardToBotOrAgent (`modeSelector: "InitiateConversation"`) + required flow-level metadata — no WaitUntilEvent |
| `examples/forward-to-bot-or-agent.json` | Reply Routing: WaitUntilEvent (email response) + forwardToBotOrAgent pair — verified against live describe |

## Outreach Initiation (BEA)

Use `forwardToBotOrAgent` with `modeSelector: "InitiateConversation"` to have a Buyer Engagement Agent (BEA) send the first email to a set of contactable records (Individuals or Contacts for example). It runs in an `AutoLaunchedFlow`; a `Segment` trigger is the verified and most common case, but any trigger that supplies the audience works (see [processType Constraints](#processtype-constraints)). No WaitUntilEvent is needed.

**Fixed action properties:**
- `actionType` / `actionName` / `nameSegment`: `forwardToBotOrAgent`
- `flowTransactionModel`: `"CurrentTransaction"`
- `storeOutputAutomatically`: `true`
- `outputParameters`: `[]`
- `faultConnector`: omit (platform accepts without it; add a fault path if error handling is desired)
- Requires an explicit `ends[]` terminal node; wire `connector.targetReference` to its `name`.
- Set `areMetricsLoggedToDataCloud: true` at the top-level `metadata` for BEA outreach flows.

### Parameters

| Name | Type | Required | Notes |
|---|---|---|---|
| `channel` | string | **yes** | `"Email"` for email outreach |
| `routingType` | string | **yes** | Always `"AgentforceServiceAgent"` for BEA outreach |
| `agentId` | string | **yes** | BotDefinition record ID (`0Xx…`). Resolve via SOQL through `dispatch_readonly`: `{ url: "/services/data/vXX.0/query", method: "GET", queryParams: { q: "SELECT Id, MasterLabel, Type FROM BotDefinition" } }` — filter `Type = 'ExternalCopilot'` and match the agent by label. (Or, for a Data Cloud DMO lookup, the Data 360 tool `d360_query_sql` via `dispatch`: `dispatch({ url: "/services/data/vXX.0/ssot/mcp/execute", method: "POST", body: { toolName: "d360_query_sql", paramsJson: "{\"input\": {\"sql\": \"SELECT ssot__Id__c, ssot__DeveloperName__c FROM ssot__Bot__dlm LIMIT 10\"}}" } })`; the `ssot__Id__c` value is the BotDefinition ID.) Then verify the agent has an active version: `SELECT Id, Status FROM BotVersion WHERE BotDefinitionId = '<0Xx…>'` — at least one row must have `Status = 'Active'`. |
| `modeSelector` | string | **yes** | `"InitiateConversation"` — exact wire value. Do NOT use `"Initial Outbound"`. |
| `maxOutreachAttempts` | number | no | Nudge count (e.g. `3`). **Not returned by `GET /services/data/vXX.0/flowbuilder/action/invocable-action-details`** — set directly via `numberValue`. |
| `timeBetweenOutreach` | number | no | Nudge interval in **minutes** (e.g. `60`). Not in descriptor; set via `numberValue`. |
| `fromAddress` | string | **yes (runtime; schema-optional)** | `SenderEmailAddress` record ID (`35a…`). Resolve via SOQL: `SELECT Id, DisplayName, Username, IsAgentConversationalActive, MessagingChannelId FROM SenderEmailAddress` — pick a row where `IsAgentConversationalActive = true` and `MessagingChannelId` is non-null (those mark an agent-usable sender); match by `DisplayName`/`Username` to the intended sender. `GET /services/data/vXX.0/flowbuilder/action/org-wide-email-addresses` is unreliable for this (returns empty on many orgs) — use the SOQL query; if still blocked, ask the user for the record ID. **Required for the message to actually send — omitting it causes a silent send failure even when the flow validates and activates cleanly.** |
| `communicationSubscriptionId` | string | **yes (runtime; schema-optional)** | `CommSubscription` record ID (`0Xl…`). Resolve via SOQL: `SELECT Id, Name FROM CommSubscription` — pick deliberately based on which subscription the outreach should send under (governs consent; do not just take the first row). **Required for the message to actually send — omitting it causes a silent send failure even when the flow validates and activates cleanly.** |

> `maxOutreachAttempts`, `timeBetweenOutreach`, `fromAddress`, and `communicationSubscriptionId` are hidden parameters — they do **not** appear in `GET /services/data/vXX.0/flowbuilder/action/invocable-action-details` output. Do not call that tool expecting to find them; use the table above directly.

**Dead-end tools — do not call for BEA outreach:**
- `GET /services/data/vXX.0/flowbuilder/action/org-wide-email-addresses` — returns empty on some orgs; cannot reliably resolve `fromAddress` IDs
- `GET /services/data/vXX.0/flowbuilder/action/invocable-action-parameter-enum-values` for `channelType` on `forwardToBotOrAgent` — always returns empty; `channelType` is not a parameter for this action (use `channel`)
- `GET /services/data/vXX.0/flowbuilder/action/invocable-action-details` — will not surface the four hidden params listed above; don't spend tool calls waiting for them to appear

### Silent send failure — the commonly-missed pair

A flow with `forwardToBotOrAgent` can **validate clean and activate successfully — yet the message never sends**, either silently (flow reports "completed," no email delivered) or with:

```text
INTERNAL_ERROR: Message didn't send because internal error occurred while trying to send message
```

The usual cause: **`fromAddress` and `communicationSubscriptionId` are missing from the flow element**. The Agent Builder UI can display these as populated because they are inherited defaults from the agent — but a flow-level F2A element does **not** inherit those defaults. The flow must set both explicitly.

> "Activated but nothing sent" → suspect missing `fromAddress` / `communicationSubscriptionId` first, before investigating channel setup, consent records, or audience membership.

### Minimal example

See `examples/bea-outreach-initiation.json` for the full fragment — the `forwardToBotOrAgent`
ActionCall (all fixed properties and input parameters above) plus the flow-level `ends[]` and
`areMetricsLoggedToDataCloud` metadata that a BEA outreach flow also requires.

## The Mandatory Pair

Every `forwardToBotOrAgent` must be preceded in the same flow by a `WaitUntilEvent`
element that waits for a response to a specific upstream send. The two elements are
linked by `associatedWaitConfiguration`.

```text
[Send action] → [WaitUntilEvent (response event)]
                       │ event path        │ timeout path
                       ▼                   ▼
               [forwardToBotOrAgent]  [no-reply handler]
```

Build in this order: send action → WaitUntilEvent → forwardToBotOrAgent.

**Channel scoping.** One send → one response WaitUntilEvent → one forwardToBotOrAgent.
Match the wait event type to the *specific channel* the user asks to route replies
from. If the user says "route replies from that email" and "you don't need to manage
RCS replies", add only the email response pair — do not add an RCS pair.

## Step 1 — WaitUntilEvent (Wait for Send Response)

`elementSubtype: "WaitUntilEvent"`. Never approximate with a classic Wait or
WaitDuration — engagement events cannot be bound on those types.

### Event branch

| Channel | `automationEventType` | `automationEventName` |
|---|---|---|
| Email reply | `trgrOnEmailResponseEngagement` | `trgrOnEmailResponseEngagement` |
| SMS reply | `trgrOnSmsResponseEngagement` | `trgrOnSmsResponseEngagement` |
| RCS reply | `trgrOnRcsResponseEngagement` | `trgrOnRcsResponseEngagement` |
| WhatsApp reply | `trgrOnWhatsAppResponseEngmt` | `trgrOnWhatsAppResponseEngmt` |

> **`automationEventName` = `automationEventType`** — confirmed via live retrieve. The `default__` prefix form (e.g. `"default__trgrOnEmailResponseEngagement"`) was not a valid value in the tested org; the platform stored `"NotFound"` when it was used — confirm this behavior holds in your target org.

> Always confirm what events are provisioned in the org before authoring — the table above reflects one org's baseline. Use **`GET /services/data/vXX.0/flowbuilder/action/invocable-events`** with `processType: "AutoLaunchedFlow"` and `triggerType: "Segment"` (the Connect OAS param names — NOT `flowProcessType`/`flowTriggerType`). It returns `invocableActions[]`; use each entry's `type` as `automationEventType` and `name` as `automationEventName`.

**`associatedContent` is required** on every messaging response event's
`inputParameters`. Bind it by `elementReference` to the upstream send action element
(not a string template ID):

```json
"inputParameters": [
  { "name": "associatedContent", "value": { "elementReference": "Send_Marketing_Email" } }
]
```

Omitting `associatedContent` blocks activation:
`"Required parameter 'associatedContent' is missing or empty"`.

Set `recordTriggerType: "Create"` on the event branch. Do **not** set `offset` on the event branch — omit it (leave null). Setting `offset: 0` is rejected or stored as a no-op.
Leave `outputParameters: []` — the agent handles the inbound message; there is
nothing to capture here for the forward pattern.

### Timeout branch

Route the timeout branch to a "no reply received" path.

| Field | Value |
|---|---|
| `offset` | 1–365 (required) |
| `offsetUnit` | `Days` / `Hours` / `Weeks` |
| `inputParameters` | `[]` |
| `outputParameters` | `[]` |

### Required shape rules (see also `../wait/wait.md`)

- `defaultConnectorLabel: "Default"` — required even on simplified subtypes or save
  is rejected (`Required field is missing: defaultConnectorLabel`).
- No `defaultConnector`, no `faultConnector` on `WaitUntilEvent`.
- No `maxBatchSize` — rejected on `AutoLaunchedFlow`.
- The **event-branch waitEvent's `name`** is the value you reference in Step 2.

## Step 2 — forwardToBotOrAgent ActionCall

```text
actionType: "forwardToBotOrAgent"
actionName: "forwardToBotOrAgent"
hasCallout:  true   →   marketing flow: faultConnector only when the user asks for error handling; any other flow type: wire one
isAsync:     false
allowsTransactionControl: true
```

### Parameters

| Name | Required | Type | Notes |
|---|---|---|---|
| `channel` | **yes** | string | Messaging channel. No static picklist — verify at author time. Describe says valid values include `"SMS"` and `"WhatsApp"`; use `"Email"` for email-reply routing (confirm per org). |
| `associatedWaitConfiguration` | **yes** | CrossElementRef | Reference to the event-branch waitEvent in the preceding WaitUntilEvent — see syntax below |
| `messagingChannelId` | no | string | Marked `configurationOnly` — `elementReference` is rejected at save time (`INPUTPARAM_INCOMPATIBLE_CONFIGURATION_ONLY`). Cannot be set to `$Context.MessagingChannelId` via element reference. Omit unless you have a static channel ID to hard-code. |
| `agentId` | no | string | ID of the Agentforce Service Agent or bot |
| `routingType` | no | string | `"Omni Flow"`, `"Omni Queue"`, or `"AgentforceServiceAgent"` (confirmed enum value for routing to an Agentforce Service Agent) |
| `modeSelector` | no | string | `"InitiateConversation"` for BEA Outreach Initiation (verified via `GET /services/data/vXX.0/flowbuilder/action/invocable-action-details` on `forwardToBotOrAgent`). `"Initial Outbound"` is **NOT** a valid wire value. For Reply Routing, use `"ManageReplies"`. |

Output: `messageId` (string) — ID of the inbound message. Capture via
`storeOutputAutomatically: true`.

### `associatedWaitConfiguration` syntax

The value is the WaitUntilEvent element's **`name`** — the API name of the Wait element only, not including any event name suffix:

```json
{
  "name": "associatedWaitConfiguration",
  "value": { "stringValue": "Wait_For_Email_Reply" }
}
```

> `associatedWaitConfiguration` has `complexType: "CrossElementRef"` in the action descriptor — that is a Flow Builder UI hint, not a wire-format directive. The Tooling API rejects `elementReference` here with `INPUTPARAM_INCOMPATIBLE_CONFIGURATION_ONLY`. Always use `stringValue` with the element name alone (no `.EventName` suffix).

### Connector and fault connector

A forward `connector` to the next element (or an End node) is **required** — omitting it leaves the action with no exit path and the flow will be invalid. *(When the forward target is an End in `AUTO_LAYOUT_CANVAS` at resolved `apiVersion` ≥ 68.0, point the connector at an explicit `ends[]` End — its own dedicated End or a shared End converged with other non-fault branches, both valid; below 68.0 and on any Free-Form flow, omit the connector instead. See `shared/anti-patterns.md` item 38 and `shared/end/end.md`.)*

`hasCallout: true` — the action can throw at runtime on routing failures. It usually runs in a marketing flow (a `Segment` or `IndivRelatedRecord` trigger). There, add a `faultConnector` only when the user asks for error handling; the platform accepts the action without one. In any other flow type, wire one (the default rule). See `shared/fault-paths/fault-paths.md` § Marketing Flows — Fault Paths Only When Asked.

### Example `inputParameters`

```json
"inputParameters": [
  { "name": "channel",                     "value": { "stringValue": "Email" } },
  { "name": "associatedWaitConfiguration", "value": { "stringValue": "Wait_For_Email_Reply" } },
  { "name": "agentId",                     "value": { "stringValue": "<agent-id>" } }
]
```

## processType Constraints

| processType | triggerType | Supported |
|---|---|---|
| `AutoLaunchedFlow` | `Segment` | **yes** — confirmed via `GET /services/data/vXX.0/flowbuilder/action/invocable-actions` |
| `AutoLaunchedFlow` | `IndivRelatedRecord` | likely yes — same catalog; confirm with `GET /services/data/vXX.0/flowbuilder/action/invocable-actions` |
| `Journey` | — | **NO** — `Journey` (label: "Audience-Driven Flow") does not support `forwardToBotOrAgent` or `WaitUntilEvent`; do not use it |

When the user's request involves a segment, audience, or marketing flow: use
`processType: AutoLaunchedFlow` + `triggerType: Segment`. Never use `Journey`.

Always confirm at author time: `dispatch_readonly(method: "GET", url: "/services/data/vXX.0/flowbuilder/schema/flow-capabilities", queryParams: { processType, triggerType })` and
verify both `WaitUntilEvent` and `ActionCall` appear in `.elements`.

## Anti-Patterns

```jsonc
// WRONG #1 — forwardToBotOrAgent with no preceding WaitUntilEvent in REPLY ROUTING mode.
// Applies ONLY when the intent is to route a customer's inbound reply to an agent.
// For modeSelector="InitiateConversation" (BEA Outreach Initiation in a Segment flow),
// NO WaitUntilEvent is needed or expected — omitting it is correct.

// WRONG #2 — Missing associatedContent on the WaitUntilEvent event branch.
// Blocks activation: "Required parameter 'associatedContent' is missing or empty".
{ "automationEventType": "trgrOnEmailResponseEngagement", "inputParameters": [] }

// WRONG #3 — associatedWaitConfiguration using elementReference.
// The parameter is configurationOnly; elementReference is rejected with
// INPUTPARAM_INCOMPATIBLE_CONFIGURATION_ONLY. Always use stringValue.
{ "name": "associatedWaitConfiguration", "value": { "elementReference": "Wait_For_Email_Reply" } }
// must be:
{ "name": "associatedWaitConfiguration", "value": { "stringValue": "Wait_For_Email_Reply" } }

// WRONG #4 — associatedWaitConfiguration with dot-notation value.
// The "ElementName.WaitEventName" form is rejected — use the element name alone.
{ "name": "associatedWaitConfiguration", "value": { "stringValue": "Wait_For_Email_Reply.Email_Reply_Event" } }
// must be:
{ "name": "associatedWaitConfiguration", "value": { "stringValue": "Wait_For_Email_Reply" } }

// WRONG #5 — The user asked for error handling, but forwardToBotOrAgent has no faultConnector.
// hasCallout is true. When the user did not ask and the flow is a marketing flow (the usual case for
// Reply Routing and BEA Outreach Initiation), omit it. In any other flow type, always wire one.
{ "actionName": "forwardToBotOrAgent", "connector": { "targetReference": "End" } }
// faultConnector missing

// WRONG #6 — processType Journey.
// Journey does not support forwardToBotOrAgent or WaitUntilEvent.

// WRONG #7 — Adding an RCS WaitUntilEvent when the user said
// "you should not need to manage RCS replies".
// Only build the pair for channels the user explicitly wants to route.

// WRONG #8 — flowTransactionModel: "Automatic".
// Does NOT fix a send failure. It moves the transaction boundary so the
// runtime error is swallowed and the flow reports "success" while still
// sending nothing. Keep "CurrentTransaction" so real send errors surface.
```

## Debugging — "activated but not sending"

When the flow activates cleanly but no message is delivered:

1. **Audience**: verify the segment contains records with a valid, non-opted-out address.
2. **Active agent version**: `SELECT Id, Status FROM BotVersion WHERE BotDefinitionId = '<0Xx…>'` — at least one row must be `Active`.
3. **Missing send parameters**: confirm `fromAddress` and `communicationSubscriptionId` are both present on the F2A element and each resolves to a current, valid record (re-query `SenderEmailAddress` / `CommSubscription` as shown in the parameters table above). A missing or stale value in either is the prime suspect.
4. **Transaction model**: confirm `flowTransactionModel` is `CurrentTransaction`, not `Automatic` — `Automatic` swallows the runtime send error so the flow reports success while sending nothing.
