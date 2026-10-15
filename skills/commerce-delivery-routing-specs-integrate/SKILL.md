---
name: commerce-delivery-routing-specs-integrate
description: "Use this skill when users want to use this workflow to propagate FulfmtRoutgSpec changes — most commonly a ProcessingTimeSpec temporary override just created by create-temporary-processing-time-override — to the external Commerce Delivery Service (CDS). Also use when you created/changed one spec and want only it to go live. Trigger when users mention sync, delivery, routing, specs."
metadata:
  version: "1.0"
  accessCheck: "CommerceDelivery.orgHasDeliveryRoutingEngineFeatureEnabled"
---

# Managing Sync Delivery Routing Specs

## When to Use This Skill

Use this workflow to propagate FulfmtRoutgSpec changes — most commonly a ProcessingTimeSpec
temporary override just created by create-temporary-processing-time-override — to the external
Commerce Delivery Service (CDS). A spec created/edited in Core is NOT live in the CDS until it
is synced. Two modes, chosen via the sync-scope choice_point:

  1. SINGLE (targeted): syncSingleFulfmtRoutgSpec — POST
     /commerce/delivery/fulfillment-routing-specs/sync/{specId} — pushes just ONE spec, by its
     1fH... Id. Use when you created/changed one spec and want only it to go live. Smaller blast
     radius. Verified live on bopis (2026-08-05): 201 {success:true, errors:[]}.
  2. ALL (org-wide bulk): syncAllFulfmtRoutgSpecs — POST
     /commerce/delivery/fulfillment-routing-specs/sync (no body) — loads and pushes EVERY
     FulfmtRoutgSpec in the org. Full reconcile; also re-pushes any other pending specs.
     Verified live on bopis (2026-08-04): 201.

Both are owned by CC OM Not Hotdog and gated by "Delivery Routing Engine enabled". NOTE: the
single-spec endpoint is live in Core but currently MISSING from the generated OAS/corpus (a
generation-staleness gap — the raw Core source spec lists it), so it's authored here against the
verified live Core contract (minVersion 262 = API v62+, path {specId}, no request body, 201).

## Workflow

Propagate FulfmtRoutgSpec changes to the external Commerce Delivery Service. TWO modes via the
sync-scope choice_point:
  - single -> sync-single-fulfillment-routing-spec: POST
    /commerce/delivery/fulfillment-routing-specs/sync/{specId} (spec Id in path, no body) —
    pushes ONLY that spec. Verified live 2026-08-05 (201). Requires a 1fH... spec Id.
  - all -> sync-all-fulfillment-routing-specs: POST
    /commerce/delivery/fulfillment-routing-specs/sync (no body, or an optional
    fulfmtRoutgSpecSyncInput.type filter — ProcessingTime | Markdown) — bulk sync of every spec,
    or every spec of one type. Verified live 2026-08-04 (201, unscoped).

Prefer SINGLE right after creating/editing one spec (e.g. a holiday ProcessingTimeSpec):
pass that spec's id. Use ALL for a full reconcile, or when no single id is in hand (single
requires the spec Id); when the caller knows the spec's Type, pass it on the ALL branch too
(type=ProcessingTime / type=Markdown) so an org-wide reconcile can't be failed by a malformed,
unrelated spec of the other type sharing the same bulk batch.

This is the propagation step a ProcessingTimeSpec needs to go live — a created spec exists in
Core but isn't fully in effect until synced. It's the delegation target of
create-temporary-processing-time-override — a deterministic caller (see the EXCEPTION above):
it only ever creates ONE spec per run, so it hardcodes sync-scope: single and passes the new
spec id, without asking. Can also run standalone after any FulfmtRoutgSpec create/edit.

## Critical Constraints

**Preconditions:**

- The Delivery Routing Engine feature must be enabled in the org (Connect org-access-check
"Delivery Routing Engine enabled"), or the sync is rejected. (check: `Delivery Routing Engine enabled`)

**Operational rules:**

- ASK which scope the customer wants (default single — smaller blast radius) — this MUST be an
explicit customer choice, never a silently-guessed default, even when this SOR is reached via
delegates_to: a delegating SOR must surface the question, not guess on the customer's behalf.
- EXCEPTION — deterministic callers may hardcode instead of asking: the "always ask" rule exists
to stop an AMBIGUOUS scope being silently guessed wrong (that was the actual 2026-08-17
incident — an agent defaulted to a scope it wasn't sure about). It does NOT apply when the
calling SOR's own flow makes the correct scope a certainty rather than a guess. The bar for
this is a STRUCTURAL invariant in the caller's OWN steps, provable by reading them — not a
feeling that a scope is "probably" right. e.g. create-temporary-processing-time-override only
ever creates exactly ONE spec per run (its create step has no fan-out, no loop, no batch input),
so "single" is the only correct answer there; asking would just be friction over a question with
one possible answer, not a real choice. That caller hardcodes sync-scope: single unconditionally.
A future caller claiming this exception must be able to point to the equivalent structural
guarantee in its own flow (e.g. "this step processes exactly one record because X"), not just
assert confidence — when a caller's own scope IS genuinely ambiguous (it doesn't know in
advance whether the customer wants one spec or a full reconcile), it must still ask.
- CORPUS NOTE: the single-spec sync is live in Core but missing from the generated OAS (staleness
gap; the raw Core source spec lists it) — authored against the verified live contract.
- DELEGATED vs STANDALONE: when invoked via delegates_to from another SOR, stay silent on
completion — the delegating SOR owns the single closing message to the customer. Only when
invoked STANDALONE (directly, not via delegation) should this SOR itself say the canonical
closing line below.
- CUSTOMER-FACING WORDING (standalone only): this SOR never writes/saves anything itself — it
only pushes whatever already exists in Core (same reasoning as the sibling sync-location-graph)
— NOT the "saved and synced" canonical line, which implies a write just happened here; that
write, if any, belongs to whichever caller created/edited the spec before reaching this SOR.
Say which spec(s) were synced, not just "synced" generically:
  - SINGLE: "Your routing spec has been synced." — this SOR only ever receives the raw specId
    (1fH...) as input — no Name or ExternalReference. Never speak that raw Id in prose. Instead
    give a best-effort link with NEUTRAL anchor text (you don't have a friendly name to use):
    [view routing spec](<orgHost>/lightning/r/FulfmtRoutgSpec/<specId>/view) — keep the `]` and
    `(` on the same line with no space/break between them, or the Markdown link renders broken.
    If the caller (a delegating SOR) already named the spec by its own Name/ExternalReference in
    ITS recap, this branch is DELEGATED, not standalone, so you're silent anyway (see above) —
    this wording only fires when an admin invoked sync-delivery-routing-specs directly with a
    bare Id and no other SOR is speaking for them.
  - ALL: no single entity to name or link. If a type filter (ProcessingTime/Markdown) was
    sent, say "Your <type> routing specs have been synced." (e.g. "Your processing-time
    routing specs have been synced.") — NOT the unqualified "all routing specs," which
    overclaims scope when only one type was actually touched. Only say "Your routing specs
    have been synced." (unqualified) when NO type filter was sent — a genuinely unscoped,
    every-type sync.
RECAP LAYOUT — MULTIPLE syncs standalone in one conversation (e.g. "sync spec A and spec B" —
two sync-scope: single calls with different spec Ids — or "sync all processing-time specs,
then all markdown specs" — two sync-scope: all calls with different type filters): give ONE
consolidated table instead of repeating the sentence form per sync —
  | Spec / Scope | Outcome |
  |---|---|
  | [view routing spec](<orgHost>/lightning/r/FulfmtRoutgSpec/<specId>/view) | synced |
  | all processing-time specs | synced |
One row per sync performed in this conversation. For a SINGLE-mode row, reuse the same
best-effort NEUTRAL-anchor-text link as above (still no friendly name to show — the anchor
text is identical across rows, only the link target differs). For an ALL-mode row, name the
type filter if one was sent (e.g. "all processing-time specs"), or "all routing specs" if
unscoped. Use whichever outcome word applies (synced / could not be synced — see the SINGLE/ALL
guidance above for what failure looks like). Say the canonical opening line once, before the
table, if every row synced — e.g. "Your routing specs have been synced." Omit it only when a
row could not be synced, since that's the one outcome it would misstate; in that case name the
failed rows separately from the succeeded ones.
Keep it under ~200 characters of VISIBLE text where possible (soft target — the link URL
doesn't count). Never say "CDS",
"Commerce Delivery Service", or "delivery service" as something distinct from the setup change
— describe it as one seamless save. Don't surface the Connect path, sObject names, or
raw HTTP codes.

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `sync-single-fulfillment-routing-spec` | write | implemented | `syncSingleFulfmtRoutgSpec` | — |
| `sync-all-fulfillment-routing-specs` | write | implemented | `syncAllFulfmtRoutgSpecs` | — |

### Write operations

#### `sync-single-fulfillment-routing-spec`

Targeted sync — push a SINGLE FulfmtRoutgSpec (e.g. the ProcessingTimeSpec just created) to
the Commerce Delivery Service by its Id, so only that spec goes live in the CDS.

**Call:** `syncSingleFulfmtRoutgSpec`   — status: `implemented`

**Inputs:**

- `specId` *(`String`)* — The FulfmtRoutgSpec / ProcessingTimeSpec Id to sync (1fH...). Provided by the caller at
invocation: a delegating SOR passes it (e.g. create-temporary-processing-time-override's
create-temporary-override.spec_id), or a standalone admin supplies it directly (e.g.
DeliveryEstimationSetup.ProcessingTimeSpecId).

#### `sync-all-fulfillment-routing-specs`

Org-wide bulk sync — load every FulfmtRoutgSpec for the org (optionally scoped to one Type)
and push the bulk payload to the Commerce Delivery Service, making all Core-side spec changes
live at once.

**Call:** `syncAllFulfmtRoutgSpecs`   — status: `implemented`

**Inputs:**

- `type` *(`String`)* — Optional FulfmtRoutgSpec.Type to scope the bulk sync to (ProcessingTime | Markdown). Omit
to sync every FulfmtRoutgSpec regardless of type — verified server-side
(CDSFulfmtRoutgSpecSyncRequestMapper): no body, or a blank type, is explicitly
backward-compatible and syncs all types. SET THIS whenever the caller only cares about one
type (e.g. delegated from a ProcessingTime-only flow): the bulk endpoint loads + PUTs every
matching spec in ONE call, so one malformed/incompatible spec of the OTHER type elsewhere in
the org can fail the entire batch even though the spec you care about is fine. An
unrecognized value 400s (INVALID_INPUT).
