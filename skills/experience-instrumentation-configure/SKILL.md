---
name: experience-instrumentation-configure
description: "Use this skill when users want to provides client-side instrumentation infrastructure for the Salesforce Lightning platform. Trigger when users mention wizard, ui, instrumentation, components."
metadata:
  version: "1.0"
---

# Managing Wizard Ui Instrumentation Components

## When to Use This Skill

Provides client-side instrumentation infrastructure for the Salesforce Lightning platform. This module handles Avro schema retrieval for AILTN (Application Instrumentation and Logging Telemetry Network) event validation, beacon-based telemetry dispatch (locator resolution and data transmission), and LEX engagement status tracking. An agent would invoke this SOR when diagnosing or orchestrating client telemetry pipelines, validating instrumentation schemas, or managing user engagement state in Lightning Experience.

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `avro-validator-controller-get-ailtn-schemas` | read | implemented | `GET /headless/invoke/platform/instrumentation/avro-validator/get-ailtn-schemas` | — |
| `instrumentation-beacon-controller-get-locators` | read | implemented | `GET /headless/invoke/platform/instrumentation/instrumentation-beacon/get-locators` | — |
| `instrumentation-beacon-controller-send-data` | write | implemented | `PATCH /headless/invoke/platform/instrumentation/instrumentation-beacon/send-data` | `instrumentation-beacon-controller-get-locators` |
| `lex-engagement-controller-get-initial-status` | read | implemented | `GET /headless/invoke/platform/agentforce-setup-beta` | — |
| `lex-engagement-controller-handle-status-change` | write | implemented | `PATCH /headless/invoke/platform/agentforce-setup-beta/handle-status-change` | `lex-engagement-controller-get-initial-status` |

### Read operations

#### `avro-validator-controller-get-ailtn-schemas`

Fetches the set of Avro schemas used to validate AILTN telemetry events on the client side. These schemas define the expected structure of instrumentation payloads before they are serialized and transmitted.

**Call:** `GET /headless/invoke/platform/instrumentation/avro-validator/get-ailtn-schemas`   — status: `implemented`

#### `instrumentation-beacon-controller-get-locators`

Retrieves the list of beacon locators (endpoint identifiers) that the client instrumentation framework uses to determine where telemetry data should be sent.

**Call:** `GET /headless/invoke/platform/instrumentation/instrumentation-beacon/get-locators`   — status: `implemented`

#### `lex-engagement-controller-get-initial-status`

Reads the current engagement status for the Lightning Experience session. This provides the baseline state (e.g., active, idle, or dismissed) that the UI uses to decide whether to show engagement prompts.

**Call:** `GET /headless/invoke/platform/agentforce-setup-beta`   — status: `implemented`

### Write operations

#### `instrumentation-beacon-controller-send-data`

Transmits collected telemetry data to the server via the instrumentation beacon endpoint. Requires locators to have been resolved first so the payload is routed correctly.

**Call:** `PATCH /headless/invoke/platform/instrumentation/instrumentation-beacon/send-data`   — status: `implemented`

**Depends on:** `instrumentation-beacon-controller-get-locators`

#### `lex-engagement-controller-handle-status-change`

Persists a change in the user's LEX engagement status (e.g., transitioning from active to dismissed). Typically invoked after the initial status has been read and the user or system triggers a state transition. Source: output of lex-engagement-controller-get-initial-status provides the baseline state that informs valid transitions.

**Call:** `PATCH /headless/invoke/platform/agentforce-setup-beta/handle-status-change`   — status: `implemented`

**Depends on:** `lex-engagement-controller-get-initial-status`
