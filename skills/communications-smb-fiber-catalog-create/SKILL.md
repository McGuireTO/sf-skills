---
name: communications-smb-fiber-catalog-create
description: "Load the Communications Cloud SMB Fiber sample product catalog into a Salesforce org that has completed comms-cloud-initial-setup. Trigger when users mention \"load the SMB Fiber sample catalog\", \"set up SMB Fiber products for a demo/POC\", or \"give me a populated Comms Cloud org to explore\". Lands ~163 sObjects (6 AttributePicklists + 19 AttributePicklistValues, 5 AttributeCategories, 8 AttributeDefinitions, 8 ProductClassifications + 8 ProductClassificationAttrs, 4 bundle Product2s + 8 simple Product2s, 28 ProductComponentGroups + 28 ProductRelatedComponents, 1 ProductCatalog + 1 ProductCategory + 4 ProductCategoryProducts, ~23 ProductSellingModelOptions, 12 PricebookEntries) via six `/composite/graph` POSTs. All DeveloperNames and codes are `CCC_*` prefixed. Preconditions: three Comms Cloud permsets on the caller, two ProductSellingModels named `Evergreen - Monthly` and `Broadband Subscription`, active Standard Price Book, and a Bundle→ClassificationComponent ProductRelationshipType."
metadata:
  version: "1.0"
---

# Communications Cloud — SMB Fiber Sample Catalog

Load the fixed SMB Fiber sample product catalog into a Salesforce org
that has completed `comms-cloud-initial-setup`. Fixed sample dataset:
product names, prices, and structure are baked in. Intended for demos,
POCs, and evaluation. The CSV fixtures ship with the skill and are
consumed as-is; editing them is not supported.

Single API: `/services/data/v67.0/composite/graph` (up to 500 sObjects
per graph, 15 graphs per request, per-graph atomic, back-refs via
`@{ref.id}`). Six graphs land the full catalog:

1. **Graph 1** — 6 AttributePicklists + 19 AttributePicklistValues.
2. **Graph 2** — 5 AttributeCategories + 8 AttributeDefinitions + 8
   ProductClassifications + 8 ProductClassificationAttrs.
3. **Graph 3** — 4 bundles + 4 PSMOs (`Evergreen - Monthly`) + 28 PCGs
   + 28 PRCs + 1 Catalog + 1 Category + 4 PCPs.
4. **Graph 4a** — 8 simples + 7 PSMOs (`Evergreen - Monthly`;
   Installation ships without a PSMO per the source inventory's
   "Sell only with Other Products" note).
5. **Graph 4b** — 12 bridge PSMOs (`Broadband Subscription`).
6. **Graph 4c** — 12 PricebookEntries against Standard Price Book.

Graph 4 is split because PricebookEntry validation checks
`(Product2Id, ProductSellingModelId)` against ProductSellingModelOption
at insert time, and a same-graph PSMO is not yet visible to that check
(`FIELD_INTEGRITY_EXCEPTION` otherwise).

One-shot. Blind re-run against an already-imported org returns
`DUPLICATE_VALUE` on Graph 1 and rolls back atomically — safe, no
partial writes. Runtime is under 60 seconds on a warm org.

Naming: the 4 bundle Product2 Names are `Fibre Broadband
Bronze/Silver/Gold/Platinum`; the 8 simple-product Names are `CPE
Router`, `CPE Router with WiFi`, `Static IP`, `Installation`, `Instant
Connect`, `Constant Connect`, `DDos Migration`, `Enhanced Security`
(verbatim from the source inventory, including the source's spelling
`DDos Migration`). Catalog Name/Code: `BroadBand Catalog` /
`CCC_CATALOG_BROADBAND`. Category Name/Code: `Fiber BroadBand` /
`CCC_CAT_FIBER`.

## Workflow

── Step 0 — target-org confirmation ──────────────────────────────────

0. Read `Organization` and surface identity to the customer before any
   write:
   `SELECT Id, Name, InstanceName, IsSandbox, OrganizationType FROM
    Organization LIMIT 1`.
   Emit:
   ```text
   About to load the SMB Fiber sample catalog into:
     Org: <Organization.Name> (<Organization.Id>)
     Instance: <Organization.InstanceName>
     Type: <Organization.OrganizationType> (IsSandbox=<true|false>)
   This will create ~163 sObjects prefixed CCC_*. Confirm to proceed.
   ```
   Do NOT proceed without explicit customer confirmation.

── Steps 1–4 — precondition probes ────────────────────────────────────

1. **Probe `/composite/graph` reachability.**
   `GET /services/data/v67.0/composite/graph` → 405 when reachable.
   A 404 means Composite API is disabled; halt with
   `PRECONDITION_VIOLATION`.

2. **Verify Comms Cloud permsets on the caller.** Flat SOQL against
   `PermissionSetAssignment`:
   ```text
   SELECT PermissionSet.Name FROM PermissionSetAssignment
    WHERE AssigneeId = <caller-user-id>
      AND PermissionSet.Name IN
        ('CMESalesStandardPermissionSet',
         'CommsCloudSalesFeatures',
         'SimpleCsvDataImport')
   ```
   Resolve `AssigneeId` from the session context — do NOT probe
   `/services/oauth2/userinfo` (unrouted on some MCP transports).
   Expect 3 rows. Halt with `PRECONDITION_VIOLATION` listing the
   missing permsets by human-readable label:
   ```text
   Your user is missing:
     - "Communications Cloud Sales — Standard" (CMESalesStandardPermissionSet)
     - "Communications Cloud Sales Features"   (CommsCloudSalesFeatures)
     - "Simple CSV Data Import"                (SimpleCsvDataImport)
   Run comms-cloud-initial-setup first (it handles license + permset
   assignment), then re-invoke this skill.
   ```

3. **Resolve or create every PSM name declared in the CSVs.** Build
   the union of non-blank `PsmName` on `bundles.csv` +
   `simple-products.csv` + every `PricingSellingModelName` on
   `pricebook-entries.csv`. For the shipped templates the set is
   `{"Evergreen - Monthly", "Broadband Subscription"}`. One SOQL:
   ```text
   SELECT Id, Name, Status FROM ProductSellingModel
    WHERE Name IN :required_psm_names
   ```
   For every required name NOT returned Active, POST it via
   `/sobjects/ProductSellingModel` with a **per-name** create body — each
   PSM needs a distinct `(SellingModelType, PricingTerm, PricingTermUnit)`
   triple (the org enforces uniqueness on that triple):
   ```text
   "Evergreen - Monthly":
     {"Name":"Evergreen - Monthly","SellingModelType":"Evergreen",
      "Status":"Active","PricingTerm":1,"PricingTermUnit":"Months"}
   "Broadband Subscription":
     {"Name":"Broadband Subscription","SellingModelType":"TermDefined",
      "Status":"Active","PricingTerm":1,"PricingTermUnit":"Months"}
   ```
   `PricingTerm` + `PricingTermUnit` are REQUIRED at create time
   (`INVALID_INPUT` otherwise; term must be `1` when the unit is
   `Months`). If a row exists but `Status != 'Active'`, PATCH it to
   Active. Build `psm_id_by_name` from the merged set of pre-existing +
   freshly-created Ids. Blank `PsmName` on `simple-products.csv` means
   "no PSMO for this product" (Installation per the source inventory) —
   not an error.

3.5. **Resolve the Bundle→ClassificationComponent ProductRelationshipType.**
   ```text
   SELECT Id FROM ProductRelationshipType
    WHERE MainProductRoleCat='Bundle'
      AND AssociatedProductRoleCat='ClassificationComponent'
    LIMIT 1
   ```
   Seeded by RC. Save the Id for PRC emission in Graph 3. Halt if
   absent.

4. **Resolve and activate Standard Price Book.**
   `SELECT Id, IsActive FROM Pricebook2 WHERE IsStandard=true LIMIT 1`.
   Save `standard_pricebook_id`. If `IsActive=false`, PATCH:
   `PATCH /services/data/v67.0/sobjects/Pricebook2/<id> {"IsActive": true}`.
   No customer prompt — the skill's job is to leave the org demo-ready.

── Steps 6.1–6.5d — the six graph writes ──────────────────────────────

6.1. **Graph 1 — Picklists + Values.** Inputs: `picklists.csv` +
   `picklist-values.csv`.
   - 6 AttributePicklist: `{Name, DataType, Status: "Active"}`.
     `DataType` = `Text` for all six.
     `picklists.csv:DeveloperName` is a fixture-level correlation key,
     NOT a Salesforce field — not emitted.
   - 19 AttributePicklistValue: `{Name, PicklistId: @{apl.id}, Code,
     Value, Sequence, Status: "Active"}`. `Code` is the unique key
     (`CCC_PKLVAL_*`, `CCC_PVLVAL_*`, or `CCC_PKVAL_*` per source
     inventory typos, copied verbatim).
   Total 25 sObjects.

6.3. **Graph 2 — Categories + Definitions + Classifications + PCAs.**
   Inputs: `attribute-categories.csv` + `attributes.csv` +
   `classifications.csv`.
   - 5 AttributeCategory: `{Name, Code, Description}`.
   - 8 AttributeDefinition: `{Name, Label, DeveloperName, DataType,
     IsActive, Code, Description, DefaultHelpText, [PicklistId]}`.
     Picklist-typed rows resolve `PicklistId` to raw Ids from Graph 1's
     response (cross-graph, not `@{ref.id}`).
   - 8 ProductClassification: `{Name, Code, Status: "Active"}`.
   - 8 ProductClassificationAttr: `{Name, ProductClassificationId,
     AttributeDefinitionId, AttributeCategoryId, Status: "Active"}`.
     `Name` synthesized as `<classification> - <attribute>` (required).
     `AttributeCategoryId` resolved from
     `attributes.csv:AttributeCategoryName`. Sourced by expanding each
     non-blank `classifications.csv:AttributeDeveloperNames` cell (a
     `;`-separated list of `CCC_ATT_*`/`CCC_CPE_*` codes) into one PCA
     per code.
   Total 29 sObjects.

6.5a. **Graph 3 — Bundles + Groups + Components + Catalog.** Inputs:
   `bundles.csv` + `component-groups.csv` + `component-wiring.csv` +
   `catalog.csv` + `categories.csv`.
   - 4 Product2 (bundles): `{Name, ProductCode, Family, Type: "Bundle",
     ConfigureDuringSale: "Allowed", IsActive: true, IsAssetizable: true,
     Description, BasedOnId: <PC.id for row.ClassificationDeveloperName
     from Graph 2 state>}`.
   - 4 ProductSellingModelOption: `{Product2Id: @{bundle.id},
     ProductSellingModelId: psm_id_by_name["Evergreen - Monthly"]}`.
   - 28 ProductComponentGroup: `{Name, Code, ParentProductId:
     @{bundle.id}, Sequence, MinBundleComponents, MaxBundleComponents}`.
     CPE groups Min=1/Max=1; every other group Min=0/Max=1.
   - 28 ProductRelatedComponent: `{ParentProductId: @{bundle.id},
     ProductRelationshipTypeId: <PRT Id from Step 3.5>,
     ProductComponentGroupId: @{pcg.id},
     ChildProductClassificationId: <PC.id from Graph 2 state>,
     Quantity: 1, Sequence: <row.Sequence>}`.
   - 1 ProductCatalog: `{Name, Code, Description}`.
   - 1 ProductCategory: `{Name, Code, Description, CatalogId:
     @{catalog.id}}`.
   - 4 ProductCategoryProduct: `{ProductCategoryId: @{category.id},
     ProductId: @{bundle.id}}` — one per bundle code in
     `categories.csv:BundleProductCodes` (`;`-separated).
   Total 70 sObjects.

6.5b. **Graph 4a — Simple Products + PSMOs.** Inputs: `simple-products.csv`.
   - 8 Product2 (simples): `{Name, ProductCode, Family, Description,
     IsActive: true, IsAssetizable}`. `Type` omitted (nullable).
     `ConfigureDuringSale` omitted (simples are PRC children, not
     parents). No classification FK — classification is wired via the
     bundle's PRC path.
   - 7 ProductSellingModelOption: `{Product2Id: @{simple.id},
     ProductSellingModelId: psm_id_by_name["Evergreen - Monthly"]}`.
     Installation (blank `PsmName`) emits Product2 but no PSMO.
   Total 15 sObjects.

6.5c. **Graph 4b — Broadband Subscription bridge PSMOs.**
   12 ProductSellingModelOption: `{Product2Id: <Product2.Id for
   pbe-row.ProductCode from Graph 3+4a state>, ProductSellingModelId:
   psm_id_by_name["Broadband Subscription"]}`. One per PBE product
   (4 bundles + 8 simples). Required because PricebookEntry validation
   checks `(Product2Id, ProductSellingModelId)` against
   ProductSellingModelOption at insert time.

6.5d. **Graph 4c — PricebookEntries.** Inputs: `pricebook-entries.csv`.
   12 PricebookEntry: `{Pricebook2Id: standard_pricebook_id, Product2Id:
   <Product2.Id for row.ProductCode>, UnitPrice, IsActive,
   ProductSellingModelId: psm_id_by_name[row.PricingSellingModelName],
   UseStandardPrice: false}`. All 12 rows name `Broadband Subscription`.
   `CurrencyIsoCode` omitted on single-currency orgs (rejected as
   `INVALID_FIELD` otherwise); re-add on multi-currency orgs.

── Step 7 — report ────────────────────────────────────────────────────

7. On success, emit:
   ```text
   SMB Fiber sample catalog loaded into <Organization.Name>.
   - 4 bundles (Fibre Broadband Bronze/Silver/Gold/Platinum) at
     $30/$40/$50/$60.
   - 8 simple products (CPE Router, CPE Router with WiFi, Static IP,
     Installation, Instant Connect, Constant Connect, DDos Migration,
     Enhanced Security) at published unit prices.
   - 28 component groups + 28 classification-child relationships.
   - Per-PSM PSMO breakdown (Evergreen - Monthly: 11,
     Broadband Subscription: 12).
   - 12 PricebookEntries against Standard Price Book.
   - 1 catalog + 1 category with 4 bundles under the category.
   - 6 attribute picklists + 19 values, 8 attribute definitions,
     5 categories, 8 classifications, 8 classification-attr wirings.
   ```

   On any graph failure, extract the first real error:
   1. Iterate `graphResponse.compositeResponse[]` in order.
   2. Skip entries with `errorCode == "PROCESSING_HALTED"` (cascade
      rollback noise from per-graph atomicity).
   3. First non-halted entry is the root cause.

   Report:
   ```text
   Graph <N> failed and rolled back atomically. Your org is unchanged.
   First error:
     referenceId: <referenceId>
     sObject:     <parsed-from-url>
     errorCode:   <errorCode>
     message:     <message>
     fields:      <fields>
   ```
   Do NOT retry automatically — per-graph rollback leaves the org
   consistent.

## Dispatch contract — `/services/data/v67.0/composite/graph`

Every write step (6.1, 6.3, 6.5a, 6.5b, 6.5c, 6.5d) goes through this
single endpoint.

Body shape:
```json
{
  "graphs": [
    {
      "graphId": "smb-fiber-g1",
      "compositeRequest": [
        {
          "method": "POST",
          "url": "/services/data/v67.0/sobjects/AttributePicklist",
          "referenceId": "apl_upload",
          "body": {"Name": "Upload Speed Picklist",
                   "DataType": "Text",
                   "Status": "Active"}
        },
        {
          "method": "POST",
          "url": "/services/data/v67.0/sobjects/AttributePicklistValue",
          "referenceId": "apv_up40",
          "body": {"Name": "Upload Speed 40",
                   "PicklistId": "@{apl_upload.id}",
                   "Code": "CCC_PKLVAL_UPLOAD_SPEED_40",
                   "Value": "40",
                   "Sequence": 10,
                   "Status": "Active"}
        }
      ]
    }
  ]
}
```

- Up to 500 sObjects per graph, 15 graphs per request. Full SMB Fiber
  payload (25 + 29 + 70 + 15 + 12 + 12 = 163 sObjects) fits well under
  both caps.
- Per-graph atomicity: any sub-request failure rolls back the entire
  graph; sibling graphs commit independently.
- Back-refs use `@{referenceId.id}` (lowercase `id`), same graph only.
  Cross-graph FKs resolve via captured Ids from prior graphs' responses.
- `graphId` must be <40 chars and start with an alphanumeric character.

## Why not the Connect API alternatives

- `/connect/pcm/actions/catalog-update` is pilot-gated and returns
  `FUNCTIONALITY_NOT_ENABLED` on standard sandboxes.
- `importCatalogProducts` (RevCloud) is not registered under
  `/actions/standard` on standard sandboxes in v67.0.

Everything routes through `/composite/graph` — a single API with broad
availability.

## Critical constraints (wire truth)

- **AttributePicklist**: no `DeveloperName`, no `MasterLabel`.
  Uniqueness by `Name`. `DataType` accepts `Boolean|Date|Datetime|
  Number|Text|Currency|Percent` (NOT `Picklist`).
- **AttributePicklistValue**: unique key is `Code`. Writable fields:
  `Name, PicklistId, Code, Value, Sequence, Status`. `DisplayValue`
  and `Abbreviation` from the source inventory are not sObject fields.
- **AttributeCategory**: writable fields are `Name, Code, Description`
  only. `Sequence/Status/IsActive/EffectiveStartDate/EffectiveEndDate`
  all rejected.
- **AttributeDefinition**: help-text field is `DefaultHelpText` (not
  `HelpText`). No `DisplaySequence`, no `AttributeCategoryId` — AD↔AC
  linkage runs through PCA. `Name` uniqueness-enforced. `DataType`
  accepts `Checkbox|Date|Datetime|Number|Text|Currency|Percent|Picklist`
  (NOT `Boolean`).
- **ProductClassification**: writable fields are `Name, Code, Status,
  ParentProductClassificationId` only. `Description` rejected.
- **ProductClassificationAttr**: `Name` is REQUIRED. No `DeveloperName`.
  Uniqueness by `(ProductClassificationId, AttributeDefinitionId)`.
- **Product2**: `Type` picklist has only `Bundle` active (simples omit
  `Type`). No `IsConfigurable`, no `CanUseRevenueSchedule`, no
  `ProductSellingModelId` — PSM linkage runs through
  `ProductSellingModelOption`. Bundles with classification-child PRCs
  MUST carry `ConfigureDuringSale="Allowed"`.
- **ProductRelatedComponent** with `ChildProductClassificationId`:
  `ProductRelationshipTypeId` REQUIRED; `ProductComponentGroupId`
  REQUIRED and at most ONE classification per PCG;
  `IsComponentRequired` must be false; `IsDefaultComponent` must be
  omitted; `ParentSellingModelId` and `ChildSellingModelId` must be
  omitted. Required-vs-optional is expressed on the PCG via
  `MinBundleComponents`/`MaxBundleComponents`, NOT on the PRC.
- **ProductComponentGroup**: no `IsActive` field.
- **ProductCatalog**: no `IsActive`, no `CatalogCode`. Natural key is
  `Code`.
- **ProductCategory**: no `IsActive`.
- **ProductCategoryProduct**: no `IsPrimaryCategory`. Emits `{ProductCategoryId,
  ProductId}` only.
- **ProductSellingModel**: uniqueness is enforced on the
  `(SellingModelType, PricingTerm, PricingTermUnit)` triple, not on
  `Name`. The two catalog PSMs are kept distinct by `SellingModelType`
  (`Evergreen - Monthly` = `Evergreen`, `Broadband Subscription` =
  `TermDefined`).
- **PricebookEntry**: `ProductSellingModelId` must be a PSM Id
  (`0jP...`), never a PSMO Id (`0iO...`). The matching PSMO for
  `(Product2Id, ProductSellingModelId)` must exist in a PRIOR graph —
  same-graph PSMO is not visible to PBE validation
  (`FIELD_INTEGRITY_EXCEPTION` otherwise). This is why Graph 4 is split
  into 4a → 4b → 4c. `CurrencyIsoCode` rejected on single-currency
  orgs.
- **Composite Graph DELETE**: does not support dependency ordering.
  Any teardown must be per-Id DELETEs on
  `/sobjects/{sobject}/{id}`.

## Fixtures

Templates at `assets/templates/`. Every row maps 1:1 to a source
inventory tab (Picklists / Picklist Values / Attributes / Attribute
Categories / Product Classification / Products / Product Groups /
Catalog / Pricebooks). See `assets/README.md` for column semantics.

| File | Rows | Feeds |
|---|---|---|
| `picklists.csv` | 6 | Graph 1 — AttributePicklist |
| `picklist-values.csv` | 19 | Graph 1 — AttributePicklistValue |
| `attribute-categories.csv` | 5 | Graph 2 — AttributeCategory |
| `attributes.csv` | 8 | Graph 2 — AttributeDefinition |
| `classifications.csv` | 8 | Graph 2 — ProductClassification + PCA |
| `bundles.csv` | 4 | Graph 3 — bundle Product2 + PSMO |
| `simple-products.csv` | 8 | Graph 4a — simple Product2 + PSMO |
| `component-groups.csv` | 28 | Graph 3 — ProductComponentGroup |
| `component-wiring.csv` | 28 | Graph 3 — ProductRelatedComponent |
| `catalog.csv` | 1 | Graph 3 — ProductCatalog |
| `categories.csv` | 1 | Graph 3 — ProductCategory + PCP |
| `pricebook-entries.csv` | 12 | Graph 4b + Graph 4c |

## Operations reference

| Step | Verb + Path | Op | Kind |
|------|---|---|---|
| 0    | `GET /services/data/v67.0/query` | Organization identity confirmation | probe |
| 1    | `GET /services/data/v67.0/composite/graph` | reachability | probe |
| 2    | `GET /services/data/v67.0/query` | PermissionSetAssignment lookup | read |
| 3    | `GET /services/data/v67.0/query` + `POST /sobjects/ProductSellingModel` (per missing PSM) | PSM lookup + auto-create missing | read+write |
| 3.5  | `GET /services/data/v67.0/query` | Bundle→ClassificationComponent PRT lookup | read |
| 4    | `GET /services/data/v67.0/query` + `PATCH /sobjects/Pricebook2/<id>` (if inactive) | Standard Pricebook lookup + auto-activate | read+write |
| 6.1  | `POST /services/data/v67.0/composite/graph` | Graph 1 | write |
| 6.3  | `POST /services/data/v67.0/composite/graph` | Graph 2 | write |
| 6.5a | `POST /services/data/v67.0/composite/graph` | Graph 3 | write |
| 6.5b | `POST /services/data/v67.0/composite/graph` | Graph 4a | write |
| 6.5c | `POST /services/data/v67.0/composite/graph` | Graph 4b | write |
| 6.5d | `POST /services/data/v67.0/composite/graph` | Graph 4c | write |
| 7    | (no HTTP) | assemble report | inline |
