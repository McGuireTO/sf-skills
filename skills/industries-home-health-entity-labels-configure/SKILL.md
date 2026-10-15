---
name: industries-home-health-entity-labels-configure
description: "Surface entity-rename label suggestions for Home Health's renamable entities and hand off the actual rename write to the admin (no CRUD endpoint exists for it). Triggers on \"rename Home Health labels\", \"update entity labels\", or as a delegation target from `home-health-guided-setup-get-org-ready` (Phase 2c)."
metadata:
  version: "1.0"
---

# Home Health — Update Entity Labels

Child skill extracted from `home-health-guided-setup` Phase 2c (`[metadata to show, data to decide, manual to write]`).

Wizard step `UpdateLabels` (`action.type: LaunchComponent`, resource `{"name": "healthcloud:renameEntities"}`). Help doc: https://sfdc.co/HomeHealthUpdateLabels.

There is **no CRUD endpoint** for the actual rename write (`CustomObjectTranslation`/`GlobalValueSetTranslation`/`StandardValueSetTranslation`/`RecordTypeTranslation` are all 404 on Tooling Describe; the underlying mechanism is internal Java + PL/SQL with no external write surface). What IS automatable:

1. Read current labels live: `GET /sobjects/<Entity>/describe` → `label`/`labelPlural`, for each of the 13 Home-Health-renamable entities (ServiceAppointment, WorkOrder, WorkPlan, WorkStep, WorkType, ServiceResource, ServiceTerritory, OperatingHours, ResourcePreference, WorkPlanTemplate, ResourceAbsence, ServiceResourceSkill, PartyAppointmentRequest).
2. Show the admin a table: entity | current label (real, from Describe) | platform's suggested label (fixed reference, not invented).
3. Ask: keep current / adopt suggested / enter a custom name, per entity or in bulk.
4. Hand off to the UI for the actual write — this step is entirely **optional** (cosmetic only, no functional impact if skipped):
   > "This is optional and purely cosmetic — nothing else in this setup depends on it. I can't write the rename myself (no API surface exists for this; it's owned by the Globalization team's Rename Tabs mechanism), but here's exactly what to enter: `<org-instance-url>/lightning/setup/RenameTab/home` (works in any language) or the Home Health 'Update Labels' modal (English-only, faster). Let me know when you're done, or say skip."

## Return contract (for callers delegating to this skill)

Report back which entities the admin chose to rename (and to what), or `skipped` if declined — this step never blocks downstream phases.

## Companion references

- `health-cloud-revan/home-health-guided-setup-get-org-ready` — Phase 2 orchestrator (sub-steps 2a-2f).
- `health-cloud-revan/home-health-guided-setup` — the root orchestrator (full 16-group Home Health wizard) that delegates to this skill.
