---
name: automotive-cloud-sales-concierge-search-grounding-configure
description: "Ground the Automotive Sales Concierge agent's search infrastructure — clone DPE definitions, configure Criteria-Based Search & Filter (CBSF), and activate the search pages. This is \"Act 2\" of the Automotive Sales Concierge steel thread, running after Act 1 (Create & Activate the Agent). Act 2 is a THIN DELEGATOR that owns only the domain-specific DATA (which DPE templates, which searchable objects, which fields) and delegates ALL mechanics to three reusable skills: (1) mfg-spartans/dpe-clone-activate for DPE clone+activate, (2) mfg-knights/CriteriaBasedSearchAndFilter for CBSF config authoring, (3) mfg-knights/activate-flexipage-via-action-override for CBSF page placement. TRIGGER when the user wants to \"ground the automotive agent's search\", \"set up CBSF for the sales concierge\", \"clone and activate the Automotive Sales Concierge DPEs and configure search\", or otherwise asks to stand up the search infrastructure the agent depends on. DO NOT TRIGGER when the user wants to enable org preferences or assign permission sets (Act 0), create or activate the agent (Act 1), or create business data."
metadata:
  version: "1.0"
---

# Ground the Agent's Search Infrastructure (Act 2)

Stand up the complete **search grounding** the **Automotive Sales Concierge** agent needs — DPE
definitions cloned + activated, CBSF search configurations authored + activated, and CBSF pages
deployed on the searchable objects — directly in a live org, **headlessly and API-first**.

This is **Act 2 — "Ground the Agent's Data Pipelines"** of the Automotive Sales Concierge steel
thread. It runs **after Act 1** (Create & Activate the Agent) in the orchestrator's fixed run order.

**Act 2 is a thin delegator, by design.** It owns the domain-specific DATA for the Sales Concierge
(which DPE templates, which searchable objects, which fields to index/display, which app to place
pages in) and delegates ALL mechanics to three reusable skills. It performs **no** clone, **no**
activation, **no** FLS deploy, **no** user creation, **no** CBSF config authoring, and **no**
FlexiPage deployment itself.

---

## The three delegates (fixed execution order)

| # | Delegate skill | What it does | Act 2's data input |
|---|---|---|---|
| 1 | `mfg-spartans/dpe-clone-activate` | Clone + activate DPE definitions; create Integration User; deploy FLS | DPE template names (`dpeTemplates` in constants.json) |
| 2 | `mfg-knights/CriteriaBasedSearchAndFilter` | Enable CBSF pref + PSL/permset; create SearchCriteriaConfiguration + mappings + SearchableObjDataSyncInfo; activate config | Per-object field mappings, config shape, DPE clone ID (`cbsfConfigs` in constants.json) |
| 3 | `mfg-knights/activate-flexipage-via-action-override` | Deploy RecordPage FlexiPage with CBSF component; activate via app-scoped actionOverride | sobjectType, flexiPageDevName, searchConfigs, appDeveloperName (`cbsfConfigs` + `flexipageConfig` in constants.json) |

**Data flows between delegates:**
- Delegate 1 produces `BatchCalcJobDefinition` Ids (9N1) per template → Act 2 links each to the
  matching `cbsfConfig` entry via `dpeTemplateLink` → passed as `DataSyncJobId` to Delegate 2.
- Delegate 2 produces `SearchCriteriaConfiguration.DeveloperName` per object → passed as
  `searchConfigs` design attribute to Delegate 3.

---

## What Act 2 owns vs. what it delegates

| Concern | Owner | Act 2's role |
|---|---|---|
| **Which** DPE templates + **which** searchable objects + **which** fields | **Act 2** (`constants.json`) | Owns the data; assembles working-sets |
| DPE clone, activation, FLS, Integration User | `mfg-spartans/dpe-clone-activate` | Delegates; never re-implements |
| CBSF pref enable, PSL/permset assign, config authoring, mappings, sync-info, config activation | `mfg-knights/CriteriaBasedSearchAndFilter` | Delegates; never re-implements |
| FlexiPage deploy + app-scoped actionOverride activation | `mfg-knights/activate-flexipage-via-action-override` | Delegates; never re-implements |
| Data Pipelines PSLs + DPE org preferences | **Act 0** | Never enables here; flags gaps for Act 0 |

> **The "NOT ours" rules for Act 2 — non-negotiable:**
> 1. **Never touch the Analytics Cloud Integration User** — the DPE delegate creates it.
> 2. **Never contain FLS logic** — the DPE delegate's job.
> 3. **Never enable PSLs or org preferences** — Act 0's job (CBSF PSL/permset are owned by the
>    CBSF delegate, not Act 0 — but Act 2 still never assigns them directly).
> 4. **Never author CBSF config inline** — the CBSF delegate owns all config mechanics.
> 5. **Never deploy FlexiPages inline** — the flexipage delegate owns deploy + activation.

---

## Prerequisites (NOT satisfied by Act 2)

1. **Act 0 + Act 1 completed** (positional dependency via the orchestrator).
2. **Data Pipelines PSLs + DPE feature licensed** — established by Act 0.
3. **Analytics Cloud Integration User** — created by the DPE delegate (fully in its scope).
4. **DPE templates exist on the org** — shipped by the Automotive Cloud package.
5. **CBSF PSL available on the org** — the CBSF delegate checks and assigns it; if the org lacks
   the license entirely, Act 2 flags it as an Act 0 gap.

---

## Required Inputs

From the orchestrator's shared runtime context:
- **`<apiVersion>`** — the org's max API version.
- **`<userId>`** — the authenticated admin user (receives CBSF PSL/permset).

All domain data (templates, objects, fields, app name) lives in [`constants.json`](constants.json).

---

## Workflow — delegate in sequence, relay between delegates

### Step 1. Confirm shared runtime (inherited)

Use `<apiVersion>` / `<userId>` from the orchestrator. If invoked standalone, resolve via
`GET /services/data/` and identity endpoint.

### Step 1.5. MANDATORY HARD GATE — Person Account enablement (user action required)

> **⚠️ THIS IS A MANDATORY HARD GATE — CANNOT BE SKIPPED, CANNOT BE BYPASSED.**
> Execution MUST NOT continue past this point if Person Accounts are not enabled.
> Do NOT offer to skip. Do NOT attempt DPE delegation without this check passing.
> Do NOT proceed under any circumstance until the check passes or the user explicitly confirms enablement.
> DPE clone WILL FAIL on Person Account-backed records without this.

Before delegating to the DPE skill, verify whether **Person Accounts** are enabled in the org.
Person Accounts are a prerequisite for the Automotive Sales Concierge DPE definitions (they index
Person Account-backed records).

**Check:** `GET /services/data/v<apiVersion>/sobjects/Account/describe` — in the `fields` array,
look for a field with `"name": "IsPersonAccount"` (primary indicator). If `IsPersonAccount` is
present, Person Accounts are enabled. Secondary confirmation: `PersonContactId` field presence.
Do NOT rely on `isPersonType` — it is not a valid field name.

**If Person Accounts are NOT enabled:**
- **HALT IMMEDIATELY** with a clear message:
  > "Person Accounts must be enabled in this org before DPE definitions can be cloned and activated.
  > Please enable Person Accounts in Setup → Account Settings → check 'Enable Person Accounts'
  > (this requires reading and accepting Terms & Conditions and cannot be done via API).
  > Confirm here once done to resume."
- **STOP HERE. Do not proceed. Do not offer to skip. Do not attempt any DPE delegation.**
- **Wait** for the user to explicitly confirm they have enabled Person Accounts.
- **Resume** only after user confirmation.

**If Person Accounts ARE already enabled:** proceed directly to Step 2.

### Step 2. Delegate DPE clone + activate

Assemble the DPE working-set from `constants.json.dpeTemplates` and invoke
`mfg-spartans/dpe-clone-activate`. Follow that skill's contract exactly.

**Input to delegate:** (template names from `constants.json.dpeTemplates` — include the managed-package namespace prefix)
```jsonc
[
  { "templateName": "industries_automotive__UpdateDealerProductSearchableFieldForAutomotive", "cloneName": "Clone_UpdateDealerProductSearchableFieldForAutomotive", "verified": false },
  { "templateName": "industries_automotive__UpdateDealerVehicleDefinitionSearchableField", "cloneName": "Clone_UpdateDealerVehicleDefinitionSearchableField", "verified": false },
  { "templateName": "industries_automotive__UpdateVehicledefinitionSearchableField", "cloneName": "Clone_UpdateVehicledefinitionSearchableField", "verified": false }
]
```

**On success:** capture the `BatchCalcJobDefinition` Id (9N1) per template. Map each to its
`feedsCbsfObject` via `dpeTemplateLink` in `cbsfConfigs`.

**On halt:** relay verbatim and STOP. Do not proceed to CBSF config.

**On timeout / transient failure:** If the DPE delegate reports a timeout (e.g., Tooling API GET
or POST timeout, blob fetch timeout, or any transient HTTP 5xx / socket timeout), **retry the
entire DPE delegation up to 5 times** with the same inputs. Only HALT after 5 consecutive
failures. Log each retry attempt number.

### Step 3. Delegate CBSF configuration (per searchable object)

**Do not author CBSF config families inline.** Enabling the CBSF preference + PSL and creating
the `SearchableObjDataSyncInfo`, `SearchCriteriaConfiguration`, and mappings (search-field
mappings, result-column mappings, sync registration, activation flip) is a shared, domain-agnostic
mechanism owned by the canonical CBSF skill. That skill is generic — it hardcodes **no** searchable
object, columns, or action, and it owns CBSF licensing/preference enablement itself (so it is NOT
assigned in prior steps). Delegate to it rather than re-implementing the Metadata/Tooling/REST
calls here.

For each entry in `constants.json.cbsfConfigs`, invoke `mfg-knights/CriteriaBasedSearchAndFilter`.
The entries are structured to match the delegate's input contract directly — pass them as-is.

**Per-object defaults (from `constants.json.cbsfConfigs`):**

```yaml
# --- VehDefSearchableField ---
searchableObject: VehDefSearchableField
filterColumns:                         # search-by fields
  - BodyType                           # TEXT — vehicle body style
  - DoorCount                          # NUMBER — door count
  - FuelSource                         # TEXT — fuel type
  - ListPrice                          # CURRENCY — MSRP
  - MakeName                           # TEXT — manufacturer brand
  - ModelName                          # TEXT — model name
  - ModelYear                          # TEXT — model year
  - ProductId                          # REFERENCE — linked Product2
  - TopSpeed                           # NUMBER — max speed
  - VehicleDefinitionName              # TEXT — definition display name
  - VehicleDefinitionId                # REFERENCE — definition record
  - TrimType                           # TEXT — trim level
  - TransmissionSystem                 # TEXT — transmission type
outputColumns:                         # result projection
  - BodyType
  - DoorCount
  - FuelSource
  - Id
  - MakeName
  - ModelName
  - ModelYear
  - Name
  - ProductId
  - TransmissionSystem
  - TopSpeed
  - TrimType
  - VariantName
  - VehicleDefinitionId
  - VehicleDefinitionName
criteriaConfigShape:
  DeveloperName: VehicleDefSearch
  MasterLabel: Vehicle Definition Search

# --- DealerProdtSearchableField ---
searchableObject: DealerProdtSearchableField
filterColumns:                         # search-by fields
  - BusinessBrandName                  # TEXT — brand name
  - DealerName                         # TEXT — dealer name
  - DealerPhone                        # PHONE — dealer phone
  - Industry                           # TEXT — industry segment
  - MakeName                           # TEXT — manufacturer brand
  - ManufacturerName                   # TEXT — manufacturer
  - ManufacturerPartNumber             # TEXT — part number
  - ModelName                          # TEXT — model name
  - ModelYear                          # TEXT — model year
  - ProductCategoryCode                # TEXT — category code
  - ProductCode                        # TEXT — product code
  - ProductFamily                      # TEXT — product family
  - ProductId                          # REFERENCE — linked Product2
  - ProductName                        # TEXT — product display name
  - RegionName                         # TEXT — region
  - ServiceTerritoryName               # TEXT — territory name
  - TrimType                           # TEXT — trim level
  - UniversalProductCode               # TEXT — UPC
  - DealerAccountId                    # REFERENCE — dealer Account
  - SellerProductId                    # REFERENCE — seller product
outputColumns:                         # result projection
  - ProductName
  - ServiceTerritoryName
  - DealerLocation
  - DealerName
  - DealerAccountId
  - MakeName
  - ManufacturerName
  - ModelName
  - ModelYear
  - ProductFamily
  - ProductId
  - ServiceTerritoryId
  - TrimType
  - SellerProductId
criteriaConfigShape:
  DeveloperName: DealerSearchForProduct
  MasterLabel: Dealer Search For Product

# --- DealerVehDefSearchableField ---
searchableObject: DealerVehDefSearchableField
filterColumns:                         # search-by fields
  - MakeName                           # TEXT — manufacturer brand
  - ModelName                          # TEXT — model name
  - SellerRole                         # TEXT — seller role
  - ServiceTerritoryName               # TEXT — territory name
  - ServiceTerritoryId                 # REFERENCE — territory record
  - TestDriveVehicleDefinition         # TEXT — test-drive eligible
  - VehicleServiceType                 # TEXT — service type
  - ProductName                        # TEXT — product display name
  - ProductId                          # REFERENCE — linked Product2
outputColumns:                         # result projection
  - DealerLocation
  - DealerName
  - Name
  - ServiceTerritoryId
  - ServiceTerritoryName
  - TestDriveVehicleDefinition
  - VehicleDefinitionId
criteriaConfigShape:
  DeveloperName: DealerSearch
  MasterLabel: Dealer Search
distanceCriteria:                      # geo-proximity (only this object)
  options: ["20"]
  unit: miles
  referenceFieldApiName: ServiceTerritoryAddress
  mapEnabled: false
  sortByDistance: false
```

**Inputs passed to the delegate (per searchable object):**

```yaml
# --- REQUIRED ---
searchableObject: <cbsfConfigs[].searchableObject>           # passed ONCE; the CBSF delegate threads
                                                             #   it into config.SearchableObject + each save-* call
filterColumns: <cbsfConfigs[].filterColumns>                  # STRING LIST → SelectedSearchFields
outputColumns: <cbsfConfigs[].outputColumns>                  # STRING LIST → SelectedResultColumns
criteriaConfigShape: <cbsfConfigs[].criteriaConfigShape>      # DeveloperName + MasterLabel only.
                                                             #   Do NOT pass FilterType or ResultDisplayFormat —
                                                             #   both optional + controller-derived.
DataSyncJobId: <9N1 Id from Step 2, matched via dpeTemplateLink>
dataSyncInfo: <cbsfConfigs[].dataSyncInfo>                    # developerName + masterLabel for
                                                             #   SearchableObjDataSyncInfo registration
# --- OPTIONAL ---
distanceCriteria: <cbsfConfigs[].distanceCriteria if present>
```

**On success per object:** capture the `SearchCriteriaConfiguration.DeveloperName` (same as
`criteriaConfigShape.DeveloperName` — used as `searchConfigs` in Step 4).

**On halt:** relay verbatim and STOP.

### Step 4. Delegate FlexiPage deploy + activation (per searchable object)

For each entry in `constants.json.cbsfConfigs`, invoke
`mfg-knights/activate-flexipage-via-action-override` with:

| Field | Source |
|---|---|
| `sobjectType` | `cbsfConfigs[].searchableObject` |
| `flexiPageDevName` | `cbsfConfigs[].flexiPageDevName` |
| `searchConfigs` | `cbsfConfigs[].criteriaConfigShape.DeveloperName` (from Step 3 output) |
| `appDeveloperName` | `flexipageConfig.appDeveloperName` = `Automotive` |

The delegate deploys a RecordPage FlexiPage hosting the CBSF component
(`industries_common:criteriaBasedSearchAndFilter`) and activates it as the View page for that
object inside the Automotive app (app-scoped actionOverride).

**On success:** capture FlexiPage Id + activation confirmation.

**On halt:** relay verbatim and STOP.

### Step 5. Relay consolidated verdict

Report the consolidated end state:
- Per DPE template: cloneName, 9N1 Id, active status
- Per searchable object: SearchCriteriaConfiguration created + activated, FlexiPage deployed + activated
- Any gaps flagged for Act 0

---

## Output Expectations

Report, in order:
1. **DPE results** — per-template: resolved cloneName, 9N1 Id, 0ma Id, active status.
2. **CBSF config results** — per-object: SearchCriteriaConfiguration DeveloperName, activated status,
   SearchableObjDataSyncInfo registered.
3. **FlexiPage results** — per-object: FlexiPage DeveloperName, deployed, activated in Automotive app.
4. **Gaps flagged** — any missing PSL/org-pref surfaced by any delegate, with Act 0 recommendation.
5. **Consolidated state** — all 3 DPEs active + all 3 CBSF configs active + all 3 pages deployed?
6. **Next step** — if complete, hand back to orchestrator. If halted, exact action needed.

---

## Rules / Constraints

| Constraint | Rationale |
|---|---|
| Delegate, don't duplicate | All mechanics live in the three delegate skills. Act 2 sequences and relays. |
| Never touch the Analytics Cloud Integration User | DPE delegate creates it. Act 2 never checks or creates. |
| No FLS logic in Act 2 | DPE delegate's job. |
| Never enable PSLs / org preferences directly | CBSF PSL is the CBSF delegate's. Data Pipelines PSLs are Act 0's. Act 2 never assigns. |
| Never author CBSF config inline | CBSF delegate owns all save-*/activate-* mechanics. |
| Never deploy FlexiPages inline | Flexipage delegate owns Tooling POST + actionOverride PATCH. |
| Generic verdict relay | Propagate every outcome with message + action. No special-casing. |
| `dispatch` only (enforced by delegates) | No `sf` CLI, no browser. Hosted-MCP customers have no shell. |
| No hardcoded org IDs, tokens, or API version | Portable across orgs. |
| Sequential delegation with data threading | DPE → CBSF → FlexiPage. Each step's output feeds the next. Halt on any failure. |

---

## Cross-Skill Integration

| Need | Belongs to |
|---|---|
| Clone + activate DPE definitions | `mfg-spartans/dpe-clone-activate` (delegate 1) |
| CBSF config: prefs, PSL, search configs, mappings, sync-info | `mfg-knights/CriteriaBasedSearchAndFilter` (delegate 2) |
| CBSF FlexiPage deploy + app-scoped activation | `mfg-knights/activate-flexipage-via-action-override` (delegate 3) |
| Enable org preferences + assign Data Pipelines PSLs | Act 0 — `enable-automotive-sales-concierge-foundation` |
| Create or activate the agent | Act 1 — `create-automotive-sales-concierge-agent` |
| Create the Analytics Cloud Integration User | `mfg-spartans/dpe-clone-activate` (delegate 1 — fully in its scope) |
