---
name: flow-element-action-call-conversation-messaging
license: LICENSE.txt has complete terms
description: "Load when authoring a Send Conversation Messages (`sendConversationMessages`) action call — the Enhanced Messaging / Digital Engagement invocable that sends a ConversationMessageDefinition to MessagingEndUser recipients. Covers the builder traits that differ from the E360 mobile actions (no callout, no transaction control, no generic types), the describe-driven input parameters, the save-time consent cross-validation, and the worked example. DO NOT load for the E360 mobile push/in-app actions or any other action call."
metadata:
  version: "1.0"
  related-skills: flow-element-action-call
---

# Conversation Messaging Action

Load this when authoring a **Send Conversation Messages** action call. The base `action-call.md` carries only the routing stub; this is the complete build guide for the action.

**Send Conversation Messages** (`sendConversationMessages`) is a standard platform invocable action owned by **Messaging Core - Digital Engagement**. It sends a `ConversationMessageDefinition` (a messaging component) to `MessagingEndUser` recipients in Enhanced Messaging channels as automated outbound notifications. The action itself is **channel-agnostic**: the delivery channel and message type (WhatsApp, SMS, and other Enhanced channel message types) are determined by how the referenced `ConversationMessageDefinition` is configured, not by the action or any input parameter. It is the messaging-session analog of the E360 mobile actions (see [`action-call.md` § Mobile App Messaging Actions](action-call.md#mobile-app-messaging-actions-e360)), but its builder traits differ — read the differences before authoring.

| Action | `actionName` (emit verbatim) | Enum (`InvocableActionType`) | Min API | Category |
|---|---|---|---|---|
| **Send Conversation Messages** | `sendConversationMessages` | `SEND_CONVERSATION_MESSAGES` | 246 | Messaging |

## How it differs from the E360 mobile actions

These come from the **live describe** (`/actions/standard/sendConversationMessages`), not just source — they change the metadata shape versus `sendMobileAppMessage` / `sendMobileAppInAppMessage`:

| Trait | Mobile push / in-app | `sendConversationMessages` | Consequence for the `actionCalls[]` entry |
|---|---|---|---|
| `hasCallout` | `true` | **`false`** | **No** record-triggered scheduled-path restriction. The action may sit on the immediate path of a `RecordAfterSave` flow, and it is **not** blocked in `RecordBeforeSave` on the callout rule. |
| `allowsTransactionControl` | `true` | **`false`** | **Do not emit `flowTransactionModel`.** (The mobile examples emit it *because* they set this true; this action does not support it.) |
| Declared outputs | none | **`requestId` (ID), `messageIdentifiers` (String ≤100)** | `storeOutputAutomatically: true` with `outputParameters: []` is valid and idiomatic — reference `{!Send_Conversation_Messages.requestId}` downstream. |
| `genericTypes` | `ContentSchema` present | **`null`** | **No `dataTypeMappings[]`.** There is no generic type to resolve. |

Both are synchronous, so — like the mobile actions — do **not** emit `timeoutConnector` / `timeoutPathUsage`. **Wire a `faultConnector`, except in a marketing flow**: although `hasCallout: false`, the action throws `ApiException` at runtime on invalid input, missing message definition, or limit-exceeded. In a marketing flow, wire one only when the user asks for error handling (`../../shared/fault-paths/fault-paths.md` § Marketing Flows — Fault Paths Only When Asked).

Each action declares a Custom Property Editor (`scrt_setup-send-conversation-messages-editor`); as with any CPE it replaces the parameter UI in the builder but does not change the saved `inputParameters[]` shape — resolve parameters from `GET /services/data/vXX.0/flowbuilder/action/invocable-action-details` when authoring metadata directly.

## Input parameters

Describe-driven — always fetch the live set with `GET /services/data/vXX.0/flowbuilder/action/invocable-action-details` before authoring. Verified shape:

| Param | Type | Required | Notes |
|---|---|---|---|
| `messageDefinitionName` | String | yes | API name of a `ConversationMessageDefinition` record |
| `requestType` | Picklist | yes | Only active value is `SendNotificationMessages` |
| `isEnforceMessagingChannelConsent` | Boolean | yes | Gates the two consent params below (see cross-validation) |
| `allowedSessionStatus` | Picklist | yes | `Any` / `NonActive` / `Closed` |
| `messagingEndUserIds` | ID (list ≤100) | yes | `MessagingEndUser` record IDs |
| `channelConsentType` | Picklist | conditional¹ | `MessagingEndUser` / `CommunicationSubscription` |
| `communicationSubscriptionId` | ID (`CommSubscription`) | conditional¹ | The communication subscription to apply for consent |
| `sessionLongevityPreference` | Picklist | no | `EndSession` / `KeepSessionOpen` / `KeepSessionOpenOrAppend` |
| `messagingDefinitionInputParameters` | Apex `RichMessaging__MessageDefinitionInputParameter` (list) | no | Merge-field values for the message definition. Describe `maxOccurs` is 2000, but the action enforces a **runtime cap of 10** parameters — exceeding it fails with `LIMIT_EXCEEDED`. |

¹ **Consent cross-validation (save-time, API ≥ 252).** Not surfaced in the describe, but enforced on save:
- `isEnforceMessagingChannelConsent: true` ⇒ `channelConsentType` is **required**.
- `channelConsentType: "CommunicationSubscription"` ⇒ `communicationSubscriptionId` is **required**; any other type ⇒ `communicationSubscriptionId` must be **absent**.
- `isEnforceMessagingChannelConsent: false` ⇒ **both** `channelConsentType` and `communicationSubscriptionId` must be absent.

This mirrors the Send Email template/subject cross-parameter validation noted under [`action-call.md` § Validation Rules and Constraints](action-call.md#validation-rules-and-constraints).

## Worked example

`examples/send-conversation-messages.json` — full `actionCalls[]` entry: required inputs plus a consistent consent pair (`isEnforceMessagingChannelConsent: true` + `channelConsentType: "MessagingEndUser"`, `communicationSubscriptionId` omitted), `messagingEndUserIds` bound to an upstream lookup, `storeOutputAutomatically: true`, and a `faultConnector` (the default rule; in a marketing flow, keep it only when the user asks for error handling).

> **Note:** The example is an `actionCalls[]` fragment, not a complete flow. It references an upstream `Get_Messaging_End_Users` element (supplying recipient IDs) and a `Log_Send_Error` fault-path target that must exist elsewhere in the flow.

## Anti-patterns (agent should reject / flag)

```jsonc
// WRONG #1 — emitting flowTransactionModel. allowsTransactionControl is false.
{ "actionName": "sendConversationMessages", "flowTransactionModel": "Automatic" }

// WRONG #2 — no fault path in a non-marketing flow, or in a marketing flow when the user asked for
// error handling. The action throws ApiException on invalid input / limit exceeded.
{ "actionName": "sendConversationMessages", "connector": { "targetReference": "END_Flow" } }
// (missing faultConnector)

// WRONG #3 — enforcing consent without a consent type. Save-time validation rejects this.
{ "actionName": "sendConversationMessages", "inputParameters": [
  { "name": "isEnforceMessagingChannelConsent", "value": { "booleanValue": true } }
  // missing channelConsentType
] }

// WRONG #4 — communicationSubscriptionId set when the consent type isn't CommunicationSubscription.
{ "inputParameters": [
  { "name": "channelConsentType", "value": { "stringValue": "MessagingEndUser" } },
  { "name": "communicationSubscriptionId", "value": { "stringValue": "0n3..." } }  // must be absent
] }
```

> **Verification note.** Metadata above verified against a **live describe** of
> `/services/data/vXX.0/actions/standard/sendConversationMessages` on a Digital Engagement org
> (v69.0, test1, 2026-08), cross-checked against `SendConversationMessagesAction.java`,
> `InvocableActionType.java` (`SEND_CONVERSATION_MESSAGES`, name-segment `sendConversationMessages`),
> and the four picklist enums (`ConvMsgSendRequestType`, `ConvMsgSendRequestAllowedSessionStatus`,
> `ConvMsgSendRequestConsentType`, `ConvMsgSendRequestSessionLongevityPreference`). Live describe
> confirmed `hasCallout: false`, `allowsTransactionControl: false`, `genericTypes: null`, and the
> `requestId` / `messageIdentifiers` outputs. Per-org, confirm the action's available process/trigger
> types live via `GET /services/data/vXX.0/flowbuilder/action/invocable-action-details` before relying on them.
