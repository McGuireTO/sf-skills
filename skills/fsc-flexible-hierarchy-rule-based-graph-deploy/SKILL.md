---
name: fsc-flexible-hierarchy-rule-based-graph-deploy
description: "Build and deploy a Rule-Based Flexible Hierarchy graph config as a `RelationshipGraphDefinition` MDAPI component — same nodeList/relationshipList capture as the bespoke sub-skill, captured up front, plus a `rules.graph.rootNode` recursive rule tree (role, filter criteria, OneToMany/ManyToMany child relationships) that drives automatic hierarchy expansion and reuses those pre-captured relationships wherever an edge needs a junction. First ask whether the admin has a config, then either take an admin-supplied config as-is (Path A) or build the node list, the node relationships, and the rule tree with them in that order (Path B), confirm right before the deploy, then create it via MDAPI deploy and read back. Invoked from the fsc-flexible-hierarchy-configure foundation skill's hierarchy-type step (Step 9) only when the admin has `enableRuleBasedHierarchyPref` on and chose Rule-Based Configuration over Bespoke Configuration."
metadata:
  relatedSkills:
  - fsc-flexible-hierarchy-configure
  version: "1.0"
  cliTools:
  - tool:
    - "sf"
    semver: ">=2.0.0"
---

# Create a Rule-Based Hierarchy Config

The **Rule-Based** branch of the hierarchy-type step (**Step 9**) of the
[`fsc-flexible-hierarchy-configure`](../../../SKILL.md) foundation skill (see
[`../foundation-configure/SKILL.md`](../foundation-configure/SKILL.md)). Step 9 delegates here
**only when** `rule_based_pref_state` is `already-on` or `enabled` **and** the admin picked
**Rule Based Configuration** at the modality question — never unconditionally. The sibling
[`../graph-config-create/SKILL.md`](../graph-config-create/SKILL.md) remains the **only** path when
the admin picks Bespoke Configuration, or when the Rule-Based preference isn't on; it is unchanged
by this skill's existence.

## Sequencing — one question at a time, never batch

This skill is multi-turn: the Path A/B branch, the node list, the node relationships, the rule
tree, and the pre-deploy confirm are each their own turn. Ask **only the current question**, wait
for the answer, then move on — **never bundle a later question into the same message as an
earlier one, and never collect several answers up front.** This applies in full even if you're
serving this skill directly rather than being routed here from the foundation skill.

A hierarchy type is still a single **`RelationshipGraphDefinition`** metadata component — same
deployable MDAPI type (`metadataApiName="RelationshipGraphDefinition"`, `manageable`,
`keyPrefix="06J"`), same **create-only** rule (never an update), and the **same transport** as the
bespoke sub-skill: creation is not supported through the generic `/headless/metadata` facet (its PUT
is update-only for this type and 400s with `INVALID_CROSS_REFERENCE_KEY` against a `DeveloperName`
that doesn't exist yet). **Create it via the raw Metadata API (mdapi package + SOAP deploy)** —
route this through `/headless/metadata`, which wraps that raw-MDAPI create path — against a
`relationshipGraphDefinitions/<DeveloperName>.relationshipGraphDefinition-meta.xml` component — **not**
the Tooling API POST create, which is unreliable for `GraphType: "FlexibleHierarchy"` (confirmed
against a live org: 5+ identical retries failed with `INVALID_FIELD_FOR_INSERT_UPDATE` on `GraphType`,
while the Setup UI and an MDAPI deploy of the identical payload both succeeded). What's different from
the bespoke
sub-skill is **only the shape of the `graphDefinition` JSON inside `relationshipGraphDefVersions`** —
it carries an additional `rules` block beside `nodeList`/`relationshipList`/`summaryRollupList`. See
[`references/rule-based-hierarchy-payload.md`](references/rule-based-hierarchy-payload.md) for the
full schema, grounding, and a validated example.

## Grounding note — read before using this skill

This sub-skill's payload schema is grounded in **one admin-provided sample config** (a
`RelationshipGraphDefinition` for a "Distribution Network Hierarchy") **plus two independent live
build-from-scratch create + re-retrieve runs against a live org** — this skill's own three-level
Account→Account→Contact rule tree, and an admin's independently UI-built rule tree captured in the
same session. The **node/edge/filter shape** is now solidly grounded by two independent live builds,
not just the one sample. The **transport is not uniformly solid**:
`FullName`/`Metadata` shape and create-only are confirmed, but **Tooling API POST create fails
reliably for `GraphType: "FlexibleHierarchy"`** (5+ identical retries, `INVALID_FIELD_FOR_INSERT_UPDATE`
on `GraphType`) —
MDAPI deploy is the transport that actually works; see the intro above. Everything about
the **`rules` tree's contents** still being refined (any `operator` beyond `gt`/`lt`/`eq`/inferred
`ne`, any `whichEntity` value beyond `TARGET`) is inferred and **not yet confirmed against a live
deploy**. Treat the fields documented in the reference as grounded up to the point noted there, not as
an exhaustively validated schema — if a live deploy of a built-from-scratch config fails, that's new
grounding to fold back into the reference (per this skill family's "a deploy result can lie, always
re-read/re-verify" discipline), not a sign to silently guess around it.

## Prerequisites (established by the foundation skill before delegating here)

Same as [`../graph-config-create/SKILL.md`](../graph-config-create/SKILL.md)'s prerequisites — FSC +
ARC enabled, Flexible Hierarchies feature preference on — **plus** `enableRuleBasedHierarchyPref`
confirmed on (`rule_based_pref_state` is `already-on` or `enabled`). Step 9 verifies this gate before
ever offering the Rule Based Configuration option; this sub-skill doesn't re-check it.

## Free-text vs. multiple-choice inputs — same discipline as the bespoke sub-skill

Every free-text-vs-picker rule in
[`../graph-config-create/SKILL.md`](../graph-config-create/SKILL.md#free-text-inputs-must-use-a-real-text-prompt--never-a-fixed-option-picker)
applies here unchanged: name, root object, other node objects, and any "enter my own" escape are real
free-text prompts, never a fixed-option picker with a dead "type your own" option. The new rule-tree
inputs below extend this the same way — **filter value** is free-text; **operator** and
**whichEntity** are multiple-choice over a known, finite set. **Relationship kind
(OneToMany/ManyToMany)** is conditional, not always a two-option picker: it's multiple-choice only
when a `relationshipList` entry already exists for the current node pair (captured in Path B step
2, before the tree) — otherwise the question is skipped entirely and One-to-many is used, since
there's no captured junction to offer as the Many-to-many option (see "Child relationships" under
"Building the rule tree"). **Role** is conditional on the org's configured `FlexibleHierarchyNodeRole`
values — see "Checking configured roles" at the top of "Building the rule tree" below — free-text
only when the org has none configured.

## First ask: do you have a hierarchy config to deploy, or should I build one?

Ask the identical Yes/No fork the bespoke sub-skill asks, just naming the rule-based shape:

> Do you already have a Rule-Based hierarchy config ready to deploy?
> - **Yes** — paste your full config (the `graphDefinition` JSON or full `RelationshipGraphDefinition`
>   XML, including the `rules` block) and I'll deploy it as-is (I'll validate the root object and
>   every object named in the rule tree exists in the org, and read the label).
> - **No** — I'll build one with you: the node objects and display fields (same as a bespoke config),
>   then the relationships connecting them, then the rule tree (role, qualifying filters, and child
>   relationships) that drives automatic hierarchy expansion.

**Do not skip this and present a build summary (developer name, label, root object, node roles)
before asking it and getting an answer.** Confirmed live: a run jumped straight to a deploy summary
with invented values (e.g. assuming `Account` as root, inventing a developer name) without ever
asking this question. If you find yourself describing field values for this hierarchy type before
this question has been asked and answered, stop and ask it now.

### Path A — the admin brings a config

Take it as-is — don't silently rewrite their node/rule choices. Reconcile only the essentials:

- **Read the name from the config's own `masterLabel`** — don't ask for a name separately; echo it
  back and let the admin correct it if wrong.
- **Confirm the root object** (`graph.rootNode.object.entity`) exists in the org — standard or
  custom — via describe/`EntityDefinition`, same as the bespoke path.
- **Confirm every object named inside the `rules.graph.rootNode` tree** — every `object.entity` at
  every depth, plus every `junctionObject.entity` on a `ManyToMany` edge — exists in the org. A rule
  tree can reference deeper/more objects than the flat `nodeList`; validate the tree's objects
  independently, don't assume they're a subset of `nodeList`.
- **Strip the duplicate `flexibleHierarchy` block if present** — see the Pitfall below. A real
  admin-provided sample carried the *entire* `nodeList`/`rules`/`relationshipList`/`summaryRollupList`
  content twice as two sibling `"flexibleHierarchy"` keys inside `globalUiConfig` (a paste artifact);
  keep exactly one.
- **Don't drop or rebuild `relationshipList`.** A rule-based config still carries the flat
  `relationshipList[]` the bespoke config uses — for every `ManyToMany` edge in the rule tree, the
  matching junction pair should also appear once in `relationshipList` (see "Node relationships" in
  Path B below for what a well-formed entry looks like). Take the admin's own `relationshipList` as
  given on this path; don't regenerate it from the rule tree unless they ask you to fix a mismatch.

### Path B — build it from scratch

Building a rule-based config from scratch is **three layers**, done in order:

1. **The node list and display config** — identical to the bespoke sub-skill's Path B, steps for
   name/`DeveloperName` uniqueness check, the reusable-template ask (`isTemplate` — optional,
   defaults to `false` if skipped), root object, other node objects, and per-object
   `graphViewFields`/`gridViewFields`/`nameField`/`showRelatedContacts` (the picker + free-text
   follow-up, the graph-view 2-field cap, the self-object-prefix normalization, the field validation
   against live describe). **This step delegates to the sibling sub-skill's own SOR — not a
   repo-relative file link, which a served SOR consumer cannot resolve:**
   **`delegates_to: fsc-darksaber/fsc-flexible-hierarchy-configure-graph-config-create`**. Call
   `describe("fsc-darksaber/fsc-flexible-hierarchy-configure-graph-config-create")` and follow its
   Path B node-list/display-field flow exactly (the wording lives there, not repeated here, so the
   two copies can't drift). The result is the same `nodeList[]` a bespoke config has.
2. **Node relationships (`relationshipList`)** — capture this now, **before** the rule tree, not
   derived from it afterward. Continue following the same delegated sub-skill's flow into its
   node-relationship capture step — the standalone opt-in walk that asks, per pair the admin wants
   connected: parent object, child object, junction object, the junction's lookup field to the
   parent, the junction's lookup field to the child, and the junction's title/name field (the same
   six-question capture the bespoke sub-skill uses). Every pair captured here becomes a
   `relationshipList[]` entry, exactly as in a bespoke config. **This list is what gates which edge
   types the rule tree (step 3) can offer for a given node pair** — see "Child relationships" below.
3. **The rule tree** — new to this sub-skill. This is the `rules.graph.rootNode` object described
   below, which layers automatic-expansion rules (role labels, qualifying filters, and
   parent→child traversal) on top of the node list, reusing the relationships captured in step 2
   wherever a rule edge needs a junction.

**Node-relationship capture now happens up front (step 2 above) — this reverses this skill's
earlier documented behavior, which derived `relationshipList` from the `ManyToMany` edges captured
mid-tree-walk.** The rule tree (step 3) now **reads** `relationshipList` rather than **writing** it:
a parent→child pair can only offer **Many-to-many** in the rule tree if a `relationshipList` entry
for that exact pair already exists from step 2; every other pair only offers **One-to-many**. See
"Child relationships" below for exactly how that gate works.

## Gate — do not start the rule tree below until you have asked the relationship question

**Before reading any further in this section, confirm you already asked the Path B layer-2
question above: "Do you want to define node relationships? (Skip if not.)"** That question must be
asked on its own, in its own message, and answered (yes with pairs captured, or no/skip) *before*
you move on to the root node or any child relationship below. **Never jump straight from the node
list (layer 1) to the rule tree (layer 3) without asking it — silence or an assumption is not an
answer.** **Confirmed live: a run captured the node list (root + other objects, display fields),
then went straight to "Now building the rule tree" and the root-role question — the relationship
question was never asked at all.** If you notice you've reached this point without having asked it,
stop and ask it now, before the root role or any other rule-tree question. And once you *are* in the tree walk: **never populate `relationshipList` by inferring a
junction from a Many-to-many edge you're about to offer or that the admin just picked in the
tree** — that direction (rule tree writes `relationshipList`) is the deprecated, reversed behavior
called out above. The tree only ever *reads* `relationshipList`; if layer 2 was skipped or a pair
wasn't captured there, that pair gets One-to-many only, full stop — do not backfill
`relationshipList` from the tree to make Many-to-many available anyway.

## Building the rule tree (`rules.graph.rootNode`)

**Checking configured roles (do this once, before Step 1).** Read the org's
`FlexibleHierarchyNodeRole` `StandardValueSet` (same object Step 7 of the foundation skill populates)
before asking about role anywhere in the tree, and cache the result for the rest of this walk:

- **If it has no `<standardValue>` entries (confirmed the common case on an org where Step 7 was
  skipped or hasn't run yet)** — **skip asking for role entirely**, at the root and at every target
  node. There's nothing configured to choose from, and asking for a free-text label the admin might
  later expect to line up with Step 7's values would be misleading. Omit the `role` key from that
  node's JSON rather than emitting a blank/placeholder value.
- **If it has one or more `<standardValue>` entries** — ask for role as a multiple-choice picker over
  those configured values (plus a free-text escape for a value not yet in the set, same
  shortlist+escape pattern used for filter fields), and validate whichever is chosen/typed against that
  same list before accepting it.

The rule tree is **recursive**: the root node and every node it expands to have the same shape —
`object` + `role` + (a `filter`, at the root only) + `childRelationships[]` — and each child
relationship's target node can itself have further `childRelationships[]`, to whatever depth the
admin needs (the grounding sample nests four levels: Account → Contact/Account → Contact → Case).
Walk it top-down, one node at a time, exactly like the bespoke sub-skill walks node relationships one
at a time — never ask the admin to describe the whole tree in one free-text blob.

**Step 1 — the root node.**
- **Root role** → `rules.graph.rootNode.role`. Follow "Checking configured roles" above: if the org
  has configured `FlexibleHierarchyNodeRole` values, offer them as a picker (+ free-text escape,
  validated) instead of the free-text prompt below; if the org has none configured, skip this question
  and omit `role` from the root node. Free-text wording, when it applies: *"What role does the root
  (`<root object>`) play in this hierarchy? (e.g. 'Manufacturer', 'Regional Distributor'.) This is a
  label shown in the UI, not a picklist value — type anything descriptive."*
- **Root filter (optional)** → `rules.graph.rootNode.filter`. Ask directly: *"Do you want to add a
  filter for the root (`<root object>`)? This restricts which `<root object>` records qualify as
  roots — skip to include all of them."* If skipped, omit `filter` entirely (don't emit an empty
  object). If yes, capture the filter (see "Capturing a filter" below).
- The root's `childRelationships` starts empty and is filled by Step 2.

**Step 2 — child relationships, one at a time, then recurse.** For the current node (root, to
start):

1. **Target object** → the child object for this relationship, multiple-choice over the objects
   already in `nodeList` (same choice-list discipline as the bespoke sub-skill's relationship
   capture — never a node outside the list), or **Done** if this node has no (more) children.
   Ask this every time, even when a self-referential junction (e.g. `AccountAccountRelation`)
   makes the target object look implied — a live run skipped the explicit confirmation on the
   assumption it was obvious and only got the right answer by coincidence.
2. **Check `relationshipList` (captured in Path B step 2, before this tree) for an entry matching
   this exact `(current node's object, target object)` pair.** This lookup decides which edge types
   you're even allowed to offer next:
   - **A matching entry exists** → offer both edge types:
     > Reach `<target object>` from `<current node's role/object>` how? A relationship for this pair
     > was already captured (junction `<junctionEntityApiName>`), so either works:
     > - **One-to-many** — through a direct lookup field on `<target object>`.
     > - **Many-to-many** — through the already-captured `<junctionEntityApiName>` junction.
   - **No matching entry** → **skip the edge-type question — go straight to One-to-many.** Don't
     offer Many-to-many for a pair with no captured relationship; this sub-skill no longer captures a
     junction mid-tree-walk (see the flow-order note above the tree section), so there's nothing to
     reuse. If the admin specifically wants a Many-to-many edge for this pair, tell them to add the
     relationship in Path B step 2 first (name the parent/child pair so they know what to add), then
     resume the tree walk from here — don't invent a junction question in the middle of the walk.

- **One-to-many (default, or the admin's choice when both are offered):**
  - **Target role** → `childRelationships[].OneToMany.targetObjectNode.role`. Same conditional
    behavior as the root role question above (picker+escape if the org has configured values, skip
    and omit `role` entirely if not); when free-text applies, use the same wording pattern naming the
    target object.
  - **Filter (optional)** → `childRelationships[].OneToMany.filter`. Ask: *"Restrict which
    `<target object>` records qualify? (Skip to include all children reached this way.)"* Same
    capture mechanics as the root filter; omit `filter` entirely if skipped.
  - **Relationship field** → `childRelationships[].OneToMany.relationshipField.field`. **Query the
    target/child object's describe for every lookup/master-detail field whose reference is the
    current/parent object — not just the first or most obviously-named one — and present the full
    set as a multiple-choice picker** (same lookup-field discovery as the bespoke sub-skill's
    junction-field questions, just direct rather than through a junction). Objects frequently expose
    more than one lookup to the same parent (e.g. `Opportunity` has both `AccountId` and
    `PrimaryPartnerAccountId` referencing `Account`) — **never default to the "standard-sounding"
    field (like `AccountId`) without asking, even when there's only one candidate; always confirm
    with the admin.** State the direction plainly: this is the field on the child that points *up* at
    the parent; picking a field that points elsewhere breaks expansion silently.
  - `relationshipUiConfig` is always emitted as `{}` — never ask about it.
- **Many-to-many (only offered when step 2 above found a matching `relationshipList` entry):**
  - **Target role** → `childRelationships[].ManyToMany.targetObjectNode.role`. Same conditional
    behavior as the root role question above.
  - **Filter (optional)** → `childRelationships[].ManyToMany.filter`, same capture mechanics as
    above.
  - **Junction object, source field, target field — reuse from the matching `relationshipList`
    entry, don't re-ask.** `childRelationships[].ManyToMany.junctionObject.entity` =
    `junctionEntityApiName`, `.sourceField.field` = `parentFieldApiName`, `.targetField.field` =
    `childFieldApiName` from that entry. Echo the reused values back to the admin (*"Using the
    `<junctionEntityApiName>` junction already captured for `<parent>`→`<child>` (`<parentField>` /
    `<childField>`)."*) so they can catch a mismatch, but don't ask them to re-pick the junction or its
    fields — that was already decided in Path B step 2.
  - `relationshipUiConfig` is always emitted as `{}` — never ask about it.
  - **No new `relationshipList` entry needed.** Because Many-to-many is only offered for a pair with
    an existing entry, this edge reuses that entry as-is — there's nothing to mirror or dedup here
    (that used to be necessary when the rule tree was the thing writing `relationshipList`; now it's
    only ever reading it). If the same `relationshipList` entry backs multiple rule edges (e.g. two
    different roles both reachable through the same junction), that's fine — every such edge points
    at the same one entry.
- **After capturing one child relationship, ask if there's another sibling under the *same* current
  node** ("Add another child relationship under `<current node>`? Or say done."), looping until the
  admin says done, **then recurse into any children just added** — ask the Step 2 question again,
  now with that new target node as the "current node," before moving on to its siblings' own
  children. Walk depth-first: finish one branch's full depth before starting the next sibling branch,
  so you never lose track of which node you're currently adding children under. Echo back what you
  just captured before asking the next question, the same way the bespoke sub-skill echoes each
  relationship before offering another.

## Capturing a filter (`filter.filterCriteria[]` + `filter.booleanFilter`)

A filter is optional at the root and at every `OneToMany`/`ManyToMany` edge (see above). When the
admin opts in, capture **one criterion at a time**, looping:

- **Field** → `filterCriteria[].field.field`. **Present as a real single-select picker over 3
  describe-derived shortlisted fields on the filtered object — the same shortlist mechanism used for
  `graphViewFields`/`gridViewFields` in the bespoke node-list flow** — followed by a separate genuine
  free-text follow-up ("Any other field? Enter its API name, or say none") for anything not
  shortlisted. Never fold the "type your own" escape into the picker itself (same dead-option rule as
  everywhere else in this skill family). Whichever way the field is named, **validate it against the
  filtered object's live schema** (the root object for a root filter; the target/child object for an
  edge filter) before accepting it — direct standard, custom `__c`, or dotted relationship path, same
  discipline as every other field input in this skill family. **Fetch that field's describe metadata
  now** (type, and `picklistValues` if it's a picklist) — the Operator and Value steps below both
  depend on it.
- **`whichEntity`** → `filterCriteria[].field.whichEntity`. **Only `TARGET` is grounded** (every
  criterion in the sample uses it, meaning "the object being filtered," i.e. the root object for a
  root filter or the target/child object for an edge filter). Default to `TARGET` and don't ask this
  as a separate question unless the admin's own Path-A config uses something else — this isn't a
  confirmed enum with other legal values.
- **Operator** → `filterCriteria[].operator`, multiple-choice, **filtered by the field's type from the
  describe fetched above — don't offer an operator that can't make sense for that type.** **Always
  present each choice as the wire token followed by its plain-English meaning in brackets** — e.g.
  *"eq (equals)"*, *"ne (not equal to)"*, *"gt (greater than)"*, *"lt (less than)"* — never show the
  bare wire token alone; the admin picks by meaning, not by memorizing the enum:
  - **`picklist`/`multipicklist`/`string`/`textarea` fields** — offer **`eq` (equals) and `ne` (not
    equal to)**. The Setup UI's own filter builder offers "Equals" and "Not Equal to" for these types
    (confirmed by direct observation on a live org) — equality-only was an earlier, now-corrected
    assumption. Flag to the admin that `ne`'s exact wire token is inferred (SOQL convention), not yet
    exercised in a live deploy payload — every grounded sample so far still used `eq` on
    string/picklist fields.
  - **`boolean`/`id`/`reference` fields** — no ordering or not-equal semantics are confirmed for these,
    so offer **only `eq` (equals)**.
  - **`int`/`double`/`currency`/`percent`/`date`/`datetime` fields** — ordering is meaningful, so offer
    **`eq` (equals), `gt` (greater than), and `lt` (less than)** — all three confirmed live (root and
    edge filters on this skill's own build-from-scratch rule tree and the admin's own UI-built rule
    tree both used `gt` and `lt` on numeric fields).
  - If the admin needs something beyond this set (e.g. `gte`/`lte`/`contains`) for any field type, tell
    them it's unconfirmed for this metadata type and offer to include it as typed free-text with an
    explicit heads-up that it hasn't been validated against a live deploy — don't silently invent an
    operator enum. If offered, still show its plain-English meaning in brackets the same way (e.g.
    *"gte (greater than or equal to)"*).
- **Value** → `filterCriteria[].value`, free-text, typed to match the field (numbers unquoted, strings
  quoted in the JSON — e.g. `3000` for `NumberOfEmployees`, `"Electronics"` for `Industry`).
  **Validate the typed value against the field's actual constraints before accepting it — this is
  mandatory, not optional, for the same reason field/object validation is mandatory elsewhere in this
  skill family: a value that looks plausible but doesn't match reality produces a filter that silently
  never matches any record.**
  - **`picklist`/`multipicklist`** — check the typed value against that field's live `picklistValues`
    (exact match). If it doesn't match, **don't silently accept it** — tell the admin the value isn't
    one of the field's configured picklist values, show a few real values as examples, and ask them to
    re-enter (a close-looking value that isn't an exact match — e.g. typing `Manufacturer` when the
    org's actual value is `Manufacturing` — is a real, confirmed-live failure mode, not a hypothetical
    one: it deploys successfully but the filter never matches any account).
  - **`int`/`double`/`currency`/`percent`** — check it parses as a number; reject and re-ask if not.
  - **`date`/`datetime`** — check it parses as a valid date/datetime; reject and re-ask if not.
  - **`boolean`** — check it's `true`/`false`; reject and re-ask if not.
  - **`string`/`textarea`/other free-text types** — no fixed value set to check against; accept as
    typed (there's nothing further to validate).
- **After each criterion, ask if there's another** ("Add another filter criterion? Or say done.").
  Stop when the admin says done; a single-criterion filter is valid (skip `booleanFilter` questions
  entirely — see below).
- **`booleanFilter`** — only needed when there are **2 or more** criteria. Once the admin is done
  adding criteria, if there are 2+, ask how they combine: *"You added `<N>` criteria. How should they
  combine? Enter a boolean expression using the criterion numbers, e.g. `1 AND 2 AND 3` or
  `(1 AND 2) OR 3`."* Default suggestion is every criterion `AND`-ed together (matches every criterion
  in the sample), but let the admin override with their own numbered expression, including nested
  parentheses — confirmed live on an admin's own independently UI-built rule tree, e.g.
  `"(1 AND 2) AND (3 AND 4) AND (5 OR 6)"`. Emit it as the literal string typed.

## ⚠️ Pitfall: the duplicate `flexibleHierarchy` block

Beyond the bespoke sub-skill's existing pitfall (never place `flexibleHierarchy` as a sibling of
`rootNode` at the `graph` root), a rule-based config has a **second** duplication trap: an
admin-provided sample carried the entire `flexibleHierarchy` object — `nodeList`, `rules`,
`relationshipList`, and `summaryRollupList` together — **twice**, as two literal sibling
`"flexibleHierarchy"` keys inside `graph.globalUiConfig` with identical content. This was initially
assumed to be a paste artifact in that sample — **that assumption was wrong.** A live build-from-scratch
create against a live org sent a payload with exactly **one** `flexibleHierarchy` key, and the
immediate MDAPI re-retrieve of the created component came back with **two**, byte-for-byte identical.
**The org itself duplicates `flexibleHierarchy` on create/retrieve for a Rule-Based
`RelationshipGraphDefinition`** — this is server-side round-trip behavior, not something the admin or
this skill introduced by pasting. **Still send only one `flexibleHierarchy` key when building/deploying
a payload** (the create call only needs — and only accepts cleanly — the single copy); the duplication
happens on the org's side afterward and is cosmetic on read-back, not something to replicate when
authoring. When reconciling an admin-supplied Path A config that already carries two identical copies
(whether from an export of this same round-trip behavior or an actual paste), strip down to one before
re-deploying.

## Deploy + verify

Identical confirm-then-deploy-then-read-back flow as the bespoke sub-skill: show the admin the
hierarchy-type name (`masterLabel`) and root object (name + root object only — never the internal
`relationshipList`/`summaryRollupList`/rule-tree wire plumbing) and ask for a go-ahead immediately
before the write:

> Ready to deploy the `<name>` hierarchy type (root object `<object>`, Rule-Based). Deploy it now?
> (yes / no)

On *yes*, create via **the raw Metadata API (mdapi package + SOAP deploy)**, wrapped by
`/headless/metadata`, against a
`relationshipGraphDefinitions/<DeveloperName>.relationshipGraphDefinition-meta.xml` component — **not**
the Tooling API POST, which fails unreliably for `GraphType: "FlexibleHierarchy"` (see the intro
above). Same `relationshipGraphDefVersions` field shape as the bespoke sub-skill, just with the
`rules` key present inside `globalUiConfig.flexibleHierarchy`. Then read back with the **same
queryable-columns limitation** as the bespoke sub-skill: `SELECT Id, DeveloperName, MasterLabel FROM
RelationshipGraphDefinition WHERE DeveloperName='<Name>'` — `GraphType`/`RootObject`/`IsActive` (and
the entire `rules` tree) are not queryable columns; they live inside
`relationshipGraphDefVersions`/`graphDefinition` and can't be verified by SOQL. If you need to verify
the rule tree itself took effect as authored, that requires re-retrieving the metadata component (not
a SOQL query) — note this limitation to the admin rather than implying the SOQL read-back proves the
rule tree deployed correctly.

## End state

A `RelationshipGraphDefinition` component carrying both the flat `nodeList`/`relationshipList` and
the `rules.graph.rootNode` rule tree — from the admin's own config (Path A) or one built with them
node-by-node and rule-by-rule (Path B) — created via MDAPI deploy and confirmed present by
read-back (existence only; the rule tree's correctness is confirmed by re-retrieve, not SOQL — see
above).

<!-- skill-validate: ignore-start -->
<!-- codey:operations start -->
## Operations Reference

Operations this skill uses — routing and dependency reference.

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `step-1-delegate-node-list-and-relationships` | delegate | — | → `fsc-darksaber/fsc-flexible-hierarchy-configure-graph-config-create` | — |
| `step-2-check-configured-node-roles` | discovery | — | `GET /sobjects/FlexibleHierarchyNode/describe` | `step-1-delegate-node-list-and-relationships` |
| `step-3-validate-rule-tree-referenced-objects` | discovery | — | `GET /services/data/v66.0/sobjects/EntityDefinition/describe` | `step-1-delegate-node-list-and-relationships` |
| `step-3b-discover-onetomany-relationship-field` | discovery | — | `GET /services/data/v66.0/sobjects/{object}/describe` | `step-3-validate-rule-tree-referenced-objects` |
| `step-3c-discover-and-validate-filter-fields` | discovery | — | `GET /services/data/v66.0/sobjects/{object}/describe` | `step-3-validate-rule-tree-referenced-objects` |
| `step-4-deploy-relationship-graph-definition` | write | — | `/headless/metadata` | `step-2-check-configured-node-roles`, `step-3-validate-rule-tree-referenced-objects`, `step-3b-discover-onetomany-relationship-field`, `step-3c-discover-and-validate-filter-fields` |
| `step-5-verify-relationship-graph-definition` | verify | — | `GET /services/data/v66.0/query` | `step-4-deploy-relationship-graph-definition` |
<!-- codey:operations end -->
<!-- skill-validate: ignore-end -->
