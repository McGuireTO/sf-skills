---
name: experience-regenerate-previews-open
description: "Use this skill when users want to navigation-only Setup recipe: invalidate cached ContentDocument preview renditions so the platform regenerates them on next access. Trigger when users mention regenerate, previews, regenerate previews."
metadata:
  version: "1.0"
---

# Managing Regenerate Previews

## When to Use This Skill

Navigation-only Setup recipe: invalidate cached ContentDocument
preview renditions so the platform regenerates them on next
access. Driven via the Setup UI at
/lightning/setup/RegeneratePreviews/home; gated by Customize
Application perm and the Files/Content org features.

No public API exposes this verb. Connect / Tooling / Metadata /
sObject / LDS-GraphQL all eliminate: 0 spec hits across
core-yamls + core-generated-yamls; live-org Tooling probe →
INVALID_TYPE on SOQL and 404 on describe; rendition-cache state
is runtime-only, not Metadata-deployable; setup manifest's
`getRenditionDeleteURL` is a UI URL method, not @AuraEnabled.

The three extractor-emitted steps (list/get/create
RegeneratePreview Tooling sObject) target a fabricated entity
that does NOT exist on the live org. Do not call them. Direct
admins to the Setup page (see navigate_regenerate_previews_setup).

## Critical Constraints

**Preconditions:**

- User has the Customize Application permission and is not in a build-template context. (check: `Customize Application permission`)
- Org has Content/Files enabled (Content, Files Tab, or Content Distributions). (check: `Salesforce CRM Content enabled || Files tab enabled || Content Deliveries enabled`)
- Org is not in deck-assembly mode. (check: `!Deck assembly feature`)

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `list_RegeneratePreview_1` | read | — | `query.RegeneratePreview` | — |
| `get_RegeneratePreview_1` | read | — | `sobjects/RegeneratePreview/{id}` | — |
| `create_RegeneratePreview_1` | write | — | `sobjects/RegeneratePreview` | — |
| `navigate_regenerate_previews_setup` | navigate | — | — | — |
| `gap_no_api_regenerate_previews` | — | — | — | — |

### Read operations

#### `list_RegeneratePreview_1`

DO NOT CALL. Targets a fabricated `RegeneratePreview` Tooling
sObject that does not exist on Salesforce: live-org SOQL returns
400 INVALID_TYPE; tooling describe returns 404. The
rendition-cache state has no API surface; admins use the Setup
page at /lightning/setup/RegeneratePreviews/home instead.

**Call:** `query.RegeneratePreview`

#### `get_RegeneratePreview_1`

DO NOT CALL. Targets a fabricated `RegeneratePreview` Tooling
sObject. Tooling describe returns 404 on
/sobjects/RegeneratePreview/describe. Use the Setup page at
/lightning/setup/RegeneratePreviews/home.

**Call:** `sobjects/RegeneratePreview/{id}`

### Write operations

#### `create_RegeneratePreview_1`

DO NOT CALL. Targets a fabricated `RegeneratePreview` Tooling
sObject; entity does not exist. The underlying admin verb
(delete cached ContentDocument renditions to force
regeneration) is exposed only through the Setup UI URL method
`getRenditionDeleteURL`. Direct admins to
/lightning/setup/RegeneratePreviews/home.

**Call:** `sobjects/RegeneratePreview`

### Other operations

#### `navigate_regenerate_previews_setup`

Open the Regenerate Previews Setup page. The admin clicks the
page action there to invalidate cached ContentDocument
renditions; the platform regenerates them on next access.

#### `gap_no_api_regenerate_previews`
