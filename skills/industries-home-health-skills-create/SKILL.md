---
name: industries-home-health-skills-create
description: "Discover or create Home Health Skill records (clinical, language, or other) via the Data API. Triggers on \"create Home Health skills\", \"add a skill\", or as a delegation target from `home-health-guided-setup-care-and-skill-setup` (Phase 4 step 4)."
metadata:
  version: "1.0"
---

# Home Health — Create Skills

Child skill extracted from `home-health-guided-setup` Phase 4 step 4 (`CreateSkills`, `[data]`). Org link: `/lightning/setup/SkillPage/home`; help doc: https://sfdc.co/HomeHealthSkills.

**API endpoint gotcha: `Skill` is created via the DATA API** (`POST /sobjects/Skill`) — the opposite endpoint from `SkillType` (`home-health-create-skill-type`, Tooling API). A `Skill` create against Tooling 404s; `Skill` is `INVALID_TYPE` on the Data-API *query* path but is createable there.

```text
POST {INST}/services/data/{API}/sobjects/Skill
{ "MasterLabel":"<SKILL_NAME>", "DeveloperName":"<Skill_Api>" }
```

Ask for real skill names, never invent (e.g. don't assume "Wound Care" or "French Speaking" unless the admin says so) — this applies equally to clinical skills and language/other SkillType-categorized skills. If `home-health-create-skill-type` created a category for this skill, confirm via Describe whether `Skill` carries a lookup to it before assuming one exists — don't invent the field name.

## Return contract (for callers delegating to this skill)

Report back the Skill Id(s) (existing or newly created), keyed by skill name, so `home-health-link-service-resource-skill` and `home-health-create-skill-requirement` can reference them.

## Companion references

- `health-cloud-revan/home-health-guided-setup-care-and-skill-setup` — combined Phase 3 + Phase 4 orchestrator.
- `health-cloud-revan/home-health-create-skill-requirement` — Phase 4 leaf — SkillRequirement.
- `health-cloud-revan/home-health-create-skill-type` — Phase 4 leaf — SkillType (optional).
- `health-cloud-revan/home-health-guided-setup` — the root orchestrator (full 16-group Home Health wizard) that delegates to this skill.
- `health-cloud-revan/home-health-link-service-resource-skill` — Phase 4 leaf — ServiceResourceSkill link.
