---
name: experience-sales-cloud-mab-configure
description: "Use this skill when users want to configure the Sales Cloud mobile app builder for the Seller-Focused Experience — list, create, clone, update, and delete app configs and their per-object record home configs, assign profiles, and publish. Trigger when users mention sales, cloud, mab, sales cloud mab."
metadata:
  version: "1.0"
  accessCheck: "MobileBuilder.userCanViewMobileBuilder"
---

# Managing Sales Cloud Mab

## When to Use This Skill

Configure the Sales Cloud mobile app builder for the Seller-Focused Experience — list, create, clone, update, and delete app configs and their per-object record home configs, assign profiles, and publish. Covers only the Seller-Focused operations of this shared builder; CAMA / Agentforce-action operations are explicitly out of scope (they route to a different service and belong to a separate SOR). DESTRUCTIVE: delete-app-config permanently removes an app config and all its record home configs, and delete-record-home-config removes a single object's record home config — both are unrecoverable, so confirm with the admin before invoking.

## Workflow

Typical create flow: get-apps → create-app-config → get-entities → create-sc-record-home-config (one per object; this publishes) → assign-profiles.

Sequencing constraint — assign-profiles: a profile can only be assigned to a published app config, and an app config with zero record home configs is never published. So always create at least one record home config (via create-sc-record-home-config, which publishes internally) before calling assign-profiles. The backend does not enforce this; the agent must, to match what the admin UI allows.

Reuse appId from get-apps output across all downstream steps that need an app reference. For create-sc-record-home-config, source objectApiName (the value) and objectName (the display text) from get-entities. API Name for create/clone is normally derived from the App Name label (no special characters, no whitespace, no consecutive underscores; must be unique among existing app configs) — don't prompt the user for it separately. contentTypeFqn is not used by this builder; omit it.

Reuse experienceContainerId and the other fields from get-profile-assignments output when calling assign-profiles — read existing values and reuse them.

Verify-after-write: after create / clone / delete-app-config → re-read get-apps (presence/absence of the appId); after update-app-config → get-apps and check the label changed (NOT state); after create / delete-sc-record-home-config → get-sc-record-home-config-summary; after assign-profiles → get-profile-assignments; after publish-experience-metadata → get-apps and check lastPublished advanced (NOT state).

Backend mechanics and constraints:
- Content type: this builder serves the experience__scmabRecordHome content type.
- Two-stage model: (1) top-level app configuration — an Experience Container created with an App Name and an API Name; a newly created app config is empty and unpublished. (2) per-object record home configurations — within an app config, create one record home page layout per object (e.g. Account, Contact). Creating a record home config publishes the app metadata as a side effect, so publish-experience-metadata is usually redundant in normal flows.
- appType is constrained to Scma for this SOR — a single valid value, not a multi-option enum.
- Dispatch: all operations dispatch through a shared internal UI controller via /headless/invoke/platform/sales-cloud-mab/.... This controller is shared across all six Mobile Builder flavors; only the Seller-Focused operations are in scope for this SOR.
- Operation inventory: list app configs (get-apps), create / clone / update / delete app configs, list / create / delete per-object record home configs, list available objects (get-entities), assign profiles, and publish.
- Deletion detail: delete-app-config unassigns any assigned profiles first, then permanently removes the app config and all its record home configs; delete-record-home-config removes a single object's record home config. Both are unrecoverable.
- Do NOT rely on the state field returned by get-apps — it is hardcoded to DRAFT. Determine published status from the lastPublished timestamp instead.

## Critical Constraints

**Preconditions:**

- User must have MobileBuilder ViewMobileBuilder access (check: `Mobile App Builder access`)
- (precondition) (check: `Mobile App Builder access`)

**Destructive operations — require explicit user confirmation:**

- **`delete-record-home-config`** — Delete a single object's record home configuration from an app config. Takes appId and contentKey. DESTRUCTIVE and unrecoverable. Confirm with admin before invoking. Verify via get-sc-record-home-config-summary (contentKey should be absent).
  - Rollback: No automatic rollback.
- **`delete-app-config`** — Delete a top-level SCMA app and all its record-home configs via the Applications Connect API
(POST /services/data/v67.0/applications/delete/{appIdOrDevName}). Identify the app by id (8sa...)
or developerName in the path; appType is NOT in the URL (resolved from the stored container).
Empty body. DESTRUCTIVE and unrecoverable — confirm with admin before invoking. Returns
{deletedExperienceContainerId, status:DELETED}. Verify via get-apps (appId absent).
  - Rollback: No automatic rollback.

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `get-apps` | read | proposed | `GET /headless/invoke/platform/sales-cloud-mab` | — |
| `get-apps-and-guardrails-info` | read | proposed | `GET /headless/invoke/platform/sales-cloud-mab/get-apps-and-guadrails-info` | — |
| `get-profile-assignments` | read | proposed | `GET /headless/invoke/platform/sales-cloud-mab/get-profile-assignments` | — |
| `assign-profiles` | write | proposed | `PATCH /headless/invoke/platform/sales-cloud-mab/assign-profiles` | `create-sc-record-home-config` |
| `update-app-config` | write | proposed | `POST /services/data/v67.0/applications/update/{appIdOrDevName}/Scma` | — |
| `get-sc-record-home-config-summary` | read | proposed | `GET /headless/invoke/platform/sales-cloud-mab/get-sc-record-home-config-summary` | — |
| `delete-record-home-config` | delete | proposed | `DELETE /headless/invoke/platform/sales-cloud-mab/delete-record-home-config` | — |
| `create-sc-record-home-config` | write | proposed | `PATCH /headless/invoke/platform/sales-cloud-mab/create-sc-record-home-config` | — |
| `create-app-config` | write | proposed | `POST /services/data/v67.0/applications/create/Scma` | — |
| `get-variant-id` | read | implemented | `GET /headless/invoke/platform/sales-cloud-mab/get-variant-id` | — |
| `publish-experience-metadata` | write | proposed | `PATCH /headless/invoke/platform/sales-cloud-mab/publish-experience-metadata` | — |
| `get-entities` | read | implemented | `GET /headless/invoke/platform/sales-cloud-mab/get-entities` | — |
| `clone-app-config` | write | proposed | `PATCH /headless/invoke/platform/sales-cloud-mab/clone-app-config` | — |
| `delete-app-config` | delete | proposed | `POST /services/data/v67.0/applications/delete/{appIdOrDevName}` | — |

### Read operations

#### `get-apps`

List all Seller-Focused app configurations (Experience Containers) of type Scma. Returns appId, apiName, appName (label), state (always DRAFT — ignore it), lastPublished timestamp (the real publish indicator), and profile assignments. Use this to enumerate existing configs or verify create/update/delete operations.

**Call:** `GET /headless/invoke/platform/sales-cloud-mab`   — status: `proposed`

**Inputs:**

- `appType` *(`String`)*

#### `get-apps-and-guardrails-info`

List app configurations with additional guardrails metadata. Returns the same core fields as get-apps plus guardrails-specific info. Most flows use get-apps; use this when you need guardrails context.

**Call:** `GET /headless/invoke/platform/sales-cloud-mab/get-apps-and-guadrails-info`   — status: `proposed`

**Inputs:**

- `appType` *(`String`)*

#### `get-profile-assignments`

List profile assignment possibilities for Seller-Focused apps. Returns all profiles in the org with their current assignment state (experienceContainerProfileAssignmentId is non-null if assigned). Use before assign-profiles to read current state.

**Call:** `GET /headless/invoke/platform/sales-cloud-mab/get-profile-assignments`   — status: `proposed`

**Inputs:**

- `appType` *(`String`)*

#### `get-sc-record-home-config-summary`

List record home configurations within an app config. Takes appId. Returns one entry per object (objectApiName, contentKey, objectName). Use to enumerate existing object configs or verify create/delete-record-home-config.

**Call:** `GET /headless/invoke/platform/sales-cloud-mab/get-sc-record-home-config-summary`   — status: `proposed`

**Inputs:**

- `appId` *(`String`)*

#### `get-variant-id`

Get the variant ID for an app config. Takes appId. Returns the variant identifier. Used internally by the UI; most agent flows don't need this.

**Call:** `GET /headless/invoke/platform/sales-cloud-mab/get-variant-id`   — status: `implemented`

**Inputs:**

- `appId` *(`String`)*

#### `get-entities`

List available objects (entities) that can have record home configurations. Returns value (objectApiName) and text (objectName display label). Use before create-sc-record-home-config to source objectApiName and objectName.

**Call:** `GET /headless/invoke/platform/sales-cloud-mab/get-entities`   — status: `implemented`

### Write operations

#### `assign-profiles`

Assign or unassign profiles to/from an app config. Takes profileAssignments (a list of assignment records with profileId, experienceContainerId, and experienceContainerProfileAssignmentId). Read current state via get-profile-assignments first, modify the list, then send. SEQUENCING: can only assign to a published app config (one with ≥1 record home config).

**Call:** `PATCH /headless/invoke/platform/sales-cloud-mab/assign-profiles`   — status: `proposed`

**Inputs:**

- `profileAssignments` *(`List<Map<String, Object>>`)* — Value for profile assignments.

**Depends on:** `create-sc-record-home-config`

#### `update-app-config`

Update a Seller-Focused (SCMA) app via the Applications Connect API
(POST /services/data/v67.0/applications/update/{appIdOrDevName}/Scma). STAGE 2 of the two-stage
model: this is where the per-object record-home layouts are set, via contents.experience__scmabRecordHome
(a list of per-object entries — objectApiName, objectName, sfdc_cms:title, and an sfdc_cms:block tree).
Can also update the label. Identify the app by id (8sa...) or developerName in the path. All body
fields optional; contents items WITH an id are updated, WITHOUT an id are created; deleteResourceIds
removes resources. Returns 201 {status:DRAFT, created/updated/deletedResourceIds}.

BLOCK-TREE RULES (record-home layout): two parent containers —
experience/scmabRecordHomeFixedContainer and experience/scmabRecordHomeContainer.
- FixedContainer allows ONLY: scmabHighlights, scmabActions, scmabStackedTabs — and scmabStackedTabs
  MUST be last.
- scmabStackedTabs may instead live in scmabRecordHomeContainer, but there must be NO duplicate (at
  most one across both containers).
- RecordHomeContainer allows ONLY: scmabActivityTimeline, scmabPath, scmabRelatedList — in any order.

**Call:** `POST /services/data/v67.0/applications/update/{appIdOrDevName}/Scma`   — status: `proposed`

**Inputs:**

- `appType` *(`String`)* — Value for the app type field.
- `label` *(`String`)* — Value for the label field.
- `appId` *(`String`)* — Id of the app.

#### `create-sc-record-home-config`

Create a record home page layout for one object within an app config. Takes appId, objectApiName, and objectName (source both from get-entities). PUBLISHES INTERNALLY — after this succeeds, the app's lastPublished timestamp advances. Verify via get-sc-record-home-config-summary (new objectApiName/contentKey present).

**Call:** `PATCH /headless/invoke/platform/sales-cloud-mab/create-sc-record-home-config`   — status: `proposed`

**Inputs:**

- `appId` *(`String`)* — Id of the app.
- `objectApiName` *(`String`)* — Name of the object api.
- `objectName` *(`String`)* — Name of the object.

#### `create-app-config`

Create a new top-level Seller-Focused (SCMA) app configuration via the Applications Connect API
(POST /services/data/v67.0/applications/create/Scma). STAGE 1 of the two-stage model: body is
developerName + label + minimal contents {experience__scmaECDefinition: [{}]}. Returns 201
{id, name, type:Scma, isPublished:false}; the id is the experienceContainerId used by the update
step (STAGE 2, which adds the per-object record-home layouts) and by delete. New configs are empty
(0 record-home configs) and unpublished. Verify via get-apps (new appId/name present).

**Call:** `POST /services/data/v67.0/applications/create/Scma`   — status: `proposed`

**Inputs:**

- `appType` *(`String`)* — Value for the app type field.
- `label` *(`String`)* — Value for the label field.
- `apiName` *(`String`)* — Name of the api.
- `contentTypeFqn` *(`String`)* — Value for the content type fqn field.

#### `publish-experience-metadata`

Publish an app config's metadata. Takes appId. This operation is somewhat redundant in normal flows — create-sc-record-home-config already publishes internally. Use when you need explicit publish without adding an object config. Verify via get-apps (lastPublished timestamp advanced; not state).

**Call:** `PATCH /headless/invoke/platform/sales-cloud-mab/publish-experience-metadata`   — status: `proposed`

**Inputs:**

- `appId` *(`String`)* — Id of the app.

#### `clone-app-config`

Clone an existing app config. Takes appType (Scma), the source appId, new label, and new apiName (derive from label). Creates a new app config with the same record home configs as the source. If the source has ≥1 object config, the clone is published immediately. Verify via get-apps (cloned appId/apiName present).

**Call:** `PATCH /headless/invoke/platform/sales-cloud-mab/clone-app-config`   — status: `proposed`

**Inputs:**

- `appType` *(`String`)* — Value for the app type field.
- `label` *(`String`)* — Value for the label field.
- `apiName` *(`String`)* — Name of the api.
- `appId` *(`String`)* — Id of the app.

### Destructive operations

#### `delete-record-home-config`

Delete a single object's record home configuration from an app config. Takes appId and contentKey. DESTRUCTIVE and unrecoverable. Confirm with admin before invoking. Verify via get-sc-record-home-config-summary (contentKey should be absent).

**Call:** `DELETE /headless/invoke/platform/sales-cloud-mab/delete-record-home-config`   — status: `proposed`

**Inputs:**

- `appId` *(`String`)*
- `contentKey` *(`String`)*

#### `delete-app-config`

Delete a top-level SCMA app and all its record-home configs via the Applications Connect API
(POST /services/data/v67.0/applications/delete/{appIdOrDevName}). Identify the app by id (8sa...)
or developerName in the path; appType is NOT in the URL (resolved from the stored container).
Empty body. DESTRUCTIVE and unrecoverable — confirm with admin before invoking. Returns
{deletedExperienceContainerId, status:DELETED}. Verify via get-apps (appId absent).

**Call:** `POST /services/data/v67.0/applications/delete/{appIdOrDevName}`   — status: `proposed`

**Inputs:**

- `appType` *(`String`)*
- `appId` *(`String`)*
