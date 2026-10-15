---
name: commerce-merchant-insights-product-performance-analyze
parent: "commerce-merchant-insights"
purpose: "Generate and run Commerce Data Cloud SQL for product performance — top/bottom sellers, product revenue and unit trends, and growth vs a prior period."
description: "Answer a B2B Commerce merchant's questions about product performance from Commerce Data Cloud: best- and worst-selling products, product revenue and unit trends over time, and period-over-period growth. Adapts the top_performers_product and product_trend anchor queries (swap the ranked column, the metric, the window, add a category filter), self-checks against the executor dialect, and runs the generated read-only SQL via the data360-query-mcp SOR. Use for \"top sellers\", \"what's declining\", \"product trend for X\", \"fastest-growing products this quarter\". Product/bundle *configuration* status (active, published, bundle membership) is NOT in Data Cloud — source it from LIVE CRM (Product2, ProductCategoryProduct, ProductRelatedComponent). Never fabricate config from the fact table."
metadata:
  version: "1.0"
---

# Product performance insights

Answer product-level questions. Follow the parent
`commerce-merchant-insights` generation contract and grounding pack.

## Use cases and anchors

| Question shape | Anchor (`queries/…`) | Adapt by |
|---|---|---|
| "top / bottom N products", "best sellers", "fastest growing" | `top_performers_product.sql` | `ORDER BY` col (cur_revenue / cur_units / growth_percent) + `ASC`/`DESC` + `LIMIT`; category clause; period |
| "product trend", "units vs revenue over months for X" | `product_trend.sql` | product name AND-clause (`AND "ssot__Goo_Name__c" = '…'`); metric; bucket grain |
| ABC / Pareto ("which products drive 80% of revenue") | `top_performers_product.sql` | add cumulative-revenue window (`sql-patterns.md` ABC formula: A80/B15/C5) |
| **"is product X active / published", "product status"** | **Live CRM** (not Data Cloud) | SOQL `Product2.IsActive` (active) + `ProductCategoryProduct` for the store's catalog (published). **In stock**: real-time via Commerce Inventory Availability API (no live-CRM stock sObject); lagging snapshot in Data Cloud `LocationInventoryChangeDMO__dlm` (the `inventory-returns` path). Report separately, don't infer from sales. See `crm-hybrid-sources.md` "Product / bundle status" |
| **"is X in a bundle / which bundle", "bundle status"** | **Live CRM** (not Data Cloud) | SOQL `ProductRelatedComponent` (`ParentProductId` = bundle, `ChildProductId` = component). Filter `ChildProductId = <product>` to find the bundle(s) it belongs to. Promotion membership is a separate Commerce Promotions source (the close-the-loop promotion path) — say so |

## Key grounding for this use case

- Product name = `"ssot__Goo_Name__c"`; category = `"ssot__Name__c"`; product revenue =
  `SUM("ssot__ProductAmount__c")`; units = `SUM("ssot__OrderQuantity__c")`. Filter
  `"ssot__Goo_Name__c" IS NOT NULL` when ranking products.
- `top_performers_product` does current-vs-prior in a **single scan** via conditional
  aggregation over a 2×period window — reuse that shape rather than two round-trips.
- Product/bundle **configuration** (active flags, bundle membership, catalog setup) is
  NOT in the fact table — it's current-state config, so read it from **live CRM**:
  - **Active** → `Product2.IsActive` (SOQL).
  - **Published to store** → `ProductCategoryProduct` (catalog/category membership for the
    resolved store).
  - **Bundle membership** → `ProductRelatedComponent` (`ParentProductId`=bundle,
    `ChildProductId`=component); resolve product Ids by name via `Product2` first.
  - **In stock** → real-time via the Commerce **Inventory Availability API** (no live-CRM
    stock sObject; `WebStoreInventorySource` is config only). A **lagging** approximate qty is
    in Data Cloud `LocationInventoryChangeDMO__dlm.ssot__AvailableToOrderQuantity__c` (the
    `inventory-returns` path). Never infer stock from sales.
  - **Promotion membership** → Commerce Promotions (the close-the-loop promotion path) — out of
    scope for this skill.
  Data Cloud answers *performance* (revenue/units/trend); live CRM answers *config/status*.
  Combine when the user asks both (e.g. "trend + status") into one merchant-facing answer —
  don't name which system each part came from (parent Format rule); note recency only if it
  affects a decision ("status as of today" vs "trend over 6 months").

## Execute

Per parent contract: `describe(execute_query-sql)` → double-encoded `paramsJson`
(`input.sql`) → `dispatch` `query-sql` on `data360/query` → format. Resolve store first;
use pinned date form.

When a question mixes performance (Data Cloud) with product/bundle status (live CRM) —
"top sellers + which are active", "trend for X + is it published" — fan out the Data Cloud
and live-CRM slices in parallel subagents and merge per the parent "Parallel hybrid
execution" rule (complementary compose — do NOT sum or dedupe rows across sources).

## Guardrail

Read-only single `SELECT`; store filter present + escaped; whitelisted `ssot__*` columns
only in dynamic sort/filter positions; bounded `LIMIT` (cap top-N at a sane max, e.g. 20).

## Definition of done

Returned ranked or trended product rows (Data Cloud) for the resolved store/window with the
requested metric correctly labeled. For a product/bundle **status** question, returned the
current config from **live CRM** (`Product2.IsActive`, `ProductCategoryProduct`,
`ProductRelatedComponent`), labeled as CRM — and where a datum has no source (in-stock →
Inventory API; promotion → the close-the-loop promotion path), said so rather than inferring it from sales.
