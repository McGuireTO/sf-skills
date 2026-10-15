---
name: industries-fsc-ai-settings-configure
description: "Use this skill when users want to toggle Financial Services Cloud AI org preferences. Trigger when users mention fsc, aisettings, fsc aisettings."
metadata:
  version: "1.0"
---

# Managing Fsc Ai Settings

## When to Use This Skill

Toggle Financial Services Cloud AI org preferences. Requires Setup admin plus Financial Services AI settings access. Only these four pref keys are valid: dispute_mgmt_generative_ai, wealth_management_ai, b2b_einstein_ai, auto_complaint_summary; any other key is rejected. Each pref exposes a current-state flag and an accessibility flag (from per-feature access checks).

## Critical Constraints

**Preconditions:**

- Caller must be a Setup admin AND have Financial Services AI settings access. Both are enforced; missing either denies the call. (check: `Financial Services AI settings access`)
- Per-pref accessibility is gated by per-feature access flags: DisputeAI requires dispute-AI-pref access; WealthManagementAI requires wealth-management-AI org access; FSCB2BEinstein requires sales-Einstein org access; AutoComplaintSummary requires both complaint-management access and service-Einstein access. A pref whose gate is off surfaces its accessibility flag as false.

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `getFSCAISettings_1` | read | implemented | `GET /headless/invoke/industries/industries-dispute-management/fsc-aisettings/get-fscaisettings` | — |
| `savePreference_2` | write | implemented | `PATCH /headless/invoke/industries/industries-dispute-management/fsc-aisettings/save-preference` | `getFSCAISettings_1` |

### Read operations

#### `getFSCAISettings_1`

Returns 8-key Map<String,Boolean>: 4 `is<X>PrefSettingsAccessible` (DisputeAI / WealthManagementAI / FSCB2BEinstein / AutoComplaintSummary — AutoComplaintSummary needs ComplaintMgmt+ServiceEinstein, others single-perm) and 4 `is<X>PrefEnabled`. AURA-IS-CANONICAL: Tooling/Metadata can't reconstruct multi-perm accessibility.

**Call:** `GET /headless/invoke/industries/industries-dispute-management/fsc-aisettings/get-fscaisettings`   — status: `implemented`

**Output:** Map<String,Boolean> with exactly these 8 keys: isDisputeAIPrefSettingsAccessible, isDisputeMgmtGenerativeAIPrefEnabled, isWealthManagementAIPrefSettingsAccessible, isWealthManagementAIPrefEnabled, isFSCB2BEinsteinPrefSettingsAccessible, isFSCB2BEinsteinPrefEnabled, isAutoComplaintSummaryPrefSettingsAccessible, isAutoComplaintSummaryPrefEnabled.

### Write operations

#### `savePreference_2`

PATCH one preference. `pref` MUST be `dispute_mgmt_generative_ai` | `wealth_management_ai` | `b2b_einstein_ai` | `auto_complaint_summary` (any other key is rejected). `enabled` = target boolean. AURA-IS-CANONICAL: substituting bypasses the server-enforced 4-key allowlist.

**Call:** `PATCH /headless/invoke/industries/industries-dispute-management/fsc-aisettings/save-preference`   — status: `implemented`

**Inputs:**

- `pref` *(`String`)*
- `enabled` *(`boolean`)*

**Depends on:** `getFSCAISettings_1`

**Rollback:** Re-invoke savePreference_2 with the same `pref` and the inverted `enabled` (or the value captured from a pre-write getFSCAISettings_1 read).
