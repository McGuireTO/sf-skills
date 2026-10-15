---
id: flow.shared.anti-patterns
name: flow-anti-patterns
description: "Ruthless do-not-do list for flow generation. Load when auditing or generating flow metadata to catch the most common failure modes before they reach save-and-validate."
metadata:
  version: "1.0"
  related-skills: flow-fault-paths, flow-conditions
---

# Flow Anti-Patterns — Do-Not-Do List

Each entry explains **what breaks** if the rule is ignored. Check this list before finalizing any flow skeleton and before calling save-and-validate.

---

## 1. CRUD inside a Loop

A **`recordCreates`** (Create Records), **`recordUpdates`** (Update Records), **`recordDeletes`** (Delete Records), or **`recordLookups`** (Get Records) element whose connector chain is reachable from a Loop's `nextValueConnector` path (i.e., inside the loop body).

**What breaks:** At N ≥ 200 records, you hit the 150-DML governor limit (or 100-SOQL limit for lookups). The flow throws a `LimitException` and rolls back partial writes. In production this manifests as silent failure for bulk loads.

**Specific concern for `recordLookups`:** The 100-SOQL-query governor limit is reached at only N≥200 records, making this easier to hit than the 150-DML limit. A Get Records inside a loop over 200 accounts will fail at runtime.

**Correct pattern depends on flow type and use case:**

### For AutoLaunchedFlow with multi-level hierarchical data (PREFERRED)

**Use the HDM (Hierarchical Data Model) pattern:**

When your flow needs to traverse parent → child → grandchild relationships (e.g., Account → Opportunity → OpportunityLineItem, Case → CaseComment → Attachment), do NOT use nested loops with CRUD. Instead:

1. **Query ALL records from each hierarchy level upfront** using relationship-based filters:
   - Example: `Get Records: Opportunity WHERE StageName IN ('Negotiation/Review', 'Closed Won')`
   - Then: `Get Records: OpportunityLineItem WHERE Opportunity.StageName IN ('Negotiation/Review', 'Closed Won')`
   
2. **Use Collection Processor (Filter/Sort)** elements to organize data by relationship fields (`AccountId`, `OpportunityId`, etc.)

3. **Use Assignment elements** to build the final report/data structure

4. **NO loops with CRUD inside** — all queries happen upfront

**Result:** Only 2-3 SOQL queries total regardless of data volume (not N×M queries in nested loops)

**When to use:** AutoLaunchedFlow (Scheduled, Record-Triggered, Platform Event) where you can load all data upfront without user-facing latency concerns

**Example transformation:**

**Wrong (nested loops with CRUD):**
```text
Loop over Accounts
  └─ Get Records: Opportunities for current Account  ← 100+ SOQL calls
     └─ Loop over Opportunities
        └─ Get Records: LineItems for current Opp  ← 1000+ SOQL calls
```

**Correct (HDM pattern):**
```text
Get Records: All Opportunities (filtered by stage)  ← 1 SOQL
Get Records: All OpportunityLineItems (filtered by Opp.stage)  ← 1 SOQL
Collection Sort: Group by AccountId
Collection Filter: Organize by OpportunityId
Assignment: Build report structure
```

### For single-level accumulate-then-bulk operations

When you're NOT traversing hierarchies but need to transform data in a loop before a single bulk operation:

**Accumulate inside the loop, CRUD outside:**

1. Build a collection variable inside the loop using **Assignment** with `operator: Add` to a collection variable declared `isCollection: true`
2. Do NOT perform CRUD inside the loop body
3. After the loop exits via `noMoreValuesConnector`, perform a **single bulk CRUD operation** on the accumulated collection

**Result:** 1 DML/SOQL per loop (not N)

**Example:**
```text
Loop over input records
  └─ Assignment: Add transformed record to varAccumulatedRecords  ← No CRUD
Exit loop
└─ Create Records: varAccumulatedRecords  ← 1 DML for all records
```

### For Screen Flow

In Screen Flows, user interaction and progressive disclosure often require showing interim results. The HDM approach (load everything upfront) may cause unacceptable latency. Balance these options:

- **Small datasets (< 50 records):** Use accumulate-then-bulk pattern
- **Large datasets:** Consider pagination, subflows, or platform events to offload to AutoLaunchedFlow
- **Never:** Put CRUD inside a loop without accumulation

### When loops with CRUD are acceptable

- **Single-record operations** where max 1 iteration is architecturally guaranteed (e.g., loop over a screen-inputted list of 1-5 items)
- **Callouts to external systems** (not Salesforce CRUD) — different governor limits apply
- **Before-save flows** mutating the triggering record in-place (no DML counted in RecordBeforeSave)

---

---

## 2. Missing `faultConnector` on a fault-capable element

Element types that can throw at runtime: `actionCalls`, `apexPluginCalls`, `recordLookups`, `recordCreates`, `recordUpdates`, `recordDeletes`, `waits`.

> **Marketing flows are the exception (check this first).** In a marketing
> flow, a missing `faultConnector` is **not** this anti-pattern. A marketing
> flow is one whose `start.triggerType` is on the list in
> `shared/fault-paths/fault-paths.md` § Marketing Flows — Fault Paths Only
> When Asked. Add fault paths there only when the user asks for error
> handling; otherwise emit none and don't flag their absence.

> **Action-specific exceptions:** Follow the action's dedicated guide when its
> persisted metadata omits `faultConnector`. LWC local actions have verified
> no-fault shapes. The `sendToJourney` and `sendSmsMessage` examples omit
> `faultConnector` because they come from Segment flows, which are marketing
> flows; the marketing-flow rule above covers them. Don't carry that omission
> into a non-marketing flow.

> **Note on Subflows:** Subflow elements do NOT support `faultConnector`. If a called subflow throws an unhandled exception, it propagates to the calling flow as an unhandled error. To catch errors from a subflow, add a `faultConnector` **inside the referenced (child) flow** itself. Never emit `faultConnector` on a `subflows[]` entry — it causes a save-time schema rejection. See `elements/subflow/subflow.md` § "No Fault Path".

> **Note on Autolaunched Flows:** `customErrors` is valid ONLY when `triggerType` is `RecordBeforeSave` or `RecordAfterSave`. If `triggerType` is absent (Autolaunched Flow, no trigger) — or is `Scheduled`, `PlatformEvent`, or any other non-record-triggered value — the flow must not contain any `customErrors[]` element at all, whether it's wired to a `faultConnector`, a regular `connector`, or left unconnected. Save fails with `TRIGGER_TYPE_ELEMENT_NOT_SUPPORTED` ("A flow can't include Custom Error elements when TriggerType is set to None"). Target a `Log_Error` actionCall or an Assignment capturing `$Flow.FaultMessage` instead (for observability, prefer a persisted/notified handler — a bare Assignment with no downstream consumer is in-memory-only; advisory, see the Observability note below). See `elements/custom-error/custom-error.md`.

**What breaks:** A runtime exception escapes to the user as the generic "An unhandled fault has occurred in this flow" screen. In an autolaunched flow with no UI, the exception silently aborts the interview and rolls back the transaction. In a record-triggered flow, the originating DML is rolled back — the user's UI tells them the save succeeded but it did not.

**Correct pattern:** Every fault-capable element gets a `faultConnector` to a Log_Error action (autolaunched flow), a `customErrors` element (record-triggered flow to block the save with a message), or an error screen (Screen Flow with a recoverable path). Apply the marketing-flow exception and the action-specific verified exceptions before this generic rule. See `shared/fault-paths/fault-paths.md`.

> **Observability (headless flows — advisory):** a fault path is only *complete* when the error leaves a durable trace. A `Log_Error` action here means an element that **persists or notifies** — a `recordCreate` to a log/error object, an admin email/notification, or a platform event — not a bare Assignment that only stores `$Flow.FaultMessage` in a variable. In a headless flow (any flow with no screen-rendering capability — Autolaunched, Scheduled, PlatformEvent, Segment, and other event-triggered types; screen-bearing types like Screen Flow, `UnifiedSchedulingFlow`, and `AgxScreenFlow` are **not** headless — route their faults to an error Screen instead), an Assignment-only fault path satisfies the `faultConnector` rule at save time but leaves failures **silently unlogged** — the value is discarded when the interview ends. Pair the Assignment with a persistence/notification element, or route the fault directly to one. **Exceptions:** an Assignment to an `isOutput` variable that a parent flow (Subflow) or Apex/REST caller consumes is observable (the caller handles it); Screen flows are exempt (the error Screen surfaces the message). This is **advisory** — the metadata is valid, not a save-time error. See `shared/fault-paths/fault-paths.md` § Observable vs. In-Memory-Only Fault Handling.

---

## 3. Hard-coded record IDs

Record IDs (`001...`, `005...`, `00G...`), `OrgWideEmailAddressId` literals, `RecordTypeId` literals, etc. embedded as literal string values in input parameters or assignment items.

**What breaks:** The flow ships fine but breaks the moment it is deployed to another org (sandbox to production, package install). The IDs do not exist there. Often discovered weeks later when a customer hits the broken path.

**Correct pattern:** Look up by name via `recordLookups`, use `$Label`, or use a `constants` resource that the customer can override per-org.

---

## 4. `variableAndFieldMapping` in flow metadata

Emitting `variableAndFieldMapping` field in flow element metadata.

**What breaks:** `variableAndFieldMapping` is a UI-only mode selector that tells the Flow Builder which configuration screen to show. It is NOT part of the flow metadata schema. Emitting it causes save validation to reject with "Unknown field" or silently ignore it, creating confusion about which output mode is active.

**Applies to:** Elements with output mode configuration:
- **`recordLookups`** (Get Records)
- **`actionCalls`** (Action/Invocable Action)
- **`subflows`** (Subflow)
- **`transforms`** (Transform)

**Correct pattern:** Never emit `variableAndFieldMapping` to metadata. Use only the documented output mode fields:

**For `recordLookups`:**
- `storeOutputAutomatically: true` (automatic mode, with or without `queriedFields`)
- `storeOutputAutomatically: false` + `outputReference: "varName"` (manual with variable)
- `storeOutputAutomatically: false` + `outputAssignments: [...]` (manual with field mapping)

**For `actionCalls`:**
- `storeOutputAutomatically: true` + `outputParameters: []` (automatic)
- `storeOutputAutomatically: false` + `outputParameters: [{ name, value }]` (manual)

**For `subflows`:**
- `storeOutputAutomatically: true` + `outputAssignments: []` (automatic)
- `storeOutputAutomatically: false` + `outputAssignments: [{ name, assignToReference }]` (manual)

**For `subflows`:**
- `storeOutputAutomatically: true` + `outputAssignments: []` (automatic)
- `storeOutputAutomatically: false` + `outputAssignments: [...]` (manual)

> `actionCalls` and `subflows` use **different** output array field names. Using `outputParameters` on a subflow (or `outputAssignments` on an action call) causes a save-time schema error.

**For `transforms`:**
- `storeOutputAutomatically: true` + `outputFieldApiName` in mappings (automatic)
- `storeOutputAutomatically: false` + `assignToReference` in targets (manual, requires org permission)

Output modes are mutually exclusive within each element type — you cannot mix automatic and manual output configurations.

---

## 5. `actionType: "flow"` in `actionCalls`

Calling a subflow via the legacy `actionCalls` form with `actionType: "flow"`.

**What breaks:** Appears to work but has subtly different bulk and fault-handling semantics from the supported `subflows` form. Future Salesforce upgrades may deprecate the legacy form.

**Correct pattern:** Put subflow calls in the top-level `subflows` array. The required field is `flowName` (not `actionName`). See `elements/subflow/subflow.md`.

---

## 6. Screen or Wait in the wrong process type

- A `Screen` element in any `AutoLaunchedFlow` (record-triggered, scheduled, platform-event, etc.).
- A `Wait` element in a `RecordBeforeSave` flow.

**What breaks:** Save validation returns an error like "Element type Screen is not supported for process type AutoLaunchedFlow with trigger type RecordAfterSave."

**Correct pattern:** Before drafting any skeleton, confirm the intended element types are supported for the chosen `(processType, triggerType)` pair. If the user wants both interactive screens and automation, propose a split-flow design: an AutoLaunchedFlow handles the automation and optionally publishes a platform event to a separate Screen Flow. *(Net-new / GENERATE only. In EVOLVE — editing a supplied flow — this is a process-type change: decline per `recipes/author/author.md` Phase 0; do not propose a separate flow.)*

---

## 7. Missing `defaultConnector` on a Decision element

A `decisions` element that has N outcome rules but no default branch.

**What breaks:** When no rule's conditions match, the interview has nowhere to go and aborts.

**Correct pattern:** Every `decisions` element must have either a `defaultConnector` pointing to the "no match" path (typically a Log_Error action or end node), or a `defaultConnectorLabel` that documents an intentional halt. *(In `AUTO_LAYOUT_CANVAS` at resolved `apiVersion` ≥ 68.0, a terminating default path reaches an explicit End — its own dedicated End or a shared End converged with other outcomes, both valid; below 68.0 omit the connector; item 38.)* See `elements/decision/decision.md`.

---

## 8. Missing `interviewLabel` or `apiVersion`

Top-level flow properties that are easy to omit.

**What breaks:**
- Missing `interviewLabel`: Save succeeds but debug logs show no identifying label, making post-mortem analysis impossible.
- Missing `apiVersion`: Save succeeds with a server default but the flow may behave differently across orgs running different API version defaults.

**Correct pattern:** Always emit both. Use the org's current API version for `apiVersion`.

---

## 9. `sortOrder: "NotSorted"` emitted as a literal string

On `recordLookups` and `dynamicChoiceSets`, the value `"NotSorted"` is an internal placeholder value meaning "no sort order is set."

**What breaks:** The server may interpret `"NotSorted"` as an invalid enum value, or silently fall back to alphabetical sort on a different field.

**Correct pattern:** When no sort is desired, omit both `sortOrder` and `sortField` entirely. Never emit the string `"NotSorted"` in saved metadata.

---

## 10. Relationship Traversal in Get Records Filters or queriedFields

Using relationship traversal syntax (field names containing `.` or `__r`) in `recordLookups[].filters[].field` or `recordLookups[].queriedFields[]` values.

**What breaks:** Field names silently corrupted to `"null__NotFound"` at save time. Flow saves but has activation-blocking errors: `"The field 'null__NotFound' for the object '[ObjectName]' doesn't exist."`

**Detection:** Scan filter and queriedFields for `.` or `__r` in field names

**Solution:** See `elements/record-lookup/patterns/basic-query.md` § "Relationship Traversal Limitations" for two-step query patterns, formula field alternatives, and Collection Processor approaches.

---

## 11. Merge Field Syntax in Assignment String Values

Using merge field template syntax (`{!...}`) directly inside assignment `stringValue` fields.

**What breaks:** Save-time validation error: `"The assignment uses a reference to '{![expression]}', which doesn't exist"`

**Detection:** Scan `assignments[].assignmentItems[].value.stringValue` for pattern `/\{!.+\}/`

**Solution:** See `elements/assignment/assignment.md` § "String Value Constraints" for Formula resource, Text Template resource, and sequential assignment patterns.

---

## 12. `"no_conditions"` internal placeholder value in saved metadata

When the UI's logic field equals `"no_conditions"`:
- The matching child array (`conditions` or `filters`) must be emitted as `[]`.
- The logic field itself (`conditionLogic` or `filterLogic`) must be **omitted** — not `null`, not the literal string.

**What breaks:** `"no_conditions"` is an internal UI placeholder that must never appear in saved metadata. On the `save_and_validate` path the server *normalizes* a stray `filterLogic: "no_conditions"` by stripping the key (not a hard rejection), but don't rely on that clean-up — emit the canonical omitted form. (Do NOT confuse this with a Decision outcome / Wait event that has `conditions: []`: that IS a hard save rejection, `RULE_MISSING_CONDITION`.)

**Correct pattern:** Applies to Decision outcomes, Wait events, Start, all Record* element filters, RecordChoiceSet filters, CollectionProcessor FILTER conditions, and FlowTest assertions. `shared/conditions/conditions.md` is authoritative for the exact save/normalize behavior.

---

## 13. Value field with two value keys, or a value key without its DataType sibling

A value field (`value`, `rightValue`, `defaultValue`, etc.) must emit **exactly one** value key (`stringValue`, `numberValue`, `booleanValue`, `dateValue`, `dateTimeValue`, `elementReference`, etc.) paired with its matching `*DataType` sibling.

**What breaks:**
- Two value keys: server picks one non-deterministically, producing hard-to-diagnose bugs.
- Value key without sibling `*DataType` (or vice versa): server rejects with a vague "invalid value field" validation error.

**Correct pattern:** Emit only the matching value key (`stringValue: "..."`, `numberValue: ...`, etc.) — no `valueDataType` companion in metadata. Never emit two value keys in the same value object. See `shared/value-rules.md`.

---

## 14. Connector `targetReference` pointing at a GUID instead of a dev-name

Connector `targetReference` values must be **dev-names** (the `name` field on the target element), not internal GUIDs.

**What breaks:** Save fails with "Element `<guid>` not found" because the runtime looks up elements by dev-name, not by GUID.

**Correct pattern:** Every `targetReference` matches the `name` field of the target element.

**Same failure, End targets — referential integrity between connectors and `ends[]`.** A connector (or `defaultConnector`, `nextValueConnector`, `noMoreValuesConnector`) whose `targetReference` is an **End name** requires a matching entry in the top-level `ends[]` array with that exact `name`. If the connector exists but the `ends[]` entry is missing, the save fails the same way — **"`<EndName>` not found"** (e.g. `End_Main not found`). This is the co-emission failure of the v68+ explicit-ends default: the terminating connector was wired but its `ends[]` entry was never emitted. **The fix is to ADD the missing `ends[]` entry, NOT to remove the connector** — removing the connector deletes the terminating branch and changes flow behavior. The invariant is bidirectional: every End-targeting connector resolves to an `ends[]` entry with that exact name, and every `ends[]` entry is targeted by at least one connector (a shared End — one entry targeted by 2+ non-fault connectors — is valid). See `shared/end/end.md` § Referential integrity and item 38.

---

## 15. `storeOutputAutomatically: true` with non-empty output assignments

When `storeOutputAutomatically: true`, the corresponding output array must be `[]` or omitted:
- `actionCalls` → `outputParameters: []`
- `recordLookups` → `outputAssignments: []`
- `subflows` → `outputAssignments: []`

Note: `actionCalls` uses `outputParameters`; `subflows` and `recordLookups` use `outputAssignments`. These field names are not interchangeable.

**What breaks:** Server returns a validation error saying the element has both automatic and manual output configured.

---

## 16. Element name exceeding 80 characters or containing non-ASCII characters

Element `name` (API/dev-name) rules:
- Maximum 80 characters.
- ASCII alphanumeric and underscore only.
- Must not start with a digit.
- Should not end with underscore.

**What breaks:** Save fails with "Invalid API name."

---

## 17. Duplicate element name within the same flow

Two elements in the same flow sharing the same `name` value.

**What breaks:** Save fails with "Duplicate element name."

---

## 18. Collection variable not declared `isCollection: true`

Assigning to a collection variable using `operator: Add` when the variable is not declared with `isCollection: true`.

**What breaks:** Runtime error "cannot use Add operator on a non-collection variable" on the first iteration.

**Correct pattern:** Every collection variable used in a Loop result must be declared with `isCollection: true` in `variables`.

---

## 19. Empty `filters` on a filter-based Record Delete

A `recordDeletes` element using filter-based mode (`object` is set, no `inputReference`) with empty `filters: []`.

**What breaks:** This would mass-delete every record on the object. The server rejects with "recordDeletes element has empty filters," but any agent building the flow should catch this before attempting to save.

---

## 20. DML on the triggering record in `RecordAfterSave` via `inputReference: "$Record"`

In an `RecordAfterSave` flow, updating `$Record` via `inputReference: "$Record"` on a `recordUpdates` element still fires as a separate DML statement. This is not the same as a before-save in-place update.

**What breaks:** Unexpected extra DML operation, potential infinite recursion if the flow entry criteria match after the update, and governor limit consumption.

**Correct pattern:** For in-place mutations on the triggering record without extra DML, use a `RecordBeforeSave` flow. For post-save side effects on related records, use `RecordAfterSave` with explicit filter-based record updates.

---

## 21. Handing off UI activation without confirming identity details

Directing the user to activate after saving a new version without first identifying the flow full name, version number, last-modified-by, last-modified-date, and target org.

**What breaks:** Wrong version may go Active in production. The user believes the right logic is now live but it is not.

**Correct pattern:** Report those details before directing the user to activate in Flow Builder UI. Never call `POST /services/data/vXX.0/flowbuilder/flow/{flowId}/actions/activate` (activateFlow) — quarantined, do not dispatch.

---

## 22. Skipping field discovery before building DML elements

Building a `recordCreates` or `recordUpdates` element with assumed field names without first verifying the object's field schema.

**What breaks:** Emitting a non-createable or non-updateable field (such as `Id` on create, or auto-managed fields like `CreatedDate`) causes save-time validation errors. Required-field violations only surface at runtime.

**Correct pattern:** Verify the object's field schema before emitting any `inputAssignments`. The current platform-family field descriptor must have `creatable: true` for creates and `editable: true` for updates. Fields with `required: true` must be included on create.

---

## 23. Re-probing the org for data already in context

Calling a schema-discovery tool with the same arguments when the result is already present in the conversation context.

**What breaks:** Wastes org API quota, burns context window tokens, and may return inconsistent data if the org schema changed mid-conversation.

**Correct pattern:** Treat prior probe results as a cache keyed on `(tool, arguments)`. Consult conversation history before making any read-only schema call. Only re-probe if the user indicates the org was modified between turns.

---

## 24. Uninitialized collection variable passed to an action

Passing a collection variable to a Loop element or collection operation without first initializing it.

**What breaks:** An unassigned (null) collection variable causes a `Missing required input parameter` runtime error — not a save-time error, so it won't be caught until the flow executes.

**Correct pattern:** Always pre-initialize collection variables (e.g., via an Assignment element that sets the variable to an empty collection or a known value) before passing them to Loop elements or any collection-aware operation.

---

## 25. Using record IDs for record type or template references

Embedding a hard-coded Record Type ID or Email Template ID as a literal value in flow metadata.

**What breaks:** Record IDs are org-specific. A flow that references an ID from sandbox will break when deployed to production because that ID does not exist in the target org. This is not caught at save time and only surfaces at runtime in the target environment.

**Correct pattern:** Use DeveloperName (not record ID) when referencing Record Types or Email Templates in flows. Look up the record by DeveloperName at runtime via a `recordLookups` element, or store DeveloperName in a flow constant that can be overridden per org.

---

## 26. Dot-notation reference to a screen InputField value

Using `{!ScreenName.fieldName}` (dot-notation) to reference the value of a screen field whose `fieldType` is `InputField` in any downstream element (`recordCreates.inputAssignments`, `decisions.rules[].conditions`, `assignments`, etc.).

**What breaks:** The platform does NOT expose `InputField` values via dot-notation. Emitting `elementReference: "ScreenName.fieldName"` or `leftValueReference: "ScreenName.fieldName"` causes a **`WARNING_BLOCK_ACTIVATION`** error at save time, blocking flow activation.

**Applies to:** All `fieldType: InputField` screen fields (Text Box, Number, Currency, Date, DateTime, Checkbox). This includes LargeTextArea and PasswordField as well — any screen field whose value is made available as a bare variable.

**Why the agent reaches for dot-notation:** The platform uses dot-notation for sObject fields (e.g., `{!myAccount.Name}`), which leads the agent to infer it also works for screen fields. It does not.

**Correct pattern:** A screen `InputField`'s value is automatically available in all downstream elements via `{!fieldApiName}`, where `fieldApiName` is the field's `name` property alone — **no screen name prefix, no dot**.

| Wrong | Correct |
|---|---|
| `elementReference: "Screen_Collect_Account_Info.varAccountName"` | `elementReference: "varAccountName"` |
| `leftValueReference: "Screen_Collect_Account_Info.varAccountName"` | `leftValueReference: "varAccountName"` |
| `{!MyScreen.myField}` in any value field | `{!myField}` |

**How to detect before saving:** Scan every `elementReference`, `leftValueReference`, `rightValueReference`, and `value.elementReference` in the flow for the pattern `ScreenElementName.fieldName`. Any match is a blocker — fix it before calling save-and-validate.

---

## 27. Retrying save-and-validate more than twice with the same error category

Making three or more save attempts that all return errors in the same category (e.g., repeated `DYNAMIC_TYPE_MAPPING_MISSING`, repeated `Unrecognized field`, repeated enum-value errors, repeated `WARNING_BLOCK_ACTIVATION` from dot-notation on screen InputField).

**What breaks:** No progress is made. Context window fills with redundant tool calls and the same error text. The user loses confidence.

**Correct pattern:** After two failed save attempts with the same error:
1. **Stop retrying.** Paste the verbatim error to the user.
2. **Pick a structurally different approach** — remove the offending field entirely, replace the component with a simpler alternative, or downgrade the feature.
3. If no alternative is obvious, **ask the user** whether the requirement is achievable or should be dropped.

Never make a third attempt with the same shape or a minor variation of the same field placement.

---

## 28. Security posture not audited before save

The flow is saved without checking its run mode, data scope, or handling of untrusted input.

**What breaks:** Nothing at save time — but the flow may bypass sharing/CRUD/FLS (`SystemModeWithoutSharing`), leak sensitive fields via "store all fields" lookups, or accept un-sanitized guest input. These are multi-tenant security exposures, not validation errors, so `POST /services/data/vXX.0/flowbuilder/flow/actions/save` (saveFlow) never catches them.

**Correct pattern:** Run the security Auditor checks in `shared/security/security.md` (the single source of truth for the specific rules) on every save and surface any findings in the Plan-phase Security note. Unlike other items in this file, security findings are **advisory** — warn, recommend the safer default, and let the user decide. Do not block the save.

---

## 29. Emitting a metadata-valid element that has no canvas palette tile

An element type that `GET /services/data/vXX.0/flowbuilder/schema/flow-capabilities` (read `.elements`) returns but that Flow Builder offers no palette tile for. The server saves it via the API, so `POST /services/data/vXX.0/flowbuilder/flow/actions/save` (saveFlow) succeeds, but the user cannot create or cleanly edit it in the canvas.

**What breaks:** The saved element renders as an orphaned node the user can't edit in the canvas — the flow becomes un-maintainable in the builder. "Supported in metadata" ≠ "authorable in the canvas."

**Correct pattern:** Only emit **palette-authorable** entries. An entry is palette-authorable when it carries a `configComponent` (an editor component); palette entries also carry `icon` / `label` / `labelNew`. **Never emit** a bare entry with `"isElementSubtype": false`, `"attributes": null`, and no `configComponent`. The known trap is the **base `Wait`** (classic Wait) — default to a Wait *subtype* (`WaitDuration` / `WaitDate` / `WaitUntilEvent`); `elements/wait/wait.md` is the single source of truth for the Wait family, including the narrow "by Criteria" (01) / record-relative-date (04) exception where a classic Wait is the only expressible shape. Apply the same `configComponent` test to any element type before drafting it.

---

## 30. Redundant Get Records + filter-based Update Records with a duplicated filter

A `recordLookups` element retrieves a collection using filter F, and a later `recordUpdates` element re-applies the **same filter F** (Mode 1 / RecordLookup) to write new field values onto the same object — instead of updating the collection the Get Records already fetched.

**What breaks:** The flow issues a second, redundant SOQL query that returns the identical record set the Get Records element already holds. At best this wastes a SOQL statement (governor-limit pressure in bulk/HDM designs) and adds a maintenance trap — the two filters can silently drift out of sync on a future edit, since nothing enforces they stay identical. A `decisions` element checking `Get_Records IsNull = false` in between (a common "records exist?" guard) reinforces the appearance that the two steps are related, but does not actually connect them: the Update still re-derives its own record set from scratch.

**Detection:** A `recordLookups` element's `object` + `filters[]` match (same object, same field/operator/value filter set, ignoring order) a later `recordUpdates` element's `object` + `filters[]` (Mode 1, `inputReference: ""`), with no other DML on that object in between that would invalidate reusing the fetched collection. The `recordLookups` element must also be **unbounded** — `getFirstRecordOnly: false` and no `limit` — so its result set is provably the same records the Mode 1 Update would touch. A Get Records with `getFirstRecordOnly: true` or a `limit` may hold only a subset of the filter's full match set (Mode 1 Update re-runs the filter with no such cap), so collapsing to Mode 2 in that case would silently narrow which records get updated. If the lookup is bounded, do not flag this anti-pattern unless there is other proof the lookup result equals the update's full target set.

**Correct pattern:** Reuse the already-fetched collection instead of re-filtering — only when the Get Records is unbounded (no `getFirstRecordOnly: true`, no `limit`):
1. Set the new field values onto the fetched records — via a `Loop` + `Assignment` (append each updated item to an output collection) or a `Transform` element, per `elements/collection-processor/collection-processor.md` / `elements/transform/transform.md`.
2. Issue a single **Mode 2** (`inputReference` = the resulting sObject collection) `recordUpdates` element — no `object`, no `filters`, no `inputAssignments`. See `elements/record-update/record-update.md` § Mode 2.
3. If the only purpose of the preceding `IsNull` Decision was to guard against updating on an empty result, drop it — a `Loop` over an empty collection, or a Mode 2 update on an empty collection, is already a no-op. Keep the Decision only if it drives a genuinely distinct business branch (e.g., an alternate path when nothing is found).

**Example transformation:**

Wrong (redundant filter):
```text
Get_Overdue_Projects: Project WHERE Status = 'In Progress' AND EndDate__c < TODAY
Decision: Get_Overdue_Projects IsNull = false
Update_Overdue_Projects (Mode 1): Project WHERE Status = 'In Progress' AND EndDate__c < TODAY
  SET Status__c = 'Overdue'
```

Correct (reuse the collection):
```text
Get_Overdue_Projects: Project WHERE Status = 'In Progress' AND EndDate__c < TODAY
Loop over Get_Overdue_Projects
  └─ Assignment: set Status__c = 'Overdue' on current item, Add to varUpdatedProjects
Update_Overdue_Projects (Mode 2): inputReference = varUpdatedProjects
```

This mirrors — and generalizes — the Mode 2 guidance in `elements/record-update/record-update.md` § Mode 2: reusing an already-fetched collection isn't limited to screen-edited Automatic Fields; it applies any time a preceding Get Records already holds the exact record set a downstream Update needs, even when the new values differ from what was read.

---

## 31. Screen with both `allowBack:false` and `allowFinish:false`

A `screens[]` element that hides both the Previous button (`allowBack: false`) and the Next/Finish button (`allowFinish: false`).

**What breaks:** Saves as a Draft, but the flow **fails activation** (the activation call → `InvalidDraft`). A dead end — the user has no way to move forward or back. See `elements/screen/examples/negative-patterns.json` `N1_both_nav_hidden`.

**Detection:** Any `screens[]` entry with the literal pair `allowBack: false` + `allowFinish: false`. Both default to `true` when omitted, so an omitted key never triggers this.

**Correct pattern:** Keep at least one of the two `true` (or omitted). `allowPause` doesn't count toward this rule. See `elements/screen/screen.md` § Navigation Button Settings and `elements/screen/examples/positive-patterns.json` P2 (Previous-only) for the valid single-button shapes.

---

## 32. Routing multiple fault paths to a shared error screen with fault-specific wording

Two or more elements' `faultConnector`s point at the same error screen in a Screen Flow, but that screen's fixed text names a cause specific to only one of the possible failures.

**What breaks:** Nothing at save or activation time — a runtime UX defect. Whenever a different fault fires, the user sees an explanation that doesn't apply to what actually happened.

**Detection:** For any error screen reachable from more than one `faultConnector`, check whether its fixed `fieldText` (apart from a generic `{!$Flow.FaultMessage}` interpolation) implies a cause specific to only one of the feeding elements.

**Correct pattern:** Share one error screen only when its message is genuinely generic (e.g. `"Something went wrong: {!$Flow.FaultMessage}"`). Give any fault needing business-specific wording its own screen — mixing a shared generic screen with dedicated specific ones on the same flow is normal. See `shared/fault-paths/fault-paths.md` § "Sharing One Error Screen Across Multiple Fault Paths". *(A shared error SCREEN is a continuing handler and stays legal; the auto-layout round-trip concern is about a shared END element — item 38, a different target type.)*

## 33. `$Record__Prior` in Start entry criteria with `doesRequireRecordChangedToMeetCriteria: true`

A record-triggered `start` (`recordTriggerType` Update / CreateAndUpdate) whose entry criteria — `filters[]` or `filterFormula` — references `$Record__Prior.*` **while** `doesRequireRecordChangedToMeetCriteria: true`.

**What breaks:** The flag makes the platform re-evaluate the entry criteria against both prior and new state, so any `$Record__Prior` reference in the Start is undefined. Blocks activation with `FORMULA_EXPRESSION_INVALID` on `$Record`: *"The formula expression is invalid: The \"$Record__Prior.<Field>\" variable isn't valid because 'When to Run the Flow for Updated Records' in the Start element changed."* Surfaces as a `warnings[]` entry with `isSuccess: true` — the flow saves as an **InvalidDraft**, so inspect `warnings`, not just `isSuccess`. Verified live.

**Detection:** A Start (`RecordBeforeSave`/`RecordAfterSave`, `recordTriggerType` Update or CreateAndUpdate) with `doesRequireRecordChangedToMeetCriteria: true` AND a `$Record__Prior` reference anywhere in `filters[]` or `filterFormula`. See `elements/start/examples/negative-priorInEntryCriteria-doesRequire.json`.

**Correct pattern:** Either set `doesRequireRecordChangedToMeetCriteria: false` (or omit it) and keep the prior-vs-new comparison in `filterFormula`/`filters`, or — **preferred** — leave entry criteria change-agnostic and do the `$Record__Prior.Field` vs `$Record.Field` comparison in a **Decision** element in the flow body, where `$Record__Prior` is always valid. See `elements/decision/decision.md`.

## 34. `faultConnector` pointing at the same target as the element's success `connector`

A fault-capable element (`recordUpdates`, `recordCreates`, `recordDeletes`, `recordLookups`, `actionCalls`, `waits`) whose `faultConnector.targetReference` equals its own `connector.targetReference`. The element has a fault path in name only — both success and failure route to the same next element.

**What breaks:** Nothing at save or activation time — a runtime correctness defect. When the operation fails, control still flows into the success continuation (a confirmation email, a "done" screen, a downstream DML). A silently failed write is reported as a success, and the rest of the flow runs on the false assumption that the operation succeeded. This is worse than a missing fault connector (item 2): the failure is not just unhandled, it is actively disguised as success.

**Detection:** For every element carrying both a `connector` and a `faultConnector`, compare `faultConnector.targetReference` against `connector.targetReference`. If they are equal, it is this anti-pattern. A fault path may still legitimately rejoin the flow — an intentional retry (a GoTo back to an earlier element, see `shared/fault-paths/fault-paths.md`) or a "log and continue" path that converges on a neutral terminal/End is fine. The defect is specifically routing the failure into a step that **assumes the operation succeeded** (the confirmation email/screen, or a downstream action that consumes the not-actually-written data) — flag that whether reached directly or through a chain, and do not flag convergence at a neutral end point. *(Layout note, `AUTO_LAYOUT_CANVAS` only, different axis from this runtime concern: a shared End across non-fault branches is valid, and a fault pointed directly at an End is silently dropped on reload — neither breaks the auto-layout round-trip. See item 38.)*

**Correct pattern:** Route the `faultConnector` to a *distinct* error-handling element that does not flow into the success continuation before completion — a `customErrors` element (record-triggered flows), a `Log_Error` action (autolaunched/scheduled flows), or a dedicated error screen (Screen Flows). See `shared/fault-paths/fault-paths.md` and `elements/record-update/record-update.md` § "Fault Connector Mandate".

## 35. Empty or separator-only item appended to a text collection

An `assignments` element that `Add`s a bare separator or empty string (e.g. `{ "stringValue": "\n" }`, `{ "stringValue": "" }`, `{ "stringValue": ", " }`) to a text collection as its own item — typically alongside a real value inside a loop, in an attempt to delimit entries.

**What breaks:** Nothing at save time — a data defect. Each iteration appends the value *and* a standalone empty/separator item, so the collection accumulates blank entries (and a trailing one after the last iteration). Downstream, that surfaces as blank lines or dangling separators in summary text, extra empty rows, or off-by-one counts.

**Detection:** In an `assignmentItems[]` targeting an `isCollection: true` text variable with operator `Add`, look for a value that is a separator/whitespace/empty `stringValue` added as its own item rather than concatenated onto the content.

**Correct pattern:** Collect only real values into the collection, then join them with a separator where the text is consumed (e.g. a text template or formula). If a running text string is genuinely needed, build it in a scalar Text variable by concatenating value **and** separator in a single expression per iteration — never add the separator as a standalone collection item.

## 36. Non-fault path targeting a fault-only error screen

An **error screen** — a terminal screen whose only content is a failure message, reached via a `faultConnector` — is *also* targeted by a non-fault connector: a success screen's `connector`, a Decision `defaultConnector`, or a Loop connector. The usual shape is a terminal success screen whose forward `connector` points at the error screen instead of ending the flow.

**What breaks:** Nothing at save or activation — the metadata is legal (a `faultConnector` target may also sit on a regular path; see `shared/fault-paths/fault-paths.md`). It's a runtime defect: a *successful* run dead-ends on the error screen, showing a failure message when nothing failed — and if that text interpolates `{!$Flow.FaultMessage}`, it renders blank, since the variable is empty off the fault path. Seen in W-23849872: `Get_All_Contacts.faultConnector → Error_Screen` (right) plus `Display_Contacts_Screen.connector → Error_Screen` (the defect), whose fixed error text showed on a successful run.

**Detection:** Find each terminal, error-message-only screen reached via a `faultConnector`. Flag it if any non-fault connector (`connector`, `defaultConnector`, `nextValueConnector`, `noMoreValuesConnector`, or a Decision rule `connector`) also targets it. A screen that instead *continues* the flow (has a forward connector) is a notify-and-continue screen, not this defect.

**Correct pattern:** Keep the error screen reachable only via fault connectors; make the last success screen terminal (omit its `connector`, or point it at a real continuation / a dedicated single-incoming End — not a shared End; item 38). See `elements/screen/screen.md` § Error/fault screen wiring and `elements/screen/examples/negative-patterns.json` N11 / `positive-patterns.json` P8.

> **Not item 32.** Sharing one error screen across several *fault* connectors is fine (item 32 only governs whether its wording fits every fault). A *non-fault* edge into it is the inverse mistake. **Not item 38** either: this item is about error *SCREENS* (a continuing handler); item 38 is about a shared *End* element.

## 37. Net-new flow saved without a `CanvasMode` process metadata value

A net-new (GENERATE) flow serialized without a `CanvasMode` entry in top-level `metadata.processMetadataValues[]` — either the array is absent, empty (`[]`), or carries other entries but not `CanvasMode`.

**What breaks:** Nothing at save time — the save succeeds and returns clean. A silent UX defect: **absence is not neutral — the builder opens a canvas-mode-less flow in Free-Form.** Canvas mode is carried **only** by this PMV. W-23938668 added a *server-side* backfill that stamps `AUTO_LAYOUT_CANVAS` on the persisted `POST /services/data/vXX.0/flowbuilder/flow/actions/save` (saveFlow) **net-new** path (`createNewFlow` / `saveAsNewDefinition`) when the caller omitted it — but that backfill does **not** cover the paths this rule targets: the no-persist Flow Builder hand-off (which returns JSON and never calls `POST /services/data/vXX.0/flowbuilder/flow/actions/save`), the other save types (`saveAsNewVersion` / `saveDraft`), and the separate `execute_metadata_action` generation pipeline. On those, the emitted PMV is the only thing that sets canvas mode. So emit it explicitly on every net-new flow and never rely on the server backfill. The PMV is what sets canvas mode; end/fault topology does not undo it — a shared End across non-fault branches is valid, and a fault pointed directly at an End is silently dropped on reload (neither breaks the auto-layout round-trip); see item 38.

**Detection (GENERATE only):** On a net-new save, confirm `metadata.processMetadataValues[]` is non-empty and contains an entry `{ "name": "CanvasMode", "value": { "stringValue": "AUTO_LAYOUT_CANVAS" } }`. This is a hard gate — emit it independently of `BuilderType` (the two are separate PMVs; never condition emitting one on the other). **Exception — non-canvas process types:** do NOT emit a `CanvasMode` PMV for a process type that has no canvas (e.g. `CustomerLifecycle`) — the server rejects the save with `CLM_UNSUPPORTED_PROCESS_MD_VALUE`. The gate applies only to canvas-based flow types.

**Correct pattern:** For a net-new flow emit the `CanvasMode` PMV explicitly (default `AUTO_LAYOUT_CANVAS`). **EVOLVE never applies here:** on an edit, preserve the source's `processMetadataValues` **verbatim** — never inject, overwrite, or flip a canvas mode the source didn't carry. Stamping `AUTO_LAYOUT_CANVAS` onto an existing Free-Form flow silently re-lays-out (and can corrupt) it; canvas mode is the user's to change, never the agent's. Any hand-off surface that emits flow JSON without calling `POST /services/data/vXX.0/flowbuilder/flow/actions/save` (saveFlow) (e.g. the Flow Builder surface's no-persist output contract) carries the same obligation — the PMV must be present in the JSON handed back. See `shared/flow-properties/flow-properties.md` § "Canvas Mode and `processMetadataValues`".

## 38. Pointing a fault at an End (silently dropped), and the myth that a shared End breaks auto-layout

**Applies to auto-layout flows** (`CanvasMode: AUTO_LAYOUT_CANVAS`; a flow with the PMV absent opens Free-Form — item 37 — and is exempt). Two shapes this item once prohibited are, in **current** Flow Builder, **not** round-trip breakers. Do not reshape a valid flow to satisfy the old rule, and do not flag either shape.

**1. A shared End is valid.** Two or more **non-fault** connectors converging on ONE explicit End (a single `ends[]` entry targeted N times) is a legal, Flow-Builder-native auto-layout shape — e.g. a Decision's default outcome and another outcome both terminating at one End. Flow Builder authors it and re-opens it in clean auto-layout. (Verified: `a_new_flow_to_test` — `Decision_2`'s `defaultConnector` and `Outcome_2` both target `END_ELEMENT_2`, and it round-trips into ALC cleanly.) One dedicated End per branch is equally valid. Neither form is mandated — never "split" a shared End, and never flag one as a defect.

**2. A fault targeting an End is silently dropped, not fatal.** A `faultConnector` whose direct target is an End — or an empty/unwired fault — is simply **removed on reload**; the flow stays `AUTO_LAYOUT_CANVAS` and does **not** fall back to Free-Form. (Verified current behavior: a flow whose `faultConnector` targets an `END_ELEMENT` directly round-trips with that fault removed and the flow still `AUTO_LAYOUT_CANVAS` — the direct fault→End case, captured explicitly; separately, `a_new_flow_to_test` opens cleanly with fault chains and five Ends, and an empty fault renders as a stub and drops on the next save.) A fault path may also validly **terminate at an End** through a handler. *(This corrects an earlier claim in this skill that a fault-into-End forces a Free-Form fallback via `compareState`, citing `@W-8249637`; that is not the observed current behavior — the fault is dropped, the flow stays auto-layout.)*

**The real (advisory) concern — silent loss.** Because an End-targeting or empty fault is dropped on reload, that error path vanishes with no error. If you want faults actually handled, route each `faultConnector` to a real handler element (a `Log_Error`/`Handle_Fault` Assignment, `customErrors` in a record-triggered flow, or an error screen) that then reaches its own End. This is a recommendation for observability, **not** a round-trip requirement. The orthogonal *runtime* defect — a fault rejoining a continuation that assumes the failed operation succeeded — is real and lives in **item 34**; keep that separation.

**Correct pattern:** On GENERATE with `AUTO_LAYOUT_CANVAS` at resolved `apiVersion` ≥ 68.0, every terminating branch reaches an explicit End (its connector + a matching `ends[]` entry, co-emitted) — this includes loop `noMoreValuesConnector` and `nextValueConnector` termini and Decision `defaultConnector`/outcome termini, which are easy to miss. Branches may each get their own End OR converge on a shared End; both are valid. Below 68.0 and on any Free-Form flow, omit the connector instead and never emit `ends[]` on Free-Form. Route faults to a handler when you want them kept.

**EVOLVE note:** preserve the source's `ends[]`; give each NEW terminating branch an explicit End (auto-layout sources only) — you may converge it on an existing End or give it its own, both valid. Never add ends to a retrieved Free-Form source.

See `shared/end/end.md`, `shared/connector/connector.md` § End topology, `shared/fault-paths/fault-paths.md`, and item 34.

---

## 39. Echoing a server read-back-only form on save (schedule and resume time/date fields)

A retrieved flow hands certain time/date fields back in a **read-back** shape that
`POST /services/data/vXX.0/flowbuilder/flow/actions/save` (saveFlow) does not accept: `Start.schedule.startTime` / `Start.schedule.endTime`
(Scheduled trigger) and `Wait` element `resumeTime` come back as
`{ "timeInMillis": N }` objects; `Start.schedule.startDate` / `Start.schedule.endDate`
and `resumeDate` come back as bare **epoch-millis integers** (all three dates are the
same `xsd:date` type, serialized as a numeric timestamp). The
agent echoes those retrieved objects/integers straight back on save instead of
converting them to the wire-string form `POST /services/data/vXX.0/flowbuilder/flow/actions/save` (saveFlow) requires.

**What breaks:** The save_flow call is rejected. For the Wait element's
`resumeTime`/`resumeDate`, the observed rejection is
`No suitable constructor found for type [...] com.sforce.ws.types.Time: can not
instantiate from JSON object` (see `elements/wait/wait.md`). For the Start
element's `schedule.startTime`/`schedule.endTime`/`schedule.startDate`/`schedule.endDate`,
the observed save_flow rejection is `ILLEGAL_QUERY_PARAMETER_VALUE` — do not treat
either string as the universal error for this class; report whichever
`validationErrors[]` text the server actually returns.

**Detection:** Scan the materialized payload for `schedule.startTime`,
`schedule.endTime`, `resumeTime` that are `{ "timeInMillis": ... }` objects rather
than time strings, and `schedule.startDate`, `schedule.endDate`, `resumeDate` that
are numbers rather than `"YYYY-MM-DD"` date strings.

**Correct pattern:** Convert every read-back form to its `POST /services/data/vXX.0/flowbuilder/flow/actions/save` (saveFlow) wire string
before saving. The time literal is a GMT wall-clock value; the server's canonical
serialized form carries a trailing `Z` (e.g. `"09:00:00.000Z"`) and the save
deserializer accepts it **with or without** the `Z`, so either `"09:00:00.000"` or
`"09:00:00.000Z"` saves cleanly.
- Time: `{ "timeInMillis": 32400000 }` → `"09:00:00.000"`; `{ "timeInMillis": 0 }` → `"00:00:00.000"`. `timeInMillis` is milliseconds past GMT midnight, so `32400000` = 9h → `"09:00:00.000"`.
- Date: reduce to the date-only string `"YYYY-MM-DD"`. **Render the epoch-millis instant with a UTC/GMT renderer — never local-time date formatting.** The dates the server hands back are midnight-UTC boundaries, so rendering the instant in any negative-UTC-offset local zone (e.g. US Pacific, UTC−7/−8) rolls the calendar day *back by one* — and because any valid `"YYYY-MM-DD"` saves, the wrong date is accepted **silently, with no error** (the flow then runs a day early, indefinitely). Compute the day in UTC — `floor(epochMillis / 86400000)` days past 1970-01-01, then format that — or if you use a date library, pass it an explicit UTC/GMT timezone. Do **not** feed the millis to a local `Date` / `toLocaleDateString` / `strftime`-without-`tz` and read the date off that.
  - **Worked midnight-boundary example:** `1773532800000` is exactly `2026-03-15T00:00:00.000Z`. Rendered in UTC → `"2026-03-15"` (**correct**). The identical instant rendered in US Pacific is `2026-03-14T17:00` → `"2026-03-14"` (**wrong — off by one, and saved silently**). Likewise `1775001600000` = `2026-04-01T00:00:00.000Z` → `"2026-04-01"` in UTC, but `"2026-03-31"` in Pacific. Always take the **UTC** calendar day.
  - **Defensive fallback:** these fields serialize as epoch-millis integers on the retrieve path, so the numeric case above is what you will actually see. If a build ever hands back a full datetime string instead, **normalize it to UTC first, then take the `YYYY-MM-DD`** — do **not** slice the leading component of a non-`Z`/`+0000` string verbatim. Example: `"2026-03-14T17:00:00.000-0700"` is the instant `2026-03-15T00:00:00Z`, so the correct date is `"2026-03-15"`, but a verbatim leading slice yields the wrong `"2026-03-14"` (a day early, saved silently).

This is the same read-back-echo failure class documented for the Wait
element's `resumeTime`/`resumeDate` (`elements/wait/wait.md`, and its sibling
`maxBatchSize` read-back caveat) and for the Start element's Scheduled-trigger
fields (`elements/start/start.md` § "Scheduled (Time-Based)"). It is also the
closest sibling to the strip-list in `shared/flow-metadata-schema.md` § "What Must
Never Be Emitted" — that list removes server-only fields outright, whereas this
one transforms a preserved field's shape before re-emitting it. Per
`recipes/author/author.md`'s EVOLVE surgical rule, this normalization is applied
to every affected element, touched or not, and is exempt from byte-for-byte
preservation.

---

## 40. Referencing a field that `GET /services/data/vXX.0/flowbuilder/platform/entity/{apiName}/fields` did not return

Emitting flow metadata that names a field which was not in the response of
`GET /services/data/vXX.0/flowbuilder/platform/entity/{apiName}/fields` for the target sObject — even a well-known standard
field like `DoNotCall`, `HasOptedOutOfFax`, or `HasOptedOutOfEmail`.

**What breaks:** `GET /services/data/vXX.0/flowbuilder/platform/entity/{apiName}/fields` is FLS-filtered by the MCP session's
authenticated Salesforce user. The tool returning field X and the running
user having FLS-read on X are the same event. If the field is absent, the
running user cannot read it — meaning either (a) it does not exist on this
org, or (b) FLS blocks it. Manufacturing knowledge of the field violates the
design invariant that *the skill should only know about fields that the user
would know* — a design-time describe that hides a field from the flow admin
in the UI must hide it from the skill too. Downstream: `sf project deploy
start` run as the same user fails the flow's field-existence check against
the metadata, and even a successful deploy produces a flow whose behavior
the user cannot audit or manage in Flow Builder (the field is invisible to
them in the UI too). Note: save-time validation is not guaranteed to enforce
user FLS on every field reference — do not treat the possibility of
save-time catch as a safety net. The blind spot is a design-time contract.

**Detection:** For each sObject the design references, hold the set of
`apiName` strings returned by the most recent `GET /services/data/vXX.0/flowbuilder/platform/entity/{apiName}/fields` call
for that sObject. Then walk every field-name-carrying position in the
emitted metadata and require every value to be in that set:
- `decisions[].rules[].conditions[].leftValueReference` — extract the field
  name after any `$Record.` / `<sObjectVar>.` prefix.
- `recordLookups[].filters[].field` and `recordLookups[].queriedFields[]`.
- `recordLookups[].sortField` and `recordLookups[].outputAssignments[].field`.
- `recordCreates[].inputAssignments[].field` and `recordCreates[].outputAssignmentFieldReference`.
- `recordUpdates[].filters[].field` and `recordUpdates[].inputAssignments[].field`.
- `recordDeletes[].filters[].field`.
- `assignments[].assignmentItems[].assignToReference` when it resolves to
  a field on an sObject variable.
- Any formula in `formulas[].expression` or `<element>.filterFormula` that
  resolves a field via `$Record.<Field>` or `<sObjectVar>.<Field>`.
Any name not in the describe's field set — do not save.

**Correct pattern:** Treat the describe response as the complete and only
field inventory. When the user's requested behavior needs a field the skill
did not receive from `GET /services/data/vXX.0/flowbuilder/platform/entity/{apiName}/fields`, branch **before** the plan
gate and present the two acceptable outcomes:

1. **Build without the missing field.** State the field is inaccessible:
   *"I don't have access to a field named `DoNotCall` on Lead. This could
   mean the field doesn't exist on your org, or your Salesforce admin has
   restricted access to it via field-level security."* Enumerate the
   accessible fields that could substitute (or say none exist). Ask the
   user whether to proceed with the reduced flow.

   **Rank the substitutes by how close they are to real data.** This also
   applies when the user names a concept rather than a field (for example
   "engaged" or "high-value") and no field matches it.
   - **Look past the triggering object first.** Before listing
     substitutes, check the related objects you can reach. For an audience
     flow that means the data graph's related DMOs
     (`elements/start/audience-common.md` § "Set the data graph"). For a
     record flow it means objects reached through lookups. Include
     engagement and calculated-insight fields. Also check records the flow
     already reads or updates, and their lookups (for example the related
     Contact and its Account).
   - **Lead with the closest real data.** For example, an engagement date
     or score for "engaged", or an order amount or annual revenue for
     "high-value".
   - **Never lead with a test-looking field.** A field whose name or label
     suggests test or sample data (for example it contains Test, Sample,
     Dummy or Placeholder) is never option 1 and never the "simplest"
     option. If you list it at all, put it last and label it as looking
     like test data. This covers examples in an open question too.
   - Ranking doesn't replace the question. Still stop and ask before
     building.

2. **Halt and refer to the admin.** If no substitute works or the user
   confirms the reduced flow is not acceptable, stop before any save call.
   Instruct the user to contact their Salesforce administrator to grant
   field-level security on the field, or to re-authenticate the MCP
   session as a user with access. Do not proceed on any override phrase.

Never author metadata that names a field the skill cannot see. See
`recipes/author/author.md` Phase 2 § Probe schema for the design-time gate
that invokes this branch, and `shared/server-functions.md` §
`GET /services/data/vXX.0/flowbuilder/platform/entity/{apiName}/fields` for the tool-level caveat.

---

## MCP/Connect Lifecycle Security Invariants

**T-1. Presenting activation as something the agent performs**

W-23666862 security-quarantines `POST /services/data/vXX.0/flowbuilder/flow/{flowId}/actions/activate` (activateFlow) on every MCP/Connect surface and environment. MCP hides it from `tools/list`; direct Connect returns 404 through `FlowBuilderDisabled`. Never treat activation as a WRITE the agent can perform or imply that a saved flow is live.

**What breaks:** The call cannot succeed through the server, so any "activated" claim is false. Worse, if the skill leads the user to believe the agent activated the right version, the user trusts a state that never changed (and, were the tool ever re-enabled, could go live on the wrong version).

**Correct pattern:** The agent never activates. After a successful `POST /services/data/vXX.0/flowbuilder/flow/actions/save` (saveFlow), hand off to the user: append the "Open in Salesforce" deep link (`preview-renderer.md`) and tell them to review and activate the version themselves in Flow Builder / Setup. The version-confirmation discipline (flow full name, version number, `lastModifiedBy`, `lastModifiedDate`, org host) now belongs to that hand-off message so the user activates the right version. See `server-functions.md` Phase 4c.

---

**T-2. Treating activation approval or deactivation as activation fallbacks**

Do not call `POST /services/data/vXX.0/flowbuilder/flow/{flowId}/actions/submit-for-activation` (submitFlowForActivation) or `POST /services/data/vXX.0/flowbuilder/flow/{flowId}/actions/deactivate` (deactivateFlow) as activation
fallbacks. `POST /services/data/vXX.0/flowbuilder/flow/{flowId}/actions/submit-for-activation` targets an
Orchestration activation-approval process; `POST /services/data/vXX.0/flowbuilder/flow/{flowId}/actions/deactivate` turns an Active
flow off. Neither activates a Draft.

**What breaks:** The agent converts a known endpoint-level restriction into a
false diagnosis about the flow's process type, ID form, or Segment activation
wiring, then calls unrelated state-changing endpoints.

**Correct pattern:** Do not call `POST /services/data/vXX.0/flowbuilder/flow/{flowId}/actions/activate` (activateFlow). If direct Connect returns 404,
treat it as the expected `FlowBuilderDisabled` behavior. Stop and hand the user
the Flow Builder deep link. Do not probe alternate lifecycle mutations.

---

**T-3. Calling `POST /services/data/vXX.0/flowbuilder/flow/{flowId}/actions/deactivate` without the two-confirm gate**

`POST /services/data/vXX.0/flowbuilder/flow/{flowId}/actions/deactivate` (deactivateFlow) STOPS A PRODUCTION AUTOMATION. Highest-risk action.

**What breaks:** Business-critical automation halts. Customer-facing side effects (e.g. closed-won opps no longer create renewals).

**Correct pattern:**
1. First confirm: "I'm about to deactivate `<flow>` version `<N>` in org `<host>`. The current Active version is `<N>`, last modified by `<user>` on `<date>`. Confirm?"
2. Then ask about `cancelOnDeactivate`: "Should I also cancel any paused interviews on this flow? (yes/no)"
3. Second confirm: "Confirming deactivation of `<flow>` v`<N>` in `<host>`, cancelOnDeactivate=`<bool>`. Proceed?"
4. Only then call `dispatch(method: "POST", url: "/services/data/vXX.0/flowbuilder/flow/{flowId}/actions/deactivate")`.

---

**T-4. Skipping schema/feasibility probing in Phase 2**

The agent reads the user's request and immediately drafts the flow without calling any read-only tool to verify the user's assertions against org state.

**What breaks:** The plan rests on assumptions instead of verified facts. The first `POST /services/data/vXX.0/flowbuilder/flow/actions/save` (saveFlow) call returns `errors[]` or `warnings[]` for things a probe would have caught (read-only field, non-existent action, unsupported element type for the trigger). Rework that a Phase 2 probe would have prevented gets thrown away.

**Correct pattern:** Every concrete user assertion gets a targeted probe call in Phase 2 step 4, verified per the "Verify each assertion" traps and the **Mandatory Probes by Element Type** table. Surface any failed assertion as Architecture Pushback in the plan summary before the approval gate. See `recipes/author/author.md` Phase 2.

---

**T-5. Skipping the tool-result cache**

Later in Phase 2 (or in a follow-up EVOLVE), the agent re-calls an MCP tool it already called with the same arguments.

**What breaks:** Wastes MCP tool call budget and context window tokens, and may return DIFFERENT data if the org schema changed mid-conversation (rare but real failure mode in sandboxes with active developers).

**Correct pattern:** Conversation history is the cache. Before any read-only MCP tool call, check whether the same `(tool, args)` already exists in history and reuse the result. See `recipes/author/author.md` Phase 2 step 4 (cache-first probing).

**Cache discipline summary:** Cache key = `(tool, args)`. Five tiers: Tier 0 (just-call, cheap probes like `get_process_types`), Tier 1 (session-immutable — reuse forever), Tier 2 (flow-scoped — reuse within this flow), Tier 3 (query-scoped — distinct args = distinct entry, never duplicate), Tier 4 (volatile — always re-fetch). After any WRITE tool, treat version/metadata tool results as stale. When the user reports external changes ("I added a field"), invalidate matching cache entries.
