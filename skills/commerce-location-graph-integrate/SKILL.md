---
name: commerce-location-graph-integrate
description: "Use this skill when users want to use this workflow to propagate a Location-graph-affecting change downstream — BOPIS pickup eligibility (enable-location-bopis), a per-location pickup time window, or a ShippingCarrierMethod / LocationShippingCarrierMethod change (update-location-shipping-carrier-method) — to the. Trigger when users mention sync, location, graph."
metadata:
  version: "1.0"
---

# Managing Sync Location Graph

## When to Use This Skill

Use this workflow to propagate a Location-graph-affecting change downstream — BOPIS pickup
eligibility (enable-location-bopis), a per-location pickup time window, or a
ShippingCarrierMethod / LocationShippingCarrierMethod change
(update-location-shipping-carrier-method) — to the external Commerce Delivery Service. A
freshly-changed field isn't reflected in a delivery/pickup estimate until this publish
completes.

triggerFullLocationGraphSync takes NO parameters — it always publishes the FULL graph (every
location), not a scoped subset. This is a delegation target, most commonly reached via
delegates_to from another SOR right after that SOR's own change is verified; it can also run
standalone.

WIRE CONTRACT (verified live 2026-08-07 on bopis, as part of enable-location-bopis before this
extraction): POST /services/data/v68.0/commerce/delivery/location-graph/uploads with NO body ->
201 {id, status:"New", type:"CdsFullLocationGraphSync", success:true} on enqueue. The SAME path's
GET (checkFullLocationGraphSyncStatus) reports status.

TERMINAL-STATE CONTRACT — WIRE GOTCHA (traced 2026-08-22 against Core source, not just a class's
own doc-comment): the OAS's `status`/`type` PROPERTY NAMES are swapped from their actual
semantics on the wire. The lifecycle values (New/InProgress/Completed/Error) arrive in the wire's
`status` key even though the OAS enumerates them under the property it names `type` — confirmed
by the live-recorded response above ({status:"New", type:"CdsFullLocationGraphSync"} — "New" is
a lifecycle value, "CdsFullLocationGraphSync" is an operation-kind value). Terminal success =
status "Completed"; terminal failure = status "Error" OR "ServiceException" (the shipped
Location Management UI's own status check tests for "ServiceException", not the OAS-declared
"Error" — the shipped code and the OAS doc disagree, so both are treated as failure here); New /
InProgress = still running.
ERROR CONTENT DIFFERS BY FAILURE STATUS (traced 2026-08-24): "Error" is Core's curated
validation-failure path — its `error` field carries a real per-location message explicitly
designed for end-user display. "ServiceException" is a DIFFERENT, generic/transport-level
failure path (traced to the remoting call itself erroring, not a validation outcome) — every
observed example has an EMPTY error field, and there is no evidence its content is safe to show
customers on the rare case it isn't empty. Treat these two statuses differently when deciding
what to relay — see the poll step's own agent_guidance.

ENQUEUE IS NOT TERMINAL: the POST only enqueues; the downstream copy is not current until the
poll below reaches "Completed". Never say "saved and synced" merely because the enqueue POST
returned successfully.

## Workflow

Publish the full location graph downstream and poll to terminal success. Two steps:

### Phase 1: publish-location-graph -> POST triggerFullLocationGraphSync, NO params -> enqueues...

publish-location-graph -> POST triggerFullLocationGraphSync, NO params -> enqueues (status
     "New", not yet synced).

### Phase 2: poll-location-graph-sync-status -> bounded poll (every ~5s, up to...

poll-location-graph-sync-status -> bounded poll (every ~5s, up to 12 attempts) of
     checkFullLocationGraphSyncStatus until status reaches Completed (success) or
     Error/ServiceException (failure) or the attempts are exhausted (still in progress).

## Critical Constraints

**Preconditions:**

- The Delivery Estimation Service / location-graph feature must be enabled in the org, or the
publish is rejected. (check: `Delivery Estimation / location-graph sync enabled`)

**Operational rules:**

- DELEGATED vs STANDALONE: when invoked via delegates_to from another SOR (enable-location-bopis,
update-location-shipping-carrier-method, or any future caller), stay SILENT on completion — the
delegating SOR owns the single closing message + recap for the entity IT changed; this SOR is
silent plumbing to that caller. Only when invoked STANDALONE (an admin asked to publish/sync
directly, not through another SOR) does this SOR say the closing line itself.
- CUSTOMER-FACING WORDING (standalone only, terminal success): this SOR never writes/saves
anything itself — it only republishes whatever is CURRENTLY in Core. Say "Your location data
has been synced." NOT the "saved and synced" canonical line — that line implies a change was
just saved, which is only true for a DELEGATING caller that performed a write before handing
off here; a standalone invocation may simply be a manual re-publish with no new change at all.
This SOR doesn't create/own any entity and takes no per-entity input
(triggerFullLocationGraphSync is always a full, unscoped sync) — there's no single record to
name, so that one sentence is the whole standalone reply; no recap or link is possible here. On
terminal failure, see the poll step's own agent_guidance — use poll_error to say WHAT is wrong,
comparing the location(s) it names against any the caller has in mind before assuming it's
unrelated. Never say "CDS", "Commerce Delivery Service", or otherwise imply there are two
separate systems. Don't surface sObject/field API names, the Connect path, Ids, or raw HTTP
codes — poll_error's own message is already customer-appropriate, no further raw detail needed.
Keep the standalone reply under ~200 characters where possible (soft target, not a hard limit).

## Verification Checklist

After every write operation, confirm the effect by re-reading state:

- After `publish-location-graph`: call `poll-location-graph-sync-status`

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `publish-location-graph` | write | implemented | `triggerFullLocationGraphSync` | — |
| `poll-location-graph-sync-status` | verify | implemented | `checkFullLocationGraphSyncStatus` | `publish-location-graph` |

### Write operations

#### `publish-location-graph`

Publish the full location graph downstream. Runs with NO parameters — always a full sync, not
a scoped one.

**Call:** `triggerFullLocationGraphSync`   — status: `implemented`

### Verify operations

#### `poll-location-graph-sync-status`

Poll the location-graph sync job (enqueued by publish-location-graph) to terminal success. The
enqueue POST only returns status:"New" — the downstream copy is not current, and the change is
not actually synced yet, until this poll reaches a terminal state.

**Call:** `checkFullLocationGraphSyncStatus`   — status: `implemented`

**Depends on:** `publish-location-graph`
