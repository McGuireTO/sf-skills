---
name: flow-element-subflow
license: LICENSE.txt has complete terms
description: "Use this skill when creating, editing, or troubleshooting a Subflow element — calling one flow from inside another flow. TRIGGER when: user asks to call a subflow, nest flows, pass variables to a child flow, configure a Subflow element, or use output from a called flow. DO NOT TRIGGER when the user needs to call an Apex action or external service (use flow-element-action-call instead)."
metadata:
  version: "1.0"
  related-skills: flow-resource-variable, flow-element-action-call, flow-anti-patterns, flow-fault-paths
---

# Subflow Element

## Reference File Index

| File | Purpose |
|---|---|
| `examples/simple-call.json` | Fire-and-forget subflow with no inputs or outputs |
| `examples/auto-output.json` | Mode A — automatic output (`storeOutputAutomatically: true`) |
| `examples/manual-output.json` | Mode B — output-only (no inputs, manual output assignments) |
| `examples/with-inputs-outputs.json` | Mode B — typed inputs and manual output assignments |
| `examples/terminal-call.json` | Terminal subflow with no connector — omit connector when no downstream elements follow |
| `examples/collection-passing.json` | Bulk-safe pattern: accumulate in loop, call subflow once outside |

## Overview
Subflow elements live in `metadata.subflows[]` — NOT `actionCalls[]`. Use `flowName` — NOT `actionName`. No fault path: `faultConnector` on a `subflows[]` entry is invalid and causes a save-time schema rejection.

## When to Use

Emit a `subflows[]` entry when the user needs to call one flow from within another and route control through it — optionally passing typed inputs and receiving typed outputs. Confirm the calling flow's `(processType, triggerType)` supports subflows via `GET /services/data/vXX.0/flowbuilder/schema/flow-capabilities` (read `.elements`) before placing the element.

## When NOT to Use

| Situation | Reason |
|-----------|--------|
| Child is a Record-Triggered Flow | Cannot be invoked imperatively → save error: `Subflow '<flowName>' not found` |
| Need to catch errors at the call site | No `faultConnector` on subflow entries; exceptions propagate as unhandled to the parent |
| Calling Apex or external service | Use `flow-element-action-call` |
| Calling flow's `(processType, triggerType)` doesn't support subflows | `GET /services/data/vXX.0/flowbuilder/flow/subflows` returns empty; save will reject |

> **`WARNING_BLOCK_ACTIVATION` on a helper-only flow is expected — but only for flows intentionally designed to have no Start trigger.** A helper AutoLaunchedFlow called exclusively as a subflow has no Start element by design; this warning is non-blocking. Do NOT suppress or ignore `WARNING_BLOCK_ACTIVATION` on any other flow type — it indicates a genuine disconnection bug. Do NOT add a Start element to a helper-only flow; doing so converts it to a triggered flow.

---

## Required Properties

| Property | Field | Constraints |
|----------|-------|-------------|
| Label | `label` | Max 255 chars |
| API Name | `name` | Unique dev-name; alphanumeric+underscore; max 80; no leading digit |
| Referenced Flow | `flowName` | Must be a flow whose `processType` is compatible with the calling flow (typically AutoLaunchedFlow or Screen Flow). Record-Triggered → save error. An On-Demand Flow (`triggerType: OnDemandNoTrigger`) can't be a subflow: save fails with `A Subflow element can’t reference a schedule-triggered flow or a record-triggered flow that runs before the record is saved.` Must not be the calling flow itself |

## Optional Properties

| Property | Field | Default | Notes |
|----------|-------|---------|-------|
| Input Assignments | `inputAssignments` | `[]` | Values into child flow's `isInput: true` variables |
| Output Assignments | `outputAssignments` | `[]` | Manual mode; mutually exclusive with automatic |
| Auto Output | `storeOutputAutomatically` | `true` | `true` = auto-resource; `false` = explicit `outputAssignments` |
| Connector | `connector` | — | `targetReference` must resolve to a valid element dev-name; omit if terminal |
| Description | `description` | `""` | |

---

## Input Assignments

Empty rows stripped before saving. Type-checked at save — mismatch → `Input '<name>' on subflow '<flowName>' has wrong type`. Use `elementReference` (not `{!var}` merge syntax) for variable refs. See `../../shared/value-rules.md`.

---

## Output Assignments

Pick one mode — never combine (see `../../shared/anti-patterns.md` § "`storeOutputAutomatically: true` with non-empty output assignments"):

**Mode A (automatic):** `storeOutputAutomatically: true` + `outputAssignments: []`. Reference outputs downstream via `"elementReference": "ElementName.OutputVar"`.

**Mode B (manual):** `storeOutputAutomatically: false` + explicit `outputAssignments[{ name, assignToReference }]`. Collection outputs require `isCollection: true` target variable.

---

## Version Warning Codes

When the referenced flow has both an active and a draft version, variable mismatches produce:

| Code | Meaning |
|------|---------|
| `NOT_AVAILABLE` | Variable gone from both active and draft versions — delete or remap assignment |
| `DATA_TYPE_CHANGED` | Type or `isCollection` changed between versions |
| `ONLY_AVAILABLE_IN_LATEST` | Exists only in draft — won't work in production until activated |
| `ONLY_AVAILABLE_IN_ACTIVE` | Exists only in active — will break when draft is activated |
| `DUPLICATE` | Same variable assigned twice — remove duplicates |

> The referenced flow must be Active before the calling flow is activated. Both activations are user actions in Flow Builder — `POST /services/data/vXX.0/flowbuilder/flow/{flowId}/actions/activate` (activateFlow) is DISABLED (DO NOT DISPATCH — quarantined; see `shared/server-functions.md` Phase 4c), so prompt the user to activate the referenced flow first, then the calling flow.

---

## No Fault Path

`faultConnector` on a `subflows[]` entry → save-time schema rejection. Exceptions propagate to the parent as unhandled errors. Add fault handling inside the child flow. See `../../shared/fault-paths/fault-paths.md`.

---

## Anti-Patterns

| Anti-Pattern | Consequence | See |
|---|---|---|
| Subflow inside a Loop body | Governor limits at N ≥ 200 — accumulate collection, call once outside loop | `examples/collection-passing.json` |
| `actionCalls[]` with `actionType: "flow"` | Save error — use `subflows[]` + `flowName` | `[[flow.shared.anti-patterns]]` §5 |
| `faultConnector` on a subflow entry | Schema rejection | `[[flow.shared.anti-patterns]]` §2; `[[flow-fault-paths]]` |
| Both `storeOutputAutomatically: true` and non-empty `outputAssignments` | Save error | `[[flow.shared.anti-patterns]]` §12 |
| Recursive subflow (circular call chain) | Save error: `"Recursive subflows detected"` | Extract shared logic into a non-calling helper |
| Uninitialized collection input | Empty collection or runtime error | Initialize with Assignment (`operator: Add`) before passing |
| GUID in `targetReference` or `assignToReference` | Runtime errors — use dev-names only | `[[flow.shared.anti-patterns]]` §11 |
| Stale output assignments after version upgrade | Runtime type mismatch | Re-verify `outputAssignments[].name` after changing `flowName` or activating new version |

---

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `Subflow '<flowName>' not found` | Incompatible processType, deleted, renamed, or no access | Verify called flow's processType is compatible with the calling flow |
| `Input '<name>' on subflow '<flowName>' has wrong type` | Value type mismatch | Match to declared `dataType` |
| `Cannot specify outputAssignments when storeOutputAutomatically is true` | Both modes active | Set `outputAssignments: []` or switch to manual |
| `Recursive subflows detected` | Circular call chain | Extract into a non-circular helper |
| Schema rejection | `faultConnector` emitted on subflow entry | Remove it |

---

## Metadata Shape

**Never emit on `subflows[]` entries:** `faultConnector`, `maxConnections`, `maxOccurs`, `actionType`, `actionName`, `variableAndFieldMapping`, GUIDs in `name`/`targetReference`.

| Field | Type | Req | Notes |
|-------|------|-----|-------|
| `name` | string | yes | Dev-name; max 80; alphanumeric+underscore; no leading digit |
| `label` | string | yes | Max 255 |
| `description` | string | no | |
| `locationX/Y` | number | yes | `0` for auto-layout |
| `flowName` | string | yes | API name of a compatible flow (AutoLaunchedFlow or Screen Flow) — NOT `actionName`. Not an On-Demand Flow (`OnDemandNoTrigger`): save fails |
| `inputAssignments` | array | yes | `[]` if none |
| `outputAssignments` | array | yes | `[]` if auto mode |
| `storeOutputAutomatically` | boolean | no | `true`/`false`; emit `false` + manual `outputAssignments` when unsupported |
| `connector` | Connector | no | `{ targetReference, isGoTo }`; omit if subflow is terminal |

---

## MCP Tools

| Tool | Purpose |
|---|---|
| `GET /services/data/vXX.0/flowbuilder/flow/subflows` | Returns callable autolaunched flows. Server-side filtered by the current `(processType, triggerType)` — the Core tool exposes optional `subflowFilterType`, `dataSpace`, `namePattern`, and `flowDefinitionId` params. Call it with no filter to get the full callable set as a fallback when a filtered call returns empty. (Core collapsed the former separate filtered/all subflow tools into this single operation.) |
| `GET /services/data/vXX.0/flowbuilder/resource/flow-input-output-variables` | Call with `flowName`. Returns `versions[]` — one entry per relevant version (active + latest), which can declare **different** variables. Select the entry with `isActiveVersion: true` (don't index `versions[0]`), then filter its `variables[]` by `isOutput`/`isInput` to get the declared input/output variable definitions. |
| `GET /services/data/vXX.0/flowbuilder/schema/flow-capabilities` (read `.elements`) | Confirm `subflows` is in the allowed element list for the calling flow's `(processType, triggerType)` before placing |
