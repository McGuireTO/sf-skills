---
name: experience-apex-components-configure
description: "Use this skill when users want to manage ApexComponent records (Visualforce custom components) via the Tooling sObject API. Trigger when users mention apex, components, apex components."
metadata:
  version: "1.0"
---

# Managing Apex Components

## When to Use This Skill

Manage ApexComponent records (Visualforce custom components) via the Tooling sObject API. Steps cover SOQL list, GET-by-Id, and POST-create against /services/data/v66.0/tooling/sobjects/ApexComponent. Body fields (Name, MasterLabel, ApiVersion, NamespacePrefix, Markup, ControllerType, ControllerKey, Description, IsExplicitImport) match the ApexComponent UDD entity; field set varies by org (managed-package fields), so call /tooling/sobjects/ApexComponent/describe before constructing create payloads. Read requires View Setup + canViewApexPagesSetup; write requires CustomizeApplication. Org must have orgHasApexPagesApi enabled (Visualforce feature gate). No Connect/Metadata/Aura alternative — Metadata API ApexComponent is deploy/retrieve XML, wrong granularity for runtime CRUD.

## Critical Constraints

**Destructive operations — require explicit user confirmation:**

- **`delete_ApexComponent_1`** — Delete a ApexComponent record by Id via the Tooling/sObject API. The {id} path parameter is the record Id.
  - Rollback: No automatic rollback.

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `list_ApexComponent_1` | read | — | `query.ApexComponent` | — |
| `get_ApexComponent_1` | read | — | `sobjects/ApexComponent/{id}` | — |
| `create_ApexComponent_1` | write | — | `sobjects/ApexComponent` | — |
| `update_ApexComponent_1` | write | — | `sobjects/ApexComponent/{id}` | — |
| `delete_ApexComponent_1` | delete | — | `sobjects/ApexComponent/{id}` | — |

### Read operations

#### `list_ApexComponent_1`

SOQL list of ApexComponent records via Tooling API (GET /services/data/v66.0/tooling/query?q=...). The {q} input is the agent-supplied SOQL string — typically `SELECT Id, Name, MasterLabel, ApiVersion FROM ApexComponent`. View Setup + canViewApexPagesSetup gated.

**Call:** `query.ApexComponent`

#### `get_ApexComponent_1`

Fetch a single ApexComponent record by Id via Tooling sObject GET (/services/data/v66.0/tooling/sobjects/ApexComponent/{id}). Returns the full record including Markup. View Setup + canViewApexPagesSetup gated. Common pairing: list_ApexComponent_1 to find the Id, then this step to retrieve the body.

**Call:** `sobjects/ApexComponent/{id}`

### Write operations

#### `create_ApexComponent_1`

Create a new ApexComponent record via Tooling sObject POST (/services/data/v66.0/tooling/sobjects/ApexComponent). Body must include Name (DeveloperName) + MasterLabel + ApiVersion + Markup; optional Description, ControllerType, ControllerKey, IsExplicitImport, NamespacePrefix. CustomizeApplication gated. Returns the new Id; verify by GET on the returned Id.

**Call:** `sobjects/ApexComponent`

#### `update_ApexComponent_1`

Update a ApexComponent record by Id via the Tooling/sObject API. The {id} path parameter is the record Id; body fields replace existing values.

**Call:** `sobjects/ApexComponent/{id}`

### Destructive operations

#### `delete_ApexComponent_1`

Delete a ApexComponent record by Id via the Tooling/sObject API. The {id} path parameter is the record Id.

**Call:** `sobjects/ApexComponent/{id}`
