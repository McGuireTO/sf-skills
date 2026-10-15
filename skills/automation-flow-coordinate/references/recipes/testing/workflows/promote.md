---
id: flow.recipes.testing.workflows.promote
description: "Debug-to-test promotion bridge — converts a satisfactory debug run into a persistent FlowTest record. Skips Phases 1–2 of author-test (intent and plan are already established by debug iteration); enters at Phase 3 (Build) with debug context."
---

<!-- Consumers: debug.md (Phase 3 hand-off), testing router (direct entry when user says "promote my last debug run") -->

# Promote a debug run to a saved FlowTest

A transition workflow, not a workflow in the same sense as author-test or debug. The user has already done the iteration in `[[flow.recipes.testing.workflows.debug]]` and decided the run is worth keeping. Promote does the narrow save-as-test eligibility check, builds the payload (two routes available), validates, saves, and verifies.

## Why promotion skips Phases 1–2 of author-test

The author-test pipeline's first two phases are about **establishing intent and a test plan**. Promotion arrives with both already established:

- **Intent** — the user iterated until the run was right. The trace observed in debug *is* the intent.
- **Plan** — the inputs used in the final debug iteration *are* the plan. The user already approved them implicitly by saying "save this".

Re-running Phases 1 and 2 here would be redundant ceremony. Promotion lands directly at the **Build** equivalent (Phase 3 of author-test) with the debug context as the seed payload. The Reviewer (Phase 4) and Save & Run (Phase 5) phases of author-test still execute, because the payload still has to pass the server's save-time validation and the run still has to confirm the assertions — regardless of how the payload was constructed.

---

## Inputs from caller

From `[[flow.recipes.testing.workflows.debug]]` Phase 3 hand-off, OR direct from the testing router:

- `interviewId` — the debug run to promote (most recent if router-direct).
- `serializedInterview` (Route B only) — the serialized debug-run interview blob captured from the run. `POST /services/data/vXX.0/flowbuilder/flow-test/actions/generate-from-debug-run` requires this blob, **not** the `interviewId`. If it wasn't captured, Route B is unavailable — use Route A.
- `inputs` — the input set used in the final debug iteration (record ID, input variables, scheduled path, etc.).
- `trace` (optional) — what was observed; used to suggest assertions.
- `flowVersionId` — pin the test to the version that produced the satisfactory run.
- `paused` — `true` when the debug run paused at a Wait element at any point (including runs that were later resumed). Defaults to `false`.

---

## Step 1 — Eligibility check (narrow)

Promotion eligibility is **narrower** than debug eligibility. Debug works for many flow shapes that cannot host a saved `FlowTest` record. Re-run the eligibility probe from `[[flow.recipes.testing.workflows.author-test]]` Phase 1:

- Confirm `processType` is `AutoLaunchedFlow`.
- Confirm `triggerType` is in `{RecordBeforeSave, RecordAfterSave, None}` (or absent for non-triggered).
- If not in the confirmed-supported set, call `dispatch_readonly(method: "GET", url: "/services/data/vXX.0/flowbuilder/schema/flow-capabilities", queryParams: { processType, triggerType })` (read `.flowFeatures`) and check for the literal `"FlowTesting"` capability.

If the flow is **not** save-eligible (e.g., screen flow, scheduled autolaunched), STOP. Surface to the user: "This flow can be debugged interactively but cannot be saved as a `FlowTest` in this org. The debug run scenario is not lost — you can re-iterate via debug, but there's no persistent test artifact available for `<processType>` × `<triggerType>` flows." Hand back to the testing router.

If the user is in silo mode (rare for promotion — most debug runs use real records), additionally probe `"FlowTestingWithDataSilo"`.

---

## Step 2 — Choose the build route

Two routes produce the same `FlowTest` record. Route choice affects how the payload is built, not what it contains.

**If `paused` is `true`, use Route A and skip the choice below.** The server's conversion (Route B) returns nothing for a paused interview and only ever builds a test with assertions, and assertions derived from a run that crossed a Wait aren't reliable. Build the payload with `assertions: []` and `testType: "WithoutAssertion"`. Set `doesTestWaitElement: true` so the saved test pauses at the Wait when replayed, as the debug run did. Then tell the user in one sentence: "This run paused at a Wait, so it can only be saved as a test without assertions." Do not offer to add assertions from the trace.

### Route A — Clean (default, recommended)

Re-state the inputs through the payload-builder — same construction as authoring from scratch, just seeded with debug inputs instead of user-stated intent.

Use Route A when:
- Debug inputs are simple (single record ID, a few scalar input variables, no scheduled path picks).
- The user wants to add or refine assertions beyond what the run produced.
- You want full control over `fullName`, `label`, and `doesCommitChanges`.

### Route B — Shortcut

`POST /services/data/vXX.0/flowbuilder/flow-test/actions/generate-from-debug-run` with the `serializedInterview` (the serialized debug-run interview). Continue only when the response has `isSuccess === true` and a string `flowTestJson`; parse that JSON-encoded string before reviewing or editing the generated definition.

Use Route B when:
- Debug inputs are **complex enough that retyping is error-prone** — large or relational `sobjectValue` payloads, multiple scheduled-path attempts, autolaunched flows with many input variables.
- You want the returned draft as a starting point; inspect the parsed payload and retain assertions only when they are actually present and match the user's intent.

Treat the shortcut's return as a draft, not a finished payload. Always pass it through Reviewer (Step 4) before save.

Ask the user once if route is ambiguous. Default to Route A when input complexity is low.

---

## Step 3 — Build the payload

Load `[[flow.recipes.testing.shared-stages.payload-builder]]`.

### Route A construction

Same as `[[flow.recipes.testing.workflows.author-test]]` Phase 3:

1. Top-level metadata. Pin a **real** record ID (not the throwaway `sobjectValue: "{}"` that interactive debug allows). For non-triggered flows, copy the input variables verbatim from the debug iteration.
2. `testPoints[]` with the Start element parameters mapped from debug inputs:

| Debug input | `testPoints[]` parameter |
|---|---|
| Trigger record's "before" snapshot | `{ leftValueReference: "$Record", type: "InputTriggeringRecordInitial", value: { sobjectValue: "<JSON>" } }` |
| Trigger record's "after" snapshot (update flows) | `{ leftValueReference: "$Record", type: "InputTriggeringRecordUpdated", value: { sobjectValue: "<JSON>" } }` |
| Scheduled path used | `{ leftValueReference: "ScheduledPathApiName", type: "ScheduledPath", value: { stringValue: "<path API name or ''>" } }` |
| Input variable used (non-triggered flows) | `{ leftValueReference: "<varName>", type: "InputVariable", value: { ... } }` |

3. Assertions — derive from observed trace if the user wants regression coverage. If the user only wants to lock in "this scenario passes", `assertions: []` is acceptable (`WithoutAssertion` semantics).

Lazy-load flowtest-element files as needed: `[[flow.recipes.testing.flowtest-elements.parameters]]`, `[[flow.recipes.testing.flowtest-elements.assertions]]`, `[[flow.recipes.testing.flowtest-elements.silo-config]]`.

### Route B construction

1. Call `dispatch(method: "POST", url: "/services/data/vXX.0/flowbuilder/flow-test/actions/generate-from-debug-run")` with `serializedInterview`.
2. Require `isSuccess === true` and a string `flowTestJson`, then parse it. If either field is missing/malformed or JSON parsing fails, surface the raw response and use Route A instead.
   Inspect its test points, parameters, and any pre-populated assertions.
3. Review any generated assertions against the user's requirements. Show the user the assertion list and ask which to keep.
4. Set `fullName`, `label`, `doesCommitChanges` (the shortcut may return defaults; override per naming conventions below).
5. Serialize the edited complete definition again: `flowTestJson = JSON.stringify(flowTest)`.

---

## Step 4 — Validate

Load `[[flow.recipes.testing.shared-stages.reviewer]]`.

Reviewer applies the same two jobs as in author-test Phase 4 — cheap local auto-fixes, and the intent check the server can't make. Two intent-class concerns are specific to promotion (both are cases where the payload would *save and resolve* but isn't the durable test the user meant — exactly what the server can't catch):

- **Throwaway record IDs.** If the debug run used `sobjectValue: "{}"` and the user didn't pin a real record in Step 3, `BLOCK` and ask for a real ID. A `{}` binding is a debug-only placeholder, not a persistent test scenario.
- **Silo `Id`s in the payload.** If silo mode and the debug run captured silo record `Id`s into `sobjectValue`, `BLOCK` — silo IDs resolve at save but aren't stable across silo rebuilds. Re-bind via the `jsonValue` envelope with the external-key fields per `[[flow.recipes.testing.flowtest-elements.silo-config]]`.

Anything structurally malformed in a Route B payload (bad `type` enums, stale references after a version change) is caught by the server on save — don't pre-check it here; the Step 5 save-and-react loop owns it.

---

## Step 5 — Save

`POST /services/data/vXX.0/flowbuilder/flow-test` with body `flowTestJson`, which must be the JSON-encoded
string produced after the final edits. Continue only when
`isSuccess === true` and `flowTestId` is a non-empty string; capture that
`320xxx` ID.

On `isSuccess === false`, surface each available error's `message` and
`statusCode`; target a field only if the message identifies one. If status
or a usable ID is missing, surface the raw response and stop because the
create outcome is unproven. A confirmed success means the payload resolved,
but the runtime probe in Step 6 is what proves the assertions hold.

---

## Step 6 — Verify (round-trip)

**Invariant — no broken test lingers in the org without the user's
say-so.** Same rule as author-test Phase 5: every terminal failure of
this step pauses for a user decision, and keeping a broken `320xxx`
is only acceptable when the user explicitly asks for it. Terminal
failure covers both **execution failed** (persistent missing/empty `results` or a server error after
retry — the promoted payload can't be made to run) and any returned
descriptor whose `testStatus` is missing or is not exactly `Pass`; both
route through the **Terminal
failure — user chooses cleanup** section at the end of this step.
Because promotion always starts with a `POST /services/data/vXX.0/flowbuilder/flow-test` (first-time save) and has no
prior passing state, the cleanup choice is **delete-or-keep** —
rollback doesn't apply here. The debug `interviewId` is preserved
either way for a follow-up promotion (usually Route A after a Route
B failure).

The single carve-out is when the user framed the failing scenario as
the artifact they want — a regression pin locking in a known fault,
not a bug in the promoted test. Confirm intent once before honoring
the carve-out ("you want to keep this failing promoted test as-is as
a regression pin, right?"); on confirmation, skip the cleanup prompt.

1. **Run immediately, then self-correct (cap at ONE silent retry).** `POST /services/data/vXX.0/flowbuilder/flow-test/actions/run` with `flowVersionId` (the pinned version — **required**), `testIds: ["320..."]`, and `showTrace: true`. Read per `[[flow.recipes.testing.run-results]]`. Same loop as author-test Phase 5:
   - Missing/empty `results` or a server error → surface the raw response. Round-trip via `dispatch_readonly(method: "GET", url: "/services/data/vXX.0/flowbuilder/flow-test/{id}")`, parse `flowTestJson`, and compare it with what was sent. Apply one fix only if the comparison proves a discrepancy, then call `dispatch(method: "PATCH", url: "/services/data/vXX.0/flowbuilder/flow-test/{id}")` with `{id, flowTestJson: JSON.stringify(completeDefinition)}`. Re-run only when the update returns `isSuccess === true`; otherwise surface its errors or raw response and hand off to terminal failure. **If the second run still fails**, hand off to the Terminal failure section below.
   - `testStatus: "Pass"` → success for the documented run-result contract.
   - Any descriptor whose `testStatus` is missing or is not exactly `Pass` → report `lastRunFailedAssertions`, `lastRunError`, and `interviewErrors` when present. Do not auto-retry; hand off to Terminal failure.
2. **Round-trip.** Call `dispatch_readonly(method: "GET", url: "/services/data/vXX.0/flowbuilder/flow-test/{id}")` and parse its `flowTestJson` string to see the server-canonical definition — important when Route B was used and you want to compare what the server stored with the shortcut output.
3. **Audit registration (best effort).** Scope `GET /services/data/vXX.0/flowbuilder/flow-test` with `flowVersionId`, an explicit `limit`, and `offset: 0`. Continue only when `flowTests` is an array. If the ID is absent and the page length equals `limit`, advance `offset` by the number of returned rows until the ID appears or a short/empty page ends the list. An absent or malformed `flowTests` makes the listing outcome unproven. Do not infer a per-test version field from the summary, and do not let a listing miss override a confirmed successful create.
4. **Coverage limitation.** No coverage operation is onboarded to MCP.
   Do not attempt a coverage call; state the limitation if the user asks.

### Terminal failure — user chooses cleanup

Reached from Step 1's failing branches once the one-shot self-correct
budget is exhausted (persistent missing/empty `results` or a server error — the test can't be made
to run), or immediately for any descriptor whose `testStatus` is missing
or is not exactly `Pass`. Skipped only after the user confirms the
fault-path carve-out from the top of this step.

1. **Surface the failure.** Report to the user:
   - (a) the verbatim run signal — `testStatus`, `lastRunFailedAssertions`,
     `lastRunError`, `interviewErrors`, the retrieved-vs-sent diff, or the
     raw absent/empty `results` response;
   - (b) the specific field(s) implicated only when the response identifies
     them;
   - (c) the current org state — the `320xxx` id.

2. **Ask the user how to handle the artifact:**

   > This promoted test is broken as saved. How do you want to handle it?
   > - **delete** — remove the `320xxx` from the org.
   > - **keep** — leave it in place for hand-editing; I'll report the
   >   `320xxx` and the failure trace.

   Silence is not consent — wait for a reply. For Route B failures,
   also mention that Route A (clean re-state from the same debug
   `interviewId`) is a robust redo path once cleanup is done — but do
   not conflate that recommendation with the delete/keep choice.

3. **Execute the choice:**
   - **delete** → `DELETE /services/data/vXX.0/flowbuilder/flow-test/{id}` with the CURRENT
     promotion's `320xxx` as the path `id` (single id per call —
     there is no bulk delete). Promotion is one-shot per `interviewId`
     (see Notes for callers), so there is never more than one id in
     scope here. Report deletion only when `isSuccess === true`. On
     `false`, surface `errorMessage` when present; when status is missing,
     report the delete outcome as unproven. The parent flow is untouched.
   - **keep** → leave the artifact in place; report the `320xxx`, the
     failure trace, and the pointer to `DELETE /services/data/vXX.0/flowbuilder/flow-test/{id}`
     for later cleanup if the user changes their mind.

4. **Offer a redesign.** After cleanup, ask whether to retry the
   promotion with adjusted inputs, switch build route (A ↔ B), or
   stop. Registration is skipped under the delete branch. Coverage
   retrieval is unavailable through MCP in every branch.

---

## Naming conventions for promoted tests

- **`fullName`.** Server-validated. Convention: `<FlowApiName>_<scenario_slug>`. For promoted runs, suffix with `_from_debug` or the date if the user wants provenance: `Update_Account_Name_To_BAC_TEMP_20260521_save_as_test_try1` — note the `_TEMP_` from the parent flow flows through automatically via `flowApiName`.
- **`label`.** Human-facing, shown in the Test runner UI. Short imperative phrases beat reused dev-name slugs. The debug iteration's intent is good source material — "Account name updates to BAC for active customers" beats "save as test try1".
- **`doesCommitChanges`.** Default `false` (rollback) on this endpoint. Promote inherits the debug session's DML mode preference: if the user iterated with rollback pinned explicitly (`enableRollbackMode:true` on the argument-driven endpoint, or `doesCommitChanges:false` on the payload-driven endpoint), the promoted test should also roll back. Only `true` when downstream effects can't be observed without persisted state — confirm explicitly with user.
- **`flowApiName`.** Inherited from the parent flow. The `_TEMP_<YYYYMMDD>` suffix flows through automatically; no manual handling needed.

---

## Error recovery

**Ineligible flow (debug works, save doesn't).** Surface in plain language. Do not call `POST /services/data/vXX.0/flowbuilder/flow-test` / `PATCH /services/data/vXX.0/flowbuilder/flow-test/{id}` — it will fail server-side with a `FlowTesting` capability error and consume Aura quota. Hand back to the testing router; user keeps the debug context but no test is produced.

**Shortcut returns malformed payload.** Generation or save can surface it through `isSuccess: false` and optional error messages. Target a field only when a returned message identifies one. Two options:
- Switch to Route A (clean re-state) using the same debug inputs — robust fallback.
- When the response identifies a field, hand-edit it and re-save; otherwise surface the raw response instead of guessing.

**Save succeeds, but the run has missing/empty `results` or a server error.** The OAS does not define the cause. Surface the raw response, round-trip via `GET /services/data/vXX.0/flowbuilder/flow-test/{id}`, parse `flowTestJson`, and compare it with what was sent. Re-save via `PATCH /services/data/vXX.0/flowbuilder/flow-test/{id}` only when that comparison proves a concrete fix. Exhausting the one-shot retry hands off to Step 6's **Terminal failure — user chooses cleanup** section; the user picks delete or keep, and the workflow waits for their answer.

**Save succeeds, run returns `testStatus: "Fail"` with populated `lastRunFailedAssertions`.** No auto-retry. Hand off immediately to Step 6's Terminal failure section: surface the returned summary, offer delete-or-keep, then act on the user's answer. When you present the choice, note that Route A is an available clean re-state path on the next attempt.

**`fullName` collision.** A test with this name already exists. Ask the user whether to:
- Update the existing test (`PATCH /services/data/vXX.0/flowbuilder/flow-test/{id}`) — destructive if the existing test was someone else's.
- Pick a different `fullName`.

**`flowVersionId` doesn't match the active version.** The flow was activated on a new version between debug and promote. Tests are version-pinned. Either save against the version the debug ran on (good for snapshotting historical behavior), or warn the user and re-run debug on the new active version (good for forward regression). Default: pin to the version the debug ran on, surface the version drift to the user.

**Aura session expired.** STOP, run `agentic-flow-poc-setup`. The debug `interviewId` may not be retrievable across the session boundary, which kills Route B. Route A still works because it only needs the inputs (which the caller passed in).

---

## Notes for callers

- Promotion is one-shot per call. If the user wants to promote multiple debug runs, call this workflow once per `interviewId`.
- `DELETE /services/data/vXX.0/flowbuilder/flow-test/{id}` removes a promoted test (pass the 320-prefixed id as the path `id` — one id per call), but it never removes the parent flow — that still requires Setup → Process Automation → Flows. Warn the user if the flow is throwaway (`_TEMP_<YYYYMMDD>` suffix) — the flow cleanup is manual.
- Route B (`POST /services/data/vXX.0/flowbuilder/flow-test/actions/generate-from-debug-run`) is **server-side conversion** and counts as one Aura call. Route A is zero MCP calls until Step 5 (save) — usually cheaper and easier to debug.
- Worked example with literal payloads (the `Update_Account_Name_To_BAC` case): see `examples/debugPromote.json` and notes referenced in `[[flow.recipes.testing]]`.
