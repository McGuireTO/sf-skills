---
name: industries-contact-center-path-knowledge-configure
description: "Act 3 of Contact Center for Health Cloud setup — turn on Path Settings and deploy an active Engagement Interaction path on Status (New, In Progress, Completed); make sure Lightning Knowledge is on, rep users are Knowledge users (on confirmation) and a How-To article record type exists, following the Service Setup Assistant's outcome."
metadata:
  version: "1.0"
---

# Act 3 of 5 — Engagement Interaction path and Knowledge (setup-page steps 4 and 5)

Part of the `contact-center-setup` skill. Runs after
Act 2 (`contact-center-setup-act2-user-access`) (reps and their profile are known).

## What this Act does

### Step 4 — Configure Engagement Interaction Path

1. **Detect Path Settings** — one `Settings:PathAssistant` retrieve; read `pathAssistantEnabled`.
2. If off, deploy the minimal settings document on its own (split-deploy — the path deploy fails while
   Path Settings is off):

   ```xml
   <PathAssistantSettings xmlns="http://soap.sforce.com/2006/04/metadata">
     <pathAssistantEnabled>true</pathAssistantEnabled>
   </PathAssistantSettings>
   ```

   Read it back.
3. **Detect an existing path** — Tooling
   `SELECT Id, MasterLabel, SobjectType, IsActive FROM PathAssistant WHERE SobjectType = 'EngagementInteraction'`.
   An active one already exists → report it and write nothing. An inactive one → ask whether to
   activate it rather than create a second.
4. **Read the Status values** — `GET /sobjects/EngagementInteraction/describe`, field `Status`. Use the
   org's active values in their order (shipped: New, In Progress, Completed). Never invent values.
5. **Deploy the path** (dry-run first), master record type:

   ```xml
   <PathAssistant xmlns="http://soap.sforce.com/2006/04/metadata">
     <active>true</active>
     <entityName>EngagementInteraction</entityName>
     <fieldName>Status</fieldName>
     <masterLabel>Engagement Interaction Path</masterLabel>
     <recordTypeName>__MASTER__</recordTypeName>
     <pathAssistantSteps><picklistValueName>New</picklistValueName></pathAssistantSteps>
     <pathAssistantSteps><picklistValueName>In Progress</picklistValueName></pathAssistantSteps>
     <pathAssistantSteps><picklistValueName>Completed</picklistValueName></pathAssistantSteps>
   </PathAssistant>
   ```

   File: `pathAssistants/Engagement_Interaction_Path.pathAssistant-meta.xml`. If Engagement Interaction
   has record types the reps use, ask which; one path per record type.
6. **Verify** with the Tooling query from step 3 — `IsActive = true`.

Guidance text per step (*Key fields*, *Guidance for success*) is optional; offer it, don't invent it.

### Step 5 — Let users access Knowledge articles

Help: *"Follow the Service Setup Assistant to add users who can create knowledge articles."* The
skill reaches the same end state directly:

1. **Detect Knowledge** — retrieve the `KnowledgeSettings` metadata; read `enableKnowledge`
   and `enableLightningKnowledge`.
2. If Lightning Knowledge is off: this is **one-way** (it cannot be turned off once on) and the plan
   must have named it. Deploy `KnowledgeSettings` with `enableKnowledge` true and
   `enableLightningKnowledge` true; read back. Turning Knowledge on needs at least one Knowledge
   user — the running admin is usually flagged by the same step; check.
3. **Knowledge users** — `SELECT Id, Name, UserPermissionsKnowledgeUser FROM User WHERE Id IN (…reps…)`.
   Flagging a user consumes a Knowledge feature license: report seats, **confirm**, then
   `PATCH /sobjects/User/{id}` with `UserPermissionsKnowledgeUser: true`. Read back.
4. **Article record type** — `SELECT DeveloperName, Name, IsActive FROM RecordType WHERE SobjectType = 'Knowledge__kav'`.
   If none, deploy a `How_To` record type on `Knowledge__kav` (label *How To*, active) and add it to
   the contact center profile's `recordTypeVisibilities` in a partial Profile deploy. Ask if the
   org uses a different article type name (some orgs use *FAQ*). The Knowledge object's API name
   may differ if the admin renamed it at enablement — read it from the Knowledge settings first.
5. **Knowledge LSF Permission Set** — Act 2 assigns it where the org has it. Mention it here if Act 2
   reported it missing.
6. Data categories and article visibility are optional; report what exists (list `DataCategoryGroup`
   metadata) and leave them to the admin.

## Act end state

- Path Settings on; an active Engagement Interaction path on Status, read back.
- Lightning Knowledge on; confirmed reps flagged as Knowledge users; an active article record type
  visible to the contact center profile.

## Gotchas

- **Path deploy before Path Settings fails.** Two transactions.
- **Lightning Knowledge is permanent.** Never turn it on without the plan having said so.
- **`UserPermissionsKnowledgeUser` fails without a seat** — report `LICENSE_LIMIT_EXCEEDED` in plain
  words ("you're out of Knowledge user licenses"), don't retry.
- **Don't create duplicate paths.** One active path per object + record type.

## Permission sets this Act may assign

None directly. The Knowledge User flag on rep users is confirmed per user like a permission set.
