---
name: fsc-product-act3-attributes-create
description: "Sub-skill of digital-origination-product-setup. Act 3 — create the Home Loan product, populate the LoanTerm attribute picklist (180/240/360 Months), and define the five product attributes: MinLoanAmount, LoanTerm, MaxLoanAmount, OfferValidPeriod, OmniScriptName."
metadata:
  version: "1.0"
  cliTools:
  - tool:
    - "sf"
    semver: ">=2.0.0"
---

# Act 3 — Product + Attribute Picklist + Attribute Definitions

Sources:
- [Create a Product for Digital Lending](https://help.salesforce.com/s/articleView?id=ind.fsc_lending_catalogs_products_product.htm&type=5)
- [Create Loan Term Attribute Picklists for Digital Lending](https://help.salesforce.com/s/articleView?id=ind.fsc_lending_catalogs_products_loan_term_picklist.htm&type=5)
- [Define and Update Product Attributes for Digital Lending](https://help.salesforce.com/s/articleView?id=ind.fsc_lending_catalogs_products_define_attributes.htm&type=5)
- [Create Offer Validity Attribute for Digital Lending](https://help.salesforce.com/s/articleView?id=ind.fsc_lending_catalogs_products_offer_attribute.htm&type=5)
- [Create Omniscript Name Attribute for Digital Lending](https://help.salesforce.com/s/articleView?id=ind.fsc_lending_catalogs_products_omniscipt_name_attribute.htm&type=5)

## Purpose

Create the Home Loan product record. Populate the loan-term picklist. Define the five
product-attribute definitions needed by the Home Loans classification (Act 4).

## Prereq gate

- Acts 1 + 2 complete.

## Ordering (within this act)

1. Product record.
2. LoanTerm picklist (parent `AttributePicklist`) + its picklist values (`AttributePicklistValue`) — MUST exist before the LoanTerm attribute definition (the attribute references the picklist by `PicklistId`).
3. Attribute definitions: MinLoanAmount, LoanTerm, MaxLoanAmount, OfferValidPeriod, OmniScriptName.
4. **Activate every attribute definition (`IsActive = true`) BEFORE proceeding to Act 4.** `ProductClassificationAttr` rejects inactive attributes with `INVALID_INPUT: You can associate only active attributes with a product classification.` (Org-verified 2026-07-29.)

For the field-by-field attribute table, see
[`../../references/attributes-and-defaults.md`](../../references/attributes-and-defaults.md).

## Schema — required fields (org-verified 2026-07-29)

| Object | Required fields (createable, non-defaulted, non-nillable) |
|---|---|
| `Product2` | `Name` |
| `AttributePicklist` | `Name` (Status enum: Draft/Active/Inactive; DataType enum: Boolean/Date/Datetime/Number/Text/Currency/Percent) |
| `AttributePicklistValue` | `Name`, `PicklistId`, `Code`, `Value` |
| `AttributeDefinition` | `Name`, `Code`, `DataType`, `Label` (org-verified required set; `Code` is the unique API-name token the UI labels "API Name"). **Do NOT send `Status`** — this entity has no `Status` column (`400 INVALID_FIELD`). Activate separately via **`IsActive` (boolean)**, which defaults to `false` on create. |

## Step 1 — Create the product

Help-doc summary: Products are all the items and services you sell. Products can also be
non-sellable. Two types: **simple** (no associated product hierarchy) and **bundled** (a
group sold as one unit).

**Steps.**

1. From the App Launcher select **Product Catalog Management**, then click **Products**.
2. From the product list view, click **New**.
3. Create a product. For example, **Home Loan**.
4. Save.

**Verify.** Query the created record.

Repeat for additional products as the admin requires.

## Step 2 — Create LoanTerm picklist values

Help-doc summary: Create loan term picklist values of 180 Months, 240 Months, 360 Months. A
picklist represents all possible values for an attribute when the attribute has multiple
values. **You must define picklists before creating picklist attributes.**

**Steps.**

1. From the App Launcher select **Product Catalog Management**, then click **Attribute Picklists**.
2. On the Attribute Picklists list view, select **All Attribute Picklists**.
3. Click **Loan Term**.
4. Click the **Related** tab. In the Attribute Picklist Values section, click **New**.
5. Create the 180 Months value:

   | Field | Value |
   |---|---|
   | Picklist | LoanTerm |
   | Name | 180 Months |
   | Status | Active |
   | Display Value | 180 Months |
   | Sequence | 1 |

   Click **Save & New**.
6. Create the 240 Months value:

   | Field | Value |
   |---|---|
   | Picklist | LoanTerm |
   | Name | 240 Months |
   | Status | Active |
   | Display Value | 240 Months |
   | Sequence | 1 |

   Click **Save & New**.
7. Create the 360 Months value:

   | Field | Value |
   |---|---|
   | Picklist | LoanTerm |
   | Name | 360 Months |
   | Status | Active |
   | Display Value | 360 Months |
   | Sequence | 1 |

   Click **Save**.

**Verify.** Query picklist values under the LoanTerm picklist; confirm three active rows.

## Step 3 — Define MinLoanAmount, LoanTerm, MaxLoanAmount attributes

Help-doc summary: Attributes capture properties of products. Define name, label, and data
type when creating.

**Steps.**

1. From the App Launcher select **Product Catalog Management**, then click **Attribute Definitions**.
2. From the Attribute Definitions list view, click **New**.
3. Create MinLoanAmount:

   | Field | Value |
   |---|---|
   | Name | MinLoanAmount |
   | Label | Minimum Loan Amount |
   | API Name | MinLoanAmount |
   | Data Type | Number |
   | Description | Minimum loan amount. |

   Click **Save & New**.
4. Create LoanTerm:

   | Field | Value |
   |---|---|
   | Name | LoanTerm |
   | Label | Loan Term |
   | API Name | LoanTerm |
   | Data Type | Picklist |
   | Picklist | LoanTerm |
   | Description | Loan term. |
   | Active | Select |

   Click **Save & New**.
5. Create MaxLoanAmount:

   | Field | Value |
   |---|---|
   | Name | MaxLoanAmount |
   | Label | Maximum Loan Amount |
   | API Name | MaxLoanAmount |
   | Data Type | Number |
   | Description | Maximum loan amount. |
   | Active | Select |

   Click **Save**.

**Note (Article 14 considerations).** MinLoanAmount and MaxLoanAmount are described as
Type **currency** in the sample-data considerations. Help-doc Article 6 lists them as
Data Type = Number. Follow the help-doc step above unless the admin's org uses the
Agentforce Financial Services sample data, in which case use currency to match the
sample-data expectations.

## Step 4 — Create OfferValidPeriod attribute

Help-doc summary: Use OfferValidPeriod to configure the validity in days for an offer
generated for a product. When configured, the pricing engine uses OfferValidPeriod and
populates the offer's valid start date and end date.

**Steps.**

1. From the App Launcher select **Product Catalog Management**, then click **Attribute Definitions**.
2. Click **New**.
3. Enter:

   | Field | Value |
   |---|---|
   | Name | OfferValidPeriod |
   | Label | Offer Valid Period |
   | API Name | OfferValidPeriod |
   | Data Type | Number |
   | Description | Offer Valid Period |
4. Save.

## Step 5 — Create OmniScriptName attribute

Help-doc summary: Use OmniScriptName to configure the loan intake process.

**Steps.**

1. From the App Launcher select **Product Catalog Management**, then click **Attribute Definitions**.
2. Click **New**.
3. Enter:

   | Field | Value |
   |---|---|
   | Name | OmniScriptName |
   | Label | OmniScript Name |
   | API Name | OmniScriptName |
   | Data Type | Text |
   | Description | Stores the name of the Omniscript that launches the applicant intake experience. |
4. Save.

**⚠️ Do NOT set the attribute-level `DefaultValue` at create time (org-verified
2026-07-29).** Help Article 8 lists
`DigitalLending_DFApplicantIntakeSecured_English` as the attribute-level default, but the
classification-level `ProductClassificationAttr.DefaultValue` set in Act 4 Step 3 is
silently **overridden** by the attribute-level default at PCA-insert time — the stored PCA
value becomes the AttributeDefinition-level value regardless of what the PCA insert
passes. Skip the attribute-level default here and let Act 4 own the per-classification
default (`ApplicantIntake` for unsecured, `ApplicantIntakeSecured` for secured). If a
legacy org already has the attribute-level default set, either clear
`AttributeDefinition.DefaultValue` before Act 4 or issue an explicit `UPDATE
ProductClassificationAttr SET DefaultValue = <secured|unsecured value>` after each PCA
insert.

## Activation step (mandatory before Act 4)

After all five attribute definitions are created, set `IsActive = true` on each:

```text
UPDATE AttributeDefinition
   SET IsActive = true
 WHERE Id IN (<the five ids>)
```

Or via `sf data update record --sobject AttributeDefinition --record-id <id> --values "IsActive=true"`.

**Verify** by re-querying: every attribute must show `IsActive = true` before Act 4
begins. Skipping this step causes Act 4 Step 2 (`ProductClassificationAttr` insert) to
fail with `INVALID_INPUT: You can associate only active attributes with a product
classification.`

## End state

- Home Loan product record exists (or the admin's chosen product name).
- LoanTerm `AttributePicklist` exists (parent record) with three active `AttributePicklistValue` rows: 180 Months / 240 Months / 360 Months. Each value carries `Code`, `Value`, `DisplayValue`.
- Five attribute definitions exist: MinLoanAmount, LoanTerm, MaxLoanAmount, OfferValidPeriod, OmniScriptName — with the field values above.
- **All five attribute definitions have `IsActive = true`.** This is the Act 4 prereq.

## See also

- Salesforce Help: Product
- Salesforce Help: Picklists; Create Picklists
- Salesforce Help: Dynamic Attributes; Create Attributes
- Salesforce Help: OmniScripts
- [`../../references/attributes-and-defaults.md`](../../references/attributes-and-defaults.md) — consolidated attribute field/default table
