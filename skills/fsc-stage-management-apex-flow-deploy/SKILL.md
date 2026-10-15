---
name: fsc-stage-management-apex-flow-deploy
parent: "digital-origination-stage-management-setup"
purpose: "Deploy the CDSCacheHelper and AutoLoanCDSUtil Apex classes and create the autolaunched Flow that stage transition rules invoke."
description: "Deploy the two Apex classes that power Compliant Data Sharing for Stage Management (CDSCacheHelper, which caches participant role and group name-to-Id maps, and AutoLoanCDSUtil, which exposes the \"Digital Lending CDS\" invocable method that reads the three decision matrices and creates or updates participant records), then create the \"Digital Lending Stage Management\" autolaunched Flow that wraps the Apex so a stage transition rule can call it. Apex and Flow are code artifacts deployed through the Metadata/Tooling API and verified with a fresh read; if the org disallows deploys, the sibling stops at a guided checkpoint. It never hand-edits the delivered class logic beyond the documented developer-name substitutions."
metadata:
  version: "1.0"
  cliTools:
  - tool:
    - "sf"
    semver: ">=2.0.0"
---

# Digital Origination Stage Management — CDS Apex and Flow

Deploy the code that runs on every stage transition. When a stage transition rule fires, an autolaunched
Flow invokes `AutoLoanCDSUtil`, which reads the three decision matrices and creates or updates the CDS
participant records that change who can see the application. This sibling deploys the two Apex classes and
creates the Flow. It does not create the perm sets, groups, matrices, stage definition, or transitions —
it only deploys the code that consumes them.

Source: Salesforce Help "Create an Apex Class CDSCacheHelper"
(`ind.fsc_lending_stage_management_apex_helper`), "Create an Apex Class CDSUtil"
(`ind.fsc_lending_stage_management_apex_cdsutil`), and "Create Digital Lending Stage Management Flow".
The complete, verbatim class bodies are inlined below — deploy them exactly as written (the only permitted
edit is the documented `FSCCDSUser` perm-set-name substitution).

## Prerequisites this sibling depends on

The Apex resolves these by name at runtime, so they must exist (from the `compliant-data-sharing` and
`decision-matrices` siblings) before the Apex can run — though the classes can be **deployed** before the
matrices exist, they will not evaluate correctly until every referenced artifact is present:

- Permission set `FSCCDSUser`
- Participant groups `Agent_Group`, `Underwriter_Group`
- Participant roles prefixed `ApplicationForm`, `ApplicationFormProduct`, `PartyProfile`
- Decision matrices `HomeLoan_CDS_Config`, `AFPStage_To_ApplicantVisibleStatus`, `AFPStage_To_AFStage`

## The two Apex classes

Deploy both classes **verbatim** as given below. `CDSCacheHelper` has no dependency; `AutoLoanCDSUtil`
depends on it (a `static {}` initializer calls `CDSCacheHelper.loadCDSData()`), so deploy them together or
helper-first.

### `CDSCacheHelper`

Caches two static name→Id maps via `loadCDSData()`: `PARTICIPANT_ROLE_NAME_TO_ID` (active
`ParticipantRole`, keyed by `DeveloperName`) and `PARTICIPANT_GROUP_NAME_TO_ID` (`Group` where
`Type='Participant'`, keyed by `DeveloperName`). The guard returns early only when **both** maps are
already populated.

```apex
public class CDSCacheHelper {

    public static Map<String, String> PARTICIPANT_ROLE_NAME_TO_ID = new Map<String, String>();
    public static Map<String, String> PARTICIPANT_GROUP_NAME_TO_ID = new Map<String, String>();

    public static void loadCDSData() {

        if (!(PARTICIPANT_ROLE_NAME_TO_ID.isEmpty() || PARTICIPANT_GROUP_NAME_TO_ID.isEmpty())) {
            return;
        }

        // Caching participant roles
        List<Participantrole> paticipantRoles = [SELECT ID, DeveloperName FROM ParticipantRole WHERE IsActive = true];
        for (Participantrole role: paticipantRoles) {
            PARTICIPANT_ROLE_NAME_TO_ID.put(role.DeveloperName, role.ID);
        }

        // Caching participant groups
        List<Group> groups = [SELECT ID, DeveloperName FROM Group WHERE Type = 'Participant'];
        for (Group groupData: groups) {
            PARTICIPANT_GROUP_NAME_TO_ID.put(groupData.DeveloperName, groupData.ID);
        }

    }

}
```

### `AutoLoanCDSUtil`

`public with sharing`, exposes `@InvocableMethod(label='Digital Lending CDS')` `execute(List<ID> ids)`
where the first Id is an `ApplicationFormProduct`. On a stage change it (1) updates
`ApplicationFormProduct.ApplicantVisibleStatus` via the `AFPStage_To_ApplicantVisibleStatus` matrix, (2)
updates the parent `ApplicationForm.Stage` via `AFPStage_To_AFStage`, and (3) creates/updates participant
records on `AppFormProductParticipant`, `ApplicationFormParticipant`, and `PartyProfileParticipant` via
`HomeLoan_CDS_Config` (outputs `Applicant_Agent_Access` and `Underwriter_Access`, comma-separated
role lists). Roles are dispatched by `startsWith` — `ApplicationFormProduct` is checked **before**
`ApplicationForm` because the latter is a prefix of the former. It calls each matrix via
`Invocable.Action.createCustomAction('runDecisionMatrix', <matrixName>)`.

**The one documented customization point:** `CDS_PERMISSION_SET_NAME = 'FSCCDSUser'`. If the admin created
the CDS permission set with a different API name, replace `'FSCCDSUser'` on that line before deploy (and
keep it in lockstep with the `compliant-data-sharing` sibling). The matrix names, group names
(`Agent_Group` / `Underwriter_Group`), and field names are load-bearing contracts — do not otherwise
rewrite the class logic.

```apex
public with sharing class AutoLoanCDSUtil {

    private static final String DM_APP_FORM_PRODUCT_STAGE_FIELD_NAME = 'ApplicationFormProductStage';
    private static final String DM_APP_FORM_STAGE_FIELD_NAME = 'ApplicationFormStage';
    private static final String DM_APPLICANT_STATUS_FIELD_NAME = 'ApplicantVisibleStatus';

    private static final String DM_AFP_STAGE_TO_AF_STAGE = 'AFPStage_To_AFStage';
    private static final String DM_AFP_STAGE_TO_APPLICANT_STATUS = 'AFPStage_To_ApplicantVisibleStatus';

    private static final String DM_AUTO_LOAN_CDS = 'HomeLoan_CDS_Config';
    private static final String DM_UW_ACCESS_FIELD_NAME = 'Underwriter_Access';
    private static final String DM_APPLICANT_AGENT_ACCESS_FIELD_NAME = 'Applicant_Agent_Access';

    private static final String APPLICATION_FORM = 'ApplicationForm';
    private static final String APPLICATION_FORM_PRODUCT = 'ApplicationFormProduct';
    private static final String PARTY_PROFILE = 'PartyProfile';

    private static final String UNDERWRITER_PARTICIPANT_GROUP_NAME = 'Underwriter_Group';
    private static final String AGENT_PARTICIPANT_GROUP_NAME = 'Agent_Group';
    private static final String CDS_PERMISSION_SET_NAME = 'FSCCDSUser';

    static {
        CDSCacheHelper.loadCDSData();
    }

    @InvocableMethod(label = 'Digital Lending CDS'
        description = 'Creates the CDS records on ApplicationForm/ApplicationFormProduct/PartyProfile based on the configuration.')
    public static List <Result> execute(List <ID> ids) {
        List <Result> results = new List <Result> ();
        Result result = new Result();
        try {

            Id applicationFormProductId = ids.get(0);

            ApplicationFormProduct appFormProduct = [SELECT Id, Stage, ApplicantVisibleStatus, ApplicationFormId FROM ApplicationFormProduct WHERE Id =: applicationFormProductId];

            updateApplicantVisibleStatus(appFormProduct);
            updateApplicationFormStage(appFormProduct);

            Invocable.Action.Result cdsDmResult = invokeDecisionMatrix(DM_AUTO_LOAN_CDS, appFormProduct.Stage);
            String applicantAgentRole = getOutputVal(cdsDmResult, DM_APPLICANT_AGENT_ACCESS_FIELD_NAME);
            String underwriterRole = getOutputVal(cdsDmResult, DM_UW_ACCESS_FIELD_NAME);

            String[] applicantAgentRoles = applicantAgentRole.split(',');
            String[] underwriterRoles = underwriterRole.split(',');

            Set <Id> partyProfileIds = new Set < Id > ();

            List <Applicant> applicants = [SELECT Id, Email, ApplicationFormId, PartyProfileId FROM Applicant WHERE ApplicationFormId =: appFormProduct.ApplicationFormId];

            for (Applicant applicant: applicants) {
                if (applicant.PartyProfileId != null) {
                    partyProfileIds.add(applicant.PartyProfileId);
                }
                // If no users where email matches applicant email, continue
                List<User> users = [SELECT Id FROM USER WHERE Email =: applicant.Email];
                if (users.size() == 0) {
                    continue;
                }
                User user = users.get(0);

                // If user does not have CDS permission, continue
                List<PermissionSetAssignment> permissionSetAssignments = [SELECT AssigneeId, PermissionSet.Name FROM PermissionSetAssignment 
                                                                           WHERE AssigneeId =: user.Id AND PermissionSet.Name =: CDS_PERMISSION_SET_NAME ];
                if (permissionSetAssignments.size() == 0) {
                    continue;
                }

                for (String cdsRole: applicantAgentRoles) {
                    if (cdsRole.startsWith(APPLICATION_FORM_PRODUCT)) {
                        handleApplicationFormProductParticipants(user.Id, appFormProduct, cdsRole);
                    } else if (cdsRole.startsWith(APPLICATION_FORM)) {
                        handleApplicationFormParticipants(user.Id, appFormProduct, cdsRole);
                    } else if (cdsRole.startsWith(PARTY_PROFILE)) {
                        handlePartyProfileParticipants(user.Id, applicant.PartyProfileId, cdsRole);
                    }
                }
            }
            // Updating / Creating Participant Records for Underwrite groups 
            handleCDSUpdatesForGroups(UNDERWRITER_PARTICIPANT_GROUP_NAME, underwriterRoles, partyProfileIds, appFormProduct);

            // Updating / Creating Participant Records for Agent groups 
            handleCDSUpdatesForGroups(AGENT_PARTICIPANT_GROUP_NAME, applicantAgentRoles, partyProfileIds, appFormProduct);
            result.isSuccess = true;
            result.message = 'Stage configuration executed successfully.';

        } catch (Exception ex) {
            result.isSuccess = false;
            result.message = ex.getMessage();
            System.debug(ex);
        }

        results.add(result);
        return results;
    }

    public static void handleCDSUpdatesForGroups(String groupName, String[] roles, Set < Id > partyProfileIds, ApplicationFormProduct appFormProduct) {
        String groupId = CDSCacheHelper.PARTICIPANT_GROUP_NAME_TO_ID.get(groupName);
        for (String cdsRole: roles) {
            if (cdsRole.startsWith(APPLICATION_FORM_PRODUCT)) {
                handleApplicationFormProductParticipants(groupId, appFormProduct, cdsRole);
            } else if (cdsRole.startsWith(APPLICATION_FORM)) {
                handleApplicationFormParticipants(groupId, appFormProduct, cdsRole);
            } else if (cdsRole.startsWith(PARTY_PROFILE)) {
                for (Id partyProfileId: partyProfileIds) {
                    handlePartyProfileParticipants(groupId, partyProfileId, cdsRole);
                }
            }
        }
    }

    public static void updateApplicantVisibleStatus(ApplicationFormProduct appFormProduct) {
        Invocable.Action.Result result = invokeDecisionMatrix(DM_AFP_STAGE_TO_APPLICANT_STATUS, appFormProduct.Stage);
        String applicantVisibleStatus = getOutputVal(result, DM_APPLICANT_STATUS_FIELD_NAME);
        appFormProduct.ApplicantVisibleStatus = applicantVisibleStatus;
        upsert appFormProduct;
    }

    public static void updateApplicationFormStage(ApplicationFormProduct appFormProduct) {
        Invocable.Action.Result result = invokeDecisionMatrix(DM_AFP_STAGE_TO_AF_STAGE, appFormProduct.Stage);
        String applicationFormStage = getOutputVal(result, DM_APP_FORM_STAGE_FIELD_NAME);
        
        ApplicationForm applicationForm = new ApplicationForm();
        applicationForm.Id = appFormProduct.ApplicationFormId;
        applicationForm.Stage = applicationFormStage;
        upsert applicationForm;
    }

    public static void handleApplicationFormParticipants(Id userOrGroupId, ApplicationFormProduct appFormProduct, String roleName) {
        List<ApplicationFormParticipant> appFormParticipants = [SELECT Id, ParticipantRoleId FROM ApplicationFormParticipant WHERE ParticipantId =: userOrGroupId AND ApplicationFormId=:appFormProduct.ApplicationFormId];
        String roleId = CDSCacheHelper.PARTICIPANT_ROLE_NAME_TO_ID.get(roleName);
        if (appFormParticipants.size() == 0) {
            ApplicationFormParticipant participant = new ApplicationFormParticipant(ApplicationFormId = appFormProduct.ApplicationFormId,
                                                                                    IsActive = true,
                                                                                    ParticipantRoleId = roleId,
                                                                                    ParticipantId=userOrGroupId);
            insert participant;
        } else {
            ApplicationFormParticipant participant = appFormParticipants.get(0);
            participant.IsActive = true;
            participant.ParticipantRoleId = roleId;
            upsert participant;
        }
    }

    public static void handleApplicationFormProductParticipants(Id userOrGroupId, ApplicationFormProduct appFormProduct, String roleName) {
        List<AppFormProductParticipant> participants = [SELECT Id, ParticipantRoleId FROM AppFormProductParticipant WHERE ParticipantId =: userOrGroupId AND ApplicationFormProductId=:appFormProduct.Id];
        String roleId = CDSCacheHelper.PARTICIPANT_ROLE_NAME_TO_ID.get(roleName);
        if (participants.size() == 0) {
            AppFormProductParticipant participant = new AppFormProductParticipant(ApplicationFormProductId = appFormProduct.Id,
                                                                                  IsActive = true,
                                                                                  ParticipantRoleId = roleId,
                                                                                  ParticipantId=userOrGroupId);
            insert participant;
        } else {
            AppFormProductParticipant participant = participants.get(0);
            participant.IsActive = true;
            participant.ParticipantRoleId = roleId;
            upsert participant;
        }
    }

    public static void handlePartyProfileParticipants(Id userOrGroupId, String partyProfileId, String roleName) {
        List<PartyProfileParticipant> participants = [SELECT Id, ParticipantRoleId FROM PartyProfileParticipant WHERE ParticipantId =: userOrGroupId AND PartyProfileId=:partyProfileId];
        String roleId = CDSCacheHelper.PARTICIPANT_ROLE_NAME_TO_ID.get(roleName);
        if (participants.size() == 0) {
            PartyProfileParticipant participant = new PartyProfileParticipant(PartyProfileId = partyProfileId,
                                                                              IsActive = true,
                                                                              ParticipantRoleId = roleId,
                                                                              ParticipantId=userOrGroupId);
            insert participant;
        } else {
            PartyProfileParticipant participant = participants.get(0);
            participant.IsActive = true;
            participant.ParticipantRoleId = roleId;
            upsert participant;
        }
    }


    public static Invocable.Action.Result invokeDecisionMatrix(String decisionMatrixName, String appFormProductStageVal) {
        // Create an Invocable.Action
        Invocable.Action action = Invocable.Action.createCustomAction('runDecisionMatrix', decisionMatrixName);
        action.setInvocationParameter(DM_APP_FORM_PRODUCT_STAGE_FIELD_NAME, appFormProductStageVal);
        List < Invocable.Action.Result > results = action.invoke();
        return results.get(0);
    }

    public static String getOutputVal(Invocable.Action.Result result, String outputFieldName) {
        return (String) result.getOutputParameters().get(outputFieldName);
    }


    public class Result {
        @InvocableVariable(label = 'Message'
                           description = 'Resulted output of the action.'
                           required = true)
        public String message;
        
        @InvocableVariable(label = 'Status'
                           description = 'Resulted status of the action.'
                           required = true)
        public boolean isSuccess;
    }
}
```

## Deploy path — direct Tooling ApexClass create (dispatchable), with a production deploy fallback + checkpoint

Apex is not headlessly *authored* through a Setup Connect API. Create it through the **Tooling REST
sObjects route** — a plain-JSON HTTP path the hosted agent drives with no CLI, local project, or
multipart body:

1. Read whether each class already exists (`SELECT Id, Name, Status FROM ApexClass WHERE Name IN
   ('CDSCacheHelper','AutoLoanCDSUtil')`). Reuse an exact-match class; on a body mismatch, present the
   diff and ask before overwriting.
2. **Create via the Tooling REST sObjects route (primary, dispatchable, org-verified):** POST
   `/services/data/vXX.0/tooling/sobjects/ApexClass` ONCE PER CLASS with a JSON body
   `{"Name":"...","Body":"<full .cls source>","Status":"Active"}`. Create **CDSCacheHelper first**, then
   **AutoLoanCDSUtil**, so the util compiles against an already-present helper (its `static{}` initializer
   calls `CDSCacheHelper.loadCDSData()`). The response is synchronous `{id, success:true}`; on
   `success:false` read the compile error (there is no async job to poll). This works in sandbox / scratch
   / developer orgs; production orgs block direct Apex create by platform rule (use the deploy fallback
   below there).
3. Re-read both classes (`SELECT Id, Name, Status FROM ApexClass WHERE Name IN (...)`) and confirm
   `Status = Active` with no compile errors.
4. **PRECONDITION — Enhanced Personal Information Management:** `AutoLoanCDSUtil` reads `User.Email`. If
   `UserManagementSettings.enableEnhancedConcealPersonalInfo` is **enabled**, `User.Email` is concealed
   from the Apex compiler for the creating user and the class will **not** compile (`success:false`, a
   "No such column 'Email' on entity 'User'"-class error). This is an org/permission condition — not a
   code defect and not a transport problem (every write channel feeds the same org Apex compiler, so
   switching deploy method does not fix it). Resolve it before creating `AutoLoanCDSUtil` (grant "View All
   Users", or disable Enhanced conceal on a disposable test org); never rewrite the class to dodge it.
5. **Production / non-dispatchable deploy fallback:** where direct Tooling create is blocked (production),
   deploy the same two class bodies (helper-first, one request) through the Metadata API `deployRequest`
   zip flow. Note this is a **multipart** upload (a binary zip part), so it is NOT drivable by the JSON
   dispatch client — it needs a multipart-capable caller (or, on a local workstation only,
   `sf project deploy start --metadata-dir <dir>`; the hosted agent cannot shell to a CLI). Do NOT use the
   Tooling `MetadataContainer` → `ApexClassMember` → `ContainerAsyncRequest` overwrite flow for these
   classes — its `ApexClassMember` POST has been observed to **500 server-side (org-verified)**.
6. **Checkpoint fallback:** if no create/deploy path is reachable at all (missing author-apex permission
   and no deploy surface), stop, report the blocker, and hand off the two class bodies inlined above
   ("The two Apex classes"). Do not report the sibling complete without the classes present.

## The autolaunched Flow

Create the **`Digital Lending Stage Management`** autolaunched Flow (No Triggers):

- One **Action** element running Apex `apex-AutoLoanCDSUtil`, with "Set Input Values" on.
- A **Variable** resource: API name `RecordId`, data type **Text**, **Available for input** = true — the
  transition rule passes the `ApplicationFormProduct` record Id into it.
- Label and API name: `Digital Lending Stage Management`.
- Save and **activate** the Flow.

Create the Flow via the **Tooling REST sObjects route (primary, dispatchable, org-verified)**: POST
`/services/data/vXX.0/tooling/sobjects/Flow` with a JSON body
`{"FullName":"Digital_Lending_Stage_Management","Metadata":{...}}` — `processType` `AutoLaunchedFlow`, a
`start` element carrying both `locationX` and `locationY` (both required), the Action element above, the
`RecordId` Text input variable (`isInput:true`), and `status` `Active`. Create it **after** the Apex
classes (its Action references `apex-AutoLoanCDSUtil`). Then re-read `FlowDefinitionView` / `Flow` to
confirm the active version references the Apex action. Where direct Tooling Flow create is blocked
(production), deliver the same `Flow` component through the Metadata API `deployRequest` zip flow — a
**multipart** upload, so NOT drivable by the JSON dispatch client; it needs a multipart-capable caller (or,
local workstation only, the `sf` CLI). The stage-transition rules (the `stage-transitions` sibling) bind to
this Flow by its exact name, so it must be active before transitions are activated.

## Idempotency and rollback

- Reuse exact-match classes and an exact-match active Flow; do not create suffixed duplicates.
- On a body/definition mismatch, present the diff and stop.
- Rollback deletes only artifacts created by this run and only after confirming no transition rule
  depends on the Flow.

## Output contract

Return: each Apex class Id and Status (or the deploy blocker), and the Flow's API name, active version
number, and confirmation that its Action element calls `apex-AutoLoanCDSUtil` with the `RecordId` input.

## Definition of done

`CDSCacheHelper` and `AutoLoanCDSUtil` are deployed and Active (deploying the verbatim bodies inlined
above; or a deploy blocker is reported with those bodies handed off), and the
`Digital Lending Stage Management` autolaunched Flow is active with a `RecordId`
Text input variable and an Action element invoking `apex-AutoLoanCDSUtil`. A partial run is never reported
as complete.
