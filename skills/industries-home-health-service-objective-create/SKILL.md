---
name: industries-home-health-service-objective-create
description: "Guide creation of a Home Health service/scheduling objective — manual, navigation-only wizard step. Triggers on \"create Home Health service objective\", or as a delegation target from `home-health-guided-setup-care-and-skill-setup` (Phase 4 step 3)."
metadata:
  version: "1.0"
---

# Home Health — Create Service Objective

Child skill extracted from `home-health-guided-setup` Phase 4 step 3 (`CreateServiceObjective`, `[data]`). Wizard step `action.type: ButtonNavigate`; org link: `/lightning/o/FSL__Service_Goal__c/home`; help doc: https://sfdc.co/HomeHealthServiceObjectives.

**No proven direct-create payload is captured for this step** — unlike the other Phase 3/4 steps, the execution playbook doesn't carry a confirmed `FSL__Service_Goal__c` field shape (the wizard button is navigation-only). Hand off with both links; if the admin wants this automated rather than done by hand in the UI, describe `FSL__Service_Goal__c` first (`GET /sobjects/FSL__Service_Goal__c/describe`) and derive required fields the same way `sfs-sobject-create` would, rather than guessing a payload — don't invent field names from the other Phase 4 steps' shapes, this object's required fields haven't been confirmed live.

## Return contract (for callers delegating to this skill)

Report back the objective record's Id if created, or `deferred-manual` with both links if the admin is completing this by hand.

## Companion references

- `health-cloud-revan/home-health-guided-setup-care-and-skill-setup` — combined Phase 3 + Phase 4 orchestrator.
- `health-cloud-revan/home-health-guided-setup` — the root orchestrator (full 16-group Home Health wizard) that delegates to this skill.
- `sfs-setup-experience/sfs-sobject-create` — the canonical entity-create pattern (describe → query-existing → create).
