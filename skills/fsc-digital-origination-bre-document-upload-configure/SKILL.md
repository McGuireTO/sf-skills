---
name: fsc-digital-origination-bre-document-upload-configure
parent: "digital-origination-bre-setup"
purpose: "Set up the document-upload decision matrix that maps a lending product and applicant type to the document types an applicant must upload."
description: "Set up Document Upload for Digital Lending: a Business Rules Engine decision matrix that determines which document types an applicant must upload based on the lending product, applicant type, and level, returning a document type label. Drives the shared decision-matrix-foundation sibling for the matrix, and reuses the approved Document Type and Document Category entity SORs for the supporting metadata. Resolves and reuses existing document types by API name, and never invents products, applicant types, or document types."
metadata:
  version: "1.0"
---

# Digital Origination document upload

Determine which document types an applicant must upload for a lending application. A decision matrix
matches the lending product, applicant type, and level to a document type label. This sibling owns the
document-upload matrix and its supporting document-type metadata. It does not create consent records or
OmniScripts.

Source: Salesforce Help "Create a Decision Matrix for Digital Lending" (document upload). The example
matches a home loan product and applicant type to the document types required for the application.

## Required inputs

- Target-org alias and acting admin.
- The lending Product (create or reuse).
- The applicant type (the example uses `Primary Applicant`) and level (example: `ApplicationFormProduct`).
- The Document Type(s) an applicant must upload, with their exact API names.

Help-article values are examples, never customer defaults.

## Decision matrix contract

Drive nested `decision-matrix-foundation` to create and activate a decision matrix (the example names it
`LendingDocumentTypes`) with:

| Column header (apiName) | columnType | dataType |
|---|---|---|
| `productId` | `Input` | `Text` |
| `applicantType` | `Input` | `Text` |
| `level` | `Input` | `Text` |
| `docTypeLabel` | `Output` | `Text` |

Use the exact `CalculationMatrixColumn` enum tokens (`Input`/`Output`, `Text`); do not submit English
labels.

## Supporting metadata (reuse Document Type / Document Category entity SORs)

Reuse the approved entity SORs rather than deploying custom objects (find each with `discover`, then
`describe` it for its operations):

- The **Document Type** entity SOR — `describe`, `list`, `get-by-id`, `create`, `update`.
- The **Document Category** entity SOR — same operations, for the category the type belongs to.
- The **Document Category Document Type** entity SOR — the junction linking a category to a type, when
  the org models that relationship.

1. **Product.** Reuse or create the lending `Product2` (Name, Product Code, Family/Type, Active) and
   capture its Id.
2. **Document Type.** Query `DocumentType` (`list` / by name) for an existing type matching the required
   document. If present, capture its **API name** and reuse it. If absent, `create` it with the approved
   values, and create/link its `DocumentCategory` and `DocumentCategoryDocumentType` where the org
   requires the category relationship. Save each Document Type's API name for the matrix row.

Do not invent a document type from a UI label; resolve the API name from the create/describe response.

**If the `DocumentType` sObject is not present on the org** (org-observed: not all Digital Lending orgs
have it), the matrix still builds — `docTypeLabel` is a free `Text` output column, so populate it with
the intended label string and report the missing `DocumentType` object as a supporting-metadata gap
rather than deploying a custom object.

## Matrix row

Hand the row to `decision-matrix-foundation` after the product and document type(s) exist:

- `productId` = the created/reused Product Id
- `applicantType` = the approved applicant type (example: `Primary Applicant`)
- `level` = the level (example: `ApplicationFormProduct`)
- `docTypeLabel` = the Document Type API name saved above

Add one row per required product / applicant-type / document-type combination. Then activate the matrix
through `decision-matrix-foundation` and confirm Active on a fresh read.

## Idempotency and rollback

- Reuse an exact-match product, document type, and matrix row rather than creating duplicates.
- Do not silently overwrite a differing document type; present current vs requested and ask.
- Rollback removes only records created by this run, and only after confirming no active matrix row
  depends on them. Never auto-delete a shared Document Type or Category.

## Output contract

Return the Product Id, the Document Type API name(s) and IDs (with any Category / junction IDs), and the
matrix Name/ID/version with its verified row(s) and activation evidence.

## Definition of done

The document-upload decision matrix is Active with the intended row(s), and every referenced Document
Type exists and is linked through the row. Any missing metadata or unresolved checkpoint is reported; a
partial run is never reported as complete.
