---
name: industries-home-health-users-create
description: "Discover or create the Users needed before Home Health license/permission assignment can reference a real User Id. Triggers on \"create Home Health users\", \"set up users for Home Health\", or as a delegation target from `home-health-guided-setup-get-org-ready` (Phase 2a)."
metadata:
  version: "1.0"
---

# Home Health — User Creation (prerequisite)

Child skill extracted from `home-health-guided-setup` Phase 2a. Not a native wizard step — several downstream steps (license assignment, portal-account ownership) need a real User Id.

**Prerequisite gate (check before creating any User): FSL installed AND Digital Experience enabled.** Confirmed live that creating Users ahead of either produces rework — a Customer Community/portal persona can't be created while `Network` is `INVALID_TYPE` (Digital Experience off), and FSL-dependent personas end up needing their permission sets assigned late by `home-health-assign-licenses` anyway. Verify both via `home-health-guided-setup-enable-org-fsl` steps 4 and 5 (or re-check directly: FSL via the `InstalledSubscriberPackage` detect query, Digital Experience via `SELECT COUNT() FROM Network` not throwing `INVALID_TYPE`) before proceeding. If a specific persona being created doesn't need either (e.g. an internal Clinician), it's still worth confirming both org-wide first rather than discovering a gap mid-batch.

`[data — ask]`: discover existing Users first (`GET /sobjects/User` query scoped to relevant profiles); only create new Users if the admin confirms new personas are needed. Never invent names/emails/usernames.

Known gotcha: the target Account's owner must have a `UserRole` assigned, or `User` creation for a portal-account-owner persona fails. Fix in order: create the `UserRole` first, assign it to the Account owner, then create the User.

Org link for manual user creation if the admin prefers the UI: `/lightning/setup/ManageUsers/home`. (Not a native wizard step, so the wizard offers no help link of its own — this link is standard Setup navigation.)

## Return contract (for callers delegating to this skill)

Report back the resolved User Id(s) (existing or newly created) keyed by persona, so `home-health-assign-licenses` can reference them without re-discovering.

## Companion references

- `health-cloud-revan/home-health-assign-licenses` — Phase 2b leaf — license and permission-set assignment.
- `health-cloud-revan/home-health-guided-setup-enable-org-fsl` — Phase 0 — enable Home Health, FSL package, Digital Experience, FSL settings/ESO.
- `health-cloud-revan/home-health-guided-setup-get-org-ready` — Phase 2 orchestrator (sub-steps 2a-2f).
- `health-cloud-revan/home-health-guided-setup` — the root orchestrator (full 16-group Home Health wizard) that delegates to this skill.
