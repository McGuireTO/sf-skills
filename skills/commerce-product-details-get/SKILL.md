---
name: commerce-product-details-get
description: "Use this skill when users want to product detail retrieval workflow with discovery preamble. Trigger when users mention product, details."
metadata:
  version: "1.0"
  accessCheck: "(Account.READ) || (OrderManagement.orgHasRepricingConnectAPIEnabled) || (Product2.READ) || (WebStore.READ)"
---

# Querying Product Details

## When to Use This Skill

Product detail retrieval workflow with discovery preamble. Three phases:

  PHASE A — Discovery (always runs)
    • discover-webstores enumerates available Commerce webstores with
      Id, Name, and Type. Agent presents Names to the user (never raw
      0ZE Ids); the chosen record's Id threads through downstream
      steps.

  PHASE B — Lookup dimension (one of two, mutually exclusive)
    • get-product-details → GET single product by SKU or Product2 Id
    • search-products     → GET list of products (keyword/pagination)

  PHASE C — Optional drill-down (only from search-products)
    • drill-down-product-details → same as get-product-details but
      invoked after the user picks a row from search-products results.
      Skipped if the user already called get-product-details directly.

The primary use case is get-product-details (by-SKU or by-ID) for CSRs
or customers who know the SKU or Product2 Id and want pricing/availability/
specs. The search-products branch is a fallback for "I don't know the exact
identifier" scenarios (keyword search across the catalog).

Customer-friendly rendering rules from product-search apply:
  • Product NAME verbatim (never abbreviate)
  • SKU verbatim (customers cross-reference these)
  • Price formatted with currency symbol + 2 decimals
  • Custom field API names rendered directly (OM API does not return labels)
  • NO internal sObject names, Ids, or step names

## Workflow

Render values VERBATIM from the response:
  • Product NAME ($.name) — never reformat, never abbreviate.
  • SKU ($.stockKeepingUnit) — verbatim. The full string is the
    cross-reference key customers use.
  • Status / availability (when present in $.fields) — verbatim
    string, never translate.

Format for human readability:
  • Price as `{currency-symbol}{amount}` with 2 decimals — `$24.99`,
    not `24.99 USD`. Use $.unitPrice or $.listPrice with
    $.currencyIsoCode.
  • Image URLs as thumbnails or hyperlinks — NEVER paste raw URLs.
    Use $.imageGroups[].
  • Custom-field RENDERING: OM API does not return field labels;
    render using API names from $.fields or maintain a separate
    label mapping if needed.

Empty product (404) — friendly "I couldn't find a product with SKU or
Id '<the SKU or Id the user supplied, rendered verbatim>' in this
webstore. Try a keyword search across the catalog?"

Likely page-based (NOT wire-verified yet; $.currentPage observed as null
in wire tests). Recommend:
  • ALWAYS SPECIFY pageSize EXPLICITLY (default varies by org).
  • Increment page until products.length < pageSize OR current_page *
    pageSize >= total_count.
  • Use total_count for "showing N of M" progress indicators.

webstoreId is REQUIRED on every step, but the SOR's discover-webstores
step sources it from a SOQL list of WebStore Id/Name/Type. The agent
presents Names to the user, the user picks, the chosen record's Id is
threaded through downstream steps via prior_step. The agent should
NEVER echo the raw 0ZE Id back to a buyer in customer-facing reply
text; CSRs may see it for disambiguation.

Usage is driven by the webstore's Type:
  • Type = B2B  → effectiveAccountId is REQUIRED (returns 400 MISSING_ARGUMENT
                  without it). Wire-verified behavior.
  • Type = B2C  → effectiveAccountId is OPTIONAL (classic B2C ignores it —
                  uniform pricing across buyers)

Note: Input schema marks required: false to allow agent to handle B2B/B2C
branching gracefully and prompt user when needed.

Unlike product-search, this SOR does NOT run discover-effective-account
(simpler authoring scope). The agent threads effectiveAccountId from
user input if the webstore requires it. For B2B webstores, prompt before
invoking: "I need a buyer account Id for this B2B webstore — do you have
one?" If the user doesn't provide it and the call returns 400
MISSING_ARGUMENT, re-prompt with error context.

Server-side patterns:
  webstoreId      → ^0ZE[A-Za-z0-9]{12}([A-Za-z0-9]{3})?$  (WebStore)
  skuOrProductId  → polymorphic — accepts SKU (any string) OR Product2 Id
                    (^01t[A-Za-z0-9]{12}([A-Za-z0-9]{3})?$)
Validate webstoreId at the agent layer before invoking. skuOrProductId
needs no pattern validation — it's customer-controlled and the endpoint
handles both SKU and Id formats.

## Critical Constraints

**Preconditions:**

- Org must have Order Management Repricing Connect API enabled —
both getProductDetails and getProductSearch endpoints carry the
x-sfdc.org-access-check for
Order Management repricing API access. Without this
feature, every step returns FEATURE_NOT_ENABLED.
 (check: `Order Management repricing API access`)
- User must have READ access to the WebStore (0ZE-prefixed record).
Unauthenticated/portal flows may be allowed depending on
webstore configuration; CSR flows require explicit WebStore.READ.
 (check: `WebStore.READ`)
- User must have READ access to Product2 — every step projects
Product2 fields (Name, StockKeepingUnit, custom fields). Without
FLS the response is empty.
 (check: `Product2.READ`)
- When querying a B2B webstore, the caller MUST supply effectiveAccountId
(returns 400 MISSING_ARGUMENT without it) and have READ access to that
Account. For B2C, effectiveAccountId is OPTIONAL. This SOR does NOT
enforce the B2B/B2CE branching that product-search does (no
discover-effective-account step) — the agent threads effectiveAccountId
from user input if needed.
 (check: `Account.READ`)

**Operational rules:**

- TYPICAL FLOW
- STEP 1 — Discover the webstore (always runs)
  Invoke discover-webstores. Present $.records[*] as a numbered menu
  using Name + Type:
    "Which store?
      1) BrightBundle Co (B2B)
      2) B2C Codecept (B2C)
      3) RefArch USD (B2CE)"
  NEVER echo the raw 0ZE Id to a buyer. Once the user picks, thread
  that record's Id as webstoreId through downstream steps.
- STEP 2 — Determine lookup dimension
  Ask the user: "Do you have a SKU or product Id (for direct lookup),
  or would you like to search by keyword?"
    • Direct lookup (by-detail) → get-product-details
    • Search (by-search)        → search-products → drill-down
- STEP 3a — Direct lookup (by-detail path)
  Prompt: "What's the SKU or product Id?"
  Invoke get-product-details with skuOrProductId (accepts both SKU
  and Product2 Id). If B2B/B2CE, also prompt for effectiveAccountId
  (optional guidance: "This webstore may require a buyer account Id
  for pricing").
- STEP 3b — Search (by-search path)
  Prompt: "What keyword should I search for?" (or "Show me all products").
  Invoke search-products with searchTerm (or omit for list-all).
  Present $.products[*] as a numbered menu using name + SKU. Once the
  user picks a row, invoke drill-down-product-details with that
  products[N].stockKeepingUnit.
- STEP 4 — Present results in customer-friendly wording
  • Product NAME ($.name) — verbatim, never abbreviate.
  • Price ($.unitPrice or $.listPrice) — with currency symbol from
    $.currencyIsoCode and 2 decimals.
  • SKU ($.stockKeepingUnit) — verbatim. Customers cross-reference
    SKUs when calling in; truncating breaks that.
  • Image URLs ($.imageGroups[]) — present as thumbnails or hyperlinks,
    NOT raw URLs.
  • Custom field values ($.fields.{customFieldApiName__c}) — OM API
    does not return field labels; render using API names or maintain
    a separate label mapping if needed.
  NO internal field names, sObject names, FQCNs, internal step names,
  18-char Ids, webstoreId, or Apex class names in the user-facing
  reply.
- STEP 5 — Hand off to cart / order actions
  OUT OF SCOPE for this SOR. The agent picks the next workflow from
  the conversation, not from this SOR. Likely targets: add-to-cart,
  place-order, etc. (separate SORs).
- CUSTOMER-FRIENDLY WORDING RULES
- Never echo:
  • Apex class names, FQCNs, internal step names.
  • webstoreId — internal Id; customers shouldn't see 0ZE identifiers
    in chat.
  • Raw error envelope ($.errors[].errorCode) — translate to friendly
    language. INVALID_ID_FIELD → "I don't recognize that product Id";
    FEATURE_NOT_ENABLED → "your org doesn't have Order Management
    Repricing API enabled."
- EMPTY RESULTS vs ERRORS
- HTTP errors (need re-verification against OM endpoint):
  400 INVALID_ID_FIELD       → documented for id-shape mismatch (webstoreId),
                                but observed as 404 NOT_FOUND in wire tests
                                against Catalog endpoint. Error code semantics
                                need re-verification against the OM endpoint
                                (/commerce/order-management/webstores/...).
                                Pre-validate webstoreId at the agent layer to
                                fail fast. skuOrProductId accepts any string,
                                so no pattern validation needed.
  401 / 403                  → user lacks WebStore READ or buyer
                                access. Surface "you don't have access
                                to this webstore" — never the raw
                                PermissionDeniedException.
  404                        → product not found. Offer to retry as
                                a keyword search.
  503 FEATURE_NOT_ENABLED    → org missing Order Management Repricing
                                API. Surface "your org doesn't have
                                Order Management Repricing API enabled"
                                — direct the user to Setup if
                                appropriate.
- PAGINATION (search-products only)
- WEBSTOREID — SOURCED FROM DISCOVERY
- EFFECTIVE ACCOUNT ID (driven by webstore type)
- ID-SHAPE PRE-VALIDATION (catches 400s before round-trip)
- SKU ACCEPTANCE RESTORED (2026-06-30)
- WIRE-VERIFIED on q3-som-e2e: The Order Management Repricing API's
{skuOrProductId} path parameter ACCEPTS BOTH SKU and Product2 Id. The
previous 404 on SKU "6010050" was caused by using the WRONG ENDPOINT
(Catalog API /commerce/webstores/{webstoreId}/products/{productId},
which only accepts Product2 Id). The CORRECT endpoint is Order Management
API /commerce/order-management/webstores/{webstoreId}/products/{skuOrProductId},
which accepts both. This SOR now uses the correct OM endpoint.

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `discover-webstores` | read | implemented | `querySoql` | — |
| `get-product-details` | read | implemented | `getProductDetails` | `discover-webstores` |
| `search-products` | read | implemented | `getProductSearch` | `discover-webstores` |
| `drill-down-product-details` | read | implemented | `getProductDetails` | `search-products` |

### Read operations

#### `discover-webstores`

Enumerate active Commerce webstores with Id, Name, and Type. Runs
FIRST in the workflow; no choice gate (always executes). The agent
presents Names to the user and threads the chosen record's Id
through downstream steps.


**Call:** `querySoql`   — status: `implemented`

#### `get-product-details`

Retrieve detailed product information by SKU or Product2 Id. The
{skuOrProductId} path parameter accepts both SKU (e.g., "6010050")
and Product2 Id (01t-prefixed). Returns prices, media, custom fields,
variations, and bundle children (all controlled via exclude* query
params).


**Call:** `getProductDetails`   — status: `implemented`

**Inputs:**

- `webstoreId` *(`String`)* — WebStore Id sourced from discover-webstores. The agent
updates this after the user picks a webstore from
discover-webstores.$.stores. Pre-validate against
^0ZE[A-Za-z0-9]{12}([A-Za-z0-9]{3})?$ before invoking.

  - **Source:** output of `discover-webstores`
- `skuOrProductId` *(`String`)* — SKU or Product2 Id. Accepts either a free-text SKU (e.g.,
"6010050") or a Product2 Id (01t-prefixed, 15- or 18-char).
The endpoint handles both — no pre-routing required. For
Product2 Ids, the pattern is
^01t[A-Za-z0-9]{12}([A-Za-z0-9]{3})?$; for SKUs, any string
format is allowed (customer-controlled).

- `effectiveAccountId` *(`String`)* — Buyer Account Id for B2B buyer-scoped pricing. REQUIRED for B2B
webstores (returns 400 MISSING_ARGUMENT without it); OPTIONAL for
B2C. Marked required: false to allow agent to prompt user when needed.
This SOR does not run discover-effective-account (simpler than
product-search) — the agent threads effectiveAccountId from user
input if the webstore requires it.

- `currencyCode` *(`String`)* — ISO 4217 currency code (e.g. USD, EUR). Optional — server
defaults to the webstore's default currency if omitted.

- `excludePrices` *(`Boolean`)* — Set to true to omit prices from the response. Useful for
catalog browsing without pricing context.

- `excludeMedia` *(`Boolean`)* — Set to true to omit media (images, videos) from the response.
Useful for lightweight lookups.

- `excludeAttributeSetInfo` *(`Boolean`)* — Set to true to omit attribute set info. Useful for
non-variation products.

- `excludeVariationInfo` *(`Boolean`)* — Set to true to omit variation info (parent/child relationships).
Useful for non-variation products.

- `excludeBundleChildrenInfo` *(`Boolean`)* — Set to true to omit bundle children info. Useful for
non-bundle products.

- `excludeQuantityRule` *(`Boolean`)* — Set to true to omit quantity rule info. Useful when quantity
constraints are not relevant.


**Depends on:** `discover-webstores`

#### `search-products`

List products from a webstore with optional keyword search and
pagination. Returns a list of product summaries; the user picks
one, then drill-down-product-details retrieves full detail.


**Call:** `getProductSearch`   — status: `implemented`

**Inputs:**

- `webstoreId` *(`String`)* — WebStore Id sourced from discover-webstores. Pre-validate
against ^0ZE[A-Za-z0-9]{12}([A-Za-z0-9]{3})?$.

  - **Source:** output of `discover-webstores`
- `searchTerm` *(`String`)* — Free-text query. Matched against product Name + indexed
attributes. Optional — omit for "list all products."

- `effectiveAccountId` *(`String`)* — Buyer Account Id for B2B buyer-scoped pricing. REQUIRED for B2B
webstores (returns 400 MISSING_ARGUMENT without it); OPTIONAL for
B2C. Marked required: false to allow agent to prompt user when needed.

- `page` *(`Integer`)* — Page index. Pagination indexing and behavior NOT wire-verified
yet — may be 0-based or 1-based. Default to 0/1 on first call;
increment for next page.

- `pageSize` *(`Integer`)* — Rows per page. Server default varies by org (likely 20 or 25).
Recommend 20 for chat-list ergonomics.


**Depends on:** `discover-webstores`

#### `drill-down-product-details`

Retrieve full product detail for a product the user picked from
search-products results. Same as get-product-details but invoked
after a search result selection. Only runs on the by-search path.


**Call:** `getProductDetails`   — status: `implemented`

**Inputs:**

- `webstoreId` *(`String`)* — WebStore Id from search-products's webstore_id echo (originally
sourced from discover-webstores).

  - **Source:** output of `search-products`, `discover-webstores`
- `skuOrProductId` *(`String`)* — The user's picked product SKU, sourced from
search-products.$.products[*].stockKeepingUnit. OM API search
results expose stockKeepingUnit (not productId), which the detail
endpoint accepts via skuOrProductId path parameter.

- `effectiveAccountId` *(`String`)* — Buyer Account Id, threaded from search-products's input.
REQUIRED for B2B webstores (returns 400 MISSING_ARGUMENT without it);
OPTIONAL for B2C. Marked required: false to allow agent to prompt
user when needed.

  - **Source:** output of `search-products`
- `currencyCode` *(`String`)* — Currency code from search-products's input. Optional.

  - **Source:** output of `search-products`

**Depends on:** `search-products`
