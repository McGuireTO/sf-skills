---
name: experience-lightning-preview-configure
description: "Use this skill when users want to reads or toggles the LocalDevelopmentPreviewPref org preference (Beta) controlling whether LWC local-development preview is available in the org. Trigger when users mention lightning, preview, lightning preview."
metadata:
  version: "1.0"
  accessCheck: "Gater.org.salesforce.lwc.localDevPreview || OrgPermissions.LocalDevelopmentPreview"
---

# Managing Lightning Preview

## When to Use This Skill

Reads or toggles the LocalDevelopmentPreviewPref org preference (Beta) controlling whether LWC local-development preview is available in the org. Single-preference SOR backed by GET/PATCH /setup/org/preferences/LocalDevelopmentPreviewPref (Connect API). Read returns isPreferenceEnabled; write takes desiredState and returns the resulting isPreferenceEnabled. Requires the org's LocalDevelopmentPreview org permission OR the org.salesforce.lwc.localDevPreview Beta gater, plus the running user's permission to modify Lightning Components Setup.

## Workflow

Workflow: (1) call step `isOrgPreferenceEnabled_wire_2` to read current state; (2) if change needed, confirm the target state with a human, then call step `setOrgPreferences_1` with `desiredState` = target boolean; (3) verify by re-reading — the PATCH response's `isPreferenceEnabled` must equal `desiredState`. Both steps target the same Connect API resource `/setup/org/preferences/LocalDevelopmentPreviewPref` (GET + PATCH). LocalDevelopmentPreviewPref is an ORG preference (org-wide singleton), not a user preference — a single write affects every user in the org. The write is idempotent: PATCH `desiredState: true` on an already-enabled preference returns 200 with `isPreferenceEnabled: true` (no error, no state change). Preconditions: the org must have either the LocalDevelopmentPreview org permission or the org.salesforce.lwc.localDevPreview Beta gater; the caller must have the "Modify Lightning Components Setup" permission (part of the Customize Application family). If either precondition fails, the setup node itself is not accessible and API calls return 403.

## Critical Constraints

**Preconditions:**

- Org must have either the LocalDevelopmentPreview org permission enabled OR the org.salesforce.lwc.localDevPreview Beta gater turned on; otherwise the LightningPreview setup node is not visible and the preference cannot be toggled. (check: `Gater.org.salesforce.lwc.localDevPreview || OrgPermissions.LocalDevelopmentPreview`)
- Running user must have the Customize Application permission family that grants modify-Lightning-Components-Setup access. (check: `Modify Lightning Components Setup permission`)

**Operational rules:**

- HUMAN CONFIRMATION REQUIRED BEFORE THE WRITE: step `setOrgPreferences_1` is an org-wide singleton — one PATCH flips LWC local-development preview for every user in the org. An autonomous agent must confirm the intended target state with a human before invoking the write. The read step is safe to call freely.

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `isOrgPreferenceEnabled_wire_2` | read | — | `/services/data/v67.0/setup/org/preferences/LocalDevelopmentPreviewPref` | — |
| `setOrgPreferences_1` | write | — | `/services/data/v67.0/setup/org/preferences/LocalDevelopmentPreviewPref` | `isOrgPreferenceEnabled_wire_2` |

### Read operations

#### `isOrgPreferenceEnabled_wire_2`

Reads the current LocalDevelopmentPreviewPref org preference state. Returns PreferenceCheckOutputRepresentation with a single boolean isPreferenceEnabled.

**Call:** `/services/data/v67.0/setup/org/preferences/LocalDevelopmentPreviewPref`

**Output:** PreferenceCheckOutputRepresentation — single boolean field isPreferenceEnabled indicating whether the named preference is currently on for the org.

**Notes:** success_shape: Spec documents only a 200 response returning PreferenceCheckOutputRepresentation with a single boolean `isPreferenceEnabled`. When the preference exists but is currently disabled the response is 200 with `isPreferenceEnabled: false` — this is NOT the "preference does not exist" case, do not conflate them.; error_contracts: Non-200 shapes are Connect API framework defaults, not documented in the v67 spec. Expect 403 when the caller lacks the "Modify Lightning Components Setup" user permission (grounded in the setup-manifest access expression's user-perm clause). An unknown preferenceName returns 404 NOT_FOUND ("The requested resource does not exist") — confirmed live on org 00Dxx00VINhTI8C, 2026-07-21. A 200 with `isPreferenceEnabled: false` therefore unambiguously means the preference exists but is currently disabled; it is never returned for a nonexistent preference. Do not conflate the two states.; idempotency: Safe to poll — GET is side-effect-free. No rate-limit contract documented for this endpoint; the wire adapter caches per-session.

### Write operations

#### `setOrgPreferences_1`

Sets the LocalDevelopmentPreviewPref org preference to the boolean desiredState in the PATCH body. Returns PreferenceCheckOutputRepresentation reflecting the post-update isPreferenceEnabled value.

**Call:** `/services/data/v67.0/setup/org/preferences/LocalDevelopmentPreviewPref`

**Depends on:** `isOrgPreferenceEnabled_wire_2`

**Output:** PreferenceCheckOutputRepresentation — isPreferenceEnabled boolean reflecting the post-update state of the preference.

**Rollback:** Re-invoke this step with `desiredState` set to the value returned by the pre-change GET (step `isOrgPreferenceEnabled_wire_2`). Rollback is a symmetric PATCH — there is no compensating action beyond flipping the boolean back. If the pre-change read returned `isPreferenceEnabled: false` and the caller enabled the preference, rollback PATCH `desiredState: false`; the response's `isPreferenceEnabled: false` confirms the restore.

**Notes:** success_shape: Spec documents only a 200 response returning PreferenceCheckOutputRepresentation with `isPreferenceEnabled` echoing the post-update state. Request body PreferenceCheckInputRepresentation has a single boolean `desiredState`; the spec schema does not mark it required, but the field is the only property — a PATCH without it is trivially malformed.; error_contracts: Non-200 shapes are Connect API framework defaults, not documented in the v67 spec. Expect 403 when the caller lacks the "Modify Lightning Components Setup" user permission (grounded in the setup-manifest access expression's user-perm clause). Malformed bodies (missing `desiredState`, wrong type, wrong content-type) hit the Connect framework's 400 BAD_REQUEST default. An unknown preferenceName returns 404 NOT_FOUND — confirmed live on org 00Dxx00VINhTI8C, 2026-07-21 (same probe as the paired read step); it is not the 200-with-false state.; idempotency: Idempotent — confirmed live on org 00Dxx00VINhTI8C, 2026-07-21: PATCH `desiredState: true` on an already-enabled preference returns 200 with `isPreferenceEnabled: true`, no error, no state change. Safe to retry on network timeout with the same `desiredState`. Verified end-to-end via a reversible enable → repeat-enable → rollback sequence.; scope: Org-wide singleton. A single successful PATCH affects every user in the org immediately — there is no per-user override for this preference.; shared_controller_dependency: The Aura route this step is substituted from (SetupMetadataController.setOrgPreference) is referenced by 30+ other preference-toggle SORs. Substituting this SOR to Connect API does not deprecate the underlying Aura route; the route remains callable and referenced. Do NOT propose an Option-3 rejection contract on the Aura route from this SOR — it would break every unrejected preference SOR that still references it.
