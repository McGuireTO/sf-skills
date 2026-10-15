---
name: commerce-fulfillment-routing-analyze
description: "Use this skill when users want to use this workflow when a customer, CSR, or admin needs to understand why an order was fulfilled from a specific location. Trigger when users mention fulfillment, routing, explanation."
metadata:
  version: "1.0"
  accessCheck: "(FulfillmentOrder.OrderSummaryId) || (OrderManagement.ReadFulfillmentOrder) || (OrderManagement.orgHasOrderManagementEnabled)"
---

# Querying Fulfillment Routing Explanation

## When to Use This Skill

Use this workflow when a customer, CSR, or admin needs to understand why
an order was fulfilled from a specific location. The workflow resolves
an OrderNumber to its OrderSummary, finds all associated FulfillmentOrders,
then calls the routing explanation API for each to surface:
  • The winning routing criterion that determined the location
  • Per-rule scoring and contributions to the routing decision, as a table
  • Line-item allocation (fulfilled vs. requested vs. available elsewhere),
    as a table
  • Split-order context when multiple locations fulfill parts of one order

Presentation is table-first and customer-centric: routing details, rule
contributions, and line items render as markdown tables by default, not
just on request. This is a read-only diagnostic workflow — it explains
past routing decisions but does not modify routing or re-route orders.

## Workflow

fulfillment-routing-explanation is a READ-ONLY diagnostic workflow. It
does not modify routing, re-route orders, or change fulfillment assignments.

## Critical Constraints

**Preconditions:**

- Org must have Order Management enabled with fulfillment routing configured (check: `OrderManagement.orgHasOrderManagementEnabled`)
- User must have access to Order Management features and fulfillment data (check: `OrderManagement.ReadFulfillmentOrder`)
- The OrderSummary must have at least one FulfillmentOrder created. Orders
still in cart/checkout phase or canceled before fulfillment began will
have no FulfillmentOrders to explain. (check: `FulfillmentOrder.OrderSummaryId`)

**Operational rules:**

- EXECUTION PATH:
  1. resolve-order-summary-by-number → OrderNumber → OrderSummary Id
     (skip if caller has the Id directly)
  2. query-fulfillment-orders → find all FulfillmentOrders for this
     OrderSummary; detect split-order case
  3. get-routing-explanation → call once per FulfillmentOrder to get
     routing details
  4. synthesize-explanation → consolidate explanations into a customer-facing
     report: one lead sentence plus markdown tables for routing details,
     rule contributions, and line items (single-location or split-order)
- SPLIT-ORDER HANDLING:
When query-fulfillment-orders returns multiple FOs, call
get-routing-explanation for EACH one in sequence, then consolidate in
synthesize-explanation. Label each FO by its FulfillmentOrderNumber and
location so the customer knows which items come from where.
- FAILURE CASES:
- No FulfillmentOrders found: order hasn't reached fulfillment or was
  canceled early. Surface friendly message and STOP.
- 404 on routing-explanation: routing explanation not available (manual
  assignment or pre-explanation era). Fall back to basic location info
  from FulfilledFromLocation.Name.
- Permission errors: surface to user and STOP.
- CUSTOMER-FACING WORDING:
- Use "location" not "Location record"
- Use "order" not "OrderSummary"
- Use "items" not "OrderItemSummary"
- Translate routing criterion names to plain language (proximity, inventory,
  cost, speed, preference)
- No raw Ids, field names, or sObject types in customer text
- REPORTING FORMAT (see synthesize-explanation for the full spec):
- Table-first, not prose-first. Rule contributions and line-item
  allocations are always rendered as markdown tables, not gated behind
  "if the customer asks for detail."
- One lead sentence, then tables. Don't pad tabular data with a
  restating paragraph underneath it.
- Split orders get an overview table across all fulfillment orders, then
  a rule-breakdown + items table pair per fulfillment order.
- WHEN TO USE THIS WORKFLOW:
- "Why was my order sent from location X?"
- "Why are my items coming from different places?"
- "How did the system decide on this fulfillment location?"
- "Explain the routing for order #{orderNumber}"
- DO NOT USE for:
- Changing fulfillment location (use re-routing workflows)
- Canceling or modifying fulfillment orders
- Viewing shipment tracking (use shipment status workflows)

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `resolve-order-summary-by-number` | read | implemented | `querySoql` | — |
| `query-fulfillment-orders` | read | implemented | `querySoql` | `resolve-order-summary-by-number` |
| `get-routing-explanation` | read | implemented | `getFulfillmentOrderRoutingExplanation` | `query-fulfillment-orders` |
| `synthesize-explanation` | read | implemented | `conversational_synthesis` | `get-routing-explanation` |

### Read operations

#### `resolve-order-summary-by-number`

Resolve a customer-provided OrderNumber to its OrderSummary Id.
Customers and CSRs work with OrderNumber (the printed order number);
the fulfillment APIs require the internal OrderSummary Id (1Os...).

IMPORTANT: OrderNumber is NOT unique — a single OrderNumber can resolve
to multiple OrderSummaries (orgs reuse it across storefronts/locales).
When this step returns more than one row, surface candidates and ask
which one before proceeding.

**Call:** `querySoql`   — status: `implemented`

**Inputs:**

- `orderNumber` *(`String`)* — Customer-facing OrderNumber (from receipt/confirmation email).
Skip this step if caller already has the OrderSummary Id (1Os...).

#### `query-fulfillment-orders`

Query all FulfillmentOrders associated with the OrderSummary.
One OrderSummary can have multiple FulfillmentOrders when the order
is split across locations (e.g., some items from warehouse A, others
from store B). Each FulfillmentOrder has its own routing explanation.

**Call:** `querySoql`   — status: `implemented`

**Inputs:**

- `orderSummaryId` *(`String`)* — OrderSummary Id from resolve-order-summary-by-number, or passed
directly by caller.
  - **Source:** output of `resolve-order-summary-by-number`

**Depends on:** `resolve-order-summary-by-number`

#### `get-routing-explanation`

Call the routing explanation API for a specific FulfillmentOrder.
Returns sections-based routing explanation with the winning criterion, per-rule
contributions, location details, and line item information.

API contract (OMS Connect API v68.0 / min version 264):
GET /commerce/fulfillment/fulfillment-orders/{fulfillmentOrderId}/routing-explanation

Returns sections-based structure:
- success: boolean indicating API call success
- location: string - winning location name (top-level field)
- sections[]: array of section objects, each with:
  - name: section identifier ("summary", "rules", "lineItems")
  - rows[]: array of free-form Map<String,Object> with dynamic keys

NOTE: rows[] fields are @ConnectHidden(from=Apex) - REST/UI-API only.
Each row is a free-form key-value map with dynamic keys specific to the
section type. Keys vary by routing strategy and configuration.

**Call:** `getFulfillmentOrderRoutingExplanation`   — status: `implemented`

**Inputs:**

- `fulfillmentOrderId` *(`String`)* — FulfillmentOrder.Id from query-fulfillment-orders $.records[].Id.
Extracted per-iteration from the loop.
  - **Source:** output of `query-fulfillment-orders`
- `fulfillmentOrderNumber` *(`String`)* — FulfillmentOrder.FulfillmentOrderNumber from query-fulfillment-orders
$.records[].FulfillmentOrderNumber. Used for labeling in split-order scenarios.
  - **Source:** output of `query-fulfillment-orders`

**Depends on:** `query-fulfillment-orders`

#### `synthesize-explanation`

Final step: synthesize all routing explanations into a single
customer-facing report of markdown tables. When multiple
FulfillmentOrders exist (split order), this step consolidates their
individual explanations into one coherent set of tables — see
agent_guidance below for the full table spec.

This is a conversational synthesis step — no API call, just presentation
logic that threads outputs from get-routing-explanation.

**Call:** `conversational_synthesis`   — status: `implemented`

**Inputs:**

- `fulfillment_order_count` *(`integer`)* — Total number of FulfillmentOrders (from query-fulfillment-orders)
  - **Source:** output of `query-fulfillment-orders`
- `routing_explanations` *(`Array`)* — Array of routing explanation outputs from get-routing-explanation,
accumulated from the per-FO loop. Each array element is an object with:
fulfillment_order_number, success, location, whyItWon, whyItWonTooltip
(optional), selectionScore, selectionScoreTooltip (optional),
unitsFilled, rules (array, each row's isOverride optional), lineItems
(array, each row's elsewhere optional).
  - **Source:** output of `get-routing-explanation`

**Depends on:** `get-routing-explanation`
