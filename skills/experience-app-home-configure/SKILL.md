---
name: experience-app-home-configure
description: "Use this skill when users want to app Manager Setup page. Trigger when users mention app, home, app home."
metadata:
  version: "1.0"
---

# Managing App Home

## When to Use This Skill

App Manager Setup page. Three operations against CustomApplication Tooling records: list the App Manager picker categories (TabSetType API name to display label), delete a CustomApplication (logs an AppManagerListView audit record; returns null when caller lacks Customize Application), and upgrade a Classic CustomApplication to Lightning (clones plus optionally copies per-profile ProfileActionOverride rows). All steps AURA-IS-CANONICAL: no public Connect, Tooling, or Metadata equivalent reproduces the audit side-effect, permission-aware return, or the composite clone-plus-profile-copy.

## Workflow

Three independent steps; no required ordering. get-list-views returns picker labels (no caller input). delete-app and upgrade-app each take a CustomApplication id sourced externally (Tooling SOQL on CustomApplication, or the page's loaded row set). All require Customize Application user permission.

## Critical Constraints

**Destructive operations — require explicit user confirmation:**

- **`delete-app`** — Delete the CustomApplication identified by id. Logs an AppManagerListView audit record on success; returns null instead of the id when caller lacks Customize Application. AURA-IS-CANONICAL: raw Tooling DELETE loses the audit side-effect and the permission-aware null return.
  - Rollback: No automatic rollback.

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `get-list-views` | read | implemented | `GET /headless/invoke/platform/app-home` | — |
| `delete-app` | delete | implemented | `DELETE /headless/invoke/platform/app-home/delete-app` | — |
| `upgrade-app` | write | implemented | `PATCH /headless/invoke/platform/app-home/upgrade-app` | — |

### Read operations

#### `get-list-views`

Return the App Manager list-view picker as a map of TabSetType API name to display label (e.g. AllApps, Classic, Lightning) that scopes which CustomApplication rows the page renders.

**Call:** `GET /headless/invoke/platform/app-home`   — status: `implemented`

**Notes:** adoption_note: Approved for agent serving. Returns the App Manager list-view picker as a map of TabSetType API name to display label (no caller input, no side effects), and carries a correct, unmasked permission gate that rejects unauthorized callers outright. The endpoint contract is sound and functional; approved for serving so it lands in the routes-jar regen.

### Write operations

#### `upgrade-app`

Clone the source Classic CustomApplication (id) to a new Lightning CustomApplication with the supplied label/developerName; asserts source UiType is not already Lightning. When preserveProfileSetting=true, copies per-profile ProfileActionOverride entries. AURA-IS-CANONICAL: composite clone-plus-profile-copy has no public equivalent.

**Call:** `PATCH /headless/invoke/platform/app-home/upgrade-app`   — status: `implemented`

**Inputs:**

- `id` *(`String`)* — Value for the id field.
- `label` *(`String`)* — Value for the label field.
- `developerName` *(`String`)* — Name of the developer.
- `preserveProfileSetting` *(`boolean`)* — Toggle the preserve profile setting preference on or off.

**Notes:** reject_on_attestation: Two-sided mutation: creates a new app cloned from the source app's metadata AND mutates the old app in place, plus copies permission-set assignments to the new app. Its only guard against a malformed invocation is not reliably enforced at runtime, so it cannot be relied on to reject one. Permission-gated but never live-validated for this node, with no natural way to read back and confirm the result afterward. Identical implementation independently gated to reject_on_attestation for the sibling NavigationMenus node on the same grounds. Too high-blast-radius and hard-to-reverse for autonomous invocation without human attestation.; masking_bug_pointer: Same pattern as delete-app: on any failure — a permission denial or any other error — this step returns a generic, uninformative error rather than one identifying the real problem. A headless caller cannot distinguish "access denied" from "clone failed" from any other failure via the error message alone.

### Destructive operations

#### `delete-app`

Delete the CustomApplication identified by id. Logs an AppManagerListView audit record on success; returns null instead of the id when caller lacks Customize Application. AURA-IS-CANONICAL: raw Tooling DELETE loses the audit side-effect and the permission-aware null return.

**Call:** `DELETE /headless/invoke/platform/app-home/delete-app`   — status: `implemented`

**Inputs:**

- `id` *(`String`)*

**Notes:** reject_on_attestation: Irreversible delete that also removes the app's per-profile visibility and its utility-bar and icon configuration, with no natural way to read back and confirm the result afterward. Permission-gated, but never live-validated for this node. Identical implementation independently gated to reject_on_attestation for the sibling NavigationMenus node on the same grounds. Do not auto-invoke; require explicit human attestation per invocation pending live E2E confirmation.; masking_bug_pointer: On any failure — including a permission denial — this step returns a generic, uninformative error rather than one identifying the real problem, so a caller cannot tell an access-denial apart from any other failure. The served description's claim that this step "returns null" on a permission failure is also inaccurate: null is returned only when the target app record is not found, never on permission denial.
