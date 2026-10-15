---
name: experience-field-service-app-builder-configure
description: "Use this skill when users want to configure the Field Service mobile app navigation tabs experience for technicians and dispatchers: create / clone / update / delete app configurations, assign user profiles, and configure navigation tabs. Trigger when users mention field, service, app, builder, field service app builder."
metadata:
  version: "1.0"
  accessCheck: "MobileBuilder.userCanViewMobileBuilder"
---

# Managing Field Service App Builder

## When to Use This Skill

Configure the Field Service mobile app navigation tabs experience for technicians and dispatchers:
create / clone / update / delete app configurations, assign user profiles, and configure navigation tabs.

Supported tab types: Content Libraries, Inventory, Lightning Web Component (LWC), List View,
LWC Attributes, Notifications, Schedule, Time Sheet.

appType is constrained to "Sfs" for this SOR. App state enum: DRAFT | PUBLISHED. Other builders
(SappMobileHome, SalesCloudMab, CAMA, CLT) use the same controller but have their own Setup pages
and SORs.

create / update / delete app configs now use the Applications Connect API
(/services/data/v67.0/applications/{create,update,delete}/Sfs). The remaining read/profile/publish/
clone steps dispatch through the UI Experience app Aura controller via
/headless/invoke/platform/field-service-app-builder/...

DESTRUCTIVE: delete-app-config permanently removes app configs — confirm with admin before invoking.

CROSS-FEATURE DEPENDENCY: assign-profiles body items carry experienceContainerId + containerType
referencing ExperienceContainer records administered by a sibling Setup workflow
(the Experience container operation, guard view Experience profile assignment). This SOR does
NOT create containers — read existing values from get-profile-assignments output and reuse them.

## Workflow

Typical create flow: get-apps → create-app-config → assign-profiles → publish-experience-metadata → verify-get-apps.

Reuse appId from get-apps output across all downstream steps that need an app reference.

Reuse experienceContainerId from get-profile-assignments output when calling assign-profiles — those
container records are administered by a sibling SOR (CustomApp / ExperienceContainer); this SOR does
not create them.

Navigation menu (create/update contents): the nav menu MUST include the mandatory Notifications item
(experience/namedPage → pageName "Notifications"); min 1 / max 15 items; sub-menus are not allowed.

Verify-after-write: after create / update / clone-app-config → re-read get-apps; after assign-profiles
→ get-profile-assignments; after publish → check lastPublished and state == PUBLISHED.

## Critical Constraints

**Preconditions:**

- User must have MobileBuilder ViewMobileBuilder access (check: `Mobile App Builder access`)
- (precondition) (check: `Mobile App Builder access`)

**Destructive operations — require explicit user confirmation:**

- **`delete-app-config`** — Delete an SFS app and all its draft content via the Applications Connect API. Identify the app by
id (8sa...) or developerName in the path; appType is NOT in the URL (resolved from the stored
container). Empty body. Returns {deletedExperienceContainerId, status:DELETED}. NOTE: the backend
blocks deletion of apps that still have live ExperienceContainers (business rule, not a skill error).
  - Rollback: No automatic rollback.

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `get-apps` | read | proposed | `GET /headless/invoke/platform/field-service-app-builder` | — |
| `get-profile-assignments` | read | proposed | `GET /headless/invoke/platform/field-service-app-builder/get-profile-assignments` | — |
| `assign-profiles` | write | proposed | `PATCH /headless/invoke/platform/field-service-app-builder/assign-profiles` | — |
| `update-app-config` | write | proposed | `POST /services/data/v67.0/applications/update/{appIdOrDevName}/Sfs` | — |
| `create-app-config` | write | proposed | `POST /services/data/v67.0/applications/create/Sfs` | — |
| `publish-experience-metadata` | write | proposed | `PATCH /headless/invoke/platform/field-service-app-builder/publish-experience-metadata` | — |
| `clone-app-config` | write | proposed | `PATCH /headless/invoke/platform/field-service-app-builder/clone-app-config` | — |
| `delete-app-config` | delete | proposed | `POST /services/data/v67.0/applications/delete/{appIdOrDevName}` | — |

### Read operations

#### `get-apps`

Get apps.

**Call:** `GET /headless/invoke/platform/field-service-app-builder`   — status: `proposed`

**Inputs:**

- `appType` *(`String`)*

#### `get-profile-assignments`

Get profile assignments.

**Call:** `GET /headless/invoke/platform/field-service-app-builder/get-profile-assignments`   — status: `proposed`

**Inputs:**

- `appType` *(`String`)*

### Write operations

#### `assign-profiles`

Assign profiles.

**Call:** `PATCH /headless/invoke/platform/field-service-app-builder/assign-profiles`   — status: `proposed`

**Inputs:**

- `profileAssignments` *(`List<Map<String, Object>>`)* — Value for profile assignments.

#### `update-app-config`

Update an existing SFS app (draft) via the Applications Connect API. All body fields optional.
contents items WITH an id are updated; WITHOUT an id are created; deleteResourceIds removes resources.
The nav menu must still satisfy the guardrails (mandatory Notifications item; min 1 / max 15; no
sub-menus). Identify the app by id (8sa...) or developerName in the path. Returns 201 with
{status:DRAFT, created/updated/deletedResourceIds}.

**Call:** `POST /services/data/v67.0/applications/update/{appIdOrDevName}/Sfs`   — status: `proposed`

**Inputs:**

- `appType` *(`String`)* — Value for the app type field.
- `label` *(`String`)* — Value for the label field.
- `appId` *(`String`)* — Id of the app.

#### `create-app-config`

Create a new SFS (Field Service) app configuration (draft) via the Applications Connect API.
Body: developerName + label + contents. contents carries a navigation menu (experience__sfsECDefinition
with navMenuId + experience__navigationMenu with the nav items). The menu MUST include the mandatory
Notifications item; min 1 / max 15 items; no sub-menus. Returns 201 {id, name, type:Sfs,
isPublished:false}; id is the experienceContainerId used by update/delete.

**Call:** `POST /services/data/v67.0/applications/create/Sfs`   — status: `proposed`

**Inputs:**

- `appType` *(`String`)* — Value for the app type field.
- `label` *(`String`)* — Value for the label field.
- `apiName` *(`String`)* — Name of the api.
- `contentTypeFqn` *(`String`)* — Value for the content type fqn field.

#### `publish-experience-metadata`

Publish experience metadata.

**Call:** `PATCH /headless/invoke/platform/field-service-app-builder/publish-experience-metadata`   — status: `proposed`

**Inputs:**

- `appId` *(`String`)* — Id of the app.

#### `clone-app-config`

Clone app config.

**Call:** `PATCH /headless/invoke/platform/field-service-app-builder/clone-app-config`   — status: `proposed`

**Inputs:**

- `appType` *(`String`)* — Value for the app type field.
- `label` *(`String`)* — Value for the label field.
- `apiName` *(`String`)* — Name of the api.
- `appId` *(`String`)* — Id of the app.

### Destructive operations

#### `delete-app-config`

Delete an SFS app and all its draft content via the Applications Connect API. Identify the app by
id (8sa...) or developerName in the path; appType is NOT in the URL (resolved from the stored
container). Empty body. Returns {deletedExperienceContainerId, status:DELETED}. NOTE: the backend
blocks deletion of apps that still have live ExperienceContainers (business rule, not a skill error).

**Call:** `POST /services/data/v67.0/applications/delete/{appIdOrDevName}`   — status: `proposed`

**Inputs:**

- `appType` *(`String`)*
- `appId` *(`String`)*
