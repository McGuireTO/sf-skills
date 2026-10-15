---
name: industries-home-health-guided-setup-get-org-ready-get
description: "Get a Health Cloud org ready to use Home Health — users/licenses, entity label suggestions, the WorkOrder record type, and the default scheduling + bundling policies. Mid-level orchestrator: delegates each lettered sub-step to its own leaf skill rather than inlining them. Triggers on \"get the org ready for Home Health\", or as a delegation target from `home-health-guided-setup` Phase 2."
metadata:
  version: "1.0"
---

# Home Health — Get Your Org Ready (Phase 2 orchestrator)

Mid-level orchestrator extracted from `home-health-guided-setup` Phase 2 (`[mixed — see per-step tags]`). Covers Group 2 (`GroupGetYourOrgReady`) steps 1–5. Per-step org link + help link (all confirmed literal, from the Home Health setup page's own labels) lives in the parent skill's setup-and-labels reference.

Each lettered sub-step below is independent enough (different mechanism, different data shape) to be its own dispatchable skill — this orchestrator's only job is to sequence the delegated calls and reconcile their returns into one `phase_complete` signal, not to re-derive any of their logic.

## Steps (each a delegation, not inline logic)

1. **2a — User creation.** `delegates_to: health-cloud-revan/home-health-create-users`. Prerequisite, not a native wizard step — several steps below need a real User Id from this one's return. **Gated: requires `home-health-guided-setup-enable-org-fsl` steps 4 (FSL installed) and 5 (Digital Experience enabled) both terminal before this runs** — confirmed live that running user creation ahead of either produces rework (a Customer Community/portal User can't be created while Digital Experience is off, and personas needing FSL-gated permission sets end up getting assigned those sets late in 2b anyway). If either is still pending, defer 2a (and therefore 2b) and keep running the FSL-independent sub-steps (2c, 2d) in the meantime.
2. **2b — Assign Licenses.** `delegates_to: health-cloud-revan/home-health-assign-licenses`. Run after 2a; pass along any User Ids 2a resolved so this doesn't re-discover them. Same FSL + Digital Experience gate as 2a (it inherits the gate transitively — if 2a was deferred, 2b is too).
3. **2c — Update Labels.** `delegates_to: health-cloud-revan/home-health-update-entity-labels`. Independent of 2a/2b/2d/2e/2f — optional, cosmetic, can run in any order relative to the others.
4. **2d — Create Record Type.** `delegates_to: health-cloud-revan/home-health-create-work-order-record-type`. Independent of every other sub-step in this phase — fully automatable, no customer context needed, safe to run first in Sweep 1.
5. **2e — Create Scheduling Policy.** `delegates_to: health-cloud-revan/home-health-create-scheduling-policy`. Requires FSL installed (`home-health-install-fsl-package`, called from `home-health-guided-setup-enable-org-fsl`) — if that hasn't completed yet, defer this sub-step and keep running the others.
6. **2f — Create Bundling Policy.** `delegates_to: health-cloud-revan/home-health-create-bundling-policy`. Same FSL prerequisite as 2e; independent of 2e otherwise (different object, no shared fields).

## Sequencing notes

- 2d is the only sub-step with zero dependencies and zero customer input — run it first regardless of what else is pending.
- **2a and 2b both gate on `home-health-guided-setup-enable-org-fsl` steps 4 (FSL) AND 5 (Digital Experience) being terminal — check both before creating any User or assigning any permission set/license, not just before 2e/2f.** If either is still pending, run 2c/2d now and defer 2a/2b until both land.
- 2a → 2b have a real order dependency (2b needs 2a's User Ids); the rest don't depend on each other.
- 2e and 2f gate on FSL being installed (step 4 only — they don't need Digital Experience) — if `home-health-guided-setup-enable-org-fsl` reports `phase_complete: false` (FSL still awaiting manual install), run 2c/2d now and defer 2a/2b/2e/2f, don't block the whole phase on FSL.

## Return contract (for callers delegating to this skill)

Report back a per-sub-step ledger (`2a`..`2f` → done / awaiting-data / deferred-manual / blocked-on-fsl) and a single `phase_complete` boolean (true only once every sub-step is in a terminal state).

## Companion references

- `health-cloud-revan/home-health-assign-licenses` — Phase 2b leaf — license and permission-set assignment.
- `health-cloud-revan/home-health-create-bundling-policy` — Phase 2f leaf — bundling policy.
- `health-cloud-revan/home-health-create-scheduling-policy` — Phase 2e leaf — scheduling policy.
- `health-cloud-revan/home-health-create-users` — Phase 2a leaf — user creation.
- `health-cloud-revan/home-health-create-work-order-record-type` — Phase 2d leaf — Work Order record type.
- `health-cloud-revan/home-health-guided-setup-enable-org-fsl` — Phase 0 — enable Home Health, FSL package, Digital Experience, FSL settings/ESO.
- `health-cloud-revan/home-health-guided-setup` — the root orchestrator (full 16-group Home Health wizard) that delegates to this skill.
- `health-cloud-revan/home-health-install-fsl-package` — leaf — FSL managed-package install (Tooling API → Setup Discovery recipe → Salesforce Go).
- `health-cloud-revan/home-health-update-entity-labels` — Phase 2c leaf — entity label updates.

<!-- skill-validate: ignore-start -->
<!-- codey:operations start -->
## Operations Reference

Operations this skill uses — routing and dependency reference.

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `delegate-create-work-order-record-type` | delegate | — | → `health-cloud-revan/home-health-create-work-order-record-type` | — |
| `delegate-update-entity-labels` | delegate | — | → `health-cloud-revan/home-health-update-entity-labels` | — |
| `delegate-create-users` | delegate | — | → `health-cloud-revan/home-health-create-users` | — |
| `delegate-assign-licenses` | delegate | — | → `health-cloud-revan/home-health-assign-licenses` | — |
| `delegate-create-scheduling-policy` | delegate | — | → `health-cloud-revan/home-health-create-scheduling-policy` | — |
| `delegate-create-bundling-policy` | delegate | — | → `health-cloud-revan/home-health-create-bundling-policy` | — |
<!-- codey:operations end -->
<!-- skill-validate: ignore-end -->
