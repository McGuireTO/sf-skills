---
name: data360-goal-based-campaign-create
description: "Use this skill when users want to execute Data Cloud GoalBasedCampaign operations via the Data 360 MCP facade. Trigger when users mention data360/goal, based, campaign, shared, cdp, mcp, connect, api, shared-cdp-mcp-connect-api."
metadata:
  version: "1.0"
---

# Managing Data360/goal Based Campaign

## When to Use This Skill

Execute Data Cloud GoalBasedCampaign operations via the Data 360 MCP facade.

## Workflow

Each step lists an `operation` id. Call describe(<operation>) BEFORE dispatching to get that tool's parameter schema and, where available, a worked example. `paramsJson` decodes to the operation's requestBody schema VERBATIM, including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap or omit it. The only envelope the step handles for you is `{toolName, paramsJson}` (its `invocation` already wraps it); do not POST the operation path directly. If the tool's error suggests `payload_examples`, ignore it — that tool isn't available here; call describe(<operation>) instead.

## Critical Constraints

**Destructive operations — require explicit user confirmation:**

- **`mes-campaign-delete`** — Delete an MES campaign by ID.
  - Rollback: No automatic rollback.

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `mes-campaign-activate` | write | implemented | `execute_mes-campaign-activate` | — |
| `mes-campaign-analytics-metadata` | read | implemented | `execute_mes-campaign-analytics-metadata` | — |
| `mes-campaign-approve` | write | implemented | `execute_mes-campaign-approve` | — |
| `mes-campaign-baselines` | read | implemented | `execute_mes-campaign-baselines` | — |
| `mes-campaign-create` | write | implemented | `execute_mes-campaign-create` | — |
| `mes-campaign-delete` | delete | implemented | `execute_mes-campaign-delete` | — |
| `mes-campaign-get` | read | implemented | `execute_mes-campaign-get` | — |
| `mes-campaign-list` | read | implemented | `execute_mes-campaign-list` | — |
| `mes-campaign-plan` | write | implemented | `execute_mes-campaign-plan` | — |
| `mes-campaign-plan-save` | write | implemented | `execute_mes-campaign-plan-save` | — |
| `mes-campaign-prune-arm` | write | implemented | `execute_mes-campaign-prune-arm` | — |
| `mes-campaign-revise` | write | implemented | `execute_mes-campaign-revise` | — |
| `mes-campaign-segments` | read | implemented | `execute_mes-campaign-segments` | — |
| `mes-campaign-summary` | read | implemented | `execute_mes-campaign-summary` | — |

### Read operations

#### `mes-campaign-analytics-metadata`

Get campaign metadata and analytics configuration for the MES attribution card, including name, dates, budget, goal, semantic model ID, and data space.

**Call:** `execute_mes-campaign-analytics-metadata`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_mes_campaign_analytics_metadata (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_mes-campaign-analytics-metadata) for the param schema and, where available, a worked example.

#### `mes-campaign-baselines`

Get email and SMS click-through-rate baselines for an MES campaign, computed from the last 30 days (excluding today). Pass the campaignId, semanticModelId, and dataSpaceApiName from the analytics-metadata response.

**Call:** `execute_mes-campaign-baselines`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_mes_campaign_baselines (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_mes-campaign-baselines) for the param schema and, where available, a worked example.

#### `mes-campaign-get`

Get an MES campaign by ID. Use to poll for plan generation status after creating or revising a plan.

**Call:** `execute_mes-campaign-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_mes_campaign_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_mes-campaign-get) for the param schema and, where available, a worked example.

#### `mes-campaign-list`

List all MES marketing expert campaigns in the current org.

**Call:** `execute_mes-campaign-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_mes_campaign_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_mes-campaign-list) for the param schema and, where available, a worked example.

#### `mes-campaign-segments`

List active segments eligible for an MES campaign in a data space, filtered to the configured PersonalizationDataGraph's root DMO when available.

**Call:** `execute_mes-campaign-segments`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_mes_campaign_segments (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_mes-campaign-segments) for the param schema and, where available, a worked example.

#### `mes-campaign-summary`

Get a natural-language performance summary for an MES campaign, including overall performance, key trends, risks, and opportunities.

**Call:** `execute_mes-campaign-summary`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_mes_campaign_summary (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_mes-campaign-summary) for the param schema and, where available, a worked example.

### Write operations

#### `mes-campaign-activate`

Activate an approved MES campaign — creates and activates the operational campaign and flows. Returns immediately with Processing status; poll d360_mes_campaign_get for completion.

**Call:** `execute_mes-campaign-activate`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_mes_campaign_activate (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_mes-campaign-activate) for the param schema and, where available, a worked example.

#### `mes-campaign-approve`

Send an MES campaign plan for approval. Campaign must be in PlanReady state.

**Call:** `execute_mes-campaign-approve`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_mes_campaign_approve (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_mes-campaign-approve) for the param schema and, where available, a worked example.

#### `mes-campaign-create`

Create a new MES marketing expert campaign with a name, business unit, and optional description.

**Call:** `execute_mes-campaign-create`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_mes_campaign_create (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_mes-campaign-create) for the param schema and, where available, a worked example.

#### `mes-campaign-plan`

Create a new execution plan for an MES campaign from the provided change intent and channels. Returns immediately with GeneratingPlan status; poll d360_mes_campaign_get for completion.

**Call:** `execute_mes-campaign-plan`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_mes_campaign_plan (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_mes-campaign-plan) for the param schema and, where available, a worked example.

#### `mes-campaign-plan-save`

Save wizard inputs onto an MES campaign's existing plan without triggering LLM regeneration. Status is unchanged and no new plan is created. Only valid before the campaign has been revised; use d360_mes_campaign_revise to change a plan with natural-language intent.

**Call:** `execute_mes-campaign-plan-save`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_mes_campaign_plan_save (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_mes-campaign-plan-save) for the param schema and, where available, a worked example.

#### `mes-campaign-prune-arm`

Prune an underperforming campaign arm by setting its allocation to zero and redistributing weight to remaining arms.

**Call:** `execute_mes-campaign-prune-arm`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_mes_campaign_prune_arm (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_mes-campaign-prune-arm) for the param schema and, where available, a worked example.

#### `mes-campaign-revise`

Revise an existing MES campaign plan via natural-language input. Updates audience, channels, budget, content, duration, or goal. Returns immediately with Processing status; poll d360_mes_campaign_get for completion.

**Call:** `execute_mes-campaign-revise`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_mes_campaign_revise (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_mes-campaign-revise) for the param schema and, where available, a worked example.

### Destructive operations

#### `mes-campaign-delete`

Delete an MES campaign by ID.

**Call:** `execute_mes-campaign-delete`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_mes_campaign_delete (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_mes-campaign-delete) for the param schema and, where available, a worked example.
