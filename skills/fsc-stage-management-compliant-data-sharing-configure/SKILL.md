---
name: fsc-stage-management-compliant-data-sharing-configure
parent: "digital-origination-stage-management-setup"
purpose: "Configure Compliant Data Sharing for stage management — org-wide sharing, the two CDS permission sets, object enablement, participant roles, and participant groups."
description: "Configure Compliant Data Sharing (CDS) for Stage Management for Digital Lending: set org-wide sharing for the Application Form, Application Form Product, and Party Profile objects to Private or Public Read-Only; create the FSCCDSUser and FSCCDSConfigUser permission sets; enable CDS on those three objects; create the nine participant roles (No Access / Read Write / Read Only per object); and create the Agent_Group and Underwriter_Group participant groups. These artifacts carry exact API names the CDS Apex resolves at runtime, so it never invents or renames them silently."
metadata:
  version: "1.0"
  cliTools:
  - tool:
    - "sf"
    semver: ">=2.0.0"
---

# Digital Origination Stage Management — Compliant Data Sharing

Set up the Compliant Data Sharing foundation that Stage Management drives. As an application form product
moves through its stages, the CDS Apex creates or updates participant records so bankers, underwriters,
and applicants gain or lose access. This sibling creates every CDS artifact those participant records
depend on. It does not deploy the Apex, create the Flow, build the matrices, or create the stage
definition.

Source: Salesforce Help "Set Up Compliant Data Sharing for Stage Management Digital Lending" and its
five child articles (CDS permission sets, object enablement, participant roles, participant groups).

## Inputs

- Target-org alias and acting admin.
- The three objects are fixed by the feature: `ApplicationForm`, `ApplicationFormProduct`, `PartyProfile`.
- The admin's per-stage access policy (which role gets Read/Write, Read Only, or No Access at each stage)
  — this drives the participant-role set and, later, the decision-matrix rows. Do not infer it.

## The exact-name contract

The CDS Apex (`AutoLoanCDSUtil`) resolves these artifacts **by API/developer name at runtime**. Create
them with exactly these names, or thread any admin-approved rename into the Apex before it is deployed:

- CDS user permission set: `FSCCDSUser`
- Participant groups: `Agent_Group`, `Underwriter_Group`
- Participant role API names begin with `ApplicationForm`, `ApplicationFormProduct`, `PartyProfile`.

## Step 1 — Org-wide sharing

Set the org-wide default sharing for `ApplicationForm`, `ApplicationFormProduct`, and `PartyProfile` to
**Private** or **Public Read-Only** (CDS requires the baseline be no broader than Read-Only so CDS grants
are additive). Confirm the current setting first; report a change as an org-wide effect and apply only
after confirming the target org. Follow Salesforce Help "Configure Your Org for Compliant Data Sharing",
"Configure Page Layouts for CDS", and "Manage Users in CDS" for the page-layout and user steps.

## Step 2 — CDS permission sets

Create two permission sets (License = **None** on both):

- **`FSCCDSUser`** (label `FSCCDSUser`) — grant the **Use Compliant Data Sharing** system permission.
  On a headless `PermissionSet` write the literal field is **`PermissionsUseCompliantDataSharing = true`**.
  This exact developer name is referenced by the Apex; a rename must be threaded into the Apex constant.
- **`FSCCDSConfigUser`** (label `FSCCDSConfigUser`) — grant **Configure Compliant Data Sharing**
  (field **`PermissionsConfigCompliantDataSharing = true`**); deselect **Use Compliant Data Sharing**
  (`PermissionsUseCompliantDataSharing = false`) if it was set.

Create them via the Metadata/Tooling API (or sObject REST for `PermissionSet` + `SetupEntityAccess` /
`PermissionSetPermissions` where available), describing first. Reuse an exact-match existing set rather
than creating a duplicate.

## Step 3 — Enable CDS on the objects (proven: Metadata API `IndustriesSettings`)

Turn on Compliant Data Sharing for `ApplicationForm`, `ApplicationFormProduct`, and `PartyProfile`.
**The proven headless path is a Metadata API `IndustriesSettings` deploy** (org-verified on fsc-dop8,
v63.0) — the Aura `updateEntityPreference` write 501s and the Org Preferences API rejects the `Cds*`
bits, so use MDAPI:

```xml
<!-- Industries.settings  (MDAPI filename MUST be Industries.settings, NOT source-format .settings-meta.xml) -->
<IndustriesSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <enableCdsApplicationForm>true</enableCdsApplicationForm>
    <enableCdsApplicationFormProduct>true</enableCdsApplicationFormProduct>
    <enableCdsPartyProfile>true</enableCdsPartyProfile>
</IndustriesSettings>
```

Package this with `package.xml` (`<members>Industries</members>` / `<name>Settings</name>`) and deploy it
**headlessly through the Metadata API REST `deployRequest` endpoint** (base64-zip POST, then poll the
deploy status) — no CLI required. Re-read the entity CDS state (`describe`) to confirm. (On a local
workstation the same zip can be deployed with `sf project deploy start --metadata-dir <dir>` — local-dev
convenience only, not a served path.) If the org disallows Metadata deploys, fall back to Setup →
**Object Enablement Settings** (turn on for CRM and Experience Cloud users) and stop at the Setup
checkpoint until the admin confirms.

## Step 4 — Participant roles

For each of the three objects, create **No Access**, **Read/Write**, and **Read Only** participant roles
(nine total) via Setup → **Participant Roles** → New (or the corresponding sObject/Metadata write,
describe-first). Each role has a Name, an API name, a parent object, and a default access level. The Apex
matches roles by API-name prefix, so keep the object prefix exact:

| Object | Example role API names | Default access |
|---|---|---|
| Application Form | `ApplicationFormNoAccess`, `ApplicationFormRW`, `ApplicationFormRead` | No Access / Read Write / Read Only |
| Application Form Product | `ApplicationFormProductNoAccess`, `ApplicationFormProductRW`, `ApplicationFormProductRead` | No Access / Read Write / Read Only |
| Party Profile | `PartyProfileNoAccess`, `PartyProfileRW`, `PartyProfileRead` | No Access / Read Write / Read Only |

The exact role API names must match the tokens the admin's decision-matrix rows emit (the
`HomeLoan_CDS_Config` matrix outputs comma-separated role lists such as
`ApplicationFormRW, ApplicationFormProductRW, PartyProfileRW`). Agree the naming with the admin up front
so roles, matrix rows, and Apex align.

## Step 5 — Participant groups

Create two participant groups (`Group` sObject with `Type = 'Participant'` — there is no dedicated
ParticipantGroup entity):

- `Agent_Group` (name and developer name `Agent_Group`)
- `Underwriter_Group` (name and developer name `Underwriter_Group`)

These developer names are hardcoded in the Apex (`AGENT_PARTICIPANT_GROUP_NAME` /
`UNDERWRITER_PARTICIPANT_GROUP_NAME`).

**Prerequisite (org-verified):** creating a `Type='Participant'` Group requires the **running/acting
user** to hold **Configure Compliant Data Sharing** — i.e. assign the `FSCCDSConfigUser` perm set (and
`FSCCDSUser`) to the acting user *before* this step. Without it the insert fails
`INSUFFICIENT_ACCESS_ON_CROSS_REFERENCE_ENTITY`. `dispatch` mints a fresh token per call, so a
just-granted `PermissionSetAssignment` takes effect on the very next call.

## Idempotency and rollback

- Query for an exact-match perm set, role, or group by API/developer name before creating; reuse it.
- On a shape mismatch (e.g. a role with the right name but wrong default access), present the diff and
  stop rather than overwriting.
- Rollback removes only artifacts created by this run, and only after confirming no participant record,
  Apex, or matrix row depends on them.
- Never change org-wide sharing back without explicit approval — other features may now depend on it.

## Output contract

Return: the org-wide sharing setting for each object (prior and final), the two perm set Ids and API
names with their granted permissions, the CDS object-enablement state for all three objects, the nine
participant role Ids/API names/default access, and the two participant group Ids/developer names.

## Definition of done

Org-wide sharing for the three objects is Private or Public Read-Only; CDS is enabled on all three; the
`FSCCDSUser` and `FSCCDSConfigUser` perm sets exist with the correct system permissions; the nine
participant roles exist with matching API-name prefixes and the intended default access; and the
`Agent_Group` and `Underwriter_Group` participant groups exist. Any missing feature/object or unresolved
checkpoint is reported; a partial run is never reported as complete.
