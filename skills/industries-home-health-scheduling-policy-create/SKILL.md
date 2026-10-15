---
name: industries-home-health-scheduling-policy-create
description: "Create Home Health's default Field Service scheduling policy via the Connect API admin-setup-step-action executor, with its fixed platform defaults presented before writing. Triggers on \"create Home Health scheduling policy\", or as a delegation target from `home-health-guided-setup-get-org-ready` (Phase 2e)."
metadata:
  version: "1.0"
---

# Home Health — Create Scheduling Policy

Child skill extracted from `home-health-guided-setup` Phase 2e (`[metadata — wizard's own action is a fixed-default create; present before writing]`).

Public doc (literal URL, confirmed via Custom Label, not a key needing further lookup): `https://sfdc.co/HomeHealthDefaultSchedulingRules`.

**This is not a standard-object create.** The wizard step (`action.type: LaunchComponent`, `resource: {"name": "healthcloud:createHHSchedulingPolicyModal"}`) dispatches through the Connect API (`POST /connect/industries/executeAdminSetupStepAction`, the admin-setup-step-action resource) to the server-side scheduling-policy creator. That creator:

1. Checks existence first (`execute()` queries for a `{namespace}__Scheduling_Policy__c` — the **FSL-package-namespaced** custom object, e.g. `SVMXC__Scheduling_Policy__c`, NOT the standard `AppointmentSchedulingPolicy` sObject — named via `LC.getLabel("HHDefaultSchedulingPolicy","SchedulingPolicyName")`, a fixed Custom Label value = "Home Health Default Scheduling Policy"). If found, tell the admin it already exists and skip.
2. If absent, creates it with **fixed, non-negotiable platform defaults** — `Name`="Home Health Default Scheduling Policy", `Description`=fixed Custom Label text, `Fix_Overlaps__c=true`, `Daily_Optimization__c=true`, `Commit_Mode__c="AlwaysCommit"` — then links a fixed, hardcoded set of `Work_Rule__c` records (Active Resources, Match Skills, Match Territory, Required Service Resource, Excluded Resources, Resource Availability, Scheduled End, Scheduled Start, Service Appointment Visiting Hours, Service Crew Resources Availability) and `Service_Goal__c` records (Preferred Service Resource — weighted 10, ASAP/Resource Priority/Skill Level — weighted 1 each) that must already exist in the org (standard FSL package content — requires `home-health-install-fsl-package` to have run first).

None of these values are a business decision — the wizard itself doesn't ask the admin anything, it just creates. Per the show-defaults-then-create pattern (below), present this exact field/value list to the admin before calling the executor, since it's writing real records even though the values are fixed:
> "Home Health's Create Scheduling Policy step creates a Field Service scheduling policy named 'Home Health Default Scheduling Policy' with these fixed settings: Fix Overlaps = on, Daily Optimization = on, Commit Mode = Always Commit, plus the standard Home Health work-rule and goal set. These are Salesforce's platform defaults, not something that varies by org — I'll create it as-is unless you want something different. Proceed?"

If the admin wants different rules/weights than the platform defaults (a real business choice), don't fight the wizard's fixed-value bean — after the default policy exists, editing `{namespace}__Scheduling_Policy__c` and its junction records directly via standard REST is a separate, valid path; ask what they want changed and treat that as a normal `ask` follow-up, distinct from this step's own automation.

**This step is complete once the named policy record exists — there is NO separate "select the default policy in Field Service Settings" action.** Home Health's flows resolve the policy by its fixed name ("Home Health Default Scheduling Policy") via the `HHDefaultSchedulingPolicy` Custom Label, not by an org-level "default policy" pointer. `FieldServiceSettings` / `FSL__Logic_Settings__c` carry no default-scheduling-policy field to set (confirmed live: no `IsDefault` on the policy object; the FSL settings custom objects are not Data-API-writable for this purpose). Do **not** direct the admin to Field Service Settings to "pick the default" after creating the policy, and do not treat the step as pending on that — creating the record is the entire step. (Bundling is separate — that's `home-health-create-bundling-policy`'s `ApptBundlePolicy`, not this policy.)

Separately: the standard `AppointmentSchedulingPolicy` sObject (keyPrefix `0Vr`) also exists and is independently REST-creatable (`POST /sobjects/AppointmentSchedulingPolicy`) — but it is a **different object** from what this wizard step produces. Don't conflate the two; only use the standard object if the admin is deliberately configuring generic Field Service appointment scheduling policies, not this Home Health wizard step.

## Show-defaults-then-create pattern

Whenever a step has fixed platform default values AND real customer-specific fields in the same create, don't silently pick one path. Discover what the admin has already said this session, present the platform defaults for the rest explicitly, and let the admin confirm or override before the write happens — never create first and explain after. This is stricter than plain `ask` (which has no default to show) and stricter than plain `automate` (which never shows a choice) — it's its own third shape: **present-then-create**. (`home-health-create-bundling-policy` uses the same pattern.)

## Return contract (for callers delegating to this skill)

Report back the policy record's Id (existing or newly created), or `blocked: FSL not installed` if the prerequisite package/work-rule/goal records aren't present yet.

## Companion references

- `health-cloud-revan/home-health-create-bundling-policy` — Phase 2f leaf — bundling policy.
- `health-cloud-revan/home-health-guided-setup-get-org-ready` — Phase 2 orchestrator (sub-steps 2a-2f).
- `health-cloud-revan/home-health-guided-setup` — the root orchestrator (full 16-group Home Health wizard) that delegates to this skill.
- `health-cloud-revan/home-health-install-fsl-package` — leaf — FSL managed-package install (Tooling API → Setup Discovery recipe → Salesforce Go).
