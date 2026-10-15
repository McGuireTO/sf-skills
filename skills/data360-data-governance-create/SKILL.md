---
name: data360-data-governance-create
description: "Use this skill when users want to execute Data Cloud DataGovernance operations via the Data 360 MCP facade. Trigger when users mention data360/data, governance, shared, cdp, mcp, connect, api, shared-cdp-mcp-connect-api."
metadata:
  version: "1.0"
---

# Managing Data360/data Governance

## When to Use This Skill

Execute Data Cloud DataGovernance operations via the Data 360 MCP facade.

## Workflow

Each step lists an `operation` id. Call describe(<operation>) BEFORE dispatching to get that tool's parameter schema and, where available, a worked example. `paramsJson` decodes to the operation's requestBody schema VERBATIM, including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap or omit it. The only envelope the step handles for you is `{toolName, paramsJson}` (its `invocation` already wraps it); do not POST the operation path directly. If the tool's error suggests `payload_examples`, ignore it — that tool isn't available here; call describe(<operation>) instead.

## Critical Constraints

**Destructive operations — require explicit user confirmation:**

- **`data-governance-access-policy-delete`** — Delete an Access Policy and all of its rules by developer name.
  - Rollback: No automatic rollback.
- **`data-governance-classification-assignment-bulk-delete`** — Bulk delete multiple classification assignments. Async operation returning per-item results.
  - Rollback: No automatic rollback.
- **`data-governance-classification-assignment-delete`** — Delete a classification assignment by ID. Async operation that returns 202 Accepted.
  - Rollback: No automatic rollback.
- **`data-governance-classification-bulk-delete`** — Bulk delete multiple classifications. Async operation returning per-item results.
  - Rollback: No automatic rollback.
- **`data-governance-classification-delete`** — Delete a data governance classification by fully-qualified name. Async operation 
  - Rollback: No automatic rollback.
- **`data-governance-classification-taxonomy-bulk-delete`** — Bulk delete multiple classification taxonomies. Returns per-item results.
  - Rollback: No automatic rollback.
- **`data-governance-classification-taxonomy-delete`** — Delete a classification taxonomy by name.
  - Rollback: No automatic rollback.
- **`data-governance-tag-assignment-bulk-delete`** — Bulk delete multiple tag assignments. Async operation returning per-item results.
  - Rollback: No automatic rollback.
- **`data-governance-tag-assignment-delete`** — Delete a tag assignment by ID. Async operation that returns 202 Accepted.
  - Rollback: No automatic rollback.
- **`data-governance-tag-bulk-delete`** — Bulk delete multiple data governance tags. Async operation returning per-item results.
  - Rollback: No automatic rollback.
- **`data-governance-tag-delete`** — Delete a data governance tag by fully-qualified name. Async operation 
  - Rollback: No automatic rollback.
- **`data-governance-tag-suggestion-reject`** — Reject one or more AI-generated tag suggestions, marking them as dismissed.
  - Rollback: No automatic rollback.
- **`data-governance-tag-taxonomy-bulk-delete`** — Bulk delete multiple tag taxonomies. Returns per-item results.
  - Rollback: No automatic rollback.
- **`data-governance-tag-taxonomy-delete`** — Delete a tag taxonomy by name.
  - Rollback: No automatic rollback.

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `data-governance-access-policy-create` | write | implemented | `execute_data-governance-access-policy-create` | — |
| `data-governance-access-policy-delete` | delete | implemented | `execute_data-governance-access-policy-delete` | — |
| `data-governance-access-policy-get` | read | implemented | `execute_data-governance-access-policy-get` | — |
| `data-governance-access-policy-list` | read | implemented | `execute_data-governance-access-policy-list` | — |
| `data-governance-access-policy-rule-get` | read | implemented | `execute_data-governance-access-policy-rule-get` | — |
| `data-governance-access-policy-rule-replace` | write | implemented | `execute_data-governance-access-policy-rule-replace` | — |
| `data-governance-access-policy-update` | write | implemented | `execute_data-governance-access-policy-update` | — |
| `data-governance-auto-tagging-job-get` | read | implemented | `execute_data-governance-auto-tagging-job-get` | — |
| `data-governance-auto-tagging-job-list` | read | implemented | `execute_data-governance-auto-tagging-job-list` | — |
| `data-governance-check-records-access` | read | implemented | `execute_data-governance-check-records-access` | — |
| `data-governance-classification-assignment-bulk-create` | write | implemented | `execute_data-governance-classification-assignment-bulk-create` | — |
| `data-governance-classification-assignment-bulk-delete` | delete | implemented | `execute_data-governance-classification-assignment-bulk-delete` | — |
| `data-governance-classification-assignment-create` | write | implemented | `execute_data-governance-classification-assignment-create` | — |
| `data-governance-classification-assignment-delete` | delete | implemented | `execute_data-governance-classification-assignment-delete` | — |
| `data-governance-classification-assignment-get` | read | implemented | `execute_data-governance-classification-assignment-get` | — |
| `data-governance-classification-assignment-list` | read | implemented | `execute_data-governance-classification-assignment-list` | — |
| `data-governance-classification-assignment-list-for-classification` | read | implemented | `execute_data-governance-classification-assignment-list-for-classification` | — |
| `data-governance-classification-bulk-create` | write | implemented | `execute_data-governance-classification-bulk-create` | — |
| `data-governance-classification-bulk-delete` | delete | implemented | `execute_data-governance-classification-bulk-delete` | — |
| `data-governance-classification-bulk-update` | write | implemented | `execute_data-governance-classification-bulk-update` | — |
| `data-governance-classification-create` | write | implemented | `execute_data-governance-classification-create` | — |
| `data-governance-classification-delete` | delete | implemented | `execute_data-governance-classification-delete` | — |
| `data-governance-classification-get` | read | implemented | `execute_data-governance-classification-get` | — |
| `data-governance-classification-list` | read | implemented | `execute_data-governance-classification-list` | — |
| `data-governance-classification-taxonomy-bulk-create` | write | implemented | `execute_data-governance-classification-taxonomy-bulk-create` | — |
| `data-governance-classification-taxonomy-bulk-delete` | delete | implemented | `execute_data-governance-classification-taxonomy-bulk-delete` | — |
| `data-governance-classification-taxonomy-bulk-update` | write | implemented | `execute_data-governance-classification-taxonomy-bulk-update` | — |
| `data-governance-classification-taxonomy-create` | write | implemented | `execute_data-governance-classification-taxonomy-create` | — |
| `data-governance-classification-taxonomy-delete` | delete | implemented | `execute_data-governance-classification-taxonomy-delete` | — |
| `data-governance-classification-taxonomy-get` | read | implemented | `execute_data-governance-classification-taxonomy-get` | — |
| `data-governance-classification-taxonomy-list` | read | implemented | `execute_data-governance-classification-taxonomy-list` | — |
| `data-governance-classification-taxonomy-update` | write | implemented | `execute_data-governance-classification-taxonomy-update` | — |
| `data-governance-classification-update` | write | implemented | `execute_data-governance-classification-update` | — |
| `data-governance-tag-assignment-bulk-create` | write | implemented | `execute_data-governance-tag-assignment-bulk-create` | — |
| `data-governance-tag-assignment-bulk-delete` | delete | implemented | `execute_data-governance-tag-assignment-bulk-delete` | — |
| `data-governance-tag-assignment-create` | write | implemented | `execute_data-governance-tag-assignment-create` | — |
| `data-governance-tag-assignment-delete` | delete | implemented | `execute_data-governance-tag-assignment-delete` | — |
| `data-governance-tag-assignment-get` | read | implemented | `execute_data-governance-tag-assignment-get` | — |
| `data-governance-tag-assignment-list` | read | implemented | `execute_data-governance-tag-assignment-list` | — |
| `data-governance-tag-assignment-list-for-tag` | write | implemented | `execute_data-governance-tag-assignment-list-for-tag` | — |
| `data-governance-tag-bulk-create` | write | implemented | `execute_data-governance-tag-bulk-create` | — |
| `data-governance-tag-bulk-delete` | delete | implemented | `execute_data-governance-tag-bulk-delete` | — |
| `data-governance-tag-bulk-update` | write | implemented | `execute_data-governance-tag-bulk-update` | — |
| `data-governance-tag-create` | write | implemented | `execute_data-governance-tag-create` | — |
| `data-governance-tag-delete` | delete | implemented | `execute_data-governance-tag-delete` | — |
| `data-governance-tag-get` | read | implemented | `execute_data-governance-tag-get` | — |
| `data-governance-tag-list` | read | implemented | `execute_data-governance-tag-list` | — |
| `data-governance-tag-propagate` | write | implemented | `execute_data-governance-tag-propagate` | — |
| `data-governance-tag-suggestion-approve` | write | implemented | `execute_data-governance-tag-suggestion-approve` | — |
| `data-governance-tag-suggestion-generate` | write | implemented | `execute_data-governance-tag-suggestion-generate` | — |
| `data-governance-tag-suggestion-get` | read | implemented | `execute_data-governance-tag-suggestion-get` | — |
| `data-governance-tag-suggestion-list` | read | implemented | `execute_data-governance-tag-suggestion-list` | — |
| `data-governance-tag-suggestion-reject` | delete | implemented | `execute_data-governance-tag-suggestion-reject` | — |
| `data-governance-tag-taxonomy-bulk-create` | write | implemented | `execute_data-governance-tag-taxonomy-bulk-create` | — |
| `data-governance-tag-taxonomy-bulk-delete` | delete | implemented | `execute_data-governance-tag-taxonomy-bulk-delete` | — |
| `data-governance-tag-taxonomy-bulk-update` | write | implemented | `execute_data-governance-tag-taxonomy-bulk-update` | — |
| `data-governance-tag-taxonomy-create` | write | implemented | `execute_data-governance-tag-taxonomy-create` | — |
| `data-governance-tag-taxonomy-delete` | delete | implemented | `execute_data-governance-tag-taxonomy-delete` | — |
| `data-governance-tag-taxonomy-get` | read | implemented | `execute_data-governance-tag-taxonomy-get` | — |
| `data-governance-tag-taxonomy-list` | read | implemented | `execute_data-governance-tag-taxonomy-list` | — |
| `data-governance-tag-taxonomy-update` | write | implemented | `execute_data-governance-tag-taxonomy-update` | — |
| `data-governance-tag-update` | write | implemented | `execute_data-governance-tag-update` | — |

### Read operations

#### `data-governance-access-policy-get`

Get an Access Policy and its embedded rules by developer name.

**Call:** `execute_data-governance-access-policy-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_governance_access_policy_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-governance-access-policy-get) for the param schema and, where available, a worked example.

#### `data-governance-access-policy-list`

List Access Policies with optional search and pagination. By default, returns only 

**Call:** `execute_data-governance-access-policy-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_governance_access_policy_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-governance-access-policy-list) for the param schema and, where available, a worked example.

#### `data-governance-access-policy-rule-get`

Get a rule within an Access Policy by its policy and rule developer names.

**Call:** `execute_data-governance-access-policy-rule-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_governance_access_policy_rule_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-governance-access-policy-rule-get) for the param schema and, where available, a worked example.

#### `data-governance-auto-tagging-job-get`

Get a single auto-tagging job by ID, reporting progress and status.

**Call:** `execute_data-governance-auto-tagging-job-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_governance_auto_tagging_job_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-governance-auto-tagging-job-get) for the param schema and, where available, a worked example.

#### `data-governance-auto-tagging-job-list`

List auto-tagging jobs with optional filtering by object or status and pagination.

**Call:** `execute_data-governance-auto-tagging-job-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_governance_auto_tagging_job_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-governance-auto-tagging-job-list) for the param schema and, where available, a worked example.

#### `data-governance-check-records-access`

Check whether records are accessible based on data governance policies. 

**Call:** `execute_data-governance-check-records-access`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_governance_check_records_access (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-governance-check-records-access) for the param schema and, where available, a worked example.

#### `data-governance-classification-assignment-get`

Get a single classification assignment by ID.

**Call:** `execute_data-governance-classification-assignment-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_governance_classification_assignment_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-governance-classification-assignment-get) for the param schema and, where available, a worked example.

#### `data-governance-classification-assignment-list`

List classification assignments with optional filtering by tag or classification name and pagination.

**Call:** `execute_data-governance-classification-assignment-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_governance_classification_assignment_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-governance-classification-assignment-list) for the param schema and, where available, a worked example.

#### `data-governance-classification-assignment-list-for-classification`

List classification assignments for a specific classification by its fully-qualified name with pagination.

**Call:** `execute_data-governance-classification-assignment-list-for-classification`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_governance_classification_assignment_list_for_classification (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-governance-classification-assignment-list-for-classification) for the param schema and, where available, a worked example.

#### `data-governance-classification-get`

Get a single data governance classification by its fully-qualified name. 

**Call:** `execute_data-governance-classification-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_governance_classification_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-governance-classification-get) for the param schema and, where available, a worked example.

#### `data-governance-classification-list`

List data governance classifications with optional filtering by taxonomy, 

**Call:** `execute_data-governance-classification-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_governance_classification_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-governance-classification-list) for the param schema and, where available, a worked example.

#### `data-governance-classification-taxonomy-get`

Get a single classification taxonomy by name.

**Call:** `execute_data-governance-classification-taxonomy-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_governance_classification_taxonomy_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-governance-classification-taxonomy-get) for the param schema and, where available, a worked example.

#### `data-governance-classification-taxonomy-list`

List classification taxonomies with optional search and pagination.

**Call:** `execute_data-governance-classification-taxonomy-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_governance_classification_taxonomy_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-governance-classification-taxonomy-list) for the param schema and, where available, a worked example.

#### `data-governance-tag-assignment-get`

Get a single tag assignment by ID.

**Call:** `execute_data-governance-tag-assignment-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_governance_tag_assignment_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-governance-tag-assignment-get) for the param schema and, where available, a worked example.

#### `data-governance-tag-assignment-list`

List tag assignments with optional filtering by object, field, tag name, and pagination.

**Call:** `execute_data-governance-tag-assignment-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_governance_tag_assignment_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-governance-tag-assignment-list) for the param schema and, where available, a worked example.

#### `data-governance-tag-get`

Get a single data governance tag by its fully-qualified name. 

**Call:** `execute_data-governance-tag-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_governance_tag_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-governance-tag-get) for the param schema and, where available, a worked example.

#### `data-governance-tag-list`

List data governance tags with optional filtering by taxonomy, parent tag, 

**Call:** `execute_data-governance-tag-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_governance_tag_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-governance-tag-list) for the param schema and, where available, a worked example.

#### `data-governance-tag-suggestion-get`

Get a single AI-generated tag suggestion by ID.

**Call:** `execute_data-governance-tag-suggestion-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_governance_tag_suggestion_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-governance-tag-suggestion-get) for the param schema and, where available, a worked example.

#### `data-governance-tag-suggestion-list`

List AI-generated tag suggestions with optional filtering by object, tag, status, and pagination.

**Call:** `execute_data-governance-tag-suggestion-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_governance_tag_suggestion_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-governance-tag-suggestion-list) for the param schema and, where available, a worked example.

#### `data-governance-tag-taxonomy-get`

Get a single tag taxonomy by name. Returns definition including label and description.

**Call:** `execute_data-governance-tag-taxonomy-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_governance_tag_taxonomy_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-governance-tag-taxonomy-get) for the param schema and, where available, a worked example.

#### `data-governance-tag-taxonomy-list`

List tag taxonomies with optional search and pagination.

**Call:** `execute_data-governance-tag-taxonomy-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_governance_tag_taxonomy_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-governance-tag-taxonomy-list) for the param schema and, where available, a worked example.

### Write operations

#### `data-governance-access-policy-create`

Create an Access Policy with exactly one rule. The request is validated atomically 

**Call:** `execute_data-governance-access-policy-create`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_governance_access_policy_create (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-governance-access-policy-create) for the param schema and, where available, a worked example.

#### `data-governance-access-policy-rule-replace`

Create or fully replace a rule within an Access Policy. The rule name in the request, 

**Call:** `execute_data-governance-access-policy-rule-replace`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_governance_access_policy_rule_replace (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-governance-access-policy-rule-replace) for the param schema and, where available, a worked example.

#### `data-governance-access-policy-update`

Update only an Access Policy's label and description. This does not rename the policy 

**Call:** `execute_data-governance-access-policy-update`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_governance_access_policy_update (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-governance-access-policy-update) for the param schema and, where available, a worked example.

#### `data-governance-classification-assignment-bulk-create`

Bulk create multiple classification assignments in a single request. Returns per-item results.

**Call:** `execute_data-governance-classification-assignment-bulk-create`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_governance_classification_assignment_bulk_create (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-governance-classification-assignment-bulk-create) for the param schema and, where available, a worked example.

#### `data-governance-classification-assignment-create`

Create a classification assignment linking a classification to a tag.

**Call:** `execute_data-governance-classification-assignment-create`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_governance_classification_assignment_create (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-governance-classification-assignment-create) for the param schema and, where available, a worked example.

#### `data-governance-classification-bulk-create`

Bulk create multiple classifications in a single request. Returns per-item results.

**Call:** `execute_data-governance-classification-bulk-create`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_governance_classification_bulk_create (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-governance-classification-bulk-create) for the param schema and, where available, a worked example.

#### `data-governance-classification-bulk-update`

Bulk update multiple classifications. Returns per-item results.

**Call:** `execute_data-governance-classification-bulk-update`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_governance_classification_bulk_update (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-governance-classification-bulk-update) for the param schema and, where available, a worked example.

#### `data-governance-classification-create`

Create a new data governance classification. Requires fullyQualifiedName 

**Call:** `execute_data-governance-classification-create`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_governance_classification_create (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-governance-classification-create) for the param schema and, where available, a worked example.

#### `data-governance-classification-taxonomy-bulk-create`

Bulk create multiple classification taxonomies in a single request. Returns per-item results.

**Call:** `execute_data-governance-classification-taxonomy-bulk-create`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_governance_classification_taxonomy_bulk_create (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-governance-classification-taxonomy-bulk-create) for the param schema and, where available, a worked example.

#### `data-governance-classification-taxonomy-bulk-update`

Bulk update multiple classification taxonomies. Returns per-item results.

**Call:** `execute_data-governance-classification-taxonomy-bulk-update`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_governance_classification_taxonomy_bulk_update (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-governance-classification-taxonomy-bulk-update) for the param schema and, where available, a worked example.

#### `data-governance-classification-taxonomy-create`

Create a new classification taxonomy. Requires name and label.

**Call:** `execute_data-governance-classification-taxonomy-create`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_governance_classification_taxonomy_create (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-governance-classification-taxonomy-create) for the param schema and, where available, a worked example.

#### `data-governance-classification-taxonomy-update`

Update an existing classification taxonomy. Supports changing label and description.

**Call:** `execute_data-governance-classification-taxonomy-update`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_governance_classification_taxonomy_update (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-governance-classification-taxonomy-update) for the param schema and, where available, a worked example.

#### `data-governance-classification-update`

Update an existing data governance classification. Supports changing label, 

**Call:** `execute_data-governance-classification-update`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_governance_classification_update (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-governance-classification-update) for the param schema and, where available, a worked example.

#### `data-governance-tag-assignment-bulk-create`

Bulk create multiple tag assignments in a single request. Returns per-item results.

**Call:** `execute_data-governance-tag-assignment-bulk-create`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_governance_tag_assignment_bulk_create (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-governance-tag-assignment-bulk-create) for the param schema and, where available, a worked example.

#### `data-governance-tag-assignment-create`

Create a tag assignment linking a tag to an object or field.

**Call:** `execute_data-governance-tag-assignment-create`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_governance_tag_assignment_create (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-governance-tag-assignment-create) for the param schema and, where available, a worked example.

#### `data-governance-tag-assignment-list-for-tag`

List tag assignments for a specific tag by its fully-qualified name with pagination.

**Call:** `execute_data-governance-tag-assignment-list-for-tag`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_governance_tag_assignment_list_for_tag (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-governance-tag-assignment-list-for-tag) for the param schema and, where available, a worked example.

#### `data-governance-tag-bulk-create`

Bulk create multiple data governance tags in a single request. Returns per-item results.

**Call:** `execute_data-governance-tag-bulk-create`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_governance_tag_bulk_create (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-governance-tag-bulk-create) for the param schema and, where available, a worked example.

#### `data-governance-tag-bulk-update`

Bulk update multiple data governance tags. Returns per-item results.

**Call:** `execute_data-governance-tag-bulk-update`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_governance_tag_bulk_update (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-governance-tag-bulk-update) for the param schema and, where available, a worked example.

#### `data-governance-tag-create`

Create a new data governance tag. Requires fullyQualifiedName 

**Call:** `execute_data-governance-tag-create`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_governance_tag_create (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-governance-tag-create) for the param schema and, where available, a worked example.

#### `data-governance-tag-propagate`

Propagate data governance tags to specified objects. Creates assignments based on tag lineage rules.

**Call:** `execute_data-governance-tag-propagate`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_governance_tag_propagate (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-governance-tag-propagate) for the param schema and, where available, a worked example.

#### `data-governance-tag-suggestion-approve`

Approve one or more AI-generated tag suggestions, materializing them as real tag assignments.

**Call:** `execute_data-governance-tag-suggestion-approve`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_governance_tag_suggestion_approve (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-governance-tag-suggestion-approve) for the param schema and, where available, a worked example.

#### `data-governance-tag-suggestion-generate`

Launch async AI-driven tag suggestion generation for one or more objects. 

**Call:** `execute_data-governance-tag-suggestion-generate`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_governance_tag_suggestion_generate (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-governance-tag-suggestion-generate) for the param schema and, where available, a worked example.

#### `data-governance-tag-taxonomy-bulk-create`

Bulk create multiple tag taxonomies in a single request. Returns per-item results.

**Call:** `execute_data-governance-tag-taxonomy-bulk-create`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_governance_tag_taxonomy_bulk_create (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-governance-tag-taxonomy-bulk-create) for the param schema and, where available, a worked example.

#### `data-governance-tag-taxonomy-bulk-update`

Bulk update multiple tag taxonomies. Returns per-item results.

**Call:** `execute_data-governance-tag-taxonomy-bulk-update`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_governance_tag_taxonomy_bulk_update (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-governance-tag-taxonomy-bulk-update) for the param schema and, where available, a worked example.

#### `data-governance-tag-taxonomy-create`

Create a new tag taxonomy. Requires name and label.

**Call:** `execute_data-governance-tag-taxonomy-create`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_governance_tag_taxonomy_create (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-governance-tag-taxonomy-create) for the param schema and, where available, a worked example.

#### `data-governance-tag-taxonomy-update`

Update an existing tag taxonomy. Supports changing label and description.

**Call:** `execute_data-governance-tag-taxonomy-update`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_governance_tag_taxonomy_update (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-governance-tag-taxonomy-update) for the param schema and, where available, a worked example.

#### `data-governance-tag-update`

Update an existing data governance tag. Supports changing label, description, 

**Call:** `execute_data-governance-tag-update`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_governance_tag_update (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-governance-tag-update) for the param schema and, where available, a worked example.

### Destructive operations

#### `data-governance-access-policy-delete`

Delete an Access Policy and all of its rules by developer name.

**Call:** `execute_data-governance-access-policy-delete`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_governance_access_policy_delete (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-governance-access-policy-delete) for the param schema and, where available, a worked example.

#### `data-governance-classification-assignment-bulk-delete`

Bulk delete multiple classification assignments. Async operation returning per-item results.

**Call:** `execute_data-governance-classification-assignment-bulk-delete`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_governance_classification_assignment_bulk_delete (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-governance-classification-assignment-bulk-delete) for the param schema and, where available, a worked example.

#### `data-governance-classification-assignment-delete`

Delete a classification assignment by ID. Async operation that returns 202 Accepted.

**Call:** `execute_data-governance-classification-assignment-delete`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_governance_classification_assignment_delete (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-governance-classification-assignment-delete) for the param schema and, where available, a worked example.

#### `data-governance-classification-bulk-delete`

Bulk delete multiple classifications. Async operation returning per-item results.

**Call:** `execute_data-governance-classification-bulk-delete`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_governance_classification_bulk_delete (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-governance-classification-bulk-delete) for the param schema and, where available, a worked example.

#### `data-governance-classification-delete`

Delete a data governance classification by fully-qualified name. Async operation 

**Call:** `execute_data-governance-classification-delete`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_governance_classification_delete (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-governance-classification-delete) for the param schema and, where available, a worked example.

#### `data-governance-classification-taxonomy-bulk-delete`

Bulk delete multiple classification taxonomies. Returns per-item results.

**Call:** `execute_data-governance-classification-taxonomy-bulk-delete`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_governance_classification_taxonomy_bulk_delete (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-governance-classification-taxonomy-bulk-delete) for the param schema and, where available, a worked example.

#### `data-governance-classification-taxonomy-delete`

Delete a classification taxonomy by name.

**Call:** `execute_data-governance-classification-taxonomy-delete`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_governance_classification_taxonomy_delete (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-governance-classification-taxonomy-delete) for the param schema and, where available, a worked example.

#### `data-governance-tag-assignment-bulk-delete`

Bulk delete multiple tag assignments. Async operation returning per-item results.

**Call:** `execute_data-governance-tag-assignment-bulk-delete`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_governance_tag_assignment_bulk_delete (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-governance-tag-assignment-bulk-delete) for the param schema and, where available, a worked example.

#### `data-governance-tag-assignment-delete`

Delete a tag assignment by ID. Async operation that returns 202 Accepted.

**Call:** `execute_data-governance-tag-assignment-delete`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_governance_tag_assignment_delete (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-governance-tag-assignment-delete) for the param schema and, where available, a worked example.

#### `data-governance-tag-bulk-delete`

Bulk delete multiple data governance tags. Async operation returning per-item results.

**Call:** `execute_data-governance-tag-bulk-delete`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_governance_tag_bulk_delete (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-governance-tag-bulk-delete) for the param schema and, where available, a worked example.

#### `data-governance-tag-delete`

Delete a data governance tag by fully-qualified name. Async operation 

**Call:** `execute_data-governance-tag-delete`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_governance_tag_delete (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-governance-tag-delete) for the param schema and, where available, a worked example.

#### `data-governance-tag-suggestion-reject`

Reject one or more AI-generated tag suggestions, marking them as dismissed.

**Call:** `execute_data-governance-tag-suggestion-reject`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_governance_tag_suggestion_reject (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-governance-tag-suggestion-reject) for the param schema and, where available, a worked example.

#### `data-governance-tag-taxonomy-bulk-delete`

Bulk delete multiple tag taxonomies. Returns per-item results.

**Call:** `execute_data-governance-tag-taxonomy-bulk-delete`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_governance_tag_taxonomy_bulk_delete (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-governance-tag-taxonomy-bulk-delete) for the param schema and, where available, a worked example.

#### `data-governance-tag-taxonomy-delete`

Delete a tag taxonomy by name.

**Call:** `execute_data-governance-tag-taxonomy-delete`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_data_governance_tag_taxonomy_delete (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_data-governance-tag-taxonomy-delete) for the param schema and, where available, a worked example.
