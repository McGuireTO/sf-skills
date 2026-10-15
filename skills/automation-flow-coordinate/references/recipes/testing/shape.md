# FlowTest definition — shape

The `flowTest` object below (`fullName` + `metadata`) is the FlowTest
**definition** shared by `POST /services/data/vXX.0/flowbuilder/flow-test`, `PATCH /services/data/vXX.0/flowbuilder/flow-test/{id}`, and
`POST /services/data/vXX.0/flowbuilder/flow-test/debug-interview-test-mode`. It is the **inner** shape, not the wire
body: each endpoint takes it as a JSON-encoded **string** in `flowTestJson`
(`flowTestJson: JSON.stringify(flowTest)`). `POST /services/data/vXX.0/flowbuilder/flow-test/debug-interview` does not
consume this shape; it is argument-driven (`flowVersionId` plus ad-hoc
`arguments`). This page is the **top-level skeleton**: the definition, the
`testPoints[]` frame, and the cross-cutting save/round-trip truths. The
per-element detail lives in dedicated files, linked inline below —
this file is the map, not the territory.

If you are mapping a debug run into a saved test, also read
[[flow.recipes.testing.workflows.promote]] — that file explains the
*workflow*; this file explains the *schema*.

## Wire format

### Top-level fields

```jsonc
{
  "fullName": "<flowApiName>_<scenario_slug>",   // server-validated identifier
  "metadata": {
    "label": "<human-facing name>",              // shown in the Tests panel
    "description": "<optional>",
    "flowApiName": "<flow API name>",            // must match the parent flow
    "flowTestFlowVersions": [                    // versions this test runs against
      { "flowVersionNumber": "2" },
      { "flowVersionNumber": "1" }
    ],
    "testType": "WithAssertion",                 // or "WithoutAssertion"
    "testPoints": [ /* see below */ ],
    "flowTestDataSources": [],                   // Apex @testSetup bindings
    "isolatedObjectExternalKeys": [],            // silo external keys — usually []
    "doesCommitChanges": false,                  // false = roll DML back on rerun
    "doesSkipStartConditions": false,            // true = bypass entry criteria
    "doesTestWaitElement": false,                // true = actually wait at Wait elements
    "isSubflowUseLatestFlowVer": false           // canonicalized on save (default false)
  }
}
```

| Field | Notes |
|---|---|
| `fullName` | Conventionally `<FlowApiName>_<scenario_slug>`. Must be unique within the flow. Server-validated. |
| `flowTestFlowVersions[]` | Each entry pins the test to one version number. A single test can run across several versions — e.g. `[{"flowVersionNumber":"2"},{"flowVersionNumber":"1"}]`. Versions are strings, not numbers. |
| `testType` | `WithAssertion` if any element has a non-empty `assertions[]`; otherwise `WithoutAssertion`. The two values and the coupling rule live in [[flow.recipes.testing.flowtest-elements.assertions]]. `WithoutAssertion` binds record-typed inputs by `Id`, with extra fields allowed only on the Updated snapshot — see [[flow.recipes.testing.flowtest-elements.parameters]] § "Record-typed inputs on `WithoutAssertion`". |
| `doesCommitChanges` | Almost always `false` for regression tests. Flip to `true` only when downstream effects (e.g. outbound message side effects) cannot be observed without persisted state. |
| `doesSkipStartConditions` | `true` lets you exercise a flow without satisfying its trigger entry filter — handy for scenarios where the trigger criteria are orthogonal to what you're testing. |
| `doesTestWaitElement` | `true` makes Wait elements actually pause when the test is replayed; `false` skips the wait so the run completes synchronously. Use `false` for `WithAssertion` tests (the runner cannot resume a paused interview). `true` suits a `WithoutAssertion` test saved from a paused debug run. For non-Wait flows the wire value is `false`. |
| `flowTestDataSources[]` | Binds silo fixture data (`AiGenerated` mock records or an Apex `@testSetup` class) that seed the Flow Test silo at run time. Default `[]` means no silo. Full shape, discovery tools, and the `jsonValue` binding it switches on: [[flow.recipes.testing.flowtest-elements.silo-config]]. |
| `isolatedObjectExternalKeys[]` | The identity bridge between the trigger record and the silo's seeded fixtures. Default `[]`. See [[flow.recipes.testing.flowtest-elements.silo-config]]. |

### `testPoints[]`

An array, one entry per element that needs scripted input or an
expectation. In practice the only entries you will see are:

- One on `Start` — supplies the trigger record (and, for update flows,
  the "after" snapshot and/or the scheduled-path pick).
- Optionally one on `Finish` — to bind assertions to "did the flow take
  the right path / leave records in the right state".

Each entry:

```jsonc
{
  "elementApiName": "Start",          // canvas element API name
  "parameters": [ /* inputs */ ],     // bind values into element
  "assertions": [ /* expectations */ ], // check values after element runs
  "isUseMockOutput": false            // canonicalized on save (default false)
}
```

The per-shape detail is split out:

- **`parameters[]`** — the typed value envelope and the
  `FlowTestParameterType` slots: [[flow.recipes.testing.flowtest-elements.parameters]].
  Binding the trigger record by flow type:
  [[flow.recipes.testing.flowtest-elements.parameters]].
- **`assertions[]`** — element-level vs. value operators, `errorMessage`,
  and the AND semantics: [[flow.recipes.testing.flowtest-elements.assertions]].
- **`testPoints[]` placement and `isUseMockOutput`** —
  [[flow.recipes.testing.flowtest-elements.test-points]].

### How the pieces assemble — minimal examples

A `WithoutAssertion` save (`Update_Account_Name_To_BAC`) — just inputs,
no expectation. Note the Id-only `sobjectValue`: on `WithoutAssertion`
tests, record-typed inputs are bound by `Id`. The one exception is the
Updated snapshot on before/after-update flows, which carries `Id` plus
the changed fields. See
[[flow.recipes.testing.flowtest-elements.parameters]] § "Record-typed
inputs on `WithoutAssertion`" for the full per-slot rule.

```json
{
  "fullName": "Update_Account_Name_To_BAC_TEMP_20260521_save_as_test_try1",
  "metadata": {
    "label": "save as test try1",
    "description": "",
    "flowApiName": "Update_Account_Name_To_BAC_TEMP_20260521",
    "flowTestFlowVersions": [{ "flowVersionNumber": "1" }],
    "testType": "WithoutAssertion",
    "testPoints": [
      {
        "elementApiName": "Start",
        "parameters": [
          {
            "leftValueReference": "$Record",
            "value": { "sobjectValue": "{\"Id\":\"001SM000001TNFCYA4\"}" },
            "type": "InputTriggeringRecordInitial"
          },
          {
            "leftValueReference": "ScheduledPathApiName",
            "value": { "stringValue": "" },
            "type": "ScheduledPath"
          }
        ],
        "assertions": []
      }
    ],
    "flowTestDataSources": [],
    "isolatedObjectExternalKeys": [],
    "doesCommitChanges": false,
    "doesSkipStartConditions": false
  }
}
```

A `WithAssertion` save (`brandNewTest`) — full trigger record on
`Start`, plus a `Finish`-element assertion that `Set_Name_To_BAC` was
visited:

```json
{
  "fullName": "brandNewTest",
  "metadata": {
    "label": "brandNewTest",
    "description": "",
    "flowApiName": "Update_Account_Name_To_BAC_TEMP_20260521-2",
    "flowTestFlowVersions": [
      { "flowVersionNumber": "2" },
      { "flowVersionNumber": "1" }
    ],
    "testType": "WithAssertion",
    "testPoints": [
      {
        "elementApiName": "Start",
        "parameters": [
          {
            "leftValueReference": "$Record",
            "value": {
              "sobjectValue": "{\"AccountNumber\":\"CD656092\",\"Name\":\"Burlington Textiles Corp of America\",\"BillingCity\":\"Burlington\",\"BillingState\":\"NC\",\"Industry\":\"Apparel\",\"Type\":\"Customer - Direct\"}"
            },
            "type": "InputTriggeringRecordInitial"
          }
        ],
        "assertions": []
      },
      {
        "elementApiName": "Finish",
        "parameters": [],
        "assertions": [
          {
            "conditions": [
              {
                "leftValueReference": "Set_Name_To_BAC",
                "operator": "WasVisited",
                "rightValue": { "booleanValue": true }
              }
            ]
          }
        ]
      }
    ],
    "flowTestDataSources": [],
    "isolatedObjectExternalKeys": []
  }
}
```

## Constraints

### Source-of-truth principle: round-trip, don't guess

Hand-written or example payloads are starting points, not authority.
The Aura wire format normalizes shapes — string-form numbers come back
as JSON numbers, optional fields appear with default values, etc.
**When in doubt, save once with `POST /services/data/vXX.0/flowbuilder/flow-test`/`PATCH /services/data/vXX.0/flowbuilder/flow-test/{id}` and
reload with `GET /services/data/vXX.0/flowbuilder/flow-test/{id}`** — parse the returned `flowTestJson` string;
that decoded definition is the canonical form for that org/release.
Update this file when a round-trip shows something the prose doesn't cover.

Worth knowing up front from probe runs:

- `POST /services/data/vXX.0/flowbuilder/flow-test`/`PATCH /services/data/vXX.0/flowbuilder/flow-test/{id}` run **deep server-side validation** on
  save. A malformed payload — bad `type` enum, mismatched value
  envelope, a `leftValueReference` that doesn't resolve to a flow
  resource or element, duplicate test points, a missing required
  parameter — can come back `isSuccess: false` with optional `errors[]`
  details. Fix a field only when a message identifies it; otherwise
  surface the raw response. Don't pre-check against a memorized rule list.
  A confirmed `isSuccess === true` response means the
  payload is well-formed and every reference resolves — but still run the
  test, because save cannot verify that an assertion's *expected value*
  is the one you meant (a semantically-valid-but-wrong expectation saves
  clean and only fails when run).
- `numberValue` accepts both `"40"` and `40` on save but the canonical
  form is the unquoted JSON number. Round-trip will normalize.
- The `value` envelope always carries `collectionElements: []` after
  canonicalization. Omitting it on save is fine; the server fills it.

> **Field discovery via round-trip.** Both `doesTestWaitElement` and
> `isSubflowUseLatestFlowVer` were discovered by saving a minimal
> payload and parsing `GET /services/data/vXX.0/flowbuilder/flow-test/{id}.flowTestJson`. When the
> docs feel incomplete, save a probe and reload.
