---
name: industries-icm-act5-genai-suggested-assessments-configure
description: "Act 5 of Health Cloud ICM setup — set up Gen AI Suggested Assessments (Agentforce recommending which assessment to run). Detect the provisioned license stack first and hard-stop if absent, deploy the three assessment-AI preferences, create and assign the Unmetered User Based AI permission set, assign the assessment perm sets (including Assessment Envelope for entity access), then report the external Salesforce-managed release setting and the manual tail this skill cannot automate. Standalone reference for the icm-setup skill's fifth phase."
metadata:
  version: "1.0"
---

# Act 5 of 8 — Gen AI Suggested Assessments

Part of the [`icm-setup`](../../SKILL.md) skill — the **fifth of eight acts**. For an
unqualified "set up ICM" this runs after [Act 1](../act1-prereqs/SKILL.md) →
[Act 2](../act2-discovery-framework/SKILL.md) → [Act 3](../act3-icm-toggles/SKILL.md) →
[Act 4](../act4-record-page/SKILL.md), and is followed by
[Act 6](../act6-mcg-integration/SKILL.md) (full MCG integration) → Act 7 → Act 8. It is **also runnable standalone**
("just set up Gen AI suggested assessments") — in that mode it re-checks and, where it can,
re-enables the Act 1–3 prerequisites the feature depends on before doing its own work (see
*Standalone entry* below).

**Gen AI Suggested Assessments is mostly gated, not mostly togglable.** The automatable surface
is small — three `IndustriesSettings` preferences, one user permission, plus perm-set assignment
— but "make it actually work" is dominated by a **provisioned license bundle** and a **Salesforce-managed
release setting**, neither of which any customer transport can flip. So this Act's discipline is:
**detect the license stack first, hard-stop with a named add-on if it's absent, deploy the prefs,
create/assign the perm sets on confirmation, and honestly report the release setting + the manual tail** —
never let a green pref-read stand in for "the feature works." Full backing analysis (gate formula,
exact names, the unactivatable shipped flow):
[`../../references/genai-suggested-assessments.md`](../../references/genai-suggested-assessments.md).

## The one feature this Act sets up

The admin asked for "Gen AI Suggested Assessments" — Agentforce recommends *which* assessment a
care coordinator should run. Master pref `enableGenAISuggestedAssmts` (min API 262); user perm
`SuggestedAssessmentGenAIUserAccess` (granted by the `SuggestedAssessmentGenAIPsl` perm set,
label "Suggested Assessments").

Do **not** conflate it with a sibling feature that shares the license stack but is **out of
scope** here:
- *Assessment Question Generation* (`GenAIAssessmentQuestions`) — a separate feature/license.

## License stack — DETECT FIRST, hard-stop if absent

This is the gating unknown for any given org, and the one place this Act stops rather than
degrades. Agentforce setup is a prerequisite, and three entitlements are required:

- **FlexCreditsMeteringAddOn OR UniversalCreditMetering** — the credit-metering bundle.
- **AgentforceForHealthCloudAddon** — Agentforce for Health Cloud.
- **UnmeteredUserBasedAIAddOn** — unmetered user-based AI.

**Detect via the queryable `*Psl` proxies, never the `*AddOn` names** (those don't exist as
`PermissionSetLicense` rows in real orgs and false-negative every check — the same lesson as
Act 1's license detection):

| Required entitlement | Queryable proxy — `PermissionSetLicense.DeveloperName` | On absence |
|---|---|---|
| Unmetered User Based AI | `UnmeteredUserBasedAIPsl` | **HARD STOP** |
| Agentforce for Health Cloud | `HealthCloudAssistiveAgentPsl` | **HARD STOP** |
| Credit metering (Flex/Universal) | *provisioned org perm — no reliable queryable PSL proxy* | **report-only** (best effort) |

```sql
SELECT DeveloperName, TotalLicenses, UsedLicenses FROM PermissionSetLicense
WHERE DeveloperName IN ('UnmeteredUserBasedAIPsl','HealthCloudAssistiveAgentPsl')
```

If **either** `UnmeteredUserBasedAIPsl` or `HealthCloudAssistiveAgentPsl` returns zero rows:
**stop and name every missing entitlement explicitly** — don't just say "a license is missing."
List each one the org lacks by its friendly name (and the add-on that provides it), e.g.
*"Gen AI suggested assessments can't be set up — your org is missing: Unmetered User Based AI
(add-on `UnmeteredUserBasedAIAddOn`) and Agentforce for Health Cloud (add-on
`AgentforceForHealthCloudAddOn`). Ask your account team to provision these, then re-run."*
Report the full list of what's absent, not the first miss. Do not deploy prefs or attempt the
perm-set creation into a feature that will stay completely dark. `UniversalCreditMetering` /
`FlexCreditsMeteringAddOn` are provisioned org perms with no reliable queryable proxy, so treat
them as **report-only** — name them too as "must also be provisioned (can't be verified from
here)", but don't make a metering-proxy miss the sole basis for the stop.

### Confirmed Agentforce-org license bundle (prerequisite context)

The earlier open question — "which org-farm licenses are strictly
required" — is now resolved. A fully-provisioned Agentforce-for-Health-Cloud org carries the
entitlement bundle below; this is the confirmed required Agentforce-org set (quantities are
org-sizing, **not** requirements — ignore them). The three feature-gating entitlements
(**AgentforceForHealthCloudAddOn**, **UnmeteredUserBasedAIAddOn**, and
**FlexCreditsMeteringAddOn / UniversalCreditMetering**, **bold** below) are a *subset* of it.

**These are subscription/product-view names (mostly `*AddOn`s) — do NOT feed them into a
`PermissionSetLicense` query.** `*AddOn` names are not PSL rows and false-negative every check
(the same lesson as the detection table above). They are *prerequisite context* the admin / their
account team confirms out-of-band; the skill's programmatic gate stays the two `*Psl` proxies +
credit-metering above.

- **Core / platform:** Salesforce, EinsteinServices, IdentityUser1SeatAddOn, DataStorage500MB,
  FileStorage50MB, LightningConsole
- **Agentforce agents & builder:** AgentforceBuilderAddon, AgentforceEmployeeAgentAddOn,
  **AgentforceForHealthCloudAddOn**, AgentforceServiceAgentAddon, AgentforceServiceAgentManagerAddon,
  HVSAgentforceAddOn, EinsteinCoachAccessAddOn, EinsteinCoachAgentAddOn, EinsteinSdrAgentAccessAddOn,
  EinsteinSdrAgentAddOn, EinsteinSdrAgentCreditsAddOn, EinsteinSdrAgentPlatformAddOn
- **Einstein GPT / generative:** EinsteinFlowGptAddOn, EinsteinForSvcInovtAddOn, EinsteinGPTCopilotAddOn,
  EinsteinGPTFeedbackAddOn, EinsteinGPTFieldGenerationAddOn, EinsteinGPTFormulasAddOn,
  EinsteinGPTGroundingStructuredDataAddOn, EinsteinGPTPlatformAddOn, EinsteinGPTPromptBuilderAddOn,
  EinsteinGPTRequestsAddOn, EinsteinGPTSalesAccessAddOn, EinsteinGPTSalesAddOn,
  EinsteinGPTServiceAccessAddOn, EinsteinGPTServiceAddOn, EinsteinGPTTrustAddOn, DCReportGPTAddOn
- **Credit metering / unmetered AI:** **FlexCreditsMeteringAddOn**, **UniversalCreditMetering**,
  **UnmeteredUserBasedAIAddOn**
- **Data Cloud / Genie / C360:** C360SuiteEE, CdpDataSpaces, CdpSegmentsActivationsCard,
  GenieDataPlatformServicesCard, GenieDataPlatformStarter, GenieDataStorage,
  SandboxCdpSegmentsActivationsCard, SandboxDataCloudSubSecondRealTime,
  SandboxGenieDataPlatformServicesCard, SandboxGenieDataStorage
- **Sandboxes:** AdditionalFullCopySandbox, AdditionalSetupSandbox, AdditionalSmallSetupSandbox
- **Service / messaging / chat:** ChatbotEnabled, ConversationsAddOn, EmbeddedServiceMessaging,
  EmbeddedServiceMessagingUserPsl, KnowledgeUser, LiveAgentUser, LiveMessage, LiveMessageUserPsl,
  ServiceDeskUser, ServiceUserAddOn, HighVelocitySales
- **Marketing:** EasyMarketingHighAddOn, EasyPlusShared, MarketingUser
- **Health Cloud (community):** HealthCloudForCmtyAddon
- **Tableau / analytics:** TableauEinsteinAddOn, TableauNextLimitedViewerAddOn, TableauNextStandardViewerAddOn

## Standalone entry — re-check and enable the prerequisites

When Act 5 runs as the tail of the full journey — after Acts 1→4 — the prerequisites are already satisfied and the
re-check steps no-op. When the admin runs **only** Act 5 ("just set up Gen AI suggested
assessments"), re-verify each prerequisite and enable what you can:

1. **Person Accounts — HARD STOP if off.** Even though Act 1 already treats this as a hard prereq,
   re-check it here for the standalone case (read `Organization.IsPersonAccountsEnabled`). It is
   an irreversible Health Cloud Basic Setup gate — this skill **cannot** enable it. If it's off,
   say it's required, **stop**, and tell the admin to complete Health Cloud Basic Setup first.
2. **Einstein master toggle** — **scriptable** (CONFIRMED) via the setup-preference Connect API:
   `PATCH /services/data/v{version}/setup/org/preferences/EinsteinGPTPlatformEnabled` with body
   `{"desiredState": true}`, then re-read the same path (`GET`) and assert `isPreferenceEnabled == true`
   (see Act 1 step 4 for the full recipe). Enable if off — no longer a manual gap.
3. **Einstein for Health Cloud** (`enableHealthCloudGenAIPref`) — enable if missing (idempotent).
4. **Context definitions enabled** — enable if missing (Connect `setAccess` PUT, gated on the
   Context Service PSL proxy, same as Act 1).
5. **Member Profile context definition present** — validate it appears in the org's context
   definitions; empty means Context Service hasn't effected yet.
6. **Care Management (`HCCareMgmt`, Act 3 master `enableIntegratedCareManagementSetting`)** —
   enable if missing. **Two of the three prefs below gate on Care Management being effective**
   (`enableSuggestedAssessmentSetting`, `enableGlobalSearchForAssmt`); deploying them before
   `HCCareMgmt` is on silently drops them. Discovery Framework (Act 2 master
   `enableIndustriesAssessment`) must likewise be on.

Reuse the existing idempotent enable/verify steps for all of the above — do not author parallel
enablement logic. Each re-read/skip is driven by the standard `optional:` + `when:` idiom.

## What this Act does

1. **Detect the license stack** (above) — hard-stop if the PSL proxies are absent.
2. **Deploy the three preferences** in one `IndustriesSettings` MDAPI deploy at the org's own API
   version, then **re-read all three back with a single `Settings:Industries` retrieve** (parent
   *Transport & deploy discipline* rule 4 — one retrieve covers every pref; the `Is*Enabled` columns
   listed below are single-field fallbacks, since the Tooling `IndustriesSettings` query server-errors
   on OrgFarm orgs) — never trust the deploy's "Changed" result (silent-drop applies to every
   `HCCareMgmt`-gated pref); in a full run these are Tier 4, batched by the consolidated enablement:
   - `enableGenAISuggestedAssmts` (min 262) → `IsGenAiSuggestedAssmtsEnabled` — the master pref
     for this feature ("Generative AI Suggested Assessments" org pref)
   - `enableSuggestedAssessmentSetting` (min 258) → `IsSuggestedAssessmentSettingEnabled` — the
     umbrella "Suggested Assessment" toggle the 262 feature sits on
   - `enableGlobalSearchForAssmt` (min 262) → `IsGlobalSearchForAssmtEnabled` — "Unified search
     for Internal and MCG Assessments" org pref

   These three are peers (none is a master of another within this set), so a single bundled deploy
   is safe. If the atomic deploy is ever rejected, fall back to per-pref deploys. If a pref reads
   back false after deploy, its gate (Care Management / Discovery Framework) is not yet effective —
   fix the gate and re-deploy, don't retry blind.
3. **Create + assign the permission sets** — check → report → confirm → assign, **never
   auto-assign** (billing-adjacent; treat with extra care). Per the Salesforce Help procedure and
   `../../references/licensing-and-permission-sets.md`:
   - **List active users** in the org and **ask which user** to assign to (reqs: provide a list of
     usernames — `SELECT Id, Username, IsActive FROM User WHERE IsActive=true`).
   - **Assign the `UnmeteredUserBasedAIPsl` permission-set license** to the chosen user
     (`PermissionSetLicenseAssign`; `DUPLICATE_VALUE` → already-assigned success).
   - **Create the custom "Unmetered User Based AI" permission set** — a `PermissionSet` whose
     XML enables `<userPermissions><name>UnmeteredUserBasedAI</name><enabled>true</enabled></userPermissions>`.
     This deploy **succeeds only if universal credit metering is enabled for the org** at
     deploy time. That in turn needs the add-on licenses provisioned **AND
     Einstein turned on** (`EinsteinGPTPlatformEnabled`, Act 1 step 4) — both must be in effect
     for the deploy to succeed. So it fails
     `Unknown user permission: UnmeteredUserBasedAI` when **Einstein is off, even with the
     `UnmeteredUserBasedAIAddOn` + `UniversalCreditMetering` licenses present (=10)**. Do NOT
     misreport this as a missing license — first verify Einstein is on (Act 1 step 4), then retry
     the deploy; only if the add-on/PSL stack is genuinely absent is it a true license gap.
   - **Assign the supporting permission sets** to the confirmed user — the full set the feature
     needs, per the Salesforce Help procedure. **Check each first (skip any already assigned;
     `DUPLICATE_VALUE` → success) and assign only the missing ones on explicit confirmation.**
     Query by **DeveloperName, never the UI label** (label-guessing returns zero rows every time —
     the documented Act-1 bug):

     | UI label (doc list) | `PermissionSet` DeveloperName | Note |
     |---|---|---|
     | Care Plans Access | `CarePlansPermissionSetLicense` | **not** `CarePlansAccess`; needs the CarePlans PSL |
     | Context Service Admin | `ContextServiceAdminPsl` | **admin user ONLY — skip for standard users** (they get Context Service Runtime instead). No bare `ContextServiceAdmin` set exists — the assignable set *is* the `Psl` form |
     | Context Service Runtime | `ContextServiceRuntimePsl` | the standard-user Context Service set — assign to everyone (admin and standard) |
     | HealthCloud Foundation | `HealthCloudFoundation` | |
     | Prompt Template Manager | `EinsteinGPTPromptTemplateManager` | Einstein Prompt Builder (not the bare `PromptTemplateManager`) |
     | Prompt Template User | `EinsteinGPTPromptTemplateUser` | Einstein Prompt Builder (not the bare `PromptTemplateUser`) |
     | Generative AI Suggested Assessments | `SuggestedAssessmentGenAIPsl` | 262 feature; grants `SuggestedAssessmentGenAIUserAccess` (the *which-assessment* user perm) |
     | Assessment Envelope | `AssessmentEnvelope` | Entity-access grant (doc step 1) — CRUD on the assessment-envelope entities. DeveloperName == UI label; **confirmed against a live Health Cloud org** (not grep-visible in the Core release checkout — HC seeds it outside `standardpermissionsets/`) |
     | Unmetered User Based AI | *(the custom set created just above)* | admin-named; created in this Act |

     **This list overlaps Act 1's Core-ICM perm-set offer** — in a full 1→8 run the shared Core
     rows (Care Plans, HealthCloud Foundation) are likely already assigned and no-op; in a
     **standalone Act 5** run none of them can be assumed, so re-check the whole list here. (The 262
     setup doc's step-3 list does **not** include **Action Plans** — Act 1 already covers it as a
     Core-ICM set — so it is not in this table.)
     Ask which user again and re-list usernames if the admin didn't already choose.

     **Per-user assignment rule — `Context Service Admin` is admin-user-only.** When assigning to a
     **standard (non-admin) user, SKIP `ContextServiceAdminPsl`** — assign `ContextServiceRuntimePsl`
     instead (every user, admin or standard, gets Runtime; only the admin additionally gets Admin).
     This mirrors the 262GA doc's explicit "(don't assign for standard user)" note on Context Service
     Admin. Concretely: determine whether the confirmed assignee is an admin (e.g. has a
     "System Administrator"-type profile / the `ManageUsers`/`ModifyAllData` perm) — assign the Admin
     set only then; for a standard user, the Admin row drops out of the offer entirely and is not
     merely "reported but unassigned." The other seven sets in the table are assigned to any confirmed
     user regardless of admin status.
4. **Report the external release setting and the manual tail** (below) — do not attempt to automate them.

## The Salesforce-managed release setting — report-only, not settable

Even with the prefs on and the perm sets assigned, the feature is additionally gated by a
Salesforce-managed release setting for this feature. It is **not
MDAPI-settable and not queryable** — there is no customer workaround. Surface it explicitly: if
the license stack is present and the prefs read back true but the "Show Gen AI Suggestions" button
still doesn't render, that Salesforce-managed release setting is the likely remaining reason and needs a Salesforce-side
confirmation, not more retries. **Never let a green pref-read stand in for "the feature works."**

## Manual tail — DEFERRED (call out, do not build)

These finish the feature but are out of scope for this Act to automate — tell the admin they remain
to be done manually. Each maps to a step in the 262GA setup doc:

> **Hand-off batching (see the parent SKILL.md "Manual-step hand-offs — batch per tier, then
> verify").** These tail items are genuinely independent of each other, so **batch them into one
> checklist** the admin can work in a single pass rather than handing them off one at a time — the
> prompt-template selection, the "Einstein Generative AI" picklist value, and the flow
> Save-as-New-Flow clone/activate all stand alone (the FLS grant is automatable — deploy it, don't put
> it in the manual list). Present them together, then verify what has a read-back (e.g. the shipped
> template selected, the flow now Active via `FlowDefinitionView`) and say what you saw; for the
> Salesforce-managed release setting, state plainly it can't be verified from here. Keep a running
> orientation marker (e.g. *"Act 5 of 9 · core enablement done; a short manual tail is all that's
> left in this act"*).

- **(doc step 1) Select the Suggested Assessment Prompt Template** — **guide the admin through it,
  don't just name it** (no default is pre-selected, so suggestions will not generate until this is
  set):
    1. In **Setup → search "Discovery Framework" → General Settings** — the *same* preference page
       where the **Gen AI Suggested Assessments** org pref was enabled in step 1.
    2. On that **Generative AI Suggested Assessments** preference, click **Edit**.
    3. In the **Suggested Assessment Prompt Template** dropdown, pick the **shipped** prompt template
       for this feature — a prompt-template *type* is delivered specifically for Suggested
       Assessments (doc step 6: it appears in the Prompt Builder search list and can be opened in
       **Preview** mode), so this is a *select-the-shipped-template* step, **not** authoring a new
       one. (Selecting it needs the **Prompt Template Manager/User** perm sets assigned in step 3.)
    4. **Save.** Without a template selected the pref can read back true yet produce no suggestions —
       treat "prefs green but no output" as a possible unset-template symptom, alongside the Salesforce-managed release setting.
- **(doc step 1) Add "Einstein Generative AI" as a Suggestion Source Type picklist value** on the
  **Suggested Assessment Reason** object (Object Manager). `SuggestionSourceType` is a customer-
  extensible dynamic picklist (`DYNAMICENUM`, enum `SARSuggestionSourceType`) that ships only `MCG`
  and `BusinessRule` — so "Einstein Generative AI" is a **genuine value add, done in Object
  Manager**. There is **no `StandardValueSet` MDAPI surface** for this standard-entity field, so it
  cannot be deployed — it is manual-UI-only. (Confirmed against the release checkout +
  the 262GA doc; supersedes an earlier draft that flagged this step "unverified.")
- **(doc step 1) Enable FLS on all fields** of **Suggested Assessment Definition**
  (`SuggestedAssessmentDef`) and **Suggested Assessment Reason** (`SuggestedAssessmentReason`).
  Assigning the **Assessment Envelope** perm set (automated in step 3 above) grants CRUD on the
  assessment-envelope entities, but **no shipped perm set carries `fieldPermissions` on these two
  `Suggested*` entities** — so field-level security is a **separate** grant. **This IS automatable
  — do NOT report it as manual.** "All fields" is a small, enumerable set:
  describe each entity, take the `permissionable == true` fields (live: `SuggestedAssessmentDef` = 3
  — `PartyId`, `SourceContextId`, `IsRequired`; `SuggestedAssessmentReason` = 5 —
  `PrimaryAssessmentId`, `PrimaryAsmtQuestionResponseId`, `SuggestionSourceType`,
  `SuggestionSourceName`, `SuggestionReason`), author a `PermissionSet` with a `fieldPermissions`
  block (`editable`+`readable`) per field, MDAPI-deploy it (dry-run first — a create-only field will
  reject `editable`), and assign on confirmation like the other sets. Enumerate from the describe at
  deploy time (field counts drift by release); never hardcode the list.
- **(doc step 5) Guide the "Save as New Flow" clone of the "Create Assessment Metadata Library
  Document" flow — the AGENT does the clone guidance + frequency, the ADMIN activates manually.**
  Walk the admin through it: Setup → **Flows** → open the shipped **Create Assessment Metadata
  Library Document** (`hc_genai_sug_assmt/CreateAssmtPdf`) → **Save As** → **Save as New Flow** →
  configure the run frequency (usually daily). **Hand the admin the exact label to use:**
  **`ICM Create Assessment Metadata Library Document`** (API name auto-fills to
  `ICM_Create_Assessment_Metadata_Library_Document`) — a distinct, named-by-us label so the clone is
  unambiguous in the flow list; if the admin picks their own, record and report it. **The agent does
  NOT activate** (there is no headless path — see below); instead **tell the admin plainly:
  "the flow named `ICM Create Assessment Metadata Library Document` is now saved as a Draft — you
  need to Activate it in Flow Builder to finish."** So this is a *guided* clone with a *named*
  hand-off, not an "it's manual, can't help" report. **No programmatic clone exists:** the shipped
  `CreateAssmtPdf` flow is managed/installed; a Metadata API `retrieve`
  returns only `package.xml` (managed source not retrievable) and the Tooling `Flow` table returns 0
  rows — so the definition can't be read and re-emitted through the Metadata API, and there's no
  flow-definition record to drive an activation against. Don't try to activate a flow version through
  an API.
- **(doc step 4b) MCG assessment-data sync** (if MCG is on) — enable the MCG Sync org pref
  (`enableMcgSyncData`) on the ICM setup page and **Run sync** to pull MCG guidelines into the
  External Assessment Definition entity. The pref is technically MDAPI-deployable but the sync
  itself is a runtime job, not a pref — so this stays a manual callout.

Plus the two genuinely-external blockers this Act can only report: the Salesforce-managed release setting above and the
provisioned credit-metering org perm.

## Act 5 end state

- License stack detected: `UnmeteredUserBasedAIPsl` + `HealthCloudAssistiveAgentPsl` present
  (credit-metering reported) — or the Act stopped with a named missing-add-on message.
- All three prefs (`enableGenAISuggestedAssmts`, `enableSuggestedAssessmentSetting`,
  `enableGlobalSearchForAssmt`) deployed **and read back true** via Tooling.
- `UnmeteredUserBasedAIPsl` PSL assigned to the confirmed user; the custom **Unmetered User Based
  AI** perm set created; the assessment perm sets (including **Assessment Envelope** for entity
  access) assigned on confirmation.
- The manual tail surfaced: the prompt-template selection, the "Einstein Generative AI" picklist
  value, FLS on the two `Suggested*` entities, the flow **Save-as-New-Flow
  clone (guided — label `ICM Create Assessment Metadata Library Document`; agent does not activate, admin
  activates manually)**, and (if MCG) the MCG sync.
- The Salesforce-managed release setting and the manual tail reported explicitly as remaining/external — the admin
  knows "prefs deployed" ≠ "feature renders."

## Gotchas learned from the reference research

- **Silent-drop of gated prefs** — a `HCCareMgmt`-gated pref can deploy "Changed" yet read back
  false when Care Management isn't effective. Always Tooling-read the three `Is*Enabled` fields
  back; if the deploy bundles fine but a pref reads false, fix the gate, don't retry blind.
- **Perm set before its PSL — and Einstein before both** — assign the `UnmeteredUserBasedAIPsl`
  license *before* creating and assigning the custom perm set. And note the create is rejected
  `Unknown user permission: UnmeteredUserBasedAI` unless universal credit metering
  is effective, which requires **Einstein turned on** (Act 1 step 4) in addition to the add-on
  licenses — with Einstein off it fails even when the licenses are provisioned (=10). Turn Einstein
  on first; don't misread the failure as a missing license.
- **Deploy at the org's own API version** — these prefs floor at API 258–262 (~API 63–66); an org
  pinned lower silently drops the higher-floor prefs.
- **The "Einstein Generative AI" picklist value is a real manual step, not automatable** — now
  **confirmed** against the 262GA doc (supersedes the earlier "unverified" flag). `SuggestionSourceType`
  on `SuggestedAssessmentReason` is a `DYNAMICENUM` shipping only `MCG` + `BusinessRule`; the admin
  adds "Einstein Generative AI" in Object Manager. No `StandardValueSet` exists to deploy it via
  MDAPI — see the manual tail.
- **Assessment Envelope perm set is real (DeveloperName `AssessmentEnvelope`)** — confirmed against
  a live HC org; it is *not* visible in a Core-source grep because HC seeds it outside
  `standardpermissionsets/`. Assign it by DeveloperName like the other sets. Its grant covers
  entity CRUD but **not** FLS on the two `Suggested*` entities — that FLS is a **separate but
  automatable** grant: describe both entities, take the `permissionable`
  fields (live: 3 + 5 = 8), author + MDAPI-deploy a `PermissionSet` with a `fieldPermissions` block
  per field (dry-run first — create-only fields reject `editable`), and assign on confirmation. Not
  a manual step.

<!-- skill-validate: ignore-start -->
<!-- codey:operations start -->
## Operations Reference

Operations this skill uses — routing and dependency reference.

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `detect-genai-assessments-license-stack` | read | — | `GET /services/data/v63.0/query` | — |
| `report-genai-suggested-assessments-release-setting` | discovery | — | — | `detect-genai-assessments-license-stack` |
| `verify-genai-suggested-assessment-prefs` | verify | — | `IndustriesSettings.query` | — |
| `query-users-for-ai-assignment` | read | — | `GET /services/data/v63.0/query` | `detect-genai-assessments-license-stack` |
| `list-genai-assessment-permission-sets` | read | — | `GET /services/data/v63.0/query` | `detect-genai-assessments-license-stack` |
| `assign-unmetered-user-based-ai-psl` | write | — | `POST /services/data/v63.0/sobjects/PermissionSetLicenseAssign` | `query-users-for-ai-assignment` |
| `verify-unmetered-user-based-ai-psl` | verify | — | `GET /services/data/v63.0/query` | `assign-unmetered-user-based-ai-psl` |
| `assign-genai-assessment-permission-sets` | write | — | `POST /services/data/v63.0/sobjects/PermissionSetAssignment` | `list-genai-assessment-permission-sets`, `query-users-for-ai-assignment` |
| `verify-genai-assessment-permission-sets` | verify | — | `GET /services/data/v63.0/query` | `assign-genai-assessment-permission-sets` |
<!-- codey:operations end -->
<!-- skill-validate: ignore-end -->
