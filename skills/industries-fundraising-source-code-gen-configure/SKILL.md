---
name: industries-fundraising-source-code-gen-configure
description: "Use this skill when users want to setup page for Fundraising Source Code Generation — configures the outreach source-code formula and the three UTM (medium / source / campaign) mappings Fundraising uses to derive attribution codes for donor outreach records. Trigger when users mention fundraising, source, code, gen, fundraising source code gen."
metadata:
  version: "1.0"
---

# Managing Fundraising Source Code Gen

## When to Use This Skill

Setup page for Fundraising Source Code Generation — configures the outreach
source-code formula and the three UTM (medium / source / campaign) mappings
Fundraising uses to derive attribution codes for donor outreach records.
Persistence layer is the Tooling Metadata sObject `FundraisingConfig`
(singleton row keyed on `DeveloperName=FundraisingConfig`), the same row the
sibling `FundraisingSettings` recipe writes NextGenCmtPrcs* fields on.
OPERATIONAL PREREQUISITE: the parent Fundraising feature must be enabled by
the `FundraisingSettings` recipe first — that step both flips the parent
org preference and inserts the default FundraisingConfig row. Any read on
this recipe before Fundraising is enabled returns an empty/absent
representation. When to pick this recipe: an admin wants to change how
Fundraising builds a donor's outreach source code (customize the formula) or
how it maps campaign / source / medium onto attribution fields. Not for
donor-record or gift-transaction workflows (those live on the
industries.fundraising / industries.fundraisingops Connect APIs).

## Workflow

Entity model: this recipe reads/writes exactly one row of the Tooling
Metadata sObject `FundraisingConfig` (DeveloperName=FundraisingConfig).
Row carries the two disjoint concept groups:
  * OWNED BY THIS RECIPE (mutable via save-settings): the seven
    recipe-owned fields — OutreachSourceCodeGenFmla, UtmMediumSrcObj,
    UtmMediumSrcObjField, UtmSourceSrcObj, UtmSourceSrcObjField,
    UtmCampaignSrcObj, UtmCampaignSrcObjField.
  * OWNED BY THE SIBLING FundraisingSettings RECIPE (untouched by any
    step in this SOR): IsNextGenCmtPrcsParallel, NextGenCmtPrcsMaxThreads,
    NextGenCmtPrcsBatchSize, DonorExternalIdField.

save-settings JSON keys (case-sensitive): formulaExpression + the six
utm* keys. `formulaExpression` is the input key; the persisted column
is `OutreachSourceCodeGenFmla` on FundraisingConfig. Sending any other
key returns CONTROLLER_ERROR.

save-settings merge semantics — recipe-owned scope is REPLACE-ALL:
every recipe-owned key not present in the payload is nulled on the
row. Only the sibling-owned scope (NextGenCmtPrcs* / DonorExternalIdField)
is preserved across saves. Consequence: a "partial edit" that ships
only one changed key clears the other six. To edit a single field,
first read the current 7-field state (via Tooling SOQL) and resend all
non-nulled values alongside the change.

check-syntax runs a recipe-specific DSL grammar validator — NOT
general Salesforce formula grammar. Empty string returns
`ERROR ... input '<EOF>'`; bare identifiers (`Name`) return
`ERROR ... input 'Name'`. Simple valid inputs: a double-quoted
string literal (`"HELLO"`) or a comparison/logical expression over
literals (`"A" == "B"`). `+` string concatenation is NOT accepted.

`sourceCodeGenerationEnabled` gates ONLY the save-settings grammar
validator, NOT whether a formula persists. Empirical behavior (probed
against a live org):
  * enabled=true  → save-settings runs the DSL grammar validator on
    `formulaExpression`. Empty string AND grammar-invalid inputs
    (bare identifiers, malformed expressions) return 500
    CONTROLLER_ERROR; only grammar-valid formulas persist.
  * enabled=false → save-settings BYPASSES the grammar validator.
    ANY string value (empty, valid, or grammar-invalid) persists
    verbatim to `OutreachSourceCodeGenFmla`. The gate is NOT
    "reject non-empty when disabled"; it is "skip validation when
    disabled." check-syntax remains callable and returns grammar
    diagnostics regardless of the toggle.

Clearing the formula: `formulaExpression:""` is REJECTED by the
grammar validator while `sourceCodeGenerationEnabled=true`. To null
the formula, first call set-source-code-generation-enabled(false),
then save-settings with `formulaExpression:""`. Re-enable after if
needed. (This works precisely because disabling bypasses grammar
validation, letting the empty string through to persistence.)

Workflow ordering:

### Phase 1: Enable the parent Fundraising feature via the sibling

Enable the parent Fundraising feature via the sibling
     FundraisingSettings recipe (writes the default FundraisingConfig
     row + flips the IndustriesFundraising org preference). Skipping
     this yields empty reads on FundraisingConfig.

### Phase 2: get-source-code-generation-enabled — read the child feature-gate

get-source-code-generation-enabled — read the child feature-gate
     org preference. Note: this toggle gates grammar VALIDATION on
     save-settings, not persistence. When false, any formula string
     (including grammar-invalid ones) will persist without validation
     — callers who want the grammar-safety net must set this true
     before writing.

### Phase 3: set-source-code-generation-enabled(isEnabled=true) — enable the

set-source-code-generation-enabled(isEnabled=true) — enable the
     child feature so save-settings will run the grammar validator.
     Verify via verify-set-source-code-generation-enabled.

### Phase 4: get-utm-settings + get-outreach-source-code-formula — read

get-utm-settings + get-outreach-source-code-formula — read
     current state via Tooling SOQL on FundraisingConfig. Capture ALL
     seven recipe-owned values before mutating.

### Phase 5: check-syntax(formulaExpression) — validate a candidate formula

check-syntax(formulaExpression) — validate a candidate formula
     string. Iterate until diagnostics array is empty.

### Phase 6: save-settings(oscSettings=<json>) — persist state. Payload MUST

save-settings(oscSettings=<json>) — persist state. Payload MUST
     carry every recipe-owned field the caller wants to keep, not
     just the changed one.

### Phase 7: verify-save-settings — Tooling SOQL read-back to confirm

verify-save-settings — Tooling SOQL read-back to confirm.

Rollback: to revert, call save-settings with the JSON originally
returned by get-utm-settings before your edit — all seven keys
together. To clear all recipe-owned state, save a payload with all
seven keys set to empty string (or omit them; both null the row's
recipe-owned columns). Sibling-owned NextGenCmtPrcs* /
DonorExternalIdField values survive either shape.

## Critical Constraints

**Preconditions:**

- Nonprofit Cloud Fundraising must be provisioned in the org. Without
it, the Fundraising Admin permission check fails and every operation
in this skill is blocked. (check: `IndustriesFundraising`)

## Verification Checklist

After every write operation, confirm the effect by re-reading state:

- After `set-source-code-generation-enabled`: call `verify-set-source-code-generation-enabled` (`GET /headless/invoke/platform/fundraising-source-code-gen`)
- After `save-settings`: call `verify-save-settings` (`GET /services/data/v67.0/tooling/query`)

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `get-source-code-generation-enabled` | read | implemented | `GET /headless/invoke/platform/fundraising-source-code-gen` | — |
| `set-source-code-generation-enabled` | write | proposed | `PATCH /headless/invoke/platform/fundraising-source-code-gen/set-source-code-generation-enabled` | — |
| `verify-set-source-code-generation-enabled` | verify | — | `GET /headless/invoke/platform/fundraising-source-code-gen` | `set-source-code-generation-enabled` |
| `save-settings` | write | implemented | `PATCH /headless/invoke/platform/fundraising-source-code-gen/save-settings` | — |
| `get-utm-settings` | read | proposed | `GET /services/data/v67.0/tooling/query` | — |
| `get-outreach-source-code-formula` | read | implemented | `GET /services/data/v67.0/tooling/query` | — |
| `check-syntax` | read | proposed | `GET /headless/invoke/platform/fundraising-source-code-gen/check-syntax` | — |
| `verify-save-settings` | verify | proposed | `GET /services/data/v67.0/tooling/query` | `save-settings` |

### Read operations

#### `get-source-code-generation-enabled`

Read the child `sourceCodeGenerationEnabled` org preference (Fundraising
Source Code Generation feature toggle). Returns a bare boolean. This
toggle gates the save-settings grammar VALIDATOR, not persistence —
when false, save-settings persists any formula string (including
grammar-invalid ones) without validation; when true, save-settings
rejects grammar-invalid formulas with 500 CONTROLLER_ERROR. Parent
IndustriesFundraising feature must be enabled first (via the sibling
FundraisingSettings recipe).

**Call:** `GET /headless/invoke/platform/fundraising-source-code-gen`   — status: `implemented`

**Output:** Boolean. True when the org-level source-code-generation preference is enabled, false otherwise.

#### `get-utm-settings`

Read the seven recipe-owned fields (formula + UTM mappings) from the
FundraisingConfig singleton via Tooling SOQL. Returns a typed
QueryResult with one record (`totalSize:0` when the parent Fundraising
feature has not been enabled yet). Preferred over the controller's
JSON-string wrapper — typed columns, filter-able, discoverable schema.

**Call:** `GET /services/data/v67.0/tooling/query`   — status: `proposed`

**Inputs:**

- `q` *(`string`)*

**Output:** String. JSON-serialized UTM-style outreach source-code settings (source/medium/campaign field mappings plus behavior toggles); same shape save-settings consumes.

#### `get-outreach-source-code-formula`

Read the current `OutreachSourceCodeGenFmla` from the FundraisingConfig
singleton via Tooling SOQL. Returns a typed one-record QueryResult
(empty when the parent Fundraising feature is not enabled). Preferred
over the controller's raw-string wrapper — typed column, discoverable
schema.

**Call:** `GET /services/data/v67.0/tooling/query`   — status: `implemented`

**Inputs:**

- `q` *(`string`)*

**Output:** String. The formula expression currently configured for the org (Fundraising source-code-formula DSL), or empty when none is set.

#### `check-syntax`

Validate a candidate outreach-source-code formula against the
recipe-specific DSL grammar. Returns an array of parser diagnostics
(empty array = valid). NOT general Salesforce formula grammar —
bare identifiers (`Name`) return `ERROR ... input 'Name'`; empty
string returns `ERROR ... input '<EOF>'`. Valid inputs include
double-quoted string literals (`"HELLO"`) and comparison/logical
expressions over them (`"A" == "B"`); `+` string concatenation is
NOT accepted. No public grammar-validator API exists; this is canonical.

**Call:** `GET /headless/invoke/platform/fundraising-source-code-gen/check-syntax`   — status: `proposed`

**Inputs:**

- `formulaExpression` *(`String`)*

**Output:** Array of strings. Each entry is a parser diagnostic message from the Fundraising formula grammar; an empty array indicates the formula expression parses cleanly.

### Write operations

#### `set-source-code-generation-enabled`

Toggle the child `sourceCodeGenerationEnabled` org preference. This
toggle gates the save-settings grammar validator: when true, the
validator runs and rejects grammar-invalid formulas (500
CONTROLLER_ERROR); when false, the validator is BYPASSED and any
formula string (valid, empty, or grammar-invalid) persists verbatim.
Set to true for admin workflows that want the grammar-safety net;
set to false to persist an empty formula (see agent_guidance
"Clearing the formula"). Idempotent — writing the current value is
a no-op returning success.

**Call:** `PATCH /headless/invoke/platform/fundraising-source-code-gen/set-source-code-generation-enabled`   — status: `proposed`

**Inputs:**

- `isEnabled` *(`boolean`)* — Whether enabled is enabled.

**Output:** SaveResult. Carries success (boolean — true when the org-pref write succeeded), id (record id of the affected entity, may be empty for org-pref writes), errors (hard errors that caused failure when success is false), warnings (non-fatal warnings, may be present even when success is true), and infos (informational messages, non-blocking).

#### `save-settings`

Persist the recipe-owned fields on the FundraisingConfig singleton.
JSON key is `formulaExpression` + the six utm* keys. Server enforces
two controls the raw Tooling write does not: (1) formula-grammar
validation gated on `sourceCodeGenerationEnabled`; (2) sibling-scope
preservation — the sibling-owned NextGenCmtPrcs* / DonorExternalIdField
values on the same row are untouched. Recipe-owned scope is
REPLACE-ALL: any of the seven keys omitted from the payload is nulled.
To change one field, first read all seven via Tooling SOQL and
resend the unchanged values.

**Call:** `PATCH /headless/invoke/platform/fundraising-source-code-gen/save-settings`   — status: `implemented`

**Inputs:**

- `oscSettings` *(`String`)* — Value for the osc settings field.

### Verify operations

#### `verify-set-source-code-generation-enabled`

Confirm the child `sourceCodeGenerationEnabled` toggle persisted by
reading the boolean back. Bind result to the value passed to
set-source-code-generation-enabled.

**Call:** `GET /headless/invoke/platform/fundraising-source-code-gen`

**Depends on:** `set-source-code-generation-enabled`

#### `verify-save-settings`

Confirm save-settings persisted by reading the FundraisingConfig
singleton back via Tooling SOQL. Verifies BOTH that the recipe-owned
fields updated AND that the sibling-owned NextGenCmtPrcs* /
DonorExternalIdField values were preserved by the server-side merge.

**Call:** `GET /services/data/v67.0/tooling/query`   — status: `proposed`

**Inputs:**

- `q` *(`string`)*

**Depends on:** `save-settings`
