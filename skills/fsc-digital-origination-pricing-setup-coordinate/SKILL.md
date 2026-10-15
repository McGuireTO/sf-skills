---
name: fsc-digital-origination-pricing-setup-coordinate
description: "End-to-end orchestrator for Digital Origination (Digital Lending) pricing after Initial Setup and Product Catalog Management are complete. Routes an unqualified \"set up lending pricing\" request through nested pricing sub-skills for permissions, pricing data, Business Rules Engine decision tables and NGPDefaultRecipe mapping, engine-specific configuration, and pricing procedure creation. Product Configurator is the default Digital Lending engine; Salesforce Pricing is an explicit alternative. Use this skill for the whole ordered journey, and use a sibling directly for a narrowed request such as \"create the pricing decision tables\" or \"configure the lending pricing procedure\"."
metadata:
  version: "1.0"
---

# Digital Origination pricing setup orchestrator

Orchestrate pricing for **Digital Origination**, whose underlying APIs and setup artifacts still use
the **Digital Lending** name. This skill owns sequencing and state transfer. It does not duplicate the
implementation contracts maintained by its nested pricing sub-skills.

## Mandatory prerequisites

Before routing to a pricing sibling, verify:

1. Digital Origination Initial Setup is complete. If not, route to
 `fsc-mandalorians/digital-origination-initial-setup` and stop pricing setup.
2. Product Catalog Management is complete: catalog, category or classification, lending products,
 product attributes, and required product relationships exist.
3. The target org alias and acting admin are explicit.
4. The admin has supplied or approved the products, base rates, effective dates, credit-score tiers,
 and term tiers. Documentation examples are not customer defaults.
5. The pricing engine is known. Use **Product Configurator** when no alternative is requested. Use
 **Salesforce Pricing** only when the admin explicitly selects it.

## Ordered journey

```text
Initial Setup (existing sibling)
 |
Product Catalog Management (assumed complete)
 |
1. Pricing permissions
 |
2. Product List Rate data
 |
3. ProductListRateDT
 |
4. Credit-score data
 |
5. CreditScoreBasedAdjustmentDT
 |
6. Term data
 |
7. TermBasedAdjustmentDT
 |
8. NGPDefaultRecipe mapping
 |
9A. Product Configurator attributes (default) OR 9B. Salesforce Pricing OmniStudio wiring
 |
10. Pricing procedure for the selected engine
 |
11. End-to-end verification
```

Run one sibling at a time. Do not continue after a sibling reports a blocking prerequisite or a
manual checkpoint that has not been completed.

### Step 1 - Pricing permissions and Core Pricing preference

Delegate to nested skill `permissions` (emitted SOR
`fsc-mandalorians/digital-origination-pricing-setup-permissions`) with hints such as:

- "assign Digital Lending pricing permission sets"
- "Salesforce Pricing Design Time and Run Time access"
- "Rule Engine Designer and Rule Engine User assignments"
- "enable the org CorePricingPreference / Salesforce Pricing preference"

This step also enables the org-level `CorePricingPreference` toggle (via the `CorePricingSetting` SOR),
a hard prerequisite that gates every downstream pricing feature. Required handoff: target user IDs,
resolved permission-set IDs/API names, license assignments, a fresh verification of every required
assignment, and confirmation that `CorePricingPreference` reads enabled.

### Step 2 - Product List Rate data

Delegate to nested skill `data-foundation` (emitted SOR
`fsc-mandalorians/digital-origination-pricing-setup-data-foundation`) first in `product-list-rate` phase
mode, with hints such as:

- "create Product List Rate records"

Required handoff: actual Product List Rate object/field API names, Product List Rate IDs, and the
product IDs each record references.

### Step 3 - ProductListRateDT

Delegate to nested skill `decision-tables` (emitted SOR
`fsc-mandalorians/digital-origination-pricing-setup-decision-tables`) in `product-list-rate` phase mode,
with hints such as:

- "create ProductListRateDT"

Required handoff: active ID/version for `ProductListRateDT`.

### Step 4 - Credit-score data foundation

Return to nested skill `data-foundation` in `credit-score` phase mode to
create or verify the Rate Adjustment By Credit Score schema and customer-approved records. Required
handoff: actual source-object/field API names and score-tier record IDs.

### Step 5 - Credit-score decision table

Return to nested skill `decision-tables` in `credit-score` phase mode to
create, refresh, and activate `CreditScoreBasedAdjustmentDT`.

Required handoff: active ID/version for `CreditScoreBasedAdjustmentDT`.

### Step 6 - Term data foundation

Return to nested skill `data-foundation` in `term` phase mode to create or verify the Rate
Adjustment By Term schema and records. Required handoff: source-object/field API names and tier IDs.

### Step 7 - Term decision table

Return to nested skill `decision-tables` in `term` phase mode to create, refresh, and
activate `TermBasedAdjustmentDT`.

Required handoff: active ID/version for `TermBasedAdjustmentDT`.

### Step 8 - NGPDefaultRecipe mapping

Return to nested skill `decision-tables` in `recipe` phase only after all three tables are
Active. Required handoff: recipe ID and verified mappings for all three table IDs/component types.

### Step 9A - Product Configurator branch (default)

Delegate to nested skill `product-configurator` (emitted SOR
`fsc-mandalorians/digital-origination-pricing-setup-product-configurator`) with hints such as:

- "make Loan Term price impacting"
- "hide Credit Score and make it price impacting"
- "configure Product Configurator attributes for lending pricing"

Required handoff: product-classification and attribute IDs plus read-back of `isPriceImpacting` and
`isHidden` for Loan Term, Credit Score, and Loan Amount.

### Step 9B - Salesforce Pricing branch (explicit alternative)

Delegate to nested skill `salesforce-pricing-omnistudio` (emitted SOR
`fsc-mandalorians/digital-origination-pricing-setup-salesforce-pricing-omnistudio`) with hints such as:

- "switch Digital Lending from Product Configurator to Salesforce Pricing"
- "repoint DigitalLendingApplicantIntake to DigitalLendingViewOffer"
- "replace the Digital Lending final-offer Integration Procedure"

Required handoff: original and new versions of both OmniScripts and both FlexCards, with verified
component references. Never run this branch in addition to 9A unless explicitly requested.

### Step 10 - Pricing procedure

Delegate to nested skill `pricing-procedure` (emitted SOR
`fsc-mandalorians/digital-origination-pricing-setup-pricing-procedure`) with hints such as:

- "create LendingProductConfigContext"
- "create digital_lending_AppFormProductProposalConfigProc"
- "add Pricing Setting, List Price, and Price Adjustment Matrix elements"

Pass the selected engine, three active decision-table IDs, recipe ID, source field names, and any
engine-specific attribute or OmniStudio results. Required handoff: context-definition ID, expression
set/procedure ID, active version, ordered element configuration, and procedure/recipe binding.

**Org feature-gate prerequisite (org-verified).** This step depends on **one**
org feature gate that is **separate from licenses and permission sets**: **Context Service**
(`ContextResourceFamily`) for the context definition. A closed gate returns 403
`FUNCTIONALITY_NOT_ENABLED`. Enable it headlessly first (org-verified primary path):
`PUT /connect/contextservice/access/contextServiceEnabled/{orgId}` body `{"isEnabled":true}` → 200; the
UI toggle at `/lightning/setup/ContextServiceSettings/home` is the fallback only if the PUT is
unavailable. Confirm the gate is open with a live 200 from `GET /connect/context-definitions` before
proceeding; the `permissions` sibling owns the enable + verification. **The pricing procedure itself is
NOT gate-blocked** — build it via the un-gated BRE endpoint `POST /connect/business-rules/expression-set`
(not `/connect/core-pricing/expression-set`, which is a separate gated surface that is not required).
`LendingProductConfigContext` is a **standard** context that already exists active on the target org — reuse
it, do not recreate. Full matrix and the verified create body live in the `permissions` and
`pricing-procedure` siblings.

## Narrowed requests

| User request | Route |
|---|---|
| Assign pricing access only | Nested `permissions` |
| Create rate objects or seed pricing records | Nested `data-foundation` |
| Create decision tables or update `NGPDefaultRecipe` | Nested `decision-tables` |
| Configure Product Configurator pricing attributes | Nested `product-configurator` |
| Switch OmniStudio to Salesforce Pricing | Nested `salesforce-pricing-omnistudio` |
| Create or repair the pricing procedure | Nested `pricing-procedure` |

For a narrowed request, validate that its upstream artifacts exist. Do not silently run the entire
journey when the user explicitly asks for one part.

## Shared invariants

- Read before write; reuse matching artifacts by API name and verified shape.
- Never infer customer rates, tiers, effective dates, products, or users.
- Preserve unrelated recipe mappings, expression-set steps, product attributes, and component JSON.
- Treat asynchronous states as in progress, not success.
- A guided Setup checkpoint is a valid partial outcome only when the relevant headless write is absent
 or unverified. State exactly what remains and resume after confirmation.
- Each sibling must produce fresh read-back evidence before this orchestrator advances.
- **Deploy-first for custom source objects.** Tables 2/3 (`CreditScoreBasedAdjustmentDT`,
 `TermBasedAdjustmentDT`) may be reported DEFERRED only after nested `data-foundation` attempted the
 `Rate_Adjustment_By_Credit_Score__c` / `Rate_Adjustment_By_Term__c` deploy AND nested
 `decision-tables` ran a probe DT create against the deployed source AND every resolution predicate
 was satisfied. A DEFERRED report without deploy + probe evidence is not accepted; re-invoke the
 deploy-first sequence.

## Definition of done

The full journey is complete only when:

1. Required permission-set and license assignments are verified, and the org-level
 `CorePricingPreference` reads enabled.
2. Product List Rate, credit-score tiers, and term tiers exist with the approved values.
3. `ProductListRateDT` is active and refreshed. `CreditScoreBasedAdjustmentDT` and
 `TermBasedAdjustmentDT` are either active-and-refreshed OR reported DEFERRED with the deploy-first
 evidence bundle attached (deploy attempted per `data-foundation` Step 2, probe DT create attempted
 per `decision-tables` Source-object gate, rejection payload captured, resolution predicates
 verified). Presumed-DEFERRED without evidence is a run failure.
4. `NGPDefaultRecipe` contains the intended mappings without losing existing mappings.
5. The selected engine's prerequisite configuration is verified.
6. `LendingProductConfigContext` and the selected pricing procedure exist, are active, and contain the
 expected ordered elements and variables.
7. `NGPDefaultRecipe` is re-read after procedure creation and points to that verified procedure while
 retaining all intended decision-table mappings.
8. Every manual checkpoint or unresolved gap is explicitly reported. A partial run is never reported
 as complete.

## Individual sibling reference

| Sibling | Responsibility | Primary corpus reuse |
|---|---|---|
| `permissions` | Pricing licenses, permission sets, and the CorePricingPreference org toggle | `entity/authorization-experience/PermSets` + `CorePricingSetting` |
| `data-foundation` | Rate objects, fields, and records | Metadata API + sObject REST pattern |
| `decision-tables` | Three BRE tables, activation, recipe mapping | BRE Taurus + Industries Pricing Connect APIs |
| `product-configurator` | Price-impacting/hidden attributes | EPC reads + verified sObject/UI checkpoint |
| `salesforce-pricing-omnistudio` | Salesforce Pricing component repointing | OmniStudio Phoenix + Orion APIs |
| `pricing-procedure` | Context and engine-specific procedure | Context Service + Industries Pricing/Expression Set APIs |

These are nested source skills. Project Codey compiles each to a parent-qualified sibling SOR and adds
formal `delegates_to` steps to this parent. Run the Path-B harness on this parent `SKILL.md`; the family
is merged, ingested, and served together.

<!-- skill-validate: ignore-start -->
<!-- codey:operations start -->
## Operations Reference

Operations this skill uses — routing and dependency reference.

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `delegate-digital-origination-pricing-setup-permissions` | delegate | — | → `fsc-mandalorians/digital-origination-pricing-setup-permissions` | — |
| `delegate-digital-origination-pricing-setup-data-foundation` | delegate | — | → `fsc-mandalorians/digital-origination-pricing-setup-data-foundation` | `delegate-digital-origination-pricing-setup-permissions` |
| `delegate-digital-origination-pricing-setup-decision-tables` | delegate | — | → `fsc-mandalorians/digital-origination-pricing-setup-decision-tables` | `delegate-digital-origination-pricing-setup-data-foundation` |
| `delegate-digital-origination-pricing-setup-product-configurator` | delegate | — | → `fsc-mandalorians/digital-origination-pricing-setup-product-configurator` | `delegate-digital-origination-pricing-setup-decision-tables` |
| `delegate-digital-origination-pricing-setup-salesforce-pricing-omnistudio` | delegate | — | → `fsc-mandalorians/digital-origination-pricing-setup-salesforce-pricing-omnistudio` | `delegate-digital-origination-pricing-setup-decision-tables` |
| `delegate-digital-origination-pricing-setup-pricing-procedure` | delegate | — | → `fsc-mandalorians/digital-origination-pricing-setup-pricing-procedure` | `delegate-digital-origination-pricing-setup-product-configurator`, `delegate-digital-origination-pricing-setup-salesforce-pricing-omnistudio` |
| `verify-pricing-simulation` | verify | — | `POST /connect/core-pricing/pricing` | `delegate-digital-origination-pricing-setup-pricing-procedure` |
| `preflight-context-service-and-lending-context` | verify | — | `GET /connect/context-definitions/LendingProductConfigContext__stdctx` | `delegate-digital-origination-pricing-setup-permissions` |
| `helper-generate-simulation-input` | read | — | `GET /connect/core-pricing/simulationInputVariablesWithData` | `delegate-digital-origination-pricing-setup-pricing-procedure` |
| `permissions-confirm-org-and-target-user` | read | — | `GET /services/data/v63.0/query` | — |
| `permissions-resolve-permission-sets-by-name` | read | — | `GET /services/data/v63.0/query` | `permissions-confirm-org-and-target-user` |
| `permissions-assign-required-license` | write | — | `POST /services/data/v63.0/sobjects/PermissionSetLicenseAssign` | `permissions-resolve-permission-sets-by-name` |
| `permissions-assign-permission-sets` | write | — | `POST /services/data/v63.0/sobjects/PermissionSetAssignment` | `permissions-assign-required-license` |
| `permissions-read-core-pricing-preference` | read | — | `GET /services/data/v67.0/setup/org/preferences/CorePricingPreference` | `permissions-assign-permission-sets` |
| `permissions-enable-core-pricing-preference` | write | — | `PATCH /services/data/v67.0/setup/org/preferences/CorePricingPreference` | `permissions-read-core-pricing-preference` |
| `permissions-enable-context-service` | write | — | `PUT /services/data/v63.0/connect/contextservice/access/contextServiceEnabled/{orgId}` | `permissions-enable-core-pricing-preference` |
| `permissions-verify-context-service-live` | verify | — | `GET /services/data/v63.0/connect/context-definitions` | `permissions-enable-context-service` |
| `permissions-verify-assignments-and-preferences` | verify | — | `GET /services/data/v63.0/query` | `permissions-verify-context-service-live` |
| `data-foundation-describe-product-list-rate-object` | read | — | `GET /services/data/v63.0/sobjects/ProductListRate/describe` | — |
| `data-foundation-discover-credit-score-term-source-objects` | read | — | `GET /services/data/v63.0/query` | — |
| `data-foundation-deploy-custom-object-shell` | write | — | `POST /services/data/v63.0/headless/metadata/CustomObject` | `data-foundation-discover-credit-score-term-source-objects` |
| `data-foundation-deploy-custom-fields` | write | — | `POST /services/data/v63.0/tooling/sobjects/CustomField` | `data-foundation-deploy-custom-object-shell` |
| `data-foundation-deploy-fls-permission-set` | write | — | `POST /services/data/v63.0/headless/metadata/PermissionSet` | `data-foundation-deploy-custom-fields` |
| `data-foundation-assign-fls-permission-set` | write | — | `POST /services/data/v63.0/sobjects/PermissionSetAssignment` | `data-foundation-deploy-fls-permission-set` |
| `data-foundation-verify-custom-object-describe` | verify | — | `GET /services/data/v63.0/sobjects/{objectApiName}/describe` | `data-foundation-deploy-custom-object-shell`, `data-foundation-deploy-custom-fields`, `data-foundation-assign-fls-permission-set` |
| `data-foundation-query-existing-product-list-rate-records` | read | — | `GET /services/data/v63.0/query` | `data-foundation-describe-product-list-rate-object` |
| `data-foundation-create-product-list-rate-records` | write | — | `POST /services/data/v63.0/sobjects/ProductListRate` | `data-foundation-query-existing-product-list-rate-records` |
| `data-foundation-verify-product-list-rate-records` | verify | — | `GET /services/data/v63.0/query` | `data-foundation-create-product-list-rate-records` |
| `data-foundation-query-existing-credit-score-adjustment-records` | read | — | `GET /services/data/v63.0/query` | `data-foundation-verify-custom-object-describe` |
| `data-foundation-create-credit-score-adjustment-records` | write | — | `POST /services/data/v63.0/sobjects/Rate_Adjustment_By_Credit_Score__c` | `data-foundation-query-existing-credit-score-adjustment-records` |
| `data-foundation-verify-credit-score-adjustment-records` | verify | — | `GET /services/data/v63.0/query` | `data-foundation-create-credit-score-adjustment-records` |
| `data-foundation-query-existing-term-adjustment-records` | read | — | `GET /services/data/v63.0/query` | `data-foundation-verify-custom-object-describe` |
| `data-foundation-create-term-adjustment-records` | write | — | `POST /services/data/v63.0/sobjects/Rate_Adjustment_By_Term__c` | `data-foundation-query-existing-term-adjustment-records` |
| `data-foundation-verify-term-adjustment-records` | verify | — | `GET /services/data/v63.0/query` | `data-foundation-create-term-adjustment-records` |
| `decision-tables-resolve-existing-decision-table` | read | — | `GET /services/data/v63.0/connect/omnistudio/decision-tables` | — |
| `decision-tables-create-product-list-rate-dt` | write | — | `POST /services/data/v63.0/connect/business-rules/decision-table/definitions` | `decision-tables-resolve-existing-decision-table` |
| `decision-tables-materialize-dt-sobject-fields` | write | — | `PATCH /services/data/v63.0/sobjects/DecisionTable/{Id}` | `decision-tables-create-product-list-rate-dt` |
| `decision-tables-activate-decision-table-version` | write | — | `PATCH /services/data/v63.0/connect/business-rules/decision-table/definitions/{decisionTableId}/versions` | `decision-tables-materialize-dt-sobject-fields` |
| `decision-tables-refresh-decision-table` | write | — | `POST /services/data/v63.0/connect/decision-table/refresh` | `decision-tables-activate-decision-table-version` |
| `decision-tables-verify-hbase-materialization` | verify | — | `GET /services/data/v63.0/query` | `decision-tables-refresh-decision-table` |
| `decision-tables-probe-custom-source-eligibility` | validate | — | `POST /services/data/v63.0/connect/business-rules/decision-table/definitions` | `decision-tables-resolve-existing-decision-table` |
| `decision-tables-list-and-read-ngp-default-recipe` | read | — | `GET /services/data/v63.0/connect/core-pricing/recipe` | `decision-tables-verify-hbase-materialization` |
| `decision-tables-resolve-recipe-mapping-parameters` | read | — | `GET /services/data/v63.0/connect/core-pricing/recipe/mapping/parameters` | `decision-tables-list-and-read-ngp-default-recipe` |
| `decision-tables-map-product-list-rate-to-recipe` | write | — | `POST /services/data/v63.0/connect/core-pricing/recipe/mapping` | `decision-tables-resolve-recipe-mapping-parameters` |
| `decision-tables-verify-recipe-mapping` | verify | — | `GET /services/data/v63.0/connect/core-pricing/recipe/{pricingRecipeId}` | `decision-tables-map-product-list-rate-to-recipe` |
| `product-configurator-resolve-existing-attributes` | read | — | `GET /services/data/v63.0/query` | — |
| `product-configurator-create-credit-score-attribute` | write | — | `POST /services/data/v63.0/sobjects/AttributeDefinition` | `product-configurator-resolve-existing-attributes` |
| `product-configurator-activate-credit-score-attribute` | write | — | `PATCH /services/data/v63.0/sobjects/AttributeDefinition/{Id}` | `product-configurator-create-credit-score-attribute` |
| `product-configurator-create-loan-amount-attribute` | write | — | `POST /services/data/v63.0/sobjects/AttributeDefinition` | `product-configurator-resolve-existing-attributes` |
| `product-configurator-activate-loan-amount-attribute` | write | — | `PATCH /services/data/v63.0/sobjects/AttributeDefinition/{Id}` | `product-configurator-create-loan-amount-attribute` |
| `product-configurator-assign-credit-score-to-classification` | write | — | `POST /services/data/v63.0/sobjects/ProductClassificationAttr` | `product-configurator-activate-credit-score-attribute` |
| `product-configurator-assign-loan-amount-to-classification` | write | — | `POST /services/data/v63.0/sobjects/ProductClassificationAttr` | `product-configurator-activate-loan-amount-attribute` |
| `product-configurator-set-flags-credit-score` | write | — | `PATCH /services/data/v63.0/sobjects/ProductClassificationAttr/{Id}` | `product-configurator-assign-credit-score-to-classification` |
| `product-configurator-set-flags-loan-amount` | write | — | `PATCH /services/data/v63.0/sobjects/ProductClassificationAttr/{Id}` | `product-configurator-assign-loan-amount-to-classification` |
| `product-configurator-set-flags-loan-term` | write | — | `PATCH /services/data/v63.0/sobjects/ProductClassificationAttr/{Id}` | `product-configurator-resolve-existing-attributes` |
| `product-configurator-verify-final-attribute-state` | verify | — | `GET /services/data/v63.0/query` | `product-configurator-set-flags-credit-score`, `product-configurator-set-flags-loan-amount`, `product-configurator-set-flags-loan-term` |
| `salesforce-pricing-omnistudio-find-omniscript-versions` | read | — | `GET /services/data/v63.0/connect/omni-designer/omni-process-list` | — |
| `salesforce-pricing-omnistudio-read-omniscript-element-tree` | read | — | `GET /services/data/v63.0/connect/omni-designer/omniprocess/{omniProcessId}` | `salesforce-pricing-omnistudio-find-omniscript-versions` |
| `salesforce-pricing-omnistudio-clone-omniscript-process` | write | — | `POST /services/data/v63.0/connect/omni-designer/clone-omni-process` | `salesforce-pricing-omnistudio-read-omniscript-element-tree` |
| `salesforce-pricing-omnistudio-delete-offer-configurator-element` | write | — | `POST /services/data/v63.0/connect/omni-designer/os/delete-omni-process-element` | `salesforce-pricing-omnistudio-clone-omniscript-process` |
| `salesforce-pricing-omnistudio-insert-view-offer-element` | write | — | `POST /services/data/v63.0/connect/omni-designer/os/insert-omni-process-element` | `salesforce-pricing-omnistudio-delete-offer-configurator-element` |
| `salesforce-pricing-omnistudio-build-save-compile-omniscript` | write | — | `POST /services/data/v63.0/connect/omni-designer/os/build-json` | `salesforce-pricing-omnistudio-insert-view-offer-element` |
| `salesforce-pricing-omnistudio-verify-cloned-omniscript-element-tree` | verify | — | `GET /services/data/v63.0/connect/omni-designer/omniprocess/{omniProcessId}` | `salesforce-pricing-omnistudio-build-save-compile-omniscript` |
| `salesforce-pricing-omnistudio-activate-omniscript-version` | write | — | `POST /services/data/v63.0/connect/omni-designer/upsert-omni-process` | `salesforce-pricing-omnistudio-verify-cloned-omniscript-element-tree` |
| `salesforce-pricing-omnistudio-verify-omniscript-activation` | verify | — | `GET /services/data/v63.0/connect/omni-designer/omni-process-list` | `salesforce-pricing-omnistudio-activate-omniscript-version` |
| `salesforce-pricing-omnistudio-resolve-card-and-active-version` | read | — | `GET /services/data/v63.0/connect/livecards/cards/{cardId}/versions` | — |
| `salesforce-pricing-omnistudio-read-card-builder-json` | read | — | `GET /services/data/v63.0/connect/livecards/versions/{versionId}` | `salesforce-pricing-omnistudio-resolve-card-and-active-version` |
| `salesforce-pricing-omnistudio-create-new-card-version` | write | — | `POST /services/data/v63.0/connect/livecards/cards/{cardId}/versions` | `salesforce-pricing-omnistudio-read-card-builder-json` |
| `salesforce-pricing-omnistudio-update-card-ip-reference` | write | — | `PUT /services/data/v63.0/connect/livecards/versions/{versionId}` | `salesforce-pricing-omnistudio-create-new-card-version` |
| `salesforce-pricing-omnistudio-validate-and-verify-card-reference-swap` | verify | — | `POST /services/data/v63.0/connect/livecards/cards/validate` | `salesforce-pricing-omnistudio-update-card-ip-reference` |
| `salesforce-pricing-omnistudio-compare-card-versions` | verify | — | `GET /services/data/v63.0/connect/livecards/versions/{versionId}/compare/{compareVersionId}` | `salesforce-pricing-omnistudio-validate-and-verify-card-reference-swap` |
| `salesforce-pricing-omnistudio-verify-card-activation-checkpoint` | verify | — | `GET /services/data/v63.0/connect/livecards/cards/{cardId}/versions` | `salesforce-pricing-omnistudio-compare-card-versions` |
| `pricing-procedure-verify-context-service-gate` | verify | — | `GET /services/data/v63.0/connect/context-definitions` | — |
| `pricing-procedure-resolve-lending-product-config-context` | read | — | `GET /services/data/v63.0/connect/context-definitions` | `pricing-procedure-verify-context-service-gate` |
| `pricing-procedure-create-pricing-procedure-shell` | write | — | `POST /services/data/v63.0/connect/business-rules/expression-set` | `pricing-procedure-resolve-lending-product-config-context` |
| `pricing-procedure-verify-recipe-listprice-registration` | verify | — | `GET /services/data/v63.0/connect/core-pricing/recipe/{pricingRecipeId}` | `pricing-procedure-create-pricing-procedure-shell` |
| `pricing-procedure-author-elements-metadata-deploy` | write | — | `POST /services/data/v67.0/tooling/sobjects/ExpressionSetDefinition` | `pricing-procedure-verify-recipe-listprice-registration` |
| `pricing-procedure-append-corrected-version-not-edit-v1` | write | — | `PATCH /services/data/v67.0/tooling/sobjects/ExpressionSetDefinition/{recordId}` | `pricing-procedure-author-elements-metadata-deploy` |
| `pricing-procedure-bind-procedure-to-recipe` | write | — | `POST /services/data/v63.0/connect/core-pricing/recipe/mapping` | `pricing-procedure-append-corrected-version-not-edit-v1` |
| `pricing-procedure-verify-recipe-procedure-binding` | verify | — | `GET /services/data/v63.0/connect/core-pricing/recipe/{pricingRecipeId}` | `pricing-procedure-bind-procedure-to-recipe` |
| `pricing-procedure-seed-simulation-entity-graph` | write | — | `POST /services/data/v63.0/sobjects/ApplicationForm` | `pricing-procedure-verify-recipe-procedure-binding` |
| `pricing-procedure-generate-simulation-input` | read | — | `GET /services/data/v63.0/connect/core-pricing/simulationInputVariablesWithData` | `pricing-procedure-seed-simulation-entity-graph` |
| `pricing-procedure-simulate-evaluate-price` | verify | — | `POST /services/data/v63.0/connect/core-pricing/pricing` | `pricing-procedure-generate-simulation-input` |
<!-- codey:operations end -->
<!-- skill-validate: ignore-end -->
