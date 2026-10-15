---
name: industries-contact-center-app-layout-configure
description: "Act 4 of Contact Center for Health Cloud setup — make the Contact Center Lightning app visible and the default on the contact center profile; add Gender and Birthdate plus the Medication Statements and Member Plans related lists to the Person Account page layout (retrieve, edit, deploy the whole layout, read back); report Timeline state without configuring it."
metadata:
  version: "1.0"
---

# Act 4 of 5 — App default and Person Account page layout (setup-page steps 6, 7 and 3)

Part of the `contact-center-setup` skill. Needs Act 1's toggle (the app) and Act 2's
contact center profile.

## What this Act does

### Step 6 — Make Contact Center easily accessible to users

1. **Find the app.** `SELECT ApplicationId, Name, Label, NamespacePrefix FROM AppMenuItem WHERE Type = 'TabSet'`
   and pick the row whose label is the Contact Center app. It appears once Contact Center for Health
   Cloud is on — if it is missing, re-check Act 1 before anything else. Use the returned `Name`
   (with namespace prefix if any) as the app's full name; never guess it.
2. **Read current visibility.** Retrieve the contact center profile **together with** that
   `CustomApplication` in one package — a profile retrieve only returns `applicationVisibilities` for
   apps in the same package.
3. **Deploy** (dry-run first) a partial Profile:

   ```xml
   <Profile xmlns="http://soap.sforce.com/2006/04/metadata">
     <applicationVisibilities>
       <application>APP_FULL_NAME</application>
       <default>true</default>
       <visible>true</visible>
     </applicationVisibilities>
   </Profile>
   ```

   Setting a new default clears the old one on that profile — say so in the report ("Reps on the
   Contact Center User profile now land in the Contact Center app instead of Service").
4. **Verify** with the paired retrieve from step 2.

### Step 7 — Configure the Person Account page layout

1. **Find the layout reps actually see.** The default is `PersonAccount-Person Account Layout`, but
   the contact center profile may be assigned another — read the profile's `layoutAssignments`
   (retrieve the profile with the `Layout` members) and use the assigned one. Tell the admin the
   layout applies to **every** profile assigned to it.
2. **Retrieve** that layout. A Layout deploy replaces the whole layout — always edit the retrieved
   XML, never deploy a fragment.
3. **Edit, only what is missing:**
   - Fields **Gender** (`PersonGender`) and **Birthdate** (`PersonBirthdate`) in a details section
     (`<layoutItems><behavior>Edit</behavior><field>PersonBirthdate</field></layoutItems>`).
   - Related lists **Medication Statements** and **Member Plans**. For these standard Health Cloud
     children the layout token is the plural child object name — `MedicationStatements`,
     `MemberPlans` (the shipped layout's `ClinicalServiceRequests` follows the same form). It is
     **not** `Child.LookupField` (`MedicationStatement.PatientId` → *Invalid related list*) and
     **not** the describe `relationshipName` (`Medication_Statement_Patient` → *Cannot find related
     list*). If the dry-run still rejects a token, retrieve a layout that already shows the list
     (or ask the admin to add it once in the layout editor) and copy its exact token — don't guess
     variants.
   - Help also suggests the **Service Appointments** related list; offer it.
4. **Dry-run, deploy, retrieve again** and confirm each item is present.

### Step 3 — Timeline (report only)

Timeline is deferred in this version. Read whether a Timeline configuration exists for Person Account
(the approved `Timeline` node's read step) and report: *"Timeline isn't set up by this skill yet. In
Setup, open Timeline and add the Engagement Interactions, Engagement Topics and Cases categories to
the Person Account timeline."* List it under *What the admin finishes by hand*. Help orders Identity
Verification after Timeline; Act 5 notes that dependency.

## Act end state

- The Contact Center app is visible and the default on the contact center profile, read back.
- The reps' Person Account layout shows Gender, Birthdate, Medication Statements and Member Plans,
  read back.
- Timeline state reported.

## Gotchas

- **Paired retrieve.** Profile `applicationVisibilities` and `layoutAssignments` come back only when
  the app / layout is in the same retrieve.
- **Layouts replace whole.** Fragment deploys wipe sections.
- **Person Account fields are `Person*` on Account.** `Gender` on Contact is a different field.
- **Dynamic Forms bypass the layout.** If the reps' Lightning record page places fields with Dynamic
  Forms, layout fields don't show there — report it so the admin adds them in Lightning App Builder.

## Permission sets this Act may assign

None.
