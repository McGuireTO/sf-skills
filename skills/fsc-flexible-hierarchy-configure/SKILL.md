---
name: fsc-flexible-hierarchy-configure
description: "Set up the Financial Services Cloud (FSC) Flexible Hierarchy foundation on an org: detect org state, validate prerequisites (edition, license/org permissions, admin access), enable the Flexible Hierarchies feature, optionally enable the (irreversible) Rule-Based Hierarchy preference, assign the Flexible Hierarchies permission sets and ARC access, optionally grant object permissions on the Flexible Hierarchy object, configure hierarchy node roles, add the hierarchy view component to record pages, and create a hierarchy type — bespoke (nodes/relations authored directly) by default, or a Rule-Based configuration (role-based filters + automatic parent/child expansion) when the org has the Rule-Based Hierarchy preference on and the admin chooses that path. Triggers on \"enable Flexible Hierarchies\", \"set up Flexible Hierarchies\", \"configure Flexible Hierarchies\", \"set up corporate entity hierarchy foundation\", \"create a hierarchy type\", \"create a rule-based hierarchy type\", \"set object permissions for Flexible Hierarchy\". Building an actual hierarchy instance from a reference artifact (org chart/CSV/existing Account hierarchy/text description), org-wide-default sharing, rollup metrics, and the Hierarchy-Aware Agent are out of scope for this skill for now."
metadata:
  version: "1.0"
---

**"Set up Flexible Hierarchies" / "configure Flexible Hierarchies" with no narrowing qualifier
means running the foundation setup below** — org connectivity check, prerequisite validation,
feature enablement, optional (irreversible) Rule-Based Hierarchy preference enablement,
permission-set assignment (Flexible Hierarchy permission sets + ARC via
whichever ARC-granting permission set — `FSCSales` / `FSCService` / `FinancialServicesCloudExtension`
— is present on the org), optional object-permission configuration,
hierarchy node-role configuration, record-page component placement, and hierarchy-type creation.
This skill's scope is currently limited to that foundation/enablement phase — it does not build
an actual hierarchy instance (nodes/relations from a reference artifact), configure rollup
metrics, or activate an agent.

## Job to be done

As a Salesforce admin, turn on and configure the Flexible Hierarchy foundation on an org — the
feature, permissions, node-role picklist, record-page placement, and hierarchy type — so a
hierarchy instance can be built on top of it later.

## Assumptions & dependencies

- Setup happens in a **Sandbox** first, not production, unless the admin explicitly says
  otherwise.
- `FlexibleHierarchy`, `FlexibleHierarchyNode`, and `FlexibleHierarchyNodeRelation` objects
  require an **FSC license** on the org — validate this before doing anything else.
- Run in **strict sequential mode**: process Steps 1–9 one at a time, never ahead of where the
  conversation actually is. For each step, ask **only that step's query** (target users and their
  permission sets, node-role values, which record-page objects, the hierarchy config — whichever
  this step needs), wait for the admin's answer, then execute that step's write (or gate) before
  moving on. Never bundle a later step's question into the same message as an earlier one, and
  never collect several steps' answers before writing any of them — the per-step
  query-then-write-then-advance IS the confirmation for every step, not just the four below. Four
  writes keep an **extra** explicit confirmation on top of that per-step flow:
  (1) **enabling the Rule-Based Hierarchy preference (Step 4)** — optional AND **irreversible**, so it
  is gated twice: an opt-in yes/no using the exact pref name `RuleBasedHierarchyPref`, then a second
  double-confirm that names the "cannot be disabled" fact before the write (and a check-before-write
  read that skips it if already on); (2) **user access (Step 5)** confirms each user with a simple
  per-user go-ahead (yes/change/skip)
  **immediately before that user's assignment is written** — a per-user confirm-then-write, not a
  batched plan-review of everyone at once; (3) **creating the hierarchy type (Step 9)** confirms right
  before the `RelationshipGraphDefinition` deploy (the sub-skill shows the name + root object and asks
  for a go-ahead just before the write); and (4) **activating** a record page as an object's org
  default (Step 8), because it changes what users can see. Deploying the record page itself needs no
  extra confirm beyond the per-step flow; only its *activation* does. The optional object-permissions
  step (Step 6) is also individually skippable.

## No upfront batch plan — announce and run one step at a time

Do **not** post a single upfront plan naming multiple steps before the first write, and do not
gather several steps' answers up front. Instead, right before each step: announce it in one line
(e.g. "Step 3: enable the Flexible Hierarchies feature"), ask that step's query, wait for the
reply, execute the write, then move to the next step and repeat. For an unqualified request this
starts at the org connectivity check (Step 1) and continues through Step 9 in order — but each
step is its own announce → ask → wait → write cycle, never a batch of several. The four writes
named above keep their own *additional* explicit confirm on top of this per-step cycle (Step 4's
opt-in + double-confirm, Step 5's per-user assignment go-ahead, Step 9's confirm right before the
hierarchy-type deploy, and Step 8's record-page activation).

## Smart defaults (all overridable — confirm before applying)

| Default | Value | Overridable? |
|---|---|---|
| Node Object Type | Account | Yes — Contact or custom object |

There is **no default hierarchy type** — the type name is always asked (Step 9), never defaulted.

## Full detail

See [`source/skills/foundation-configure/SKILL.md`](source/skills/foundation-configure/SKILL.md) for the
complete step-by-step detail: org connectivity check, the prerequisites checklist, feature
enablement, optional (irreversible) Rule-Based Hierarchy preference enablement, permission-set/ARC
assignment, optional object-permission
configuration, node-role picklist configuration, record-page component placement, and bespoke
hierarchy-type creation.

## End state (the whole skill)

An unqualified "set up/enable Flexible Hierarchies" is complete when: prerequisites are reported
as an itemized checklist; the feature preference is confirmed enabled; the optional (irreversible)
`RuleBasedHierarchyPref` is left as-is unless the admin opted in AND passed the "cannot be disabled"
double-confirm, in which case it's enabled and confirmed by re-read (skipped when already on);
every target user's
permission set (and ARC access, if requested) is assigned from the per-user permission-set query,
each written on a per-user go-ahead right before that user's assignment;
object permissions are configured or skipped (optional, verified by an `ObjectPermissions` read when
done); the
node-role picklist is populated from admin-provided values; the hierarchy type is created after a
confirm shown right before its deploy — bespoke by default, or Rule-Based (with its role/filter/
child-relationship rule tree captured first) when the admin chose that path at the modality gate
Step 9 asks whenever the Rule-Based preference is on; and
the record-page component is placed on the object(s) the admin named — with its activation as the
org-default record page confirmed with the admin (activated + verified by re-read when they said
yes, left deployed-but-inactive when they declined). See
`source/skills/foundation-configure/SKILL.md`'s end-state section for the full checklist.

## Out of scope / deferred

- Parsing a reference artifact (org chart image, CSV, existing `Account.ParentId` chain, text
  description) into hierarchy nodes/relations, with a preview-before-write gate.
- **Org-wide-default (OWD) sharing for `FlexibleHierarchy`.** It's a non-customizable standard
  entity — the `<sharingModel>` CustomObject MDAPI channel rejects both retrieve and deploy for it
  (confirmed live), so OWD can't be set headlessly; it's a Setup → Sharing Settings UI action. The
  current value is readable via `EntityDefinition.InternalSharingModel` but not writable through this
  skill.
- Rollup metrics (DPE-based) for the hierarchy type.
- Hierarchy-Aware Agent activation and validation.
- **Summary Rollup** — `summaryRollupList` is always emitted empty (`[]`) by both hierarchy-type
  creation paths; rollup metrics themselves are deferred (DPE-based, see below).
- *Enabling* the `RuleBasedHierarchyPref` preference (Step 4, opt-in + double-confirm +
  check-before-write) and *authoring* a Rule-Based hierarchy type's rule tree (Step 9's Rule-Based
  branch — role labels, filters, and OneToMany/ManyToMany child relationships) are both **now in
  scope**, but only together and only when the admin explicitly opts in at each gate: Step 4 never
  auto-enables the preference, and Step 9 never offers the Rule-Based branch unless Step 4 already
  found/left the preference on. Everything else about the Rule-Based Hierarchy Builder beyond that
  scoped tree — e.g. any UI-only configuration not represented in the `RelationshipGraphDefinition`
  metadata itself — remains out of scope. This skill still defaults to creating **bespoke** hierarchy
  types (nodes/relations authored directly) whenever the admin doesn't choose Rule-Based.

## Sample prompts

- "Enable Flexible Hierarchies on this org."
- "Enable the Rule-Based Hierarchy preference (`RuleBasedHierarchyPref`) on this org."
- "Set up the Flexible Hierarchy foundation — Legal Entity type, Account nodes."
- "Assign the Flexible Hierarchy Manager permission set to alice@acme.com."
- "Configure the hierarchy node role picklist with Parent, Subsidiary, Branch."
- "Create a Legal Entity hierarchy type."
- "Create a rule-based hierarchy type rooted on Account with a Manufacturer role."
- "Add the Flexible Hierarchy component to the Account record page."
- "Grant CRUD on the Flexible Hierarchy object to the FH Admin profile."

<!-- skill-validate: ignore-start -->
<!-- codey:operations start -->
## Operations Reference

Operations this skill uses — routing and dependency reference.

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `delegate-fsc-flexible-hierarchy-configure-foundation-configure` | delegate | — | → `fsc-darksaber/fsc-flexible-hierarchy-configure-foundation-configure` | — |
| `delegate-fsc-flexible-hierarchy-configure-fsc-flexible-hierarchy-rule-based-graph-config-create` | delegate | — | → `fsc-darksaber/fsc-flexible-hierarchy-configure-fsc-flexible-hierarchy-rule-based-graph-config-create` | — |
| `delegate-fsc-flexible-hierarchy-configure-graph-config-create` | delegate | — | → `fsc-darksaber/fsc-flexible-hierarchy-configure-graph-config-create` | — |
<!-- codey:operations end -->
<!-- skill-validate: ignore-end -->
