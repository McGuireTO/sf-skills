---
name: industries-home-health-fsl-settings-validate
description: "Confirm the Field Service (FSL) org-preference cascade landed correctly on a Health Cloud org — the re-surfacing check for admins who reach the Home Health guided-setup wizard mid-flow. Triggers on \"confirm FSL settings\", \"is Field Service set up\", or as a delegation target from `home-health-guided-setup` Phase 1."
metadata:
  version: "1.0"
---

# Home Health — Confirm Field Service Setup

Child skill extracted from `home-health-guided-setup` Phase 1 — Salesforce Field Service Setup (`[metadata — automate the toggle; scheduling nuances are data]`).

Org link: `/lightning/setup/FieldServiceSettings/home`. Help doc: https://sfdc.co/HomeHealthFieldServiceSettings.

This phase confirms the FSL org-preference cascade from `home-health-guided-setup-enable-org-fsl` landed correctly; the wizard group this maps to is largely a re-surfacing of that phase's FSL step for admins who reach the wizard mid-flow (i.e. who didn't run the full guided setup from Phase 0, or whose session restarted). Discover state before re-running any write — never assume `phase_complete` from a prior session carries forward, since the org may have changed between sessions.

## Discovery check

Re-run the same read `home-health-guided-setup-enable-org-fsl` step 5 used (`FieldServiceSettings.fieldServiceOrgPref`) plus the Enhanced Scheduling and Optimization toggle from that skill's step 6. If both are already set, report this phase done without writing anything. If either is missing, the caller should re-invoke `home-health-guided-setup-enable-org-fsl` rather than this skill re-deriving the write logic — this skill is a confirm-only re-surfacing, not a second owner of the write.

## Return contract (for callers delegating to this skill)

Report back `phase_complete: true` with the confirmed settings, or `phase_complete: false` naming which upstream step (`home-health-guided-setup-enable-org-fsl` step 5 or 6) needs to run.

## Companion references

- `health-cloud-revan/home-health-guided-setup-enable-org-fsl` — Phase 0 — enable Home Health, FSL package, Digital Experience, FSL settings/ESO.
- `health-cloud-revan/home-health-guided-setup` — the root orchestrator (full 16-group Home Health wizard) that delegates to this skill.
