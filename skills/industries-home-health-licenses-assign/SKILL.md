---
name: industries-home-health-licenses-assign
description: "Assign Home Health permission-set licenses to the right Users. Triggers on \"assign Home Health licenses\", or as a delegation target from `home-health-guided-setup-get-org-ready` (Phase 2b)."
metadata:
  version: "1.0"
---

# Home Health — Assign Licenses

Child skill extracted from `home-health-guided-setup` Phase 2b (`[data — ask which licenses go to which users]`).

Wizard step `AssignLicenses` (`action.type: Manual` — the wizard itself only self-attests, it has no in-app assignment UI of its own). Help doc: https://sfdc.co/HomeHealthLicenses (Starter-edition orgs get a separate article instead: https://help.salesforce.com/s/articleView?id=ind.lsc_home_health.htm — check org edition before choosing which link to hand the admin).

**Prerequisite gate (check before assigning any license/permission set): FSL installed AND Digital Experience enabled.** Same gate as `home-health-create-users` — confirmed live that FSL-gated permission sets (e.g. the Field Service Call Center Rep/Dispatcher/Integration sets) should only be assigned once FSL is actually installed, and some assignments depend on a persona that itself required Digital Experience to exist. Verify both via `home-health-guided-setup-enable-org-fsl` steps 4 and 5 before proceeding.

Discover available `PermissionSetLicense` records and existing Users via query; ask the admin which licenses go to which users — never invent the mapping. If `home-health-create-users` has already run this session, use its returned User Ids rather than re-discovering. Assign via `PermissionSetLicenseAssign` (license) and `PermissionSetAssignment` (permission set) — both standard REST-createable. Org link for manual review: `/lightning/setup/ManageUsers/home` → user detail → Permission Set License Assignments related list.

## Return contract (for callers delegating to this skill)

Report back which User → license/permission-set assignments were created, and any the admin deferred.

## Companion references

- `health-cloud-revan/home-health-create-users` — Phase 2a leaf — user creation.
- `health-cloud-revan/home-health-guided-setup-enable-org-fsl` — Phase 0 — enable Home Health, FSL package, Digital Experience, FSL settings/ESO.
- `health-cloud-revan/home-health-guided-setup-get-org-ready` — Phase 2 orchestrator (sub-steps 2a-2f).
- `health-cloud-revan/home-health-guided-setup` — the root orchestrator (full 16-group Home Health wizard) that delegates to this skill.
