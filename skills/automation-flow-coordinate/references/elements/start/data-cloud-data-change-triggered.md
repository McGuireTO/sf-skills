---
name: flow-element-start-data-cloud-data-change-triggered
license: LICENSE.txt has complete terms
description: "Load when building a Data Cloud-Triggered flow — triggerType `DataCloudDataChange`, processType `AutoLaunchedFlow` — that FIRES when a single Data Cloud DMO record is created or updated. Covers discovering the DMO at runtime (`flowbuilder_get_data_cloud_entities` + entity fields), the start-element shape (`object` = DMO API name, `recordTriggerType`), referencing the changed record via `$Record.<dmoField>` in a downstream Decision, the rule that Create/Update/Delete elements must target a writable SObject (never a DMO), and the hard line vs a data-graph trigger (`DataGraphDataChange`), vs core-SObject record triggers (`RecordAfterSave`/`RecordBeforeSave`/`RecordBeforeDelete`), vs an engagement `AutomationEvent`. DO NOT load for any other trigger type."
metadata:
  version: "1.0"
  related-skills: flow-element-start, flow-flow-properties
---

# Data Cloud-Triggered (Single DMO Record Change)

Load this when `triggerType` is `DataCloudDataChange`. It is the complete build guide for the Data Cloud-triggered start element; the base `start.md` carries only the routing stub.

The whole flow FIRES when a **single Data Cloud Data Model Object (DMO) record** is created or updated — the changed DMO record is exposed to the flow body as `$Record`. This is a record-change trigger on **one** DMO, not on a data graph (multiple related objects) and not on a core CRM SObject.

- **triggerType**: `DataCloudDataChange`. Author **`processType: "AutoLaunchedFlow"`** (headless). Do not substitute a core record trigger based on the word "record" in the prompt.
- The DMO is chosen ON the start element via **`object`** — set to the DMO's bare API name (a `ssot__*__dlm` / `*__dlm` developer name), the same field a core record trigger uses for its SObject.
- Supports **`recordTriggerType`** `Create`, `CreateAndUpdate`, or `Update` — there is **no `Delete`** for this trigger (unlike a core `RecordBeforeDelete`).
- Requires a **Data Cloud-provisioned org** and **API version 59.0+**: the `DataCloudDataChange` trigger and DMOs do not exist on a plain org. If the trigger type is not offered, or no DMO matches the user's intent, STOP and tell the user the org is not Data Cloud-provisioned — do NOT fall back to a core record trigger or an engagement event.

## Discover the DMO — don't hard-code it

The DMO name is org-specific; treat discovery as the source of truth. Do not guess a `ssot__*__dlm` name.

1. **List the org's Data Cloud DMOs.** Call the salesforce-flow tool **`flowbuilder_get_data_cloud_entities`** to enumerate the Data Cloud DLM/DMO entities the org exposes (with their capabilities). Match the user's intent (the object whose change should fire the flow) to a row and take its **exact API name** (e.g. `ssot__Opportunity__dlm`). If nothing matches, STOP (see the provisioning note above) — do not substitute a core SObject.
2. **Set the trigger identity from it.** Put that exact DMO API name in **`start.object`** and set **`recordTriggerType`** (`Create`, `CreateAndUpdate`, or `Update`) from the user's intent.
3. **Learn the DMO's fields** for `$Record.<field>` references and any entry filters: `dispatch_readonly(method: "GET", url: "/flowbuilder/platform/entity/<the DMO API name>/fields")`. Reference only fields this returns — a field valid on a core SObject may not exist on the DMO.

> **Capabilities probe won't list these fields.** The `DataCloudDataChange` start-field shape (`object` + `recordTriggerType` on a DMO) is not advertised by a flow-capabilities / metadata-describe probe — it only surfaces on validation. Build the start from this guide; do NOT conclude the trigger is unsupported just because a capabilities call doesn't enumerate it.

## Do NOT confuse with three look-alikes

| The user wants… | Use | Where / how the object is set |
|---|---|---|
| the flow to **FIRE when a single Data Cloud DMO record** is created/updated | **`DataCloudDataChange`** start (this guide) | `object` = the **DMO** API name (`ssot__*__dlm`) on the **start** |
| the flow to fire on a **multi-object DATA GRAPH** change | **`DataGraphDataChange`** — NOT this guide (see "Out of scope" below); it is org-gated | `triggeringDataGraph` + `triggeringDataModelObjectPath` on the start |
| the flow to fire on a **core CRM SObject** create/update/delete (Account, Opportunity, Contact, custom `__c`) | `RecordAfterSave` / `RecordBeforeSave` / `RecordBeforeDelete` — see `start.md` | `object` = the **SObject** API name (never a `__dlm` DMO) |
| the flow to fire on an **email-engagement event** (open / link click / bounce / response) | `AutomationEvent` — see `automation-event-triggered.md` | `eventName` / `eventType` on the start |

A DMO API name ends in `__dlm`; a core SObject does not. If the target ends in `__dlm`, this is `DataCloudDataChange` (single DMO) or `DataGraphDataChange` (a data graph) — never a core record trigger.

## Start element shape

| Field | Value |
|---|---|
| `triggerType` | `"DataCloudDataChange"` |
| `object` | the triggering DMO's API name — from discovery (e.g. `"ssot__Opportunity__dlm"`) |
| `recordTriggerType` | `"Create"`, `"CreateAndUpdate"`, or `"Update"` (no `Delete`) |
| `filters` / `filterLogic` | optional entry criteria on the DMO's fields; omit `filterLogic` when `filters: []` (the no_conditions omission rule — see `start.md`) |
| `doesRequireRecordChangedToMeetCriteria` | optional; only valid for `Update` / `CreateAndUpdate` |
| `processType` (flow root) | `"AutoLaunchedFlow"` |

```json
"start": {
  "locationX": 0, "locationY": 0,
  "triggerType": "DataCloudDataChange",
  "object": "ssot__Opportunity__dlm",
  "recordTriggerType": "Create",
  "filters": [],
  "doesRequireRecordChangedToMeetCriteria": false,
  "connector": { "targetReference": "<first element>", "isGoTo": false }
}
```

*Note: the DMO name above is illustrative — use the exact API name `flowbuilder_get_data_cloud_entities` returns for the org.* A verified reference build saved AND validated cleanly (no `InvalidDraft`) with just `object` + `recordTriggerType` + empty `filters`; no flow-level `dataSpace` was required to save or validate this single-DMO trigger.

Do **NOT** emit `triggeringDataGraph` or `triggeringDataModelObjectPath` on a `DataCloudDataChange` start — those fields belong to `DataGraphDataChange` only (see "Out of scope").

## `$Record` — the triggering DMO record

- `$Record` = the changed DMO record; it is **read-only**.
- Reference the changed record's fields as **`$Record.<dmoField>`** (e.g. `$Record.ssot__TotalAmount__c`) — use only field API names returned by the entity-fields describe in discovery.
- The "decide on the triggering record's data" pattern is a body **Decision** whose conditions read `$Record.<dmoField>`. Do the criteria evaluation in the body; the start's optional entry `filters[]` narrow which DMO changes enter the flow at all (literal typed values only, same restrictions as a record-triggered start — see `start.md` / [[flow.shared.record-filter]]).

## Write targets — DMOs are read/trigger-only

Data Cloud DMOs are **read/trigger-only**: their fields are not creatable, and a DMO is never a valid write target. A `Create Records` / `Update Records` / `Delete Records` element in this flow MUST target a normal **writable SObject** (e.g. `Task`, `Case`, a custom `__c`), never a `__dlm` DMO.

Canonical pattern for this flow type:

> DMO record change (`DataCloudDataChange` start) → read `$Record.<dmoField>` → Decision on criteria → **Create Records on a writable CRM SObject** (e.g. a `Task`) populated from `$Record` fields.

## Special treatment — what discovery does NOT tell you

- **Version floor (functional prerequisite):** `DataCloudDataChange` requires **API version 59.0+**. Below that floor the trigger is unavailable — check the flow's API version.
- **No `Delete`:** `recordTriggerType` is `Create` / `CreateAndUpdate` / `Update` only. There is no before/after-delete flavor for this trigger.
- **No data-graph fields:** `triggeringDataGraph` / `triggeringDataModelObjectPath` are `DataGraphDataChange`-only — emitting them here is wrong.
- **`dataSpace` is not required to save/validate** the single-DMO trigger (unlike Segment / Automation Event flows). If a specific target org blocks **activation** with `DATA_SPACE_REQUIRED_FOR_FLOW_TYPE`, resolve a data space via `d360_dataspace_list` (H360 `dispatch` — see `audience-common.md`) and set it as the flow-level `dataSpace`; otherwise omit it.

## Out of scope — data-graph trigger (STOP and route)

`DataGraphDataChange` (fire on a change across a **multi-object data graph**) is a DIFFERENT trigger type, not this single-DMO one. It is **org-gated**: it needs Real-Time Data Graphs enabled on the org, the create/modify-data-graph-trigger user permission, and API version 63.0+, and its start uses `triggeringDataGraph` + `triggeringDataModelObjectPath` (its primary DMO must be `UnifiedIndividual` / `Individual`). If the user wants a data-graph-scoped trigger, that is a separate capability — do NOT emit `DataGraphDataChange` fields on a `DataCloudDataChange` flow, and do NOT silently downgrade a data-graph request to a single-DMO trigger. Confirm the org is provisioned for it first.
