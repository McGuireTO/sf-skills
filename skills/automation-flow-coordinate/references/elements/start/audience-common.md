---
name: flow-element-start-audience-common
license: LICENSE.txt has complete terms
description: "Shared build contract for ALL audience-triggered flows — the run schedule, top-level `timeZoneSidKey`, top-level `dataSpace`, optional `dataGraph`, re-entry (`entryType`), the save-and-activate gates, and the builder round-trip defaults common to `triggerType` `Segment`, `List`, `CampaignMember`, and `RecordQuery` (they all share Core's `BaseAudienceTriggerTypeHandler`). Load this FIRST, then load the per-trigger binding guide: `segment-triggered.md`, `list-campaignmember.md`, or `recordquery.md`. Covers only what is identical across the four; the audience binding and record context live in the per-trigger files. DO NOT load for RecordAfterSave, Scheduled, PlatformEvent, or any non-audience trigger."
metadata:
  version: "1.0"
  related-skills: flow-element-start, flow-flow-properties, flow-element-wait
---

# Audience-Triggered Flows — Shared Contract

Load this **first** for any audience-style trigger, then load the matching
binding guide for how the audience is bound and referenced:

| Trigger | UI name | Audience | Binding guide |
|---|---|---|---|
| `Segment` | Segment Flow | a marketing **Segment**'s individuals (Data Cloud) | `segment-triggered.md` |
| `List` | List Flow | an **Actionable List**'s members | `list-campaignmember.md` |
| `CampaignMember` | Campaign Member Flow | a **Campaign**'s members (Contacts/Leads) | `list-campaignmember.md` |
| `RecordQuery` | Record Query | **all records of one SObject** matching a filter | `recordquery.md` |

All four enter an audience of members when the flow runs and share one Core base
— `BaseAudienceTriggerTypeHandler` (→ `DefaultScheduledTriggerTypeHandler`) —
which is why the run schedule, `timeZoneSidKey`, `dataSpace`, `dataGraph`,
`entryType`, and the save-and-activate gates below are **identical** across them.
The only per-trigger differences are the **audience binding** and the
**record-context handle** — both documented in the per-trigger guides.

## Reference File Index

| File | Purpose |
|---|---|
| `examples/segment-weekly-schedule.json` | Weekly run-schedule start-element example (schedule shape is shared by all four triggers) |
| `segment-triggered.md` | Bind + reference a `Segment` audience |
| `list-campaignmember.md` | Bind + reference a `List` or `CampaignMember` audience |
| `recordquery.md` | Bind + reference a `RecordQuery` audience |

## processType, activation, and Draft status

- **processType** is always `AutoLaunchedFlow` for all four triggers. Author it for
  both `POST /services/data/vXX.0/flowbuilder/flow/actions/save` and legacy `saveAndValidateFlow`
  lifecycles. Do not substitute `Journey` based on the builder surface name or a
  Connect enum member.
- Keep `processType: "AutoLaunchedFlow"` when activation must happen in the UI. A
  save yields a **Draft**; activation is a user action in the builder (the
  `POST /services/data/vXX.0/flowbuilder/flow/{flowId}/actions/activate` endpoint (activateFlow — DO
  NOT DISPATCH, quarantined) is disabled for every flow type — a 404 from it does
  NOT indicate a process-type mismatch). Open the version with
  `builderType=JourneyBuilder` and let the user activate it there. See
  `../../shared/preview-renderer.md`.
- With the Core HTTP lifecycle, **omitting `start.triggerType`** makes Core
  validate the flow as a plain autolaunched flow; audience-only actions then fail
  with `ACTIONCALL_NOT_SUPPORTED_FOR_PROCESSTYPE`. Always set the trigger type.
- A Core save with `isSuccess: true` and `status: "InvalidDraft"` is **not**
  complete. Fix every missing/blocking warning and save again until
  `status: "Draft"`. A save returning `isSuccess: true` **with warnings** is not
  "done" — clear all four `WARNING_BLOCK_ACTIVATION` gates below or the draft
  can't be activated.

## Requirements to save-and-activate (all four triggers)

Inherited from `BaseAudienceTriggerTypeHandler`. Each validates as
`isSuccess: true` even while missing, but each is a `WARNING_BLOCK_ACTIVATION`
that stops the draft going live — set all four on the **first** save:

1. **Audience selection** — per-trigger; see the binding guide. (`Segment`:
   `start.segment` + `start.object`; `List`/`CampaignMember`: `start.listAction`;
   `RecordQuery`: `start.object`.) Each has its own missing-audience error.
2. **Run schedule** — `start.schedule.frequency` is required (see [Run schedule](#run-schedule)).
   Missing → `FLOW_SCHEDULE_INFORMATION_INCOMPLETE`.
3. **Time zone** — top-level `metadata.timeZoneSidKey` (see [timeZoneSidKey](#timezonesidkey--top-level-and-required)).
   Missing → `TIME_ZONE_REQUIRED_FOR_TRIGGER_TYPE`.
4. **Data space** — top-level `metadata.dataSpace` (see [Set the data space](#set-the-data-space)).
   Missing → `DATA_SPACE_REQUIRED_FOR_FLOW_TYPE`.

Fault paths are **not** among these requirements. An audience-triggered flow is
a marketing flow: add a `faultConnector` or error-handling branch only when the
user asks for error handling. A flow with no fault paths saves and activates.
See `../../shared/fault-paths/fault-paths.md` § Marketing Flows — Fault Paths Only When Asked.

## Run schedule

An audience flow's cadence is its **run schedule** (`start.schedule`) — NOT a
Scheduled-flow trigger. The fields below are the ones the platform's validator
actually checks, and its feedback is misleading: it reports a *missing* timezone
when the value is merely mis-placed, and conditional-field errors only surface
after a save. So a wrong shape almost never self-corrects — get it exact up front.

- **`frequency: "OnActivate"`** runs when the flow is activated and needs **no**
  `startDate`/`startTime` — the right default when the prompt names no cadence.
- Every other frequency needs `startDate` + `startTime`.

| Field | Type | When | Notes |
|---|---|---|---|
| `frequency` | string | always | One of `OnActivate`, `Once`, `Hourly`, `Daily`, `Weekdays`, `Weekly`, `Monthly`, `Yearly` |
| `startDate` | string (date) | always (except `OnActivate`) | e.g. `"2026-06-01"` |
| `startTime` | string (time) | always (except `OnActivate`) | e.g. `"09:00:00.000"` |
| `frequencyNumber` | integer ≥ 1 | required for `Hourly`, `Weekly`, `Monthly` | number of units between runs |
| `daysOfWeekToRun` | string | required for `Weekly` | numeric day codes — see below |
| `dayOfMonthToRun` | integer | required for `Monthly` | `1`–`31`, or `-1` for last day of month |

- **`Weekly`:** set `frequencyNumber` (integer ≥ 1) **and `daysOfWeekToRun` as a comma-separated string of numeric day codes** — **1=Sunday, 2=Monday, 3=Tuesday, 4=Wednesday, 5=Thursday, 6=Friday, 7=Saturday.** Use the NUMBER, not the day name, and not a list: "every Tuesday" → `"3"`; "Monday and Wednesday" → `"2,4"`; "Tuesday and Thursday" → `"3,5"`. The platform enforces the regex `^([1-7](,[1-7])*)$`; a day name like `"Tuesday"` is rejected with "Enter a valid value for the Days of Week to Run field."
- **`Monthly`:** set `dayOfMonthToRun` (a scalar integer `1`–`31`, or `-1` for the last day). `dayOfMonthToRun` is allowed ONLY for `Monthly`.
- **`Daily` takes NO `frequencyNumber`.** `frequencyNumber` is allowed only for `Hourly`, `Weekly`, and `Monthly` — setting it on a `Daily` (or `Weekdays`/`Yearly`/`Once`) schedule fails with `INVALID_FIELD_FOR_CONFLICTING_FIELD_VALUE`. **There is no N-day-interval frequency**: "every 3 days" is NOT expressible as a single schedule. Model it as plain `Daily` (dropping the interval) or with an in-flow `Wait` loop — do NOT emit `Daily` + `frequencyNumber: 3`.
- **`Weekdays`** is a standalone frequency meaning Monday–Friday. It takes neither `frequencyNumber` nor `daysOfWeekToRun` — both are rejected.
- **Value caps:** `Hourly` `frequencyNumber` ≤ 168; `Monthly` `frequencyNumber` ≤ 12; both ≥ 1. `dayOfMonthToRun` out of range (not 1–31 and not -1) fails with `WAITEVENT_INVALID_VALUE`; a malformed `daysOfWeekToRun` string fails with `FLOW_START_INPUT_REQUIRED`.

### Worked example — "every Tuesday and Thursday at 9 AM Eastern"

See `examples/segment-weekly-schedule.json` for the start-element shape — note
`daysOfWeekToRun` is the numeric-code string `"3,5"` (Tue + Thu), never
`["Tuesday","Thursday"]`. The required `timeZoneSidKey` (`"America/New_York"`) is
**not** part of that snippet: it lives at the flow's top level
(`metadata.timeZoneSidKey`, a sibling of `start`), per the placement rule below —
never inside `schedule` or on the Start element.

## timeZoneSidKey — top-level and REQUIRED

- **`timeZoneSidKey` is a REQUIRED top-level flow property — a sibling of `start` inside `metadata` (`metadata.timeZoneSidKey`), NEVER `start.timeZoneSidKey`.** Both omitting it and mis-placing it on the start element fail as `TIME_ZONE_REQUIRED_FOR_TRIGGER_TYPE` (the placement error misleadingly reads as "no timezone supplied").
- Value is an IANA timezone id, e.g. `"America/New_York"`. A bogus id fails with `INVALID_TIME_ZONE`.
- **Which value when the user is silent: default to the org default timezone — do NOT ask the user to pick one.** Resolve the org default from the org itself (`SELECT TimeZoneSidKey FROM Organization`, the running user's `TimeZoneSidKey`, or the `timeZoneSidKey` on an existing active flow in the org). Only use a specific IANA id when the user explicitly names a timezone. Because an audience flow *cannot* omit `timeZoneSidKey` (unlike a plain AutoLaunchedFlow, which must omit it), "default timezone" here means **auto-fill the org default**, never blank. See the Wait timezone rule in `../wait/wait.md`.

## Set the data space

Required. Set `dataSpace` on the **top-level** flow object (`metadata.dataSpace`,
API ≥ 258) to a data space's `name` (e.g. `"default"`), resolved through `dispatch`/`dispatch_readonly` by
**either** path:
- SOQL via `dispatch_readonly({ url: "/services/data/vXX.0/query", method: "GET", queryParams: { q: "SELECT Id, Name FROM DataSpace" } })` → `records[]`, each `{Id, Name}`. Use `Name`.
- the Data 360 tool `d360_dataspace_list` (`dispatch` POST to `/services/data/vXX.0/ssot/mcp/execute`, `paramsJson: "{\"batchSize\": 50, \"offset\": 0}"`) → `result.dataSpaces[]`, each `{id, label, name, status}`. Use `name`, not `id` or `label` — this path also yields `label`/`status`.

1. Only one data space → use it silently.
2. Multiple + user specified one → match by `name`/`label` and use that.
3. Multiple + user didn't specify → ask which data space to use. Do not guess a default.

- **List/CampaignMember/RecordQuery audiences are Core records (ActionableList / Campaign / an SObject), not Data-Cloud assets, so their home data space isn't resolvable through the Data 360 tool** — default to the org default and surface the assumption at the plan gate. The SOQL path above still resolves the data space itself either way.
- For `sendToJourney` (a Segment flow), also require the selected business unit's `businessUnitsToDataSpaces[].dataSpaceName` to equal this `name`. Follow `../action-call/send-to-journey.md` for business-unit and Journey selection.

## Set the data graph

Optional. Set `dataGraph` on the **start element** (`metadata.start.dataGraph`) to
a data graph's `developerName`, resolved via the Data 360 tool
`d360_datagraph_metadata` (`dispatch`): `dispatch({ url: "/services/data/vXX.0/ssot/mcp/execute", method: "POST", body: { toolName: "d360_datagraph_metadata", paramsJson: "{\"dataspace\": \"<the dataSpace name from above>\"}" } })` → `result.dataGraphMetadata[]`, each `{developerName, dataspaceName, dgObject: {developerName: <backing DMO>, relatedObjects: [...], ...}}`. Omit
`dataGraphEntityName` in `paramsJson` to list every graph in that data space; add a
specific `"dataGraphEntityName"` to fetch just that graph's full schema. (This
metadata tool is the source for the graph's backing DMO and related-object schema;
a `DataGraph` SOQL query returns only `DataGraphApiName`/`PrimaryDmo`/`Status`, not
`relatedObjects`.)

1. User specifies a data graph → use its `developerName`. If no data space was specified, use that graph's own `dataspaceName`.
2. User specifies both → verify the graph's `dataspaceName` matches the data space chosen above. If it doesn't, ask the user how to proceed.
3. User does NOT specify a data graph → leave it blank.

## Re-entry — `entryType` on the Start element

`entryType` governs whether — and *when* — a single member who has **already
entered** the flow may enter it **again**. Omit unless the prompt restricts re-entry.

| Re-entry for a member who already entered | `entryType` |
|---|---|
| may enter again any time, even while a prior run is still in progress (default) | omit (= `Always`) |
| may enter again, but only after finishing the current run — no two overlapping runs for the same member | `AfterCompletion` |
| may never enter more than once | `Never` |

Write `entryType` only as `AfterCompletion` or `Never`. When the prompt says
nothing about re-entry, leave `entryType` out of the Start. A made-up value such
as `AllRecords` stops the flow from activating: `'AllRecords' is not a valid value for the enum 'FlowEntryType'`.

## Record context ($Input / $Record) — globals available

The **per-trigger member handle** is documented in each binding guide, because it
differs by trigger: List / CampaignMember / RecordQuery expose the member row on
`$Input.…`; **Segment exposes the member as `$Record`** (a row of the segment's DMO,
e.g. `$Record.ssot__FirstName__c`; see `segment-triggered.md`). The global
availability:

| Global | Available? | Notes |
|---|---|---|
| `$Input` | Yes for List / CampaignMember / RecordQuery; No for Segment | Trigger-input container. Member handle is per-trigger; **not** exposed for Segment. |
| `$Record` | Segment only | In a Segment flow, the current member (a row of the `segmentOnApiName` DMO): write `$Record.<field>`, never the bare field name. Not available for List / CampaignMember / RecordQuery. |
| `$Contact` / `$Lead` / `$Prospect` | No | Not exposed for audience triggers — use `$Input` (List/CampaignMember/RecordQuery) or `$Record` (Segment). |
| `$Flow.*` | Yes | `CurrentDate`, `CurrentDateTime`, `InterviewStartTime`, `InterviewGuid`, `FaultMessage` |

## What the builder normalizes on save (round-trip defaults)

A save through the builder rewrites the metadata with a default skeleton.
Engine-supplied — do NOT hand-author, and don't treat their appearance on a
retrieve as drift:

- **Metadata level:** `accessType: "NamespaceRestricted"`, `areMetricsLoggedToDataCloud: true`, every element collection present as `[]`.
- **`schedule`** with `OnActivate`: `dayOfMonthToRun: 0`, `frequencyNumber: 0` (zero placeholders — not a cadence).
- The save stays on the same Draft version (no new version created).
- The **per-binding** skeleton (the `listAction` FlowActionCall fields, or the RecordQuery Start skeleton) is documented in the binding guides.
