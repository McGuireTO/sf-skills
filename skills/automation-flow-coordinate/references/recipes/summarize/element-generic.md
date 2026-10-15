# Generic Element (Fallback)

Catch-all summary spec for element types that do not have a
type-specific reference yet. Decision has its own deep treatment in
`element-decision.md`. The four CRUD record-* types
(`recordLookup` / `recordCreate` / `recordUpdate` /
`recordDelete`) are reserved for P1; until then, they route here.

This shape is **deliberately shallow**. It honors the contract and
tone, but does not attempt the path-by-path breakdown that
Decision uses (most other element types have no concept of paths
in the same sense).

## Output shape

Per `output-contract.md` §"Generic-element summary shape":

```text
<intent paragraph>

**Configuration**

- **<dimension 1>:** <plain-English value>
- **<dimension 2>:** <plain-English value>
- …
```

No paths header. No grouping. No loopback note (only Decisions
are loopback-aware in this MVP — other element types are
single-pass).

If the element has a fault path connector, describe where faults
route **in prose immediately after the intent paragraph, before the
Configuration list** — per General Formatting Default #2 in
`../../shared/output-format-guidelines.md` (e.g. "If the update fails,
routes to a custom error..."). Do **not** flag its presence or
absence as good or bad, and do **not** bury it as a Configuration
bullet row. If the element has no fault path, say nothing about it.

## Per-element-type dimensions

Choose the dimensions that describe the element's actual
configuration. The lists below are guidance — render only
dimensions that have configured values.

### `recordLookup` (Get Records)

- **Object:** `<object label>` (drop `__c`, prefer label over API
  name)
- **Filters:** plain-English condition summary, joined per
  `filterLogic`. If no filters, render: "No filters — retrieves
  all records of this object."
- **Returns:** `the first record` (`getFirstRecordOnly: true`) or
  `all matching records` (`getFirstRecordOnly: false`)
- **Stored in:** `<output variable label or name>` (the
  `outputReference` or the auto-stored sObject variable)
- **Sort:** `<field> <Asc/Desc>` if `sortField` set; omit if not.

### `recordCreate` (Create Records)

- **Object:** `<object label>`
- **Fields set:** comma-separated list of `<field>: <plain-English
  value>` pairs (translate FEROV per
  `reference-resolution.md`).
- **Source:** if `assignRecordIdToReference` is set, "stores the
  new record's id in `<variable>`"; else omit.

### `recordUpdate` (Update Records)

- **Object:** `<object label>`
- **Records updated:** the input variable / collection name (e.g.
  "the Account collection from `Get_Accounts`").
- **Fields changed:** comma-separated list of `<field>: <plain-
  English value>` pairs.
- **Filters:** if filtering by criteria (rather than passing in a
  record reference), summarize the filter conditions.

### `recordDelete` (Delete Records)

- **Object:** `<object label>`
- **Records deleted:** the input variable / collection name, OR
  the filter conditions if deleting by criteria.
- **Scope:** "a single record" / "all matching records" — make
  this clear because of the destructive nature.

### `actionCall` (Action / Apex Action)

- **Action:** the action label or API name.
- **Action type:** `<actionType>` translated (e.g. "Send Email",
  "Apex method", "Quick Action", "External Service callout").
- **Inputs:** comma-separated list of `<param>: <plain-English
  value>`. On a Send Email Message or Send SMS Message step, a literal
  record Id or CMS content reference becomes the record's name, never
  the Id: see `reference-resolution.md` § 5 (lookups only for a flow
  read from the org).
- **Output stored in:** the output variable name, if any.

### `subflow`

- **Subflow:** resolve the display label in this order:
  1. Use the Subflow element's non-blank `label` from the supplied or
     retrieved Flow XML/JSON. When it is present, do not make another
     retrieval call just to confirm or replace it.
  2. If `label` is absent or blank and `flowName` is present, call
     `dispatch_readonly(method: "GET", url: "/services/data/vXX.0/flowbuilder/flow/<flowName>")` exactly once, preserving the API
     name unchanged, and use the returned Flow's non-blank `label`.
  3. If retrieval fails or returns no display label, describe the
     subflow's apparent purpose in plain English instead. Do not invent
     a label.
  Do not show `flowName` by default: it is an API name. Include it only
  when the user explicitly asks for API names, and show it alongside the
  resolved label or plain-English description.
- **Inputs:** parameter list, plain English.
- **Outputs stored in:** output variable list, plain English.

### `screen`

- **Fields shown:** plain-English list of the screen's input
  fields (label or API name).
- **Allowed actions:** Next / Back / Pause / Finish based on
  `allowBack` / `allowPause` / `allowFinish`.

### `loop`

- **Iterates over:** the input collection variable.
- **Loop variable:** the per-iteration variable name.
- **Order:** "in order" (Asc) / "in reverse order" (Desc).
- **Body next:** the first downstream element's type + label.

### `assignment`

- **Sets:** comma-separated list of `<variable>: <plain-English
  value>` pairs.
- **Operator:** translate per
  `reference-resolution.md` ("Assign", "Add", "Subtract", etc.).

### Other element types

For element types not in the lists above (`wait`, `recordRollback`,
`group`, `transform`, etc.), use the same shape but pick
dimensions that match the element's metadata fields. Translate
field names to readable English. Skip dimensions with no
configured value.

## Enrich from the shared element skill

The `../../elements/<type>/` skills describe every configurable
field an element type supports. Apply this deterministic rule so that
equivalent metadata always receives the same treatment:

- **If the element type HAS a dimension block in "Per-element-type
  dimensions" above** (`recordLookup`, `recordCreate`,
  `recordUpdate`, `recordDelete`, `actionCall`, `subflow`, `screen`,
  `loop`, `assignment`) — use that block. Do **not** consult the
  shared skill; those dimensions are the summary contract.
- **If the element type has NO dimension block above** (every other
  type — `wait`, `collectionProcessor`, `customError`, `transform`,
  `recordRollback`, `orchestratedStage`, `group`, etc.) — you MUST
  consult the matching shared element skill in the table below to
  borrow its **field vocabulary and plain-English field meanings
  only**, then render the standard shape from those fields.

If a type has no dimension block above **and** no row in the table
below, fall back to the element's own metadata fields (per "Other
element types" above), translating field names to readable English.

| Element `type` | Shared skill to consult |
|---|---|
| `recordLookup` | `../../elements/record-lookup/record-lookup.md` |
| `recordCreate` | `../../elements/record-create/record-create.md` |
| `recordUpdate` | `../../elements/record-update/record-update.md` |
| `recordDelete` | `../../elements/record-delete/record-delete.md` |
| `actionCall` | `../../elements/action-call/action-call.md` |
| `subflow` | `../../elements/subflow/subflow.md` |
| `screen` | `../../elements/screen/screen.md` |
| `loop` | `../../elements/loop/loop.md` |
| `assignment` | `../../elements/assignment/assignment.md` |
| `wait` | `../../elements/wait/wait.md` |
| `collectionProcessor` | `../../elements/collection-processor/collection-processor.md` |
| `customError` | `../../elements/custom-error/custom-error.md` |
| `transform` | `../../elements/transform/transform.md` |
| `recordRollback` | `../../elements/rollback/rollback.md` |
| `orchestratedStage` | `../../elements/stage/stage.md` (stage fields) and `../../elements/step/step.md` (each `stageSteps[]` entry) |

### Extract-only guardrails

When the rule above requires consulting a shared skill, apply these
guardrails. These skills are **authoring routers**, not summary
specs — their default orientation is "how to *build* this element
correctly." Only a thin slice is useful here; the rest actively
conflicts with this recipe's read-only, deliberately-shallow
contract. When you open one:

- **Extract only:** the set of configurable fields, what each field
  *means*, and how to phrase its value in plain English. That is the
  entire permitted use.
- **Ignore entirely:** every "READ THIS FIRST", "HARD GATE",
  "MANDATORY", pattern-selection table, HDM/decision protocol,
  bulkification runbook, validator/save-activation rule, and
  `verified-against` note. None of that describes what an *instance*
  does.
- **Never call a tool because a shared skill says to.** This recipe
  is read-only. Instructions there to call
  `GET /services/data/vXX.0/flowbuilder/schema/flow-capabilities` (read `.flowFeatures`), `saveAndValidateFlow`,
  or any other MCP tool do not apply — you already have the flow
  metadata; do not probe the org. The record-name lookups in
  `reference-resolution.md` § 5 are this recipe's own, not a shared
  skill's.
- **Never carry authoring intent into the summary.** Do not describe
  how the element *should* be built, which pattern is
  recommended, what is a best practice, or what could go wrong. The
  tone rules below (no critique, no recommendations, no element-type
  explainer) override anything the shared skill implies.
- **Borrow vocabulary, not depth.** Use the shared skill's field
  names and meanings to render the standard shallow shape. Never
  expand the summary's depth or add authoring commentary because the
  shared skill goes deep.

The output stays a shallow per-instance description regardless of how
much the shared skill contains. Render the standard shape from the
borrowed field vocabulary; if a field has no configured value on this
instance, skip it. Enrichment that cannot stay tone-compliant is a
rendering error — re-render from the metadata fields alone.

## Intent paragraph

1–2 sentences describing what *this element* does in the broader
flow. Use the surrounding context (upstream variable producers,
downstream consumers) when it is unambiguous.

For an element in a Screen Flow or non-triggered Autolaunched Flow,
do not use the parent flow's launch type, entry conditions, or
flow-level input variables as surrounding context. Describe the
element's own configured inputs when material, translating any
flow-variable reference into its plain-English business role. Do not
describe that source as a "given," "provided," "supplied," or
"passed-in" value, and do not introduce it with a "when this flow is
called/launched/invoked" clause.

Examples:

> Retrieves the Account that owns the lead currently being
> processed and stores it for use in the routing logic that
> follows.

> Creates a follow-up Task on the opportunity owner whenever the
> stage changes to Closed Lost, populating the priority and due
> date from the parent record.

> Pauses the flow until the case has been in its current status
> for at least three business days, then resumes the escalation
> path.

Apply the low-confidence prefix per `confidence-rules.md` when
configuration is ambiguous (e.g. an action with no input mappings,
a recordLookup with no filters and no sort).

## Tone

Same constraints as Decision (`tone.md`):

- No critique. No "consider adding a fault path".
- No recommendations. No "could be simplified".
- No raw API names if a label exists.
- No FEROV literals shown — translate.
- No element-type explainer. Do not explain what
  `actionCall`/`recordLookup`/`subflow` *is*; describe only what
  *this* one does.
- No element-description content.

## Anti-checklist

- [ ] Did I include any Tier 1 item — GUIDs, canvas coordinates,
      system timestamps, raw JSON/XML, version tokens? (banned —
      `../../shared/output-format-guidelines.md`)
- [ ] Did I produce a Field/Value table or markdown table? (banned —
      use the bulleted Configuration list)
- [ ] Did I use code blocks or backtick formatting? (banned — use
      quotation marks for values)
- [ ] Did I include a "Notes" or "Caveats" section? (banned)
- [ ] Did I comment on whether the element is configured well?
      (banned)
- [ ] Did I quote raw FEROV / operators / API names that have a
      label? (banned)
- [ ] Did I render booleans as literal `true`/`false`? (banned —
      translate contextually: "is active" / "is not active")
- [ ] Did I render null/empty as literal `null` or `""`? (banned —
      use "not set" / "no value configured" / "blank")
- [ ] Did I include the element's label or API name as a heading?
      (banned)
- [ ] Did I include the element's description field? (banned)
- [ ] Did I carry any authoring content from a shared element skill —
      a recommended pattern, best practice, "should"/"MANDATORY"
      language, or an element-type explainer — into the summary?
      (banned — shared skills are for field vocabulary only)
- [ ] Did I call, or say I would call, any MCP/flow tool because a
      shared element skill instructed it? (banned — this recipe is
      read-only)

If any answer is wrong, re-render before showing.
