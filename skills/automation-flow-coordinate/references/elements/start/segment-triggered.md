---
name: flow-element-start-segment-triggered
license: LICENSE.txt has complete terms
description: "Load when building a Segment-triggered (Audience) marketing flow — triggerType `Segment`, processType `AutoLaunchedFlow`. Covers only what is Segment-specific: the segment name→ID→DMO binding chain (via `dispatch`-invoked Data 360 tools), the `segmentOnApiName` eligibility gate, `publishSegment`, segment outreach actions (BEA / send-to-journey), and the `$Record` member context. MUST load `audience-common.md` first for the shared run schedule / top-level `timeZoneSidKey` / `dataSpace` / `dataGraph` / re-entry contract. DO NOT load for any other trigger type."
metadata:
  version: "1.0"
  related-skills: flow-element-start, flow-element-start-audience-common, flow-flow-properties
---

# Segment-Triggered (Audience Flow)

Load this when `triggerType` is `Segment`. A broadcast flow that fans out a dynamic segment is `BroadcastNoTrigger`, documented in `start.md`. Do not load this file for it, and do not apply the eligibility gate below.

> **MUST load [`audience-common.md`](audience-common.md) first.** It holds the
> shared scheduled-audience contract — run schedule, top-level `timeZoneSidKey`,
> top-level `dataSpace`, optional `dataGraph`, re-entry (`entryType`), the
> save-and-activate gates, and the builder round-trip defaults, all identical
> across `Segment`, `List`, `CampaignMember`, and `RecordQuery`. This file adds
> ONLY what is specific to the Segment trigger: the segment binding, the
> eligibility gate, `publishSegment`, outreach actions, and the `$Record` member context.

- **triggerType**: `Segment`. Author `processType: "AutoLaunchedFlow"` for both
  `POST /services/data/vXX.0/flowbuilder/flow/actions/save` and legacy `saveAndValidateFlow` lifecycles. This is the verified
  Tooling API input and persisted value. Do not substitute `Journey` based on
  the builder surface name or the live Connect enum member.
- Targets a marketing segment/audience for outreach (email campaigns, drip sequences, re-engagement, nurture journeys).
- Do NOT use `Scheduled` or `RecordAfterSave` for segment-based marketing — those lack audience targeting, segment membership context, and marketing frequency caps. A broadcast that fans out a dynamic segment now is `BroadcastNoTrigger`, not `Segment`.
- For a `sendSmsMessage` flow, `dataGraph`, `schedule.frequency: "OnActivate"`,
  and an explicit End node were observed in one hand-built draft's persisted
  metadata. Preserve them when reproducing that flow, but do not treat them as
  activation requirements without live validation evidence.

## Reference File Index

| File | Purpose |
|---|---|
| `audience-common.md` | The shared schedule / timezone / dataSpace / dataGraph / entryType contract (load first) |
| `examples/segment-weekly-schedule.json` | Weekly run-schedule start-element example (the schedule shape is documented in `audience-common.md`) |

## Bind the segment

The prompt gives a segment name. `start.segment` and `start.object` are NOT
derivable from it, and **plain SOQL cannot supply `segmentOnApiName`** — the
`MarketSegment` sObject exposes `Id`, `Name`, `SegmentStatus`, `PublishStatus`,
`SegmentMembershipTable`, `DataSpaceId`, and `DataGraphId`, but **not** the
`segmentOnApiName` DMO that binds to `start.object`. Resolve the segment via the
`dispatch`-invoked Data 360 (`d360_*`) segment tools before every save.

The `d360_*` tools run through `dispatch`, not a standalone server: dispatch
a POST to `/services/data/vXX.0/ssot/mcp/execute` with body
`{ "toolName": "<d360_tool>", "paramsJson": "<params as a JSON-ENCODED STRING>" }`
— `paramsJson` is a **string** (double-encoded JSON), never a nested object. Use
`dispatch` (POST). If a tool's exact param shape is unclear,
`discover` then `describe` the matching `d360_*` recipe before dispatching — don't
guess the shape. (A `MarketSegment` SOQL query is fine as a supplemental
name→`Id`/status lookup, but it can never stand in for the `d360` resolution
because it lacks `segmentOnApiName`. Its `SegmentMembershipTable`, e.g.
`Individual_Unified_SMH_<n>__dlm`, is the segment's membership table, never
`start.object`: with it the org refuses to activate the flow ("The segment you
selected in this flow's Start element contains objects that aren't associated
with individuals").)

1. `dispatch({ url: "/services/data/vXX.0/ssot/mcp/execute", method: "POST", body: { toolName: "d360_segment_get", paramsJson: "{\"segmentApiName\": \"<name>\"}" } })` — fast path only when the prompt supplies the segment's exact developer/API name.
2. If that returns not-found (the prompt gave a display name, or a fuzzy/partial name), fall back to `d360_segment_list` (`paramsJson: "{\"batchSize\": 50, \"offset\": 0}"`), paginating with `offset` as needed, and match the target in `result.segments[]` by its `displayName` or `apiName`. The list result already contains the same fields as `d360_segment_get` — no follow-up `get` call is needed once you've matched a row. (`d360_segment_get_by_id`, `paramsJson: "{\"segmentId\": \"<1sg… id>\"}"`, resolves a segment already known by `marketSegmentId`.)
   - **No segment in the org matches the prompt's name at all → STOP and ask the user for the correct segment name.** Do NOT silently substitute a different, unrelated segment that happens to exist (e.g. picking whatever segment comes back first) — a flow built against the wrong audience is worse than no flow.
3. From whichever call resolved the segment, read:
   - `marketSegmentId` (18-char `1sg…`) → `start.segment`.
   - `segmentOnApiName` → `start.object`.
   Require `segmentStatus: "ACTIVE"` and `publishStatus: "SUCCESS"` when the
   response includes those fields. Stop when the segment is inactive,
   unpublished, or its last publish failed.
4. Eligibility gate — check `segmentOnApiName`:
   - the Unified Individual DMO (e.g. `UnifiedIndividual__dlm`) → proceed; saves and activates cleanly.
   - a non-unified Individual DMO (e.g. `ssot__Individual__dlm`) → proceed, but warn the user: the flow will SAVE, yet it can't ACTIVATE without an activation template (save returns a `WARNING_BLOCK_ACTIVATION` / `ACTIVATION_TEMPLATE_REQUIRED_FOR_NON_UNIFIED_INDIVIDUAL`; the template is set via `start.activationTemplate` — a dev name of an existing Data Cloud template — which this flow's save cannot create).
   - anything else (`Account__dlm`, `Lead__dlm`, …) → STOP for a Segment-triggered flow. Tell the user the segment is built on `<segmentOnApiName>` and cannot trigger a segment flow; a segment on individuals is required. Do NOT substitute another segment. If the user asked for a broadcast flow, leave this file and author `BroadcastNoTrigger` instead of stopping.

Set BOTH `segment` and `object` on every save; don't rely on a `segment` ID persisting on its own — re-set `object` from step 3 alongside it.

Never write the segment name, `marketSegmentDefinitionId`, or `segmentOnId`
into `start.segment`. Use `marketSegmentId`. An invalid value can return
`isSuccess: true` with `InvalidDraft`, `FLOW_START_INPUT_INVALID_TYPE`, and an
omitted persisted segment. Redo step 1/2 and save again.

Salesforce record-ID substrings do not identify an org. Never compare fragments
in unrelated record IDs to infer an authentication mismatch. Compare the
Organization IDs returned by each authenticated service when org identity must
be verified.

On save error `TRIGGER_TYPE_CONTEXT_OBJECT_NOT_SUPPORTED` for a Segment-triggered flow: the segment is ineligible (individual-based required). Report it and do not retry with a substitute segment. This error does not apply to `BroadcastNoTrigger`.

`object` is the `segmentOnApiName` DMO from step 3 (e.g. `"UnifiedIndividual__dlm"`), NOT anything from a data graph and NOT the `SegmentMembershipTable`.

| Field | Value |
|---|---|
| `publishSegment` | Default `false`/omit: the flow does not (re)publish the segment; membership is assumed already published. Set `true` only if the prompt asks the flow to publish the segment when it runs. |

## Record context — the segment member is `$Record`

In a Segment flow, `$Record` is the current segment member: a row of the
`segmentOnApiName` DMO (the `start.object`, e.g. `UnifiedIndividual__dlm`). Read
the member's fields as **`$Record.<field API name>`**, for example
`$Record.ssot__FirstName__c`. This works with or without a `dataGraph` on the Start
element.

**Always write the `$Record.` prefix.** A bare field name or a DMO-qualified name
is rejected:

| Reference | Result |
|---|---|
| `$Record.ssot__FirstName__c` | valid |
| `ssot__FirstName__c` | `The "ssot__FirstName__c" element doesn't exist. Remove references to the element in all conditions.` |
| `UnifiedIndividual__dlm.ssot__FirstName__c` | `The "UnifiedIndividual__dlm.ssot__FirstName__c" element doesn't exist. …` |

Decision condition on the member's first name:

```json
{ "leftValueReference": "$Record.ssot__FirstName__c", "operator": "EqualTo", "rightValue": { "stringValue": "Alex" } }
```

Write the same reference in a condition-based exit rule's `conditions[]`
(`../exit-rule/exit-rule.md`).

Use field API names of the `segmentOnApiName` DMO; read them from the DMO's
describe (`GET /services/data/vXX.0/flowbuilder/platform/entity/{apiName}/fields`)
rather than guessing. Segment has **no `$Input` member row** (unlike
List/CampaignMember/RecordQuery, see `list-campaignmember.md` / `recordquery.md`):
do not invent one. `$Flow.*` globals remain available per the shared table in
`audience-common.md`.

## Data space note for `sendToJourney`

The shared data-space rules live in `audience-common.md`. For `sendToJourney`
specifically, also require the selected business unit's
`businessUnitsToDataSpaces[].dataSpaceName` to equal the chosen data space `name`.
Follow `../action-call/send-to-journey.md` for business-unit and Journey selection.

## Data graph note for `sendSmsMessage`

The shared data-graph rules live in `audience-common.md`. For `sendSmsMessage`,
preserve a source flow's existing graph; do not select one solely to copy the
observed example. A populated `dataGraph` was observed in the verified
`sendSmsMessage` draft, but no save or activation error establishes it as mandatory.

## Outreach actions for segment flows

For flows that route segment members to a Buyer Engagement Agent (BEA) for email outreach, load `../forward-to-bot-or-agent/forward-to-bot-or-agent.md` and follow the **Outreach Initiation (BEA)** section.

Key points:
- The action is `forwardToBotOrAgent` with `modeSelector: "InitiateConversation"`. **Do NOT use `assignTargetToAgent`** — that action does not support the nudge count/interval/from-address parameters the BEA uses and is not the correct action for this flow type.
- Set `areMetricsLoggedToDataCloud: true` at the `metadata` level (verified in BEA segment flow saves).
- The flow ends with an explicit `ends[]` element; wire the action's `connector.targetReference` to it.
- Schedule: `frequency: "OnActivate"` is the standard choice unless the user specifies a recurring cadence.
