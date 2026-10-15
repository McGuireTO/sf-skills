---
name: industries-tpm-system-processing-service-configure
description: "Use this skill when users want to register or check the org's Trade Promotion Management / Retail Execution processing-services tenant certificate. Trigger when users mention tpm, system, processing, service, tpm system processing service."
metadata:
  version: "1.0"
---

# Managing Tpm System Processing Service

## When to Use This Skill

Register or check the org's Trade Promotion Management / Retail Execution processing-services tenant certificate. Read state via get-tenant-registration-state; register/update via update-tenant-certificate. Both route through the native Connect API at /connect/consumer-goods/tenant-registration — no Aura/headless-invoke leg required. Use view_url only for scenarios these two operations don't cover.

## Verification Checklist

After every write operation, confirm the effect by re-reading state:

- After `update-tenant-certificate`: call `verify-update-tenant-certificate` (`GET /services/data/v67.0/connect/consumer-goods/tenant-registration`)

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `get-tenant-registration-state` | read | implemented | `GET /services/data/v67.0/connect/consumer-goods/tenant-registration` | — |
| `update-tenant-certificate` | write | implemented | `PUT /services/data/v67.0/connect/consumer-goods/tenant-registration` | `get-tenant-registration-state` |
| `verify-update-tenant-certificate` | verify | — | `GET /services/data/v67.0/connect/consumer-goods/tenant-registration` | `update-tenant-certificate` |

### Read operations

#### `get-tenant-registration-state`

Check whether the org's Trade Promotion Management / Retail Execution processing-services tenant certificate is available and what the current registration state is. Native Connect API — no Aura round trip needed.

**Call:** `GET /services/data/v67.0/connect/consumer-goods/tenant-registration`   — status: `implemented`

**Output:** TenantCertificateStateRepresentation — isCertAvailable (boolean), state (string, e.g. "Registered").

### Write operations

#### `update-tenant-certificate`

Registers/updates the org's processing-services tenant certificate for Trade Promotion Management. On Core this Connect resource is backed by an internal Aura controller method, but it is exposed as a native Connect REST endpoint and should be called directly rather than via the Aura/headless-invoke leg.

**Call:** `PUT /services/data/v67.0/connect/consumer-goods/tenant-registration`   — status: `implemented`

**Depends on:** `get-tenant-registration-state`

**Output:** TenantCertificateUpdateStatusRepresentation — certificateUpdateStatus (string).

**Notes:** no_request_body: Confirmed via live dispatch during factory-review testing on 2026-09-02 — the spec defines no requestBody/parameters and a bare PUT with no body returns 200 with certificateUpdateStatus = "Updated". The endpoint (re)issues/refreshes the org's own tenant cert server-side; there is no client-supplied input.; idempotent_when_already_registered: Calling PUT while state is already "Registered" still returns 200 Updated, and a follow-up GET shows state unchanged at "Registered" — safe to call repeatedly without a precondition check.

### Verify operations

#### `verify-update-tenant-certificate`

Read back via get-tenant-registration-state to confirm state/isCertAvailable reflect the update just submitted.

**Call:** `GET /services/data/v67.0/connect/consumer-goods/tenant-registration`

**Depends on:** `update-tenant-certificate`
