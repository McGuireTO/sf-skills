---
name: experience-custom-domain-create
description: "System-of-record describing the Salesforce Connect REST API routes for managing custom domains — onboard a new domain to Cloudflare (the only supported CDN partner), list registered domains, check pending-configuration status, activate a domain, list / fetch custom URLs for a domain or site, and associate a domain to a site. Routes only — runtime dispatch (auth, transport, retries) is handled by the MCP tool that consumes this description."
metadata:
  version: "1.0"
---

# sf-custom-domain

System-of-record for the Salesforce Connect REST API routes used to manage custom domains. **This skill describes the API contract only — it does not invoke any CLI or shell commands.** Runtime dispatch (auth, transport, retries) is the responsibility of the MCP tool that consumes this description.

Nine user-facing operations against `/services/data/v<version>/connect/custom-domain/...`:

- **Onboard** — trigger phrases: "onboard `<domain>`", "register `<domain>` to cloudflare", "add custom domain `<domain>`". Primary route: `POST /connect/custom-domain/domains`.
- **List domains** — trigger phrases: "list custom domains", "show all custom domains", "what domains are registered". Primary route: `GET /connect/custom-domain/domains`.
- **Pending status** — trigger phrases: "status of `<domain>`", "pending configuration for `<domain>`", "is `<domain>` activated yet". Primary route: `GET /connect/custom-domain/domains/{domainId}/pending-configuration`.
- **Activate** — trigger phrases: "activate `<domain>`", "activate custom domain `<domain>`", "move `<domain>` to active". Primary route: `POST /connect/custom-domain/domains/{domainId}/activate`.
- **List URLs by domain** — trigger phrases: "list urls for `<domain>`", "custom urls on `<domain>`", "what urls point at `<domain>`". Primary route: `GET /connect/custom-domain/domains/{domainId}/custom-urls`.
- **List all URLs** — trigger phrases: "list all custom urls", "all custom urls", "every custom url in the org", "show me all the urls". Composes **List domains** + **List URLs by domain** for each.
- **Get URL** — trigger phrases: "show url `<customUrlId>`", "details of url `<customUrlId>` on `<domain>`". Primary route: `GET /connect/custom-domain/domains/{domainId}/custom-urls/{customUrlId}`.
- **List URLs by site** — trigger phrases: "list urls for site `<siteId>`", "custom urls on site `<storeOrSiteId>`". Primary route: `GET /connect/custom-domain/domains/sites/{storeOrSiteId}/custom-urls`.
- **Associate domain to site** — trigger phrases: "associate `<domain>` with site `<siteName|siteId>`", "attach site `<siteName|siteId>` to `<domain>` at path `<path>`", "associate site `<siteName>` with `<domain>`", "add a custom url". Primary route: `POST /connect/custom-domain/domains/{domainId}/custom-urls`.

API version is read from `constants.json`, which pins `apiVersion` to **v67.0** for every operation in this skill — always call these routes at v67.0 or higher.

See the companion `references.md` for DNS-prerequisite documentation and Connect API reference material.

## Output rules — strict (applies to all ops)

- The skill produces *exactly one* result message and stops. No follow-up verification, no extra tables, no "should I also..." questions.
- Do not run additional checks after the result message. If something needs verifying, the user will ask separately.
- Confirmation prompts are allowed only at the points called out below ("proceed despite warnings"). Nowhere else.

## Common — error-shape contract

All Connect API errors follow the standard Salesforce shape: an array of `{errorCode, message}`. When mapping errors, surface the first entry's message verbatim and apply the per-operation error tables below. If the response indicates an unknown / unsupported endpoint, suggest checking the API version on https://developer.salesforce.com/docs/atlas.en-us.chatterapi.meta/chatterapi/connect_resources_custom_domain_resources.htm and confirm the org supports v67.0+ — see `constants.json`. Never retry automatically — the user retries.

---

## Operation: Onboard

Register a new custom domain. The CDN partner is always Cloudflare (the only supported `cdnPartner` enum value).

### Required inputs

- `domainName` — required. Strip leading/trailing whitespace, lowercase. Reject if it doesn't match a basic FQDN pattern (`^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)+$`). If not supplied, ask:
  > What domain do you want to onboard? (e.g. `www.example.com`)
- `cdnPartner` — always `Cloudflare`. This is the only supported enum value. If the user supplies any value other than `cloudflare`/`Cloudflare` (case-insensitive), reject the request (see edge cases). Normalize to the exact string `Cloudflare` before sending.
- `configurationOption` — always `CdnPartner` for this skill. Other options (`ExternalHttps`, `NoHttps`, `SitesRuntime`) are out of scope.

### Helper routes (optional, for remediation only)

Two read-only Connect API routes return the authoritative CNAME-target values for a domain. They are **not** invoked as part of onboarding — Salesforce runs its own validation when the registration POST is called and returns a clear error if DNS isn't ready. These routes exist so the consumer can surface the expected target in error remediation when Salesforce's own message doesn't include it.

**Route — ownership CNAME**
- **Method/path:** `GET /services/data/v<version>/connect/custom-domain/domains/{domainName}/expected-cname`
- **Request:** no body.
- **Response shape (200):** JSON object containing the CNAME target the domain's DNS must point to.

**Route — CDN validation CNAME**
- **Method/path:** `GET /services/data/v<version>/connect/custom-domain/domains/{domainName}/expected-cdn-validation-cname`
- **Request:** no body.
- **Response shape (200):** JSON object containing the `_acme-challenge.<domain>` CNAME target the CDN partner uses for cert provisioning.

If both routes return `NOT_FOUND` at the configured API version, the documented format is `[domainName].[orgId-lowercased].live.siteforce.com` (see `references.md`). On internal/non-production stacks the actual provisioned target may include extra path segments before `siteforce.com` — the API routes above are the source of truth; the constructed format is best-effort.

### Step 1: Register the domain

- **Method/path:** `POST /services/data/v<version>/connect/custom-domain/domains`
- **Response shape (success, HTTP 2xx):** JSON object with `domainId` and `domainName` (and additional metadata fields).

**Request body:**

```json
{
  "domainName": "<domainName>",
  "configurationOption": "CdnPartner",
  "cdnPartner": "Cloudflare"
}
```

`cdnPartner` is fixed to the literal string `"Cloudflare"`; it is the only supported enum value.

### Step 2: Interpret the response

**On success:**
```text
## ✅ Domain submitted for provisioning

- **Domain**: `<domainName>`
- **CDN partner**: `<cdnPartner>`
- **API version**: v<version>

The domain has been submitted to Salesforce for provisioning — it is **not active yet**. Provisioning can take up to 24 hours.

Salesforce response (pretty-printed JSON):
<pretty-printed response>

Next step: check provisioning status with `pending configuration for <domainName>`.
```

**On error** — map the first entry of the JSON error array. Standard known error patterns:

- **`can't validate the domain` AND `CNAME record may still be processing`** → DNS not ready. **Extract the expected CNAME target from the error message itself** — Salesforce includes it in the message ("Make sure the domain name X uses Y as its CNAME target"). Quote that target verbatim to the user. DNS can take up to 24 hours to propagate. If the error message doesn't include the target, fall back to calling `GET /connect/custom-domain/domains/<domainName>/expected-cname` (or the documented format `<domain>.<orgIdLower>.live.siteforce.com`).
- **`domain may not belong to you`** (without the CNAME-processing phrase) → Salesforce can't prove ownership of `<domain>`. Get the authoritative CNAME target via `GET /connect/custom-domain/domains/<domainName>/expected-cname` and tell the user the CNAME must point there so Salesforce can verify control.
- **`DUPLICATE_VALUE` / `already exists` / `already registered`** → `<domain>` is already registered in this org. Use the `list custom domains` op to see all registered domains, or check pending-configuration.
- **`INVALID_INPUT` and message mentions `domainName`** → `<domain>` failed format validation by Salesforce. Confirm it's a valid public FQDN you control (no leading/trailing dots, no underscores, valid TLD).
- **`INSUFFICIENT_ACCESS` / `INSUFFICIENT_ACCESS_OR_READONLY`** → the user doesn't have permission to register custom domains. Ask an admin to grant the relevant permission set (often `Modify All Data` or a custom-domain-specific perm set).
- **`NOT_FOUND` and the path is `/connect/custom-domain/domains`** → the API endpoint isn't available at v<version>. Check https://developer.salesforce.com/docs/atlas.en-us.chatterapi.meta/chatterapi/connect_resources_custom_domain_resources.htm for the current "Available Version" of `POST /connect/custom-domain/domains`.
- **Anything else** → surface the raw `errorCode` + `message` verbatim, then suggest: "If this looks like a wrong API version, check the endpoint's Available Version on https://developer.salesforce.com/docs/atlas.en-us.chatterapi.meta/chatterapi/connect_resources_custom_domain_resources.htm."

Always wrap the error in:

```text
## ❌ Onboarding failed

- **Domain**: `<domainName>`
- **CDN partner**: `<cdnPartner>`

**Error**: `<errorCode>` — `<one-line summary>`

**What this means:** <plain-English from the table above>

**What to try:** <action from the table above>

Raw response (JSON):
<error JSON>
```

---

## Operation: List

List all custom domains registered in the org.

### API call

- **Method/path:** `GET /services/data/v<version>/connect/custom-domain/domains`
- **Request:** no body.
- **Response shape (success):** JSON object whose primary array contains entries with `domainId` and `domainName` (and additional metadata fields).

### Display

**Success:** render as a markdown table.
```text
## Custom domains

| Domain ID | Domain Name |
|---|---|
| 0I4… | <name1> |
| 0I4… | <name2> |
```
If the array is empty: `No custom domains are registered.`

**Error:** same wrapper as Onboard's error block, minus the domain-specific fields.

---

## Operation: Pending status

Fetch the in-flight provisioning status of a single domain.

### Required input

- `domainName` — required. If not given, ask for it.

### Step 1: Resolve domainId from domainName

Call the **List** route to get the full `{domainId, domainName}` mapping. Find the entry with `domainName == <user-supplied>` (case-insensitive match).

- **Found** → carry `domainId` forward.
- **Not found** → surface a clear error and list valid choices, then stop (no further calls):

```text
## ❌ Domain not found

`<user-supplied>` is not registered. Registered domains:

- `<name1>` — `<id1>`
- `<name2>` — `<id2>`
…
```

### Step 2: Fetch pending configuration

- **Method/path:** `GET /services/data/v<version>/connect/custom-domain/domains/{domainId}/pending-configuration`
- **Request:** no body.
- **Response shape (success, HTTP 2xx with body):** JSON object containing `domainStatus`, `configurationOption`, `cdnPartnerOptions`, `associateType` (and additional metadata fields).
- **Special-case response:** `NOT_FOUND` / `The requested resource does not exist` is the **expected** outcome when the domain is fully provisioned with no pending configuration — render this as success, not as an error.

### Step 3: Display

**On success (HTTP 2xx with body):** pretty-print the JSON inside a result block; surface the key fields if present (`domainStatus`, `configurationOption`, `cdnPartnerOptions`, `associateType`).
```text
## Pending configuration — `<domainName>`

- **Domain ID**: `<domainId>`
- **Status**: `<domainStatus>`
- **Config option**: `<configurationOption>`
- **CDN partner**: `<cdnPartner if any>`
- **Associate type**: `<associateType>`

Full response (pretty-printed JSON):
<pretty-printed body>
```

**`NOT_FOUND` / `The requested resource does not exist`:**
```text
## ✅ No pending configuration

`<domainName>` (`<domainId>`) has no pending configuration — it appears to be fully provisioned and active.
```

This is *not* an error. Do not show a red ❌ block.

**Other errors:** generic error wrapper, surface `errorCode` + `message` verbatim.

---

## Operation: Activate

Move a domain whose `domainStatus` is `AwaitingActivation` to `Completed`.

### Required input

- `domainName` — required. If not given, ask for it.

### Step 1: Resolve domainId from domainName

Call the **List** route (using the global `apiVersion`) to get the full `{domainId, domainName}` mapping. Find the entry with `domainName == <user-supplied>` (case-insensitive match).

- **Found** → carry `domainId` forward.
- **Not found** → same "Domain not found" block as Pending status. Stop.

### Step 2: Activate

Use the global `apiVersion` (v67.0).

- **Method/path:** `POST /services/data/v<version>/connect/custom-domain/domains/{domainId}/activate`
- **Request body:** `{}` (empty JSON object — required even though the operation takes no parameters).
- **Response shape (success, HTTP 2xx):** JSON object containing `domainName` and the new `domainStatus` (and additional metadata fields).

### Step 3: Interpret the response

**On success:**
```text
## ✅ Domain activated

- **Domain**: `<domainName>`
- **Domain ID**: `<domainId>`
- **Status**: `<domainStatus>`
- **API version**: v<version>

Salesforce response (pretty-printed JSON):
<pretty-printed response>
```

**Known error patterns:**

- **`INVALID_INPUT` and message contains `must be in AwaitingActivation status`** → `<domainName>` is not in `AwaitingActivation` status — it cannot be activated right now. Check current status with `pending configuration for <domainName>`. If it's already `Completed`, no action is needed.
- **`NOT_FOUND` / `The requested resource does not exist`** → the activate endpoint isn't available at the configured version. Check https://developer.salesforce.com/docs/atlas.en-us.chatterapi.meta/chatterapi/connect_resources_custom_domain_resources.htm for the current Available Version.
- **`INSUFFICIENT_ACCESS` / `INSUFFICIENT_ACCESS_OR_READONLY`** → the user doesn't have permission to activate custom domains. Ask an admin to grant the relevant permission set.
- **Anything else** → surface raw `errorCode` + `message` verbatim.

Wrap errors in:
```text
## ❌ Activation failed

- **Domain**: `<domainName>`
- **Domain ID**: `<domainId>`
- **API version**: v<version>

**Error**: `<errorCode>` — `<one-line summary>`

**What this means:** <plain-English from the table above>

**What to try:** <action from the table above>

Raw response (JSON):
<error JSON>
```

---

## Operation: List URLs by domain

List every custom URL bound to a registered custom domain. Each row carries the domain ↔ site association (a single domain can serve multiple paths, each routed to a different site).

### Required input

- `domainName` *or* `domainId` — exactly one is required. If only `domainName` is given, resolve `domainId` via the **List domains** route (case-insensitive match). If neither is given, ask:
  > Which domain do you want the custom URLs for? (`<domainName>` or `<domainId>`)

### API call

- **Method/path:** `GET /services/data/v<version>/connect/custom-domain/domains/{domainId}/custom-urls`
- **Request:** no body.
- **Response shape (success, HTTP 2xx):** JSON object with a `customUrls` array. Each entry contains: `customUrlId`, `domainId`, `domainName`, `path`, `primarySiteUrl`, `siteId`, `siteName`, `siteType` (Community / LightningExperience / etc.). May also include `lastModified` and `status` (`Published`, `Preview`, etc.). The response shape does **not** carry site description — use the [Site metadata enrichment](#site-metadata-enrichment-site-entity) section below if needed.

### Display

Render as a markdown table.

```text
## Custom URLs on `<domainName>` (`<domainId>`)

| customUrlId | path | siteId | siteName | siteType | primary | status |
|---|---|---|---|---|---|---|
| 0Jf… | / | 0DM… | t1 | Community | false | Published |
…
```

If the array is empty: `No custom URLs are associated with <domainName> yet.`

**Error:** generic error wrapper from Onboard.

---

## Operation: List all URLs

Aggregate every custom URL across every registered domain in the org. The Connect API does **not** expose an org-wide custom-URL list — this op is a composition of two existing routes: **List domains** to discover the domain set, then **List URLs by domain** for each `domainId`.

Use when the user asks "show me all the custom urls", "list all custom urls", or any phrasing that implies org-wide scope without naming a specific domain or site.

### No additional inputs

Take no arguments. Do not ask the user to narrow scope — the whole point of this op is "everything." If the user already named a domain or site, route to **List URLs by domain** or **List URLs by site** instead.

### Step 1: List all domains

Call **List domains**:
- **Method/path:** `GET /services/data/v<version>/connect/custom-domain/domains`
- **Request:** no body.
- **Response shape:** JSON object whose primary array contains entries with `domainId` and `domainName`.

If the array is empty:
```text
## No custom URLs

No custom domains are registered in this org, so there are no custom URLs to list.
```
Stop. No further calls.

If the call errors, surface the generic error wrapper from Onboard. Stop.

### Step 2: For each `domainId`, fetch its custom URLs

For each `(domainId, domainName)` from Step 1, call **List URLs by domain**:
- **Method/path:** `GET /services/data/v<version>/connect/custom-domain/domains/{domainId}/custom-urls`
- **Request:** no body.
- **Response shape:** JSON object with a `customUrls` array (per-row shape: `customUrlId`, `domainId`, `domainName`, `path`, `primarySiteUrl`, `siteId`, `siteName`, `siteType`, optional `lastModified`, `status`).

These calls are independent and **may be issued in parallel** (the consuming runtime decides — this skill does not constrain concurrency). Treat each per-domain call independently:
- Per-domain success → append rows to the aggregate.
- Per-domain failure → record the error with its `domainName` and `domainId`, but **do not abort the whole op**. Continue with the remaining domains.
- Per-domain empty array → silently include 0 rows for that domain (no error, no separate "empty" annotation in the per-row table).

### Step 3: Display

Render one consolidated table sorted by `domainName`, then `path`. Domains with zero URLs are listed in a separate one-liner block at the bottom so they're not lost.

```text
## All custom URLs in the org

| Domain | customUrlId | path | siteId | siteName | siteType | primary | status |
|---|---|---|---|---|---|---|---|
| <domainName1> | 0Jf… | / | 0DM… | t1 | Community | false | Published |
| <domainName1> | 0Jf… | /lwr2vforcesite | 0DM… | lwr2 | Community | false | Published |
| <domainName2> | 0Jf… | / | 0DM… | s1 | Communities | true | Published |
…

**Totals**: <N> URLs across <M> domain(s).

**Domains with no URLs yet**: `<domainName3>`, `<domainName4>` (if any — omit this line otherwise).

**Per-domain failures** (if any — omit this block otherwise):
- `<domainName>` (`<domainId>`) — `<errorCode>`: `<message>`
```

If the aggregate row count is zero AND every per-domain call succeeded:
```text
## No custom URLs

<M> domain(s) registered, none with any custom URLs yet:
- `<domainName1>` (`<domainId>`)
…
```

If **every** per-domain call errored, surface the failures and stop:
```text
## ❌ List all URLs failed

All <M> per-domain `GET .../custom-urls` calls returned errors. Likely a permission, version, or auth issue affecting the whole org rather than one domain.

Per-domain errors:
- `<domainName>` — `<errorCode>`: `<message>`
…
```

### Output rules (specific to this op)

- **Single result message.** Even though the op makes N+1 API calls, render exactly one consolidated message at the end. Do not stream per-domain progress updates.
- **Don't auto-fall-back.** If `GET /domains/{domainId}/custom-urls` returns the same shape of server-side bug as `GET /custom-urls/{customUrlId}` (`INTERNAL_ERROR / query returned more than one row`), record the failure for that domain and move on — do not rerun anything for that domain.
- **No per-URL details fetch.** This op does not call `Get URL` for each row; the **List URLs by domain** response carries everything needed for the table.

---

## Operation: Get URL

Fetch metadata for a single custom URL by its `customUrlId`.

### Required input

- `domainId` (or `domainName` resolved via List) and `customUrlId` — both required. If only `customUrlId` is given without a domain, resolve via **List URLs by site** or **List URLs by domain** first.

### API call

- **Method/path:** `GET /services/data/v<version>/connect/custom-domain/domains/{domainId}/custom-urls/{customUrlId}`
- **Request:** no body.
- **Response shape (success, HTTP 2xx):** single JSON object with the same per-row fields as **List URLs by domain** (`customUrlId`, `domainId`, `domainName`, `path`, `primarySiteUrl`, `siteId`, `siteName`, `siteType`, plus optional `lastModified`, `status`).

### Display

Pretty-print as a key/value block:

```text
## Custom URL `<customUrlId>` on `<domainName>`

- **Path**: `<path>`
- **Primary**: `<primarySiteUrl>`
- **Site**: `<siteName>` (`<siteId>`, `<siteType>`)
- **Status**: `<status>`
- **Last modified**: `<lastModified>`

Full response (pretty-printed JSON):
<pretty-printed body>
```

### Known issue: `INTERNAL_ERROR` / `query returned more than one row`

The endpoint occasionally returns HTTP 500 with:
```text
errorCode: INTERNAL_ERROR
message: "ERROR: query returned more than one row ..."
```
Reason: if the site behind the requested `customUrlId` is published under more than one domain/path mapping, the lookup matches multiple rows and can't disambiguate. Site-side ambiguity, not a `customUrlId` collision — `customUrlId` itself is unique.

**When this fires:** surface a clear, plain-English message and **fall back** to the **List URLs by domain** op so the user can locate the row by `path` instead. Do not retry the same call.

```text
## ⚠ Custom URL lookup failed (server-side issue)

The `GET .../custom-urls/<customUrlId>` endpoint returned `INTERNAL_ERROR` on `<domainName>` — this is a known server-side bug where the stored procedure can't pick a single row.

Falling back to listing all custom URLs on the domain instead.
```

Then immediately render the **List URLs by domain** result for the same `domainId`.

**Other errors:** generic error wrapper.

---

## Operation: List URLs by site

Fetch every custom URL associated with a given site / store, across all custom domains in the org. Useful when you have a `siteId` and want to discover which domain(s) it sits behind.

### Required input

- `storeOrSiteId` — required. The 15-char or 18-char Salesforce ID of the site or store (`0DM…` for Communities, `0DR…` etc.). If not given, ask for it.

### API call

- **Method/path:** `GET /services/data/v<version>/connect/custom-domain/domains/sites/{storeOrSiteId}/custom-urls`
- **Request:** no body.
- **Response shape (success, HTTP 2xx):** JSON object with a `customUrls` array using the same per-row shape as **List URLs by domain**. May also surface `lastModified` and `status`.

### Display

```text
## Custom URLs for site `<siteName>` (`<storeOrSiteId>`)

| customUrlId | domainName | path | primary | status |
|---|---|---|---|---|
| 0Jf… | <name> | / | false | Preview |
…
```

If the array is empty: `No custom URLs are bound to site <storeOrSiteId>.`

**Error:** generic error wrapper.

---

## Operation: Associate domain to site

Bind an existing custom domain to a site (or store) at a given path. Uses the global `apiVersion` (v67.0), same as every other operation in this skill.

**Wire-verified behavior** (one POST, two rows):
- The server creates **two** `customUrl` records per call:
  - **Row 1** — the `path` as-supplied (the LWR sub-site row).
  - **Row 2** — `path` with the site's `Site.UrlPathPrefix` appended. Example: POST `/testpath` against a site whose `UrlPathPrefix` is `vforcesite` ⇒ a second row at `/testpathvforcesite`.
- The POST response body returns **only Row 1**. Use **List URLs by domain** on the same `domainId` to see both rows.
- An 18-char `siteId` in the request is normalised to 15-char in the response.
- **Not idempotent.** A repeat POST at the same `(domainId, path)` returns `400 DUPLICATE_VALUE`.

### Required inputs

- `domainName` *or* `domainId` — exactly one. Resolve `domainName → domainId` via **List domains** (Step 1).
- `siteName` *or* `siteId` — exactly one. The site (Site / store) to bind. Must already exist; this skill does not create sites. If `siteName` is given, resolve `siteName → siteId` via the [Site metadata enrichment](#site-metadata-enrichment-site-entity) SOQL against `Site` (Step 2). If multiple sites match the same name, ask the user to disambiguate before proceeding.
- `path` — optional. Site-relative URL prefix (e.g. `/`, `/lwr2`, `/store`). Must start with `/` if given. Default: `/` (the apex). The empty string is invalid.

If `domainName`/`domainId` or `siteName`/`siteId` is missing, ask:
> Which domain and site should I associate? (`<domainName|domainId>` and `<siteName|siteId>`, optionally a `<path>` — defaults to `/`)

This op is intentionally agnostic about whether the user gives names or IDs. "associate `acme.com` to site `Storefront`" must work end-to-end without further ID prompts when the names are unambiguous.

### Step 1: Resolve domainId from domainName (if `domainId` not supplied)

Call **List domains**, case-insensitive match on `domainName`. Stop with the "Domain not found" block if the user-supplied name is not registered. If a `domainId` was supplied directly, skip this step.

### Step 2: Resolve siteId from siteName (if `siteId` not supplied)

The Custom Domain Connect API has no site-by-name lookup, so this resolution goes through the platform `Site` SObject (the underlying record for every Experience Cloud site / store). The consuming runtime executes the SOQL — this skill specifies the query and how to interpret the result.

**Query** (case-insensitive name match; surface `Description` so the user can disambiguate among same-named sites):

```sql
SELECT Id, Name, Description, UrlPathPrefix, Status
FROM Site
WHERE Name = '<siteName-escaped>'
```

Where `<siteName-escaped>` is the user-supplied name with single quotes / backslashes escaped per SOQL string-literal rules. If the consumer is unsure about case, use `WHERE Name LIKE '<siteName-escaped>'` instead — the consumer is free to widen, but the skill defaults to exact case-insensitive match.

**Interpret the result:**

- **Exactly one row** → carry `siteId = result[0].Id` forward to Step 3. Capture `Description` and `UrlPathPrefix` for the eventual success block; you'll need them for the display.
- **Zero rows** → surface a clear error and stop. No further calls.
- **Two or more rows** → **do not pick one automatically.** Ask the user to disambiguate, surfacing every candidate's `Description` so the choice is informed. Stop. Do not POST. The user re-issues the command with `siteId` chosen explicitly.

**Zero rows:**

```text
## ❌ Site not found

No site named `<siteName>` exists in this org (queried `Site` via SOQL).

- Check the spelling of the site name.
- If the site is a store, confirm it's published / accessible to your user.
- You can also pass the site ID directly (`0DM…` for Communities).
```

**Two or more rows:**

```text
## ⚠ Multiple sites named `<siteName>`

<N> sites in this org share that name. Pick one by ID before I proceed:

| siteId | Description | UrlPathPrefix | Status |
|---|---|---|---|
| 0DM…1 | <description1 or "(no description)"> | <prefix1 or "(none)"> | <status1> |
| 0DM…2 | <description2 or "(no description)"> | <prefix2 or "(none)"> | <status2> |
…

Re-run with the explicit `siteId` you want. (No site has been associated yet.)
```

If the SOQL itself errors (e.g. no read on `Site`, malformed query), surface the error verbatim under a `## ❌ Site lookup failed` block and stop. The user retries with `siteId`.

If a `siteId` was supplied directly, skip this step entirely. Optionally fetch the row for that `siteId` (`SELECT Id, Name, Description, UrlPathPrefix FROM Site WHERE Id = '<siteId>'`) to enrich the success block; if the lookup fails, fall through and use only the API-returned `siteName`/`siteType` in the display.

### Step 3: POST the association

After Steps 1 and 2, both `domainId` and `siteId` are known. The user may have supplied them directly, or this skill may have resolved them from `domainName` and `siteName` via List domains + the `Site` SOQL.

Use the global `apiVersion` (v67.0).

- **Method/path:** `POST /services/data/v<version>/connect/custom-domain/domains/{domainId}/custom-urls`
- **Request body fields:**
  - `siteId` — required. 15- or 18-char `0DM…`; server normalises to 15-char.
  - `path` — required. Must begin with `/`. Omitting it returns `400 DUPLICATE_VALUE` (not `REQUIRED_FIELD_MISSING` — wire-verified).
  - No other fields are accepted by this skill. Do not pass `customUrlId` (server-assigned), `domainId` (from URL path), `siteName`, or `siteType` (server-resolved).
- **Response shape (HTTP 201):** the Row-1 record only (see example below). Row 2 (`path + UrlPathPrefix`) is created server-side but **not** returned in this response. Run **List URLs by domain** on the same `domainId` to inspect it.

**Request body:**

```json
{
  "siteId": "0DM…",
  "path": "/<path>"
}
```

**Response shape (HTTP 201):**

```json
{
  "customUrlId": "0Jf…",
  "domainId":   "0I4…",
  "domainName": "<domainName>",
  "path":       "/your-path",
  "primarySiteUrl": false,
  "siteId":     "0DM… (15-char)",
  "siteName":   "<site name>",
  "siteType":   "Community",
  "status":     "Published"
}
```

### Step 4: Display

```text
## ✅ Site associated with domain

- **Domain**: `<domainName>` (`<domainId>`)
- **Site**: `<siteName>` (`<siteId>`, `<siteType>`)
- **Site description**: `<Site.Description from Step 2 — or "(no description)" if blank, or omit this line entirely if Step 2 was skipped>`
- **Path (server-normalised)**: `<path>`
- **Custom URL ID**: `<customUrlId>`
- **Status**: `<status>`
- **API version**: v<version>

Salesforce response (pretty-printed JSON):
<pretty-printed response>
```

If the server-normalised `path` differs from the requested input, surface a one-line note above the success block:

```text
ℹ Server normalised the path: requested `<requested>` → stored `<stored>`. (Salesforce appends the site's URL path prefix when the site has one.)
```

### Known error patterns

- **`404 NOT_FOUND` / `The requested resource does not exist`** — endpoint not exposed at this org's version at all. Check https://developer.salesforce.com/docs/atlas.en-us.chatterapi.meta/chatterapi/connect_resources_custom_domain_resources.htm for the current Available Version.
- **`500 UNKNOWN_EXCEPTION`** — bogus / non-existent `siteId`. `<siteId>` cannot be resolved by the server. Confirm the ID format (`0DM…` for Communities) and that the site exists in this org. The server returns 500 (not 400) for unknown siteIds — wire-verified.
- **`400 DUPLICATE_VALUE` — `A custom URL already exists for this domain and path`** — repeat POST at same `(domainId, path)`. A custom URL already exists at `<path>` on `<domainName>`. The op is **not idempotent** — use **List URLs by domain** to inspect the existing binding.
- **`400 DUPLICATE_VALUE`** (no `path` field) — `path` missing from the request body. `path` is required and must begin with `/`. The server returns `DUPLICATE_VALUE` (not `REQUIRED_FIELD_MISSING`) for this case — wire-verified.
- **`400 INVALID_INPUT` and message mentions `path`** — malformed path. Must start with `/` and contain only URL-safe characters. The empty string is invalid; use `/` for the apex.
- **`403 INSUFFICIENT_ACCESS` / `INSUFFICIENT_ACCESS_OR_READONLY`** — caller lacks the perm. Ask an admin to grant the relevant permission set.
- **Anything else** — surface raw `errorCode` + `message` verbatim.

Wrap errors in:

```text
## ❌ Site association failed

- **Domain**: `<domainName>` (`<domainId>`)
- **Site**: `<siteId>`
- **Path**: `<path>`
- **API version**: v<version>

**Error**: `<errorCode>` — `<one-line summary>`

**What this means:** <plain-English from the table above>

**What to try:** <action from the table above>

Raw response (JSON):
<error JSON>
```

---

## Site metadata enrichment (Site entity)

The custom-URL routes return `siteId`, `siteName`, and `siteType`, but **not** the human-friendly `Description` or the site's own `UrlPathPrefix`. The Connect API also has no site-by-name lookup, so resolving a user-supplied site name to its `siteId` likewise depends on the platform `Site` SObject.

- **Object:** `Site` (the platform-internal record for every Experience Cloud / Communities site / store; one row per site).
- **Join key:** `Site.Id == customUrls[*].siteId` — the site IDs returned by the custom-URL routes are `Site.Id` values.
- **Fields worth surfacing:** `Id`, `Name`, `Description`, `UrlPathPrefix`, `Status`, `SiteType`, `MasterLabel`.

This metadata source is consumed by the skill in two distinct ways:

1. **Display enrichment (optional).** Custom-URL display ops (List URLs by domain / List URLs by site / List all URLs / Get URL) may fold `Description` and `UrlPathPrefix` into the per-row table alongside `siteName`. **Do not block** the primary custom-URL display on this enrichment — render with API fields first, layer on `Site` data when present.

2. **Name resolution (required when used).** [Operation: Associate domain to site](#operation-associate-domain-to-site) uses this object to resolve a user-supplied `siteName` to a `siteId` before the POST. That resolution **is** load-bearing: zero rows ⇒ stop with a "site not found" error; multiple rows ⇒ stop and ask the user to disambiguate using the per-row `Description`. See Associate's Step 2 for the exact behavior.

**Example SOQL queries** (the consumer constructs and executes these — this skill specifies the queries but does not invoke SOQL itself):

Bulk display enrichment:
```sql
SELECT Id, Name, Description, UrlPathPrefix, Status
FROM Site
WHERE Id IN ('<siteId1>', '<siteId2>', …)
```

Name resolution for Associate Step 2:
```sql
SELECT Id, Name, Description, UrlPathPrefix, Status
FROM Site
WHERE Name = '<siteName-escaped>'
```

---

## Edge cases (all ops)

- **User asks for a CDN partner other than Cloudflare** — reject with: "Only `Cloudflare` is supported. Use `cloudflare`."
- **User passes a domain with a wildcard** (`*.example.com`) — reject in input validation.
- **Pending-configuration response with anything OTHER than `NOT_FOUND`** is an error — generic error wrapper.
- **`GET /custom-urls/{customUrlId}` returns `INTERNAL_ERROR` / `query returned more than one row`** — fall back to **List URLs by domain** for the same `domainId` (see [Get URL — Known issue](#known-issue-internal_error--query-returned-more-than-one-row)).
- **`POST /custom-urls` returns `NOT_FOUND` at v67.0** — confirm the org has the version of the API that exposes the associate endpoint; older patches resolve only at v67+.

<!-- skill-validate: ignore-start -->
<!-- codey:operations start -->
## Operations Reference

Operations this skill uses — routing and dependency reference.

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `get-expected-cname` | read | — | `GET /services/data/v67.0/connect/custom-domain/domains/{domainName}/expected-cname` | — |
| `get-expected-cdn-validation-cname` | read | — | `GET /services/data/v67.0/connect/custom-domain/domains/{domainName}/expected-cdn-validation-cname` | — |
| `onboard-custom-domain` | write | — | `POST /services/data/v67.0/connect/custom-domain/domains` | `get-expected-cname`, `get-expected-cdn-validation-cname` |
| `list-custom-domains` | read | — | `GET /services/data/v67.0/connect/custom-domain/domains` | — |
| `get-pending-configuration` | read | — | `GET /services/data/v67.0/connect/custom-domain/domains/{domainId}/pending-configuration` | `list-custom-domains` |
| `activate-custom-domain` | write | — | `POST /services/data/v67.0/connect/custom-domain/domains/{domainId}/activate` | `list-custom-domains`, `get-pending-configuration` |
| `list-custom-urls-by-domain` | read | — | `GET /services/data/v67.0/connect/custom-domain/domains/{domainId}/custom-urls` | `list-custom-domains` |
| `list-custom-urls-by-site` | read | — | `GET /services/data/v67.0/connect/custom-domain/domains/sites/{storeOrSiteId}/custom-urls` | — |
| `get-custom-url-detail` | read | — | `GET /services/data/v67.0/connect/custom-domain/domains/{domainId}/custom-urls/{customUrlId}` | `list-custom-urls-by-domain` |
| `associate-domain-to-site` | write | — | `POST /services/data/v67.0/connect/custom-domain/domains/{domainId}/custom-urls` | `list-custom-domains`, `resolve-site-name-to-id` |
| `resolve-site-name-to-id` | read | — | `GET /services/data/v67.0/query` | — |
<!-- codey:operations end -->
<!-- skill-validate: ignore-end -->
