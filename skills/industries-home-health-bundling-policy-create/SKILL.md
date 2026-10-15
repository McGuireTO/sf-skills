---
name: industries-home-health-bundling-policy-create
description: "Create a Home Health appointment bundling policy (`ApptBundlePolicy`) via direct REST create, going further than the wizard's own navigation-only button, with real business rules confirmed before writing. Triggers on \"create Home Health bundling policy\", or as a delegation target from `home-health-guided-setup-get-org-ready` (Phase 2f)."
metadata:
  version: "1.0"
---

# Home Health — Create Bundling Policy

Child skill extracted from `home-health-guided-setup` Phase 2f (`[data for real business rules — but the wizard button itself is pure navigation, not automation]`).

Public doc (literal URL, confirmed via Custom Label): `https://sfdc.co/HomeHealthBundlePolicy`.

**No wizard-native executor exists for this step.** Unlike `home-health-create-work-order-record-type` / `home-health-create-scheduling-policy`, the wizard step is a plain navigation button to `/lightning/o/ApptBundlePolicy/home` — none of the wizard's automated setup actions (label get/update, scheduling policy, work-order/budget record types, reschedule-flow toggle, permission validation) touch `ApptBundlePolicy`. The wizard's own button truly does nothing but open the object's list view; the admin creates the record by hand in that UI.

That said, the underlying `ApptBundlePolicy` object is directly REST-creatable — `createAccess="always"`, gated only by Field Service being enabled (i.e. requires `home-health-install-fsl-package` to have run first). So this skill CAN offer to create it via `POST /sobjects/ApptBundlePolicy`, going further than the wizard's own button, as long as the real business rules are confirmed first. Real field values, with the platform's own defaults surfaced (per the show-defaults-then-create pattern):

| Field | Platform default | Nature |
|---|---|---|
| `Name` | none — required, unique | **ask** |
| `Priority` | none — required, unique, must be positive | **ask** |
| `IsManualBundling` | none (never required) | ask if relevant |
| `IsAutomaticBundling` | `false` | present as default, let admin override |
| `LimitAmountOfBundleMembers` | `50` (valid range 2–200, server-enforced) | present as default, let admin override |
| `LimitDurationOfBundle` | none (non-negative if set) | ask |
| `BundleStartTimeFieldName` / `BundleEndTimeFieldName` | none — enum of `ServiceAppointment` datetime fields (e.g. `ServiceAppointment.SchedStartTime` / `SchedEndTime`) | ask, offer the enum's real options via Describe |
| `IsTimeCalcByBundleDurationFld` | has an insert default, never required in UI | present as default |
| `ConstantTimeValue` | none (non-negative if set) | ask, only relevant if not calculating from the duration field |
| `FilterCriteria` | none — FK to a `RecordsetFilterCriteria` | ask if the admin wants filtered bundling |
| `CanAllowSchleDepndInBundle` | `false` | present as default, let admin override |

Present this table to the admin as: "here are Salesforce's platform defaults for the fields that have one — want to keep them, or change any? Name and Priority are required and I need your real values for those either way." Only call the create once the admin has confirmed or overridden. Never invent `Name`/`Priority` or the start/end-time field choice — those are real business decisions with no platform default.

**Public-doc content note**: the article at `https://sfdc.co/HomeHealthBundlePolicy` could not be independently read for this skill (Salesforce Help returned a loading-error page on fetch, both directly and via the resolved short-link) — the field-level detail above comes from the `ApptBundlePolicy` object definition and its validation rules, not from the article's own text. Still surface the link to the admin — just don't claim the article's content was verified.

## Show-defaults-then-create pattern

Whenever a step has fixed platform default values AND real customer-specific fields in the same create, don't silently pick one path. Discover what the admin has already said this session, present the platform defaults for the rest explicitly, and let the admin confirm or override before the write happens — never create first and explain after. (`home-health-create-scheduling-policy` uses the same pattern.)

## Return contract (for callers delegating to this skill)

Report back the policy record's Id and the final field values used, or `blocked: FSL not installed` if the prerequisite isn't met.

## Companion references

- `health-cloud-revan/home-health-create-scheduling-policy` — Phase 2e leaf — scheduling policy.
- `health-cloud-revan/home-health-create-work-order-record-type` — Phase 2d leaf — Work Order record type.
- `health-cloud-revan/home-health-guided-setup-get-org-ready` — Phase 2 orchestrator (sub-steps 2a-2f).
- `health-cloud-revan/home-health-guided-setup` — the root orchestrator (full 16-group Home Health wizard) that delegates to this skill.
- `health-cloud-revan/home-health-install-fsl-package` — leaf — FSL managed-package install (Tooling API → Setup Discovery recipe → Salesforce Go).
