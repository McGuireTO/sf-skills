---
name: data360-activation-v2-create
description: "Use this skill when users want to execute Data Cloud ActivationV2 operations via the Data 360 MCP facade. Trigger when users mention data360/activation, v2, shared, cdp, mcp, connect, api, shared-cdp-mcp-connect-api."
metadata:
  version: "1.0"
---

# Managing Data360/activation V2

## When to Use This Skill

Execute Data Cloud ActivationV2 operations via the Data 360 MCP facade.

## Workflow

Each step lists an `operation` id. Call describe(<operation>) BEFORE dispatching to get that tool's parameter schema and, where available, a worked example. `paramsJson` decodes to the operation's requestBody schema VERBATIM, including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap or omit it. The only envelope the step handles for you is `{toolName, paramsJson}` (its `invocation` already wraps it); do not POST the operation path directly. If the tool's error suggests `payload_examples`, ignore it — that tool isn't available here; call describe(<operation>) instead.

## Critical Constraints

**Destructive operations — require explicit user confirmation:**

- **`activation-platform-delete`** — Delete an Activation Platform. Fails with 412 if the platform is still referenced by activation targets or market segment activations — unlink or delete those first.
  - Rollback: No automatic rollback.

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `activation-channel-list` | read | implemented | `execute_activation-channel-list` | — |
| `activation-channel-preference-list` | read | implemented | `execute_activation-channel-preference-list` | — |
| `activation-consent-dmo-get` | read | implemented | `execute_activation-consent-dmo-get` | — |
| `activation-data-object-category-list` | read | implemented | `execute_activation-data-object-category-list` | — |
| `activation-data-source-list` | read | implemented | `execute_activation-data-source-list` | — |
| `activation-disable` | write | implemented | `execute_activation-disable` | — |
| `activation-enable` | write | implemented | `execute_activation-enable` | — |
| `activation-full-refresh-trigger` | write | implemented | `execute_activation-full-refresh-trigger` | — |
| `activation-history-list` | read | implemented | `execute_activation-history-list` | — |
| `activation-match-boost-identity-provider-list` | read | implemented | `execute_activation-match-boost-identity-provider-list` | — |
| `activation-platform-action-source-list` | read | implemented | `execute_activation-platform-action-source-list` | — |
| `activation-platform-create` | write | implemented | `execute_activation-platform-create` | — |
| `activation-platform-delete` | delete | implemented | `execute_activation-platform-delete` | — |
| `activation-platform-disable` | write | implemented | `execute_activation-platform-disable` | — |
| `activation-platform-enable` | write | implemented | `execute_activation-platform-enable` | — |
| `activation-platform-event-list` | read | implemented | `execute_activation-platform-event-list` | — |
| `activation-platform-get` | read | implemented | `execute_activation-platform-get` | — |
| `activation-platform-list` | read | implemented | `execute_activation-platform-list` | — |
| `activation-platform-partner-object-type-list` | read | implemented | `execute_activation-platform-partner-object-type-list` | — |
| `activation-platform-privacy-type-set` | write | implemented | `execute_activation-platform-privacy-type-set` | — |
| `activation-platform-publish` | write | implemented | `execute_activation-platform-publish` | — |
| `activation-platform-sync-retry` | write | implemented | `execute_activation-platform-sync-retry` | — |
| `activation-platform-update` | write | implemented | `execute_activation-platform-update` | — |
| `activation-related-attribute-limit-get` | read | implemented | `execute_activation-related-attribute-limit-get` | — |
| `activation-related-attribute-quota-get` | read | implemented | `execute_activation-related-attribute-quota-get` | — |
| `activation-streaming-eligibility-get` | read | implemented | `execute_activation-streaming-eligibility-get` | — |
| `activation-sync-retry` | write | implemented | `execute_activation-sync-retry` | — |
| `activation-target-ad-account-assign` | write | implemented | `execute_activation-target-ad-account-assign` | — |
| `activation-target-ad-account-list` | read | implemented | `execute_activation-target-ad-account-list` | — |
| `activation-target-capping-dataspace-list` | read | implemented | `execute_activation-target-capping-dataspace-list` | — |
| `activation-target-dataspace-account-validate` | read | implemented | `execute_activation-target-dataspace-account-validate` | — |
| `activation-target-disable` | write | implemented | `execute_activation-target-disable` | — |
| `activation-target-enable` | write | implemented | `execute_activation-target-enable` | — |
| `activation-target-mc-enterprise-list` | read | implemented | `execute_activation-target-mc-enterprise-list` | — |
| `activation-target-partner-object-list` | read | implemented | `execute_activation-target-partner-object-list` | — |
| `activation-target-platform-field-list` | read | implemented | `execute_activation-target-platform-field-list` | — |
| `activation-target-platform-list` | read | implemented | `execute_activation-target-platform-list` | — |
| `activation-target-sync-retry` | write | implemented | `execute_activation-target-sync-retry` | — |

### Read operations

#### `activation-channel-list`

List available activation channels (Email, Phone, Push, Whatsapp, DigitalId) and their backing Data Model Objects for a data space and activate-on DMO.

**Call:** `execute_activation-channel-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_activation_channel_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_activation-channel-list) for the param schema and, where available, a worked example.

#### `activation-channel-preference-list`

List channel preference options (e.g. Primary, Secondary) for a channel/Data Model Object pair, used to select which contact point type to activate on.

**Call:** `execute_activation-channel-preference-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_activation_channel_preference_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_activation-channel-preference-list) for the param schema and, where available, a worked example.

#### `activation-consent-dmo-get`

Get the standard consent data model objects (ContactPointConsent, CommunicationSubscriptionConsent) for a data space and activate-on DMO.

**Call:** `execute_activation-consent-dmo-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_activation_consent_dmo_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_activation-consent-dmo-get) for the param schema and, where available, a worked example.

#### `activation-data-object-category-list`

List data object category types that can be activated (e.g. PROFILE, ENGAGEMENT, OTHER), optionally scoped to a data space.

**Call:** `execute_activation-data-object-category-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_activation_data_object_category_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_activation-data-object-category-list) for the param schema and, where available, a worked example.

#### `activation-data-source-list`

List available data sources for a Data Model Object, optionally filtered by channel. Data space context is derived from the Data Model Object.

**Call:** `execute_activation-data-source-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_activation_data_source_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_activation-data-source-list) for the param schema and, where available, a worked example.

#### `activation-history-list`

List paginated publish history for a Market Segment Activation, or for all activations under a Market Segment (the service routes based on the supplied id's entity key prefix).

**Call:** `execute_activation-history-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_activation_history_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_activation-history-list) for the param schema and, where available, a worked example.

#### `activation-match-boost-identity-provider-list`

List identity providers eligible for match-boost on a given activation target and Data Model Object.

**Call:** `execute_activation-match-boost-identity-provider-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_activation_match_boost_identity_provider_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_activation-match-boost-identity-provider-list) for the param schema and, where available, a worked example.

#### `activation-platform-action-source-list`

List action sources valid for a given event on a streaming activation platform (e.g. Website, App, Offline). Get the event name from d360_activation_platform_event_list first.

**Call:** `execute_activation-platform-action-source-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_activation_platform_action_source_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_activation-platform-action-source-list) for the param schema and, where available, a worked example.

#### `activation-platform-event-list`

List the standard event names configured on a streaming activation platform (e.g. Purchase, AddToCart). Use the event name with d360_activation_platform_action_source_list to discover valid action sources.

**Call:** `execute_activation-platform-event-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_activation_platform_event_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_activation-platform-event-list) for the param schema and, where available, a worked example.

#### `activation-platform-get`

Get a single Activation Platform by ID or API name.

**Call:** `execute_activation-platform-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_activation_platform_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_activation-platform-get) for the param schema and, where available, a worked example.

#### `activation-platform-list`

List Activation Platforms with pagination. Use d360_activation_platform_get to fetch a single platform's full details.

**Call:** `execute_activation-platform-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_activation_platform_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_activation-platform-list) for the param schema and, where available, a worked example.

#### `activation-platform-partner-object-type-list`

List partner-object types supported by a streaming activation platform (e.g. Pixel, App, CrmEventSet, OfflineEventSet, MobileApp, ConversionRule). Each type feeds d360_activation_target_partner_object_list's type filter.

**Call:** `execute_activation-platform-partner-object-type-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_activation_platform_partner_object_type_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_activation-platform-partner-object-type-list) for the param schema and, where available, a worked example.

#### `activation-related-attribute-limit-get`

Get the static configuration limits (max hops, attributes per activation, etc.) for related-attribute activations.

**Call:** `execute_activation-related-attribute-limit-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_activation_related_attribute_limit_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_activation-related-attribute-limit-get) for the param schema and, where available, a worked example.

#### `activation-related-attribute-quota-get`

Get the org-wide quota for related-attribute activations (current usage vs max allowed). Optionally excludes one activation from the current count for edit flows.

**Call:** `execute_activation-related-attribute-quota-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_activation_related_attribute_quota_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_activation-related-attribute-quota-get) for the param schema and, where available, a worked example.

#### `activation-streaming-eligibility-get`

Check whether streaming activation is allowed for a given Data Model Object, and return the reason when it is not.

**Call:** `execute_activation-streaming-eligibility-get`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_activation_streaming_eligibility_get (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_activation-streaming-eligibility-get) for the param schema and, where available, a worked example.

#### `activation-target-ad-account-list`

List ad accounts for a platform that are not already assigned in the specified data space, for a given activation target.

**Call:** `execute_activation-target-ad-account-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_activation_target_ad_account_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_activation-target-ad-account-list) for the param schema and, where available, a worked example.

#### `activation-target-capping-dataspace-list`

List data spaces that have communication-capping configurations linked to activation targets, across the org.

**Call:** `execute_activation-target-capping-dataspace-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_activation_target_capping_dataspace_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_activation-target-capping-dataspace-list) for the param schema and, where available, a worked example.

#### `activation-target-dataspace-account-validate`

Check whether a given ad account is available (not already assigned) in the specified data space for a platform.

**Call:** `execute_activation-target-dataspace-account-validate`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_activation_target_dataspace_account_validate (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_activation-target-dataspace-account-validate) for the param schema and, where available, a worked example.

#### `activation-target-mc-enterprise-list`

List Marketing Cloud enterprises with their business units (EIDs and BUs) for the connected org.

**Call:** `execute_activation-target-mc-enterprise-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_activation_target_mc_enterprise_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_activation-target-mc-enterprise-list) for the param schema and, where available, a worked example.

#### `activation-target-partner-object-list`

List partner-platform objects (conversion rules, pixels, apps, event sets) of a given type for a CAPI or strategic activation target. Cursor-paginated — follow nextPageUrl rather than constructing pageToken.

**Call:** `execute_activation-target-partner-object-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_activation_target_partner_object_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_activation-target-partner-object-list) for the param schema and, where available, a worked example.

#### `activation-target-platform-field-list`

List target-level configuration fields exposed by an activation platform (e.g. account number).

**Call:** `execute_activation-target-platform-field-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_activation_target_platform_field_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_activation-target-platform-field-list) for the param schema and, where available, a worked example.

#### `activation-target-platform-list`

List activation platforms available for creating activation targets, optionally filtered by platform type or name.

**Call:** `execute_activation-target-platform-list`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_activation_target_platform_list (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_activation-target-platform-list) for the param schema and, where available, a worked example.

### Write operations

#### `activation-disable`

Disable a Market Segment Activation by id. Stops future publishes until re-enabled.

**Call:** `execute_activation-disable`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_activation_disable (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_activation-disable) for the param schema and, where available, a worked example.

#### `activation-enable`

Enable a Market Segment Activation by id. Publishing resumes on the activation's configured schedule.

**Call:** `execute_activation-enable`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_activation_enable (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_activation-enable) for the param schema and, where available, a worked example.

#### `activation-full-refresh-trigger`

Trigger an on-demand full-refresh publish for a Market Segment Activation. Subject to a 24-hour publish-limit; fails with 400 if exceeded.

**Call:** `execute_activation-full-refresh-trigger`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_activation_full_refresh_trigger (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_activation-full-refresh-trigger) for the param schema and, where available, a worked example.

#### `activation-platform-create`

Create a new Activation Platform from structured input (name, label, description, platformType, outputFormat, outputGrouping, refreshSettings required). Returns the created platform including its assigned ID.

**Call:** `execute_activation-platform-create`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_activation_platform_create (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_activation-platform-create) for the param schema and, where available, a worked example.

#### `activation-platform-disable`

Disable an Activation Platform.

**Call:** `execute_activation-platform-disable`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_activation_platform_disable (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_activation-platform-disable) for the param schema and, where available, a worked example.

#### `activation-platform-enable`

Enable an Activation Platform.

**Call:** `execute_activation-platform-enable`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_activation_platform_enable (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_activation-platform-enable) for the param schema and, where available, a worked example.

#### `activation-platform-privacy-type-set`

Set the privacy type classification (ThirdParty, ServiceProvider, UpdateFailed, NotApplicable) for an Activation Platform.

**Call:** `execute_activation-platform-privacy-type-set`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_activation_platform_privacy_type_set (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_activation-platform-privacy-type-set) for the param schema and, where available, a worked example.

#### `activation-platform-publish`

Publish an Activation Platform, changing its status to active. Fails with 400 if the platform is not in a publishable state.

**Call:** `execute_activation-platform-publish`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_activation_platform_publish (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_activation-platform-publish) for the param schema and, where available, a worked example.

#### `activation-platform-sync-retry`

Retry the sync operation for an Activation Platform that previously failed. Runs asynchronously.

**Call:** `execute_activation-platform-sync-retry`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_activation_platform_sync_retry (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_activation-platform-sync-retry) for the param schema and, where available, a worked example.

#### `activation-platform-update`

Partially update an Activation Platform by ID or API name. Only provided fields are modified; list-valued fields (fields, identifiers, activationPlatformAttributes) replace the full set when supplied.

**Call:** `execute_activation-platform-update`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_activation_platform_update (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_activation-platform-update) for the param schema and, where available, a worked example.

#### `activation-sync-retry`

Retry the sync for a Market Segment Activation that previously failed.

**Call:** `execute_activation-sync-retry`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_activation_sync_retry (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_activation-sync-retry) for the param schema and, where available, a worked example.

#### `activation-target-ad-account-assign`

Assign an ad account to a strategic activation platform target. Use d360_activation_target_ad_account_list first to find an available account.

**Call:** `execute_activation-target-ad-account-assign`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_activation_target_ad_account_assign (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_activation-target-ad-account-assign) for the param schema and, where available, a worked example.

#### `activation-target-disable`

Disable an Activation Target by id. Fails if communication-capping metadata is still present.

**Call:** `execute_activation-target-disable`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_activation_target_disable (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_activation-target-disable) for the param schema and, where available, a worked example.

#### `activation-target-enable`

Enable an Activation Target by id.

**Call:** `execute_activation-target-enable`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_activation_target_enable (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_activation-target-enable) for the param schema and, where available, a worked example.

#### `activation-target-sync-retry`

Retry the sync for an Activation Target that previously failed.

**Call:** `execute_activation-target-sync-retry`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_activation_target_sync_retry (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_activation-target-sync-retry) for the param schema and, where available, a worked example.

### Destructive operations

#### `activation-platform-delete`

Delete an Activation Platform. Fails with 412 if the platform is still referenced by activation targets or market segment activations — unlink or delete those first.

**Call:** `execute_activation-platform-delete`   — status: `implemented`

**Inputs:**

- `paramsJson` *(`string`)* — JSON-encoded params for d360_activation_platform_delete (a STRING, double-encoded). Serialize the operation's requestBody schema VERBATIM including its top-level key (e.g. `input`, `dataTransform`) — do not unwrap it. Call describe(execute_activation-platform-delete) for the param schema and, where available, a worked example.
