---
name: commerce-merchant-insights-account-health-churn-analyze
parent: "commerce-merchant-insights"
purpose: "Generate and run Commerce Data Cloud SQL for account-level health — at-risk / churning accounts, per-account revenue trend, category churn, and customer profiles."
description: "Answer a B2B Commerce merchant's questions about individual account health and churn from Commerce Data Cloud: accounts with stale ordering activity, current-vs-prior-year revenue per account, category-level churn for an account, top customers, and a single customer's profile. Adapts the at_risk_accounts anchor (recency threshold, sort, which account dimensions) and the top-N shape in customer mode, self-checks against the executor dialect, and runs the generated read-only SQL via the data360-query-mcp SOR. Use for \"which accounts are at risk\", \"is account X churning\", \"account revenue trend\", \"top customers\", \"profile for account X\". Degrades to raw recency if RFM is unpopulated."
metadata:
  version: "1.0"
---

# Account health & churn insights

Answer per-account health and churn questions. Follow the parent
`commerce-merchant-insights` generation contract and grounding pack.

## Use cases and anchors

| Question shape | Anchor (`queries/…`) | Adapt by |
|---|---|---|
| "at-risk accounts", "who's about to churn" | `at_risk_accounts.sql` | recency threshold days; sort; `LIMIT` |
| "account revenue trend", "is account X growing/shrinking" | `at_risk_accounts.sql` | filter to one `"ssot__SoldToCustomerId__c"`; keep current/prior-year CTEs |
| "category churn for account X" | `at_risk_accounts.sql` | GROUP BY `"ssot__Name__c"` (category) within the account; compare current vs prior |
| "top customers", "biggest accounts" | `top_performers_product.sql` (customer mode) | GROUP BY `"ssot__SoldToCustomerId__c"`; `ORDER BY cur_revenue DESC LIMIT N` |
| "customer profile for X" | `at_risk_accounts.sql` + **live-CRM extras** | Data Cloud gives recency, behaviour class, revenue, top categories, trend. **Contact last-login** (`User.LastLoginDate`, join Account→Contact/buyer User) and **buyer-group membership** (`BuyerGroupMember` / `WebStoreBuyerGroup`) are **live CRM**, NOT on the fact table — fetch and fold into one profile. See `crm-hybrid-sources.md` "Account profile extras" |

## Key grounding for this use case

- Account/customer id = `"ssot__SoldToCustomerId__c"`; join
  `ssot__Account__dlm` on `acc."ssot__Id__c"` for the account name. Revenue per account =
  `SUM("ssot__TotalPriceAmount__c")` grouped by `"ssot__SoldToCustomerId__c"`.
- **Account label — DO use `acc."ssot__Name__c"` from `ssot__Account__dlm`.**
  **DON'T** build a label from `"ssot__Ind_FirstName__c" || ' ' || "ssot__Ind_LastName__c"` on
  the fact table — those columns are the *individual buyer contact* (a person who placed the
  order), NOT the B2B account. Using them shows "James Wilson" instead of "Acme Corp" and
  silently collapses multi-buyer accounts into whichever contact placed the most recent order.
  If the CRM `Account` row isn't ingested for a given `ssot__SoldToCustomerId__c`, present the
  id + `(name unavailable)` — do NOT substitute the individual name.
- **Account-level revenue = `SUM("ssot__TotalPriceAmount__c")` (order-level total).**
  **DON'T** use `SUM("ssot__ProductAmount__c")` for account rollups — that's the *line-level*
  amount (pre-discount, pre-shipping, pre-tax); summed across an account it double-counts
  multi-line orders and diverges from what the merchant sees on the order. Reserve
  `"ssot__ProductAmount__c"` for **product/SKU-level** aggregates (top sellers, category mix);
  use `"ssot__TotalPriceAmount__c"` for anything grouped by account/customer/store.
- **Recency alone is NOT enough — every "at-risk" / "churning" / trend answer MUST include a
  prior-period baseline.** The anchor's current-vs-prior CTEs (±365 / ±730 day windows over
  `"ssot__CreatedDate__c"`) are load-bearing, not optional. An account with
  `ssot__DaysSinceLastPurchase__c > N` but current-year revenue **higher** than prior-year is
  a growing whale who happens to buy in bulk, NOT a churn risk; flagging them wastes the
  merchant's outreach and hides real churn. Rank by recency **filtered by** current-vs-prior
  delta (e.g. `current_revenue < prior_revenue`, or a % drop threshold), never by recency
  alone. Precomputed recency: `"ssot__DaysSinceLastPurchase__c"`; behaviour class:
  `"ssot__CustomerBehaviour__c"`.
- **DON'T rank at-risk / churn by unbounded lifetime `SUM("ssot__TotalPriceAmount__c")`.**
  Lifetime revenue is a size signal, not a risk signal — it flattens a shrinking $10M account
  and a growing $10M account into the same row. Always window revenue to the current period
  (and compare to prior) when the question is about *change*.
- **CLV** (`sql-patterns.md`): AOV×APF×ACL; but prefer live
  `SUM("ssot__TotalPriceAmount__c")` for monetary value — `ssot__LifeSpanValue__c` is
  TIME, and `ssot__GrossSales__c` is a stale snapshot in dev orgs.
- **Degrade rule:** if behaviour/RFM columns are empty, rank by raw
  `"ssot__DaysSinceLastPurchase__c"` **combined with** the current-vs-prior delta, and
  disclose the fallback. Never degrade to recency-only.
- **Profile extras are live CRM, not Data Cloud — and store-scoped + best-effort.**
  *Contact/buyer last-login activity* → `User.LastLoginDate` for the account's buyer User(s);
  *buyer-group membership* → `BuyerGroupMember` **intersected with `WebStoreBuyerGroup` for the
  resolved store** (a group not assigned to this store doesn't count — verified: `WebStore` =
  the store → its buyer groups). Neither is on the fact table. **Buyer group ≠ RFM behaviour
  class** — `"ssot__CustomerBehaviour__c"` (Repeat/New Customers) is a Data Cloud computed
  class; a *buyer group* (e.g. Enterprise, Mid-Market) is CRM commerce config. Don't present the
  RFM class as the account's "buyer group". Fold both CRM extras into one profile answer (parent
  Format rule — no system names).
  - **The account may not exist in this CRM at all.** Data Cloud can be ingested from a
    *different* source org, so the DC account can have **no matching local CRM record** → no
    User, no buyer-group row. That's expected, not an error: match on account id/name, and if
    there's no match report last-login / buyer-group as **not available** (business terms) and
    keep the Data-Cloud profile. Same when CRM is simply unreachable. Never fabricate the extra.

## Execute

Per parent contract: `describe(execute_query-sql)` → double-encoded `paramsJson`
(`input.sql`) → `dispatch` `query-sql` on `data360/query` → format. Resolve store first;
resolve the target account (match name → `ssot__SoldToCustomerId__c`, ask if ambiguous);
use pinned date form.

For a customer/account **profile** answer (Data Cloud core + live-CRM extras — contact
last-login, buyer-group membership), fan out the Data Cloud and live-CRM slices in
parallel subagents and merge per the parent "Parallel hybrid execution" rule
(complementary compose — do NOT dedupe or sum; a missing CRM extra degrades to "not
available"). Pure at-risk / trend / churn questions are Data-Cloud-only — single path,
no fan-out.

## Guardrail

Read-only single `SELECT`/`WITH`; store filter present + escaped; account id/name
validated + single-quote-escaped before interpolation; whitelisted `ssot__*` columns
only; bounded `LIMIT`. See parent "Security guardrail".

## Definition of done

Before returning an at-risk / churn / trend answer, verify **every** item:

- [ ] **Store filter uses `"ssot__WebStoreId__c" = '<id>'`** (the resolved store id), NOT the
      name column `"ssot__SalesStoreId__c"` — the id works on raw-DMO joins too. Id resolved
      once, reused across every CTE.
- [ ] **Account label comes from `acc."ssot__Name__c"`** via `LEFT JOIN "ssot__Account__dlm"
      acc ON <id> = acc."ssot__Id__c"`. **No `ssot__Ind_FirstName__c` / `ssot__Ind_LastName__c`
      anywhere in the SELECT for the account label.** Missing CRM row → `(name unavailable)`,
      never substituted with the individual buyer.
- [ ] **Account revenue = `SUM("ssot__TotalPriceAmount__c")`** grouped by
      `"ssot__SoldToCustomerId__c"`. **No `SUM("ssot__ProductAmount__c")` for account rollups.**
- [ ] **Current-vs-prior baseline present** (±365 / ±730 CTEs, or the equivalent windowed pair
      for the merchant's stated window). At-risk / churn ranking uses the delta
      (`current_revenue - prior_revenue`, or a % drop), NOT recency alone, NOT unbounded
      lifetime SUM. If merchant explicitly asked for recency-only, disclose the limitation.
- [ ] **RFM/behaviour fallback disclosed** when `"ssot__CustomerBehaviour__c"` is empty.
- [ ] **Profile answers** fold Data Cloud core (recency/behaviour/revenue/categories/trend)
      with live-CRM extras (contact last-login, buyer-group membership) into one
      merchant-facing answer — buyer group kept distinct from RFM behaviour, no system names.
      A datum in neither source is reported in business terms, never fabricated.
