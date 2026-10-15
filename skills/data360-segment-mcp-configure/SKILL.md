---
name: data360-segment-mcp-configure
description: "Use this skill when users want to execute Data Cloud Segment operations via the Data 360 MCP facade. Trigger when users mention data360/segment, shared, cdp, mcp, connect, api, shared-cdp-mcp-connect-api."
metadata:
  version: "1.0"
---

# Managing Data360/segment

## When to Use This Skill

Execute Data Cloud Segment operations via the Data 360 MCP facade.

## Workflow

Each step lists an `operation` id. Call describe(<operation>) BEFORE dispatching to get that tool's parameter schema and, where available, a worked example. `paramsJson` decodes to the operation's requestBody schema VERBATIM, including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap or omit it. The only envelope the step handles for you is `{toolName, paramsJson}` (its `invocation` already wraps it); do not POST the operation path directly. If the tool's error suggests `payload_examples`, ignore it — that tool isn't available here; call describe(<operation>) instead.

## Critical Constraints

**Destructive operations — require explicit user confirmation:**

- **`segment-delete`** — Delete an audience segment by segmentApiName. Removes the segment definition; published audiences are no longer regenerated.
  - Rollback: No automatic rollback.

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `segment-count` | read | implemented | `execute_segment-count` | — |
| `segment-create` | write | implemented | `execute_segment-create` | — |
| `segment-deactivate` | write | implemented | `execute_segment-deactivate` | — |
| `segment-deactivate-by-name` | write | implemented | `execute_segment-deactivate-by-name` | — |
| `segment-delete` | delete | implemented | `execute_segment-delete` | — |
| `segment-get` | read | implemented | `execute_segment-get` | — |
| `segment-get-by-id` | read | implemented | `execute_segment-get-by-id` | — |
| `segment-list` | read | implemented | `execute_segment-list` | — |
| `segment-member-list` | read | implemented | `execute_segment-member-list` | — |
| `segment-publish` | write | implemented | `execute_segment-publish` | — |
| `segment-update` | write | implemented | `execute_segment-update` | — |

### Read operations

#### `segment-count`

Trigger an asynchronous count of an audience segment by segmentApiName. Returns a job handle; poll for completion. Use to estimate audience size before publishing.

**Call:** `execute_segment-count`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_segment_count (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_segment-count) for the param schema and, where available, a worked example.

#### `segment-get`

Get a specific audience segment by its segmentApiName. Returns segment definition, criteria, and metadata.

**Call:** `execute_segment-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_segment_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_segment-get) for the param schema and, where available, a worked example.

#### `segment-get-by-id`

Get a specific audience segment by its 18-character segmentId (ID-typed lookup, distinct from d360_segment_get which uses segmentApiName). Returns segment definition, criteria, and metadata.

**Call:** `execute_segment-get-by-id`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_segment_get_by_id (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_segment-get-by-id) for the param schema and, where available, a worked example.

#### `segment-list`

List audience segments with batchSize/offset paging, ordering, and optional filters. Use d360_segment_get to fetch a single segment by API name.

**Call:** `execute_segment-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_segment_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_segment-list) for the param schema and, where available, a worked example.

#### `segment-member-list`

List members of an audience segment by segmentApiName. Supports pagination (limit/offset), ordering, field projection, and filtering. Use after d360_segment_publish to inspect the resolved audience.

**Call:** `execute_segment-member-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_segment_member_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_segment-member-list) for the param schema and, where available, a worked example.

### Write operations

#### `segment-create`

Create a new segment. DEPENDENCY: All CIs referenced in segment filters must be in ACTIVE status before creation. 

**Call:** `execute_segment-create`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_segment_create (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_segment-create) for the param schema and, where available, a worked example.

#### `segment-deactivate`

Deactivate an audience segment by segmentId. Stops scheduled publishes; existing audiences remain but are no longer regenerated.

**Call:** `execute_segment-deactivate`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_segment_deactivate (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_segment-deactivate) for the param schema and, where available, a worked example.

#### `segment-deactivate-by-name`

Deactivate an audience segment by segmentApiName (name-based; pair with d360_segment_deactivate which uses segmentId). Stops scheduled publishes; existing audiences remain but are no longer regenerated.

**Call:** `execute_segment-deactivate-by-name`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_segment_deactivate_by_name (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_segment-deactivate-by-name) for the param schema and, where available, a worked example.

#### `segment-publish`

Publish an audience segment on demand by segmentId. Triggers immediate evaluation and produces a fresh audience snapshot.

**Call:** `execute_segment-publish`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_segment_publish (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_segment-publish) for the param schema and, where available, a worked example.

#### `segment-update`

Update an existing audience segment by segmentApiName. Use to modify criteria, label, or metadata without recreating the segment.

**Call:** `execute_segment-update`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_segment_update (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_segment-update) for the param schema and, where available, a worked example.

### Destructive operations

#### `segment-delete`

Delete an audience segment by segmentApiName. Removes the segment definition; published audiences are no longer regenerated.

**Call:** `execute_segment-delete`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_segment_delete (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_segment-delete) for the param schema and, where available, a worked example.
