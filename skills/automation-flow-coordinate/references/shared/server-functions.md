---
id: flow.shared.server-functions
---

# Connect API catalog — Flow Builder (`/services/data/vXX.0/flowbuilder/*`)

This catalog is keyed by **Connect API path**. Read paths (GET) are dispatched via
the `dispatch_readonly` tool
(e.g. `dispatch_readonly(method: "GET", url: "/services/data/vXX.0/flowbuilder/schema/flow-capabilities")`);
the WRITE paths in Phase 4c use `dispatch`. The
`salesforce-flow` MCP tool names are retired from this catalog in favor of the
Connect paths they wrap — where a table below has a "Wraps `operationId`" column,
that operationId documents the backing op and is fine to cite. A small set of
salesforce-flow tools have no verified Connect path; those are kept as bare tool
names and marked **(salesforce-flow tool — no Connect path)** — call them by name,
not via `dispatch` or `dispatch_readonly`. Sizes are measured against
a clean dev sandbox; production orgs are larger. **Always prefer
Phase 4a drill-downs over Phase 3 bulk calls when the target is
known.**

## Version segment — REQUIRED on every dispatch

Every Connect API path below is dispatched against `/services/data/vXX.0/...`.
**Always send the full, version-qualified path — never the bare `/flowbuilder/...`
form.** A bare path (no `/services/data/vXX.0` prefix) returns `ROUTE_NOT_FOUND` in
production (it may appear to work locally, which masks the bug).

`vXX.0` is the org's current REST API version. **Resolve it once per session and reuse
it** for every dispatch — do **not** hardcode a release (e.g. `v68.0`) into your calls.
Two equivalent in-session sources (both currently resolve to `v68.0`):
- the version segment already present in any `describe` result's returned `path`, or
- `max(apiVersionsList)` from `dispatch_readonly(method: "GET", url: "/services/data/vXX.0/flowbuilder/flow/version-info")`.

This REST path segment is **distinct** from the Flow's `apiVersion` **metadata** field
(see `flow-properties.md`) — they are numerically related but different concepts; do not
conflate them.

## Calling `describe` / `discover` — use real ids, never invent them

`describe`'s `id` **must be an exact `operationId` or `sor_id`** — passing a
made-up camelCase verb (e.g. `getAccountFields`) fails with
`No operation or SOR found for id: …`. Use the operationId from a table's
"Wraps `operationId`" column (e.g. the entity-fields op is **`listFieldsForEntity`**,
not `getAccountFields`). If you don't have a valid id, call `discover` first and use an
id it returns.

For the pre-baked operations in this catalog, **prefer dispatching the documented
(version-qualified) path directly** — a `describe` round-trip is only needed when you
lack the contract; it is not a prerequisite for the paths listed here.

**Authoritative no-Connect-path tool surface**: for tools marked "no Connect path",
the registered set is `src/tools/register.ts` — trust the live `tools/list` response
over any count in this file.

Several tool names described in older sections of this catalog are NOT
registered by the MCP server (they were considered, then dropped, or
their HARs were captured but never wired). Those are flagged
**[NOT REGISTERED]** in the tables below and kept as bare names — an
unregistered tool has no backing operation, so there is no path to give it.
Calling them will fail. They are kept in this catalog only so
references in older HARs / docs / model training data resolve to a
known-bad note rather than a hallucinated success.

If a live `tools/list` response from the MCP server contradicts the
no-Connect-path portion of this catalog, trust the live response and note the
discrepancy.

## Platform family — exact contracts (10)

All inputs below are top-level properties — queryParams for `dispatch_readonly`
(path params go in the URL). A trailing `?` means optional.

| Tool / path | Wraps `operationId` | Inputs |
|---|---|---|
| `GET /services/data/vXX.0/flowbuilder/platform/entities` | `listEntities` | `crudType?`, `builderType?`, `namePattern?`, `customOnly?`, `limit?`, `offset?` |
| `GET /services/data/vXX.0/flowbuilder/platform/entity/{apiName}` | `getEntity` | `apiName` (required, path), `builderType?` |
| `GET /services/data/vXX.0/flowbuilder/platform/entity/{apiName}/fields` | `listFieldsForEntity` | `apiName` (required), `builderType?`, `fieldType?`, `customOnly?`, `nameableOnly?`, `namePattern?` |
| `GET /services/data/vXX.0/flowbuilder/platform/entity/{apiName}/related-record-fields` | `listRelatedRecordFieldsForEntity` | `apiName` (required), `crudType?`, `builderType?` |
| `GET /services/data/vXX.0/flowbuilder/platform/associated-record-entity` | `getAssociatedRecordEntity` | `processType` (required), `triggerType?` |
| `GET /services/data/vXX.0/flowbuilder/platform/event-types` | `listEventTypes` | `eventType` (required: `Runtime`, `Setup`, or `ManagedSetup`), `builderType?` |
| `GET /services/data/vXX.0/flowbuilder/platform/event-types/{apiName}/parameters` | `listEventTypeParameters` | `apiName` (required) |
| `GET /services/data/vXX.0/flowbuilder/platform/record-id` | `getRecordIdByDevName` | `devName` (required), `entity` (required: `User`, `Group`, or `Queue`) |
| `GET /services/data/vXX.0/flowbuilder/platform/user-access` | `getUserAccess` | `builderType?` |
| `GET /services/data/vXX.0/flowbuilder/platform/permission-set/{name}` | `checkPermissionSetAssignment` | `name` (required, path) |

For `crudType`, use `CREATABLE`, `UPDATABLE`, `DELETABLE`, `QUERYABLE`, or `ALL`
(`ALL` is the default). A `GET /services/data/vXX.0/flowbuilder/platform/entities` call with omitted or
non-positive `limit`
returns at most 100 rows; target by `namePattern` when the object is known, or page
with `limit`/`offset` until all `pagination.totalSize` matches are collected.
`builderType` defaults to `FlowBuilder`; other valid values are `JourneyBuilder`,
`OrchestrationBuilder`, and `AutolaunchedFlowApprovalProcessBuilder`.

---

## Marketing Journey discovery

Call `dispatch_readonly(method: "GET", url: "/services/data/vXX.0/flowbuilder/mce/journeys", queryParams: { mceBuSelector: "<EID>-<MID>", status: "Published", entrySource: "API_EVENT" })`. Load
`elements/action-call/send-to-journey-discovery.md` for selection and schema
resolution. Load `elements/action-call/send-to-journey-recovery.md` only after
Journey-not-found validation.

---

## Phase 1 — describe flow types (3)

Cheap. Required for any new-flow conversation.

| Tool / path | Wraps `operationId` | When to call |
|---|---|---|
| `GET /services/data/vXX.0/flowbuilder/schema/process-types` | `getProcessTypes` | First call when picking a flow type. Returns the org's allowed process types as `{ name, label }` **only** — no `iconName` / `isPauseSupported` / `associatedRecordEntity` (pause support and per-trigger metadata live on `GET /services/data/vXX.0/flowbuilder/schema/trigger-types` detail mode). |
| `flowbuilder_get_flow_entries` (salesforce-flow tool — no Connect path) | `getFlowEntries` | Most LLM-friendly "describe" payload. Returns the New Flow modal tile grid with `label`, `description`, `recommended`, `categoryTags`. |
| `GET /services/data/vXX.0/flowbuilder/schema/flow-capabilities` | `getFlowCapabilities` | **Composite.** One call for a `(processType, triggerType)` returns all 7 capability sections — `.elements`, `.resourceTypes`, `.features`, `.flowFeatures`, `.operators`, `.runInModes`, `.debugAsUser`. Replaces the old per-section calls (`getSupportedElements`, `getResourceTypes`, `getSupportedFeaturesList`, `getSupportedFlowFeaturesList`, `getOperators`, `getRunInModes`). Design-experience feature tokens (StoreOutputAutomatically, FlowTesting, TestModeExperience, …) are in **`.flowFeatures`** (NOT `.features`). Cache once, keyed by the full argument set (`processType, triggerType, recordTriggerType, apiVersion`) — see the composite section below for why the pair alone is insufficient — and read every section from that one result. |

---

## `GET /services/data/vXX.0/flowbuilder/schema/flow-capabilities` — the composite

One Connect operation (`getFlowCapabilities`) that replaces five older per-section
tools. **It always returns all 7 sections**, so five previously-independent cheap
calls are now one heavier call — fire it once, cache the result **keyed by the full
argument set** (`processType, triggerType, recordTriggerType, apiVersion`), and read
each section as needed.

**Params:** `processType` (required), `triggerType?`, `recordTriggerType?`,
`builderType?`, `apiVersion?`.

> **Cache by the full args, not just `(processType, triggerType)`.** `recordTriggerType`
> changes `.operators` and `apiVersion` filters `.flowFeatures`, so a result cached before
> either is known must be **refreshed** once it is (e.g. after `GET /services/data/vXX.0/flowbuilder/flow/version-info` supplies
> `apiVersion`). Reusing a pair-keyed result across a differing `recordTriggerType`/`apiVersion`
> can serve stale operators/features. `.elements`/`.resourceTypes`/`.runInModes` are safe to
> reuse for the same `(processType, triggerType)`.

**Sections (all always present):**

| Section | Was (old tool) | Contents |
|---|---|---|
| `.elements` | `getSupportedElements` | Allowed element node types for the pair. **Mandatory before drafting any element.** Listed ≠ canvas-authorable — emit only palette-authorable entries (carrying a `configComponent`); see `shared/anti-patterns.md` item 29. |
| `.resourceTypes` | `getResourceTypes` | Resource types the user can create (Variable, Constant, …) with attribute schemas. |
| `.features` | `getSupportedFeaturesList` | Process-type-scoped feature list (no trigger dimension). **Does NOT carry the design-experience/testing tokens.** |
| `.flowFeatures` | `getSupportedFlowFeaturesList` | **Trigger-scoped design-experience feature tokens** — `FlowTesting`, `FlowTestingWithDataSilo`, `TestModeExperience`, `StoreOutputAutomatically`, `SupportHierarchicalQuery`, pause-related opt-ins, etc. **This is the section every feature probe reads.** |
| `.operators` | `getOperators` | Operator `{name: label}` dictionary for the flow context (keyed by trigger type + `recordTriggerType`) — **NOT** field-type specific. To validate an operator against a field's data type, use `GET /services/data/vXX.0/flowbuilder/schema/operator-rules`. For **formula** operators use `GET /services/data/vXX.0/flowbuilder/resource/formula-operators` instead. |
| `.runInModes` | `getRunInModes` | `DefaultMode` / `SystemModeWithSharing` / `SystemModeWithoutSharing` with help text. Org-global. Required input to every flow's `runInMode`. |
| `.debugAsUser` | (new) | `{ showIsDebugAsUserAllowed, showIsDebugAsUserAllowedInNonPrd }`. |

> **Pause support** is **not** a token in `.features`/`.flowFeatures`. For whether a **Wait
> element is authorable** for a `(processType, triggerType)` pair, check `.elements` (filtered
> by both) — that is the authoritative signal. `GET /services/data/vXX.0/flowbuilder/schema/trigger-types` detail-mode `.isPauseSupported`
> is a related **trigger-level** hint keyed by `triggerType` alone (see Phase 4a), not the
> dual-keyed element-availability check.

---

## Phase 2 — New Flow modal extras (5 registered)

Mostly debugging. Skip unless explicitly relevant.

| Tool / path | When to call |
|---|---|
| `flowbuilder_get_context` (salesforce-flow tool — no Connect path) | **Heavy (~36 KB).** Org-level Flow Builder UI context: `orgId`, `devMode`, `testMode`, `canVAD`, `builderConfig`. Mostly debugging. |
| `GET /services/data/vXX.0/flowbuilder/resource/apex-types` | Apex-defined types usable in flows. Often `[]` in orgs without custom Apex invocables. |
| `flowbuilder_is_flow_automation_agent_enabled` (salesforce-flow tool — no Connect path) | Is the Flow Automation Agent (Agentforce-style AI authoring) enabled. |
| `GET /services/data/vXX.0/flowbuilder/platform/permission-set/{name}` | Checks whether the current user has a named permission set. Required path param: `name` (bare or namespace-qualified developer name). |
| `flowbuilder_get_templates` (salesforce-flow tool — no Connect path) | **Heavy (~126 KB).** Org-wide template library. (Single source — `flowbuilder_get_modal_templates` is **[NOT REGISTERED]**.) |
| `flowbuilder_get_frequently_used_types` **[NOT REGISTERED]** | use `GET /services/data/vXX.0/flowbuilder/schema/process-types` instead. |
| `flowbuilder_get_modal_templates` **[NOT REGISTERED]** | use `flowbuilder_get_templates` instead (salesforce-flow tool — no Connect path). |

---

## Phase 3 — canvas hydration (18 registered)

### Editor primitives (5 registered)

| Tool / path | When to call |
|---|---|
| `GET /services/data/vXX.0/flowbuilder/schema/flow-capabilities` (`.elements`) | Allowed element node types for `(processType, triggerType)`. **Mandatory before drafting any element.** Listed ≠ canvas-authorable: emit only palette-authorable entries (carrying a `configComponent`) — see `shared/anti-patterns.md` item 29. Section of the composite (was `getSupportedElements`) — one call also yields resource types, operators, features, run-in-modes. |
| `GET /services/data/vXX.0/flowbuilder/schema/flow-capabilities` (`.resourceTypes`) | Resource types user can create (Variable, Constant, …) with attribute schemas. Section of the composite (was `getResourceTypes`). |
| `GET /services/data/vXX.0/flowbuilder/schema/flow-capabilities` (`.operators`) | Operator `{name: label}` dictionary for the flow context (keyed by trigger type + `recordTriggerType`) — **NOT** field-type specific; use `GET /services/data/vXX.0/flowbuilder/schema/operator-rules` to validate a field/operator pairing. For **formula** operators (`+ - * / ^ & = <> < > <= >= && \|\|`) use `GET /services/data/vXX.0/flowbuilder/resource/formula-operators` instead — formula syntax is its own vocabulary. Section of the composite (was `getOperators`). |
| `GET /services/data/vXX.0/flowbuilder/schema/operator-rules` | **Heavy (~470 KB).** Assignment/decision rule matrix. **Default-caps at 100 rules when `limit` is omitted or non-positive** — an explicit positive `limit` overrides it (even >100), and `pagination.totalSize` reports the true post-filter count. A bare call is NOT the full matrix: filter with `operator`/`ruleType` or page with `limit`/`offset`. |
| `GET /services/data/vXX.0/flowbuilder/resource/formula-functions` | Formula functions grouped by category (Logical, Text, Math, Date & Time, Advanced), scoped to `(processType, triggerType)`. ~90 functions on a standard flow. **Discover here rather than hardcoding — availability is context-specific.** See [[flow.shared.formula-expression]]. |
| `GET /services/data/vXX.0/flowbuilder/resource/formula-operators` | Formula operator vocabulary for the context. Note equality is `=` / `<>` (not `==` / `!=`). |
| `flowbuilder_validate_formula_syntax` (salesforce-flow tool — no Connect path) | On-demand syntax check for one formula expression (Check Syntax button). Returns `{ isValidSyntax, validationMessage }`. **Requires `validationOptions.flowMetadata` (a JSON string of the surrounding flow) + `elementType: "Formula"` + `dataType` — omitting `flowMetadata` 500s.** Only resolves field/resource refs present in that flowMetadata; for a formula in a flow you're building, `POST /services/data/vXX.0/flowbuilder/flow/actions/save` checks it in full context. |
| `flowbuilder_get_palette` **[NOT REGISTERED]** | element data lives in `GET /services/data/vXX.0/flowbuilder/schema/flow-capabilities` (`.elements`). |

### Org schema (4 registered)

| Tool / path | When to call |
|---|---|
| `GET /services/data/vXX.0/flowbuilder/platform/entities` | **Heavy at org scale (~355 KB).** Defaults to at most 100 rows. Target with `namePattern`, or page with `limit`/`offset`; optional filters include `crudType`, `builderType`, and `customOnly`. Prefer `GET /services/data/vXX.0/flowbuilder/platform/entity/{apiName}/fields` when you know the target. |
| `flowbuilder_get_data_cloud_entities` (salesforce-flow tool — no Connect path) | Data Cloud DLM/DMO entities with capabilities. |
| `GET /services/data/vXX.0/flowbuilder/platform/event-types` | Platform events. Requires `eventType` (`Runtime`, `Setup`, or `ManagedSetup`) with no default; optional `builderType`. Query all three categories when the intent is broad. |
| `GET /services/data/vXX.0/flowbuilder/flow/version-info` | Per-process-type API version lists/defaults. Accepts optional `builderType` only; it does not accept `processType`. Select the current flow type from `processTypes[]`, then pick from that row's `apiVersionsList`. **Required before save** to pick `apiVersion`. |
| `flowbuilder_get_workflow_enabled_entities` **[NOT REGISTERED]** | `GET /services/data/vXX.0/flowbuilder/platform/entities` can verify object existence and CRUD capability, but its current response cannot prove record-trigger eligibility. |
| `flowbuilder_get_feature_configurations_for_flow_type` **[NOT REGISTERED]** | feature config lives in `GET /services/data/vXX.0/flowbuilder/schema/flow-capabilities` (`.flowFeatures`). |

### Globals / runtime context (3 registered)

| Tool / path | When to call |
|---|---|
| `GET /services/data/vXX.0/flowbuilder/resource/system-variables` | `$Flow.*` system variables. |
| `GET /services/data/vXX.0/flowbuilder/resource/global-variables` | Global variables (`$Api`, `$Organization`, `$User`, `$Profile`, `$Label`, …). Core consolidated the former split `get_all_but_label_global_variables` + `get_label_global_variables` tools into this one op. Requires `processType`. **Unscoped it is heavy (~73 KB)** — narrow with `section` (`user`, `organization`, `system`, `api`, `profile`, `setup`, `permission`, `labels`); for the high-cardinality `labels` section, further filter with `namePattern` (case-insensitive substring; ignored for other sections). |
| `GET /services/data/vXX.0/flowbuilder/platform/associated-record-entity` | Requires `processType`; optional `triggerType` (defaults to `None`). Returns `{associatedRecordEntity: string \| null}`. |
| `flowbuilder_get_frp_quick_access` **[NOT REGISTERED]** | hardcode `['Account', 'Contact', 'Opportunity']` if you need a quick-access list. |

### Invocables / subflows / extensions (6)

| Tool / path | When to call |
|---|---|
| `GET /services/data/vXX.0/flowbuilder/action/invocable-actions` | **Heavy on integration-rich orgs (multiple MB).** Single combined catalog of standard invocable actions (platform built-ins) AND dynamic actions (managed/custom/External Connector/External Service/ESR). Core collapsed the former separate standard/dynamic catalogs into this one op. **Excludes transform actions** — the server filters those out, and no Connect path exposes them. Required `processType`; narrow with `actionType`/`namePattern`/`limit`; `dataSpace`/`flowDefinitionId` scope the **dynamic portion** of the combined result (they don't split it — Core always calls `getAllowedActions` with `includeStandard=true, includeDynamic=true`, so there is no standard-only or dynamic-only variant). Prefer `GET /services/data/vXX.0/flowbuilder/action/invocable-action-details` for one action. |
| `GET /services/data/vXX.0/flowbuilder/action/invocable-events` | Engagement/automation events a WaitUntilEvent element can bind to (email-open, SMS-response, etc.). Required `processType`; optional `triggerType`, `builderType`, `dataSpace`, `actionType`, `namePattern`, `limit`. Response: `invocableActions[]`; each entry's `type` = `automationEventType`, `name` = `automationEventName`. Call before authoring a WaitUntilEvent to confirm provisioned event types and their exact spellings. |
| `flowbuilder_get_apex_plugins` (salesforce-flow tool — no Connect path) | Legacy `Process.Plugin` Apex plugins. Often `[]`. |
| `GET /services/data/vXX.0/flowbuilder/flow/subflows` | Autolaunched flows callable as subflows. Can be large. **Required for any subflow element.** Optional server-side filters: `flowDefinitionId`, `dataSpace`, `subflowFilterType` (e.g. `MARKETING`), `namePattern`, `builderType` — all optional, so a bare call to this path with no query params returns the full callable set. |
| `GET /services/data/vXX.0/flowbuilder/screen-component` | LWC/Aura extension LIST usable on Screens. **Required `processType`** (the available set varies by process type). Optional server-side filters: `builderType`, `namePattern`, `type` (case-insensitive extension-type filter, e.g. `lightning__component`), `limit`. Returns each component's API name + metadata; pass `expand=parameters` to fold each component's input/output params into the list result (same data `GET /services/data/vXX.0/flowbuilder/screen-component/{apiName}` returns, in one call) — but `expand=parameters` requires at least one of `namePattern`/`type`/`limit` (a bare `expand=parameters` returns 400, to prevent expanding every component in the org). Without `expand`, drill into one component's schema with `GET /services/data/vXX.0/flowbuilder/screen-component/{apiName}`. |
| `flowbuilder_get_auto_generated_required_variables` (salesforce-flow tool — no Connect path) | Auto-bound input variables. Often `[]`. Until a Connect path exists, the per-processType required variables come from the interim hardcoded `../shared/required-variables/required-variables.json`; switch to the probe once available. |

---

## Phase 4a — read-only drill-downs

Targeted single-item lookups. **Always prefer these over Phase 3 bulk
calls when you know the target.**

| Tool / path | When to call |
|---|---|
| `GET /services/data/vXX.0/flowbuilder/platform/entity/{apiName}/fields` | Field schema for ONE sObject. Requires `apiName`; optional `builderType`, `fieldType`, `customOnly`, `nameableOnly`, `namePattern`. ~53 KB for Account. **Mandatory for any element referencing a sObject field.** **FLS-filtered by the MCP session's authenticated Salesforce user, and the response is authoritative** — the returned list *is* the field inventory the skill may reference for this sObject. A field not in the response is inaccessible: it may not exist on this org, or the user is FLS-blocked. In either case, the skill MUST NOT reference the field in flow metadata (filter conditions, `leftValueReference`, `assignToReference`, `queriedFields`, output mappings) even if the field name is a well-known standard field like `DoNotCall`, `HasOptedOutOfEmail`, or `HasOptedOutOfFax`. When the user's request depends on a field not in the response, either build without it or halt and refer the user to their Salesforce admin — see `../shared/anti-patterns.md` item 40. A `namePattern` filter that returns `{"fields":[]}` for a well-known standard field is the same signal — an FLS-hidden field, not a broken filter. |
| `GET /services/data/vXX.0/flowbuilder/mce/journeys` | Discover Marketing Cloud Journeys for one required `mceBuSelector`. Optional `categoryId`, `nameSearch`, `status`, and `entrySource`; no `flowDefinitionId`. Follow the dedicated section above and `elements/action-call/send-to-journey.md`. |
| `GET /services/data/vXX.0/flowbuilder/action/invocable-events` | Discover engagement and automation events for `WaitUntilEvent`. Require `processType`; optionally pass `triggerType`, `builderType`, `dataSpace`, `actionType`, `namePattern`, or `limit`. Read descriptors from `invocableActions[]`: bind each row's `type` to `automationEventType` and `name` to `automationEventName`. Do not use `GET /services/data/vXX.0/flowbuilder/platform/event-types`, which lists classic platform events. |
| `GET /services/data/vXX.0/flowbuilder/action/invocable-action-details` | Full schema for ONE invocable action. ~38 KB for `emailSimple`. **Mandatory for any `actionCalls[]` element.** Inspect the response for a non-empty `genericTypes[]` — if present, the action has placeholder types (`U__input`/`U__output`) that need `GET /services/data/vXX.0/flowbuilder/action/invocable-action-generic-type-enum-values` once the user has picked the driving input. |
| `GET /services/data/vXX.0/flowbuilder/action/invocable-action-generic-type-enum-values` | Resolve generic-type placeholders. For `sendToJourney`, pass `builderType: "JourneyBuilder"`, `processType: "AutoLaunchedFlow"`, `requestedGenericTypes: ["JourneyDataExtensionSchema"]`, and JSON-string `inputParamsJson` containing both selectors. Require `ALL_VALUES_PROVIDED`; read the sole `typeProviders.values[0].value` URI and require it to end in the selected Journey ID. |
| `GET /services/data/vXX.0/flowbuilder/action/schema-uri-parameters` | Resolve fields behind one schema URI. For `sendToJourney`, pass `schemaUri` and `builderType: "JourneyBuilder"`. Stop when any returned field lacks `isRequired`. |
| `GET /services/data/vXX.0/flowbuilder/screen-component/{apiName}` | Full parameter schema for ONE LWC/Aura screen extension, identified by a singular `apiName` (path) — **not batched**; one component per call. Also requires `processType` (the returned schema varies by process type — pass the same value used for the list call). Optional: `builderType`. **Mandatory for any Screen field with `fieldType: ComponentInstance` / `ComponentChoice` / `ComponentMultiChoice`.** Drill-down companion to `GET /services/data/vXX.0/flowbuilder/screen-component` (Phase 3 list): use that to discover API names, then call this per component (or skip it by passing `expand=parameters` to a *filtered* list call — `expand` needs at least one of `namePattern`/`type`/`limit`). |
| `flowbuilder_get_connector_details` (salesforce-flow tool — no Connect path) | Configuration for ONE external connector by developer name. **Mandatory when configuring an HTTP Callout action or any action backed by a Named Credential** — validates the connector exists and exposes its config. Lives on `ExternalConnectivityController` (not `FlowBuilderController`), same cross-controller pattern as `flowbuilder_get_templates`. Can return an ERROR state if the name is not a valid external connector; treat that as a Probe failure, not a transient error. |
| `GET /services/data/vXX.0/flowbuilder/flow/{flowDefinitionId}/versions` | Version list for one flow definition. **Required before any save with `saveAsNewVersion`, before `POST /services/data/vXX.0/flowbuilder/flow/{flowId}/actions/deactivate`, and before handing UI activation to the user.** |
| `GET /services/data/vXX.0/flowbuilder/schema/trigger-types` (detail mode) | **Heavy (~45 KB).** Comprehensive metadata for ONE trigger type. Required when picking record/event/schedule trigger. Detail mode = pass `processType` (**required**) **and** `triggerType`; the response wraps the single descriptor as `{ triggerTypes: [ <descriptor> ] }` — unwrap `triggerTypes[0]`. The descriptor carries `.isPauseSupported`. (Was `getTriggerTypeInfo`, which took only `triggerType`; the new contract adds the required `processType`.) A bare call to this path with `processType` and no `triggerType` is list mode — all trigger types for the process type. |
| `GET /services/data/vXX.0/flowbuilder/platform/event-types/{apiName}/parameters` | Field schema for ONE platform event. Requires its `apiName`. **Mandatory for `triggerType=PlatformEvent`.** |
| `flowbuilder_get_log_metrics_in_data_cloud_supported` (salesforce-flow tool — no Connect path) | Boolean. |
| `flowbuilder_is_flow_run_setup_in_data_cloud` (salesforce-flow tool — no Connect path) | Boolean (org-wide). |
| `GET /services/data/vXX.0/flowbuilder/action/org-wide-email-addresses` | Org-wide email addresses for Send Email actions, as address strings without Ids. Often `[]`. To bind `senderId`, look the Id up with SOQL (see [`../elements/action-call/action-call.md`](../elements/action-call/action-call.md) § Resolve names to Ids). |
| `GET /services/data/vXX.0/flowbuilder/messaging/sender-sms-codes` | Discover active SMS senders before authoring `sendSmsMessage`. Omit `businessUnitId` unless you have a verified 15- or 18-character Salesforce record ID. A direct Business Unit ID starts with `1QO`; accept another prefix only after verifying that the record is related to that Business Unit. Never pass an MCE `mid` or `<EID>-<MID>` selector. Read `senderSmsCodes[]`, then bind a selected row's `id` to `senderId`, never its `messagingPlatformKey`. |
| `GET /services/data/vXX.0/flowbuilder/messaging/sender-rcs-agents` | Discover RCS sender agents whose Flow capability is active. Omit `businessUnitId` unless you have a verified 15- or 18-character Salesforce record ID. A direct Business Unit ID starts with `1QO`; accept another prefix only after verifying that the record is related to that Business Unit. Never pass an MCE `mid` or `<EID>-<MID>` selector. Bind a selected row's `id` to `senderAgentId`, never its `messagingPlatformKey`. |
| `GET /services/data/vXX.0/flowbuilder/messaging/content-fqn` | Resolve a `managedContentId` (discovered via SOQL over `ManagedContent` or the CMS Connect API `GET /connect/cms/delivery/channels/{channelId}/contents` — see [`../elements/action-call/action-call.md`](../elements/action-call/action-call.md) § `contentId` Rule) to the FQN required by messaging `contentId`. Bind only the returned `contentFqn`; never bind the CMS content key, `9Ps` variant ID, title, URL name, or raw managed-content ID. |
| `GET /services/data/vXX.0/flowbuilder/messaging/communication-subscriptions` | Discover consent subscriptions for SMS, RCS or email. For SMS and RCS, pass `contactPointType`, `messagingChannelId` (the sender's `id`), and `channel`. For email (`sendEmailMessage`), pass `channel: "email"` and `contactPointType: "Email"` and omit `messagingChannelId`. Omit `businessUnitRelatedId` unless you have a verified 15- or 18-character Salesforce record ID. A direct Business Unit ID starts with `1QO`; accept another prefix only after verifying that the record is related to that Business Unit. Never pass an MCE `mid` or `<EID>-<MID>` selector. Read `communicationSubscriptions[]`, then bind one row's `id` and `channelTypeId` together. |
| `flowbuilder_get_overridable_flows` **[NOT REGISTERED]** | use `GET /services/data/vXX.0/flowbuilder/flow/{flowDefinitionId}/versions` and inspect `isOverridable`. |
| `flowbuilder_get_action_creation_data` **[NOT REGISTERED]** | action builder is out of scope for this PoC. |
| `flowbuilder_get_is_pause_supported` **[NOT REGISTERED]** | read `.isPauseSupported` from `GET /services/data/vXX.0/flowbuilder/schema/trigger-types` detail mode (pass `processType` + `triggerType`). It is **not** a feature-list token. |

---

## Phase 4a — messaging send-action discovery (4 registered)

Org-configuration reads for authoring the E360 messaging send actions
(`sendSmsMessage`, `sendRcsMessage`). Wrap the `flow-builder-messaging`
Connect operations; builder-agnostic (no `processType`/`builderType`).
Both the RCS and SMS discovery workflows use these — see
[`../elements/action-call/action-call.md`](../elements/action-call/action-call.md)
§§ Send RCS Message Action / Send SMS Message Action. RCS binds
discovered Ids via `elementReference`; SMS binds them as design-time
`stringValue` literals (it rejects element references).

| Path | Wraps `operationId` | When to call |
|---|---|---|
| `GET /services/data/vXX.0/flowbuilder/messaging/sender-rcs-agents` | `listSenderRcsAgents` | Lists RCS sender agents for `senderAgentId`. Optional `businessUnitId` (reuse the same value as `businessUnitRelatedId` on `GET /services/data/vXX.0/flowbuilder/messaging/communication-subscriptions`). Returns `senderRcsAgents[] { id, messagingPlatformKey, masterLabel, useCase }` — bind `id`, never `messagingPlatformKey`. |
| `GET /services/data/vXX.0/flowbuilder/messaging/communication-subscriptions` | `listCommunicationSubscriptions` | Lists consent subscriptions for a messaging channel. **Required `contactPointType`, `messagingChannelId`, `channel`** (`channel:"rcs"` for RCS, `channel:"sms"` for SMS; `contactPointType:"Phone"` and `messagingChannelId` = the sender's `id` for both); optional `businessUnitRelatedId`. Returns `communicationSubscriptions[] { id, name, channelTypeId }` — bind one row's `id` → `communicationSubscriptionId` and that same row's `channelTypeId` → `commSubscriptionChannelTypeId`. |
| `GET /services/data/vXX.0/flowbuilder/messaging/content-fqn` | `describeContentFqn` | Resolves a managed-content Id to its FQN for `contentId`. **Required `managedContentId`** (a real Id — a name/slug hard-fails). Returns `{ managedContentId, contentFqn }` — bind `contentFqn`. |
| `GET /services/data/vXX.0/flowbuilder/messaging/sender-sms-codes` | `listSenderSmsCodes` | Lists SMS sender codes for `sendSmsMessage`'s `senderId`. Optional `businessUnitId`. Returns `senderSmsCodes[] { id, messagingPlatformKey, isoCountryCode }` — bind the chosen row's `id` (a MessagingChannel Id) to `senderId` as a literal, never `messagingPlatformKey`. |

---

## Phase 4b — read-only data lookup (1)

| Tool | When to call |
|---|---|
| `flowbuilder_fetch_records` (salesforce-flow tool — no Connect path) | **Returns USER DATA, not metadata.** Searches actual records (Documents, Attachments, …) by string. Different cognitive bucket. Use sparingly. |

---

## Phase 4d — full flow body reads (2 registered)

| Path | When to call |
|---|---|
| `GET /services/data/vXX.0/flowbuilder/flow/{id}` | Wraps `retrieveFlow` — returns the raw Flow element graph without validation results. Prefer this lighter read for flow and element summarization. Its `id` accepts four forms: (1) a `301xxx` FlowVersion id (exact version, used as-is); (2) a `300xxx` FlowDefinition id (resolved server-side to the Active version, else the latest when none is active); (3) a custom flow's API/developer name — either bare (`My_Flow`) or namespace-qualified (`namespace__My_Flow`) — resolved server-side to Active-else-latest; or (4) a standard / managed-package flow's version durable id of the form `namespace__ApiName-N` (e.g. `omnichannel_chat__QueuesChat-1`, used as-is — a standard flow must be addressed by this versioned durable id, not its bare `namespace__ApiName` definition name). For forms (2) and (3) the response echoes `resolvedFlowVersionId` and `resolvedFrom` (`definitionId` or `apiName`). Never pass display labels, and do not make a separate `GET /services/data/vXX.0/flowbuilder/flow/{flowDefinitionId}/versions` call for summarization. |
| `GET /services/data/vXX.0/flowbuilder/flow/{id}/validation-results` | Wraps `retrieveFlowWithValidationResults` — returns the entire element graph plus `validationResults` for an existing flow version. Params: path `id` (a `301xxx` FlowVersion id, or a `300xxx` FlowDefinition id to resolve+read its Active version) + optional `builderType` — same id contract as `GET /services/data/vXX.0/flowbuilder/flow/{id}`; there is no `flowVersionId` param. NOT to be confused with `GET /services/data/vXX.0/flowbuilder/flow/{flowDefinitionId}/versions` (version metadata only) or `GET /services/data/vXX.0/flowbuilder/schema/operator-rules` (org-wide rule catalog). Note: SKILL.md still says "no round-trip read"; this path is the exception, but the element graph it returns is large — use only when editing requires the existing shape. |

---

## Phase 4c — WRITE actions (mutate org state)

Give every callable WRITE a one-line confirmation summary first: path (or tool
name for no-Connect-path tools), target, and org host. Apply the tool-specific
restrictions below.

| Tool / path | When to call |
|---|---|
| `POST /services/data/vXX.0/flowbuilder/flow/actions/validate` | **Not a WRITE** (POST via `dispatch`) — never persists; no confirmation summary. Use only where save is DISABLED (save already validates). Body `{flow: {fullName, metadata}}`; returns `isSuccess`, `errors[]`, `warnings[]`. |
| `POST /services/data/vXX.0/flowbuilder/flow/actions/save` `[WRITE]` | Creates new flow, saves a new version, or updates the current draft in place. `saveType` (case-sensitive): `createNewFlow` / `saveAsNewVersion` / `saveAsNewDefinition` / `saveDraft`. Optional `currentFlowId` (the currently open Flow Version ID) and `builderType`. **Returns `errors[]` and `warnings[]`; treat both as the validation source of truth.** (Cloning to a brand-new definition is a distinct path, `POST /services/data/vXX.0/flowbuilder/flow/actions/clone`, not this one.) |
| `POST /services/data/vXX.0/flowbuilder/flow/{flowId}/actions/activate` (`activateFlow`) `[WRITE]` | **Disabled; do not dispatch it.** MCP does not expose it; direct Connect returns 404. Prompt the user to activate the flow in Flow Builder UI through the post-save "Open in Salesforce" deep link instead; see `preview-renderer.md`. |
| `POST /services/data/vXX.0/flowbuilder/flow/{flowId}/actions/deactivate` `[WRITE]` | Call only after confirming that `id` identifies the Active `301…` version. Stop before the call when no Active version exists; Core rejects it with HTTP 400. **This stops a production flow.** Pass optional `cancelOnDeactivate` to cancel paused interviews. |
| `POST /services/data/vXX.0/flowbuilder/flow/{flowId}/actions/submit-for-activation` `[WRITE]` | Submits an activation-approval request through the server's hard-coded `OrchestrationBuilder` service. Call only when an Orchestration activation-approval workflow explicitly requires submission. Never call it after `POST /services/data/vXX.0/flowbuilder/flow/{flowId}/actions/activate` returns 404, and never use it to activate an ordinary or Segment flow. A 404 does not indicate the flow has the wrong `processType`; it means this approval route did not resolve the target. |
| `POST /services/data/vXX.0/flowbuilder/flow-test/actions/copy-to-version` `[WRITE]` | Copies FlowTestFieldValue records between versions. Required body: `sourceVersionId`, `targetVersionId`. Report completion only when the optional response field is explicitly `isSuccess === true`; otherwise the copy outcome is failed or unproven. **Mandatory after `saveAsNewVersion` when the source version has saved FlowTests**, regardless of trigger type; the operation has no effect when versioned FlowTest support is disabled. |

---

## Heavy-tool budget (cumulative tokens, rough)

If the agent fires every Phase 2 + Phase 3 bulk path/tool once, that's
roughly:
- `GET /services/data/vXX.0/flowbuilder/schema/operator-rules` — 470 KB
- `GET /services/data/vXX.0/flowbuilder/platform/entities` — 355 KB
- `flowbuilder_get_templates` (no Connect path) — 126 KB
- `GET /services/data/vXX.0/flowbuilder/action/invocable-actions` — 92 KB+ (unfiltered; multiple MB on integration-rich orgs)
- `GET /services/data/vXX.0/flowbuilder/resource/global-variables` — 73 KB (unscoped; narrow with `section` to shrink)
- `GET /services/data/vXX.0/flowbuilder/schema/trigger-types` (detail mode) — 45 KB

Together ≈ **1.16 MB** of bulk JSON before the agent has even drafted
the plan. `author.md` Phase 2 prevents this: probe only what a concrete
user assertion requires, ask for exact names before enumerating, cap at
~10 probe calls, prefer drill-downs (Phase 4a), and reuse the
conversation-history probe cache.

---

## Phase 5 — Flow Testing and debug runtime

Read operations below are dispatched via `dispatch_readonly`; WRITE operations
(flagged `[WRITE]`) use `dispatch`. The no-Connect-path
tools among them (flagged inline) are still called by their bare
`snake_case(operationId)` name, with no server prefix (`AGENT_NAME_PREFIX` and
`NAME_OVERRIDES` are empty).
Historical UI helpers that are not onboarded are labeled separately and must
never be called.

If a live `tools/list` response from the MCP server contradicts the
no-Connect-path portion of this catalog, **trust the live response** and
update the catalog.

---

### Debug & runtime (6)

Inspect the flow runtime: discover what inputs the flow accepts, build
sample inputs, run the flow with those inputs (DML on or off), resume a
paused run, and read past interview traces.

| Tool / path | When to call |
|---|---|
| `GET /services/data/vXX.0/flowbuilder/flow-test/debug-component-config` | Returns the per-element debug-input config for a flow version — what variables the flow accepts, which are required, sample shape per type. **Mandatory** before any debug run on a flow you have not seen the inputs for. Query param: `flowVersionId` (`301xxx`). |
| `POST /services/data/vXX.0/flowbuilder/flow-test/debug-data` | Queries any object you name (`objectName`) for the fields you list (`columns`) and returns field schema plus matching records. Required body: `objectName`, `columns`; optional `limit`, `dataSpaceName`, `debugRecordId`, `debugRecordType`, `builderType`. Use it to find a real trigger record for a record-triggered debug run. |
| `POST /services/data/vXX.0/flowbuilder/flow-test/debug-interview-test-mode` | Payload-driven debug run for flow types whose capability probe reports `TestModeExperience` support (see the routing probe in [[flow.recipes.testing.workflows.debug]]). Rolls back when the test's `doesCommitChanges` is `false` (default), commits when `true`. Required body: `flowVersionId`, `flowTestJson` (a JSON-encoded string of the same FlowTest definition used by `POST /services/data/vXX.0/flowbuilder/flow-test`/`PATCH /services/data/vXX.0/flowbuilder/flow-test/{id}`); optional `enableTrace`, `showGovernorLimit`. To pause at Wait elements, set `doesTestWaitElement: true` inside `flowTestJson` (autolaunched flows with no trigger only; a Wait the test mocks never pauses). Returns `results[]`, one entry per debugged record. Neither run endpoint is a global default — the debug workflow probes and picks; see the routing probe in [[flow.recipes.testing.workflows.debug]]. |
| `POST /services/data/vXX.0/flowbuilder/flow-test/debug-interview` | Argument-driven debug run for flow types whose capability probe does NOT report `TestModeExperience` support (see the routing probe in [[flow.recipes.testing.workflows.debug]]). Commits when `enableRollbackMode` is `false` (default), rolls back when `true`. Required body: `flowVersionId`; optional `flowDevName`, `arguments` (input vars as a JSON **string**, not a nested object), and run knobs (`enableTrace`, `useLatestSubflow`, `debugWaits`, `scheduledPathSelection`, `debugAsUserId`, …). Returns `results[]`, one entry per debugged record. NEVER commit real DML against production records without explicit user confirmation that quotes the org host. Also used for a final sanity check on a sandbox you're about to promote. |
| `POST /services/data/vXX.0/flowbuilder/flow-test/debug-interview-resume` | Continues a debug interview paused at a Wait element (`interviewStatus` `WAITING` / `ASYNC_WAITING`). Required body: `flowVersionId` plus the four state fields fed back VERBATIM from the prior run's result — `serializedInterview`, `resolvedContext`, `serializedCumulativeDebugInfo`, `waitEvent`; `waitEvent` is the `name` of one `waitEvents[]` entry (never its `value`), and a blank one makes the resume fail. The server does not compare settings with the original run, so pass the same `enableRollbackMode` / `debugAsUserId` / `enableTrace` / `showGovernorLimit`; `useLatestSubflow` is ignored; optional `arguments`, `enableTrace`, `enableRollbackMode`, `showGovernorLimit`, `debugAsUserId`, `useLatestSubflow`. Returns a single `{runInterviewResult, canvasDecorator}` (not the list wrapper). |
| `GET /services/data/vXX.0/flowbuilder/flow-test/debug-run-as-validation` | Pre-flight guard for **debug-as-another-user**: returns `{ showIsDebugAsUserAllowed, showIsDebugAsUserAllowedInNonPrd }` (prod + non-prod). Query `flowVersionId` OR `flowDevName` (supply one). Cheap. Call this **before** passing a `debugAsUserId` to `POST /services/data/vXX.0/flowbuilder/flow-test/debug-interview` — it validates run-as-user permission, not whether a flow is debuggable in general. |

---

### Interview history (2)

| Path | When to call |
|---|---|
| `GET /services/data/vXX.0/flowbuilder/flow-test/interview-history` | Pulls the full element-by-element execution trace for one interview. Required query params: `interviewGUID` (the run's interview identifier — **not** a generic `interviewId`) and `flowVersionId`; the history is returned only when its captured version matches `flowVersionId`. Produced by an earlier `POST /services/data/vXX.0/flowbuilder/flow-test/debug-interview` / `POST /services/data/vXX.0/flowbuilder/flow-test/debug-interview-test-mode` call. **Per-flow-version only — no inter-org / cross-session forensic queries.** Use when investigating "why did the flow do X?" after the fact. |
| `GET /services/data/vXX.0/flowbuilder/flow-test/record-run-data` | Drills into ONE record's execution after a multi-record (high-scale) debug run. Required query params: `flowRunId` (the record's run id / interview GUID) and `flowVersionId`. Returns a single `{runInterviewResult, canvasDecorator}` — use instead of re-running the whole interview when the run produced several records. |

---

### Saved-test management (8)

Persist debug runs as `FlowTest` records (`320xxx` IDs), list them,
load them, delete them, and convert a debug interview into a draft
test definition.

| Tool / path | When to call |
|---|---|
| `POST /services/data/vXX.0/flowbuilder/flow-test` `[WRITE]` | First-time save of a flow test. Required body: `flowTestJson`, a JSON-encoded **string** of the FlowTest definition (`JSON.stringify(flowTest)`). Continue only when the response has `isSuccess === true` and a non-empty string `flowTestId`; other response shapes do not prove a usable test was created. There is no `saveType` switch — use this path only for first save. **Mutates org state — confirm with user first.** Definition shape: [[flow.recipes.testing.shape]]. |
| `PATCH /services/data/vXX.0/flowbuilder/flow-test/{id}` `[WRITE]` | Re-save an existing test. Required path: `id` (the `320xxx` ID); required body: `flowTestJson`, the complete updated definition as a JSON-encoded **string** (`JSON.stringify(completeDefinition)`). There is no partial patch. Re-run or report the update only when `isSuccess === true`. **Mutates org state — confirm with user first.** |
| `GET /services/data/vXX.0/flowbuilder/flow-test/{id}` | Round-trip a saved test. Required path: `id`. Returns `{flowTestJson: string}`; parse that JSON-encoded string before inspecting `fullName`, `metadata.testPoints`, assertions, or `doesCommitChanges`. Unknown IDs return HTTP 404. |
| `GET /services/data/vXX.0/flowbuilder/flow-test` | Lists a flow's tests with their latest run summaries — the single listing path. Query params: `flowDefinitionId?`, `flowVersionId?` (scope to one version), `offset?`, `limit?` (paginated), `includeDebugRunTest?`. When requested, an available auto-generated debug-run test is returned separately as `debugRunFlowTest`; parse it only when `typeof debugRunFlowTest === "string"`. Absent/null means no debug-run payload, and it is never inserted into `flowTests[]`. |
| `GET /services/data/vXX.0/flowbuilder/flow-test/debug-run-result` | Returns the auto-generated test saved from the **most recent debug run** of the given flow version (the `WithoutAssertion` debug-run test) — **not** a saved `320xxx` test selected by id. Returns an **empty result** when that version has no debug-run test. Query param: `flowVersionId` (required). Use it to inspect what a prior debug run exercised before re-running or building a formal test from it. |
| `DELETE /services/data/vXX.0/flowbuilder/flow-test/{id}` `[WRITE]` | Delete a single test. Path: `id` (required — one `320xxx` test per call; there is no bulk `flowTestIds[]` form). Report deletion only when `isSuccess === true`; on `false`, surface `errorMessage` when present, and treat missing status as unproven. **Mutates org state — confirm with user first.** Note: this removes the test, not the parent flow. |
| `POST /services/data/vXX.0/flowbuilder/flow-test/actions/generate-from-debug-run` | Required body: `serializedInterview`. Its response fields are optional: continue only when `isSuccess === true` and `flowTestJson` is a string, then parse the JSON-encoded FlowTest; on missing/null/malformed output, surface the raw response or use Route A. |
| `POST /services/data/vXX.0/flowbuilder/flow-test/actions/generate-test-detail` | Required body: `serializedInterview`. Returns an optionally populated structured FlowTest detail; inspect only fields that are present (`id`, `apiName`, `label`, `description`, `flowApiName`, `testType`, `testPoints[]` are all optional), and handle an empty representation. It is distinct from `POST /services/data/vXX.0/flowbuilder/flow-test/actions/generate-from-debug-run`, which returns `flowTestJson`. |

---

### Test execution (1)

Run the saved tests; `POST /services/data/vXX.0/flowbuilder/flow-test/actions/run` honours each
test's `doesCommitChanges` setting (false → DML rolled back, true → committed).

| Path | When to call |
|---|---|
| `POST /services/data/vXX.0/flowbuilder/flow-test/actions/run` | Run saved tests. Body: `flowVersionId` (required); `testIds?` (a subset — omit or pass an empty array to run the flow's whole suite); `flowDefinitionId?` (supply for a whole-suite run); `showTrace?: bool = false`. This one path covers both subset and full-suite runs. Single-test debugging → set `showTrace=true` for heavier execution-trace detail. Large runs (20+ tests) → leave `showTrace=false` for compact pass/fail. When present, the response's `results` field is an array of per-test descriptors with status/errors/timestamps — see [[flow.recipes.testing.run-results]]. |

---

### Coverage data unavailable through MCP

| Tool | When to call |
|---|---|
| `flowbuilder_get_flow_test_coverage_results_and_decorators` — **[not callable]** | Historical Flow Builder UI operation; no MCP server operation exists. Do not attempt the call. Interpret externally supplied coverage data with [[flow.recipes.testing.coverage-interpretation]]. |

---

### Apex test-setup discovery unavailable through MCP

The "Apex Test Setup Class" dropdown in the Save Flow Test dialog,
plus its two preview helpers. Together these populate
`flowTestDataSources[]` and `isolatedObjectExternalKeys[]` on the
saved test — see [[flow.recipes.testing.flowtest-elements.silo-config]].

| Tool | When to call |
|---|---|
| `flowbuilder_get_available_apex_classes_with_set_up` — **[not available as an MCP tool — no server operation exists]** | Conceptually: lists global/public Apex classes with at least one `@testSetup` method (the "Apex Test Setup Class" dropdown candidates). **Not onboarded to the MCP server** — no callable tool exists today; do not attempt the call. |
| `flowbuilder_retrieve_silo_records` — **[not available as an MCP tool — no server operation exists]** | Conceptually: previews the records a candidate `@testSetup` class would create inside the test silo (`{orgData, siloData}` — `siloData[<SObject>]` in-silo fixtures, `orgData[<SObject>]` the running user's org records). **Not onboarded to the MCP server** — no callable tool exists today; do not attempt the call. |
| `flowbuilder_get_apex_class_details` — **[not available as an MCP tool — no server operation exists]** | Conceptually: provenance metadata for a single Apex class (`createdBy`, `name`, `namespace`, `methodName`, `apexClassId`, …), powering the "Class details" panel in the Save Flow Test dialog. **Not onboarded to the MCP server** — no callable tool exists today; do not attempt the call. |

---

### Quick rule of thumb

- "Run my flow with these inputs" → `POST /services/data/vXX.0/flowbuilder/flow-test/debug-interview-test-mode`.
  Switch to `POST /services/data/vXX.0/flowbuilder/flow-test/debug-interview` only when the user explicitly asked
  for committed DML AND has confirmed the org host.
- "Save this run" → `POST /services/data/vXX.0/flowbuilder/flow-test` (first save) or `PATCH /services/data/vXX.0/flowbuilder/flow-test/{id}`
  (re-save an existing `320xxx` test); shortcut route:
  `POST /services/data/vXX.0/flowbuilder/flow-test/actions/generate-from-debug-run` → `POST /services/data/vXX.0/flowbuilder/flow-test`.
- "Show me the tests" → `GET /services/data/vXX.0/flowbuilder/flow-test` (paginated, version-scopable — the
  single listing path).
- "Re-run my tests" → `POST /services/data/vXX.0/flowbuilder/flow-test/actions/run`: pass `testIds` for a subset, or omit
  them (set `flowDefinitionId`) to run the whole suite. There is no separate
  coverage path onboarded to Connect today.

---

## Token cost reference

These are the numbers cited throughout this file. They are
measured against a clean dev sandbox; production orgs are larger.

| Path / tool | Approx tokens | Tier |
|---|---|---|
| `GET /services/data/vXX.0/flowbuilder/schema/operator-rules` | ~120K (≈470 KB raw) | 3 |
| `GET /services/data/vXX.0/flowbuilder/platform/entities` | ~30K–90K (≈355 KB max) | 3 |
| `flowbuilder_get_templates` (no Connect path) | ~32K–126K | 3 |
| `GET /services/data/vXX.0/flowbuilder/action/invocable-actions` | ~23K–92K+ (multiple MB unfiltered on integration-rich orgs) | 3 |
| `GET /services/data/vXX.0/flowbuilder/resource/apex-types` | ~15K–80K | 3 |
| `flowbuilder_get_data_cloud_entities` (no Connect path) | ~50K–100K | 3 |
| `GET /services/data/vXX.0/flowbuilder/resource/global-variables` (unscoped) | ~73K | 2 |
| `GET /services/data/vXX.0/flowbuilder/resource/global-variables` (`section=labels`) | ~20K–50K | 2 |
| `GET /services/data/vXX.0/flowbuilder/platform/entity/{apiName}/fields` | ~13K–50K | 2 |
| `GET /services/data/vXX.0/flowbuilder/schema/trigger-types` (detail mode) | ~45K | 2 |
| `GET /services/data/vXX.0/flowbuilder/action/invocable-action-details` | ~10K–38K | 2 |
| `GET /services/data/vXX.0/flowbuilder/flow/subflows` | ~30K | 2 |
| `GET /services/data/vXX.0/flowbuilder/screen-component/{apiName}` | ~5K–10K | 2 |
| `GET /services/data/vXX.0/flowbuilder/schema/flow-capabilities` (composite — all 7 sections) | ~12K+ | 1 |
| Most other paths / tools | <5K | 0 / 1 |

These token costs inform reuse decisions. Before calling any Tier 2-3 path or tool, check conversation history for an existing result with the same `(path or tool, args)` — a single duplicate of a heavy call (30K-120K) can consume the entire context window.

---

## Unregistered tool names (use the alternative)

These names appear in older Flow Builder HARs, training data, and
draft docs, but **the agentic-flow-poc MCP server does not expose
them**. Calling `flowbuilder_<name>` for any of these will fail with
"unknown tool". They are listed here only so the agent stops
hallucinating them; pick the alternative immediately, do not
attempt the call.

| Unregistered name | Why missing | Use instead |
|---|---|---|
| `flowbuilder_get_frequently_used_types` | UI-curated subset, not exposed | `GET /services/data/vXX.0/flowbuilder/schema/process-types` (returns the full canonical set) |
| `flowbuilder_get_modal_templates` | UI-curated subset, not exposed | `flowbuilder_get_templates` (no Connect path; filter client-side) |
| `flowbuilder_get_palette` | UI-only, not exposed | `GET /services/data/vXX.0/flowbuilder/schema/flow-capabilities` (`.elements`) |
| `flowbuilder_get_workflow_enabled_entities` | Not exposed | No exact replacement. `GET /services/data/vXX.0/flowbuilder/platform/entities` proves existence/CRUD capability, not record-trigger eligibility |
| `flowbuilder_get_feature_configurations_for_flow_type` | Redundant, not exposed | `GET /services/data/vXX.0/flowbuilder/schema/flow-capabilities` (`.flowFeatures`) |
| `flowbuilder_get_is_pause_supported` | Single-feature check, not exposed | `GET /services/data/vXX.0/flowbuilder/schema/trigger-types` detail mode `.isPauseSupported` |
| `flowbuilder_get_frp_quick_access` | Not exposed | Hardcode `['Account', 'Contact', 'Opportunity']` |
| `flowbuilder_get_overridable_flows` | Not exposed | `GET /services/data/vXX.0/flowbuilder/flow/{flowDefinitionId}/versions` and check `isOverridable` |
| `flowbuilder_get_action_creation_data` | Not exposed (action builder out of scope) | Ask the user; do not generate |

**Note**: `flowbuilder_get_log_metrics_in_data_cloud_supported` and
`flowbuilder_is_flow_run_setup_in_data_cloud` ARE registered — they
are not in this table. They are lightweight Data Cloud booleans (no Connect
path) the agent may call directly by name.

The authoritative list of no-Connect-path (registered) tools is
`src/tools/register.ts` in this repo. If the live `tools/list` response
disagrees with this file, trust the live response.

---

## Phase 4a drill-down paths

Three new drill-down operations were added for advanced configuration scenarios. Use these AFTER their corresponding discovery calls.

### 1. `GET /services/data/vXX.0/flowbuilder/screen-component/{apiName}` (query: `processType`)

**Purpose**: Get the parameter schema for ONE LWC/Aura screen extension

**Contract**: `apiName` (required, path — the qualified API name of a single component) and `processType` (required, query — the returned schema varies by process type; pass the same value used for the list call). Optional: `builderType`. It is **not batched** — one component per call; there is no `names[]` parameter.

**Use AFTER**: `GET /services/data/vXX.0/flowbuilder/screen-component` (which returns the available extensions for the process type)

**Use when**: Configuring Screen fields with `fieldType='ComponentInstance'`, `'ComponentChoice'`, or `'ComponentMultiChoice'`

**Returns**: Parameter schema for the extension: `{ parameters[], configurationEditor, stylingHooks[] }`

**Token Cost**: ~5-10K per component

**Example workflow**:
```text
1. User: "I want to add a datatable to my screen"
2. Agent calls: dispatch_readonly(method: "GET", url: "/services/data/vXX.0/flowbuilder/screen-component", queryParams: { processType: "Flow" }) → Gets list including 'flowruntime:datatable'
3. Agent calls: dispatch_readonly(method: "GET", url: "/services/data/vXX.0/flowbuilder/screen-component/flowruntime:datatable", queryParams: { processType: "Flow" }) → Gets parameter schema
4. Agent configures: Screen field with correct input/output parameters
```

> **Batch shortcut**: to avoid a per-component call, pass `expand=parameters` on a *filtered* `GET /services/data/vXX.0/flowbuilder/screen-component` call — the list then folds each component's `parameters[]` inline (the same data this path returns). `expand=parameters` requires at least one of `namePattern`/`type`/`limit`; a bare `expand=parameters` returns 400 (guard against expanding every component in the org).

---

### 2. `GET /services/data/vXX.0/flowbuilder/action/invocable-action-generic-type-enum-values`

**Purpose**: Resolve action generic-type placeholders (`U__*`, `T__*`) whose concrete type depends on other input parameter values.

**Prefixes**:
- `U__<name>` — uniform generic (same type used across multiple params).
- `T__<name>` — per-parameter typed placeholder (often used for external-connector request bodies like `T__body`).

Both prefixes resolve through this same path.

**Use AFTER**: `GET /services/data/vXX.0/flowbuilder/action/invocable-action-details` returns a non-empty `genericTypes[]` that has a `typeProvider` field in the values in the array.

**Use when**: Action has generic type placeholders that depend on user's input selections. Required for every `genericTypes[]` entry before save — unresolved `U__*` / `T__*` strings in saved metadata are rejected.

**Required inputs** (matching the Connect OAS contract): `actionType`, `actionName`, `requestedGenericTypes` — a **JSON array of placeholder-name strings** (e.g. `["T__body"]`); the OAS schema is `type: array, items: {type: string}`, so the caller must send an array even for a single placeholder, not a bare string — and `inputParamsJson` — a **JSON-encoded string** whose decoded form is `[{path, value}, ...]` covering every path listed in each placeholder's `typeProviders.dependsOn`. Optional: `processType`, `triggerType`, `builderType` (note: `processType`/`triggerType`, NOT `flowProcessType`/`flowTriggerType`).

**`value` shape inside `inputParamsJson`**: an OBJECT, never a bare string. Use `{stringValue: "..."}` or `{numberValue: 1}` — a **literal**. This path's server-side resolver reads only `stringValue`/`numberValue`; other FEROV variants (`elementReference`, etc.) resolve to null and are dropped, so a type-provider dependency pointed at a variable reference won't resolve. Resolve the driving input to a concrete literal first. Passing a bare string returns `400 Expected object, received string`.

**Returns**: Resolved type descriptors with enumerated values + dependency metadata.

**Token Cost**: ~3-8K per call.

**Example scenario (U__ placeholder)**:
```text
1. Agent calls: dispatch_readonly(method: "GET", url: "/services/data/vXX.0/flowbuilder/action/invocable-action-details", queryParams: { actionType: "component", actionName: "extractDataFromDocument" })
2. Response includes: genericTypes: [{name: 'U__output', typeProviders: {dependsOn: [['documentProcessingConfiguration']]}}]
3. User selects: documentProcessingConfiguration = 'SampleInvoiceConfiguration'
4. Agent calls: dispatch_readonly(method: "GET", url: "/services/data/vXX.0/flowbuilder/action/invocable-action-generic-type-enum-values", queryParams: {
     actionType: 'component',
     actionName: 'extractDataFromDocument',
     requestedGenericTypes: ['U__output'],                        // JSON array of placeholder names (string[])
     inputParamsJson: '[{"path":["documentProcessingConfiguration"],"value":{"stringValue":"SampleInvoiceConfiguration"}}]'  // JSON-encoded string
   })
5. Response: Concrete output type based on selected configuration.
6. Agent emits dataTypeMappings: [{typeName: 'U__output', apexClass: '<resolved>'}] on the action call.
```

**Example scenario (T__ placeholder, External Connector)**:
```text
1. Agent calls: dispatch_readonly(method: "GET", url: "/services/data/vXX.0/flowbuilder/action/invocable-action-details", queryParams: { actionType: "externalConnector", actionName: "JiraV2.createIssue" })
2. Response includes: genericTypes: [{name: 'T__body', superType: 'APEXTYPE',
                       typeProviders: {dependsOn: [['issueType'],['project'],['connection']]}}]
   and parameters[].body.apexClass: 'T__body'
3. User picks: connection='JiraV21leads', project='10000', issueType='10003' (Epic)
4. Agent calls dispatch_readonly(method: "GET", url: "/services/data/vXX.0/flowbuilder/action/invocable-action-generic-type-enum-values", queryParams: {...}) with all three inside `inputParamsJson` (a JSON-encoded string; each value wrapped as {stringValue}), `requestedGenericTypes: ['T__body']` (a JSON array), and `actionType: 'externalConnector'`.
5. Resolved apex class returned, e.g.
     ExternalConnect.JiraV21leads_createIssueMetadataProvidercreatex5f10000x5f10003
6. Agent emits dataTypeMappings: [{typeName: 'T__body', apexClass: '<resolved>'}] on the action call.
```

**Note**: This is required, not optional, when `genericTypes[]` is non-empty. The action will not save otherwise.

---

### 3. flowbuilder_get_connector_details(connectorDeveloperName)

**Purpose**: Get external connector details for HTTP Callout / named-credential integrations

**Controller**: Uses `ExternalConnectivityController` (not FlowBuilderController)

**Use when**: User is configuring HTTP Callout action or named-credential-backed integration

**Returns**: Connector configuration object

**Token Cost**: ~3-5K per connector

**Example workflow**:
```text
1. User: "I want to call an external API using MyConnector"
2. Agent calls: flowbuilder_get_connector_details('MyConnector')
3. Response: Connector configuration (or ERROR if connector doesn't exist)
4. Agent validates: Connector exists and is properly configured
```

**Note**: This tool has a narrower scope than general action lookups (salesforce-flow tool — no Connect path). Use only for external connectors.
