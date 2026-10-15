---
name: industries-fsc-wealth-agent-settings-configure
description: "Use this skill when users want to read or set the org switch for Financial Advisor Assistance. Trigger when users mention fscwealth, agent, settings, fscwealth agent settings."
metadata:
  version: "1.0"
---

# Managing Fsc Wealth Agent Settings

## When to Use This Skill

Read or set the org switch for Financial Advisor Assistance. The customer-facing
name is "Financial Advisor Assistance"; the preference is `WealthAgentPref`.

  GET   /services/data/v67.0/setup/org/preferences/WealthAgentPref
        -> {isPreferenceEnabled: boolean}
  PATCH same path, body {desiredState: boolean}
        -> echoes the post-write {isPreferenceEnabled}

PATCH self-verifies, so no read-back is needed. Two-way toggle; the preference
name is case-sensitive.

Requires View Setup AND the org to be provisioned for the feature, satisfied by
either the Financial Advisor Assistance org permission or its pilot equivalent.
An unprovisioned org returns an error, not a false reading.

This preference is one of four switches and does not make the feature usable on
its own. Check the preconditions before reporting success.

## Workflow

Only a 200 tells you the switch's real state. Treat any other response as "could
not determine" and never report the feature as off because of an error. The Setup
page makes exactly that mistake: when its read fails it still renders the toggle
in the Off position.

Not every failure is about the org. Two of them are about your own request, and
reporting either as a provisioning problem is wrong:
  400 - your request is malformed, typically a missing or non-boolean
        `desiredState` on the PATCH. Fix the body and retry; says nothing about
        the org.
  404 - the preference name is wrong. The name is a permanent key in the
        server's allowlist, so a correctly spelled name cannot 404 on any org.
        Retry with the exact spelling.

Any OTHER non-2xx means the org is not provisioned, or the caller lacks View
Setup. This surfaces as 401 INSUFFICIENT_ACCESS, with different messages on the
read and write paths so you can tell the customer which half failed. The
published OAS documents 403 here, so do not match on the code alone.

If asked to turn the feature on, confirm afterwards that the advisors who need it
hold the per-user Financial Advisor Assistance access permission, and say which
pieces you could not verify. In the UI, enabling is gated behind a disclosure
that the feature uses generative AI, that output may be inaccurate, that the
customer assumes responsibility for how it is applied, and that it consumes
Einstein Requests, Flex Credits or Data Cloud Requests. The API applies no such
gate, so surface that before writing.

## Critical Constraints

**Preconditions:**

- View Setup is necessary but not sufficient. This preference carries an additional per-preference access check, satisfied by either the Financial Advisor Assistance org permission or its pilot equivalent, and it gates reads as well as writes. Without it the caller cannot even read the current state. (check: `Org provisioned for Financial Advisor Assistance`)
- Four things must be true: the org provisioned with the org permission or its pilot equivalent, this preference on, and each advisor granted the per-user Financial Advisor Assistance access permission. Flipping this preference on an org missing the others changes nothing an advisor can observe. (check: `The preference alone does not enable the feature`)
- The Setup page is registered under FSC Setup Home and is visible only in orgs with Financial Services Cloud. The API call does not gate on the license, but the feature only does anything in a licensed org. (check: `Financial Services Cloud licensing`)

## Verification Checklist

After every write operation, confirm the effect by re-reading state:

- After `setOrgPreferences_1`: call `verify-is-org-preference-enabled` (`GET /services/data/v67.0/setup/org/preferences/WealthAgentPref`)

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `isOrgPreferenceEnabled_wire_2` | read | — | `GET /services/data/v67.0/setup/org/preferences/WealthAgentPref` | — |
| `setOrgPreferences_1` | write | — | `PATCH /services/data/v67.0/setup/org/preferences/WealthAgentPref` | `isOrgPreferenceEnabled_wire_2` |
| `verify-is-org-preference-enabled` | verify | — | `GET /services/data/v67.0/setup/org/preferences/WealthAgentPref` | `setOrgPreferences_1` |

### Read operations

#### `isOrgPreferenceEnabled_wire_2`

Read the switch. Returns {isPreferenceEnabled: boolean} for this one preference. The name is case-sensitive.

**Call:** `GET /services/data/v67.0/setup/org/preferences/WealthAgentPref`

**Output:** {isPreferenceEnabled: boolean} - a single boolean for this preference, not a map keyed by preference name.

### Write operations

#### `setOrgPreferences_1`

Set the switch. Body is {desiredState: <bool>}; the response echoes the post-write state, so no separate verify step is needed.

**Call:** `PATCH /services/data/v67.0/setup/org/preferences/WealthAgentPref`

**Depends on:** `isOrgPreferenceEnabled_wire_2`

**Output:** {isPreferenceEnabled: boolean} echoing the post-write state.

### Verify operations

#### `verify-is-org-preference-enabled`

Optional re-read. The PATCH already echoes post-write state, so this is only worth running when a concurrent writer may have raced.

**Call:** `GET /services/data/v67.0/setup/org/preferences/WealthAgentPref`   — _optional_

**Depends on:** `setOrgPreferences_1`

**Output:** {isPreferenceEnabled: boolean}. Passes when it matches the value just written.
