---
name: data360-semantic-engine-mcp-configure
description: "Use this skill when users want to execute Data Cloud SemanticEngine operations via the Data 360 MCP facade. Trigger when users mention data360/semantic, engine, shared, cdp, mcp, connect, api, shared-cdp-mcp-connect-api."
metadata:
  version: "1.0"
---

# Managing Data360/semantic Engine

## When to Use This Skill

Execute Data Cloud SemanticEngine operations via the Data 360 MCP facade.

## Workflow

Each step lists an `operation` id. Call describe(<operation>) BEFORE dispatching to get that tool's parameter schema and, where available, a worked example. `paramsJson` decodes to the operation's requestBody schema VERBATIM, including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap or omit it. The only envelope the step handles for you is `{toolName, paramsJson}` (its `invocation` already wraps it); do not POST the operation path directly. If the tool's error suggests `payload_examples`, ignore it — that tool isn't available here; call describe(<operation>) instead.

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `sdm-formula-metadata` | read | implemented | `execute_sdm-formula-metadata` | — |
| `sdm-generate-sql` | write | implemented | `execute_sdm-generate-sql` | — |
| `sdm-query` | read | implemented | `execute_sdm-query` | — |

### Read operations

#### `sdm-formula-metadata`

Get supported formula metadata for semantic models.

**Call:** `execute_sdm-formula-metadata`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_sdm_formula_metadata (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_sdm-formula-metadata) for the param schema and, where available, a worked example.

#### `sdm-query`

Execute a semantic query against a semantic data model. The body must follow this structure: { semanticModelId, structuredSemanticQuery: { fields: [{expression, alias, rowGrouping?, semanticAggregationMethod?}, ...], options: {limitOptions: {limit: 10}} } }. For regular fields: use tableField with tableName (e.g. 'Norm_Geography' in table 'AccountRevenue'). For calculated dimensions/measurements: use semanticField with just name (e.g. {semanticField: {name: 'Cluster_Size_Tier'}}) — these are model-level, NOT on a specific table.

**Call:** `execute_sdm-query`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_sdm_query (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_sdm-query) for the param schema and, where available, a worked example.

### Write operations

#### `sdm-generate-sql`

Generate SQL from a semantic data model query without executing it. Takes the same body shape as d360_sdm_query and returns the SQL string that would be executed against the data source.

**Call:** `execute_sdm-generate-sql`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_sdm_generate_sql (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_sdm-generate-sql) for the param schema and, where available, a worked example.
