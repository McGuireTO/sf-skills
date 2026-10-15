---
id: flow.recipes.testing.workflows.save-debug
description: "Boilerplate WithoutAssertion FlowTest — pin a scenario's inputs as a re-runnable smoke test with no expectations. The assertions-free subset of author-test; for promoting an interactive debug run instead, use promote."
---

<!-- Consumers: testing router (direct entry when user says "save a smoke test", "no assertions", "just lock in that this passes") -->

# Save a WithoutAssertion smoke test

Use when the user wants to persist a scenario's **inputs** as a
re-runnable test but has **no expectations to assert** — "just save that
this flow runs clean for this record", "lock in this input set", "a
smoke test, no assertions". The output is a `WithoutAssertion` FlowTest:
a Start binding, `assertions: []`, and nothing else.

This is the assertions-free subset of
[[flow.recipes.testing.workflows.author-test]]. It exists as its own
recipe because the boilerplate is small and the user should not be
walked through assertion-intent ceremony they explicitly don't want.

**Pick a different recipe when:**

- The inputs come from an **interactive debug run** the user just
  iterated → [[flow.recipes.testing.workflows.promote]] (its Route A
  with `assertions: []` is this same payload, seeded from debug context).
- The user **does** want to check an outcome → the full
  [[flow.recipes.testing.workflows.author-test]].

What "passes" means here: a `WithoutAssertion` test has no assertions to
fail, so a run succeeds iff the flow completes without a fault. The run
step still matters — it's what catches a binding that saved clean but
drives the flow into an error path.

---

## Phase 1 — Assess (shared stage)

Load [[flow.recipes.testing.shared-stages.intent-analyzer]].

It confirms the flow is **save-eligible** (`"FlowTesting"` in the
features list — narrower than debug eligibility), reads the flow shape,
and emits the assessment object the builder consumes. Silo mode is
auto-detected the same way as in author-test; if the user named an
`@testSetup` class, the silo gate (`"FlowTestingWithDataSilo"`) is
probed too.

If the flow is not save-eligible, STOP and route to
[[flow.recipes.testing.workflows.debug]] for ad-hoc validation — there
is no persistent artifact to produce. Do not call
`POST /services/data/vXX.0/flowbuilder/flow-test` / `PATCH /services/data/vXX.0/flowbuilder/flow-test/{id}` against an ineligible flow.

---

## Phase 2 — Build (shared stage, assertions skipped)

Load [[flow.recipes.testing.shared-stages.payload-builder]]. Run it
**without Step 4**:

- **Step 2** — top-level fields. `doesCommitChanges: false` unless the
  user explicitly asked for a committing test. If the Intent Analyzer's
  `flowShape.hasWaits` is `true`, also decide `doesTestWaitElement`:
  a `WithoutAssertion` test is a saved debug-run setup, and
  `doesTestWaitElement: true` makes it pause at Waits when replayed, as the
  debug run did. Propose `true` when the flow is an autolaunched flow with
  no trigger.
- **Step 3** — the Start `testPoint`, bound by trigger type per
  [[flow.recipes.testing.flowtest-elements.parameters]]. This is the
  whole payload's substance — pin the real inputs the scenario uses
  (a real record ID for record-triggered, one `InputVariable` per
  declared variable for non-triggered).
- **Skip Step 4 entirely.** No assertion `testPoint`. The single Start
  entry carries `assertions: []`.
- **Step 5** — `testType: "WithoutAssertion"`. (With no non-empty
  `assertions[]` anywhere, this is the only correct value; the reviewer
  auto-fix in Phase 3 confirms it.)
- **Step 6** — silo additions only if `siloMode: true`.

The result is a one-`testPoint` payload: `Start` bound, `assertions:
[]`, `testType: "WithoutAssertion"`.

---

## Phase 3 — Review (shared stage, auto-fixes only)

Load [[flow.recipes.testing.shared-stages.reviewer]], but only its
**job 1** applies here:

- **Apply the cheap local auto-fixes** — `testType` correctness,
  `flowVersionNumber` stringification, `sobjectValue` stringification,
  legacy `"Input"` → `"InputVariable"`. Report each as a one-line `WARN`.

The reviewer's **job 2 (assertion intent check) does not apply** — there
are no assertions to second-guess. The one intent concern that *does*
survive is the same as promotion's: a `WithoutAssertion` test built from
a throwaway `sobjectValue: "{}"` placeholder isn't a durable scenario.
If the Start binding is `"{}"` rather than a real record, `BLOCK` and ask
for a real record ID before saving.

---

## Phase 4 — Save & run

**Invariant — no broken test lingers in the org without the user's
say-so.** Same rule as author-test Phase 5: on terminal run failure,
pause and ask the user how to handle the artifact. `save-debug`
always starts with a `POST /services/data/vXX.0/flowbuilder/flow-test` (first-time save) and never has a prior passing
state to restore to, so the cleanup choice is **delete-or-keep** —
rollback doesn't apply here. The single carve-out is the fault-path
case at the end of this phase — a `WithoutAssertion` test that
consistently reaches a known fault is a valid regression scenario,
so the failure IS the intended artifact and the cleanup prompt is
skipped (confirm this intent with the user before treating the
failure as intended).

`POST /services/data/vXX.0/flowbuilder/flow-test` with body `flowTestJson`. Continue only when
`isSuccess === true` and `flowTestId` is a non-empty string; capture that
`320xxx` ID.

On `isSuccess: false`, surface each returned error's `message` and
`statusCode`; target a field only if the message identifies one, then
re-save (cap: one retry). The server's deep validator owns structural
correctness — don't pre-check against a memorized rule list. **No org
cleanup needed** on a failed `POST /services/data/vXX.0/flowbuilder/flow-test` — nothing was persisted.
If status or a usable ID is missing, surface the raw response and stop;
the create outcome is unproven, so do not run, update, or delete without a
confirmed ID.

Then **run it once** — `POST /services/data/vXX.0/flowbuilder/flow-test/actions/run` with the pinned `flowVersionId`
(**required**), the new `testIds`, and `showTrace: true`. Read per
[[flow.recipes.testing.run-results]]:

- `testStatus: "Pass"` → success for the documented run-result contract.
  Report the `320xxx` ID and the version it's pinned to, and surface any
  `interviewErrors` or `lastRunError` fields that are also present.
- Missing/empty `results` or a server error with no descriptor → no
  documented per-test descriptor is available. Surface the raw response without inferring a
  cause. Round-trip via `GET /services/data/vXX.0/flowbuilder/flow-test/{id}`, parse `flowTestJson`, and compare
  it with what was sent. Apply one fix only if that comparison proves a
  discrepancy, then call `dispatch(method: "PATCH", url: "/services/data/vXX.0/flowbuilder/flow-test/{id}")` with
  `{id, flowTestJson: JSON.stringify(completeDefinition)}`. Re-run only
  when the update returns `isSuccess === true`; otherwise surface its
  errors or raw response and hand off to terminal failure. If the second
  run still fails, hand off to the Terminal failure section below.
- Any returned descriptor whose `testStatus` is missing or is not exactly
  `Pass` → report `lastRunFailedAssertions`, `lastRunError`, and
  `interviewErrors` when present, then hand off to Terminal failure. Do not
  assume a runtime error means `results` is absent.
- A fault path the user actually wants to lock in → the fault-path
  carve-out applies. Confirm with the user; if confirmed, keep the
  test and skip the Terminal failure prompt.

### Terminal failure — user chooses cleanup

Reached when no descriptor reports exactly `testStatus: "Pass"` after the one-shot self-correct
and the fault-path carve-out does not apply.

1. **Surface the failure.** Report to the user:
   - (a) the verbatim run signal — `testStatus`, `lastRunFailedAssertions`,
     `lastRunError`, `interviewErrors`, the retrieved-vs-sent diff, or the
     raw absent/empty `results` response;
   - (b) the specific binding field(s) implicated only when the response
     identifies them;
   - (c) the current org state — the `320xxx` id.

2. **Ask the user how to handle the artifact:**

   > This smoke test is broken as saved. How do you want to handle it?
   > - **delete** — remove the `320xxx` from the org.
   > - **keep** — leave it in place for hand-editing; I'll report the
   >   `320xxx` and the failure trace.

   Silence is not consent — wait for a reply.

3. **Execute the choice:**
   - **delete** → `DELETE /services/data/vXX.0/flowbuilder/flow-test/{id}` with the CURRENT
     smoke test's `320xxx` as the path `id` (single id per call —
     there is no bulk delete). `save-debug` is one-shot per
     invocation, so there is never more than one id in scope here.
     Report deletion only when `isSuccess === true`. On `false`, surface
     `errorMessage` when present; when status is missing, report the delete
     outcome as unproven. The parent flow is untouched.
   - **keep** → leave the artifact in place; report the `320xxx`, the
     failure trace, and the pointer to `DELETE /services/data/vXX.0/flowbuilder/flow-test/{id}`
     for later cleanup if the user changes their mind.

4. **Offer a redesign.** After cleanup, ask whether to re-enter at
   Phase 1 (Assess) with a different binding, or stop.

---

## Editing an existing WithoutAssertion test

To change the pinned inputs, parse the current complete definition, make
the edits, and call `dispatch(method: "PATCH", url: "/services/data/vXX.0/flowbuilder/flow-test/{id}")` with
`{id, flowTestJson: JSON.stringify(completeDefinition)}`. Require
`isSuccess === true`; the wire shape has no partial patch. To **add**
assertions later (promote a smoke test to a real
assertion test), switch to
[[flow.recipes.testing.workflows.author-test]]'s build phase: add a
`Finish` `testPoint`, flip `testType` to `"WithAssertion"`, and re-save.

---

## Notes for callers

- This recipe is intentionally thin: it is author-test minus assertion
  authoring and minus the assertion-intent review. If a scenario grows an
  expectation, it graduates to author-test — don't bolt assertion logic
  onto this path.
- Tool budget: 2–4 calls in the happy path (1 retrieve for eligibility/
  shape via the analyzer, 1 store, 1 run, optionally 1 retrieve
  round-trip on failure).
