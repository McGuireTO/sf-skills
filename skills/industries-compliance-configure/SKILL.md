---
name: industries-compliance-configure
description: "Use this skill when users want to read or toggle Industries Compliance org preferences. Trigger when users mention compliance, setup, compliance setup."
metadata:
  version: "1.0"
---

# Managing Compliance Setup

## When to Use This Skill

Read or toggle Industries Compliance org preferences. The wire tokens (used
both as getPrefs output keys AND as the saveOrgPreference `preference`
argument) are CmplLogUseUserLocale (admin user-locale formatting in
compliance views), CmplStatusTransValidation (enforce predefined status
transitions), and CmplControlTestPref (control-test framework) — NOT the
friendly UI labels. Per-call atomic write of one preference. A wrong/unknown
token is a silent no-op (HTTP 200, no change), so always read back via
getPrefs. Requires Compliance read-write access; org gate
Compliance features access. No public Connect/Tooling/Metadata/sObject
alternative — controller is canonical.

## Workflow

Call getPrefs_1 first (returns a map keyed by wire token, each
{isAccessible, isEnabled}). saveOrgPreference_2 toggles ONE of
CmplLogUseUserLocale | CmplStatusTransValidation | CmplControlTestPref via
the `preference` arg (wire token, case-sensitive) + enable=true|false;
flipping all three needs 3 calls (no batch endpoint). A wrong token returns
200 but silently does nothing — always re-read via getPrefs_1 and compare
the target token's isEnabled to the enable you passed.

## Critical Constraints

**Preconditions:**

- Org has the Industries Compliance feature provisioned (Compliance features access). Surfaced in the unified spec info.description; without it the Compliance Setup node is not reachable. (check: `Compliance features access`)
- Caller holds Compliance read-write access. Both reading (getPrefs_1) and
writing (saveOrgPreference_2) require the same access — there is no read-only
tier, so a caller who can read the preferences can also toggle them. (check: `Compliance read-write access`)

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `getPrefs_1` | read | implemented | `GET /headless/invoke/platform/compliance-setup/get-prefs` | — |
| `saveOrgPreference_2` | write | implemented | `PATCH /headless/invoke/platform/compliance-setup/save-org-preference` | `getPrefs_1` |

### Read operations

#### `getPrefs_1`

Read all three Industries Compliance preferences in one call. Returns a map
keyed by wire token (CmplLogUseUserLocale, CmplStatusTransValidation,
CmplControlTestPref), each entry carrying {isAccessible, isEnabled}. There is
no per-preference read — a single call returns the full set.

**Call:** `GET /headless/invoke/platform/compliance-setup/get-prefs`   — status: `implemented`

**Output:** Map<String,Object> aggregate. Top level carries one entry per preference,
keyed by the WIRE TOKEN (not the friendly UI label): CmplLogUseUserLocale,
CmplStatusTransValidation, CmplControlTestPref. Each entry's shape is
{isAccessible: boolean, isEnabled: boolean}. isAccessible reflects license +
read-write access; isEnabled reflects the current toggle state. Read all
three via one call — no per-preference GET.

### Write operations

#### `saveOrgPreference_2`

Toggle one Industries Compliance preference. Pass the wire token
(CmplLogUseUserLocale, CmplStatusTransValidation, or CmplControlTestPref —
the same keys getPrefs_1 returns, case-sensitive) as `preference`, plus
enable=true|false. One preference per call (no batch endpoint); returns
HTTP 200 with an empty body on success. A friendly UI label or any
unrecognized token is a SILENT NO-OP — HTTP 200 with no change — so always
confirm the result with a getPrefs_1 read-back. Requires Compliance
read-write access.

**Call:** `PATCH /headless/invoke/platform/compliance-setup/save-org-preference`   — status: `implemented`

**Inputs:**

- `preference` *(`String`)*
- `enable` *(`boolean`)*

**Depends on:** `getPrefs_1`

**Rollback:** Call saveOrgPreference_2 again with the same preference and
the inverse enable value. Toggle is idempotent per preference —
the store persists the last write; there is no history.

**Notes:** idempotency: Re-issuing the same (preference, enable) pair is a no-op at the
store level. Retries on network error are safe.; atomicity: One preference per call; batching three toggles requires three
sequential calls. Partial-failure recovery is caller's
responsibility.; inputs_contract: Both request-body fields — `preference` and `enable` — are required. The full
request schema, including the valid `preference` enum, is published in the
OpenAPI spec for this operation.
