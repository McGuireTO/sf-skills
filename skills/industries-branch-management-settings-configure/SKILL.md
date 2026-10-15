---
name: industries-branch-management-settings-configure
description: "Use this skill when users want to read and toggle Branch Management org preferences. Trigger when users mention branch, management, settings, branch management settings."
metadata:
  version: "1.0"
  accessCheck: "(BranchManagementAccessCheck.ORG_HAS_BRANCH_MANAGEMENT) || (UngroupedSettingAccessCheck.USER_PERMISSION_CUSTOMIZE_APPLICATION)"
---

# Managing Branch Management Settings

## When to Use This Skill

Read and toggle Branch Management org preferences. The BRANCH_ASSOCIATION_PREF enum currently exposes one member, associateAccountWithBranch (when on, records the user's branch on accounts they create or own). Read returns Map<prefName,Boolean>. Write takes (pref, enabled) where enabled is the ABSOLUTE target state, not a flip. CRITICAL: savePref is declared void, so a 200 with an empty body means only that the call was accepted — it is NOT proof the preference changed. An unrecognized pref name matches no enum member and returns an identical empty 200 while persisting nothing, so an agent MUST confirm every write by re-reading getBranchManagementPrefs. Pref matching is case-insensitive (equalsIgnoreCase). Access: reads need (View Setup OR View All Data) AND ORG_HAS_BRANCH_MANAGEMENT, else NoAccessException; writes need Customize Application AND ORG_HAS_BRANCH_MANAGEMENT, and when either is missing the call THROWS AuraHandledException rather than silently no-opping. No public Connect, Tooling, or Metadata alternative — the controller is canonical. Wire-verified 2026-09-01 against orgfarm-a557ae8f7b (API v66.0).

## Critical Constraints

**Preconditions:**

- Org must have Branch Management enabled (ORG_HAS_BRANCH_MANAGEMENT feature gate). When off, both read and write throw NoAccessException.checkRequiredAccess / hasRequiredAccess. (check: `BranchManagementAccessCheck.ORG_HAS_BRANCH_MANAGEMENT`)
- Caller must have View Setup or View All Data user permission to read the preferences. (check: `UngroupedSettingAccessCheck.USER_PERMISSION_VIEW_SETUP or USER_PERMISSION_VIEW_ALL_DATA`)
- Caller must have Customize Application user permission to write a preference (savePref), in addition to ORG_HAS_BRANCH_MANAGEMENT. When either is missing, hasRequiredAccess throws AuraHandledException — it never returns false, and the write never silently no-ops. (check: `UngroupedSettingAccessCheck.USER_PERMISSION_CUSTOMIZE_APPLICATION`)

**Operational rules:**

- CANONICAL SEQUENCE — read, write, then re-read to verify.
1. getBranchManagementPrefs_1 — returns {associateAccountWithBranch: <bool>}. Use it to learn the current state and to confirm access before writing.
2. savePref_2 — pref='associateAccountWithBranch', enabled=<desired absolute state>.
3. getBranchManagementPrefs_1 again — assert the returned value equals what you sent.
Step 3 is MANDATORY, not optional. savePref returns void, so a successful write and a silently ignored write are indistinguishable on the wire: both return HTTP 200 with an empty body. The only value of `pref` that does anything is 'associateAccountWithBranch'; any other string, including a typo or an empty string, is ignored and still returns 200. Matching is case-insensitive, so 'ASSOCIATEACCOUNTWITHBRANCH' also works, but send the canonical casing.
`enabled` is an absolute target state, not a toggle — send true to turn the preference on and false to turn it off. Do not send the inverse of the current value expecting a flip.
If a write throws AuraHandledException, the caller is missing Customize Application or the org lacks Branch Management. Re-read to confirm nothing changed, then surface the permission gap rather than retrying.
SCOPE — this Setup page exposes exactly one control, the associateAccountWithBranch toggle. Its other client-side handlers (init, toggleBranchAssociation) are UI wrappers over these same two controller methods and add no server-side behavior: init calls getBranchManagementPrefs on page load, and toggleBranchAssociation calls savePref then updates local component state and raises a success toast. There is no further agent-callable capability on this page.

## Verification Checklist

After every write operation, confirm the effect by re-reading state:

- After `savePref_2`: call `verify-save-pref` (`GET /headless/invoke/platform/branch-management-settings/get-branch-management-prefs`)

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `getBranchManagementPrefs_1` | read | implemented | `GET /headless/invoke/platform/branch-management-settings/get-branch-management-prefs` | — |
| `savePref_2` | write | implemented | `PATCH /headless/invoke/platform/branch-management-settings/save-pref` | `getBranchManagementPrefs_1` |
| `verify-save-pref` | verify | implemented | `GET /headless/invoke/platform/branch-management-settings/get-branch-management-prefs` | `savePref_2` |

### Read operations

#### `getBranchManagementPrefs_1`

Returns Map<String,Boolean> of Branch Management prefs (currently only associateAccountWithBranch). Requires View Setup or View All Data + ORG_HAS_BRANCH_MANAGEMENT feature gate; else NoAccessException.

**Call:** `GET /headless/invoke/platform/branch-management-settings/get-branch-management-prefs`   — status: `implemented`

**Output:** Map<String,Boolean> keyed by BRANCH_ASSOCIATION_PREF prefName — one entry per enum member, currently only associateAccountWithBranch; each value is the current org-pref enabled state. The controller iterates the enum on every call, so the key set is fixed by the enum rather than by org configuration. Live-verified 2026-09-01 against orgfarm-a557ae8f7b (API v66.0): returned exactly {"associateAccountWithBranch": false} on an org with the preference off.

### Write operations

#### `savePref_2`

Set a BRANCH_ASSOCIATION_PREF org pref. Matching is case-insensitive (equalsIgnoreCase) against the enum's prefName; an unrecognized name matches nothing and persists nothing while still returning 200. Returns void — the response never confirms persistence, so always re-read getBranchManagementPrefs to verify. Requires Customize Application AND ORG_HAS_BRANCH_MANAGEMENT; when either is missing hasRequiredAccess THROWS AuraHandledException rather than no-opping.

**Call:** `PATCH /headless/invoke/platform/branch-management-settings/save-pref`   — status: `implemented`

**Inputs:**

- `pref` *(`String`)*
- `enabled` *(`boolean`)*

**Depends on:** `getBranchManagementPrefs_1`

**Output:** Empty JSON object. savePref is declared void, so a 200 carries no payload and is NOT evidence that the preference persisted — an unrecognized pref name returns an identical empty 200 having changed nothing. Live-verified 2026-09-01 against orgfarm-a557ae8f7b (API v66.0): pref='totallyBogusPrefName' and pref='' each returned 200 {} and left associateAccountWithBranch unchanged, while pref='associateAccountWithBranch' returned the same 200 {} and did persist. Confirm every write by re-reading getBranchManagementPrefs.

### Verify operations

#### `verify-save-pref`

Re-read getBranchManagementPrefs after savePref_2 and assert the returned value for the pref you wrote equals the `enabled` value you sent. REQUIRED, not optional: savePref is declared void and returns an empty 200 whether it persisted the change or silently ignored the request, so this read is the only signal that the write took effect. If the value did not change, the pref name matched no BRANCH_ASSOCIATION_PREF member — check it against the enum's single member, associateAccountWithBranch.

**Call:** `GET /headless/invoke/platform/branch-management-settings/get-branch-management-prefs`   — status: `implemented`

**Depends on:** `savePref_2`

**Output:** Map<String,Boolean> — the same shape getBranchManagementPrefs_1 returns. Assert the associateAccountWithBranch entry equals the `enabled` value passed to savePref_2. Live-verified 2026-09-01 against orgfarm-a557ae8f7b (API v66.0): after writing true the read returned {"associateAccountWithBranch": true}; after writing false it returned {"associateAccountWithBranch": false}; after writing a bogus pref name it was unchanged.
