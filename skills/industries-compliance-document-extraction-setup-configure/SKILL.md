---
name: industries-compliance-document-extraction-setup-configure
description: "Use this skill when users want to read or change the org-wide Compliance Clause Extraction setting (Compliance Document Extraction Setup). Trigger when users mention compliance, document, extraction, setup, compliance document extraction setup."
metadata:
  version: "1.0"
  accessCheck: "Industries.userHasComplianceClauseExtractionAccess"
---

# Managing Compliance Document Extraction Setup

## When to Use This Skill

Read or change the org-wide Compliance Clause Extraction setting
(Compliance Document Extraction Setup).

Two operations:
  - Read the setting. Returns one entry keyed ComplianceClauseExtrctPref with
    isEnabled (current state) and isAccessible (always true).
  - Turn it on or off: pass preference = ComplianceClauseExtrctPref and
    enable = true or false.

Good to know:
  - An unrecognized preference name returns success but changes nothing, so
    read the setting back after a write.
  - The same setting is the public Metadata API field
    IndustriesSettings.enableComplianceClauseExtrctPref, readable through
    Tooling API as IndustriesSettings.IsComplianceClauseExtrctPrefEnabled.

Requires Industries Compliance and Einstein generative AI on the org, and a
Compliance Admin user with access to NLP Service and Scoring Framework.

## Workflow

Call getPrefs_1 to read the current state. To change it, call saveOrgPreference_2 with preference = ComplianceClauseExtrctPref and the desired enable value, then call getPrefs_1 again and compare isEnabled to the value you passed — the write returns an empty 200 even when the name is not recognized. If the user prefers Metadata API, deploying IndustriesSettings with enableComplianceClauseExtrctPref sets the same value.

## Critical Constraints

**Preconditions:**

- Industries Compliance and Einstein generative AI must be enabled for the org. The user needs the Compliance Admin permission set and access to NLP Service and Scoring Framework. Reading and changing the setting require the same access. (check: `Compliance Clause Extraction access`)

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `getPrefs_1` | read | implemented | `GET /headless/invoke/industries/industries-compliance-docextraction/doc-extraction-org-pref-settings/get-prefs` | — |
| `saveOrgPreference_2` | write | implemented | `PATCH /headless/invoke/industries/industries-compliance-docextraction/doc-extraction-org-pref-settings/save-org-preference` | `getPrefs_1` |

### Read operations

#### `getPrefs_1`

Read the Compliance Clause Extraction setting. Returns a map with one entry, keyed ComplianceClauseExtrctPref.

**Call:** `GET /headless/invoke/industries/industries-compliance-docextraction/doc-extraction-org-pref-settings/get-prefs`   — status: `implemented`

**Output:** Object keyed by preference name. ComplianceClauseExtrctPref → {isEnabled (boolean — whether Compliance Clause Extraction is on), isAccessible (boolean — always true)}.

### Write operations

#### `saveOrgPreference_2`

Turn Compliance Clause Extraction on or off. preference must be ComplianceClauseExtrctPref (matched case-insensitively); enable is true or false. Returns HTTP 200 with an empty body. An unrecognized name also returns 200 but changes nothing; omitting preference fails.

**Call:** `PATCH /headless/invoke/industries/industries-compliance-docextraction/doc-extraction-org-pref-settings/save-org-preference`   — status: `implemented`

**Inputs:**

- `preference` *(`String`)*
- `enable` *(`boolean`)*

**Depends on:** `getPrefs_1`
