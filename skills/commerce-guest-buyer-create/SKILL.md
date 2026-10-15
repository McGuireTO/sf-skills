---
name: commerce-guest-buyer-create
description: "Use this skill when users want to use this workflow when a user wants to register an existing Account as a (guest) buyer for a specific Commerce webstore — the prerequisite that lets that account shop, or be shopped-on-behalf-of, in that store. Trigger when users mention register, guest, buyer."
metadata:
  version: "1.0"
  accessCheck: "(Account.exists) || (OrderManagement.orgHasRegisterGuestBuyerAPIEnabled) || (WebStore.READ)"
---

# Managing Register Guest Buyer

## When to Use This Skill

Use this workflow when a user wants to register an existing Account as a (guest) buyer for a specific Commerce webstore — the prerequisite that lets that account shop, or be shopped-on-behalf-of, in that store. Registration enrolls the account as a buyer for the store, adds it to the store's buyer group, and marks the account as a buyer; the confirmation should tell the user the account can now shop the store (and is in its buyer group), not just report "success".

Scope boundaries (pick-signal):
- The Account must ALREADY EXIST. This workflow does not create accounts, does not do buyer-group / entitlement setup beyond that enrollment, and does not start any shopping / cart / pricing flow — those live in separate SORs.
- B2B stores ONLY. B2CE and B2C stores are rejected by the server (ERROR_ENABLING_BUYER). Do NOT pre-check store Type client-side — attempt the call and translate the error. (Wire-verified: B2B ok, B2CE 400.)
- Portal users are NOT allowed (allowsPortalUsers=false on the resource).
- Idempotent: re-registering an already-registered account returns success:true again (wire-verified) — safe to re-run.

Never echo raw 0ZE / 001 Ids or the raw error envelope to a buyer — translate success and errors to friendly language and offer a next step on failure. See agent_guidance and steps[] for the path parameters, empty POST body, response handling, and precondition gates.

## Workflow

### Phase 1: discover-webstores -> numbered menu of store Names; user...

discover-webstores  -> numbered menu of store Names; user picks one.
                          The chosen record's Id becomes webstoreId.

### Phase 2: account-input choice -> if the user gave a...

account-input choice -> if the user gave a 001 Id: by-id (skip lookup).
                          If they gave a name: by-name -> identify-account
                          resolves Name -> accountId.

### Phase 3: register-guest-buyer -> POST (empty body); read success/errors

register-guest-buyer -> POST (empty body); read success/errors.

- The register endpoint is POST-only and takes NO body — the two path
  params (webstoreId 0ZE, accountId 001) are the whole contract. The
  response is success + errors only; there is no entity payload, so
  $.success is the confirmation. The call returns HTTP 200 for BOTH success
  and business-rule failures — always branch on $.success, never on the
  HTTP status alone.

- What registration ACCOMPLISHES (wire-verified): it enrolls the account as
  a buyer for the store AND adds it to that store's buyer group, and flips
  Account.IsBuyer to true. So the success message should tell the user the
  account can now shop the store (and is in its buyer group) — that is the
  user-visible outcome, not just "success:true".

- B2B ONLY — do NOT pre-check the store Type client-side. Registration works
  on B2B stores; B2CE (and B2C) are rejected by the server with a clear
  error (ERROR_ENABLING_BUYER, "not supported for B2CE store"). Let the API
  be the authority and translate its error rather than maintaining a
  client-side Type allow-list that could drift. WIRE-VERIFIED on q3Sdb27:
  BrightBundle Co (B2B) succeeded; RefArch USD (B2CE) returned 400
  success:false.

- Idempotent: re-registering an already-registered account on the same store
  returns success:true again (no error) — safe to re-run without a pre-check.
  WIRE-VERIFIED on q3Sdb27.

- Pre-validate both Id shapes at the agent layer to fail fast (0ZE / 001).

- Preconditions: org gate Register Guest Buyer API enabled
  + user check userHasRegisterGuestBuyerAPIAccess. Portal users are not
  permitted (allowsPortalUsers=false).

- The Account must ALREADY EXIST. This SOR does not create accounts and does
  not start shopping — those are separate workflows (out of scope).

- Customer-friendly wording: never echo raw 0ZE / 001 Ids, the raw error
  envelope, or errorCode strings; translate success and errors to plain
  language and always offer a next step on failure.

- Request body detail: the register action takes an EMPTY body — the RegisterGuestBuyerInputRepresentation has no fields, so send {} / no body. (The endpoint is the Order Management Repricing API register-guest-buyer action; see the register-guest-buyer step.)

## Critical Constraints

**Preconditions:**

- Org must have the Order Management Register Guest Buyer Connect API
enabled — this is the x-sfdc org-access-check on the postRegisterGuestBuyer
endpoint. Without it, the call returns FEATURE_NOT_ENABLED.
 (check: `Register Guest Buyer API enabled`)
- Calling user must pass the resource's user dynamic check
userHasRegisterGuestBuyerAPIAccess (declared on RegisterGuestBuyerResource
via userDynamicChecks). Without it the call is rejected (403); surface a
friendly access message, never the raw exception.
 (check: `userHasRegisterGuestBuyerAPIAccess`)
- The target Account (001-prefixed) must already exist. This SOR does NOT
create accounts — if the user references an account that doesn't exist,
resolve/confirm it first (identify-account) or stop and tell the user the
account must be created before it can be registered as a buyer.
 (check: `Account.exists`)
- Caller needs READ access to WebStore (to list/select the store) and to
Account (to resolve the account by name). Portal users are not permitted
(the resource sets allowsPortalUsers=false).
 (check: `WebStore.READ`)

**Operational rules:**

- TYPICAL FLOW
- KEY CONTRACTS (source-verified against the Register Guest Buyer resource):

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `discover-webstores` | read | implemented | `querySoql` | — |
| `identify-account` | read | implemented | `querySoql` | — |
| `register-guest-buyer` | write | implemented | `postRegisterGuestBuyer` | `discover-webstores` |

### Read operations

#### `discover-webstores`

Enumerate Commerce webstores with Id, Name, and Type. Runs FIRST; no
choice gate (always executes). The agent presents Names to the user and
threads the chosen record's Id into the register step as webstoreId.


**Call:** `querySoql`   — status: `implemented`

#### `identify-account`

Resolve an Account by name to its 001-prefixed Id. Runs ONLY when the user
supplied a company / account NAME rather than an Id (account-input = by-name).
Skipped when the user already gave a 001 Id.


**Call:** `querySoql`   — status: `implemented`

**Inputs:**

- `accountName` *(`String`)* — The company / account name (or fragment) the user gave. Matched with a
LIKE filter; present matches for the user to pick when more than one.
WILDCARD SAFETY: before binding, escape SOQL LIKE metacharacters in the
user's input — backslash-escape `\`, `%`, and `_` (\\ , \%, \_) so a
user cannot pass a bare `%`/`_` to enumerate every visible Account. A
lone `%` or empty string must be rejected, not run as "match all".

### Write operations

#### `register-guest-buyer`

Register the selected Account as a (guest) buyer for the selected webstore.
POST to the Order Management Repricing API register-guest-buyer action.
The request body is EMPTY — the whole contract is the two path params.
Response carries success + errors only (no entity payload).


**Call:** `postRegisterGuestBuyer`   — status: `implemented`

**Inputs:**

- `webstoreId` *(`String`)* — WebStore Id from discover-webstores (the store the user picked).
Pre-validate against ^0ZE[A-Za-z0-9]{12}([A-Za-z0-9]{3})?$ before invoking.

  - **Source:** output of `discover-webstores`
- `accountId` *(`String`)* — Account Id (001-prefixed) to register as a buyer. Sourced from
identify-account when the user gave a name (account-input = by-name), or
supplied directly by the user (by-id). Pre-validate against
^001[A-Za-z0-9]{12}([A-Za-z0-9]{3})?$ before invoking.


**Depends on:** `discover-webstores`
