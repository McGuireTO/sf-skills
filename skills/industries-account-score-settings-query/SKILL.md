---
name: industries-account-score-settings-query
description: "Use this skill when users want to read or toggle the Health Cloud Account Score org preference (ORG_PREFERENCE_ACCOUNT_SCORE_ENABLED). Trigger when users mention account, score, settings, account score settings."
metadata:
  version: "1.0"
  accessCheck: "HealthCloudAccessCheck.ORG_HAS_HEALTH_CLOUD"
---

# Querying Account Score Settings

## When to Use This Skill

Read or toggle the Health Cloud Account Score org preference (ORG_PREFERENCE_ACCOUNT_SCORE_ENABLED). Step 1 returns the current boolean; step 2 flips it. Both routes are AURA-IS-CANONICAL — no Connect / Tooling / sObject column exposes this single org-pref bit, and substituting Metadata API IndustriesSettings deploy is contract-lossy (drops the controller's per-call HealthCloud-license + Customize-Application gate and the single-call atomicity admins rely on). Score-range classification CRUD is rendered as a child component but lives behind a separate operation in its own setup node, not this SOR.

## Critical Constraints

**Preconditions:**

- Org licensed for Health Cloud (HealthCloudAccessCheck.ORG_HAS_HEALTH_CLOUD). Without the license the write step throws NoAccessException; the read step returns the underlying pref but is not exposed in the Setup UI. (check: `HealthCloudAccessCheck.ORG_HAS_HEALTH_CLOUD`)
- Caller holds Customize Application or System Administrator. Required for the toggle write; the read is ungated. (check: `Customize Application permission`)

## Verification Checklist

After every write operation, confirm the effect by re-reading state:

- After `handleAccountScoreEnabledToggle_2`: call `verify-handle-account-score-enabled-toggle` (`GET /headless/invoke/industries/industries-healthcare/account-score-settings/get-account-score-enabled-org-pref`)

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `getAccountScoreEnabledOrgPref_1` | read | implemented | `GET /headless/invoke/industries/industries-healthcare/account-score-settings/get-account-score-enabled-org-pref` | — |
| `handleAccountScoreEnabledToggle_2` | read | implemented | `PATCH /headless/invoke/industries/industries-healthcare/account-score-settings/handle-account-score-enabled-toggle` | `getAccountScoreEnabledOrgPref_1` |
| `verify-handle-account-score-enabled-toggle` | verify | implemented | `GET /headless/invoke/industries/industries-healthcare/account-score-settings/get-account-score-enabled-org-pref` | `handleAccountScoreEnabledToggle_2` |

### Read operations

#### `getAccountScoreEnabledOrgPref_1`

Read ORG_PREFERENCE_ACCOUNT_SCORE_ENABLED. Returns a single boolean reflecting whether Health Cloud Account Score is on for this org. Ungated read. AURA-IS-CANONICAL: no public Connect/Tooling/sObject surface exposes this single org-pref bit, and Metadata IndustriesSettings retrieve returns ~200 sibling booleans for one bit of state.

**Call:** `GET /headless/invoke/industries/industries-healthcare/account-score-settings/get-account-score-enabled-org-pref`   — status: `implemented`

**Output:** JSON boolean. true = Account Score is enabled for this org; false = disabled. The toggle UI binds directly to this value.

#### `handleAccountScoreEnabledToggle_2`

Toggle ORG_PREFERENCE_ACCOUNT_SCORE_ENABLED. Body is a JSON boolean (true=enable, false=disable). Per-call gate enforces ORG_HAS_HEALTH_CLOUD + Customize Application (or System Admin) and throws NoAccessException on failure. AURA-IS-CANONICAL: substituting Metadata IndustriesSettings deploy is contract-lossy — async deploy job, the per-call license + perm check is bundled into deploy-result feedback rather than thrown synchronously, and atomicity for a single-pref toggle is dropped.

**Call:** `PATCH /headless/invoke/industries/industries-healthcare/account-score-settings/handle-account-score-enabled-toggle`   — status: `implemented`

**Inputs:**

- `value` *(`boolean`)*

**Depends on:** `getAccountScoreEnabledOrgPref_1`

**Rollback:** Re-issue handleAccountScoreEnabledToggle_2 with the prior boolean
captured from getAccountScoreEnabledOrgPref_1 before the write. The
org pref is a scalar boolean and the write is idempotent — issuing
the same value twice is a no-op; flipping back restores state. No
separate rollback API exists.

### Verify operations

#### `verify-handle-account-score-enabled-toggle`

Re-read ORG_PREFERENCE_ACCOUNT_SCORE_ENABLED to confirm handleAccountScoreEnabledToggle_2 set the pref to the requested value. Same backing helper as step 1; semantic verify pair (read returns the exact bit the write set).

**Call:** `GET /headless/invoke/industries/industries-healthcare/account-score-settings/get-account-score-enabled-org-pref`   — status: `implemented`

**Depends on:** `handleAccountScoreEnabledToggle_2`

**Output:** JSON boolean equal to the value passed into handleAccountScoreEnabledToggle_2 if the toggle succeeded.
