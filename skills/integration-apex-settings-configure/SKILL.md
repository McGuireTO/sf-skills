---
name: integration-apex-settings-configure
description: "Use this skill when users want to manage Apex org-wide settings. Trigger when users mention apex, settings, apex settings."
metadata:
  version: "1.0"
---

# Managing Apex Settings

## When to Use This Skill

Manage Apex org-wide settings. Read current values via Tooling API SOQL (SELECT ... FROM ApexSettings LIMIT 1). Write changes via Metadata API deploy using sf project deploy with an ApexSettings XML file. Settings include: aggregate code coverage only, compile-on-deploy, parallel test execution, debug logs during deployment, default queueable delay, and security preference flags (Aura controller access checks, implicit with-sharing, approval lock/unlock, etc.). Note: dispatch cannot dispatch Metadata API writes; use sf CLI directly for updates.

## Workflow

{'overview': 'ApexSettings is a Visualforce-backed Setup page. There is no Aura controller or Connect API for this surface. Use Tooling API to read current settings and Metadata API (sf project deploy) to apply changes.', 'preferred_flow': '1. Read current settings via Tooling API SOQL (get_ApexSettings_config_1). 2. Determine which fields need changing. 3. Author an Apex.settings-meta.xml with the desired values. 4. Deploy via sf project deploy start --source-dir <dir> (update_ApexSettings_config_1).', 'caveats': ['XML field names in Apex.settings-meta.xml differ from Tooling API field names (e.g., enableAggregateCodeCoverageOnly vs IsAggregateCodeCoverageOnlyEnabled).', 'dispatch cannot dispatch Metadata API writes. The agent must shell out to sf CLI for the deploy step.', 'There is no programmatic read-back after Metadata API deploy; confirm success via the sf deploy exit code or a follow-up Tooling API query.']}

## Critical Constraints

**Preconditions:**

- Requires Modify All Data or Customize Application permission to deploy Apex org settings via Metadata API.
- For Tooling API reads: API Enabled permission required.
- For Metadata API writes: sf CLI must be authenticated against the target org.

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `get_ApexSettings_config_1` | read | — | `tooling.query.ApexSettings` | — |
| `update_ApexSettings_config_1` | write | — | `metadata.deploy.ApexSettings` | — |

### Read operations

#### `get_ApexSettings_config_1`

Read current Apex org settings via Tooling API SOQL. Execute: GET /services/data/v67.0/tooling/query?q=SELECT Id, DurableId, IsAggregateCodeCoverageOnlyEnabled, IsCompileOnDeployEnabled, IsDebugLogsDuringDeploymentEnabled, IsDisableParallelApexTestingEnabled, DefaultQueueableDelay, IsTestSetupSkipTestResultsEnabled, IsSecureNoArgConstructorPrefEnabled, IsAuraApexCtrlGuestUserAccessCheckPrefEnabled, IsApexAccessRightsPrefEnabled, IsApexCtrlImplicitWithSharingPrefEnabled, IsMngdCtrlActionAccessPrefEnabled, IsRestrictCommunityExecAnonEnabled, IsApexApprovalLockUnlockEnabled, IsApexPropertyGetterPrefEnabled, IsNonCertifiedApexMdCrudEnabled, IsAuraApexCtrlAuthUserAccessCheckPrefEnabled, IsGaplessTestAutoNumEnabled FROM ApexSettings LIMIT 1. Returns a single record (Id is always 000000000000000AAA).

**Call:** `tooling.query.ApexSettings`

### Write operations

#### `update_ApexSettings_config_1`

Modify Apex org settings via Metadata API deploy. Create a file at force-app/main/default/settings/Apex.settings-meta.xml with the desired settings, then deploy with: sf project deploy start --source-dir force-app.
Example XML (include only fields you want to change):
  <?xml version="1.0" encoding="UTF-8"?>
  <ApexSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <enableAggregateCodeCoverageOnly>false</enableAggregateCodeCoverageOnly>
    <enableCompileOnDeploy>false</enableCompileOnDeploy>
    <enableDisableParallelApexTesting>false</enableDisableParallelApexTesting>
    <enableDebugDiagnostic>false</enableDebugDiagnostic>
  </ApexSettings>

Note: XML field names differ from Tooling API field names (e.g., enableAggregateCodeCoverageOnly vs IsAggregateCodeCoverageOnlyEnabled). dispatch cannot dispatch Metadata API operations (SOAP protocol); use sf CLI directly.

**Call:** `metadata.deploy.ApexSettings`
