---
name: automotive-cloud-mfg-agent-data-pipelines-configure
description: "Ground the Industries Sales Concierge agent's search infrastructure — clone the DPE definition, configure Criteria-Based Search & Filter (CBSF), and activate the search page. This is \"Act 2\" of the Industries Sales Concierge steel thread, running after Act 1 (Create & Activate the Agent). Act 2 is a THIN DELEGATOR that owns only the domain-specific DATA (which DPE template, which searchable object, which fields) and delegates ALL mechanics to three reusable skills: (1) mfg-spartans/dpe-clone-activate for DPE clone+activate, (2) mfg-knights/CriteriaBasedSearchAndFilter for CBSF config authoring, (3) mfg-knights/activate-flexipage-via-action-override for CBSF page placement. TRIGGER when the user wants to \"ground the industries sales concierge agent's search\", \"set up CBSF for the industries sales concierge\", \"clone and activate the Industries Sales Concierge DPE and configure search\", or otherwise asks to stand up the search infrastructure the agent depends on. DO NOT TRIGGER when the user wants to enable org preferences or assign permission sets (Act 0), create or activate the agent (Act 1), or create business data."
metadata:
  version: "1.0"
---

# Ground the Agent's Search Infrastructure (Act 2)

Stand up the complete **search grounding** the **Industries Sales Concierge** agent needs — a DPE
definition cloned + activated, a CBSF search configuration authored + activated, and a CBSF page
deployed on the searchable object — directly in a live org, **headlessly and API-first**.

This is **Act 2 — "Ground the Agent's Data Pipelines"** of the Industries Sales Concierge steel
thread. It runs **after Act 1** (Create & Activate the Agent) in the orchestrator's fixed run order.

**Act 2 is a thin delegator, by design.** It owns the domain-specific DATA for the Sales Concierge
(which DPE template, which searchable object, which fields to index/display, which app to place the
page in) and delegates ALL mechanics to three reusable skills. It performs **no** clone, **no**
activation, **no** FLS deploy, **no** user creation, **no** CBSF config authoring, and **no**
FlexiPage deployment itself.

---

## The three delegates (fixed execution order)

| # | Delegate skill | What it does | Act 2's data input |
|---|---|---|---|
| 1 | `mfg-spartans/dpe-clone-activate` | Clone + activate the DPE definition; create Integration User; deploy FLS | DPE template name (`dpeTemplates` in constants.json) |
| 2 | `mfg-knights/CriteriaBasedSearchAndFilter` | Enable CBSF pref + PSL/permset; create SearchCriteriaConfiguration + mappings + SearchableObjDataSyncInfo; activate config | Object field mappings, config shape, DPE clone ID (`cbsfConfigs` in constants.json) |
| 3 | `mfg-knights/activate-flexipage-via-action-override` | Deploy RecordPage FlexiPage with CBSF component; activate via app-scoped actionOverride | sobjectType, flexiPageDevName, searchConfigs, appDeveloperName (`cbsfConfigs` + `flexipageConfig` in constants.json) |

**Data flows between delegates:**
- Delegate 1 produces a `BatchCalcJobDefinition` Id (9N1) for the template → Act 2 links it to the
  matching `cbsfConfig` entry via `dpeTemplateLink` → passed as `DataSyncJobId` to Delegate 2.
- Delegate 2 produces `SearchCriteriaConfiguration.DeveloperName` for the object → passed as
  `searchConfigs` design attribute to Delegate 3.

---

## What Act 2 owns vs. what it delegates

| Concern | Owner | Act 2's role |
|---|---|---|
| **Which** DPE template + **which** searchable object + **which** fields | **Act 2** (`constants.json`) | Owns the data; assembles the working-set |
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
4. **DPE template exists on the org** — shipped by the Manufacturing Cloud package.
5. **CBSF PSL available on the org** — the CBSF delegate checks and assigns it; if the org lacks
   the license entirely, Act 2 flags it as an Act 0 gap.

---

## Required Inputs

From the orchestrator's shared runtime context:
- **`<apiVersion>`** — the org's max API version.
- **`<userId>`** — the authenticated admin user (receives CBSF PSL/permset).

All domain data (template, object, fields, app name) lives in [`constants.json`](constants.json).

---

## Workflow — delegate in sequence, relay between delegates

### Step 1. Confirm shared runtime (inherited)

Use `<apiVersion>` / `<userId>` from the orchestrator. If invoked standalone, resolve via
`GET /services/data/` and identity endpoint.

### Step 2. Delegate DPE clone + activate

Assemble the DPE working-set from `constants.json.dpeTemplates` and invoke
`mfg-spartans/dpe-clone-activate`. Follow that skill's contract exactly.

**Input to delegate:** (template name from `constants.json.dpeTemplates` — include the managed-package namespace prefix)
```jsonc
[
  { "templateName": "industries_manufacturing__UpdateDealerProdtSearchableFieldValues", "cloneName": "Clone_UpdateDealerProdtSearchableFieldValuesForMfgSca", "verified": false }
]
```

**On success:** capture the `BatchCalcJobDefinition` Id (9N1) for the template. Map it to its
`feedsCbsfObject` via `dpeTemplateLink` in `cbsfConfigs`.

**On halt:** relay verbatim and STOP. Do not proceed to CBSF config.

**On timeout / transient failure:** If the DPE delegate reports a timeout (e.g., Tooling API GET
or POST timeout, blob fetch timeout, or any transient HTTP 5xx / socket timeout), **retry the
entire DPE delegation up to 5 times** with the same inputs. Only HALT after 5 consecutive
failures. Log each retry attempt number.

### Step 3. Delegate CBSF configuration (for the searchable object)

**Do not author CBSF config families inline.** Enabling the CBSF preference + PSL and creating
the `SearchableObjDataSyncInfo`, `SearchCriteriaConfiguration`, and mappings (search-field
mappings, result-column mappings, sync registration, activation flip) is a shared, domain-agnostic
mechanism owned by the canonical CBSF skill. That skill is generic — it hardcodes **no** searchable
object, columns, or action, and it owns CBSF licensing/preference enablement itself (so it is NOT
assigned in prior steps). Delegate to it rather than re-implementing the Metadata/Tooling/REST
calls here.

For the single entry in `constants.json.cbsfConfigs`, invoke `mfg-knights/CriteriaBasedSearchAndFilter`.
The entry is structured to match the delegate's input contract directly — pass it as-is.

**Object defaults (from `constants.json.cbsfConfigs`):**

```yaml
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
  - SellerProductId
criteriaConfigShape:
  DeveloperName: DealerSearchForProduct
  MasterLabel: Dealer Search For Product
```

**Inputs passed to the delegate (for the searchable object):**

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

**On success:** capture the `SearchCriteriaConfiguration.DeveloperName` (same as
`criteriaConfigShape.DeveloperName` — used as `searchConfigs` in Step 4).

**On halt:** relay verbatim and STOP.

### Step 4. Delegate FlexiPage deploy + activation (for the searchable object)

For the single entry in `constants.json.cbsfConfigs`, invoke
`mfg-knights/activate-flexipage-via-action-override` with:

| Field | Source |
|---|---|
| `sobjectType` | `cbsfConfigs[].searchableObject` |
| `flexiPageDevName` | `cbsfConfigs[].flexiPageDevName` |
| `searchConfigs` | `cbsfConfigs[].criteriaConfigShape.DeveloperName` (from Step 3 output) |
| `appDeveloperName` | `flexipageConfig.appDeveloperName` = `Manufacturing` |

The delegate deploys a RecordPage FlexiPage hosting the CBSF component
(`industries_common:criteriaBasedSearchAndFilter`) and activates it as the View page for that
object inside the Manufacturing app (app-scoped actionOverride).

**On success:** capture FlexiPage Id + activation confirmation.

**On halt:** relay verbatim and STOP.

### Step 5. Relay consolidated verdict

Report the consolidated end state:
- For the DPE template: cloneName, 9N1 Id, active status
- For the searchable object: SearchCriteriaConfiguration created + activated, FlexiPage deployed + activated
- Any gaps flagged for Act 0

---

## Output Expectations

Report, in order:
1. **DPE results** — for the template: resolved cloneName, 9N1 Id, 0ma Id, active status.
2. **CBSF config results** — for the object: SearchCriteriaConfiguration DeveloperName, activated status,
   SearchableObjDataSyncInfo registered.
3. **FlexiPage results** — for the object: FlexiPage DeveloperName, deployed, activated in Manufacturing app.
4. **Gaps flagged** — any missing PSL/org-pref surfaced by any delegate, with Act 0 recommendation.
5. **Consolidated state** — 1 DPE active + 1 CBSF config active + 1 page deployed?
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
| Clone + activate the DPE definition | `mfg-spartans/dpe-clone-activate` (delegate 1) |
| CBSF config: prefs, PSL, search configs, mappings, sync-info | `mfg-knights/CriteriaBasedSearchAndFilter` (delegate 2) |
| CBSF FlexiPage deploy + app-scoped activation | `mfg-knights/activate-flexipage-via-action-override` (delegate 3) |
| Enable org preferences + assign Data Pipelines PSLs | Act 0 — `enable-mfg-sales-concierge-foundation` |
| Create or activate the agent | Act 1 — `create-mfg-sales-concierge-agent` |
| Create the Analytics Cloud Integration User | `mfg-spartans/dpe-clone-activate` (delegate 1 — fully in its scope) |
