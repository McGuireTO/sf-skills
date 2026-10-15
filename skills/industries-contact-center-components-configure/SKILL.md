---
name: industries-contact-center-components-configure
description: "Act 5 of Contact Center for Health Cloud setup — the contact center components: an Identity Verification process that searches by account name, account number, phone number or postal code; the Action Launcher and Record Alerts on the reps' record page; the Patient Card and Profile Card / Member Plan FlexCards (report); and an optional Open CTI softphone (detect and hand off)."
metadata:
  version: "1.0"
---

# Act 5 of 5 — Contact center components

Part of the `contact-center-setup` skill. These are the Help article's components,
not numbered setup-page steps. Help orders Identity Verification **after** Contact Center and
Timeline — Act 1 and the Act 4 Timeline report come first.

Ask the admin which components they want before writing; any component they decline is recorded as
*skipped by choice*, not as a gap.

## What this Act does

### Identity Verification

Reps verify a caller by **account name, account number, phone number or postal code** (Help).

1. **Detect** — read the process and its records:
   `SELECT Id, DeveloperName, MasterLabel FROM IdentityVerificationProcDef`, then its
   `IdentityVerificationProcDtl` (search objects) and `IdentityVerificationProcFld` (search and
   verification fields).
2. **Report.** A shipped sample process may already exist. Show what it searches and verifies on,
   in plain words, and ask whether it fits or whether to create the contact center's own process.
3. **Create on confirmation** of the search object (Account / Person Account) and fields — use the
   sObject creates on `IdentityVerificationProcDef`, then `IdentityVerificationProcDtl`, then
   `IdentityVerificationProcFld`, and read them back. Account Number access for the reps is Act 2's
   step 8; re-check it here if Act 2 didn't run.
4. **Placement.** The Identity Verification component goes on the record page or utility bar the reps
   use — same placement pattern as the Action Launcher below.
5. **Verify** by re-reading the definition, details and fields.

### Action Launcher

Contextual quick actions for the contact center.

1. **Find the reps' record page** — the Person Account Lightning record page assigned for the Contact
   Center app and profile (`SELECT DeveloperName, MasterLabel, EntityDefinitionId FROM FlexiPage WHERE Type = 'RecordPage'`
   via Tooling, then read the app's `profileActionOverrides` from the `CustomApplication` retrieve).
2. **Detect** — retrieve the FlexiPage; look for an Action Launcher `componentInstance`.
3. **Place.** If another FlexiPage in the org already contains the Action Launcher, copy its exact
   `componentName` and properties into the retrieved page, dry-run, deploy the whole page, retrieve
   again. Otherwise hand off: *"In Lightning App Builder, open the record page your reps use, drag
   Action Launcher into the right column, and save."* — then retrieve and confirm. Never guess a
   component name.
4. Customizing which actions it shows (deployment and action categories) is the admin's choice;
   report what is configured.

### Record Alerts

Informs reps about record changes that need attention.

1. Reps need Read, Create, Edit on Record Alert — Act 2's object permissions. Re-check if Act 2
   didn't run.
2. Detect the Record Alerts component on the reps' record page (same retrieve as above); place it
   the same way.
3. Alerts themselves come from the org's data and integrations; report how many `RecordAlert` rows
   exist, don't create sample alerts.

### FlexCards — Patient Card, Profile Card and Member Plan (report)

Patient Card (medication requests, health conditions, allergies, immunizations) and Profile Card /
Member Plan show on the record page as OmniStudio FlexCards. Detect whether they're on the page;
reps need the OmniStudio User permission set (Act 2). Placement uses the same retrieve-or-hand-off
pattern. Don't author or edit FlexCard definitions.

### Open CTI softphone (optional)

Only if the admin uses a third-party telephony provider through Open CTI.

1. Ask first. Skip by default if they use Service Cloud Voice instead.
2. Detect call centers — `SELECT Id, Name, InternalName FROM CallCenter`. Softphone layouts are
   checked in Setup.
3. Hand off the call-center import (the provider supplies the definition file) and adding users to
   the call center; verify by re-reading the call centers.

## Act end state

- Each component the admin chose is present and read back; each declined one recorded as skipped.
- The Identity Verification process searches the fields the admin confirmed.

## Gotchas

- **FlexiPages replace whole** — edit the retrieved XML, deploy the full page.
- **Activation lives on the app / profile, not the page.** Adding a component to an unassigned page
  changes nothing reps see — confirm which page is assigned first.
- **Don't duplicate the sample identity process** without asking; reps would see two verification
  flows.

## Permission sets this Act may assign

None. OmniStudio User for FlexCards and the Action Launcher is Act 2's.
