---
name: industries-home-health-guided-setup-enable-org-fsl-get
description: "Enable Home Health plus its Field Service (FSL) dependency on a Health Cloud org — the org-preference toggle cascade, Chatter precondition, and FSL settings/ESO follow-on toggles. Triggers on \"enable Home Health\", \"turn on Home Health\", or as a delegation target from `home-health-guided-setup` Phase 0. The master toggle itself and the FSL package install are each delegated further, not re-derived here."
metadata:
  version: "1.0"
---

# Home Health — Enable Org + Field Service Dependency

Child skill extracted from `home-health-guided-setup` Phase 0 (`[metadata — automate the toggles; Field Service package install is a genuine manual hand-off]`). Covers Group 1 (`GroupSalesforceFieldServiceSetup`) steps 1–3 verbatim. Every step below shows both its org link and its resolved help-doc link — full per-step table (all 75 steps, all 16 groups) lives in the parent skill's setup-and-labels reference; the links here are copied from there, not re-derived.

## Session state (scoped to this skill)

- `org_alias` — which org this run targets (confirm explicitly, never assume).
- `step_status[1..7]` — per-step status for this phase's 7 steps, reported back to the caller as a single `phase_complete` boolean once all are terminal.

**Org-Id independence (NON-NEGOTIABLE):** every Id this skill writes or compares against must be resolved fresh, on the current target org, at runtime — never carried over from a reference doc, a prior run, or a different org. The only exceptions are genuine platform-fixed literals (`DeveloperName`s, FQNs, enum values) that are the same on every org by construction.

## Steps

1. **Discover current state first**: query `IndustriesSettings.IsHomeHealthEnabled` via Tooling API before assuming anything needs to change.
2. **Chatter precondition**: if off, retrieve the full `ChatterSettings` metadata body, deploy it back with only `enableChatter` flipped (never a bare single-field payload — other Chatter fields can silently reset to defaults on a partial deploy), verify via Tooling read-back.
3. **Enable Home Health — delegate to the master-toggle SOR, do not re-author it here.** This step **`delegates_to: health-cloud-revan/HomeHealthSettings`** (the standard Setup-page leaf SOR; use `health-cloud-renegade/HomeHealthSettingsLSC` instead when the org drives the toggle through the Lightning Setup Component). That SOR owns the enable itself — it drives the Home Health setup page's toggle action, which cascades the full FSL preference chain (`FieldServiceEnabled → OptimizationServiceAccess → O2EngineEnabled → HomeHealthEnabled → RescheduleAll`) and re-reads to confirm, which is strictly more complete than a bare `IndustriesSettings.enableHomeHealth` metadata flip. Invoke it, don't inline the toggle logic — this skill deliberately reuses that leaf SOR rather than duplicating (and drifting from) its cascade. Fallback only if that SOR is unavailable at runtime: `IndustriesSettings.enableHomeHealth = true` via Metadata deploy, verified via Tooling.
4. **Install the Field Service managed package.** This step **`delegates_to: health-cloud-revan/home-health-install-fsl-package`** — invoke it rather than re-deriving the detect/primary-install/secondary-recipe/manual-fallback logic inline (it's a reusable, generalized pattern, not specific to this phase). Treat its `installed` return as satisfying this step. On `in-progress` (install accepted, takes ~20-30 min; NOT a failure) return control to the caller with `phase_complete: false` / blocking step 4 so it can start Phase 13 (`home-health-guided-setup-agentforce-setup`) while the install runs; the caller re-checks FSL at safe points and, once `FSL` is confirmed, resumes this phase at **step 5** (then 6, 7). On `awaiting-manual`, surface the Salesforce Go hand-off, keep Phase 13 / non-FSL work going, and keep re-polling the detect query.
5. **Enable Digital Experience (`CommunitiesSettings.enableNetworksEnabled` + `enableOotbProfExtUserOpsEnable`) — MANDATORY, promoted from an optional downstream toggle.** **Enable only — do NOT create or build a site here** (the Experience Cloud site is built later in Phase 10). Deploy via Metadata API (`settings/Communities.settings` + a `Settings`-type `package.xml` member `Communities`); verify by querying `SELECT COUNT() FROM Network` — `INVALID_TYPE` means it did NOT take, a count (even 0) means it did. **This is now a hard gate, same tier as step 4 (FSL), not a "nice to have ahead of the Patient App phase":** `home-health-guided-setup-get-org-ready` will not run User creation (2a) or license/permission-set assignment (2b) until both this step and step 4 report done — confirmed necessary live: a Customer Community (portal) User cannot be created while `Network` is `INVALID_TYPE`, and some permission sets (e.g. the FSL-gated Scheduler sets) only make sense once FSL is actually installed, so running user/permission-set work ahead of these two toggles produces partial, re-work-requiring state.
6. **FSL settings cascade**: once FSL is confirmed installed (step 4 returned `installed`), deploy `FieldServiceSettings.fieldServiceOrgPref = true` (a separate Metadata object from `IndustriesSettings` — don't conflate them), verify. Wizard step `ChangeFSLSettings` (`action.type: ButtonNavigate`) — org link: `/lightning/setup/FieldServiceSettings/home`; help doc: https://sfdc.co/HomeHealthFieldServiceSettings. Surface both even though this write is automated, so the admin can review the setting directly if they want.
7. **Enable Enhanced Scheduling and Optimization** — wizard step `EnableESO` (`action.type: ButtonNavigate`) — org link: `/lightning/setup/FieldServiceSettings/home`; help doc: https://sfdc.co/HomeHealthEnhancedSchedulingOptimization ("Show Me How" style link — more procedural than the "Learn More" links elsewhere).
8. Optional downstream toggles surfaced by live setup runs (confirm relevance before enabling — not every org needs every one): `IndustriesPricingSettings`, `RevenueManagementSettings.enableCoreCPQ`, `EinsteinGptSettings.enableEinsteinGptPlatform` (only once real Agentforce/Einstein agents are in play), Context Service access (`PUT /connect/contextservice/access/contextServiceEnabled/contextServiceEnabled` — Connect API, not Metadata). **`QuoteSettings.enableQuote` is NOT optional once Phase 11 (Budget) is in scope** — it's a hard prerequisite for the Budget container's Quote tab; enable it here proactively on any full "set up Home Health" run rather than waiting for the Budget phase to discover it's missing.
   - **Work Order Billing enablement** now lives in Phase 11 step 3 (`3b. EnableBilling`, alongside `EnablePricing`) in `home-health-guided-setup` — not here.

## Return contract (for callers delegating to this skill)

Report back `phase_complete: true` once steps 1-8 are each in a terminal state (done / delegated-done / deferred-manual per the parent skill's terminal-state contract), or `phase_complete: false` with the specific blocking step (most commonly step 4 FSL `in-progress` / awaiting the manual hand-off, or step 5 for Digital Experience) so the caller can decide whether to keep running other non-dependent phases in parallel. **Steps 4 and 5 together are the gate `home-health-guided-setup-get-org-ready` checks before running User creation or license/permission-set assignment** — report their status distinctly, don't fold them into a single boolean.

## Companion references

- `health-cloud-revan/home-health-guided-setup-agentforce-setup` — Phase 13 — Agentforce/Einstein enablement and Home Health agent build.
- `health-cloud-revan/home-health-guided-setup-get-org-ready` — Phase 2 orchestrator (sub-steps 2a-2f).
- `health-cloud-revan/home-health-guided-setup` — the root orchestrator (full 16-group Home Health wizard) that delegates to this skill.
- `health-cloud-revan/home-health-install-fsl-package` — leaf — FSL managed-package install (Tooling API → Setup Discovery recipe → Salesforce Go).
- `health-cloud-revan/HomeHealthSettings` — leaf SOR — the Home Health master toggle (standard Setup page).
- `health-cloud-renegade/HomeHealthSettingsLSC` — leaf SOR — the master toggle, Lightning Setup Component variant.

<!-- skill-validate: ignore-start -->
<!-- codey:operations start -->
## Operations Reference

Operations this skill uses — routing and dependency reference.

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `enable-home-health` | delegate | — | → `health-cloud-revan/HomeHealthSettings` | — |
| `delegate-install-fsl-package` | delegate | — | → `health-cloud-revan/home-health-install-fsl-package` | — |
<!-- codey:operations end -->
<!-- skill-validate: ignore-end -->
