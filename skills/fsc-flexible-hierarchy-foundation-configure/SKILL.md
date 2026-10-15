---
name: fsc-flexible-hierarchy-foundation-configure
description: "Financial Services Cloud Flexible Hierarchy foundation setup — confirm org connectivity, validate prerequisites, enable the feature, assign the Flexible Hierarchies permission sets and ARC access via whichever ARC-granting permission set (`FSCSales` / `FSCService` / `FinancialServicesCloudExtension`) is actually present on the org, configure hierarchy node roles, add the hierarchy component to record pages, and create the hierarchy type. Full detail for the fsc-flexible-hierarchy-configure skill."
metadata:
  relatedSkills:
  - fsc-flexible-hierarchy-configure
  - platform-flexipage-generate
  version: "1.0"
  cliTools:
  - tool:
    - "python3"
    semver: ">=3.8"
  - tool:
    - "sf"
    semver: ">=2.0.0"
---

# Enable & Configure the Foundation

Full detail for the [`fsc-flexible-hierarchy-configure`](../../../SKILL.md) skill, whose scope is currently
limited to this foundation/enablement phase. Building an actual hierarchy instance (parsing a
reference artifact, creating nodes/relations, rollup metrics, agent activation) is out of scope
for this skill for now.

## Sequencing — run one step at a time, never batch

This skill is multi-turn: process the steps below one at a time, in the order the conversation
actually needs. For each step, ask **only that step's query**, wait for the answer, then execute
that step's write (or gate) before moving on. **Never bundle a later step's question into the
same message as an earlier one, and never collect several steps' answers up front.** This rule
applies in full even if you're serving this skill directly rather than being routed here from the
parent `fsc-flexible-hierarchy-configure` skill — it is not context you're expected to have
carried over from elsewhere.

## Session state (track across the conversation)

This skill is multi-turn and branch-driven — thread this state across turns rather than
re-deriving it, and never lose a decision the admin already made:

- `target_org_alias` — org being configured; confirmed before any write.
- `org_state` — the Step 1 detection result: feature pref already on? hierarchy type(s) already
  present? permission sets already assigned to some users? Feeds every check-before-write.
- `prereqs` — the Step 2 checklist result per item (Flexible Hierarchy org perm, ARC org
  perm, admin access), each ✅/❌ with the value actually queried.
- `feature_pref_state` — `enableFlexibleHierarchyPref` value confirmed by **re-read** after Step 3,
  not the deploy result.
- `rule_based_pref_state` — the optional Step 4 result: `enableRuleBasedHierarchyPref` value confirmed
  by **re-read**, and which terminal state this run reached — `skipped` (opt-in declined), `already-on`
  (check-before-write found it true), `declined-at-confirm` (backed out at the irreversibility gate),
  or `enabled` (turned on and verified by re-read). This preference is **one-way** — once `enabled`,
  never re-toggle or offer to disable it.
- `arc_permset` — the Step 5 lead-in result: which permission set on **this org** actually grants
  ARC access (`FinancialServices2UserAccess`) — resolved once, before the per-user loop, by querying
  which of the known candidates (`FSCSales` / `FSCService` / `FinancialServicesCloudExtension`) exist
  on the org. Reused for every user in the loop; never re-resolved per user.
- `user_permset_list` — the per-user `{user, permission set, arc?}` list accumulated in Step 5 from
  **individual** answers (never one permission set applied to the whole batch), plus each user's ARC
  (`arc_permset`) choice. Each user is confirmed with a per-user go-ahead and written **immediately**,
  right before moving to the next user (pick → role → ARC → confirm → write per user); this list is
  the running record of who's been handled for the end-of-step report, not a batch collected up front
  and deployed at the end.
- `object_permissions` — the optional Step 6 result: which profile (if any) the admin
  chose to grant object CRUD on the master `FlexibleHierarchy` (the two detail objects inherit it),
  the access level, and whether the step was skipped.
- `node_role_values` — the comma-separated role picklist values the admin gave for Step 7.
- `record_page_objects` — which of the 11 objects the admin confirmed for Step 8 (Account by default).
- `hierarchy_type` — the confirmed type name handed to Step 9.
- `hierarchy_config_mode` — Step 9's modality result: `bespoke` (the only value when
  `rule_based_pref_state` isn't `already-on`/`enabled`, or when it is but the admin picked Bespoke
  anyway) or `rule-based` (admin picked Rule Based Configuration at the modality gate). Determines
  which sub-skill Step 9 delegates to — `graph-config-create` or `fsc-flexible-hierarchy-rule-based-graph-config-create`.

## Entry point — route on the admin's actual ask

An unqualified "set up / enable Flexible Hierarchies" runs Steps 1–9 in order. A narrow ask should
start at the matching step (still verifying the earlier steps' gates first — e.g. you can't assign a
permset if the license prereq in Step 2 fails), not restart at Step 1:

| Admin ask signal | Where to start | What to run |
|---|---|---|
| "Set up / enable Flexible Hierarchies" (unqualified) | Step 1 | Steps 1–9 in order |
| "Enable the Flexible Hierarchies feature" | Step 3 | Verify Step 2 gate, then Step 3 |
| "Enable Rule-Based Hierarchy / `RuleBasedHierarchyPref`" | Step 4 | Verify Step 2 + Step 3 gates, then Step 4 (optional, irreversible — opt-in + double-confirm) |
| "Assign the Flexible Hierarchy Manager/Admin/User permset to \<user\>" / "give \<user\> ARC access" | Step 5 | Verify Step 2 gate, then Step 5 for those users |
| "Grant object permissions on the Flexible Hierarchy objects to \<profile\>" | Step 6 | Step 6 only |
| "Configure the hierarchy node role picklist" | Step 7 | Step 7 only |
| "Add the Flexible Hierarchy component to the \<object\> record page" | Step 8 | Step 8 only |
| "Create a \<Legal Entity/…\> hierarchy type" | Step 9 | Verify prereqs, then Step 9 → modality gate (if Rule-Based pref is on) → bespoke or rule-based sub-skill |

## Transport & deploy discipline

Applies to every write below — hoisted here so it isn't re-stated per step:

1. **Prefer `dispatch` over CLI.** Use the canonical operation paths against the live org; CLI
   (`sf project deploy`, `sfdx`) is a fallback only where no API path exists.
2. **Dry-run first.** Before each write, state the operation + payload (which pref, which permset
   Id, which StandardValueSet values) so the admin can review scope.
3. **Split deploy per step.** One step's write at a time — don't batch the pref deploy, permset
   assignments, node-role SVS, FlexiPage, and RGD into one transaction. Each has its own confirm.
4. **Re-read to verify — a deploy result can lie.** `IndustriesSettings` and other metadata deploys
   can report `changed=true` / "Succeeded" while an access gate silently no-ops the change. **Always
   re-read the setting/record after deploying and confirm the new value stuck** — never trust the
   deploy response alone. (Proven on this skill: the Step 3 pref deploy returns success, and only the
   re-read confirms `enableFlexibleHierarchyPref` actually flipped.)
5. **Ground the final report in reads.** Report done from what you re-read back, not from write
   responses.
6. **Config ≠ data — this is a mixed-transport skill; use the right one per step.**
   - **Data records → REST/SOQL create**, *not* MDAPI: `PermissionSetAssignment` (Step 5). Never try
     to MDAPI-deploy a permission-set assignment.
   - **Metadata → MDAPI deploy** (via `/headless/metadata`): the `IndustriesSettings`
     `enableFlexibleHierarchyPref` (Step 3) and — optionally, one-way — `enableRuleBasedHierarchyPref`
     (Step 4), both PUT-only on the `IndustriesSettings` singleton;
     the `Profile` `objectPermissions` (Step 6),
     the `FlexiPage` (Step 8), and the `RelationshipGraphDefinition` (Step 9).
   - **Metadata → genuine MDAPI CLI, *not* the facade** (`sf project retrieve` / `sf project deploy`):
     the `FlexibleHierarchyNodeRole` `StandardValueSet` (Step 7). The `/headless/metadata` facade
     blocks BOTH directions for this type (confirmed live — see Step 7 below) — this is the one
     metadata write in this skill that must bypass `dispatch` entirely, not a dispatch-first,
     CLI-only-as-fallback case like the others above.

**If you fall back to the `sf` CLI (no `dispatch` available), two setup gotchas will look like org
problems but aren't.** Both bit a real run:
- **`sf project retrieve/deploy` needs a DX project scaffold.** Run from a dir with a minimal
  `sfdx-project.json` (a `packageDirectories` entry, e.g. `force-app`) or the command fails with
  `InvalidProjectWorkspaceError: This directory does not contain a valid Salesforce DX project` —
  which reads like a connection/auth failure but is just a missing scaffold. Create it **once** up
  front, before the first retrieve, and reuse it for every step's write.
- **Build manifests and metadata XML with a file-writing tool, not shell heredocs.** A mistyped
  heredoc terminator silently writes the *trailing shell commands* into the manifest instead of
  closing it, producing a corrupt `package.xml` that then fails opaquely downstream. Every write in
  this skill (`package.xml`, the settings/profile/SVS/FlexiPage/RGD components) is small and
  known-shape — author it as a file directly rather than piping a heredoc through the shell. (This is
  distinct from the quote-escaping note below, which is about inline `python3 -c` formatting code, not
  metadata files.)

**User-facing prompt language — never expose internal step numbers.** In anything the admin sees —
questions, option labels, skip choices — refer to the *work*, never the skill's ordinal. Every
optional step must offer a way out, and that option is always labelled **"Skip this step"** (or
"skip <the work>", e.g. "skip adding the record-page component"), **never "Skip Step 6/7/8/9."** This
applies to every skip/opt-out throughout the skill, not just one step.

**Free-text inputs must use a real text prompt — never a fixed-option picker.** One input in this
foundation skill is open free-text, not a selection from a known set: the node-role picklist values
(Step 7) — the admin invents them, so there's no list to pick from. Ask it as a plain free-text
question the admin types into. **If the only question mechanism available forces fixed selectable
options with no real text field** — e.g. an `AskUserQuestion`-style tool where free text arrives only
via an auto-added "Other" — **do not use it for this input**: a label like "Enter role values" inside
such a picker is a *dead option* (selecting it captures the literal label string, with nowhere to
type the actual values). Ask as a plain free-text turn and read the answer from the admin's reply.
(This class of bug bit a real run.) Note the **record-page objects (Step 8) are NOT free-text** —
they're a selection from the fixed 11-object set, so they use a multiple-choice picker (no typed
list); and the hierarchy-type name (handled in the bespoke sub-skill) remains free-text there.

**API-version floor — deploy at the org's max supported API version, not the CLI default; v66.0+ is a
supported floor, don't invent a stricter one.** The
`enableFlexibleHierarchyPref` field and the FSC objects
(`FlexibleHierarchy`, `FlexibleHierarchyNode`, `RelationshipGraphDefinition`) **do not exist at older
API versions** — deploying at an older version fails with `Property 'enableFlexibleHierarchyPref' not
valid in version <n>.0`, and those sObjects describe as "not supported"; at a recent enough version
the deploy succeeds and the objects come online. If a deploy is rejected as an invalid property, or
an FSC object reads as "not supported," **suspect the API version before concluding the org isn't
provisioned** — the two failure modes look identical but the fix is a version bump, not a licensing
escalation. **Don't hardcode a version number, and don't flag a discovered max version as a blocker
just because it isn't the newest release** — this skill's writes are confirmed working from **API
v66.0 and above**; a discovered max of v66.0, v67.0, v68.0, etc. is a fine floor, not a gap to report
to the admin or ask them how to proceed about. Discover the org's max supported API version at
connect time (Step 1) — e.g. the highest entry from `GET /services/data/` — pin every write in this
skill to that discovered version, and **don't re-verify it again in later steps** — one discovery at
connect time covers the whole run.

**Inline scripting to format query results — avoid the quote-escaping trap.** Several steps format
live query results into a picker or table for the admin (the Step 5 user picker `Name — Username`,
the Step 6 profile picker, the permission/assignment tables). If you build these with
an inline `python3 -c "..."` wrapped in a **double-quoted** shell string, **do not reuse `"` inside
the Python, and never backslash-escape quotes inside an f-string expression** — `f"{x[\"Name\"]}"`
fails with `SyntaxError: f-string expression part cannot include a backslash` (bit a real run on the
Step 5 user picker). Use single quotes inside instead (`f"{x['Name']}"`), or pass the code via a
heredoc / temp `.py` file. Better still, apply the same read-then-parse hygiene as the `sf` CLI note
in Step 6: dump the query result to a file and parse the file, rather than piping formatted output
through a fragile one-liner.

## What this skill does

1. **Authenticate + confirm org connectivity.** Before touching anything, confirm the target org
   is authenticated and reachable — resolve the alias/username, confirm a live connection, and
   **discover the org's max supported API version** (e.g. the highest entry from `GET /services/data/`),
   which every later write pins to. That's the whole of this step: **just connectivity.** Do **not** probe
   feature-preference state, permission-set assignments, or object existence here — those reads
   belong to the steps that own them (the pref to Step 3, assignments to Step 5, existing hierarchy
   types to Step 9), each of which does its own check-before-write when it runs.
2. **Validate true prerequisites. Surface these as an explicit, itemized checklist up front —
   one reported line per item with its live value — not a silent internal gate.** Report each
   as ✅/❌ with the value actually queried, present the whole checklist even when everything
   passes:
   - **License / provisioning** — the **Flexible Hierarchy** org permission (a provisioned
     permission) must be granted by SKU/entitlement; this is not admin-toggleable — if
     absent, the feature cannot be enabled at all (Step 3 will find the preference ungated and
     stop). Confirm the platform license named `FlexibleHierarchy-1` is present (its
     `PermissionSetLicense` `DeveloperName` is `FlexibleHierarchyPsl` — note it does **not** contain
     "FSC", so a `LIKE '%FSC%'` license scan won't surface it; query it by its own name).
     **Do NOT gate this step on describing the `FlexibleHierarchy` / `FlexibleHierarchyNode` /
     `RelationshipGraphDefinition` sObjects.** Those sObjects do **not** exist until Step 3 enables
     the feature — on a fresh, correctly-licensed org they describe as **"not supported"** and a
     `SELECT ... FROM FlexibleHierarchy` returns `sObject type ... is not supported`. That is the
     *expected* pre-enablement state, **not** a missing-provisioning signal; treat the platform
     license (above) as the pre-enablement proxy for the org permission, and expect the sObjects to
     come online only *after* Step 3. (They become the read surface for Step 9's read-back once the
     feature is on.)
   - **Actionable Relationship Center (ARC) enabled** — the **ARC** org permission (a provisioned
     permission).
     Unlike Flexible Hierarchy, ARC has **no separate admin-toggleable preference** — this
     permission alone gates the `RelationshipGraphDefinition` object Step 9 creates records in
     and the user-level `FinancialServices2UserAccess` permission Step 5 assigns, so it's
     check-only here, not something to enable. It's typically bundled in via a
     Permission Set License such as `FSCSales` / `FSCService` / `FinancialServicesCloudExtension`
     — if absent, report it and note ARC access (Step 5) can't proceed until it's provisioned.
     **Which of those PSLs is present varies by SKU** (e.g. an org provisioned via the
     `FSCServiceAddon` SKU has `FSCService`, not `FSCSales`) — this check only confirms ARC is
     provisioned *at all*; Step 5 resolves *which specific permission set* to assign from
     whatever's actually on this org, never assuming `FSCSales` specifically.
   - **Admin access** to the org.

   Any unmet item → report which one, redirect to Salesforce/the license add-on process, **stop**.
   These cannot be fixed by this skill; they're the customer's or Salesforce's provisioning
   decisions, not something to work around. Do not attempt Step 3 without the org permission
   confirmed present. Present the whole checklist even when everything passes, so the admin sees
   what was verified rather than an unexplained "prereqs OK."
3. **Enable the Flexible Hierarchies feature, if not already on.** The master toggle is the
   **`FlexibleHierarchyPref`** org preference — MDAPI `IndustriesSettings.enableFlexibleHierarchyPref`
   (boolean) — confirmed live in `FlexibleHierarchyUdd.settings.xml`. **Check its current value
   first via MDAPI, not SOQL** (don't assume it's off): retrieve the `IndustriesSettings` metadata
   (`Settings:Industries`) and read `enableFlexibleHierarchyPref` from it. **Do not attempt to query
   this preference with SOQL** — it is a settings field, not a queryable sObject column, so
   `SELECT enableFlexibleHierarchyPref FROM ...` fails with `INVALID_FIELD` (a "No such column"
   error); that failure means "wrong transport," not "feature absent." The same MDAPI-not-SOQL rule
   applies to reading it back after the deploy. If already on, report that and move on to the next
   step (Step 4, the optional Rule-Based Hierarchy preference). If off, **ask a single explicit
   go-ahead confirm before deploying — `enableFlexibleHierarchyPref` is not reversible; there is no
   supported way to turn it back off once enabled** (lighter than Step 4's double-confirm, since
   Step 4 gates a second, independently-irreversible preference stacked on top of this one). Only
   on that confirm, deploy `IndustriesSettings` with `enableFlexibleHierarchyPref=true` (equivalent
   to the in-product Setup Discovery / Salesforce Go "Enable" action on the Flexible Hierarchy
   tile, which flips this same preference under the hood), then re-read the setting to confirm it
   stuck — don't trust the deploy result alone. This step depends on Step 2's org-permission check: the
   preference's `editAccess` gate requires the **Flexible Hierarchy** org permission already being
   present, so without that permission this deploy will not take effect.
4. **Enable the Rule-Based Hierarchy preference (optional, IRREVERSIBLE).** Beyond the base feature
   (Step 3), Flexible Hierarchy has a second, separate org preference — **`RuleBasedHierarchyPref`**,
   MDAPI `IndustriesSettings.enableRuleBasedHierarchyPref` (boolean) — that turns on the Rule-Based
   Hierarchy mode. It is a **sibling** of `enableFlexibleHierarchyPref` in the same
   `IndustriesSettings` (`Settings:Industries`) metadata. **Version gate — this optional step needs
   v68.0+:** `enableFlexibleHierarchyPref` (Step 3, the base feature) is present in the retrieved xmlRep
   from API **v66.0+**, but `enableRuleBasedHierarchyPref` appears only from **v68.0+** — at v66.0/v67.0
   the RBH element is absent from the xmlRep entirely. So keep the same **v66.0+** gate as before for the
   base workflow, and treat Step 4 as available **only when the org's pinned max version is v68.0 or
   higher**. If the org is on v66.0/v67.0, **silently ignore Step 4** — record `rule_based_pref_state`
   as skipped (not applicable at this version), move straight to Step 5, and do **not** raise it as a
   blocker or "out-of-range" error to the admin; the RBH element's absence is expected on those
   releases. This step **only flips that preference on** — it does not author any rule content
   itself. Authoring the actual `rules.graph.rootNode` tree (role labels, filters, and
   OneToMany/ManyToMany child relationships) happens later, and only conditionally: Step 9 asks
   whether to build a Bespoke or Rule-Based hierarchy type, and only offers the Rule-Based path when
   this step left `rule_based_pref_state` as `already-on` or `enabled`.

   This step is **optional AND one-way** — treat it more carefully than the reversible Step 3 toggle.
   Run it as a gated sequence, and do **not** proceed past any gate without an explicit yes:

   1. **Optional opt-in gate — ask first, using the exact preference name.** Before doing anything,
      ask a plain yes/no using the real pref name so the admin knows exactly what's being toggled:
      > Do you want to enable **`RuleBasedHierarchyPref`** (the Rule-Based Hierarchy mode) on this org?
      > - **Yes**
      > - **Skip this step**

      On **Skip**, record `rule_based_pref_state` as skipped and move straight to Step 5 — don't read,
      don't deploy, don't ask anything further. (Label the opt-out per the user-facing-language rule —
      "Skip this step", never "Skip Step 4".)
   2. **Check-before-write — read the current value first; it may already be on.** On **Yes**, before
      any deploy, **read `enableRuleBasedHierarchyPref` via MDAPI** (retrieve `IndustriesSettings` /
      `Settings:Industries` and read the element — the same MDAPI-not-SOQL rule as Step 3; a
      `SELECT enableRuleBasedHierarchyPref FROM …` fails `INVALID_FIELD`, which means "wrong
      transport," not "absent"). **An org that already has `FlexibleHierarchyPref` on can also,
      occasionally, already have `RuleBasedHierarchyPref` on** — so don't assume it's off. If the
      re-read shows it is **already `true`**, report that it's already enabled, record
      `rule_based_pref_state` as already-on, and **skip the deploy entirely** — there is nothing to do
      (and nothing could be undone anyway). Only proceed to the confirmation gate when it reads
      `false`.
   3. **Irreversibility double-confirm — this is the extra gate the reversible Step 3 doesn't have.**
      `RuleBasedHierarchyPref` **cannot be turned off once enabled** — there is no supported way to
      disable it afterward. So even though the admin already said Yes in the opt-in gate, **ask a
      second, explicit confirmation that names the irreversibility** before writing:
      > ⚠️ **`RuleBasedHierarchyPref` cannot be disabled once it's turned on.** Do you wish to turn it
      > on?
      > - **Yes, turn it on** (this is permanent)
      > - **No, leave it off**

      Only on an explicit **Yes, turn it on** do you deploy. On **No**, record `rule_based_pref_state`
      as declined-at-confirm and move on — the admin backed out at the irreversibility gate, which is
      a valid outcome, not an error.
   4. **Deploy, then re-read to verify.** Deploy `IndustriesSettings` with
      `enableRuleBasedHierarchyPref=true` via `/headless/metadata` at the org's max supported API
      version (discovered in Step 1). **`IndustriesSettings` is a singleton settings type — deploy with
      PUT, not POST** (POST returns 400 `UNSUPPORTED_OPERATION`, same as the Step 3 pref deploy). Leave
      `enableFlexibleHierarchyPref` at its current value in the payload (don't flip the base feature off
      as a side effect). Then **re-read `enableRuleBasedHierarchyPref` via MDAPI and confirm it now
      reads `true`** — a deploy "Succeeded" is not proof (the "a deploy result can lie" rule from the
      transport discipline; the pref's `editAccess` gate can silently no-op the change without the
      **Flexible Hierarchy** org perm from Step 2 and the feature from Step 3 both in
      place). Record `rule_based_pref_state` from the re-read, not the deploy response.

   Depends on Step 2's org-permission check and Step 3's feature enablement: Rule-Based mode sits on
   top of the base Flexible Hierarchy feature, so if the feature preference isn't on (or the org
   permission is absent), this deploy won't take effect — surface that rather than reporting success.

5. **Assign user access — a Flexible Hierarchies permission set, and ARC via whichever permission
   set actually grants it on this org.** Three Flexible Hierarchy permission sets exist —
   `FlexibleHierarchiesUser`, `FlexibleHierarchyManager`, `FlexibleHierarchyAdmin` — but **only one
   is needed per user**, matching the role they'll actually play (viewer/user vs. manager vs.
   admin). **Heads-up on the names: they are NOT uniformly pluralized.** The viewer set is plural —
   label "Flexible Hierarch**ies** User", API name `FlexibleHierarchiesUser` — while Manager and Admin
   are singular ("Flexible Hierarchy Manager/Admin", `FlexibleHierarchyManager`/`FlexibleHierarchyAdmin`).
   **Do not "regularize" the viewer set to the singular "Flexible Hierarchy User" / `FlexibleHierarchyUser`
   — that name does not exist on the org, and a lookup for it comes back empty.** (Verified live on an
   FSC org.)

   **Resolve the ARC permission set once, before anything else in this step — never hardcode
   `FSCSales`.** Step 2 only confirmed the ARC org permission is provisioned; it did not
   pin down *which* permission set on this specific org grants the user-level
   `FinancialServices2UserAccess` permission that backs it, and that varies by SKU (e.g. the
   `FSCServiceAddon` SKU provisions `FSCService`, not `FSCSales` — an org with only `FSCService`
   has no `FSCSales` permission set to assign, and treating `FSCSales` as fixed fails outright on
   that org). Resolve it once per session, not per user:
   1. Query `SELECT Id, Name FROM PermissionSet WHERE Name IN ('FSCSales', 'FSCService',
      'FinancialServicesCloudExtension')` (the known candidates from Step 2's PSL list) to see which
      of them actually exist on this org.
   2. **Exactly one exists** → that's `arc_permset`; use it for every user in the loop below, no
      further prompt.
   3. **More than one exists** → ask the admin once, up front, which one to use for ARC access —
      e.g. *"This org has both `FSCSales` and `FSCService` available for ARC access. Which should I
      assign?"* — and use their answer as `arc_permset` for the whole loop. Don't re-ask per user.
   4. **None exist** → ARC access can't be assigned via a known permission set even though
      the ARC org permission is provisioned; leave `arc_permset` unresolved, report that gap, and treat ARC
      as blocked for the rest of this step rather than guessing a name (inferred — the
      three-candidate list is what Step 2 already documents; verify against a live
      `FSCServiceAddon`-only org and extend the list if a new PSL surfaces). **When `arc_permset` is
      unresolved, bypass every ARC-specific action in the rest of Step 5:** query and report existing
      assignments for the three role permission sets only (not a fourth ARC set), skip the per-user
      ARC prompt (sub-step 3) entirely, and never create an ARC `PermissionSetAssignment`. The
      role-permission-set workflow still runs in full — only the ARC lookup/prompt/create is skipped,
      so the no-candidate org degrades cleanly to "roles assigned, ARC reported as blocked."

   **First, surface what's already assigned — don't jump straight to collecting new users.** Query
   `PermissionSetAssignment` for the three role permission sets plus the resolved `arc_permset`
   **when ARC is available** — on the no-candidate org from branch 4 above, `arc_permset` is
   unresolved, so query the three role sets only and never reference a fourth ARC set. If any users
   already have them, **show the admin the current assignments as a table (user → permission set,
   and — only when ARC is available — whether they have ARC via `arc_permset`) and
   ask whether any changes are needed** — "Here's who's already set up. Do you want to add/change
   any assignments, or should I proceed to the next step?" If the admin says no changes, **skip the
   rest of this step and move on** — don't re-ask the per-user permission-set questions for users
   who are already correctly assigned. Only when they want changes (or there are no existing
   assignments at all) do you collect the targets below.

   **Collect targets one user at a time — a pick-then-loop flow, not one big up-front list.** Handle
   each user completely (who → role → ARC) before offering to add another, rather than gathering a
   roster first and asking roles afterward. For each user:

   1. **Pick the user (single-select).** Query the org's **assignable human users** and present them
      as the options: `SELECT Id, Username, Name, UserType FROM User WHERE IsActive = true` —
      **exclude system/integration users. Filter structurally, not by a hardcoded name list:** keep
      only `UserType = 'Standard'` (drop `AutomatedProcess`, `CsnOnly`, portal/community types, etc.),
      and additionally drop the platform integration/service accounts that still describe as
      `Standard` — those whose username ends in a non-login suffix like `.ext` or matches a known
      integration pattern (e.g. `Automated Process`, `Platform Integration User`, `Insights
      Integration` / `insightsintegration@…`, `Analytics Cloud Integration/Security User`, `Sales
      Insights Integration User`, `B2B/B2C Store Integration User`, `Integration User`, `Security
      User`). When in doubt whether an account is a human login, **leave it out of the picker** rather
      than offering it — a system/integration user should never appear as an assignment target.
      (A real run surfaced `Insights Integration` as an option because the filter only excluded a
      hardcoded name set; the `UserType`/suffix check above closes that gap.) Show each option as
      `Name — Username`. **The picker holds four choices, so cap it: if there are three or fewer
      assignable users, list them all; if there are more than three, show the first three as options
      and make the fourth option "Type a username/email"** (an explicit type-it-in escape). That
      typed-entry option is also the fallback whenever the target isn't among the shown three. Pick
      **one user** here; don't multi-select a batch.
   2. **Pick that user's role (single-select — exactly one).** Present **exactly these three
      options and no others** — this is a fixed, known set, so the picker must NOT carry a fourth
      "Other" / "Type a permission-set name" / free-text option (unlike the user picker in sub-step 1,
      whose targets aren't a fixed set). Any FH permission set a user could need is one of these three;
      a typed/other option here is a dead option that can only capture an invalid value. **Show each
      option's exact label AND API name — the three are NOT uniformly named (see the heads-up in the
      step intro): the viewer set is plural, Manager/Admin are singular. Present the labels verbatim;
      don't regularize the viewer set to "Flexible Hierarchy User".** Present them
      as a single-select so more-than-one is structurally impossible:
      > *"Which Flexible Hierarchy permission set should `<user>` get?*
      > - *Flexible Hierarchies User (`FlexibleHierarchiesUser`) — view and work with hierarchies*
      > - *Flexible Hierarchy Manager (`FlexibleHierarchyManager`) — build and edit hierarchies*
      > - *Flexible Hierarchy Admin (`FlexibleHierarchyAdmin`) — full administration*
      > *(Pick one — each user needs exactly one.)"*

      **When you resolve the chosen set's Id, match on the EXACT API `Name` above** — e.g.
      `SELECT Id, Name, Label FROM PermissionSet WHERE Name = 'FlexibleHierarchiesUser'`. A
      `WHERE Name LIKE '%FlexibleHierarchy%'` / `Label LIKE '%Flexible Hierarchy %'` scan **silently
      misses the viewer set** (its name/label is "…Hierarch**ies**…", not "…Hierarchy…") — that exact
      miss is what makes "Flexible Hierarchy User" appear not to exist. If you must pattern-match across
      all three at once, use the plural-safe stem `LIKE '%Hierarch%'`. (Verified live on an FSC org:
      `SELECT Name, Label FROM PermissionSet` returns Label "Flexible Hierarchies User" / Name
      `FlexibleHierarchiesUser`, "Flexible Hierarchy Manager" / `FlexibleHierarchyManager`, and
      "Flexible Hierarchy Admin" / `FlexibleHierarchyAdmin`.)
   3. **Confirm that user's ARC access (single-select, still inside the loop).** **Skip this
      sub-step entirely when `arc_permset` is unresolved** (the no-candidate branch 4 above) — there
      is no ARC-granting permission set to assign, so don't prompt for ARC and set this user's `arc?`
      to "blocked"; go straight to sub-step 4 with the role permission set only. Otherwise, right
      after the role, handle **this** user's ARC access (the per-user ARC question detailed below) — keep each
      user's full setup together rather than batching ARC into a separate pass. **Frame ARC as
      required, not optional:** Actionable Relationship Center is what backs the
      `RelationshipGraphDefinition` object hierarchy operations run against, so a user cannot actually
      view or work with hierarchies without it. Word the prompt to say ARC is **required to perform
      hierarchy operations** and default to Yes — e.g. *"`<user>` needs ARC access to work with
      hierarchies. Assign it now? (Recommended — hierarchy operations don't work without it.)"* Only
      an admin who explicitly declines for a specific user skips it; don't present it as a neutral,
      equally-weighted yes/no.
   4. **Confirm THIS user's assignment, then write it — one go-ahead right before the write.** Once
      you have this user's `{user, permission set, arc?}`, show that one user's line back and ask for a
      go-ahead just for them, immediately before creating their `PermissionSetAssignment`(s):

      > Assign `<Name — Username>` the `<FlexibleHierarchyManager>` permission set (plus ARC via
      > `<arc_permset>`)? (yes / change / skip)

      On *yes*, write **this user's** assignments now — the role permission set, plus `arc_permset`
      when their ARC choice was Yes (the `PermissionSetAssignment` creates described below). On *change*,
      let them amend this user's role or ARC choice and re-show the one line. On *skip*, drop this user
      and move on. This per-user yes/no is the confirmation gate for Step 5 — **one simple go-ahead
      immediately before each user's write, not a batched plan-review of everyone at once.** It does
      not change the skill's minimal-intervention default for the other steps, which still proceed
      straight from their own information-gathering answers.

   5. **Offer to add another user, then loop.** After writing (or skipping) this user, append the
      handled `{user, permission set, arc?}` to `user_permset_list` for the end-of-step report, then
      ask **"Assign another user?"** — on *yes*, loop back to sub-step 1 (drop already-handled users
      from the picker) and run pick → role → ARC → confirm-and-write again for the next user; on *no*,
      end the step. Never ask for all users in a single prompt, and never assume one user is the whole
      set — handle each user completely (pick → role → ARC → confirm → write) before offering the next.

   Ask the role **per user** — don't assume everyone needs the same permission set, and don't ask
   once and apply the answer to the whole batch. Build a per-user `{user, permission set, arc?}`
   record from each loop iteration's answers, and **confirm-then-write that one user before moving to
   the next** (sub-step 4). For each user, at the confirm step: check assigned-vs-needed by querying
   `PermissionSetAssignment` for that user and the permission set's Id, then, on their go-ahead,
   assign by creating a `PermissionSetAssignment` record
   (`AssigneeId`=that user's Id, `PermissionSetId`=that set's Id) if they need it —
   **the per-user confirm (sub-step 4) is the one gate right before that user's write; don't also
   batch everyone into a separate plan-review pass**.
   **Query `PermissionSetAssignment` by the raw `AssigneeId` / `PermissionSetId` fields, not by
   relationship traversal.** On Core-backed orgs `SELECT Assignee.Username, PermissionSet.Name FROM
   PermissionSetAssignment` fails with `INVALID_OPERATION` ("operation not yet supported by this
   sObject storage type") — resolve the user Id and the permission-set Id first (a separate query on
   `User`/`PermissionSet`), then filter the assignment query on those raw Ids. Don't mistake that
   query error for a missing assignment. (Verified against a live org.) Never assign a
   permission set to a user who wasn't individually asked about it. A `DUPLICATE_VALUE` response on that
   create means it's already assigned — treat that as success, not an error. Report the resulting
   assignments as a table when done.

   **Actionable Relationship Center (ARC) access rides on the same per-user loop** (step 3 above) — it is
   *not* a separate Setup-UI-only step, and *not* a batched pass after all users are collected. ARC's
   user-level gate is the `FinancialServices2UserAccess`
   user permission, which the standard **`FSCSales`** permission set (label "FSC Sales", API
   name `FSCSales`) grants — confirmed live via `FSCSalesPsl-1.uld.xml`'s
   `standardPermissionSets` block — but `FSCSales` is only one of the possible carriers: on an
   org provisioned via a different SKU (e.g. `FSCServiceAddon`), the equivalent grant comes from
   `FSCService` or `FinancialServicesCloudExtension` instead, and `FSCSales` won't exist at all.
   That's why this step resolves `arc_permset` once, up front (see the resolution sub-step above),
   rather than assuming `FSCSales`. **ARC is required, not optional, for a user to work with
   hierarchies** — hierarchy operations run against the `RelationshipGraphDefinition` object ARC
   backs, so a user without it can't view or edit hierarchies. Ask each user in turn, right after
   their role, framing ARC as required and defaulting to Yes (see sub-step 3); record the choice on
   that user's record. For each user whose ARC choice is Yes, check/assign the resolved
   `arc_permset` the same way as the Flexible Hierarchy permission set above (query
   `PermissionSetAssignment`, then assign on that user's per-user go-ahead in sub-step 4, in the
   same write as their role set — `DUPLICATE_VALUE` = already assigned).
   This requires the org's ARC org permission (Step 2) to already be provisioned —
   `arc_permset` only grants the user-level permission, not the org-level one.
   ([Help: assign permissions](https://help.salesforce.com/s/articleView?id=ind.fsc_flexible_hierarchies_assign_permissions.htm))
6. **Set object permissions (optional).** To make Flexible Hierarchies usable and let admins manage
   hierarchy types, a profile needs object-level access (CRUD) to the FH object
   family. There are three objects — **`FlexibleHierarchy`**, **`FlexibleHierarchyNode`**, and
   **`FlexibleHierarchyNodeRelation`** (provisioned on Core as the 40-char-truncated
   `FlexibleHierarchyNodeRela` — use that API name in any query/describe) — but **only the master
   `FlexibleHierarchy` carries its own object permissions.** `FlexibleHierarchyNode` and
   `FlexibleHierarchyNodeRela` are **detail objects** (each has a master-detail field
   `FlexibleHierarchyId` → `FlexibleHierarchy`, `relationshipOrder 0`), so they **inherit** object
   access from the master and **cannot hold independent `<objectPermissions>`**. Granting CRUD on
   `FlexibleHierarchy` alone gives the profile access across the whole hierarchy.
   **This step grants object permissions via a PROFILE only** — the permission-set path is intentionally
   out of scope here (users get their day-to-day access from the Step 5 role permission sets; this step
   is specifically for granting object CRUD on the FH objects at the profile level). Because the target
   is a `Profile`, **two different silent-failure modes are in play, and they have different causes —
   don't conflate them.** In both, the `/headless/metadata` deploy returns "Succeeded"/"Created" for the
   whole `Profile`; only a re-read of the live `ObjectPermissions` reveals what actually stuck. This is
   the "a deploy result can lie" case from the transport discipline above, in two distinct forms:

   - **Standard profiles reject the whole grant (nothing sticks).** Object permissions on a **standard**
     profile (`System Administrator`, `Standard User`, `Minimum Access - Salesforce`, etc.) are **not
     editable through the Metadata API at all** — the platform silently ignores the entire
     `<objectPermissions>` block, master included, and still reports the deploy as succeeded. Confirmed
     live: a Step-6-style grant against `Standard User` left `ObjectPermissions` with **zero rows** for
     `FlexibleHierarchy` — the grant never applied. **You cannot grant FH object permissions on a
     standard profile via this step; see the standard-profile branch in sub-step 1 for the remediation.**
   - **Detail-object blocks are dropped on any profile (custom included).** Even on a **custom** profile
     where the grant does apply, the two detail-object blocks are silently dropped because they're
     detail objects that inherit (see above) — only the master `FlexibleHierarchy` block can stick.
     Confirmed live: a grant against a custom profile ("Flexible Hierarchy Access") took `allowRead=true`
     on `FlexibleHierarchy`; the detail objects never carried their own row (expected — they inherit).

   So the deploy only does something real on a **custom** profile, and even there only the master block
   matters. **Emit only the master `FlexibleHierarchy` block from the start** — don't add
   `<objectPermissions>` for the detail objects (dropped regardless), and don't deploy against a
   standard profile at all (the whole block is dropped).

   **This step is optional — open it with a plain yes/no gate, and surface the profile-edit heads-up
   in the prompt itself.** Many orgs already grant these object permissions through the Flexible
   Hierarchy role permission sets assigned in Step 5, so ask first whether the admin wants to touch
   profile object permissions at all, as a simple two-option yes/no. **Give the admin the heads-up up
   front — a profile edit applies to every user assigned to that profile — so it's part of the
   question they answer, not an aside the agent keeps to itself.** Ask this gate on its own, in its
   own message — don't combine it with any other step's question:

   > **Heads-up:** editing object permissions on a profile applies to **every user assigned to that
   > profile**, not just one user. (Per-user access is handled by the Step 5 role permission sets.)
   >
   > Do you want to make changes to object permissions on the Flexible Hierarchy objects for any of
   > the profiles?
   > - **Yes**
   > - **No**

   On **No**, record `object_permissions` as skipped and move on — don't ask anything further. On
   **Yes**, proceed to gather the details below. If they proceed, gather two
   answers (these questions are this step's query — no separate per-write confirmation once answered).
   **Never take the profile as bare free text** — profiles are a known, queryable set on the org, so
   present them as options and resolve the real API name, same pick-from-a-query pattern Step 5 uses
   for choosing a user:
   1. **Which profile?** **Query profiles WITH their custom-vs-standard flag** — `Profile` itself has
      no queryable `IsCustom` field (a `SELECT IsCustom FROM Profile` errors with no-such-column), so
      read it through the profile-owned permission set instead:

      ```sql
      SELECT ProfileId, Profile.Name, IsCustom FROM PermissionSet WHERE IsOwnedByProfile = true
      ```

      Each row's `IsCustom` is that profile's flag — `false` = **standard** profile (grant will no-op),
      `true` = **custom** profile (grant applies). (Verified live: standard profiles — `Standard User`,
      `System Administrator`, `Minimum Access - Salesforce`, … — all return `IsCustom=false`.) Present
      the results as a single-select showing `Name` **and whether each is standard or custom**, so the
      admin sees up front which targets can actually take the grant. **Cap the picker: if there are
      three or fewer, list them all; if more than three, show the closest three plus a fourth option
      "Type the API name"** (an explicit type-it-in escape, also the fallback when the target isn't
      among the shown three).

      **When the admin TYPES a name (the "Type the API name" escape), validate then reconfirm — don't
      deploy straight off a typed string.** Two gates, in order:
      1. **Validate against the org.** Resolve the typed name against `Profile` (`SELECT Id, Name FROM
         Profile WHERE Name = '<typed>'`) — it must exist. If it doesn't resolve, **tell the admin it
         wasn't found and re-ask** — never deploy against an unresolved name. Resolve its `IsCustom` the
         same way (`SELECT IsCustom FROM PermissionSet WHERE IsOwnedByProfile = true AND ProfileId =
         '<resolved id>'`) so the standard-profile check below applies to typed names too.
      2. **Reconfirm the resolved target before proceeding.** Once it validates, echo back the
         **resolved `Name` (and Id)** and ask the admin to confirm it's the one they meant
         before moving on to the access-level question — e.g. *"Found `<Name>` (`<Id>`). Grant
         object permissions on this one? (yes / pick another)."* Only continue on an explicit yes; on
         "pick another," re-open the picker/typed-entry. This reconfirm applies to the typed path
         specifically — a name the admin typed is easy to fat-finger, so confirm the match before it
         feeds the deploy. (Picking a shown option is already an explicit selection and needs no extra
         reconfirm.)

      **If the chosen profile is STANDARD (`IsCustom=false`), stop before deploying and offer the
      remediation** — a Metadata API `<objectPermissions>` deploy against it silently no-ops (see the
      two-failure-modes note above), so deploying anyway would look like it worked and change nothing.
      Tell the admin plainly and offer the two real paths:

      > `<Profile>` is a **standard profile**. Salesforce doesn't let object permissions on standard
      > profiles be set through the API, so a grant here would silently do nothing. Two options:
      > - **Use the Step 5 permission sets instead (recommended)** — assign `FlexibleHierarchyManager`
      >   or `FlexibleHierarchyAdmin` to the specific users; that grants FH object access per-user
      >   without touching the profile.
      > - **Clone this standard profile to a custom one**, grant the object permissions on the clone,
      >   then reassign the affected users to it. Note: cloning does **not** move existing users —
      >   they stay on `<Profile>` until each is reassigned to the new custom profile (a base-profile
      >   change, heavier than a permission-set assignment).

      Only proceed to a deploy on the clone path once the admin picks it and names/confirms the custom
      clone (create it via a `Profile` MDAPI deploy or in Setup, then re-run the picker against the new
      custom profile). Otherwise route them to Step 5 and record `object_permissions` as
      redirected-to-permission-sets. **Never deploy `<objectPermissions>` against a standard profile.**
   2. **Which access level** on the three objects (single-select):
      - **Read-only** — `allowRead` only.
      - **Full CRUD** — `allowRead` + `allowCreate` + `allowEdit` + `allowDelete`.

      The chosen level is what lands on the master `FlexibleHierarchy`; the two detail objects inherit
      it — so there's nothing to differ per object.

   Deploy via `/headless/metadata` as a `Profile` component carrying a
   `<objectPermissions>` block for **`FlexibleHierarchy`** only — with `<object>` set to the API name and the
   `<allowRead>`/`<allowCreate>`/`<allowEdit>`/`<allowDelete>`/`<viewAllRecords>`/`<modifyAllRecords>`
   booleans for the chosen level. **Emit only the master block — do NOT add `<objectPermissions>` blocks
   for `FlexibleHierarchyNode`/`FlexibleHierarchyNodeRela`.** They're detail objects (see above): the
   platform silently drops those blocks, so including them buys nothing and just makes the deploy look
   like it granted more than it did. This isn't a try-all-three-then-retry situation — grant the master
   in one deploy from the start. **Dry-run first**, deploy at the org's max
   supported API version (Step 1), then **re-read** the deployed `Profile` and confirm
   the `objectPermissions` for `FlexibleHierarchy` stuck — a deploy "Succeeded" is not proof (it will
   report success whether the grant applied, was dropped as a detail block, or was wholesale-ignored on
   a standard profile). The MDAPI profile re-read only
   projects back `<objectPermissions>` for objects **also named in the retrieve manifest**, and it can
   omit detail objects entirely; the authoritative live check is the **`ObjectPermissions` sObject**.
   Query it for the master only — the two detail objects will never return a row, so don't treat their
   absence as a failure:

   ```sql
   SELECT SobjectType, PermissionsCreate, PermissionsRead, PermissionsEdit, PermissionsDelete
   FROM ObjectPermissions
   WHERE Parent.ProfileId = '<profileId>' AND SobjectType = 'FlexibleHierarchy'
   ```

   **Read the result against the profile's custom-vs-standard flag — the two zero-row cases are NOT the
   same failure:**
   - **A `FlexibleHierarchy` row with the expected C/R/E/D booleans** → the grant applied. The absence
     of `FlexibleHierarchyNode`/`FlexibleHierarchyNodeRela` rows is **expected** (they inherit) — not a
     failure. This is the only success state, and it only happens on a **custom** profile.
   - **Zero rows on a STANDARD profile** → the whole grant was silently ignored because standard-profile
     object permissions aren't API-writable (the cause named in the two-failure-modes note above).
     Don't retry the same deploy — it will keep no-op'ing. Route to the clone-to-custom or Step-5
     permission-set remediation.
   - **Zero rows on a CUSTOM profile** → a genuine deploy problem (bad object name, skipped dry-run fix,
     wrong API version) — investigate the deploy, don't chalk it up to inheritance.

   **Two query
   traps that will make this fail — avoid both:** (a) `SobjectType` and the parent id take `=`, **never
   `LIKE`** — `LIKE` on an id field errors with `invalid operator on id field`, and there's no need to
   pattern-match when the only object that can carry a row is `FlexibleHierarchy`; (b) if you shell out
   to the `sf` CLI, redirect stdout to a file and parse the file — the `NODE_TLS_REJECT_UNAUTHORIZED=0`
   warning prints to stdout and corrupts inline JSON parsing. Report the resulting object permissions as
   a small table (object → C/R/E/D) grounded in that read, noting that `FlexibleHierarchyNode`/
   `FlexibleHierarchyNodeRela` inherit the master's access rather than carrying their own row.

   **Object permissions here cover the hierarchy object family only — NOT the validation-job-run
   objects.** The Flexible Hierarchy validation feature has its own objects — **`FlexHierVldJobRun`**
   (validation job run) and **`FlexHierVldJobRunItm`** (its line items) — and they are **not** part of
   the `FlexibleHierarchy` master/detail family, so granting `FlexibleHierarchy` object permissions in
   this step does **nothing** for them (confirmed live: a `Standard User` grant showed zero
   `FlexHierVldJobRun` rows, and a custom-profile `FlexibleHierarchy` grant doesn't reach them either).
   **Access to these two objects comes from the Step 5 role permission sets, not this profile step:**
   `FlexibleHierarchyManager` grants **Read** on the validation-job-run objects and
   `FlexibleHierarchyAdmin` grants **full CRUD**. If a user needs to run or read hierarchy-validation
   jobs, route them to the appropriate Step 5 permission set — don't try to add `FlexHierVldJobRun`/
   `FlexHierVldJobRunItm` to a profile here.
   (Help: the FSC "Set Tab Visibility and Object Permissions" step — link the real
   `help.salesforce.com` article ID once confirmed; not yet verified during authoring.)
7. **Configure hierarchy node roles** — the `FlexibleHierarchyNode.Role` field is a
   `DYNAMICENUM` flexField (`enum="FlexibleHierarchyNodeRole"` — confirmed in
   `FlexibleHierarchyNode.entity.xml`) backed by the **`FlexibleHierarchyNodeRole`**
   `StandardValueSet`, which ships **empty** — no `<standardValue>` entries — so there's nothing
   to pick from until this step populates it. **Read the current values first via a REST
   `describe`** — `GET /sobjects/FlexibleHierarchyNode/describe`, then read the `Role` field's
   `picklistValues` (don't assume it's still empty — an earlier run or another admin may have added
   values). **If it already has values, show them to the admin and ask whether more are needed
   before asking for anything**:

   > The hierarchy node-role picklist already has these values:
   > - `<value 1>`
   > - `<value 2>`
   >
   > Do you want to add more, or should I proceed to the next step?

   If the admin says no
   more are needed, **skip the deploy and move on** — the picklist is already populated; don't
   re-write it or ask for values just to re-confirm what's there. Only when the set is empty, or the
   admin wants to add values, do you **ask which role values they want on this picklist** — on its
   own, in its own message, not combined with any other step's question.

   **Ask this as an open, typed, free-text question — NOT a multiple-choice picker.** There is no
   canonical or default set of role values; the admin invents them for their org, so you cannot offer
   a fixed list of options to select from. Present it exactly as a fill-in-the-blank prompt where the
   admin types their own values:

   > What role values should the hierarchy node-role picklist have?
   > **Type your own values as a comma-separated list** — one entry per role.
   > For example, an org might use `Parent, Subsidiary, Branch`, but enter whatever roles fit your
   > hierarchy.
   > (I'll add these alongside any values already there.)

   Make the comma-separated format explicit in the prompt, and be clear the example is **illustrative
   only, not a suggested or default set** — don't present `Parent, Subsidiary, Branch` (or any other
   fixed list) as options to pick from, and don't pre-fill or default to them if the admin gives no
   answer (re-ask instead). Take the
   answer as a comma-separated list rather than guessing or
   defaulting to a fixed set, split on commas, trim whitespace per value, and echo the parsed list as
   you collect it (asking for the values is this step's query — no separate approval of the parsed list
   needed). **This picklist cannot be deployed through this skill's usual REST transport — deploy it
   via a real Metadata API retrieve/deploy (`sf project retrieve` / `sf project deploy`) instead**; see
   the confirmed facade-vs-MDAPI split below. Manual Setup entry is a fallback only, for when `sf` CLI
   isn't available — it is **not** the primary path.

   **⚠️ Confirmed live (re-verified 2026-09-29 against this org): the `/headless/metadata` dispatcher
   facade blocks BOTH directions for this metadata type, but genuine MDAPI works for both.**
   - **Facade READ is blocked — use REST `describe` instead.** `GET /sobjects/FlexibleHierarchyNode/describe`,
     then read the `Role` field's `picklistValues` (each entry carries `value`/`label`/`active`). **The
     dispatcher's `/headless/metadata` facade does not support reading a `StandardValueSet` at all** —
     confirmed against a live org: `GET .../headless/metadata?type=StandardValueSet&fullName=FlexibleHierarchyNodeRole`
     returns `400 UNSUPPORTED_OPERATION` — `"MetadataCrud does not support READ on type: StandardValueSet"`.
     This is a facade-level restriction on the **type**, not specific to this StandardValueSet's name —
     don't retry the same call with a different `fullName` expecting it to work.
   - **Facade WRITE is blocked too, but that is a facade limitation, not a platform one.**
     `updateMetadata` on `type=StandardValueSet`, `fullName=FlexibleHierarchyNodeRole` via
     `/headless/metadata` ALSO returns `400 UNSUPPORTED_OPERATION` — `"MetadataCrud does not support
     UPDATE on type: StandardValueSet"` — confirmed live. Don't retry this call expecting a different
     `fullName`, API version, or payload shape to change the result — it won't.
   - **Genuine MDAPI (`sf project retrieve` / `sf project deploy`) DOES write this type — confirmed
     live.** This was previously untested and wrongly assumed to dead-end the same way as the facade.
     Re-verified end-to-end on 2026-09-29: `sf project retrieve start --metadata
     "StandardValueSet:FlexibleHierarchyNodeRole"` succeeds and returns the current `<standardValue>`
     list (don't skip this — you need it to avoid dropping existing values, since the deploy replaces
     the full component); edit the retrieved XML to add the admin's new values alongside the existing
     ones; `sf project deploy start --metadata "StandardValueSet:FlexibleHierarchyNodeRole"` succeeds
     (`status: Succeeded`); and — per this SOR's own "a deploy result can lie, always re-read" rule — a
     follow-up `GET /sobjects/FlexibleHierarchyNode/describe` confirmed the new value actually landed in
     `picklistValues`. Use the same `sfdx-project.json` scaffold this SOR already sets up once for the
     Step 9 `RelationshipGraphDefinition` MDAPI deploy; no new transport is introduced. **This is now
     the primary write path for this step — only fall back to the manual Setup hand-off below if `sf`
     CLI genuinely isn't available in the environment.**
   - **Manual fallback (only when `sf` CLI is unavailable):** tell the admin to add the values themselves
     at **Setup → Object Manager → Flexible Hierarchy Node → Fields & Relationships → Role → New**.

   Do **not** reach for the Tooling API (`/tooling/sobjects/...`, `/tooling/query`) or a
   `StandardValueSet`/`GlobalValueSet` generic sObject to read or write these values — that surface does
   **not** service this StandardValueSet and the attempt dead-ends the same way as the facade (this is
   distinct from genuine MDAPI above, which is a different transport and does work). Step 9's
   `RelationshipGraphDefinition` deploy is no longer the only MDAPI write in this skill — this step now
   uses the same `sf` CLI MDAPI transport.
   ([Help: configure roles](https://help.salesforce.com/s/articleView?id=ind.fsc_flexible_hierarchies_configure_roles.htm))
8. **Add the hierarchy component to record pages.** The `flexible_hierarchy:flexibleHierarchyBase`
   Lightning component is offered — **not required** (`isRequired: false` on every entry) — on
   11 standard objects: Account, Contact, FinancialAccount, PartyRelationshipGroup, Opportunity,
   Case, BranchUnit, FinancialDeal, Product2, InsurancePolicy, Lead.

   **⚠️ You do NOT deploy or retrieve `flexible_hierarchy:flexibleHierarchyBase` as an LWC/Aura
   bundle — and its absence from the org's LWC/Aura bundle list does NOT mean it's UI-only.** It is a
   **platform/managed runtime component** provisioned by the FSC Flexible Hierarchy feature/license
   (the same `fsc-license-provisioned` precondition that gates this whole skill) — exactly like
   `force:highlightsPanel`, `force:relatedListContainer`, and `runtime_sales_activities:activityPanel`,
   none of which are retrievable source bundles either. So do **not** query the Tooling API for a
   `LightningComponentBundle`/`AuraDefinitionBundle`, try to `retrieve` the component, or conclude
   "not available via API → add it in Lightning App Builder" when no bundle turns up — **that
   conclusion is wrong.** You add it **by name** as a `<componentInstance>` inside a `FlexiPage` and
   deploy the *FlexiPage* via MDAPI (the exact XML + placement is spelled out below). Once the feature
   is provisioned the `flexible_hierarchy:flexibleHierarchyBase` reference resolves at deploy time; the
   Lightning App Builder path in the Skip option below is a manual *fallback*, never the required path.

   **Confirm the admin wants to do this step BEFORE asking which object(s) — a Yes/No gate first.**
   Placing the component is optional (`isRequired: false` on every object), and modifying record pages
   changes what users see, so don't jump straight into the object picker. Ask a simple go-ahead first,
   on its own — don't combine it with any other step's question:

   > Do you want to add the Flexible Hierarchy component to any record pages now?
   > - **Yes** — I'll ask which object(s) to place it on.
   > - **Skip this step** — no record-page changes; you can add the component later in Lightning App
   >   Builder.

   Only on **Yes** do you proceed to the object picker below. On **Skip**, record
   `record_page_objects` as skipped and move straight to the next step — don't show the object
   multi-select at all. (Label the opt-out per the user-facing-language rule — "Skip this step", never
   "Skip Step 8".)

   On Yes, **ask which object(s) they want the component on** (this is the step's query):

   > Which object(s) should get the Flexible Hierarchy component on their record page?
   > It's supported on: Account, Contact, FinancialAccount, PartyRelationshipGroup, Opportunity,
   > Case, BranchUnit, FinancialDeal, Product2, InsurancePolicy, Lead.
   > (Most setups only need it on the hierarchy's node object — Account by default.)

   **Present the 11 supported objects as a multiple-choice picker — NOT a free-text list.** The
   objects are a **fixed, known set**, so the admin selects from them; there is no "Enter objects
   (comma-separated)" / type-it-in option (that was a free-text answer this skill has since replaced —
   a typed list here is a dead option that can only introduce an unsupported name). Because the admin
   can want the component on *any subset*, present this as a **multi-select** over the 11 objects so
   they can pick one, several, or all:

   - The **11 supported objects** as selectable options: Account, Contact, FinancialAccount,
     PartyRelationshipGroup, Opportunity, Case, BranchUnit, FinancialDeal, Product2, InsurancePolicy,
     Lead. (`Account` is the default node object and the common single-object case — note it as the
     typical pick, but don't pre-select or force it.)
   - A **"Skip this step"** choice — placing the component is optional (`isRequired: false` on every
     object), so this is the way out; labelled per the user-facing-language rule above (never "Skip
     Step 8").

   Do **not** add any free-text / "Other" option and do **not** enumerate pre-baked combos (e.g.
   "Account + Contact") — a multi-select over the 11 already covers every subset. Selecting from the
   fixed set makes an unsupported object **structurally impossible**, so there's no typed list to
   parse, no allowlist re-check, and no reject-and-re-ask to perform — echo the chosen set back to the
   admin and proceed to deploy to exactly those objects.

   The config offers all 11, but a real
   setup typically only needs it on the confirmed node object (Account by default). The component is
   deployed as a standard MDAPI `FlexiPage` update, same pattern as other record-page component
   placements in this corpus — but **how** it lands depends on what record pages the object already
   has, so resolve that per object before deploying.
   ([Help: customize record pages](https://help.salesforce.com/s/articleView?id=ind.fsc_flexible_hierarchies_customize_record_pages.htm))

   **Always clone the object's CURRENTLY-ACTIVE page — never edit any page in place.** For each object
   the admin picked, determine its currently-active record page (its org-default `View` assignment —
   the same `actionOverride` the activation gate below reads/writes), then **clone that active page
   into a new `FlexiPage`** and add the component to the clone's **Related section**. This is the
   single path for both cases — whether the active page is a **custom `FlexiPage`** or the
   **system/out-of-box default**, you clone it rather than modifying it. Cloning (not in-place editing)
   keeps the page users currently see untouched until the admin explicitly activates the new one, so
   **the activation gate below always applies** (every chosen object produces a new, inactive page).

   To clone: **retrieve the object's currently-active `FlexiPage` from the live org via MDAPI** — do
   **not** copy from a baked-in sample or reconstruct the page from memory; the page users actually see
   is the only correct source. Issue an MDAPI **retrieve** with a `package.xml` manifest that names the
   active page as a `FlexiPage` member, e.g.:

   ```xml
   <?xml version="1.0" encoding="UTF-8"?>
   <Package xmlns="http://soap.sforce.com/2006/04/metadata">
       <types>
           <members>Account_Record_Page</members>
           <name>FlexiPage</name>
       </types>
       <version>66.0</version>
   </Package>
   ```

   Use the actual active-page `DeveloperName` resolved from the `View` `actionOverride` as the
   `<members>` value (add one `<members>` line per object when the admin picked several — the sample
   manifest the admin may supply can list `Account_Record_Page`, `Contact_Record_Page`, etc.), and pin
   `<version>` to the org's max supported API version (Step 1). Take the **retrieved** FlexiPage XML,
   copy its regions/content into a new `FlexiPage` (new `DeveloperName`/`masterLabel`), append the
   component to the Related section (see placement below), and deploy the clone. Never redeploy the
   existing active page with the component added — always land the change on a fresh clone built from
   the freshly-retrieved XML.

   - **⚠️ Grounding caveat — the *system default* may not be retrievable to clone.** This skill has
     confirmed against a live org that for objects like **Account, when the active page is the
     *system* default, that out-of-box page is generally NOT retrievable/customizable as a `FlexiPage`**
     — you can't clone what MDAPI won't hand you. When the active page is instead a **custom
     `FlexiPage`** (e.g. Account's `sfa__Account_rec_L`), it **is** retrievable and clones cleanly — the
     grounded example in the placement note below is exactly such a page. **If the active page can't be
     retrieved for cloning** (the system-default case), **do NOT fall back to a bare FH-only page — build
     a fresh COMPLETE `RecordPage` FlexiPage** (the grounded complete-page skeleton in the schema note
     below): highlights panel + record details + related lists + a sidebar Activities panel, WITH the
     Flexible Hierarchy component added to the Related tab. **A page carrying only the FH component would wipe the highlights panel,
     record details, and related lists the system default showed — and activating that as the org
     default is a destructive, org-wide UX regression** (this is a real bug the bare-page fallback
     caused). The fallback must reproduce the standard record-page furniture, not just the FH component.
     The fresh complete page is also inactive, so it runs the activation gate too — and because it is a
     **brand-new page, not the admin's existing layout**, the activation gate carries an EXTRA alert (see
     "Fallback case" in the activation gate below). What remains **not yet verified against the target
     org** is cloning the *system default* specifically — treat that branch as `inferred` (the
     complete-page skeleton itself is grounded from a real retrieved page on the same template), dry-run
     the complete page, and verify on the next org-backed run.

   Note inactive custom pages that are **not** the active page don't drive this — always clone whatever
   page is *currently active* (the one users see), not some stray inactive page.

   **⚠️ FlexiPage schema — get the region shape right or the deploy fails.** A `flexiPageRegions`
   region places components **only** through `itemInstances > componentInstance`, and **every
   `componentInstance` needs an `<identifier>`**. Do **not** put a bare `<componentInstances>` block
   (a component directly under the region, no `itemInstances` wrapper) — that fails dry-run with
   `Property 'componentInstances' not valid in version <n>.0` (confirmed against a live org). The
   highlights panel is **`force:highlightsPanel`** and it belongs in a **`header` `<type>Region</type>`**
   — do **not** use `flexipage:highlightsPanel` or drop a highlights panel into a plain content
   `Region`, which fails with "couldn't retrieve design time component information" (confirmed against a
   live org). Every page carries `<sobjectType>`,
   `<template><name>flexipage:recordHomeTemplateDesktop</name></template>`, and `<type>RecordPage</type>`
   — the root element is **`<type>`, never `<pageType>`** (a real deploy failure:
   `Element pageType invalid at this location in type FlexiPage`), and the template name is
   **exactly** `flexipage:recordHomeTemplateDesktop` — do **not** guess alternatives like
   `force_base_layout:BaseManagedLayout`, `force_base_layout:BaseLayout`,
   `lightning_record_page:RecordPageTemplate3Col`, or any `one:*` name; all of those have failed live
   with `Template <name> doesn't exist`, and there is no metadata-list way to enumerate valid
   templates (`FlexiPageTemplateBundle` isn't a real type) — they're platform-shipped, not
   discoverable org content.

   **Use the ready-to-copy sample instead of authoring this shape from prose.** A full,
   deploy-shaped XML for this exact fallback skeleton — header/main/sidebar regions, both tabs, the
   FH component placed in Related, every `<componentInstanceProperties>` filled in — is at
   [`references/flexipage-record-page-sample.md`](references/flexipage-record-page-sample.md), along
   with a table of every wrong template/element name that has actually failed a live deploy while
   improvising this page. Copy that sample rather than reconstructing the shape from the bullets
   below.

   **Grounded complete-page skeleton — the fresh-fallback shape (build this, NOT a bare FH-only page).**
   When you can't clone the active page and must build one (the system-default case above), reproduce
   this full shape so the result is a normal record page. It is grounded from a real retrieved record
   page on the same `recordHomeTemplateDesktop` template (`Security_Assurance_Team_Record_Page`), so it
   deploys cleanly. Regions and their contents:
   - `header` `<type>Region</type>` → `force:highlightsPanel` (identifier `force_highlightsPanel`)
   - `main` `<type>Region</type>` → `flexipage:tabset` (identifier `flexipage_tabset`, property
     `tabs=maintabs`)
   - `maintabs` `<type>Facet</type>` → two `flexipage:tab`s: one with properties `title=Standard.Tab.detail`,
     `body=detailTabContent`, `active=true`; one with `title=Standard.Tab.relatedLists`,
     `body=relatedTabContent`
   - `detailTabContent` `<type>Facet</type>` → `force:detailPanel` (identifier `force_detailPanel`)
   - `relatedTabContent` `<type>Facet</type>` → `force:relatedListContainer` (identifier
     `force_relatedListContainer`) **plus** `flexible_hierarchy:flexibleHierarchyBase` in its own
     `itemInstances` block (identifier `flexible_hierarchy_flexibleHierarchyBase`)
   - `sidebar` `<type>Region</type>` → `flexipage:tabset` (identifier `flexipage_tabset_sidebar`,
     property `tabs=sidebartabs`) — the template's third (right-hand) region
   - `sidebartabs` `<type>Facet</type>` → one `flexipage:tab`: `title=Activity`,
     `body=activityTabContent`, `active=true`
   - `activityTabContent` `<type>Facet</type>` → `runtime_sales_activities:activityPanel` (identifier
     `runtime_sales_activities_activityPanel`) — the standard Activities panel (log a call, new
     task/event, activity timeline)

   **⚠️ Do NOT add `<mode>Replace</mode>` on any facet in this fresh-build skeleton.** `<mode>Replace</mode>`
   is only valid when a page **overrides an existing parent template's region** — that's the clone case
   below (§"Grounded example — the Related facet AFTER inserting the component"), where you're editing a
   page retrieved from the org. A page built fully from scratch, like this fallback skeleton, has no
   parent region to override, so `<mode>Replace</mode>` on one of its facets fails dry-run (confirmed
   against a live org):
   `The '<facet>' region (type Facet) specifies mode 'REPLACE' but a parent region enabling that mode
   doesn't exist.` Omit `<mode>` entirely on every `flexiPageRegions` element you author fresh.

   That reproduces the standard record page — highlights, a Details tab (record detail), a Related
   tab (related lists) with the FH component in Related, and an **Activities panel in the right-hand
   sidebar**. **Always include the sidebar Activities panel** — the full three-region shape above is the
   fallback page to build; don't drop the sidebar. (Grounded: `runtime_sales_activities:activityPanel`
   in a `sidebar`-region tabset facet passes a dry-run on a live org at the org's max API version;
   the tab is titled `Activity` — a literal custom label, not the `Standard.Tab.activities` token.) A **Chatter** tab is deliberately NOT
   included here — `forceChatter:feed` in that facet fails dry-run ("component isn't allowed in the
   region … doesn't implement any of the region's allowed interfaces"), so the correct Chatter
   component/placement is `inferred` and unverified; don't add a chatter tab to this skeleton until it's
   grounded. The FH component still obeys the Related-facet placement rule below (resolve the facet from
   the tab whose `title=Standard.Tab.relatedLists` via its `body`). Only if even this complete build
   fails dry-run should you consider a reduced page — and if you do, say so in the activation alert.

   **Place the component in the Related section — resolve the region by tab, not by guessing.** The
   component goes into the cloned page's **Related** area — not the highlights panel, not a new
   top-of-page region. On a real Account record page the Related area is **not** a top-level
   `<type>Region</type>`; it's a **`<type>Facet</type>` region** whose content is surfaced through a
   `flexipage:tab`. Resolve it deterministically in the retrieved/cloned FlexiPage:

   1. Find the `flexipage:tab` `componentInstance` whose `title` property is
      **`Standard.Tab.relatedLists`** (the Related tab). Read its **`body`** property — that value is
      the **`name` of the facet `flexiPageRegions`** holding the Related content (commonly
      `relatedTabContent`). Don't hardcode the name; read it from the tab's `body` (custom pages can
      name the facet differently).
   2. In that facet region, **append a new `<itemInstances>` block** carrying a single
      `componentInstance` for `flexible_hierarchy:flexibleHierarchyBase` with its own unique
      `<identifier>` (e.g. `flexible_hierarchy_flexibleHierarchyBase`). Each `componentInstance` is
      wrapped in its **own** `<itemInstances>` element — that's the real shape (each related-area
      component sits in a separate `itemInstances` sibling), not multiple `componentInstance`s under
      one `itemInstances`.

   Preserve every existing component carried over from the source page (the highlights panel, the
   related-list container, activity panel, the tabset/tab wiring, etc.) — you're **adding** the
   component to the Related facet, not replacing the region's contents or its `<mode>Replace</mode>`.
   Keep the `itemInstances > componentInstance` shape and the `<identifier>` requirement from the rule
   above for the added instance.

   **Grounded example — the Related facet AFTER inserting the component into the retrieved page's XML**
   (from a real retrieved Account page, `parentFlexiPage=sfa__Account_rec_L`). This is the *insertion
   target*, not a page to author from scratch: you retrieve the live FlexiPage (above), locate its
   `relatedTabContent` facet, and add the FH component's `itemInstances` block — shown here as the
   first block, ahead of the page's existing merge-preview and related-list-container components, all
   of which stay:

   ```xml
   <flexiPageRegions>
       <itemInstances>
           <componentInstance>
               <componentName>flexible_hierarchy:flexibleHierarchyBase</componentName>
               <identifier>flexible_hierarchy_flexibleHierarchyBase</identifier>
           </componentInstance>
       </itemInstances>
       <itemInstances>
           <componentInstance>
               <!-- existing related-list container, preserved -->
               <componentName>force:relatedListContainer</componentName>
               <identifier>force_relatedListContainer</identifier>
           </componentInstance>
       </itemInstances>
       <mode>Replace</mode>
       <name>relatedTabContent</name>
       <type>Facet</type>
   </flexiPageRegions>
   ```

   That `relatedTabContent` facet is bound into the page by a `flexipage:tab`
   (`title=Standard.Tab.relatedLists`, `body=relatedTabContent`) sitting in the `maintabs` facet, which
   is the `tabs` of the `flexipage:tabset` in the page's `main` `<type>Region</type>` — so the resolve-
   by-tab walk in step 1 above lands you here.

   **Activation is a separate action from the deploy — confirm before activating.** Deploying the
   `FlexiPage` only *creates* the page; because this step **always clones into a new page** (the clone,
   or the fresh fallback page), the deployed page is always inactive and users still see the current
   page until it's assigned. **The activation gate therefore always applies** — every chosen object
   produced a new page. **After the deploy, always ask before activating** — activation is the one
   write in this step that keeps an **extra** explicit confirm on top of the per-step
   query-then-write-then-advance cycle (see the root skill's strict-sequential-mode section),
   because it changes what every user sees.

   **This deploy-vs-activation split is internal mechanics — do NOT narrate it to the admin.** The
   paragraph above is authoring rationale for you, not a message to relay. Don't announce things like
   "Deploy only — activation is a separate confirmed step after," or explain that the deploy merely
   creates an inactive page; just perform the deploy quietly and go straight to the activation
   question below. The admin should see only the deploy result (done) and the activation Yes/No — not
   a lecture on why the two are separate.

   **Before presenting the activation prompt — check for an existing higher-precedence
   assignment.** Activating only writes the object's **org-default** record-page assignment (the
   `View` `actionOverride` below), which is the *lowest* tier in Lightning's page-assignment
   precedence (App default > App + record type + profile > App + record type > App + profile >
   **Org default**). Every tier above org-default lives on a `CustomApplication`'s `Metadata`, as
   an entry with `actionName=View`, `type=Flexipage`, `pageOrSobjectType=<object>` — but **App
   Default and Profile Default are two separate sibling arrays, not one array split by an
   attribute**: `Metadata.actionOverrides` holds the App Default tier (no `profile` attribute) and
   the separate `Metadata.profileActionOverrides` array holds the Profile Default tier
   (admin-facing wording for the App + profile tier) — confirmed live as a distinct sibling field,
   not merged into `actionOverrides`; scanning only one misses a whole precedence tier. Rather than
   only caveating about this after the fact, check for one **before** asking the admin anything, via
   Tooling API SOQL (`GET /services/data/v66.0/tooling/query`) in two passes: (1) enumerate —
   `SELECT Id, DeveloperName FROM CustomApplication` with NO `Metadata` field and no `WHERE` clause
   (confirmed live: 200, returned all 31 apps in one call, unrestricted row count since `Metadata`
   wasn't selected); (2) per-app read — for each `DeveloperName` from pass 1, `SELECT Id,
   DeveloperName, Metadata FROM CustomApplication WHERE DeveloperName='<app>'` (confirmed live: 200,
   returns the app's full `Metadata` blob). Scan both `actionOverrides` and `profileActionOverrides`
   from pass 2 for a match on this object.

   **Every other transport for this read was tried live and failed — do not rediscover this from
   scratch:** `/headless/metadata` `readMetadata` on `type=CustomApplication` is NOT a substitute
   for pass 2 above — confirmed live: it actually succeeds (`200`, full metadata) for standard
   apps, but only when `fullName` carries the Metadata API's `standard__` prefix (e.g.
   `standard__Sales`); the bare `DeveloperName` from pass 1 404s `INVALID_CROSS_REFERENCE_KEY`
   instead, and two custom-named apps tried the same way 404'd too, so no working `fullName`
   convention for custom apps is confirmed. Since that prefix isn't derivable from the
   enumeration step, use the two-pass Tooling SOQL above instead of this transport.
   `/headless/metadata?type=CustomApplication` with no `fullName` (a bare list) 400s `INVALID_INPUT`
   ("Query parameters 'type' and 'fullName' are required") — no list-without-a-name mode either.
   `ActionOverride` is NOT a queryable sObject/Tooling type on its own — confirmed live: `400
   INVALID_TYPE` ("sObject type 'ActionOverride' is not supported"); it only exists nested inside
   `CustomApplication`/`CustomObject` `Metadata`. A bare bulk Tooling query selecting `Metadata` (or
   `FullName`) across every `CustomApplication` row at once, with no `WHERE` narrowing to one row,
   400s `MALFORMED_QUERY` ("query qualifications must specify no more than one row for retrieval")
   — either field forces exactly one row, hence the two-pass split above. Never call the `sf` CLI
   directly as the served step, and never scaffold a local DX project (`sfdx-project.json`, a
   `package.xml` manifest, a `retrieved/` output dir) to do this read — confirmed live: `sf project
   retrieve start --manifest package.xml` outside a DX project gets `InvalidProjectWorkspaceError`,
   and a full-org `sf` retrieve of every app also timed out/got killed live. None of these problems
   exist on the two-pass Tooling SOQL query above.

   - **No match found** → nothing to check; go straight to the standard/fallback prompt below.
   - **One or more matches found** → surface the conflict to the admin BEFORE the standard prompt
     (skip straight to the conflict prompt, don't show the plain org-default question first). If
     matches exist at more than one app/tier, lead with the highest-precedence one found (App
     Default before Profile Default) and just mention the others exist.

     > Heads-up: `<object>` already has a page activated as the **App Default for `<App Name>`**
     > (or: **Profile Default for `<Profile Name>` on `<App Name>`**, whichever was found).
     > Activating the new page as the **org default** won't change that — those users keep seeing
     > the existing page, not this one.
     > Do you want to **override** that assignment so it shows the new page instead, or just set
     > the **org default** (the new page will only show for users who don't already have a
     > more-specific assignment)?
     > - **Override the app/profile default** — ⚠️ this replaces the page currently assigned there;
     >   any configuration specific to that existing assignment is lost, and the change affects
     >   every user under that app/profile, not just you.
     > - **Just set the org default** — leaves the existing app/profile assignment untouched; those
     >   users won't see the new page.
     > - **Neither** — skip activation; the new page stays deployed but inactive.

     - **Override** → retrieve the matched `CustomApplication`'s current metadata, replace that one
       matched `actionOverrides` entry's `content` with the newly-deployed page's `DeveloperName`
       (keep its existing `profile`/`recordType`/`formFactor` attributes as-is — only `content`
       changes), leave every other entry in the array untouched, redeploy, then re-retrieve and
       confirm the entry now reads `content=<the new page>` before reporting success.
     - **Just set the org default** → fall through to the standard/fallback prompt below exactly as
       if no conflict had been found.
     - **Neither** → stop here; report the page as deployed-but-inactive, same as declining the
       standard prompt below.

   **Fallback case — when the page was freshly built because the active page couldn't be cloned, the
   activation question MUST carry an extra alert.** For a *cloned* page the admin is activating a copy of
   what they already had plus the FH component, so the standard prompt below is fine. But for the
   *system-default fallback*, the deployed page is a **brand-new complete page**, not the admin's
   existing layout — so before the Yes/No, tell them plainly what happened and what activating will do.
   This "couldn't clone, so I built X" disclosure is the one thing to surface in the fallback case (it
   is admin-facing, unlike the deploy-vs-activation mechanics above, which stay unnarrated). Use the
   fallback prompt instead of the standard one:
   > Heads-up: `<object>`'s current record page is the Salesforce **system default**, which can't be
   > retrieved to clone — so I built a **fresh complete page** (highlights panel, record details,
   > related lists, an Activities panel, plus the Flexible Hierarchy component). Activating it as the org default will
   > **replace** the current layout for every `<object>` user.
   > ⚠️ **Heads-up:** this sets the page as **`<object>`'s org default** — the lowest-precedence
   > tier. That only changes what's shown to users who don't already have a more-specific app- or
   > profile-level assignment (checked above); if one exists and you'd rather change that instead,
   > decline here and pick the override choice above, or use Lightning App Builder → **Activation**
   > later.
   > Activate this new page as the **org default** for `<object>` now?
   > - **Yes** — every `<object>` user sees this new page instead of the system default.
   > - **No** — it stays deployed but inactive and the system default stays in place; you can activate
   >   it later in Lightning App Builder.

   For the cloned-page case, the standard prompt applies:
   > The `<object>` record page is deployed, but it isn't active yet.
   > ⚠️ **Heads-up:** this sets the page as **`<object>`'s org default** — the lowest-precedence
   > tier. That only changes what's shown to users who don't already have a more-specific app- or
   > profile-level assignment (checked above); if one exists and you'd rather change that instead,
   > decline here and pick the override choice above, or use Lightning App Builder → **Activation**
   > later.
   > Activate it as the **org default** record page for `<object>` now?
   > - **Yes** — every `<object>` user sees this page.
   > - **No** — it stays deployed but inactive; you can activate it later in Lightning App Builder.
   - **No** (the default posture) → stop here; report the page as deployed-but-inactive and note it
     can be activated later in Lightning App Builder → Activation.
   - **Yes** → assign the deployed page as the **org default** record page for that object. The
     org-default assignment is **not** a field on the `FlexiPage` or a standalone metadata type —
     do NOT add an `<activations>` element to the `FlexiPage` XML itself (confirmed live: MDAPI
     deploy rejects it — `"Error parsing file: Element {http://soap.sforce.com/2006/04/metadata}
     activations invalid at this location in type FlexiPage"`). It
     is the object's **`View` `actionOverride`** on its `CustomObject`. Deploy a decomposed
     `CustomObject` fragment for the object carrying an `actionOverrides` block with
     `actionName=View`, `type=Flexipage`, `content=<the FlexiPage DeveloperName>` (App Builder's
     "Assign as Org Default" for desktop flips the `formFactor=Large` View override; set that one and
     leave the `Small`/phone override alone unless the admin asks). Scope it to the confirmed object
     only — do not touch app-, profile-, or record-type-level assignments. Dry-run first, deploy at
     the org's max supported API version (discovered in Step 1), then **re-read the object's `View` `actionOverride` and confirm it
     now reads `type=Flexipage` with `content` = the deployed page** — a deploy "Succeeded" is not
     proof it took (verified against a live org: after the CustomObject deploy, the Account `Large`
     View override re-read as `type=Flexipage`, `content=Account_Flexible_Hierarchy_Record_Page`,
     while the untouched form factors stayed `type=Default`). If the re-read still shows
     `type=Default`, report it as not activated and direct the admin to Lightning App Builder →
     Activation rather than reporting success.
9. **Create hierarchy type(s)** — deploy a **`RelationshipGraphDefinition`** metadata component.
   This is where the confirmed hierarchy type gets created.

   **Modality gate FIRST, before anything else in this step — Bespoke vs. Rule-Based.** Check
   `rule_based_pref_state`: only when it is `already-on` or `enabled` (i.e. `enableRuleBasedHierarchyPref`
   is actually on), ask the admin a multiple-choice modality question **before** the Path A/Path B
   fork below — on its own, in its own message, not combined with any other step's question:

   > This org has the Rule-Based Hierarchy preference enabled. How do you want to create this
   > hierarchy type?
   > - **Bespoke Configuration** — author nodes and relationships directly (the existing flow).
   > - **Rule Based Configuration** — author role-based rules (filters + automatic parent/child
   >   expansion) on top of the node list.

   When `rule_based_pref_state` is anything else (`skipped`, `declined-at-confirm`, or the pref was
   never reached because Step 4 was version-gated out), **skip this question entirely** — proceed
   straight to Bespoke exactly as before. Never ask the modality question when the preference isn't
   actually on.

   - **Bespoke Configuration chosen (or the question was skipped because the pref is off):**
     proceed exactly as documented below — no change from today's behavior.
   - **Rule Based Configuration chosen:** delegate instead to
     **`delegates_to: fsc-darksaber/fsc-flexible-hierarchy-configure-fsc-flexible-hierarchy-rule-based-graph-config-create`**
     (the fsc-flexible-hierarchy-rule-based-graph-config-create sub-skill) in place of the bespoke delegation below. It
     captures the same node list this step's bespoke path would, **plus** the `rules.graph.rootNode`
     rule tree (role, qualifying filters, and OneToMany/ManyToMany child relationships) before the
     same confirm-then-deploy-then-read-back flow. Record which modality was used in
     `hierarchy_type` for the end-of-step report. See
     [`../fsc-flexible-hierarchy-rule-based-graph-config-create/SKILL.md`](../fsc-flexible-hierarchy-rule-based-graph-config-create/SKILL.md) for
     the full flow and
     [`../fsc-flexible-hierarchy-rule-based-graph-config-create/references/rule-based-hierarchy-payload.md`](../fsc-flexible-hierarchy-rule-based-graph-config-create/references/rule-based-hierarchy-payload.md)
     for the payload schema — grounded in an admin-provided sample, not an exhaustively validated
     schema (see that reference's Grounding section).

     **⚠️ Do NOT compose or present a deploy plan yourself right after the admin picks Rule Based
     Configuration.** The very next turn is the sub-skill's own "Do you already have a Rule-Based
     hierarchy config ready to deploy, or should I build one with you?" fork — confirmed live: a run
     skipped straight from the modality choice to presenting a deploy summary with invented values
     (developer name, root object) and never asked that fork question at all. If you're about to
     describe field values for the hierarchy type without having asked it first, stop and ask it now.

   **The rest of this step (Bespoke path) is unchanged:** **Ask the "have a config or build one?"
   (Path A / Path B) fork FIRST, before asking for a name** — a Path A config already carries its
   `masterLabel`, so a name is only asked when building from scratch (Path B), never defaulted (there
   is no default hierarchy type). **The one write in this step — the `RelationshipGraphDefinition`
   deploy — is gated by an explicit confirm immediately before it** (the sub-skill shows the name +
   root object and asks for a go-ahead just before deploying). `RelationshipGraphDefinition`
   is a deployable MDAPI type (`metadataApiName="RelationshipGraphDefinition"`, `manageable`,
   `keyPrefix="06J"`), but this is always a **create** (never an update), and creation is the one
   write in this skill that does **not** go through the generic `/headless/metadata` facet used
   everywhere else — that facet's PUT is update-only for this type and 400s with
   `INVALID_CROSS_REFERENCE_KEY` ("Component does not exist") against a `DeveloperName` that doesn't
   exist yet (confirmed against a live org). The Tooling API's generic-sObject POST is
   `createable: true` for this type via `GET .../tooling/sobjects/RelationshipGraphDefinition/describe`,
   but for `GraphType: "FlexibleHierarchy"` specifically that POST is unreliable — confirmed live
   failing 5+ identical retries with `INVALID_FIELD_FOR_INSERT_UPDATE` on `GraphType`, on an org where
   the Setup UI and an MDAPI deploy of the identical payload both succeeded immediately after.
   **Create it via MDAPI deploy instead:** `sf project deploy start --source-dir <path>` against a
   `relationshipGraphDefinitions/<DeveloperName>.relationshipGraphDefinition-meta.xml` component with
   the same field shape JSON would carry, HTML-escaped into XML — see
   [`../graph-config-create/references/hierarchy-type-payload.md`](../graph-config-create/references/hierarchy-type-payload.md)
   for the exact shape and full transport-failure writeup. Not a Java service call either way. There is no
   `FlexibleHierarchyType` sObject despite the `FlexibleHierarchySetup` Setup node's name; a
   `FlexibleHierarchy` instance's `HierarchyTypeReferenceId` is a lookup to this record — creating
   the actual `FlexibleHierarchy` instance is out of scope for this skill.

   **Read-back — query only the sObject's queryable columns.** When you verify the deployed
   component by SOQL, `RelationshipGraphDefinition` exposes just `Id`, `IsDeleted`, `DeveloperName`,
   `Language`, `MasterLabel`, `NamespacePrefix`, and the audit fields
   (`CreatedDate`/`CreatedById`/`LastModifiedDate`/`LastModifiedById`/`SystemModstamp`) — confirmed against a live org. **`GraphType`, `RootObject`, and `IsActive` are NOT queryable columns** (they
   live inside `relationshipGraphDefVersions`/`graphDefinition`); selecting or filtering on them fails
   with `INVALID_FIELD` ("No such column"). Verify existence with
   `SELECT Id, DeveloperName, MasterLabel FROM RelationshipGraphDefinition WHERE DeveloperName='<Name>'`
   — don't reach for `GraphType`/`RootObject`/`IsActive` in the read-back.

   **Build the bespoke config — delegate, do not re-author it here.** On the **Bespoke
   Configuration** branch of the modality gate above (the only branch when the Rule-Based preference
   isn't on), this step
   **`delegates_to: fsc-darksaber/fsc-flexible-hierarchy-configure-graph-config-create`** (the
   graph-config-create sub-skill) — nodes and relations authored directly. See the out-of-scope note
   in the End state below for what's still deferred outside the two modality branches above. That
   sub-skill owns the whole bespoke flow: the Path A
   (admin brings a config) / Path B (build from scratch) branch **asked first** (Path A reads the type
   name from the config's own `masterLabel`; only Path B asks for a name — no description either way,
   that element is invalid on `RelationshipGraphDefinition`),
   root/node object selection from the 11-object allowlist, per-object graph/grid
   view fields, node-relationship definition, the `flexibleHierarchy`-placement pitfall, the confirm
   shown right before the deploy, the deploy-and-read-back of the `RelationshipGraphDefinition`
   component, and the full per-field
   checklist in [`../graph-config-create/references/hierarchy-type-payload.md`](../graph-config-create/references/hierarchy-type-payload.md).
   Invoke it, don't inline the config-building logic — this keeps Step 9 a thin gate over the reusable
   sub-skill rather than duplicating (and drifting from) it.
   ([Help: create hierarchy types](https://help.salesforce.com/s/articleView?id=ind.fsc_flexible_hierarchies_create_hierarchy_types.htm))

## End state

- Org connectivity confirmed and prerequisites (edition, Flexible Hierarchy license/org
  permission, ARC license/org permission, admin access) reported as an
  itemized ✅/❌ checklist, even when all pass
- Flexible Hierarchies feature enabled — `IndustriesSettings.enableFlexibleHierarchyPref`
  confirmed `true` by re-read, not just a reported deploy. This preference is not reversible
  (no supported way to turn it back off), so the deploy only happens after a single explicit
  go-ahead confirm
- (Optional, irreversible) Rule-Based Hierarchy preference — `enableRuleBasedHierarchyPref` — handled
  per the admin's choice: either **skipped** at the opt-in gate, reported **already-on** by the
  check-before-write read, **declined** at the "cannot be disabled" double-confirm, or **enabled** and
  confirmed `true` by re-read. Never turned on without both the opt-in Yes and the explicit
  irreversibility confirmation. Authoring the actual `rules.graph.rootNode` tree — role labels,
  filters, and OneToMany/ManyToMany child relationships — is now in scope, but only as Step 9's
  Rule-Based branch (see below); Step 4 itself only flips the org preference, it does not author
  any rule content
- Existing permission-set assignments surfaced to the admin up front and confirmed as-is when no
  changes are needed (the step is skipped in that case); otherwise, for every target user
  individually: the permission set they need (one of exactly `FlexibleHierarchiesUser` /
  `FlexibleHierarchyManager` / `FlexibleHierarchyAdmin` — a fixed three-option pick, no typed/other
  option) collected via the per-user query — never all three, and never a permission set applied to a
  user who wasn't individually asked. Each user is **confirmed with a single per-user go-ahead
  immediately before that user's assignment is written** (pick → role → ARC → confirm → write, then
  offer the next user) — a simple yes/change/skip right before each write, not a batched plan-review
  of everyone at once
- ARC access treated as **required** for every user to work with hierarchies, defaulted to Yes and
  assigned per-user via whichever permission set (`FSCSales` / `FSCService` /
  `FinancialServicesCloudExtension`) is actually present on this org — resolved once up front, not
  assumed to be `FSCSales` (same check-then-assign discipline as the Flexible Hierarchy permission
  set), unless the admin explicitly declined it for a specific user
- (Optional) Object permissions granted to the admin-chosen **profile** via
  `<objectPermissions>` on the master **`FlexibleHierarchy`** (the detail objects
  `FlexibleHierarchyNode`/`FlexibleHierarchyNodeRela` inherit it and can't carry their own), confirmed
  by an `ObjectPermissions` read — or the step skipped by the admin (the Step 5 role sets already cover
  master-object CRUD). This step grants via a profile only; the permission-set path is out of scope
- Existing hierarchy node-role picklist values surfaced to the
  admin and confirmed as-is when no more are needed (the deploy is skipped in that case) —
  otherwise new values collected from the admin (comma-separated) and merged onto the existing
  `FlexibleHierarchyNodeRole` `StandardValueSet` via `updateMetadata`
- Hierarchy type created for the confirmed type (e.g. Legal Entity) — **Bespoke** by default, or
  **Rule-Based** when `rule_based_pref_state` is `already-on`/`enabled` and the admin picked it at
  the modality gate (`hierarchy_config_mode`). Either way, the Path A / Path B fork is asked first (a
  name is only asked when building from scratch, since a Path A config carries its own
  `masterLabel`), and a `RelationshipGraphDefinition` component **deployed only after an explicit
  confirm shown right before the deploy** (name + root object) via **MDAPI deploy**
  (`sf project deploy start --source-dir <path>`) — not the Tooling API POST, which fails
  unreliably for `GraphType: "FlexibleHierarchy"` — from the admin's own config or one
  built with them, confirmed by read-back. The Rule-Based path additionally builds the
  `rules.graph.rootNode` tree (role, filters, OneToMany/ManyToMany child relationships) before that
  same confirm-then-deploy
- Hierarchy view component placement decided with the admin (multi-select over the 11 supported
  objects) and, per chosen object, added to the **Related section** of a **clone of the object's
  currently-active page** (whether that active page is custom or the system default; falling back to a
  fresh page when the active page can't be cloned) — never editing any page in place. Because every
  chosen object produces a new page, activation is always confirmed with the admin — first checking
  every `CustomApplication` for an existing App Default / Profile Default assignment on that object
  and, if one exists, letting the admin choose to override it there instead of (or as well as) the
  org default. Whichever assignment was written is verified by re-read to confirm it points at the
  deployed page (left deployed-but-inactive when the admin declined activation entirely)

## Gotchas learned from the Setup Discovery config

- **Feature enablement is two layers, not one.** The **Flexible Hierarchy** org permission is a
  license/provisioning-controlled org permission — not something this skill or an admin can
  flip; it comes from SKU/entitlement. `OrgPreferences.FlexibleHierarchyPref` is the genuine
  admin-toggleable preference (`editAccess` requires the org permission + admin + `ViewSetup`),
  and it's what Step 3 actually deploys. If the org permission is missing, the preference's
  access gate blocks the deploy from taking effect even though the deploy itself may report
  "Changed" — always re-read the setting after deploying to confirm it actually stuck. This
  preference is also **not reversible** — once turned on, there is no supported way to turn it
  back off — so Step 3 asks a single go-ahead confirm before deploying (lighter than Step 4's
  double-confirm, since Step 4 gates a second, independently-irreversible preference stacked on
  top of this one).
- **Rule-Based Hierarchy is a SECOND, one-way preference sitting beside the base feature.**
  `OrgPreferences.RuleBasedHierarchyPref` / `IndustriesSettings.enableRuleBasedHierarchyPref` is a
  sibling of `enableFlexibleHierarchyPref` in the same `IndustriesSettings` metadata, but the two do
  not surface at the same API version: `enableFlexibleHierarchyPref` (Step 3) is present in the
  retrieved xmlRep from **v66.0+**, whereas `enableRuleBasedHierarchyPref` appears only from **v68.0+**
  and is absent from the xmlRep entirely at v66.0/v67.0 (grounded live: retrieving the same FSC org at
  v68 returned both `<enableFlexibleHierarchyPref>true</enableFlexibleHierarchyPref>` and
  `<enableRuleBasedHierarchyPref>false</enableRuleBasedHierarchyPref>`, while the v66.0 and v67.0
  retrieves returned only the `enableFlexibleHierarchyPref` element). So don't assume RBH is queryable
  wherever the base feature is — it follows Step 4's version gate: available only when the org's pinned
  max version is **v68.0 or higher**, silently skipped at v66.0/v67.0. Two things warrant an
  *extra* gate here beyond Step 3's single confirm, even though both preferences are equally
  irreversible: (1) this one is **optional** — many admins don't need Rule-Based mode at all — so
  Step 4 requires an explicit double-confirm (opt-in, then a second confirm naming the
  irreversibility) to guard against accidentally opting into a permanent, org-wide mode change
  that wasn't actually wanted; Step 3's base feature isn't optional in that sense (nearly every
  Flexible Hierarchy setup needs it), so one confirm suffices there; and (2) an org that already has
  `FlexibleHierarchyPref` on can (rarely) already have this on too, so Step 4 does a
  check-before-write MDAPI read and skips the deploy when it's already `true`. This step only flips the
  preference; authoring rule configuration itself happens later, conditionally, at Step 9's modality
  gate (see [`../fsc-flexible-hierarchy-rule-based-graph-config-create/SKILL.md`](../fsc-flexible-hierarchy-rule-based-graph-config-create/SKILL.md)).
- **ARC has no enablement preference at all — it's permission-only.** The **ARC** org permission
  gates the `RelationshipGraphDefinition` object and the user-level ARC permission directly, with
  no `OrgPreferences.*` toggle sitting on top the way `FlexibleHierarchyPref` does for Flexible
  Hierarchy. That's why Step 2 only *checks* for it (report ✅/❌) rather than Step 3 having a
  matching "enable ARC" sub-step — there's nothing to toggle; it's provisioned or it isn't. The
  user-level grant itself is headless too — Step 5 assigns whichever standard permission set
  (`FSCSales` / `FSCService` / `FinancialServicesCloudExtension`) actually grants it on this org,
  resolved dynamically rather than assumed to be `FSCSales` — not a Setup-UI-only action.
  (Assuming `FSCSales` unconditionally is a real failure mode: orgs provisioned via
  the `FSCServiceAddon` SKU carry `FSCService` instead and have no `FSCSales` permission set at
  all, so a hardcoded check fails Step 5's pre-check outright on those orgs.)
- **Not everything here is `dispatch`-dispatchable, but fewer steps are Setup-UI-only than
  the original config implied.** This config describes a Setup UI checklist, not a headless API
  contract, and See [`../../PLAN.md`](../../PLAN.md)'s step-type → transport mapping table for
  the full picture — but two steps originally modeled as bare `setup_discovery__Url` deep links
  turned out to have confirmed headless mechanisms during authoring: ARC access (Step 5, via
  whichever ARC-granting permission set is resolved present on the org) and hierarchy node roles
  (Step 7, via `updateMetadata` on the
  `FlexibleHierarchyNodeRole` `StandardValueSet`). `setup_discovery__UserAssignment`,
  `setup_discovery__RecordPage`, and `setup_discovery__OrgPreference` steps were already
  concretely automatable.
- **Object permissions (`EnhancedProfiles`) are an optional step (Step 6), not out of scope.**
  Object CRUD is authored as `<objectPermissions>` on a **`Profile`** (this step grants via a profile
  only — the permission-set path is intentionally out of scope here); the step is skippable. A profile
  edit is heavier than a permission-set change — it hits every user assigned to that profile — so the
  offer says so and defaults to letting the admin skip. If they skip, the Step 5 role sets already
  cover master-object CRUD. **Object CRUD only lands on the master `FlexibleHierarchy`.** `FlexibleHierarchyNode` and
  `FlexibleHierarchyNodeRela` are master-detail children of `FlexibleHierarchy` (`FlexibleHierarchyId`,
  `relationshipOrder 0`), so they inherit object access from the master and can't hold their own
  `<objectPermissions>` — a deploy carrying detail-object blocks reports success but silently drops
  them (confirmed against a live org). Grant CRUD on the master and verify via the `ObjectPermissions`
  sObject, not the deploy response.
- **OWD sharing (`SecuritySharing`) is out of scope — it can't be set headlessly for
  `FlexibleHierarchy`.** OWD is the `<sharingModel>` element inside the object's own `CustomObject`
  metadata, but `FlexibleHierarchy` is a **non-customizable standard entity**: the CustomObject MDAPI
  channel rejects both retrieve and deploy for it (`Can't deploy non-customizable CustomObject named:
  FlexibleHierarchy`, confirmed against a live org), and there is no "SecuritySharing" MDAPI type
  (that string is only the Setup UI node id). The current OWD value is *readable* via
  `EntityDefinition.InternalSharingModel` but not *writable* headlessly — changing it is a Setup →
  Sharing Settings UI action, so this skill does not attempt it. (The detail objects read as
  `ControlledByParent` and follow the master's OWD regardless.)
  **`PermSets` is still not part of this skill** — it's used only by the deferred
  `manageDataCloudObjectPermissions` step in `unlockAdvancedFunctionality` (granting Flexible
  Hierarchy object permissions to the Data Cloud integration permission set), which stays out of scope.
- **`isRequired: false` on every record-page object** — the config offers placement on 11
  objects but mandates none of them. Don't deploy the component to all 11 by default; confirm
  scope with the admin first.

## Permission sets this skill may assign (from the per-user permission-set query)

Three role permission sets exist — `FlexibleHierarchiesUser`, `FlexibleHierarchyManager`,
`FlexibleHierarchyAdmin` — but a given user needs exactly **one**, matching their intended role.
When there are multiple target users, **ask the permission set separately for each user** — different users
on the same request can legitimately need different permission sets; don't assign more than one per
user, and don't apply one answer to the whole batch. These three are a **fixed, complete set** — the
per-user role picker presents exactly them, with no typed/"Other" fourth option. For each user,
gather their role + ARC choice, **confirm that one user with a per-user go-ahead, and assign them
immediately before moving to the next user** (Step 5's per-user confirm-then-write) — a simple
yes/change/skip right before each write, not a batched plan-review of everyone at once. No further
canonical-list reference doc exists yet for this skill (unlike `icm-setup`, which has a
dedicated `licensing-and-permission-sets.md`); these three names are the complete set per the
Setup Discovery config's `assignmentSources`.

Separately, an ARC-granting permission set is assigned per user for ARC access — it's not a
Flexible Hierarchy role permission set, but ARC is **required** to work with hierarchies, so it's
defaulted to Yes and assigned alongside the user's role permission set unless the admin explicitly
declines it for that user (Step 5). **Which permission set that is varies by org/SKU — resolve it,
don't hardcode it.** `FSCSales` (label "FSC Sales") is the common case, but an org provisioned via
the `FSCServiceAddon` SKU carries `FSCService` instead and has no `FSCSales` permission set at
all; `FinancialServicesCloudExtension` is a third known carrier. Step 5 queries which of these
three exist on the org once, up front (`arc_permset`) — using the one present, asking the admin to
pick when more than one is, and reporting the gap as blocked if none is — rather than assuming
`FSCSales`.

Mechanically: check via `SELECT Id FROM PermissionSetAssignment WHERE AssigneeId = :userId AND
PermissionSetId = :permSetId`; assign via a `PermissionSetAssignment` create
(`AssigneeId`/`PermissionSetId`) on that user's per-user go-ahead (the Step 5 per-user confirm right
before each write is the one gate — no separate batched plan-review on top). `DUPLICATE_VALUE`
on that create = already assigned = success, not an error.

<!-- skill-validate: ignore-start -->
<!-- codey:operations start -->
## Operations Reference

Operations this skill uses — routing and dependency reference.

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `step-1-confirm-org-connectivity` | discovery | — | `GET /services/data/` | — |
| `step-2-validate-prerequisites` | validate | — | `GET /services/data/v66.0/query` | `step-1-confirm-org-connectivity` |
| `step-3-enable-flexible-hierarchy-pref` | write | — | `PUT /services/data/v66.0/headless/metadata` | `step-2-validate-prerequisites` |
| `step-3-verify-flexible-hierarchy-pref` | verify | — | `GET /services/data/v66.0/headless/metadata?type=IndustriesSettings&fullName=Industries` | `step-3-enable-flexible-hierarchy-pref` |
| `step-4-enable-rule-based-hierarchy-pref` | write | — | `PUT /services/data/v68.0/headless/metadata` | `step-3-verify-flexible-hierarchy-pref` |
| `step-4-verify-rule-based-hierarchy-pref` | verify | — | `GET /services/data/v68.0/headless/metadata?type=IndustriesSettings&fullName=Industries` | `step-4-enable-rule-based-hierarchy-pref` |
| `step-5-resolve-arc-permission-set` | discovery | — | `GET /services/data/v66.0/query` | `step-2-validate-prerequisites` |
| `step-5-assign-user-permission-sets` | write | — | `POST /services/data/v66.0/sobjects/PermissionSetAssignment` | `step-5-resolve-arc-permission-set`, `step-3-verify-flexible-hierarchy-pref` |
| `step-6-grant-object-permissions` | write | — | `PUT /services/data/v66.0/headless/metadata` | `step-5-assign-user-permission-sets` |
| `step-6-verify-object-permissions` | verify | — | `GET /services/data/v66.0/query` | `step-6-grant-object-permissions` |
| `step-7-read-node-role-picklist` | discovery | — | `GET /sobjects/FlexibleHierarchyNode/describe` | `step-3-verify-flexible-hierarchy-pref` |
| `step-7-configure-node-role-picklist` | write | — | `FlexibleHierarchyNode.Role.configure` | `step-7-read-node-role-picklist` |
| `step-8-add-record-page-component` | write | — | `POST /services/data/v66.0/headless/metadata` | `step-3-verify-flexible-hierarchy-pref` |
| `step-8-check-existing-app-profile-default` | discovery | — | `GET /services/data/v66.0/tooling/query` | `step-8-add-record-page-component` |
| `step-8-activate-record-page-component` | write | — | `PUT /services/data/v66.0/headless/metadata` | `step-8-add-record-page-component`, `step-8-check-existing-app-profile-default` |
| `step-8-verify-record-page-activation` | verify | — | `GET /services/data/v66.0/headless/metadata?type=CustomObject&fullName={object}` | `step-8-activate-record-page-component` |
| `step-8-override-app-profile-default` | write | — | `PUT /services/data/v66.0/headless/metadata` | `step-8-check-existing-app-profile-default` |
| `step-8-verify-app-profile-override` | verify | — | `GET /services/data/v66.0/tooling/query` | `step-8-override-app-profile-default` |
| `step-9-check-existing-hierarchy-types` | discovery | — | `GET /services/data/v66.0/tooling/query` | `step-3-verify-flexible-hierarchy-pref` |
<!-- codey:operations end -->
<!-- skill-validate: ignore-end -->
