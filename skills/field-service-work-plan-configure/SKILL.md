---
name: field-service-work-plan-configure
description: "Use this skill when users want to configure org-level Salesforce Field Service Work Plans settings and template-to-record custom field mappings. Trigger when users mention work, plan, settings, work plan settings."
metadata:
  version: "1.0"
  accessCheck: "(FieldServiceAccessCheck.ORG_HAS_WORK_PLANS_GENERAL) || (FieldServiceAccessCheck.ORG_PERMISSION_FIELD_SERVICE) || (FieldServiceSettingAccessCheck.ORG_PERMISSION_WORK_PLANS_DURATION) || (OldAccessCheck.USER_HAS_CUSTOMIZE_APPLICATION_OR_SYS_ADMIN)"
---

# Managing Work Plan Settings

## When to Use This Skill

Configure org-level Salesforce Field Service Work Plans settings and
template-to-record custom field mappings. Covers the auto-generation,
manual-status-update, and hide-not-applicable toggles, the work-order
duration source, and custom field mappings from Work Plan Template / Work
Step Template / Work Plan Template Entry to the generated Work Plan and
Work Step records. Use for Field Service Work Plans configuration and
field mapping — NOT for unrelated "work", "plan", or "settings" requests
outside Field Service Work Plans.

## Critical Constraints

**Preconditions:**

- Field Service feature must be enabled at the org level (FieldServiceAccessCheck.ORG_PERMISSION_FIELD_SERVICE). When off, getWorkPlansSettingsConfiguration short-circuits at the fieldServicePerm check and returns only fieldServicePerm + hasCustomizeApplicationPerm. (check: `FieldServiceAccessCheck.ORG_PERMISSION_FIELD_SERVICE`)
- Work Plans General feature must be on at org level (FieldServiceAccessCheck.ORG_HAS_WORK_PLANS_GENERAL). hasAccess() AND-combines this with the Customize Application/Sys Admin perm; without it saveWorkPlansSettings throws NoAccessException. (check: `FieldServiceAccessCheck.ORG_HAS_WORK_PLANS_GENERAL`)
- Customize Application permission OR System Administrator (OldAccessCheck.USER_HAS_CUSTOMIZE_APPLICATION_OR_SYS_ADMIN). Required by hasAccess(); save throws NoAccessException otherwise. (check: `OldAccessCheck.USER_HAS_CUSTOMIZE_APPLICATION_OR_SYS_ADMIN`)
- workOrderDurationSource write additionally requires FieldServiceSettingAccessCheck.ORG_PERMISSION_WORK_PLANS_DURATION; without it the duration write is silently skipped (other toggles still persist). (check: `FieldServiceSettingAccessCheck.ORG_PERMISSION_WORK_PLANS_DURATION`)

**Operational rules:**

- WHAT WORK PLANS ARE
Field Service Work Plans give front-line and back-office workers an
ordered checklist of "work steps" on a Work Order (WO) or Work Order Line
Item (WOLI), so jobs are completed consistently. The feature has a
reusable "library" plus generated instances:
  - Work Step Template (WST): a reusable task (may carry a quick action or
    a Field Service mobile flow).
  - Work Plan Template (WPT): a reusable ordered list of steps.
  - Work Plan Template Entry (WPTE): a WST placed into a WPT.
  - Work Plan Selection Rule (WPSR): logic that picks which WPT(s) apply to
    a WO/WOLI (by work type, asset, location, service contract, etc.).
    NOTE: selection rules support STANDARD fields only.
  - Work Plan (WP) / Work Step (WS): the point-in-time instances generated
    onto the WO/WOLI from the templates (WP↔WS is master-detail).
On WO/WOLI create, the WPSR is evaluated → the matching WPT + its WSTs are
copied into a WP + WS set on the record.
- SCOPE OF THIS SKILL
This skill is the ORG-LEVEL Work Plans SETTINGS page (Setup → Work Plans).
It owns: the three org toggles (auto-generation, manual work-step status
update, hide-not-applicable), the work-order duration source, and the
CUSTOM FIELD MAPPINGS. It does NOT create the library records or generate
plans — see "broader feature" below.
- CUSTOM FIELD MAPPING
Standard fields are auto-mapped from templates to the generated records and
CANNOT be changed (WPT→WP: Name, Description, Execution Order; WST/WPTE→WS:
Action Definition, Action Type, Description, Execution Order, Name, Work
Plan Execution Order). Custom field mapping lets an admin (Customize
Application) carry CUSTOM template fields onto the generated WP/WS records —
e.g. a procedures-doc URL, a compliance picklist, or a "mandatory" flag on a
step. Three fixed mapping types: WorkPlanTemplate→WorkPlan,
WorkStepTemplate→WorkStep, WorkPlanTemplateEntry→WorkStep.
Workflow:
  1. getObjectMappingConfiguration_3 — the authoritative field-discovery +
     read step. Returns the SUPPORTED source custom fields (allSourceFields[],
     already filtered — no External Lookup / Encrypted Text / Rollup) with
     their allowed, type-compatible targetFields[], plus the current
     mappings. Do NOT use a raw FieldDefinition/describe query to pick
     fields — it returns more than the mapper supports.
  2. saveWorkPlansSettings_2 with hasMappedFieldDataChanged=true and the
     mappedFieldData composite (see that step's notes for the exact
     {sourceEntity, targetEntity, mappedFields} shape; all five hasXChanged
     flags must be present even on a mappings-only save). Only map a source
     field to a target drawn from that source field's targetFields[]. Two
     mappings that share a target object (WST→WS and WPTE→WS both target
     WorkStep) must use DISTINCT target fields.
  3. Re-read via getObjectMappingConfiguration_3 to confirm persistence
     (save returns a bare true). Mappings persist as FieldServiceSettings
     metadata (Tooling API), not org prefs.
- BROADER FEATURE (outside this settings page)
Building the library and generating plans is done elsewhere and is
supported by standard/public APIs — this skill can guide a user there:
  - Create/manage WorkPlanTemplate, WorkStepTemplate, WorkPlanTemplateEntry,
    WorkPlanSelectionRule, WorkPlan, WorkStep as standard sObjects (REST/
    SOQL/Tooling); the record-level Generate / Add / Delete Work Plans and
    Add Work Steps actions live on the WO/WOLI (see the sibling controllers
    generate-work-plans, add-work-plans, delete-work-plans,
    add-work-steps-to-work-plan, update-work-plan-template-entry — separate
    from this settings page).
  - Typical setup order: (1) Enable Work Plans + add the WO/WOLI related
    lists and the Generate/Add/Delete actions (Object Manager); (2) assign
    user permissions (CRUD + View All on WPT/WST/WPSR; Read/Update on WP/WS;
    Run Flows for mobile-flow steps); (3) build WSTs, WPTs, WPTEs, and
    selection rules; (4) map custom fields (this page); (5) generate plans.
- PUBLIC DOCS
  - Intro: https://help.salesforce.com/s/articleView?id=service.fs_work_plans_intro.htm&type=5
  - Enable: https://help.salesforce.com/s/articleView?id=service.fs_work_plans_enable.htm&type=5
  - Customize settings: https://help.salesforce.com/s/articleView?id=service.fs_work_plans_customize_settings.htm&type=5
  - Assign permissions: https://help.salesforce.com/s/articleView?id=service.fs_work_plans_assign_user_perms.htm&type=5
  - Map custom fields: https://help.salesforce.com/s/articleView?id=service.fs_work_plans_map_custom_fields.htm&type=5
  - Selection rules: https://help.salesforce.com/s/articleView?id=service.fs_work_plans_create_selection_rules.htm&type=5
  - Generate plans: https://help.salesforce.com/s/articleView?id=service.fs_work_plans_generate_work_plans.htm&type=5

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `getWorkPlansSettingsConfiguration_1` | read | implemented | `GET /headless/invoke/service/fieldservice/work-plans-settings/get-work-plans-settings-configuration` | — |
| `saveWorkPlansSettings_2` | write | implemented | `PATCH /headless/invoke/service/fieldservice/work-plans-settings/save-work-plans-settings` | `getWorkPlansSettingsConfiguration_1` |
| `getObjectMappingConfiguration_3` | read | implemented | `GET /headless/invoke/service/fieldservice/field-service-object-mapping/get-object-mapping-configuration` | `getWorkPlansSettingsConfiguration_1` |

### Read operations

#### `getWorkPlansSettingsConfiguration_1`

Returns WorkPlansSettingsConfiguration: toggle values, workOrderDurationSource picklist with conditional workOrderDurationSourceOptions, and gating booleans the agent uses to decide which controls are mutable. AURA-IS-CANONICAL — no public Connect/Tooling/Metadata equivalent.

**Call:** `GET /headless/invoke/service/fieldservice/work-plans-settings/get-work-plans-settings-configuration`   — status: `implemented`

**Output:** WorkPlansSettingsConfiguration object. Toggle values:
isWorkPlansAutoGenerationEnabled, isWorkStepManualStatusUpdateEnabled,
isWorkStepsHideNotApplicableEnabled, workOrderDurationSource (string,
nullable). Gating booleans: fieldServicePerm, fieldServiceOrgPref,
hasWorkPlansDurationPerm, hasCustomizeApplicationPerm. When the duration
perm is granted, workOrderDurationSourceOptions is also returned (the
picklist for the duration source). mappingTypes is a fixed 3-element
array: WorkPlans_WorkPlanTemplate_WorkPlan,
WorkPlans_WorkStepTemplate_WorkStep,
WorkPlans_WorkPlanTemplateEntry_WorkStep — used by the save step's
optional mappedFieldData composite upsert. When Field Service is off
(fieldServicePerm=false), the response short-circuits and returns only
fieldServicePerm + hasCustomizeApplicationPerm.

#### `getObjectMappingConfiguration_3`

THE field-discovery + read step for custom field mapping — use this
(not a raw FieldDefinition/describe query) to learn which fields can be
mapped. Returns an array; each element (one per requested mappingType)
has: type (the mappingType), sourceApiName + sourceLabel (source object,
e.g. WorkPlanTemplate), targetApiName + targetLabel (target object, e.g.
WorkPlan), allSourceFields[] and mappedFields.
- allSourceFields[]: the ONLY custom source fields that may be mapped.
  The controller already filters out unsupported source types (External
  Lookup, Encrypted Text, Rollup Summary). Each entry has value (source
  field API name) + targetFields[]: the allowed targets for THAT source
  field — restricted to data-type-compatible custom fields on the target
  object, plus a "None" ({value:""}) option. Only pair a source field
  with a target from its own targetFields[] list.
- mappedFields: the currently-configured {sourceFieldApiName:
  targetFieldApiName} map for this mappingType.
Empty allSourceFields / mappedFields means no custom fields are defined
or none are mapped yet. This is the READ half of the workflow; the WRITE
half is saveWorkPlansSettings with mappedFieldData. Backed by the
embedded customFieldMapperSetupWrapper UI subcomponent on the Work Plan
Settings page.

**Call:** `GET /headless/invoke/service/fieldservice/field-service-object-mapping/get-object-mapping-configuration`   — status: `implemented`

**Inputs:**

- `mappingTypes` *(`List`)* — List of mappingType enum values to fetch. The three valid values
(from getWorkPlansSettingsConfiguration's mappingTypes[]):
WorkPlans_WorkPlanTemplate_WorkPlan (WorkPlanTemplate→WorkPlan),
WorkPlans_WorkStepTemplate_WorkStep (WorkStepTemplate→WorkStep),
WorkPlans_WorkPlanTemplateEntry_WorkStep (WorkPlanTemplateEntry→WorkStep).

**Depends on:** `getWorkPlansSettingsConfiguration_1`

### Write operations

#### `saveWorkPlansSettings_2`

Persist Work Plans toggles. workPlansSettings map MUST include all five
pairs (hasIsWorkPlansAutoGenerationEnabledChanged,
hasIsWorkStepManualStatusUpdateEnabledChanged,
hasIsWorkStepsHideNotApplicableEnabledChanged,
hasWorkOrderDurationSourceChanged, hasMappedFieldDataChanged) + their
matching new values; a missing hasXChanged key raises 500
CONTROLLER_ERROR. Duration-source writes require the WORK_PLANS_DURATION
org perm — without it the write is silently skipped while save still
returns true. Optional mappedFieldData drives a composite upsert against
one of the fixed mappingTypes returned by the GET step. Throws
NoAccessException without Customize Application + Work Plans General.
Returns bare true — verify persistence by re-reading via
getWorkPlansSettingsConfiguration. AURA-IS-CANONICAL — controller value-add
(gate + batch + mappedFieldData).

**Call:** `PATCH /headless/invoke/service/fieldservice/work-plans-settings/save-work-plans-settings`   — status: `implemented`

**Inputs:**

- `workPlansSettings` *(`LinkedHashMap`)*

**Depends on:** `getWorkPlansSettingsConfiguration_1`

**Rollback:** getWorkPlansSettingsConfiguration_1

**Notes:** payload_contract: workPlansSettings map keys (all five hasXChanged flags are REQUIRED to
avoid a 500 NPE; matching value fields are read only when the
corresponding hasXChanged is true):
  hasIsWorkPlansAutoGenerationEnabledChanged + isWorkPlansAutoGenerationEnabled (boolean)
  hasIsWorkStepManualStatusUpdateEnabledChanged + isWorkStepManualStatusUpdateEnabled (boolean)
  hasIsWorkStepsHideNotApplicableEnabledChanged + isWorkStepsHideNotApplicableEnabled (boolean)
  hasWorkOrderDurationSourceChanged + workOrderDurationSource (string or null)
  hasMappedFieldDataChanged + mappedFieldData (composite upsert object or null); error_contracts: {'empty_or_partial_payload': "Missing workPlansSettings input OR missing any hasXChanged key →\n500 CONTROLLER_ERROR (the controller unboxes booleans without null\nchecks). Send all five hasXChanged keys explicitly, even the ones\nyou don't intend to change (set those to false).", 'missing_access': 'NoAccessException when Customize Application or Sys Admin perm is\nabsent, or when Work Plans General feature is off at the org level.', 'duration_perm_silently_skipped': 'When the Work Plans Duration org permission is not granted, a\nworkOrderDurationSource write is dropped silently; save still\nreturns true. Confirm hasWorkPlansDurationPerm=true from the read\nstep before setting hasWorkOrderDurationSourceChanged=true.', 'error_message_shapes': 'Two distinct 500 CONTROLLER_ERROR message shapes distinguish payload\ndefects — inspect the error body to pick the fix:\n  - Outer-null (body={} or workPlansSettings unset): the error\n    reports that "workPlansSettings" is null → wrap the input in the\n    workPlansSettings key.\n  - Inner-null (workPlansSettings present but a hasXChanged key\n    missing): the error names the missing flag directly\n    (e.g. hasMappedFieldDataChanged) → default the named flag to\n    false. On some orgs the message instead reports a null value for\n    the workPlansSettings map lookup without naming the flag.', 'mapping_type_enum_mismatch': 'When hasMappedFieldDataChanged=true AND mappedFieldData contains a key\nthat isn\'t one of the three mappingTypes enum values, save fails with\n500 CONTROLLER_ERROR "No enum constant MappingType.<attempted-key>" —\ncomposite keys are validated pre-mutation against the mapping-type\nenum. Fix: cross-check mappedFieldData keys against mappingTypes[]\nreturned by getWorkPlansSettingsConfiguration_1 before sending.', 'mapping_data_type_mismatch': 'Catch-all 500 CONTROLLER_ERROR "We can\'t map these fields. Verify that\nthe data type details of the source and target fields match." raised\nwhen the Tooling upsert of FieldServiceSettings rejects the mapping.\nIt is NOT limited to data-type mismatches — verified against a live\norg, it also fires when:\n  - source/target field data types are incompatible;\n  - sourceEntity or targetEntity is omitted from a mappedFieldData\n    entry (the controller builds a null ObjectMapping);\n  - two mappings that share a target entity point at the SAME target\n    field (e.g. WorkStepTemplate→WorkStep and\n    WorkPlanTemplateEntry→WorkStep both mapping to\n    WorkStep.Custom_text_field__c) — each target field on a shared\n    target object can be the destination of only one source mapping.\nThe write is atomic: on this error NOTHING persists (state unchanged).\nFix: build mappings ONLY from getObjectMappingConfiguration_3 — pick a\nsource field from allSourceFields[] and a target from that field\'s own\ntargetFields[] list (both are already filtered to supported +\ntype-compatible fields); always include sourceEntity + targetEntity;\nand give each target field on a shared target object a distinct source\nmapping. Safest pattern: read the current valid config and modify it.'}; flag_gate_semantics: Flag-gate is STRICT. When hasXChanged=false the paired value is
silently ignored — sending a new value alongside flag=false never
writes and never errors. Consequence: all-hasXChanged=false is a
safe no-op payload (idempotent contract). Corollary: to guarantee a
write happens, set hasXChanged=true and populate the paired value.; loose_schema_tolerance: Unknown keys in the workPlansSettings map are silently dropped — the
server returns 200 true with no error and does not persist the typo.
Callers get no server-side signal on misspelled flag names. Validate
against payload_contract keys client-side before send.; mapping_types_enum: ['WorkPlans_WorkPlanTemplate_WorkPlan', 'WorkPlans_WorkStepTemplate_WorkStep', 'WorkPlans_WorkPlanTemplateEntry_WorkStep']; mapped_field_data: Optional composite upsert of custom field mappings. Set
hasMappedFieldDataChanged=true and populate mappedFieldData; leave both
unset/false on a toggles-only save. mappedFieldData is a MAP keyed by
mappingType enum name; the VALUE under each key is an object with THREE
fields (NOT a bare {source:target} map):
  {
    "<mappingType>": {
      "sourceEntity": "<source object API name>",   # e.g. WorkPlanTemplate
      "targetEntity": "<target object API name>",   # e.g. WorkPlan
      "mappedFields": { "<sourceFieldApiName>": "<targetFieldApiName>" }
    }
  }
sourceEntity/targetEntity come from sourceApiName/targetApiName in the
getObjectMappingConfiguration_3 read; each sourceField + targetField pair
in mappedFields MUST come from that read's allSourceFields[] (the source)
and that source field's targetFields[] (the allowed, type-compatible
target). Omitting sourceEntity or targetEntity makes the controller build
a null ObjectMapping and the Tooling upsert fails with
dataTypeMismatchError. Persistence is a Tooling API upsert of the
FieldServiceSettings metadata record (ObjectMappingItem[]) — mappings
survive as org metadata, not an org pref. Verified example against a
live org (200 true, idempotent re-apply):
  "mappedFieldData": {
    "WorkPlans_WorkPlanTemplate_WorkPlan": {
      "sourceEntity": "WorkPlanTemplate", "targetEntity": "WorkPlan",
      "mappedFields": {"Custom_text_field__c": "Custom_text_field__c"}},
    "WorkPlans_WorkStepTemplate_WorkStep": {
      "sourceEntity": "WorkStepTemplate", "targetEntity": "WorkStep",
      "mappedFields": {"Custom_text_field__c": "Custom_text_field__c"}},
    "WorkPlans_WorkPlanTemplateEntry_WorkStep": {
      "sourceEntity": "WorkPlanTemplateEntry", "targetEntity": "WorkStep",
      "mappedFields": {"Custom_text_field__c": "Custom_text_field_2__c"}}
  }; idempotency: Save is idempotent for toggles — re-issuing the same payload is a safe
no-op. All-hasXChanged=false is also a safe no-op (flag-gate strict).
To roll back a toggle change: (1) capture the GET response before save;
(2) re-PATCH with hasXChanged=true for each changed pair and the prior
value.
