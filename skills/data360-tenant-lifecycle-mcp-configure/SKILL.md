---
name: data360-tenant-lifecycle-mcp-configure
description: "Use this skill when users want to execute Data Cloud TenantLifecycle operations via the Data 360 MCP facade. Trigger when users mention data360/tenant, lifecycle, shared, cdp, mcp, connect, api, shared-cdp-mcp-connect-api."
metadata:
  version: "1.0"
---

# Managing Data360/tenant Lifecycle

## When to Use This Skill

Execute Data Cloud TenantLifecycle operations via the Data 360 MCP facade.

## Workflow

Each step lists an `operation` id. Call describe(<operation>) BEFORE dispatching to get that tool's parameter schema and, where available, a worked example. `paramsJson` decodes to the operation's requestBody schema VERBATIM, including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap or omit it. The only envelope the step handles for you is `{toolName, paramsJson}` (its `invocation` already wraps it); do not POST the operation path directly. If the tool's error suggests `payload_examples`, ignore it — that tool isn't available here; call describe(<operation>) instead.

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `tenantlifecycle-details` | read | implemented | `execute_tenantlifecycle-details` | — |
| `tenantlifecycle-enable` | write | implemented | `execute_tenantlifecycle-enable` | — |
| `tenantlifecycle-retry` | write | implemented | `execute_tenantlifecycle-retry` | — |
| `tenantlifecycle-status` | read | implemented | `execute_tenantlifecycle-status` | — |

### Read operations

#### `tenantlifecycle-details`

Retrieve detailed Data Cloud (Data 360) tenant metadata for the org: homeOrgId, homeOrgInstance, tenantEndpoint, tenantId, coreId, and the counts of configured data spaces (dataSpacesCount) and connections (connectionsCount). Prerequisite: the tenant must already be provisioned — this metadata is only available after provisioning has completed successfully. Call d360_tenantlifecycle_status first and confirm isProvisioned is true before calling this tool; if the tenant is not yet provisioned, enable it with d360_tenantlifecycle_enable.

**Call:** `execute_tenantlifecycle-details`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_tenantlifecycle_details (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_tenantlifecycle-details) for the param schema and, where available, a worked example.

#### `tenantlifecycle-status`

Retrieve the current Data Cloud (Data 360) tenant lifecycle status for the org. Returns isActive (the tenant has a valid license and provisioning completed successfully), isProvisioned (provisioning finished successfully), isLicensed (the org has a valid Data Cloud license), and the current provisionStatus code with a provisionStatusDetail message. Call this first to decide the next step: if isProvisioned is false and isLicensed is true, enable provisioning with d360_tenantlifecycle_enable; if a prior provisioning attempt failed, retry with d360_tenantlifecycle_retry; once isProvisioned is true, fetch tenant metadata with d360_tenantlifecycle_details.

**Call:** `execute_tenantlifecycle-status`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_tenantlifecycle_status (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_tenantlifecycle-status) for the param schema and, where available, a worked example.

### Write operations

#### `tenantlifecycle-enable`

Enable Data Cloud (Data 360) tenant provisioning for the org. Optionally set installCIMPackage to true to also install the Customer Information Model (CIM) package as part of provisioning. Validation: the org must hold a valid Data Cloud license and must not already be provisioned — first call d360_tenantlifecycle_status and confirm isLicensed is true and isProvisioned is false before invoking this tool. This is an asynchronous, long-running operation; it returns the provisioning action result (status, message, success). Poll d360_tenantlifecycle_status for completion, and if provisioning fails use d360_tenantlifecycle_retry.

**Call:** `execute_tenantlifecycle-enable`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_tenantlifecycle_enable (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_tenantlifecycle-enable) for the param schema and, where available, a worked example.

#### `tenantlifecycle-retry`

Retry a previously failed Data Cloud (Data 360) tenant provisioning attempt for the org. Optionally set installCIMPackage to true to install the Customer Information Model (CIM) package during the retry. Use this when d360_tenantlifecycle_status reports a provisioning failure (isProvisioned is false with an error provisionStatus) after a prior d360_tenantlifecycle_enable call. This is an asynchronous, long-running operation; it returns the provisioning action result (status, message, success). Poll d360_tenantlifecycle_status for completion.

**Call:** `execute_tenantlifecycle-retry`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_tenantlifecycle_retry (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_tenantlifecycle-retry) for the param schema and, where available, a worked example.
