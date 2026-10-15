---
id: flow.recipes.testing.shared-stages.intent-analyzer
description: "Phase 1 of author-test and debug workflows — classify the user request, run the eligibility probe, detect silo mode, and extract the flow shape."
---

# Intent analyzer (shared stage)

<!-- Consumers: workflows/author-test.md (Phase 1), workflows/debug.md (Phase 1), workflows/save-debug.md (Phase 1) -->

The first phase in the author-test and debug workflows. Reads the user
request and the parent flow, classifies what the user is asking for,
confirms the flow is eligible, and emits a structured assessment that
later phases consume.

This stage is **read-only**: no `POST /services/data/vXX.0/flowbuilder/flow-test`/`PATCH /services/data/vXX.0/flowbuilder/flow-test/{id}`,
a `run_*` call, or any other write call happens here. Output is a
plain assessment object handed to the next phase.

## Step 1 — Input classification

The Route-by-intent table in [[flow.recipes.testing]] is the **single
source of truth for the trigger phrases** — this stage does not re-list
them. The router already picked a workflow from that table; this stage's
job is to **confirm that routing was right** for the flow at hand and
emit the matching intent (one of `author-test`, `debug`, `promote`,
`save-debug`, `run-saved`, `coverage`) in the Step 5 assessment.

Confirm against the router's table rather than re-deriving from scratch:
the consuming workflow tells you which intent it expects (author-test
expects `author-test`, debug expects `debug`, and so on). **If the flow
or request doesn't match that expected intent, hand control back to the
router** — do not silently proceed down the wrong workflow.

If the intent is `run-saved` or `coverage`, hand control back to the
router — those paths skip this stage and go directly to the run-tool
decision table or the coverage interpretation-only path. No coverage
operation is onboarded to MCP.

## Step 2 — Eligibility check (mandatory, no shortcuts)

Call `dispatch_readonly(method: "GET", url: "/services/data/vXX.0/flowbuilder/flow/{id}")` for the target flow. Read:

- `processType` (top-level)
- `metadata.start.triggerType` (treat absent as `"None"`)

Check against the confirmed-supported combos:

| `processType` | `triggerType` | Status |
|---|---|---|
| `AutoLaunchedFlow` | `RecordBeforeSave` | Supported |
| `AutoLaunchedFlow` | `RecordAfterSave` | Supported |
| `AutoLaunchedFlow` | `None` (or absent) | Supported |
| `AutoLaunchedFlow` | `Scheduled` | **Not supported** |
| `Flow` | `None` (screen flow) | **Not supported** |
| anything else | anything else | **Probe** |

If the combo is unknown, call
`GET /services/data/vXX.0/flowbuilder/schema/flow-capabilities` (read `.flowFeatures`) with that exact
`(processType, triggerType)` pair. Look for the literal string
`"FlowTesting"` in the returned `Array<string>`. **Do not key off
`"TestModeExperience"`** — that flag is also present on screen flows
and is misleading.

Full table and decision flow: [[flow.recipes.testing.eligibility]].

## Step 3 — Silo detection

Scan the user message for any of these signals:

- Literal `@testSetup`
- The words "silo", "isolated", "fixture", "test data", "seeded data"
- A specific Apex class name the user named as the seed source

If any signal is present, set `siloMode: true`. When silo mode is on,
the eligibility check also requires `"FlowTestingWithDataSilo"` in the
features array — surface that as a second probe before proceeding.

### Silo sub-type selection

When silo mode is active, choose the `dataSourceType`:

- **`AiGenerated` (default)** — when the user has NOT named a specific
  Apex class or said `@testSetup`. The AI becomes the fixture generator.
- **`ApexClass` (opt-in)** — when the user explicitly names an Apex
  class or says `@testSetup`.

The default flip is behavioral: "silo" no longer implies "Apex" —
AiGenerated is the new default, and Apex is an opt-in.

## Step 4 — Flow shape extraction

From the `GET /services/data/vXX.0/flowbuilder/flow/{id}` response, extract:

- `elementCount` — total number of canvas elements
- `triggerType` — record-triggered (`RecordBeforeSave` /
  `RecordAfterSave`), non-triggered (`None`), or other
- `inputVariables[]` — only relevant for non-triggered flows; each
  entry is `{ name, dataType, isInput, isOutput }`. Pulled from the
  flow's `variables[]` filtered by `isInput: true`.
- `startConfig` — `{ object, recordTriggerType, scheduledPaths }` —
  needed by the payload-builder to pick `InputTriggeringRecordInitial`
  vs. `InputVariable` parameter types.
- `hasWaits` — `true` when `metadata.waits[]` is non-empty. Detection
  only: a Wait never makes a flow ineligible, and each workflow decides
  what to do with it.

This is the structural difference that drives payload shape: a
record-triggered flow takes `sobjectValue`-bound `$Record`; a
non-triggered flow takes one `InputVariable` parameter per declared
input variable.

### SObject-reference scan (for AiGenerated silo)

When `siloMode: true` and the silo sub-type is `AiGenerated`, identify
the target SObject that the generator should fabricate a fixture record
for:

- **Record-triggered flows** (`RecordBeforeSave` / `RecordAfterSave`)
  — the trigger object is `start.object`.
- **Autolaunched flows** (`triggerType: None`) — scan the flow elements
  for the first `recordLookup`, `recordCreate`, `recordUpdate`, or
  `recordDelete` element and extract its `object` field. Alternatively,
  scan `variables[]` for an SObject-typed variable.

This story supports **single-object scope only**: if the flow touches
multiple SObject types, pick the one the user's scenario names and note
the others as out-of-scope. This scan supports AC-5 (detect and offer).

## Step 5 — Output contract

Emit a single assessment object:

```jsonc
{
  "intent": "author-test" | "debug" | "promote" | "save-debug" | "run-saved" | "coverage",
  "eligible": true,
  "flowShape": {
    "flowApiName": "<api name>",
    "processType": "AutoLaunchedFlow",
    "triggerType": "RecordAfterSave",
    "elementCount": 7,
    "inputVariables": [],
    "startConfig": { "object": "Account", "recordTriggerType": "Update" },
    "hasWaits": false
  },
  "siloMode": false,
  "targetSObject": null,
  "features": ["FlowTesting", "FlowTestCoverage", "FlowTestingWithDataSilo"]
}
```

`targetSObject` is the single object type the AiGenerated generator will
fabricate a fixture for — set from the SObject-reference scan above.
For record-triggered flows it equals `startConfig.object`; for
autolaunched flows it is the object resolved from the first
`recordLookup` / `recordCreate` / `recordUpdate` / `recordDelete`
element (or an SObject-typed variable). Leave `null` when
`siloMode: false` or the sub-type is `ApexClass` (the Apex path sources
its own records). The payload-builder Step 6 and
[[flow.recipes.testing.workflows.author-test]] Phase 3 both read this
field to drive the generator.

## Step 6 — Error path

If `eligible: false`:

1. Tell the user FlowTest is not supported for this `(processType,
   triggerType)` combo, naming both values.
2. Offer the debug workflow as the ad-hoc-validation alternative — point
   them at [[flow.recipes.testing.workflows.debug]], which probes the
   flow's supported features and picks the right run endpoint.
3. Stop. Do not attempt `POST /services/data/vXX.0/flowbuilder/flow-test`/`PATCH /services/data/vXX.0/flowbuilder/flow-test/{id}` against an
   ineligible flow — the wrapper will forward the payload, Aura will
   reject with `state: "ERROR"`, and the wrapper re-throws. There is
   no implicit fallback.

If `eligible: true` but `siloMode: true` and
`"FlowTestingWithDataSilo"` is absent: tell the user silo mode isn't
supported here, ask whether to proceed without silo (live-org binding
via `sobjectValue`) or stop.
