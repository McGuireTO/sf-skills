---
name: experience-agentforce-vibes-in-react-configure
description: "Use this skill when users want to toggle the Salesforce App Domain org preference so web applications are served from a dedicated salesforce.app domain. Trigger when users mention agentforce, vibes, react, agentforce vibes in react."
metadata:
  version: "1.0"
---

# Managing Agentforce Vibes In React

## When to Use This Skill

Toggle the Salesforce App Domain org preference so web applications are served
from a dedicated salesforce.app domain. This setup page has a single toggle for
the SalesforceAppDomain preference (enable or disable via the Setup Connect API).
The toggle is only visible when the com.salesforce.lwr.salesforceAppDomain gate
is active for the org — if it is not present, the feature is not yet available.

## Critical Constraints

**Preconditions:**

- The com.salesforce.lwr.salesforceAppDomain gate must be active for the org.
Without this gate, the SalesforceAppDomain toggle will not appear on the
Setup page and the preference cannot be set. Verify gate status via
GET /headless/invoke/platform/webapp/is-salesforce-app-domain-gate-enabled
before attempting to enable.

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `isOrgPreferenceEnabled_wire_3` | read | — | `GET /services/data/v67.0/setup/org/preferences/SalesforceAppDomain` | — |
| `setOrgPreferences_1` | write | — | `PATCH /services/data/v67.0/setup/org/preferences/SalesforceAppDomain` | `isOrgPreferenceEnabled_wire_3` |

### Read operations

#### `isOrgPreferenceEnabled_wire_3`

Read the current state of the SalesforceAppDomain org preference via the
Setup Connect API. Returns {isPreferenceEnabled: boolean}. If the endpoint
returns 404 'The requested resource does not exist', the preference resource
is not mounted on this org build. If it returns 404 'Invalid named
preference', the preference name is not registered on IOrgPreferencesResource
for this org/version.

**Call:** `GET /services/data/v67.0/setup/org/preferences/SalesforceAppDomain`

### Write operations

#### `setOrgPreferences_1`

Enable the SalesforceAppDomain org preference via the Setup Connect API.
PATCH the preference resource with body {desiredState: true}. The response
echoes the persisted state as {isPreferenceEnabled: boolean}. A 403 means the
running user lacks permission to modify the preference.

**Call:** `PATCH /services/data/v67.0/setup/org/preferences/SalesforceAppDomain`

**Depends on:** `isOrgPreferenceEnabled_wire_3`
