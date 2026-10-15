---
name: fsc-digital-origination-initial-setup-configure
description: "Guided end-to-end admin setup of Digital Origination (DOP) Initial Setup for a Financial Services Cloud org — the Salesforce Go \"Digital Origination Initial Setup\" journey. \"Set up Digital Origination\", \"set up DOP\", \"configure Digital Origination\", \"turn on Digital Origination\", \"run Digital Origination initial setup\", or \"enable digital lending\" (the legacy name) with no narrowing qualifier means running ALL FOUR TURN-ON STEPS in dependency order — Step 1 (Discovery Framework, a prerequisite feature), Step 2 (Know Your Customer, a prerequisite feature), Step 3 (Digital Origination itself), Step 4 (Import or Export) — followed by enabling Discovery Framework Sample Templates, plus the required Manage User Access step, NOT just flipping the Digital Origination toggle. Digital Origination is the renamed Digital Lending feature; the underlying Discovery Framework config, org preferences, license, and permission set still carry the DigitalLending name. Triggers on \"set up Digital Origination\", \"configure DOP\", \"enable digital lending\", \"turn on loan origination\", \"prepare my org for Digital Origination\". Sequences the industries-fsc-digital-lending-initial-setup Discovery Framework feature (dependencies KYC + Discovery Framework, the digitalLendingPref + DiscoveryFrameworkMetadata org preferences, the DigitalLendingAdminUser permission gate, and the cloned Digital Lending admin permission-set assignment) into one ordered admin journey."
metadata:
  version: "1.0"
---

# Setting up Digital Origination (DOP) Initial Setup for Financial Services Cloud

**"Set up Digital Origination" / "Set up DOP" / "Configure Digital Origination" / "Enable digital
lending" with no narrowing qualifier means running the WHOLE Initial Setup journey — the two
prerequisite features (Discovery Framework, Know Your Customer), the Digital Origination feature
itself, Import or Export, enabling Discovery Framework Sample Templates, AND the required Manage
User Access step — in dependency order. It does
NOT mean "flip the Digital Origination toggle."** This is the Salesforce Go **Digital Origination
Initial Setup** page (Setup → Salesforce Go → Digital Origination Initial Setup), which prepares a
Financial Services Cloud org with the essential Digital Origination capabilities before an admin
configures product catalogs, pricing, qualification rules, or the client-experience portal.

Guide an FSC admin through this **as a real customer-org admin legitimately can**: validate the
external prerequisites (edition, license, add-ons — check only, never fabricate), turn on the two
prerequisite Discovery Framework features, prepare and assign an admin-capable clone of the Digital
Lending permission set, turn on Digital Origination, then enable Import or Export and Sample
Templates in Discovery Framework General Settings. Everything here is something
a customer admin could do themselves — just faster and in the right order.

## ⚠️ Naming: Digital Origination IS Digital Lending (read first)

Digital Origination (DOP) is the **renamed Digital Lending** feature. The customer-facing labels now
say "Digital Origination," but **every API name,
org preference, license, permission set, gate, and Discovery Framework config file still carries the
`DigitalLending` name.** When you query or configure the org, use the `DigitalLending` names —
they are the source of truth. When you talk to the admin, use "Digital Origination."

| Concept | Customer-facing label | Actual API / metadata name (use this against the org) |
|---|---|---|
| Feature / Salesforce Go page | Digital Origination Initial Setup | `industries-fsc-digital-lending-initial-setup` (feature enum `INDUSTRIES_FSC_DIGITAL_LENDING_INITIAL_SETUP`) |
| Core feature org preference | Digital Origination | `OrgPreferences.digitalLendingPref` (org perm `DigitalLending`) |
| Import/Export org preference | Import or Export | `OrgPreference.DiscoveryFrameworkMetadata` |
| Sample Templates preference | Discovery Framework → General Settings → Sample Templates | `OrgPreference.DiscoveryFrwrkSampleTemplate` / `IndustriesSettings.Metadata.enableDiscoveryFrwrkSampleTemplate` |
| Base permission set | Digital Lending | `DigitalLending` (standard, immutable; includes `DigitalLendingUser` but may not include the admin permission) |
| Admin permission-set requirement | Clone of Digital Lending | Custom clone with System Permission `DigitalLendingAdminUser` enabled, assigned to the acting admin |
| Gating user permission | Digital Origination Admin | `DigitalLendingAdminUser` |
| Platform license | Digital Origination | `DigitalLending` (`DigitalLending-1.pld.xml`) + `DigitalLendingPsl` |

If you find yourself telling the admin "there's no such thing as DigitalLending, it's Digital
Origination" — stop. Both are correct; the API layer just hasn't been renamed.

## Scope & definition of done — READ THIS FIRST

**"Set up Digital Origination" with no narrowing qualifier means run ALL of Steps 1→4 in order,
then enable Sample Templates, plus the required Manage User Access step.** It does **not** mean
"turn on the Digital Origination
preference." Turning on Digital Origination (Step 3) is only *one* of four ordered steps, and it is
**blocked** until Steps 1–2 (its prerequisite features) are on and the admin has the Digital
Origination Admin permission. If you find yourself about to run only Step 3 for an unqualified "set
up DOP" request, that is the bug this section exists to prevent — go back and start at Step 1.

**You are NOT done after Step 3 or Step 4.** The setup is complete only when Import or Export
(Step 4) and Discovery Framework Sample Templates are enabled, and the **required Manage User Access
step** has been handled (required permission sets and licenses assigned and verified). A run that ends
after the Digital Origination toggle is a *partial* run, not a
completed setup — say so plainly if you must stop early.

**A blocked step is reported, not silently skipped.** If a documented gate blocks a step (missing
license, missing prerequisite feature, missing admin permission), **report that gate explicitly and
still run every step that is not blocked** — never silently stop.

## Supported utterances

- "Set up Digital Origination" / "Set up DOP" / "Configure Digital Origination"
- "Run the Digital Origination initial setup" / "Prepare my org for Digital Origination"
- "Turn on Digital Origination" / "Enable Digital Origination"
- "Enable digital lending" / "Set up digital lending" (legacy name — same feature)
- "Turn on loan origination for FSC"

## Session state (track across the conversation)

- `target_org_alias` — the org being configured; confirmed explicitly before any write (never
  silently inherited).
- `true_prereqs_confirmed` — bool; the external prerequisites below all pass.
- `license_present` — is the Digital Lending / Digital Origination license provisioned on the org?
- `df_enabled`, `kyc_enabled` — the two prerequisite feature states (Steps 1 and 2).
- `dop_enabled`, `import_export_enabled` — Steps 3 and 4.
- `sample_templates_enabled` — Discovery Framework General Settings → Sample Templates preference.
- `admin_perm_present` — bool; does the current admin hold `DigitalLendingAdminUser`? (Gates Step 3.)
- `admin_perm_set_ready` — bool; an assigned custom clone of `DigitalLending` carries
  `DigitalLendingAdminUser`.
- `perm_sets_missing` — list of explicitly identified target users lacking the appropriate Digital
  Lending access; assign the verified required access, but never infer users or assign service accounts.

## Entry point — route on the admin's actual ask

**Default rule:** unless the admin's ask *explicitly narrows the scope* (a specific step, or "the
prerequisites are already on, I just need X"), treat it as the full setup and **run Steps 1→2 →
prepare admin permission set → Step 3 → Step 4 → enable Sample Templates → Manage User Access in
order.** When
in doubt, run the full journey.

| Signal | Where to start |
|---|---|
| **"Set up Digital Origination / DOP" / "enable digital lending" / no narrowing qualifier / no prior state known** | **Run the FULL journey: detect org state, validate prerequisites, run Step 1 → Step 2 → prepare and assign the admin-capable permission-set clone → Step 3 → Step 4 → enable Sample Templates → Manage User Access. NOT just the Step 3 toggle.** |
| "Discovery Framework and KYC are already on, I just need Digital Origination" | Confirm `df_enabled` + `kyc_enabled`, prepare/assign the admin-capable permission-set clone if needed, then run Step 3 → Step 4 → enable Sample Templates → user access. |
| "Just turn on Import or Export" | Step 4 only (`DiscoveryFrameworkMetadata`), after confirming Digital Origination is on. |
| "Assign the Digital Origination admin permission" | Check for an assigned custom clone of `DigitalLending` with `DigitalLendingAdminUser=true`; if absent, guide clone → enable System Permission → assign to admin. |
| "Set up Know Your Customer" / "set up Discovery Framework" alone | That's a prerequisite feature on its own — Step 1 or Step 2 in isolation; do not proceed into Digital Origination unless asked. |

## Prerequisites

### A. True prerequisites — external to this skill (validate only)

These gate the flow. If unmet, report which one and stop for that item — don't fabricate a license or
guess an entitlement. **Surface every item as a discrete checked line (✅/❌ + the value you queried),
up front, even when they all pass.**

- **Edition:** Financial Services Cloud (Enterprise or Unlimited).
- **License:** the **Digital Lending / Digital Origination** platform license must be provisioned
  (`DigitalLending-1.pld.xml`, which sets org perms `DigitalLending`, `DigitalLendingExtensions`,
  `Omnistudio`, `CompliantDataSharing`, and more; PSL `DigitalLendingPsl`). Absent → the feature tile
  will not be available in the org (`isFeatureAvailableInOrg` gates on
  `OrgHasAccessToDigitalLendingAndFSC`). Report and stop for Step 3 if it's missing.
- **Admin access** to the org, **plus the Digital Origination Admin user permission**
  (`DigitalLendingAdminUser`). This is a **hard enablement gate**: the feature's pre-enablement check
  blocks turn-on with a `NO_USER_PERMISSIONS` error if the
  admin lacks it. The standard `DigitalLending` permission set is immutable and can carry
  `DigitalLendingUser` without carrying `DigitalLendingAdminUser`; assigning it alone does not clear
  this gate. Check the permission fields rather than trusting the permission-set name.

**Explicitly excluded from this skill:** do not enable OmniStudio and do not enable Associated Object
Access. They can be handled by separate setup flows if requested, but they are not part of this DOP
journey and must not block or be inserted into its ordered steps.

### B. Automatable by this skill (the Steps below)

The two prerequisite feature enablements (Discovery Framework, Know Your Customer), the Digital
Origination feature preference, the Import-or-Export preference, the Discovery Framework Sample
Templates preference, and the required permission-set / permission-set-license assignments. Creating
or editing the custom admin permission-set clone may require a guided Setup UI checkpoint when no
verified API operation is available.

## Permission sets — prepare, assign, and verify automatically

Permission-set and permission-set-license assignments required by this workflow are part of the setup;
perform them without a separate confirmation prompt. Scope them safely: the acting admin is always an
explicit target, and additional users are targets only when the request names them or supplies an
authoritative list. Never assign access to Automated Process, integration, or other service accounts.
A `DUPLICATE_VALUE` response means the assignment already exists and is success, not an error.

For the acting admin, do not assume the standard **Digital Lending** permission set clears the gate.
Use this procedure before Step 3:

1. Inspect the acting user's assigned permission sets for `DigitalLendingAdminUser`.
2. If an assigned custom permission set already carries that permission, reuse it.
3. Otherwise create the admin-capable custom permission set through the verified sObject path: first
   query the standard `DigitalLending` permission set and reuse its
   `LicenseId`; then `POST /services/data/v62.0/sobjects/PermissionSet` with a unique API name (for
   example `Digital_Lending_Admin`), label **Digital Lending Admin**, that `LicenseId`,
   `PermissionsDigitalLendingUser=true`, and `PermissionsDigitalLendingAdminUser=true`. This is the
   API equivalent of cloning Digital Lending and enabling **System Permissions → Digital Lending
   Admin User**. Do not edit the standard permission set.
4. Re-query the new permission set and verify it is custom, bound to the Digital Lending PSL, and has
   both permission fields true. If permission-set creation is unavailable, use the Setup UI clone
   procedure instead.
5. Check whether the acting admin holds the permission set's Digital Lending PSL. If not, assign it
   first with `POST /services/data/v62.0/sobjects/PermissionSetLicenseAssign` using `AssigneeId` and
   `PermissionSetLicenseId`.
6. Assign the custom permission set with
   `POST /services/data/v62.0/sobjects/PermissionSetAssignment` using `AssigneeId` and
   `PermissionSetId`.
7. Re-query the assignment and permission fields. Proceed to Step 3 only when the acting user has an
   assigned permission set with both `DigitalLendingUser=true` and `DigitalLendingAdminUser=true`.

Before creating records, query for an equivalent custom permission set and existing assignments so
reruns remain idempotent.
If the sObject operations are unavailable, stop at the manual Setup checkpoint and resume after the
admin confirms completion.

The two prerequisite features have their own broader Manage-User-Access permission-set lists (FSC
Foundations/Sales/Service, Document Checklist, BRE, Compliance, Industries
Assessment, etc.) — surface those when handling Steps 1–2, but the DOP feature's own required step is
Digital Lending access appropriate to those users. Do not substitute
`DigitalLendingEditReadOnlyRecords` as the general end-user set unless product ownership confirms it;
its name and permission fields serve a narrower purpose.

## Enable & verify discipline (applies to every step — read before your first write)

1. **Use the Salesforce Go headless dispatcher as the primary write path.** Call
   `PATCH /headless/invoke/platform/salesforce-go/enable-feature` through `dispatch` (hosted) or
   `dispatch` (local development), with JSON body `{"featureApiName":"<feature-api-name>"}`.
   The operation is **PATCH, not POST**; POST can fail with `No controller mapping`. This invokes the
   platform's own `enableFeature()` recipe, including side-effect preferences. Use these feature API
   names in order:
   - Step 1: `industries-fsc-discovery-framework`
   - Step 2: `industries-fsc-know-your-customer`
   - Step 3: `industries-fsc-digital-lending-initial-setup`
   Step 3 may set Step 4 as a side effect, but Step 4 remains explicit: always read it and enable it
   directly when false.
2. **Do not confuse Connect API availability with dispatcher availability.** A 404 from
   `/connect/setup/discovery/*` does not mean the headless dispatcher is absent. Try the canonical
   Salesforce Go headless path above independently. Likewise, a dispatcher read serialization error
   does not mean its write path is unusable.
3. **MDAPI is a last-resort fallback, not the automatic fallback.** Only use an `IndustriesSettings`
   metadata deploy after the canonical headless write path itself is confirmed unavailable and the
   admin approves the fallback. If an MDAPI deploy or retrieve remains `Pending` with
   `numberComponentsTotal: 0`, treat the org's asynchronous metadata queue as unavailable: do not
   wait indefinitely and do not claim the preference changed. Report the job ID and verify current
   state through Tooling API.
4. **Respect the feature dependency order.** Digital Origination declares Know Your Customer and
   Discovery Framework as its feature dependencies. Step 3
   (Digital Origination) **cannot** be enabled before both are on. Enable Discovery Framework first
   (it also underpins KYC's assessments), then KYC, then Digital Origination.
5. **Clear the admin-permission gate before Step 3.** Read `DigitalLendingUser` and
   `DigitalLendingAdminUser` on permission sets assigned to the acting admin. If no assignment carries
   both, create the admin-capable custom permission set, enable **Digital Lending Admin User**, ensure
   the required PSL assignment exists, and assign the custom permission set. Do not attempt the
   Digital Origination toggle until the assignment reads back, or enablement is blocked with
   `NO_USER_PERMISSIONS`.
6. **Re-read to verify — never trust the write result.** Prefer the feature's documented access check.
   If `salesforce-go/get-feature-status` or another dispatcher read returns a `ConnectJSONFilter`
   serialization / `JSON_PARSER_ERROR`, verify through a Tooling API read of `IndustriesSettings.Metadata`:
   - Step 1: `enableIndustriesAssessment = true`
   - Step 2: `enableIndustriesKYC = true`, plus `enablePartyProfileParentSharingOrgPref = true` and
     `enablePartyprofParentMultiSharingOrgPref = true`
   - Step 3: `enableDigitalLendingPref = true`
   - Step 4: `enableDiscoveryFrameworkMetadata = true`
   - Post-step preference: `enableDiscoveryFrwrkSampleTemplate = true`
   A 200 response with an empty body, timeout, or reported change is not proof; the read-back is proof.
7. **Ground the final report in fresh queries**, not stale session notes — re-query end state
   immediately before reporting "done."
8. **Config ≠ data.** These steps enable *features and preferences*, not records. The Digital
   Origination data model (Application Form, Applicant, Application Form Product, etc.) and the sample
   app are separate — tell the admin that turning the feature on is necessary but not sufficient to
   *see* a working origination journey; that comes in the per-capability setup pages afterward.

## The Digital Origination Initial Setup journey — Steps 1→5 + Manage User Access

The two prerequisite features render on the Salesforce Go page as blue linked items ("Turn on
Discovery Framework", "Turn on Know Your Customer"); the Digital Origination and Import-or-Export
items are the feature's own automation steps. Run them in this order.

### Step 1 of 5 — Turn on Discovery Framework (prerequisite feature)

> Feature `INDUSTRIES_FSC_DISCOVERY_FRAMEWORK`. A declared dependency of Digital Origination — must be
> on first. Backed by `industries-fsc-discovery-framework.configuration.json`.

1. Turn on the **Discovery Framework** feature (org has `IndustriesAssessment`). Verify with the
   `IndustriesAssessment.orgHasIndustriesAssessment` access check. Use the canonical Salesforce Go
   enable call with `featureApiName: industries-fsc-discovery-framework`; if the access-check read
   cannot be serialized, verify `IndustriesSettings.Metadata.enableIndustriesAssessment = true`.
2. Its required post-enablement steps (Manage User Access with the FSC/Compliance/BRE/
   Industries-Assessment permission sets, Enhanced Questions, add the `industries_common:assessmentContainer`
   component to Account/Contact/Case/ApplicationForm/DisputeItem record pages, configure Question
   Category picklist values) are the Discovery Framework feature's own — handle them if the admin is
   doing a full DF setup, but the **minimum for DOP** is that Discovery Framework itself is on.

**Step 1 end state:** Discovery Framework enabled (`orgHasIndustriesAssessment` = true).

### Step 2 of 5 — Turn on Know Your Customer (prerequisite feature)

> Feature `INDUSTRIES_FSC_KNOW_YOUR_CUSTOMER`. The second declared dependency of Digital Origination.
> Backed by `industries-fsc-know-your-customer.configuration.json`.

1. Turn on the **Know Your Customer** feature — automation step `enableKYCFeature`
   (type `enableFeature`, critical), using the canonical Salesforce Go enable call with
   `featureApiName: industries-fsc-know-your-customer`.
2. The KYC config then flips a set of Party-profile org preferences (`PartyProfileParentSharing`,
   `PartyprofParentMultiSharing`) enabling Identity Document, Party Identity Verification, Party
   Profile Address / Risk / Screening Summary / Credit Profile, Party Expense / Income, Person
   Employment, Party Financial Asset / Liability. These fire as part of the KYC turn-on recipe — run
   them via the same enable path.
3. Its required step is Manage User Access with the FSC permission sets (`force__FSCFoundations`,
   `force__FSCSales`, `force__FSCService`, EU/OZ variants, `force__FinancialServicesCloudExtension`).

**Step 2 end state:** Know Your Customer enabled (`enableIndustriesKYC = true`); the Party-profile
preferences `enablePartyProfileParentSharingOrgPref` and
`enablePartyprofParentMultiSharingOrgPref` are both true.

### Step 3 of 5 — Turn on Digital Origination

> Automation step `enableDigitalLendingFeature` (type `enableFeature`, **critical**) →
> `OrgPreferences.digitalLendingPref`. This is the feature this whole page is named for. **Blocked
> until Steps 1–2 are on and the admin holds `DigitalLendingAdminUser`.**

1. **Precondition check (do this before toggling):** confirm `df_enabled` and `kyc_enabled` are both
   true (read them back — don't trust session memory), and confirm the acting admin has an assigned
   permission set carrying both `DigitalLendingUser` and `DigitalLendingAdminUser`.
2. If the admin permission is absent, follow the permission-set procedure above. Prefer creating the
   admin-capable custom permission set, required PSL assignment, and permission-set assignment through
   the verified sObject APIs; fall back to the Setup UI clone procedure only when
   those operations are unavailable. Do not continue until the assignment reads back successfully.
3. Turn on **Digital Origination** — set `OrgPreferences.digitalLendingPref = true` (enabling the
   feature sets this org preference; org perm `DigitalLending`) using the canonical
   Salesforce Go enable call with
   `featureApiName: industries-fsc-digital-lending-initial-setup`.
4. Verify with the `orgHasAccessToGlobalDigitalLending` access check (this is what the feature's
   enablement state reads). If that read cannot be serialized, verify
   `IndustriesSettings.Metadata.enableDigitalLendingPref = true` through Tooling API.

**Step 3 end state:** `digitalLendingPref` = true; `orgHasAccessToGlobalDigitalLending` = true.

### Step 4 of 5 — Turn on Import or Export

> Setup → Discovery Framework → General Settings → **Import or Export** →
> `OrgPreference.DiscoveryFrameworkMetadata = true`.

1. Read `IndustriesSettings.Metadata.enableDiscoveryFrameworkMetadata`. If true, Step 4 is complete.
2. If false, enable **Import or Export** directly through the Discovery Framework settings controller:
   call `PATCH /headless/invoke/platform/kyc-settings/handle-pref-enable` with
   `{"pref":"DiscoveryFrameworkMetadata","value":true}`. This is the same action as turning on the
   toggle in Setup → Discovery Framework → General Settings.
   This enables Discovery Framework metadata import/export so origination assessment forms and related
   metadata can be migrated between orgs.
3. Verify `IndustriesSettings.Metadata.enableDiscoveryFrameworkMetadata = true`. Non-critical: if it
   fails, report it but the core feature (Step 3) is still functional.

**Step 4 end state:** `DiscoveryFrameworkMetadata` = true.

### Step 5 of 5 — Enable Discovery Framework Sample Templates

> Setup → Discovery Framework → General Settings → **Sample Templates**. This is a separate
> preference from Import or Export and must run only after Steps 1→4 are verified.

1. Read `GET /headless/invoke/platform/kyc-settings` and inspect the Sample Templates enabled state
   when the response exposes it. If it is already enabled, do not write it again.
2. Otherwise call `PATCH /headless/invoke/platform/kyc-settings/handle-pref-enable` with body
   `{"pref":"DiscoveryFrwrkSampleTemplate","value":true}`. Use this controller path rather than a
   direct persistence write because its server-side allowlist, setup-admin / Industries Assessment
   gates, telemetry, and `instrumentDfOutOfTheBox` side effect are part of the operation.
3. Re-read the access-check map. If that response does not expose or serialize the state, verify
   `IndustriesSettings.Metadata.enableDiscoveryFrwrkSampleTemplate = true` through Tooling API.

**Step 5 end state:** Discovery Framework Sample Templates is enabled. Enabling the preference is the
end of this skill; do not fetch, deploy, or create records from sample templates.

### Required step — Complete the Required Steps → Manage User Access

> The Digital Origination Initial Setup config's own required post-enablement step
> (`completeRequiredSteps` → `userAssignment`, `progressType: required`). This is part of "done" —
> the setup is not complete until it's handled.

1. Confirm the acting admin has the cloned Digital Lending permission set with **Digital Lending Admin
   User** enabled, as required before Step 3.
2. Determine which additional users need Digital Origination access (loan officers, underwriters,
   bankers) and inspect their existing permissions.
3. For explicitly identified additional users, assign only access whose permission fields are verified
   to satisfy their requested role. Do not infer users from all active users, do not assign service
   accounts, and do not assume `DigitalLendingEditReadOnlyRecords` is the general user permission set.
4. Treat `DUPLICATE_VALUE` as already assigned and therefore successful.

**Required-step end state:** the acting admin's custom admin-capable permission set and PSL assignment
are verified, and access for every explicitly identified additional target user is assigned and
verified.

## Definition of done (the whole skill)

An unqualified Digital Origination setup is **complete only when all of the following hold**:
Step 1 (Discovery Framework enabled) → Step 2 (Know Your Customer enabled) → cloned Digital Lending
admin permission set prepared, assigned, and verified → Step 3
(`digitalLendingPref` on, verified via `orgHasAccessToGlobalDigitalLending`) → Step 4
(`DiscoveryFrameworkMetadata` on) → Discovery Framework Sample Templates enabled
(`enableDiscoveryFrwrkSampleTemplate`) → the required Manage User Access step handled. If any step is blocked by a
documented gate (missing license, missing prerequisite feature, missing admin permission), **report
the gate and complete every step that is not blocked** — then close with an explicit list of what
remains. Reporting "done" after only the Step-3 toggle is a defect, not a valid completion.

## Out of scope / deferred (call out, don't block on)

These are the *per-capability* configuration pages that come **after** Initial Setup — mention them as
follow-ups so the admin knows Initial Setup is the on-ramp, not the whole product:
OmniStudio enablement, Associated Object Access, Product Catalog Management, Product Configurator,
Product Qualification Rules, Pricing, Credit
Scoring, Disclosures and Consent, Stage Management, Integration Definitions / Orchestration, the
Client Experience (Experience Cloud) portal, Document Checklist / Matrix / Validation, and the sample
app / demo data. Each is its own Discovery Framework feature in the `DigitalLendingFeatureSet` and its
own setup page.

<!-- skill-validate: ignore-start -->
<!-- codey:operations start -->
## Operations Reference

Operations this skill uses — routing and dependency reference.

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `feature-status-precheck` | read | — | `GET /headless/invoke/platform/salesforce-go/get-feature-status` | — |
| `enable-discovery-framework` | write | — | `PATCH /headless/invoke/platform/salesforce-go/enable-feature` | `feature-status-precheck` |
| `enable-know-your-customer` | write | — | `PATCH /headless/invoke/platform/salesforce-go/enable-feature` | `enable-discovery-framework` |
| `clone-admin-permset` | write | — | `POST /services/data/vXX.0/sobjects/PermissionSet` | `enable-know-your-customer` |
| `assign-admin-psl` | write | — | `POST /services/data/vXX.0/sobjects/PermissionSetLicenseAssign` | `clone-admin-permset` |
| `assign-admin-permset` | write | — | `POST /services/data/vXX.0/sobjects/PermissionSetAssignment` | `assign-admin-psl` |
| `enable-digital-origination` | write | — | `PATCH /headless/invoke/platform/salesforce-go/enable-feature` | `assign-admin-permset`, `enable-know-your-customer` |
| `enable-import-export` | write | — | `PATCH /headless/invoke/platform/kyc-settings/handle-pref-enable` | `enable-digital-origination` |
| `enable-sample-templates` | write | — | `PATCH /headless/invoke/platform/kyc-settings/handle-pref-enable` | `enable-import-export` |
| `verify-composite-state` | verify | — | `GET /services/data/vXX.0/tooling/query` | `enable-discovery-framework`, `enable-know-your-customer`, `enable-digital-origination`, `enable-import-export`, `enable-sample-templates` |
<!-- codey:operations end -->
<!-- skill-validate: ignore-end -->
