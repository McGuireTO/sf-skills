---
name: fsc-digital-origination-bre-setup-coordinate
description: "End-to-end orchestrator for the Digital Origination (Digital Lending) Business Rules Engine setups that run on decision matrices: Disclosures and Consent, Document Upload, and Straight-Through Processing (applicant eligibility). Routes an unqualified \"set up the lending BREs\" request through nested sub-skills for permissions, the shared decision-matrix create/activate mechanics, and each of the three feature builds. Use this skill for the whole ordered journey, and use a sibling directly for a narrowed request such as \"create the disclosures and consent decision matrix\" or \"set up the STP eligibility matrix\"."
metadata:
  version: "1.0"
---

# Digital Origination Business Rules Engine setup orchestrator

Orchestrate the three decision-matrix-based Business Rules Engine setups for **Digital Origination**,
whose underlying APIs and setup artifacts still use the **Digital Lending** name. This skill owns
sequencing and state transfer between the sub-skills. It does not duplicate the implementation
contracts maintained by its nested sub-skills.

All three features share the same building block: a Business Rules Engine **decision matrix** (an
admin-typed lookup of input columns to output columns), created and activated through the shared
`decision-matrix-foundation` sibling, then populated with feature-specific columns and rows. This is a
different Business Rules Engine surface from the source-object **decision tables** used by
`digital-origination-pricing-setup`; do not conflate the two.

## Mandatory prerequisites

Before routing to any sibling, verify:

1. Digital Origination Initial Setup is complete. If not, route to
   `fsc-mandalorians/digital-origination-initial-setup` and stop.
2. The target org alias and acting admin are explicit.
3. The relevant feature is understood: **Disclosures and Consent**, **Document Upload**, and
   **applicant-eligibility STP** are three independent Discovery Framework features. Set up only the
   ones the admin requests.
4. The admin has supplied or approved the concrete inputs — products, applicant types, credit-score
   cutoffs, document types, and consent/disclosure text. Help-article examples are never customer
   defaults.

## Ordered journey

```text
Initial Setup (existing sibling)
 |
1. BRE permissions
 |
2. Feature build(s), each: decision-matrix-foundation (create + activate) then the feature sibling
    - Disclosures and Consent
    - Document Upload
    - STP applicant eligibility
```

The three feature builds are independent — run whichever the admin asked for, in any order. Within a
feature build, always create and activate the matrix shell through `decision-matrix-foundation` before
the feature sibling loads columns/rows and supporting records. Run one sibling at a time. Do not
continue after a sibling reports a blocking prerequisite or a manual checkpoint that has not been
completed.

### Step 1 - BRE permissions

Delegate to nested skill `permissions` (emitted SOR
`fsc-mandalorians/digital-origination-bre-setup-permissions`) with hints such as:

- "assign the Digital Lending permission set"
- "assign Rule Engine Designer and Product Catalog Management Designer"
- "assign Product Catalog Management Viewer and OmniStudio User for runtime"
- "enable Context Service for decision-matrix evaluation"

Required handoff: target user IDs, resolved permission-set IDs/API names, and a fresh verification of
every required assignment.

### Step 2 - Decision-matrix foundation (per feature)

Delegate to nested skill `decision-matrix-foundation` (emitted SOR
`fsc-mandalorians/digital-origination-bre-setup-decision-matrix-foundation`) to create the named matrix (a
`CalculationMatrix` sObject), add its columns (which auto-creates version 1), add its rows, and activate
it. Pass the exact matrix name, the column contract, and the row values from the feature sibling.
Required handoff: `CalculationMatrix` id, `CalculationMatrixVersion` id, and a fresh read confirming the
version's active window (StartDateTime set, EndDateTime null).

### Step 3 - Disclosures and Consent

Delegate to nested skill `disclosures-consent` (emitted SOR
`fsc-mandalorians/digital-origination-bre-setup-disclosures-consent`) with hints such as:

- "set up disclosure and consent for a home loan product"
- "create the data use purpose and authorization form"

This sibling drives `decision-matrix-foundation` for a matrix keyed on Product Id / ApplicantType /
Level with a Data Use Purpose output, and creates the supporting Product, Data Use Purpose, and
Authorization Form records. Required handoff: matrix ID/version, Data Use Purpose ID, Authorization
Form ID, and the activated matrix row linking them.

### Step 4 - Document Upload

Delegate to nested skill `document-upload` (emitted SOR
`fsc-mandalorians/digital-origination-bre-setup-document-upload`) with hints such as:

- "set up the document upload decision matrix for lending"
- "create the lending document types"

This sibling drives `decision-matrix-foundation` for a matrix keyed on productId / applicantType /
level with a docTypeLabel output, and reuses the Document Type / Document Category entity SORs.
Required handoff: matrix ID/version, Document Type API name(s), and the activated matrix row.

### Step 5 - STP applicant eligibility

Delegate to nested skill `stp-eligibility` (emitted SOR
`fsc-mandalorians/digital-origination-bre-setup-stp-eligibility`) with hints such as:

- "set up the IsSTPApplication decision matrix"
- "automatically approve or reject a loan by credit score"

This sibling drives `decision-matrix-foundation` for the `IsSTPApplication` matrix (CreditScore input,
IsSTP output) and then **verifies and activates** the preconfigured `DigitalLendingDFIsSTPApplication`
OmniScript that references the matrix. Required handoff: matrix ID/version, the live BRE lookup result,
and the OmniScript verification/activation result.

**OmniScript dependency (blocker, not a build).** The `DigitalLendingDFIsSTPApplication` OmniScript
(type `DigitalLendingDF`, subType `IsSTPApplication`; variant `DigitalLendingDFIsSTPApplicationAAE`) is
delivered by a Discovery Framework template, not created here. If it is absent, the STP sibling reports
a blocker; obtain the Discovery Framework / Digital Lending sample-template deployment from its owner
before completing STP. If it is present but inactive (template deploys land it `IsActive=false`), the
sibling activates it. Disclosures and Document Upload do not depend on it.

## Narrowed requests

| User request | Route |
|---|---|
| Assign the BRE / lending permissions only | Nested `permissions` |
| Create or activate a lending decision matrix shell | Nested `decision-matrix-foundation` |
| Set up disclosure and consent | Nested `disclosures-consent` |
| Set up document upload / lending document types | Nested `document-upload` |
| Set up STP / applicant-eligibility approval | Nested `stp-eligibility` |

For a narrowed request, validate that its upstream artifacts (permissions, matrix shell) exist. Do not
silently run the entire journey when the user asks for one feature.

## Shared invariants

- Read before write; reuse a matching matrix, record, or permission-set by exact API name and verified
  shape rather than creating a duplicate.
- Never infer customer products, applicant types, credit-score cutoffs, document types, or disclosure
  text. Help-article values are examples only.
- Treat a bare activation 200 as in progress, not success. Require a fresh read of the
  `CalculationMatrixVersion` showing an active window (StartDateTime set, EndDateTime null) before
  advancing — and for a matrix that feeds runtime, additionally require a live BRE lookup
  (`POST /connect/business-rules/decision-matrices/{name}`) that returns an output. A matrix can read
  Active and still return "no output for the specified input" if `CalculationMatrix.Type` is null (the
  derived version `MatrixType` then breaks the lookup) or its row `Name` hashes are wrong; see
  `decision-matrix-foundation`.
- A guided Setup checkpoint is a valid partial outcome only when the relevant headless write is absent
  or unverified. State exactly what remains and resume after confirmation.
- Each sibling must produce fresh read-back evidence before this orchestrator advances.

## Definition of done

The requested feature build is complete only when:

1. The required permission-set assignments are verified for the acting user, and Context Service is
   enabled for matrix evaluation.
2. Each feature's decision matrix exists as a `CalculationMatrix`, carries the exact columns and rows
   for that feature, and its version reads active (StartDateTime set, EndDateTime null) on a fresh read.
3. Disclosures and Consent additionally has an active Data Use Purpose and an Authorization Form
   (English locale, with an active default Authorization Form Text and a Data Use junction) linked
   through the activated matrix row.
4. Document Upload additionally has the intended Document Type label(s) in the activated matrix row. If
   the `DocumentType` sObject is absent on the org, note it as a supporting-metadata gap (the matrix
   still builds — `docTypeLabel` is a free Text column).
5. STP additionally has the `IsSTPApplication` matrix returning a decision from a live BRE lookup, and
   the `DigitalLendingDFIsSTPApplication` OmniScript verified to reference the matrix and Active — or a
   blocker reported if that OmniScript is absent.
6. Every manual checkpoint or unresolved gap is explicitly reported. A partial run is never reported
   as complete.

## Individual sibling reference

| Sibling | Responsibility | Primary corpus reuse |
|---|---|---|
| `permissions` | Digital Lending / Rule Engine / PCM / OmniStudio permission sets and Context Service | `entity/authorization-experience/PermSets` + Context Service enable |
| `decision-matrix-foundation` | Create, populate, and activate a decision matrix shell | `CalculationMatrix` sObject insert (with `Type="Standard"`) + BRE Taurus decisionmatrix Connect columns API (`post-decision-matrix-columns`) + direct `CalculationMatrixRow` inserts (MD5-hash `Name`) + decision-matrix builder `activate-dmversion` |
| `disclosures-consent` | Consent matrix plus Data Use Purpose and Authorization Form records | `decision-matrix-foundation` + sObject REST (describe-first) |
| `document-upload` | Document-type matrix plus lending document types | `decision-matrix-foundation` + `entity/fsc-darksaber/DocumentType` + `entity/fsc-mandalorians/DocumentCategory` |
| `stp-eligibility` | IsSTPApplication matrix plus OmniScript verification | `decision-matrix-foundation` + OmniStudio read |

These are nested source skills. Project Codey compiles each to a parent-qualified sibling SOR and adds
formal `delegates_to` steps to this parent. Run the Path-B harness on this parent `SKILL.md`; the
family is merged, ingested, and served together.

<!-- skill-validate: ignore-start -->
<!-- codey:operations start -->
## Operations Reference

Operations this skill uses — routing and dependency reference.

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `delegate-digital-origination-bre-setup-permissions` | delegate | — | → `fsc-mandalorians/digital-origination-bre-setup-permissions` | — |
| `delegate-digital-origination-bre-setup-decision-matrix-foundation` | delegate | — | → `fsc-mandalorians/digital-origination-bre-setup-decision-matrix-foundation` | `delegate-digital-origination-bre-setup-permissions` |
| `delegate-digital-origination-bre-setup-disclosures-consent` | delegate | — | → `fsc-mandalorians/digital-origination-bre-setup-disclosures-consent` | `delegate-digital-origination-bre-setup-permissions` |
| `delegate-digital-origination-bre-setup-document-upload` | delegate | — | → `fsc-mandalorians/digital-origination-bre-setup-document-upload` | `delegate-digital-origination-bre-setup-permissions` |
| `delegate-digital-origination-bre-setup-stp-eligibility` | delegate | — | → `fsc-mandalorians/digital-origination-bre-setup-stp-eligibility` | `delegate-digital-origination-bre-setup-permissions` |
| `preflight-context-service-enabled` | verify | — | `/connect/context-definitions` | `delegate-digital-origination-bre-setup-permissions` |
| `preflight-stp-omniscript-present` | verify | — | — | `delegate-digital-origination-bre-setup-permissions` |
| `permissions-confirm-org-and-target-user` | read | — | `GET /services/data/v63.0/query` | — |
| `permissions-resolve-permission-sets-by-name` | read | — | `GET /services/data/v63.0/query` | `permissions-confirm-org-and-target-user` |
| `permissions-assign-required-license` | write | — | `POST /services/data/v63.0/sobjects/PermissionSetLicenseAssign` | `permissions-resolve-permission-sets-by-name` |
| `permissions-assign-permission-sets` | write | — | `POST /services/data/v63.0/sobjects/PermissionSetAssignment` | `permissions-assign-required-license` |
| `permissions-enable-context-service` | write | — | `PUT /services/data/v63.0/connect/contextservice/access/contextServiceEnabled/{orgId}` | `permissions-assign-permission-sets` |
| `permissions-verify-context-service-live` | verify | — | `GET /services/data/v63.0/connect/context-definitions` | `permissions-enable-context-service` |
| `permissions-verify-assignments` | verify | — | `GET /services/data/v63.0/query` | `permissions-verify-context-service-live` |
| `decision-matrix-foundation-verify-context-service-gate` | verify | — | `GET /services/data/v63.0/connect/context-definitions` | — |
| `decision-matrix-foundation-resolve-existing-calculation-matrix` | read | — | `GET /services/data/v63.0/query` | `decision-matrix-foundation-verify-context-service-gate` |
| `decision-matrix-foundation-create-calculation-matrix` | write | — | `POST /services/data/v63.0/sobjects/CalculationMatrix` | `decision-matrix-foundation-resolve-existing-calculation-matrix` |
| `decision-matrix-foundation-set-matrix-type-standard` | write | — | `PATCH /services/data/v63.0/sobjects/CalculationMatrix/{matrixId}` | `decision-matrix-foundation-create-calculation-matrix` |
| `decision-matrix-foundation-add-decision-matrix-columns` | write | — | `POST /services/data/v63.0/connect/omnistudio/decision-matrices/{matrixId}/columns` | `decision-matrix-foundation-set-matrix-type-standard` |
| `decision-matrix-foundation-resolve-auto-created-version` | verify | — | `GET /services/data/v63.0/query` | `decision-matrix-foundation-add-decision-matrix-columns` |
| `decision-matrix-foundation-verify-decision-matrix-columns` | verify | — | `GET /services/data/v63.0/connect/omnistudio/decision-matrices/{matrixId}/columns` | `decision-matrix-foundation-resolve-auto-created-version` |
| `decision-matrix-foundation-insert-calculation-matrix-rows` | write | — | `POST /services/data/v63.0/sobjects/CalculationMatrixRow` | `decision-matrix-foundation-verify-decision-matrix-columns` |
| `decision-matrix-foundation-verify-calculation-matrix-rows` | verify | — | `GET /services/data/v63.0/connect/omnistudio/decision-matrices/{matrixId}/versions/{versionId}/rows` | `decision-matrix-foundation-insert-calculation-matrix-rows` |
| `decision-matrix-foundation-activate-matrix-version` | write | — | `PATCH /headless/invoke/industries/industries-interaction-decisionmatrix/activate-dmversion` | `decision-matrix-foundation-verify-calculation-matrix-rows` |
| `decision-matrix-foundation-verify-active-window` | verify | — | `GET /services/data/v63.0/query` | `decision-matrix-foundation-activate-matrix-version` |
| `decision-matrix-foundation-verify-live-bre-lookup` | verify | — | `POST /services/data/v63.0/connect/business-rules/decision-matrices/{matrixName}` | `decision-matrix-foundation-verify-active-window` |
| `decision-matrix-foundation-edit-rows-on-enabled-version` | write | — | `PATCH /services/data/v63.0/sobjects/CalculationMatrixVersion/{versionId}` | `decision-matrix-foundation-verify-live-bre-lookup` |
| `disclosures-consent-resolve-or-create-lending-product` | write | — | `GET /services/data/v63.0/query` | — |
| `disclosures-consent-resolve-or-create-data-use-purpose` | write | — | `GET /services/data/v63.0/query` | `disclosures-consent-resolve-or-create-lending-product` |
| `disclosures-consent-create-authorization-form` | write | — | `POST /services/data/v63.0/sobjects/AuthorizationForm` | `disclosures-consent-resolve-or-create-data-use-purpose` |
| `disclosures-consent-create-authorization-form-text` | write | — | `POST /services/data/v63.0/sobjects/AuthorizationFormText` | `disclosures-consent-create-authorization-form` |
| `disclosures-consent-set-default-auth-form-text` | write | — | `PATCH /services/data/v63.0/sobjects/AuthorizationForm/{authorizationFormId}` | `disclosures-consent-create-authorization-form-text` |
| `disclosures-consent-link-authorization-form-data-use` | write | — | `POST /services/data/v63.0/sobjects/AuthorizationFormDataUse` | `disclosures-consent-set-default-auth-form-text` |
| `disclosures-consent-activate-data-use-purpose` | write | — | `PATCH /services/data/v63.0/sobjects/DataUsePurpose/{dataUsePurposeId}` | `disclosures-consent-link-authorization-form-data-use` |
| `disclosures-consent-resolve-or-create-consent-matrix` | write | — | `POST /services/data/v63.0/sobjects/CalculationMatrix` | `disclosures-consent-activate-data-use-purpose` |
| `disclosures-consent-add-consent-matrix-columns` | write | — | `POST /services/data/v63.0/connect/omnistudio/decision-matrices/{matrixId}/columns` | `disclosures-consent-resolve-or-create-consent-matrix` |
| `disclosures-consent-insert-consent-matrix-row` | write | — | `POST /services/data/v63.0/sobjects/CalculationMatrixRow` | `disclosures-consent-add-consent-matrix-columns` |
| `disclosures-consent-activate-consent-matrix-version` | write | — | `PATCH /headless/invoke/industries/industries-interaction-decisionmatrix/activate-dmversion` | `disclosures-consent-insert-consent-matrix-row` |
| `disclosures-consent-verify-consent-matrix-live` | verify | — | `POST /services/data/v63.0/connect/business-rules/decision-matrices/{matrixName}` | `disclosures-consent-activate-consent-matrix-version` |
| `document-upload-resolve-or-create-lending-product` | write | — | `GET /services/data/v63.0/query` | — |
| `document-upload-resolve-or-create-document-type` | write | — | `GET /services/data/v63.0/query` | `document-upload-resolve-or-create-lending-product` |
| `document-upload-resolve-or-create-document-category-and-junction` | write | — | `POST /services/data/v63.0/sobjects/DocumentCategoryDocumentType` | `document-upload-resolve-or-create-document-type` |
| `document-upload-resolve-or-create-document-upload-matrix` | write | — | `POST /services/data/v63.0/sobjects/CalculationMatrix` | `document-upload-resolve-or-create-document-category-and-junction` |
| `document-upload-add-document-upload-matrix-columns` | write | — | `POST /services/data/v63.0/connect/omnistudio/decision-matrices/{matrixId}/columns` | `document-upload-resolve-or-create-document-upload-matrix` |
| `document-upload-insert-document-upload-matrix-rows` | write | — | `POST /services/data/v63.0/sobjects/CalculationMatrixRow` | `document-upload-add-document-upload-matrix-columns` |
| `document-upload-activate-document-upload-matrix-version` | write | — | `PATCH /headless/invoke/industries/industries-interaction-decisionmatrix/activate-dmversion` | `document-upload-insert-document-upload-matrix-rows` |
| `document-upload-verify-document-upload-matrix-live` | verify | — | `POST /services/data/v63.0/connect/business-rules/decision-matrices/{matrixName}` | `document-upload-activate-document-upload-matrix-version` |
| `stp-eligibility-resolve-or-create-stp-matrix` | write | — | `POST /services/data/v63.0/sobjects/CalculationMatrix` | — |
| `stp-eligibility-add-stp-matrix-columns` | write | — | `POST /services/data/v63.0/connect/omnistudio/decision-matrices/{matrixId}/columns` | `stp-eligibility-resolve-or-create-stp-matrix` |
| `stp-eligibility-insert-stp-matrix-rows` | write | — | `POST /services/data/v63.0/sobjects/CalculationMatrixRow` | `stp-eligibility-add-stp-matrix-columns` |
| `stp-eligibility-activate-stp-matrix-version` | write | — | `PATCH /headless/invoke/industries/industries-interaction-decisionmatrix/activate-dmversion` | `stp-eligibility-insert-stp-matrix-rows` |
| `stp-eligibility-verify-stp-matrix-live` | verify | — | `POST /services/data/v63.0/connect/business-rules/decision-matrices/IsSTPApplication` | `stp-eligibility-activate-stp-matrix-version` |
| `stp-eligibility-resolve-stp-omniscript` | read | — | `GET /services/data/v63.0/query` | `stp-eligibility-verify-stp-matrix-live` |
| `stp-eligibility-verify-omniscript-references-matrix` | verify | — | `GET /services/data/v63.0/query` | `stp-eligibility-resolve-stp-omniscript` |
| `stp-eligibility-activate-omniscript-if-inactive` | write | — | `PATCH /services/data/v63.0/sobjects/OmniProcess/{omniProcessId}` | `stp-eligibility-verify-omniscript-references-matrix` |
| `stp-eligibility-verify-omniscript-active` | verify | — | `GET /services/data/v63.0/query` | `stp-eligibility-activate-omniscript-if-inactive` |
<!-- codey:operations end -->
<!-- skill-validate: ignore-end -->
