---
name: fsc-product-act5-considerations-get
description: "Sub-skill of digital-origination-product-setup. Act 5 — surface the Salesforce Help considerations and limitations for Digital Lending catalogs and products (100-product FlexCard cap, no pagination, dynamic name/image/description, currency vs number typing for loan-amount attributes, LoanTerm as months picklist, DigitalLendingTransFormProductInfo data-mapper update requirement when custom attributes are added). Not a write step — alignment step."
metadata:
  version: "1.0"
---

# Act 5 — Considerations & limits

Source: [Considerations and Limitations for Catalogs and Products for Digital Lending](https://help.salesforce.com/s/articleView?id=ind.fsc_lending_catalogs_products_considerations.htm&type=5)

## Purpose

Alignment step, not a write step. Surface each consideration to the admin so downstream
expectations (product listing, offer validity, data mapper updates) are set correctly.

## Prereq gate

- Acts 1–4 complete, OR the admin explicitly asked for a considerations-only summary.

## What to surface

Full verbatim list at [`../../references/considerations-and-limits.md`](../../references/considerations-and-limits.md).
Walk the admin through each bullet; capture acknowledgement.

Priority items to call out:

1. **100-product FlexCard cap + no pagination.** Product List Page FlexCard shows up to 100 products from the CPQ API. If the admin plans to onboard more, this is a design blocker.
2. **Category-required rule.** If not using parent + child categories, products MUST be assigned to a category. If using parent + child, use subcategories.
3. **Attribute grouping.** Add LoanTerm, MinLoanAmount, MaxLoanAmount, OmniScriptName, OfferValidPeriod in the same attribute category OR as uncategorized. Do not split across attribute categories.
4. **Type mismatch — MinLoanAmount / MaxLoanAmount.** Sample-data considerations describe these as Type **currency**. Help-doc creation steps (Article 6, Act 3) use Data Type = **Number**. If the admin plans to use the Agentforce Financial Services sample data, use currency; otherwise follow Number per the creation steps.
5. **LoanTerm — picklist in months.** LoanTerm is a picklist type with loan terms as picklist values. Values are in months.
6. **Data mapper update requirement.** If the admin creates attributes beyond LoanTerm / MinLoanAmount / MaxLoanAmount / OmniScriptName / OfferValidPeriod, they MUST update the DigitalLendingTransFormProductInfo Data Mapper Transform with the custom attributes. This is out of scope for this SKILL — flag it as follow-up.
7. **Dynamic product-card fields.** Name, display URL, and description shown on the product card come from the product record's name / display URL / description attributes. Values are dynamic per product.
8. **CPQ Fetch product detail API.** Returns new attributes; the updated attributes appear on the product detail page. Wire-up is out of scope for this SKILL.

## End state

- Admin has acknowledged each consideration.
- Follow-up items captured (custom-attribute data-mapper update, FlexCard scale, sample-data currency typing).

## See also

- [`../../references/considerations-and-limits.md`](../../references/considerations-and-limits.md) — verbatim source
