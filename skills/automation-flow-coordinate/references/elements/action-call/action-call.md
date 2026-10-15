---
name: flow-element-action-call
license: LICENSE.txt has complete terms
description: "Use this skill when creating, editing, or troubleshooting Flow Action elements — invocable actions including Apex methods, External Services, Quick Actions, REST callouts, Email Alerts, LWC local actions (toasts, navigation), and other invocable actions. TRIGGER when: user asks to call an Apex action, invoke an external service, add an action call, configure an Email Alert, show a toast/notification message, navigate or open a page/URL/record, or use any invocable action in a flow. DO NOT TRIGGER when the user only needs a subflow call (use flow-element-subflow)."
metadata:
  version: "1.0"
  related-skills: flow-output-assignments, flow-fault-paths
---

# Action Element (Invocable Actions)

## Reference File Index

| File | Purpose |
|---|---|
| `examples/inline-transform-input.json` | `actionCalls[]` entry with an inline-Transform Apex input and a `setupReference` connection input |
| `examples/push-notification.json` | E360 "Send Mobile App Message" (push) — verified worked example |
| `examples/in-app-message.json` | E360 "Send Mobile App In-App Message" — verified worked example |
| `examples/send-conversation-messages.json` | "Send Conversation Messages" (Enhanced Messaging / Digital Engagement) — verified worked example |
| `conversation-messaging.md` | Send Conversation Messages action build guide — MUST load before authoring a `sendConversationMessages` action call (trait differences vs. E360 mobile, input parameters, consent cross-validation, anti-patterns) |
| `../forward-to-bot-or-agent/forward-to-bot-or-agent.md` | Forward to Bot/Agent build guide — MUST load before authoring a `forwardToBotOrAgent` action call. Covers the mandatory WaitUntilEvent companion, `associatedWaitConfiguration` cross-reference, channel and event-type scoping, processType constraints, and fault-path requirement. |
| `examples/send-sms-message.json` | E360 "Send SMS Message" (`sendSmsMessage`) — verified worked example; load before authoring a `sendSmsMessage` action call (see [Send SMS Message Action](#send-sms-message-action-e360)) |
| `examples/send-email-message.json` | E360 "Send Email Message" — source-derived worked example (`senderId` + `communicationSubscriptionId` + `commSubscriptionChannelTypeId`); load before authoring a `sendEmailMessage` action call (see [Send Email Message](#send-email-message-e360)) |
| `examples/exit-from-flow.json` | Exit an Individual from one selected marketing flow, across one or all running versions |
| `examples/send-to-journey-no-fields.json` | Verified persisted `sendToJourney` action shape when the Journey schema has no required field mappings |
| `send-to-journey.md` | Send to Journey action build guide — MUST load before authoring a `sendToJourney` action call |
| `validators.md` | Save/activation validation rules for action elements |

## Overview

The Action element is the most versatile callout element in Flow Builder. It covers every invocable action registered with Salesforce: Apex-annotated methods (`@InvocableMethod`), External Services (OpenAPI-backed REST callouts), Quick Actions, Email Alerts, outbound messages, and platform-supplied actions (Einstein, journeys, etc.). In the metadata they all share the same `ActionCall` container — only the `actionType` field distinguishes them.

## When to Use

Use an Action element when a flow needs to:
- Call a custom Apex method marked `@InvocableMethod`
- Call an External Service (REST or MuleSoft)
- Send an Email Alert via a predefined email alert record
- Run any other registered invocable action

For calling another flow, use a Subflow element.

## Action Discovery — One Combined Catalog

Before authoring an `actionCalls[]` entry, locate the action with `GET /services/data/vXX.0/flowbuilder/action/invocable-actions`. A wrong `processType`/`triggerType` filter, or a stale action name, both surface as "Action not found" at save time even though the action exists.

`GET /services/data/vXX.0/flowbuilder/action/invocable-actions` returns a **single combined catalog** covering both action sources (Core collapsed the former separate standard/dynamic catalogs into this one operation). **Transform actions are excluded** — the server filters them out and no MCP tool exposes the transform-action catalog (author Transform elements from the target type schema instead; see the flow-element-transform skill):

| Action source | How it appears in `GET /services/data/vXX.0/flowbuilder/action/invocable-actions` | Notes |
|---|---|---|
| Platform built-ins | Included in the combined result (filter with `actionType`/`namePattern`) | Stock platform invocables (email, Chatter, approval, outbound message, etc.). ~36 on a stock org. |
| Managed packages, custom `@InvocableMethod`, External Connectors, External Services, ESR-backed actions | Included in the combined result; `dataSpace`/`flowDefinitionId` scope the dynamic portion (they don't yield a dynamic-only list) | Anything installed or namespaced. 3500+ entries on orgs with integrations — FILTER WITH `namePattern`/`actionType`/`limit` (or jq) AS THE COMBINED RESULT IS USUALLY TOO LONG. |

Rule of thumb: there is one catalog. Narrow it — pass `actionType` (e.g. `apex`, `flow`, `emailSimple`) and/or `namePattern` (case-insensitive substring on API name + label) to find third-party/managed/custom actions; `dataSpace`/`flowDefinitionId` scope the **dynamic portion** of that combined result. There is no standard-only or dynamic-only MCP variant — Core always calls `getAllowedActions` with `includeStandard=true, includeDynamic=true`.

Always pass the flow's exact `processType` (required) and `triggerType` (optional) to `GET /services/data/vXX.0/flowbuilder/action/invocable-actions`. Same action name can be filtered out by trigger type (e.g. callout actions blocked on `RecordBeforeSave`).

Once the target action is identified, always drill in with `GET /services/data/vXX.0/flowbuilder/action/invocable-action-details` (`actionName` + `actionType`, both required; optional `builderType`/`expand`) to get the authoritative parameter schema before authoring metadata. This call does not take `processType`/`triggerType`.

## Required Properties

| Property | Description | Constraints |
|---|---|---|
| Label | Human-readable name shown on the canvas | Cannot be blank |
| API Name | Unique developer name within the flow | Must be alphanumeric and start with a letter |
| Action | The specific invocable action to execute | Must resolve to an action registered for this flow's process type and trigger type; cannot be null |

## Optional Properties

| Property | Description | Default |
|---|---|---|
| Description | Free-text documentation | None |
| Manually Assign Variables | When enabled, exposes output parameters for explicit assignment instead of using automatic output handling | Disabled (automatic output enabled where supported) |
| Transaction Control | On supported process types, controls whether the action runs in the current, new, or automatic transaction | Automatic (when supported) |
| Store Output Automatically | Whether the action output is stored as a typed auto-output variable | true (where process type supports it) |

## Input Parameters

Input parameters are driven entirely by the action's describe metadata. The Flow Builder UI:

1. Fetches all declared input parameters from the server when an action is selected.
2. Merges them with any values already saved in the flow, preserving prior assignments.
3. Displays required parameters with a validation error if left blank.
4. Hides parameters containing the internal prefix `__` (double-underscore) — these are system-generated and not customer-facing.
5. Parameters can have a "controlling field" that drives conditional visibility: if parameter A controls parameter B, clearing A's value automatically clears B's value.
6. Some parameters have enumerated values that are loaded dynamically based on the values of other parameters (dependency chains).

### How to bind an input parameter's value

Every entry in `inputParameters[].value` is one of **five** shapes. Pick by what the value actually is — not by habit.

| Shape | Use when | Example |
|---|---|---|
| `{ "stringValue": "X" }` / `{ "numberValue": N }` / `{ "booleanValue": ... }` | Value is a **literal known at design time**. This includes any value chosen from an enumerated-values response when the parameter is a primitive. | `{ "name": "connection", "value": { "stringValue": "Quickbooks1t2" } }` |
| `{ "setupReference": "<devName>", "setupReferenceType": "<TypeName>" }` | Value is a **named setup record** referenced by developer name — ExternalServiceRegistration (named connection), NamedCredential, Permission Set, Recipient Group, etc. Emitted when the parameter is typed as a setup reference rather than a primitive enum. | `{ "name": "connection", "value": { "setupReference": "Quickbooks1t2", "setupReferenceType": "ExternalServiceRegistration" } }` |
| `{ "elementReference": "$Record.Field" }` or `{ "elementReference": "<TransformName>" }` or `{ "elementReference": "<RecordLookupName>.Id" }` | Value comes from **another flow element at runtime** — record trigger field, prior lookup, prior transform, prior action output, formula. | `{ "name": "createCustomerRequest", "value": { "elementReference": "Build_Request" } }` |
| `{ "elementReference": "<VariableName>" }` | Value must vary per invocation (caller passes it in as `isInput: true`) **or** is genuinely reused by multiple elements **or** is computed at runtime via Assignment. | `{ "name": "approverId", "value": { "elementReference": "User_Selected_Approver" } }` |
| `{ "transform": { ... } }` — **inline Transform** | Parameter is typed `Apex` / `SObject` / `schemaUri` AND there is no existing upstream Transform / variable / element to point at. Builds the typed wrapper object **inline** inside the action's input. See [Inline Transform Inputs](#inline-transform-inputs) below. | `{ "name": "createCustomerRequest", "value": { "transform": { "dataType": "Apex", "apexClass": "StdExtConnect__Quickbooks_Tx5fCustomerCreateRequest", "isCollection": false, "transformValues": [ ... ] } } }` |

**Picking between a standalone Transform vs. an inline Transform** for an `Apex` / `SObject` / `schemaUri` input:

| Situation | Use |
|---|---|
| The shaped object is consumed by **one action**, isn't reused, and doesn't need to appear as its own canvas node. | **Inline transform** — `value.transform: { ... }` directly on the action input. |
| The shaped object is consumed by **multiple downstream elements**, the user wants it visible on the canvas, or downstream logic needs to reference it by name. | **Standalone Transform** element in `transforms[]`, then `elementReference` to that Transform's name on the action input. |

**Anti-pattern — DO NOT do this:** wrapping a known-at-design-time literal in a `String` variable just to indirect through `elementReference`.

```json
// WRONG — literal hidden behind a variable
"variables": [{ "name": "QB_Connection_Id", "dataType": "String",
                "value": { "stringValue": "Quickbooks1t2" }, "isInput": true }],
"inputParameters": [{ "name": "connection",
                      "value": { "elementReference": "QB_Connection_Id" } }]

// RIGHT — literal bound directly
"variables": [],
"inputParameters": [{ "name": "connection",
                      "value": { "stringValue": "Quickbooks1t2" } }]
```

Why it's wrong: the variable adds no behavior, and if `isInput: true` it lets callers pass a value the action's enum/type constraint would otherwise reject at design time. Variables earn their keep only when the value (a) is computed, (b) varies per caller, or (c) is reused across multiple elements.

### Inline Transform Inputs

When an action declares an input parameter typed `Apex` / `SObject` / `schemaUri` and **no existing flow element** (variable, prior lookup, standalone Transform, prior action output) holds a suitable value, build the wrapper **inline** at the action's input using a `transform` value. This keeps the metadata local to the action instead of dropping a standalone Transform on the canvas.

**Wire shape.** The `value` becomes `{ "transform": { ...transform-body... } }`. The inner `transform` body is **identical** in shape to a standalone Transform element body (same `transformValues[]`, same `transformValueActions[]`, same `transformType: "Map"` semantics) — minus the canvas-level fields. See the **flow-element-transform skill** (`transform.md` § Inline Transform, § transformValues Structure, § TransformValueAction Shapes) for the full body shape; the action-call skill does not duplicate those rules.

**Required fields on the inline transform body:**

| Field | Required | Notes |
|---|---|---|
| `dataType` | yes | `"Apex"`, `"SObject"`, or matching the parameter's declared type |
| `apexClass` / `objectType` / `schemaUri` | yes (one) | Exactly one — pick by `dataType` |
| `isCollection` | yes | Mirror the parameter's `maxOccurs` (false for singular, true when the param is a list) |
| `transformValues` | yes | One outer entry containing `transformValueActions[]` |

**Fields OMITTED from an inline transform** (canvas-only on a standalone Transform):
- `name`, `label`, `locationX`, `locationY` — not a canvas node
- `connector` — flow continues from the host action, not the inline transform
- `storeOutputAutomatically` — the wrapper is consumed inline; no separate output resource

**TransformValueAction value shapes** (same as standalone Transform; cross-link to transform skill for full rules):

```jsonc
// Literal scalar
{ "transformType": "Map", "outputFieldApiName": "GivenName",
  "value": { "stringValue": "John Doe", "inputConfiguratorMode": "Resource" } }

// Enum-resolved scalar (Custom mode signals a picked enum literal)
{ "transformType": "Map", "outputFieldApiName": "PreferredDeliveryMethod",
  "value": { "stringValue": "Email", "inputConfiguratorMode": "Custom" } }

// Element reference (from $Record, prior lookup, prior action output)
{ "transformType": "Map", "outputFieldApiName": "ShipAddr.PostalCode",
  "value": { "elementReference": "Get_Records_1.MailingPostalCode",
             "inputConfiguratorMode": "Resource" } }
```

**Nested fields** (e.g. `ShipAddr.PostalCode`, `PrimaryEmailAddr.Address`) use the **dot-path** form of `outputFieldApiName`. The Transform editor recurses into the parent Apex sub-object automatically; the inline transform body does the same. The dot-path rule is owned by the transform skill — see `transform.md` § Required-on-Save Rules.

**Don't:** create a standalone Transform with `transformValues` that contains only one mapping action, then `elementReference` it from a single action input. That's the inline-transform case in disguise — collapse it.

**Do:** when the user later asks to reuse the shaped wrapper from a second action or expose it on the canvas, promote the inline transform to `transforms[]` and switch the action input to `elementReference`.

**Reference example:** `examples/inline-transform-input.json` — full `actionCalls[]` entry combining an inline-Transform Apex input, a `setupReference` connection input, three mapping styles (literal, enum-resolved, element reference), and a nested dot-path field.

### Dynamic Type Mappings (Generic Types)

**Decision gate — run this before writing any `actionCalls[]` entry.** Inspect `GET /services/data/vXX.0/flowbuilder/action/invocable-action-details`'s `genericTypes[]`:

- **Empty `genericTypes[]`** → the action is non-generic; emit **no** `dataTypeMappings` (a stray entry is rejected — see [Save-time rejections](#save-time-rejections)).
- **Non-empty `genericTypes[]`** → for **each non-`NamedAutomationSchema` placeholder**, run the Resolution workflow in [Generic-Type Placeholders](#generic-type-placeholders-u__-t__) and emit one `dataTypeMappings[]` entry (`typeName` = the placeholder's `genericTypes[].name`; plus exactly one concrete `typeValue`/`apexClass`/`schemaUri`). `NamedAutomationSchema` placeholders (e.g. `ContentSchema`) are optional and may be left unmapped.

Actions can declare generic parameters (e.g., "T extends SObject"). Flow Builder presents a type mapping row for each generic type, and the user must choose a concrete Salesforce object or Apex type before parameters that depend on it are shown. Rules:

- Each generic type mapping must have a non-blank, valid value — except `NamedAutomationSchema` type mappings, which are optional and can be left unmapped.
- Changing a type mapping reloads dependent input/output parameters.
- **The metadata field is `dataTypeMappings`, despite this section's name.** `dynamicTypeMappings` is not a real field — the server won't flag it as unknown, it just fails the whole save with a generic top-level rejection (see "Save-time rejections" below). Same trap applies to any action with generic types, not just this one.
- **Resolve every non-`NamedAutomationSchema` `genericTypes[]` entry, even one the flow's design doesn't actively use.** This includes `SCHEMAURI` (`schemaUri`) placeholders — only `NamedAutomationSchema` is exempt. A generic placeholder blocks validation regardless of whether the flow reads that specific generic-typed parameter — e.g. a flow that only assigns a sibling String/primitive output still fails `DYNAMIC_TYPE_MAPPING_MISSING` if an unrelated Apex-typed generic sibling parameter is left unmapped. Check `genericTypes[]` on every action drill-down and resolve all of it, not just the placeholder(s) feeding the parameter you plan to use.


## Output Parameters

There are two modes:

**Automatic output handling (default where supported)**
- Output is stored as a single, typed Flow resource named after the action element.
- The data type is either `ActionOutput` (generic) or a specific Apex/SObject type if the action declares a system-generated output.
- No individual output parameters appear in the editor.

**Manual assignment (advanced)**
- The user switches the toggle to manually assign variables.
- Each output parameter from the action descriptor becomes an assignable row.
- Outputs that are blank (unassigned) are stripped before saving to metadata.
- Empty string values on output rows are treated as null (no assignment).
- Parameters marked as `NOT_AVAILABLE` (removed from the action definition) show a warning badge "Will Cause Errors" and are disabled.

## Fault Path

Fault-capable Action elements have a fault path (connector type `FAULT`). This path is taken when the action throws an exception at runtime. Apply the action-specific persisted shape before this generic rule.

**Marketing flows: fault path only when asked.** In a marketing flow, add a `faultConnector` to an action only if the user asks for error handling. A marketing flow is one whose `start.triggerType` is on the list in `shared/fault-paths/fault-paths.md` § Marketing Flows — Fault Paths Only When Asked. This covers every marketing action below (Send Email Message, Send SMS, Send RCS, push, in-app, and Exit From Flow). In any other flow type, including a plain Autolaunched Flow with no `triggerType`, the fault-path rules in this file apply as written.

- Default available connections: one regular path + one fault path.
- `maxConnections` is 2 for non-branching actions.

## Async Actions (Wait Until Completed)

Some actions declare `isAsync = true`. When the flow is configured to wait for completion (`isWaitUntilCompleted = true`), the element gains two child branches:

- **Default path** — taken when the action completes successfully.
- **Timeout path** — taken if the action does not complete within the configured window. The timeout path can be hidden/disabled via `timeoutPathUsage`. In auto-layout canvas, the timeout path defaults to disabled; in free-form canvas it defaults to enabled.

Timeout configuration:
- `offset` must be a number between 1 and 365 (inclusive).
- `offsetUnit` can be `Minutes`, `Hours`, `Days`, `Weeks`, or `Months`; it must not be blank.
- Changing a branching async action triggers the `ACTION_CALL_WITH_MODIFIED_AND_DELETED_PATHS` element type to signal path cleanup.

**Authoring an async action call — required field set.** When `GET /services/data/vXX.0/flowbuilder/action/invocable-action-details` reports `isAsync: true` for the target action, always emit all three together on the `actionCalls[]` entry, even if the user's request only mentions waiting for the result:

```json
"isWaitUntilCompleted": true,
"offset": 1,
"offsetUnit": "Hours"
```

Omitting `isWaitUntilCompleted` fails validation with `ACTIONCALL_INVALID_ISWAITUNTILCOMPLETED` ("you must set isWaitUntilCompleted to true"). Omitting `offset`/`offsetUnit` fails/warns with `ACTIONCALL_MISSING_OFFSET`. Both are cheap to preempt: check `isAsync` on every action drill-down before authoring, not after the first validation round-trip flags it.

## Actions With Outcome Paths (Branching Actions)

Certain action types (e.g., `INDV_PREFERRED_RECORD_DECISION`, some orchestration steps) return a list of named outcome paths instead of a single result. These are called "dependent outcomes". The flow editor:

1. Fetches available outcomes from the server using the action name, type, and current input parameter values.
2. Presents each outcome as a selectable path.
3. Creates an `ActionCallPath` child element per outcome, plus a hidden default path in metadata.
4. Path names come from the action descriptor; path labels are auto-generated or localized.

Child paths use the naming convention `<elementName>:<pathName>` to ensure uniqueness in nested contexts.

## Versioned Actions

Actions can declare multiple versions via a `versionList`. When an action is versioned:
- The editor shows a version picker.
- Switching versions re-fetches parameters and merges them with the current element state.
- Parameters that existed in the old version but not the new version are flagged with warnings; required or populated ones are retained with an error; optional unset ones are dropped.
- If the action also has a Custom Property Editor (CPE), all parameters with warnings are purged before the CPE is rendered (to avoid presenting invalid parameters to the CPE).

## Configuration Editors (Custom Property Editors)

An action can declare a `configurationEditor` — a custom Lightning component that replaces the standard parameter list UI. When present:
- The CPE receives the flow state, input variables, and type mappings.
- Changes from the CPE are handled via `ConfigurationEditorChangeEvent` and `ConfigurationEditorPropertyDeleteEvent`.
- Mini-CPEs are detected when any input parameter has a `cpeName` attribute.

## Warnings During Merge

When the saved flow metadata is merged with the latest action describe, parameters can carry these warnings:

| Warning Code | Meaning | Visual |
|---|---|---|
| `NOT_AVAILABLE` | Parameter was removed from the action | Badge: "Will Cause Errors"; input disabled |
| `DATA_TYPE_CHANGED` | Parameter data type changed between versions | Warning icon |
| `DUPLICATE` | Same parameter name assigned more than once (CFD edit) | Marked for deletion |

## Validation Rules and Constraints

- Action must be selected and non-null before saving.
- All required input parameters must have a value (not null, not blank).
- Resource picker values are validated for correct format and reference.
- Generic type mappings must be filled (except `NamedAutomationSchema`).
- For async actions: `offset` is required, numeric, range 1–365; `offsetUnit` is required.
- Email-sending actions (Send Email) have cross-parameter validation: template vs. subject/body choice fields must be consistently set; recipient ID is required when a template is used. See [Send Email Actions](#send-email-actions) for the verified `sendEmailMessage`/`emailSimple` shapes and a note on which of these checks reproduced at `validate_flow` time.
- Parameters with `__` in their name are internal and excluded from the customer-facing UI.
- **RecordBeforeSave flows cannot use actions with external callouts at all** — before-save flows have no scheduled path; deployment or activation is blocked. **RecordAfterSave flows** with `hasCallout: true` must place the action on a **scheduled path** (`scheduledPaths[]` on the Start element), not the immediate path. Save succeeds; activation is blocked with `WARNING_BLOCK_ACTIVATION` if the action sits on the immediate path.

## Common Patterns

- To pass a record ID into an action, map an input parameter to the record ID variable from the triggering record or a lookup result.
- To use an action's output in a subsequent element, reference the auto-output variable `{!ElementApiName.OutputFieldName}` (automatic mode) or the manually assigned variable.
- Actions that modify records should use the fault path to handle errors gracefully (in a marketing flow, only when the user asks for error handling; see [Fault Path](#fault-path)).
- For actions with generic types (`genericTypes[]` non-empty on the describe — placeholder names like `T__body`, `U__output`, `sObjectType`), resolve the placeholder(s) first and emit `dataTypeMappings[]` on the action call. Parameters typed against an unresolved placeholder won't accept concrete values until the mapping is set. See [Generic-Type Placeholders](#generic-type-placeholders-u__-t__) below.
- When an action version list is present, always confirm the desired version before configuring parameters, because switching versions resets parameters.

## MCP Tools for Action Discovery

Agents call these flow MCP tools, not the raw Aura functions.

| Tool | Use when |
|---|---|
| `GET /services/data/vXX.0/flowbuilder/action/invocable-actions` | Single discovery tool for BOTH platform built-ins (`emailSimple`, `chatterPost`, `submitForApproval` — ~36 on a stock org) AND dynamic actions (managed-package, External Connector, External Service, ESR-backed, custom `@InvocableMethod` — 3500+ on orgs with integrations). Core collapsed the former separate standard/dynamic catalogs into this one operation, which returns the **combined** list (transform actions are excluded — no MCP tool lists them). Required `processType`; optional `triggerType`, `builderType`, `actionType` (filter by type, e.g. `apex`/`flow`), `namePattern` (case-insensitive substring on API name + label), `limit`, and `dataSpace`/`flowDefinitionId` (scope the dynamic portion of the combined result — ignored for standard built-ins; they don't produce a dynamic-only list). **CRITICAL: on orgs with integrations the combined payload is extremely large (multiple MB from dynamic actions). Always narrow with `namePattern`/`actionType`/`limit` (or filter with jq) before reading.** |
| `GET /services/data/vXX.0/flowbuilder/action/invocable-action-details` | Full schema for ONE action — required inputs, generic types, output shape. **Mandatory** before authoring any `actionCalls[]` element. Params: `actionType`, `actionName` (both required); optional `builderType` and `expand` (pass `expand=SchemaParameters` to fold schema-backed params' nested fields inline, one level, avoiding a separate `GET /services/data/vXX.0/flowbuilder/action/schema-uri-parameters` call). There is no `processType`/`triggerType`/`flowProcessType`/`flowTriggerType` param. |
| `GET /services/data/vXX.0/flowbuilder/action/invocable-action-generic-type-enum-values` | Resolve generic-type placeholders — any `genericTypes[].name` starting with `U__` (uniformly-typed param) or `T__` (per-action typed param like `T__body`). Call only when `GET /services/data/vXX.0/flowbuilder/action/invocable-action-details` returned non-empty `genericTypes[]` AND every path listed under each placeholder's `typeProviders.dependsOn` has a resolved upstream value. Required params: `actionType`, `actionName`, `requestedGenericTypes` (a **JSON array of placeholder-name strings**, e.g. `["T__body"]` — the OAS schema is `type: array, items: {type: string}`, so send an array even for one placeholder, not a bare string), and `inputParamsJson` (a **JSON-encoded string** of `[{path, value}]` objects); optional `processType`, `triggerType`, `builderType`. Each `value` inside `inputParamsJson` must be an **object** holding a **literal** (`{stringValue: "..."}` / `{numberValue: 1}`) — the resolver reads only `stringValue`/`numberValue`, so an `elementReference` or other FEROV variant resolves to null and is dropped; resolve the driving input to a literal first. |
| `GET /services/data/vXX.0/flowbuilder/action/invocable-action-parameter-enum-values` | Resolve dynamic picklist / dependent-enum values on one or more parameters. Call when `GET /services/data/vXX.0/flowbuilder/action/invocable-action-details` returned a parameter (or `subfieldEnums[]` entry) with `status: "NOT_ENOUGH_INFO"` AND the upstream `dependsOn` inputs are now known. Required params: `actionType`, `actionName`, `requestedParamsJson` (a **JSON-encoded string** of the list-of-paths, e.g. `[["param"],["wrapper","subfield"]]`), and `inputParamsJson` (a **JSON-encoded string** of `[{path, value}]` objects supplying every `dependsOn` path); optional `processType`, `triggerType`, `builderType`. Returns `List<InvocableActionParameterDescriptor>` with the populated enum value set. |
| `GET /services/data/vXX.0/flowbuilder/resource/apex-types` | Browse Apex request/response classes by namespace + name. Required when an action input has `dataType: apex`. **Must pass `processType`** (required); optional `builderType`, `namePattern`, `limit`. There is no trigger-type param. |

Naming convention for raw Aura references in Salesforce docs (mapping if you read upstream code):

| Aura function | MCP tool |
|---|---|
| `getAllInvocableActionsForType` | `GET /services/data/vXX.0/flowbuilder/action/invocable-actions` (returns standard + dynamic combined) |
| `getStandardInvocableActionsForType` | `GET /services/data/vXX.0/flowbuilder/action/invocable-actions` (standard actions are included in the combined result; filter with `actionType`/`namePattern`) |
| `getDynamicInvocableActionsForType` | `GET /services/data/vXX.0/flowbuilder/action/invocable-actions` (`dataSpace`/`flowDefinitionId` scope the dynamic portion of the combined result — there is no dynamic-only MCP variant) |
| `getInvocableActionDetails` | `GET /services/data/vXX.0/flowbuilder/action/invocable-action-details` |
| `getInvocableActionParameterWithEnumeratedValues` | `GET /services/data/vXX.0/flowbuilder/action/invocable-action-parameter-enum-values` |
| `getInvocableActionGenericTypesWithEnumeratedValues` | `GET /services/data/vXX.0/flowbuilder/action/invocable-action-generic-type-enum-values` |
| `getDependentOutcomes` | `GET /services/data/vXX.0/flowbuilder/action/dependent-outcomes` (dedicated tool; params `actionType`, `actionName`, `paramValuesJson`) |

## Apex-Typed Input Parameters

When `GET /services/data/vXX.0/flowbuilder/action/invocable-action-details` returns a parameter with `dataType: "Apex"` (or a non-null `apexClass` field), the action expects a typed Apex object — not a flat set of scalar inputs. This is true across ALL actions.

**Workflow:**

1. From the parameter descriptor, capture the `apexClass` value.
2. Call `dispatch_readonly(method: "GET", url: "/services/data/vXX.0/flowbuilder/resource/apex-types", queryParams: { processType })` (optionally `namePattern` to narrow by class name, `limit`) and locate the class by matching `apexClass` against `apexTypes[].name`. Each entry returns `properties[]` listing `{ name, dataType, objectType, apexClass, isCollection }` and an `innerTypes[]` array holding the nested Apex types referenced by this class.
3. Recurse into any property whose `dataType: "Apex"` — resolve its nested shape by looking up its `apexClass` in `innerTypes[]` (or the top-level `apexTypes[]` list) to enumerate nested children.
4. Author a **Transform element** (`transforms[]`) whose `apexClass` / `objectType` matches the request class. Map scalar children directly; use dot-path `outputFieldApiName` for nested children (e.g. `"BillAddr.City"`). See the flow-element-transform skill.
5. Pass the Transform as the action's input via `value: { elementReference: "<TransformName>" }`.

Do not pass flat scalar fields directly as top-level `inputParameters[]` when the action signature is a single Apex wrapper — the save will succeed but the action will fail at runtime because the wrapper is unset.

## Generic-Type Placeholders (`U__*`, `T__*`)

Some invocable actions don't have a static input/output type — the type is computed per upstream binding (e.g. for `JiraV2.createIssue` the request body shape depends on which `project` + `issueType` was chosen; for `extractDataFromDocument` the output shape depends on the document configuration). These actions surface as `genericTypes[]` entries on the action describe.

**Recognition.** `GET /services/data/vXX.0/flowbuilder/action/invocable-action-details` returns:

```json
"genericTypes": [
  {
    "name": "T__body",                       // or "U__input" / "U__output" / "T__<param>"
    "superType": "APEXTYPE",                 // or "SOBJECT" / "SCHEMAURI"
    "typeProviders": { // Type providers is optional, when not including select the type based on the input/output values
      "dependsOn": [["issueType"], ["project"], ["connection"]],
      "values":    [],
      "status":    "NOT_ENOUGH_INFO"
    }
  }
]
```

AND one or more `parameters[]` entries whose `apexClass` / `sobjectType` / `schemaUri` equals the placeholder name (e.g. `"apexClass": "T__body"`). Those parameters get their concrete shape from the resolved placeholder.

**`superType` picks the `dataTypeMappings` field — don't guess, don't default to `typeValue`.** Match directly, no exceptions:

| `genericTypes[].superType` | `dataTypeMappings` field to emit |
|---|---|
| `APEXTYPE` | `apexClass` |
| `SOBJECT` | `typeValue` |
| `SCHEMAURI` | `schemaUri` |
| `NAMED_AUTOMATION_SCHEMA` | `schemaUri`, never `typeValue` (the mapping is optional, see [Key rules](#key-rules); `send-to-journey.md` emits one) |

`extractDataFromDocument`'s `U__output` is `superType: "APEXTYPE"` — the resolved value (e.g. `DocumentProcessing__invoiceconfig_invoiceconfig`) goes in `apexClass`. Emitting it as `typeValue` passes the "is it resolved" check but fails a second round with `TYPE_MAPPING_NOT_SUPPORTED`.

**Check `genericTypes[]` before the first `validate_flow` call, not after an error.** Same cheap-to-preempt pattern as the `isAsync` check in [Validation Rules and Constraints](#validation-rules-and-constraints): read `GET /services/data/vXX.0/flowbuilder/action/invocable-action-details`'s `genericTypes[]` up front. Non-empty means resolve every entry via `GET /services/data/vXX.0/flowbuilder/action/invocable-action-generic-type-enum-values` and emit `dataTypeMappings[]` in the very first payload — don't build the action call, validate, and let `DYNAMIC_TYPE_MAPPING_MISSING` tell you what the describe already told you.

**Naming.**
- `U__<name>` — generic placeholder shared across multiple params with the same type (uniform).
- `T__<name>` — per-parameter typed placeholder (typically request bodies on External Connector actions).

Both resolve through the same tool; the prefix is a hint about scope, not a different mechanism.

**Resolution.**

1. Bind every `dependsOn[]` path with a concrete upstream value.
2. Call `dispatch_readonly(method: "GET", url: "/services/data/vXX.0/flowbuilder/action/invocable-action-generic-type-enum-values")`:

   ```json
   {
     "actionType":            "<actionType>",
     "actionName":            "<actionName>",
     "processType":           "AutoLaunchedFlow",
     "triggerType":           "RecordAfterSave",
     "requestedGenericTypes": ["T__body"],
     "inputParamsJson":       "[{\"path\":[\"connection\"],\"value\":{\"stringValue\":\"<ESR_DeveloperName>\"}},{\"path\":[\"project\"],\"value\":{\"stringValue\":\"<projectKey>\"}},{\"path\":[\"issueType\"],\"value\":{\"stringValue\":\"<issueTypeId>\"}}]"
   }
   ```

   `inputParams[].value` is a FEROV object — `{stringValue: ...}` / `{numberValue: ...}` / `{booleanValue: ...}` — NOT a bare string. Only these three literal keys are supported here (no `elementReference`, no date variants); the resolver needs a design-time literal, not a runtime reference. The server returns `400` with `Expected object, received string` if you pass a bare string.

   WRONG — bare string, fails with 400 "Expected object, received string":
   ```json
   { "path": ["<paramName>"], "value": "<value>" }
   ```

   RIGHT — wrapped in a FEROV literal:
   ```json
   [
     { "path": ["<paramName>"], "value": { "stringValue": "<value>" } },
     { "path": ["<paramName>"], "value": { "numberValue": 42 } },
     { "path": ["<paramName>"], "value": { "booleanValue": true } }
   ]
   ```

   Same rule applies to `flowbuilder_get_invocable_action_parameter_with_enumerated_values`'s `inputParams[]` — both enum-resolution tools share this shape.
   The tool params match the Connect OAS contract: `actionType` + `actionName` are required; `processType`/`triggerType`/`builderType` are optional (note: `processType`/`triggerType`, **not** `flowProcessType`/`flowTriggerType`). `requestedGenericTypes` is a **JSON array of placeholder-name strings** (schema `type: array, items: {type: string}`) — send `["T__body"]`, not the bare string `"T__body"`, even for a single placeholder. `inputParamsJson` is a **JSON-encoded string** (not a structured array) whose decoded form is `[{path, value}]`. Inside it, each `value` is an OBJECT holding a **literal** (`{stringValue: ...}` / `{numberValue: ...}`), NOT a bare string — the server returns `400` with `Expected object, received string` if you pass a bare string. Note this resolver reads only `stringValue`/`numberValue`; an `elementReference` (or any other FEROV variant) resolves to null and is dropped, so a `dependsOn` input pointed at a variable won't resolve — bind it to a concrete literal first.

3. Read the response's resolved `apexClass` / `objectType` / `schemaUri` for each requested placeholder.
4. Emit `dataTypeMappings[]` on the action call (see "Metadata Shape" below).


## Dynamic-Picklist Parameters (Dependent Enums)

Some parameters have enum value sets that cannot be resolved until upstream input parameters are known. The mechanism is the same regardless of `actionType`.

**Recognition.** `GET /services/data/vXX.0/flowbuilder/action/invocable-action-details` returns descriptors of this shape:

```json
{
  "name": "<paramName>",
  "subfieldEnums": [
    {
      "path": ["<paramName>", "<subfield>"],
      "enums": {
        "dependsOn": [["<upstreamParam>"]],
        "values":    [],
        "status":    "NOT_ENOUGH_INFO"
      }
    }
  ]
}
```

Or at the parameter level itself:

```json
{ "name": "<paramName>", "enums": { "dependsOn": [["<other>"]], "status": "NOT_ENOUGH_INFO" } }
```

`status: "NOT_ENOUGH_INFO"` + non-empty `dependsOn` ⇒ needs resolution.

**Resolution.** Call `dispatch_readonly(method: "GET", url: "/services/data/vXX.0/flowbuilder/action/invocable-action-parameter-enum-values")`:

```json
{
  "actionType":         "<actionType>",
  "actionName":         "<actionName>",
  "processType":        "AutoLaunchedFlow",
  "triggerType":        "RecordAfterSave",
  "requestedParamsJson": "[[\"<paramName>\",\"<subfield>\"]]",
  "inputParamsJson":     "[{\"path\":[\"<upstreamParam>\"],\"value\":{\"stringValue\":\"<resolvedValue>\"}}]"
}
```

`actionType` + `actionName` are required; `processType`/`triggerType`/`builderType` are optional (note: `processType`/`triggerType`, **not** `flowProcessType`/`flowTriggerType`). `requestedParamsJson` is a **JSON-encoded string** whose decoded form is a list of paths (single-element for top-level params, multi-element for nested subfields). `inputParamsJson` is a **JSON-encoded string** whose decoded form is `[{path, value}]` and must supply every path listed in the target's `dependsOn[]`. Returns `List<InvocableActionParameterDescriptor>` with `enums.values[]` now filled.

### Picking the value to assign

**Rule (bind-as-literal).** For any parameter or subfield whose `enums.values[]` was resolved by `GET /services/data/vXX.0/flowbuilder/action/invocable-action-parameter-enum-values`:

> Bind the chosen `value` **directly** at the action's `inputParameters[].value` (or the Transform's mapped value, for an Apex wrapper subfield) as a `{ "stringValue": "..." }` literal. **Do not** wrap it in a flow variable, formula, or constant first.

The enum's `value` field (not its `label`) is what gets written. Pick exactly one entry from the resolved set.

#### Right vs. wrong

```json
// RIGHT — enum value pinned as a literal at the action input
"variables": [],
"inputParameters": [
  { "name": "connection", "value": { "stringValue": "Quickbooks1t2" } }
]

// WRONG #1 — variable indirection for a value known at design time
"variables": [{ "name": "QB_Connection_Id", "dataType": "String",
                "value": { "stringValue": "Quickbooks1t2" }, "isInput": true }],
"inputParameters": [
  { "name": "connection", "value": { "elementReference": "QB_Connection_Id" } }
]

// WRONG #2 — picking the label instead of the value
"inputParameters": [
  { "name": "connection", "value": { "stringValue": "t2" } }   // label, not value
]

// WRONG #3 — hard-coded from documentation when the live tool returned a set
"inputParameters": [
  { "name": "connection", "value": { "stringValue": "QBO_PROD_TROPICAL_2" } }
]
```

#### Workflow

1. After `GET /services/data/vXX.0/flowbuilder/action/invocable-action-details` flags a parameter/subfield with `dependsOn[]` and `status: "NOT_ENOUGH_INFO"`, resolve any upstream paths first.
2. Call the enumerated-values tool with the resolved values in `inputParamsJson` and the target path in `requestedParamsJson` (both JSON-encoded strings).
3. From the returned descriptor, read `enums.values[]` (top-level) or the matching `subfieldEnums[i].enums.values[]`.
4. Choose **exactly one entry's `value`** (not `label`) and bind it per the rule above.
5. If multiple entries are returned and the user has not specified which to use, pick the first entry and note the choice in your output so the user can override.

#### When the rule does NOT apply

- **User specifies a literal not in the set.** Trust the user's value. Still call the enumerated-values tool if you need to verify the value is in the set before binding.
- **Value must vary at runtime.** If the value genuinely depends on caller input, prior flow data, or a computed expression, use `elementReference` to a variable, formula, or upstream element output. The rule only forbids indirection for *known-at-design-time* literals.
- **Upstream dependency unresolvable.** If the upstream input itself is a flow variable whose value isn't known at design time, skip enum resolution for the dependent subfield — leave it unset. `subfieldEnums` validation is design-time guidance, not a save-time requirement.

#### Why this matters

- The enum set is **org-specific** (named-connection IDs, dependent record types, configured options). Only the live tool reflects what this org accepts.
- Indirection adds noise to the metadata and obscures the design intent: a literal pinned at the input documents itself.


## Metadata Shape

Elements of this type live in `metadata.actionCalls[]`. Each entry:

| Field | Type | Required | Notes |
|---|---|---|---|
| `name` | string | yes | dev-name; unique; ≤ 80 chars |
| `label` | string | yes | display label |
| `actionName` | string | yes | action API name (`emailSimple`, `<MyApexClass>`, etc.) |
| `actionType` | string | yes | one of ~70 enum values (e.g. `apex`, `emailSimple`, `emailAlert`, `flow`, `chatterPost`, `submitForApproval`) |
| `nameSegment` | string | derived | mirrors `actionName` |
| `inputParameters` | array | yes | resolved from `getInvocableActionDetails` |
| `outputParameters` | array | conditional | `[]` when `storeOutputAutomatically: true` |
| `storeOutputAutomatically` | boolean | no | omit when the org doesn't support automatic output handling |
| `connector` | Connector | yes | single outgoing edge |
| `faultConnector` | Connector | conditional | Mandatory for fault-capable actions, except in a marketing flow (only when the user asks for error handling); apply the action-specific persisted shape first |
| `timeoutConnector` | Connector | conditional | async-with-timeout actions only |
| `flowTransactionModel` | string | yes | `"Automatic"`, `"CurrentTransaction"`, or `"NewTransaction"` — always emitted; no default |
| `actionCallPaths` | array | conditional | multi-path actions (e.g. `EinsteinDecidePath`) |
| `timeoutPathUsage` | string | conditional | `"EnableTimeoutPath"` for async-with-timeout |
| `dataTypeMappings` | array | conditional | One entry per generic placeholder; emit only when the action describe returns non-empty `genericTypes[]` |

### `dataTypeMappings` Entry Shape

| Field | Type | Required | Notes |
|---|---|---|---|
| `typeName` | string | conditional | placeholder name from `genericTypes[].name`; required unless `valueMappingKey` is set (XOR) |
| `typeValue` | string | conditional | concrete sObject API name (`Account`, `Custom__c`); one-of {`typeValue`, `apexClass`, `schemaUri`} |
| `apexClass` | string | conditional | concrete Apex class API name; one-of {`typeValue`, `apexClass`, `schemaUri`} |
| `schemaUri` | string | conditional | remote schema URI; one-of {`typeValue`, `apexClass`, `schemaUri`} |
| `valueMappingKey` | string | conditional | value-mapping variant; XOR with `typeName` |
| `valueMappingTarget` | string | conditional | required when `valueMappingKey` is set; must not equal `valueMappingKey` |
| `valueMappingTransformType` | `FlowValueMappingType` | conditional | required when `valueMappingKey` is set |

### `dataTypeMappings` Examples

One entry per placeholder from `genericTypes[]`. Pick the value field by what the resolved type actually is — never guess, always resolve via `GET /services/data/vXX.0/flowbuilder/action/invocable-action-generic-type-enum-values` first (see [Generic-Type Placeholders](#generic-type-placeholders-u__-t__)).

```json
// Apex class resolved — use apexClass
"dataTypeMappings": [
  { "typeName": "U__output", "apexClass": "MyNamespace__SomeApexWrapper" }
]

// sObject resolved — use typeValue
"dataTypeMappings": [
  { "typeName": "T__body", "typeValue": "Account" }
]

// remote schema resolved — use schemaUri
"dataTypeMappings": [
  { "typeName": "T__request", "schemaUri": "AutomationSchema:SchemaAction/schemaType" }
]

// multiple placeholders on one action — resolve and emit every one
"dataTypeMappings": [
  { "typeName": "T__issueType", "apexClass": "JiraV2__IssueTypeWrapper" },
  { "typeName": "T__project",   "typeValue": "Custom_Project__c" }
]

// value-mapping variant — valueMappingKey XOR typeName
"dataTypeMappings": [
  {
    "valueMappingKey": "SourceField__c",
    "valueMappingTarget": "TargetField__c",
    "valueMappingTransformType": "DirectMap"
  }
]
```

Wrong vs. right — the two mistakes that produce the vague top-level rejection or a silent generic-placeholder leak:

```jsonc
// WRONG — field name typo'd; server rejects the whole flow generically
"dynamicTypeMappings": [{ "typeName": "U__output", "apexClass": "MyClass" }]

// WRONG — two value variants set at once (must be exactly one)
{ "typeName": "U__output", "apexClass": "MyClass", "typeValue": "Account" }

// WRONG — unresolved placeholder string left as the value
{ "typeName": "U__output", "apexClass": "U__output" }

// RIGHT — one field name, one value variant, concrete resolved value
{ "typeName": "U__output", "apexClass": "MyNamespace__SomeApexWrapper" }
```

### Key rules

- **`faultConnector` is mandatory for fault-capable actions.** Action calls can fail at runtime (DML, callout, governor limits). Apply the action-specific persisted shape before this generic rule. In a marketing flow, emit it only when the user asks for error handling (see [Fault Path](#fault-path)).
- **`actionType: "flow"` is forbidden** — calling a subflow via `actionCalls` with `actionType: "flow"` has subtly different semantics. Always use top-level `subflows[]` instead.
- **`storeOutputAutomatically: true` ⇒ `outputParameters: []`.** If the org does not support automatic output handling, omit `storeOutputAutomatically` entirely and populate `outputParameters` manually.
- **`actionType: "emailAlert"` forces `storeOutputAutomatically: false** regardless of org settings.
- **Generic types** (placeholders starting with `U__` or `T__`): if `genericTypes[]` from the action drill-down is non-empty, EVERY entry must be resolved to a concrete type and emitted as a `dataTypeMappings[]` row before saving. The placeholder `name` (e.g. `T__body`, `U__output`) goes verbatim into `dataTypeMappings[].typeName`; the resolved concrete value goes into exactly one of `typeValue` (sObject) / `apexClass` / `schemaUri`. Parameters whose `apexClass`, `sobjectType`, or `schemaUri` field equals the placeholder name are pointing at that mapping — their input shape comes from the resolved class/sObject/schema. Leaving any `U__*` / `T__*` string in saved metadata causes a server rejection. Resolve via `GET /services/data/vXX.0/flowbuilder/action/invocable-action-generic-type-enum-values`; if its `typeProviders.status` is `ERROR` (managed-package / external-system failure on this org), fall back to the static apex catalog (`GET /services/data/vXX.0/flowbuilder/resource/apex-types`) to find the corresponding per-ESR materialized class (e.g. `ExternalConnect.<ESR>_<action>MetadataProvider...` for External Connector actions).
- **Enum-resolved values bind as literals.** When a value comes from `GET /services/data/vXX.0/flowbuilder/action/invocable-action-parameter-enum-values`, write it directly at `inputParameters[].value` as `{ "stringValue": "..." }`. Do not introduce a `String` variable just to hold the enum value and reference it via `elementReference` — see "Picking the value to assign" above for the right/wrong examples.
- **Async-with-timeout** actions emit `connector` + `timeoutConnector` + `timeoutPathUsage: "EnableTimeoutPath"`.
- **Multi-path actions** (e.g. `EinsteinDecidePath`) emit `actionCallPaths[]`. The `pathName === "DEFAULT"` entry corresponds to the regular `connector`; non-default paths live only in `actionCallPaths[]`.
- **`dataTypeMappings` only on generic actions.** When `genericTypes[]` is empty, omit the field (or emit `[]`); a stray entry is rejected. One entry per non-`NamedAutomationSchema` placeholder; `NamedAutomationSchema` is the only optional case. **Every emitted `typeName` MUST equal one of the action's `genericTypes[].name` placeholder strings verbatim — never an output- or param-name (e.g. `SuccessMessage`); a name that matches no declared placeholder is rejected at save (see § Save-time rejections).**
- **One value variant per `dataTypeMappings` entry.** Exactly one of `typeValue` / `apexClass` / `schemaUri`; values must be concrete (no `U__*` / `T__*` strings).
- **`typeName` XOR `valueMappingKey`.** Value-mapping entries also require `valueMappingTarget` + `valueMappingTransformType` and `key != target`.
- **Dynamic types require process-type support and API version ≥ 48.0.**

### `flowTransactionModel` is action-specific

`flowTransactionModel` is always emitted. For the actions below specifically,
**do not copy a value across actions** — each rejects one of the two values,
and copying the wrong one fails validation with
`ACTIONCALL_TRANSACTION_MODEL_NOT_ALLOWED`. Check the target action before
binding:

| Action | Allowed `flowTransactionModel` |
|---|---|
| `sendEmailMessage` (UMS email) | `Automatic` |
| `emailSimple` (stock Send Email) | `CurrentTransaction` only (rejects `Automatic`) |
| `sendSmsMessage` (E360) | `CurrentTransaction` (supports `Automatic` too) |
| `exitIndividualsFromFlow` | `CurrentTransaction` (rejects `Automatic`) |
| LWC local actions (`lwcComponent`) | `CurrentTransaction` |

Extend this table as new actions are verified. For any action not listed
here, check the describe's `allowsTransactionControl`: when `true`, either
`Automatic` or `CurrentTransaction` is generally accepted (verify against the
specific action); when `false`, **omit `flowTransactionModel` entirely** —
emitting it against an action that doesn't support transaction control produces invalid
action metadata (e.g. `sendConversationMessages`, see
[Conversation Messaging Action](#conversation-messaging-action)).

### Save-time rejections

- `Required input parameter '<name>' is missing`
- `Output parameter '<name>' is not valid for this action when storeOutputAutomatically is true`
- `Action '<actionName>' of type '<actionType>' not found`
- Unresolved `U__input` / `U__output` placeholders in saved metadata
- `Connector '<name>' not found` (HTTP Callout / named credential)
- `dataTypeMappings` entry missing `typeName` / `valueMappingKey`, or with both set
- `dataTypeMappings` entry with multiple of `typeValue` / `apexClass` / `schemaUri`
- `dataTypeMappings` `typeValue` / `apexClass` / `schemaUri` not resolvable in this org
- `valueMappingKey` set without `valueMappingTarget` or `valueMappingTransformType`, or `key == target`
- Dynamic types not supported by this process type, or API version < 48.0
- **Generic top-level `{"errorCode":"ILLEGAL_QUERY_PARAMETER_VALUE","message":"The flow property is not a valid flow definition."}`** — unlike the specific errors above, this gives no field name or reason. Seen when an `actionCalls[]` entry uses a wrong/misspelled top-level field name (e.g. `dynamicTypeMappings` instead of `dataTypeMappings`) — the payload isn't recognized as a valid flow shape at all, so it fails generically instead of naming the bad field. If a save rejects with this vague error and everything else looks right, binary-search the payload (trim elements down via `saveType: "createNewFlow"` on a minimal copy) to isolate which top-level field name is wrong, rather than guessing at content-level fixes.

### Fixing repeated validation failures — resolve, don't retry blind

When `validate_flow`/`POST /services/data/vXX.0/flowbuilder/flow/actions/save` returns an error tied to a specific element, resolve it with the matching MCP discovery tool before re-submitting the same payload:

| Error signals | Fix by calling |
|---|---|
| `DYNAMIC_TYPE_MAPPING_MISSING` | `GET /services/data/vXX.0/flowbuilder/action/invocable-action-generic-type-enum-values` — resolve the named placeholder to a concrete `apexClass`/`typeValue`/`schemaUri`, emit `dataTypeMappings[]` |
| `ACTIONCALL_INVALID_ISWAITUNTILCOMPLETED` / `ACTIONCALL_MISSING_OFFSET` | No lookup needed — the action's `isAsync: true` from `GET /services/data/vXX.0/flowbuilder/action/invocable-action-details` already told you to add `isWaitUntilCompleted`/`offset`/`offsetUnit` |
| Unresolved dependent enum (`NOT_ENOUGH_INFO` on a param) | `GET /services/data/vXX.0/flowbuilder/action/invocable-action-parameter-enum-values` |
| `Action '<name>' of type '<type>' not found` | Re-run `dispatch_readonly(method: "GET", url: "/services/data/vXX.0/flowbuilder/action/invocable-actions")` with the flow's exact `processType`/`triggerType` — the action may be filtered out for this context |

Re-validate after each targeted fix rather than changing multiple guessed fields at once — each error usually names exactly one field or one missing declaration.

**Stray / mismatched `dataTypeMappings` value — verbatim platform errors.** Both fire on an action-call carrying a `dataTypeMappings[]` entry whose `typeName` is not a real `genericTypes[].name` placeholder — most often an output- or param-like name (e.g. `SuccessMessage`) emitted on a **non-generic** action (empty `genericTypes[]`):

| Platform error (verbatim) | Cause | Fix |
|---|---|---|
| `In Apex action "<label>", type mapping "<X>" is not a supported type.` | Value `<X>` doesn't resolve to a real type (stray / placeholder-looking). | Remove the mapping if the action is non-generic; else set a concrete value for the matching generic param. |
| `Data type mapping "<X>" isn't referenced in action "<apiName>".` | `typeName` matches no generic param (e.g. a mapping on a non-generic action). | Remove the stray mapping; only map declared `genericTypes[].name`. |

Either string can fire depending on the stray value: an unresolvable value trips *is not a supported type*; a resolvable-but-unreferenced value trips *isn't referenced in action*. See § Key rules (the `dataTypeMappings` hard guard) and `validators.md`.

**Missing mapping when the action IS generic — the inverse failure.** The mapping is not merely optional-when-present: when `GET /services/data/vXX.0/flowbuilder/action/invocable-action-details` returns a **non-empty `genericTypes[]`**, a `dataTypeMappings[]` entry is **required** for every non-`NamedAutomationSchema` placeholder, and the flow will **not save** until each is set to a concrete type. This is the "generic type wasn't set when it should have been" case:

| Platform error | Cause | Fix |
|---|---|---|
| `Enter a value for data type mapping "<placeholder>" in Apex action "<label>".` (Core label `ActionCallDataTypeMappingMissing`; the generic **Data type mapping required** validator in `validators.md` — *"The action requires a data type mapping."* — covers the same save-blocking condition). | The action's describe has a non-empty `genericTypes[]`, but the action call emits no matching `dataTypeMappings[]` entry — or leaves an unresolved `U__*` / `T__*` placeholder string in the saved metadata (see the *Unresolved `U__input` / `U__output` placeholders* entry above). | Emit one `dataTypeMappings[]` entry per placeholder: set `typeName` to the `genericTypes[].name`, and exactly one of `typeValue` (sObject) / `apexClass` (Apex class) / `schemaUri` to the concrete type resolved via `GET /services/data/vXX.0/flowbuilder/action/invocable-action-generic-type-enum-values`. |

Rule of thumb (both directions): `dataTypeMappings` presence tracks `genericTypes[]` — **each non-`NamedAutomationSchema` placeholder in a non-empty `genericTypes[]` requires a mapping; `NamedAutomationSchema` placeholders (e.g. `ContentSchema`) stay optional and may be omitted; empty `genericTypes[]` ⇒ no mapping (a stray one is rejected).**

### Activation-time rejections (save succeeds, activate fails)

- `WARNING_BLOCK_ACTIVATION: <elementName> (Action) — A record-triggered flow can't execute actions that make external callouts in a path that runs immediately. Remove this element from the flow, or move it to a scheduled path.` — emitted when `hasCallout: true` action sits on the immediate path of a record-triggered flow. Move the action under a `scheduledPaths[]` entry on the Start element to clear.

## JSON Example

```json
{
  "name": "Send_Welcome_Email",
  "label": "Send Welcome Email",
  "locationX": 200,
  "locationY": 100,
  "actionType": "emailSimple",
  "actionName": "emailSimple",
  "nameSegment": "emailSimple",
  "flowTransactionModel": "CurrentTransaction",
  "storeOutputAutomatically": true,
  "inputParameters": [
    { "name": "emailAddresses", "value": { "elementReference": "varRecipient" } },
    { "name": "emailSubject", "value": { "stringValue": "Welcome" } },
    { "name": "emailBody", "value": { "elementReference": "tplWelcome" } }
  ],
  "outputParameters": [],
  "connector": { "targetReference": "end_path", "isGoTo": false },
  "faultConnector": { "targetReference": "Log_Error", "isGoTo": false }
}
```

## Exit from a Flow (`exitIndividualsFromFlow`)

Add this element to `metadata.actionCalls[]`. Never add it to `metadata.subflows[]`.

This action is supported only in a Segment-triggered marketing flow. Load `../start/segment-triggered.md` and follow its process-type, segment-binding, schedule, data-space, timezone, and data-graph rules before authoring this action. Do not reuse the Exit action's target flow as the authoring segment unless the user explicitly asked for that configuration.

1. If no resource containing the Data Cloud Individual ID is named, ask for that resource and stop. Do not perform discovery, author an action, validate, or save until the answer identifies a real flow resource.
2. Call `dispatch_readonly(method: "GET", url: "/services/data/vXX.0/flowbuilder/action/invocable-action-details", queryParams: { actionName: "exitIndividualsFromFlow", actionType: "exitIndividualsFromFlow" })` before emitting metadata. This special action may not appear in the generic invocable-action catalog, so do not treat catalog omission as proof that it is unsupported.
3. Call `dispatch_readonly(method: "GET", url: "/services/data/vXX.0/flowbuilder/flow/subflows", queryParams: { subflowFilterType: "MARKETING" })` to discover eligible targets. Match a named target by `fullName` or `label`; when the user did not name one, ask them to choose from the filtered results. Never select a record-triggered, screen, or scheduled flow. Treat running-version status as unverified until the action describe, save, activation, or runtime response confirms it.
4. Bind `inputParameters[].value.elementReference` for `IndividualId` to the confirmed real flow resource. Never emit a placeholder value.
5. Add a `faultConnector` only if the user asks for error handling; a Segment flow is a marketing flow (see [Fault Path](#fault-path)). When asked, route it to a real named handler, such as a `Capture_Exit_Fault` Assignment that stores `$Flow.FaultMessage` in a Text variable; no bare end element exists. Because a Segment flow is headless, a bare capture is in-memory-only — for observability, follow it with a persistence/notification step (advisory; see `shared/fault-paths/fault-paths.md` § Observable vs. In-Memory-Only Fault Handling). Handle failures caused by an unsupported target type, no running target version, or missing user access.

Ask which target flow to exit when it is not named. Ask whether to exit one running version or all running versions of that target. Ask for the resource that contains the Data Cloud Individual ID when no existing resource is named.

**Required-input preflight:** if the target flow is named but no `IndividualId` source is named, ask only: "Which flow resource contains the Data Cloud Individual ID for the customer?" Stop and wait for that answer. Never invent a literal, use `PLACEHOLDER`, or substitute a CRM User, Contact, or Account ID.

Never emit `exitFromFlow`, `exitJourney`, `removeFromFlow`, `exitFlowParticipant`, or a `FlowInterview` query/delete. Emit only `actionType: "exitIndividualsFromFlow"` for this behavior.

Never place this action after Create, Update, or Delete Records in the same transaction: the action rejects pending DML. Put the exit on a process-type-supported separate transaction boundary, then confirm the resulting flow structure. `flowTransactionModel: "CurrentTransaction"` does not create a boundary.

| Version scope | `actionName` | `FlowVersionId` |
|---|---|---|
| All running versions | Selected target flow API name | Leave unset or empty |
| One running version | Selected target flow API name | Set to a running version ID returned for that target |

Set `actionType: "exitIndividualsFromFlow"`. Set `actionName` to the selected target flow API name. Set `flowTransactionModel: "CurrentTransaction"`; this action rejects `"Automatic"`. Do not persist `FlowApiName` or `flowApiName`; the editor uses it only as a synthetic selector. Do not use `nameSegment` as target-flow identity.

Set `storeOutputAutomatically: true` and `outputParameters: []` when automatic output handling is available. Otherwise, resolve the live types before assigning `ExitStatuses`, `FlowVersionId`, `isSuccess`, or `IndividualId` manually.

Treat a successful draft-save as insufficient evidence of activation or runtime support. Report feature-gate, target-flow-type, and user-permission failures from the describe, save, activation, or runtime response.

Use `examples/exit-from-flow.json` as an `actionCalls[]` fragment. Add the referenced `IndividualId` resource and `connector.targetReference` success target to the complete flow. The fragment has no `faultConnector`; add one and its handler only when the user asks for error handling. Replace the example target names with real elements in the authored flow.

## Send to Journey (`sendToJourney`)

Before authoring this action, load `send-to-journey.md` and follow it. That file
owns business-unit and Journey selection, Journey Builder-context DE schema
resolution, required-field mapping, and the persisted action shape.

## LWC Local Actions (`actionType: "lwcComponent"`)

A handful of stock actions run **client-side in the browser** rather than as a server callout. In the metadata they are still `actionCalls[]` entries, distinguished by `actionType: "lwcComponent"`. The two most common are:

| Action (`actionName` / `nameSegment`) | What it does |
|---|---|
| `flowruntime:showToastMessage` | Pops a Lightning **toast** notification (the "show a success/error message" pattern). |
| `flowruntime:openAPage` | **Navigates** the browser. Opening an external URL (`pageType: "WebPage"`) is verified live; the action also supports other page targets (record, list view, etc.) that are documented but not verified here. |

These are the correct answer when a screen flow needs to *tell the user something* (toast) or *send them somewhere* (open a page) as a step on the canvas — not a screen field. They only work at runtime in a Lightning context (Lightning app/console, a community, the mobile app); they are inert in other runtimes.

### How local actions differ from server actions

- **No `faultConnector`.** They run in the browser with no callout/DML, so there is no fault path — omit it entirely. The server neither requires nor auto-adds one; verified live.
- **No output.** Always `storeOutputAutomatically: false` and `outputParameters: []` — nothing comes back into the flow.
- `flowTransactionModel: "CurrentTransaction"`, `isWaitUntilCompleted: false`.
- The component must exist in the org. `flowruntime:showToastMessage` and `flowruntime:openAPage` are stock and surface via `getDynamicInvocableActionsForType` (type `lwcComponent`), so they are available in Screen flows without any deploy.
- Input values accept literals or merge fields exactly like any other action — e.g. a toast body of `"Hello {!userName}, your flow ran successfully."` interpolates a screen input at runtime.

### `flowruntime:showToastMessage` inputs

| Param | Type | Notes |
|---|---|---|
| `toastMessageTitle` | string | Bold heading of the toast. Optional. |
| `toastMessageBody` | string | Body text; supports merge fields. Optional. |
| `dismissalMethod` | string | `"Auto"` (auto-fades) or `"Manual"` (user must close). |
| `toastMessageStyle` | string | `"Information"`, `"Success"`, `"Warning"`, or `"Error"` — drives icon/color (all four verified live). The value is enforced by the component, not at save/activate, so stick to these four. |
| `toastMessageBodyLinks` | Apex | Optional embedded links (advanced; usually omitted). |

> The builder's CPE may add `"inputConfiguratorMode": "Custom"` onto the `toastMessageStyle` value object when you edit it in the UI. It is **not required** — a plain `{ "stringValue": "Success" }` saves and activates fine.

### `flowruntime:openAPage` inputs

| Param | Type | Notes |
|---|---|---|
| `pageType` | string | The navigation target kind. Only `"WebPage"` is verified here; other kinds (record, list view, etc.) exist but were not probed and likely take their own companion params — confirm against `getInvocableActionDetails` before relying on them. |
| `webPageUrl` | string | The URL to open when `pageType` is `"WebPage"` (verified). |

### JSON Example (verified: saves AND activates)

Chained on a screen flow — `Start → Screen → Show_Toast → Open_Page → End`:

```jsonc
{
  "name": "Show_Toast",
  "label": "Show Toast",
  "actionType": "lwcComponent",
  "actionName": "flowruntime:showToastMessage",
  "nameSegment": "flowruntime:showToastMessage",
  "flowTransactionModel": "CurrentTransaction",
  "storeOutputAutomatically": false,
  "isWaitUntilCompleted": false,
  "inputParameters": [
    { "name": "toastMessageTitle", "value": { "stringValue": "Welcome!" } },
    { "name": "toastMessageBody",  "value": { "stringValue": "Hello {!userName}, your flow ran successfully." } },
    { "name": "dismissalMethod",   "value": { "stringValue": "Auto" } },
    { "name": "toastMessageStyle", "value": { "stringValue": "Success" } }
  ],
  "outputParameters": [],
  "connector": { "targetReference": "Open_Page" }
  // no faultConnector — client-side action
}
```

```jsonc
{
  "name": "Open_Page",
  "label": "Open Page",
  "actionType": "lwcComponent",
  "actionName": "flowruntime:openAPage",
  "nameSegment": "flowruntime:openAPage",
  "flowTransactionModel": "CurrentTransaction",
  "storeOutputAutomatically": false,
  "isWaitUntilCompleted": false,
  "inputParameters": [
    { "name": "pageType",   "value": { "stringValue": "WebPage" } },
    { "name": "webPageUrl", "value": { "stringValue": "https://www.salesforce.com" } }
  ],
  "outputParameters": [],
  "connector": { "targetReference": "END_Flow" }
}
```

## `contentId` Rule (Marketing Messaging Actions)

Applies to `sendEmailMessage`, `sendMobileAppMessage`, `sendMobileAppInAppMessage`, `sendRcsMessage`, `sendSmsMessage`, `sendWhatsAppMessage`.

- **Never fabricate or guess a `contentId`.** An unresolvable value hard-fails the save (`Invalid Managed Content Key!`).
- **Discover SMS, RCS, and email content before omitting `contentId`.** Follow the CMS workflow below whenever `dispatch_readonly` is available (all CMS reads route through it). For `sendEmailMessage`, see [CMS discovery for Email](#cms-discovery-for-email-sendemailmessage).
- **Bind only a resolved FQN.** Pass the selected CMS row's `managedContentId` to `GET /services/data/vXX.0/flowbuilder/messaging/content-fqn`, then bind its non-empty `contentFqn` as `{ "stringValue": "<contentFqn>" }`.
- **Omit unresolved content.** Omit `contentId` only when CMS discovery is unavailable, returns no eligible row, or `GET /services/data/vXX.0/flowbuilder/messaging/content-fqn` returns no FQN. State that activation remains blocked; never substitute the CMS content key, variant ID, title, URL name, or raw `managedContentId`.

### CMS discovery for SMS and RCS

All CMS reads go through `dispatch_readonly`
against the CMS Connect API (`/connect/cms/...`) and SOQL (`/query`). There is no
`content-readonly` server. Steps 1, 3, and 4 issue the `dispatch_readonly` reads that replace it
(steps 2 and 5 are decision/filter steps with no tool call); the channel-delivery
read in step 4 is the authoritative **channel-publication** proof.

1. Select the Marketing **content space (workspace)**. SOQL is the fast path:
   `dispatch_readonly({ url: "/services/data/vXX.0/query", method: "GET", queryParams: { q: "SELECT Id, Name FROM ManagedContentSpace" } })` →
   `records[]`, each `{Id, Name}` (e.g. `"Content Workspace for Marketing Cloud"`).
   (Equivalent Connect read: `GET /connect/cms/spaces`.) Ask the user to choose
   when multiple marketing workspaces match and the request does not identify one.
2. Pick the content-type FQN matching your action's channel — **do not hardcode
   blindly:** `sfdc_cms__sms` for SMS; `sfdc_cms__multiChannelContent` (RCS) for
   RCS; `sfdc_cms__email` for email (`sendEmailMessage`). It becomes the
   `contentTypeFQN` filter in step 4; if no content of that type surfaces in the
   step-4 delivery read, stop — the workspace has none (this is where the old
   "content type absent" fail-fast now surfaces).
3. Resolve the messaging **delivery channel**:
   `dispatch_readonly({ url: "/services/data/vXX.0/connect/cms/spaces/<0Zu spaceId>/channels", method: "GET" })` →
   `spaceChannels[]`, each `{channelSummary: {id (0ap…), name, type}}`. Select the
   channel whose `name` is exactly `Marketing Messages`. If no channel or multiple
   channels match, ask the user to select one by channel name and ID.
4. Read **published content from the delivery channel** — this is the
   publication proof:
   `dispatch_readonly({ url: "/services/data/vXX.0/connect/cms/delivery/channels/<0ap channelId>/contents", method: "GET", queryParams: { contentTypeFQN: "<type>", page: "0", pageSize: "250" } })` →
   `contents[]`, each `{managedContentId, contentKey, contentType.fullyQualifiedName, publishedDate, title, urlName}`. A row here **is** channel-published (it carries a `publishedDate`).
   - When the user names content or supplies keywords, filter these results by
     `title`, or use the channel search route
     `GET /connect/cms/delivery/channels/<channelId>/contents/search` (or
     `/query`) with the same `contentTypeFQN`.
   - A `ManagedContent` SOQL lookup (`SELECT Id, Name, ContentKey, ContentTypeFullyQualifiedName FROM ManagedContent WHERE ContentTypeFullyQualifiedName = '<type>' AND Name = '<title>'`) is a fast name→`managedContentId` path, but `ManagedContent` carries **no publication status** — never bind a row that does not also appear in this channel `contents[]`.
   - Page with `page` from `0` and `pageSize` `1`–`250`. Stop after the first
     empty `contents` collection; do not rely on `nextPageUrl` alone (it can stay
     populated after an empty page).
5. Require published content. Match a requested title exactly; select one exact
   match automatically, ask among multiple eligible rows, and stop when none
   match. For enumeration, ask the user to choose from the published rows.
6. Read `managedContentId` from the selected row. Do not use its
   `contentKey`, `id` (`9Ps...` variant), `title`, or `urlName` as `contentId`.
7. Call `dispatch_readonly(method: "GET", url: "/services/data/vXX.0/flowbuilder/messaging/content-fqn")` with that `managedContentId`. Require
   a non-empty `contentFqn`, then bind it to the messaging action's `contentId`.
   Make this call for every content item; don't build the FQN yourself from the
   space name and `contentKey`. The last segment is the item's API name, which is
   often the content key for email but not for SMS (for example
   `…sfdc_cms__sms--Welcome_Drip_1`). The org rejects a guessed FQN
   that doesn't exist, even in a Draft flow: `Failed to get content key by FQN: …`
   on save, `We couldn't find the selected content.` on activation.

The Connect routes, SOQL objects, and field names above were verified against a
live org: `ManagedContentSpace`/`ManagedContent` SOQL, `spaceChannels[]` with
`channelSummary.{id,name,type}`, and delivery `contents[]` with `managedContentId`,
`contentKey`, `contentType.fullyQualifiedName`, and `publishedDate`.

Read authored CMS content rather than electronic media: SMS and RCS message
definitions are non-media managed content. Re-run the selected lookup path
immediately before save and reject a row that is no longer Published.

### CMS discovery for Email (`sendEmailMessage`)

`sendEmailMessage` (UMS marketing email) needs an **email** CMS content item
(`sfdc_cms__email`) — not `sfdc_cms__sms` / `sfdc_cms__multiChannelContent`. The
discovery path mirrors the SMS/RCS workflow above, with two differences:

1. In step 2, require `sfdc_cms__email` as the `contentTypeFQN`.
2. In steps 3–4, do **not** assume a channel name for email — the channel that
   delivers `sfdc_cms__email` varies by org. Identify it by **which channel's
   delivery `contents[]` actually returns `sfdc_cms__email` rows** for the
   step-3 `spaceChannels[]`: run the step-4 read against a candidate channel and
   keep the one whose results include published `sfdc_cms__email` items. (On the
   test org the email items happened to live on the same `Marketing Messages`
   channel as SMS/RCS — treat that as one org's layout, not a default; a distinct
   email channel is equally valid.) If the space-scoped channels read fails, fall
   back to `GET /connect/cms/channels` and filter client-side, still selecting by
   the content-type the channel actually delivers rather than by name.

Everything else is identical: page the delivery-channel `contents[]` from `0`,
require the selected row's `managedContentId` there (its `publishedDate` is the
publication proof), then resolve it with `GET /services/data/vXX.0/flowbuilder/messaging/content-fqn` and bind the
returned `contentFqn` to `contentId`.

A real published `sfdc_cms__email` item resolves to
`marketing--Default_Content_Workspace.sfdc_cms__email--<CONTENT_KEY>` and, once
bound, clears both Content-ID validation warnings on `sendEmailMessage`. Never
fabricate this value; omit `contentId` (activation stays blocked) when no
published email content exists.

## Mobile App Messaging Actions (E360)

Two standard platform invocable actions owned by **E360 Messaging Mobile Push** deliver messages to a mobile app. They are ordinary `actionCalls[]` entries; the agent selects between them by `actionName` alone — there is **no shared action name and no disambiguation logic required**.

| Action | `actionName` (emit verbatim) | Enum (`InvocableActionType`) | Min API | Delivery |
|---|---|---|---|---|
| **Send Mobile App Message** (push notification) | `sendMobileAppMessage` | `SEND_MOBILE_APP_MESSAGE` | 256 | Push |
| **Send Mobile App In-App Message** | `sendMobileAppInAppMessage` | `SEND_MOBILE_APP_IN_APP_MESSAGE` | 262 | In-App |

> Historic confusion: an earlier note claimed `sendMobileAppMessage` was shared between push and in-app. It is not — the two are distinct registered actions with distinct `actionName` strings. Emit the exact name for the channel you want.

### Shared metadata characteristics (both actions)

Both actions are registered with identical builder traits, so the same rules apply to each:

- **Fault path: only when asked in a marketing flow.** Both declare `hasCallout: true` in the action describe, and both can throw at runtime (record operations, callouts, or governor limits). In a marketing flow, add a `faultConnector` only if the user asks for error handling; in any other flow type, always wire one (see [Fault Path](#fault-path)).
- **No output.** Both run in the high-scale flow runtime (not core) and return no data. Emit `storeOutputAutomatically: false` with `outputParameters: []` — do not attempt automatic output handling.
- **Transaction control is supported.** `allowsTransactionControl: true`, `doRollbackOnError: false` — always emit `flowTransactionModel` (no default).
- **Synchronous.** Neither is async; do **not** emit `timeoutConnector` / `timeoutPathUsage`.
- **Custom Property Editor.** Each declares a `configurationEditor`
  (`builder_e360_journeys-send-mobile-app-message-editor` /
  `builder_e360_journeys-send-mobile-app-in-app-message-editor`). In the builder UI the CPE
  replaces the standard parameter list — see [Configuration Editors](#configuration-editors-custom-property-editors). When authoring metadata directly, still resolve parameters from `GET /services/data/vXX.0/flowbuilder/action/invocable-action-details`; the CPE does not change the saved `inputParameters[]` shape.
- **Generic type — `ContentSchema`.** As of core-264 the describe returns a non-empty
  `genericTypes[]` carrying a `ContentSchema` entry, plus an optional `contentSchema` input
  parameter. It is a **design-time authoring aid** for binding values into the selected
  content's variables (merge fields); it is **not consumed by the runtime send path**, so the
  action sends whether or not you map it. Follow the
  [Dynamic Type Mappings](#dynamic-type-mappings-generic-types) rules: resolve it and emit a
  `dataTypeMappings[]` row **if** you want to bind content variables in-flow; otherwise omit it.
  `ContentSchema` resolves to a `NamedAutomationSchema`-typed placeholder in the describe output — it therefore falls under the existing exemption in [Key Rules](#key-rules) ("One entry per non-`NamedAutomationSchema` placeholder; `NamedAutomationSchema` is the only optional case"). You may omit the `dataTypeMappings[]` row for `ContentSchema` without save or activation errors.
- **Callout + record-triggered flows.** Because `hasCallout: true`: these actions **cannot be used in `RecordBeforeSave` flows** (before-save flows have no scheduled path; deployment or activation is blocked). In **`RecordAfterSave` flows**, they must sit on a **scheduled path** (`scheduledPaths[]` on the Start element), not the immediate path — see [Validation Rules and Constraints](#validation-rules-and-constraints).

### Input parameters

Parameters are describe-driven — always fetch the live set with
`GET /services/data/vXX.0/flowbuilder/action/invocable-action-details` before authoring. The core-264 shapes:

**`sendMobileAppMessage` (push)**

| Param | Type | Required |
|---|---|---|
| `mobileAppId` | String | yes |
| `contentId` | String | yes¹ |
| `categoryName` | String | no |
| `contentSchema` | (generic — `ContentSchema`) | no |

¹ Required for activation, not draft save — omit when unknown. See the [`contentId` Rule](#contentid-rule-marketing-messaging-actions) above.

**`sendMobileAppInAppMessage` (in-app)**

| Param | Type | Required |
|---|---|---|
| `mobileAppId` | String | yes |
| `contentId` | String | yes¹ |
| `messageExpirationType` | String | yes |
| `messageTrigger` | String | yes |
| `displayStartDatetime` | String | no |
| `displayEndDatetime` | String | no |
| `displayTimezone` | String | no |
| `displayTimezoneOffset` | Double | no |
| `dynamicTimeframe` | Integer | no |
| `dynamicTimeframeUnit` | String | no |
| `priority` | Integer | no |
| `messageDelayDisplay` | Integer | no |
| `messageDelayDisplayUnit` | String | no |
| `displayControl` | String | no |
| `displayRepeatFrequency` | String | no |
| `displayMessageLimit` | Integer | no |
| `messageSuppressionActions` | String | no |
| `contentSchema` | (generic — `ContentSchema`) | no |

### Worked examples

Full `actionCalls[]` entries for both actions live in the example files:

- **Push notification:** `examples/push-notification.json` — `sendMobileAppMessage` with `mobileAppId` / `contentId` / `categoryName`, no output, no `faultConnector` (the marketing-flow default).
- **In-app message:** `examples/in-app-message.json` — `sendMobileAppInAppMessage` adding the required `messageExpirationType` / `messageTrigger`, no output, no `faultConnector` (the marketing-flow default).

> **Note:** These are `actionCalls[]` entry fragments, not complete flows. They reference upstream elements (`Get_Push_Content`, `Get_InApp_Content`) that must exist elsewhere in the flow. Do not paste them verbatim as a standalone flow — supply the matching Get Records element to produce a deployable whole. Add a `faultConnector` and its handler (for example `Log_Send_Error`) only when the user asks for error handling or the flow is not a marketing flow.

### Anti-patterns (agent should reject / flag)

```jsonc
// WRONG #1 (non-marketing flow, or the user asked for error handling) — no fault path. Both actions can throw at runtime.
{ "actionName": "sendMobileAppMessage", "connector": { "targetReference": "END_Flow" } }
// (missing faultConnector)

// WRONG #2 — automatic output on an action that returns nothing.
{ "actionName": "sendMobileAppInAppMessage", "storeOutputAutomatically": true }
// Correct: storeOutputAutomatically: false, outputParameters: []

// WRONG #3 — timeout path on a synchronous action.
{ "actionName": "sendMobileAppMessage",
  "timeoutConnector": { "targetReference": "On_Timeout" },
  "timeoutPathUsage": "EnableTimeoutPath" }
// Neither action is async — omit timeout entirely.

// WRONG #4 — inventing a shared/generic name to "cover both channels".
{ "actionName": "sendMobileMessage" }   // no such action; use the exact channel name
```

> **Verification note.** Metadata above verified against `InvocableActionType.java`,
> `MobileAppParameterUtils.java`, `MobileAppInAppParameterUtils.java`, and the two action
> classes (`InvocableSendMobileAppMessageAction.java`, `InvocableSendMobileAppInAppMessageAction.java`)
> on **core-264** (`p4/264-main`) as of 2026-07. The `ContentSchema` generic type is fully
> wired on both actions (each overrides `getInvocableActionGenericTypeEnumeratedValues()`, with
> unit-test coverage). Per-org, confirm the concrete `ContentSchema` shape and each action's
> available process/trigger types live via `GET /services/data/vXX.0/flowbuilder/action/invocable-action-details` before
> relying on them.

## Send Email Message (E360)

The standard platform invocable action **Send Email Message** (`actionName: sendEmailMessage`) is owned by **E360 Messaging Email** and delivers a marketing/engagement email through the E360 send pipeline. It is an ordinary `actionCalls[]` entry — `actionType`, `actionName`, and `nameSegment` are all the literal string `sendEmailMessage`. Minimum API version **242**. In the builder UI a Custom Property Editor (`configurationEditor: "builder_e360_journeys-send-email-editor"`) replaces the standard parameter list.

### ⚠️ The two fields agents get wrong most often

Both failures are **wrong parameter names**. The product concepts "from address" and "communication subscription" do **not** map to input parameters called `fromAddress` / `communicationSubscription`:

| Product concept | ❌ Name agents wrongly emit | ✅ Real describe parameter(s) | Value shape |
|---|---|---|---|
| Sender / From | `fromAddress` | **`senderId`** | Literal **record Id** — `{ "stringValue": "<Id>" }` only (no references) |
| Consent / subscription | `communicationSubscription` | **`communicationSubscriptionId`** + mandatory **`commSubscriptionChannelTypeId`** | Two literal **record Ids** — both `{ "stringValue": "<Id>" }` |

Three rules that follow from this — internalize them before authoring:

1. **The sender is `senderId`, a record Id — not a free-text email.** `senderId` takes the Id of a configured sender record (see the deep dive below). `fromAddress` **is** a real parameter, but it is a *separate, optional, dynamic-from override* that is **not read on the standard send path** — setting it does not set the sender. `fromAddress`/`fromName`/`replyToAddress`/`replyToName` are only consumed by the E360 dynamic-from/reply feature.
2. **`communicationSubscriptionId` never travels alone.** If you set it you MUST also set `commSubscriptionChannelTypeId`, or activation fails (`COMMUNICATION_SUBSCRIPTION_CHANNEL_TYPE_ID_MISSING`). Both are **record Ids**, not developer names. The bare `communicationSubscription` (no `Id`) is a Flow *Start* parameter and does not exist on this action.
3. **These Ids are NOT in the action describe — look them up.** `GET /services/data/vXX.0/flowbuilder/action/invocable-action-details` returns **no** enumerated values / `dependsOn` for `senderId`, `communicationSubscriptionId`, or `commSubscriptionChannelTypeId` — the builder's picklists come from the CPE, not describe. Bind an Id the user supplies; when the user names the sender or the subscription instead, resolve the name with the reads in [Resolve names to Ids](#resolve-names-to-ids). All three are **literal `{stringValue}` record Ids** — **never fabricate an Id**, and **never** bind them via `elementReference`, including to a Get Records lookup in the flow (see anti-pattern WRONG #2). Omit an unknown one to save a draft (they gate *activation*, not draft save — except `senderId`, see below).

### Shared metadata characteristics

- **Fault path: only when asked in a marketing flow.** The describe reports `hasCallout: true`; the action performs record work + callouts and throws on validation failures. In a marketing flow, add a `faultConnector` only if the user asks for error handling; in any other flow type (for example a record-triggered flow's scheduled path), always wire one (see [Fault Path](#fault-path)).
- **Output.** The action declares a single `messageId` (String) output (populated per recipient). Automatic output handling is therefore available: emit `storeOutputAutomatically: true` with `outputParameters: []`, or switch to manual and assign the `messageId` row. **This differs from the E360 mobile actions, which return nothing.** *(Confirm the org's flow runtime accepts automatic output for this action live via `GET /services/data/vXX.0/flowbuilder/action/invocable-action-details` / a save test — see Verification note.)*
- **Transaction control is supported.** `allowsTransactionControl: true`, `doRollbackOnError: false` — always emit `flowTransactionModel` (no default).
- **Not async.** There is no async trait. The action implements execution *delay* for Send-Time Optimization (`useSto` / `stoTimeFrame`), which is scheduling, not an async wait-for-completion. Do **not** emit `timeoutConnector` / `timeoutPathUsage`.
- **Custom Property Editor.** `builder_e360_journeys-send-email-editor`. As with the mobile actions, the CPE only changes the builder UI — when authoring metadata directly, still resolve parameters from `GET /services/data/vXX.0/flowbuilder/action/invocable-action-details`; the CPE does not change the saved `inputParameters[]` shape.
- **Generic type — `ContentSchema`.** The describe returns a non-empty `genericTypes[]` carrying one `ContentSchema` entry (schema-URI-typed) whose enumerated values depend on `contentId` and start at `status: NOT_ENOUGH_INFO`. It is a **design-time aid** for binding values into the selected content's merge variables; it is **not required to send**. Resolve it (and emit a `dataTypeMappings[]` row) only if you want to bind content variables in-flow; otherwise omit it — the send works without it. `contentId` must be set before the content schema can resolve.
- **Callout + record-triggered flows.** Because `hasCallout: true`: cannot be used in `RecordBeforeSave` flows; in `RecordAfterSave` flows it must sit on a **scheduled path** (`scheduledPaths[]` on Start), not the immediate path — see [Validation Rules and Constraints](#validation-rules-and-constraints).

### Input parameters (describe-driven — always fetch the live set)

Only `contentId` is describe-*required*. Several others are effectively required by **save/activation validation** (flagged below). Full list comes from `GET /services/data/vXX.0/flowbuilder/action/invocable-action-details`; the load-bearing subset:

| Param | Type | Binding | Effectively required? | Notes |
|---|---|---|---|---|
| `contentId` | String | `{stringValue}` literal | **Yes (save)** | Managed Content **FQN** (`marketing--…sfdc_cms__email--<KEY>`), **not** a bare CMS key. Subject/body/template all come from the content record — they are **not** action inputs. See the [`contentId` Rule](#contentid-rule-marketing-messaging-actions). |
| `senderId` | String | `{stringValue}` literal **only** | **Yes (save/activation)** — omitting → `FROM_USER_EMPTY` | The From/sender. Record Id (see deep dive). |
| `communicationSubscriptionId` | String | `{stringValue}` literal | Conditional (see deep dive) | CommSubscription record Id. |
| `commSubscriptionChannelTypeId` | String | `{stringValue}` literal | Required **iff** `communicationSubscriptionId` is set | CommSubscriptionChannelType record Id. |
| `fromAddress` / `fromName` | String | `{stringValue}` **or** `{elementReference}` / merge field | No | Dynamic-from override (feature-gated); **not** the standard sender. |
| `replyToAddress` / `replyToName` | String | reference/merge allowed | No | Dynamic reply-to override. |
| `clickTracking` / `openTracking` | Boolean | literal | No | Tracking toggles. |
| `ccRecipientAddresses` / `isCcEnabled` | String / Boolean | ref allowed / literal | No | CC addresses + toggle. |
| `useSto` / `stoTimeFrame` | Boolean / Integer | literal | No | Send-Time Optimization (delayed execution); `stoTimeFrame` in hours. |
| `isTemplate` | Boolean | literal | No | Distributed Marketing: treat content as template. |
| `locale` | String | Custom/Resource | No | Locale. |
| `timeToLive` | Integer | literal (1–1440 min) | No | **Gated** — only present when the email-TTL gate is on. |
| `contentSchemaParameter` | (generic `ContentSchema`) | nested schema | No | Hidden content merge-variable schema; resolves after `contentId`. |

> Implicit inputs (`individualMember`, `idempotencyKey`, `flowId`, `elementName`, `segmentId`, …) are set by the Flow runtime, not the author — do not emit them.

### `senderId` — the sender (deep dive)

`senderId` is a **literal String record Id** (`{ "stringValue": "<Id>" }`; references are not accepted — it is a configuration parameter). Accepted Id kinds, resolved in this order:

1. **OrgWideEmailAddress (OWEA)** Id — must be **verified** (`OWEA_NOT_VERIFIED` otherwise) and accessible to the user.
2. **SenderEmailAddress** Id — must have an **active EmailDomainKey** (`SENDER_EMAIL_NOT_ACTIVE` otherwise).
3. **User** Id (`005…`) — must be active (`USER_NOT_ACTIVE` otherwise).
4. The **DefaultFromAddress sentinel** string.
5. *(Legacy fallback only)* a raw email string that matches an email regex; anything else → `FROM_USER_UNKNOWN_ERROR` ("Invalid format for from address"). Discouraged — prefer a record Id.

Save/activation validation (`SendEmailMessageActionSaveValidator.validateFromAddress`) runs for all orgs and **throws `FROM_USER_EMPTY` when `senderId` is null** — so although describe marks it optional, it is effectively required. Additional cross-checks: E360 standalone orgs require the resolved address to be **DKIM-authenticated** (`EMAIL_ACTIVE_DKIM_REQUIRED`); with Business Units enabled, the from-domain must match the flow's business unit.

```json
{ "name": "senderId", "value": { "stringValue": "0D2XXXXXXXXXXXXXXX" } }
```

Optional dynamic-from override (only when that feature is enabled — does **not** replace `senderId`):

```json
{ "name": "fromAddress", "value": { "elementReference": "Get_Contact.Email" } }
```

### `communicationSubscriptionId` + `commSubscriptionChannelTypeId` — consent (deep dive)

- `communicationSubscriptionId` is a **`CommSubscription` record Id** (literal). `commSubscriptionChannelTypeId` is a **`CommSubscriptionChannelType` record Id** (literal). Both are Ids, **not** developer names.
- **Companion rule:** setting `communicationSubscriptionId` without `commSubscriptionChannelTypeId` fails with `COMMUNICATION_SUBSCRIPTION_CHANNEL_TYPE_ID_MISSING`. Emit both or neither.
- **Conditional requiredness:** enforced only on **E360 standalone orgs**, at save and activation. When `communicationSubscriptionId` is null the validator checks whether the content's message purpose requires consent under the org's UMA config — promotional/commercial content typically **requires** it (`COMMUNICATION_SUBSCRIPTION_REQUIRED`); transactional content typically does not. When unknown, omit it (draft saves); supply it before activation for promotional sends.
- **Dependency:** comm-sub validation derives the email messaging channel from `senderId`, and the `commSubscriptionChannelType` must resolve to the **email** engagement channel type — so `senderId` must be valid for comm-sub validation to pass.

```json
{ "name": "communicationSubscriptionId",   "value": { "stringValue": "0LnXXXXXXXXXXXXXXX" } },
{ "name": "commSubscriptionChannelTypeId", "value": { "stringValue": "0LpXXXXXXXXXXXXXXX" } }
```

### Resolve names to Ids

A request usually names the email, the sender and the subscription ("send our Spring Sale email from Jordan Lee with consent from our Newsletter subscription") instead of giving Ids. Resolve each name with a read-only lookup before you write the action, then bind the Id you found as a literal. Match names exactly. If a name matches nothing, or matches more than one record, ask the user; never pick a near match or fall back to a default.

| The user names | Look it up | Bind |
|---|---|---|
| The email | [CMS discovery for Email](#cms-discovery-for-email-sendemailmessage): the published `sfdc_cms__email` row whose `title` is the name, then `GET /services/data/vXX.0/flowbuilder/messaging/content-fqn` with its `managedContentId` | `contentId` = the returned `contentFqn` |
| The sender | Run all three SOQL lookups: `SELECT Id, DisplayName, Address FROM OrgWideEmailAddress WHERE DisplayName = '<name>' OR Address = '<name>'`, `SELECT Id, DisplayName FROM SenderEmailAddress WHERE DisplayName = '<name>'` and `SELECT Id, Name, Email FROM User WHERE Name = '<name>' AND IsActive = true`. Bind only when exactly one record matches across all three. If several match (for example an org-wide address and a User both named "Jordan Lee") or none do, ask the user and list each candidate's type, name and address. If the user names the sender type or gives an Id, look up only that. | `senderId` = that `Id` |
| The subscription | `dispatch_readonly(method: "GET", url: "/services/data/vXX.0/flowbuilder/messaging/communication-subscriptions", queryParams: { channel: "email", contactPointType: "Email" })`. Omit `messagingChannelId` for email: the sender is not a messaging channel, and passing the sender's Id returns an empty list. | The row whose `name` is the name: `id` → `communicationSubscriptionId`, the same row's `channelTypeId` → `commSubscriptionChannelTypeId` |

`GET /services/data/vXX.0/flowbuilder/action/org-wide-email-addresses` lists the org-wide addresses the running user may send from as plain address strings, without Ids; use the SOQL above for the Id.

### Other cross-parameter rules

- **`contentId` is the single source of subject/body/template** — there is no template-vs-subject/body input choice on this action (contrast the platform `emailSimple` action). Validate the content record exists; never fabricate the key.
- **Promotional content requires an org physical (postal) address** on the org, else `PROMO_EMAIL_WITH_EMPTY_ORG_ADDRESS` at runtime.
- **STO:** when `useSto: true`, `stoTimeFrame` is validated.
- **TTL (gated):** literal must be 1–1440 minutes; flow references skip the save-time range check.

### Worked example

`examples/send-email-message.json` — a full `actionCalls[]` entry with `senderId` (record Id), `contentId`, and the `communicationSubscriptionId` / `commSubscriptionChannelTypeId` pair, `messageId` via automatic output, and no `faultConnector` (the marketing-flow default).

> **Note:** This is an `actionCalls[]` fragment, not a complete flow. `contentId` is bound as a resolved `sfdc_cms__email` **FQN literal** (per the [`contentId` Rule](#contentid-rule-marketing-messaging-actions)) — replace `<CONTENT_KEY>` with the real resolved key; never bind a raw CMS managed-content key or an `elementReference`. In a record-triggered flow it must sit on a scheduled path and needs a `faultConnector` to a handler such as `Log_Send_Error`; in a marketing flow, add one only when the user asks for error handling.

### Anti-patterns (agent should reject / flag)

```jsonc
// WRONG #1 — sender set via a made-up "fromAddress" as a literal email.
{ "actionName": "sendEmailMessage",
  "inputParameters": [ { "name": "fromAddress", "value": { "stringValue": "noreply@acme.com" } } ] }
// Correct: set senderId to a verified OWEA / active SenderEmailAddress / User Id.
//   { "name": "senderId", "value": { "stringValue": "0D2..." } }

// WRONG #2 — senderId bound to a flow reference (it is literal-only), e.g. a variable or a Get Records
// lookup of the sender. Activation fails: The input parameter "Sender ID" cannot contain element references or merge fields.
{ "name": "senderId", "value": { "elementReference": "varSenderId" } }
// Correct: { "name": "senderId", "value": { "stringValue": "0D2..." } } — look the Id up before authoring (§ Resolve names to Ids).

// WRONG #3 — consent field named "communicationSubscription" (no such param here).
{ "name": "communicationSubscription", "value": { "stringValue": "0Ln..." } }
// Correct: use communicationSubscriptionId (+ commSubscriptionChannelTypeId).

// WRONG #4 — subscription Id without its mandatory channel-type companion.
{ "name": "communicationSubscriptionId", "value": { "stringValue": "0Ln..." } }
// (missing commSubscriptionChannelTypeId) → COMMUNICATION_SUBSCRIPTION_CHANNEL_TYPE_ID_MISSING

// WRONG #5 — a developer name instead of a record Id for either consent param.
{ "name": "communicationSubscriptionId", "value": { "stringValue": "My_Newsletter_Sub" } }
// Correct: a CommSubscription record Id.

// WRONG #6 (non-marketing flow, or the user asked for error handling) — no fault path. The action has hasCallout:true and can throw.
{ "actionName": "sendEmailMessage", "connector": { "targetReference": "END_Flow" } }

// WRONG #7 — timeout path on a non-async action.
{ "actionName": "sendEmailMessage",
  "timeoutConnector": { "targetReference": "On_Timeout" },
  "timeoutPathUsage": "EnableTimeoutPath" }
// Not async — omit timeout entirely. Use useSto/stoTimeFrame for send-time optimization.
```

> **Verification note.** Parameter names, types, binding rules, requiredness, cross-parameter
> validation, and builder traits above were verified against **core-264**
> (`gitcore.soma.salesforce.com/core-2206/core-264-public`, ref `p4/264-patch`) on **2026-08-26**
> — `InvocableSendEmailMessageAction.java`, `EmailParameterUtils.java`, `ParameterConstants.java`,
> `SendEmailMessageActionSaveValidator.java`, `CommSubValidator.java`, and the
> `sendEmailMessage()` factory in `InvocableActionType.java`. This is **source-derived, not yet
> live-verified** by a builder save/activate round-trip (unlike the mobile examples). Per org,
> confirm live via `GET /services/data/vXX.0/flowbuilder/action/invocable-action-details` before relying on: (a) the org's
> flow runtime accepting `storeOutputAutomatically: true` for this action, (b) the exact
> describe-surfaced casing of each param, and (c) that the CPE does not hide `senderId` /
> comm-sub params from the direct-metadata describe path.

## Send SMS Message Action (E360)

One standard platform invocable action, owned by **E360 Journeys**, sends an SMS through a Marketing Messaging Action.

| Action | `actionName` (emit verbatim) | Enum (`InvocableActionType`) | Min API | Delivery |
|---|---|---|---|---|
| **Send SMS Message** | `sendSmsMessage` | `SEND_SMS_MESSAGE` | 246 | SMS |

> **Authority.** `examples/send-sms-message.json` records the exact
> `Flow.Metadata` persisted after a hand-built Segment flow was saved as a
> Draft through Flow Builder. It was not activated, so fields observed there
> are not proof of activation requirements. The Flow Builder MCP describe path
> does not currently resolve `sendSmsMessage` on the verified org; do not
> replace the persisted action shape with generic Action defaults.

### Discovery workflow

1. Call `dispatch_readonly(method: "GET", url: "/services/data/vXX.0/flowbuilder/action/invocable-action-details", queryParams: { actionName: "sendSmsMessage", actionType: "sendSmsMessage" })`. If the verified org returns no action, continue with the persisted contract below; do not invent parameters.
2. Resolve `contentId` through the [CMS discovery workflow](#cms-discovery-for-sms-and-rcs) with `contentTypeFQN: "sfdc_cms__sms"`.
3. Call `dispatch_readonly(method: "GET", url: "/services/data/vXX.0/flowbuilder/messaging/sender-sms-codes")`. Omit `businessUnitId` unless you have a
   verified 15- or 18-character Salesforce record ID. A direct Salesforce Core
   Business Unit ID starts with `1QO`; accept another prefix only after
   verifying that the record is related to that Business Unit. Never pass the
   numeric MCE `mid` or the `<EID>-<MID>` selector. Select a returned row and bind its `id` to
   `senderId`; never bind `messagingPlatformKey` or a phone number. Stop when
   the list is empty.
4. Call `dispatch_readonly(method: "GET", url: "/services/data/vXX.0/flowbuilder/messaging/communication-subscriptions")` with `messagingChannelId` set to the
   selected sender row's `id`, `channel: "sms"`, and
   `contactPointType: "Phone"`. Omit `businessUnitRelatedId` unless step 3 used
   a verified 15- or 18-character Salesforce record ID: a direct Business Unit
   ID starting with `1QO`, or another record ID verified as related to that
   Business Unit. Then pass that same Salesforce ID. Never pass an MCE `mid` or
   `<EID>-<MID>` selector.
   Read rows from `communicationSubscriptions[]`. When rows exist, select one
   and bind its `id` to `communicationSubscriptionId` and its `channelTypeId`
   to `commSubscriptionChannelTypeId`. When the list is empty, omit both inputs
   only when the selected content does not require a communication subscription;
   otherwise stop. Never invent either ID.

### Shared metadata characteristics

- **Fault path: only when asked in a marketing flow.** The action declares
  `hasCallout: true` and can fail at runtime. In a marketing flow (the list in
  `../../shared/fault-paths/fault-paths.md`), add a `faultConnector` only if the
  user asks for error handling. In any other flow type, wire one when the live
  action shape supports it. One verified persisted Draft has
  `faultConnector: null`.
- **Emit automatic output exactly.** Set `storeOutputAutomatically: true` and `outputParameters: []`.
- **Output.** Current Core declares `messageId` (String). Automatic output makes
  it available as `{!<actionApiName>.messageId}` without explicit assignments.
- **Emit the observed empty generic mapping.** Set `dataTypeMappings: []`; the
  persisted draft had no resolved generic placeholders.
- **Set transaction control exactly.** Emit `flowTransactionModel: "CurrentTransaction"`.
- **Omit async fields.** Do not emit `isWaitUntilCompleted`, `timeoutConnector`, or `timeoutPathUsage`.
- **Custom Property Editor.** Declares `configurationEditor: "builder_e360_journeys-send-sms-editor"`. In the builder UI the CPE replaces the standard parameter list — see [Configuration Editors](#configuration-editors-custom-property-editors). When authoring metadata directly, bind the parameters below.
- **Never place on `RecordBeforeSave` or `RecordAfterSave`.** Unlike callout actions in general (see [Validation Rules and Constraints](#validation-rules-and-constraints)), `sendSmsMessage` (`hasCallout: true`) is rejected outright on **every** such shape — no scheduled-path placement fixes it.
- **Use a Marketing flow context that exposes the action.** Call `dispatch_readonly(method: "GET", url: "/services/data/vXX.0/flowbuilder/action/invocable-actions")` with the intended `processType`, `triggerType`, `builderType`, and `dataSpace`, and require `sendSmsMessage` in the result before authoring it. This skill fully documents `processType: "AutoLaunchedFlow"` with `start.triggerType: "Segment"` (see `../start/segment-triggered.md`) or `"OnDemandNoTrigger"` (see `../start/start.md` § On-Demand); Core also allows the action for Data Graph Data Change flows, but their Start contract is outside this recipe. Omitting `start.triggerType` makes Core validate the flow as a plain autolaunched flow and can fail with `ACTIONCALL_NOT_SUPPORTED_FOR_PROCESSTYPE`.
- **Do not generalize the surrounding draft.** The hand-built source also
  persisted `environments: ["Default"]`, `areMetricsLoggedToDataCloud: true`,
  `dataGraph`, `schedule.frequency: "OnActivate"`, and an explicit `ends[]`
  target. Preserve those fields when reproducing that source, but do not require
  or invent them for every `sendSmsMessage` flow without live validation.
  When evolving that source in an `AUTO_LAYOUT_CANVAS` flow, give each newly-added
  terminating branch an explicit End (its own or a shared one — both valid); a
  fault pointed directly at an End is silently dropped on reload (not a round-trip
  breaker), so route faults to a handler when you want them kept — see
  `shared/anti-patterns.md` item 38.

### Input parameters (confirmed against real saved metadata — see status note above)

| Param | Type | Required | Notes |
|---|---|---|---|
| `contentId` | String | yes¹ | Managed Content **FQN**, not a bare key. Confirmed shape: `"marketing--Default_Content_Workspace.sfdc_cms__sms--<API_NAME>"`, as returned by `content-fqn`. ¹Required for activation, not draft save — omit when unknown. See the [`contentId` Rule](#contentid-rule-marketing-messaging-actions) above. Never fabricate. |
| `senderId` | String | yes¹ | **Not `senderSmsCode`.** Bind the selected `GET /services/data/vXX.0/flowbuilder/messaging/sender-sms-codes` row's `id` as a literal `stringValue`; element references are rejected. Never bind `messagingPlatformKey`, a phone number, or a fabricated ID. ¹Gates activation, not draft save. |
| `clickTracking` | Boolean | no | Literal design-time choice; confirmed value `true`. |
| `communicationSubscriptionId` | String | no | Bind the selected `GET /services/data/vXX.0/flowbuilder/messaging/communication-subscriptions` row's `id`. |
| `commSubscriptionChannelTypeId` | String | no | Bind the same subscription row's `channelTypeId`; never mix IDs from different rows. |
| `blockoutWindowBehaviour` | String | no | Static enum. Confirmed value `"doNotSend"`; do not guess other members. |
| `messageSendTiming` | String | no | Emit one live-described literal: `"Anytime"`, `"NotDuringActiveSession"`, or `"NotDuringOpenSession"`. Omit it to use Core's `"NotDuringActiveSession"` default. |
| `timeToLive` | Integer | feature-gated | Emit only when the live describe exposes it. Use minutes from `1` through `1440`; values outside that range fail save validation. |
| `sendTimeAttributeKeys` | String | feature-gated | Emit only when the live describe exposes it. Supply the marketer-selected attribute names as a comma-separated design-time literal, not a collection or element reference. |
| `sendTimeAttributeSources` | String | feature-gated | Pair each selected attribute with its Flow source as `<attribute>=<value>`, then join entries with the literal `~|~`, for example `Loyalty_Tier={!Customer.Tier__c}~|~Order_Id={!Order.Id}`. This parameter permits Flow references. |
| `contentSchemaParameter` | `ContentSchema` generic | no | Optional content-variable bindings; resolve and emit `dataTypeMappings[]` only when used. |

### Worked example

`examples/send-sms-message.json` — confirmed persisted draft action fragment
with literal `contentId`, `senderId`, subscription IDs, `clickTracking`, and
`blockoutWindowBehaviour`; `dataTypeMappings: []`;
`storeOutputAutomatically: true`; and no `faultConnector` (the marketing-flow
default). Add a fault path only when the user asks for error handling; see
`../../shared/fault-paths/fault-paths.md` § Marketing Flows — Fault Paths Only When Asked. The fragment
is Draft-save evidence only; it is not proof of activation.

> **Note:** This is an `actionCalls[]` entry fragment, not a complete flow. Add it only to an `AutoLaunchedFlow` with `start.triggerType: "Segment"` or `"OnDemandNoTrigger"`.

### Anti-patterns (agent should reject / flag)

```jsonc
// WRONG #1 (non-marketing flow, or the user asked for error handling) — no fault path.
{ "actionName": "sendSmsMessage", "storeOutputAutomatically": true }
// Add faultConnector to a real handler. In a marketing flow (fault-paths.md list) where
// the user did not ask for error handling, omitting it is correct.

// WRONG #2 — fabricating a contentId the user never supplied.
{ "name": "contentId", "value": { "stringValue": "MC_GUESSED_VALUE" } }
// Omit the field entirely instead — see the contentId Rule above.

// WRONG #3 — using sendSmsMessage without proving the Marketing flow context exposes it.
{ "actionName": "sendSmsMessage" }   // RecordBeforeSave, RecordAfterSave, or unprobed plain autolaunched
// Refuse. Require it in GET /services/data/vXX.0/flowbuilder/action/invocable-actions for the exact context first.

// WRONG #4 — wrong parameter name and a fabricated sender code.
{ "name": "senderSmsCode", "value": { "stringValue": "SC-ACME-US-2025" } }
// Use `senderId` with the exact sender record ID supplied or resolved for the org.
```

> **Verification note.** `Flow.Metadata` verifies the action envelope and six emitted inputs. Core 264 verifies `InvocableActionType.SEND_SMS_MESSAGE`, minimum API version 246, the three `messageSendTiming` literals, optional gated `timeToLive` and send-time attributes, and the `messageId` output.

## Send RCS Message Action (E360)

| Action | `actionName` (emit verbatim) | Enum (`InvocableActionType`) | Min API | Delivery |
|---|---|---|---|---|
| **Send RCS Message** | `sendRcsMessage` | `SEND_RCS_MESSAGE` | 262 | RCS |

### Discovery workflow

1. Call `dispatch_readonly(method: "GET", url: "/services/data/vXX.0/flowbuilder/action/invocable-action-details", queryParams: { actionName: "sendRcsMessage", actionType: "sendRcsMessage" })`. Treat an absent action or a 403 as an
   availability failure; do not invent metadata.
2. Resolve `contentId` through the [CMS discovery workflow](#cms-discovery-for-sms-and-rcs) with `contentTypeFQN: "sfdc_cms__multiChannelContent"`.
3. Call `dispatch_readonly(method: "GET", url: "/services/data/vXX.0/flowbuilder/messaging/sender-rcs-agents")`:
   - Omit optional `businessUnitId` unless you have a verified 15- or
     18-character Salesforce record ID. A direct Salesforce Core Business Unit
     ID starts with `1QO`; accept another prefix only after verifying that the
     record is related to that Business Unit. Never pass the numeric MCE `mid`
     or the `<EID>-<MID>` selector.
   - Items: `id`, `messagingPlatformKey`, `masterLabel`, `useCase`. Empty list → halt; do not guess an agent.
   - Do not copy sender-agent `useCase` into `inputParameters`.
4. Bind the selected item's `id` to `senderAgentId`. Never bind `messagingPlatformKey`.
5. Call `dispatch_readonly(method: "GET", url: "/services/data/vXX.0/flowbuilder/messaging/communication-subscriptions")`:
   - `messagingChannelId`: the sender's `id` (MessagingChannel.Id) from step 3. Never `messagingPlatformKey`.
   - `channel: "rcs"`, `contactPointType: "Phone"` — fixed RCS mapping. Omitting either → 400.
   - Omit `businessUnitRelatedId` unless step 3 used a verified 15- or
     18-character Salesforce record ID: a direct Business Unit ID starting with
     `1QO`, or another record ID verified as related to that Business Unit.
     Then pass that same Salesforce ID. Never pass an MCE `mid` or
     `<EID>-<MID>` selector.
   - Empty list → halt; do not guess.
   - Each row is one subscription with one `channelTypeId` (`MIN(CommSubscriptionChannelType.Id)` when several channel types share a subscription). Bind that row's `id` → `communicationSubscriptionId`, `channelTypeId` → `commSubscriptionChannelTypeId`.
   - Skip this pair only with `bypassConsent: true`, and only after explicit user confirmation of external consent.
6. Require the CMS-selected `managedContentId` to resolve through `GET /services/data/vXX.0/flowbuilder/messaging/content-fqn`; bind only the returned `contentFqn`. A name, slug, content key, variant ID, raw managed-content ID, or unresolved FQN hard-fails save (`ManagedContentIdException` / `Invalid Managed Content Key!`).

### Metadata characteristics

- **Fault path: only when asked in a marketing flow.** `hasCallout: true` can throw at runtime. In a marketing flow, add a `faultConnector` only if the user asks for error handling; in any other flow type, always wire one (see [Fault Path](#fault-path)).
- **Output.** Describe returns `messageId` (String). Emit `storeOutputAutomatically: true` and `outputParameters: []`.
- **Transaction control.** `allowsTransactionControl: true`, `doRollbackOnError: false` — always emit `flowTransactionModel`.
- **Synchronous.** Omit `timeoutConnector` / `timeoutPathUsage`.
- **CPE.** `configurationEditor: "builder_e360_journeys-send-rcs-editor"`. Resolve params from the live describe anyway.
- **`ContentSchema`.** Optional `contentSchemaParameter`. Emit `dataTypeMappings[]` only when binding content variables.
- **Record-triggered.** Refuse `RecordBeforeSave`. In `RecordAfterSave`, put the action on `scheduledPaths[]`, never the immediate path.
- **Consent is required.** Bind `communicationSubscriptionId` + `commSubscriptionChannelTypeId` on every send. `bypassConsent: true` is the only skip, and only after explicit external-consent confirmation. Sender `useCase` does not change this.
- **Describe-driven tracking and content-derived use case.** Emit
  `isTrackingLinks` only when the live describe exposes it and the user selects
  a value. When the live describe exposes `messageUseCase`, derive its value
  from the selected RCS content metadata. Never ask the user to choose it
  independently and never copy sender-agent `useCase`. Continue to omit the
  SMS-only `clickTracking` and `blockoutWindowBehaviour` fields.

### Input parameters

Always re-fetch with `GET /services/data/vXX.0/flowbuilder/action/invocable-action-details`. Verified core-264 shape:

| Param | Type | Required by describe | Notes |
|---|---|---|---|
| `contentId` | String | yes | Runtime FQN. Omit when unknown. Never fabricate. |
| `senderAgentId` | String | no¹ | `GET /services/data/vXX.0/flowbuilder/messaging/sender-rcs-agents` → `[].id` only. |
| `communicationSubscriptionId` | String | no² | One list row's `id`. Pair with that same row's `channelTypeId`. Required unless `bypassConsent` is true. |
| `commSubscriptionChannelTypeId` | String | no² | Same row's `channelTypeId`. Do not mix ids across rows. Required unless `bypassConsent` is true. |
| `messageSendTiming` | String | no | Literal from the live describe. |
| `bypassConsent` | Boolean | no | `true` only after explicit external-consent confirmation; then omit the subscription pair. |
| `isTrackingLinks` | Boolean | no | Optional link-tracking choice from the live describe. |
| `messageUseCase` | String | no | Derive from the selected RCS content metadata when exposed by the live describe. Never accept an independent user choice or copy sender-agent `useCase`. |
| `contentSchemaParameter` | `ContentSchema` generic | no | Content-variable bindings. |

¹Describe marks this optional; save validation rejects an empty sender for a usable send. Discover and bind before activation.
²Describe marks these optional; product requires the pair unless `bypassConsent` is true.

`clickTracking` and `blockoutWindowBehaviour` are SMS-only
(`SMSParameterUtils`; RCS never registers `blockoutWindowBehaviour`).

`testPhoneNumber` is a required **pre-debug extension**, not a persisted input. Use it only for Send Test Messages debug.

### Worked example

`examples/send-rcs-message.json` — selected `senderAgentId` and consent IDs bound
as literals from discovery, and `contentId` omitted only until CMS discovery plus
`GET /services/data/vXX.0/flowbuilder/messaging/content-fqn` resolves a real FQN; `storeOutputAutomatically: true`,
no `faultConnector` (the marketing-flow default).

Bind those RCS IDs as design-time literals under the general literal-binding
rule. No RCS-specific live rejection of `elementReference` was verified; do not
claim that the RCS action rejects runtime references solely from the SMS
contract.

> Fragment only. Replace each ID placeholder with the selected discovery row's
> literal ID. It references `END_Flow`; define that target in the complete flow. For `RecordAfterSave`, place the action under Start
> `scheduledPaths[]`.

### Anti-patterns (agent should reject / flag)

```jsonc
// WRONG #1 — provider key instead of discovered messaging-channel id.
{ "name": "senderAgentId", "value": { "stringValue": "provider-agent-key" } }

// WRONG #2 — unresolved name/FQN as contentId (hard-fails save).
{ "name": "contentId", "value": { "stringValue": "RCS_Welcome_Transactional" } }
// Omit until GET /services/data/vXX.0/flowbuilder/messaging/content-fqn returns a real FQN.

// WRONG #3 — omitting consent, or bypassConsent without confirmed external consent.
{ "name": "bypassConsent", "value": { "booleanValue": true } }
// Also wrong: no communicationSubscriptionId / commSubscriptionChannelTypeId and no bypassConsent.
// Also wrong: skipping consent because the sender useCase is TRANSACTIONAL.

// WRONG #4 (non-marketing flow, or the user asked for error handling) — no fault path.
{ "actionName": "sendRcsMessage", "connector": { "targetReference": "END_Flow" } }

// WRONG #5 — RecordAfterSave immediate path, or any RecordBeforeSave emit.
{ "actionName": "sendRcsMessage", "connector": { "targetReference": "Next_Element" } }

// WRONG #6 — SMS-only params.
{ "name": "clickTracking", "value": { "booleanValue": true } }
{ "name": "blockoutWindowBehaviour", "value": { "stringValue": "WaitUntilWindowEnds" } }
```

> **Verification note.** Action metadata: core-264 `InvocableActionType.java` + `testSimpleDescribeAction` goldfile. Sender discovery: W-23731426 `listSenderRcsAgents`. Consent listing: `E360JourneyStaticMethods.getCommunicationSubscriptionsBuFiltering` (Connect maps `commSubId`/`commSubChannelTypeId` → `id`/`channelTypeId`; RCS `contactPointType` is `Phone` via `CHANNEL_TO_CONTACT_POINT`). Per-org, re-run describe and discovery before authoring.

## Conversation Messaging Action

**Send Conversation Messages** (`sendConversationMessages`) is the Enhanced Messaging / Digital Engagement analog of the E360 mobile actions above — it sends a `ConversationMessageDefinition` to `MessagingEndUser` recipients. Its builder traits differ (no callout, no transaction control, no generic types) and it carries save-time consent cross-validation.

**When authoring this action, load `conversation-messaging.md` and follow it** — it is the complete build guide (trait differences, describe-driven input parameters, consent rules, worked example, and anti-patterns).

## Send Email Actions

*(UMS `sendEmailMessage` + stock `emailSimple`)*

Two different email-sending actions with materially different shapes:

| Action | `actionType` / `actionName` | Container | `contentId` (CMS) | `flowTransactionModel` |
|---|---|---|---|---|
| **Send Email Message** (UMS marketing email, E360) | `sendEmailMessage` | A marketing flow whose action catalog lists it, for example a Journey / `AutomationEvent` start (`trgrOnEmailSubscription`), `IndivRelatedRecord`, or `OnDemandNoTrigger` (`../start/start.md` § On-Demand); confirm with `invocable-actions` for the exact context | **Required** for activation — resolve `sfdc_cms__email` FQN via [CMS discovery for Email](#cms-discovery-for-email-sendemailmessage) | `Automatic` |
| **Send Email** (stock) | `emailSimple` | Bare `AutoLaunchedFlow` with no trigger (no `triggerType`) | None (no CMS dependency) | `CurrentTransaction` only |

### `sendEmailMessage` (UMS marketing email)

> **Same action as [Send Email Message (E360)](#send-email-message-e360) above.** That
> section is the authoritative, describe-driven parameter contract (`senderId`, the consent
> pair, `contentId`, builder traits, anti-patterns). This subsection keeps the **Journey /
> `AutomationEvent` container** framing and a **live-verified** save; the two live-observed
> warnings below independently corroborate the E360 section's `senderId` and
> `commSubscriptionChannelTypeId` requirements. Author against the E360 section for the full
> parameter set — the bullets here only add the container-specific rules.

- In a Journey / `AutomationEvent` flow: author in a **Journey** flow whose `start.triggerType` is `AutomationEvent` with
  `eventType`/`eventName` `trgrOnEmailSubscription`. The start's single required
  input is `communicationSubscription` (bind a real subscription `id`) — there is
  **no** `messagingChannel` analog like SMS has. This is the same subscription `id`
  bound below as the action's `communicationSubscriptionId` input parameter — one
  value, referenced under different field names on the Start element vs. the
  action call.
- In an On-Demand Flow, use the On-Demand Start instead (`../start/start.md` § On-Demand): no
  start inputs and no recipient record, because the caller passes the person.
- In a Journey / `AutomationEvent` flow, create the recipient first (e.g. Create Records →
  Contact), then the action.
- Resolve `contentId` through [CMS discovery for Email](#cms-discovery-for-email-sendemailmessage)
  and bind the resolved `sfdc_cms__email` FQN. Omit only when unresolvable
  (activation stays blocked).
- Bind **`senderId`** (a verified OrgWideEmailAddress / active SenderEmailAddress / active
  User Id — a record Id, literal `{stringValue}` only). Omitting it fails save with
  `FROM_USER_EMPTY`, and a missing/invalid sender is what surfaces the *Select a valid From
  address* activation warning below. See the [E360 `senderId` deep dive](#send-email-message-e360).
- If you set `communicationSubscriptionId`, set its mandatory companion
  **`commSubscriptionChannelTypeId`** too (both are record Ids) — the Id alone fails with
  `COMMUNICATION_SUBSCRIPTION_CHANNEL_TYPE_ID_MISSING`.
- `flowTransactionModel: "Automatic"`.
- No `faultConnector` unless the user asks for error handling; this is a marketing flow (see [Fault Path](#fault-path)).

> **Activation-gating (not save-blocking) warnings observed on a live org:**
> even with a valid `contentId`, `sendEmailMessage` retained two warnings —
> `Select a valid From address` (the org had **zero** org-wide email addresses:
> `GET /services/data/vXX.0/flowbuilder/action/org-wide-email-addresses` → `{"addresses":[]}`) and `We couldn't find a
> Communication Subscription Channel Type ID` (no `commSubscriptionChannelTypeId` was bound). Both clear once
> `senderId` and the consent pair are bound. A User can be the sender when the org has no org-wide address, and
> `GET /services/data/vXX.0/flowbuilder/messaging/communication-subscriptions` with `channel: "email"`,
> `contactPointType: "Email"` and no `messagingChannelId` returns the email subscriptions with their
> `channelTypeId`; see [Resolve names to Ids](#resolve-names-to-ids).
> `validate_flow` still returns `isSuccess: true` with these warnings. **Both are the
> activation-time manifestation of the E360 section's required params** — *Select a
> valid From address* ↔ `senderId` (`FROM_USER_EMPTY`), and the missing channel-type ↔
> `commSubscriptionChannelTypeId`; see [Send Email Message (E360)](#send-email-message-e360).

```jsonc
// actionCalls[] fragment — Journey/AutomationEvent flow. Save-verified (isSuccess:true) against a live org,
// but this minimal shape kept two activation warnings (see note above): for activation, also bind senderId
// and commSubscriptionChannelTypeId — see § Send Email Message (E360) for the full contract.
{
  "name": "Send_Email_Message",
  "label": "Send Email Message",
  "actionType": "sendEmailMessage",
  "actionName": "sendEmailMessage",
  "nameSegment": "sendEmailMessage",
  "flowTransactionModel": "Automatic",
  "storeOutputAutomatically": false,
  "inputParameters": [
    { "name": "communicationSubscriptionId", "value": { "stringValue": "<real subscription id>" } },
    { "name": "contentId", "value": { "stringValue": "marketing--Default_Content_Workspace.sfdc_cms__email--<CONTENT_KEY>" } }
  ],
  "outputParameters": []
  // no faultConnector: marketing flow, add one only if the user asks for error handling
}
```

### `emailSimple` (stock Send Email)

- Minimal container: a bare `AutoLaunchedFlow` with no trigger (Autolaunched
  Flow, No Trigger) — the persisted `start` has `triggers: []` and no
  `triggerType` key. No CMS/`contentId` dependency. This is not the
  `OnDemandNoTrigger` marketing flow type (On-Demand Flow), so the default
  fault-path rule applies.
- `flowTransactionModel: "CurrentTransaction"` — **required**; `emailSimple`
  rejects `Automatic` with `ACTIONCALL_TRANSACTION_MODEL_NOT_ALLOWED: The action
  'EMAILSIMPLE' only supports 'CurrentTransaction'`.
- All input parameters report `isRequired: false` in the describe; the "required"
  behavior is enforced as **cross-parameter runtime logic**, not static flags:
  - `emailAddresses` (or `emailAddressesArray`), `emailSubject`, `emailBody` for a
    body-only send.
  - `emailTemplateId` **requires** `recipientId` — validate emits
    `Because an email template was specified, Recipient ID is required.`
- Wire a `faultConnector`.

> **Nuance on the generic cross-parameter note in
> [Validation Rules and Constraints](#validation-rules-and-constraints):** the
> `recipientId`-required-with-template rule reproduced and is real. A hard
> "template conflicts with explicit subject/body" validation error did **not**
> reproduce at `validate_flow` time — only an ID-format/existence check on
> `emailTemplateId` appeared. **Caveat:** the probe used a synthetic, unresolvable
> `emailTemplateId` (no real `EmailTemplate` record was obtainable in the test org), so
> whether a *resolvable* template + explicit body triggers a distinct path remains
> an open question, not a settled result.

```jsonc
// actionCalls[] fragment — bare AutoLaunchedFlow (no triggerType). Verified isSuccess:true, warnings:[] against a live org.
{
  "name": "Send_Email",
  "label": "Send Email",
  "actionType": "emailSimple",
  "actionName": "emailSimple",
  "nameSegment": "emailSimple",
  "flowTransactionModel": "CurrentTransaction",
  "storeOutputAutomatically": true,
  "inputParameters": [
    { "name": "emailAddresses", "value": { "stringValue": "qa@example.com" } },
    { "name": "emailSubject",   "value": { "stringValue": "QA Test" } },
    { "name": "emailBody",      "value": { "stringValue": "QA body." } }
  ],
  "outputParameters": [],
  "faultConnector": { "targetReference": "Log_Fault" }
}
```

> **Verification note.** Both actions were authored, `validate_flow`'d
> (`isSuccess: true`, `errors: []`), saved, and retention-confirmed via
> `GET /services/data/vXX.0/flowbuilder/flow/{id}` against a live org: `sendEmailMessage` and `emailSimple` both
> saved as fully valid `Draft` versions. `processType: "Journey"` was
> observed to persist **non-deterministically** — some saves coerced it to
> `AutoLaunchedFlow`, others retained `Journey`. Because `sendEmailMessage` requires
> a Journey container, this is not a cosmetic drift: after every `POST /services/data/vXX.0/flowbuilder/flow/actions/save` on a
> `sendEmailMessage` flow, re-read the persisted `processType` via `GET /services/data/vXX.0/flowbuilder/flow/{id}`
> and treat a coercion to `AutoLaunchedFlow` as a save failure — do not proceed to
> activation on the assumption the container held.
