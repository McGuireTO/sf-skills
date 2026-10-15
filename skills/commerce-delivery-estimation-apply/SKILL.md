---
name: commerce-delivery-estimation-apply
description: "Use this skill when users want to use this workflow to (re-)enable and push a delivery estimation configuration so the delivery estimation service picks up the current DeliveryEstimationSetup values — e.g. Trigger when users mention enable, push, delivery, estimation, setup."
metadata:
  version: "1.0"
  accessCheck: "CommerceDelivery.orgHasDeliveryEstimationServiceEnabled"
---

# Managing Enable And Push Delivery Estimation Setup

## When to Use This Skill

Use this workflow to (re-)enable and push a delivery estimation configuration so
the delivery estimation service picks up the current DeliveryEstimationSetup values
— e.g. after update-delivery-estimation-setup changes the processing time. It calls
the Commerce Delivery "Delivery Configuration Setup" endpoint
(POST /commerce/delivery/estimation/configuration) with isEnabled=true and the
configuration's ExternalReference in the body. This SOR is the delegation target of
update-delivery-estimation-setup's push step, and can also run standalone.

Verified live against a Core org (Connect API v67.0, 2026-08-03):
  • POST /commerce/delivery/estimation/configuration?isEnabled=true with body
    {"deliveryConfigurationExternalReference":"west"} → HTTP 201,
    {success:true, errors:[]}.
  • The body key is deliveryConfigurationExternalReference — the
    DeliveryEstimationSetup record's ExternalReference field (NOT its 2A0 Id).
  • isEnabled is a QUERY param (true = enable + push; false = disable).

## Workflow

Enable + push a delivery estimation configuration. Single implemented Connect call:
  POST /commerce/delivery/estimation/configuration?isEnabled={isEnabled}
  body {"deliveryConfigurationExternalReference": "<ExternalReference>"}
keyed on the DeliveryEstimationSetup record's ExternalReference (NOT the 2A0 Id). isEnabled is
the caller's resolved value (true to enable — the default; false to disable) — never hardcode
true here regardless of what the caller asked for.

This SOR is the delegation target of update-delivery-estimation-setup,
update-location-delivery-processing-time, update-delivery-business-hours,
update-location-business-hours, and update-location-temporary-operating-hours —
each calls it automatically, right after its own change is verified, and never
asks the admin first. It also runs standalone. Success = HTTP 201 {success:true,
errors:[]} (verified live 2026-08-03 on record "west"). No GET echoes the service
state, so the response body is the confirmation.

## Critical Constraints

**Preconditions:**

- The Delivery Estimation Service must be enabled/provisioned in the org (Connect
org-access-check "Delivery Estimation Service enabled"). Without it the POST is
rejected. (check: `Delivery Estimation Service enabled`)
- A DeliveryEstimationSetup record with the target ExternalReference must exist
(created per delivery Channel + LocationGroup). Obtain its ExternalReference via
update-delivery-estimation-setup's resolve step, or a SOQL read of
DeliveryEstimationSetup.ExternalReference. (check: `DeliveryEstimationSetup record with the given ExternalReference exists`)

**Operational rules:**

- DELEGATED vs STANDALONE: when invoked via delegation, do NOT emit your own
customer-facing sentence — the delegating SOR already owns the single closing
message + recap for the entity it changed; this call is silent plumbing to that
caller. Only when invoked STANDALONE (an admin asked to push directly, not
through another SOR) do you say the closing line yourself.
- CUSTOMER-FACING WORDING (standalone only): say the canonical line verbatim, THEN a second
sentence naming the actual outcome — never let the canonical line stand alone when the outcome
needs disambiguating, and never fold the outcome into the same sentence with a dash/clause (that
reads as walking the save back rather than adding detail; see the sibling SORs in this family for
the same two-sentence pattern):
  - isEnabled true (the common case): "Your change has been saved and synced." Followed by
    which setup (see below) — always, not just when it happens to be obvious from context;
    the "Either way, name which setup" instruction below is unconditional and takes
    precedence over any impression that naming it is optional here.
  - isEnabled false (disabling): "Your change has been saved and synced." "Delivery estimation
    has been disabled for <setup>." — the second sentence is REQUIRED here (not optional like the
    true case's OWN second sentence naming the setup) because "saved and synced" alone doesn't
    communicate that the configuration is now OFF, and could be misread as "delivery estimation
    is now active and in sync."
Either way, name which setup: the deliveryConfigurationExternalReference input you were
called with (e.g. "Setup: west"). This SOR doesn't create/own a record, but it DOES act on a
specific, caller-identified one — always name it, don't just confirm generically. When invoked
via DELEGATION, don't attempt a link yourself — you're silent anyway (see DELEGATED vs
STANDALONE above), so building one would be unused work; that's the delegating caller's job if
it already has the Id. When invoked STANDALONE, run resolve-delivery-estimation-setup-id (below)
first and, on exactly one match, link the setup instead of naming it in plain text — this skill
only ever receives the ExternalReference itself, never the setup's 2A0 Id, so the link depends
on that optional best-effort lookup finding exactly one match, not on the input already having
an Id. If the lookup found none or more than one match, fall back to plain text as before.
RECAP LAYOUT — ONE setup pushed (the common case): the sentence forms above. If the customer
asked to push/re-push MULTIPLE setups standalone in this same conversation (e.g. "push west
and east"), give ONE consolidated table instead of repeating the two-sentence form per setup —
  | Setup | Outcome |
  |---|---|
  | west | synced |
  | east | disabled |
One row per setup, using whichever outcome word applies (synced / disabled / could not be
synced — see PUSH FAILURE-equivalent guidance above for that last case). Say the canonical
line once, before the table, if every row SAVED — a disabled row counts as saved, exactly as
in the single-setup isEnabled=false case above, where the canonical line is REQUIRED and the
outcome is disambiguated by a following sentence rather than by dropping the line. Omit the
canonical line only when a row could not be synced, since that is the one outcome it would
misstate; in that case name the failed setups separately from the saved ones.
Never say "CDS", "Commerce Delivery Service", "delivery estimation service", or otherwise
imply there are two separate systems — this is one seamless save from the
customer's perspective. Don't surface the sObject / field API names, the Connect
path, or raw HTTP codes. Keep the standalone reply under ~200 characters where
possible for a single-setup response (soft target, not a hard limit).

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `enable-and-push-configuration` | write | implemented | `postCommerceDeliveryEstimationConfiguration` | — |
| `resolve-delivery-estimation-setup-id` | read | implemented | `querySoql` | — |

### Read operations

#### `resolve-delivery-estimation-setup-id`

OPTIONAL, best-effort: look up the DeliveryEstimationSetup record's Id by the same
ExternalReference already used above, purely so a STANDALONE closing message can link to the
record instead of naming it in plain text. Never blocks, delays, or affects the outcome of
enable-and-push-configuration, which already completed by the time this runs.

**Call:** `querySoql`   — status: `implemented`

**Inputs:**

- `deliveryConfigurationExternalReference` *(`String`)* — Same value passed to enable-and-push-configuration. Source: user_input.

### Write operations

#### `enable-and-push-configuration`

Enable and push the delivery estimation configuration identified by its
ExternalReference. isEnabled=true both enables the service for the configuration
and pushes the current setup; safe to re-run (re-pushes the latest values).

**Call:** `postCommerceDeliveryEstimationConfiguration`   — status: `implemented`

**Inputs:**

- `deliveryConfigurationExternalReference` *(`String`)* — The DeliveryEstimationSetup record's ExternalReference (e.g. "west"), NOT its
2A0 Id. Source: update-delivery-estimation-setup
.resolve-delivery-estimation-setup.external_reference (when delegated), or a
SOQL read of DeliveryEstimationSetup.ExternalReference. Must be a
DeliveryEstimationSetup ExternalReference — a Location's ExternalReference is
rejected (HTTP 403 INVALID_INPUT "A Delivery Estimation Setup record doesn't
exist with external reference ..."), verified live 2026-08-03.
- `isEnabled` *(`Boolean`)* — Query param. true = enable the service for this configuration and push the
current setup (the common case); false = disable. Source: user_input.
