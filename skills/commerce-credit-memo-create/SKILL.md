---
name: commerce-credit-memo-create
description: "Use this skill when users want to use this workflow to turn a return/cancel/adjust ChangeOrder into a POSTED CreditMemo and confirm it landed. Trigger when users mention create, credit, memo."
metadata:
  version: "1.0"
  accessCheck: "(OrderManagement.orgHasOrderManagementConnectAPIEnabled) || (UserPermissions.UseOrderManagementAPIs || UserPermissions.UseCreateCreditMemo)"
---

# Managing Create Credit Memo

## When to Use This Skill

Use this workflow to turn a return/cancel/adjust ChangeOrder into a POSTED
CreditMemo and confirm it landed. It does TWO things:

  changeOrderIds  ->  create-credit-memo (postCreateCreditMemo, Core posts it)
                  ->  verify-credit-memo (POSTED, Balance > 0, account surfaced)

WHEN TO USE:
  • You have ChangeOrder Id(s) (801-prefix) from a prior return/cancel/adjust
    submit and need a posted CreditMemo — e.g. before an ensure-refunds-async
    refund, a store-credit (ensure-payment-credit) issue, or an invoice
    settlement.
  • You want the memo as an intermediate artifact WITHOUT immediately refunding
    (billing/accounting, manual ops). ensure-order-refund calls this SOR for its
    Phase-2 and then runs the refund itself.

KEY CONTRACTS (from Core source):
  1. postCreateCreditMemo posts the memo (CreditMemoStatus.Posted) before
     returning creditMemoId — the output is a real, persisted, POSTED CreditMemo.
  2. A credit memo is built from ChangeOrder Ids; at least one non-empty
     changeOrderIds is required. There is nothing to create for an
     excess-funds-only refund (that path does not use this SOR).
  3. The memo's BillingAccount must match the OrderSummary's Account (unless the
     org sets OrgPermissions.fundsAccountValidationOff) — surfaced here so the
     caller can enforce the account-match rule before refunding.

## Workflow

This SOR does NOT move money. It stops at a verified POSTED CreditMemo. The
caller decides what to do next — ensure-refunds-async (cash refund),
ensure-payment-credit (store credit), or invoice settlement. ensure-order-refund
delegates here for its Phase 2, then runs the async refund itself.

## Critical Constraints

**Preconditions:**

- Org must have Order Management Connect API enabled. Composed in Core as
orgHasOrderManagementEnabled && OrgPermissions.OMConnAPIKillSwitch. (check: `Order Management API enabled`)
- User must be able to create a credit memo. Core access check
userHasCreateCreditMemo =
UserPermissions.UseOrderManagementAPIs || UserPermissions.UseCreateCreditMemo. (check: `UserPermissions.UseOrderManagementAPIs || UserPermissions.UseCreateCreditMemo`)
- A ChangeOrder must already exist for the OrderSummary (from a prior
return/cancel/adjust). A credit memo can only be created from ChangeOrder
Ids; without one there is nothing to build. (check: `Order.RecordType == 'ChangeOrder' AND Order.GrandTotalAmount != 0`)

**Operational rules:**

- ORCHESTRATION MAP:
  Phase 1: CREATE
    create-credit-memo (postCreateCreditMemo → POSTED CreditMemo Id)
  Phase 2: VERIFY (hard gate)
    verify-credit-memo (POSTED, Balance > 0, BillingAccount surfaced)
- OUTPUT CONTRACT (what a caller consumes — the verify-credit-memo step's output
keys, all snake_case):
  • credit_memo_id        — the verified POSTED CreditMemo Id
  • credit_memo_balance   — its current Balance (the PRE-refund balance a caller
                            can use as the ground-truth baseline for a later
                            balance-drop check)
  • billing_account_id    — for the OrderSummary-account match rule
  • credit_memo_status    — 'Posted'
  (Currency is NOT returned — CreditMemo.CurrencyIsoCode exists only under
   multi-currency and would 400 the verify query on a single-currency org.
   Derive display currency from the order/org context.)
- DO NOT use this for an excess-funds-only refund (no ChangeOrder, no credit memo);
that path skips credit-memo creation entirely.
- WORDING RULES:
  • Never expose sObject names, raw Salesforce IDs, or internal field names.
  • Never hardcode '$' — render amounts in the order/org currency. (Do NOT read
    CreditMemo.CurrencyIsoCode: it exists only on multi-currency orgs and 400s
    the verify query elsewhere.)

## Verification Checklist

After every write operation, confirm the effect by re-reading state:

- After `create-credit-memo`: call `verify-credit-memo`

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `create-credit-memo` | write | implemented | `postCreateCreditMemo` | — |
| `verify-credit-memo` | verify | implemented | `query` | `create-credit-memo` |

### Write operations

#### `create-credit-memo`

Create a CreditMemo from the ChangeOrder Ids. Core explicitly posts it
(CreditMemoStatus.Posted) before returning its Id, so the output is a
real, persisted, POSTED CreditMemo — exactly what a downstream refund
requires.

**Call:** `postCreateCreditMemo`   — status: `implemented`

**Inputs:**

- `orderSummaryId` *(`String`)* — OrderSummary Id (from the caller).
- `changeOrderIds` *(`Array`)* — Change Order (801-prefix) Ids to build the credit memo from (from the caller's changeOrderIds input).
  - schema: `{'minItems': 1, 'items': {'type': 'string', 'pattern': '^(801)\\w{12,15}$'}}`

**Rollback:** Creating a credit memo is effectively irreversible via this API. A posted
CreditMemo can be voided/recovered through the billing Connect APIs
(billing.connect.api.postVoidPostedCreditMemo /
billing.connect.api.postCreditMemoRecovery), not through Order Management.

### Verify operations

#### `verify-credit-memo`

Confirm the CreditMemo exists, is POSTED, and has Balance > 0. This is the
single most important precondition for any downstream refund — it rejects a
missing credit memo or null/zero/negative balance. Also surfaces
BillingAccount for the account-match rule.

**Call:** `query`   — status: `implemented`

**Inputs:**

- `creditMemoId` *(`String`)* — CreditMemo Id from create-credit-memo.credit_memo_id.
  - **Source:** output of `create-credit-memo`

**Depends on:** `create-credit-memo`
