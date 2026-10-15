---
name: industries-home-health-guided-setup-care-and-skill-get
description: "Set up a Home Health org's care personnel, regions, service offerings, and skills — ServiceResource/OperatingHours/ServiceTerritory through WorkType/SkillType/Skill/SkillRequirement. Mid-level orchestrator: delegates each step to its own leaf skill and owns the combined entity-intake batching across both phases. Triggers on \"set up Home Health care resources and skills\", or as a delegation target from `home-health-guided-setup` Phases 3-4."
metadata:
  version: "1.0"
---

# Home Health — Care Resources & Work/Skill Setup (Phase 3+4 orchestrator)

Mid-level orchestrator extracted from `home-health-guided-setup` Phases 3 (`GroupCarePersonnelAndTerritorySetup`) and 4 (`GroupWorkTypeAndSkillSetup`), combined deliberately rather than split into two independent orchestrators. **Why combined:** the source doc couples them explicitly — the customer-context pattern (`sfs-sobject-create`) and the batched-entity-intake timing rule are both written as spanning "this phase and Phase 4," and Phase 4 step 5/6 (`home-health-link-service-resource-skill`, `home-health-create-skill-requirement`) have a hard data dependency on Phase 3's ServiceResource/ServiceTerritory Ids. Splitting them into two orchestrators would force one to reach into the other for Ids and would break the single combined intake prompt.

Every create in both phases follows the **`sfs-sobject-create` customer-context pattern**: describe → query existing (reuse/reactivate) → ask only for what's missing → create → confirm by reading back. Never invent resource names, territory names, coverage hours, work types, or skills — if the customer already gave values this session, use them, don't re-ask.

**Timing — do NOT prompt for entity details inline.** On a full "set up Home Health" run, defer every entity-detail prompt across both phases until the automatable `[metadata — automate]` steps elsewhere in the flow have completed; raise them as **one** batched entity-intake spanning both phases, and mark each step `partial (awaiting: <entity> details)` in the ledger until answered. Prompt immediately only on a targeted single-phase ask (e.g. "I just need care personnel / territories set up," or "I just need work types and skills set up").

A typical baseline on a target org (re-discover per org, don't assume): active users incl. real personas like `Clinician 1–4`, `Care Coordinator1`, `Caregiver Internal1`/`Caregiver External1`; an **inactive** `ServiceResource` such as "Home Health Nurse - Primary" (reactivate rather than duplicate); generic reusable `OperatingHours` records (e.g. "Base Calendar", "Gold Appointments Calendar"); and possibly **zero** `ServiceTerritory`/`ServiceTerritoryMember` records on a fresh org.

## Steps (each a delegation, not inline logic)

**Phase 3 — Care Resources and Regions:**
1. **3.1 — Create Service Resource.** `delegates_to: health-cloud-revan/home-health-create-service-resource`.
2. **3.2/3.3 — Create Operating Hours (+ time slots).** `delegates_to: health-cloud-revan/home-health-create-operating-hours`. Independent of step 1.
3. **3.4 — Create Service Territory.** `delegates_to: health-cloud-revan/home-health-create-service-territory`. Needs step 2's OperatingHours Id.
4. **3.5 — Link Service Territory Member.** `delegates_to: health-cloud-revan/home-health-link-service-territory-member`. Join dependency on steps 1 and 3 — run last within Phase 3.

**Phase 4 — Work Type and Skill Setup:**
5. **4.1 — Create Work Type.** `delegates_to: health-cloud-revan/home-health-create-work-type`. Independent of Phase 3.
6. **4.2 — Create Skill Type.** `delegates_to: health-cloud-revan/home-health-create-skill-type`. Optional; independent of every other step.
7. **4.3 — Create Service Objective.** `delegates_to: health-cloud-revan/home-health-create-service-objective`. Independent of every other step; largely manual.
8. **4.4 — Create Skills.** `delegates_to: health-cloud-revan/home-health-create-skills`. Independent of 4.1-4.3; may follow 4.2 if a category was created, but doesn't require it.
9. **4.5 — Link Service Resource Skill.** `delegates_to: health-cloud-revan/home-health-link-service-resource-skill`. Join dependency on step 1 (Phase 3) and step 8.
10. **4.6 — Create Skill Requirement.** `delegates_to: health-cloud-revan/home-health-create-skill-requirement`. Join dependency on step 5 and step 8; may loop back to step 5 if the territory-scoping decision requires a new territory-specific WorkType.

## Sequencing notes

- Steps 1, 2, 5, 6, 7, 8 have no inbound dependency within this orchestrator — safe to run first/in parallel once their own customer data is known.
- Step 3 needs step 2's OperatingHours Id. Step 4 (ServiceTerritoryMember) needs both step 1 and step 3 — the last Phase-3 step to resolve.
- Step 9 needs step 1 (cross-phase) and step 8. Step 10 needs step 5 and step 8, and may send the caller back to step 5 for a territory-scoped WorkType — this is a real loop, not a bug, triggered only by the admin's territory-scoping answer in step 10.
- None of these steps gate on FSL — unlike `home-health-guided-setup-get-org-ready`'s 2e/2f, nothing here requires the FSL package.

## Return contract (for callers delegating to this skill)

Report back a per-step ledger (`3.1`..`3.5`, `4.1`..`4.6` → done / awaiting-data / blocked-on-dependency) and a single `phase_complete` boolean (true only once every step is in a terminal state).

## Companion references

- `health-cloud-revan/home-health-create-operating-hours` — Phase 3 leaf — OperatingHours and time slots.
- `health-cloud-revan/home-health-create-service-objective` — Phase 4 leaf — ServiceObjective.
- `health-cloud-revan/home-health-create-service-resource` — Phase 3 leaf — ServiceResource.
- `health-cloud-revan/home-health-create-service-territory` — Phase 3 leaf — ServiceTerritory.
- `health-cloud-revan/home-health-create-skill-requirement` — Phase 4 leaf — SkillRequirement.
- `health-cloud-revan/home-health-create-skill-type` — Phase 4 leaf — SkillType (optional).
- `health-cloud-revan/home-health-create-skills` — Phase 4 leaf — Skills.
- `health-cloud-revan/home-health-create-work-type` — Phase 4 leaf — WorkType.
- `health-cloud-revan/home-health-guided-setup-get-org-ready` — Phase 2 orchestrator (sub-steps 2a-2f).
- `health-cloud-revan/home-health-guided-setup` — the root orchestrator (full 16-group Home Health wizard) that delegates to this skill.
- `health-cloud-revan/home-health-link-service-resource-skill` — Phase 4 leaf — ServiceResourceSkill link.
- `health-cloud-revan/home-health-link-service-territory-member` — Phase 3 leaf — ServiceTerritoryMember link.
- `sfs-setup-experience/sfs-sobject-create` — the canonical entity-create pattern (describe → query-existing → create).

<!-- skill-validate: ignore-start -->
<!-- codey:operations start -->
## Operations Reference

Operations this skill uses — routing and dependency reference.

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `delegate-create-service-resource` | delegate | — | → `health-cloud-revan/home-health-create-service-resource` | — |
| `delegate-create-operating-hours` | delegate | — | → `health-cloud-revan/home-health-create-operating-hours` | — |
| `delegate-create-service-territory` | delegate | — | → `health-cloud-revan/home-health-create-service-territory` | — |
| `delegate-link-service-territory-member` | delegate | — | → `health-cloud-revan/home-health-link-service-territory-member` | — |
| `delegate-create-work-type` | delegate | — | → `health-cloud-revan/home-health-create-work-type` | — |
| `delegate-create-skill-type` | delegate | — | → `health-cloud-revan/home-health-create-skill-type` | — |
| `delegate-create-service-objective` | delegate | — | → `health-cloud-revan/home-health-create-service-objective` | — |
| `delegate-create-skills` | delegate | — | → `health-cloud-revan/home-health-create-skills` | — |
| `delegate-link-service-resource-skill` | delegate | — | → `health-cloud-revan/home-health-link-service-resource-skill` | — |
| `delegate-create-skill-requirement` | delegate | — | → `health-cloud-revan/home-health-create-skill-requirement` | — |
<!-- codey:operations end -->
<!-- skill-validate: ignore-end -->
