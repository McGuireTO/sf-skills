---
name: commerce-fees-apply
description: "Use this skill when users want to use this SOR when a cancel or return operation needs to apply a fee. Trigger when users mention fees, support."
metadata:
  version: "1.0"
---

# Querying Fees Support

## When to Use This Skill

Use this SOR when a cancel or return operation needs to apply a fee. This is a REUSABLE MODULE
that asks whether to apply a fee, collects the appropriate fee fields based on operation type,
resolves fee product names to IDs, and returns properly-nested fee payloads for the caller to
merge into their preview/submit requests.

WHEN TO USE:
- User mentions "fee", "charge", "penalty", "restocking fee", "cancellation fee"
- During cancel/return flows when fees might apply
- When caller explicitly requests fee collection

OPERATION TYPES SUPPORTED:
- partial-cancel: Uses changeItemFees with new-fee-charge shape
- cancel-all: Uses changeItemFees with new-fee-charge shape + orderDeliveryGroupSummaryId
- return-preview/return-submit: Uses changeItemFees with new-fee-charge shape
- return-items: Uses returnOrderItemFees with fee-quantity-adjust shape (no amount)

OUTPUT CONTRACT:
Returns a fee payload object that the caller merges into their request:
{
  "feePayload": {
    "changeItemFees": [...] OR "returnOrderItemFees": [...]
  },
  "feeDescription": "human-readable fee summary for customer"
}

## Workflow

1. INVOKE fees-support with operation_type:
   result = invoke("fees-support", {operation_type: "partial-cancel", context_data: {orderId: "..."}})

2. MERGE result.feePayload into your preview/submit request:

- For partial-cancel, return-preview, return-submit:
     Parent MUST merge changeItemFees into EACH changeItem:
     previewRequest = {
       ...baseRequest,
       changeItems: [
         {
           ...itemData,
           changeItemFees: result.feePayload.changeItemFees  # PER-ITEM nesting
         }
       ]
     }

- For cancel-all:
     Parent merges changeItemFees at ROOT level:
     previewRequest = {
       ...baseRequest,
       changeItemFees: result.feePayload.changeItemFees  # ROOT-level nesting
     }

ChangeInputRepresentation (partial-cancel, return) only accepts changeItems[].changeItemFees[];
   root-level changeItemFees is silently ignored for these operations.

3. SURFACE fee impact from preview response:
   After preview, look for changeBalances to show customer the fee's financial impact.

4. INCLUDE result.feeDescription in customer-facing summary:
   "Preview: Your cancellation will proceed. {result.feeDescription}"

User: "Cancel item X and apply a $25 cancellation fee"

Agent:
1. Invoke fees-support:
   {operation_type: "partial-cancel", context_data: {orderSummaryId: "..."}}

2. fees-support collects:
   - fee_product_name: "Cancellation Fee"
   - amount: 25.00
   - amount_type: "AmountWithTax"
   - Resolves to product2Id + priceBookEntryId

3. fees-support returns:
   {
     feePayload: {
       changeItemFees: [{product2Id: "...", amount: 25.00, amountType: "AmountWithTax", ...}]
     },
     feeDescription: "A flat fee of $25.00 (Cancellation Fee) will be applied."
   }

4. Caller merges into preview request:
   POST /commerce/order-management/preview-cancel
   {
     orderSummaryId: "...",
     changeItems: [{orderItemSummaryId: "...", quantity: 1, reason: "..."}],
     changeItemFees: [{product2Id: "...", amount: 25.00, ...}]  # MERGED
   }

5. Caller shows customer:
   "Preview: Cancelling 1 unit of Product X. A flat fee of $25.00 (Cancellation Fee) will be applied.
    Total refund: $75.00 (original $100.00 - $25.00 fee)."

6. User confirms, caller submits with same merged payload.

## Critical Constraints

**Operational rules:**

- INTEGRATION PATTERN FOR CALLERS:
- IMPORTANT - DESCRIPTION vs REASON:
- `description` = free text customer wording (e.g., "Late cancellation after 24 hours")
- `reason` = REQUIRED picklist value from OrderItemSummaryChange.Reason (e.g., "Customer Request", "Unknown")
- The API validates `reason` against the picklist; unrecognized values return 400 INVALID_API_INPUT
- fees-support resolves the picklist and presents valid options for selection
- NESTING BY OPERATION TYPE:
- IMPORTANT: fees-support returns a BARE fee structure in changeItemFees[].
   The CALLER is responsible for nesting it correctly based on operation_type.
- CUSTOMER-FACING WORDING:
- NEVER say "changeItemFees", "product2Id", "priceBookEntryId", "returnOrderLineItemId"
- DO say "fee", "charge", "restocking fee", "cancellation fee"
- DO show the fee amount and product name in plain language
- DO surface the financial impact from preview changeBalances (e.g., "Total refund: $75.00")
- EXAMPLE INTEGRATION (partial-cancel):
- ERROR HANDLING:
- If fee product name not found: Ask user to verify the product name exists in their org
- If preview fails with fee: Show the error, offer to retry without fee
- If fee amounts seem wrong in preview: Surface changeBalances so customer can verify

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `check-fee-intent` | read | — | — | — |
| `determine-fee-shape` | read | — | — | — |
| `collect-fee-product-name` | read | — | — | — |
| `collect-fee-amount` | read | — | — | — |
| `resolve-fee-reasons` | read | — | `describeOrderItemSummaryChange` | — |
| `collect-fee-description-and-reason` | read | — | — | — |
| `resolve-fee-product-id` | read | — | `querySoql` | — |
| `collect-fee-quantity-adjust-fields` | read | — | — | — |
| `build-fee-payload-new-charge` | read | — | — | — |
| `build-fee-payload-quantity-adjust` | read | — | — | — |
| `return-no-fee` | read | — | — | — |

### Read operations

#### `check-fee-intent`

Ask whether to apply a fee

#### `determine-fee-shape`

Determine which fee structure to use based on operation type

#### `collect-fee-product-name`

Ask for the fee product name

**Inputs:**

- `fee_product_name` *(`string`)*

#### `collect-fee-amount`

Collect fee amount and amount type

**Inputs:**

- `amount` *(`number`)*
- `amount_type` *(`string`)*

#### `resolve-fee-reasons`

Resolve the org's allowed fee reasons from the live
OrderItemSummaryChange.Reason picklist. Required because the
controller validates `reason` against this picklist on both preview
and submit; sending an unrecognized value returns 400
INVALID_API_INPUT "No matching reason found."


**Call:** `describeOrderItemSummaryChange`

#### `collect-fee-description-and-reason`

Collect fee description (free text) and reason (picklist selection)

**Inputs:**

- `description` *(`string`)*
- `reason` *(`string`)*

#### `resolve-fee-product-id`

Resolve fee product name to product2Id and priceBookEntryId

**Call:** `querySoql`

**Inputs:**

- `fee_product_name` *(`string`)*

#### `collect-fee-quantity-adjust-fields`

Collect returnOrderLineItemId and quantities for fee adjustment (returnItems only)

**Inputs:**

- `returnOrderLineItemId` *(`string`)*
- `quantityReturned` *(`number`)*
- `quantityToCancel` *(`number`)*

#### `build-fee-payload-new-charge`

Build changeItemFees payload for new fee charge operations

#### `build-fee-payload-quantity-adjust`

Build returnOrderItemFees payload for fee quantity adjustment (returnItems)

#### `return-no-fee`

Return empty fee payload when user declines fee
