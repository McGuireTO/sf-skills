---
name: industries-field-service-settings-configure
description: "Use this skill when users want to two org-level boolean toggles on Metadata type IndustriesFieldServiceSettings (singleton, fullName='IndustriesFieldServiceSettings'): enableIndustriesFieldService (Asset Service Lifecycle / IFS master, persists to ORG_PREFERENCE_INDUSTRIES_FIELD_SERVICE_ON, gated on the Industrie. Trigger when users mention industries, field, service, settings, industries field service settings."
metadata:
  version: "1.0"
  accessCheck: "(ApiOrgPermissionsBit.apiEnabled) || (IndustriesFieldServiceSettingAccessCheck.ORG_PERMISSION_INDUSTRIES_FIELD_SERVICE) || (OldAccessCheck.USER_HAS_CUSTOMIZE_APPLICATION_OR_SYS_ADMIN)"
---

# Managing Industries Field Service Settings

## When to Use This Skill

Two org-level boolean toggles on Metadata type IndustriesFieldServiceSettings (singleton, fullName='IndustriesFieldServiceSettings'): enableIndustriesFieldService (Asset Service Lifecycle / IFS master, persists to ORG_PREFERENCE_INDUSTRIES_FIELD_SERVICE_ON, gated on the IndustriesFieldService org perm) and enableAutomotiveServiceCampaignManagement (Product Service Campaign Mgmt, persists to ORG_PREFERENCE_PRODUCT_SVC_CAMPAIGN_MGMT_ENABLED, gated on the IndustriesServiceCampaignManagement org perm). Read returns both fields in one record; each write is a single-field updateMetadata. Field-name mismatch with legacy Aura: setProductSvcCampaignPref maps to enableAutomotiveServiceCampaignManagement.

## Workflow

Read via readMetadata on type IndustriesFieldServiceSettings; writes are single-field updateMetadata bodies (wrap <enableIndustriesFieldService>{bool}</enableIndustriesFieldService> or <enableAutomotiveServiceCampaignManagement>{bool}</enableAutomotiveServiceCampaignManagement> in <IndustriesFieldServiceSettings>). Verify re-reads. Two prefs independent; partial body accepted.

## Critical Constraints

**Preconditions:**

- Caller must have Customize Application OR System Administrator user permission. Aura controller checkAccess gates on USER_HAS_CUSTOMIZE_APPLICATION_OR_SYS_ADMIN; Metadata API requires customizeApplication for settings-type writes. (check: `OldAccessCheck.USER_HAS_CUSTOMIZE_APPLICATION_OR_SYS_ADMIN`)
- Org has IndustriesFieldService org permission enabled (ORG_PERMISSION_INDUSTRIES_FIELD_SERVICE). Required for the IFS-pref read/write path on both surfaces; Metadata API mirrors this via mdApiAccess=Field Service feature on field enableIndustriesFieldService. (check: `IndustriesFieldServiceSettingAccessCheck.ORG_PERMISSION_INDUSTRIES_FIELD_SERVICE`)
- Org has IndustriesServiceCampaignManagement org permission enabled. Gates the Product Service Campaign toggle on the Metadata API path (mdApiAccess=Service Campaign Management enabled on field enableAutomotiveServiceCampaignManagement). Aura controller bundles this under the IFS perm; Metadata API enforces per-field. (check: `Service Campaign Management enabled`)
- Org has API access enabled (apiEnabled). Required for any Metadata API call. (check: `ApiOrgPermissionsBit.apiEnabled`)

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `set-industries-field-service-pref` | write | implemented | `/headless/metadata` | — |
| `set-product-svc-campaign-pref` | write | implemented | `/headless/metadata` | — |

### Write operations

#### `set-industries-field-service-pref`

updateMetadata on type IndustriesFieldServiceSettings with body <IndustriesFieldServiceSettings><enableIndustriesFieldService>{bool}</enableIndustriesFieldService></IndustriesFieldServiceSettings>. Persists ORG_PREFERENCE_INDUSTRIES_FIELD_SERVICE_ON. Gates Customize Application + IndustriesFieldService org perm.

**Call:** `/headless/metadata`   — status: `implemented`

**Inputs:**

- `enable` *(`boolean`)* — Toggle the enable preference on or off.

**Output:** Metadata API SaveResult — {success: <bool>, fullName: 'IndustriesFieldServiceSettings', errors: [{statusCode, message, fields}...]}. success=true means the org-pref persisted; success=false carries errors[] (e.g. INSUFFICIENT_ACCESS when the IndustriesFieldService org perm is off).

**Notes:** verification_note: Metadata WRITE (updateMetadata) is the canonical customer-facing write surface. Corpus precedent confirms the identical field `enableIndustriesFieldService` is written on the identical singleton via the identical path. Success signal is the SaveResult `success: true` returned inline; a subsequent readback returns 400 UNSUPPORTED_OPERATION on some orgs so it is NOT a reliable secondary check.; wire_contract: Request body MUST target the fully-qualified path `/services/data/v<apiVersion>/headless/metadata` (a bare `/headless/metadata` mis-routes into the reflective-invoke envelope). Body MUST include three top-level string fields: `type` = "IndustriesFieldServiceSettings", `fullName` = "IndustriesFieldServiceSettings" (singleton — the fullName equals the type), and `xmlRep` — an XML string of the form `<?xml version="1.0" encoding="UTF-8"?><IndustriesFieldServiceSettings xmlns="http://soap.sforce.com/2006/04/metadata"><enableIndustriesFieldService>true</enableIndustriesFieldService></IndustriesFieldServiceSettings>`. Do NOT use a `{Metadata: {...}}` shorthand — that shape 400s. Full-record replace semantics apply: agents that need to change only one field should read-merge-write when the READ surface is available.; error_contracts: Observed error shapes on `/services/data/v<apiVersion>/headless/metadata` (2026-09-01):
(a) Missing any of `type` | `fullName` | `xmlRep` (or `xmlRep=""`): 400 INVALID_INPUT `{errorCode: "INVALID_INPUT", message: "Fields 'type', 'fullName', and 'xmlRep' are required"}`. All three are mandatory; an empty-string xmlRep is treated as missing.
(b) Well-formed body on an org where the type is not yet mounted: 400 UNSUPPORTED_OPERATION `{errorCode: "UNSUPPORTED_OPERATION", message: "MetadataCrud does not support UPDATE on type: IndustriesFieldServiceSettings"}`. This is an org-rollout condition (see /notes/known_issues/metadata_write_org_rollout_gap), NOT a signal that the substitution is wrong.
(c) Well-formed body on a properly-entitled org: 200 with SaveResult body `{success: true, fullName: "IndustriesFieldServiceSettings", errors: []}`.

#### `set-product-svc-campaign-pref`

updateMetadata on type IndustriesFieldServiceSettings with body <IndustriesFieldServiceSettings><enableAutomotiveServiceCampaignManagement>{bool}</enableAutomotiveServiceCampaignManagement></IndustriesFieldServiceSettings>. Persists ORG_PREFERENCE_PRODUCT_SVC_CAMPAIGN_MGMT_ENABLED. Gates Customize Application + IndustriesServiceCampaignManagement org perm.

**Call:** `/headless/metadata`   — status: `implemented`

**Inputs:**

- `enable` *(`boolean`)* — Toggle the enable preference on or off.

**Output:** Metadata API SaveResult — {success: <bool>, fullName: 'IndustriesFieldServiceSettings', errors: [{statusCode, message, fields}...]}. success=true means the campaign org-pref persisted; success=false carries errors[].

**Notes:** verification_note: Metadata WRITE (updateMetadata) targets field `enableAutomotiveServiceCampaignManagement` on singleton IndustriesFieldServiceSettings. Note the field name differs from the Aura setter name (`setProductSvcCampaignPref`) — do not derive the Metadata field name from the operation id. Success signal is the SaveResult; the parent org-pref `enableIndustriesFieldService` may need to be true first (feature ordering).; wire_contract: Same wire contract as set-industries-field-service-pref, targeting the sibling field. Fully-qualified path `/services/data/v<apiVersion>/headless/metadata`; body `{type: "IndustriesFieldServiceSettings", fullName: "IndustriesFieldServiceSettings", xmlRep: "<?xml version=\"1.0\" encoding=\"UTF-8\"?><IndustriesFieldServiceSettings xmlns=\"http://soap.sforce.com/2006/04/metadata\"><enableAutomotiveServiceCampaignManagement>true</enableAutomotiveServiceCampaignManagement></IndustriesFieldServiceSettings>"}`. Full-record replace semantics: an agent editing only this field on an org where the sibling `enableIndustriesFieldService` is already true should read-merge-write to preserve the sibling; if the READ is unavailable (see known_issues), the agent SHOULD include both fields in the xmlRep with their intended target state rather than a single-field write.; error_contracts: Identical error surface to set-industries-field-service-pref: (a) missing/empty `type` | `fullName` | `xmlRep` -> 400 INVALID_INPUT with the "Fields 'type', 'fullName', and 'xmlRep' are required" message; (b) well-formed body on a not-yet-mounted org -> 400 UNSUPPORTED_OPERATION UPDATE; (c) well-formed body on an entitled org -> 200 SaveResult. Both writes share the same MetadataCrud handler, so the error taxonomy is identical.

## Notes

- **known_issues:** {'metadata_read_unreliable': 'Metadata READ on IndustriesFieldServiceSettings is org-dependent as of 2026-09-01. Observed 400 UNSUPPORTED_OPERATION on some orgs and 200 with EMPTY xmlRep on others. No Tooling sObject alternative (404). No Organization sObject column. Verification of writes must rely on the SaveResult (success:true) returned by the updateMetadata call itself. Read/verify steps are marked `pending: true` in this SOR until a reliable read surface is available. When a caller reports "write succeeded but the setting is not active", the most likely cause is the `IndustriesFieldServiceAddOn` PSL not being provisioned (or the sibling automotive-service-campaign parent perm for the child pref).', 'metadata_write_org_rollout_gap': 'Direct probe (2026-09-01) returned 400 UNSUPPORTED_OPERATION UPDATE on the well-formed metadata write to type `IndustriesFieldServiceSettings` — both the parent field (`enableIndustriesFieldService`) and the child field (`enableAutomotiveServiceCampaignManagement`) surface the same error. The same UNSUPPORTED_OPERATION UPDATE appears for other Metadata Settings types on an unentitled org, while the identical wire pattern invokes successfully on a properly-entitled org — this is an org-level entitlement/rollout gap for MetadataCrud on Settings types, NOT a substitution error. The served SOR keeps `/headless/metadata` as the canonical write surface because hosted-MCP customers on properly-entitled orgs can invoke it today, and every entitlement expansion widens the served surface at zero SOR-authoring cost. When an agent hits UNSUPPORTED_OPERATION UPDATE from this SOR: report it to the customer as an org-provisioning gap on their target org (contact their Salesforce provisioning team to enable Metadata CRUD for Settings types), NOT as a broken SOR.', 'metadata_delete_pending': 'DELETE on `/headless/metadata` for `IndustriesFieldServiceSettings` returns a dispatch-server `pending_implementation` marker as of 2026-09-01 — the Core Metadata DELETE verb is not yet wired for a REAL delete (an interim no-op that deletes nothing is planned; real delete has no committed ETA). This SOR carries no delete step because `IndustriesFieldServiceSettings` is a Metadata singleton (delete is not a supported customer operation on Settings types anyway — you disable the org-prefs via update, not delete). Documented here for agents that speculatively try DELETE.'}
- **verification_signal:** For both write steps, the primary verification signal is the SaveResult (`success: true`) returned inline by the updateMetadata call. Do NOT chain a metadata READ as a secondary verify — on this type it returns 400 UNSUPPORTED_OPERATION on some orgs. If a downstream workflow needs to confirm active state, surface the SaveResult back to the caller and instruct them to re-open the Setup page (Setup > Feature Settings > Industries Field Service Settings) to inspect the toggles in the UI.
- **wire_contract_summary:** Canonical wire pattern for both writes on this SOR:
Path: `/services/data/v<apiVersion>/headless/metadata` (must be fully-qualified — a bare `/headless/metadata` mis-routes into the reflective-invoke envelope and 400s with "Request body is required").
Method: PUT (updateMetadata semantics).
Body: `{"type": "IndustriesFieldServiceSettings", "fullName": "IndustriesFieldServiceSettings", "xmlRep": "<?xml version=\"1.0\" encoding=\"UTF-8\"?><IndustriesFieldServiceSettings xmlns=\"http://soap.sforce.com/2006/04/metadata\"><enableIndustriesFieldService>true</enableIndustriesFieldService></IndustriesFieldServiceSettings>"}`.
All three body fields (`type`, `fullName`, `xmlRep`) are required; an empty-string `xmlRep` is treated as missing.
Semantics: full-record replace. To flip only one field, either (a) include both fields in the xmlRep at their intended target state, or (b) read-merge-write when the READ surface is available (see /notes/known_issues/metadata_read_unreliable).
Success: 200 with body `{"success": true, "fullName": "IndustriesFieldServiceSettings", "errors": []}` — the SaveResult is the authoritative verification signal (see /notes/verification_signal).
