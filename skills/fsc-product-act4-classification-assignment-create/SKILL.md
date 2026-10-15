---
name: fsc-product-act4-classification-assignment-create
description: "Sub-skill of digital-origination-product-setup. Act 4 — create the Home Loans product classification, assign the five attributes to it, set default values (MinLoanAmount=1000, MaxLoanAmount=100000, OmniScriptName=ApplicantIntake or ApplicantIntakeSecured, OfferValidPeriod=30), point the Home Loan product's Based On field to the classification, and assign the product to the Home Loans category."
metadata:
  version: "1.0"
---

# Act 4 — Classification + Assignment

Sources:
- [Create Personal Loans Product Classification for Digital Lending](https://help.salesforce.com/s/articleView?id=ind.fsc_lending_catalogs_products_classifications.htm&type=5)
- [Assign and Edit Attributes in the Personal Loans Product Classification for Digital Lending](https://help.salesforce.com/s/articleView?id=ind.fsc_lending_catalogs_products_edit_attributes.htm&type=5)
- [Add Product Classification to Personal Loan Product for Digital Lending](https://help.salesforce.com/s/articleView?id=ind.fsc_lending_catalogs_products_classification_loan.htm&type=5)
- [Assign Products to Catalog Categories for Digital Lending](https://help.salesforce.com/s/articleView?id=ind.fsc_lending_catalogs_products_assign_categories.htm&type=5)

## Purpose

Tie together the pieces built in Acts 2 + 3: create the classification, attach the
attributes with defaults, point the product at the classification, and assign the product
to a category.

## Prereq gate

- Acts 1, 2, 3 complete.
- Five attribute definitions exist (Act 3): MinLoanAmount, LoanTerm, MaxLoanAmount, OfferValidPeriod, OmniScriptName.
- **All five attribute definitions have `IsActive = true`.** `ProductClassificationAttr` inserts fail with `INVALID_INPUT: You can associate only active attributes with a product classification.` otherwise. Verify with `SELECT Name, IsActive FROM AttributeDefinition` before running Step 2. Org-verified 2026-07-29.
- Home Loan product exists (Act 3).
- Home Loans category exists (Act 2).

## Schema — required fields (org-verified 2026-07-29)

| Object | Required fields (createable, non-defaulted, non-nillable) | Notes |
|---|---|---|
| `ProductClassification` | `Name`, `Code` | Status enum: Draft/Active/Inactive. Default is Draft. Set to Active on create. |
| `ProductClassificationAttr` | `Name`, `ProductClassificationId`, `AttributeDefinitionId` | Also creatable: `AttributeCategoryId`, `IsHidden`, `IsRequired`, `Status`, `Sequence` (**int**), `DefaultValue`, `IsPriceImpacting`. Referenced `AttributeDefinition.IsActive` MUST be true. |
| `Product2` — `BasedOnId` | reference, updateable | Field name confirmed: **`BasedOnId`** (help doc says "Based On"). |
| `ProductCategoryProduct` (junction) | `ProductCategoryId`, `ProductId` | Insert one junction record per product ↔ category link. |

## Ordering (within this act)

1. Create classification (`ProductClassification` with `Status=Active`).
2. Assign attributes to classification (one `ProductClassificationAttr` per attribute; requires `AttributeDefinition.IsActive=true`).
3. Edit default values on the assigned attributes (set `DefaultValue` on each `ProductClassificationAttr`).
4. Set product `BasedOnId` = classification Id.
5. Insert `ProductCategoryProduct` junction — product ↔ category.

## Step 1 — Create Home Loans product classification

Help-doc summary: A product classification is a template used to create similar products.
Create a classification you can assign attributes to and base products on.

**Steps.**

1. From the App Launcher select **Product Catalog Management**, then click **Product Classifications**.
2. On the Product Classifications list view page, click **New**.
3. Enter:

   | Field | Value |
   |---|---|
   | Product Classification Name | Home Loans |
   | Code | Home Loans |
   | Status | Active |
4. Save.

## Step 2 — Assign the five attributes to the classification

Help-doc summary: Product classifications hold a collection of attributes describing
general properties of products. Assign individual attributes or a collection via attribute
categories.

**Steps.**

1. From App Launcher, select **Product Catalog Management**, then select **Product Classifications**.
2. Click the Home Loans classification created in Step 1.
3. Click the **Attributes** tab.
4. In the Attributes section, click **Assign**.
5. Select **Assign Attributes by Category** and click **Next**.
6. Select **LoanTerm**, **MaxLoanAmount**, **MinLoanAmount**, **OmniScriptName**, and **OfferValidPeriod** and click **Assign**.

**Note (Article 14 considerations).** Add these five attributes in the same attribute
category or as uncategorized attributes.

## Step 3 — Edit default values

**Steps.**

1. From App Launcher, select **Product Catalog Management**, then select **Product Classifications**.
2. Click the Home Loans classification.
3. Click the **Attributes** tab.
4. For each attribute, click the action icon → **Edit** → enter the default value → save:

   | Attribute | Default (unsecured) | Default (secured — auto/home loan) |
   |---|---|---|
   | MinLoanAmount | 1000 | 1000 |
   | MaxLoanAmount | 100000 | 100000 |
   | OmniScriptName | ApplicantIntake | ApplicantIntakeSecured |
   | OfferValidPeriod | 30 | 30 |

**Secured-loan variant.** Help-doc note (Article 10): for a secured loan product — a home
loan is secured — enter **ApplicantIntakeSecured** as the default value for OmniScriptName.

LoanTerm has no default value edit in the help doc — its values come from the picklist
created in Act 3.

**Programmatic equivalent.** Combine Steps 2+3 into one `ProductClassificationAttr` insert
per attribute (set `DefaultValue` at create time):

```text
ProductClassificationAttr:
  Name: <attr name>                 # e.g. MinLoanAmount
  ProductClassificationId: <classification Id>
  AttributeDefinitionId: <attr def Id>
  Sequence: <int>                   # 10 / 20 / 30 / 40 / 50 recommended (int, not "1")
  Status: Active
  DefaultValue: <value>             # per table above; omit for LoanTerm
```

`Sequence` is **integer** (not the string "1" the UI shows for picklist-value sequences).

**⚠️ PCA DefaultValue can be overridden by AttributeDefinition-level default (org-verified
2026-07-29).** If the referenced `AttributeDefinition.DefaultValue` is non-null (e.g.
OmniScriptName was created per help Article 8 with
`DigitalLending_DFApplicantIntakeSecured_English`), the insert silently stores the
AttributeDefinition-level value in `ProductClassificationAttr.DefaultValue` — even when
the PCA insert body explicitly passes a different `DefaultValue`. Two fixes:
- **Preferred (per Act 3 update):** don't set `AttributeDefinition.DefaultValue` at create
  time; own the default at the PCA (classification) layer.
- **Alternative for legacy orgs:** after each PCA insert, verify with `SELECT DefaultValue
  FROM ProductClassificationAttr WHERE Id = <pca id>` and issue `UPDATE
  ProductClassificationAttr SET DefaultValue = <target value>` if it drifted.

**Verify.** Re-open each attribute on the classification; confirm the default value saved.
Programmatically: `SELECT Name, DefaultValue FROM ProductClassificationAttr WHERE
ProductClassificationId = <id>` and confirm each row matches the target unsecured/secured
value from the table above.

## Step 4 — Set the product's Based On to the classification

Help-doc summary: Assign the Home Loans classification to the product created in Act 3.

**Steps.**

1. From the App Launcher select **Product Catalog Management**, then click **Products**.
2. Click the product created in Act 3 (for example, Home Loan).
3. In the **Based On** field, select **Home Loans**.
4. Save.

**Programmatic.** UPDATE `Product2` SET `BasedOnId` = <classification Id>. Field name
confirmed as `BasedOnId` (org-verified 2026-07-29).

**Verify.** `SELECT Id, Name, BasedOnId FROM Product2 WHERE Id = <product Id>`. `BasedOnId`
must equal the classification's Id.

## Step 5 — Assign the product to a catalog category

Help-doc summary: Organize products by assigning them to catalog categories and
subcategories.

**Steps.**

1. From the App Launcher, select **Product Catalog Management**, then select **Categories**.
2. From the Categories list view, click the category (or subcategory) to which you want to assign one or more products.
3. From the Category page, click the **Related** tab.
4. In the Products section, click **Assign Products**.
5. Select the Home Loan product.
6. Click **Next** and save.

**Programmatic.** The UI "Assign Products" action inserts a `ProductCategoryProduct`
junction row:

```text
ProductCategoryProduct:
  ProductCategoryId: <category Id>
  ProductId: <product Id>
```

**Verify.** `SELECT Id FROM ProductCategoryProduct WHERE ProductId = <product Id> AND ProductCategoryId = <category Id>`. Exactly one row expected.

**Note (Article 14 considerations).**
- You must add products to a category if you're not using parent and child categories.
- When you use parent and child categories, categorize products by using subcategories.

## End state

- `ProductClassification` exists with `Status=Active` (e.g. Home Loans).
- Five `ProductClassificationAttr` rows exist under the classification, each with the correct `DefaultValue` for the loan variant (unsecured OR secured). LoanTerm carries no `DefaultValue`.
- `Product2.BasedOnId` = classification Id.
- One `ProductCategoryProduct` row links product ↔ category (or subcategory if using parent/child hierarchy).

## See also

- Salesforce Help: Product Classifications
- Salesforce Help: Assign Attributes to a Product Classification
- Salesforce Help: View Products Based on a Product Classification
- Salesforce Help: Assign Products to Catalog Categories and Subcategories
- [`../../references/attributes-and-defaults.md`](../../references/attributes-and-defaults.md)
