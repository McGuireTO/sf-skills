---
name: fsc-product-act2-catalog-categories-create
description: "Sub-skill of digital-origination-product-setup. Act 2 — create the Digital Lending catalog (Sales type, unique code, effective start/end dates), then create catalog categories (e.g. Home Loans) and optionally subcategories under it."
metadata:
  version: "1.0"
---

# Act 2 — Catalog + Categories/Subcategories

Sources:
- [Create a Catalog for Digital Lending](https://help.salesforce.com/s/articleView?id=ind.fsc_lending_catalogs_products_create_catalog.htm&type=5)
- [Create Catalog Categories and Subcategories for Digital Lending](https://help.salesforce.com/s/articleView?id=ind.fsc_lending_catalogs_products_categories.htm&type=5)

## Purpose

Create the catalog that holds Digital Lending products, and the category hierarchy inside
it so applicants can browse.

## Prereq gate

- Act 1 complete (PCM Designer perm set assigned).

## Step 1 — Create the catalog

Help-doc summary: A catalog is a collection of the products you sell, organized into
categories for easier findability. Create a catalog before creating catalog categories +
assigning products. Use Product Catalog Management.

**Steps.**

1. From the App Launcher select **Product Catalog Management**, then click **Catalogs**.
2. From the catalogs list view page, click **New**.
3. In the New Catalog window, enter the details:
   - **Name** and **description** for the catalog.
   - **Unique catalog code**.
   - **Effective start date** — date/time the catalog becomes available to users.
   - **Effective end date** — date/time after which the catalog is no longer available.
   - **Type** — select **Sales**. (A Sales catalog is a catalog for products; a Service Process is a catalog for a suite of services.)
4. Save.

**Verify.** Query the created record; confirm all six fields populated as entered.

## Step 2 — Create catalog categories

Help-doc summary: To organize + group products, create catalog categories and
subcategories. A product can be assigned to more than one category / subcategory. The
Categories tab shows a hierarchical view — expandable/collapsible to show/hide
subcategories.

**Steps.**

1. From the App Launcher select **Product Catalog Management**, then click **Catalogs**.
2. From the catalogs list view, click the catalog created in Step 1.
3. Click **Categories**.
4. Click **Create Category**.
5. In the New Catalog Category window, enter:
   - **Name** and **description** for the category.
   - **Catalog** — auto-populated with the parent catalog.
   - **Parent category** — select if this category is a subcategory. If it's the first (top-level) category in the hierarchy, leave blank.
   - **Sort order** — determines the order categories are shown to users in the purchase flow.
   - **Category code**.
6. Save.

**Verify.** Re-open the Categories tab; confirm the new category appears in the hierarchy at
the expected level.

## Optional — subcategories

Repeat Step 2 with **Parent category** set to a previously-created category. Help-doc Article
5 notes: use subcategories to further group products. Article 14 considerations state:
"When you use parent and child categories, categorize products by using subcategories."

## End state

- One catalog exists — name / description / unique code / effective start / effective end / type=Sales.
- At least one top-level category exists under the catalog (e.g. Home Loans).
- Optional subcategories exist as needed.

## See also

- Salesforce Help: Product Catalog Management
- Salesforce Help: Create Catalog Categories and Subcategories
