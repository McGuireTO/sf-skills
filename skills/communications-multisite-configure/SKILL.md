---
name: communications-multisite-configure
description: "\"Enable MultiSite\" / \"turn on Location Based Quoting and Ordering\" / \"enable MultiLocationFeatureOrgPref\" / \"set up multi-recipient / multi-site quoting\" / \"verify the CME multi-recipient org permission\" / \"edit the Quote and Order page display columns / Recipient Wrapper fields\" for Communications Cloud. The concrete enablement layer of the Comms Cloud MultiSite steel thread (workflow #2): flip the MultiLocationFeatureOrgPref org preference, verify the CMEMultiRecipient org permission (and, from the perms side, the derived CMESales user permission), then edit the Quote/Order page display columns. Runs after comms-cloud-initial-setup and is delegated to from comms-cloud-multisite-setup."
metadata:
  version: "1.0"
---

# Communications Cloud — MultiSite Enablement (org preference + permission + display columns)

The **enablement layer** of the MultiSite steel thread (Comms Cloud workflow **#2**). Four concrete
pieces:

1. **Enable the `MultiLocationFeatureOrgPref` org preference** — the "Location Based Quoting and
   Ordering" toggle on the *Revenue Cloud for Communications Settings* page. **Mechanism: Toggle
   (OrgPreference) via the approved SOR `RevenueCloudforCommunicationsSettings`, over its friendly
   `/headless/invoke/industries/industries-communications-sales/…` route — headless, no gap, proven
   end-to-end.**
2. **Verify the `CMEMultiRecipient` org permission** and, from the permissions side, the derived
   `CMESales` user permission. **Mechanism: read/verify (headless) + permission-set assignment
   (headless); provisioning the org permission itself is out-of-band (licensing).**
3. **Edit the Quote and Order page display columns** (Locations tab / Recipient Wrapper fields).
   **Mechanism: Manual-UI (Lightning App Builder + Flow Builder) — ⚠ GAP, no headless surface.**
4. **Stand up the Context Service extension that backs the multi-recipient attributes** — a custom
   context-definition extension (`baseReference` on the standard `ConsumerSalesContext__stdctx`) that
   adds the recipient / recipient-group attributes + mappings + hydration the Quote/Order pages surface
   in Step 3 (e.g. `RecipientCity__c → ServiceCity`, the RecipientGroup counts). **Mechanism: Context
   Connect API (native REST) via `dispatch` — headless, no gap, proven end-to-end.** *Sequencing: the
   context attributes must exist before Step 3 can surface them, so run Step 4 before Step 3's page
   edits.*

> **STATUS.** Steps 1–2 (org preference + permission verification) and **Step 4 (Context Service
> extension)** are grounded, headless, and **verified end-to-end on a dev org via `dispatch` (create +
> activate + read-back / structural compare, no `sf` CLI)** — see the boxes in Steps 1 and 4. Step 3
> (page display columns) is a **Manual-UI gap** — documented here so an admin can complete it, but there
> is no headless/dispatch path for it today.

## Grounding (source of truth)

All API names below come from the **`IndustriesCommunicationsSales` UDD setting group** (module
`industries-communications-sales-udd`, owner *Comms Cloud Grand Canyon*) — the authoritative
definition of these org permissions, user permissions, and org preferences. The org-preference
read/write **mechanism** is the approved SOR **`RevenueCloudforCommunicationsSettings`**: read
`get-comms-org-preferences`, write `set-multi-location-enabled` / `set-multi-subscriber-enabled`.

| UDD element | API name | Kind | minApiVersion | Gate |
|---|---|---|---|---|
| Org preference | `MultiLocationFeatureOrgPref` | orgPreference (boolean) | 262 (API v67.0) | `orgAccess = OrgPermissions.MultiRecipient \|\| OrgPermissions.CMEMultiRecipient`; `editAccess = UserPermissions.CustomizeApplication`; `sysAdminEditable=true` |
| Org permission | `CMEMultiRecipient` | orgPermission, `type="provisioned"` | 260 (API v66.0) | "Allows an org to use CME MultiSite/MultiRecipient features" |
| Org permission | `MultiRecipient` | orgPermission, `type="provisioned"` | 254 | "features related to MultiRecipient" — the *base* alternative gate for the org pref |
| User permission | `CMESales` | userPermission (`PermissionsCMESales`) | 260 | `orgAccess = OrgPermissions.CMEMultiRecipient` |
| User permission | `UseCommsCloudSalesFeatures` | userPermission (`PermissionsUseCommsCloudSalesFeatures`) | 258 | `orgAccess = OrgPermissions.CommsSales` |

Related org preferences unlocked by `CMEMultiRecipient` (out of scope here, listed for context):
`MultiSubscriberFeatureOrgPref`, `CMELinearRelationshipRulePref`.

## Scope & definition of done

**In scope:** enable `MultiLocationFeatureOrgPref`; verify `CMEMultiRecipient` and assign the derived
`CMESales` user permission; document the Quote/Order page display-column edits.

**Definition of done:** `get-comms-org-preferences` returns `multiLocationEnabled: true`; `CMESales`
assigned to the intended profile/permission set (only if the org permission gate is satisfied); the
Manual-UI page edits documented/handed to the admin.

## Preconditions

- **Communications Cloud initial setup complete** — see `comms-cloud-initial-setup` (the three sales
  permission sets assigned; Revenue Cloud base + context service + pricing set up).
- **Licenses required for MultiSite** (per Comms Cloud #2): `CommsCloudRLMAddOn`,
  `CSVImportLicenseAddOn`, `RevenueLifecycleManagementAddOn`, `CMERLMB2BAddon`. The CME add-on
  (`CMERLMB2BAddon`) is what provisions the `CMEMultiRecipient` org permission (Step 2); the
  MultiRecipient PermissionSetLicenses (`CMEMultiRecipientPsl`, `RevLifecycleMgmtMultiRecipientPsl`)
  back the org-permission gate.
- **Running-user permissions** (per Comms Cloud #2): *View Setup and Configuration*; *Modify All Data*
  **or** *Customize Application* (the org pref's `editAccess`); *Assign Permission Sets*; *Manage
  Users*; *Manage Profiles and Permission Sets*; *Revenue Cloud for Communications Features*; *Manage
  Flow*.

---

## Step 1 — Enable `MultiLocationFeatureOrgPref` (Location Based Quoting and Ordering)

**Mechanism: Toggle (OrgPreference) via the approved SOR `RevenueCloudforCommunicationsSettings`, over
its friendly `/headless/invoke/industries/industries-communications-sales/…` route. Headless — no gap.
All calls go through `dispatch`; the `sf` CLI is never used.**

> **Surface correction (load-bearing).** This pref is **NOT** on the generic native-REST org-preference
> registry: `GET`/`PATCH /services/data/v67.0/setup/org/preferences/MultiLocationFeatureOrgPref`
> returns **`404 NOT_FOUND` for both verbs** (the unrelated `CorePricingPreference` 200s on that same
> surface, so the surface works — this Industries pref simply isn't registered on it). **Do not use
> `/setup/org/preferences/…` for this toggle.** The working surface is the approved SOR's own friendly
> `/headless/invoke/industries/industries-communications-sales/…` route.

**Call shape — friendly route via `dispatch`.** The approved SOR
`RevenueCloudforCommunicationsSettings` publishes these operations into the dispatch route table, so a
plain `dispatch` to the friendly path resolves the controller for you — no envelope, no internal class
path. Scalar write args ride in the request `body`.

- **Read** — `GET /headless/invoke/industries/industries-communications-sales/get-comms-org-preferences`
  → `{ multiLocationEnabled, multiSubscriberEnabled, productRelationshipRuleEnabled, qtyEditEnabled }`.
- **Write** — `PATCH /headless/invoke/industries/industries-communications-sales/set-multi-location-enabled`
  with body `{ "value": true }` → returns `true` on success.

**1a. Read first (`get-comms-org-preferences`) — this doubles as the org-permission gate probe.**
- **`200` with a prefs map** → the `userCanUseMultiRecipientFeatureEnabled` gate passes (the org has
  `MultiRecipient || CMEMultiRecipient`). Inspect `multiLocationEnabled`:
  - `true` → already enabled; done.
  - `false` → proceed to the write (1b).
- **`403` / access-guard error** → the org-permission gate is unmet (neither base `MultiRecipient` nor
  `CMEMultiRecipient` is provisioned — see Step 2). Surface it as a licensing/provisioning gap and stop.

**1b. Write `set-multi-location-enabled` with `{value:true}`, then re-read `get-comms-org-preferences`**
and confirm `multiLocationEnabled:true`. A `true` return on the write alone is not proof — always read
back. Editing requires **Customize Application** (the pref's UDD `editAccess`).

> **Verified on a dev org (via `dispatch`, no `sf` CLI).** `get-comms-org-preferences` → `200
> {multiLocationEnabled:true, multiSubscriberEnabled:false, productRelationshipRuleEnabled:false,
> qtyEditEnabled:false}` — **the pref is already enabled and the gate passes**;
> `set-multi-location-enabled {value:true}` → `200 true`; read-back → `multiLocationEnabled:true`. The
> dev org holds both `CMEMultiRecipientPsl` and `RevLifecycleMgmtMultiRecipientPsl` PermissionSetLicenses
> (Active), so the base org-permission gate is satisfied there. **Correction:** an earlier claim that a
> `404` on `/setup/org/preferences/…` meant a licensing gap was wrong — that `404` was a *wrong-surface*
> artifact of the native-REST path, not a licensing gap. Dev/scratch success is still not proof of
> prod-safety.

**UI equivalent (for the admin):** Setup → *Revenue Cloud for Communications Settings* → turn on
**Location Based Quoting and Ordering**.

---

## Step 2 — Verify the `CMEMultiRecipient` org permission (and the perms-side `CMESales` user perm)

**Mechanism: read/verify (headless) + permission-set assignment (headless). Provisioning the org
permission is out-of-band.**

**Key fact — you cannot flip `CMEMultiRecipient` from the permissions UI.** It is an **org permission
with `type="provisioned"`** — granted by *license/feature provisioning* (the `CMERLMB2BAddon` add-on),
not by an admin toggle or a permission-set field. There is no headless "enable org permission" step
because there is no such admin operation; the only way to obtain it is to provision the licence.

**2a. Verify presence — the cheapest signal is the Step-1 read.** If `get-comms-org-preferences`
(Step 1a) returned **`200` (not `403`)**, the `userCanUseMultiRecipientFeatureEnabled` gate —
`OrgPermissions.MultiRecipient || OrgPermissions.CMEMultiRecipient` — is already satisfied, so the base
org permission is present. To distinguish base-vs-CME and confirm the CME tier, corroborate via
licenses and the derived user permission (a provisioned org permission has no direct admin read
surface):
- **License check** — `SELECT DeveloperName, MasterLabel, Status FROM PermissionSetLicense`; look for
  the MultiRecipient PSLs `CMEMultiRecipientPsl` (CME tier) and `RevLifecycleMgmtMultiRecipientPsl`
  (base) Active, plus the add-ons in Preconditions. Absent `CMEMultiRecipientPsl` ⇒ the CME tier isn't
  provisioned even if base `MultiRecipient` is.
- **PSL-assignment check (the reliable CME-tier signal)** — `SELECT AssigneeId, Assignee.Name,
  PermissionSetLicense.DeveloperName FROM PermissionSetLicenseAssign WHERE
  PermissionSetLicense.DeveloperName IN ('CMEMultiRecipientPsl','RevLifecycleMgmtMultiRecipientPsl')`. A
  `CMEMultiRecipientPsl` row means the CME seat is assigned to a real user, so the CME tier is
  provisioned and `CMESales` is assignable.
- **Named permission-set check** — query the CME set **specifically**: `SELECT Id, Name, Label FROM
  PermissionSet WHERE Name = 'CMESalesStandardPermissionSet' OR Label = 'CME Sales Features'`. A row here
  confirms the assignable CME Sales permission set exists; use its `Id` as the `PermissionSetId` in 2b.
  Do **not** substitute `CommsCloudSalesFeatures` (Label 'Revenue Cloud for Communications Features') — it
  is a **distinct base-tier** set carrying only `PermissionsUseCommsCloudSalesFeatures` (assigned during
  `comms-cloud-initial-setup`), **not** the CME/MultiSite grant. If a broad query surfaces both, pick the
  `CMESalesStandardPermissionSet` row; assigning the base set leaves the user without MultiSite.

> ⚠ **Do NOT detect CME via the `PermissionsCMESales` boolean column.** The `Permissions*` columns on
> `PermissionSet` (including `PermissionsCMESales` and the base `PermissionsUseCommsCloudSalesFeatures`)
> are frequently **not SOQL-queryable** even when the feature is fully provisioned and the permission set
> is assigned — `SELECT ... WHERE PermissionsCMESales = true` returns **0 rows** and a `FieldDefinition
> LIKE 'PermissionsCME%'` probe returns nothing / `No such column`. **That is a query-surface limitation,
> not evidence the tier is absent** (observed on a dev org that had `CMEMultiRecipientPsl` assigned and
> `CMESalesStandardPermissionSet` present). Detect via the **PSL-assignment** + **named permission-set**
> checks above instead.

**2b. If the CME tier is provisioned (a `CMEMultiRecipientPsl` seat is assigned AND the CME Sales
permission set exists) → enable from the perms side.** Assign the **`CMESalesStandardPermissionSet`**
found in 2a to the intended user (headless, standard permission-set assignment — the same mechanism
`comms-cloud-initial-setup` uses): `POST /sobjects/PermissionSetAssignment {AssigneeId, PermissionSetId}`,
where `PermissionSetId` is the `CMESalesStandardPermissionSet` Id.
The `CMESalesStandardPermissionSet` carries `PermissionsCMESales` (gated on `CMEMultiRecipient`) — this is
the MultiSite grant; `CommsCloudSalesFeatures` carries the base `PermissionsUseCommsCloudSalesFeatures`
(gated on `CommsSales`) and is **not** interchangeable — never assign it as the CME tier.

**2c. Only if the CME tier is genuinely absent (NO `CMEMultiRecipientPsl` seat AND NO CME Sales
permission set) → report a licensing gap, do not proceed to enable.** Note that
`MultiLocationFeatureOrgPref` (Step 1) may still be enableable via the **base `MultiRecipient`** org
permission (minApi 254) even without the CME add-on — but CME-specific MultiSite/MultiRecipient
features (and `MultiSubscriberFeatureOrgPref`, `CMELinearRelationshipRulePref`) will not be available.

> ⚠ **GAP — provisioned org permission.** `CMEMultiRecipient` cannot be enabled headlessly or from
> Setup; it is licence-provisioned. This step *verifies and reports*; it does not (and cannot) grant it.

---

## Step 3 — Edit the Quote and Order page display columns  ⚠ Manual-UI GAP

**Mechanism: Manual-UI (Lightning App Builder + Flow Builder). No headless/dispatch surface today.**
Enabling Step 1 adds the **Locations** capability; surfacing it on the pages is a manual App Builder
edit. Document these for the admin (fields below are the SMB Fiber recipient attributes defined in
**Comms Cloud #3 — SMB Fiber Products**).

**3a. Add the Locations tab + Recipient Wrapper (Edit Quote and Order Page):**
1. Click the **Tab** component → **Add Tab** in the Tabs component properties.
2. Set the tab label to **Custom** and enter **Locations**.
3. Drag the **Recipient Wrapper** component into the Location section.
4. **Save** → **Activate** the page → **Assign as Org Default**.

**3b. Quote Line Items section → Select from Display Columns** — move these from Available to Selected,
then **OK → Save → Activate**:
`Product` · `Quantity` · `Quote Recipient Group` · `Recipient Scaled Quantity` ·
`Selling Model Type` · `Discount (Percentage)` · `List Price` · `Total Price` ·
`Quote Line Item Recipient`.

**3c. Recipient Wrapper → Display Fields (Locations tab)** — under *Display Fields → Select…*, move to
Selected and arrange:
`Service Street` · `Max Download Speed` · `Max Upload Speed` · `Service Postal Code` ·
`Broadband Connection Type` · `Service City` · `Service Country` · `Service State` · `Name`.

**3d. Recipient Wrapper → Organise Fields (View By Predefined Type)** — under *Organise Fields →
Select…*, move to Selected:
`Service Street` · `Max Download Speed` · `Max Upload Speed` · `Service Postal Code`.

**3e. Onboarding Flow (optional, Manual-UI / Flow Builder).** In the *Customer Onboarding* flow, create
a Text collection variable (Allow multiple values, Available for input), add an Assignment after the
*Customer Quote Form* element that Adds `QuoteLineItemRecipient.<column_name>` entries, then on the
*ValidateAddress* element's **Recipient Wrapper** component select that collection variable under
**Display Fields** (and repeat with a second collection variable under **Organise Fields**). Save +
activate the flow.

> ⚠ **GAP — Manual-UI.** Steps 3a–3e have no headless surface. An agent cannot verify the page/flow
> state via `dispatch`; verification is visual/manual.

---

## Step 4 — Stand up the Context Service extension for multi-recipient attributes  (headless)

**Mechanism: Context Connect API (native REST) via `dispatch` — headless, no gap.** All calls are plain
authenticated `dispatch` to `/services/data/v67.0/connect/context-*` (native-REST pass-through, **not**
the `/headless/invoke` envelope, **not** the `sf` CLI). Every op carries the org-access-check
**`Context Definitions enabled`**. *Run this before Step 3 — the page can only surface attributes that
already exist on the context definition.*

**What this is.** The multi-recipient / MultiSite recipient fields the Quote/Order pages show (Step 3:
`Service City`, the Recipient Group counts, …) are backed by a **Context Service context definition**.
A fresh Comms Cloud org already ships the standard **`ConsumerSalesContext__stdctx`** definition. You do
**not** rebuild it and you do **not** diff it against anything at run time — you create a thin **custom
extension** of it (`definitionType: custom_nonexecutable`, `baseReference:
ConsumerSalesContext__stdctx`) that inherits every base node/attribute untouched and layers on **only**
the MultiSite deltas below. (The CME B2B reference definition `CME_264_B2B_Ctx` was used *once, offline*,
to derive exactly which deltas are needed — the concrete list is now baked into the tables below, so no
CMEB2B definition need exist in the target org.)

The delta is small and fully specified: **5 new attribute definitions** across 2 inherited nodes, and
**16 attribute-mappings** across all **4** entity groups (Cart / Quote / Order / **Asset**). Nothing is
removed; no new node is created.

**5a. Delta attribute definitions to add** (onto the two already-inherited nodes):

| Inherited node | Attribute (`key`/`title`) | dataType |
|---|---|---|
| `SalesTransactionItem` | `RecipientCity__c` | string |
| `SalesTransactionItem` | `RecipientGroupMemberCount__c` | number |
| `SalesTransactionItem` | `RecipientGroupExpectedCount__c` | number |
| `SalesTransactionItem` | `DerivedSellingModelType__c` | string |
| `SalesTransactionItemDetail` | `SalesTransactionItemDetailGroup__c` | string |

All five are `fieldType: inputoutput`. That's **5 attribute definitions** — but each maps into more than
one entity, giving 16 mappings below.

**5b. The 16 attribute-mappings — one row per (entity group → node → sObject → attribute).** `src` is the
`contextInputAttributeName` (the field/relationship the mapping reads); `hydration` is spelled out for
the 5 rows that need it, everything else is a plain direct field.

**Cart group** (`CartEntitiesMapping`) — all 5 direct, no hydration:

| Node | sObject | attribute | src | hydration |
|---|---|---|---|---|
| `SalesTransactionItem` | `CartItem` | `RecipientGroupMemberCount__c` | `RecipientGroupMemberCount__c` | — direct |
| `SalesTransactionItem` | `CartItem` | `RecipientGroupExpectedCount__c` | `RecipientGroupExpectedCount__c` | — direct |
| `SalesTransactionItem` | `CartItem` | `RecipientCity__c` | `RecipientCity__c` | — direct |
| `SalesTransactionItem` | `CartItem` | `DerivedSellingModelType__c` | `DerivedSellingModelType__c` | — direct |
| `SalesTransactionItemDetail` | `CartItemDetail` | `SalesTransactionItemDetailGroup__c` | `SalesTransactionItemDetailGroup__c` | — direct |

**Quote group** (`QuoteEntitiesMapping`) — 4 hydrated + 1 direct:

| Node | sObject | attribute | src | hydration |
|---|---|---|---|---|
| `SalesTransactionItem` | `QuoteLineItem` | `RecipientGroupMemberCount__c` | `RecipientGroupMemberCount__c` | 2-hop `QuoteLineItem → QuoteRecipientGroup` → leaf `ActualMemberCount` |
| `SalesTransactionItem` | `QuoteLineItem` | `RecipientCity__c` | `RecipientCity__c` | 2-hop `QuoteLineItem → QuoteLineItemRecipient` → leaf `ServiceCity` |
| `SalesTransactionItem` | `QuoteLineItem` | `RecipientGroupExpectedCount__c` | `RecipientGroupExpectedCount__c` | 2-hop `QuoteLineItem → QuoteRecipientGroup` → leaf `ExpectedMemberCount` |
| `SalesTransactionItem` | `QuoteLineItem` | `DerivedSellingModelType__c` | `DerivedSellingModelType__c` | 1-hop `QuoteLineItem → Derived_Selling_Model_Type__c` |
| `SalesTransactionItemDetail` | `QuoteLineDetail` | `SalesTransactionItemDetailGroup__c` | `SalesTransactionItemDetailGroup__c` | — direct |

**Order group** (`OrderEntitiesMapping`) — 1 hydrated + 4 direct:

| Node | sObject | attribute | src | hydration |
|---|---|---|---|---|
| `SalesTransactionItem` | `OrderItem` | `RecipientCity__c` | `RecipientCity__c` | 2-hop `OrderItem → OrderItemRecipient` → leaf `ServiceCity` |
| `SalesTransactionItem` | `OrderItem` | `RecipientGroupExpectedCount__c` | `RecipientGroupExpectedCount__c` | — direct |
| `SalesTransactionItem` | `OrderItem` | `RecipientGroupMemberCount__c` | `RecipientGroupMemberCount__c` | — direct |
| `SalesTransactionItem` | `OrderItem` | `DerivedSellingModelType__c` | `DerivedSellingModelType__c` | — direct |
| `SalesTransactionItemDetail` | `OrderItemDetail` | `SalesTransactionItemDetailGroup__c` | `SalesTransactionItemDetailGroup__c` | — direct |

**Asset group** (`AssetEntitiesMapping`) — 1 mapping (do **not** skip this group):

| Node | sObject | attribute | src | hydration |
|---|---|---|---|---|
| `SalesTransactionItemDetail` | `SalesTransactionItemDetail` | `SalesTransactionItemDetailGroup__c` | `SalesTransactionItemDetailGroup__c` | — direct |

**Why hydration only in Quote/Order.** On `CartItem` and `OrderItem` the recipient/count/selling-model
values live as direct columns, so the mapping reads them straight. On `QuoteLineItem` those same values
live on related records (`QuoteRecipientGroup`, `QuoteLineItemRecipient`) — hence the 2-hop trees — and
`Derived_Selling_Model_Type__c` is reached via a single hop. `RecipientCity__c` on `OrderItem` is the one
Order-group value that also lives on a related record (`OrderItemRecipient`), so it too hydrates. **5
mappings hydrate (4 two-hop + 1 one-hop); the other 11 are direct.**

**Call sequence (all `dispatch`, base `/services/data/v67.0/connect/`):**

1. **Preflight the base, then create the extension.** First confirm the base definition exists —
   `GET /context-definitions/ConsumerSalesContext__stdctx` must return `200`. A fresh Comms Cloud org
   ships it; a `404` means Context Service / the standard Consumer Sales context isn't provisioned in this
   org — **stop and resolve that first**, since the whole extension `baseReference`s it and the create will
   otherwise fail. Then `POST /context-definitions` with body
   `{"developerName":"customcommsconsumersalescd","name":"customcommsconsumersalescd","baseReference":"ConsumerSalesContext__stdctx"}`
   (sensible default — rename freely, but mind two wire-proven limits: **`name` (the label) must be ≤30
   chars, alphanumeric only, NO spaces** — a spaced/long label is rejected `INVALID_INPUT`/`RECORD_CREATION_FAILED`;
   `developerName` allows underscores, starts with a letter, no trailing/double underscore). **The `POST` is
   asynchronous: a `500 INTERNAL_ERROR` (or timeout) is a spurious sync-timeout, NOT a failure — the record
   materializes a moment later. Do not branch on 200-vs-500; confirm by polling.** Poll
   `GET /context-definitions/{developerName}` up to ~6× with a short wait, and read the *shape*, not `isSuccess`:
   when `contextDefinitionId` is a real id (starts with `11O…`) and `contextDefinitionVersionList` is non-empty
   the create is done — capture that `11O…` id and stop. While it is still in-flight (or genuinely absent) the GET
   returns an identical empty shell (`isSuccess:false`, `contextDefinitionId` echoing the developerName, empty
   version list) — that shape is NOT proof of absence, so keep polling until the window elapses. Re-`POST` only if
   the whole window stays the echo-shell; and if a `POST` ever returns "already exists"/duplicate, that PROVES it
   was created — **never `DELETE` and recreate** (delete-then-recreate on a just-created record is the infinite
   loop). Returns the new `contextDefinitionId`. (Leave `isActive` off / false — activate last, step 7, after the context tags in step 6.) Then
   `GET /context-definitions/{id}` (or `getContextDefinitionWithDynamicAttributes`) to read back the
   inherited node/mapping ids — you need each node's `contextNodeId` (step 2) and each entity's
   `nodeMappingId` (step 3), and they're inherited from the base, not authored by you.
2. **Add the 5 delta attribute definitions** (table 5a) — `POST /context-nodes/{contextNodeId}/context-attributes`
   with `{"contextAttributes":[ {"name":"RecipientCity__c","dataType":"STRING","fieldType":"INPUTOUTPUT"}, … ]}`:
   the 4 recipient attributes onto the `SalesTransactionItem` node, `SalesTransactionItemDetailGroup__c`
   onto the `SalesTransactionItemDetail` node. **`dataType`/`fieldType` are UPPERCASE enums** (`STRING`,
   `NUMBER`, …, `INPUTOUTPUT`) — the values are stored and returned uppercase; map the 5a table's
   `string`/`number` to `STRING`/`NUMBER`. **Capture the returned `contextAttributeId` for each** — the
   response `attributes[]` (and a follow-up GET) carry it, and step 3 references the attribute **by that
   id**, not by name.
3. **Create the 16 attribute-mappings** (table 5b) — `POST /context-node-mappings/{nodeMappingId}/context-attribute-mappings`
   with `{"contextAttributeMappings":[ {…} ], "deleteExistingHydrationDetails": false}`, once per entity
   group's node-mapping — **all four: Cart, Quote, Order, and Asset.** Each mapping element is
   `{"contextAttributeId":"<id from step 2>","contextInputAttributeName":"<src>"}` — the mapping links to
   the attribute by its **`contextAttributeId`** (there is **no** `contextAttribute`/`contextAttributeName`
   input field; posting a name is silently ignored → the mapping binds to nothing). The 11 direct rows stop
   there; the 5 hydrated rows add a `hydrationDetails` block (step 4). The Asset group is a single mapping
   (`SalesTransactionItemDetailGroup__c` on `SalesTransactionItemDetail`) — easy to forget; do not skip it.
4. **Attach hydration on the same POST** (the hydrated rows) via a `hydrationDetails` block. The wrapper is
   **recursive at every level**: the top `hydrationDetails` value **and** each hop's `childDetails` value are
   the object `{"contextAttrHydrationDetails":[ <hop>, … ]}` — **never a bare array**. Each hop is
   `{"queryAttribute":"<rel-or-field>","sObjectDomain":"<parent sObject>","childDetails":{…}}`, and a **leaf
   hop OMITS `childDetails` entirely** (a bare-array `childDetails:[…]`, an empty `childDetails:[]`, or a
   `childDetails:{queryAttribute:…}` object without the `contextAttrHydrationDetails` wrapper are all
   rejected with `JSON_PARSER_ERROR`). **2-hop** (e.g. Quote `RecipientCity__c` — `childDetails` re-wraps):
   ```json
   {"hydrationDetails":{"contextAttrHydrationDetails":[
     {"queryAttribute":"QuoteLineItemRecipient","sObjectDomain":"QuoteLineItem",
      "childDetails":{"contextAttrHydrationDetails":[
        {"queryAttribute":"ServiceCity","sObjectDomain":"QuoteLineItemRecipient"}
      ]}}
   ]}}
   ```
   **1-hop** (Quote `DerivedSellingModelType__c` → a single leaf hop, `childDetails` omitted):
   ```json
   {"hydrationDetails":{"contextAttrHydrationDetails":[
     {"queryAttribute":"Derived_Selling_Model_Type__c","sObjectDomain":"QuoteLineItem"}
   ]}}
   ```
   Two attributes may share the first hop and differ only by the leaf `queryAttribute` (the two
   RecipientGroup counts both hop `QuoteLineItem → QuoteRecipientGroup`, differing only by leaf
   `ActualMemberCount` vs `ExpectedMemberCount`) — that is **not** a collision. On **read-back**, the same
   tree renders under `contextAttrHydrationDetailList` where `childDetails` IS a plain array — the array↔
   object-wrapper asymmetry between read and POST-input is the single biggest time-sink here.
   > ⚠ **The 1-hop leaf `QuoteLineItem.Derived_Selling_Model_Type__c` must exist on the target org.** This
   > mapping is a **CMEB2B delta** — it exists because the `CME_264_B2B_Ctx` reference definition maps it on
   > `QuoteLineItem` (Cart/Order carry the value as a direct column instead). If that custom field is **absent
   > on the target org's `QuoteLineItem`**, the hop can't resolve and this one tree silently no-ops → you get
   > **4/5** hydration trees, not 5. The field's provisioning source is org-dependent (present on one
   > verification org, absent on another) — **verify the field exists before expecting all 5**; do not assume
   > any particular steel thread creates it.
5. **Verify each write with a read-back** — `GET /context-node-mappings/{nodeMappingId}/context-attribute-mappings/{attrMappingId}`;
   the persisted hydration renders under `contextAttrHydrationDetailList` with the nested leaf under
   `childDetails`. Confirm all 16 mappings and all 5 hydration trees are present.
6. **Create a context tag for each delta attribute — COMPULSORY, do this BEFORE activation (step 7).** The 5 attribute
   definitions from step 2 are *not enough on their own*: a Pricing Procedure (ExpressionSet,
   `interfaceSourceType=PricingProcedure`) resolves an attribute's **data type by its context-tag
   name, not by the attribute name**. Every base attribute inherits a tag automatically, but the
   **skill-added deltas do not** — so without this step the extension is structurally complete yet a
   Pricing Procedure that references it fails to compile with
   **`Specify a valid data type for the formula-section-0-output variable`** (the tag lookup returns
   nothing → unresolvable data type). Create one tag per delta, **tag `name` == the attribute's API
   name** (this mirrors how `CME_264_B2B_Ctx` tags its custom `__c` deltas — the tag `<title>` equals
   the attribute API name):

   `POST /context-definitions/{contextDefinitionId}/context-tags` with

   ```json
   {"contextTags":[
     {"name":"RecipientCity__c",                 "contextAttributeId":"<RecipientCity__c id>"},
     {"name":"RecipientGroupMemberCount__c",      "contextAttributeId":"<RecipientGroupMemberCount__c id>"},
     {"name":"RecipientGroupExpectedCount__c",    "contextAttributeId":"<RecipientGroupExpectedCount__c id>"},
     {"name":"DerivedSellingModelType__c",        "contextAttributeId":"<DerivedSellingModelType__c id>"},
     {"name":"SalesTransactionItemDetailGroup__c","contextAttributeId":"<SalesTransactionItemDetailGroup__c id>"}
   ]}
   ```

   | Tag `name` (== attribute API name) | Links to attribute on node |
   |---|---|
   | `RecipientCity__c` | `SalesTransactionItem` |
   | `RecipientGroupMemberCount__c` | `SalesTransactionItem` |
   | `RecipientGroupExpectedCount__c` | `SalesTransactionItem` |
   | `DerivedSellingModelType__c` | `SalesTransactionItem` |
   | `SalesTransactionItemDetailGroup__c` | `SalesTransactionItemDetail` |

   **Wire gotchas (both cost a round-trip if missed):**
   - The tag-input schema accepts **only `name` + `contextAttributeId`**. Posting `dynamic` (or any
     other field copied from the read-back shape) is rejected `400 JSON_PARSER_ERROR:
     "Unrecognized field 'dynamic'"`. `dynamic` defaults to `false` and comes back on the response —
     it is **output-only**, never input.
   - A tag binds to its attribute **by `contextAttributeId`** (the id captured in step 2), same as the
     mappings — there is no name-based binding.

   Returns a `contextTagId` per tag. Verify with `GET /context-definitions/{id}/context-tags` (or the
   `attributeTags[]` on a `getContextDefinitionWithDynamicAttributes` read-back) — the 5 deltas should
   now each carry a tag whose `name` equals the attribute API name.
7. **Set a default mapping FIRST, then activate (LAST step).** Activation refuses a definition that has no default
   entity-mapping (`400 DATA_MAPPING_NOT_FOUND: "Cannot activate a definition without default mapping"`) —
   and the inherited mappings come across with `isDefault:false`, so you **must** flip one on yourself. Mirror
   the **base** default: read `GET /context-definitions/ConsumerSalesContext__stdctx`, find the
   `contextMappings[]` entry with `isDefault:true` (it is **`CartEntitiesMapping`**), then
   `PATCH /context-definitions/{contextDefinitionId}/context-mappings` with
   `{"contextMappings":[{"contextMappingId":"<your Cart mapping id>","name":"CartEntitiesMapping","isDefault":true}]}`.
   Only then `PATCH /context-definitions/{contextDefinitionId}` with `{"isActive": true}` → returns
   `isActive:true` + an `activeVersionId`. Confirm both. The context tags (step 6) **must already exist
   before this activate** — activating first leaves the deltas untagged and a downstream Pricing
   Procedure won't compile.

> **Load-bearing gotchas.**
> - **A mapping references its attribute by `contextAttributeId`, not by name.** The mapping-input schema
>   (`ContextAttributeMappingsInputRepresentation`) has `contextAttributeId` + `contextInputAttributeName`
>   only — there is **no** `contextAttribute`/`contextAttributeName` input field. So you must create the
>   attribute first (step 2), keep its returned `contextAttributeId`, and feed that id into the mapping.
>   Posting an attribute *name* is accepted but binds the mapping to nothing.
> - **`hydrationDetails` — object wrapper, not a bare array.** The OAS declares `hydrationDetails` as an
>   *array of hops* on the mapping input, but the runtime wants the **object-wrapper** form
>   `{"hydrationDetails":{"contextAttrHydrationDetails":[ <hop> ]}}` (schema
>   `ContextAttrHydrationDetailListInputRepresentation`). Posting the bare-array shape the OAS implies
>   fails — this, plus guessing the leaf shape, is what produced the two `INVALID_DEFINITION` errors when
>   this was first built.
> - **Hydration persists only on the create-list `POST`.** `PATCH` on an attribute-mapping **silently
>   drops** hydration (returns success, hydration gone). To *replace* wrong hydration, re-POST with
>   **`deleteExistingHydrationDetails: true`** (or DELETE the mapping and re-POST) — never PATCH it.
> - **`childDetails` on POST-input IS a `{contextAttrHydrationDetails:[…]}` wrapper (recursive), not a bare
>   array.** The wrapper repeats at every non-leaf level; leaf hops omit `childDetails`. (Read-back inverts
>   this: there `childDetails` is a plain array — do not copy the read shape into a POST.)
> - **Activation needs a default mapping (step 7).** A brand-new extension inherits every mapping with
>   `isDefault:false`; `PATCH {isActive:true}` on it fails `DATA_MAPPING_NOT_FOUND` until you flip one
>   (`CartEntitiesMapping`, mirroring the base) to `isDefault:true`.
> - **Delta attributes need context tags or pricing can't resolve them (step 6, before activation).** Creating the
>   attribute + mapping is not sufficient for a Pricing Procedure: the ExpressionSet resolves each
>   output variable's data type via the attribute's **context-tag name**. Base attributes inherit
>   their tags; the 5 skill-added deltas do **not** — you must POST a tag (`name` == attribute API
>   name) for each, or the PP compile fails `Specify a valid data type for the formula-section-0-output
>   variable`. This is invisible at the CD level (the definition activates fine) — it only surfaces
>   when a pricing procedure references the definition.
> - A write returning `isSuccess:true` / `true` is a call-succeeded flag, **not** proof of persisted
>   state — always read back (same verify-before-substitute discipline as Step 1).

> **Verified end-to-end on dev orgs (via `dispatch`, no `sf` CLI).** Built the extension as a
> `custom_nonexecutable` with `baseReference: ConsumerSalesContext__stdctx`; added the 5 delta attribute
> definitions; created all 16 mappings across Cart/Quote/Order/Asset; attached the hydration trees (two-hop
> + one-hop, each hop a recursive `childDetails:{contextAttrHydrationDetails:[…]}` wrapper); activated with
> `PATCH {isActive:true}`. Every mapped field, `sObjectDomain`, and hop tree matched the delta tables above.
> Activation required the default-mapping precondition (Step 6) — the base default is `CartEntitiesMapping`;
> without re-asserting `isDefault:true` on the Cart mapping the activate returns `DATA_MAPPING_NOT_FOUND`.
>
> **Hydration-tree count is org-dependent.** One verification org persisted **5/5** trees; another persisted
> **4/5** — on the latter the Quote 1-hop leaf `QuoteLineItem.Derived_Selling_Model_Type__c` was absent, so
> that single tree silently dropped (target-org field-presence, **not** a wire bug and **not** a steel-thread
> sequencing dependency — see Step 4 item 4). The other 15 mappings and 4 hydration trees are unaffected.
>
> Fully headless — every call is authenticated Connect REST, so it runs the same from a hosted agent
> (ChatGPT/Slackbot) as from Claude Code. Dev/scratch success is still not proof of prod-safety.
>
> **Tag step verified.** Created the 5 attribute-level context tags (`name` == attribute API name,
> bound by `contextAttributeId`) on the extension **before activating**, then activated — all via
> `dispatch`. Read-back (`GET /context-definitions/{id}/context-tags`) returns one tag per delta. The
> tags are what let a downstream Pricing Procedure resolve each delta's data type by its tag name;
> authoring/deploying that Pricing Procedure is the next steel thread's concern and is out of scope
> here.

---

## Verification & handoff

- **Headless-verifiable:** `get-comms-org-preferences` (Step 1) → `multiLocationEnabled:true`
  (Step 1b); `CMESales` present on the target profile/permission set (Step 2b, when applicable); the
  Context Service extension (Step 4) active with the 5 delta attribute definitions, all 16 mappings
  (Cart/Quote/Order/Asset), the 5 hydration trees (4 two-hop + 1 one-hop), and the 5 context tags
  (one per delta, `name` == attribute API name — Step 4 item 6, created before activation) present — `GET
  /context-definitions/{id}` → `isActive:true`, per-mapping read-backs match the delta tables in
  Step 4, and `GET /context-definitions/{id}/context-tags` returns a tag per delta.
- **Manual-only (⚠ gap):** Quote/Order pages modified; onboarding flow configured — confirmed
  visually, not via `dispatch`. Per Comms Cloud #2 there is no headless way to render a Go-style
  "setup complete / what's next" view; assemble the summary from raw introspection.
- **Handoff:** the MultiSite thread hands off to **Comms Cloud #3 — SMB Fiber Products** (catalog CSV
  import), which defines the products behind the display fields above.

## Notes

- This is the enablement layer of the second of three Comms Cloud steel threads:
  **initial setup → multisite (enable → this) → SMB fiber product setup.**
- **Use the approved SOR `RevenueCloudforCommunicationsSettings` friendly-route surface, NOT the
  native-REST `/setup/org/preferences/{name}` surface.** For this Industries Comms Sales pref the
  native-REST surface `404`s (both verbs) — it isn't on that registry — while `CorePricingPreference`
  200s on the same surface. The friendly `/headless/invoke/industries/industries-communications-sales/…`
  route resolves through the approved SOR's published route entry and works regardless of the client's
  knowledge of the backing controller. Apply **verify-before-substitute**: `get-comms-org-preferences`
  read first (a `403` is a licensing/permission gap; a `200` map means the gate passes), then write,
  then read back.
- **A `404` on `/setup/org/preferences/MultiLocationFeatureOrgPref` is NOT "disabled" and NOT a
  licensing gap** — it means the pref isn't on that generic REST surface. Diagnose enablement/gating
  via the SOR read (`403` = gate unmet) and the PermissionSetLicense query, never via that 404.
- Provisioned org permissions (`CMEMultiRecipient`, `MultiRecipient`) are **not** admin-toggleable —
  never author a headless "enable" step for them; verify + report the licensing gap instead.
- **Context Service extension (Step 4) is native Connect REST, not `/headless/invoke`.** Build the
  MultiSite recipient attributes as a `baseReference` extension of the org's standard
  `ConsumerSalesContext__stdctx` (add the 5 delta attributes + 16 mappings from the Step-4 tables — do
  not diff against a CMEB2B definition at run time; the deltas are already spelled out); activate via
  `PATCH /context-definitions/{id} {isActive:true}`. Two hard-won rules: hydration persists **only** on
  the create-list POST (`PATCH` silently drops it — use `deleteExistingHydrationDetails:true` to
  replace), and the nested hydration leaf key is `childDetails`. Attributes must exist here before Step 3
  can surface them on the page.
- **All calls in Steps 1–2 go through `dispatch` (no `sf` CLI).** A hosted agent (ChatGPT, Slackbot)
  has no shell, so a CLI step would no-op there. Dev/scratch success is not proof of prod-safety.

<!-- skill-validate: ignore-start -->
<!-- codey:operations start -->
## Operations Reference

Operations this skill uses — routing and dependency reference.

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `step1-get-comms-org-preferences` | read | — | `GET /headless/invoke/industries/industries-communications-sales/get-comms-org-preferences` | — |
| `step1-set-multi-location-enabled` | write | — | `PATCH /headless/invoke/industries/industries-communications-sales/set-multi-location-enabled` | `step1-get-comms-org-preferences` |
| `step1-verify-multi-location-enabled` | verify | — | `GET /headless/invoke/industries/industries-communications-sales/get-comms-org-preferences` | `step1-set-multi-location-enabled` |
| `step2-query-multirecipient-psl-status` | verify | — | `GET /services/data/v67.0/query` | — |
| `step2-query-cmemultirecipient-psl-assignment` | verify | — | `GET /services/data/v67.0/query` | — |
| `step2-find-cme-sales-permset` | read | — | `GET /services/data/v67.0/query` | `step2-query-cmemultirecipient-psl-assignment` |
| `step2-assign-cme-sales-permset` | write | — | `POST /services/data/v67.0/sobjects/PermissionSetAssignment` | `step2-find-cme-sales-permset` |
| `gap-cmemultirecipient-provisioning` | verify | — | — | — |
| `gap-quote-order-page-display-columns` | navigate | — | — | — |
| `step4-preflight-base-context-def` | precondition | — | `GET /services/data/v67.0/connect/context-definitions/ConsumerSalesContext__stdctx` | — |
| `step4-create-extension` | write | — | `POST /services/data/v67.0/connect/context-definitions` | `step4-preflight-base-context-def` |
| `step4-get-extension-with-dynamic-attrs` | read | — | `GET /services/data/v67.0/connect/context-definitions/{contextDefinitionId}` | `step4-create-extension` |
| `step4-add-delta-attributes` | write | — | `POST /services/data/v67.0/connect/context-nodes/{contextNodeId}/context-attributes` | `step4-get-extension-with-dynamic-attrs` |
| `step4-create-attribute-mappings` | write | — | `POST /services/data/v67.0/connect/context-node-mappings/{nodeMappingId}/context-attribute-mappings` | `step4-add-delta-attributes` |
| `step4-verify-attribute-mappings` | verify | — | `GET /services/data/v67.0/connect/context-node-mappings/{nodeMappingId}/context-attribute-mappings/{attrMappingId}` | `step4-create-attribute-mappings` |
| `step4-create-context-tags` | write | — | `POST /services/data/v67.0/connect/context-definitions/{contextDefinitionId}/context-tags` | `step4-verify-attribute-mappings` |
| `step4-set-default-cart-mapping` | write | — | `PATCH /services/data/v67.0/connect/context-definitions/{contextDefinitionId}/context-mappings` | `step4-create-context-tags` |
| `step4-activate-extension` | write | — | `PATCH /services/data/v67.0/connect/context-definitions/{contextDefinitionId}` | `step4-set-default-cart-mapping` |
<!-- codey:operations end -->
<!-- skill-validate: ignore-end -->
