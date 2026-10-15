---
name: agentforce-wizard-ui-sales-einstein-components-configure
description: "Use this skill when users want to wizard subset of the Sales Email Assistant setup and filter-row picklist operations. Trigger when users mention wizard, ui, sales, einstein, components."
metadata:
  version: "1.0"
---

# Managing Wizard Ui Sales Einstein Components

## When to Use This Skill

Wizard subset of the Sales Email Assistant setup and filter-row picklist operations. Two boolean org-pref toggles (EinsteinGPTSalesEmailsPref and ORG_PREFERENCE_CALL_SUMMARIZATION) plus a filter-row picklist read for the filter-row UI. The sales-email toggle, when Discovery Framework is off and enabled=true, performs an atomic bulk pref write flipping OnlyUseBuilderPrompts to false alongside the pref write; both toggles echo the saved Boolean. The picklist read returns {label, value} pairs; fieldApiName='RecordTypeId' branches to return the object's record types instead (label = record-type label, value = record-type id). Sibling SOR GPTEmailGeneration covers the remaining 7 toggles + composite getState read on this setup page.

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `filter-row-picklist-controller-get-picklist-values` | read | implemented | `GET /headless/invoke/einstein/sales-einstein/filter-row-picklist/get-picklist-values` | — |
| `sales-email-assistant-setup-controller-handle-sales-email-pref-toggle` | write | implemented | `PATCH /headless/invoke/platform/gptemail-generation/handle-sales-email-pref-toggle` | — |
| `sales-email-assistant-setup-controller-handle-sales-call-summarization-pref-toggle` | write | implemented | `PATCH /headless/invoke/platform/gptemail-generation/handle-sales-call-summarization-pref-toggle` | — |

### Read operations

#### `filter-row-picklist-controller-get-picklist-values`

Returns the available picklist values as {label, value} pairs for a field on an object, used to populate filter-row options. When the field is 'RecordTypeId', returns the object's record types instead (label = record-type label, value = record-type id). Returns an empty list when the object or field is not supplied. Requires View Setup access.

**Call:** `GET /headless/invoke/einstein/sales-einstein/filter-row-picklist/get-picklist-values`   — status: `implemented`

### Write operations

#### `sales-email-assistant-setup-controller-handle-sales-email-pref-toggle`

Sets EinsteinGPTSalesEmailsPref to `enabled`. When Discovery Framework is off and enabled=true, an atomic bulk pref write also flips OnlyUseBuilderPrompts to false (open-prompt defaults on); otherwise the write routes through the Discovery Framework path for the Sales Email feature. Returns Boolean. AURA-IS-CANONICAL: pref absent from Metadata Settings types and from Tooling Organization columns (source-verified).

**Call:** `PATCH /headless/invoke/platform/gptemail-generation/handle-sales-email-pref-toggle`   — status: `implemented`

#### `sales-email-assistant-setup-controller-handle-sales-call-summarization-pref-toggle`

Enables or disables the Sales Call Summarization org preference. Writing the preference requires Setup administrator access, and the saved boolean value is returned.

**Call:** `PATCH /headless/invoke/platform/gptemail-generation/handle-sales-call-summarization-pref-toggle`   — status: `implemented`
