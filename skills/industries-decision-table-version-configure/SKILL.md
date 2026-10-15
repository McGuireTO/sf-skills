---
name: industries-decision-table-version-configure
description: "Use this skill when users want to use this composite when a skill needs a CSV/versioned Decision Table cloned from a template with its initial version activated but NO rows loaded — e.g. Trigger when users mention decision, table, version, activate, tables, decision tables."
metadata:
  version: "1.0"
  accessCheck: "UserPermissions.BREDecisionTableAdmin"
---

# Managing Decision Table Version Activate

## When to Use This Skill

Use this composite when a skill needs a CSV/versioned Decision Table cloned from a template with its initial version activated but NO rows loaded — e.g. the Tariff Comparison feature-setup path that only asks "create the DTs from the templates". NOT for source-object (HBASE) DTs (use `decision-table-hbase-activate`) and NOT for cases where rows are required at setup time (use `decision-table-rows-load`).

## Critical Constraints

**Preconditions:**

- User must have BREDecisionTableAdmin permission (check: `UserPermissions.BREDecisionTableAdmin`)
- Org must have BusinessRulesEngine feature enabled

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `clone-template` | write | implemented | `POST /connect/business-rules/decision-table/templates/instantiate` | — |
| `activate-version` | write | implemented | `PATCH /connect/business-rules/decision-table/definitions/{decisionTableId}/versions/{versionNumber}` | `clone-template` |
| `refresh-cache` | write | implemented | `POST /connect/decision-table/refresh` | `activate-version` |

### Write operations

#### `clone-template`

Instantiate a new DecisionTable from the namespace-qualified template. Application Usage defaults to `Default`. Template instantiation automatically creates an initial ExpressionSetVersion (versionNumber 1) in `Draft` status with the template's column definitions but zero rows. Request-body field for the new DT's developer name is `decisionTableName` (NOT `apiName`) — POST fails JSON_PARSER_ERROR on `apiName`.

**Call:** `POST /connect/business-rules/decision-table/templates/instantiate`   — status: `implemented`

**Inputs:**

- `templateName` — templateName input to this composite
- `decisionTableName` — Wired from this composite's `apiName` input — the request-body key is `decisionTableName`.

**Rollback:** DELETE /connect/business-rules/decision-table/definitions/{decisionTableId} removes the DT and its version. Use with care.

#### `activate-version`

Activate the initial version (versionStatus = Active) with no row load. The DT is queryable and returns zero rows until a downstream flow loads them via `postDecisionTableRows`. Activation on an empty version is accepted — the endpoint does NOT require a minimum row count. Use the version-scoped URI (`.../versions/{versionNumber}`) — the collection URI (`.../versions`) rejects the update with MISSING_ARGUMENT because it expects a full definition body.

**Call:** `PATCH /connect/business-rules/decision-table/definitions/{decisionTableId}/versions/{versionNumber}`   — status: `implemented`

**Inputs:**

- `decisionTableId` — From clone-template output
- `versionNumber` — versionNumber input to this composite
- `versionStatus`

**Depends on:** `clone-template`

#### `refresh-cache`

Refresh the DT cache so the activated (empty) version is served by the runtime. `postDecisionTableRefresh` returns `Queued`; poll `DecisionTable.RefreshStatus` until it reads `Completed`.

**Call:** `POST /connect/decision-table/refresh`   — status: `implemented`

**Inputs:**

- `decisionTableId` — From clone-template output
- `versionNumber` — versionNumber input to this composite

**Depends on:** `activate-version`
