---
name: agentforce-wizard-ui-forecasting-analytics-components-configure
description: "Use this skill when users want to einstein Forecasting Prediction Tuner setup (ForecastingPredictive AI application type). Trigger when users mention wizard, ui, forecasting, analytics, components."
metadata:
  version: "1.0"
---

# Managing Wizard Ui Forecasting Analytics Components

## When to Use This Skill

Einstein Forecasting Prediction Tuner setup (ForecastingPredictive AI application type). Three Aura ops — get-tuner-setup-state reads whether the predictor's AI application is provisioned; load-tuner-metadata returns the Opportunity field catalog plus the saved prediction configuration; save-tuner-metadata upserts the prediction configuration and returns the AI application id. All gate on Predictive Forecasting + Customize Application + Modify All Data. No public Connect/Tooling/Metadata alternative — the AI application record is tooling-internal.

## Critical Constraints

**Preconditions:**

- Org has Predictive Forecasting (Einstein Forecasting Prediction) enabled. (check: `Predictive Forecasting enabled`)
- Running user has the Customize Application user permission. (check: `USER_PERMISSION_CUSTOMIZE_APPLICATION`)
- Running user has the Modify All Data user permission. (check: `USER_PERMISSION_MODIFY_ALL_DATA`)

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `forecasting-prediction-tuner-setup-flow-controller-get-tuner-setup-state` | read | implemented | `GET /headless/invoke/analytics/forecasting-analytics/get-tuner-setup-state` | — |
| `forecasting-prediction-tuner-setup-flow-controller-load-tuner-metadata` | read | implemented | `GET /headless/invoke/analytics/forecasting-analytics/load-tuner-metadata` | `forecasting-prediction-tuner-setup-flow-controller-get-tuner-setup-state` |
| `forecasting-prediction-tuner-setup-flow-controller-save-tuner-metadata` | write | implemented | `PATCH /headless/invoke/analytics/forecasting-analytics/save-tuner-metadata` | `forecasting-prediction-tuner-setup-flow-controller-load-tuner-metadata` |

### Read operations

#### `forecasting-prediction-tuner-setup-flow-controller-get-tuner-setup-state`

Read whether the ForecastingPredictive AI application is provisioned. Returns hasAIApplication=true when the AI application exists with a valid id; false blocks downstream tuner steps until upstream Einstein/AI application setup runs.

**Call:** `GET /headless/invoke/analytics/forecasting-analytics/get-tuner-setup-state`   — status: `implemented`

**Output:** A single boolean field hasAIApplication. True when a ForecastingPredictive AI application exists in the org with a valid id; false otherwise.

#### `forecasting-prediction-tuner-setup-flow-controller-load-tuner-metadata`

Load Opportunity custom fields, picklist fields paired with their values (CurrencyIsoCode excluded), the RecordTypeId field with RecordTypeInfo entries when custom record types exist, and the org's saved prediction configuration (null on a fresh org).

**Call:** `GET /headless/invoke/analytics/forecasting-analytics/load-tuner-metadata`   — status: `implemented`

**Depends on:** `forecasting-prediction-tuner-setup-flow-controller-get-tuner-setup-state`

**Output:** Carries availableOppFields (Opportunity custom field list), oppPicklistFieldsAndValues (picklist fields + values plus RecordTypeId+RecordTypeInfo when custom record types exist), and predictionConfig (current saved prediction configuration or null on a fresh org).

### Write operations

#### `forecasting-prediction-tuner-setup-flow-controller-save-tuner-metadata`

Upsert the org's prediction configuration. Accepts a Map<String,Object> under key `predictionConfig`, but the controller first re-serializes it through a string-valued map type — every value is string-coerced — before deserializing into the prediction-config object, so send string-valued fields (e.g. `excludedFields` as a JSON-encoded string, not a native array). Updates when the config carries both AIApplicationId and PredictionDefinitionId, else creates the ForecastingPredictive AI application. Returns the AI application id. Round-trip predictionConfig from the load-tuner-metadata read on partial mutations to preserve unset fields.

**Call:** `PATCH /headless/invoke/analytics/forecasting-analytics/save-tuner-metadata`   — status: `implemented`

**Depends on:** `forecasting-prediction-tuner-setup-flow-controller-load-tuner-metadata`

**Output:** String — the AI application id (aiAppId) of the upserted ForecastingPredictive AI application record. Use as evidence the predictor is now provisioned (a subsequent get-tuner-setup-state read should return hasAIApplication=true).
