---
name: commerce-merchant-insights-query
description: "Answer a B2B Commerce merchant's natural-language questions about store health, product performance, inventory and returns, customer segments, and account health/churn by generating and running Commerce Data Cloud SQL — no admin-screen navigation. Routes an unqualified \"show me how the store is doing / what's selling / what's dead stock / which accounts are at risk\" request to the matching sub-skill. Each sub-skill teaches the agent the Commerce Data Cloud data model plus one canonical anchor query per use case, and the agent ADAPTS the anchor to author read-only SQL for the specific question, executing it via the data360-query-mcp SOR. Use a sibling directly for a narrowed request (e.g. \"top-selling products this quarter\" → product-performance)."
metadata:
  version: "1.0"
---

# Merchant Insights

Give a B2B Commerce admin store, product, inventory, segment, and
account-health insights from Commerce Data Cloud, in reply to plain-language questions
asked on a conversational assistant. Insight generation is **read-only** — it authors and
runs `SELECT`s, and never writes. The agent may also **close the loop**: turn an insight
into an action by recommending a promotion, showing the merchant a draft, and creating it
in the live CRM org **only on explicit merchant confirmation** — by delegating to the
existing promotion skill (see "Closing the loop — creating a promotion" below). That
confirmed hand-off is the sole write path.

This skill does **not** ship a locked query per question. It teaches the agent the data
model and gives one canonical **anchor** query per major use case; the agent adapts the
anchor to the specific utterance, self-checks, and runs it. Coverage therefore includes
both the enumerated catalog and open-ended "ask anything" — subject to what the org's
DMOs actually hold.

## Read the grounding pack first (shared by all sub-skills)

Before generating any SQL, load the shared references (served with this skill's
artifacts; read them via `describe(ref:...)` or from `source/references/`):

- `dialect-d360-query-sql.md` — **AUTHORITATIVE** executor dialect + runtime wire shape.
  Overrides the pattern file where they conflict. Read it every time.
- `dmo-reference.md` — which DMOs exist, which fields *matter* + what they *mean* (gotchas,
  money-vs-time, stale precomputed). Not an exhaustive authoritative field list — resolve exact
  names/types/table-suffix at runtime via the `SELECT * LIMIT 1` probe (see contract step 5).
- `data-transforms.md` — how the derived fact table is built (precomputed fields).
- `sql-patterns.md` — business-logic formulas (attrition, CLV, ABC, days-of-supply,
  period-over-period). Its *syntax* section is superseded by `dialect-d360-query-sql.md`.
- `queries/*.sql` — the ~8 canonical anchor templates (Commerce analytics reference SQL;
  adapt each one to the executor dialect before dispatch).
- `crm-hybrid-sources.md` — when to use **live CRM** vs Data Cloud, the CRM sources
  (recent orders via `search-order-summaries`; goals via the Business Objectives Connect
  API), the recent-data merge rule, and the **Data-Cloud-optional** degradation path.
  Read it for any recent/current/goal question or when Data Cloud may be absent.

## The one runtime SOR (reuse — do not build)

All execution goes through the existing **`data360/query`** SOR,
step **`query-sql`**, tool `d360_query_sql`:

1. `describe(execute_query-sql)` FIRST — get the param schema + worked example.
2. `dispatch` the `query-sql` step with a single input `paramsJson`, a **double-encoded**
   JSON string whose value is `{"input":{"sql":"<your SELECT>"}}` (inner key `input.sql`).
3. Small queries return synchronously (`result.data` + `result.metadata` inline). Only
   large sets need `d360_query_sql_status` → `d360_query_sql_rows`.

The `paramsJson` double-encoding and the `input.sql` inner key are the two most common
mistakes — see `dialect-d360-query-sql.md`.

## Generation contract (every sub-skill follows this)

1. **Understand** the utterance: which use case, what window, what grouping/sort, which
   store, any product/category/account filter.
2. **Resolve the store scope — confirm when ambiguous.** Enumerate distinct stores on the
   org. Then:
   - Merchant named a store → use it.
   - Merchant said "all stores" / "across stores" / "the whole org" → span all stores
     (aggregate, or `GROUP BY` store so each store's line is visible). This is a valid scope.
   - Org has exactly one store → use it.
   - **Org has multiple stores and the merchant didn't specify → ASK** which store, a subset,
     or all of them. Do NOT silently pick one, and do NOT silently assume all. A single-store
     answer when they meant the whole org (or vice-versa) is wrong and misleading.
   **Prefer `ssot__WebStoreId__c` = the store id** — it's the canonical FK the raw DMOs
   (`ssot__SalesOrder__dlm`, `ssot__ReturnOrder__dlm`, `ssot__Account__dlm`, etc.) all carry, so
   the same filter works on the derived fact **and** on every raw-DMO join. Resolve the id once
   (probe `SalesOrderCategoryAddressDMO__dlm` or list `ssot__WebStore__dlm`) and reuse it. The
   name-based column `ssot__SalesStoreId__c` **only exists on the derived fact
   `SalesOrderCategoryAddressDMO__dlm`** — using it silently breaks any query that joins to a
   raw DMO (the join column is missing) and can collide across stores that share a name. Never
   guess. See `dialect-d360-query-sql.md` "Store filter".
3. **Pick the matching anchor** template for the use case (table below).
4. **Adapt** it — window, `GROUP BY`, filter, JOIN, sort — using the grounding pack.
   Use the org's **pinned** date form (not `INTERVAL … DAY`).
5. **Self-check** (see the checklist in `dialect-d360-query-sql.md`): identifiers exist;
   dialect-legal; store filter present + escaped; single read-only `SELECT`; bounded.
   **Resolve field names + table name at runtime, don't trust the catalog blindly** — the
   catalog teaches which fields *matter* and what they *mean*; the exact names, types, and
   the per-org table suffix come from a cheap probe: `SELECT * FROM <dmo> LIMIT 1` returns
   `result.metadata` (every column + type). Use it to confirm a field exists / find the
   suffixed table name / detect a DMO that isn't present in this org (query fails → report
   "not in Data Cloud", don't fabricate). No metadata API is available — `ssot/metadata/objects`
   is NOT_FOUND and there is no `d360_metadata_search` tool; the `LIMIT 1` probe is the resolver.
6. **Dispatch** via `execute_query-sql`; on a `sqlState` error, read it, correct the one
   named thing, retry **once**, else report the error + SQL.
7. **Format** rows for the user; label money as money and time as time (never present
   `ssot__LifeSpanValue__c` as dollars). **Merchant-facing register — hide the plumbing:**
   - Never name the underlying system or mechanics (no "Data Cloud", "CRM", "Account DMO",
     "the join", DMO/column names, `sqlState`, "unseeded record"). The merchant asked a
     business question; answer it in business terms.
   - **Resolve identifiers to names silently.** If an account/product name doesn't resolve
     from the primary source, fall back to live CRM by Id **automatically** (`Account.Name`,
     `Product2.Name`) — don't surface a raw `001…`/`01t…` Id or explain why. If a name truly
     can't be found, show "(name unavailable)", not the reason.
   - **Source only as plain recency, and only when it changes a decision** — say "as of today"
     vs "historical / last 90 days", never *which system* it came from. Freshness can matter
     to the merchant; provenance does not.
   - Data quality gaps are stated in business terms ("we don't track account type yet"), not
     as source/seeding mechanics.

If no anchor fits the use case, generate from the fact table + grounding.

**Data Cloud is required for insights; live CRM grounds and supplements it.** Every insight
analytic (revenue, trends, segments, dead-stock, returns analysis, account health) comes from
Data Cloud — it's a hard precondition (see Preconditions). Live CRM is used alongside it, per
`crm-hybrid-sources.md`:
- **Recent / current orders** ("last 24h", "latest orders", order #X) → live CRM via the
  `search-order-summaries` SOR — used to **freshen** the recent window on top of the Data Cloud
  result when the CRM→Data Cloud sync lags. Not a standalone substitute for DC.
- **Business objectives / goals / KPI targets** ("% to goal", "AOV target") → the Business
  Objectives Connect API (`get-business-objectives`) — CRM/Connect-native, never in Data Cloud.
- **Recent-data questions** → query Data Cloud (trend/context) **and** CRM (current slice) and
  merge: CRM wins the current window (freshens DC), Data Cloud supplies the trend.
- **No Data Cloud on the org** → the insight **cannot be produced** (the Preconditions gate
  this). Say so plainly; do NOT substitute a CRM-only aggregate for the insight. Point lookups
  (a specific order's state, a store's delegated accounts, tracked goals) still answer via
  CRM/OMS/Connect — they never used Data Cloud.

Only when a datum is in **neither** CRM nor Data Cloud (e.g. product/bundle *configuration*,
or conversion when no traffic/KPI source exists) do you say so plainly — never fabricate.

**Two cross-source invariants (every sub-skill):**
- **Scope everything to the confirmed store scope.** Once the scope is settled (step 2 — one
  store, a subset, or all, confirming with the merchant when ambiguous), apply it to *every*
  query — Data Cloud SQL *and* every CRM read. One store → filter `"ssot__WebStoreId__c" =
  '<id>'` (CRM: `search-order-summaries` per store, buyer groups via `WebStoreBuyerGroup`,
  catalog via `WebStoreCatalog`). Subset/all → `IN (…)` or `GROUP BY` store so each store's
  line shows. Never mix stores the merchant didn't ask for into a single-store answer, and never
  collapse an all-stores request down to one store.
- **Data Cloud may be ingested from a *different* org than this CRM.** The DC customer/account
  may have **no matching record in the CRM you're querying**, so a CRM enrichment (contact
  last-login, buyer group, order summary) can legitimately come back **empty even though the DC
  row exists**. Treat CRM extras as **best-effort**: match on a stable key (account id / name),
  and if there's no local CRM match, report that piece as unavailable (business terms) — do NOT
  assume CRM mirrors Data Cloud, and never fabricate the missing piece.

## Parallel hybrid execution — fan out, then aggregate + dedupe

Whenever a question needs **both** Data Cloud and live CRM (`store-health` recent-orders +
revenue/pipeline; `product-performance` performance + status; `account-health-churn` profile core
+ CRM extras; `order-shopper-lookups` OMS order + entitlement; any
"recent-data" merge), **fan out parallel subagents — one per source — instead of querying them
one after another.** Steps:

1. **Decide the source set for the confirmed store scope.** Data Cloud path *only if DC is
   provisioned* (fact-table probe succeeds); live CRM path for the recent/current/config/entitlement
   slice. A purely-DC or purely-CRM question uses a single path — **no fan-out** (don't spawn a
   subagent that has nothing to do).
2. **Dispatch the source queries concurrently** — e.g. one subagent runs the Data Cloud
   `execute_query-sql`, another runs the CRM read (`search-order-summaries` / Connect API /
   `delegated-account` / SOQL). They are independent, so run them in parallel, not in sequence.
3. **Barrier: wait for all source subagents**, then **merge — pick the mode by how the two
   results relate** (they rarely combine the same way):
   - **(a) Complementary — different fields → compose, do NOT dedupe.** The two sides are
     different sections of the answer (DC revenue/trend + CRM recent-orders/goals/status). Just
     assemble the sections. No key-matching, no summing — matching complementary rows is a bug.
   - **(b) Same entity in both → dedupe by a normalized key, one source wins.** Only when both
     return the *same* entity (order pipeline: DC `FulfillmentOrder` DMO + CRM `FulfillmentOrder`).
     Normalize the join key first (`FulfillmentOrderNumber`/`OrderNumber` for orders, account id
     for accounts, product id/SKU for products), **CRM wins for the current window** (DC fills only
     rows CRM lacks). Count the entity **once**, sum its value **once**. Never add DC + CRM counts
     or union across different status/segment scales.
   - **(c) Same metric, different window → reconcile, do NOT add.** DC historical/trend vs CRM
     current slice measure overlapping things (e.g. revenue). Present CRM as "current," DC as
     "trend"; where windows overlap, CRM wins the recent slice. Summing them double-counts.
   Cross-cutting: normalize keys before any match (store name↔id per step 2); for an all-stores
   scope aggregate **per store** (`GROUP BY` store) then total, never blend stores; if a shared
   key's value differs materially between sources, **flag it** (stale DC sync) rather than
   silently choosing.
4. **Return one merged, merchant-facing answer** (Format rule — no system names; recency in plain
   words). If a **CRM-native supplement** (recent orders, goals, config) is absent, present the
   Data Cloud insight without it and note the reduced depth in business terms. If **Data Cloud**
   is absent, the insight itself is unavailable — report that plainly (don't substitute a CRM-only
   aggregate).

Degenerate cases: **DC absent → insights unavailable** (Preconditions fail; report plainly — do
not fan out a CRM-only substitute), while point lookups (order state, delegated accounts, goals)
still answer via CRM/OMS/Connect; single-source question → single path. Fan out only when there
is genuinely parallel work across sources.

## Routing → sub-skills

| The user is asking about… | Route to | Anchor(s) / sources |
|---|---|---|
| store snapshot, revenue, order pipeline/status, recent orders, goals/% to goal | `store-health` | revenue_summary, order_pipeline, product_trend (Data Cloud) + live CRM: `search-order-summaries` (recent orders), Business Objectives Connect API (goals). Hybrid: Data Cloud insights + live-CRM freshness grounding |
| product trends, top/bottom sellers, product/bundle status | `product-performance` | product_trend, top_performers_product |
| dead stock, inventory levels, returns (summary/reasons/trend/top) | `inventory-returns` | dead_stock_inventory, returns_summary |
| customer/RFM segments, segment revenue, at-risk vs active mix | `segment` | segment_performance |
| at-risk accounts, account revenue trend, category churn, customer profile | `account-health-churn` | at_risk_accounts, top_performers_product (customer mode) |
| look up a specific order / shopper's effective accounts | `order-shopper-lookups` | **live OMS** `search-order-summaries` (order status/total/line items) + `BuyerAccount`/buyer-group (effective accounts). NOT Data Cloud |

Route to one sibling at a time. Run whichever the user asked for. Each sibling owns its
own generation contract, template citations, and guardrails.

## Closing the loop — creating a promotion

An insight often implies an action: dead stock → a clearance offer; a declining top product
→ a targeted discount; a fast-moving anchor product → a buy-X-get-Y (BOGO) bonus offer; an
at-risk account → a win-back offer. When the merchant asks the
agent to act on such a signal ("set up a promotion for that", "what should I do — just do
it"), the agent **recommends and creates a Commerce promotion** — it does **not** build its
own create logic.

**Reuse — do not build.** All promotion creation delegates to the existing
**`merchant-promotion-management`** SOR. It resolves the
target webstore + currency, optionally seeds from a quick-start template / existing promotion /
AI prompt, then persists via the composite-promotions Connect resource and reads the promotion
back to verify. It supports percentage / fixed-amount / fixed-price / bonus-product discounts,
buy-X-get-Y **qualifier**-gated offers (BOGO), scoped by webstore and/or buyer group, at
transaction, shipping, or product/category level. **The promo skill owns all body mechanics**
(target shape, `qualifierType`, per-type required fields) — recommend the *offer*, not the
payload. `describe(merchant-promotion-management)` for the full param schema before invoking.

**Mandatory draft-then-confirm gate — this is a live CRM write, not an insight.** The agent
MUST:

1. **Ground the recommendation** in the insight just shown (which product/account/segment, why,
   the proposed discount + duration + audience).
2. **Show the merchant the full draft** — discount, target (order / product / category),
   any qualifier (buy-X-get-Y), audience (webstore / buyer group), dates — in plain business
   terms, and **wait**.
3. **Create only after explicit confirmation, editing the draft on request first.** No
   confirmation → no write. The merchant may revise any draft dimension before it's created —
   discount type/amount, target, qualifier ("only if they buy 2"), audience ("Loyal Customers
   only"), dates. Apply each edit and **re-show**, looping until they confirm; only then create.
   This is edit-before-create — the draft isn't persisted until confirmed.
4. **Delegate the create** to `merchant-promotion-management` (which enforces the
   server's hard rules: ≥1 target + ≥1 segment; every qualifier carries a `qualifierType`),
   then confirm back what was created (name, discount, audience, live/inactive) — never the
   underlying resource or payload mechanics.

Default a freshly created promotion to **inactive** unless the merchant explicitly says to make
it live now; state which it is. Rollback (if asked): the delegated skill deletes the `Promotion`
record or sets it inactive.

## Security guardrail (applies to every insight and the promotion hand-off)

The agent authors SQL, so this skill owns injection defense:

- Store name/ids and any interpolated value are validated and single-quote-escaped.
- Only whitelisted `ssot__*` columns from the catalog may appear in dynamic
  segment/sort/filter positions — never a raw user string.
- Read-only: emit a single `SELECT` (or `WITH … SELECT`); reject any DML/DDL.
- Bound every query: store filter + a sane period and/or `LIMIT`.

## Definition of done

The agent resolved the store, generated a dialect-legal read-only query by adapting the
right anchor, ran it through `execute_query-sql`, and returned correctly-labeled rows —
or reported plainly that the datum is not available in Data Cloud.

<!-- skill-validate: ignore-start -->
<!-- codey:operations start -->
## Operations Reference

Operations this skill uses — routing and dependency reference.

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `pay-zen-commerce-merchant-insights-enumerate-stores` | read | — | `POST /services/data/v67.0/ssot/mcp/execute` | — |
| `data360-query-mcp-query-sql` | read | — | `POST /services/data/v67.0/ssot/mcp/execute` | `pay-zen-commerce-merchant-insights-enumerate-stores` |
| `data360-query-mcp-query-sql-status` | read | — | `POST /services/data/v67.0/ssot/mcp/execute` | `data360-query-mcp-query-sql` |
| `data360-query-mcp-query-sql-rows` | read | — | `POST /services/data/v67.0/ssot/mcp/execute` | `data360-query-mcp-query-sql-status` |
| `delegate-commerce-merchant-insights-account-health-churn` | delegate | — | → `pay-zen/commerce-merchant-insights-account-health-churn` | — |
| `delegate-commerce-merchant-insights-inventory-returns` | delegate | — | → `pay-zen/commerce-merchant-insights-inventory-returns` | — |
| `delegate-commerce-merchant-insights-order-shopper-lookups` | delegate | — | → `pay-zen/commerce-merchant-insights-order-shopper-lookups` | — |
| `delegate-commerce-merchant-insights-product-performance` | delegate | — | → `pay-zen/commerce-merchant-insights-product-performance` | — |
| `delegate-commerce-merchant-insights-segment` | delegate | — | → `pay-zen/commerce-merchant-insights-segment` | — |
| `delegate-commerce-merchant-insights-store-health` | delegate | — | → `pay-zen/commerce-merchant-insights-store-health` | — |
<!-- codey:operations end -->
<!-- skill-validate: ignore-end -->
