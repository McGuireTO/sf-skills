---
name: flow-recipe-summarize
license: LICENSE.txt has complete terms
description: "Use this skill to summarize a Salesforce Flow or any of its elements in plain English using the flow MCP. TRIGGER when: user says 'summarize this flow', 'summarize the X element', 'summarize Decision_1', 'what does this flow do', 'what does the [Element] do', 'explain Get_Account', 'walk me through Decision_1', 'break down the routing logic', 'I don't understand what this decision is doing', 'tell me what the [Element] does', or pastes Flow JSON, Salesforce Metadata API XML, or element JSON and asks for an explanation. Also TRIGGER for API-name and durable-version references like 'summarize Is_VIP' or 'summarize SvcCopilotTmpl__AddCaseComment-1'. DO NOT TRIGGER when: building or editing a flow (use flow-recipe-author), running tests (use flow-recipe-testing), or asking how a flow element type works in general (e.g. 'what is a Decision element' is a Salesforce-docs question, not a per-instance summary)."
metadata:
  version: "2.0"
  related-skills: flow-recipe-author, flow-recipe-testing
id: flow.recipes.summarize
requires:
  - flow.shared.output-format-guidelines
  - flow.shared.flow-properties
---

# Flow & Element Summarization

Plain-English explanation of what a Salesforce Flow or one of its
elements does. **Decision** elements get the full PRD-level treatment
(intent + path-by-path breakdown + grouping + loopback notes). All
other element types get a tone-compliant shallow summary via the
generic fallback. Whole-flow summaries roll up the high-level path
skeleton and include start context only when Flow Builder exposes
start configuration for that flow type.

This recipe is **read-only**. It never writes, saves, activates,
deactivates, or modifies a flow. It produces summary content only.

## Read before you render (mandatory)

This recipe is an index, not the full specification. The rules that shape the
output live in the referenced files, not in this file. The Hard Constraints
below are a safety net, not a substitute. Before producing any summary, open
and read these files during the current turn:

- `../../shared/output-format-guidelines.md` — always. Resolve this path from
  this recipe's directory; it points to the shared guidance under
  `references/shared/`.
- `output-contract.md` — always.
- `display.md` — always; select its matching view only after the
  summary content passes the gates below. Determines whether output
  is a tool call or plain Markdown based on the tool list.
- `tone.md` — always.
- The dispatch file for the requested summary:
  - Whole flow → `flow-overall.md`.
  - Decision element → `element-decision.md`.
  - Any other element → `element-generic.md`.
- `reference-resolution.md` § 5 — when the flow was read from the org
  and a step you describe has a record Id or CMS content reference in
  its inputs (a send's sender, consent subscription, or content).

Do not render from this recipe's inline instructions alone. Use the retrieved
or provided Flow metadata as the source of facts, then apply the referenced
files as the rendering contract. If the required files have not been opened
and read during the current turn, open them before drafting the summary.

## Goal

Given a FlowVersion id (`301xxx…`), a FlowDefinition id (`300xxx…`), a custom
Flow API name, a standard Flow's namespaced durable version id, or a complete
Flow definition as Flow JSON or Salesforce Metadata API XML, produce summary
content that:

1. Complies with `../../shared/output-format-guidelines.md` — the
   cross-cutting suppression tiers, data-value translations, and
   formatting defaults that apply to ALL element summaries.
2. Conforms to the **output structure** in `output-contract.md`.
3. Uses the deterministic render-tool or Markdown branch in
   `display.md`.
4. Obeys the **tone constraints** in `tone.md` (no critique, no
   recommendations, no jargon, no raw FEROV syntax).
5. Applies the **confidence prefix** rules in `confidence-rules.md`.
6. Applies the **grouping rules** in `grouping.md` when a Decision has
   13 or more paths.
7. Handles the **edge cases** in `edge-cases.md` (empty conditions,
   invalid values, missing downstream, etc.).

If the output you are about to produce violates any of these, stop
and re-render before showing it to the user.

## When to Use This Skill

Trigger on any of these phrasings (the description carries more —
this is the short list):

- "Summarize this flow" / "Summarize the [Element] decision" /
  "Summarize Decision_1" / "Summarize Is_VIP".
- "What does this flow do?" / "What does this decision do?" / "What
  does Get_Account do?".
- "Explain this flow" / "Explain Get_Account".
- "Walk me through Decision_1" / "Break down the routing logic for
  me" / "I don't understand what this decision is doing".
- User pastes element JSON or flow JSON and asks for a summary.

**Do not** trigger when:

- The user is creating or editing a flow (route to `flow-recipe-author`).
- The user is testing/debugging a flow (route to
  `flow-recipe-testing`).
- The user is asking "what is a Decision element" in general — that
  is a docs question about the *type*, not a summary of an
  *instance*. Defer to Salesforce documentation.

## Routing

Six steps, in order. Do not skip step 1.

### Step 1 — Resolve the available summary context

Whole-flow context is preferred because it enables downstream-element
labels, formula expressions, FEROV references, and loopback detection.
An element-only definition is still valid input; summarize it with the
documented low-confidence limitations. See `reference-resolution.md`
for the full ladder. Short version:

| Input you have | What to do |
|---|---|
| `301xxx…` (FlowVersion id) | Call `dispatch_readonly(method: "GET", url: "/services/data/vXX.0/flowbuilder/flow/<id>")` directly. |
| `300xxx…` (FlowDefinition id) | Call `dispatch_readonly(method: "GET", url: "/services/data/vXX.0/flowbuilder/flow/<id>")` directly. The tool resolves the Active version, or the latest version when none is Active; do not make a separate version-list call. |
| Custom Flow API name (e.g. `Lead_Routing` or `acme__Lead_Routing`) | Call `dispatch_readonly(method: "GET", url: "/services/data/vXX.0/flowbuilder/flow/<id>")` with the exact API name. The tool resolves the Active version, or the latest version when none is Active. Do not translate labels, add/remove a namespace, or make a separate version-list call. |
| Standard Flow namespaced durable version id (e.g. `SvcCopilotTmpl__AddCaseComment-1`) | Call `dispatch_readonly(method: "GET", url: "/services/data/vXX.0/flowbuilder/flow/<id>")` with the exact durable id. The `-N` suffix selects that standard Flow version. |
| Flow label (e.g. `Lead Routing`) | A label is not a supported `GET /services/data/vXX.0/flowbuilder/flow/{id}` identifier. Ask for the exact API name, a `301xxx…` FlowVersion id, or the complete Flow definition as Flow JSON or Salesforce Metadata API XML. Do not convert spaces to underscores or otherwise guess an API name. |
| Element definition pasted as Flow JSON or Salesforce Metadata API XML, no flow context | Summarize from the element only and apply the low-confidence prefix; loopback and downstream labels will be unresolved |
| Complete Flow definition pasted as Flow JSON or Salesforce Metadata API XML | Use directly for read-only summarization; no MCP call needed |

If resolution fails (no metadata returned, session expired, or the referenced
flow does not exist), stop and report the failure plainly. Ask the user to
provide one of these supported inputs:

1. The exact custom Flow API name, including its namespace when applicable.
2. The standard Flow's namespaced durable version id, including its `-N`
   version suffix.
3. The FlowVersion id (the `301…` id) or FlowDefinition id (the `300…` id).
4. The complete Flow definition as either Flow JSON or Salesforce Metadata API
   XML.

Metadata API XML is accepted as read-only summarization input only. Do not pass
XML to save operations, which require the Flow MCP JSON schema.
Never invent metadata.

### Step 2 — Decide flow vs. element

- User asked about **the flow as a whole** ("summarize this flow",
  "what does this flow do") → open and read `flow-overall.md`, then
  render to its contract. Do not free-form the summary directly from
  the Flow metadata retrieved in step 1.
- User named **a single element** ("summarize Decision_1", "what does
  Get_Account do") → continue to step 3.
- User pasted **a single element JSON** with no broader request →
  continue to step 3.
- Ambiguous (multiple Decisions exist and user said "summarize the
  decision") → ask one disambiguation question. Do not guess.

### Step 3 — Locate the target element

Find it by `name` (API name) first, then `label`. If multiple
elements share the same label, ask which one the user meant. If no
match, say so and list the element names that *do* exist.

### Step 4 — Dispatch by element type

| Element `type` in metadata | Reference to load |
|---|---|
| `Decision` | `element-decision.md` (full PRD treatment) |
| any other type | `element-generic.md` (shallow but tone-compliant) |

Open and read the dispatched file before rendering. The inline Hard
Constraints below are not a substitute for its complete contract.

`element-record-lookup.md`, `element-record-create.md`,
`element-record-update.md`, `element-record-delete.md` are reserved
for P1 — they do not exist yet. Until they do, CRUD elements route
to `element-generic.md`.

### Step 5 — Build and validate summary content

Apply, in order:

1. Remove every Flow-level and element-level `description` field from
   the facts available for drafting. Derive intent only from configured
   Start behavior, elements, connectors, conditions, assignments, and
   values. If an intent clause cannot be traced to that configuration,
   delete it. Do not name an actor, persona, caller, or beneficiary (for
   example, a customer, agent, or administrator) unless that role is
   explicitly represented by a configured Screen, action, condition, or
   record relationship.
2. For a Screen Flow or non-triggered Autolaunched Flow, remove all
   `variables[]` entries with `isInput: true` from the summary input
   before interpreting references. When an element references one of
   those variables, resolve only the target's business role from the
   element/object context (for example, "the case being handled");
   never reveal the variable, its value, its source, or invocation
   context. In the final draft, replace any source-implying use of
   "given," "provided," "supplied," "passed-in," or "input" with the
   value's business noun, such as "the comment text."
3. The suppression tiers from `../../shared/output-format-guidelines.md`
   (Tier 1 items removed unconditionally; Tier 2 items translated;
   data values humanized; formatting defaults enforced).
4. The shape from `output-contract.md`.
5. The grouping rules from `grouping.md` (Decision only, when path
   count ≥ 13).
6. The confidence prefix from `confidence-rules.md`.
7. The tone constraints from `tone.md` — read this last, because it
   is also the gate that blocks output.

Cross-check the rendered output against the closest example in
`examples/`. If your output diverges materially from every example,
something is wrong with the rendering — fix before showing.

When a render tool will be used, apply this example gate to the text
inside `detailedSummary` and `shortSummary`, not to the tool-call
envelope.

### Step 6 — Deliver

Open `display.md` and use exactly one matching view:

- Whole-flow summary → `display.md` §"summarize-flow".
- Single-element summary → `display.md` §"summarize-element".

The view's guarded rules decide tool call vs. plain Markdown.

### Before you show the output (gate)

Confirm every item below is true. If any item is false, stop and fix it:

- You opened and read `../../shared/output-format-guidelines.md`,
  `output-contract.md`, `display.md`, and `tone.md` during the current
  turn.
- You opened and read the dispatch file for this request
  (`flow-overall.md`, `element-decision.md`, or `element-generic.md`) and
  rendered to its contract.
- You checked the tool list for the current turn against `display.md`
  and chose the matching view per its guarded rules.
- The summary content matches the closest applicable file in
  `examples/`. In tool-call mode, check the summary parameter values
  rather than the tool envelope.

If the draft was produced from this recipe's inline instructions without
opening those files, discard it and re-render from the referenced contracts.

## Hard Constraints

These are violations that automatically reject the output. Each is
expanded with reasoning in `tone.md` and
`../../shared/output-format-guidelines.md`.

Exception: **if a matching tool is in the tool list** for this
summary type, call it instead of emitting plain text. See `display.md`
for the guarded views, parameter contract, schema compatibility, and
the plain-Markdown fallback used when no such tool is present or a
call fails. The tool call itself is not a violation of the constraints
below — but they still apply in full to the text inside each parameter
value.

Tools are an internal detail of how the recipe produces output.
Never name a tool, name its parameters, state which branch (tool
call or plain text) was taken, or narrate the detection step — in
either branch. Never emit a preamble, framing sentence, or
disclaimer before the summary. The first character of the response
is the first character of the summary. Return the summary, not an
account of producing it.

- **Tier 1 suppression (unconditional).** Never show GUIDs/UUIDs,
  canvas coordinates (x/y), internal system timestamps
  (SystemModstamp, LastModifiedById), raw JSON/XML payloads, or
  Salesforce version tokens/etags. If a user asks for one, politely
  note it's not useful and offer to summarize instead.
- **No critiques.** Never write "consider", "should", "may want to",
  "appears unreachable", "largely unreachable in practice", "is
  fine", "no error, no log, no fault", or any other evaluative
  language. State what the configuration *does*, not whether it is
  good.
- **No recommendations.** Do not propose changes, alternatives, or
  improvements.
- **No raw condition syntax.** `StageName == "Closed Won"` becomes
  "Stage is Closed Won". If the user explicitly asks for raw syntax,
  show it alongside (never instead of) the plain-English
  translation.
- **No FEROV literals shown.** A `booleanValue: false` or
  `numberValue: 100000` is rendered as plain English ("is not
  active", "exceeds $100,000"). Booleans are rendered contextually
  ("is active" / "is not active", "is checked" / "is unchecked") —
  never literal `true`/`false`.
- **No element-type explainer.** Do not explain what a Decision
  element *is* in general; describe only what *this* one does.
- **No description-field content.** Flow and element descriptions are
  excluded from input (PRD §2.2 footnote — descriptions are
  frequently stale and unreliable).
- **No markdown tables in output.** Use bullet lists. Tables are
  acceptable only if the user explicitly requests a comparison or
  table layout.
- **No code blocks or backtick formatting.** Write values in plain
  text with quotation marks (e.g., Stage is "Closed Won").
  Acceptable only if user explicitly asks for code output.
- **Null/empty → human text.** Render as "not set," "no value
  configured," or "blank." Never write `null`, `""`, or similar
  literally.
- **No inapplicable start context.** For Screen Flows and
  non-triggered Autolaunched Flows, never summarize the trigger or
  launch type, entry conditions, or flow-level input variables. Do
  not render empty-state statements for them and do not move them
  into the intent or path text. See
  `../../shared/output-format-guidelines.md` §"Flow-Type Start-Context
  Suppression."
- **Default path is always the final bullet** in a path list, and
  labeled as the fallback for "all other cases" / "records that
  don't match any of the above conditions".

## Reference Index

| File | When to consult |
|---|---|
| `../../shared/output-format-guidelines.md` | Every render — suppression tiers, data translations, formatting defaults |
| `output-contract.md` | Every render — defines output structure |
| `display.md` | Every render — selects the tool call or Markdown fallback |
| `tone.md` | Every render — defines what cannot appear |
| `confidence-rules.md` | When deciding to prefix with "It appears that" |
| `grouping.md` | Decision with 13+ paths |
| `edge-cases.md` | Empty/invalid conditions, missing downstream, duplicate logic |
| `reference-resolution.md` | Translating ids, FEROVs, formulas, downstream labels |
| `element-decision.md` | Element type = Decision (MVP) |
| `element-generic.md` | Any non-Decision element type |
| `flow-overall.md` | Whole-flow summary requests |
| `examples/*.md` | Quality-bar reference; cross-check final output |
