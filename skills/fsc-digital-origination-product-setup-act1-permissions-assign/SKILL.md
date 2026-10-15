---
name: fsc-digital-origination-product-setup-act1-permissions-assign
description: "Sub-skill of digital-origination-product-setup. Act 1 — assign the Product Catalog Management Designer permission set (and the two companion perm sets: Digital Lending, PCM Viewer) to users who configure Digital Lending. Check → report → confirm → THEN assign. Never auto-assign."
metadata:
  version: "1.0"
---

# Act 1 — Permissions

Source: [Assign Product Catalog Permissions for Digital Lending](https://help.salesforce.com/s/articleView?id=ind.fsc_lending_catalogs_products_assign_permission.htm&type=5)

## Purpose

Grant admins + users the permission sets required to configure Digital Lending products
and product catalogs.

## Perm sets required

See [`../../references/permission-sets.md`](../../references/permission-sets.md) for the
full matrix.

| Perm set | Unlocks |
|---|---|
| Digital Lending | Setting up Digital Lending |
| Product Catalog Management Designer | Setting up Product Catalog Management features + objects |
| Product Catalog Management Viewer | Viewing Product Catalog Management features + objects |

## Policy — check → report → confirm → THEN assign

1. **Check.** Query `PermissionSetAssignment` for the target user(s). List which of the three perm sets are already assigned vs missing.
2. **Report.** Present the missing list to the admin with what each perm set unlocks.
3. **Confirm.** Wait for explicit admin confirmation on which perm sets to assign, and to which users.
4. **Assign.** Insert `PermissionSetAssignment` records only for confirmed (perm-set, user) pairs.
5. **Verify.** Re-query `PermissionSetAssignment` to confirm the insert.

`DUPLICATE_VALUE` = already assigned = success, not error.

## Steps (help-doc verbatim, for Product Catalog Management Designer)

1. From Setup, in the Quick Find box, enter **Permission Sets**, and then click **Permission Sets**.
2. Click the **Product Catalog Management Designer** permission set.
3. Click **Manage Assignments**, and then click **Add Assignments**.
4. Select the checkbox for each user who needs the permission set, and then click **Assign**.

Repeat for **Digital Lending** and **Product Catalog Management Viewer**.

## Programmatic equivalent

For scripted setup, insert `PermissionSetAssignment` records via the Data API. First
resolve `PermissionSet.Id` by `Name` (org-verified 2026-07-29):

| UI label | API `Name` |
|---|---|
| Digital Lending | `DigitalLending` |
| Product Catalog Management Designer | `ProductCatalogManagementAdministrator` |
| Product Catalog Management Viewer | `ProductCatalogManagementViewer` |

```text
PermissionSetAssignment:
  AssigneeId: <User.Id>
  PermissionSetId: <PermissionSet.Id where Name = 'ProductCatalogManagementAdministrator'>
```

**Important.** UI label says "Product Catalog Management Designer" but the API `Name` is
`ProductCatalogManagementAdministrator`. Do NOT use `ProductCatalogManagementDesigner` —
returns 0 rows. Always confirm names against the target org (managed-package prefixes
vary):

```text
SELECT Id, Name, Label FROM PermissionSet
WHERE Label IN ('Digital Lending', 'Product Catalog Management Designer', 'Product Catalog Management Viewer')
```

## End state

- All three perm sets assigned to the admin doing the setup.
- All three perm sets assigned to any additional users the admin identified.
- `PermissionSetAssignment` re-query confirms.

## See also

- Salesforce Help: Set Up Product Catalog Management
- Article 9 (Create Omniscript Name Attribute) lists broader Digital Lending perm sets (Rule Engine Designer/Runtime, OmniStudio Admin/User, Compliant Data Sharing Manager, Document Checklist, PCM Designer/Viewer, Product Discovery Admin/User, Salesforce Pricing Admin/Design Time/Runtime). See [`../../references/permission-sets.md`](../../references/permission-sets.md).
