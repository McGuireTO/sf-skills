---
name: experience-schema-builder-open
description: "Use this skill when users want to schema Builder is a UI-only Setup page that visualizes the org's data model (objects, fields, relationships). Trigger when users mention schema, builder, schema builder."
metadata:
  version: "1.0"
---

# Querying Schema Builder

## When to Use This Skill

Schema Builder is a UI-only Setup page that visualizes the org's data model (objects, fields, relationships). No public Connect/Tooling/Metadata API exposes this visualization; the underlying schema CRUD lives in peer SORs (CustomObjects, CustomFields). Open view_url for manual use. Requires Customize Application permission.

## Critical Constraints

**Preconditions:**

- The running user must have the Customize Application permission; Schema Builder access is gated on it. (check: `The running user has the Customize Application permission.`)
- Setup UI must not be restricted for the running user (a license-restricted Setup UI suppresses Schema Builder). (check: `Setup UI is not restricted for the running user.`)
- The running user must not be a delegated administrator acting in system-administrator mode; the access gate denies Schema Builder access while that mode is active. (check: `The running user is not a delegated administrator acting in system-administrator mode.`)

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `view_SchemaBuilder_1` | read | — | `SchemaBuilder.view` | — |

### Read operations

#### `view_SchemaBuilder_1`

Open the Schema Builder app at view_url for manual use. The same URL is also returned by the Aura helper getSchemaBuilderUrl (GET /headless/invoke/platform/objectmanager-setup/schema-builder-link/get-schema-builder-url) — calling it just round-trips the value already in view_url, so this step prefers the static value.

**Call:** `SchemaBuilder.view`
