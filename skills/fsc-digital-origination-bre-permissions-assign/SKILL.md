---
name: fsc-digital-origination-bre-permissions-assign
parent: "digital-origination-bre-setup"
purpose: "Assign and verify the permission sets and Context Service access needed to build and run the lending decision-matrix BREs."
description: "Assign and verify the permission-set access required to configure and run the Digital Lending decision-matrix Business Rules Engine setups (Disclosures and Consent, Document Upload, and STP applicant eligibility), and enable Context Service so decision-matrix evaluation works. Handles the Digital Lending, Rule Engine Designer, Product Catalog Management Designer/Viewer, and OmniStudio Admin/User access documented by the help articles. Reuses the approved PermSets SOR and standard assignment APIs, is idempotent on rerun, and never assigns access to inferred users or service accounts."
metadata:
  version: "1.0"
---

# Digital Origination BRE permissions

Prepare a specifically identified admin or runtime user for the lending decision-matrix Business Rules
Engine setups, and enable Context Service so the matrices can be evaluated. This sibling manages access
and one org-level enablement; it does not create matrices, records, or OmniScripts.

## Inputs

- Explicit target-org alias
- Explicit target user ID or username
- Role: design-time admin, runtime user, or both

Never select all active users. Never target Automated Process, integration, guest, or service users.

## Required access matrix

The three help articles state the same permission surface. Resolve exact API names from the target org;
labels can differ by release.

| Role | Required product-supplied access |
|---|---|
| Set up Digital Lending | Digital Lending permission set |
| Configure the Business Rules Engine (design time) | Rule Engine Designer AND Product Catalog Management Designer AND OmniStudio Admin |
| Run the Business Rules Engine (runtime) | Product Catalog Management Viewer AND OmniStudio User |

Do not manufacture a custom replacement for a missing product-supplied set. Report a missing
entitlement or package artifact as a blocker.

## Reusable operations

Use the **Permission Sets** entity SOR (find it with `discover`, then `describe` it for these operations):

- `get-permission-set-details` - Tooling read of a permission set and its `Permissions*` fields.
- `assign-users` - create `PermissionSetAssignment` using AssigneeId and PermissionSetId.
- `unassign-users` - rollback an assignment created by this run.
- `edit-assignment-expiration` - update an explicitly requested expiration.

For any permission-set-license required by the selected sets, query and create `PermissionSetLicenseAssign`
through standard sObject REST. Assign a missing license before its permission set.

## Context Service enablement

Decision-matrix evaluation runs behind the Context Service feature family (`ContextResourceFamily`,
org gate `IndustriesContext.orgHasIndustriesContextService`). When the gate is off, the matrix
evaluation and OmniScript decision-matrix action element return HTTP 403 `FUNCTIONALITY_NOT_ENABLED`.

Enable it headlessly via the Context Service Connect API — the `preferenceName` must be exactly
`contextServiceEnabled` (not `ContextService`), and `uniqueIdentifier` is the 18-char Org Id:

```text
PUT /connect/contextservice/access/contextServiceEnabled/{orgId}  {"isEnabled":true}
```

If the family-level gate itself is not yet on, the PUT cannot reach the resource; in that case stop at
the Setup checkpoint **Context Service Settings → enable Context Definitions**
(`/lightning/setup/ContextServiceSettings/home`) and resume after the admin confirms. Verify a gate by
calling its cheapest live endpoint (e.g. a decision-matrix read) rather than trusting the preference
read-back, which can lag.

Enabling an org preference is an org-wide change: report it explicitly and enable only after confirming
the target org is the intended one.

## Workflow

1. Confirm org and target user. Query `User` and report username, profile, active state, and user type.
2. Resolve each required set by its unique API `Name` first — the `Name` column is unique per org, the
   `Label` is not. Query `PermissionSet` by `Name`, and fall back to `Label` only when the API name is
   unknown. Capture Id, `Name`, `Label`, LicenseId, `NamespacePrefix`, and `IsOwnedByProfile`.
3. If a `Label` query returns more than one candidate — common for the OmniStudio sets whose display
   labels (`OmniStudio User`, `OmniStudio Admin`) collide with profile-owned or duplicate sets —
   disambiguate deterministically **before** halting: keep only the product-supplied set
   (`IsOwnedByProfile = false` with a non-null managed `NamespacePrefix`) and de-duplicate on `Name`.
   Stop and ask **only** when two genuinely distinct product-supplied sets still survive that narrowing;
   a profile-owned or namespace-duplicate label collision is NOT a reason to halt. Never guess between
   two real product-supplied sets.
4. Query any required `PermissionSetLicense` and existing `PermissionSetLicenseAssign`. Assign a
   missing license before its permission set.
5. Query existing `PermissionSetAssignment` records for the target user and candidate set IDs.
6. Create only missing assignments. Treat `DUPLICATE_VALUE` as already assigned, then re-query.
7. Re-read the assigned permission sets and assignments and verify each is attached to the intended
   user.
8. Confirm Context Service is enabled; if not, enable it as above and re-verify with a live endpoint.

## Failure and rollback rules

- Missing permission set or license: report the exact missing API/label and stop dependent BRE steps.
- License-limit failure: do not remove another user's license; report the limit.
- Assignment failure: preserve successful pre-existing assignments; remove only assignments created by
  this run and only when the user requests rollback.
- Never edit a standard managed permission set.

## Output contract

Return a table with target user, role, permission-set API name/ID, license ID if applicable, prior
state, action, verified final state, and the Context Service enablement result. Separate blockers from
optional runtime-user access.

## Definition of done

Every required design-time or runtime assignment for the explicitly selected role is present and
verified in fresh queries, and Context Service reads enabled (or a Setup checkpoint is reported). No
unrelated user or assignment was changed.
