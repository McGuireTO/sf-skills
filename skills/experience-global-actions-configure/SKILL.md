---
name: experience-global-actions-configure
description: "Use this skill when users want to manage Global Actions in Salesforce Setup. Trigger when users mention global, actions, global actions."
metadata:
  version: "1.0"
  accessCheck: "OrgPermissions.RuntimeUi"
---

# Managing Global Actions

## When to Use This Skill

Manage Global Actions in Salesforce Setup. Global Actions (QuickActionDefinition
in the Tooling API) are actions that appear in the global publisher bar and can
be used across objects. Admins use this page to create, view, and delete global
actions. Common action types include Create, Update, LogACall, and custom actions.
Note: assigning actions to a layout is done via GlobalPublisherLayouts, not here.

## Workflow

All four steps target the real QuickActionDefinition Tooling API object and are live-validated — go ahead and call them. Before deleting a global action, confirm it isn't assigned to a GlobalPublisherLayout (the delete call fails if it is); use GlobalPublisherLayouts to unassign first.

## Critical Constraints

**Preconditions:**

- Org has Lightning Experience runtime UI enabled — the GlobalActions Setup page itself is gated by OrgPermissions.RuntimeUi per the setup-manifest entry. (check: `OrgPermissions.RuntimeUi`)
- Admin needs the standard QuickAction CRUD permission (typically Customize Application). Not artifact-grounded to a single check method in this factory-harness pass; the canonical gate is enforced server-side by the Metadata API deploy when substitution becomes possible.

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `list-global-actions` | read | — | `query.QuickActionDefinition` | — |
| `get-global-action` | read | — | `sobjects/QuickActionDefinition/{id}` | — |
| `create-global-action` | write | — | `sobjects/QuickActionDefinition` | — |
| `delete-global-action` | write | — | `sobjects/QuickActionDefinition/{id}` | — |

### Read operations

#### `list-global-actions`

Query QuickActionDefinition records via the Tooling API. Use fields Id, DeveloperName, Label, Type to identify actions. Type values include Create, Update, LogACall, and others.

**Call:** `query.QuickActionDefinition`

#### `get-global-action`

Fetch a single QuickActionDefinition record by its Tooling API Id.

**Call:** `sobjects/QuickActionDefinition/{id}`

### Write operations

#### `create-global-action`

Create a new QuickActionDefinition record via the Tooling API. Required fields vary by Type — at minimum provide Label, DeveloperName, and Type. Verify the action appears in Setup > Global Actions after creation.

**Call:** `sobjects/QuickActionDefinition`

#### `delete-global-action`

Delete a QuickActionDefinition record by its Tooling API Id. Verify the action is not assigned to any layout before deleting — removing an action that is part of a GlobalPublisherLayout will fail.

**Call:** `sobjects/QuickActionDefinition/{id}`
