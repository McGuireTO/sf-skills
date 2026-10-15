---
name: data360-machine-learning-mcp-configure
description: "Use this skill when users want to execute Data Cloud MachineLearning operations via the Data 360 MCP facade. Trigger when users mention data360/machine, learning, shared, cdp, mcp, connect, api, shared-cdp-mcp-connect-api."
metadata:
  version: "1.0"
---

# Managing Data360/machine Learning

## When to Use This Skill

Execute Data Cloud MachineLearning operations via the Data 360 MCP facade.

## Workflow

Each step lists an `operation` id. Call describe(<operation>) BEFORE dispatching to get that tool's parameter schema and, where available, a worked example. `paramsJson` decodes to the operation's requestBody schema VERBATIM, including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap or omit it. The only envelope the step handles for you is `{toolName, paramsJson}` (its `invocation` already wraps it); do not POST the operation path directly. If the tool's error suggests `payload_examples`, ignore it — that tool isn't available here; call describe(<operation>) instead.

## Critical Constraints

**Destructive operations — require explicit user confirmation:**

- **`ml-configured-model-delete`** — Delete a configured model.
  - Rollback: No automatic rollback.
- **`ml-model-artifact-delete`** — Delete a model artifact.
  - Rollback: No automatic rollback.
- **`ml-model-setup-delete`** — Delete a model-setup container. Cascades to all versions. Irreversible.
  - Rollback: No automatic rollback.
- **`prediction-job-def-delete`** — Delete a prediction job definition. Irreversible.
  - Rollback: No automatic rollback.
- **`retriever-config-delete`** — Delete one configuration version of a retriever by version ID or API name. The active version cannot be deleted — 
  - Rollback: No automatic rollback.
- **`retriever-delete`** — Delete a retriever by ID or API name, including all of its configuration versions. This is irreversible. The retriever 
  - Rollback: No automatic rollback.

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `ml-alert-update` | write | implemented | `execute_ml-alert-update` | — |
| `ml-alerts-query` | read | implemented | `execute_ml-alerts-query` | — |
| `ml-configured-model-activate` | write | implemented | `execute_ml-configured-model-activate` | — |
| `ml-configured-model-create` | write | implemented | `execute_ml-configured-model-create` | — |
| `ml-configured-model-delete` | delete | implemented | `execute_ml-configured-model-delete` | — |
| `ml-configured-model-get` | read | implemented | `execute_ml-configured-model-get` | — |
| `ml-configured-model-history-get` | read | implemented | `execute_ml-configured-model-history-get` | — |
| `ml-configured-model-history-list` | read | implemented | `execute_ml-configured-model-history-list` | — |
| `ml-configured-model-list` | read | implemented | `execute_ml-configured-model-list` | — |
| `ml-configured-model-update` | write | implemented | `execute_ml-configured-model-update` | — |
| `ml-model-artifact-delete` | delete | implemented | `execute_ml-model-artifact-delete` | — |
| `ml-model-artifact-get` | read | implemented | `execute_ml-model-artifact-get` | — |
| `ml-model-artifact-list` | read | implemented | `execute_ml-model-artifact-list` | — |
| `ml-model-artifact-update` | write | implemented | `execute_ml-model-artifact-update` | — |
| `ml-model-setup-create` | write | implemented | `execute_ml-model-setup-create` | — |
| `ml-model-setup-delete` | delete | implemented | `execute_ml-model-setup-delete` | — |
| `ml-model-setup-get` | read | implemented | `execute_ml-model-setup-get` | — |
| `ml-model-setup-list` | read | implemented | `execute_ml-model-setup-list` | — |
| `ml-model-setup-update` | write | implemented | `execute_ml-model-setup-update` | — |
| `ml-predict` | read | implemented | `execute_ml-predict` | — |
| `ml-query-data-profile` | read | implemented | `execute_ml-query-data-profile` | — |
| `ml-query-outcome` | read | implemented | `execute_ml-query-outcome` | — |
| `ml-query-row-count` | read | implemented | `execute_ml-query-row-count` | — |
| `ml-query-setup-fields` | read | implemented | `execute_ml-query-setup-fields` | — |
| `ml-setup-version-create` | write | implemented | `execute_ml-setup-version-create` | — |
| `ml-setup-version-get` | read | implemented | `execute_ml-setup-version-get` | — |
| `ml-setup-version-inspector-metrics-get` | read | implemented | `execute_ml-setup-version-inspector-metrics-get` | — |
| `ml-setup-version-list` | read | implemented | `execute_ml-setup-version-list` | — |
| `ml-setup-version-update` | write | implemented | `execute_ml-setup-version-update` | — |
| `prediction-job-def-activate` | write | implemented | `execute_prediction-job-def-activate` | — |
| `prediction-job-def-create` | write | implemented | `execute_prediction-job-def-create` | — |
| `prediction-job-def-create-binary-classification` | write | implemented | `execute_prediction-job-def-create-binary-classification` | — |
| `prediction-job-def-create-clustering` | write | implemented | `execute_prediction-job-def-create-clustering` | — |
| `prediction-job-def-create-multiclass-classification` | write | implemented | `execute_prediction-job-def-create-multiclass-classification` | — |
| `prediction-job-def-create-regression` | write | implemented | `execute_prediction-job-def-create-regression` | — |
| `prediction-job-def-create-sentiment-detection` | write | implemented | `execute_prediction-job-def-create-sentiment-detection` | — |
| `prediction-job-def-create-topic-classification` | write | implemented | `execute_prediction-job-def-create-topic-classification` | — |
| `prediction-job-def-deactivate` | write | implemented | `execute_prediction-job-def-deactivate` | — |
| `prediction-job-def-delete` | delete | implemented | `execute_prediction-job-def-delete` | — |
| `prediction-job-def-get` | read | implemented | `execute_prediction-job-def-get` | — |
| `prediction-job-def-list` | read | implemented | `execute_prediction-job-def-list` | — |
| `prediction-job-def-update` | write | implemented | `execute_prediction-job-def-update` | — |
| `prediction-job-run` | write | implemented | `execute_prediction-job-run` | — |
| `retriever-config-create-custom-sql` | write | implemented | `execute_retriever-config-create-custom-sql` | — |
| `retriever-config-create-ensemble` | write | implemented | `execute_retriever-config-create-ensemble` | — |
| `retriever-config-create-no-code` | write | implemented | `execute_retriever-config-create-no-code` | — |
| `retriever-config-delete` | delete | implemented | `execute_retriever-config-delete` | — |
| `retriever-config-get` | read | implemented | `execute_retriever-config-get` | — |
| `retriever-config-list` | read | implemented | `execute_retriever-config-list` | — |
| `retriever-config-update` | write | implemented | `execute_retriever-config-update` | — |
| `retriever-create-custom-sql` | write | implemented | `execute_retriever-create-custom-sql` | — |
| `retriever-create-ensemble` | write | implemented | `execute_retriever-create-ensemble` | — |
| `retriever-create-no-code` | write | implemented | `execute_retriever-create-no-code` | — |
| `retriever-delete` | delete | implemented | `execute_retriever-delete` | — |
| `retriever-get` | read | implemented | `execute_retriever-get` | — |
| `retriever-integrations-get` | read | implemented | `execute_retriever-integrations-get` | — |
| `retriever-list` | read | implemented | `execute_retriever-list` | — |
| `retriever-review` | read | implemented | `execute_retriever-review` | — |
| `retriever-update` | write | implemented | `execute_retriever-update` | — |

### Read operations

#### `ml-alerts-query`

Query data alerts for a model artifact. Returns training-time findings (e.g. ObviousPredictor, 

**Call:** `execute_ml-alerts-query`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_ml_alerts_query (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_ml-alerts-query) for the param schema and, where available, a worked example.

#### `ml-configured-model-get`

Get a configured model by id or developer name. Notable fields: status, 

**Call:** `execute_ml-configured-model-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_ml_configured_model_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_ml-configured-model-get) for the param schema and, where available, a worked example.

#### `ml-configured-model-history-get`

Get one configured-model history snapshot. The 'configuredModel' field on the response carries the 

**Call:** `execute_ml-configured-model-history-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_ml_configured_model_history_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_ml-configured-model-history-get) for the param schema and, where available, a worked example.

#### `ml-configured-model-history-list`

List history snapshots for a configured model. Snapshots are content-based — no entry for no-op edits. OOTB models have no history.

**Call:** `execute_ml-configured-model-history-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_ml_configured_model_history_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_ml-configured-model-history-list) for the param schema and, where available, a worked example.

#### `ml-configured-model-list`

List configured models. When looking for a specific predictive model prefer narrowing with search 

**Call:** `execute_ml-configured-model-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_ml_configured_model_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_ml-configured-model-list) for the param schema and, where available, a worked example.

#### `ml-model-artifact-get`

Get a model artifact by id or developer name. Notable fields: status, modelType, sourceType, 

**Call:** `execute_ml-model-artifact-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_ml_model_artifact_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_ml-model-artifact-get) for the param schema and, where available, a worked example.

#### `ml-model-artifact-list`

List trained ML model artifacts. Artifacts are auto-created when a setup-version reaches Published. 

**Call:** `execute_ml-model-artifact-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_ml_model_artifact_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_ml-model-artifact-list) for the param schema and, where available, a worked example.

#### `ml-model-setup-get`

Get a model-setup container by id or developer name.

**Call:** `execute_ml-model-setup-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_ml_model_setup_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_ml-model-setup-get) for the param schema and, where available, a worked example.

#### `ml-model-setup-list`

List model-setup containers. Optional filters: search (free-text), modelType, modelCapability, setupType, connectorType. Pagination via limit/offset.

**Call:** `execute_ml-model-setup-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_ml_model_setup_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_ml-model-setup-list) for the param schema and, where available, a worked example.

#### `ml-predict`

Run synchronous prediction against a configured model. 

**Call:** `execute_ml-predict`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_ml_predict (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_ml-predict) for the param schema and, where available, a worked example.

#### `ml-query-data-profile`

Profile values on a data source. For numeric fields returns min/max plus the bucketing strategy used; 

**Call:** `execute_ml-query-data-profile`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_ml_query_data_profile (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_ml-query-data-profile) for the param schema and, where available, a worked example.

#### `ml-query-outcome`

List candidate outcome columns (Binary, Discrete, Continuous) in the data source. 

**Call:** `execute_ml-query-outcome`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_ml_query_outcome (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_ml-query-outcome) for the param schema and, where available, a worked example.

#### `ml-query-row-count`

Row count for the data source after filters and joins are applied. 

**Call:** `execute_ml-query-row-count`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_ml_query_row_count (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_ml-query-row-count) for the param schema and, where available, a worked example.

#### `ml-query-setup-fields`

Enumerate fields and applicable transformations for a data source. 

**Call:** `execute_ml-query-setup-fields`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_ml_query_setup_fields (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_ml-query-setup-fields) for the param schema and, where available, a worked example.

#### `ml-setup-version-get`

Get a specific setup version by id. Container can be referenced by api name or id; versionId must always be an id.

**Call:** `execute_ml-setup-version-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_ml_setup_version_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_ml-setup-version-get) for the param schema and, where available, a worked example.

#### `ml-setup-version-inspector-metrics-get`

Training-time inspector metrics for a setup version. Returns AUC, gini, MCC, MSE, RMSE, 100-threshold confusion matrices, gain table, outcome distribution. gauges is a comma-separated subset of: All, Overview, GainTable, Residuals, Correlations, FeatureImportances, Coefficients, DataSegments, CrossValidations, OutcomeDistribution, PairwiseCorrelations. Defaults to 'Overview' if omitted.

**Call:** `execute_ml-setup-version-inspector-metrics-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_ml_setup_version_inspector_metrics_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_ml-setup-version-inspector-metrics-get) for the param schema and, where available, a worked example.

#### `ml-setup-version-list`

List versions of a model setup. Use active=true to return only the active (published) version.

**Call:** `execute_ml-setup-version-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_ml_setup_version_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_ml-setup-version-list) for the param schema and, where available, a worked example.

#### `prediction-job-def-get`

Get a prediction job definition by id or developer name.

**Call:** `execute_prediction-job-def-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_prediction_job_def_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_prediction-job-def-get) for the param schema and, where available, a worked example.

#### `prediction-job-def-list`

List prediction job definitions. Optional modelId filter narrows the list to definitions for a specific configured model.

**Call:** `execute_prediction-job-def-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_prediction_job_def_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_prediction-job-def-list) for the param schema and, where available, a worked example.

#### `retriever-config-get`

Get one configuration version of a retriever by version ID or API name. Returns query type, query template definition, 

**Call:** `execute_retriever-config-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_retriever_config_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_retriever-config-get) for the param schema and, where available, a worked example.

#### `retriever-config-list`

List all configuration versions of one retriever as a paginated collection (by retriever ID or API name). Each version 

**Call:** `execute_retriever-config-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_retriever_config_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_retriever-config-list) for the param schema and, where available, a worked example.

#### `retriever-get`

Get one RAG retriever by ID or API name, with its latest and active configurations — query type, query template 

**Call:** `execute_retriever-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_retriever_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_retriever-get) for the param schema and, where available, a worked example.

#### `retriever-integrations-get`

Returns the identified entities that reference this retriever, grouped by reference type. A retriever with references can not be deleted, deactivated, or activated to a new version with input incompatible changes. 

**Call:** `execute_retriever-integrations-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_retriever_integrations_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_retriever-integrations-get) for the param schema and, where available, a worked example.

#### `retriever-list`

List RAG retrievers as a paginated collection, each with its latest and active configuration. Out-of-the-box 

**Call:** `execute_retriever-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_retriever_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_retriever-list) for the param schema and, where available, a worked example.

#### `retriever-review`

Review a CustomSql retriever definition BEFORE creating or updating its version — CustomSql only. Pass retrieverInput 

**Call:** `execute_retriever-review`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_retriever_review (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_retriever-review) for the param schema and, where available, a worked example.

### Write operations

#### `ml-alert-update`

Triage a data alert. accepted=true flags the alert's directives for auto-application on the 

**Call:** `execute_ml-alert-update`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_ml_alert_update (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_ml-alert-update) for the param schema and, where available, a worked example.

#### `ml-configured-model-activate`

Activate a configured model (sets status=Enabled). Required before model can be used for inference.

**Call:** `execute_ml-configured-model-activate`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_ml_configured_model_activate (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_ml-configured-model-activate) for the param schema and, where available, a worked example.

#### `ml-configured-model-create`

Create a configured model wrapping an existing model artifact. The artifact reference is REQUIRED — 

**Call:** `execute_ml-configured-model-create`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_ml_configured_model_create (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_ml-configured-model-create) for the param schema and, where available, a worked example.

#### `ml-configured-model-update`

Update a configured model. Partial update — send only fields you want to change. 

**Call:** `execute_ml-configured-model-update`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_ml_configured_model_update (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_ml-configured-model-update) for the param schema and, where available, a worked example.

#### `ml-model-artifact-update`

Update a model artifact. Partial update. PATCH blocked on OOTB. Status accepts only Enabled/Disabled — Draft/Deprecated/Rerouted are rejected. featureOverrideValues are upsert-by-sourceValue.

**Call:** `execute_ml-model-artifact-update`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_ml_model_artifact_update (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_ml-model-artifact-update) for the param schema and, where available, a worked example.

#### `ml-model-setup-create`

Create a model-setup container (the parent record that groups setup versions). 

**Call:** `execute_ml-model-setup-create`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_ml_model_setup_create (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_ml-model-setup-create) for the param schema and, where available, a worked example.

#### `ml-model-setup-update`

Update a model-setup container. Partial update — send only fields you want to change.

**Call:** `execute_ml-model-setup-update`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_ml_model_setup_update (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_ml-model-setup-update) for the param schema and, where available, a worked example.

#### `ml-setup-version-create`

Author a new setup version on an existing container. 

**Call:** `execute_ml-setup-version-create`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_ml_setup_version_create (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_ml-setup-version-create) for the param schema and, where available, a worked example.

#### `ml-setup-version-update`

Update a setup version. Driver for the training lifecycle: setting status=Training kicks off the training run. Container can be referenced by api name or id; versionId must always be an id.

**Call:** `execute_ml-setup-version-update`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_ml_setup_version_update (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_ml-setup-version-update) for the param schema and, where available, a worked example.

#### `prediction-job-def-activate`

Activate a prediction job definition (sets activationStatus=Active). A definition must be Active before it can be submitted via d360_prediction_job_run.

**Call:** `execute_prediction-job-def-activate`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_prediction_job_def_activate (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_prediction-job-def-activate) for the param schema and, where available, a worked example.

#### `prediction-job-def-create`

Create a prediction job definition (generic). 

**Call:** `execute_prediction-job-def-create`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_prediction_job_def_create (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_prediction-job-def-create) for the param schema and, where available, a worked example.

#### `prediction-job-def-create-binary-classification`

Create a BinaryClassification prediction job definition. Required: apiName, model (binary-classification-trained), inputDataObject, fields, outputObjectName. binaryClassificationSettings ranges enforced server-side: maxTopContributors 0-3, maxPrescriptions 0-3, prescriptionThreshold 0-100. showClassProbabilities defaults to true.

**Call:** `execute_prediction-job-def-create-binary-classification`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_prediction_job_def_create_binary_classification (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_prediction-job-def-create-binary-classification) for the param schema and, where available, a worked example.

#### `prediction-job-def-create-clustering`

Create a Clustering prediction job definition. Required: apiName, model (clustering-trained), inputDataObject, fields, outputObjectName, and clusteringSettings with clusterIdFieldLabel + clusterLabelFieldLabel. Optional: maxTopContributors 0-3.

**Call:** `execute_prediction-job-def-create-clustering`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_prediction_job_def_create_clustering (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_prediction-job-def-create-clustering) for the param schema and, where available, a worked example.

#### `prediction-job-def-create-multiclass-classification`

Create a MulticlassClassification prediction job definition. Required: apiName, model (multiclass-classification-trained), inputDataObject, fields, outputObjectName. multiclassClassificationSettings: maxTopContributors 0-3, numberOfClasses ≥ 1 (default = all classes).

**Call:** `execute_prediction-job-def-create-multiclass-classification`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_prediction_job_def_create_multiclass_classification (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_prediction-job-def-create-multiclass-classification) for the param schema and, where available, a worked example.

#### `prediction-job-def-create-regression`

Create a Regression prediction job definition. Required: apiName, model (regression-trained), inputDataObject, fields (feature→DMO mappings), outputObjectName. regressionSettings ranges enforced server-side: maxTopContributors 0-3, maxPrescriptions 0-3, prescriptionThreshold 0-100. scoringMode defaults to Batch.

**Call:** `execute_prediction-job-def-create-regression`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_prediction_job_def_create_regression (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_prediction-job-def-create-regression) for the param schema and, where available, a worked example.

#### `prediction-job-def-create-sentiment-detection`

Create a SentimentDetection prediction job definition. Required: apiName, inputDataObject, textFields (up to 3), outputObjectName. model defaults to a reference by name to 'sfdc_ai__DefaultSalesforceSentimentAnalysis' when omitted. scoringMode defaults to Batch.

**Call:** `execute_prediction-job-def-create-sentiment-detection`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_prediction_job_def_create_sentiment_detection (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_prediction-job-def-create-sentiment-detection) for the param schema and, where available, a worked example.

#### `prediction-job-def-create-topic-classification`

Create a TopicClassification prediction job definition. Required: apiName, inputDataObject, textFields (up to 3), topicLabels (2-5 distinct, each ≤ 100 chars), outputObjectName. model defaults to a reference by name to 'sfdc_ai__DefaultSalesforceTopicClassification' when omitted. scoringMode defaults to Batch.

**Call:** `execute_prediction-job-def-create-topic-classification`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_prediction_job_def_create_topic_classification (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_prediction-job-def-create-topic-classification) for the param schema and, where available, a worked example.

#### `prediction-job-def-deactivate`

Deactivate a prediction job definition (sets activationStatus=Inactive). Inactive definitions cannot be run.

**Call:** `execute_prediction-job-def-deactivate`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_prediction_job_def_deactivate (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_prediction-job-def-deactivate) for the param schema and, where available, a worked example.

#### `prediction-job-def-update`

Update a prediction job definition. Partial-update semantics: send only the fields you want to change. 

**Call:** `execute_prediction-job-def-update`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_prediction_job_def_update (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_prediction-job-def-update) for the param schema and, where available, a worked example.

#### `prediction-job-run`

Submit a prediction job for execution. Async — the response carries a job id and an initial status. 

**Call:** `execute_prediction-job-run`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_prediction_job_run (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_prediction-job-run) for the param schema and, where available, a worked example.

#### `retriever-config-create-custom-sql`

Add a new CustomSql configuration version to an EXISTING retriever (by retriever ID or API name). Pick this flavor to run a user-authored Data 360 SQL query (DMO/DLO/CalculatedInsight, or vector_search()/hybrid_search()). Call d360_retriever_review on the definition first. Required in customSqlConfiguration: retrieverQueryTemplateDefinition (retrieverQueryTemplate SQL plus its queryTemplatePlaceholders). Optional: numberOfResults (default 10); isActive (at most one version active per retriever); isCitationSupported (true requires queryCitationDefinition); isEnrichedIndexSupported (true requires enrichedSearchIndexDefinition). queryType is fixed to CustomSql by this tool. To create the retriever itself, use d360_retriever_create_custom_sql.

**Call:** `execute_retriever-config-create-custom-sql`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_retriever_config_create_custom_sql (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_retriever-config-create-custom-sql) for the param schema and, where available, a worked example.

#### `retriever-config-create-ensemble`

Add a new Ensemble configuration version to an EXISTING retriever (by retriever ID or API name). Pick this flavor to fan out to multiple existing NoCode sub-retrievers and combine their results with reranking. Required in ensembleConfiguration: referencedRetrievers (references, by ID or API name, to existing NoCode retrievers). Optional: outputFields (labels to project; must match the sub-retrievers' output field labels; defaults to their union); numberOfResults (default 10); isActive (at most one version active per retriever). queryType is fixed to Ensemble by this tool. To create the retriever itself, use d360_retriever_create_ensemble.

**Call:** `execute_retriever-config-create-ensemble`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_retriever_config_create_ensemble (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_retriever-config-create-ensemble) for the param schema and, where available, a worked example.

#### `retriever-config-create-no-code`

Add a new NoCode configuration version to an EXISTING retriever (by retriever ID or API name). Pick this flavor to retrieve from a Data 360 search index without hand-written SQL. Required in noCodeConfiguration: input (search index ID or API name) and outputFields (DMO fields to return). Optional: numberOfResults (positive integer, default 10); isActive (activate this version on create — deactivates any other active version); queryFilter (search index pre-filter expression); citationConfiguration. queryType is fixed to NoCode by this tool. To create a new retriever itself, use d360_retriever_create_no_code.

**Call:** `execute_retriever-config-create-no-code`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_retriever_config_create_no_code (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_retriever-config-create-no-code) for the param schema and, where available, a worked example.

#### `retriever-config-update`

Activate or deactivate a retriever configuration version by version ID or API name. Set isActive=true to activate this 

**Call:** `execute_retriever-config-update`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_retriever_config_update (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_retriever-config-update) for the param schema and, where available, a worked example.

#### `retriever-create-custom-sql`

Create a new CustomSql RAG retriever — the retriever plus its initial CustomSql configuration in one call. Pick this flavor to run a user-authored Data 360 SQL query (DMO/DLO/CalculatedInsight, or the vector_search()/hybrid_search() functions). Call d360_retriever_review on the definition first to check errors and suggestions. Required: label; dataSpaces (required for CustomSql, only one data space is allowed); and customSqlConfiguration with retrieverQueryTemplateDefinition (retrieverQueryTemplate SQL plus its queryTemplatePlaceholders). Optional: description (highly recommended to set a detailed description to explain this retriever's purpose and behavior. This helps AI agent to discover and understand this retriever); numberOfResults (default 10); isActive; isCitationSupported (when true, queryCitationDefinition is required); isEnrichedIndexSupported (when true, enrichedSearchIndexDefinition is required). queryType is fixed to CustomSql by this tool. The response returns the retriever's id and name, and optionally namespace; the fully qualified API name is namespace__name when namespace is present, otherwise name. Use that API name (or id) to reference the retriever in later requests.

**Call:** `execute_retriever-create-custom-sql`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_retriever_create_custom_sql (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_retriever-create-custom-sql) for the param schema and, where available, a worked example.

#### `retriever-create-ensemble`

Create a new Ensemble RAG retriever — the retriever plus its initial Ensemble configuration in one call. Pick this flavor to fan out to multiple existing NoCode sub-retrievers and combine their results with reranking. Required: label; and ensembleConfiguration with referencedRetrievers (references, by ID or API name, to existing NoCode retrievers). Do NOT set dataSpaces — for Ensemble they are derived from the referenced retrievers. Optional: description (highly recommended to set a detailed description to explain this retriever's purpose and behavior. This helps AI agent to discover and understand this retriever); outputFields (labels to project; must match the sub-retrievers' output field labels; defaults to their union); numberOfResults (default 10); isActive. queryType is fixed to Ensemble by this tool. The response returns the retriever's id and name, and optionally namespace; the fully qualified API name is namespace__name when namespace is present, otherwise name. Use that API name (or id) to reference the retriever in laster requests.

**Call:** `execute_retriever-create-ensemble`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_retriever_create_ensemble (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_retriever-create-ensemble) for the param schema and, where available, a worked example.

#### `retriever-create-no-code`

Create a new NoCode RAG retriever — the retriever plus its initial NoCode configuration in one call. Pick this flavor to retrieve from a Data 360 search index WITHOUT hand-written SQL; the SQL query template is generated for you. First call d360_search_index_list to find the search index. Required: label; dataSpaces (required for NoCode, only one data space is allowed); and noCodeConfiguration with input (the search index ID or API name) and outputFields (the DMO fields to return). Optional: description (highly recommended to set a detailed description to explain this retriever's purpose and behavior. This helps AI agent to discover and understand this retriever); numberOfResults (positive integer, default 10); isActive (activate this version on create); queryFilter (pre-filter conditions on search-index prefilter fields); citationConfiguration for default or custom citations. queryType is fixed to NoCode by this tool. The response returns the retriever's id and name, and optionally namespace; the fully qualified API name is namespace__name when namespace is present, otherwise name. Use that API name (or id) to reference the retriever in laster requests.

**Call:** `execute_retriever-create-no-code`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_retriever_create_no_code (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_retriever-create-no-code) for the param schema and, where available, a worked example.

#### `retriever-update`

Update a retriever's label and/or description by ID or API name. This does NOT change retrieval behavior — to change 

**Call:** `execute_retriever-update`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_retriever_update (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_retriever-update) for the param schema and, where available, a worked example.

### Destructive operations

#### `ml-configured-model-delete`

Delete a configured model.

**Call:** `execute_ml-configured-model-delete`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_ml_configured_model_delete (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_ml-configured-model-delete) for the param schema and, where available, a worked example.

#### `ml-model-artifact-delete`

Delete a model artifact.

**Call:** `execute_ml-model-artifact-delete`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_ml_model_artifact_delete (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_ml-model-artifact-delete) for the param schema and, where available, a worked example.

#### `ml-model-setup-delete`

Delete a model-setup container. Cascades to all versions. Irreversible.

**Call:** `execute_ml-model-setup-delete`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_ml_model_setup_delete (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_ml-model-setup-delete) for the param schema and, where available, a worked example.

#### `prediction-job-def-delete`

Delete a prediction job definition. Irreversible.

**Call:** `execute_prediction-job-def-delete`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_prediction_job_def_delete (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_prediction-job-def-delete) for the param schema and, where available, a worked example.

#### `retriever-config-delete`

Delete one configuration version of a retriever by version ID or API name. The active version cannot be deleted — 

**Call:** `execute_retriever-config-delete`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_retriever_config_delete (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_retriever-config-delete) for the param schema and, where available, a worked example.

#### `retriever-delete`

Delete a retriever by ID or API name, including all of its configuration versions. This is irreversible. The retriever 

**Call:** `execute_retriever-delete`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_retriever_delete (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_retriever-delete) for the param schema and, where available, a worked example.
