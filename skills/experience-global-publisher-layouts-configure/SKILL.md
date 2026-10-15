---
name: experience-global-publisher-layouts-configure
description: "Use this skill when users want to manage the Global Publisher Layout in Salesforce Setup. Trigger when users mention global, publisher, layouts, global publisher layouts."
metadata:
  version: "1.0"
---

# Managing Global Publisher Layouts

## When to Use This Skill

Manage the Global Publisher Layout in Salesforce Setup. The Global Publisher
Layout controls which actions appear in the global publisher bar for all users
org-wide. It is represented in the Metadata API as a Layout record named
"Global-Global Layout" containing a quickActionList with quickActionListItems
(each item is an action name like NewEvent, LogACall, NewContact, etc.).

The canonical way to read and update this layout is via the Metadata API,
routed through /headless/metadata (dispatch dispatches read vs. write
per op — no separate transport to model):
- Read: metadataRetrieveLayout with fullName "Global-Global Layout"
- Update: round-trip the retrieved body, edit quickActionList, then
  metadataUpdateLayout with the modified body

The Layout metadata shape is:
  quickActionList:
    quickActionListItems:
      - quickActionName: NewEvent
      - quickActionName: LogACall
      ...

To add an action: add a quickActionListItems entry with the action's DeveloperName.
To remove an action: remove the corresponding quickActionListItems entry.
To reorder: change the order of quickActionListItems entries.
Action names must match existing QuickActionDefinition DeveloperNames.

## Critical Constraints

**Preconditions:**

- Requires Customize Application permission to deploy Layout metadata.
- Action names used in the layout must be DeveloperNames of existing QuickActionDefinition records. Adding a non-existent action name will cause the deploy to fail.
- The update step must round-trip the exact body returned by the read step (read-global-publisher-layout) — Layout metadata update is full-replace, so omitting fields from the retrieved body will drop them from the deployed layout.

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `read-global-publisher-layout` | read | — | `/headless/metadata` | — |
| `update-global-publisher-layout` | write | — | `/headless/metadata` | `read-global-publisher-layout` |
| `list-available-actions` | read | — | `query.QuickActionDefinition` | — |

### Read operations

#### `read-global-publisher-layout`

Retrieve the Global Publisher Layout via the Metadata API. The layout is named "Global-Global Layout" and contains the list of actions in the global publisher bar. Target /headless/metadata (dispatch dispatches the retrieve); the response is the Layout metadata with its current quickActionList and all quickActionListItems.

**Call:** `/headless/metadata`

#### `list-available-actions`

Query QuickActionDefinition records to find available actions that can be added to the Global Publisher Layout. Use fields Id, DeveloperName, Label, Type to identify actions. The DeveloperName is the value used in the layout XML.

**Call:** `query.QuickActionDefinition`

### Write operations

#### `update-global-publisher-layout`

Update the Global Publisher Layout via the Metadata API. Target /headless/metadata (dispatch dispatches the deploy; the dispatcher routes sync-CRUD vs. the XML-deploy shim per op — no method/body modeled here). Retrieve the current layout first (read-global-publisher-layout step), round-trip its body while adding, removing, or reordering quickActionListItems entries. Action names must match DeveloperName values of existing QuickActionDefinition records.

**Call:** `/headless/metadata`

**Depends on:** `read-global-publisher-layout`
