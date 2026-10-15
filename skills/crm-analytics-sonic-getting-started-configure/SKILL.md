---
name: crm-analytics-sonic-getting-started-configure
description: "Use this skill when users want to toggle Sonic (Data Pipelines / ELT) org prefs in Analytics Data Manager Setup. Trigger when users mention sonic, getting, started, sonic getting started."
metadata:
  version: "1.0"
  accessCheck: "OrgPermissions.SonicLicensedOrg"
---

# Querying Sonic Getting Started

## When to Use This Skill

Toggle Sonic (Data Pipelines / ELT) org prefs in Analytics Data Manager Setup. Step 1: master license, scoped by `appType` (`DataManager`→`ORG_PREFERENCE_SONIC_ENABLED`, `MulesoftDataPath`→`ORG_PREFERENCE_MDWENABLED`); atomic `BulkPrefOperation`, runs `SonicEnablementUtil.postSonicOrgPrefEnable` on enable. Step 2: one output-connector pref; controller enforces server-side allowlist (`amazonS3`, `snowflake`, `tableauHyper`, `salesforce`). Both gated on View Setup + `USER_PERMISSION_SONIC_CONSUMER`. Both AURA-IS-CANONICAL — no Connect/Tooling/Metadata/sObject equivalent; controller is value-add (atomic batch, post-enable hook, allowlist).

## Critical Constraints

**Preconditions:**

- Caller holds `View Setup` AND `SONIC_CONSUMER` user permissions (composed access guard `Pipeline Inspector setup access` = `UserPermissions.ViewSetup && UserPermissions.SonicConsumer`). Both controller methods throw `NoAccessException` when either is absent. (check: `Pipeline Inspector setup access`)
- Org has the Sonic license — `OrgPermissions.SonicLicensedOrg` enabled. The connector toggles in `handleOutputConnectorPref` map every connector to `PermPrefEnabler.*.isAccessAllowed` against `ORG_PERMISSION_SONIC_LICENSED_ORG`; without the license the prefs cannot be flipped. (check: `OrgPermissions.SonicLicensedOrg`)

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `handleSonicPref_1` | read | implemented | `PATCH /headless/invoke/platform/sonic-getting-started/handle-sonic-pref` | — |
| `handleOutputConnectorPref_2` | read | implemented | `PATCH /headless/invoke/platform/sonic-getting-started/handle-output-connector-pref` | — |

### Read operations

#### `handleSonicPref_1`

Set master Sonic license org pref. Body: `value` (bool), `appType` (`DataManager`→`ORG_PREFERENCE_SONIC_ENABLED`, `MulesoftDataPath`→`ORG_PREFERENCE_MDWENABLED`); any other `appType` string (including `CdpDataManager`) is silently accepted but writes no pref — string-equality dispatch, not enum validation. Atomic `BulkPrefOperation`; on enable runs `SonicEnablementUtil.postSonicOrgPrefEnable` — NOT a narrow single-pref flip: it additionally enables `waveReplication`, `insightsIncrementalSync`, and `waveReplicationEnabled` org-wide via `InsightsUtilImpl.enableReplicationPermsAndPrefs` (confirmed against Core source + `SonicEnablementTest`'s own doc comment). AURA-IS-CANONICAL — atomic batch + this wider replication-enablement side effect not reconstructable from a generic pref-write.

**Call:** `PATCH /headless/invoke/platform/sonic-getting-started/handle-sonic-pref`   — status: `implemented`

**Inputs:**

- `value` *(`boolean`)*
- `appType` *(`String`)*

#### `handleOutputConnectorPref_2`

Toggle one Sonic output-connector pref. Body: `value` (bool), `connectorpref` (one of `amazonS3`, `snowflake`, `tableauHyper`, `salesforce`; controller switches on this against `PermPrefEnabler` constants, other values throw). AURA-IS-CANONICAL — substituting drops the server-enforced allowlist (contract-fidelity gate).

**Call:** `PATCH /headless/invoke/platform/sonic-getting-started/handle-output-connector-pref`   — status: `implemented`

**Inputs:**

- `value` *(`boolean`)*
- `connectorpref` *(`String`)*
