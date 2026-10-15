---
name: data360-multi-org-mcp-configure
description: "Use this skill when users want to execute Data Cloud MultiOrg operations via the Data 360 MCP facade. Trigger when users mention data360/multi, org, shared, cdp, mcp, connect, api, shared-cdp-mcp-connect-api."
metadata:
  version: "1.0"
---

# Managing Data360/multi Org

## When to Use This Skill

Execute Data Cloud MultiOrg operations via the Data 360 MCP facade.

## Workflow

Each step lists an `operation` id. Call describe(<operation>) BEFORE dispatching to get that tool's parameter schema and, where available, a worked example. `paramsJson` decodes to the operation's requestBody schema VERBATIM, including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap or omit it. The only envelope the step handles for you is `{toolName, paramsJson}` (its `invocation` already wraps it); do not POST the operation path directly. If the tool's error suggests `payload_examples`, ignore it — that tool isn't available here; call describe(<operation>) instead.

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `multiorg-connection-disconnect` | write | implemented | `execute_multiorg-connection-disconnect` | — |
| `multiorg-connection-get` | read | implemented | `execute_multiorg-connection-get` | — |
| `multiorg-connection-list` | read | implemented | `execute_multiorg-connection-list` | — |
| `multiorg-scope-dependencies` | read | implemented | `execute_multiorg-scope-dependencies` | — |
| `multiorg-scope-get` | read | implemented | `execute_multiorg-scope-get` | — |
| `multiorg-scope-list` | read | implemented | `execute_multiorg-scope-list` | — |
| `multiorg-scope-share` | write | implemented | `execute_multiorg-scope-share` | — |
| `multiorg-scope-unshare` | write | implemented | `execute_multiorg-scope-unshare` | — |

### Read operations

#### `multiorg-connection-get`

Get detailed status of a specific multi-org connection by ID. Returns connection metadata, sync status, pending changesets, and metadata sync errors. Use includeScopes=true to see all assigned scopes and their states.

**Call:** `execute_multiorg-connection-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_multiorg_connection_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_multiorg-connection-get) for the param schema and, where available, a worked example.

#### `multiorg-connection-list`

List all multi-org connections for the current org. Returns connection status, org info, and optionally scope details. Use filters to narrow by orgType (HOME/LOB), developerName, or scopeFeatureType (Dc1/Tua/Moma). Set includeScopes=true to embed scope arrays.

**Call:** `execute_multiorg-connection-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_multiorg_connection_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_multiorg-connection-list) for the param schema and, where available, a worked example.

#### `multiorg-scope-dependencies`

Get cross-org references (dependencies) for a scope before unsharing. Returns records grouped by entity type (segments, activations, etc.) that reference this scope from other orgs. Use pagination (pageSize/pageOffset) for large result sets. MUST check before unshare - dependencies block unshare operations.

**Call:** `execute_multiorg-scope-dependencies`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_multiorg_scope_dependencies (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_multiorg-scope-dependencies) for the param schema and, where available, a worked example.

#### `multiorg-scope-get`

Get detailed status of a single scope within a connection. Use for polling after share/unshare operations. Returns status (SHARING/ACTIVATING/ACTIVE/REMOVING_SHARING/ERROR), day0 errors (Home org only), sync timestamps, and sharing metadata. Returns 404 when scope is fully unshared (expected after successful unshare).

**Call:** `execute_multiorg-scope-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_multiorg_scope_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_multiorg-scope-get) for the param schema and, where available, a worked example.

#### `multiorg-scope-list`

List all scopes (dataspaces) assigned to a connection with their sharing status. Filter by featureType (Dc1/Tua/Moma). Returns scope metadata, sync status, last synced timestamp, and who shared it.

**Call:** `execute_multiorg-scope-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_multiorg_scope_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_multiorg-scope-list) for the param schema and, where available, a worked example.

### Write operations

#### `multiorg-connection-disconnect`

Disconnect a multi-org connection and revoke 3-way trust. All scopes must be unshared first - check with d360_multiorg_connection_get to verify no active scopes remain. Returns 412 if scopes are still shared.

**Call:** `execute_multiorg-connection-disconnect`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_multiorg_connection_disconnect (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_multiorg-connection-disconnect) for the param schema and, where available, a worked example.

#### `multiorg-scope-share`

Share one or more dataspaces (scopes) with a connected companion org. Triggers async sharing pipeline - returns 202 Accepted immediately. Poll d360_multiorg_scope_get to track status flow SHARING to ACTIVATING to ACTIVE. Returns 409 if scope already shared or sandbox reconciliation in progress.

**Call:** `execute_multiorg-scope-share`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_multiorg_scope_share (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_multiorg-scope-share) for the param schema and, where available, a worked example.

#### `multiorg-scope-unshare`

Unshare one or more dataspaces from a connected companion org. Check d360_multiorg_scope_dependencies first - returns 412 if dependencies exist. Triggers async removal - status flow ACTIVE to REMOVING_SHARING to UNSHARED (404). Returns 409 if sandbox reconciliation in progress.

**Call:** `execute_multiorg-scope-unshare`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_multiorg_scope_unshare (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_multiorg-scope-unshare) for the param schema and, where available, a worked example.
