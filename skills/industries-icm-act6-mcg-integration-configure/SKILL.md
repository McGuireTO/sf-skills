---
name: industries-icm-act6-mcg-integration-configure
description: "Act 6 of Health Cloud ICM setup — the sixth act of the full 1→8 journey (runs after Act 5 for an unqualified \"set up ICM\", followed by Acts 7-8; also runnable standalone on an explicit MCG ask) — stand up the working MCG (Milliman Care Guidelines) integration end-to-end, not just the Act 3 reveal toggle. Detect the MCG license stack first (hard-stop on the ISE PSL if absent), verify-then-enable the MCG preference + Discovery Framework, build the External/Named Credential chain (secrets are hard-manual; the principal-access permission set is automatable, authored here), create + activate the Integration Definition (prefer the controller dispatch the Setup UI itself uses; fall back to the UI create for the managed MCG case), then set the org-value the sync depends on (MANDATORY on the MDAPI path), wire the Assessment component's External Assessment Integration attribute (Tooling), and (on confirmation) guide the first data sync. Backing runbook: source/references/mcg-integration-runbook.md."
metadata:
  version: "1.0"
  cliTools:
  - tool:
    - "sf"
    semver: ">=2.0.0"
---

# Act 6 — Full MCG (Milliman Care Guidelines) integration

Part of the [`icm-setup`](../../SKILL.md) skill — the **sixth act** of the full 1→8
journey. For an unqualified "set up ICM" it runs **after
[Act 5](../act5-genai-suggested-assessments/SKILL.md)** and is followed by Acts 7-8; it is also runnable standalone on an
explicit MCG ask ("set up MCG", "configure Milliman Care Guidelines", "wire up the MCG
integration"). Because MCG requires a provisioned MCG license, a real Milliman (CareWebQI) account,
and customer secrets, Act 6 — like Act 5 — may legitimately **hard-stop for a genuinely absent
license stack**: detect the license FIRST, and if it's absent, report the named prerequisite rather
than forcing the integration (that's the act *running and reporting*, not being skipped). Runs after
— or re-verifies — [Act 2](../act2-discovery-framework/SKILL.md) (Discovery Framework) and
[Act 3](../act3-icm-toggles/SKILL.md) (whose toggle 5 only *reveals* MCG in the ICM Setting UI). The
full backing detail — component map, per-step automation verdict, transport contracts, the
unified-search dependency — lives in
[`../../references/mcg-integration-runbook.md`](../../references/mcg-integration-runbook.md);
**read it before telling an admin "MCG is set up."**

> ⚠️ **Secrets handling — non-negotiable.** The MCG **ClientID**, **HashKey**, and **endpoint
> URL** are Basic-Auth credentials to an external (Milliman) system. They must **never** be
> echoed into chat, prompts, logs, committed artifacts, or a deploy file — secure UI entry only.
> Never surface a literal MCG URL, ClientID, or HashKey even as an example; use placeholders
> (`{MCG_URL}`, `{MCG_CLIENT_ID}`, `{MCG_HASH_KEY}`). This applies to every step below that
> touches the credential chain.

## What "MCG" actually is (and why the Act-3 toggle is not enough)

MCG is **not** a toggle. Act 3's toggle 5 (`mcgPreference`) only **reveals** MCG in the ICM
Setting UI. The **working feature** is an external-system integration: Salesforce calls out to
Milliman's CareWebQI API to fetch guidelines, and an async job syncs MCG data back into the
`ExternalAssessmentDefinition` entity that the Assessment Library's **unified search** reads. That
requires a full Named-Credential → Integration-Definition → org-value → sync chain — none of which
the basic toggle touches. **This Act builds that chain.**

**Net scope (validated live):** the automatable-via-compliant-transport pieces are the
prerequisite toggles (MCG preference, Discovery Framework), the credential-chain *structure* + the
**principal-access permission set** (Phase 4b, MDAPI `PermissionSet` — this skill authors it, not the
admin), the `enableMcgSyncData` preference
(MDAPI `IndustriesSettings`), the `MCG_INTEGRATION_DEF_DETAILS` org-value write (**the Setup Connect
API for org values**), and the Assessment-component wiring (**Tooling** FlexiPage). The
**Integration-Definition create+activate** (Phase 5) should route to the **`IntegrationConfigurationSetup`
controller** (`/headless/invoke/platform/integration-configuration/*` — the surface the Setup UI
itself uses); **prefer** it, but its **managed-`healthcloudext`-Apex-class bind is not yet
live-verified** over headless dispatch (validate live first), and a subscriber **MDAPI deploy can't
bind that managed class at all** (MDAPI create works only for Java/LowCode/unmanaged-Apex), so **fall
back to the Setup UI create** for the managed MCG case if the controller bind isn't confirmed. The
one step with **no compliant API surface at all** is the `runSync` first sync (no
MDAPI/Tooling/Connect/invocable/platform-event surface of its own) — guided-manual UI + read-only
verify. The secret-bearing credential entry (Phase 4a) is the hard-manual step (structure deploys,
secrets don't); the Phase 4b principal-access perm set is automatable.
⚠️ **Runtime object vs deployable metadata type — don't conflate them:** the runtime object
`IntegrationProviderDefinition` has **no SOQL/Tooling *read* surface** — but it IS
readable through the `platform/integration-configuration` dispatch surface
(the `.../get-integration-config-definition-details` read-back + the list route), and the **deployable
metadata type `IntegrationProviderDef`** (a different, shorter name — dir
`integrationProviderDefinitions/`, suffix `.integrationProviderDefinition`) is a real public MDAPI
type. Verify read-only via those controller reads or `listMetadata`/retrieve, **never** SOQL. ⚠️
**Critical consequence:** the legacy UI wizard set `MCG_INTEGRATION_DEF_DETAILS` **for free**, but a
**controller- or MDAPI-created definition may NOT** — so Phase 5b's org-value write is
**verify-or-repair on every path** (read it back; write it if missing/stale; never assume). That
closes the #1 silent-failure trap only if you *always* verify it.

> **Transport discipline for this Act: MD-API / Tooling / Connect only.** The `runSync` first sync
> is the one capability whose **only** supported surface is the setup UI — a **guided manual** UI
> action plus read-only verify, never an API call from this skill. The Integration-Definition create
> is **not** UI-only: prefer the `IntegrationConfigurationSetup` controller dispatch
> (`/headless/invoke/platform/integration-configuration/*`, a compliant Connect surface). Its managed
> `healthcloudext` Apex-class bind is **not yet live-verified** over headless dispatch, and a
> subscriber MDAPI deploy can't bind that managed class at all (MDAPI only for
> Java/LowCode/unmanaged-Apex), so **fall back to the UI create** for the managed MCG case if the
> controller bind isn't confirmed.
>
> **Read `IndustriesSettings` state (the MCG reveal toggle, Discovery Framework master,
> `enableMcgSyncData`, `enableGlobalSearchForAssmt`) with a single `Settings:Industries` retrieve**
> (parent *Transport & deploy discipline* rule 4), not per-toggle Tooling `Is*Enabled` queries — the
> Tooling `SELECT … FROM IndustriesSettings` path server-errors on OrgFarm orgs. The Tooling column
> names used below are single-field fallbacks / for resolving exact element names, not the primary
> read. (`IntegrationProviderDefinition` is a separate matter — a non-queryable runtime POJO read via
> `listMetadata`/retrieve, never SOQL/Tooling, as its step already states.)

## Never defer the whole Act because of one manual step

**A confirmed live-run miss:** MCG setup was deferred **in its entirety** — the credential-chain
principal-access perm set (Phase 4b, fully MDAPI-automatable — author+deploy+assign) was skipped
along with the genuinely-manual credential-entry, Integration-Definition create, and `runSync`
steps — because the admin balked at the manual tail and treating the whole Act as deferred felt
like the simpler offer. **Do not do this.** The three things in this Act that require an admin
to leave the chat are (a) entering the MCG secrets (Phase 4a), (b) the MCG **Integration Definition**
create (Phase 5) — **only if** the controller dispatch can't bind the managed `healthcloudext` Apex
class (attempt the controller first; a subscriber MDAPI deploy definitely can't bind it, so the UI
fallback is the leave-the-chat path when the controller bind isn't confirmed), and (c)
confirming/running the first sync (Phase 7). Everything else — license detect, preference toggles, the **Phase 4b perm set**
(author+deploy+assign), the `MCG_INTEGRATION_DEF_DETAILS`/`enableMcgSyncData` writes, and the
Assessment-component wiring — has a compliant transport and must run regardless of whether or when
the admin does the three manual pieces. In particular **the Phase 4b perm set is NOT part of the
credential's manual boundary** — build and assign it even when the admin enters the secrets by hand.
If the admin isn't ready for credential entry yet, say so plainly and keep going with everything
that doesn't depend on the credential existing yet (the Phase 4b perm set can be authored and
deployed before secrets are entered); only the pieces that genuinely need the credential/definition
to exist first (the `MCG_INTEGRATION_DEF_DETAILS` write, the component wiring, `runSync`) wait on it.

## License stack — DETECT FIRST, hard-stop if the ISE PSL is absent

MCG's gating unknown for any given org. Detect via the real `PermissionSetLicense.DeveloperName`
values (never the non-existent `*AddOn` names — the same lesson as Act 1/Act 5 license detection):

| Required entitlement | Queryable proxy — `PermissionSetLicense.DeveloperName` | On absence |
|---|---|---|
| Industries Service Excellence (backs the Integration Definition) | `IndustriesServiceExcellencePsl` | **HARD STOP** |
| Health Cloud base | `HealthCloudGA_HealthCloudPsl` | **HARD STOP** |
| OmniStudio (the sync runs an OmniStudio Integration Procedure) | `OmniStudioDesigner`, `OmniStudioRuntime`, `OmniStudioRuntimeCC` | report + continue best-effort |
| Dynamic Assessments | `DynamicAssessmentPsl` | report + continue |
| Community access (if MCG via a site) | `HealthCloudCmtyAccessPSL` | report + continue |

```sql
SELECT DeveloperName, TotalLicenses, UsedLicenses FROM PermissionSetLicense
WHERE DeveloperName IN ('IndustriesServiceExcellencePsl','HealthCloudGA_HealthCloudPsl',
  'OmniStudioDesigner','OmniStudioRuntime','OmniStudioRuntimeCC','DynamicAssessmentPsl')
```

If `IndustriesServiceExcellencePsl` (or the HC base PSL) returns zero rows: **stop and name every
missing entitlement explicitly** — "MCG can't be set up — your org is missing Industries Service
Excellence; ask your account team to provision it, then re-run." Don't attempt the Integration
Definition create into an org that lacks it (Phase 5 will reject). Report the full list of what's
absent, not the first miss.

## Standalone entry — re-check and enable the prerequisites

When Act 6 is asked for on its own, re-verify the two prerequisites it depends on and enable what
you can (reuse the existing idempotent enable/verify idiom — do not author parallel logic):

1. **Discovery Framework** (Act 2 master `enableIndustriesAssessment`) — enable if off. The
   Assessment component and its unified search gate on it.
2. **MCG preference** (Act 3 toggle 5, `mcgPreference`, enable and verify via the
   existing toggle steps) — enable
   if off. This only *reveals* MCG in the UI; the rest of this Act does the real work.

Person Accounts and the base ICM prereqs are Act 1's concern; if Act 6 is truly the first thing
run against a green org, defer to Act 1's hard-stop on Person Accounts before proceeding.

## What this Act does — the phases

Follow the runbook's per-step automation verdicts; the phases below are the validated live
sequence. **Every write uses a compliant transport — MD-API / Tooling / Connect only.**
The `runSync` first sync (Phase 7 — no supported API surface) is **guided manual** (setup-UI action +
read-only verify, not an API call from this skill). The **Integration-Definition create+activate
(Phase 5)** prefers the **`IntegrationConfigurationSetup` controller dispatch**
(`/headless/invoke/platform/integration-configuration/*`) — its managed-`healthcloudext`-Apex-class
bind is **not yet live-verified** over headless dispatch, and a subscriber MDAPI deploy can't bind
that managed class at all (MDAPI viable only for Java/LowCode/unmanaged-Apex service classes), so
**fall back to the UI create** for the managed MCG case if the controller bind isn't confirmed. Standard
write discipline otherwise (MDAPI/Tooling fallback on 404; dry-run before real deploys; re-read to
verify — see the parent SKILL.md "Transport & deploy discipline").

> **Hand-off batching (see the parent SKILL.md "Manual-step hand-offs — batch per tier, then
> verify").** This Act is the case that shows why you batch *within* a tier and never collapse the
> chain. Three manual boundaries exist along the automated chain: the **Phase 4a credential entry**
> (External Credential + Named Principal + Named Credential secrets) is one manual cluster the admin
> does in a single trip to Setup, up front; the **Phase 5 Integration-Definition create** — a manual
> boundary **only if** its controller dispatch can't bind the managed Apex class (then a UI-create
> hand-off); and the **Phase 7 first sync**. Between them sit the fully
> automated pieces this skill runs itself: the **Phase 4b principal-access perm set**, the **Phase 5b**
> org-value write, and the **Phase 6** component wiring. So hand off the credential cluster together,
> verify it read-only, author+deploy+assign the Phase 4b perm set, attempt the Phase 5 controller
> create (hand off the UI create only if it can't bind the managed class),
> then run the automated Phase 5b → 6 work, then hand off Phase 7 (sync) at its point in the chain.
> Keep the admin oriented with a running marker (e.g. *"Act 6 of 9 · credential entry is the manual
> step (plus the Integration-Definition create if the controller can't bind the managed class); the
> first sync is the last hand-off after I wire the org value"*), and verify every hand-off by reading
> org state back (`calloutStatus`, the
> definition read back via `listMetadata`/retrieve, `MCG_INTEGRATION_DEF_DETAILS`, the
> `MCG_SYNC_JOB_DETAILS` poll) — never on the admin's "done" alone.

### Phase 1 — Licenses (detect + report)
The license table above. Hard-stop on a missing `IndustriesServiceExcellencePsl` / HC base PSL;
otherwise report and continue.

### Phase 2 — MCG preference (verify-then-enable)
Act 3 toggle 5. Verify `getPreference(mcgPreference)`; enable if off. Idempotent.

### Phase 3 — Discovery Framework (verify-then-enable)
Act 2 master. Verify; enable if off. Idempotent.

### Phase 4 — Credential chain (secret entry is hard-manual; the principal-access perm set is AUTOMATABLE)
This phase has **two distinct halves** — do not collapse them. 4a (secrets) is hard-manual; 4b (the
MCG permission set) is a compliant MDAPI deploy this skill **must author itself**, even when the admin
builds 4a in the UI.

**4a — External + Named Credential (HARD-MANUAL, secret-bearing):**
1. **External Credential** (Basic Auth) `MCG` + a **Named Principal** — ⚠️ **sequenceNumber `2`
   (NOT 1)**. The `ExternalCredential` *structure* is MDAPI-deployable, but the
   **ClientID (username) + HashKey (password) are secrets** — **guide the admin through secure
   UI entry**; never bake them into a deploy artifact, script, or committed metadata.
2. **Named Credential** `MCG` pointing at the MCG endpoint (`{MCG_URL}` — customer-specific;
   presumes a real Milliman account), enabled for callout. Verify `calloutStatus = Enabled`.

**4b — MCG permission set (AUTOMATABLE — this skill authors, deploys, and assigns it):**
3. **Permission Set** (suggested API name **`ICM_MCG_External_Credential_Access`**, label "Health
   Cloud ICM MCG External Credential Access" — detect an existing equivalent first, don't blind-create)
   with an **`externalCredentialPrincipalAccesses`** entry granting access to the 4a Named Principal,
   the **`UserExternalCredentials`** user permission, and the **SetupEntityAccess** row wiring the perm
   set to the principal. This is a normal MDAPI `PermissionSet` deploy — **it has a compliant transport
   and is NOT part of the manual secret entry.**
4. **Assign** that perm set — gated like every perm-set assignment in this skill:
   check → report → confirm → assign, **never auto-assign** (`DUPLICATE_VALUE` = already-assigned
   success).

> ⚠️ **The perm set is a SEPARATE deliverable from the credential — build it even when the admin
> enters the credentials manually.** A confirmed live-run miss: the admin created the External/Named
> Credential + principal in the UI, so the run treated *all* of Phase 4 as "the admin's manual work"
> and **never authored the principal-access permission set at all** — then, when asked "what's the
> name of the custom MCG perm set you created?", answered "I didn't create one." The only genuinely
> hard-manual piece is the **secret entry (4a)**; the **permission set (4b) is always this skill's job**
> and produces a named, deployable artifact the admin can point to. Authoring it needs only the
> Named Principal to exist (4a step 1) — it does **not** wait on Phase 5.

### Phase 5 — Integration Definition (create + activate)
The **runtime** object is the Industries Consumption Framework **`IntegrationProviderDefinition`** —
not SOQL-queryable. It is reachable through **three** surfaces, not the two
("MDAPI vs. UI") this Act originally framed:
- **A dispatchable server-side surface** — the public `platform/integration-configuration` dispatch
  routes under `/headless/invoke/platform/integration-configuration/*`. They carry both the
  **create/activate writes** the Setup UI itself calls and the **dispatch reads**
  (`.../get-integration-config-definition-details` + the list route) — so the runtime object
  is NOT read-surface-less; only *SOQL/Tooling* can't see it.
- **The `IntegrationProviderDef` Metadata API type** (a *different, shorter* name — dir
  `integrationProviderDefinitions/`, suffix `.integrationProviderDefinition`), a real public type.
- **The Setup UI** create wizard.

> ⚠️ **PREFER the controller dispatch; fall back to the UI for the managed MCG case.** The controller
> is the surface the Setup UI itself uses, so it is the right thing to **attempt** from a hosted agent
> (no CLI / no local deploy / no external auth):
> 1. `GET /headless/invoke/platform/integration-configuration/fetch-apex-class-records` — resolve the
>    Apex class id (the same picker the UI uses; it surfaces managed/namespaced classes like
>    `healthcloudext.HealthCareICMExternalService`).
> 2. `PATCH .../create-or-update-integration-configuration-definition` with
>    `integrationConfigurationDefinitionJson` = `{ definitionType: Apex, the resolved apexClassId,
>    integrationProviderAttributes Edition + Named Credential }`.
> 3. `PATCH .../activate` with the returned definition id.
> 4. Verify via the dispatch reads (`.../get-integration-config-definition-details` or the list
>    route) — `isActive=true`, capture `developerName`.
>
> ⚠️ **This managed-class bind is NOT yet live-verified over headless dispatch — validate it
> end-to-end on a live org (expertise harness) before promising it.** What **is** live-proven: a
> subscriber **MDAPI deploy CANNOT bind the managed Apex class.** MCG's def points at `type=Apex`,
> `apexClass=healthcloudext.HealthCareICMExternalService` — a **managed-package global class**. A
> subscriber's **MDAPI `ApexClassId` resolver cannot bind a managed global class** that isn't
> subscriber-SOQL-visible (`SELECT … FROM ApexClass` returns 0 rows; Tooling too), even though the
> **Setup UI apex-class picker resolves it fine**. A live run proved this: with a fully valid XML
> body, the deploy failed `In field: ApexClassId - no ApexClass named
> healthcloudext.HealthCareICMExternalService found` — for *every* reference format
> (`HealthCareICMExternalService`, `healthcloudext__HealthCareICMExternalService`,
> `healthcloudext.HealthCareICMExternalService`). This is a **platform visibility boundary, not a
> naming mistake**. So **if the controller bind is not (yet) confirmed for the managed class, guide
> the admin to create + activate the definition in the Setup UI** (Integrated Care Management Setting
> → the MCG section, or Consumption Framework "Integrations" → New), then resume automation. The MDAPI
> deploy is only viable when the service class is **`type=Java`/`type=LowCode`, or
> first-party/unmanaged Apex** — not the managed `healthcloudext` class. (The earlier "AUTOMATABLE via
> a compliant MDAPI deploy, verified end-to-end" verdict was validated against the shipped `type=Java`
> **sample** class `industriesintegrationfwk.SampleJavaClass`, which binds fine — it never exercised
> the managed MCG Apex class, which does not.)

**Create values** (controller payload, or the wizard fields on the UI fallback):
- **Apex class**: `healthcloudext.HealthCareICMExternalService` (resolve its id via
  `fetch-apex-class-records` for the controller payload).
- **Named Credential**: the NC from Phase 4a (`MCG`)
- **Edition**: an **admin question** — ask; **default the current release value, e.g. `29`**; it
  upgrades across releases, don't assume.
- **Active**: yes (the `activate` call, or check "Active" on save in the UI).
- **Name**: anything (e.g. `MCGNEW`) — **auto-discover it afterward** (controller read /
  `listMetadata`), so the admin doesn't need to report it. (`MCGNEW` is a common wizard default; other
  orgs differ — never hardcode.)

After create+activate: **read it back** — via the dispatch reads
(`.../get-integration-config-definition-details` or the list route) or `listMetadata`/retrieve — confirm `active=true`
and **capture the org's actual `developerName`** for Phases 5b and 6. **Do not SOQL
`IntegrationProviderDefinition`** (the runtime object isn't SOQL/Tooling-visible); the dispatch reads
or `listMetadata`/retrieve are the supported read paths.

**If you DO deploy via MDAPI (Java/LowCode/unmanaged-Apex case), the exact `IntegrationProviderDef`
schema is (reverse-engineered live — don't re-discover it by dry-run iteration):**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<IntegrationProviderDef xmlns="http://soap.sforce.com/2006/04/metadata">
  <active>true</active>                        <!-- the active element does the activation -->
  <apexClass>...</apexClass>                   <!-- or <javaClassName>/<lowCode ref>; NO top-level masterLabel (label = file name) -->
  <integrationProviderAttributes>
    <dataType>String</dataType>                <!-- per-attribute REQUIRED, alphabetical order: -->
    <developerName>Edition</developerName>     <!-- dataType, developerName, label, required, stringValue -->
    <label>Edition</label>
    <required>false</required>
    <stringValue>29</stringValue>              <!-- value element is stringValue, NOT value/masterLabel -->
  </integrationProviderAttributes>
  <integrationProviderAttributes>
    <dataType>String</dataType>
    <developerName>NamedCredential</developerName>
    <label>Named Credential</label>
    <required>false</required>
    <stringValue>MCG</stringValue>
  </integrationProviderAttributes>
  <type>Apex</type>                            <!-- top-level order: active, apexClass, attributes, type -->
</IntegrationProviderDef>
```
The two MCG attribute developerNames — **`Edition`** and **`NamedCredential`** — are **live-confirmed**
against a UI-created def's retrieve (Edition=`29`, NamedCredential=`MCG`); the retrieve normalizes the
class to `healthcloudext__HealthCareICMExternalService`.

> The old NPE/`apexOldAttributes` and reflected-attribute-casing traps belonged to a *different*,
> internal programmatic create path and do **not** apply to the `IntegrationProviderDef` MDAPI deploy
> or the UI-wizard fallback.

### Phase 5b — Set the org-value the sync depends on ⚠️ CRITICAL — VERIFY-OR-REPAIR on every path
⚠️ **Whichever way Phase 5 created the definition (controller dispatch, MDAPI, or the UI fallback),
this org value may not be set — so read it back and write it if missing/stale; never assume.** A
**controller- or MDAPI-created `IntegrationProviderDef` may NOT populate `MCG_INTEGRATION_DEF_DETAILS`**
— only the legacy UI wizard set it "for free," and even then a live run found it `null` after a UI
create. So `GET` it first; if it is missing or stale (pointing at a since-replaced def), **you must
write it.** If it stays unset, the sync no-ops → **zero** `ExternalAssessmentDefinition` records →
**unified assessment search silently returns nothing** while everything *looks* configured (the #1
silent failure). Treat Phases 5 → 5b → 7 as one indivisible unit.

1. **`MCG_INTEGRATION_DEF_DETAILS`** must carry the **active definition's developerName** (Phase 5 —
   read it from the definition via the controller reads or `listMetadata`/retrieve, never hardcode).
   Always `GET` the org value first; write it via `PATCH
   /services/data/v{version}/setup/org/values/MCG_INTEGRATION_DEF_DETAILS` only if it is missing or
   stale — this **is a compliant, supported transport** (**the Setup Connect API** — a supported
   REST/Connect resource). ⚠️ The PATCH **request** field is
   **`orgValue`** (a bare `stringValue`/`value` → `JSON_PARSER_ERROR`; the GET *response* shape
   `{stringValue,booleanValue,…}` is NOT the request shape):
   ```json
   {"orgValue":"{\"developerName\":\"<active def developerName>\"}"}
   ```
   ⚠️ **Read the developerName from the active `IntegrationProviderDefinition` — never hardcode a
   literal.** It is customer-specific (`MCGNEW` is a common wizard default; other orgs differ). The
   enum name is underscored (`MCG_INTEGRATION_DEF_DETAILS`), **not** camelCase.
2. **`enableMcgSyncData = true`** (`IndustriesSettings`) — the sync's org preference gate.
   `PUT /services/data/v{version}/headless/metadata` with a **minimal** settings body — ⚠️ the
   envelope is `{type, fullName, xmlRep}` (raw XML in `xmlRep`), **not** `{metadataType, fullName,
   body}`; and use a **single-field** body — round-tripping a full read redeploys read-only prefs
   and 500s (`INSUFFICIENT_ACCESS_OR_READONLY`):
   ```json
   {"type":"IndustriesSettings","fullName":"Industries",
    "xmlRep":"<IndustriesSettings xmlns=\"http://soap.sforce.com/2006/04/metadata\"><enableMcgSyncData>true</enableMcgSyncData></IndustriesSettings>"}
   ```
   ⚠️ **Read-back caveat (don't burn cycles retrying the GET):** the `Settings:Industries`
   settings-read GET **does not reliably echo `enableMcgSyncData`** — a live run saw it return only
   `enableMcgSetting` while `enableMcgSyncData` was simply absent from the response, which is **not**
   evidence the write failed. Confirm persistence via the **Tooling** object instead
   (`SELECT EnableMcgSyncData FROM IndustriesSettings`, non-OrgFarm only — the OrgFarm caveat above
   still applies); if neither read surface returns the field on this org, **rely on the PUT/deploy
   success** rather than re-issuing the read in different query-string forms. (On an org where the
   `headless/metadata` PUT is not available, the customer-transport equivalent is an
   `sf project deploy` of the same one-field `IndustriesSettings`.)

### Phase 6 — Wire the Assessment component's External Assessment Integration attribute
The Assessment component (`industries_common:assessmentContainer`) exposes the design attribute
**`integrationDefinition`** (LAB label "External Assessment Integration"), which must hold the
Integration Definition's **developerName**. A Tooling FlexiPage metadata write, independent of
FlexCard activation:

1. Find the FlexiPage(s) carrying the component: `SELECT Id,DeveloperName FROM FlexiPage` (Tooling),
   retrieve each, and match the `componentInstance` with
   `componentName = "industries_common:assessmentContainer"` — the **ICM** Account record page
   (e.g. `ICM_Account_Record_Page` from Act 4, matched by its tab-label props), **not** the plain
   `Account_Record_Page` (which has no assessmentContainer).
2. Inject/replace `{"name":"integrationDefinition","value":"<active def developerName>"}` in that
   instance's `componentInstanceProperties`, then `PATCH` the FlexiPage with the full `Metadata`
   block (HTTP 204). Read-back to confirm it persisted.
3. ⚠️ **Read the value from the active definition — never hardcode a literal** (`MCGNEW`/`MCG`
   differ per org). Same rule as Phase 5b.

### Phase 7 — (optional, on confirmation) kick off the first data sync — GUIDED MANUAL (no compliant API)
There is **no supported API to trigger the sync** — there is **no MDAPI / Tooling /
Connect / invocable / platform-event** surface, so it is **out of this skill's transport scope**.
**Do not attempt it programmatically.** Instead, guide the admin to run the sync from the **Integrated Care Management
Setting** UI (the "Sync" / "Sync Now" action on the MCG section). ⚠️ This is a **real external
callout to the customer's MCG endpoint** = *using* the feature, not strictly a setup step, and it is
guarded to sysadmin/customize-application + `ORG_HAS_HEALTH_CLOUD` + `ORG_HAS_CARE_PLANS`. **Only
proceed on explicit admin confirmation.** The sync reads `developerName` out of
`MCG_INTEGRATION_DEF_DETAILS` (Phase 5b), runs the OmniStudio IP `GetGuidelines_Metadata`, and
upserts `ExternalAssessmentDefinition` (Name←GuidelineTitle, SourceSystemName='MCG', …). Verify
read-only: poll the `MCG_SYNC_JOB_DETAILS` org value (`currentSyncStatus`/`lastSyncStatus`) for
completion. On success, `ExternalAssessmentDefinition` populates and the Assessment Library's
unified search returns those indexed records (allow a few minutes for SOSL indexing lag).

## Unified search dependency (why "search returns nothing" after setup)

When **`enableGlobalSearchForAssmt` / `IsGlobalSearchForAssmtEnabled`** (the "Unified Search
Experience for Assessments" pref, API 67.0+, **deployed in [Act 5](../act5-genai-suggested-assessments/SKILL.md),
NOT this Act**) is ON, the Assessment Library search runs as a
**SOSL** query over `OmniProcess` + `ExternalAssessmentDefinition` and returns only **indexed**
records. `ExternalAssessmentDefinition` is populated **exclusively by the MCG sync** (Phase 7). So
the chain that MUST be complete for unified search to return results is:
**Act 5 (`enableGlobalSearchForAssmt` genuinely effective) → Phase 5 (create+activate def) → Phase
5b (`MCG_INTEGRATION_DEF_DETAILS` + `enableMcgSyncData`) → Phase 7 (`runSync` upserts
`ExternalAssessmentDefinition`)**. Break any link — most commonly a **Phase 5 create (controller or
MDAPI) with Phase 5b skipped** (a programmatic create may NOT set the org value, so skipping 5b is
the default failure on the automated path) — and unified search silently shows the empty state even though direct
(pref-OFF) search works.

**Recognized recurring symptom — "search works with the pref off but fails with it on."** This has
recurred across multiple runs even after being fixed once before, so treat it as a known failure
class, not a one-off: it means the pref is reading `true` but at least one link in the chain above
is actually broken. **Don't stop at "the preference reads true" — re-verify the whole chain every
time this symptom is reported:**
1. **Re-confirm `enableGlobalSearchForAssmt` is genuinely effective** — re-read
   `IsGlobalSearchForAssmtEnabled`, and confirm it isn't itself silently dropped (Act 5's own
   gate/version-floor caveats apply here too).
2. **Re-read `MCG_INTEGRATION_DEF_DETAILS`** — don't assume the earlier Phase 5b write is still
   correct. A later redeploy of the Integration Definition, or a definition recreated with a new
   `developerName`, leaves the org value pointing at a **stale** definition — it will still be
   "set" (non-null), so a naive presence-check passes while the value itself is wrong. Compare its
   `developerName` against the **currently active** `IntegrationProviderDef` read via
   `listMetadata`/retrieve, not just "is it non-null."
3. **Run an explicit `ExternalAssessmentDefinition` COUNT, don't infer it from "the sync ran
   successfully."** `SELECT COUNT() FROM ExternalAssessmentDefinition` (or `WHERE
   SourceSystemName='MCG'`) — a `runSync` that reports success can still upsert zero rows if
   `MCG_INTEGRATION_DEF_DETAILS` was stale at sync time (step 2) or the callout partially failed.
   Zero rows here is the direct, unambiguous cause of the empty-state symptom; a non-zero count that
   still doesn't show up in search points at indexing lag (next) instead.
4. **Allow longer than "a few minutes" for SOSL indexing before concluding it's broken.** Indexing
   lag on `ExternalAssessmentDefinition` (an `isTextIndexed` object) has been observed to run
   noticeably longer than a first-glance check accounts for — if the COUNT in step 3 is non-zero,
   re-check search after a longer wait (on the order of 15-30 minutes, not 2-3) before concluding
   the chain is broken again; re-verify steps 1-3 first so you're not just waiting out an indexing
   delay that's masking a real stale-value bug.

**Separate, org-side condition (not fixable from this Act):** the LAB **OmniProcess Fields /
Unified Search Fields** default-field pickers only render their built-in defaults with
a Salesforce-managed release setting (API version 67.0+) enabled; on an older org, or one where
that release setting isn't enabled, those lists show empty and "Add Field" errors. That's an org
version / release-setting condition, **not** a metadata write — flag it, don't try to fix it via
the component.

## Deferred / report-only (call out, do not build)

- **Named-Credential endpoint + secrets** (Phase 4a) — the structure deploys, the ClientID/HashKey/
  URL do not. Hard-manual, secure UI entry. (The Phase 4b principal-access perm set is a SEPARATE,
  automatable deliverable — it is NOT deferred; see Act end state.)
- **MCG Integration-Definition create** (Phase 5, real-MCG case) — **not flatly deferred: attempt the
  `platform/integration-configuration` dispatch surface first** (`/headless/invoke/platform/integration-configuration/*`
  — fetch the managed apex class id, `create-or-update-integration-configuration-definition`, then
  `activate`). That dispatch-bound create is **not yet live-verified for the managed `healthcloudext`
  Apex class**, and the subscriber **MDAPI** `IntegrationProviderDef` deploy definitely can't bind it
  (MDAPI create is viable only for Java/LowCode/unmanaged-Apex) — so if the controller create fails on
  the managed class, **fall back to the guided Setup-UI create**. Everything around it
  (Edition/NamedCredential values, read-back, the `MCG_INTEGRATION_DEF_DETAILS` verify-or-repair,
  component wiring) is automated regardless of which create path lands.
- **"User External Credentials" on a standard-user profile** — profile edits are heavy/risky;
  treat as guided, confirm scope before touching a shared profile.
- **Automated Process user perm-set grant for the cron sync** — binding the MCG permission set to
  the Automated Process user (for the cron sync job) has no supported customer API surface. Report as a gap; don't fabricate a
  call path.
- **The API-67 / release-setting condition** behind the empty LAB field-pickers (above).

## Act 6 end state

- MCG license stack detected (`IndustriesServiceExcellencePsl` + HC base present) — or the Act
  stopped with a named missing-license message.
- MCG preference + Discovery Framework verified/enabled.
- Credential chain built: External Credential + Named Principal (**sequenceNumber 2**), Named
  Credential (`calloutStatus = Enabled`) — with the secret entry done by the admin, never by this
  skill (Phase 4a).
- **MCG permission set authored, deployed, and assigned by this skill (Phase 4b)** — a named artifact
  (e.g. `ICM_MCG_External_Credential_Access`) with `externalCredentialPrincipalAccesses` to the Named
  Principal + the `UserExternalCredentials` user perm + SetupEntityAccess, assigned on confirmation.
  **Built even when the admin created the credentials manually** — it is not part of the manual secret
  entry, and the admin should be able to name it.
- Integration Definition created **and activated**, Edition set to the admin's value, Named Credential
  wired — **dispatch-first for MCG** (via the public
  `/headless/invoke/platform/integration-configuration/*` routes), **guided Setup-UI create as the fallback**
  if the controller-bound create can't bind the managed `healthcloudext` Apex class (that bind is not
  yet live-verified; the subscriber MDAPI deploy definitely can't do it — MDAPI create is viable only
  for Java/LowCode/unmanaged-Apex), with the org's actual `developerName` read back via the controller
  read / `listMetadata` (not SOQL).
- **`MCG_INTEGRATION_DEF_DETAILS` set** via the Connect PATCH (on any **programmatic create path**
  — controller or MDAPI — assume it is NOT set for you; on the **UI create path** the wizard
  *sometimes* sets it — a live run found it `null` after a UI create, so on **every** path **read it
  back and write it if missing/stale**, never assume) and **`enableMcgSyncData = true`**.
- Assessment component's `integrationDefinition` attribute set to the active def's developerName
  (Tooling FlexiPage, read not hardcoded).
- Optionally, the first sync run from the UI on confirmation → `ExternalAssessmentDefinition`
  populated → unified assessment search returns results.
- The genuine deferrals (`runSync` = guided-manual, no compliant API at all; secret entry; User
  External Credentials profile flag; Automated Process user grant; the API-67 / release-setting
  field-picker condition) reported explicitly. **The MCG Integration-Definition create is NOT in this
  list** — it is controller-first with a UI fallback (the fallback fires only if the not-yet-live-verified
  controller bind of the managed `healthcloudext` Apex class fails), reported as such.

## Gotchas learned from live execution

- **Transport discipline: controller / MD-API / Tooling / Connect — in that order of preference.**
  Only **one** thing has **no compliant write path for the real MCG case** and is flatly guided-manual:
  **`runSync`** (no MDAPI/Tooling/Connect/invocable/platform-event/controller surface at all). The
  **MCG Integration-Definition create** is NOT in that bucket — it has a real server-side surface, the
  public **`platform/integration-configuration`** dispatch routes at `/headless/invoke/platform/integration-configuration/*`
  (the same picker the UI uses; it surfaces managed classes). **Attempt that dispatch create first**
  (fetch apex class id → `create-or-update-integration-configuration-definition` → `activate`). CAUTION:
  binding the managed `healthcloudext` Apex class over that controller is **not yet live-verified** —
  so if it fails, fall back to the guided Setup-UI create. The deployable metadata type
  **`IntegrationProviderDef`** (shorter name than the runtime POJO `IntegrationProviderDefinition`)
  *is* a real public MDAPI type, BUT a subscriber MDAPI deploy **definitely cannot bind MCG's managed
  `healthcloudext` Apex class** (not subscriber-SOQL-visible, so the `ApexClassId` resolver fails) —
  which is exactly what a live run hit — so MDAPI create is viable only for Java/LowCode/unmanaged-Apex
  integration defs. Don't re-conflate the non-queryable runtime POJO (no SOQL *read* surface) with the
  deployable metadata type; read the created def back via the controller read / `listMetadata`, never SOQL.
- **The `MCG_INTEGRATION_DEF_DETAILS` org value is load-bearing — and MANDATORY to verify-or-repair on
  every programmatic create path.** A **programmatically created def (controller OR MDAPI) may NOT set
  it** (only the legacy UI wizard did, for free — and a live run found even a UI create left it `null`) —
  so on any automated path you must read it back and PATCH it yourself; skipping it silently no-ops the
  sync → 0 `ExternalAssessmentDefinition` → unified search returns nothing while looking correct.
  Write/repair via the compliant Connect PATCH (the Setup Connect API for org values). Always do
  Phases 5 → 5b → 7 as a unit. (An earlier research pass used the wrong camelCase enum name and
  wrongly concluded the org value "didn't apply" — the real name is underscored and it IS required.)
- **Transport request-vs-response shapes differ.** The org-value PATCH accepts `{"orgValue":…}`,
  not the GET's `{stringValue,…}` response shape. The `/headless/metadata` deploy body is
  `{type,fullName,xmlRep}` (raw XML), not `{metadataType,fullName,body}`; use a minimal one-field
  settings body or a full round-trip 500s on read-only prefs.
- **Never hardcode the definition developerName** — read it from the active `IntegrationProviderDef`
  via `listMetadata`/retrieve (never SOQL — the runtime `IntegrationProviderDefinition` POJO has no
  queryable surface). It is customer-specific (`MCGNEW` common default; others differ) and is written
  in two places (Phase 5b org value + Phase 6 component attr) — both must use the org's actual value.
- **`runSync` is a real external MCG callout**, not a passive setup step — proceed only on explicit
  confirmation (from the setup UI), and only once the credential chain + Phase 5b are complete.

<!-- skill-validate: ignore-start -->
<!-- codey:operations start -->
## Operations Reference

Operations this skill uses — routing and dependency reference.

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `detect-mcg-license-stack` | read | — | `GET /services/data/v63.0/query` | — |
| `establish-mcg-credential-chain` | discovery | — | — | `detect-mcg-license-stack` |
| `provision-mcg-integration-definition` | write | — | `PATCH /headless/invoke/platform/integration-configuration/create-or-update-integration-configuration-definition` | `establish-mcg-credential-chain` |
| `verify-mcg-integration-definition-active` | verify | — | `GET /headless/invoke/platform/integration-configuration/get-integration-config-definition-details` | `provision-mcg-integration-definition` |
| `run-mcg-first-data-sync` | discovery | — | — | — |
<!-- codey:operations end -->
<!-- skill-validate: ignore-end -->
