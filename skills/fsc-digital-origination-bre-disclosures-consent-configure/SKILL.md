---
name: fsc-digital-origination-bre-disclosures-consent-configure
parent: "digital-origination-bre-setup"
purpose: "Set up disclosure and consent for a lending product via a decision matrix, a data use purpose, and an authorization form."
description: "Set up Disclosures and Consent for Digital Lending: a Business Rules Engine decision matrix that matches a lending product and applicant type to the data use purpose that defines why consent and disclosure are collected, plus the supporting home loan product, Data Use Purpose record, and locale-scoped Authorization Form. Drives the shared decision-matrix-foundation sibling for the matrix, and handles the Data Use Purpose and Authorization Form objects through standard sObject REST with describe-first discovery. Never invents disclosure text, products, or applicant types."
metadata:
  version: "1.0"
---

# Digital Origination disclosure and consent

Automate which disclosure-and-consent applies to a lending application. A decision matrix matches the
lending product and applicant type to a **Data Use Purpose** record (the reason consent and disclosure
are collected); an **Authorization Form** holds the locale-scoped text the applicant sees. This sibling
owns the consent matrix and its supporting records. It does not create OmniScripts or document types.

Source: Salesforce Help "Disclosure and Consent for Digital Lending" and its use-case example. Concept:
*disclosure* is information the institution must share with a customer; *consent* is the permission the
customer grants the institution to act on their behalf.

## Required inputs

- Target-org alias and acting admin.
- The lending Product (create or reuse) and the applicant type (the example uses `Primary Applicant`).
- The Data Use Purpose definition — the business reason for collecting consent/disclosure.
- The disclosure-and-consent text and its locale (the example uses English).

Help-article values are examples, never customer defaults. A missing product, purpose, or text is a
user decision, not something to infer.

## Decision matrix contract

Drive nested `decision-matrix-foundation` to create and activate a decision matrix with:

| Column header (apiName) | columnType | dataType |
|---|---|---|
| `ProductId` | `Input` | `Text` |
| `ApplicantType` | `Input` | `Text` |
| `Level` | `Input` | `Text` |
| `DataUsePurpose` | `Output` | `Text` |

Use the exact `CalculationMatrixColumn` enum tokens (`Input`/`Output`, `Text`); do not submit English
labels. The `DataUsePurpose` output cell holds the activated Data Use Purpose Id.

## Supporting records (sObject REST, describe-first)

The Data Use Purpose and Authorization Form objects have no dedicated corpus SOR. Handle them through
standard sObject REST, describing each object first and binding only to field API names the describe
returns. Never guess a field name from a UI label. Org-verified objects on a Digital Lending org:
`DataUsePurpose` (`0ZW`, has `IsActive`), `AuthorizationForm` (`0cI`, has `DefaultAuthFormTextId`,
`EffectiveFromDate`/`EffectiveToDate`), `AuthorizationFormText` (`0cN`, has `Locale`/`LocaleSelection`
picklists — English is `en_US` — plus `IsActive` and `DetailAuthorizationFormText`), and the
`AuthorizationFormDataUse` junction (`0cM`, links `AuthorizationFormId` + `DataUsePurposeId`).

**Order matters — each step gates the next (org-verified):**

1. **Product.** Reuse an existing lending product or create one (`Product2`) with the admin-approved
   Name, Product Code, and Active = true. Capture its Id.
2. **Data Use Purpose.** Query for an existing record matching the approved purpose before creating
   one. Create it with the approved definition (do not activate it yet — activation fails until it is
   linked to an Authorization Form). Capture its Id.
3. **Authorization Form.** Create the `AuthorizationForm`.
4. **Authorization Form Text.** Create an `AuthorizationFormText` with `Locale`/`LocaleSelection` =
   `en_US`, `IsActive` = true, and the approved disclosure-and-consent text in
   `DetailAuthorizationFormText`.
5. **Set the form's default text.** Update the `AuthorizationForm.DefaultAuthFormTextId` to the text
   created in step 4. The next step fails ("Authorization Form doesn't have default text assigned") if
   this is skipped.
6. **Link form to purpose.** Create the `AuthorizationFormDataUse` junction referencing the form and the
   Data Use Purpose.
7. **Activate the Data Use Purpose** (`IsActive` = true) and confirm with a fresh read. This fails
   ("must be associated with an Authorization Form") if the junction in step 6 is missing.

If describe shows either object is not present in the target org, stop and report it as a blocker
(missing feature/package artifact) rather than deploying an ad-hoc custom object.

## Matrix row

After the supporting records exist and the Data Use Purpose is active, hand the row to
`decision-matrix-foundation`:

- `ProductId` = the created/reused Product Id
- `ApplicantType` = the approved applicant type (example: `Primary Applicant`)
- `Level` = the application-form product level (example: `ApplicationFormProduct`)
- `DataUsePurpose` = the activated Data Use Purpose Id

Then activate the matrix through `decision-matrix-foundation` and confirm Active on a fresh read.

## Idempotency and rollback

- Reuse an exact-match product, purpose, form, and matrix row rather than creating duplicates.
- Do not silently overwrite differing disclosure text or a differing purpose; present current vs
  requested and ask.
- Rollback removes only records created by this run, and only after confirming no active matrix row or
  application depends on them.

## Output contract

Return the Product Id, Data Use Purpose Id and active status, Authorization Form Id and locale, the
matrix Name/ID/version with its verified row, and the activation evidence.

## Definition of done

The consent decision matrix is Active with the linking row, the Data Use Purpose is active, and the
Authorization Form exists with the English locale and is linked to the purpose. Any missing object or
unresolved checkpoint is reported; a partial run is never reported as complete.
