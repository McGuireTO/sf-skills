---
name: experience-community-theme-definition-list-query
description: "Use this skill when users want to lists Experience Cloud theme definitions (CommunityThemeDefinition metadata type) for the Setup > Networks > Theme Definitions page. Trigger when users mention community, theme, definition, list, community theme definition list."
metadata:
  version: "1.0"
---

# Querying Community Theme Definition List

## When to Use This Skill

Lists Experience Cloud theme definitions (CommunityThemeDefinition metadata type) for the Setup > Networks > Theme Definitions page. Programmatic inventory available via Metadata API listMetadata at /headless/metadata. Edit / create of theme definitions has no public Connect / Aura alternative — agent must open view_url for those flows. Page-access requires the Networks feature (orgHasNetworks || orgHasNetworksEnabledOnce), the org NOT being a Service-SMB Help-Center-only org, and Community templates enabled.

## Critical Constraints

**Preconditions:**

- Experience Cloud (Networks) feature must be enabled on the org — either currently (Experience Cloud sites enabled) or previously enabled at any point (Experience Cloud sites enabled). Without one of these, the Setup page is hidden. (check: `Experience Cloud sites enabled || Experience Cloud sites enabled`)
- Org must NOT be a Service-SMB Help-Center-only org. Help-Center-only Service SMB orgs have a restricted Networks surface that hides the general Theme Definitions list. (check: `!Help Center networks-only mode`)
- Org must have the Community-Template feature license — theme definitions are templated artifacts and require the template entitlement to be visible. (check: `Community templates enabled`)

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `view_CommunityThemeDefinitionList_1` | read | — | `CommunityThemeDefinitionList.view` | — |

### Read operations

#### `view_CommunityThemeDefinitionList_1`

Open Theme Definitions Setup page for manual edit/create/delete of CommunityThemeDefinition. No public Connect/Tooling/Aura covers themeSetting, customThemeLayoutType, defaultBrandingSet, or bundlesInfo mutations.

**Call:** `CommunityThemeDefinitionList.view`
