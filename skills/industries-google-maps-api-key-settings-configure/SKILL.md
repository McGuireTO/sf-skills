---
name: industries-google-maps-api-key-settings-configure
description: "Use this skill when users want to read, set, or clear the org-wide Google Maps API key consumed by Consumer Goods Cloud / Retail Execution map and visit-routing surfaces. Trigger when users mention google, maps, api, key, settings, google maps api key settings."
metadata:
  version: "1.0"
---

# Managing Google Maps Api Key Settings

## When to Use This Skill

Read, set, or clear the org-wide Google Maps API key consumed by Consumer Goods Cloud / Retail Execution map and visit-routing surfaces. The key is a single org-level credential string (no per-user / per-record variants). All three operations route to Connect resource IGoogleMapsApiKeyResource at /connect/industries/retail/google-map-api-key (GET / PUT / DELETE) and require the caller's user to have Retail Execution or Direct Store Delivery enabled.

## Critical Constraints

**Preconditions:**

- Caller's user must have Retail Execution OR Direct Store Delivery enabled (the Connect resource's userDynamicChecks gate UserHasRetailExecutionOrDirectStoreDeliveryEnable). The Aura wrapper's gate Run Retail Execution permission is a strict subset. (check: `UserHasRetailExecutionOrDirectStoreDeliveryEnable`)
- Customize Application (or equivalent admin permission) is required to mutate org-wide credentials, consistent with other org-level credential settings.

**Destructive operations — require explicit user confirmation:**

- **`deleteGoogleMapsApiKey_3`** — Clear the org-wide Google Maps API key. After this returns, getGoogleMapsApiKey responds with apiKey null/empty until a new value is saved.
  - Rollback: No automatic rollback.

## Verification Checklist

After every write operation, confirm the effect by re-reading state:

- After `saveGoogleMapsApiKey_2`: call `verify-saveGoogleMapsApiKey_2` (`/services/data/v67.0/connect/industries/retail/google-map-api-key`)

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `getGoogleMapsApiKey_1` | read | implemented | `/services/data/v67.0/connect/industries/retail/google-map-api-key` | — |
| `saveGoogleMapsApiKey_2` | write | implemented | `/services/data/v67.0/connect/industries/retail/google-map-api-key` | `getGoogleMapsApiKey_1` |
| `deleteGoogleMapsApiKey_3` | delete | implemented | `/services/data/v67.0/connect/industries/retail/google-map-api-key` | `getGoogleMapsApiKey_1` |
| `verify-saveGoogleMapsApiKey_2` | verify | — | `/services/data/v67.0/connect/industries/retail/google-map-api-key` | `saveGoogleMapsApiKey_2` |

### Read operations

#### `getGoogleMapsApiKey_1`

Read the org-wide Google Maps API key. Returns a GoogleMapsApiKeyRepresentation with one field, apiKey (String); apiKey is null/empty when no key has been saved yet.

**Call:** `/services/data/v67.0/connect/industries/retail/google-map-api-key`   — status: `implemented`

**Output:** GoogleMapsApiKeyRepresentation — single field apiKey (String). Null/empty when no key has been configured for the org.

### Write operations

#### `saveGoogleMapsApiKey_2`

Persist the org-wide Google Maps API key. Body GoogleMapsApiKeyInputRepresentation has one non-empty apiKey String; idempotent overwrite. Response echoes the persisted apiKey.

**Call:** `/services/data/v67.0/connect/industries/retail/google-map-api-key`   — status: `implemented`

**Inputs:**

- `apiKey` *(`String`)*

**Depends on:** `getGoogleMapsApiKey_1`

### Verify operations

#### `verify-saveGoogleMapsApiKey_2`

Read back via getGoogleMapsApiKey to confirm saveGoogleMapsApiKey persisted: response apiKey should equal the value just submitted.

**Call:** `/services/data/v67.0/connect/industries/retail/google-map-api-key`

**Depends on:** `saveGoogleMapsApiKey_2`

### Destructive operations

#### `deleteGoogleMapsApiKey_3`

Clear the org-wide Google Maps API key. After this returns, getGoogleMapsApiKey responds with apiKey null/empty until a new value is saved.

**Call:** `/services/data/v67.0/connect/industries/retail/google-map-api-key`   — status: `implemented`

**Depends on:** `getGoogleMapsApiKey_1`
