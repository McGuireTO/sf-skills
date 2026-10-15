# Send to Journey (`sendToJourney`)
Add this element to `metadata.actionCalls[]`. Never emit the legacy
`triggerJourney` action.

Set `processType: "AutoLaunchedFlow"` and build the Start for the flow's trigger:

| Trigger | Start | Person's fields |
|---|---|---|
| `Segment` (the default) | `../start/segment-triggered.md` | `$Record.<field>` |
| `OnDemandNoTrigger` (an On-Demand Flow) | `../start/start.md` § On-Demand | `$SelectedIndividual.<field>` (needs `start.dataGraph`) |
| `IndivRelatedRecord` (a CRM-triggered marketing flow, e.g. "when a Lead's Status is Nurturing, send it to a journey") | `../start/start.md` § Engagement / Journey-Triggered | `$Input.<field>` (the triggering record) |

The rest of this file applies to all three; only a Segment flow has a Segment to
re-read in Plan And Pre-Save Checks. Stop for other trigger variants because they
are outside this MVP, not unsupported by the platform. A no-trigger autolaunched
Flow fails with `ACTIONCALL_NOT_SUPPORTED_FOR_PROCESSTYPE`.

## Resolve Dependencies

Load `send-to-journey-discovery.md`. Complete its Business Unit, Journey, and DE
schema procedures before emitting the action. Use its selected
`mceBuSelector`, `mceJourneySelector`, `metadata.dataSpace`, schema URI, and field
mappings without reconstructing or substituting values.

## Emit The Action

Before emitting either the required-field or no-field action shape, emit these
two entries in top-level `metadata.processMetadataValues`:

```json
[
  { "name": "BuilderType", "value": { "stringValue": "LightningFlowBuilder" } },
  { "name": "CanvasMode", "value": { "stringValue": "AUTO_LAYOUT_CANVAS" } }
]
```

Never omit `processMetadataValues` from a generated Send-to-Journey flow. The
flow can save as valid JSON without these entries, but Flow Builder then treats
the `locationX: 0` / `locationY: 0` elements as free-form coordinates and
renders them on top of one another instead of applying auto-layout. Apply this
requirement to both field-mapped and no-field Journeys.

Use the persisted no-field evidence for the fixed action envelope:

- Set `actionName`, `actionType`, and `nameSegment` to `sendToJourney`.
- Set `flowTransactionModel: "CurrentTransaction"`.
- Set `outputParameters: []`.
- Omit `faultConnector` unless the user asks for error handling. A Segment flow
  is a marketing flow; see `../../shared/fault-paths/fault-paths.md`
  § Marketing Flows — Fault Paths Only When Asked.
- Omit `storeOutputAutomatically` and `isWaitUntilCompleted` only when
  reproducing the verified no-field Draft shape. Do not generalize that
  omission to a field-mapped action.
- Bind `mceBuSelector` and `mceJourneySelector` as string literals.
- Emit one `dataTypeMappings[]` entry with
  `typeName: "JourneyDataExtensionSchema"` and the resolved `schemaUri`.
- Omit `connector` when this action is terminal. Otherwise, target the real next
  element. Do not invent an `ends[]` node for a terminal action.

**Hard rule: the journey type mapping uses `schemaUri`.** The describe lists
`JourneyDataExtensionSchema` with `superType: "NAMED_AUTOMATION_SCHEMA"`; its value
is a schema URI, so it goes in `schemaUri` (`action-call.md` § Generic-Type Placeholders, the `superType`
table). Putting the same URI in `typeValue` fails activation:
`In Apex action "<element name>", type mapping "InputAutomationSchema:schemaOnlyJourneyDataExtension/<journey id>" is not a supported type.`

```jsonc
// correct
"dataTypeMappings": [
  { "typeName": "JourneyDataExtensionSchema",
    "schemaUri": "InputAutomationSchema:schemaOnlyJourneyDataExtension/<journey id>" }
]
// WRONG: fails activation with "... is not a supported type."
"dataTypeMappings": [
  { "typeName": "JourneyDataExtensionSchema",
    "typeValue": "InputAutomationSchema:schemaOnlyJourneyDataExtension/<journey id>" }
]
```

When at least one field is mapped, add this input. Wire a `faultConnector` to a
real handler only when the user asks for error handling. If you wire one, remove
it only if `POST /services/data/vXX.0/flowbuilder/flow/actions/save` rejects it
for that exact field-mapped action contract.

```json
{
  "name": "journeyDataExtensionSchemaParameter",
  "value": {
    "inputConfiguratorMode": "Custom",
    "transform": {
      "isCollection": false,
      "schemaUri": "<resolved URI>",
      "transformValues": [
        {
          "transformValueActions": [
            {
              "outputFieldApiName": "<exact Journey field name>",
              "transformType": "Map",
              "value": { "elementReference": "<compatible Flow resource>" }
            }
          ]
        }
      ]
    }
  }
}
```

Add one `transformValueActions[]` entry per mapped field. Omit the entire input
when no fields are mapped and none are required. Never emit an empty Transform.

**Do not conclude "no fields" from a single empty schema read.** An unprimed
Journey can also return `parameters: []` and therefore look field-less. Emit the
no-field shape only after the prime-then-re-resolve procedure in
`send-to-journey-discovery.md` step 6 still returns `parameters: []`.

Use `examples/send-to-journey-no-fields.json` for the verified no-field action
fragment. Replace its illustrative selectors and Journey values with live
values. A live save verified this no-field action in a Segment-triggered Flow
whose status reached `Draft`. Do not claim that save validation proves runtime
Journey delivery.

## Plan And Pre-Save Checks

- Show the business unit as `<Business Unit Name> (MID: <MID>)` and show the
  mapped Data Space separately. Do not show only the MID or selector.
- Re-read the live business-unit mapping, Segment, generic schema, and DE fields
  immediately before every save.
- **Re-prime the Journey immediately before saving.** Call
  `dispatch(method: "POST", url: "/services/data/vXX.0/connect/e360mcetransformation/journey/upsert", body: { mceBuSelector: "<EID>-<MID>", journeyId: "<journey id>" })`
  so its API-event registration is fresh at save time.
  - The Journey field is **`journeyId`**, not `mceJourneySelector` or
    `journeyKey`. `<journey id>` is the same selected `id` bound to
    `mceJourneySelector`.
  - This is a raw Connect REST resource invoked through the authenticated
    Headless 360 `dispatch` tool. It is not a `/flowbuilder/...` endpoint or a
    `d360_*` operation; do not invent another tool for it.
  - A 500 does not by itself mean the prime failed. Confirm by re-resolving the
    DE schema before treating the response as a failure.
  - Priming sends no messages and enrolls no contacts. It is idempotent, so
    re-priming an already-primed Journey is a no-op re-registration.
  - Priming runs once at discovery time when the schema resolves empty and
    again here. Disclose the discovery-time prime as an already-performed
    prerequisite. Surface this pre-save re-prime in the approved plan summary
    as a prerequisite write.
  - If the call is unauthorized or the schema still does not resolve after a
    real prime attempt, use the manual fallback in
    `send-to-journey-recovery.md` step 2.
- Call `dispatch(method: "POST", url: "/services/data/vXX.0/flowbuilder/flow/actions/save", body: { builderType: "JourneyBuilder" })`. Use
   `saveType: "createNewFlow"` for a new Flow. Use `saveType: "saveDraft"` with
   the latest returned `flowId` as `currentFlowId` to revalidate an existing
   draft after an org-side prerequisite changes. `saveDraft` updates the current
   Draft version in place. Treat the response's `flowId` as authoritative, but
   do not claim that this save type creates or rotates a version ID.
- Require the schema URI suffix to match `mceJourneySelector`, in `schemaUri`
  with no `typeValue`.
- Require every mandatory DE field to have a compatible mapping.
- Verify one inline mapping per mapped field, or omit the schema input for a
  confirmed no-field Journey.
- Require `metadata.processMetadataValues` to contain exact
  `BuilderType: LightningFlowBuilder` and `CanvasMode: AUTO_LAYOUT_CANVAS`
  entries. Stop before `POST /services/data/vXX.0/flowbuilder/flow/actions/save` if either entry is absent or has another
  value.
- Reject `InvalidDraft` and activation-blocking warnings even when
  `isSuccess: true`.
- Before saving, load `../../shared/preview-renderer.md`. After a clean Draft
  save, stop and return its Journey Builder deep link for the latest returned
  version ID. Do
  not call `POST /services/data/vXX.0/flowbuilder/flow/{flowId}/actions/activate` (activateFlow),
  `POST /services/data/vXX.0/flowbuilder/flow/{flowId}/actions/deactivate` (deactivateFlow), or
  `POST /services/data/vXX.0/flowbuilder/flow/{flowId}/actions/submit-for-activation` (submitFlowForActivation).
  Preserve `processType: "AutoLaunchedFlow"`;
  activation endpoint 404s do not imply that Segment flows use another
  persisted process type.

## Resolve Journey-Not-Found Validation

Load and follow `send-to-journey-recovery.md` when `POST /services/data/vXX.0/flowbuilder/flow/actions/save` returns
`ACTIONCALL_INPUT_VALIDATION_FAILED` with "Can't find the journey. Check whether
it was renamed or deleted in Marketing Cloud."
