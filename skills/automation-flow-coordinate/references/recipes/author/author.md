---
name: flow-recipe-author
license: LICENSE.txt has complete terms
description: "Load when building a NEW Salesforce Flow from scratch OR editing/patching/extending/repairing an EXISTING one via the flow MCP. A Mode Detection gate (Phase 0) decides GENERATE vs EVOLVE from the user's intent and whether flow JSON was supplied by the client. Pipeline: Detect -> [Load, evolve only] -> Plan -> Save, with a hard approval gate before any save. TRIGGER when: user asks to create a flow, automate a process, build/generate flow metadata, OR update/add-to/change/extend/fix an existing flow, OR the client passed existing flow JSON for modification. DO NOT TRIGGER when running tests (use flow-recipe-testing), summarizing a flow (use flow-recipe-summarize), or building an Orchestrator / ApprovalWorkflow flow (Phase 2 hands those to flow-recipe-orchestrate)."
metadata:
  version: "3.2"
  related-skills: flow-type-resolver, flow-anti-patterns, flow-element-start, flow-flow-properties, flow-metadata-schema, flow-value-rules, flow-formula-expression, flow-preview-renderer, flow-recipe-orchestrate
---

# Flow Author — Create or Evolve

Builds a complete, deployable Salesforce Flow, whether it is **net-new** or an
**edit to an existing flow**. One pipeline, two modes, selected by a Mode
Detection gate up front:

- **GENERATE** — net-new build from the user's request. Skips the Load phase.
- **EVOLVE** — edits an existing flow supplied as JSON by the client. Runs the
  Load phase first, edits **surgically**, and never skips the approval gate.

Output format is **JSON** (Tooling API wire format) for
`POST /services/data/vXX.0/flowbuilder/flow/actions/save`. Not XML. (If a client persists the flow by
writing a `.flow-meta.xml` and deploying it as metadata instead of calling the
save endpoint, the same topology rules still apply — a metadata deploy stores the
flow verbatim, so every `AUTO_LAYOUT_CANVAS` v68 terminating branch must still
carry an explicit `ends[]` End. See `../../shared/end/end.md`. In the XML, write
each element and field under the name the JSON uses: one repeated element per
array entry (`<ends>`, `<waitEvents>`, `<actionCalls>`), and nothing the JSON
shape doesn't have on that element. An unknown or misplaced element fails the
deploy with `Error parsing file: Element … invalid at this location`.)

Phase 2 asks targeted clarifying questions inline when the request is
materially ambiguous (see Plan step 1) before moving into design.

---

## Phase 0 — Mode Detection (read this first)

Decide the mode before doing anything else. This is the intent guardrail that
keeps a net-new build from mutating a live flow, and an edit from silently
becoming a brand-new flow.

```text
Mode = EVOLVE if ANY of:
  - the client supplied existing flow JSON (input payload, prior save response,
    a local file, or a Flow Builder source export), OR
  - the user named an existing flow to change ("update Lead_Routing",
    "add a step to my onboarding flow"), OR
  - the request references an existing element, version, or a save-time
    validation error to repair.
Mode = GENERATE otherwise (the request describes a new flow and no existing
       flow is in play).
```

**JSON availability is the deciding signal.** Non-empty flow JSON means an
existing flow is in play → **EVOLVE**, even when the wording says
"create"/"build"/"make" (a single request has no second flow to create). Intent
only breaks the tie when **no** or **empty** JSON is supplied:

| User intent | Flow JSON supplied? | Resolution |
|---|---|---|
| New flow | none | **GENERATE** |
| New flow wording | present (non-empty) | **EVOLVE** — non-empty JSON is an existing flow in play; "create" wording does not spawn a second flow. |
| Edit existing | present (non-empty) | **EVOLVE** |
| Edit existing | **empty or missing** | **EVOLVE intent stands — do NOT downgrade to GENERATE.** The flow body is a required input the client must provide. Ask for the current flow JSON and stop; do not fabricate a net-new flow to "fill the gap". |

**Re-detect every turn — a "yes" follow-up does not flip the mode.** Mode is decided on the flow JSON attached to the **current** request, on every turn. While the client keeps attaching a non-empty flow JSON, every turn stays **EVOLVE** — including an affirmative follow-up ("yes", "create it", "go ahead", "yes create a flow") that lands after you declined a process-type change. That reply is the same blocked request reworded, not a new GENERATE: the attached flow has not changed, so its `processType` still cannot change — decline again and stop. GENERATE begins **only** when the client stops attaching an existing flow (the user opens a new or blank flow, so no non-empty JSON arrives). You cannot spawn a net-new flow while one is attached, no matter how many "yes"es precede it.

**One edit session = one flow. No "separate new flow" escape.** In EVOLVE the
supplied JSON is the single flow this control point saves back to — there is no
second slot. If the request describes something the loaded flow cannot become
without a different `processType` than the loaded flow's — in either direction, for
**any** flow type — that is a **process-type change → decline with a reason** per the
change-type table in Phase 2. (Fixed-platform incompatibility only: the element or
behavior cannot exist under the loaded flow's `processType`. Not the org-availability
(`.elements`) or FLS gate, which keep their build-without / halt branch at Phase 2 §
Probe schema.)
Do **not** offer a new / separate flow, offer to design / build / "help with" one,
ask whether to proceed ("would you like me to…?"), or propose any other workaround.
Decline and **stop** — state once that they can make a new flow themselves, then end
the turn. A net-new save on this control point overwrites the flow in context. "The
loaded flow isn't what the user asked for" is **never** a license to switch to
GENERATE or create a second flow — it is the decline trigger. Any affirmative
follow-up ("yes", "create it", "go ahead", "yes create a flow") is that same blocked
request reworded, not permission to build; while the flow JSON is still attached it
stays EVOLVE and is declined again (see "Re-detect every turn" above).

**Ambiguous intent?** Ask exactly one question and stop until answered:

> "Are you starting a new flow, or editing one that already exists?"

Hard rules that follow from the mode:

- Enter **Phase 1 (Load) only in EVOLVE**. Never run it in GENERATE.
- The override phrase (`"skip the"` / `"don't ask"`) may skip the Plan-phase
  intent capture **only in GENERATE**. In EVOLVE the gate is never skipped —
  every save touches a flow that may already be active or referenced by other
  automation.

### EVOLVE hard limitations (surface these before starting an edit)

1. **The editable flow body is a client-supplied input.**
   `GET /services/data/vXX.0/flowbuilder/flow/{id}` can return the raw graph for read-only
   summarization, and `GET /services/data/vXX.0/flowbuilder/flow/{id}/validation-results` can return the graph with
   validation results. EVOLVE still requires the exact client-supplied working
   body (from Flow Builder, Vibes, or an agentic orchestrator managing its own
   copy — Claude Code, Cursor, Copilot, etc.) rather than silently replacing it
   with an org read. If it is absent, request it; editing "by description
   alone" without the user's source is lossy — tell the user this upfront.
2. **No flow deletion.** Use Setup → Process Automation → Flows to delete.
   Throwaway flows should be suffixed `_TEMP_<YYYYMMDD>`.

### EVOLVE surgical / minimal-surface rule (applies to the whole EVOLVE path)

**Touch only what the requested change requires.** The edit modifies the target
element(s) and the connectors that must be rewired to keep the graph valid —
and nothing else.

- Everything else in the client-supplied JSON is preserved **byte-for-byte**:
  unrelated elements, element ordering, resources, `locationX`/`locationY`,
  existing `processMetadataValues`, labels, and descriptions.
- No opportunistic "improvements", reformatting, renaming, or re-topology of
  untouched parts. If the user did not ask for it, do not change it.
- Advisory Auditor/security findings on **untouched** elements are reported to
  the user, never auto-fixed inside an evolve. Surface, do not silently repair.

**Bounded exception — server read-back forms that cannot be saved verbatim.**
A retrieve hands back some fields in a *read-back* shape the server itself
rejects on save — specifically, the times `schedule.startTime` /
`schedule.endTime` / `resumeTime` as `{ "timeInMillis": N }` objects and the
dates `schedule.startDate` / `schedule.endDate` / `resumeDate` as epoch-millis
integers, instead of the wire-string form `POST /services/data/vXX.0/flowbuilder/flow/actions/save`
requires. These
fields are normalized to their wire-string form on **every** element that
carries them, touched or not — this is a mechanical serialization fix, not a
design change. It is exempt from byte-for-byte preservation and **overrides**
the "report-don't-fix untouched elements" rule above for these fields
specifically: the agent repairs them, it does not just report them. See
`../../shared/anti-patterns.md` item 39 for the full field list and conversions.

Rationale: unbounded edits compound flow complexity across sessions and are not
deterministic across LLM runs. Surgical edits keep evolve reviewable and
reproducible.

---

## Approval gate

One hard gate separates Plan and Save:

**End of Phase 2 (Plan):** the agent presents the plan summary and asks
"Approve this plan?" The user MUST explicitly accept (e.g., "yes", "looks
good", "approved", "ship it") before Phase 3 (Save) begins. Skipping the gate
is a contract violation.

**The plan gate is NEVER skipped.** Even on full autopilot, the user sees and
approves the plan summary before any save call. In EVOLVE this is
absolute — every save touches an existing flow that may be active or referenced
by other automation.

**Silence is NOT acceptance.** If the user replies with a refinement, a
question, or anything that isn't an unambiguous accept, treat it as "still
refining" and re-present the plan summary with the refinement applied.

**Override phrases (GENERATE only).** If a GENERATE request begins with
`"skip the"` or `"don't ask"` (e.g., "don't ask, just build it"), the agent
infers the design silently and presents the plan with minimal back-and-forth —
but the Phase 2 plan gate still stands. The user always approves the
plan summary before any save. This override has no effect in EVOLVE.

---

## Phase 1 — Load  (EVOLVE ONLY — skipped entirely in GENERATE)

Establish the baseline before touching anything.

1. **Ingest the client-supplied flow JSON.** The current flow body is provided
   by the client as input (see EVOLVE hard limitation 1). If it has not been
   provided, ask for it and stop — do not reconstruct it from the org and do
   not fall back to a net-new build.
2. **Call `dispatch_readonly(method: "GET", url: "/services/data/vXX.0/flowbuilder/flow/<definition ID>/versions")`** to confirm the
   target version number and active/draft status. (Volatile — always re-fetch,
   never reuse from history.)
3. **Call `dispatch_readonly(method: "GET", url: "/services/data/vXX.0/flowbuilder/flow/<id>/validation-results")`** for the version-level
   metadata (label, processType, apiVersion, runInMode). Do not reuse a cached
   call — this is Tier 4.
4. Parse the supplied JSON and build an **internal element index**:
   name → type → connectors. This is the working graph for the session.
5. **Note pre-existing `processMetadataValues`** (especially `BuilderType` and
   `CanvasMode`). In EVOLVE these are preserved **verbatim** — never inject,
   overwrite, or flip a canvas mode the source didn't ask for (silently
   re-laying-out an existing flow can corrupt it). See `../../shared/anti-patterns.md`
   item 37.

---

## Phase 2 — Plan  (shared by both modes)

Translate the request into a concrete flow design (GENERATE) or apply the
requested change to the working graph (EVOLVE), run audits, and present the
plan summary for approval. This is internal work that produces **one
user-visible artifact**: the plan summary.

### Plan steps (do all in order, no tool calls visible to the user except as needed for schema)

1. **Clarify underspecified business intent, if needed.** Check whether the
   request gives enough business detail to design confidently: the
   trigger/starting condition, the core action(s), any branching or decision
   logic, and the expected outcome. If a material gap exists (e.g., the
   request implies branching but names no conditions, the outcome is
   ambiguous, or a consequential edge case is unaddressed), ask the user 1-2
   targeted questions in plain business language before drafting. Do not ask
   about objects, fields, trigger types, or other implementation details —
   those are resolved by schema probing in step 4. Skip this step entirely if
   the request is already unambiguous; this is a gap check, not a mandatory
   Q&A round. *(Override phrase: if the request began with `"skip the"` /
   `"don't ask"`, infer reasonable defaults instead of asking — GENERATE only,
   per the Approval gate override.)*
   **One exception on trigger types:** if the flow-type resolver in step 2
   returns `mustAsk: true` (for example a "CRM Triggered Flow" request that
   does not say "marketing"), ask its `decidingClarification` in plain words
   before drafting, and build the type the user picks. Don't choose for them.
   With the override phrase, use the resolver's leaning `tuple` and say in one
   line which type you built.
2. **Pick `processType` and `triggerType`.** **Load and apply the flow-type-resolver
   reference (`../../shared/flow-type-resolver/flow-type-resolver.md`)** to map the
   request's characteristics and described trigger ("when an order is placed", "on a
   button click", etc.) to the correct tuple. It is the single source of flow-type
   classification — do **not** re-derive the tuple inline from this recipe or any other
   reference file.
   - **[Orchestration hand-off — run it the moment the resolver returns a tuple.]**
     If the resolved `processType` is `Orchestrator` or `ApprovalWorkflow`, stop
     this recipe and hand control, with the resolution, to
     `../orchestrate/orchestrate.md`. It owns the shape gate, the per-stage loop,
     and the per-stage saves. Do not plan stages here. Step flows and evaluation
     flows that the orchestration co-generates come back here as ordinary
     GENERATE requests. (EVOLVE of a loaded orchestration hands off the same
     way, after the processType lock below.)
   - **Build the Start for the resolved tuple (GENERATE).** For a new flow, write the resolved `triggerType`
     into `start.triggerType` (omit it for `None`), and read that trigger type's section of
     `../../elements/start/start.md` before writing the Start. A Start without the
     resolved `triggerType` makes a different flow type. For example, an
     `AutoLaunchedFlow` with no `start.triggerType` is a plain autolaunched flow, not
     an On-Demand Flow: for `OnDemandNoTrigger`, follow § On-Demand
     (`start.triggerType` `OnDemandNoTrigger` and a top-level `dataSpace`). In EVOLVE,
     keep the loaded `start.triggerType` unless the user asks to change the trigger.

   Call
   `dispatch_readonly(method: "GET", url: "/services/data/vXX.0/flowbuilder/schema/flow-capabilities", queryParams: { processType, triggerType })` **once** and read both
   `.elements` and `.flowFeatures` from that single cached result — confirm
   every element type the design will use is available in this org and any
   opt-in features are gated.
   - **[EVOLVE — processType lock; mechanical, run it the moment the resolver returns a tuple.]** The resolver is prompt-only and never saw the loaded flow, so this compare is **yours, not the resolver's**: take the resolver's resolved `processType` and compare it against the **loaded flow's `processType`** (the `metadata.processType` of the client-supplied JSON, captured in Phase 1). **If resolved `processType` ≠ loaded `processType` → STOP:** it is a process-type change. Decline per the change-type table below and do **not** emit the tuple, draft, save, or offer a new / separate flow — a later "yes, make it separate" is the same blocked request reworded (see Phase 0). This holds for **any** flow type, in either direction; a confident, high-confidence resolver result does not override it. A differing `triggerType` *within the same* `processType` is a legal edit — reuse the loaded `processType` and re-read flow-capabilities when the trigger changes or when adding net-new nodes. This lock is the `processType` compare only; the org-availability (`.elements`) and FLS gates keep their own build-without / halt branch at § Probe schema.
   - **"Supported in metadata" ≠ "authorable in the canvas."** Emit only
     palette-authorable entries (those carrying a `configComponent`); never emit
     a bare entry with `"isElementSubtype": false`, `"attributes": null`, and no
     `configComponent`. See `../../shared/anti-patterns.md` item 29 (the base `Wait`
     is the known trap — use a Wait subtype; `../../elements/wait/wait.md`).
3. **Pick API version.** Call `dispatch_readonly(method: "GET", url: "/services/data/vXX.0/flowbuilder/flow/version-info")` with optional
   `builderType` only; the tool does not accept `processType`. Select the entry
   in `processTypes[]` whose `processType` equals the chosen flow process type,
   and set `apiVersion = max(apiVersionsList)` (the latest supported version,
   currently 68) unless the user explicitly specified a different version. Do
   NOT use `defaultApiVersion` — that is the server's fallback for flows that
   omit `apiVersion` entirely; it resolves to an obsolete version (49) and
   disables recent features (Data Space v65+, scheduled-flow `maxBatchSize`
   v63+, and others). *(EVOLVE: preserve the existing flow's `apiVersion`
   unless the user asked to change it.)*
   **The resolved version is fixed by `GET /services/data/vXX.0/flowbuilder/flow/version-info` — never lower it, and
   never assert a version cap, to work around a save error.** A save failure such
   as `<EndName> not found` is a referential-integrity bug (a connector targets an
   End with no matching `ends[]` entry — see `../../shared/anti-patterns.md`
   item 14), **not** a signal that the org lacks v68 or that ends are unsupported.
   Diagnose the actual error and fix it (add the missing `ends[]` entry); do NOT
   downgrade `apiVersion`, drop `ends[]`, or claim the flow must open in Free-Form.
   Whether ends are storable is decided **only** by the verified
   `max(apiVersionsList)` above, never inferred from a save error.
4. **Probe schema.** For every object the design references, call
   `dispatch_readonly(method: "GET", url: "/services/data/vXX.0/flowbuilder/platform/entity/<Object>/fields")`. For every action call, call
   `dispatch_readonly(method: "GET", url: "/services/data/vXX.0/flowbuilder/action/invocable-action-details", queryParams: { actionType, actionName })`. For
   every Screen LWC, call `dispatch_readonly(method: "GET", url: "/services/data/vXX.0/flowbuilder/screen-component")` +
   `GET /services/data/vXX.0/flowbuilder/screen-component/{apiName}`. **Cache aggressively** — never
   re-call a tool with the same args if the result is already in conversation
   history (Tier 1-3).
   
   **`GET /services/data/vXX.0/flowbuilder/platform/entity/{apiName}/fields` is authoritative and FLS-filtered.** The response
   is the complete field inventory the skill may reference for that sObject —
   fields not in the response are inaccessible, and MUST NOT appear in any
   metadata the skill emits, even well-known standard fields (`DoNotCall`,
   `HasOptedOutOfFax`, `HasOptedOutOfEmail`, etc.). If the user's requested
   behavior names a field not in the response, or uses a business term
   (for example "engaged" or "high-value") that no returned field clearly
   matches, do NOT proceed to Phase 3.
   Instead, stop here and present the two branch options to the user:

   - *Build without the field* — describe what is (and isn't) possible with
     the accessible fields, and ask the user to confirm the reduced scope.
     List substitutes closest real data first. Check related objects, data
     graph DMOs, and records the flow already reads (for example a related
     Contact and its Account). Put any test-looking field last and label it,
     even when you only name it as an example.
   - *Halt* — instruct the user to have their Salesforce admin grant FLS on
     the field, or re-authenticate the MCP session as a user with access.

   Wait for the user's decision before moving on. See
   `../../shared/anti-patterns.md` item 40.

   **Send to Journey probe sequence.** When the design contains
   `sendToJourney`, load `../../elements/action-call/send-to-journey.md` and the
   Start guide its trigger table names (for a Segment flow,
   `../../elements/start/segment-triggered.md` plus its shared contract in
   `../../elements/start/audience-common.md`). Complete both before drafting
   the action. Stop for trigger variants outside the documented MVP without
   describing those variants as unsupported by the platform.

   **Marketing message probe sequence.** When the design sends a marketing
   email, SMS or RCS message (`sendEmailMessage`, `sendSmsMessage`,
   `sendRcsMessage`), read that action's section of
   `../../elements/action-call/action-call.md` (Send Email Message, Send SMS
   Message or Send RCS Message) and its § `contentId` Rule before drafting the
   action, not only the top of the file. They turn the content, sender and
   subscription the user names into the values the action binds: `contentId` is
   the `contentFqn` from `GET /services/data/vXX.0/flowbuilder/messaging/content-fqn`, never a
   `ManagedContent` or `EmailContent` Id, and a subscription's `id` and
   `channelTypeId` are bound together.
5. **Draft the element list, connector topology, and resource list.** Decompose
   the request into logical units of business work, then map each unit to one or
   more concrete FDL elements. Load per-element skills from the registry below
   as each element type is named. If any element or resource uses a **formula
   expression** (a Formula resource, or a condition/filter in Formula mode),
   read `../../shared/formula-expression.md` first — it carries the operator,
   function-availability, picklist (`ISPICKVAL`), and type-coercion rules that
   apply to every formula.

   **[EVOLVE addendum] Identify the change type and apply it surgically to the
   working graph.** Per the minimal-surface rule, touch only the affected nodes
   and connectors.

   | Change type | Description | Key risk |
   |---|---|---|
   | **Add element** | Insert a new node into the graph | Connector wiring — must update upstream element's `connector` to point to the new node, and new node's `connector` to point to the former target |
   | **Remove element** | Delete a node | Dangling connectors — upstream elements still reference the removed node |
   | **Modify element** | Change config on an existing node | Schema re-resolution — re-probe `dispatch_readonly(method: "GET", url: "/services/data/vXX.0/flowbuilder/platform/entity/{apiName}/fields")` or `dispatch_readonly(method: "GET", url: "/services/data/vXX.0/flowbuilder/action/invocable-action-details")` if the object/action changes |
   | **Add path** | New Decision outcome or scheduled path | `defaultConnector` must still exist; audit all outcomes |
   | **Fix validation error** | Repair a save-time rejection | Map error to anti-pattern, apply targeted fix, do not over-correct |
   | **Rename flow** | Change label or API name | `fullName` change requires `saveType: "saveAsNewDefinition"` — confirm with user |
   | **Change process type** | Switch `processType` on an existing flow (e.g. Screen Flow ↔ record/schedule/autolaunched) | **Not supported — decline with a reason.** Tell the user changing the process type of an existing flow isn't supported. Do **not** offer to create a new flow, or any other workaround — decline and stop; this is one edit session on one control point, so a net-new build would save over the flow in context. Do not name any skill, router, mode, or internal reason. |
   | **Change trigger type** | Switch `triggerType` within the same `processType` | **Load and apply the flow-type-resolver reference (`../../shared/flow-type-resolver/flow-type-resolver.md`)** to re-pick the tuple (do not classify inline); re-read flow-capabilities; many element types may become unsupported |

   **[EVOLVE] Graph mutation semantics:**

   Adding an element between two existing nodes:
   ```text
   Before: A --connector--> B
   After:  A --connector--> NEW --connector--> B
   ```
   - Build the new element JSON using the appropriate element skill from the registry.
   - Set `NEW.connector.targetReference = B.name`.
   - Set `A.connector.targetReference = NEW.name`.
   - Add `NEW` to the appropriate element-type array.

   Removing an element:
   ```text
   Before: A --connector--> REMOVE --connector--> B
   After:  A --connector--> B
   ```
   - Find every connector in the flow that references `REMOVE.name`
     (`connector`, `faultConnector`, `defaultConnector`, `nextValueConnector`,
     `noMoreValuesConnector`).
   - Re-point each to `REMOVE`'s outgoing connector target (`B.name`).
   - Remove `REMOVE` from its element-type array.

   Adding a terminating branch or fault path (auto-layout sources):
   - When the retrieved source has explicit End element(s) — Flow-Builder- and
     MES-generated flows do — preserve the source's `ends[]`. Give each NEW
     terminating branch an explicit End: either converge it on an existing End
     (a shared End is valid) or add its own dedicated End. Both are valid
     Flow-Builder-native auto-layout shapes.
   - Route new faults to a dedicated error handler (`Log_Error` or a
     persisted/notified Assignment handler; one shared handler across faults is
     fine — item 32) that reaches its own End — a fault pointed directly at an
     End (or left empty) is silently dropped on reload (the error path vanishes),
     so a handler keeps it. This is an observability preference, not a round-trip
     requirement.
   - In a marketing flow, add a fault path only when the user asks for error
     handling; see `../../shared/fault-paths/fault-paths.md` § Marketing Flows —
     Fault Paths Only When Asked.
   - See `../../shared/anti-patterns.md` item 38 and the `../../shared/connector/connector.md`
     § Terminal Elements EVOLVE worked example.

   Fixing a validation error:
   - Quote the verbatim `errors[]` or `warnings[]` entry.
   - Map to the matching anti-pattern in `../../shared/anti-patterns.md`.
   - Apply the targeted fix described there.
   - Do not change any other elements — surgical fixes only.

   **`targetReference` must always be a dev-name, never a GUID.** See
   `../../shared/anti-patterns.md` item 14.

   **[EVOLVE] Re-probe schema only when the change targets a NEW schema-bound
   resource:**

   | Change | Re-probe needed |
   |---|---|
   | Object field changed on a record element | `dispatch_readonly(method: "GET", url: "/services/data/vXX.0/flowbuilder/platform/entity/<NewObject>/fields")` |
   | Action changed on an action element | `dispatch_readonly(method: "GET", url: "/services/data/vXX.0/flowbuilder/action/invocable-action-details", queryParams: { actionType: <type>, actionName: <new name> })` |
   | Subflow target changed | `GET /services/data/vXX.0/flowbuilder/flow/subflows` |
   | Screen LWC component changed | `dispatch_readonly(method: "GET", url: "/services/data/vXX.0/flowbuilder/screen-component/<qualifiedApiName>", queryParams: { processType })` (qualified name, e.g. `flowruntime:datatable` — re-`GET /services/data/vXX.0/flowbuilder/screen-component` if only the informal name is known) |
   | Trigger type changed | `dispatch_readonly(method: "GET", url: "/services/data/vXX.0/flowbuilder/schema/flow-capabilities", queryParams: { processType, triggerType })` once (read both `.elements` and `.flowFeatures` from the one result) |

   Do NOT re-probe if only the value/assignment on an already-resolved field
   changes — the schema hasn't changed, so reuse from conversation history.

6. **Run Auditor checks** before presenting the plan summary:
   - CRUD inside a loop? See `../../shared/anti-patterns.md` item 1.
   - Missing `faultConnector` on fault-capable elements (`actionCalls`, `apexPluginCalls`, `recordLookups`, `recordCreates`, `recordUpdates`, `recordDeletes`, `waits`)? See `../../shared/anti-patterns.md` item 2. Apply each action-specific persisted shape before this generic check. **Skip this check in a marketing flow** (its `start.triggerType` is on the list in `../../shared/fault-paths/fault-paths.md` § Marketing Flows — Fault Paths Only When Asked) unless the user asked for error handling: there, no fault paths is the correct default, so do not flag, add, or recommend them.
   - Any non-empty `customErrors[]` (reached via `faultConnector`, a regular `connector`, or left unconnected) when `triggerType` is absent or not `RecordBeforeSave`/`RecordAfterSave`? Invalid — save fails with `TRIGGER_TYPE_ELEMENT_NOT_SUPPORTED` regardless of how the element is reached. Retarget fault paths to a `Log_Error` actionCall or a `$Flow.FaultMessage` Assignment. See `../../shared/anti-patterns.md` item 2. *(For observability, prefer a persisted/notified handler — see the advisory check below.)*
   - **[Observability — advisory; headless flows]** In a headless flow (any flow with no screen-rendering capability — Autolaunched, Scheduled, PlatformEvent, Segment, and other event-triggered types; screen-bearing types like Screen Flow, `UnifiedSchedulingFlow`, and `AgxScreenFlow` are **not** headless — route their faults to an error Screen instead), does any `faultConnector` terminate at an Assignment whose `assignmentItems` write `$Flow.FaultMessage` **only to a non-output flow variable** — not to an `isOutput` variable a caller consumes — with **no** downstream element that persists or notifies (a `recordCreate` to a log object, an admin email/notification, or a platform event)? If so, the error is captured in memory only and vanishes when the interview ends — flag it as a silent-failure risk in the plan summary and recommend adding a persistence/notification step (if the element is inside a Loop, accumulate and log once after the loop — item 1). Do **not** block the save (it is valid metadata), and on EVOLVE do not auto-fix untouched elements. Screen flows are exempt (the error Screen surfaces it), as is an Assignment to an `isOutput` variable a parent/Apex caller handles. See `../../shared/anti-patterns.md` item 2 (Observability note) and `../../shared/fault-paths/fault-paths.md` § Observable vs. In-Memory-Only Fault Handling.
   - Missing `defaultConnector` on any Decision? See `../../shared/anti-patterns.md` item 7.
   - Redundant Get Records + filter-based Update Records re-applying the same filter? See `../../shared/anti-patterns.md` item 30 — reuse the fetched collection (Mode 2 update) instead of re-filtering.
   - Any `screens[]` element with both `allowBack: false` and `allowFinish: false`? See `../../shared/anti-patterns.md` item 31.
   - Any non-fault connector targeting a terminal, error-message-only screen that's reached via a `faultConnector` (e.g. a success screen falling through into it)? See `../../shared/anti-patterns.md` item 36.
   - **[GENERATE; `AUTO_LAYOUT_CANVAS`; resolved `apiVersion` ≥ 68.0] Explicit ends stored:** every terminating branch reaches an explicit `ends[]` entry (`END_ELEMENT_n`) — its connector and the entry co-emitted — including the easy-to-miss loop `noMoreValues`/`nextValue` and decision `default`/outcome termini. Branches may each get their own End or converge on a shared End; both valid. v68.0 made End nodes storable metadata, so a net-new auto-layout flow stores them rather than relying on the implicit omit-the-connector form. Below 68.0, and on any Free-Form flow, emit **no** `ends[]` (omit the connector) — **never emit `ends[]` on a Free-Form flow**. See `../../shared/end/end.md`. *(EVOLVE: preserve the source's `ends[]`; add an explicit End for each NEW terminating branch on an auto-layout source — its own or a shared one.)*
   - **[`AUTO_LAYOUT_CANVAS`; applies to GENERATE and EVOLVE] Every terminating branch reaches an explicit End?** Confirm no v68 terminating branch (loop exit, loop body, decision default/outcome, plain element) is left without an `ends[]` target. A shared End (2+ non-fault connectors into one entry) is **valid** — do NOT flag or split it. A `faultConnector` pointed directly at an End is **not** a defect either — it is silently dropped on reload; only advise routing faults to a handler so the error path is not lost silently. See `../../shared/anti-patterns.md` item 38. *(Mid-graph convergence on a continuing element or a shared error screen is also fine; Free-Form sources are exempt.)*
   - **[GENERATE] Canvas mode:** a net-new flow must carry the `CanvasMode` PMV — absence is not neutral; the flow silently opens in Free-Form (non-canvas process types like `CustomerLifecycle` are excepted — they take no `CanvasMode`). See `../../shared/anti-patterns.md` item 37. *(EVOLVE: never inject or flip — preserve the source's `processMetadataValues` verbatim.)*
   - Every field name in `decisions[].rules[].conditions[].leftValueReference`, `recordLookups[].filters[].field`, `recordLookups[].queriedFields[]`, `recordCreates`/`recordUpdates`/`recordDeletes` filter/input fields, `assignments[].assignmentItems[].assignToReference`, and any `$Record.<Field>` or `<sObjectVar>.<Field>` in a `formulas[]` expression or `filterFormula` — is each one present in the most recent `GET /services/data/vXX.0/flowbuilder/platform/entity/{apiName}/fields` result for its sObject? If not, do NOT save; branch to *build without the field* or *halt and refer to the admin* per Phase 2 § Probe schema. See `../../shared/anti-patterns.md` item 40.
   - Hard-coded IDs? See `../../shared/anti-patterns.md` item 3.
   - Element names unique and ≤ 80 chars? See `../../shared/anti-patterns.md` items 16, 17.
   - Value field consistency: every value key paired with its `*DataType`, no two value keys, no GUIDs in `elementReference`. See `../../shared/value-rules.md`.
   - **Security posture** (advisory): run the checks in `../../shared/security/security.md`. See `../../shared/anti-patterns.md` item 28. *(EVOLVE: pay attention to changes that newly introduce a risk — switching to system mode, adding a whole-record write, adding a guest-facing screen input.)*

   Fix all failures **introduced by this build/change** before presenting the
   plan summary. Security and headless-flow observability findings are **advisory** — do not fix silently or block;
   carry them into the plan summary (Security note / a silent-failure-risk note). *(EVOLVE:
   findings on untouched elements are reported, never auto-fixed — see the
   surgical rule.)*

### Plan summary artifact

The plan summary is the deliverable of the Plan phase: a concise
**business-language description** of what the flow will do — a short
ordered list of steps in plain English, no diagram. It is an approval aid, not a
faithful reconstruction of the flow: the exact element graph lives in the FDL
itself (and, after save, in the real flow via the "Open in Salesforce" link).

Build the summary from these step types:

| Step type | Description |
|---|---|
| Start condition | What triggers the flow |
| Process | A unit of business work + its expected result |
| Decision branch | A conditional fork based on business logic |
| Loop | A repeating process over a set of items |
| End state | Final outcome or termination point |

Keep each step to one line of plain business meaning, and **describe branches and
loops narratively** in that line rather than drawing them out as a nested tree or
labeling every arm:
- Decision: "routes high-value cases to a specialist, everything else to the standard queue."
- Loop: "for each overdue invoice, sends a reminder."

**Decisions only branch — they never retrieve.** If a decision needs
information, there is a Process step before it ("find the account" → "if active,
do X"). Decisions are not limited to yes/no — they can fan out to several labeled
outcomes.

**No redundant steps.** If one step logically implies another, collapse them.
"Ask user for input" already means "capture input" — don't add a separate step.
This applies below the step level too: a Process step that Get-Records-then-
filters, followed by a Decision that only guards "did we find anything," followed
by another Process step whose Update Records re-applies that same filter, is one
unit of work, not three — the fetched collection already implies the update
target. See `../../shared/anti-patterns.md` item 30.

Each step maps to the concrete FDL elements that implement it.

**Marketing flows: leave error handling out of the plan.** In a marketing flow
(its `start.triggerType` is on the list in `../../shared/fault-paths/fault-paths.md`
§ Marketing Flows — Fault Paths Only When Asked) where the user didn't ask for
error handling, the plan has no fault paths. Don't ask whether to add them, don't
offer to add them, and don't list their absence as a note or a risk.

**[EVOLVE] Highlight the change in the summary.** Mark affected steps with a
text prefix:
- Added steps: prefix with `+ ` (e.g., `+ Send Email`)
- Modified steps: prefix with `~ `
- Removed steps: omit (the summary is the post-change state)

If the user supplied the current design in a readable form and the change is
small, a short "before / after" step list is acceptable.

### Security note (present with the plan summary)

Alongside the plan summary, present a short **Security** block so the user
approves the security posture alongside the design — inline just below the plan
summary unless the active surface specifies a different presentation channel.
Include:

- **Run mode** — user context (default) vs. system mode; if
  `SystemModeWithoutSharing`, state that sharing/CRUD/FLS are bypassed and why
  it's needed.
- **Guest exposure** — whether the flow is reachable by Experience Cloud /
  guest users.
- **Data scope** — any "store all fields" lookups or whole-record DML.
- Any advisory warnings from the `../../shared/security/security.md` checks, each
  with the recommended safer default.

*(EVOLVE: focus on what the edit changes — run mode, guest exposure, new "store
all fields" lookups or whole-record DML, untrusted input. If the change
introduces no new security concern, say so in one line.)*

If none apply, render one line:
`Security: user context, no guest exposure, fields scoped — no concerns.`
These are advisory — never block the plan on them; the user decides whether to
accept.

### Phase 2 closing

Present the plan summary (business-language step list) followed by the Security
note and ask for approval:

> Approve this plan?
>
> Reply "approve" / "yes" to save, or describe what to change.

Valid responses:
- **Accept** → proceed to Phase 3 (Save).
- **Refine** → adjust the design, re-present the plan summary, re-ask.
- **Reject** (EVOLVE) → ask the user what to revisit; iterate until accept or abandon.

Do not call `POST /services/data/vXX.0/flowbuilder/flow/actions/save` without an explicit accept of the
plan summary.

---

## Phase 3 — Save

**Save policy.** If the surface config declared save DISABLED, skip persistence: run
the steps below through step 5's validate, then hand the final FDL to the client
once. Never hand it off before validate. Otherwise proceed with the save steps below.

### Save steps

1. **Materialize the FDL.** Fill in element shapes from the per-element skills.
   Apply mutual-exclusivity and mode rules documented in each element's skill
   file. *(EVOLVE: emit the full working graph — the loaded flow plus the
   surgical change, with all untouched parts preserved verbatim — **except**
   the read-back-form normalization described in the surgical rule above,
   which applies even to untouched elements. See `../../shared/anti-patterns.md`
   item 38.)*

2. **Handle `processMetadataValues` — mode-branched:**
   - **GENERATE except `CustomerLifecycle`:** always emit in the top-level `metadata` object:
     ```json
     "processMetadataValues": [
       { "name": "BuilderType", "value": { "stringValue": "LightningFlowBuilder" } },
       { "name": "CanvasMode",  "value": { "stringValue": "AUTO_LAYOUT_CANVAS" } }
     ]
     ```
     `AUTO_LAYOUT_CANVAS` is the required default for net-new flows, emitted
     **independently of** `BuilderType` — the two are separate PMVs; never gate
     emitting one on the presence of the other. Absence is not neutral: the
     builder opens a canvas-mode-less flow in **Free-Form**. Emitting the
     `CanvasMode` entry is a hard gate on a net-new save — do not rely on the
     server-side backfill, which covers only the persisted `POST /services/data/vXX.0/flowbuilder/flow/actions/save` net-new
     path, not the no-persist hand-off or other save types (see
     `../../shared/anti-patterns.md` item 37).
   - **GENERATE `CustomerLifecycle`:** omit `BuilderType`, `CanvasMode`, and
     `OriginBuilderType`. Emit only `{ "name": "ObjectType", "value": {
     "stringValue": "<metadata.start.object>" } }` — a `CanvasMode` PMV is rejected.
   - **EVOLVE:** preserve the source flow's `processMetadataValues` **verbatim**
     — never inject, overwrite, or flip `BuilderType`/`CanvasMode`/`OriginBuilderType`.
     If the source carries no `CanvasMode`, leave it absent: the flow is already
     Free-Form in the builder, and stamping `AUTO_LAYOUT_CANVAS` would silently
     re-layout (and can corrupt) an existing flow. Never synthesize
     `OriginBuilderType`. Canvas mode is the user's to change, never the agent's.
     For `CustomerLifecycle`, preserve or set only `ObjectType` to match
     `metadata.start.object`; do not inject canvas entries.

3. **Determine `saveType` — mode-branched:**

   - **GENERATE:** new definition (net-new save). Use `saveType: "createNewFlow"`.
     **Name-collision guard:** before saving, if the chosen flow label /
     `fullName` would collide with an existing flow definition in the org,
     surface it to the user and confirm before proceeding (rename, or
     intentionally version the existing one). Do not silently create a
     duplicate or clobber an existing definition.
   - **EVOLVE:**

     | Situation | saveType |
     |---|---|
     | Editing the current draft version in place | `saveDraft` with `currentFlowId` |
     | Saving as a new version (keep old active) | `saveAsNewVersion` |
     | Renaming / new API name | `saveAsNewDefinition` — confirm with user first |

     The standalone MCP `POST /services/data/vXX.0/flowbuilder/flow/actions/save` contract does not expose the legacy
     `updateFlow` value. Use `saveDraft` for in-place draft updates.

4. **Pre-save Auditor pass** — repeat the Phase 2 Auditor checks plus:
   - **Schema check:** the flow matches `../../shared/flow-metadata-schema.md`, and every element used matches its own reference: only documented keys, at the documented level, with values that element accepts.
   - `no_conditions` internal placeholder omitted (replaced by `[]` and absent logic field). See `../../shared/anti-patterns.md` item 12.
   - `sortOrder: "NotSorted"` omitted (both `sortOrder` and `sortField` absent). See `../../shared/anti-patterns.md` item 9.
   - `storeOutputAutomatically: true` paired with empty or absent output assignments. See `../../shared/anti-patterns.md` item 15.
   - **[GENERATE] Process metadata present:** `processMetadataValues` is **non-empty**; for every process type except `CustomerLifecycle`, require `CanvasMode: AUTO_LAYOUT_CANVAS` + `BuilderType: LightningFlowBuilder` (each emitted independently — a missing or empty `[]` array opens the flow in Free-Form). For `CustomerLifecycle`, require only `ObjectType` matching `metadata.start.object` and reject canvas entries. Do not synthesize `OriginBuilderType`; preserve it only when evolving a supported source that already has it. See `../../shared/flow-properties/flow-properties.md` § "Canvas Mode and `processMetadataValues`" and `../../shared/anti-patterns.md` item 37. *(EVOLVE: preserve the source's `processMetadataValues` verbatim — never inject or flip.)*
   - **[`AUTO_LAYOUT_CANVAS`] End/fault topology (re-verify):** at materialization/connector-wiring time, confirm every terminating branch reaches an explicit End. A shared End (2+ non-fault connectors into one entry) is valid — do not flag or split it. A `faultConnector` targeting an End is not a defect (it drops silently on reload); advise a handler only for observability. See `../../shared/anti-patterns.md` item 38.
   - **[GENERATE; `AUTO_LAYOUT_CANVAS`; `apiVersion` ≥ 68.0] Explicit ends present:** the materialized payload carries an `ends[]` array, and every terminating branch's connector targets an entry in it (`END_ELEMENT_n`) — dedicated or shared. Below 68.0 and on Free-Form, confirm `ends[]` is **absent** (branches omit their connector) — a Free-Form flow must never carry `ends[]`. See `../../shared/end/end.md`. *(EVOLVE: `ends[]` matches the source plus any Ends added for new auto-layout branches.)*
   - **[`AUTO_LAYOUT_CANVAS`] End referential integrity:** every connector whose `targetReference` is an End name has a matching `ends[]` entry with that exact `name`, and every `ends[]` entry is targeted by at least one connector. A connector to an undefined End fails the save with **"`<EndName>` not found"** — **fix by ADDING the `ends[]` entry, never by removing the connector** (removing it deletes the terminating branch). See `../../shared/anti-patterns.md` item 14 and `../../shared/end/end.md` § Referential integrity.
   - **Coordinate bounds:** require every `locationX` and `locationY` to be
     between `0` and `500000`, inclusive. Negative coordinates fail
     `POST /services/data/vXX.0/flowbuilder/flow/actions/save` with `ELEMENT_COORDINATES_INVALID` even under
     `AUTO_LAYOUT_CANVAS`. See `../../shared/node/node.md`.
   - **Coordinates present on every node:** the `start` element, every `ends[]`
     entry and every other canvas element carry `locationX` and `locationY`
     (`0` and `0` for `start` and the Ends; in Flow XML, `<locationX>` and
     `<locationY>` inside `<start>` and inside each `<ends>`), whatever the
     trigger. One missing pair and the org rejects the flow:
     `Required field is missing: locationX`.
   - **Security posture** (advisory): re-run the `../../shared/security/security.md` checks against the materialized FDL. Warn only; never block the save. See `../../shared/anti-patterns.md` item 28.
   - **Read-back-form scheduling fields.** Scan the materialized payload for `schedule.startTime`/`schedule.endTime`/`schedule.startDate`/`schedule.endDate` (Start element, Scheduled trigger) and `resumeTime`/`resumeDate` (Wait element) that are still in server read-back shape — a `{ "timeInMillis": N }` object for a time field, or an epoch-millis integer for a date field. Convert every one to its wire-string form (`"HH:mm:ss.SSS"` / `"YYYY-MM-DD"`) before calling `POST /services/data/vXX.0/flowbuilder/flow/actions/save`, on touched AND untouched elements alike. See `../../shared/anti-patterns.md` item 39.
   - Any non-empty `customErrors[]` when `triggerType` is absent or not `RecordBeforeSave`/`RecordAfterSave`? Invalid — save fails with `TRIGGER_TYPE_ELEMENT_NOT_SUPPORTED`. Retarget fault paths to a `Log_Error` actionCall or a `$Flow.FaultMessage` Assignment. See `../../shared/anti-patterns.md` item 2. *(Observability is advisory — prefer a persisted/notified handler; see `../../shared/fault-paths/fault-paths.md` § Observable vs. In-Memory-Only Fault Handling.)* *(Redundant with the Phase 2 check above — Phase 2 should have caught this, but it is re-verified here because materialization in Step 5 can introduce or reconnect a `customErrors` element after the Phase 2 pass.)*
   - **Transform depth and scoping rule**: for any `transforms[]` element, verify the depth difference between the deepest source `elementReference` (number of `[$EachItem]` iterators) and the output depth is ≤ 1. A depth-2 source cannot produce a depth-1 **primitive** output — that is an invalid use case for Map (use Loop + Assignment instead). For SObject/Apex output at depth-N, verify that the same `transformValueActions` array contains at least one scoping action at each intermediate depth level 1 through N-1 (an action whose `elementReference` has exactly that many `[$EachItem]` iterators). Same rule applies to Sum/Count on nested collections — scoping lines must establish the collection hierarchy. See `../../elements/transform/types/map.md` § Nested collection scoping line missing.
   - **Send to Journey live gate**: rerun the pre-save checklist in
     `../../elements/action-call/send-to-journey.md`. Stop when any live selector,
     Segment binding, schema URI, requiredness flag, or required mapping differs
     from the materialized FDL.

5. **Persist per the active surface config's save policy.** If the active surface config
   disables persistence, do not save. Instead call
   `dispatch(method: "POST", url: "/services/data/vXX.0/flowbuilder/flow/actions/validate", body: {"flow": {"fullName": "<flow API name>", "metadata": <materialized FDL>}})`.
   Fix its `errors[]` and `warnings[]` (even when `isSuccess: true`) on what
   this change touched — on EVOLVE, leave the rest unchanged (minimal-surface
   rule) and report it only where the surface's response policy permits — and,
   if anything changed, re-validate (**cap at 3 silent retries**). A 400 that
   rejects the flow definition (e.g. `ILLEGAL_QUERY_PARAMETER_VALUE`, "not a
   valid flow definition") may mean the step 4 schema check missed something.
   Redo it on what this change touched; if that finds a defect, fix it and
   re-validate under the same cap. Otherwise treat the call as having no
   result. Any other non-2xx, a 400 once the cap is reached, or a response
   without `isSuccess` is a call with no result. If the first validate has no
   result, return the FDL unchanged. If a re-validate has no result or adds an
   issue, return the FDL from before that round's fixes. Otherwise return the
   latest FDL.
   Report per the surface's response policy.

   If persistence is enabled, construct the complete save request before
   dispatching. The request root contains `flow` and `saveType`; `fullName` and
   `metadata` belong **inside** `flow`. For a new flow, use this envelope:

   ```json
   {
     "flow": {
       "fullName": "My_Flow",
       "metadata": {}
     },
     "saveType": "createNewFlow"
   }
   ```

   Replace the empty example `metadata` with the complete materialized FDL.
   For an existing flow, keep the same envelope and use the Step 3 `saveType`
   and any required `currentFlowId` at the request root. Before dispatch,
   verify that root `flow` is an object, root `saveType` is present, and root
   `fullName`, `metadata`, and `versionNumber` are absent. A bare tooling Flow
   body causes HTTP 400 `JSON_PARSER_ERROR` (`Unrecognized field "fullName"`).
   Call `dispatch(method: "POST", url: "/services/data/vXX.0/flowbuilder/flow/actions/save", body: <checked envelope>)`.
   On failure, parse
   `errors[]` and `warnings[]`, map each to an anti-pattern or shape rule, apply a
   targeted fix, and retry. **Cap at one silent retry.** If still failing after
   one retry, surface the verbatim `errors[]` and `warnings[]` to the user.
   *(Exception: a step flow that `../orchestrate/orchestrate.md` co-generates
   uses that recipe's step-flow save loop instead: up to 3 attempts, until the
   save's `status` is `Draft`.)*

6. **Return the deep link.** If the active surface config's save policy disables
   persistence, skip this step — no saved definition exists to link to, and you
   already returned the FDL to the client in step 5. Otherwise append the
   "Open in Salesforce" link per `../../shared/preview-renderer.md` § "Deep-link template".
   Stop after this hand-off. Do not call `POST /services/data/vXX.0/flowbuilder/flow/{flowId}/actions/activate` (activateFlow — DO NOT DISPATCH, quarantined), `POST /services/data/vXX.0/flowbuilder/flow/{flowId}/actions/deactivate`, or
   `POST /services/data/vXX.0/flowbuilder/flow/{flowId}/actions/submit-for-activation` after a successful save. Direct activation is
   disabled, deactivation is the inverse operation, and activation-approval
   submission is not a fallback activation route.

*(EVOLVE: after a successful save, treat `GET /services/data/vXX.0/flowbuilder/flow/{flowDefinitionId}/versions` and
`GET /services/data/vXX.0/flowbuilder/flow/{id}/validation-results` as stale — re-fetch on next use.)*

---

## Connector Wiring

- Regular outgoing edge: `connector` field.
- Default (no-match) branch on Decision: `defaultConnector`.
- Loop per-iteration path: `nextValueConnector`. Loop exit: `noMoreValuesConnector`.
- Fault path: `faultConnector`.
- `targetReference` on every connector must be the dev-name of the target element, never a GUID.
- Last element in a branch (flow end): on GENERATE with `AUTO_LAYOUT_CANVAS` at resolved `apiVersion` ≥ 68.0, point its `connector` at a dedicated `ends[]` entry (`END_ELEMENT_n`, one per branch — the v68+ default); below 68.0 and on any Free-Form flow, omit the `connector` field entirely and emit no `ends[]` (**never emit `ends[]` on Free-Form**). See `../../shared/end/end.md`.
- A terminal error-only screen (reached via `faultConnector`) takes no non-fault inbound edge; keep the last success screen terminal instead of pointing it at the error screen. See `../../shared/anti-patterns.md` item 36.

---

## Element Skill Registry

Load the relevant skill **before** generating any element. Do not preload all
skills at session start — load lazily as the design (GENERATE) or the change
(EVOLVE) names each type.

### Elements

| Element | Skill Path | Load When |
|---|---|---|
| Assignment | `../../elements/assignment/assignment.md` | Set/change a variable value |
| Decision | `../../elements/decision/decision.md` | Branching / conditional logic |
| Experiment | `../../elements/experiment/experiment.md` | A/B test split in journey flows |
| Loop | `../../elements/loop/loop.md` | Iterate over a list/collection |
| Custom Error | `../../elements/custom-error/custom-error.md` | Throw a custom error message |
| Screen | `../../elements/screen/screen.md` | User input or display |
| Screen Fields | `../../elements/screen/SCREEN-FIELDS.md` | Configuring specific screen fields |
| Get Records | `../../elements/record-lookup/record-lookup.md` | Query Salesforce records |
| Create Records | `../../elements/record-create/record-create.md` | Insert new Salesforce records |
| Update Records | `../../elements/record-update/record-update.md` | Modify existing Salesforce records |
| Delete Records | `../../elements/record-delete/record-delete.md` | Remove Salesforce records |
| Action / Apex | `../../elements/action-call/action-call.md` | Call Apex, external service, or invocable action; **show a toast / success / error / notification message, or navigate / open a page / URL** (LWC local actions) |
| Exit from a Flow | `../../elements/action-call/action-call.md` | Remove an Individual from one named running marketing flow or all applicable running marketing flows; this is an invocable action, not a Subflow |
| Send Email / SMS / RCS Message | `../../elements/action-call/action-call.md` | Send a marketing email, text or RCS message (`sendEmailMessage`, `sendSmsMessage`, `sendRcsMessage`); read the action's section (Phase 2 step 4, Marketing message probe sequence) |
| Apex Plugin | `../../elements/action-call/action-call.md` | Legacy Apex Plugin element (section in action-call skill) |
| AI Agent Response | `../../elements/action-call/action-call.md` | Generate AI agent response (section in action-call skill) |
| Subflow | `../../elements/subflow/subflow.md` | Call another flow |
| Wait / Pause | `../../elements/wait/wait.md` | Pause until a time, event, or condition |
| Start Element | `../../elements/start/start.md` | Configure flow trigger and entry criteria |
| Audience Flow — shared contract | `../../elements/start/audience-common.md` | Shared build contract for ALL audience triggers (Segment / List / CampaignMember / RecordQuery) — run schedule, top-level `timeZoneSidKey`, top-level `dataSpace`, optional `dataGraph`, re-entry, save-and-activate gates, builder round-trip defaults. **Load FIRST for any audience trigger**, then the matching per-trigger file below |
| Segment-Triggered Flow | `../../elements/start/segment-triggered.md` | Segment (Audience) marketing flow build guide — REQUIRED (after `audience-common.md`) before configuring a Segment flow (segment binding chain, eligibility gate, `publishSegment`, outreach actions, `$Record` member context) |
| List / CampaignMember Flow | `../../elements/start/list-campaignmember.md` | Actionable List (`triggerType: List`) + Campaign Member (`triggerType: CampaignMember`) build guide — REQUIRED (after `audience-common.md`) before configuring either (the `start.listAction` binding, audience-selection gate, `$Input` member handles, validate-vs-save gotcha, examples) |
| Record Query Flow | `../../elements/start/recordquery.md` | Record Query (`triggerType: RecordQuery`, all records of one SObject matching a filter) build guide — REQUIRED (after `audience-common.md`) before configuring it (the `start.object` + optional `start.filters` binding, `CRM_OBJECT_SELECTION_REQUIRED` gate, direct `$Input.<field>` record context, example) |
| Collection Processor | `../../elements/collection-processor/collection-processor.md` | Filter, sort, or map a collection into **another collection** (many → many). For narrowing a collection to a **single** record, use Collection Filter Criteria (Resources, below) instead. |
| Transform | `../../elements/transform/transform.md` | Extract or map fields uniformly from a collection (prefer over Loop + Assignment when no per-item branching is needed); transform data between collections |
| Rollback | `../../elements/rollback/rollback.md` | Rollback database changes in a transaction |
| Exit Rule | `../../elements/exit-rule/exit-rule.md` | End a Segment/On-Demand/Journey/Digital Form flow interview early for an individual on a condition or an engagement event |
| Group (canvas layout) | `../../shared/group/group.md` | Node grouping requested (`groups`/`nodeGroups`/FlowNodeGroup, "add elements to a group") — **NOT authorable from AI surfaces**; load to decline & redirect to Flow Builder |

### Resources

| Resource | Skill Path | Load When |
|---|---|---|
| Variable | `../../resources/variable/variable.md` | Storing / passing data values |
| Constant | `../../resources/constant/constant.md` | Fixed values used throughout the flow |
| Formula | `../../resources/formula/formula.md` | Calculated expressions |
| Text Template | `../../resources/text-template/text-template.md` | Dynamic text with merge fields |
| Choice / Choice Sets | `../../resources/choice/choice.md` | Choices for screen picklists/radio buttons |
| Collection Filter Criteria | `../../resources/collection-filter-criteria/collection-filter-criteria.md` | Filter + sort an existing collection down to a **single** record (top/first match, e.g. highest-value opp, most recent case); read-only. **Not** for producing a new collection — that's Collection Processor. |

### Shared Features

| Feature | Skill Path | Load When |
|---|---|---|
| Conditions & Logic | `../../shared/conditions/conditions.md` | AND/OR/custom filter logic |
| Record Filters | `../../shared/record-filter/record-filter.md` | Building `filters[]` on recordDeletes, recordUpdates, recordLookups, recordCreates (upsert), or start |
| Output Assignments | `../../shared/output-assignments/output-assignments.md` | Mapping element outputs to variables |
| Fault Paths | `../../shared/fault-paths/fault-paths.md` | Error handling for DML/Action elements |
| Ends | `../../shared/end/end.md` | Terminating a branch — when to store an explicit `ends[]` End (GENERATE, `AUTO_LAYOUT_CANVAS`, `apiVersion` ≥ 68.0) vs. omit the connector; never on Free-Form |
| Validation Rules | `../../shared/validation-rules/validation-rules.md` | Validating screen field input |
| Flow Properties | `../../shared/flow-properties/flow-properties.md` | Flow label, API name, run mode, API version |
| Security | `../../shared/security/security.md` | Auditing run mode, data scope, and untrusted input — advisory security checks run before every save |

### Reference Files (always available)

| Topic | File | Load When |
|---|---|---|
| Anti-patterns | `../../shared/anti-patterns.md` | Before every save — mandatory Auditor pass |
| Value field rules | `../../shared/value-rules.md` | Setting field values, conditions, assignments, action parameters |
| Formula expression language | `../../shared/formula-expression.md` | Writing any formula expression — operators, functions, picklist/ISPICKVAL, limits, type coercion |
| Flow JSON schema | `../../shared/flow-metadata-schema.md` | Building a complete flow payload or debugging a JSON shape error |
| Process/trigger decision | `../../shared/flow-type-resolver/flow-type-resolver.md` | Picking processType + triggerType in Phase 2 |
| Tool catalog / limits | `../../shared/server-functions.md` | Checking tool costs, governor limits, unregistered tool names |
| Preview rendering | `../../shared/preview-renderer.md` | "Open in Salesforce" deep link appended after a successful save |

---

## Mandatory Probes by Element Type

Run these in Phase 2 step 4 (Probe schema), once per unique argument set:

| Element type | Tool to call |
|---|---|
| `actionCalls` | `dispatch_readonly(method: "GET", url: "/services/data/vXX.0/flowbuilder/action/invocable-action-details", queryParams: { actionType, actionName })` |
| `recordCreates`, `recordUpdates`, `recordLookups`, `recordDeletes` | `dispatch_readonly(method: "GET", url: "/services/data/vXX.0/flowbuilder/platform/entity/{apiName}/fields")` |
| `decisions`, `recordLookups` (filters) | `GET /services/data/vXX.0/flowbuilder/schema/flow-capabilities` (read `.operators`) |
| `subflows` | `GET /services/data/vXX.0/flowbuilder/flow/subflows` |
| Screen `ComponentInstance` fields | `GET /services/data/vXX.0/flowbuilder/screen-component` + `GET /services/data/vXX.0/flowbuilder/screen-component/{apiName}` |

---

## Build Order (Phase 3 metadata dependency order)

```text
1. Flow Properties      (label, processType, apiVersion, runInMode, interviewLabel,
                         processMetadataValues with BuilderType + CanvasMode; preserve source OriginBuilderType only)
2. Resources            (variables, constants, formulas, text templates, choices)
3. Start element        (trigger configuration)
4. Flow elements        (in execution order)
5. Connectors           (linking elements; on GENERATE + AUTO_LAYOUT_CANVAS + apiVersion >= 68.0,
                         each terminating branch's connector targets a dedicated ends[] entry)
6. Ends                  (ends[] entries — GENERATE + AUTO_LAYOUT_CANVAS + apiVersion >= 68.0 only;
                         none below 68.0 or on Free-Form. See shared/end/end.md)
```

*(EVOLVE preserves the existing order and only inserts/removes/modifies the
elements the change requires — see the surgical rule.)*

---

## Common Failures

**Calling save_and_validate before the plan gate.** Hard contract violation.
The user has not approved the plan summary yet; saving without their
accept is a forbidden write. The plan gate is never skipped, even with an
override phrase.

**Downgrading an evolve to a net-new build because JSON was missing.** If the
intent is to edit an existing flow, an empty/absent flow body is a STOP-and-ask
condition, not a license to generate a fresh flow. See Phase 0.

**Over-editing in EVOLVE.** Rewriting, reformatting, or "improving" elements the
user did not ask about violates the surgical rule and makes the edit
non-reviewable. Touch only what the change requires.

**Re-calling probe tools across phases.** Each `GET /services/data/vXX.0/flowbuilder/platform/entity/{apiName}/fields`
or `GET /services/data/vXX.0/flowbuilder/action/invocable-action-details` call counts against Salesforce API rate
limits. If Phase 2 step 4 already called a tool with the same arguments,
reuse the result throughout the rest of the phase. See `../../shared/anti-patterns.md` item 23.

**Skipping the Auditor checks.** The platform validator returns one error at a
time. Run Auditor checks locally before every save call.

**Handing off activation without version identification.** Report the flow full
name, version number, last-modified-by, last-modified-date, and target org before
directing the user to activate in Flow Builder UI. Never call `POST /services/data/vXX.0/flowbuilder/flow/{flowId}/actions/activate` (activateFlow — DO NOT DISPATCH, quarantined).
See `../../shared/anti-patterns.md` item 21.

**Emitting XML.** The save-and-validate API accepts JSON only. Never emit XML
angle brackets, namespace declarations, or CDATA sections. See
`../../shared/flow-metadata-schema.md`.

**Forgetting `processMetadataValues` (GENERATE).** An absent `CanvasMode` opens
the flow in **Free-Form** in the builder. Always emit the
`CanvasMode=AUTO_LAYOUT_CANVAS` entry (independently of `BuilderType`) for a
net-new canvas-based flow — don't rely on the server backfill, which covers only
the persisted `POST /services/data/vXX.0/flowbuilder/flow/actions/save` net-new path. For `CustomerLifecycle`, emit only
`ObjectType` matching `metadata.start.object` (no canvas entries). In EVOLVE,
preserve the source's values **verbatim** — never inject or flip. See
`../../shared/anti-patterns.md` item 37.

---

## Stop Conditions

Stop and ask the user when:

- **[EVOLVE]** No source flow JSON is available and the user wants element-level edits.
- Object or field names are not specified after Phase 2 schema probing reveals the ambiguity.
- Conflicting trigger requirements emerge during Phase 2.
- The intent is ambiguous between a new flow and an edit (ask the Phase 0 tie-breaker).
- The plan summary is rejected twice without convergence.
- One failed `POST /services/data/vXX.0/flowbuilder/flow/actions/save` retry in Phase 3.
- Probe budget exceeded (> 10 probe calls for one Phase 2).
- A Send to Journey business unit is missing, unmapped, or mapped to a Data Space other than `metadata.dataSpace`.
- A Send to Journey lookup has no compatible Journey, or has multiple matches without a user selection.
- The `sendToJourney` descriptor, Journey schema, or a required Journey-field mapping cannot be resolved.
- **[EVOLVE]** The requested change conflicts with a platform constraint (e.g., adding a DML element inside a before-save flow).
- **[EVOLVE]** The edit requires renaming the flow's API name (`saveAsNewDefinition`) — confirm before proceeding.
- **[EVOLVE]** Architecture Pushback: the requested change introduces an anti-pattern (CRUD in loop, missing fault path outside a marketing flow, hard-coded ID) — surface it, do not silently fix.
