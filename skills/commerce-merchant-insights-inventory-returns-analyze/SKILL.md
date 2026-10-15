---
name: commerce-merchant-insights-inventory-returns-analyze
parent: "commerce-merchant-insights"
purpose: "Generate and run Commerce Data Cloud SQL for inventory health (dead stock, days of supply) and returns analysis (summary, reasons, monthly trend, top returned products)."
description: "Answer a B2B Commerce merchant's questions about inventory and returns from Commerce Data Cloud: dead / slow-moving stock and on-hand levels (joining the inventory DMO), days of supply, and returns broken down by count/refund, reason, month, or product. Adapts the dead_stock_inventory and returns_summary anchor queries (change threshold, swap the returns GROUP BY, re-slice), self-checks against the executor dialect, and runs the generated read-only SQL via the data360-query-mcp SOR. Use for \"what's dead stock\", \"slow movers\", \"days of supply\", \"returns this month\", \"top return reasons\", \"most returned products\". Requires the OCI inventory / OMS returns kits — say so if absent."
metadata:
  version: "1.0"
---

# Inventory & returns insights

Answer inventory-health and returns questions. Follow the parent
`commerce-merchant-insights` generation contract and grounding pack.

## Use cases and anchors

| Question shape | Anchor (`queries/…`) | Adapt by |
|---|---|---|
| "dead stock", "slow movers", "unsold with stock on hand" | `dead_stock_inventory.sql` | staleness threshold days; `LIMIT`/offset; add days-of-supply column |
| "days of supply for X", "how long will stock last" | `dead_stock_inventory.sql` | `ROUND("ssot__AvailableToOrderQuantity__c" / NULLIF("ssot__Agg_AvgOrderedQty__c",0))` (sql-patterns Days-of-Supply) |
| "$ tied up in dead stock", "value of unsold inventory", "how much is sitting there" | `dead_stock_inventory.sql` + `price` CTE | add avg-realized-price CTE, `est_tied_value = on_hand_qty × avg_price`; SUM for total (sql-patterns "Dead-stock valuation"). **Retail value, not cost; never-sold rows = qty-only, value N/A** |
| "returns summary", "return rate this period" | `returns_summary.sql` | period; return rate = return_count / NULLIF(total_orders,0) |
| "top return reasons", "returns by reason" | `returns_summary.sql` | GROUP BY reason column on `ssot__ReturnOrderProduct__dlm` |
| "monthly return trend" | `returns_summary.sql` | GROUP BY `EXTRACT(year/month FROM …)` |
| "most returned products" | `returns_summary.sql` | GROUP BY product; `ORDER BY returned_qty DESC LIMIT N` |

## Key grounding for this use case

- **Dead stock JOIN (validated anchor behavior, differs from `sql-patterns.md`):** base on
  `ssot__GoodsProduct__dlm` so never-sold products surface; LEFT JOIN the fact table on
  **product id** (`s."ssot__ProductID__c" = p."ssot__Id__c"`) and LEFT JOIN
  `LocationInventoryChangeDMO__dlm` on **product id** (`inv."ssot__Goo_Id__c" =
  p."ssot__Id__c"`) — NOT on SKU. On-hand = `"ssot__OnHandQuantity__c"`, available =
  `"ssot__AvailableToOrderQuantity__c"`. Pin the exact inventory field names per org.
- Returns are **OMS-kit** raw DMOs (`ssot__ReturnOrder__dlm`,
  `ssot__ReturnOrderProduct__dlm`) joined through `ssot__SalesOrder__dlm` +
  `ssot__WebStore__dlm`, filtered on `ws."ssot__Id__c"` (WebStore **id**). Not the fact table.
- **Dead-stock $ value** = `on_hand_qty × avg realized selling price` (fact table
  `SUM(ProductAmount)/SUM(OrderQuantity)` per product — the transacted, store/buyer-effective
  price, so no pricebook resolution). It is **retail value, not carrying cost** (no cost field
  exists — never call it cost). Never-sold products have no realized price → report them
  **qty-only, value "N/A (never sold)"**; do NOT value them off a flat `PricebookEntry` (B2B
  price is store/buyer-group-scoped via `WebStorePricebook`/`BuyerGroupPricebook`/entitlement).
  Catalog value of never-sold stock, if needed, routes to the Commerce Pricing API. See
  sql-patterns "Dead-stock valuation".
- **Data availability:** dead stock needs the OCI inventory transform
  (`LocationInventoryChangeDMO__dlm`); returns need the OMS Data Kit. If either DMO is
  empty/absent, report "not in Data Cloud for this org" — don't return a misleading zero.

## Execute

Per parent contract: `describe(execute_query-sql)` → double-encoded `paramsJson`
(`input.sql`) → `dispatch` `query-sql` on `data360/query` → format. Resolve store first;
use pinned date form; note this use case joins across multiple DMOs, so verify each table exists.

## Guardrail

Read-only single `SELECT`/`WITH`; store filter present + escaped; whitelisted `ssot__*`
columns only; bounded `LIMIT`. See parent "Security guardrail".

## Definition of done

Returned dead-stock / days-of-supply / returns rows for the resolved store and window with
quantities and refunds correctly labeled — or reported that the OCI inventory or OMS
returns data is not present in this org's Data Cloud.
