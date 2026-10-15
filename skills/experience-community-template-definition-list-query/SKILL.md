---
name: experience-community-template-definition-list-query
description: "Use this skill when users want to lists Experience Cloud community templates (Aloha, Build Your Own, Customer Service, Help Center, Partner Central, etc.) available in the org. Trigger when users mention community, template, definition, list, community template definition list."
metadata:
  version: "1.0"
---

# Querying Community Template Definition List

## When to Use This Skill

Lists Experience Cloud community templates (Aloha, Build Your Own, Customer Service, Help Center, Partner Central, etc.) available in the org. Use the programmatic step `read-get-community-template-collection` to retrieve `{publisher, templateName}` per template via `GET /connect/communities/templates`. The setup_page step is the manual UI fallback at `/lightning/setup/CommunityTemplateDefinitionList/home`. Read-only — template creation is a Salesforce-published artifact, not a customer-org operation.

## Critical Constraints

**Preconditions:**

- Digital Experiences (Communities/Networks) is enabled or has been enabled at least once in the org. (check: `Experience Cloud sites enabled || Experience Cloud sites enabled`)
- The org is not on a Help-Center-only edition (which suppresses the template list). (check: `!Help Center networks-only mode`)
- Community Template feature is available to this org. (check: `Community templates enabled`)
- User has permission to create community templates. (check: `create community template permission`)

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `view_CommunityTemplateDefinitionList_1` | read | — | `CommunityTemplateDefinitionList.view` | — |
| `read-get-community-template-collection` | read | implemented | `GET /services/data/v66.0/connect/communities/templates` | — |

### Read operations

#### `view_CommunityTemplateDefinitionList_1`

Open the Setup page UI at view_url for manual template browsing. Programmatic alternative: step `read-get-community-template-collection` (GET /connect/communities/templates) returns the same template list as JSON.

**Call:** `CommunityTemplateDefinitionList.view`

#### `read-get-community-template-collection`

List the community templates available in this org. Returns `{templates: array<{publisher, templateName}>, total: integer}`. No parameters; pulls the org-context template registry.

**Call:** `GET /services/data/v66.0/connect/communities/templates`   — status: `implemented`

**Output:** `CommunityTemplateCollectionRepresentation` — `{templates: array<CommunityTemplateRepresentation{publisher: string, templateName: string}>, total: integer}`.
