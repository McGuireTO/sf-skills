---
name: fsc-digital-origination-pricing-setup-procedure-create
parent: "digital-origination-pricing-setup"
purpose: "Create and verify the lending pricing context, procedure, elements, and recipe binding."
description: "Create or repair the LendingProductConfigContext and the selected Digital Lending pricing procedure after ProductListRateDT, CreditScoreBasedAdjustmentDT, and TermBasedAdjustmentDT are active. Supports the Product Configurator procedure digital_lending_AppFormProductProposalConfigProc and the Salesforce Pricing alternative, using approved Context Service and Industries Pricing Expression Set APIs where the schema is explicit and a precise Pricing Designer checkpoint where per-element write payloads remain unresolved. Verifies context mappings, ordered pricing elements, variables, recipe binding, and active procedure state."
metadata:
  version: "1.0"
  cliTools:
  - tool:
    - "sf"
    semver: ">=2.0.0"
---

# Digital Origination pricing procedure

Create the context and ordered pricing procedure for one selected engine. This sibling does not create
source data, decision tables, or engine prerequisite configuration.

## Required inputs

- Target-org alias
- Engine: Product Configurator or Salesforce Pricing
- Exact procedure API name. Product Configurator defaults to
 `digital_lending_AppFormProductProposalConfigProc`; Salesforce Pricing requires an explicit name
 from the user or one uniquely resolved from the target org.
- Active IDs for `ProductListRateDT`, `CreditScoreBasedAdjustmentDT`, `TermBasedAdjustmentDT`
- `NGPDefaultRecipe` ID and verified mapping
- Product/attribute/source field API names
- Product Configurator attribute verification or Salesforce Pricing OmniStudio verification

`ProductListRateDT` (List Price) must be Active and registered in `NGPDefaultRecipe` before authoring
the ListPrice element. If `CreditScoreBasedAdjustmentDT` / `TermBasedAdjustmentDT` are blocked (the
source-object resolution limit documented in `decision-tables`), do NOT stop the whole procedure —
author a **ListPrice-only procedure** (Pricing Setting + List Price elements) that prices correctly,
OMIT the Credit Score (element 3) and Loan Term (element 4) Price Adjustment Matrix containers, and
report them as DEFERRED. Only stop if `ProductListRateDT` itself is inactive or the recipe has no
List Price mapping.

## Connect feature gates — hard prerequisites for this sibling (org-verified)

This sibling depends on **one** org feature gate: Context Service. It returns HTTP 403
`FUNCTIONALITY_NOT_ENABLED` (`This feature is not currently enabled for this user type or org:
[<Family>]`) until its **org feature toggle** is on. The gate is separate from licenses and permission
sets — assigning entitlements populates the sObjects/data model but does **not** open the gate.

- **Context Service** (`ContextResourceFamily`, flag `IndustriesContext.orgHasIndustriesContextService`)
 gates every `/connect/context-definitions*` call in Step 1. **Enable headlessly via API** (no UI step
 required, org-verified): `PUT /connect/contextservice/access/contextServiceEnabled/{orgId}`
 body `{isEnabled:true}` → 200. The `preferenceName` segment **must be `contextServiceEnabled`**; the
 value `ContextService` 404s on PUT (see the `permissions` sibling for the details).
 After enabling, verify with a live `GET /connect/context-definitions` (200), not the
 `getContextServiceAccess` read (which can still report `isEnabled:false`). The Setup UI toggle
 (**Context Service Settings** -> **Context Definitions**, `/lightning/setup/ContextServiceSettings/home`)
 is an equivalent fallback.

**The pricing procedure itself is NOT gate-blocked (org-verified).** Build it via
the **BRE** endpoint `POST /connect/business-rules/expression-set`, which is open on a Digital Lending
org and needs no extra permission set (a pricing-procedure expression set was created here directly,
`201 Created`). Do **not** route through `/connect/core-pricing/expression-set` — that separate
Salesforce-Pricing surface is fronted by `IExpressionSetResourceFamily` and 403s, but it is not
required to create the procedure. See "Reusable procedure operations" below for the verified field
recipe. Confirm the Context Service gate is open (a live 200 from `GET /connect/context-definitions`)
before Step 1; if it is closed, stop at that toggle as a manual checkpoint and resume after the user
confirms.

## Reusable Context Service operations

Use approved SOR
`connect-api/cs-context-service/industries-context-connect-api__industries.context.connect.api_oas_67.0`:

| Purpose | Operation | Endpoint |
|---|---|---|
| Create definition | `post-context-definitions` (`postContextDefinitions`) | `POST /connect/context-definitions` |
| Read definition | `get-context-definition` (`getContextDefinition`) | `GET /connect/context-definitions/{contextDefinitionId}` |
| Add nodes | `post-context-nodes` (`postContextNodes`) | `POST /connect/context-definitions/{contextDefinitionId}/context-nodes` |
| Add attributes | `post-context-attributes` (`postContextAttributes`) | `POST /connect/context-nodes/{contextNodeId}/context-attributes` |
| Create mapping | `post-context-mappings` (`postContextMappings`) | `POST /connect/context-definitions/{contextDefinitionId}/context-mappings` |
| Map nodes/attributes | `post-context-node-mappings`, `post-context-attribute-mappings` | Context mapping endpoints |
| Build context | `post-build-context` (`postBuildContext`) | `POST /connect/contexts` |

## Step 1 - Resolve or create LendingProductConfigContext

**Reuse-first (org-verified).** `LendingProductConfigContext` ships as a
**standard** context definition and was found already present and **active** on the target org once the
Context Service gate was enabled — `contextDefinitionId: LendingProductConfigContext__stdctx`,
`isActive: true`, with the full ApplicationForm -> product node/attribute mappings already populated.
Treat Step 1 as a **resolve-and-verify (reuse)**, not a create, unless the definition is genuinely
absent. Do not create a new definition when the standard one resolves.

1. Search context definitions by developer/display name `LendingProductConfigContext`.
2. If present, read nodes, attributes, mappings, effective dates, active version, and TTL. Reuse only
 an equivalent lending product configuration context.
3. If absent, do not infer a graph from object describe alone. Retrieve the standard
 `LendingProductConfigContext` definition from the installed release's setup template, sample
 metadata, or documented context-definition source. Creation requires an explicit node hierarchy,
 attribute names/types/tags, source objects/fields, node mappings, and attribute mappings. If that
 canonical definition is unavailable, stop at the Business Rules Engine **Create Context
 Definition** UI checkpoint and capture the resulting graph; do not create a guessed minimal context.
4. Create definition, nodes, attributes, context mapping, node mappings, and attribute mappings in
 dependency order.
5. Build a test context and query it. The definition is not ready until the expected tags/attributes
 resolve from representative input.

Do not copy `LendingProductDiscoveryContext`; qualification and pricing configuration contexts serve
different purposes.

Before any context write, save the complete existing definition, active version, nodes, attributes,
and mappings. If an incompatible same-name context exists, stop with a field-level diff; do not patch
it into a different semantic shape. On partial create failure, delete only artifacts created by this
run and only when no existing mapping references them.

## Reusable procedure operations

A Pricing Procedure is an Expression Set. **Build it through the BRE Orion endpoint**
(`industries-interaction-rule-connect-api`), which is un-gated on a Digital Lending org
(org-verified, `201 Created`):

- `postExpressionSetCreate` - `POST /connect/business-rules/expression-set` (create the procedure shell)
- `patchExpressionSet` - `PATCH /connect/business-rules/expression-set/{expressionSetId}` (add versions/steps)
- `getExpressionSet` - `GET /connect/business-rules/expression-set/{expressionSetId}` (read/verify)
- `deleteExpressionSet` - `DELETE /connect/business-rules/expression-set/{expressionSetId}` (rollback)

**Verified minimal create body for a pricing-procedure expression set (201):**

```json
{
 "name": "<display name>",
 "apiName": "<developer_api_name>",
 "description": "<optional>",
 "interfaceSourceType": "PricingProcedure",
 "usageType": "DefaultPricing",
 "usageSubtype": "RevenueCloud",
 "type": "Custom",
 "executionMode": "Cloud",
 "executionScale": "Low",
 "resourceInitializationType": "Off"
}
```

Field notes learned from the org's own validation errors (each was a 400 that walked to the fix):
`name` is required (distinct from `apiName`); `usageType: DefaultPricing` is the "Pricing" usage type
(its default `usageSubtype` is `RevenueCloud`); and `DefaultPricing` **requires**
`resourceInitializationType: Off` (`"...doesn't allow you to turn on defaulting..."`). Create returns
`id` plus an auto-created `versions[0]` (V1, `enabled:false`, empty `steps`/`variables`).

Do **not** use `/connect/core-pricing/expression-set` (Industries Pricing SOR
`connect-api/cme-core-veda/...`) as the build target — it is a separate Salesforce-Pricing surface
gated by `IExpressionSetResourceFamily` (403) and is not required here. Its read ops
(`get-industries-pricing-element-metadata-get`, `post-industries-pricing-metadata`) may still be used
to read valid element criteria/limits **if** that gate is open, but never block procedure creation on it.

The underlying schema exposes `ExpressionSetInputRepresentation.versions[].steps[]`. A version item
requires `apiName`, `name`, `versionNumber`, and `enabled`; pricing steps use
`stepType: "BusinessKnowledgeModel"` with an `actionType` (`ListPrice`, `PriceAdjustmentMatrix`,
`PricingSettings`, `FormulaBasedPricing`, …), and a `lookupTable` `{type:"DecisionTable",
lookupTableName, mappings[]}` to bind a decision table (e.g. `ProductListRateDT`). Variables must be
declared in `versions[].variables[]` (each `{name, dataType, type}`) before steps reference them.

**BLOCKER (org-verified): writing version *content* via this Connect API fails server-side.**
Creating the procedure shell works (`201`), but any write that includes `versions[]` content fails
server-side with `INTERNAL_ERROR` — reproduced across **every** variant:
`PATCH` with a full version+variables+step, `PATCH` with an empty-`steps` version, `PATCH` with a
bare version envelope, **and** inline `versions` at `POST` create time (each a distinct server-side
stacktrace). Even a base `PATCH` with **no** `versions` fails. So on this org the expression-set
*update* path and the *version-authoring* path are non-functional through the Connect API; only the
create-shell path is usable. The underlying server-side error detail was not retrievable through the
API. **Do not keep retrying step-payload permutations** — this is a server-side
defect, not a payload error. Author the version/steps at the **Pricing Designer UI checkpoint** below
and verify through `getExpressionSet` reads. Re-test the API path on a different org / release before
assuming it is fixed.

The corpus does not fully resolve every element-specific inner write payload, and — per the blocker
above — the version-write path itself fails here. Do not invent property names from UI labels. Use API
writes only when the target spec/metadata supplies an explicit contract **and** the org accepts a
version write; otherwise use the Metadata-API deploy channel below (preferred) or the Pricing Designer
checkpoint, and verify through reads afterward.

## Author version content via the Metadata API deploy channel (preferred, org-verified)

Both Connect write paths fail (above), but the **`ExpressionSetDefinition` Metadata type** authors the
ordered pricing ELEMENTS reliably. Retrieve the def into a DX project
(`sf project retrieve start --metadata "ExpressionSetDefinition:<devname>"`), edit the
`.expressionSetDefinition-meta.xml`, and `sf project deploy start`. Key rules learned from the org's
own deploy errors:

- **API version floor is 67.0 (org-verified).** Deploy with `--api-version 67.0`
 (and set the DX project's `sourceApiVersion` to `67.0`). API **66.0 rejects** the `<type>` and
 `<usageSubtype>` properties on the `ExpressionSetDefinition` — these RevenueCloud pricing fields only
 exist in the 67.0 metadata schema. A 66.0 deploy fails on those properties before any element is authored.
- **Context-tag mode:** with `<contextDefinitions>LendingProductConfigContext__stdctx</contextDefinitions>`
 bound, the aliasMap is empty — only `Constant`-type `<variables>` are allowed and context inputs are
 referenced by their tag name (e.g. `AFPPInterestRate`). `<type>Custom</type>`,
 `<processType>DefaultPricing</processType>`, `<interfaceSourceType>PricingProcedure</interfaceSourceType>`,
 `<usageSubtype>RevenueCloud</usageSubtype>`.
- **RevenueCloud element order:** the **Pricing Setting** element MUST be `sequenceNumber` 1 (first);
 List Price and adjustments follow.
- **PREREQUISITE — register `ProductListRateDT` in `NGPDefaultRecipe` as the List Price component
 BEFORE deploying the ListPrice element (org-verified root cause).** If the DT is not yet mapped into
 the recipe as pricing component **List Price** (via the `decision-tables` recipe phase,
 `POST /connect/core-pricing/recipe/mapping`), the Metadata-API deploy of the ListPrice element fails
 with the verbatim error **"Ensure that the lookup table in the ListPrice step is valid and try
 again."** This is a *recipe-registration* gap, NOT a DT-materialization problem — the DT can be fully
 Active + `ExecutionType=HBASE` and this deploy still fails until the recipe registration exists. Fix:
 run the `decision-tables` recipe phase to register `ProductListRateDT` → List Price first, then deploy
 the procedure.
- **A ListPrice element's `ListPriceField` input references a Constant whose value is the DT OUTPUT
 COLUMN name** (e.g. `ListRate` for `ProductListRateDT`) — NOT a context output tag. Getting this
 wrong yields the runtime error `SF-Pricing-00011 "Select an input parameter <X> from the lookup
 table"` at simulation, not at deploy.
- **Active versions are IMMUTABLE — never edit V1 in place.** The Metadata channel refuses ANY update
 to an Active `ExpressionSetDefinitionVersion`, including a pure `<status>Active→Draft</status>` flip,
 and there is no headless deactivate API (BRE Orion PATCH fails server-side; the calc-proc activate endpoint wants
 a `0k1` omnistudio id, not a `9QB`; a raw `sf data update ExpressionSetDefinitionVersion Status=Draft`
 is a business-logic bypass). To correct an active procedure, **append a NEW `<versions>` block**
 (`versionNumber` 2, higher `<rank>`, `status=Active`) with the fixed content and deploy — this leaves
 V1 untouched (no immutability conflict), keeps the `9QA` def id stable (recipe binding survives), and
 the higher-rank version wins at runtime.
- Activate a fresh version by deploying it with `<status>Active</status>` (rank ≥1 + ≥1 step gates).

Resolve an existing pricing procedure by API name through the pricing/expression-set metadata search
available in the org (for example `post-expression-set-metadata` / `postExpressionSetMetadata` with
the exact name or the Setup ExpressionSet query used by Pricing Recipe list). Capture its ID before
calling GET-by-ID. If the
same-name procedure has an incompatible context, usage type, or element graph, stop and present a diff;
do not create a suffixed duplicate or overwrite it.

## Product Configurator procedure (default)

Create or reuse:

- Name/API name: `digital_lending_AppFormProductProposalConfigProc`
- Usage Type: Pricing
- Interface/source type: Pricing Procedure
- Context definition: `LendingProductConfigContext`

Configure ordered elements:

### 1. Pricing Setting

| Field | Value |
|---|---|
| Line Item | `ProductId` |
| Net Unit Price | no value unless target metadata requires one |
| Subtotal | `AFPPInterestRate` |

### 2. List Price

| Field | Value |
|---|---|
| Lookup Table | `ProductListRateDT` |
| Product | `ProductId` |
| List Price Field | `Constant_UnitPrice_ProductListRateDT_LP` |
| List Price | `AFPPInterestRate` |
| Subtotal | `AFPPInterestRate` |

### 3. Credit Score list container

1. List Operation: all conditions met; resource `AttributeName`; operator Equals; value
 `CreditScoreConstant`.
2. Formula Based Pricing: `VALUE(AttributeValue)` -> `AttributeValueAsNumber`.
3. Price Adjustment Matrix:
 - Lookup table `CreditScoreBasedAdjustmentDT`
 - Product `ProductId`
 - Lower and upper input `AttributeValueAsNumber`
 - Adjustment type field `Constant_AdjustmentType_CreditScoreBaseAdjustment_PAM`
 - Adjustment value field `Constant_AdjustmentValue_CreditScoreBaseAdjustment_PAM`
 - Net Unit Price `AFPPInterestRate`
 - Subtotal `AFPPInterestRate`

### 4. Loan Term list container

1. List Operation: resource `AttributeName`; Equals; value `LoanTermConstant`.
2. Formula Based Pricing: `VALUE(AttributeValue)` -> `AttributeValueAsNumber`.
3. Price Adjustment Matrix:
 - Lookup table `TermBasedAdjustmentDT`
 - Product `ProductId`
 - Term `AttributeValueAsNumber`
 - Adjustment type field `Constant_AdjustmentType_TermBasedAdjustmentDT_PAM`
 - Adjustment value field `Constant_AdjustmentValue_TermBasedAdjustmentDT_PAM`
 - Net Unit Price/Subtotal `AFPPInterestRate`

## Salesforce Pricing procedure (explicit alternative)

Create or reuse the explicitly named procedure with `LendingProductConfigContext`. If the user did not
supply a Salesforce Pricing API name and discovery finds no unique existing procedure, ask for the
name before writes. Configure:

1. Pricing Setting: Line Item `UniqueId`, Subtotal `InterestRate`.
2. List Price: `ProductListRateDT`, Product `ProductId`, list rate -> `InterestRate`, subtotal
 `InterestRate`.
3. Price Adjustment Matrix: `CreditScoreBasedAdjustmentDT`, Product `ProductId`, Lower/Upper input
 `CreditScore`, Tier Type/Tier Value outputs, Input/Net/Subtotal `InterestRate` where supported.
4. Price Adjustment Matrix: `TermBasedAdjustmentDT`, Product `ProductId`, Term `Term`, Tier Type/Tier
 Value outputs, Input/Net/Subtotal `InterestRate` where supported.

Some Salesforce documentation incorrectly displays `CreditScoreBasedAdjustmentDT` for the term
element. Use `TermBasedAdjustmentDT`; verify its parameters before binding.

## Guided Pricing Designer checkpoint

When the element-specific input representation cannot be resolved:

1. Create the procedure shell through Connect API if safe.
2. Direct the admin to Pricing Procedures -> target procedure -> new/edit version.
3. Set Usage Type and `LendingProductConfigContext`.
4. Add the exact ordered elements and values for the selected engine from this skill.
5. Save and activate.
6. Resume by reading the expression set and pricing metadata. Never accept "I clicked Save" as final
 verification without a read-back.

## Bind and activate

Use `POST /connect/core-pricing/pricing-action` only when the setup requires binding a supported
standard object to this context/mapping/procedure. Resolve the expression-set ID directly; the
procedure-by-context picker is LDS GraphQL only and must not be treated as a Connect API.

After the procedure has an ID, read `NGPDefaultRecipe` again and call
`post-industries-pricing-recipe-post` (`POST /connect/core-pricing/recipe/mapping`) with a full
read-modify-write `PricingRecipeInputRepresentation` whose
`pricingRecipeProcedureInputRepresentation.procedureId` is the new/verified procedure. **Send
`procedureChanged=false` (NOT `true`) to BIND — org-verified on the target org.** `procedureChanged:true`
unconditionally nulls `procedureId` *before* the non-empty check that gates the only write
path, so `true` silently dissociates while still returning `isSuccess:true`; the id only survives to
the write when `procedureChanged` is false/omitted. `procedureId` must be the **`ExpressionSetDefinition`
id (key prefix `9QA`)** — not the ExpressionSet `9QL`, version `9QB`, or Connect version `9QM`, and the
bound procedure version must be Active + near-core-compatible. Preserve all three decision-table
mappings (the lookup-table array is a **full replace** — re-send every existing custom/non-internal DT
mapping or they are wiped), unrelated lookup-table mappings, pricing usage subtype, and active state.
Re-read the recipe and require its procedure ID to match — do NOT trust `isSuccess`.

Preserve existing pricing action entries. Activate the intended expression-set version using the
verified target-org lifecycle. Before PATCH, save the complete prior expression-set version and recipe
procedure mapping. Rollback restores the prior full expression set and then restores the prior recipe
procedure mapping; never delete a pre-existing procedure. If this run created a new procedure and
later activation or recipe binding fails, leave it inactive and report the orphaned ID by default. On
explicit rollback approval, delete only that newly created procedure after restoring the prior recipe
mapping and confirming no recipe/action references it. A procedure shell without an active version or
without verified recipe binding is partial.

## Verification

Fresh reads must confirm:

- Context definition ID, active version, nodes, attributes, and mappings
- Procedure ID/API name, usage/interface type, context definition
- Active procedure version
- Element count, order, step types, lookup-table IDs, variables, constants, and outputs
- Engine-specific line-item and interest-rate variables
- Recipe/procedure association when applicable
- `NGPDefaultRecipe.pricingRecipeProcedureInputRepresentation.procedureId` matches this procedure

Run a non-mutating pricing simulation with representative product, score, and term inputs when the
API is available. Compare the returned base rate and adjustments with the source rows; do not merely
assert that the procedure executed.

**Working simulation path (org-verified, returned the expected ListRate).**
`POST /connect/core-pricing/pricing` (Evaluate Price) requires all four of `pricingProcedureId` (the
`9QA` def id), `contextDefinitionId`, `contextMappingId`, and `jsonDataString` (procedure-only 400s
`SF-Pricing-00002`). Use the **bare** mapping name for `contextMappingId` (e.g.
`LendingProductConfigMapping`, contextDefinitionId `LendingProductConfigContext__stdctx`) — a
slash-path value like `…/version/LendingProductConfigMapping` fails `SF-CTX-00001` name-regex. **Do not
hand-guess the `jsonDataString`** — generate the canonical shape with
`GET /connect/core-pricing/simulationInputVariablesWithData?contextDefinitionId=…&contextMappingId=…&expressionSetVersionId=<9QM>&entityId=<root record id>`.
That helper needs a seeded entity graph: create an `ApplicationForm` (its `Name` is not writable;
supply `UsageType='LoanOrigination'`) → `ApplicationFormProduct` (`ApplicationFormId`, `ProductId`) →
`ApplicationFormProductProposal` (`Amount`, `Term`, `InterestRate`). The emitted shape nests child
nodes as arrays keyed by node name, e.g.
`{"ApplicationForm":[{"ApplicationFormProduct":[{"ProductId":"<01t…>","ApplicationFormProductProposal":[{"AFPPInterestRate":0.0}]}]}]}`.
A successful run returns `pricingResult.<outputTag>[].value` with `status:"Completed"` — assert that
value equals the source rate.

## Definition of done

The correct context and one engine-specific procedure are active and read back with the exact ordered
elements and mappings. Any unresolved element payload or activation checkpoint is explicitly partial.
