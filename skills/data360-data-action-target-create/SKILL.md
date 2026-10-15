---
name: data360-data-action-target-create
description: "Use this skill when users want to execute Data Cloud DataActionTarget operations via the Data 360 MCP facade. Trigger when users mention data360/data, action, target, shared, cdp, mcp, connect, api, shared-cdp-mcp-connect-api."
metadata:
  version: "1.0"
---

# Managing Data360/data Action Target

## When to Use This Skill

Execute Data Cloud DataActionTarget operations via the Data 360 MCP facade.

## Workflow

Each step lists an `operation` id. Call describe(<operation>) BEFORE dispatching to get that tool's parameter schema and, where available, a worked example. `paramsJson` decodes to the operation's requestBody schema VERBATIM, including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap or omit it. The only envelope the step handles for you is `{toolName, paramsJson}` (its `invocation` already wraps it); do not POST the operation path directly. If the tool's error suggests `payload_examples`, ignore it — that tool isn't available here; call describe(<operation>) instead.

## Critical Constraints

**Destructive operations — require explicit user confirmation:**

- **`data-action-target-delete`** — Delete a data action target by API name.
  - Rollback: No automatic rollback.

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `data-action-target-create` | write | implemented | `execute_data-action-target-create` | — |
| `data-action-target-create-crm` | write | implemented | `execute_data-action-target-create-crm` | — |
| `data-action-target-create-mc-api-event` | write | implemented | `execute_data-action-target-create-mc-api-event` | — |
| `data-action-target-create-mc-email` | write | implemented | `execute_data-action-target-create-mc-email` | — |
| `data-action-target-create-webhook` | write | implemented | `execute_data-action-target-create-webhook` | — |
| `data-action-target-delete` | delete | implemented | `execute_data-action-target-delete` | — |
| `data-action-target-disable` | write | implemented | `execute_data-action-target-disable` | — |
| `data-action-target-enable` | write | implemented | `execute_data-action-target-enable` | — |
| `data-action-target-get` | read | implemented | `execute_data-action-target-get` | — |
| `data-action-target-list` | read | implemented | `execute_data-action-target-list` | — |
| `data-action-target-list-mc-email-templates` | read | implemented | `execute_data-action-target-list-mc-email-templates` | — |
| `data-action-target-list-mc-journeys` | read | implemented | `execute_data-action-target-list-mc-journeys` | — |
| `data-action-target-update` | write | implemented | `execute_data-action-target-update` | — |

### Read operations

#### `data-action-target-get`

Get a data action target by API name.

**Call:** `execute_data-action-target-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_action_target_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-action-target-get) for the param schema and, where available, a worked example.

#### `data-action-target-list`

List data action targets with pagination and ordering.

**Call:** `execute_data-action-target-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_action_target_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-action-target-list) for the param schema and, where available, a worked example.

#### `data-action-target-list-mc-email-templates`

List the Marketing Cloud email content templates available for a business unit so an agent can discover the contentTemplate/contentKey values to pass to d360_data_action_target_create_mc_email. First call d360_connection_list with connectorType=SalesforceMarketingCloud; use an activation business unit's mid as businessUnitId and the account's eid as enterpriseId. In each returned item, itemLabel is the contentTemplate and itemKey is the contentKey.

**Call:** `execute_data-action-target-list-mc-email-templates`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_action_target_list_mc_email_templates (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-action-target-list-mc-email-templates) for the param schema and, where available, a worked example.

#### `data-action-target-list-mc-journeys`

List the Marketing Cloud journeys / API-event interactions available for a business unit so an agent can discover the contentTemplate/contentKey values to pass to d360_data_action_target_create_mc_api_event. First call d360_connection_list with connectorType=SalesforceMarketingCloud; use an activation business unit's mid as businessUnitId and the account's eid as enterpriseId. Only published API events are returned. In each returned item, itemLabel is the contentTemplate and itemKey is the contentKey.

**Call:** `execute_data-action-target-list-mc-journeys`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_action_target_list_mc_journeys (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-action-target-list-mc-journeys) for the param schema and, where available, a worked example.

### Write operations

#### `data-action-target-create`

Create a data action target.

**Call:** `execute_data-action-target-create`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_action_target_create (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-action-target-create) for the param schema and, where available, a worked example.

#### `data-action-target-create-crm`

Create a CRM (Core) data action target that publishes platform events to a connected Salesforce CRM org. First call d360_connection_list with connectorType=SalesforceDotCom to find the connected org, then pass its org id (00D...) as orgId.

**Call:** `execute_data-action-target-create-crm`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_action_target_create_crm (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-action-target-create-crm) for the param schema and, where available, a worked example.

#### `data-action-target-create-mc-api-event`

Create a Marketing Cloud data action target that triggers an API event (Journey entry). First call d360_connection_list with connectorType=SalesforceMarketingCloud; use an activation business unit's mid as businessUnitId and the account's eid as enterpriseId. Use d360_data_action_target_list_mc_journeys to look up the available (published) API events and their contentTemplate/contentKey values. Only published API events can be used as a target.

**Call:** `execute_data-action-target-create-mc-api-event`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_action_target_create_mc_api_event (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-action-target-create-mc-api-event) for the param schema and, where available, a worked example.

#### `data-action-target-create-mc-email`

Create a Marketing Cloud data action target that triggers an email. First call d360_connection_list with connectorType=SalesforceMarketingCloud; use an activation business unit's mid as businessUnitId and the account's eid as enterpriseId. Use d360_data_action_target_list_mc_email_templates to look up the available email templates and their contentTemplate/contentKey values.

**Call:** `execute_data-action-target-create-mc-email`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_action_target_create_mc_email (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-action-target-create-mc-email) for the param schema and, where available, a worked example.

#### `data-action-target-create-webhook`

Create a WebHook data action target that POSTs data action events to an external HTTPS endpoint. Provide the webhook URL as targetEndpoint. No connection lookup is required.

**Call:** `execute_data-action-target-create-webhook`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_action_target_create_webhook (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-action-target-create-webhook) for the param schema and, where available, a worked example.

#### `data-action-target-disable`

Disable a data action target by API name, transitioning it to INACTIVE. 

**Call:** `execute_data-action-target-disable`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_action_target_disable (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-action-target-disable) for the param schema and, where available, a worked example.

#### `data-action-target-enable`

Enable a data action target by API name, transitioning it to ACTIVE. 

**Call:** `execute_data-action-target-enable`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_action_target_enable (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-action-target-enable) for the param schema and, where available, a worked example.

#### `data-action-target-update`

Update a data action target by API name.

**Call:** `execute_data-action-target-update`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_action_target_update (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-action-target-update) for the param schema and, where available, a worked example.

### Destructive operations

#### `data-action-target-delete`

Delete a data action target by API name.

**Call:** `execute_data-action-target-delete`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_action_target_delete (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-action-target-delete) for the param schema and, where available, a worked example.
