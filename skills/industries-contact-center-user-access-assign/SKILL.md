---
name: industries-contact-center-user-access-assign
description: "Act 2 of Contact Center for Health Cloud setup — give contact center reps access: check-report-confirm-assign the Contact Center for Health Cloud, Health Cloud Foundation, Knowledge LSF and OmniStudio User permission sets; create the Contact Center User profile (a Standard User clone) with Read, Create and Edit on Engagement Interaction, Engagement Topic, Engagement Attendee and Record Alert; verify Account Number field-level security; assign the profile on confirmation."
metadata:
  version: "1.0"
---

# Act 2 of 5 — User access (setup-page steps 1, 2 and 8)

Part of the `contact-center-setup` skill. Runs after
Act 1 (`contact-center-setup-act1-prereqs-enable`) has turned Contact Center for Health Cloud on.

## What this Act does

### Step 1 — Assign permissions and licenses to users

1. Ask the admin **which users are contact center reps** (by name or by an existing profile / role).
   Never assume the admin is a rep.
2. For each rep, read assigned permission sets and licenses:
   `SELECT AssigneeId, PermissionSet.Name FROM PermissionSetAssignment WHERE AssigneeId IN (…)` and
   `SELECT AssigneeId, PermissionSetLicense.DeveloperName FROM PermissionSetLicenseAssign WHERE AssigneeId IN (…)`.
3. Required for every rep (query by DeveloperName):

   | UI label | DeveloperName | Note |
   |---|---|---|
   | Contact Center for Health Cloud | `ContactCenterforHealthCloud` | The admin got it in Act 1; reps still need it |
   | Health Cloud Foundation | `HealthCloudFoundation` | |
   | Knowledge LSF Permission Set | resolve by label → `Name` on the org | Only exists if the org has the Salesforce Knowledge feature license; absent = report, not an error |
   | OmniStudio User | `OmniStudioUser` (and `OmniStudioExecution` if a second *OmniStudio User* set exists) | If there are two OmniStudio User sets, assign both |

4. Report the per-user gap in plain language and **assign only what the admin confirms**:
   `POST /sobjects/PermissionSetAssignment`. Permission set licenses are assigned automatically when
   the permission set is assigned; if an assignment fails for a missing license, assign it with
   `POST /sobjects/PermissionSetLicenseAssign` and retry. `DUPLICATE_VALUE` = already assigned.
5. Read assignments back.

### Step 2 — Contact Center User profile and object permissions

1. **Detect the profile.** Ask what the reps' profile is called (suggest *Contact Center User*);
   `SELECT Id, Name, UserLicense.Name FROM Profile WHERE Name = '<name>'`.
2. **If missing — hand off the clone.** Cloning in Setup keeps Standard User's baseline permissions;
   a profile created from metadata starts with almost nothing, so do not create it by deploy:
   *"From Setup, enter Profiles in Quick Find, click Clone next to Standard User, name it Contact
   Center User, and save. Tell me when it's there."* Then re-query.
3. **Object permissions.** Read
   `SELECT SobjectType, PermissionsRead, PermissionsCreate, PermissionsEdit FROM ObjectPermissions WHERE Parent.Profile.Name = '<name>' AND SobjectType IN ('EngagementInteraction','EngagementTopic','EngagementAttendee','RecordAlert')`.
   For anything missing, deploy a **partial Profile** (only these elements) — Read, Create, Edit on all
   four:

   ```xml
   <Profile xmlns="http://soap.sforce.com/2006/04/metadata">
     <objectPermissions>
       <object>EngagementInteraction</object>
       <allowRead>true</allowRead><allowCreate>true</allowCreate><allowEdit>true</allowEdit>
       <allowDelete>false</allowDelete><viewAllRecords>false</viewAllRecords><modifyAllRecords>false</modifyAllRecords>
     </objectPermissions>
     <!-- same for EngagementTopic, EngagementAttendee, RecordAlert -->
     <fieldPermissions>
       <field>Account.AccountNumber</field><readable>true</readable><editable>true</editable>
     </fieldPermissions>
   </Profile>
   ```

   The file name is the profile's API name (for a cloned profile, its name with spaces, e.g.
   `Contact Center User.profile-meta.xml`). Dry-run, deploy, re-read `ObjectPermissions`.
4. **Assign the profile** to the rep users — **confirm first** (changing a user's profile changes
   everything they can do): `PATCH /sobjects/User/{id}` with `ProfileId`. Read back.

### Step 8 — Verify automated setup actions (Account Number field-level security)

Turning Contact Center on grants access to the Account **Account Number** field — identity
verification searches on it. Verify for the contact center profile:
`SELECT PermissionsRead, PermissionsEdit FROM FieldPermissions WHERE SobjectType = 'Account' AND Field = 'Account.AccountNumber' AND Parent.Profile.Name = '<name>'`.
If missing, it rides in the same partial Profile deploy above (`fieldPermissions`). A cloned profile
created **after** the toggle may not have inherited it — always check.

## Act end state

- Each confirmed rep holds the four permission sets (or the Knowledge set reported as unavailable).
- The contact center profile exists with Read, Create, Edit on the four objects and Account Number
  readable, all read back.
- Confirmed reps are on that profile.

## Gotchas

- **Labels vs. names.** *Knowledge LSF Permission Set* has no fixed API name across orgs —
  resolve it by `Label` and use the returned `Name`; zero rows means no Knowledge feature license.
- **Profile deploys are partial; layouts are not.** Listing only `objectPermissions` and
  `fieldPermissions` in a Profile deploy changes only those entries.
- **Don't deploy a new profile.** Clone in Setup; then deploy the deltas.
- **Rep vs. admin.** Assign to the rep users the admin names. The admin gets rep sets only if they ask.

## Permission sets this Act may assign (on confirmation)

Contact Center for Health Cloud, Health Cloud Foundation, Knowledge LSF Permission Set, OmniStudio
User — see `ref:contact-center-setup/source/references/licensing-and-permission-sets`. Plus the profile assignment itself.
