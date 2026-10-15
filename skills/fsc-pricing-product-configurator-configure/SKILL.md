---
name: fsc-pricing-product-configurator-configure
parent: "digital-origination-pricing-setup"
purpose: "Configure Product Configurator attributes for the default lending pricing engine."
description: "Configure the Product Configurator prerequisites for Digital Lending pricing by resolving Loan Term, Credit Score, and Loan Amount attributes on the target lending product classification, creating the Credit Score and Loan Amount base attribute definitions headlessly when they are missing (they are net-new to this sibling — the product-setup sibling creates the other five), assigning them to the classification, setting the required Is Price Impacting and Is Hidden flags, and verifying the resulting product-attribute state. Uses Enterprise Product Catalog reads and verified sObject writes (AttributeDefinition + ProductClassificationAttr); the Connect API exposes isPriceImpacting/isHidden as read-only outputs, so the flags are written by sObject PATCH after a describe-verify, with a Product Catalog Management UI checkpoint only as a last resort."
metadata:
  version: "1.0"
---

# Digital Origination Product Configurator pricing prerequisites

Configure the three price-driving attributes required by the default Digital Lending Product
Configurator path. This sibling does not create decision tables or pricing procedures.

## Inputs and prerequisites

- Target-org alias
- Exact product-classification ID and lending product IDs
- Product Catalog Management already complete
- Product Catalog Management Designer access verified

Resolve attributes by record ID and API name. Do not change a similarly labeled attribute on another
classification.

## Required final state

| Attribute | Data type | Is Price Impacting | Is Hidden |
|---|---|---|---|
| Loan Term | Existing supported type, normally picklist/text-backed | true | preserve current value |
| Credit Score | Number | true | true |
| Loan Amount | Currency | true | preserve current value |

Supported documentation examples include Number for Credit Score, text-backed Picklist for Loan Term,
and Currency for loan/down-payment values. Validate the actual procedure and target release.

## Reusable EPC reads

Use approved SOR
`connect-api/cme-core-shasta/industries-epc-connect-api__sfdc.industries.epc.connect.api_oas_67.0`:

- `get-product-attributes` (`getProductAttributes`) - `GET /connect/pcm/product/{productId}/attributes`
- `post-product-classification-list` - resolve classifications
- `post-product-classification-details` - read classification details
- `get-categories` / `get-category-details` - verify catalog/category relationships
- `post-product-attribute-definition` (`postProductAttributeDefinition`) - creates a
  product-attribute-definition assignment from an
  existing `attributeDefinitionId`; it does not create the base Attribute Definition.

The Connect input representation for `postProductAttributeDefinition` does not contain
`isPriceImpacting` or `isHidden`. Across the current corpus those fields are outputs/read filters, not
typed writes.

## Step 1 - Resolve existing definitions and assignments

1. Read the target classification and products.
2. Read product attributes; capture AttributeDefinition, ProductClassificationAttribute, and
   ProductAttributeDefinition IDs/API names plus data type and current flags.
3. Reuse exact Loan Term, Credit Score, and Loan Amount attributes.
4. If **Loan Term** is missing, it belongs to the product-setup sibling (Act 3) — report it as an
   upstream gap and continue. If **Credit Score** or **Loan Amount** is missing, this sibling OWNS
   creating them (they are net-new here, NOT part of Act 3's five) — go straight to Step 2 and create
   them headlessly. **Do NOT stop to ask** — creation is the expected path on a fresh org, and a run
   that leaves them uncreated is incomplete, not "done pending approval."

## Step 2 - Create the missing base attribute (headless, deterministic)

Base definitions this sibling creates when absent (net-new to this sibling — the product-setup Act 3
sibling creates the other five with the identical contract):

| Attribute | Label | API name (`Code`) | `DataType` |
|---|---|---|---|
| Credit Score | Credit Score | `CreditScore` | Number |
| Loan Amount | Loan Amount | `LoanAmount` | Currency |

The help article contains a typo `CreaditScore` in one Name field; do not reproduce it — the API name is
`CreditScore`.

There is no typed Connect operation to create the base AttributeDefinition, but the **direct sObject REST
path is proven** (identical to the product-setup Act 3 contract). Create each missing attribute, then
activate and assign it:

1. **Create the base `AttributeDefinition`** — `POST /services/data/vXX.0/sobjects/AttributeDefinition`
   with the four required fields **`Name`, `Code`, `DataType`, `Label`** (org-verified): Credit Score →
   `{Name:"CreditScore", Code:"CreditScore", Label:"Credit Score", DataType:"Number"}`; Loan Amount →
   `{Name:"LoanAmount", Code:"LoanAmount", Label:"Loan Amount", DataType:"Currency"}`. **Do NOT send a
   `Status` field** — `AttributeDefinition` has no `Status` column (`400 INVALID_FIELD`). It is created
   `IsActive=false`.
2. **Activate it** — `PATCH /sobjects/AttributeDefinition/<id> {"IsActive": true}` (the activation field
   is `IsActive`, NOT `Status`). This MUST precede the classification assignment: `ProductClassificationAttr`
   rejects an inactive attribute with `INVALID_INPUT: You can associate only active attributes with a
   product classification.`
3. **Assign it to the target classification** — POST a **`ProductClassificationAttr`** junction with the
   required `Name`, `ProductClassificationId` (the lending classification), and `AttributeDefinitionId`
   (the active attribute). This is the same junction the product-setup Act 4 `assign-attr-to-classification`
   step writes, and it is the record that carries the Step 3 pricing flags (`IsPriceImpacting` /
   `IsHidden`).
4. When the per-product assignment input IDs are known, `postProductAttributeDefinition`
   (`POST /connect/pcm/product-attribute-definitions`) records the product-level assignment.

Verify each create/activate/assign with a fresh read before moving on. Fall back to a guided PCM
checkpoint only if the target org actually rejects these sObject writes.

## Step 3 - Set pricing flags

The `isPriceImpacting` / `isHidden` flags surface on the **`ProductClassificationAttr`** junction
(fields `IsPriceImpacting` / `IsHidden`). The Connect API exposes them as READ-ONLY outputs
(`getProductAttributes`; the `postProductAttributeDefinition` input carries no such fields), so the write
is a **standard sObject PATCH on `ProductClassificationAttr`** — attempt this headless path FIRST, with
the PCM UI only as a last-resort fallback.

Write order:

1. Resolve the exact `ProductClassificationAttr` record for each attribute on the target classification,
   and **describe it to confirm `IsPriceImpacting` / `IsHidden` are `updateable`** (guards against a
   release where they are calculated/read-only).
2. If updateable, PATCH each junction record, preserving unrelated fields:
   - Loan Term: `IsPriceImpacting = true`.
   - Credit Score: `IsPriceImpacting = true`, `IsHidden = true`.
   - Loan Amount: `IsPriceImpacting = true`.
3. Only if the describe shows the fields are NOT updateable on this org/release, use the PCM UI
   checkpoint as a fallback: Product Catalog Management -> Product Classification -> target classification
   -> Attributes -> edit attribute -> set the same flags -> Save.
4. Re-read all three with `get-product-attributes` and confirm the flags match the required final state.

Credit Score is hidden because the applicant must not enter it; the Digital Lending configurator
retrieves it from the party credit profile.

## Idempotency and safety

- Skip writes when the flags already match.
- Never clear an existing Hidden flag on Loan Term or Loan Amount without an explicit request.
- Do not create duplicate attribute definitions or suffixed API names automatically.
- Do not assign the attribute to unrelated products or classifications.
- If record-level writes are not in an approved SOR, label them as standard sObject fallback and
  verify updateability before execution.

## Output contract

Return classification ID, product IDs, attribute-definition and assignment IDs, actual API names,
data types, previous flags, action path (API or UI), and verified final flags. Pass this result to
nested `pricing-procedure` for the Product Configurator branch.

## Definition of done

The target classification exposes Loan Term, Credit Score, and Loan Amount as **active** attributes with
the required Is Price Impacting / Is Hidden flags, all confirmed through fresh reads. On a fresh org that
means Credit Score and Loan Amount were CREATED (base `AttributeDefinition` + activation + classification
assignment) and every flag was set — a run that stops without creating a missing Credit Score / Loan
Amount attribute is INCOMPLETE, not "partial by design." A UI fallback is acceptable only if the target
org's describe proved the flag fields non-updateable.
