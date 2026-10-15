---
name: platform-label-workbench-import-create
description: "Use this skill when users want to import translated metadata files into the org using the Translation Workbench Connect API. Trigger when users mention label, workbench, import, label workbench import."
metadata:
  version: "1.0"
---

# Managing Label Workbench Import

## When to Use This Skill

Import translated metadata files into the org using the Translation Workbench Connect API. Use this SOR when a user wants to upload completed translations (XLIFF, STF, or ZIP containing multiple translation files). The import runs asynchronously: submit the file via multipart/form-data, receive a jobId, then poll the status endpoint until completion. Supports validate-only mode to check the file without applying changes, and configurable error handling (fail-fast or continue-on-error).
LIMITATION: The TWB Connect API currently supports importing Metadata translations only (labels, help text, picklist values, etc.). Data Translations (EDT — translated record field values) are NOT supported by this API at this time; support is planned for a future release. Workaround for Data Translations: write translated field values directly to the translatable data entities using the Bulk API or sObject API.
RELATED: The Connect-API-keyed skill i18n-connect-api-i18n.api.connect-oas-67.0 covers the same submit/poll endpoints (post-twb-import, get-twb-import-status) with cross-references back to this skill for full contract detail. That skill additionally exposes read-only reference-data steps an agent may need alongside an import workflow: get-languages (org's enabled languages with localized labels), get-state-country-translations (translated state/country picklist values), get-timezone-api (timezone identifiers localized to a requested locale).

## Critical Constraints

**Preconditions:**

- Org must have Translation Workbench enabled (LanguageSettings.enableTranslationWorkbench)
- Org must have Translation Workbench Connect API enabled (LanguageSettings.enableTranslationWorkbenchConnectAPI)
- User must have "Manage Translation" permission
- API version must be 67.0 or higher

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `submit-import` | write | implemented | `POST /services/data/v67.0/connect/i18n/translation/import` | — |
| `poll-import-status` | read | implemented | `GET /services/data/v67.0/connect/i18n/translation/import/{jobId}/status` | `submit-import` |

### Read operations

#### `poll-import-status`

Poll the import job status until it reaches Completed or Failed. On Completed, all translations in the file have been applied to the org.

**Call:** `GET /services/data/v67.0/connect/i18n/translation/import/{jobId}/status`   — status: `implemented`

**Inputs:**

- `jobId` — The jobId returned by the submit-import step (prefixed "import_").

**Depends on:** `submit-import`

**Output:** Job status object. When status is Completed, all translations have been applied. When Failed, message and reportLinks contain error details.

### Write operations

#### `submit-import`

Submit an asynchronous translation import job. Upload a translation file (XLIFF, STF, or ZIP archive) as a multipart/form-data `file` field. Import options (errorHandling, validateOnly) go on the URL QUERY string as a `parameters` JSON value — NOT as a second multipart part (a multipart parameters part is rejected with INVALID_MULTIPART_REQUEST). Returns a jobId for status polling.

**Call:** `POST /services/data/v67.0/connect/i18n/translation/import`   — status: `implemented`

**Inputs:**

- `file` — Translation file to import, sent as a multipart/form-data `file` field. This is the ONLY multipart part — import options go on the query string (see `parameters`), not as a second part. Supported formats: single XLIFF (.xlf/.xliff) file, single STF (.stf) file, or ZIP archive containing multiple XLIFF or STF files. The OpenAPI spec declares this body as application/octet-stream — that is INCORRECT; an octet-stream body fails with REQUIRED_FIELD_MISSING: file. Use multipart/form-data with a `file` field. Wire-verified 2026-06-30 against a test org (API v67.0).
  - schema: `{'type': 'string', 'format': 'binary'}`
- `parameters` — JSON string with import options, passed as a URL QUERY parameter — NOT as a multipart part. Sending parameters as a multipart/form-data part (application/json or octet-stream) is rejected with INVALID_MULTIPART_REQUEST. The multipart body carries ONLY the `file` field; import options ride on the query string. Wire-verified 2026-06-30 against a test org (API v67.0). Controls error-handling behavior and whether to validate without applying.
  - schema: `{'type': 'string', 'description': 'JSON-encoded object with optional fields: errorHandling (FailOnFirstError or ContinueOnError) and validateOnly (boolean).', 'example': '{"errorHandling": "ContinueOnError", "validateOnly": false}'}`

**Output:** JSON with jobId (prefixed "import_"), status ("Pending"), and message. Use jobId to poll the status endpoint.
