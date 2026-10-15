---
name: fsc-flexible-hierarchy-graph-config-create
description: "Build and deploy a bespoke Flexible Hierarchy graph config as a `RelationshipGraphDefinition` MDAPI component — first ask whether the admin has a config, then either take an admin-supplied config as-is (Path A, name read from its `masterLabel`) or ask the name and construct the `graphDefinition` from scratch (Path B: root object, node objects, per-object graph/grid view fields, node relationships), confirm right before the deploy, then create it via MDAPI deploy and read back. Invoked from the fsc-flexible-hierarchy-configure foundation skill's hierarchy-type step to create the bespoke hierarchy config."
metadata:
  relatedSkills:
  - fsc-flexible-hierarchy-configure
  version: "1.0"
  cliTools:
  - tool:
    - "sf"
    semver: ">=2.0.0"
---

# Create a Bespoke Hierarchy Config

The **Bespoke Configuration** branch of the hierarchy-type step (**Step 9**) of the
[`fsc-flexible-hierarchy-configure`](../../../SKILL.md) foundation skill (see
[`../foundation-configure/SKILL.md`](../foundation-configure/SKILL.md)). The foundation skill
delegates here to build a **bespoke** hierarchy config — nodes and relations authored directly. This
is the *only* path when the org's Rule-Based Hierarchy preference isn't on, and remains available
even when it is (the admin can still choose Bespoke over Rule-Based at Step 9's modality gate).
Authoring a **Rule-Based** config — the `rules.graph.rootNode` tree of role-based filters and
automatic parent/child expansion — is out of scope for *this* skill; Step 9 delegates that to the
sibling [`../fsc-flexible-hierarchy-rule-based-graph-config-create/SKILL.md`](../fsc-flexible-hierarchy-rule-based-graph-config-create/SKILL.md)
sub-skill instead.

## Sequencing — one question at a time, never batch

This skill is multi-turn: the Path A/B branch, the name, and the pre-deploy confirm are each their
own turn. Ask **only the current question**, wait for the answer, then move on — **never bundle a
later question (e.g. node objects, relationships, the pre-deploy confirm) into the same message as
an earlier one, and never collect several answers up front.** This applies in full even if you're
serving this skill directly rather than being routed here from the foundation skill.

A hierarchy type is a **`RelationshipGraphDefinition`** metadata component — a deployable MDAPI type
(`metadataApiName="RelationshipGraphDefinition"`, `manageable`, `keyPrefix="06J"`). **This skill always
creates a brand-new record — never an update** (the `DeveloperName` uniqueness check above guarantees
it), and creation for this type needs a different **verb** than the rest of this skill uses on the
generic `/headless/metadata` facet. That facet's **PUT is update-only** for this type: PUT against a
`DeveloperName` that doesn't exist yet returns 400 `INVALID_CROSS_REFERENCE_KEY` ("Component does not
exist"), even with an otherwise-valid payload (confirmed against a live org — repeated identical
retries fail the same way, ruling out transience or a stale partial-create). **POST is a working create
transport in principle**, on either facet — confirmed `POST /services/data/v{version}.0/headless/metadata`
(body `{type, fullName, xmlRep}`) returns 200 with the new record's id, and the Tooling API's
generic-sObject POST is `createable: true` for this type via
`GET .../tooling/sobjects/RelationshipGraphDefinition/describe`. **But for
`GraphType: "FlexibleHierarchy"` specifically, the Tooling API POST is unreliable** — confirmed live
failing 5+ identical retries with `INVALID_FIELD_FOR_INSERT_UPDATE` on `GraphType`, on an
org where the Setup UI and an MDAPI deploy of the identical payload both succeeded immediately after.
**Create it via MDAPI deploy instead:** `sf project deploy start --source-dir <path>` against a
`relationshipGraphDefinitions/<DeveloperName>.relationshipGraphDefinition-meta.xml` component with the
same field shape as JSON would carry, HTML-escaped into XML. **Deploy at the org's highest supported
API version, not the CLI's/project's default** — confirmed live that an MDAPI deploy of this exact
type can fail with the *same* `INVALID_FIELD_FOR_INSERT_UPDATE`-style "Looks like you don't have access
to Graph Type FlexibleHierarchy" message purely from an API-version gap (deploying at v60 failed,
identical payload at v67 — the org's own default — succeeded), even though the running user genuinely
has access. So this error string alone doesn't prove a permission problem: before troubleshooting
access/permission sets, check the org's max supported API version (e.g. `GET /services/data` for the
version list, or the version a plain describe call resolves to) and pass it explicitly
(`sf project deploy start --api-version <max>`, and/or bump `sourceApiVersion` in `sfdx-project.json`)
rather than trusting whatever a scratch/default project scaffold ships with. See
[`references/hierarchy-type-payload.md`](references/hierarchy-type-payload.md) for the exact shape and
the full transport-failure writeup. Not a Java service call either way. There
is no `FlexibleHierarchyType` sObject despite the `FlexibleHierarchySetup` Setup node's name; a
`FlexibleHierarchy` instance's `HierarchyTypeReferenceId` is a lookup to this record — creating the
actual `FlexibleHierarchy` instance is out of scope.

## Prerequisites (established by the foundation skill before delegating here)

- FSC + ARC (Actionable Relationship Center) enabled on the org, with the running user able to
  access and modify ARC graphs, and the Flexible Hierarchies feature preference on —
  all confirmed in the foundation skill's earlier steps.
- The record-page placement made in the foundation skill's record-page step (its Step 8), **if any**.
  This is context only — the config's root object does **not** have to match it. Step 8 is optional
  (placement may be skipped entirely) and multi-select (the component may go on several objects), so
  there's often no single record-page object to align to. Pick the hierarchy root independently from the
  supported objects (see below).

## Free-text inputs must use a real text prompt — never a fixed-option picker

Several inputs in this skill are **open free-text**, not selections from a known set: the hierarchy-type
name, the root object, the "any other node objects" list, and the graph/grid view fields' "Enter my
own" escape. For every one of these, **ask a plain free-text question the admin types into** — do not
render it through a mechanism that only offers fixed selectable options.

**Tooling note (the trap that bit a real run):** if the only question mechanism available forces fixed
selectable options with no real text field — e.g. an `AskUserQuestion`-style tool where free text
arrives *only* via an auto-added "Other" — **do not use it for these inputs.** A label like "Type a
name" or "Enter objects (comma-separated)" inside such a picker is a **dead option**: selecting it
captures the literal string of the label, not what the admin meant to type, and there's nowhere to type
it. Ask as a plain free-text turn and read the answer from the admin's reply. This applies to *every*
free-text input below, not just one prompt.

**Second tooling note (also bit a real run):** don't try to work around the dead-option trap above by
calling an `AskUserQuestion`-style tool with a single placeholder option (e.g. one option reading "Type
it below") just to get a required field past the tool's validation — the tool itself requires **≥2
real, distinct options** and rejects a one-option call outright (`InputValidationError:
[...] expected array to have >=2 items`). Don't retry by inventing a second filler option either; that
just produces two meaningless choices for a question that has no fixed set of answers. For a genuinely
open, no-default, no-fixed-set field, abandon the picker tool entirely and ask in plain text — same
outcome as the first tooling note, reached from a different failed attempt.

## First ask: do you have a hierarchy config to deploy, or should I build one?

**Ask this fork FIRST — before the name.** It decides the `graphDefinition` payload (the hard part of
the component) and **determines whether you get interviewed for nodes and display fields.** It also
governs whether the name even needs asking: a Path A config already carries its own `masterLabel`, so
for a deploy of an existing config **you don't need to ask for a name separately** — you read it from
the config (and only confirm it). Only Path B, where you build from scratch, has no name to read, so
that's the branch that asks for one. Ask the fork as a **Yes/No choice the admin selects — not a
free-text answer they type.** Present exactly two options (Yes / No); don't make them guess the
wording:

> Do you already have a hierarchy config ready to deploy?
> - **Yes** — paste your `graphDefinition` JSON or full `RelationshipGraphDefinition` XML and I'll
>   deploy it as-is (I'll only validate the root object exists in the org — standard or custom — and
>   read the label).
> - **No** — I'll build one with you: the root object, any other node objects, the graph/grid
>   display fields for each, and optional node relationships.

Two paths follow from that answer:

- **Path A — the admin brings a config.** If they hand you a `graphDefinition` JSON or a full
  `RelationshipGraphDefinition` MDAPI XML (like the sample in the reference), **use it as-is** —
  don't silently rewrite their node/relationship choices. Reconcile only the essentials: confirm its
  root object (`graph.rootNode.object.entity`) is a real entity in the org — **standard or custom**
  (validate it against the org's describe, not a fixed list); it does **not** need to match any Step 8
  record-page object (see Prerequisites),
  and **read the name from the config's own `masterLabel`** — **don't ask for a name separately on
  this path**; just echo the `masterLabel` you found and let them correct it if it's wrong. **Strip
  the invalid duplicate `flexibleHierarchy` block if present** (see the pitfall below). This is the
  preferred path when a config already exists.
- **Path B — build it from scratch.** Only here do you construct the graph, and that means gathering
  **every field** from the admin — including the **name** (Path A read it from the config; Path B has
  none, so ask for it here):

  > What should the hierarchy type be called? (Required — there's no default.)

  The **name** becomes the component's `masterLabel` (and `DeveloperName`). **Ask it as an open,
  typed, free-text question — NOT a multiple-choice picker** (see the free-text-input rule hoisted at
  the top of this skill). There is no default hierarchy type and no suggested list, so you cannot offer
  options to select from: don't present a fixed choice (e.g. "Legal Entity") as option 1, don't
  pre-fill or default to any name, and — because the name is **required** — **do not offer a "Skip"
  option**. **Keep the prompt clean and do NOT improvise a suggested name from external or attached
  context** — do not mine the conversation, Downloads, an attached Apex script, an existing
  `RelationshipGraphDefinition` `DeveloperName`, or any other artifact to propose "something like
  `<X>`". Even a soft, "it's your call" suggestion biases the answer and leaks unrelated context into
  the prompt. Ask the bare open question — e.g. *"What should the hierarchy type be called? (Required —
  there's no default.)"* — and nothing more; let the admin supply the name unprompted.

  **`DeveloperName` must be unique — check for a collision and, if it exists, ask for another name.**
  The typed label becomes both `masterLabel` and `DeveloperName`, and `DeveloperName` derives by
  normalizing the label to a valid API name (spaces/punctuation → underscores, collapse repeats, strip
  leading/trailing and leading-digit issues — e.g. `Legal Hierarchy` → `Legal_Hierarchy`). Because the
  org **only accepts a unique `DeveloperName`** for `RelationshipGraphDefinition`, before building the
  payload **query the org for an existing record with that `DeveloperName`** —
  `SELECT Id, DeveloperName, MasterLabel FROM RelationshipGraphDefinition WHERE DeveloperName='<derived>'`.
  If a record already exists, **do not overwrite it and do not silently append a suffix** — tell the
  admin the name is already taken and **ask for a different name**, then re-derive and re-check, looping
  until the `DeveloperName` is free. Word it plainly — e.g. *"A hierarchy type with the API name
  `<derived>` already exists. Please choose a different name."* Only proceed to build the payload once
  the derived `DeveloperName` is confirmed unique. **Do not ask for a description, and do not emit a `<description>` element**;
  `RelationshipGraphDefinition` does **not** accept `<description>` — deploying one fails dry-run with
  `Element ...description invalid at this location in type RelationshipGraphDefinition` (confirmed against a live org).

  **Ask whether to save this as a reusable template — a real field, unlike description:**

  > Do you want to save this as a reusable template? (yes / no — defaults to no if skipped)

  Set `isTemplate` to `true` only if the admin opts in; leave it `false` (the default) on "no" or on
  no answer. This is optional and skippable — don't block on it or re-ask if declined. Then construct
  the graph. Ask for the root object **as typed free-text, not multiple-choice**:
  > Which object should be the root object? Enter the object API name — e.g. `Account` or
  > `My_Object__c`.
  → `graph.rootNode.object.entity`. **Validate that the typed object actually exists in the org —
  standard or custom.** Common choices are standard objects like Account, Contact, FinancialAccount,
  PartyRelationshipGroup, Opportunity, Case, BranchUnit, FinancialDeal, Product2, InsurancePolicy, or
  Lead, but **custom objects (anything ending in `__c`) are fully supported too** — don't reject an
  object just because it's custom or isn't in that common set. Confirm it against the org's schema
  (e.g. an `EntityDefinition` query or describe); if it doesn't exist in the org, **tell the admin no
  such object exists and ask them to enter another** — don't silently accept or drop it. The root is
  validated **by existence in the org only** — it does **not** have to match any object chosen for
  Step 8 record-page placement (which is optional and multi-select).
  Build one `nodeList` entry per object, **handling each object's fields right after it's chosen**
  rather than collecting all objects first. Start with the **root object** (already chosen above),
  then ask for the other node objects **as typed free-text, not multiple-choice** — phrase it around
  the chosen root, e.g.:
  > Any other node objects besides `<root object>`? Enter the object API names, comma-separated —
  > or leave it blank / say "none" if there aren't any.
  This is **skippable**: a blank / "none" answer means `nodeList` holds just the root object's entry
  (a valid single-object hierarchy). **Validate each typed object against the org's schema — standard
  or custom** (split on commas, trim, and confirm each exists via `EntityDefinition`/describe).
  Standard objects like Account, Contact, FinancialAccount, PartyRelationshipGroup, Opportunity, Case,
  BranchUnit, FinancialDeal, Product2, InsurancePolicy, and Lead are the common choices, but **custom
  objects (`__c`) are fully supported** — never reject one just for being custom. **Reject and re-ask
  anything that doesn't exist in the org** (report which one); don't silently drop it.
  For the root object, and then for **each** node object as it's selected, gather that object's
  display fields → `graphViewFields` + `gridViewFields` for its `nodeList` entry (`entityApiName`,
  `graphViewFields`, `gridViewFields`).
  **Ask the graph-view and grid-view fields as TWO SEPARATE questions** — the two lists can differ,
  so don't fold them into one prompt.

  **Present each as a real interactive multi-select picker, NOT a static markdown list and NOT bare
  free-text — and never fold the "any other fields" escape into the picker itself.** You already have
  to `describe` the object to validate the fields (below), so use that same describe to *offer* fields
  as genuine selectable options (e.g. via the host's actual multi-select question tool) instead of
  dumping a list of field names as text or making the admin recall API names cold. Because an object
  can have dozens/hundreds of fields — including **custom** ones — you can't list them all, so build
  the picker like this, **identically for every node — the root object and every other node object
  alike**:
  - Offer exactly **3 shortlisted fields** — the object's own likely display fields pulled from the
    describe (common, human-meaningful fields for that object — e.g. for Account: `Industry`, `Type`,
    `AnnualRevenue`; for Contact: `Title`, `Department`, `Email`) — as the picker's selectable options.
    On a **custom object** the shortlist is built the same way from *its* describe (its own `__c`
    fields are perfectly valid display fields — surface the meaningful ones rather than leaving the
    shortlist empty).
  - **Do not add an "Enter my own" option inside the picker.** A picker option that's really an
    invitation to type free text is a *dead option* — the exact anti-pattern the free-text-input rule
    at the top of this skill already forbids (selecting it captures the literal label, not what the
    admin meant to type). Instead, **immediately after the picker answer comes back, ask a separate,
    genuine free-text follow-up**: *"Any other fields for the `<view>` view on `<object>`? Enter API
    names, comma-separated, or say none."* This is what keeps custom and related fields (`My_Field__c`,
    `Owner.Name`, `My_Lookup__r.Name`) reachable without turning the picker into a dead-option trap.
    **Custom fields are fully supported in both the graph view and the grid view, for the root object
    and every other node** — validate them against the describe exactly like standard fields (see
    below); never reject a field just because it's custom.

  For the **graph view**, present the picker as a **multi-select over the 3 shortlisted fields, capped
  at 2 picks** (the Name field always shows automatically, so the card holds Name + up to 2 more = 3
  total):
  > **Graph view — `<object>` (pick up to 2; Name always shows automatically):**
  > - `<shortlisted field 1>`
  > - `<shortlisted field 2>`
  > - `<shortlisted field 3>`

  Then, as its own separate turn: *"Any other fields for the graph view on `<object>`? Enter API
  names, comma-separated, or say none."*

  For the **grid view**, present the **same 3-option multi-select picker — same shortlist — but with
  NO cap** (pick as many of the 3 as they want). This list can differ from the graph view, so ask it as
  its own distinct question:
  > **Grid view — `<object>` (pick as many as you want):**
  > - `<shortlisted field 1>`
  > - `<shortlisted field 2>`
  > - `<shortlisted field 3>`

  Then, as its own separate turn: *"Any other fields for the grid view on `<object>`? Enter API names,
  comma-separated, or say none."*

  **Graph-view hard cap: at most 2 fields in `graphViewFields`.** The Name field is carried
  separately in `nameField` and always renders, so the graph card shows Name + up to 2 more (3 total).
  If the admin types more than 2 for the graph view, **warn them that the graph is limited to 2 (plus
  the auto-shown Name), show the first 2 you would keep as the default, and ask whether they want to
  change the selection** rather than silently proceeding. Phrase it as a proceed-or-modify prompt —
  e.g. *"Heads-up: the graph view is capped at 2 fields (plus Name, which always shows). You picked
  `<N>`, so I'll go with `<field 1>` and `<field 2>` and drop `<the rest>`. Keep these two, or pick a
  different two?"* — and **default to proceeding with those first 2**; only re-collect if the admin
  says they want to change it. Never silently truncate without this warning, and never re-collect
  without offering the keep-these default. If they include the Name field itself among the 2, it lives
  in `nameField`, so don't count or duplicate it.
  **The grid view has no such limit** — `gridViewFields` can hold as many as they want.
  `nameField` is **mandatory on every node and set automatically** from the object's standard name
  field (`Name`, or `CaseNumber` for Case) — don't ask for it; if the admin also lists the name field
  among their view fields, keep it in `nameField` and don't duplicate it.
  `showRelatedContacts` is **asked only for the `Account` object** ("Should Account nodes show
  related contacts?"); for every other object don't ask — default it to `false`.
  **Validate every typed field against that object's live schema before deploying — this is
  mandatory, not optional, precisely because the input is free-text.** Describe the object (e.g. `sf
  sobject describe` / `EntityDefinition` + `FieldDefinition`) and confirm each named field actually
  exists on it. Fields may be:
  - **direct standard** — `Name`, `Industry`, `AnnualRevenue`;
  - **custom** — anything ending in `__c` (e.g. `My_Custom_Field__c`). **Custom fields are fully
    supported** — validate them against the describe exactly like standard fields; never reject a
    field just because it's custom;
  - **dotted relationship paths** — standard (`Owner.Name`, `Account.AccountNumber`) **or custom
    relationships** ending in `__r` (e.g. `My_Lookup__r.Name`). Resolve a dotted path by traversing
    the relationship: confirm the relationship (`Owner` / `Account` / `My_Lookup__r`) exists on the
    starting object, then confirm the trailing field exists on the related object.

  **Normalize the self-object prefix — don't reject it.** Admins frequently type a field on the
  node object *itself* with the object name prefixed, e.g. `Account.Type` while configuring the
  `Account` node, or `Case.CreatedDate` on the `Case` node. That's not a relationship path — it's the
  object's own `Type`/`CreatedDate` field. **When the leading segment equals the node object's own
  API name, strip it** and validate/emit the bare field (`Account.Type` → `Type`); mention that you
  normalized it. Only treat a dotted path as a real relationship traversal when the leading segment is
  a *relationship* on the object (`Owner`, `Account` on Contact, a `__r`), not the object's own name.
  Split the comma-separated input, trim each entry, and validate each one. **Reject and re-ask any
  field that doesn't resolve** (report which one and why — "no such field `Foo` on `Account`"); don't
  silently drop it and don't deploy a config containing an unvalidated field. Echo back the validated
  field list before building the payload. Then ask **"Do you want to define node relationships? (Skip if not.)"** —
  **opt-in and skippable**: if the admin declines, `relationshipList` stays empty `[]` (the common
  case). **The ASK itself is not optional — it must be its own standalone message with an explicit
  answer, never inferred from silence or from moving on to the next topic.** Confirmed live: a run
  built the node list and display fields, then moved straight into the next phase without ever asking
  this question at all — that is not the same as the admin declining, and `relationshipList` being
  empty because of it is a bug, not the documented common case. Only if they opt in, gather **each
  relationship** through six questions — **present every one as a multiple-choice question so the
  admin can only pick a legal value, never free-text**:
  - **Parent Node Object** → `parentNodeEntityApiName`. **Choices = the objects already in
    `nodeList`** (the root + node objects chosen above) — not the full supported-object set.
  - **Child Node Object** → `childNodeEntityApiName`. **Choices = the objects already in `nodeList`.**
  - **Junction Object** → `junctionObjectProperties.junctionEntityApiName`. **First check whether any
    real junction is even available before offering this path.** A valid junction is an object the
    user can read that carries lookup fields pointing at **both** the chosen Parent Node Object **and**
    the chosen Child Node Object — nothing else can serve as a junction. So, once parent and child are
    picked, query the org's accessible entities and their lookup fields (e.g. `EntityDefinition` +
    `FieldDefinition`/describe, filtering `ReferenceTo` for the parent and child objects) and build the
    candidate list from only the objects that have **both** required lookups. **Choices = that
    computed candidate list**, not the full set of readable objects. **Filter `ReferenceTo`
    client-side, not via a SOQL WHERE-clause operator** — `contains`/`LIKE`/`INCLUDES` are not
    confirmed to work against this field; fetch the describe/query results and check each field's
    `ReferenceTo` list in code instead. This is one instance of a general rule for every filter this
    skill builds: only use an operator that's actually confirmed for that field's datatype — for the
    plain string/id fields these steps otherwise filter on (e.g. the `DeveloperName` uniqueness check),
    that means `=`/`!=` (eq/ne) only. If a filter you need isn't confirmed-safe for a field's datatype,
    that's a validation error — stop before firing the query and tell the admin what's blocked, rather
    than guessing at an operator and reporting whatever error the org returns.
    - **If one or more junction candidates exist:** ask the Junction Object question (multiple-choice
      over the candidates), then its three field questions below.
    - **If NO object qualifies:** the relationship **cannot be added by default** — a junction object
      is required, so without one there is no legal relationship to capture. Do **not** fall through
      to a direct parent→child relationship, and **do not offer to create a new custom junction
      object** — building supporting metadata (new custom objects/fields) is out of scope for this
      skill entirely; never present "create a new object" as an option, on this or any other path.
      **Tell the admin why the relationship can't be added** — e.g. *"No junction object is available
      for `<Parent>` → `<Child>` (no object you can access has lookup fields to both), so this
      relationship can't be added."* — then give them exactly one recovery option: **name an existing
      object** they believe qualifies, as typed free-text (e.g. *"If you know of an existing object
      with lookups to both `<Parent>` and `<Child>`, you can type its API name — otherwise I'll drop
      this relationship."*). Validate whatever they type the same way as the automated scan (must
      carry lookups to both the parent and child); if it validates, treat it as the chosen junction and
      continue to the three junction-field questions; if it doesn't validate, explain why (e.g. "no
      lookup to `<Child>` on that object") and drop the relationship. If the admin has no such object,
      offer to capture a **different** parent/child pair or finish (`relationshipList` may stay empty
      `[]` if no pair has a junction). Don't silently omit any of this; state the reason so the admin
      understands the junction path was checked and ruled out, not forgotten.
  - **Parent Lookup field** → `junctionObjectProperties.parentFieldApiName` (choices = lookup fields
    on the chosen junction object that reference the Parent Node Object). **State the direction in the
    prompt so the admin can't pick it backwards:** the *parent lookup* is the junction field pointing
    at the **parent (higher) node** — the one whose children you're expanding. The graph expands a node
    N by finding junction rows where `parentFieldApiName = N.Id` and reading each child from
    `childFieldApiName`, so **reversing these two inverts the entire tree** (parents render as
    children). *Only asked when a junction was available and chosen.*
  - **Child Lookup field** → `junctionObjectProperties.childFieldApiName` (choices = lookup fields on
    the junction object that reference the Child Node Object). The *child lookup* points at the
    **child (lower) node**. *Only asked when a junction was available and chosen.*
  - **⚠️ Self-referential junctions (both lookups reference the SAME node object) — recommend the
    correct direction, don't leave it to a coin-flip.** When the parent and child node are the same
    object (e.g. an Account→Account hierarchy via `AccountAccountRelation`, whose `AccountId` and
    `RelatedAccountId` both look up to `Account`), "which lookup is the parent" is genuinely ambiguous
    and easy to reverse — a real run picked it backwards and produced an inverted tree. For these,
    surface the FSC convention as the **recommended default** (still overridable): for
    `AccountAccountRelation`, **parent = `AccountId`, child = `RelatedAccountId`**. This is grounded —
    it's what the FSC "create hierarchy type" UI generates, and it matches the `HierarchyType`
    picklist's `Child` semantics (a record `{Account, RelatedAccount, HierarchyType=Child}` means the
    RelatedAccount is a child of the Account). Present it as *"Parent lookup — recommended `AccountId`
    (the FSC default for Account hierarchies)"*, not as an unlabeled equal choice.
  - **Relationship name field** → `junctionObjectProperties.titleFieldApiName` (choices = **text
    (`string`/`textarea`) and picklist fields** on the junction object). **Always ask this — present
    the picker; never silently default it to `Name`.** The org accepts a text OR a picklist field here
    and **rejects reference/lookup, date, and other types** with `INVALID_FIELD_FOR_INSERT_UPDATE`
    *"Specify a text field for Relationship Name Field"* (grounded via live Tooling-API creates on
    `AccountAccountRelation`: `Name`/string ✅ and `HierarchyType`/picklist ✅ both created;
    `RelatedAccountId`/reference ❌ and `EndDate`/date ❌ both rejected with that error). So build the
    choice list from the junction object's describe **filtered to `string`/`textarea`/`picklist`
    fields**, and never surface reference, date, number, or boolean fields as options.
    **⚠️ Do NOT mirror the FSC UI's own "Relationship Name" dropdown — it is broader than what actually
    deploys.** That UI dropdown also lists the junction's reference/lookup fields (on
    `AccountAccountRelation` it shows Account, Related Account, Party Role Relationship, Related Inverse
    Account alongside the text/picklist fields), but selecting one of those fails the create — the UI is
    permissive, the create is not (the "a deploy result can lie" discipline, inverted). Offer only the
    string/textarea/picklist fields. *Only asked when a junction was available and chosen.*

  **A junction object is required for every relationship** — there is no direct-lookup fallback. If no
  qualifying junction exists for the chosen parent/child pair, the relationship can't be added (see the
  "If NO object qualifies" branch above); emit a `relationshipList` entry **only** when a junction was
  available and chosen, carrying `parentNodeEntityApiName` + `childNodeEntityApiName` +
  `junctionObjectProperties`.
  **Validation (baked into the choice lists — don't relax it):** parent and child **must be objects
  already in `nodeList`**; the junction **must be one the user has access to AND carry lookups to both
  the parent and child** (the junction option is only offered when at least one such object exists —
  see the pre-check above); the three junction fields must exist on the chosen junction object — and
  the **relationship name field (`titleFieldApiName`) must be a *text* (`string`/`textarea`) or
  *picklist* field** (the org rejects reference/lookup, date, number, etc. with "Specify a text field
  for Relationship Name Field" — grounded by live creates: string ✅, picklist ✅, reference ❌, date ❌),
  so its choice list is pre-filtered to string/textarea/picklist fields; note the FSC UI dropdown is
  more permissive than the create (it lists lookup fields too), so don't copy the UI's reference entries. `summaryRollupList` is emitted as an empty array
  `[]` in the payload (rollup is out of scope) — but it is **internal wire plumbing only: never ask
  about it, never offer it, and never show it when echoing/summarizing the config back to the admin.**
  The admin can't add rollups here, so surfacing an empty `summaryRollupList: []` only confuses them;
  keep it in the deployed JSON, keep it out of everything the user sees. **Don't reconstruct the shape
  from memory — pattern-match the validated example and the full
  per-field input checklist in [`references/hierarchy-type-payload.md`](references/hierarchy-type-payload.md).**

  **Loop — after each relationship, ask if they want to capture another.** As soon as one relationship
  is fully captured (parent/child + the junction details), append it to `relationshipList`,
  echo back the relationship you just recorded, and ask:

  > **Captured: `<Parent>` → `<Child>` (junction via `<Junction>`).**
  > Do you want to capture another node relationship? (Say "no" / "done" to finish.)

  Keep looping through the six-question capture for each "yes"; stop only when the admin says no/done.
  Don't assume a single relationship is the whole set, and don't ask for all relationships in one
  prompt — capture one, confirm it, then offer to add more.

## ⚠️ Pitfall (both paths): the `flexibleHierarchy` block belongs ONLY under `graph.globalUiConfig`

The `graph` object allows exactly `rootNode` + `globalUiConfig` (`additionalProperties: false`); a
`flexibleHierarchy` copy placed as a sibling at the graph root is schema-invalid and trips Jackson's
`FAIL_ON_UNKNOWN_PROPERTIES`. Some exported/hand-authored configs carry this redundant top-level copy
— strip it before deploying.

## Defaults that don't need to be asked

`isActive` = `true` (the type goes live immediately), and `graphType` = the fixed constant
`FlexibleHierarchy`. The component's `RootObject` field is system-derived from
`rootNode.object.entity` — never set it directly. `isTemplate` is the one exception in this
section — it's asked (see the template question above), defaulting to `false` only when skipped or
declined, not asked-and-answered.

## Deploy + verify

**Confirm right before the deploy — one explicit go-ahead immediately before the write.** Once the
component is assembled (Path A's reconciled config or Path B's built graph), show the admin what's
about to be deployed — the hierarchy-type name (`masterLabel`) and root object — and ask for a
go-ahead just before deploying:

> Ready to deploy the `<name>` hierarchy type (root object `<object>`). Deploy it now? (yes / no)

Deploy only on *yes*. This confirm is **specific to this final write** — it's the one gate in Step 9,
placed immediately before the `RelationshipGraphDefinition` deploy, not a re-confirmation of the name
or config questions already answered above. (Don't surface `summaryRollupList` or other internal wire
plumbing in this summary — name + root object is what the admin decides on.)

On *yes*, create the component via **MDAPI deploy** (`sf project deploy start --source-dir <path>
--api-version <org's max>`) against a
`relationshipGraphDefinitions/<DeveloperName>.relationshipGraphDefinition-meta.xml`
component — **not** the Tooling API POST, which fails unreliably for `GraphType: "FlexibleHierarchy"`
(see the transport note above). Don't PUT either (that facet's PUT is update-only for this type and
400s on a genuinely new `DeveloperName`). **Always deploy at the org's highest supported API version**
— see the transport note above for why a lower/default version can produce the same
"don't have access to Graph Type FlexibleHierarchy" error as a genuine permission gap. Then read back to confirm the record exists. **Read back
with queryable columns only:**
`RelationshipGraphDefinition` exposes just `Id`, `IsDeleted`, `DeveloperName`, `Language`,
`MasterLabel`, `NamespacePrefix`, and the audit fields — **`GraphType`, `RootObject`, and `IsActive`
are NOT queryable** (they live inside `relationshipGraphDefVersions`/`graphDefinition`) and a
`SELECT`/`WHERE` on them fails with `INVALID_FIELD` (confirmed against a live org). Use
`SELECT Id, DeveloperName, MasterLabel FROM RelationshipGraphDefinition WHERE DeveloperName='<Name>'`.
([Help: create hierarchy types](https://help.salesforce.com/s/articleView?id=ind.fsc_flexible_hierarchies_create_hierarchy_types.htm))

## End state

A `RelationshipGraphDefinition` component for the confirmed hierarchy type (from the admin's own
config or one built with them) created via MDAPI deploy and confirmed present by read-back.

<!-- skill-validate: ignore-start -->
<!-- codey:operations start -->
## Operations Reference

Operations this skill uses — routing and dependency reference.

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `step-1-validate-root-object` | discovery | — | `GET /services/data/v66.0/sobjects/EntityDefinition/describe` | — |
| `step-2-check-developer-name-uniqueness` | discovery | — | `GET /services/data/v66.0/query` | `step-1-validate-root-object` |
| `step-3-validate-node-objects-and-fields` | discovery | — | `GET /services/data/v66.0/sobjects/{object}/describe` | `step-1-validate-root-object` |
| `step-4-resolve-junction-candidates` | discovery | — | `GET /services/data/v66.0/query` | `step-3-validate-node-objects-and-fields` |
| `step-5-deploy-relationship-graph-definition` | write | — | `/headless/metadata` | `step-2-check-developer-name-uniqueness`, `step-3-validate-node-objects-and-fields`, `step-4-resolve-junction-candidates` |
| `step-6-verify-relationship-graph-definition` | verify | — | `GET /services/data/v66.0/query` | `step-5-deploy-relationship-graph-definition` |
<!-- codey:operations end -->
<!-- skill-validate: ignore-end -->
