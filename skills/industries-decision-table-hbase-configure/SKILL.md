---
name: industries-decision-table-hbase-configure
description: "Use this skill when users want to use this composite when a CME/Industries skill needs to activate a source-object Decision Table headlessly (e.g. Trigger when users mention decision, table, hbase, activate, tables, decision tables."
metadata:
  version: "1.0"
  accessCheck: "UserPermissions.BREDecisionTableAdmin"
---

# Managing Decision Table Hbase Activate

## When to Use This Skill

Use this composite when a CME/Industries skill needs to activate a source-object Decision Table headlessly (e.g. AttributeDetailsConfigDT, AttributePicklistConfigDT). NOT for CSV/versioned DTs — use `decision-table-rows-load` instead.

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
| `get-current-definition` | read | implemented | `GET /connect/business-rules/decision-table/definitions/{decisionTableId}` | `clone-template` |
| `activate-definition` | write | implemented | `PATCH /connect/business-rules/decision-table/definitions/{decisionTableId}` | `get-current-definition` |
| `refresh-cache` | write | implemented | `POST /connect/decision-table/refresh` | `activate-definition` |

### Read operations

#### `get-current-definition`

Read the full DT definition to preserve every required field for the subsequent full-body PATCH. Partial PATCH fails with "Required field is missing: fullName / sourceObject".

**Call:** `GET /connect/business-rules/decision-table/definitions/{decisionTableId}`   — status: `implemented`

**Inputs:**

- `decisionTableId` — From clone-template output

**Depends on:** `clone-template`

### Write operations

#### `clone-template`

Instantiate the HBASE DecisionTable from the template. The template's auto-populate query pulls rows directly from the source SObject — no admin row input required. Request-body field for the new DT's developer name is `decisionTableName` (NOT `apiName`) — POST fails JSON_PARSER_ERROR on `apiName`. Same wire-body key as the CSV versioned instantiate call.

**Call:** `POST /connect/business-rules/decision-table/templates/instantiate`   — status: `implemented`

**Inputs:**

- `templateName` — templateName input to this composite
- `decisionTableName` — Wired from this composite's `apiName` input — the request-body key is `decisionTableName`.

#### `activate-definition`

Mutate the returned definition map — set `status = "Active"` — and PATCH the whole map back. Body MUST include ALL of setupName, fullName, sourceObject, sourceType, type, usageType, executionType, conditionCriteria, conditionType, decisionResultPolicy, collectOperator, rowLevelOverrideType, doesConsiderNullValue, isIncrementalSyncEnabled, status, description.

**Call:** `PATCH /connect/business-rules/decision-table/definitions/{decisionTableId}`   — status: `implemented`

**Inputs:**

- `decisionTableId` — From clone-template output
- `body` — get-current-definition.definition with status overridden to "Active". Do NOT partial-PATCH.

**Depends on:** `get-current-definition`

**Rollback:** DELETE /connect/business-rules/decision-table/definitions/{decisionTableId} removes the DT. Use with care.

#### `refresh-cache`

Refresh the DT cache. `postDecisionTableRefresh` returns `Queued`; poll `DecisionTable.RefreshStatus` until it reads `Completed`. HBASE DTs return `versions: []` in the refresh response — this is the EXPECTED Completed shape (versions endpoint doesn't apply). Do NOT assert `versions[*].refreshStatus == Completed`.

**Call:** `POST /connect/decision-table/refresh`   — status: `implemented`

**Inputs:**

- `decisionTableId` — From clone-template output

**Depends on:** `activate-definition`
