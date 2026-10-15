---
name: fsc-digital-origination-bre-decision-matrix-foundation-create
parent: "digital-origination-bre-setup"
purpose: "Create, populate, and activate a Business Rules Engine decision matrix used by a lending BRE feature."
description: "Create a Business Rules Engine decision matrix, define its input and output columns, load its rows, and activate the version - the shared building block for the Digital Lending Disclosures and Consent, Document Upload, and STP applicant eligibility features. The matrix is a CalculationMatrix sObject (key prefix 0lI); its Type field MUST be set to \"Standard\" (the derived version MatrixType formula reads from it - a null Type makes the runtime lookup throw \"Unsupported Matrix type null\"). Columns are written through the BRE Taurus decision-matrix Connect builder API (columns auto-create version 1); rows are written by direct CalculationMatrixRow sObject insert with an engine-computed MD5-hash Name into a draft version; and the version is activated through the decision-matrix builder controller. Resolves an existing matrix by exact name before creating one, and validates activation with a fresh read AND a live BRE lookup."
metadata:
  version: "1.0"
---

# Digital Origination decision-matrix foundation

Create the Business Rules Engine **decision matrix** that a lending BRE feature depends on: a lookup of
input column values to output column values. This sibling owns the matrix lifecycle only — create,
columns, rows, activate. The calling feature sibling supplies the matrix name, the column contract, and
the concrete rows, and consumes the returned matrix and version IDs.

A decision matrix here is the admin-typed lookup surface from the help articles (Business Rules Engine →
Lookup Tables → New → Decision Matrix), **not** the source-object decision *table* used by
`digital-origination-pricing-setup`. Do not use the decision-table Connect API for this work.

## The matrix is a CalculationMatrix, not a DecisionMatrixDefinition

Org-verified: the FSC Digital Lending decision matrix is stored as a **`CalculationMatrix`** sObject
(key prefix `0lI`), with `CalculationMatrixVersion` (`0lN`), `CalculationMatrixColumn` (`0lJ`), and
`CalculationMatrixRow` (`9mt`). The BRE `DecisionMatrixDefinition`/`DecisionMatrixDefinitionVersion`
sObjects (prefixes `9QN`/`9QO`) are a **different model** — the Connect decision-matrix API rejects a
`9QN` id with `INVALID_ID_FIELD`. Always create and address the matrix as a `CalculationMatrix`.

There is **no Connect "create matrix definition" operation.** The matrix definition is created by a
direct `CalculationMatrix` sObject insert (or, the officially supported path, a Metadata API deploy of a
`DecisionMatrixDefinition` metadata component with `type` set). Do not look for a
`POST /connect/business-rules/...` create op — it does not exist.

## The single most important field: `CalculationMatrix.Type`

**Org-verified root cause — set `CalculationMatrix.Type` or the matrix will never evaluate.**
`CalculationMatrixVersion.MatrixType` is a **derived formula field** that mirrors the parent
`CalculationMatrix.Type` at query time (it is read-only — createable=false, updateable=false — so nothing
writes it directly). A raw `CalculationMatrix` sObject insert leaves `Type` null, so `MatrixType` reads
null on every version forever, and the runtime lookup dispatch (`Standard` vs `Grouped`) falls through to
`throw "Unsupported Matrix type null"` — surfaced to callers as *"there isn't any output for the specified
input parameters."* The same null also 500s the Connect rows write.

**Fix / requirement:** immediately after inserting the `CalculationMatrix`, PATCH
`Type = "Standard"` (a plain settable STATICENUM; enum `CalcMatrixType` = `Standard` | `Grouped` — use
`Standard` unless you genuinely need grouped semantics). Verify with a query that
`CalculationMatrixVersion.MatrixType` reads `Standard`, not null. The supported *creation* path — a
Metadata API deploy of a `DecisionMatrixDefinition` with a required `type` — sets `Type` for you; a raw
sObject insert does not, so you must PATCH it.

## Preconditions and input contract

Require from the calling feature sibling:

- Target-org alias and acting admin.
- Exact matrix **Name**.
- Column contract: for each column, the header name/apiName, header type (`Input` or `Output`), and
  data type. Use the exact enum the `CalculationMatrixColumn` describe accepts — verified tokens:
  `ColumnType` = `Input` | `Output`; `DataType` = `Text` | `Number` | `NumberRange` | `TextRange` |
  `Currency` | `Percent` | `Boolean`. Map help-article labels (e.g. "Number Range") to these tokens
  (`NumberRange`) — never submit the English label.
- Row contract: one or more rows, each mapping input values to output values.

Confirm Rule Engine Designer access from the `permissions` sibling before creating a matrix.

## Corpus operations and sObjects to use

**Create the matrix definition (sObject insert).** Insert a `CalculationMatrix` record — required field
`Name`, optional `Description`. Capture the returned id (`0lI…`) as `matrixId`. **Then PATCH
`CalculationMatrix.Type = "Standard"`** (see "The single most important field" above) — without it the
matrix never evaluates.

**Columns — approved BRE Taurus decision-matrix Connect API**
(SOR `connect-api/bre-taurus/industries-interaction-decisionmatrix-connect-api__sfdc.industries.interaction.decisionmatrix.connect.api_oas_67.0`):

| Purpose | Step | Endpoint |
|---|---|---|
| Add columns | `post-decision-matrix-columns` | `POST /connect/omnistudio/decision-matrices/{matrixId}/columns` |
| Verify columns | `verify-columns` / `get-decision-matrix-columns` | `GET /connect/omnistudio/decision-matrices/{matrixId}/columns` |
| Read rows | `verify-rows` / `get-decision-matrix-rows` | `GET /connect/omnistudio/decision-matrices/{matrixId}/versions/{versionId}/rows` |

Rows are written by **direct `CalculationMatrixRow` sObject insert**, not a Connect POST — see the rows
section below. The Connect `post-decision-matrix-rows` op exists but 500s on the verified org.

Each column object: `{name, apiName, columnType, dataType, displaySequence}` — and, for a `NumberRange`
input column, `rangeValues` (see below). **The first `post-decision-matrix-columns` call auto-creates
version 1** (`CalculationMatrixVersion`, `0lN`). Do **not** insert a `CalculationMatrixVersion` yourself —
inserting it before columns fails ("needs at least one input and one output column"), and inserting it
after fails ("version number 1 already in use"). Read the auto-created version id with a SOQL query on
`CalculationMatrixVersion` filtered by `CalculationMatrixId`.

**`NumberRange` banding is a column property, set at column-creation time.** A `NumberRange` input column
carries a `rangeValues` string — a comma-separated list of band boundaries (org-verified shape, e.g.
`"0,740,10000"` for two bands 0–739 and 740–9999). It **cannot** be edited later: once the version is
enabled the Connect columns-POST returns "You can't edit the column data in an enabled Decision Matrix
version," and once the matrix has more than one version it returns "Can't edit columns in a Decision
Matrix with more than 1000 rows or more than one version." So set `rangeValues` on the very first
`post-decision-matrix-columns` call. A column posted without it reads back `rangeValues: null` and the
runtime lookup will never match a range row.

**Rows — direct `CalculationMatrixRow` sObject insert with an engine-computed MD5-hash `Name`
(org-verified).** Insert each row as a `CalculationMatrixRow` sObject. Fields: `CalculationMatrixVersionId`
(the ONLY FK — there is no `CalculationMatrixId` field on the row), `Name` (the engine hash, below),
`InputData` (JSON string), `OutputData` (JSON string). Direct inserts **do** materialize into the runtime
lookup **once `CalculationMatrix.Type` is set** (the earlier belief that they don't was a
misdiagnosis — the real blocker was the null `Type`). The Connect `post-decision-matrix-rows` write 500s
on the verified org (`UNKNOWN_EXCEPTION`) regardless of body, so do not depend on it.

- **The `Name` MUST be the engine's row hash, or the lookup won't find the row.** Algorithm (this is the
  exact hash the matrix engine computes to match a row at lookup time, reproduced here): over the **input columns only**, sort keys in natural String order;
  for each build `columnName + String.valueOf(value).toLowerCase()` (the column `Name` is NOT lowercased,
  the value IS); join with `""` (no separator); MD5 the UTF-8 bytes; hex-encode lowercase (32 chars).
  Example (`CreditScore` boundary `740`): `md5("CreditScore740")` = `f3b5ae55316f2fb03e4b416d3b80940e`.
- **`InputData` shape:** for a `NumberRange` column, the **band-boundary value as a string**
  (`{"CreditScore":"0"}`, `{"CreditScore":"740"}` — NOT `{"min":0,"max":739}`; the boundary is the hashed
  value). For `Text`, the literal value. `OutputData` carries the raw typed output (`{"IsSTP":true}`,
  `{"docTypeLabel":"ApplicationForm"}`, `{"DataUsePurpose":"<id>"}`).
- **Rows can only be inserted/deleted while the version is a draft (`IsEnabled=false`)** — an enabled
  version rejects row DML. Set `IsEnabled=false` first. To change an existing row, DELETE then INSERT
  (an in-place UPDATE is rejected by the matrix save-hook). To add rows to an already-enabled matrix,
  disable the version (or append a new draft version — see step 4a), do the row DML, then re-activate.

Verify with the `get-decision-matrix-rows` GET (or a SOQL on `CalculationMatrixRow`), then prove
materialization with a live BRE lookup.

**Activate — decision-matrix builder controller** (SOR
`wizard-ui-industries-interaction-decisionmatrix-components`):

| Purpose | Step | Endpoint |
|---|---|---|
| Activate a matrix version | `decision-matrix-version-controller-activate-d-m-version` | `PATCH /headless/invoke/industries/industries-interaction-decisionmatrix/activate-dmversion` (body `{decisionMatrixVersionId}`) |

Related builder ops exist (`get-decision-matrix-definition-id`, `create-new-dmversion`,
`is-missing-columns-in-dm`) but `create-new-dmversion` needs an existing anchor version, so it is for
adding a **second** version to an already-built matrix, not the initial build.

## Create-or-reuse algorithm

1. **Resolve existing.** SOQL `CalculationMatrix` by exact `Name`. If found, capture its id and its
   latest `CalculationMatrixVersion`; read its columns/rows via the Connect GETs. Do not create a
   duplicate merely because an id was not handed in. (`GET /connect/omnistudio/decision-matrices` search
   is gated by `orgHasInteractionCalculationAccess` and may 400 — fall back to SOQL.)
2. **Create the matrix if absent.** Insert a `CalculationMatrix` sObject with the requested `Name`.
   Capture `matrixId`. **PATCH `Type = "Standard"`** and confirm the version's derived `MatrixType` reads
   `Standard` (not null) — this is the step that makes the matrix evaluable at runtime.
3. **Add columns (with `NumberRange` banding).** Call `post-decision-matrix-columns` with the full column
   contract — including `rangeValues` on any `NumberRange` input column, because it cannot be set later —
   then confirm with `get-decision-matrix-columns`. This auto-creates version 1 — read its id from
   `CalculationMatrixVersion` (filter on `CalculationMatrixId`). Set input attributes on input columns
   only.
4. **Add rows by direct sObject insert.** For the auto-created draft version 1, insert each
   `CalculationMatrixRow` with `CalculationMatrixVersionId`, the MD5-hash `Name`, `InputData`
   (`NumberRange` = boundary-scalar string, `Text` = literal), and `OutputData` (raw typed value). Confirm
   with the `get-decision-matrix-rows` GET (or SOQL) that every row round-trips. The version must be a
   draft (`IsEnabled=false`) for the insert; the auto-created v1 is a draft until you activate it.
   4a. **Editing rows on an already-enabled matrix.** If the target version is enabled, set
   `IsEnabled=false` first (or append a new draft `CalculationMatrixVersion` — the `create-new-dmversion`
   clone API returns "Cannot create definition record" on sObject-created matrices, so a direct version
   insert with `IsEnabled=false` and the next `VersionNumber` is the fallback), do the row DML
   (DELETE+INSERT to change a row — in-place UPDATE is rejected by the save-hook), then re-activate.
5. **Activate.** Call `activate-dmversion` with the version id, then re-read the
   `CalculationMatrixVersion`. Activation is confirmed when `StartDateTime` is set and `EndDateTime` is
   null (there is no `Status` field on the version and no `ActiveVersionId` on the matrix). A 200 alone
   is not proof — require the fresh read.
5a. **Prove runtime materialization.** Call the live BRE lookup
   `POST /connect/business-rules/decision-matrices/{Name}` with a representative input and confirm it
   returns the expected output (not "there isn't any output for the specified input parameters"). An
   Active window with a failing lookup means the rows did not materialize — revisit step 4.
6. **Setup checkpoint fallback.** If `activate-dmversion` is rejected or the version never shows an
   active window, stop at the Setup checkpoint: App Launcher → Business Rules Engine → Lookup Tables →
   open the matrix → open the version → Save and Activate. Resume only after re-reading the active
   window. Do not report an in-progress or draft matrix as active.

## Idempotency and rollback

- Reuse an exact-match matrix (same columns, same header/data types) and exact-match rows.
- Do not create suffixed duplicates such as `IsSTPApplication2` automatically. On a shape mismatch,
  stop and present the diff.
- Rollback for rows added by this run is a targeted removal; do not delete a matrix that a feature or
  OmniScript already depends on without explicit approval.

## Output contract

Return matrix Name, `CalculationMatrix` id (`0lI…`), `CalculationMatrixVersion` id (`0lN…`), active
status (the version's `StartDateTime`/`EndDateTime` window), the verified column list (with
header/data types), and the verified row set. These IDs are the handoff back to the calling feature
sibling.

## Definition of done

The requested matrix exists exactly once as a `CalculationMatrix`, carries the exact columns and rows
supplied by the feature sibling, its version reads active (StartDateTime set, EndDateTime null) on a
fresh read, **and a live BRE lookup against the matrix returns the expected output** (proving the rows
materialized into the runtime index). A matrix that is Active but whose lookup returns "no output for the
specified input" is NOT done. A manual activation checkpoint left incomplete means this sibling is
partial.
