---
name: fsc-digital-origination-product-setup-coordinate
description: "Guided admin setup of the product-catalog data slice of Financial Services Cloud (FSC) Digital Lending — permission-set assignment, catalog + category/subcategory creation, Home Loan product creation, LoanTerm picklist values, MinLoanAmount / MaxLoanAmount / LoanTerm / OfferValidPeriod / OmniScriptName attribute definitions, Home Loans product classification with attribute assignment and default values, product-to- classification binding, and product-to-category assignment. Triggers on \"set up digital lending product catalog\", \"create digital lending catalog\", \"configure digital lending products\", \"create home loan product in FSC\", \"assign product classification for lending\", \"configure loan term attributes\", \"set up loan origination products\". This SKILL is the product-catalog slice only — initial setup (Discovery Framework + KYC + Digital Origination + Import/Export + Sample Templates + Manage User Access) is a prereq slice owned by the sibling digital-origination-initial-setup child."
metadata:
  version: "1.0"
---

# digital-origination-product-setup

Guide admin through product-catalog data creation for FSC Digital Lending: catalog,
categories/subcategories, Home Loan product, LoanTerm picklist, five product
attributes, Home Loans product classification with attributes + defaults, and
category/classification assignments — in strict order the Salesforce Help doc prescribes.

Source: [Create Catalogs and Products for Digital Lending](https://help.salesforce.com/s/articleView?id=ind.fsc_lending_catalogs_products.htm&type=5)
(13 child articles). Every field name, default value, and step below is verbatim from that
doc.

## Scope & definition of done — READ THIS FIRST

**This SKILL is one slice of a larger Digital Lending setup journey.** Slices:

1. **Prereq slice — initial setup** (Discovery Framework, Know Your Customer, Digital Origination feature, Import or Export, Sample Templates, Manage User Access). Owned by sibling child: [`../digital-origination-initial-setup/SKILL.md`](../digital-origination-initial-setup/SKILL.md). MUST be complete before this SKILL runs.
2. **THIS SKILL — product-catalog setup** (Acts 1–5 below).
3. **Future slices** — data-mapper wiring, CPQ Fetch API integration, FlexCard config, pricing-engine wiring, GitHub sample-data loader path. Not covered here.

**"Set up Digital Lending product catalog" / "Configure Digital Lending products" with no
narrowing qualifier means running Acts 1–5 end-to-end.** Reporting done after just the
catalog is a defect. "Out of scope" notes are NOT stop signals — call them out, then
finish every non-blocked step.

**End state.** Home Loan product visible on Product List FlexCard with LoanTerm /
MinLoanAmount / MaxLoanAmount / OmniScriptName / OfferValidPeriod attributes populated,
Based On = Home Loans classification, assigned to Home Loans category. Classification
holds the five attributes with defaults MinLoanAmount=1000, MaxLoanAmount=100000,
OmniScriptName=ApplicantIntakeSecured (Home Loan is a secured product; use ApplicantIntake
for an unsecured loan), OfferValidPeriod=30.

## Mandatory pre-write plan — state this before your FIRST write

Before touching the org, restate to the admin:

1. Target org alias (confirm).
2. Prereq check — initial setup complete? Delegate to sibling initial-setup child if not.
3. Perm-set check — which of the three required perm sets (DL, PCM Designer, PCM Viewer) are already assigned vs missing.
4. Which acts you'll run (default: all 5). Route narrower asks per Entry Point table below.
5. Split-deploy plan — one act at a time; re-read after each write; ground final report in Tooling reads.

Do NOT proceed until the admin confirms.

## Supported utterances

- "Set up Digital Lending product catalog" / "Configure Digital Lending products"
- "Create Digital Lending catalog and products"
- "Create home loan product for Digital Lending"
- "Assign product classification for lending"
- "Configure loan term picklist / attributes for Digital Lending"
- "Set up loan origination products in FSC"

## Session state (track across the conversation)

- `target_org_alias` — org being configured; confirmed before any write.
- `prereq_initial_setup_verified` — did sibling initial-setup child's Definition of done pass.
- `perm_sets_missing` — surfaced to admin; nothing assigned until confirmed.
- `catalog_name`, `catalog_code`, `catalog_effective_start`, `catalog_effective_end`.
- `category_names` — categories/subcategories (help-doc example: Home Loans).
- `product_names` — products created (help-doc example: Home Loan).
- `picklist_values_created` — LoanTerm 180/240/360 Months.
- `attribute_defs_created` — MinLoanAmount, LoanTerm, MaxLoanAmount, OfferValidPeriod, OmniScriptName.
- `classification_name` — e.g. Home Loans.
- `classification_defaults_set` — MinLoanAmount=1000, MaxLoanAmount=100000, OmniScriptName=ApplicantIntake|ApplicantIntakeSecured, OfferValidPeriod=30.
- `product_based_on_set`, `product_assigned_to_category`.
- `considerations_surfaced` — Act 5 items acknowledged.

## Entry point — route on the admin's actual ask

| Admin ask signal | Where to start | What to run |
|---|---|---|
| "Set up Digital Lending product catalog" (unqualified) | Act 1 | Acts 1–5 in order |
| "I already have perms — start with the catalog" | Act 2 | Verify Act 1 gate, then Acts 2–5 |
| "Just create the catalog and categories" | Act 2 | Act 2 only; note remaining acts blocked |
| "Create the Home Loan product and its attributes" | Act 3 | Verify Acts 1–2 gate, then Act 3 |
| "Just define the attributes / picklist" | [`source/skills/act3-product-and-attributes/SKILL.md`](source/skills/act3-product-and-attributes/SKILL.md) | Act 3 sub-steps only |
| "Set up the Home Loans product classification" | Act 4 | Verify Acts 1–3 gate, then Act 4 |
| "Considerations / limits for DL catalog" | Act 5 | Read-only summary from [`source/references/considerations-and-limits.md`](source/references/considerations-and-limits.md) |
| "Configure secured loan product (auto/home)" | Act 4 | Same as unsecured, but OmniScriptName default = ApplicantIntakeSecured |

## Prerequisites

### A. External — validate only (do not attempt to fix)

- **Edition:** Lightning Experience — Professional, Enterprise, or Unlimited.
- **License:** Financial Services Cloud with Digital Lending entitlement.
- **Admin access** to the org.
- **Initial setup complete** — delegate to [`../digital-origination-initial-setup/SKILL.md`](../digital-origination-initial-setup/SKILL.md). If any Step (Discovery Framework, KYC, Digital Origination, Import/Export, Sample Templates, Manage User Access) is missing, STOP and route the admin to that SKILL first.

### B. Automatable — permission sets (Act 1)

See [`source/references/permission-sets.md`](source/references/permission-sets.md) for the full matrix.

**Policy: check → report → confirm → THEN assign. Never auto-assign.** Present the missing
list with what each perm set unlocks. Assign only the ones the admin confirms.
`DUPLICATE_VALUE` on assignment = already assigned = success, not an error.

## Transport & deploy discipline

1. **Dispatcher fallback.** Prefer typed APIs. When missing, fall back to `dispatch` with the raw route.
2. **Dry-run first.** For every write, state the operationId + payload before invoking.
3. **Split deploy per act.** One act at a time. Do not batch across acts.
4. **Re-read verify.** After each write, re-read the record via Tooling / Query and confirm.
5. **Ground final report in reads.** Never claim done from write success alone — read back.
6. **Config ≠ data.** PCM records (catalog, category, product, picklist, attribute, classification) are DATA, not metadata. Do NOT MDAPI-deploy them. Use the PCM REST/Query APIs.

## Setup journey — 5 acts

Each act delegates to a sub-skill under [`source/skills/`](source/skills/). Sub-skills hold
verbatim help-doc steps.

---

### Act 1 — Permissions

Assign Product Catalog Management Designer + Digital Lending + PCM Viewer perm sets to
the users who configure Digital Lending.

Delegate: [`source/skills/act1-permissions/SKILL.md`](source/skills/act1-permissions/SKILL.md)

**End state.** All required perm sets assigned to the admin + any additional users the
admin identifies.

---

### Act 2 — Catalog + Categories/Subcategories

Create the Digital Lending catalog (Sales type, effective dates, unique code). Under it,
create the Home Loans category. Optionally create subcategories.

Delegate: [`source/skills/act2-catalog-and-categories/SKILL.md`](source/skills/act2-catalog-and-categories/SKILL.md)

**End state.** Catalog exists with name / description / unique code / effective start-end /
type=Sales. At least one category (e.g. Home Loans) exists under the catalog.

---

### Act 3 — Product + Attribute Picklist + Attribute Definitions

Create the Home Loan product. Populate the LoanTerm attribute picklist (180 Months / 240
Months / 360 Months). Define the five product attributes: MinLoanAmount, LoanTerm,
MaxLoanAmount, OfferValidPeriod, OmniScriptName.

Delegate: [`source/skills/act3-product-and-attributes/SKILL.md`](source/skills/act3-product-and-attributes/SKILL.md)

**End state.** Home Loan product exists. LoanTerm picklist has three values. Five
attribute definitions exist. See [`source/references/attributes-and-defaults.md`](source/references/attributes-and-defaults.md)
for field-by-field detail.

---

### Act 4 — Classification + Assignment

Create the Home Loans product classification. Assign the five attributes and set
defaults (MinLoanAmount=1000, MaxLoanAmount=100000, OmniScriptName=ApplicantIntakeSecured
for the secured Home Loan — ApplicantIntake for an unsecured loan, OfferValidPeriod=30). Set the Home Loan
product's Based On = Home Loans. Assign the product to the Home Loans category.

Delegate: [`source/skills/act4-classification-and-assignment/SKILL.md`](source/skills/act4-classification-and-assignment/SKILL.md)

**End state.** Classification exists with five attributes + defaults. Product's Based On
points to classification. Product appears under Home Loans category.

---

### Act 5 — Considerations & limits

Surface the Salesforce Help considerations to the admin. Not a write step — an alignment
step. Especially: 100-product FlexCard cap, no pagination, name/image/description dynamic
from product, MinLoanAmount/MaxLoanAmount type=currency, LoanTerm=picklist in months,
DigitalLendingTransFormProductInfo Data Mapper Transform must be updated if custom
attributes are added beyond the five.

Delegate: [`source/skills/act5-considerations/SKILL.md`](source/skills/act5-considerations/SKILL.md)
Reference: [`source/references/considerations-and-limits.md`](source/references/considerations-and-limits.md)

**End state.** Admin has acknowledged each consideration.

---

## Definition of done (the whole skill)

- Prereq initial setup verified via sibling initial-setup child.
- Perm sets confirmed + assigned (Act 1).
- Catalog + at least one category exist (Act 2).
- Home Loan product + LoanTerm picklist (180/240/360) + five attribute definitions exist (Act 3).
- Home Loans classification exists with five attributes + defaults set correctly for secured vs unsecured (Act 4).
- Product Based On = Home Loans, product assigned to Home Loans category (Act 4).
- Considerations surfaced (Act 5).
- Final report grounded in Tooling reads, not just write responses.

## Out of scope / deferred

- **Initial setup** — prereq slice owned by sibling child ([`../digital-origination-initial-setup/SKILL.md`](../digital-origination-initial-setup/SKILL.md)).
- **DigitalLendingTransFormProductInfo Data Mapper Transform** updates for custom attributes — referenced (Act 5) but not covered.
- **CPQ Fetch product detail API integration**, Product List Page FlexCard, pricing-engine wiring.
- **GitHub sample-data loader path** — alternate to hand-creating records.
- **Other loan-product variants** beyond flagging OmniScriptName=ApplicantIntakeSecured.

## Companion references

- Prereq initial-setup child: [`../digital-origination-initial-setup/SKILL.md`](../digital-origination-initial-setup/SKILL.md)
- Salesforce Help parent: [Create Catalogs and Products for Digital Lending](https://help.salesforce.com/s/articleView?id=ind.fsc_lending_catalogs_products.htm&type=5)
- Salesforce Help: Product Catalog Management
- Salesforce Help: Product Classifications
- Salesforce Help: Dynamic Attributes
- Salesforce Help: OmniScripts
- Internal architecture: [`source/PLAN.md`](source/PLAN.md)

<!-- skill-validate: ignore-start -->
<!-- codey:operations start -->
## Operations Reference

Operations this skill uses — routing and dependency reference.

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `act1-query-permsets` | read | — | `GET /services/data/v63.0/query` | — |
| `act1-query-existing-assignments` | read | — | `GET /services/data/v63.0/query` | `act1-query-permsets` |
| `act1-assign-permset` | write | — | `POST /services/data/v63.0/sobjects/PermissionSetAssignment` | `act1-query-existing-assignments` |
| `act2-create-catalog` | write | — | `POST /services/data/v63.0/sobjects/ProductCatalog` | — |
| `act2-create-category` | write | — | `POST /services/data/v63.0/sobjects/ProductCategory` | `act2-create-catalog` |
| `act2-create-subcategory` | write | — | `POST /services/data/v63.0/sobjects/ProductCategory` | `act2-create-category` |
| `act3-create-product` | write | — | `POST /services/data/v63.0/sobjects/Product2` | — |
| `act3-create-picklist` | write | — | `POST /services/data/v63.0/sobjects/AttributePicklist` | — |
| `act3-create-picklist-value` | write | — | `POST /services/data/v63.0/sobjects/AttributePicklistValue` | `act3-create-picklist` |
| `act3-activate-picklist` | write | — | `PATCH /services/data/v63.0/sobjects/AttributePicklist/{Id}` | `act3-create-picklist-value` |
| `act3-create-attribute-def` | write | — | `POST /services/data/v63.0/sobjects/AttributeDefinition` | `act3-activate-picklist` |
| `act3-activate-attribute-def` | write | — | `PATCH /services/data/v63.0/sobjects/AttributeDefinition/{Id}` | `act3-create-attribute-def` |
| `act4-create-classification` | write | — | `POST /services/data/v63.0/sobjects/ProductClassification` | — |
| `act4-activate-classification` | write | — | `PATCH /services/data/v63.0/sobjects/ProductClassification/{Id}` | `act4-create-classification` |
| `act4-assign-attr-to-classification` | write | — | `POST /services/data/v63.0/sobjects/ProductClassificationAttr` | `act4-activate-classification`, `act3-activate-attribute-def` |
| `act4-bind-product-basedon` | write | — | `PATCH /services/data/v63.0/sobjects/Product2/{Id}` | `act3-create-product`, `act4-activate-classification` |
| `act4-assign-product-to-category` | write | — | `POST /services/data/v63.0/sobjects/ProductCategoryProduct` | `act3-create-product`, `act2-create-category` |
| `delegate-digital-origination-product-setup-act1-permissions` | delegate | — | → `fsc-mandalorians/digital-origination-product-setup-act1-permissions` | — |
| `delegate-digital-origination-product-setup-act2-catalog-and-categories` | delegate | — | → `fsc-mandalorians/digital-origination-product-setup-act2-catalog-and-categories` | — |
| `delegate-digital-origination-product-setup-act3-product-and-attributes` | delegate | — | → `fsc-mandalorians/digital-origination-product-setup-act3-product-and-attributes` | — |
| `delegate-digital-origination-product-setup-act4-classification-and-assignment` | delegate | — | → `fsc-mandalorians/digital-origination-product-setup-act4-classification-and-assignment` | — |
| `delegate-digital-origination-product-setup-act5-considerations` | delegate | — | → `fsc-mandalorians/digital-origination-product-setup-act5-considerations` | — |
<!-- codey:operations end -->
<!-- skill-validate: ignore-end -->
