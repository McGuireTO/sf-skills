---
name: experience-defer-rendering-workspace-page-setup-configure
description: "Use this skill when users want to toggles the DeferRenderingWorkspacePage org preference. Trigger when users mention defer, rendering, workspace, page, setup, defer rendering workspace page setup page."
metadata:
  version: "1.0"
---

# Managing Defer Rendering Workspace Page Setup Page

## When to Use This Skill

Toggles the DeferRenderingWorkspacePage org preference. GET /setup/org/preferences/DeferRenderingWorkspacePage returns {isPreferenceEnabled:bool}; PATCH same path with body {desiredState:bool} flips it and returns the post-write state — no separate verify. Read-then-conditional-write is optional; PATCH alone suffices when the desired state is known.

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `isOrgPreferenceEnabled_wire_2` | read | — | `checkPreference` | — |
| `setOrgPreferences_1` | write | — | `updatePreference` | `isOrgPreferenceEnabled_wire_2` |

### Read operations

#### `isOrgPreferenceEnabled_wire_2`

Wire-fetch the current value of the DeferRenderingWorkspacePage org preference. The result drives the toggle's checked state on page load.

**Call:** `checkPreference`

### Write operations

#### `setOrgPreferences_1`

Persist the new boolean value of the DeferRenderingWorkspacePage org preference when the admin flips the toggle. On failure the UI dispatches an error toast with the UpdatePrefError label.

**Call:** `updatePreference`

**Depends on:** `isOrgPreferenceEnabled_wire_2`
