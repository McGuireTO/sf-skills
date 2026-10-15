---
name: communications-initial-setup-configure
description: "Perform the initial setup for Communications Cloud on a Salesforce org that already has Revenue Cloud base setup in place. Trigger when users mention \"set up Communications Cloud\", \"Comms Cloud initial setup\", \"provision Comms Cloud for a new org\", \"assign Comms Cloud permission sets\", \"deploy the Comms Product Discovery context definition\", or \"create the Comms discovery pricing procedure\". Assumes Communications Cloud add-on licenses are provisioned. Runs step-by-step against small-payload Connect APIs. Three outcomes: (1) assigns the three required permission sets on a target user; (2) builds `customcommsproductdiscovery` by extending `CommsProductDiscoveryContext__stdctx` via POST `/connect/context-definitions`, applies the small hardcoded delta through POST `/connect/context-node-mappings/{id}/context-attribute-mappings`, promotes a default mapping, then activates with PATCH `{isActive: true}`; (3) authors the `Comms_Product_Discovery_Pricing_Procedure` ExpressionSetDefinition (bound to the CD from outcome 2) in a single POST to `/connect/business-rules/expression-set` carrying the full V1 version body — 2 steps (`ListPrice`, `PricingSetting`) plus 1 Constant variable — since the Connect API accepts inline `versions[].steps[].customElement.parameters` on the create call and PATCH of that version content is not supported."
metadata:
  version: "1.0"
---

# Communications Cloud — Initial Setup

## When to Use This Skill

Perform the initial setup for Communications Cloud on a Salesforce org that
already has Revenue Cloud base/initial setup complete and the Communications
Cloud add-on licenses provisioned. Three outcomes, all dispatched through
`/services/data/v67.0/*` REST — no multipart, no CLI shell-out:

1. Assign (or confirm) the three Comms Cloud sales permission sets on the
   target user: `CMESalesStandardPermissionSet` (label "CME Sales Features"),
   `CommsCloudSalesFeatures` (label "Revenue Cloud for Communications
   Features"), and `SimpleCsvDataImport` (label "Basic CSV Data Import"). The
   assignments are idempotent — every write is preceded by a "check what's
   already assigned" SOQL and only missing rows are created.

2. Build `customcommsproductdiscovery` — an ACTIVE extension of
   `CommsProductDiscoveryContext__stdctx` — through a fixed script of Connect
   API calls. Extend via POST `/connect/context-definitions`, apply the one
   hardcoded delta below (3 new attribute-mappings on shared base-inherited
   mappings, hydrating `Account.id` from `Account.Id`; 0 new attributes, 0
   new context-mappings, 0 new node-mappings, 0 new tags, 0 new nodes), then
   flip `isActive=true` after PATCHing one mapping to `isDefault=true`. Each
   POST is a JSON body under a few KB.

3. Author `Comms_Product_Discovery_Pricing_Procedure` — a
   `usageType=DefaultPricing`, `interfaceSourceType=PricingProcedure`
   ExpressionSetDefinition bound to `customcommsproductdiscovery` — in a
   SINGLE `POST /connect/business-rules/expression-set` carrying the full V1
   version content inline (`versions[0].steps[]` + `versions[0].variables[]`)
   with `versions[0].enabled=true` so V1 is ACTIVE on the 201 response. The
   body ships 2 hardcoded steps in this order: `PricingSetting`
   (`sequenceNumber=1`, `actionType=PricingSettings`) then `ListPrice`
   (`sequenceNumber=2`, `actionType=ListPrice`), plus 1 Constant variable
   (`Constant_UnitPrice_Price_Book_Entry_Decision_Table_v2_LP`). Each step's
   parameter list is fully specified in Step 8 below. Payload is a few KB.

Naming: "Communications Cloud" (or "Comms Cloud" for short). The three
permission-set Names above are the identifiers to write; the human labels are
for operator-facing messages only. `customcommsproductdiscovery` is the
developer name AND the label — they match on this extension. On the Connect
API input rep the label field is `name`, and the parent-CD pointer is
`baseReference`; the metadata-flavored `masterLabel` /
`inheritedFromDeveloperName` names do NOT apply here.

**Out of scope for this version:** promotions
(`promotionMappingwithcustom` mapping and any promotion-only attributes such
as `SalesTransaction.Channel__c`), channel attributes
(`Account.channelFinal__c`), the `ConsumerSalesExtended266` CD, the
Location-Based Pricing surface, and Rate Management enablement. Rank
promotion or multi-version selection for the pricing procedure is also out
of scope — the recipe writes exactly one active V1 (`rank=1`,
`enabled=true`). If the user asks for any of those, say so explicitly.

## Workflow

Eight steps against a single org. Steps 1–5 are plain sObject/REST (SOQL +
PermissionSetAssignment writes). Steps 6–7 build and verify the
`customcommsproductdiscovery` CD via the Connect API extend-then-augment
loop. Step 8 authors the `Comms_Product_Discovery_Pricing_Procedure`
ExpressionSetDefinition against that CD in one shot on the BRE Connect API.
All writes route through native `/services/data/v67.0/*` endpoints.

── Steps 1–5 — permission-set assignment (idempotent) ─────────────────────

`sor_input: target_user_id` — 18-char User Id who should receive the
permission sets. When omitted, the skill resolves the running (authenticated)
user's Id and assigns to them. Either `dispatch_readonly` on
`GET /services/data/v67.0/` (returns the identity URL for the current user)
or `SELECT Id FROM User WHERE Username='<running username>'` is an acceptable
resolver.

1. **Resolve the three Comms permission set Names to Ids** —
   `SELECT Id, Name FROM PermissionSet WHERE Name IN ('CMESalesStandardPermissionSet','CommsCloudSalesFeatures','SimpleCsvDataImport')`.
   Any Name that does NOT resolve means the backing add-on license isn't
   provisioned on this org — record it as a **partial-success gap** and
   continue with the ones that do resolve.

2. **Resolve the assignee** — either the caller-supplied `target_user_id` or
   the running user's Id.

3. **Check existing assignments (idempotency gate)** —
   `SELECT PermissionSetId, PermissionSet.Name FROM PermissionSetAssignment WHERE AssigneeId = <assignee_id> AND PermissionSet.Name IN (…the same three…)`.
   The to-assign list for Step 4 is `(Step 1 Ids) − (Step 3 Ids already assigned)`.

4. **Assign the missing permission sets** —
   `POST /services/data/v67.0/sobjects/PermissionSetAssignment` with body
   `{"AssigneeId": "<assignee_id>", "PermissionSetId": "<perm_set_id>"}`. One
   call per missing permission set.

5. **Verify** — re-run the Step 3 SOQL and confirm every Name that resolved
   in Step 1 appears in the assignee's rows.

── Steps 6–7 — build `customcommsproductdiscovery` via Connect APIs ──────

The delta from base `CommsProductDiscoveryContext__stdctx` to the target
extension `customcommsproductdiscovery` is baked into Step 6e below — the
skill does NOT re-diff at runtime. Step 6 is a fixed sequence: extend →
resolve draft Ids from the extend response → apply the one hardcoded delta →
activate. The target shape is exactly:

- **0 new context-attributes**
- **0 new context-tags**
- **0 new top-level mappings**
- **3 new attribute-mappings on shared base-inherited mappings** (all on
  their `Account` node-mapping, all `id` hydrated from `Account.Id`, on
  `QuoteProductDiscoveryMapping`, `OrderProductDiscoveryMapping`, and
  `ProductDiscoveryMapping`)
- **0 new context-nodes**

Idempotency: Step 6b (skip-if-present) short-circuits when the extension
already exists and is active. If it exists inactive with some deltas already
applied, running Step 6e will re-POST each hardcoded delta; each POST
endpoint returns 400 on duplicate name / Id — treat 400 with a "duplicate"
or "already exists" body as a no-op signal and continue.

6. **Build `customcommsproductdiscovery` (extend + augment).**

   6a. **Discover base CD id.** `GET /services/data/v67.0/connect/context-definitions`
       and read out the record for
       `developerName=CommsProductDiscoveryContext__stdctx`. Capture
       `contextDefinitionId` — for a stock CD this is the developer name
       itself (`CommsProductDiscoveryContext__stdctx`), NOT an `11ODX…`
       key-prefix id. The `11ODX…` shape applies only to custom / extension
       CDs (Step 6c's response and Step 6b when the extension already exists).

   6b. **Skip-if-present gate.** `GET /services/data/v67.0/connect/context-definitions`
       filtered by `developerName=customcommsproductdiscovery`. If it already
       exists and `isActive=true`, jump to Step 7 (idempotent short-circuit).
       Otherwise, if it exists inactive, capture its id and skip the extend
       in 6c — proceed directly to 6d.

   6c. **Extend the base CD.** `POST /services/data/v67.0/connect/context-definitions`
       with body
       ```json
       {
         "developerName": "customcommsproductdiscovery",
         "name": "customcommsproductdiscovery",
         "baseReference": "CommsProductDiscoveryContext__stdctx"
       }
       ```
       Response echoes the new `contextDefinitionId` (`11ODX…`) and
       `activeVersionId` (`11pDX…`) for the draft. The draft is inactive by
       default — do NOT send `isActive`. The input rep field is
       `baseReference` (not `inheritedFromDeveloperName`), and the label
       field is `name` (not `masterLabel`); sending
       `masterLabel` / `inheritedFromDeveloperName` / `isActive` returns
       `Unrecognized field` 400s from the input rep on v67.

   6d. **Fetch the draft to resolve org-specific Ids.**
       `GET /services/data/v67.0/connect/context-definitions/{draftId}` —
       returns the full nested tree under
       `contextDefinitionVersionList[0]`. The draft's `contextNodes[]` and
       `contextMappings[]` are copied from the base, so before posting the
       hardcoded delta below resolve these org-specific Ids from the draft
       response:
       - Base attribute Id on the draft's `Account` node needed by the
         shared-mapping loop:
           - `id` on the draft's `Account` node → attribute Id (`11nDX…`).
         (Look this up by `name` on `contextNodes[*].attributes[*]`.)
       - The three shared-mapping node-mapping Ids (`11bDX…`) on the draft —
         needed to POST the shared-mapping attribute-mappings:
           - `QuoteProductDiscoveryMapping / Account` node-mapping Id
           - `OrderProductDiscoveryMapping / Account` node-mapping Id
           - `ProductDiscoveryMapping / Account` node-mapping Id
         (Walk `contextMappings[*].contextNodeMappings[*]`, filter by mapping
         `name` + node-mapping `contextNodeName=Account`, read out
         `contextNodeMappingId`.)

   6e. **Apply the one hardcoded delta** — 3 attribute-mapping POSTs under
       the shared base-inherited mappings' `Account` node-mappings. Every
       Connect POST endpoint takes a LIST-wrapper input rep. Halt the whole
       step on any 4xx that is not a "duplicate" / "already exists" body.

       **6e-i. Create the 3 shared-mapping attribute-mappings on the
       `Account` node-mapping of each shared base-inherited mapping.**

       Parents are the draft's `Account` node-mapping Ids under
       `QuoteProductDiscoveryMapping` / `OrderProductDiscoveryMapping` /
       `ProductDiscoveryMapping` (resolved in 6d). The attribute Id is the
       draft's `Account.id` (base attribute — every org has it).

       **`ProductDiscoveryMapping / Account`** — 1 attribute-mapping:
       ```json
       { "contextAttributeMappings": [{"contextAttributeId": "<Account.id.attrId>", "contextInputAttributeName": "id", "hydrationDetails": {"contextAttrContextHydrationDetails": [], "contextAttrHydrationDetails": [{"queryAttribute": "Id", "sObjectDomain": "Account"}]}}], "deleteExistingHydrationDetails": false }
       ```

       **`QuoteProductDiscoveryMapping / Account`** — 1 attribute-mapping:
       ```json
       { "contextAttributeMappings": [{"contextAttributeId": "<Account.id.attrId>", "contextInputAttributeName": "id", "hydrationDetails": {"contextAttrContextHydrationDetails": [], "contextAttrHydrationDetails": [{"queryAttribute": "Id", "sObjectDomain": "Account"}]}}], "deleteExistingHydrationDetails": false }
       ```

       **`OrderProductDiscoveryMapping / Account`** — 1 attribute-mapping:
       ```json
       { "contextAttributeMappings": [{"contextAttributeId": "<Account.id.attrId>", "contextInputAttributeName": "id", "hydrationDetails": {"contextAttrContextHydrationDetails": [], "contextAttrHydrationDetails": [{"queryAttribute": "Id", "sObjectDomain": "Account"}]}}], "deleteExistingHydrationDetails": false }
       ```

       All three `id` attribute-mappings hydrate from `Account.Id`, which
       every org has.

   6f. **Ensure a default mapping exists, then activate.** Activation enforces
       a hard gate — a version with zero mappings flagged `isDefault=true`
       returns `DATA_MAPPING_NOT_FOUND: Cannot activate a definition without
       default mapping` on the PATCH below. The Connect extend copies the
       base's mappings but does NOT preserve the base version's `isDefault`
       flag — every mapping on the draft comes back `isDefault=false`.

       6f-i. **Promote one mapping to default** — for
       `customcommsproductdiscovery` the default mapping is
       `QuoteProductDiscoveryMapping`. Resolve its `contextMappingId` on the
       draft. Then
       `PATCH /services/data/v67.0/connect/context-definitions/{draftId}/context-mappings`
       with body
       `{"contextMappings": [{"contextMappingId": "<11jDX…>", "isDefault": true}]}`.
       Skip 6f-i if the draft already has a mapping with `isDefault=true`.

       6f-ii. **Activate** —
       `PATCH /services/data/v67.0/connect/context-definitions/{draftId}`
       with `{"isActive": true}`. Expect 200 with `isActive=true` in the
       response body.

7. **Verify `customcommsproductdiscovery`** —
   `GET /services/data/v67.0/connect/context-definitions/{draftId}`. Confirm
   `isActive=true`, `definition=customcommsproductdiscovery`,
   `baseReference=CommsProductDiscoveryContext__stdctx`. Spot-check the
   target shape: 4 top-level mappings (the base-inherited set —
   `ProductDiscoveryPromoMapping`, `ProductDiscoveryMapping`,
   `QuoteProductDiscoveryMapping`, `OrderProductDiscoveryMapping` — with
   `QuoteProductDiscoveryMapping.isDefault=true`); no new context-attributes
   on any node; the three shared mappings (`QuoteProductDiscoveryMapping`,
   `OrderProductDiscoveryMapping`, `ProductDiscoveryMapping`) each have an
   extra `Account`-scoped `id` attribute-mapping hydrated from `Account.Id`.
   No `promotionMappingwithcustom` mapping should be present. No
   `channelFinal__c` attribute or attribute-mapping should be present.

── Step 8 — author `Comms_Product_Discovery_Pricing_Procedure` ────────────────

Author the discovery-flow pricing procedure as a Business Rules Engine
ExpressionSetDefinition bound to `customcommsproductdiscovery` from Step 6.
Both the shell AND the full V1 version content (steps + variables +
customElement parameters) go in a SINGLE
`POST /connect/business-rules/expression-set` — the Connect API's
`postExpressionSetCreate` accepts nested `versions[]` on create. PATCH of
version content on this API is not supported (returns `INTERNAL_ERROR`), so
the create is the only successful write path.

8. **Author `Comms_Product_Discovery_Pricing_Procedure`.**

   8a. **Skip-if-present gate.**
       `GET /services/data/v67.0/query?q=SELECT+Id,DeveloperName,MasterLabel+FROM+ExpressionSetDefinition+WHERE+DeveloperName='Comms_Product_Discovery_Pricing_Procedure'`.
       (The Connect collection `/connect/business-rules/expression-set` is
       `POST`-only — a `GET` returns `405 METHOD_NOT_ALLOWED`, so the
       skip-if-present gate goes through SOQL.) If `totalSize=1`, capture
       `records[0].Id` (`9QLDX…`) and skip 8b–8c — the procedure already
       exists. Skip-if-present treats an existing record as terminal
       regardless of its `enabled` state; do NOT attempt to reactivate an
       existing procedure from this step. If `totalSize=0`, proceed.

   8b. **Resolve the bound CD id.** From the Step 7 GET body, capture the
       `contextDefinitionId` (`11ODX…`) for `customcommsproductdiscovery` —
       needed for the `contextDefinitions[]` entry in the POST below. Both
       `id` and `name` are required on the array element; supplying just
       one returns `INVALID_INPUT: Specify a value for name parameter`.

   8c. **POST the full V1 body — active on create.**
       `POST /services/data/v67.0/connect/business-rules/expression-set`
       with the body below. `usageType=DefaultPricing` implies
       `usageSubtype=RevenueCloud` server-side (do NOT send `usageSubtype`;
       the server sets it). `interfaceSourceType=PricingProcedure` classifies
       the ESD as a pricing procedure on the runtime index. The two steps'
       `sequenceNumber` values fix execution order: `PricingSetting=1`,
       `ListPrice=2`. `versions[0].enabled` is `true` so V1 is active on
       the 201 response — a single POST, no follow-up activation call.

       ```json
       {
         "name": "Comms Product Discovery Pricing Procedure",
         "apiName": "Comms_Product_Discovery_Pricing_Procedure",
         "usageType": "DefaultPricing",
         "interfaceSourceType": "PricingProcedure",
         "contextDefinitions": [
           {"id": "<customcommsproductdiscovery.contextDefinitionId>", "name": "customcommsproductdiscovery"}
         ],
         "versions": [{
           "apiName": "Comms_Product_Discovery_Pricing_Procedure_V1",
           "name": "Comms Product Discovery Pricing Procedure V1",
           "decimalScale": 2,
           "enabled": true,
           "rank": 1,
           "showExplExternally": false,
           "versionNumber": 1,
           "variables": [{
             "name": "Constant_UnitPrice_Price_Book_Entry_Decision_Table_v2_LP",
             "description": "Constant_UnitPrice_Price_Book_Entry_Decision_Table_v2_LP",
             "type": "Constant",
             "dataType": "Text",
             "collection": false,
             "decimalPlaces": 2,
             "input": false,
             "output": false,
             "value": "UnitPrice"
           }],
           "steps": [
             {
               "name": "PricingSetting",
               "description": "Pricing Setting",
               "stepType": "BusinessKnowledgeModel",
               "actionType": "PricingSettings",
               "sequenceNumber": 1,
               "resultIncluded": false,
               "shouldExposeExecPathMsgOnly": true,
               "shouldExposeConditionDetails": false,
               "shouldShowExplExternally": false,
               "customElement": {
                 "parameters": [
                   {"name": "LineItemId",           "type": "Parameter", "value": "PricingId",       "input": true,  "output": false},
                   {"name": "IsDerived",            "type": "Parameter", "value": "IsDerived",       "input": true,  "output": false},
                   {"name": "sectionCount",         "type": "Literal",   "value": "0",               "input": true,  "output": false},
                   {"name": "Subtotal",             "type": "Parameter", "value": "SubTotal",        "input": false, "output": true},
                   {"name": "selectedFunction",     "type": "Literal",   "value": "Get",             "input": true,  "output": false},
                   {"name": "IsRealTime",           "type": "Literal",   "value": "false",           "input": true,  "output": false},
                   {"name": "IsPropagationEnabled", "type": "Literal",   "value": "false",           "input": true,  "output": false},
                   {"name": "PriceWaterfall",       "type": "Parameter", "value": "price_water_fall","input": false, "output": true},
                   {"name": "NetUnitPrice",         "type": "Parameter", "value": "NetUnitPrice",    "input": false, "output": true}
                 ]
               }
             },
             {
               "name": "ListPrice",
               "description": "List Price",
               "stepType": "BusinessKnowledgeModel",
               "actionType": "ListPrice",
               "sequenceNumber": 2,
               "resultIncluded": false,
               "shouldExposeExecPathMsgOnly": true,
               "shouldExposeConditionDetails": false,
               "shouldShowExplExternally": false,
               "customElement": {
                 "parameters": [
                   {"name": "ListPriceField",            "type": "Parameter", "value": "Constant_UnitPrice_Price_Book_Entry_Decision_Table_v2_LP", "input": true,  "output": false},
                   {"name": "LookUpName",                "type": "Literal",   "value": "Price Book Entries V2",              "input": true,  "output": false},
                   {"name": "LookUpId",                  "type": "Literal",   "value": "0lDDX00000000WW2AY",                 "input": true,  "output": false},
                   {"name": "Product2Id",                "type": "Parameter", "value": "PricingProductId",                   "input": true,  "output": false},
                   {"name": "Pricebook2Id",              "type": "Parameter", "value": "PricebookId",                        "input": true,  "output": false},
                   {"name": "ProductSellingModelId",     "type": "Parameter", "value": "ProductSellingModelId",              "input": true,  "output": false},
                   {"name": "Quantity",                  "type": "Parameter", "value": "ProductQuantity",                    "input": true,  "output": false},
                   {"name": "LookUpApiName",             "type": "Literal",   "value": "Price_Book_Entry_Decision_Table_v2", "input": true,  "output": false},
                   {"name": "IsContractEnabled",         "type": "Literal",   "value": "false",                              "input": true,  "output": false},
                   {"name": "HideWaterfall",             "type": "Literal",   "value": "false",                              "input": true,  "output": false},
                   {"name": "IsOutputResolutionEnabled", "type": "Literal",   "value": "false",                              "input": true,  "output": false},
                   {"name": "sectionCount",              "type": "Literal",   "value": "0",                                  "input": true,  "output": false},
                   {"name": "selectedFunction",          "type": "Literal",   "value": "Get",                                "input": true,  "output": false},
                   {"name": "IsRealTime",                "type": "Literal",   "value": "false",                              "input": true,  "output": false},
                   {"name": "Id",                        "type": "Parameter", "value": "PriceBookEntryId",                   "input": false, "output": true},
                   {"name": "IsDerived",                 "type": "Parameter", "value": "IsDerived",                          "input": false, "output": true},
                   {"name": "ListPrice",                 "type": "Parameter", "value": "UnitPrice",                          "input": false, "output": true},
                   {"name": "Subtotal",                  "type": "Parameter", "value": "SubTotal",                           "input": false, "output": true}
                 ]
               }
             }
           ]
         }]
       }
       ```

       Expect 201 with `id` (`9QLDX…`), `versions[0].id` (`9QMDX…`),
       `versions[0].steps` echoing both steps, `versions[0].variables`
       echoing the single Constant, `contextDefinitions[0]` echoing the
       bound CD. The server auto-remaps the `LookUpId` literal value to
       whatever `Id` the target `Price_Book_Entry_Decision_Table_v2`
       decision table holds on THIS org — the literal `0lDDX00000000WW2AY`
       posted in the body is the source-org id from the reference
       procedure; the server's response body carries the org-local id.
       Both are `0lDDX…` prefix. Do NOT try to preserve the source id.

   8d. **Verify.** `GET /services/data/v67.0/connect/business-rules/expression-set/{id}`
       (using the id from 8c's 201 response). Confirm:
       - `apiName=Comms_Product_Discovery_Pricing_Procedure`
       - `usageType=DefaultPricing`, `usageSubtype=RevenueCloud`,
         `interfaceSourceType=PricingProcedure`
       - `contextDefinitions[0].name=customcommsproductdiscovery`
       - `versions` length 1, `versions[0].versionNumber=1`,
         `versions[0].enabled=true` (active on create)
       - `versions[0].steps` length 2 with a `PricingSetting`
         (`sequenceNumber=1`, `actionType=PricingSettings`) and a
         `ListPrice` (`sequenceNumber=2`, `actionType=ListPrice`)
       - `versions[0].variables` length 1 with
         `name=Constant_UnitPrice_Price_Book_Entry_Decision_Table_v2_LP`,
         `type=Constant`, `dataType=Text`, `value=UnitPrice`

## Critical Constraints

- **Idempotency at Step 3.** Do NOT rely on caller-side "have I run this
  before?" flags. The three permission-set writes MUST be preceded by the
  Step 3 SOQL every run; assigning an already-assigned permission set errors
  with `DUPLICATE_VALUE`.

- **Steps 1–5 and Steps 6–7 are independent.** If Context Service isn't
  enabled or the base CD is missing, Step 6 fails while Steps 1–5 succeed.
  Report Step 6 as a **gap** and keep the Steps 1–5 result. Do NOT abort the
  whole run on a Step 6 failure.

- **Do NOT try to POST a full active-extension CD in one Connect call.** A
  single POST to `/connect/context-definitions` carrying `developerName`,
  `isActive=true`, and the entire mapping bundle in one body returns
  `DATA_MAPPING_NOT_FOUND`. The working shape is the Step 6 sequence:
  extend inactive → resolve draft Ids → augment via the granular child
  endpoints → PATCH `isDefault=true` on one mapping → PATCH `isActive=true`.

- **Do NOT try to POST the whole CD xmlRep to `/headless/metadata`.** The
  extension CD xmlRep is large (~178 KB) and prone to request-size / gateway
  errors on that transport. The Connect-API extend-then-augment loop is the
  supported path.

- **Diff by name, never by Id.** Every `contextNodeId`, `contextMappingId`,
  `contextNodeMappingId`, `contextAttributeId`, and `contextTagId` is
  org-specific (`11o…`, `11j…`, `11b…`, `11n…`, `11T…`). Match records
  across base and draft by `name` / `developerName` and walk `childNodes`
  recursively; use Ids only to address the correct parent when POSTing a
  delta.

- **Verify by developer name.** Step 7 filters
  `GET /connect/context-definitions` by `developerName`. A generated record
  Id (`11ODX…`, custom CDs only) is not stable across orgs; developer name
  is.

- **`CommsProductDiscoveryContext__stdctx` must exist on the org before
  Step 6.** It ships with Revenue Cloud Comms. If absent, the Step-6c
  extend call fails — the `baseReference` FK is invalid.

- **All child POST endpoints take LIST-wrapper input reps.** POST
  `{contextMappings: [...]}`, `{contextNodeMappings: [...]}`,
  `{contextAttributes: [...]}`, and
  `{contextAttributeMappings: [...], deleteExistingHydrationDetails: false}`
  — never a bare object.

- **Attribute-mapping POST uses `contextAttributeId`, not
  `contextAttributeName`.** Resolve the Id from the draft first via the
  6d GET response.

- **`hydrationDetails` on the attribute-mapping POST is an OBJECT wrapper**
  with two typed lists (`contextAttrContextHydrationDetails` and
  `contextAttrHydrationDetails`), NOT the bare-array shape the output tree
  returns as `contextAttrHydrationDetailList`. Posting a bare array returns
  `Can not deserialize: unexpected array`.

- **Activation gate — a mapping must have `isDefault=true` first.** The
  Connect extend copies base mappings but each comes back `isDefault=false`;
  activating without promoting one first returns `DATA_MAPPING_NOT_FOUND:
  Cannot activate a definition without default mapping`. Step 6f-i handles
  this.

- **Hydration-detail portability.** Every
  `hydrationDetails.contextAttrHydrationDetails[*].queryAttribute` value is
  either an sObject field name paired with `sObjectDomain` (used by 6e-i's
  three `Account.id` mappings — hydrated from `Account.Id`, which every org
  has), OR the name of a tag on some other CD referenced by
  `mappedContextDefinitionName`. This version only ships the first shape,
  so no runtime portability failure is expected here. If a future extension
  re-introduces cross-CD hydration and the target CD is absent, the POST
  fails with either `UNKNOWN_EXCEPTION: Context Attr Context Details Write
  error` or `REQUIRED_FIELD_MISSING: [ObjectName]`. Fallback: retry the
  same POST without the `hydrationDetails` key — the attribute-mapping
  lands with an empty `contextAttrHydrationDetailList` and its runtime
  hydration silently no-ops. Do NOT try to satisfy the `[ObjectName]` error
  by adding an `objectName` / `ObjectName` / `sObjectName` field at the
  attribute-mapping item level — those are rejected as `Unrecognized field`
  by the input rep.

- **Steps 6 and 8 are chained.** Step 8's POST body carries
  `contextDefinitions[0].id = <customcommsproductdiscovery.contextDefinitionId>`
  resolved from the Step 7 verify. If Step 6 gaps out, Step 8 CANNOT run —
  the ESD's `contextDefinitions` binding is required at create time (the
  server rejects a subsequent PATCH that adds it with `INTERNAL_ERROR`), so
  a null CD means no valid POST body. Report Step 8 as blocked-by-Step-6 in
  that case.

- **Step 8 uses `POST`-with-full-body, NOT `POST`-then-`PATCH`.** The BRE
  Connect API's `postExpressionSetCreate` accepts `versions[].steps[]` and
  `versions[].variables[]` inline. `patchExpressionSet` on the same shell
  with version content returns `INTERNAL_ERROR`; do NOT split the write.
  Similarly, `contextDefinitions` MUST be set on the POST — a subsequent
  PATCH to add / change the CD binding on an existing shell also returns
  `INTERNAL_ERROR`.

- **Step 8 activates on create in one POST.** The POST body carries
  `versions[0].enabled=true`; `postExpressionSetCreate` accepts an active
  version on create as long as the body carries at least one step, and
  the 201 response echoes `versions[0].enabled=true`. Do NOT split into
  POST-inactive-then-PATCH-active. Rank promotion (multi-version
  selection) and effective-date windows are out of scope.

- **Step 8 skip-if-present is `developerName`-based.** The ESD's
  `developerName` (`apiName` on the Connect API is the same identity) is
  globally unique on the org; a duplicate POST returns 400. Guard with
  the 8a SOQL first — the recipe treats any existing record as terminal
  regardless of `enabled`.

- **`LookUpId` on `ListPrice` is an sObject Id and is not portable
  cross-org.** The literal `0lDDX00000000WW2AY` in the reference body maps
  to the source org's `Price_Book_Entry_Decision_Table_v2` decision table.
  The server auto-remaps it on-write to the target org's decision-table Id
  (both are `0lDDX…` prefix; the response body carries the org-local
  value). If the decision table is missing on the target org, the POST
  still returns 201 but the runtime `ListPrice` step fails on first
  execution — verify the decision table exists as a precondition (see
  below).

- **No Setup UI walks, no CLI shell-outs.** Every step routes through a
  dispatched REST call — Steps 1–5 through sObject/REST, Steps 6–7 through
  `/services/data/v67.0/connect/*`, Step 8 through
  `/services/data/v67.0/connect/business-rules/expression-set`. If a
  precondition is not satisfied, halt with a gap; do NOT attempt a
  shell-out or multipart deploy.

## Preconditions

Before Step 1, confirm:

1. **Comms Cloud add-on licenses are provisioned.** Step 1's SOQL is the
   canonical check.
2. **Revenue Cloud base/initial setup is complete.**
3. **Context Service is enabled and the base CD is present.**
   `CommsProductDiscoveryContext__stdctx` ships with Revenue Cloud Comms;
   Step 6 extends it.
4. **Business Rules Engine (BRE) is enabled and the
   `Price_Book_Entry_Decision_Table_v2` decision table exists on the org.**
   Step 8's `ListPrice` step references it by API name; the server
   auto-resolves the target-org `0lDDX…` id at write time. If the decision
   table is absent, the POST still succeeds structurally but the pricing
   procedure will fail at first-invocation. Sanity check with
   `GET /services/data/v67.0/connect/business-rules/decision-tables?apiName=Price_Book_Entry_Decision_Table_v2`
   (or SOQL against the corresponding sObject).

If precondition 3 is missing, Steps 6–7 gap out; Steps 1–5 still complete.
If precondition 4 is missing, Step 8 structurally succeeds but is flagged
as a runtime gap; earlier steps are unaffected.

## Verification Checklist

- Step 3 SOQL returns 0–3 rows and the "already assigned" set is computed
  correctly against Step 1's resolved Ids.
- Step 4 posts one `PermissionSetAssignment` per missing permission set and
  each returns `201` with a generated Id (`0Pa…`).
- Step 5 SOQL returns one row per resolved permission-set Name.
- Step 6a resolves the `CommsProductDiscoveryContext__stdctx` base
  `contextDefinitionId`. For stock CDs the returned id equals the developer
  name; the `11ODX…` key-prefix shape only applies to custom / extension CDs.
- Step 6c `POST /connect/context-definitions` (extend) returns 201 with a
  new `contextDefinitionId` for the draft; `developerName` echoes
  `customcommsproductdiscovery`, `isActive=false`.
- Step 6e writes: 3 context-attribute-mappings on shared base-inherited
  mappings' `Account` node-mappings (`id` on `ProductDiscoveryMapping`,
  `QuoteProductDiscoveryMapping`, and `OrderProductDiscoveryMapping` — each
  hydrated from `Account.Id`). Every response body is 200/201 with the
  created child Id, or a duplicate-name 400 treated as a no-op.
- Step 6f-i default-mapping PATCH: 200 and response body shows the chosen
  mapping with `isDefault=true`.
- Step 6f-ii activate: PATCH returns 200 and the response body shows
  `isActive=true`.
- Step 7 `GET /connect/context-definitions?developerName=customcommsproductdiscovery`
  returns 1 row with `isActive=true`, label = `customcommsproductdiscovery`,
  and `baseReference=CommsProductDiscoveryContext__stdctx`.
- Step 8a skip-if-present SOQL returns 0 rows (fresh org) or 1 row
  matching `DeveloperName=Comms_Product_Discovery_Pricing_Procedure`
  (idempotent re-run).
- Step 8c POST returns 201 with `id` (`9QLDX…`), `versions[0].id` (`9QMDX…`),
  server-set `usageSubtype=RevenueCloud`, `contextDefinitions` echoing the
  bound `customcommsproductdiscovery`. Response `versions[0].steps` length
  is 2; `versions[0].variables` length is 1.
- Step 8d verify GET returns the shape asserted in 8d: 2 steps with correct
  `sequenceNumber` + `actionType`, 1 Constant variable, and each step's
  `customElement.parameters` list length matches the POST body (9 for
  `PricingSetting`, 18 for `ListPrice`).

## Operations Reference

| Step | Verb + Path                                                       | Op / body                                                                        | Kind    |
|------|-------------------------------------------------------------------|----------------------------------------------------------------------------------|---------|
| 1    | `GET /services/data/v67.0/query`                                  | `q = SELECT Id, Name FROM PermissionSet WHERE Name IN (…3 names…)`               | read    |
| 2    | `GET /services/data/v67.0/` (or `SELECT Id FROM User …`)          | resolve running user                                                             | read    |
| 3    | `GET /services/data/v67.0/query`                                  | `q = SELECT PermissionSetId, PermissionSet.Name FROM PermissionSetAssignment …`  | read    |
| 4    | `POST /services/data/v67.0/sobjects/PermissionSetAssignment`      | `{AssigneeId, PermissionSetId}` per missing set                                  | write   |
| 5    | `GET /services/data/v67.0/query`                                  | re-run Step 3 SOQL                                                               | verify  |
| 6a   | `GET /services/data/v67.0/connect/context-definitions`            | resolve `CommsProductDiscoveryContext__stdctx` id                                | read    |
| 6b   | `GET /services/data/v67.0/connect/context-definitions`            | skip-if-present gate on `customcommsproductdiscovery`                            | read    |
| 6c   | `POST /services/data/v67.0/connect/context-definitions`           | extend body: `{developerName, name, baseReference}` (no `isActive`)              | write   |
| 6d   | `GET /services/data/v67.0/connect/context-definitions/{draftId}`  | resolve org-specific Ids on draft (shared-mapping Account node-mapping Ids; base `Account.id` attr Id) | read    |
| 6e-i | `POST /services/data/v67.0/connect/context-node-mappings/{sharedMapping.Account.nodeMappingId}/context-attribute-mappings` × 3 | shared-mapping attrs: `id` on Product / Quote / Order Discovery (each hydrated from `Account.Id`) | write   |
| 6f-i | `PATCH /services/data/v67.0/connect/context-definitions/{draftId}/context-mappings` | `{contextMappings: [{contextMappingId, isDefault: true}]}` — required before activation | write   |
| 6f-ii| `PATCH /services/data/v67.0/connect/context-definitions/{draftId}`| `{isActive: true}`                                                               | write   |
| 7    | `GET /services/data/v67.0/connect/context-definitions?developerName=customcommsproductdiscovery` | verify active                                                | verify  |
| 8a   | `GET /services/data/v67.0/query?q=SELECT+Id,DeveloperName,MasterLabel+FROM+ExpressionSetDefinition+WHERE+DeveloperName='Comms_Product_Discovery_Pricing_Procedure'` | skip-if-present gate (Connect collection is `POST`-only — a `GET` returns 405, so this gate is SOQL) | read    |
| 8b   | (in-memory)                                                       | resolve `customcommsproductdiscovery.contextDefinitionId` from Step 7            | derive  |
| 8c   | `POST /services/data/v67.0/connect/business-rules/expression-set` | full V1 body: shell + `contextDefinitions[]` + inline `versions[]` (steps, variables, customElement.parameters) | write   |
| 8d   | `GET /services/data/v67.0/connect/business-rules/expression-set/{id}` | verify shape (2 steps, 1 Constant, correct sequenceNumbers, bound CD)         | verify  |

<!-- skill-validate: ignore-start -->
<!-- codey:operations start -->
## Operations Reference

Operations this skill uses — routing and dependency reference.

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `resolve-permission-set-ids` | read | — | `GET /services/data/v67.0/query` | — |
| `resolve-target-user` | read | — | `GET /services/data/v67.0/` | — |
| `check-existing-assignments` | read | — | `GET /services/data/v67.0/query` | `resolve-permission-set-ids`, `resolve-target-user` |
| `assign-permission-set` | write | — | `POST /services/data/v67.0/sobjects/PermissionSetAssignment` | `check-existing-assignments` |
| `verify-assignments` | verify | — | `GET /services/data/v67.0/query` | `assign-permission-set` |
| `confirm-base-cd-active` | read | — | `GET /services/data/v67.0/connect/context-definitions` | — |
| `skip-if-present-cd` | read | — | `GET /services/data/v67.0/connect/context-definitions` | `confirm-base-cd-active` |
| `extend-context-definition` | write | — | `POST /services/data/v67.0/connect/context-definitions` | `skip-if-present-cd` |
| `fetch-draft-node-mappings` | read | — | `GET /services/data/v67.0/connect/context-definitions/{contextDefinitionId}` | `extend-context-definition` |
| `augment-shared-attribute-mappings` | write | — | `POST /services/data/v67.0/connect/context-node-mappings/{parentNodeMappingId}/context-attribute-mappings` | `fetch-draft-node-mappings` |
| `promote-default-mapping` | write | — | `PATCH /services/data/v67.0/connect/context-mappings/{contextMappingId}` | `augment-shared-attribute-mappings` |
| `activate-context-definition` | write | — | `PATCH /services/data/v67.0/connect/context-definitions/{contextDefinitionId}` | `promote-default-mapping` |
| `verify-context-definition-active` | verify | — | `GET /services/data/v67.0/connect/context-definitions` | `activate-context-definition` |
| `skip-if-present-esd` | read | — | `GET /services/data/v67.0/query` | `verify-context-definition-active` |
| `author-pricing-procedure` | write | — | `POST /services/data/v67.0/connect/business-rules/expression-set` | `skip-if-present-esd` |
| `verify-pricing-procedure` | verify | — | `GET /services/data/v67.0/connect/business-rules/expression-set/{expressionSetId}` | `author-pricing-procedure` |
<!-- codey:operations end -->
<!-- skill-validate: ignore-end -->
