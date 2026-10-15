---
id: flow.recipes.testing.workflows.debug
description: "Pure debug workflow — interactive run-trace-refine loop on an existing flow with no test artifact produced. Three phases: Setup → Iterate → Decide. Endpoint chosen by probing `TestModeExperience` support; offers promotion to a saved FlowTest at end."
---

<!-- Consumers: testing router -->

# Debug a flow (no test artifact produced)

Use when the user is investigating "did my flow do X?" or "why did the flow do Y?" with no upfront intent to save a test. The workflow is driven by the two debug-run endpoints covered in `## Tool routing`, plus a small set of supporting tools as the run demands: `POST /services/data/vXX.0/flowbuilder/flow-test/debug-interview-resume` (continue a run paused at a Wait element), `GET /services/data/vXX.0/flowbuilder/flow-test/record-run-data` (drill into one record of a multi-record run), `GET /services/data/vXX.0/flowbuilder/flow-test/interview-history` (inspect prior runs of this flow version), and `GET /services/data/vXX.0/flowbuilder/flow-test/debug-run-as-validation` (pre-flight guard for debug-as-another-user). At the end of the iterate loop the user is offered a promotion path to `[[flow.recipes.testing.workflows.promote]]` — that is the **only** way to produce a persistent FlowTest from this workflow.

This skill is only intended to be used with Supported Flow Process Types listed below, even though debugging is available for a broader list of process types via the Flow Builder.

---

## Supported flow process types

Match `(processType, metadata.start.triggerType)` from `GET /services/data/vXX.0/flowbuilder/flow/{id}` against this allow-list before any run work. Treat an absent `triggerType` as `None`.

| `processType` | `triggerType` | Shorthand | Debug workflow |
|---|---|---|---|
| `AutoLaunchedFlow` | `RecordBeforeSave` | Record-triggered (RT) | Supported |
| `AutoLaunchedFlow` | `RecordAfterSave` | Record-triggered (RT) | Supported |
| `AutoLaunchedFlow` | `None` (or absent) | Autolaunched (ALF) | Supported |
| `AutoLaunchedFlow` | `Scheduled` | Scheduled | Supported |
| `AutoLaunchedFlow` | `Segment` | Segment-triggered | Supported |
| `AutoLaunchedFlow` | `AutomationEvent` | Automation-event-triggered | Supported |
| `AutoLaunchedFlow` | `IndivRelatedRecord` | Individual-related-record-triggered | Supported |
| `AutoLaunchedFlow` | `List` | List-triggered | Supported |
| `AutoLaunchedFlow` | `FormSubmissionEvent` | Form-submission-event-triggered | Supported |
| `AutoLaunchedFlow` | `CampaignMember` | Campaign-member-triggered | Supported |
| `Flow` | `None` | Screen flow | **Not supported** — hand back to the testing router |
| `AutoLaunchedFlow` | `PlatformEvent` | Platform-event-triggered | **Not supported** — hand back to the testing router |
| Any other combo | | — | **Not supported** — hand back to the testing router |

If unsupported, STOP before the routing probe and surface: "This workflow currently supports the above listed process types. `<processType>` × `<triggerType>` is out of scope." Do not proceed to the routing probe or Phase 2.

---

## Tool routing

Two endpoints exist for running debug iterations. Neither is a default — the workflow probes the flow's `(processType, triggerType)` combo and picks based on whether the org / flow-type supports test mode:

- **`POST /services/data/vXX.0/flowbuilder/flow-test/debug-interview-test-mode`** — payload-driven behavior. Takes the FlowTest as `flowTestJson` (a JSON-**encoded string** of the same definition `POST /services/data/vXX.0/flowbuilder/flow-test`/`PATCH /services/data/vXX.0/flowbuilder/flow-test/{id}` consumes, unsaved). Rolls back unless the test's `doesCommitChanges` is `true`.
- **`POST /services/data/vXX.0/flowbuilder/flow-test/debug-interview`** — argument-driven DML behavior. Required `flowVersionId`; optional `flowDevName`, `arguments` (input vars as a JSON string). Commits when `enableRollbackMode` is `false` (default).

### Routing probe

**Mandatory before the first debug run.** The probe is the ONLY sanctioned way to pick between the two endpoints — do NOT infer the choice from the user's prompt phrasing (mentions of "test mode", "rollback", etc.), the tool-list order, or prior conversation.

Call `dispatch_readonly(method: "GET", url: "/services/data/vXX.0/flowbuilder/schema/flow-capabilities")` (read `.flowFeatures`) for the flow's `(processType, triggerType)` and inspect the returned feature-name list for **`TestModeExperience`**:

- **`TestModeExperience` present** → use `POST /services/data/vXX.0/flowbuilder/flow-test/debug-interview-test-mode`
- **`TestModeExperience` absent** → use `POST /services/data/vXX.0/flowbuilder/flow-test/debug-interview`.

Cache the probe result for the session — the feature list does not change within one Aura session. For both endpoints, default to rollback debug option (no DML commits) unless explicitly approved by user.

### Resume endpoint

A run that stops at a Wait element is continued with a third call, whichever run endpoint started it:

- **`POST /services/data/vXX.0/flowbuilder/flow-test/debug-interview-resume`** — required `flowVersionId` plus four values fed back **verbatim** from the paused result: `serializedInterview`, `resolvedContext`, `serializedCumulativeDebugInfo`, `waitEvent`. `waitEvent` is the **`name`** of one entry in the result's `waitEvents[]`, never its `value`; a blank `waitEvent` makes the resume fail. Returns a single `{runInterviewResult, canvasDecorator}`, not a `results[]` array.

The server does **not** check that a resume's settings match the original run, so the workflow does (see `### Paused runs` in Phase 2).

---

## Phase 1 — Setup

Load `[[flow.recipes.testing.shared-stages.intent-analyzer]]`.

The Intent Analyzer in this workflow is responsible for:

1. **Confirming debug intent.** This is run-trace-refine, not test authoring and not promotion. If the user wants to author a test from scratch, hand back to the testing router; it should route to `[[flow.recipes.testing.workflows.author-test]]`.
2. **Identifying the flow.** Read the parent flow via `GET /services/data/vXX.0/flowbuilder/flow/{id}`. Capture `processType`, `metadata.start.triggerType`, the flow's input variables (for non-triggered flows), and the active version ID.
3. **Eligibility check.** Match `(processType, triggerType)` against the allow-list in `## Supported flow process types`. If the combo isn't on the allow-list, STOP: surface the ineligibility per that section and hand back to the testing router. **Do not** check for `"FlowTesting"` here — debug runs work for shapes (like scheduled) that cannot be saved as tests.
4. **Route the run endpoint.** Call `dispatch_readonly(method: "GET", url: "/services/data/vXX.0/flowbuilder/schema/flow-capabilities")` (read `.flowFeatures`) for the flow's `(processType, triggerType)` and inspect for `TestModeExperience` per `## Tool routing`. Cache the result on the session. If test mode is absent, surface the constraint to the user now (before any input work) and gate on host-quoted confirmation; do not proceed to input-gathering until confirmed.
5. **Assemble the run inputs for the routed endpoint.** The test-mode endpoint takes a full `FlowTest` definition (same shape as `POST /services/data/vXX.0/flowbuilder/flow-test`/`PATCH /services/data/vXX.0/flowbuilder/flow-test/{id}`, unsaved), JSON-encoded into its `flowTestJson` **string** field — hand off to `[[flow.recipes.testing.shared-stages.payload-builder]]` to build it in memory, then serialize it. The non-test-mode endpoint takes flat ad-hoc arguments (required `flowVersionId`; optional `flowDevName`, JSON-encoded `arguments`).

6. **Offer pausing at Wait elements.** If the Intent Analyzer's `flowShape.hasWaits` is `true`, tell the user the flow has Wait elements and propose debugging with pausing enabled, so the run stops at a Wait instead of running past it. Enable it per the routed endpoint:
   - **`debug-interview`** — set `debugWaits: true` on the request.
   - **`debug-interview-test-mode`** — set `doesTestWaitElement: true` inside the `flowTestJson` definition. Core only allows this for autolaunched flows with no trigger, and a Wait that the test mocks never pauses. If pausing isn't available for this flow shape, say so plainly rather than offering it.

   Pausing is opt-in: if the user declines, leave it off and run as before.

Phase 1 emits: `{flow, processType, triggerType, runEndpoint, runInputs, activeVersion, debugWaits}`. No write-side tool calls other than the read-only routing probe.

---

## Phase 2 — Iterate

The run → trace → refine loop. The user stays in this phase as long as they want.

### Loop body

1. **Run.** Call the endpoint selected by the Phase 1 routing probe (per `## Tool routing`). If the probe hasn't run yet in this session, STOP and run it now — do NOT guess between the two endpoints from prompt phrasing, tool-list order, or prior conversation. Both run endpoints return a `results[]` array — **one entry per debugged record** (`{runInterviewResult, canvasDecorator}`), so a high-scale record-triggered flow can produce several. Iterate `results[]`; for a single-record flow it has one entry. **Capture each entry's run identifier** — this same value is the `interviewGUID` for `GET /services/data/vXX.0/flowbuilder/flow-test/interview-history`, the `flowRunId` for `GET /services/data/vXX.0/flowbuilder/flow-test/record-run-data`, and the `interviewId` handed to `[[flow.recipes.testing.workflows.promote]]` (for a multi-record run, pick the record you want to promote). To drill into one record's run after a multi-record debug, call `GET /services/data/vXX.0/flowbuilder/flow-test/record-run-data` with that record's `flowRunId` + `flowVersionId`. If a result's `interviewStatus` is `WAITING` or `ASYNC_WAITING`, the run is paused at a Wait element — follow `### Paused runs` below instead of treating it as finished.
2. **Render the trace in two layers.** Emit the **Headline** layer using the verbatim skeleton and worked example in `examples/debug-output-template.md` — same headers, same order, every section present even if a section is `None`. Do not paraphrase headers, merge sections, or reorder. The **Details** layer is on-demand only (do not emit unless the user asks).

   - **Details (raw, on demand).** Only when the user asks ("show raw trace", "deep dive", "why did element X…"), surface the `executionLog`, element-level inputs/outputs, and any fault paths taken. Scope to what they asked about — do not dump the full raw trace by default.
3. **Ask the user what's next:**
   > Deep dive into execution details? Refine inputs? Try a different scenario? Or save this run as a test?
4. **Three valid responses:**
   - **Refine** → mutate the payload (new record ID on the `$Record` test-point, different `parameters[]` values, switch scheduled path), loop back to step 1. **Discard any paused-run state** (see `### Paused runs`) — a paused interview belongs to the inputs that produced it and must never be resumed on top of changed ones.
   - **New scenario** → discard the current payload, re-gather from the user, rebuild via the payload-builder, loop back to step 1. Treat as a fresh iteration; old `interviewId` and any paused-run state are not reused.
   - **Save / promote** → exit Phase 2, go to Phase 3.

### Paused runs

A run is **paused** when a result's `interviewStatus` is `WAITING` (stopped at a Wait element) or `ASYNC_WAITING`. Do not test for `PAUSED` — that is a different engine status, even though the endpoint's schema example mentions it.

1. **Say it's paused.** Render the headline with the `### Paused` block from `examples/debug-output-template.md` (see that file for the exact shape), not a "finished" summary.
2. **Enumerate the resumable events.** `waitEvents[]` is a list of `{name, value}`: `name` is the wait event's API name, `value` is its resume time (empty for a platform-event wait). Show both and ask which event to resume. If there is only one, still confirm before resuming.
3. **Resume** with `POST /services/data/vXX.0/flowbuilder/flow-test/debug-interview-resume`, passing the chosen event's **`name`** as `waitEvent` and the paused result's `serializedInterview`, `resolvedContext` and `serializedCumulativeDebugInfo` verbatim.
4. **Keep the debug settings identical.** Send the same `enableRollbackMode`, `debugAsUserId`, `enableTrace` and `showGovernorLimit` as the original run, and do not change `arguments`. The server does not compare them, so a mismatch silently changes rollback or run-as behavior partway through one run. `useLatestSubflow` is ignored on resume; do not rely on it.
5. **Append, don't restart.** Add the resumed leg's results to the existing trace and render one cumulative headline (Summary covers the run so far). A resumed run can pause again: repeat from step 1 until the status is no longer waiting.
6. **Warn about rollback once.** Each leg is committed or rolled back on its own, so with rollback on, DML from earlier legs is already undone when the resume runs. Values carried over from an earlier leg (for example a new record's Id) may point at records that no longer exist. Say this before the first resume.
7. **Record that the run paused.** If any leg paused, the final scenario is `paused` for Phase 3 and `[[flow.recipes.testing.workflows.promote]]`.

Paused-run state is `{serializedInterview, resolvedContext, serializedCumulativeDebugInfo, waitEvents}`. Hold it only until the next run; **refine** and **new scenario** discard it (see the loop's step 4).

**When the user requests a past-run trace** ("what did this flow do recently?"), call `dispatch_readonly(method: "GET", url: "/services/data/vXX.0/flowbuilder/flow-test/interview-history")` with the run's `interviewGUID` + `flowVersionId` (both **required**; the query param is `interviewGUID`, NOT `interviewId`). History is returned only when its captured version matches the supplied `flowVersionId` — **per-flow-version**. Historic forensic queries across unrelated flow versions are out of scope.

### Stop conditions inside the loop

- User signals satisfaction with the run ("looks good", "that's it") → offer promotion in Phase 3.
- User abandons ("never mind", "stop") → exit gracefully, no Phase 3.
- 3 consecutive iterations with the same input pattern producing the same failure → STOP and surface the failure to the user. Don't spiral; ask for direction.
- Aura session error (`aura:invalidSession` / `Aura HTTP 401`) → STOP, run `agentic-flow-poc-setup`, do not retry the failing call automatically.

---

## Phase 3 — Decide

The promotion offer. Brief and explicit.

> Would you like to save this debug run as a persistent test?
> 
> Reply **"yes"** to convert this scenario into a FlowTest record (320xxx) for regression. Reply **"no"** or **"end"** to wrap up.

Three valid responses:

- **Yes / save** → hand off to `[[flow.recipes.testing.workflows.promote]]` with the debug context: `{interviewId, serializedInterview?, inputs, trace, flowVersionId, paused}`. Capture the `serializedInterview` blob if it's available (Route B needs it, not the id); if it isn't, promote falls back to Route A. Set `paused: true` if the run paused at any point. Promote will check the narrower save-as-test eligibility, build the payload, validate, save, and verify.
  - **Paused or resumed runs can only be saved as a `WithoutAssertion` test.** Say so before the hand-off: "This run paused at a Wait, so it can be saved only as a test without assertions." Do not offer to derive assertions from a paused or resumed trace.
- **No / end** → wrap up. Show one-line summary of what was iterated. Do not save anything.
- **Not sure / what does that do?** → explain in one paragraph what a saved FlowTest gives them (regression coverage, re-runnable, tied to a flow version, contributes to coverage decorators), then re-ask.

If the flow is debug-eligible but not save-eligible (scheduled `AutoLaunchedFlow`), pre-empt the promotion offer: tell the user the run was useful but cannot be saved as a `FlowTest` for this flow shape. Skip Phase 3's question.

---

## Error recovery

**Session expired mid-iterate.** STOP, run `agentic-flow-poc-setup`. The `interviewId` from previous iterations is bound to the old session and may not be retrievable in interview-history. The user can re-run the same inputs after re-auth.

**Record not found.** The user supplied a record ID that doesn't exist in the target org. Surface the failure verbatim, ask for a different ID. Don't auto-retry with a guessed ID.

**Flow version mismatch.** The active version changed mid-session (someone activated a new version). The next run will execute the new active version. Surface this once: "Flow version changed — runs will now execute v<N>." Subsequent runs continue normally.

**User asked for real DML without quoting the org host.** Don't proceed. Re-ask per `## Tool routing`: "Real DML against `<orgHost>`? Quote the host explicitly to confirm."

**Resume fails.** Most often `waitEvent` was blank or was the event's `value` instead of its `name`, or the run was not actually paused. Surface the error verbatim, re-list `waitEvents[]` from the paused result, and ask again. Do not guess an event or retry the same call.

**Session expired while paused.** The paused state is bound to the old session and cannot be recovered. Tell the user the paused run is lost and offer to re-run from the start with the same inputs.

**Run returns a fault.** A flow element hit an error and took a `faultConnector` (or unhandled, in which case the flow halts). Show the fault in the headline ("the flow failed at element `<X>` because `<reason>`") and offer the raw stack in the details. Then ask whether to refine inputs to avoid the fault or treat the fault as the scenario to lock in (which routes to Phase 3 for promotion).

---

## Notes for callers

- Tool routing is discussed in `## Tool routing` — the default and the two ways to opt into committing DML are covered there.
- The final iteration's context is the handoff to `[[flow.recipes.testing.workflows.promote]]`. Route A (clean re-state) needs the `inputs`; Route B (shortcut via `POST /services/data/vXX.0/flowbuilder/flow-test/actions/generate-from-debug-run`) needs the `serializedInterview` blob from the run — **not** the `interviewId`. Capture the serialized interview if Route B is a possibility; if only the id is available, Route B is off and promote uses Route A.
- Tool budget: 1 `GET /services/data/vXX.0/flowbuilder/flow/{id}` + 1 `GET /services/data/vXX.0/flowbuilder/schema/flow-capabilities` (read `.flowFeatures`) at start, then N iterations of the routed run endpoint. Optional, as the run demands: 1×`POST /services/data/vXX.0/flowbuilder/flow-test/debug-interview-resume` per pause, 1×`GET /services/data/vXX.0/flowbuilder/flow-test/record-run-data` per record drill-in, 1×`GET /services/data/vXX.0/flowbuilder/flow-test/interview-history` per history lookup, and a one-time `GET /services/data/vXX.0/flowbuilder/flow-test/debug-run-as-validation` pre-flight when debugging as another user. Each call is one Aura call. Cap run iterations at 10 before pausing to summarize and ask for direction.
- **Debug as another user.** To run the interview as a different user (`debugAsUserId` on `dispatch(method: "POST", url: "/services/data/vXX.0/flowbuilder/flow-test/debug-interview")`), call `dispatch_readonly(method: "GET", url: "/services/data/vXX.0/flowbuilder/flow-test/debug-run-as-validation")` FIRST as a pre-flight guard — pass `flowVersionId` or `flowDevName`; it returns `{showIsDebugAsUserAllowed, showIsDebugAsUserAllowedInNonPrd}` (NOT `{canDebug}`), validating the debug-**as-another-user** permission (prod + non-prod). Only pass `debugAsUserId` when allowed.
- This workflow is **per-session**: state (`interviewId`, last inputs, last trace) does not persist across Aura sessions. If the user wants persistence, that's exactly what the promotion offer in Phase 3 is for.
