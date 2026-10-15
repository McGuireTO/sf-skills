---
name: industries-decision-matrix-builder-configure
description: "Use this skill when users want to manage Decision Matrix versions in Industries Business Rules Engine. Trigger when users mention wizard, ui, industries, interaction, decisionmatrix, components."
metadata:
  version: "1.0"
---

# Managing Wizard Ui Industries Interaction Decisionmatrix Components

## When to Use This Skill

Manage Decision Matrix versions in Industries Business Rules Engine. This setup wizard allows an admin to activate a decision matrix version, export it as a DMN file, create new versions, and validate column completeness. Use this SOR when a user needs to manage the lifecycle of a Decision Matrix definition — versioning, activation, export, or pre-activation validation.

## Critical Constraints

**Preconditions:**

- Industries Cloud / Business Rules Engine licensing must be provisioned on the org — backed by CalculationMatrixStandardEntity / CalculationMatrixVersionStandardEntity (industries.interaction.calculation UDD). (check: `None`)
- A parent Decision Matrix Definition record (DecisionMatrixDefinition / CalculationMatrix) must already exist before any version-lifecycle step runs; create-new-DM-version, activate, export, and is-missing-columns all take a Decision Matrix Version Id, which presupposes the version (and therefore its parent definition) is present. (check: `None`)
- For the get-decision-matrix-definition-id step, the calling user must satisfy Decision Matrix user access — the only method-level access guard on this controller. (check: `Decision Matrix user access`)

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `decision-matrix-version-controller-is-missing-columns-in-d-m` | validate | implemented | `GET /headless/invoke/industries/industries-interaction-decisionmatrix/is-missing-columns-in-dm` | — |
| `decision-matrix-version-controller-create-new-d-m-version` | write | implemented | `PATCH /headless/invoke/industries/industries-interaction-decisionmatrix/create-new-dmversion` | — |
| `decision-matrix-version-controller-activate-d-m-version` | write | implemented | `PATCH /headless/invoke/industries/industries-interaction-decisionmatrix/activate-dmversion` | `decision-matrix-version-controller-is-missing-columns-in-d-m` |
| `decision-matrix-version-controller-export-as-d-m-n-file` | read | implemented | `PATCH /headless/invoke/industries/industries-interaction-decisionmatrix/export-as-dmnfile` | — |
| `decision-matrix-version-controller-get-decision-matrix-definition-id` | read | implemented | `/headless/invoke/industries/industries-interaction-decisionmatrix/get-decision-matrix-definition-id` | — |

### Read operations

#### `decision-matrix-version-controller-export-as-d-m-n-file`

Serializes the Version to DMN (Decision Model and Notation) XML, delivered via file-download channel; JSON body is empty (void). AURA-IS-CANONICAL: no public DMN-export surface; client-side serialization would push DMN namespace + element-generation rules to the agent.

**Call:** `PATCH /headless/invoke/industries/industries-interaction-decisionmatrix/export-as-dmnfile`   — status: `implemented`

#### `decision-matrix-version-controller-get-decision-matrix-definition-id`

Returns the parent DecisionMatrixDefinitionId for a given CalculationMatrix Id via SOQL with system-elevation. Navigation pre-step before listing or creating versions. AURA-IS-CANONICAL: SOQL substitution drops the userHasDecisionMatrixUserAccess guard and the pushFullAccessRights FLS elevation.

**Call:** `/headless/invoke/industries/industries-interaction-decisionmatrix/get-decision-matrix-definition-id`   — status: `implemented`

**Inputs:**

- `decisionMatrixId` *(`string`)* — Id of the Decision Matrix (CalculationMatrix) record to look up; must be a valid entity Id.

**Output:** String. The parent Decision Matrix Definition record Id (15- or 18-character Salesforce Id).

### Write operations

#### `decision-matrix-version-controller-create-new-d-m-version`

Clones a new Version under the same parent Definition as decisionMatrixVersionId; isCarryForward=true copies source rows, false starts empty; versionDetailsMap keys must be in the allowlist or InvalidVersionDetails throws. AURA-IS-CANONICAL: raw sObject INSERT drops carry-forward, the keys allowlist gate, and the per-row error array.

**Call:** `PATCH /headless/invoke/industries/industries-interaction-decisionmatrix/create-new-dmversion`   — status: `implemented`

#### `decision-matrix-version-controller-activate-d-m-version`

Promotes the version to active and atomically deactivates the previously-active sibling on the parent Definition. AURA-IS-CANONICAL: raw sObject UPDATE leaves two versions active and breaks BRE evaluation; no Connect/Tooling activate primitive exists.

**Call:** `PATCH /headless/invoke/industries/industries-interaction-decisionmatrix/activate-dmversion`   — status: `implemented`

**Depends on:** `decision-matrix-version-controller-is-missing-columns-in-d-m`

### Other operations

#### `decision-matrix-version-controller-is-missing-columns-in-d-m`

Returns true when the version is missing required columns vs its parent Definition's schema; gates activation. AURA-IS-CANONICAL: no public surface for the version-vs-definition column-schema diff that Decision Matrix Column Check owns.

**Call:** `GET /headless/invoke/industries/industries-interaction-decisionmatrix/is-missing-columns-in-dm`   — status: `implemented`
