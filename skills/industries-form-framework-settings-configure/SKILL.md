---
name: industries-form-framework-settings-configure
description: "Use this skill when users want to toggle the FormFramework org preference (Industries Form Framework). Trigger when users mention form, framework, settings, form framework settings."
metadata:
  version: "1.0"
---

# Querying Form Framework Settings

## When to Use This Skill

Toggle the FormFramework org preference (Industries Form Framework). Read state via Setup-Connect checkPreference (GET /services/data/v63.0/setup/org/preferences/FormFramework). Enable via updatePreference (PATCH same path, body PreferenceCheckInputRepresentation{desiredState:true}). Both return PreferenceCheckOutputRepresentation{isPreferenceEnabled:boolean}. One-way enable: once enabled, the preference cannot be disabled — API calls attempting to disable it (desiredState=false) will fail with an error. The setup-page UI wraps updatePreference in a confirmation modal; programmatic agents call it directly. Editing requires Customize Application permission.

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `isOrgPreferenceEnabled_wire_1` | read | — | `checkPreference` | — |

### Read operations

#### `isOrgPreferenceEnabled_wire_1`

Fetch the current enabled/disabled state of the "FormFramework" org preference via the isOrgPreferenceEnabled wire adapter. The result drives the toggle's checked state on the settings page.

**Call:** `checkPreference`
