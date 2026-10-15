---
name: commerce-merchant-insights-order-shopper-get
parent: "commerce-merchant-insights"
purpose: "Look up a specific order's live detail via the OMS OrderSummary skill, and list the storefront's external-managed (delegated) account relationships via the Commerce entitlement API — point lookups that are live CRM/OMS, not Data Cloud analytics."
description: "Answer a B2B Commerce merchant's point-lookup questions. A specific order's CURRENT state (status, total, line items, placed/shipped dates, payment, shipping) is LIVE OMS data — reuse the existing `search-order-summaries` SOR (`search-by-order-number` + line-item drilldown), NOT a Data Cloud query. The storefront's delegated / external-managed account relationships come from the delegated-account Connect API (`get-external-managed-account`, **store-scoped — keyed on `webStoreId` only, so it returns ALL external-managed accounts for the storefront, not one buyer's**), NOT a `BuyerAccount` SOQL and NOT Data Cloud. Data Cloud only supplies historical/aggregate order facts, never the live order state or the entitlement graph. Use for \"look up order X\", \"which accounts have delegated / managed relationships in this store\"."
delegates_to:
- "search-order-summaries"
- "delegated-account-connect-api-sfdc.delegated.account.connect.api-oas-67.0"
metadata:
  version: "1.0"
---

# Order & shopper lookups

Answer point-lookup questions. Follow the parent
`commerce-merchant-insights` generation contract and grounding pack. **These are live
CRM/OMS lookups, not Data Cloud analytics** — a specific order's current state and a buyer's
entitlement are not what the Data Cloud fact table is for.

## Use cases and sources

| Question shape | Source | How |
|---|---|---|
| "look up order #X", "order summary for X", status/total/dates/line items | **Live OMS** — reuse `search-order-summaries` SOR | `search-by-order-number` (matches `OrderSummary.OrderNumber` **or** `OrderSummaryNumber`) → `Status`, `GrandTotalAmount`, `OrderedDate`; then the line-item drilldown (`OrderItemSummary`) for count/rollup. Do NOT hand-roll SOQL or query Data Cloud for live status — the SOR owns it |
| order **payment** status ("captured?") | **Live OMS** | `OrderPaymentSummary` for the `OrderSummaryId` (`Status`). Sibling of OrderSummary; not on the fact table |
| order **shipping** method / shipped date | **Live OMS** | `OrderDeliveryGroupSummary` for the order (delivery method, dates). Sibling of OrderSummary |
| "which accounts have delegated / managed relationships in this store", "external-managed accounts" | **Commerce delegated-account API** | Call `delegated-account-connect-api` op `get-external-managed-account` → `GET /commerce/webstores/{webStoreId}/external-managed-accounts`. **This op is keyed on `webStoreId` ONLY — it lists ALL external-managed accounts for the storefront, it does NOT take a buyer id and does NOT filter to one shopper's effective accounts.** If asked "what can buyer Y order for", say the store-scoped op returns the store's whole delegated-account set (a true per-buyer entitlement resolution isn't available from this op in this dispatch model) — don't present the store-wide list as buyer Y's. NOT Data Cloud (sold-to *history* ≠ entitlement), NOT a `BuyerAccount` SOQL (see grounding) |
| historical/aggregate order facts (how many orders, revenue over time) | Data Cloud | that's the `store-health` / `product-performance` path — route there, not here |

## Key grounding for this use case

- **A specific order's current state is OMS, not Data Cloud.** The Data Cloud fact table lags
  and is built for aggregates; "is order #X shipped, was payment captured" must come from the
  live OMS `OrderSummary` (+ `OrderItemSummary` / `OrderPaymentSummary` /
  `OrderDeliveryGroupSummary`). Reuse `search-order-summaries` — don't rebuild it, don't
  approximate order status from a DC row.
- **External-managed accounts = the delegated-account API, not a `BuyerAccount` query — but it is
  store-scoped, not buyer-scoped.** `delegated-account-connect-api` `get-external-managed-account`
  (`GET /commerce/webstores/{webStoreId}/external-managed-accounts`) is keyed on `webStoreId`
  ONLY; per its own SOR it "lists ALL external managed accounts associated with that storefront."
  So it does **not** resolve one shopper's effective accounts — resolving buyer Y first has no
  effect on what it returns. Present it as the store's delegated-account relationship set; a true
  per-buyer entitlement resolution isn't available from this op in the single-connection dispatch
  model (it would need the buyer's own session context). **Do NOT use `BuyerAccount`** either: its
  `BuyerId` references an **Account** (it marks an account as buyer-*enabled* + its buyer group),
  it is NOT a person→accounts map. The underlying multi-account link is `AccountContactRelation`,
  which may be absent on an org. Data Cloud `ssot__SoldToCustomerId__c` is sold-to *history* (who
  has ordered), NOT who a buyer *may* order for — never present it as entitlement.
- **Store-scoped + cross-org (parent invariants).** Scope order lookups and effective-account
  resolution to the confirmed store(s). Because Data Cloud can be ingested from another org, an
  order/buyer seen in DC history may have **no live OMS/CRM record here** — say the live detail
  isn't available for it rather than fabricating; conversely a live order may pre-date DC sync.
- **Resolve the id first.** Order number / buyer to a concrete record; ask if ambiguous. Never
  guess an id.

## Execute

When a single request needs both an order lookup AND the store's external-managed accounts (or
order-summary + payment/shipping siblings for the same order), fan out those independent
CRM/OMS reads in parallel subagents and merge per the parent "Parallel hybrid execution" rule
(complementary compose — different sections; do NOT dedupe or sum). A lone order lookup or a
lone entitlement read is single-path — no fan-out.

- **Order lookup**: `describe` then `dispatch` the `search-order-summaries` `search-by-order-number`
  step (live OMS SOQL); drill into line items via its item step. Fetch payment/shipping from the
  sibling summary objects if asked. No Data Cloud dispatch for live order state.
- **External-managed accounts**: `describe`+`dispatch` `delegated-account-connect-api`
  `get-external-managed-account` for the store (`webStoreId`) — the op takes no buyer id, so this
  returns the storefront's whole delegated-account set. If the merchant named a shopper, say the
  result is store-scoped rather than filtered to that shopper. No Data Cloud dispatch, no
  `BuyerAccount` SOQL.
- Data Cloud (`execute_query-sql`) is used here **only** if the question is actually a
  historical/aggregate order fact — in which case route to `store-health` / `product-performance`.

## Guardrail

Read-only. Reuse `search-order-summaries` (it owns its account-scoping + injection defense —
don't hand-roll order SOQL). Ids validated + escaped. Effective-account reads are
`BuyerAccount.READ` etc., store-scoped. See parent "Security guardrail".

## Definition of done

Returned a specific order's live detail (status/total/dates/line items, plus payment/shipping
when asked) from the OMS `search-order-summaries` path, or the storefront's external-managed
account relationships from the `delegated-account-connect-api` `get-external-managed-account` op
— scoped to the confirmed store(s), folded into one merchant-facing answer (no system names). A
shopper-scoped request is answered honestly: the delegated-account op is store-scoped, so the
result is the store's whole set, not that one shopper's effective accounts. Any datum with no
live record (e.g. a DC-only historical order with no OMS record on this org) is reported as
unavailable in business terms, never fabricated.
