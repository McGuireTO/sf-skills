---
name: crm-analytics-tableau-next-app-deploy
description: "Install a Tableau Next / App-Framework template as a new app on a Salesforce org, end-to-end and self-contained. Scoped to an explicit ALLOWLIST — Service Insights (`sfdc_internal__ServiceInsights`), Sales Insights TN (`sfdc_internal__SalesInsightsTN`), Employee Agent Analytics (`sfdc_internal__Employee_Agent_Analytics`), Service Agent Analytics (`sfdc_internal__Service_Agent_Analytics`), and C360 Semantic Model (`sfdc_internal__C360UnifiedSemanticModel`). Any other template request is refused with a \"not supported\" message. Use when the user says \"install <one of the allowed templates>\", \"provision the ServiceInsights app\", \"spin up Sales Insights TN\", \"install Employee Agent Analytics\", \"install Service Agent Analytics\", or \"install C360 Semantic Model\". This skill performs the entire install workflow itself (allowlist gate → enumerate templates → fetch variables → detect C360 base-model dependency → check readiness → create app → poll status → optional rollback) using `sf api request rest` against the org's `/app-framework/*` endpoints — it does NOT depend on the project-codey MCP tools or the tableau-next-apps-mcp/-beta tools, though it can opportunistically use them if they're connected."
metadata:
  version: "1.0"
  accessCheck: "(AppTemplatingFramework.hasAppFrameworkAccess) || (DataCloud.enabled) || (UnifiedAnalytics.orgHasTableauOrSemanticLayerEnabled) || (UserPermissions.AppFrameworkManageTemplate)"
  cliTools:
  - tool:
    - "jq"
    semver: ">=1.6"
  - tool:
    - "python3"
    semver: ">=3.8"
  - tool:
    - "sf"
    semver: ">=2.0.0"
---

# tableau-next-app-install

## What this does

Drives a full **App-Framework template install** against the configured Salesforce org, entirely on its own. This skill is **self-contained**: it executes each step via `sf api request rest` (the sf-CLI's typed REST wrapper) against the App-Framework Connect API — at whatever API version the org publishes at runtime (see "Discover API version") — so it can run even when the project-codey MCP tools or the tableau-next-apps-mcp / tableau-next-apps-mcp-beta MCP tools are unreachable or unresponsive.

The workflow it drives (each step is a direct `sf api request rest` call — no MCP tool required):

| Step | Endpoint | Purpose |
|---|---|---|
| 1 | `GET /app-framework/templates` | Enumerate available templates on the org |
| 2 | `GET /app-framework/templates/{id}/configuration` | Discover what inputs the template expects at install time (variables live under `.variables` in the response body) |
| 2b | `GET /app-framework/templates/{id}/assets` | Detect C360 Semantic Model base-model dependency — refuse install if the required C360 app isn't installed on the org (see step 2b) |
| 3 | `POST /app-framework/templates/{id}/readiness` | Ask the platform "can this template install right now?" |
| 4 | `POST /app-framework/apps` | Kick off the async install |
| 5 | `GET /app-framework/apps/{id}` (repeat) | Poll `applicationStatus` until it settles |
| 6 | `DELETE /app-framework/apps/{id}` | Roll back a failed / unwanted install |
| 6b | `PUT /app-framework/apps/{id}` | Update / reconfigure an existing app in-place (the API-driven equivalent of App Hub → tile → Update). Used by 2b.5 to auto-remediate a C360 template-version mismatch on the HOME org without requiring the user to run the App Hub wizard by hand. |

If the caller has MCP tools connected — either project-codey's five install tools OR the tableau-next-apps-mcp/-beta family — the skill MAY use them as a faster path (they wrap the same endpoints), but it is not required to. See "Fast path (optional)" below.

## Supported templates (ALLOWLIST — refuse anything else)

**This skill installs ONLY the templates in the list below.** Any request naming a template outside the list — even if the template exists on the org and would install fine — MUST be refused with the exact message documented under "Allowlist gate" and the caller directed to the appropriate scope-owner. Do NOT proceed past step 1 for a non-allowlisted template. Silently substituting a "close match" is a correctness bug.

| User-facing name | Accepted apiName(s) | Accepted labels (case-insensitive EXACT match after normalization: lowercased, trimmed, internal whitespace collapsed) |
|---|---|---|
| Service Insights | `sfdc_internal__ServiceInsights` | `service insights`, `serviceinsights`, `service_insights` |
| Sales Insights TN | `sfdc_internal__SalesInsightsTN` | `sales insights`, `salesinsights`, `sales_insights`, `sales insights tn`, `salesinsightstn` |
| Employee Agent Analytics | `sfdc_internal__Employee_Agent_Analytics` | `employee agent analytics`, `employee_agent_analytics`, `employeeagentanalytics` |
| Service Agent Analytics | `sfdc_internal__Service_Agent_Analytics` | `service agent analytics`, `service_agent_analytics`, `serviceagentanalytics` |
| C360 Semantic Model | `sfdc_internal__C360UnifiedSemanticModel` | `c360 semantic model`, `c360semanticmodel`, `c360_semantic_model`, `c360 unified semantic model`, `c360unifiedsemanticmodel`, `c360` |

**Match discipline: EXACT string equality after normalization — NEVER substring.** A substring implementation would let `install "agent"` silently install one of the Agent Analytics templates, or `install "service agent analytics dashboard"` match Service Agent Analytics against a request that isn't for it. The code below implements exact match; do not "help" by softening it to `contains`.

**Note on the bare label `agent analytics`:** with two allowlisted Agent Analytics templates (Employee, Service), the bare label alone is ambiguous — resolved to `AMBIGUOUS_AGENT_ANALYTICS` and the caller is asked to pick.

**Canonical apiName resolution — do this BEFORE step 1:**

```bash
# Normalize the user's input (lowercase, collapse whitespace) and match against the allowlist.
# Case-insensitive; strip leading/trailing whitespace; treat "sfdc_internal__" prefix as optional
# so users can say "SalesInsightsTN" or "sfdc_internal__SalesInsightsTN" interchangeably.
resolve_allowed_template() {
  local raw="$1"
  # Normalize once: lowercase, then convert ALL whitespace (tabs, newlines, etc.)
  # to single spaces via `tr -s '[:space:]' ' '`, then trim leading/trailing spaces.
  # `tr -s` squeezes runs, so multi-tab and mixed tab/space also collapse cleanly.
  local norm
  norm=$(printf '%s' "$raw" | tr '[:upper:]' '[:lower:]' | tr -s '[:space:]' ' ' | sed 's/^ //; s/ $//')

  case "$norm" in
    sfdc_internal__serviceinsights|serviceinsights|"service insights"|service_insights)
      echo "sfdc_internal__ServiceInsights" ;;
    sfdc_internal__salesinsightstn|salesinsightstn|salesinsights|"sales insights"|"sales insights tn"|sales_insights)
      echo "sfdc_internal__SalesInsightsTN" ;;
    sfdc_internal__employee_agent_analytics|employee_agent_analytics|"employee agent analytics"|employeeagentanalytics)
      echo "sfdc_internal__Employee_Agent_Analytics" ;;
    sfdc_internal__service_agent_analytics|service_agent_analytics|"service agent analytics"|serviceagentanalytics)
      echo "sfdc_internal__Service_Agent_Analytics" ;;
    sfdc_internal__c360unifiedsemanticmodel|c360unifiedsemanticmodel|"c360 unified semantic model"|c360_unified_semantic_model|c360semanticmodel|"c360 semantic model"|c360_semantic_model|c360)
      echo "sfdc_internal__C360UnifiedSemanticModel" ;;
    "agent analytics"|agentanalytics|agent_analytics)
      # Ambiguous — two templates match. Ask the caller which one.
      echo "AMBIGUOUS_AGENT_ANALYTICS" ;;
    0nk*)
      # Raw Salesforce template id (case-insensitive `0Nk…`). We can't resolve
      # to a canonical apiName here without a REST call, so pass through with
      # a marker; step 1's Path B will do the /templates lookup and re-check
      # the resolved .name against the allowlist. Echo the ORIGINAL (case-
      # preserving) raw input, not the lowercased $norm — Salesforce ids are
      # case-sensitive on the wire.
      echo "$raw" ;;
    *)
      echo "REFUSED" ;;
  esac
}

TEMPLATE_NAME_OR_ID=$(resolve_allowed_template "$USER_INPUT")

case "$TEMPLATE_NAME_OR_ID" in
  REFUSED)
    cat >&2 <<'MSG'
Sorry — this skill only installs Service Insights, Sales Insights TN, Employee Agent Analytics, Service Agent Analytics, and C360 Semantic Model.

The requested template is not on the allowlist and this skill will not proceed.
MSG
    return 1 2>/dev/null || exit 1
    ;;
  AMBIGUOUS_AGENT_ANALYTICS)
    cat >&2 <<'MSG'
"Agent Analytics" matches two allowlisted templates:
  - sfdc_internal__Employee_Agent_Analytics  (Employee-facing)
  - sfdc_internal__Service_Agent_Analytics   (Service-facing)
Ask the caller which one to install, then re-invoke with the full apiName.
MSG
    return 1 2>/dev/null || exit 1
    ;;
esac
```

The refusal message deliberately DOES NOT list alternatives, name specific non-allowlisted templates, or route the caller to other tooling. That's the guard against turning this skill into an index of "here's what you could have installed instead" — see anti-pattern rule.

**Allowlist gate — invariants:**
- The gate runs BEFORE any App-Framework REST call. Do not `GET /templates` first "just to help the user pick" — this skill never suggests non-allowlisted templates.
- If the user hands you a raw `0Nk…` id, RESOLVE it against `GET /templates` and reject if the resolved `.name` is not one of the five allowlisted apiNames.
- If the org's `GET /templates` response omits the allowlisted template the user asked for (feature-gated off, wrong release, etc.), report "not available on this org" and STOP — do NOT offer a "similar" template.
- The refusal message MUST NOT list alternatives outside the allowlist. Silence on alternatives is deliberate.

## When to use this vs alternatives

- **Use this skill** whenever the user wants to install **one of the five allowlisted templates** (Service Insights, Sales Insights TN, Employee Agent Analytics, Service Agent Analytics, C360 Semantic Model) on the currently-authenticated org. This is the default path for those five.
- **Refuse and stop** for any other template request — do not fall through to a "generic" install path. The whole scope of this skill is the allowlist.
- **Route to `codey-gap-triage`** if the user is describing a missing capability (e.g. "the readiness check doesn't validate chain nodes when readiness.json is absent") rather than an install. Chain-node evaluation is a separate MVP2 concern.
- **Do NOT delegate to another skill for orchestration** of an allowlisted install — this one is authoritative.

## Install-target thumb rule (READ BEFORE ANY `POST /apps`)

**The `--target-org` for the caller-template `POST /apps` is ALWAYS `$ORG_ALIAS` (the org the user named), NEVER `$RESOLVED_ORG_FOR_C360`, NEVER `$HOME_ORG_ALIAS`.** The C360-on-HOME auto-install driven by 2b.3/2b.5 is a *prerequisite* that installs a *different template* (`sfdc_internal__C360UnifiedSemanticModel`) on the HOME publisher — it must not be conflated with the caller template's install target. Two cases, no exceptions:

1. **`$ORG_ALIAS` is HOME (standalone or paired publisher).** Everything happens in `$ORG_ALIAS`. If 2b.3 detects C360 is missing on this org, `install_c360_on_home_and_wait_for_sync` self-installs C360 here (target = `$ORG_ALIAS` = `$RESOLVED_ORG_FOR_C360`); then the caller template (`SalesInsightsTN`, `ServiceInsights`, `Employee_Agent_Analytics`, `Service_Agent_Analytics`) also installs here in step 4. One org, two POSTs (only if C360 was missing), both targeting `$ORG_ALIAS`.

2. **`$ORG_ALIAS` is COMPANION.** The C360 prerequisite installs on `$HOME_ORG_ALIAS` (the paired publisher, target = `$RESOLVED_ORG_FOR_C360` = `$HOME_ORG_ALIAS`); the SDM then propagates from HOME to the companion via multi-org sync (`wait_for_c360_sdm_visible` blocks on this). Only *after* SDM visibility on the companion does step 4 fire, and its target MUST be `$ORG_ALIAS` (the companion). Two orgs, two POSTs against two different `--target-org` values — do not merge them.

The caller-template install NEVER lands on `$HOME_ORG_ALIAS` — HOME is the C360 publisher, not a place to host consumer apps on the COMPANION path. If you find yourself typing `--target-org "$HOME_ORG_ALIAS"` in step 4 or later steps, STOP — that's the bug this section exists to prevent. The mandatory guard in step 4 (`Step-4 target-org guard`) refuses at runtime, but you should also refuse at reading time.

Consumer templates on the COMPANION path (post-2b, i.e. step 3 readiness through step 5 poll) all use `$ORG_ALIAS`:

```bash
# HOME path (standalone or publisher):
#   $ORG_ALIAS == $RESOLVED_ORG_FOR_C360; both C360 (2b.3) and caller template (step 4) install here.
# COMPANION path:
#   C360 (2b.3): --target-org "$RESOLVED_ORG_FOR_C360"  (== $HOME_ORG_ALIAS)
#   Caller template (step 3 readiness, step 4 create, step 5 poll, step 6 delete, step 6b update):
#                --target-org "$ORG_ALIAS"              (== the companion)
```

## Preconditions

Before running the steps, confirm:

1. **Org is authenticated.** Run `sf org list --json` and require at least one org where `isConnected: true`. If the user hasn't told you which alias to use, prefer:
   - the org they named in the last message,
   - otherwise `sf config get target-org --json` (`.result[0].value`),
   - otherwise the first `isConnected: true` entry.
   If nothing is connected, stop and ask them to `sf org login web`.

2. **Caller holds the `AppFrameworkManageTemplate` user permission** (the "Manage App Templates" perm). The readiness, create, and delete calls all return HTTP 403 `ACCESS_DENIED` / `INSUFFICIENT_ACCESS` without it. If any App-Framework endpoint returns 403, this is almost always the cause — tell the user to have an admin assign a permission set carrying `AppFrameworkManageTemplate`, then retry. Distinct from feature-gate 403s (see precondition 3).

3. **Tableau Next is enabled on the org.** If `GET $API_BASE/templates` returns an empty list, `INSUFFICIENT_ACCESS` on the endpoint itself (not the caller), or `NOT_FOUND`, Tableau Next / App-Framework isn't provisioned — this skill can't fix that; route the user to Tableau Next enablement (out of scope).

4. **Data Cloud is provisioned AND the target data space exists.** The readiness/create bodies bind any DataSpaceType variable to an existing data space name; a missing/invalid data space does NOT surface as a clean readiness `FailedStatus` — it fails variable-definition parsing FIRST, so readiness POST returns HTTP 400 `TEMPLATEPARSEERROR: Data space [<X>] ... is unknown` (wire-verified 2026-08-19), or HTTP 400 `CDP not enabled` when Data Cloud is off entirely. **Always run the resolve-data-space pre-flight (`GET /ssot/data-spaces`) before the readiness POST** so an opaque `TEMPLATEPARSEERROR` becomes an actionable "enable Data Cloud / create the data space" message. See wire rule G.

5. **User has confirmed which template.** Don't guess. If the user said "install the sales app" but the org has three sales-adjacent templates, ask them to pick.

## Discover API version + resolve endpoints

Do NOT hardcode `v67.0` — resolve the highest API version the org actually publishes at runtime, and derive every endpoint URL from it. This lets the skill work on any org (test, sandbox, prod) regardless of the release train.

```bash
# GET /services/data returns an array of {label, url, version}. Take max(version).
# `| floor` is REQUIRED: jq's tonumber renders 68.0 as the float 68.0, and the
# format string "v\(.).0" would then produce "v68.0.0". Coerce to int with floor.
API_VERSION=$(sf api request rest "/services/data" \
  --target-org "$ORG_ALIAS" --method GET \
  | jq -r '[.[] | .version | tonumber | floor] | max | "v\(.).0"')
echo "Using API $API_VERSION"

# Sanity: expect exactly one dot, e.g. "v68.0" — bail if the format is off.
case "$API_VERSION" in
  v[0-9]*.0) : ;;
  *) echo "Bad API_VERSION='$API_VERSION' — abort"; return 1 2>/dev/null || exit 1 ;;
esac

# All subsequent App-Framework calls use this base.
API_BASE="/services/data/$API_VERSION/app-framework"
```

Every step below references `$API_BASE`. If the discovery call fails (no auth, no `sf` CLI, org unreachable), stop and remediate — every downstream step depends on it.

## Wire-shape rules (KNOW THESE COLD — the API is strict)

These are the App-Framework Connect API wire shapes as verified on 2026-08-18 against v67.0 (they continue to hold on later versions unless the OAS changes). They are the entire reason the skill exists as a self-contained fallback — the MCP tool wrappers historically drifted from these and the errors are opaque.

**A. Readiness body MUST be wrapped as `{"templateValues": {...}}`:**
- Bare `{}` is rejected with `JSON_PARSER_ERROR: Value does not match expected type`.
- Empty templateValues (`{"templateValues": {}}`) is allowed — the outer wrapper is what's required.
- The `required==true` filter is the STARTING point for `templateValues` — but see wire rules E and F for two MUST-DO extensions: unconditional `isTest: false` injection (rule E), and client-side resolution of `{{Variables.X.Y}}` placeholders in defaults (rule F). Step 2's builder handles both automatically. Do not send raw `{{Variables...}}` tokens.

**B. Create-app body OAS field is `templateValues` (per `AppInputRepresentation`), NOT `values` and NOT `userInputsForSingleClickDeploy`:**
- Required top-level fields on the POST body: `templateSourceId`, `label`, `name`.
- `templateValues` is optional — omit it entirely if step 2 returned no required variables and the user supplied none.
- Sending `values` or `userInputsForSingleClickDeploy` returns `JSON_PARSER_ERROR: Found unexpected object property`.

**C. Data-space variable shape is TEMPLATE-DEPENDENT — dispatch on `variableType.type` from `/configuration`'s `.variables` field:**

The variable name is NOT fixed — templates call it `dataSpaceApiName`, `defaultDataspace`, `dataspace`, etc. Do NOT hardcode a variable name. Dispatch on `variableType.type` for every required variable:
- The wire shape depends on how the template declared the variable in its `variables.json`:
  - `variableType.type == "StringType"` → send as bare String: `"dataSpaceApiName": "default"`.
  - `variableType.type == "DataSpaceType"` → send as an object: `"dataSpaceApiName": {"dataSpaceName": "default"}`.
- Sending the wrong shape raises symmetric errors:
  - `StringType` template + object → `BAD_REQUEST: variable name [dataSpaceApiName] with value [{dataSpaceName=default}] and type [LinkedHashMap] is not of expected type [String]` (seen on `sfdc_internal__itsm`).
  - `DataSpaceType` template + bare string → `BAD_REQUEST: The variable name [dataSpaceApiName] with value [default] and type [String] is not of expected type [Object]` (seen on `sfdc_internal__servicecloudinsights`).
- Rule of thumb: NEVER hardcode the shape. Always dispatch on `variableType.type` from step 2's response. Step 2's builder handles this for you.

**D. App status field is `applicationStatus`, NOT `status`:**
- On `GET /app-framework/apps/{id}`, `.status` is null. The real state is `.applicationStatus`.
- Terminal values: `SuccessStatus` (installed OK), `FailedStatus` (with `.failureReasons[]`). In-flight: `InProgressStatus`.

**E. `templateValues` must be complete for ANY variable the template's readiness EL expression references — silently missing variables cause false-negative DMO failures:**
- Templates like `sfdc_internal__servicecloudinsights` use `${Variables.isTest ? '' : ...}Case__dlm`-style expressions in `DataCloudRowCountReadiness` checks. When `Variables.isTest` isn't bound in `templateValues`, the EL evaluator fails silently, falls back to each check's `valueOnError` (typically `-1`), and the readiness response reports every DMO as "not ready" — even when they exist on the org.
- The trap: some templates reference `Variables.isTest` in their readiness EL *without declaring `isTest` in their `/configuration` response's `.variables` map*. This means (a) required-only filtering (wire rule A) is not sufficient, and (b) gating on `.variables | has("isTest")` still misses the case. **Always inject `isTest: false` unconditionally** — it's cheap, matches the platform's own test-mode-off convention, and eliminates a whole class of false negatives.
- Rule of thumb: if readiness comes back with wall-to-wall "DMO not ready" for DMOs the org actually has, suspect an unbound EL var (typically `isTest`) before you suspect the DMOs.

**F. `{{Variables.<name>.<subfield>}}` placeholders in variable defaultValues are NOT server-resolved at readiness time — you must inline them client-side:**
- Some templates ship variable defaults like `CaseContactReasonField.defaultValue = {"objectName": "{{Variables.CaseContactReasonObj.objectName}}", ...}`. The App-Framework `/configuration` endpoint returns the raw placeholder string under `.variables[<name>].defaultValue`; the readiness endpoint does NOT expand it.
- If you POST the raw placeholder, readiness rejects with e.g. `BAD_REQUEST: Object [{{Variables.CaseContactReasonObj.objectName}}] in variable [CaseContactReasonField] is unknown, not supported, or is invalid.`
- Resolve placeholders client-side before sending: for each `{{Variables.X.Y}}` token, look up the already-computed value of `X.Y` in `templateValues` and substitute. Iterate to a fixed point (a resolved value may itself reference another placeholder). Step 2's builder does this pass.

**G. Data space names must be RESOLVED via `GET /ssot/data-spaces`, never hardcoded as `"default"`:**
- Any variable of type `DataSpaceType`, or a `StringType` variable whose name semantically carries a data space apiName (e.g. `dataSpaceApiName`, `defaultDataspace`), takes a real data space name — not the literal string `"default"`.
- Some orgs have no data space named `default`; their sole data space might be `Corp_Ds`, `Sales_Ds`, `Foundations_Corp_Ds`, etc. Wire-verified 2026-08-19: on three such orgs, posting `dataSpaceApiName: {"dataSpaceName": "default"}` returned HTTP 400 `TEMPLATEPARSEERROR: Data space [default] ... is unknown`. On a Data-Cloud-off org it returned HTTP 403 on the underlying `ssot/data-spaces` endpoint or HTTP 400 `CDP not enabled` on the readiness POST.
- **Do this before step 3 (readiness)**: `DATA_SPACE_NAME=$(sf api request rest "/services/data/$API_VERSION/ssot/data-spaces" --target-org "$ORG_ALIAS" --method GET | jq -r '(.dataSpaces // [] | .[0].name) // "default"')` then substitute `$DATA_SPACE_NAME` into every DataSpaceType / data-space-carrier variable. The pre-flight also catches Data-Cloud-off orgs early (empty list or 403) so you can fail with a clear "enable Data Cloud" message instead of an opaque `TEMPLATEPARSEERROR` on the readiness call.

**H. `NumberType` variables MUST be emitted as FLOAT / decimal literals — bare integers 400 on the wire:**
- The `/configuration` endpoint serializes both `defaultValue` and `variableType.enums` (under `.variables[<name>]`) as BARE INTEGERS (e.g. an Agent Analytics `maxWaitTimeInMinutesForDMO` comes back as `defaultValue: 360` with `enums: [5, 10, 15, 30, 45, 60, 120, 360]` — no decimal point anywhere). You **cannot** infer the required format from the variable definition.
- The readiness/create validator requires the FLOAT form and rejects the integer. Wire-verified 2026-08-19: POSTing `maxWaitTimeInMinutesForDMO: 360` returns HTTP 400 `The variable name [maxWaitTimeInMinutesForDMO] with value [360] must be one of the following values [5.0, 10.0, 15.0, 30.0, 45.0, 60.0, 120.0, 360.0].`
- **Rule: append `.0` to every whole-number NumberType value before POSTing** (`360` → `360.0`, `30` → `30.0`). Do NOT "preserve the returned JSON type" for numbers — the returned type is a bare int and is wrong on the wire. This applies to enum-constrained AND free NumberType variables. Non-integer NumberType values (already decimal) pass through unchanged. Keep `DateType` / `DateTimeType` values as their exact returned strings; keep string-typed values as strings.

**I. Update-app (`PUT /app-framework/apps/{id}`) — same body shape as create, minus `label`/`name`:**
- Endpoint: `PUT /services/data/{api_version}/app-framework/apps/{appId}/`. This is the API-driven equivalent of App Hub → tile → **Update** (aka Reconfigure). It re-runs the template's install chain against the existing app record, upgrading it to the template's *current* `templateVersion` and re-applying the supplied `templateValues`. Use this to auto-remediate a 2b.5 C360 version mismatch on the HOME org without asking the user to click through the App Hub wizard.
- Body:
  ```json
  {
    "templateSourceId": "sfdc_internal__C360UnifiedSemanticModel",
    "templateValues": {
      "isTest": false,
      "DataSpace": { "dataSpaceName": "default" }
    }
  }
  ```
  - `templateSourceId` MUST match the apiName of the template that originally installed the app. On a version drift, the template metadata may have advanced but the apiName is stable — use the apiName the app was installed with (read from `GET /apps/{id}` — either `.templateSourceId` or `.templateApiName`, whichever the release exposes).
  - `templateValues` follows the SAME wire rules as create (A/C/E/F/G/H): required-var filter + `isTest` unconditional inject + `{{Variables.X.Y}}` client-side resolution + DataSpaceType/StringType dispatch + `NumberType` decimal coercion. The step-2 builder is reused verbatim — do NOT hand-craft a different body for PUT.
  - Data space name MUST be resolved via `GET /ssot/data-spaces` (wire rule G). Do not hardcode `"default"` — the readiness stage of the update chain re-validates it and rejects unknown data spaces with the same `TEMPLATEPARSEERROR` as create.
  - Do NOT include `label` or `name` in the PUT body — those are set at create-time and are read-only on update. Sending them either 400s or is silently ignored depending on the release.
- Response: same async-install pattern as create — the PUT returns quickly with an updated app envelope (`applicationStatus: InProgressStatus` typically) and the caller then polls `GET /apps/{id}` until terminal (wire rule D — check `.applicationStatus`, not `.status`; terminal values are `SuccessStatus`, `SuccessWithWarningsStatus`, `FailedStatus`). Poll cadence and timeout are the same as step 5.
- Auth / permission: same as create — caller needs `AppFrameworkManageTemplate`. The PUT target org MUST be the org that owns the app record (i.e. HOME on the C360-mismatch remediation path — `$RESOLVED_ORG_FOR_C360`). A companion session cannot PUT against a HOME app because sessions do not cross the Home/Companion boundary. Route the update through the HOME org alias exactly as with the manual Reconfigure.
- Companion blast radius still applies: the HOME's C360 app is shared by every paired companion. Auto-remediating from ONE companion's caller-invocation would mutate a shared resource for all of them. This is a policy decision, not a wire limitation — 2b.5 CONFIRMS with the user before running PUT on the companion-remediation path (see step 2b.5).

## Steps

Every step below uses `sf api request rest` — no MCP tool is required. If you prefer to use `mcp__project-codey__*` or `mcp__tableau-next-apps-mcp-beta__*` as an accelerator when they're connected and healthy, see "Fast path (optional)"; the wire-shape rules above still apply.

**All snippets below assume `$API_BASE` and `$ORG_ALIAS` are set** — `$API_BASE` comes from the "Discover API version + resolve endpoints" section above; `$ORG_ALIAS` is the sf-CLI alias for the target org. Copying a step in isolation without running discovery first will produce a bare `/app-framework/...` URL and every call will 404.

### 0. Preflight generic checks (delegated sub-skills)

Before touching templates, run the two **generic, app-agnostic readiness checks** every App-Framework install shares. Each is packaged as its own `user-invocable: false` skill and invoked here — the agent reads the sub-skill file on demand and runs its single read-only probe in this same shell, so an org that isn't provisioned fails fast with a clear message instead of an opaque error many steps later. (The third generic check — the C360 base-model gate — runs at Step 2b, not here, because it needs the *resolved* template's `/assets`.)

Run both **before Step 1**, in order, in the current shell.

> **Sub-skill path resolution (read first).** The three delegated sub-skills (`tableau-next-readiness`, `tableau-next-datacloud-readiness`, `tableau-next-c360-basemodel-gate`) are installed as sibling folders under `./.afv/skills/`, **relative to your current working directory (the workspace root — the folder that contains `.afv/`)**. Read each with a plain filesystem read at the literal relative path `./.afv/skills/<child>/SKILL.md`. There is **NO** `load_skill` / `search_skills` / `skill_bridge` tool on this host — a filesystem read is the ONLY route. Do **NOT** construct a path from memory, do **NOT** use any absolute path, and do **NOT** use any editor/extension `globalStorage` path — those hold System/Global skills and contain **none** of these workspace sub-skills. If the literal relative read fails, **STOP and report** — never substitute a remembered, absolute, or `globalStorage` location. Secondary fallback ONLY if the `./.afv/skills/` directory does not exist relative to CWD: the HOME-relative `~/.claude/skills/<child>/SKILL.md` (Claude Code). Never use `.vibes`.

> **Invoke the Tableau Next readiness check.** Read the literal relative path `./.afv/skills/tableau-next-readiness/SKILL.md`, resolved relative to your current working directory (the workspace root) — do **NOT** build a path from memory, and do **NOT** use any absolute or `globalStorage` path; if this read fails, **STOP and report** (never substitute a remembered path); secondary fallback ONLY if `./.afv/skills/` is absent: the HOME-relative `~/.claude/skills/tableau-next-readiness/SKILL.md` — and execute its check against `$ORG_ALIAS` / `$API_BASE` in the current shell. It confirms `GET $API_BASE/templates` returns a non-empty list (Tableau Next / App-Framework is provisioned, not empty / 403 / NOT_FOUND) and leaves the fetched payload in `$TEMPLATES_JSON`. It returns **PROCEED** or **STOP** (Tableau Next not provisioned — route the user to enablement; out of scope for this skill).

> **Invoke the Data Cloud readiness check.** Read the literal relative path `./.afv/skills/tableau-next-datacloud-readiness/SKILL.md`, resolved relative to your current working directory (the workspace root) — do **NOT** build a path from memory, and do **NOT** use any absolute or `globalStorage` path; if this read fails, **STOP and report** (never substitute a remembered path); secondary fallback ONLY if `./.afv/skills/` is absent: the HOME-relative `~/.claude/skills/tableau-next-datacloud-readiness/SKILL.md` — and execute its check against `$ORG_ALIAS` / `$API_VERSION` in the current shell. It confirms Data Cloud is provisioned and resolves the target data space into `$DATA_SPACE_NAME` (wire rule G — never hardcode `"default"`). It returns **PROCEED** or **STOP** (Data Cloud off / no data space — an install that binds a `DataSpaceType` variable would otherwise 400 with `TEMPLATEPARSEERROR`).

**Hard gate — do NOT continue to Step 1 unless BOTH checks returned PROCEED.** If either STOPs, surface its message verbatim and halt.

**Outputs these checks leave in your shell (later steps reuse them — run them in the SAME shell as the rest of this skill):** `$TEMPLATES_JSON` (Step 1 reuses it instead of re-fetching) and `$DATA_SPACE_NAME` (Step 2's builder and wire rule G reuse it instead of re-resolving). If your harness ran a check in a separate shell, those variables won't be set here — the corresponding step re-derives them idempotently via a `${VAR:-…}` fallback, so the skill still works, just with one extra GET.

### 1. Enumerate templates (filtered by allowlist)

The allowlist gate above has already produced a canonical apiName in `$TEMPLATE_NAME_OR_ID`. This step confirms the template EXISTS on this org and captures its `.id` for downstream logging. It also serves as the check that catches the "user handed us a raw `0Nk…` id" path — we look the id up and reject if its `.name` isn't on the allowlist.

```bash
ALLOWLIST='["sfdc_internal__ServiceInsights","sfdc_internal__SalesInsightsTN","sfdc_internal__Employee_Agent_Analytics","sfdc_internal__Service_Agent_Analytics","sfdc_internal__C360UnifiedSemanticModel"]'

# Reuse the payload the preflight 'tableau-next-readiness' check already fetched
# (Step 0); re-fetch only if this step is run standalone (TEMPLATES_JSON unset).
TEMPLATES_JSON="${TEMPLATES_JSON:-$(sf api request rest "$API_BASE/templates" \
  --target-org "$ORG_ALIAS" --method GET)}"

# Path A — canonical apiName input (either resolve_allowed_template produced it or
#          the caller supplied it directly). Path B — raw `0Nk…` id.
# We must re-check the allowlist on BOTH paths — Path A because $TEMPLATE_NAME_OR_ID
# may have been set outside resolve_allowed_template (env var, prior shell state,
# hand-editing), and Path B because ids don't self-identify their template name.
# This is a DOUBLE GATE: resolve_allowed_template (up-front) + this step (post-
# resolve). Do NOT rely on either alone.
# case-glob (dash/sh/bash portable) — the rest of the file uses `case`, not `[[ ... ]]`.
case "$TEMPLATE_NAME_OR_ID" in
  0Nk*)
    # Path B: id → resolve .name via /templates.
    RESOLVED_NAME=$(echo "$TEMPLATES_JSON" | jq -r \
      --arg id "$TEMPLATE_NAME_OR_ID" \
      '.templates[] | select(.id == $id) | .name' | head -n 1)
    if [ -z "$RESOLVED_NAME" ]; then
      echo "Template id $TEMPLATE_NAME_OR_ID is not published on this org. Refusing." >&2
      return 1 2>/dev/null || exit 1
    fi
    # Rewrite to canonical apiName for the rest of the flow — the allowlist check below
    # then runs on the CANONICAL name for both paths uniformly.
    TEMPLATE_NAME_OR_ID="$RESOLVED_NAME"
    ;;
esac

# Belt-and-braces allowlist re-check — applies to Path A AND (post-resolve) Path B.
# This closes the "env-var bypass" escape hatch: even if $TEMPLATE_NAME_OR_ID was
# populated without going through resolve_allowed_template, a non-allowlisted
# apiName is rejected HERE before any variables/readiness/create call runs.
IS_ALLOWED=$(echo "$ALLOWLIST" | jq -r --arg n "$TEMPLATE_NAME_OR_ID" 'index($n) != null')
if [ "$IS_ALLOWED" != "true" ]; then
  echo "Template '$TEMPLATE_NAME_OR_ID' is not on the allowlist. Refusing." >&2
  return 1 2>/dev/null || exit 1
fi

# Show ONLY the allowlisted templates that are present on this org.
echo "$TEMPLATES_JSON" | jq --argjson allow "$ALLOWLIST" '
  .templates[]
  | select(.name as $n | $allow | index($n))
  | {name, label, id, templateType, templateSubtype, templateStatus}
'

# Confirm the chosen template is actually present on this org before proceeding.
EXISTS=$(echo "$TEMPLATES_JSON" | jq -r --arg n "$TEMPLATE_NAME_OR_ID" \
  '.templates | map(select(.name == $n)) | length')
if [ "$EXISTS" = "0" ]; then
  echo "Template $TEMPLATE_NAME_OR_ID is not available on this org (not returned by /templates)." >&2
  echo "This is a scope / provisioning issue. This skill will NOT suggest a substitute." >&2
  return 1 2>/dev/null || exit 1
fi
```

Response follows `TemplateCollectionRepresentation`: entries under `.templates[]`, each is a `TemplateRepresentation` with `.id`, `.name` (API name), `.label`, `.description`, `.templateType`, `.templateSubtype`, `.templateStatus`.

Present a short list to the user — `name` + `label` — showing ONLY the allowlisted templates present on this org, and ask which one to install. Never install without an explicit user pick. Never expand the list beyond the allowlist.

**Failure — empty `.templates[]`:** Tableau Next isn't enabled OR user lacks visibility. Say so; don't retry.
**Failure — the allowlisted template the user chose is not in `.templates[]`:** the template isn't provisioned on this org. Report "not available on this org" and stop — do NOT suggest an alternative (see allowlist invariants).

### 2. Fetch the template's required variables

Use `GET /app-framework/templates/{id}/configuration` — the variables live under `.variables` at the top of the response body. This endpoint replaces the older `/variables` endpoint (which no longer ships on newer API versions); `/configuration` returns the full install-time configuration blob with the same `.variables` OBJECT MAP wire shape underneath.

```bash
sf api request rest "$API_BASE/templates/$TEMPLATE_NAME_OR_ID/configuration" \
  --target-org "$ORG_ALIAS" --method GET \
  | jq '.variables'
```

**Response shape — `.variables` is an OBJECT MAP, not an array.** The `/configuration` response wraps it at the top level. Real templates (e.g. `sfdc_internal__itsm`) return:

```json
{
  "variables": {
    "VarNameA": { "defaultValue": "...", "required": true,  "variableType": "StringType", ... },
    "VarNameB": { "defaultValue": "...", "required": false, "variableType": "StringType", ... }
  },
  ...other configuration keys...
}
```

Downstream jq / python passes below reference `.variables` off the top-level `/configuration` payload exactly as before — the wrapper key is unchanged, only the HTTP path moved.

Iterate it with `.variables | to_entries[]` — writing `.variables[]` or `.variables[]?` will yield the *value objects* (whose `.name` is undefined) and any subsequent `{(.name): ...}` construction crashes with `Cannot use null (null) as object key`.

**Only variables where `required == true` belong in `templateValues`** — WITH TWO EXCEPTIONS documented below. The server does NOT support `?required=true` as a query param — filter client-side in jq. Sending optional variables is harmless most of the time but muddies the payload and can trip stricter server-side validation for readiness on some templates.

**Exception 1 — sentinel defaults for required vars with `defaultValue == null`.** Some templates declare a required variable with no default (e.g. `dataSpaceApiName` on `sfdc_internal__servicecloudinsights` is required + `DataSpaceType` + `defaultValue: null`). If you simply skip null defaults, the readiness call fails with `variable [X] is required`. Inject a type-aware sentinel:

| `variableType.type` | Sentinel value | Rationale |
|---|---|---|
| `DataSpaceType` | `{"dataSpaceName": "<data_space_name>"}` | wire rule C object form. **Never hardcode `"default"`** — resolve the actual data space name from `GET /ssot/data-spaces` first (see wire rule G below). The rest of the codepath validated this on 2026-08-19: three orgs returned a `TEMPLATEPARSEERROR: Data space [default] ... unknown` on the readiness POST because their data spaces have non-`default` apiNames. |
| `StringType` + variable name that semantically carries a data space apiName (e.g. `defaultDataspace`, `dataSpaceApiName`, `data_space_name`, `dataspaceId`) | `"<data_space_name>"` | Same — the ACTUAL apiName resolved via `GET /ssot/data-spaces`, not the literal string `"default"`. Empty string fails the server-side DataSpace apiName lookup; the wrong string 400s with `TEMPLATEPARSEERROR: Data space [X] ... unknown`. |
| `StringType` (any other name) | `""` | Empty string is the platform's convention for "not specified" on plain string inputs. |
| `BooleanType` | `false` | Matches the platform's default-off convention. |
| `NumberType` | (see wire rule G below — always emit as a decimal literal) | Bare integers 400 on the wire. |
| any other type | (log a warning + skip) | Unknown types must be resolved by the caller — never invent. |

**Exception 2 — always inject `isTest: false`, unconditionally.** This is wire rule E: readiness EL expressions can reference `Variables.isTest` in DMO-name construction, and some templates (e.g. `sfdc_internal__servicecloudinsights`) reference it in EL *without declaring it in `/configuration`'s `.variables`*. Leaving it unbound silently returns `-1` for every DMO check. Gating on "template declared isTest" misses the pathological case, so just always inject `false` — it's a no-op for templates that don't consume it.

Build the `templateValues` map used in steps 3 and 4 — the jq below does the required filter, sentinel injection, `isTest` sentinel, AND the `{{Variables.X.Y}}` placeholder resolution (wire rule F) in one pass:

```bash
# Fetch the template configuration once. Variables live under `.variables`
# (an object map) — we keep the whole /configuration payload in VARS_JSON so
# every downstream `.variables | to_entries[]` walk below continues to work
# without a change.
VARS_JSON=$(sf api request rest "$API_BASE/templates/$TEMPLATE_NAME_OR_ID/configuration" \
  --target-org "$ORG_ALIAS" --method GET)

# ---- Pass 1: build the raw templateValues map -------------------------------
#  - iterate .variables as key/value pairs (it's an object map)
#  - keep required == true OR name == "isTest" (wire rule E — readiness needs it bound)
#  - if defaultValue is null AND variable is required, inject a type-aware sentinel
#    (wire rule C: DataSpaceType → object form; StringType → ""; BooleanType → false)
#    Exception: StringType variables that semantically CARRY a data space name
#    (variable name contains "datasp" case-insensitive — matches `dataSpaceApiName`,
#    `defaultDataspace`, `dataspace`, `dataSpace`, etc.) sentinel to the ACTUAL
#    resolved data space name (see wire rule G — resolve-data-space pre-flight),
#    NOT the literal string "default". Some orgs have no data space named "default"
#    (their sole data space might be `Corp_Ds`, `Sales_Ds`, etc.), and posting
#    "default" 400s with `TEMPLATEPARSEERROR: Data space [default] ... unknown`.
#    The caller MUST resolve $DATA_SPACE_NAME via `GET /ssot/data-spaces` before
#    this pass and substitute it here. Empty string is also wrong — it fails
#    DataSpace lookup with `INVALID_INPUT: DataSpace with apiName [] not found`.
#  - non-null defaults pass through unchanged
#  - `has("defaultValue")` guards `defaultValue // <sentinel>`: raw `//` treats
#    an explicit `false` as null and would clobber a legitimate BooleanType default.
# Resolve $DATA_SPACE_NAME via GET /ssot/data-spaces FIRST (wire rule G below).
# Do NOT hardcode "default" — some orgs have no data space by that name; the
# readiness POST 400s with TEMPLATEPARSEERROR when the string doesn't match.
# Reuse the value the preflight 'tableau-next-datacloud-readiness' check resolved
# (Step 0); re-resolve only if this step is run standalone (DATA_SPACE_NAME unset).
DATA_SPACE_NAME="${DATA_SPACE_NAME:-$(sf api request rest "/services/data/$API_VERSION/ssot/data-spaces" \
  --target-org "$ORG_ALIAS" --method GET \
  | jq -r '(.dataSpaces // [] | .[0].name) // "default"')}"

TEMPLATE_VALUES_RAW=$(echo "$VARS_JSON" | jq --arg ds "$DATA_SPACE_NAME" '
  # Sentinel dispatch is TWO-DIMENSIONAL: (variable name pattern, variableType.type).
  # StringType data-space carriers ("defaultDataspace", "dataSpaceApiName",
  # "data_space_name", "DATA_SPACE_NAME", etc.) sentinel to $ds — the LIVE-resolved
  # data space apiName from GET /ssot/data-spaces, NOT the literal "default".
  # Plain-StringType inputs (labels, filter criteria, etc.) sentinel to "" as before.
  #
  # Heuristic: normalize the name (lowercase, strip [_-.]), then require the
  # token "dataspace" as a whole word AT the head OR AT the tail of the string,
  # not just anywhere in it. This catches: dataSpaceApiName, defaultDataspace,
  # data_space, DATA_SPACE_NAME, my.dataspace, dataspaceId — while rejecting
  # accidental substrings like "metadataspec" or "dataSparkline" that happen to
  # contain the letters d-a-t-a-s-p in sequence.
  def is_dataspace_carrier(name):
    (name | ascii_downcase | gsub("[_.\\-]"; ""))
    | test("(^dataspace|dataspace$|^dataspacename$|dataspaceapiname$|dataspaceid$)");

  def sentinel(name; t):
    if   t == "DataSpaceType"                                 then {dataSpaceName: $ds}
    elif t == "StringType"  and is_dataspace_carrier(name)    then $ds
    elif t == "StringType"                                    then ""
    elif t == "BooleanType"                                   then false
    elif t == "NumberType"                                    then 0.0
    else null end;

  [ (.variables // {})
    | to_entries[]
    | select(.value.required == true or .key == "isTest")
    | . as $e
    | ( if ($e.value | has("defaultValue")) and ($e.value.defaultValue != null)
        then $e.value.defaultValue
        elif $e.value.required == true
        then sentinel($e.key; ($e.value.variableType.type // $e.value.variableType))
        elif $e.key == "isTest"
        then false
        else null end
      ) as $v
    | select($v != null)
    | {($e.key): $v}
  ] | add // {}
')

# Warn on any required var whose variableType.type has no sentinel — the row was
# silently dropped above. Surface to stderr so the caller can supply a value.
UNKNOWN_TYPES=$(echo "$VARS_JSON" | jq -r '
  (.variables // {})
  | to_entries[]
  | select(.value.required == true)
  | select(((.value | has("defaultValue")) | not) or (.value.defaultValue == null))
  | . as $e
  | ($e.value.variableType.type // $e.value.variableType) as $t
  | select($t != null)
  | select(["DataSpaceType","StringType","BooleanType","NumberType"] | index($t) | not)
  | "\($e.key) (variableType.type=\($t))"
')
if [ -n "$UNKNOWN_TYPES" ]; then
  echo "WARN: required variables with null default AND unrecognized variableType — silently skipped, caller must supply values:" >&2
  echo "$UNKNOWN_TYPES" | sed 's/^/  - /' >&2
fi

# Belt-and-braces: unconditionally inject `isTest: false` if not already present.
# Wire rule E — some templates (e.g. sfdc_internal__servicecloudinsights) reference
# `Variables.isTest` in their readiness EL expressions WITHOUT declaring `isTest`
# in their /configuration response's `.variables` map. Gating on `.variables | has("isTest")` misses these
# and causes the wall-of-DMO-not-ready false negative. Always inject.
TEMPLATE_VALUES_RAW=$(echo "$TEMPLATE_VALUES_RAW" | jq '. + (if has("isTest") then {} else {isTest: false} end)')

# ---- Pass 1b: coerce every NumberType value to a decimal literal (wire rule H) --
# jq collapses `360.0` back to `360` on JSON re-serialization in most versions —
# so we use Python for this pass. Load the two inputs, walk templateValues, and
# convert any integer whose key was declared NumberType in /configuration's `.variables` into a
# float. `json.dumps` in Python DOES preserve the "360.0" form for float values.
TEMPLATE_VALUES_RAW=$(python3 -c "
import json, sys
tv = json.loads(sys.argv[1])
vs = json.loads(sys.argv[2])
num_keys = {
    k for k, v in (vs.get('variables') or {}).items()
    if (v.get('variableType') or {}).get('type') == 'NumberType'
    or v.get('variableType') == 'NumberType'
}
for k in list(tv):
    if k in num_keys and isinstance(tv[k], int) and not isinstance(tv[k], bool):
        tv[k] = float(tv[k])
print(json.dumps(tv))
" "$TEMPLATE_VALUES_RAW" "$VARS_JSON")

# ---- Pass 2: resolve {{Variables.X.Y}} placeholders client-side (wire rule F) --
# Some templates ship defaults like {"objectName": "{{Variables.CaseContactReasonObj.objectName}}"}.
# The readiness endpoint does NOT expand these — you must inline the referenced value
# before POSTing. Walk the map recursively, substitute every {{Variables.X.Y[...]}}
# token with the resolved value from the same map, and iterate until fixed point
# (a resolved value may itself contain another placeholder).
resolve_placeholders() {
  local input="$1"
  local prev=""
  local iters=0
  # Cap iterations to catch pathological cycles — 8 passes is plenty in practice.
  while [ "$input" != "$prev" ] && [ $iters -lt 8 ]; do
    prev="$input"
    input=$(echo "$input" | jq --argjson root "$input" '
      # Resolve {{Variables.X.Y.Z...}} tokens against the root map.
      # Contract: strings without a placeholder pass through UNCHANGED. If the
      # ENTIRE string is a single placeholder AND the resolved value is a non-
      # string (object/array/number/bool), return that value verbatim to preserve
      # structure. If the string is a template mixing placeholder(s) with text,
      # each token is stringified and substituted in place (all occurrences).
      #
      # Notes on prior failure modes:
      #  - `capture(...)?` returns jq-empty on no-match; combined with
      #    `with_entries(.value |= walk_resolve(root))` it nulled every non-
      #    placeholder string. Gate with `test(...)` first.
      #  - Anchored `capture` only handles ONE placeholder per pass. `gsub`
      #    with a named-capture regex handles all occurrences.
      #  - `reduce .[$k]` crashes with "Cannot index string" if an intermediate
      #    path segment is a scalar. Guard the step.
      def lookup_path(root; path_str):
        (path_str | split(".")) as $keys
        | reduce $keys[] as $k (root;
            if . == null or (type != "object") then null
            else .[$k] end);

      def resolve_str(s; root):
        if (s | test("\\{\\{Variables\\.")) | not then s
        else
          # Whole-string single-placeholder fast path: return the raw resolved
          # value so we can substitute an object/number/array without stringifying.
          # Note: `capture(...)?` on no-match yields the empty stream (NOT null),
          # which combined with `with_entries(.value |= walk_resolve(root))` would
          # null the surrounding entry. `// null` collapses empty to a concrete null.
          ( ((s | capture("^\\{\\{Variables\\.(?<path>[A-Za-z_][A-Za-z0-9_.]*)\\}\\}$")?) // null) ) as $whole
          | if $whole != null then
              (lookup_path(root; $whole.path)) as $v
              | if $v == null then s else $v end
            else
              # Template-substitution path: replace every occurrence in place.
              # Unresolved tokens are left untouched so the outer loop can retry
              # (or the final WARN can surface them).
              (s | gsub("\\{\\{Variables\\.(?<path>[A-Za-z_][A-Za-z0-9_.]*)\\}\\}";
                        (lookup_path(root; .path)) as $v
                        | if $v == null then "{{Variables.\(.path)}}"
                          elif ($v|type) == "string" then $v
                          else ($v|tostring) end))
            end
        end;

      def walk_resolve(root):
        if type == "string" then resolve_str(.; root)
        elif type == "object" then with_entries(.value |= walk_resolve(root))
        elif type == "array" then map(walk_resolve(root))
        else . end;

      walk_resolve($root)
    ')
    iters=$((iters + 1))
  done
  # If unresolved placeholders remain, warn — do not silently POST them.
  if echo "$input" | grep -q '{{Variables\.'; then
    echo "WARN: unresolved {{Variables.X.Y}} placeholders remain in templateValues after $iters passes." >&2
    echo "$input" | jq -r '..
      | strings
      | select(test("\\{\\{Variables\\."))' >&2
  fi
  echo "$input"
}

TEMPLATE_VALUES=$(resolve_placeholders "$TEMPLATE_VALUES_RAW")
```

**If the response is empty (`.variables: {}`, or the key absent):** the template is a single-click install. `TEMPLATE_VALUES` will be `{}` — step 3 still needs the outer wrapper (wire rule A), and step 4 can either send `"templateValues": {}` or omit the field entirely. Both are accepted by the server.

**If the response returns `NOT_FOUND`:** the templateIdOrApiName doesn't resolve on this org. Re-check spelling and offer to re-list.

### 2b. Detect C360 Semantic Model base-model dependency (REQUIRED — do NOT skip)

Some allowlisted templates ship SDMs that **extend** the shared `C360SemanticModel_c360` semantic model (a.k.a. `sfdc_internal__C360UnifiedSemanticModel`). If the C360 app isn't already installed on the org — OR is installed at a stale `templateVersion` — the extending SDMs cannot resolve their base model and the install will fail late, after `POST /apps` has already spent minutes provisioning downstream assets. Detect this dependency BEFORE readiness and refuse cleanly.

**This check is a generic, app-agnostic prerequisite and is packaged as its own skill: [`tableau-next-c360-basemodel-gate`](../tableau-next-c360-basemodel-gate/SKILL.md).** Every allowlisted install except C360 itself must clear it. Run it now — **before Step 3 (readiness) and before Step 4 (create)** — in this same shell session:

> **Invoke the gate.** Read the literal relative path `./.afv/skills/tableau-next-c360-basemodel-gate/SKILL.md`, resolved relative to your current working directory (the workspace root) — do **NOT** build a path from memory, and do **NOT** use any absolute or `globalStorage` path; if this read fails, **STOP and report** (never substitute a remembered path); secondary fallback ONLY if `./.afv/skills/` is absent: the HOME-relative `~/.claude/skills/tableau-next-c360-basemodel-gate/SKILL.md` — and execute its steps against `$ORG_ALIAS` in the current shell. It resolves the HOME/COMPANION multi-org role, detects the C360 base-model dependency in the caller template's `/assets`, and enforces the mandatory 3-step verification (SDM presence → installed C360 app `SuccessStatus` → templateVersion parity). It returns **PROCEED** (all clear) or **REFUSE / STOP** with an actionable message.

**Hard gate — do NOT continue past this point unless the gate returned PROCEED.** If it REFUSES or STOPs, surface its message verbatim and halt; do not run Step 3.

**Non-bypassable invariants (unchanged — enforced inside the gate skill):**
- **Skip iff installing C360 itself.** When `$TEMPLATE_NAME_OR_ID == "sfdc_internal__C360UnifiedSemanticModel"` the gate is a no-op — a template does not depend on itself.
- **Whitelist-green only.** Only `SuccessStatus` / `SuccessWithWarningsStatus` count as an installed C360 app; `InProgressStatus` / `FailedStatus` never seed the installed version.
- **HOME vs COMPANION asymmetry.** HOME auto-remediates a missing/stale C360 inline (self-install + `update_app`); COMPANION refuses a shared-HOME mutation by default and only proceeds on explicit opt-in (`TABNEXT_ALLOW_SHARED_HOME_C360_UPDATE=1` or a TTY `y`).
- **templateVersion parity = HARD STOP.** An unreadable installed version OR an unreadable current template version refuses — there is no soft-degrade path.

**Outputs the gate leaves in your shell (Steps 4 and 6b depend on these — run the gate in the SAME shell as the rest of this skill):** `$ORG_ROLE` (HOME / COMPANION / UNKNOWN), `$RESOLVED_ORG_FOR_C360` (= `$ORG_ALIAS` on HOME, = `$HOME_ORG_ALIAS` on COMPANION), and `$HOME_ORG_ALIAS`. The Step-4 target-org guard and the Step-6b update path read these directly. If your harness ran the gate in a separate shell, re-run its `resolve_c360_gate_orgs` in this shell before Step 4 so these variables are set.

> **Cross-reference note.** Other steps in this skill mention the sub-step numbers **2b.0 / 2b.2 / 2b.3 / 2b.4 / 2b.5** and the helper functions **`resolve_c360_gate_orgs`**, **`wait_for_c360_sdm_visible`**, **`install_c360_on_home_and_wait_for_sync`**, and **`compare_versions`** — these now live inside the `tableau-next-c360-basemodel-gate` skill (the numbering and function names are preserved verbatim there). Those mentions are explanatory; the code that runs them executes inside the gate.

### 3. Check readiness

**Body construction — wire rule A applies:**

```bash
# Guard: TEMPLATE_VALUES must be valid JSON before we splice it. If step 2 was
# skipped or produced nothing, default to {} — the outer wrapper is still required.
[ -z "$TEMPLATE_VALUES" ] && TEMPLATE_VALUES='{}'

# Write the readiness body to a temp file so `--body '@file'` parses it directly.
# `mktemp` without -t is portable on macOS + Linux; the trailing suffix requires GNU
# `mktemp --suffix=.json`, which isn't universal, so we rename after.
READINESS_BODY_TMP=$(mktemp /tmp/readiness_body.XXXXXX)
READINESS_BODY_FILE="${READINESS_BODY_TMP}.json"
mv "$READINESS_BODY_TMP" "$READINESS_BODY_FILE"

# Compose the body via jq so we never emit malformed JSON when TEMPLATE_VALUES is {}.
echo "$TEMPLATE_VALUES" | jq '{templateValues: .}' > "$READINESS_BODY_FILE"

sf api request rest "$API_BASE/templates/$TEMPLATE_NAME_OR_ID/readiness" \
  --target-org "$ORG_ALIAS" --method POST \
  --body "@$READINESS_BODY_FILE" \
  --header "Content-Type: application/json" \
  | jq '.'

rm -f "$READINESS_BODY_FILE"
```

Inspect the response's status field. Not every template ships a `readiness.json` — for templates without one, the platform's `OrgReadinessAssembler.assemble()` catches `AppFrameworkErrorCode.ChainNotFound` and returns `SuccessWithWarningsStatus`, which reads as green but means "we didn't actually check anything." **Treat `SuccessWithWarnings` as a soft-yes, not a hard-yes.**

**Failure modes:**
- `Status: Failed` in the readiness payload — surface the failure reasons verbatim (they name the DMO, permission, or feature flag that's missing). Do NOT proceed to install.
- `Status: Success` or `SuccessWithWarnings` — safe to proceed.
- `JSON_PARSER_ERROR: Value does not match expected type` — your body wasn't wrapped in `templateValues`. Re-read wire rule A.
- `BAD_REQUEST: variable name [dataSpaceApiName] ... not of expected type [String]` — the template declares `dataSpaceApiName` as `StringType` but you sent the object form. Wire rule C — dispatch on `variableType.type`.
- `BAD_REQUEST: The variable name [dataSpaceApiName] with value [default] and type [String] is not of expected type [Object]` — the template declares `dataSpaceApiName` as `DataSpaceType` but you sent a bare string. Wire rule C — dispatch on `variableType.type`.
- `BAD_REQUEST: Object [{{Variables.X.Y}}] in variable [Z] is unknown, not supported, or is invalid` — a variable default contains a `{{Variables.X.Y}}` placeholder that wasn't resolved client-side before POSTing. Wire rule F — step 2's builder resolves these; if you constructed `templateValues` by hand, run the placeholder-resolution pass.
- **Every DMO reported "not ready" despite existing on the org** — the template's readiness EL expressions reference a variable (typically `isTest`) that isn't bound in your `templateValues`. Wire rule E — sentinel-inject `isTest: false` and retry. Step 2's builder does this automatically when the variable is declared on the template.

### 4. Create the app

Confirm with the user before this step — it's the first write. Show:
- Template apiName + label
- The label + apiName the new installed app will have
- The variables map you're about to send (values only, no secrets)

**Body construction — wire rules B + C apply:**

```bash
APP_NAME="${APP_NAME:-MyApp_$(date +%Y_%m_%d_%H%M)}"   # user's choice — see naming rules
APP_LABEL="${APP_LABEL:-My App}"                       # user's choice
[ -z "$TEMPLATE_VALUES" ] && TEMPLATE_VALUES='{}'               # from step 2

# ---- Pre-POST safety: enforce maxAppCount (fixes S2-I) --------------------
# Some templates enforce a per-org install cap (e.g. ServiceInsights=5,
# SalesInsightsTN=1, Employee/Service_Agent_Analytics=1, C360UnifiedSemanticModel=1).
# Hitting the cap surfaces reactively as
# `MAXAPPSEXCEEDED` from `POST /apps`. Check FIRST so the user gets a clean
# "you're at the cap, delete an existing app or pick a new template" message
# instead of a half-written client-timeout state.
TEMPLATE_META=$(sf api request rest "$API_BASE/templates/$TEMPLATE_NAME_OR_ID" \
  --target-org "$ORG_ALIAS" --method GET)
MAX_APPS=$(echo "$TEMPLATE_META" | jq -r '.maxAppCount // .maxAppsCount // empty')

if [ -n "$MAX_APPS" ] && [ "$MAX_APPS" != "null" ]; then
  # Count installed apps for THIS template by both the raw input AND the resolved id.
  RESOLVED_TEMPLATE_ID=$(echo "$TEMPLATE_META" | jq -r '.id // empty')
  CURRENT_COUNT=$(sf api request rest "$API_BASE/apps?type=App" \
    --target-org "$ORG_ALIAS" --method GET \
    | jq -r --arg t "$TEMPLATE_NAME_OR_ID" --arg tid "$RESOLVED_TEMPLATE_ID" '
        (.apps // .items // .records // [])
        | map(select(
            (.templateSourceId == $t) or
            (.templateSourceId == $tid) or
            (.templateApiName  == $t)
          ))
        | length
      ')
  if [ "$CURRENT_COUNT" -ge "$MAX_APPS" ] 2>/dev/null; then
    echo "Refusing to create: $TEMPLATE_NAME_OR_ID enforces maxAppCount=$MAX_APPS and $CURRENT_COUNT already installed." >&2
    echo "Delete an existing installation (step 6) or pick a different allowlisted template, then retry." >&2
    return 1 2>/dev/null || exit 1
  fi
fi

# ---- Pre-POST baseline snapshot (fixes S2-G) -------------------------------
# Capture the current /apps ids BEFORE the POST so timeout-recovery can identify
# the NEW record unambiguously — matching on name alone is fragile if a stale
# record with the same name exists (partial delete, propagation lag) or if a
# concurrent operator kicks off a same-named install in the same window.
BASELINE_APP_IDS=$(sf api request rest "$API_BASE/apps?type=App" \
  --target-org "$ORG_ALIAS" --method GET \
  | jq -c '[ (.apps // .items // .records // [])[] | .id ]')
BASELINE_TS=$(date +%s)

CREATE_APP_BODY_TMP=$(mktemp /tmp/create_app_body.XXXXXX)
CREATE_APP_BODY_FILE="${CREATE_APP_BODY_TMP}.json"
mv "$CREATE_APP_BODY_TMP" "$CREATE_APP_BODY_FILE"

# Compose via jq so shell interpolation never produces malformed JSON. If TEMPLATE_VALUES
# is {} we still include the key — the server accepts empty templateValues, and doing it
# this way keeps one code path for both single-click and variable-driven installs.
jq -n \
  --arg tid   "$TEMPLATE_NAME_OR_ID" \
  --arg label "$APP_LABEL" \
  --arg name  "$APP_NAME" \
  --argjson tv "$TEMPLATE_VALUES" \
  '{templateSourceId: $tid, label: $label, name: $name, templateValues: $tv}' \
  > "$CREATE_APP_BODY_FILE"

# If you prefer to omit templateValues entirely for a single-click install, use:
#   jq 'del(.templateValues)' "$CREATE_APP_BODY_FILE" > "${CREATE_APP_BODY_FILE}.tmp" && mv "${CREATE_APP_BODY_FILE}.tmp" "$CREATE_APP_BODY_FILE"
# (Or use `sponge` from moreutils if available.) Both shapes are accepted by the v67 endpoint; keeping the key is simpler.

# ---- Step-4 target-org guard (enforces Install-target thumb rule) ---------
# The caller-template install ALWAYS targets $ORG_ALIAS — never HOME, never
# $RESOLVED_ORG_FOR_C360. Refuse if the effective target has drifted OR if the
# template we're about to POST is C360 itself (C360 belongs to the 2b.3 prereq
# path, not step 4). Rule of thumb: if $ORG_ALIAS is a COMPANION and
# $TEMPLATE_NAME_OR_ID is a consumer template, we MUST be targeting the
# companion here — a HOME target means somebody merged the C360-prereq install
# with the caller-template install. That's the mistake this guard catches.
INSTALL_TARGET_ORG="$ORG_ALIAS"
if [ "$TEMPLATE_NAME_OR_ID" = "sfdc_internal__C360UnifiedSemanticModel" ] \
   && [ "${ORG_ROLE:-UNKNOWN}" = "COMPANION" ]; then
  cat >&2 <<MSG

REFUSING: Step 4 is about to POST a C360 install directly against companion
$ORG_ALIAS. C360 belongs on the paired HOME ($RESOLVED_ORG_FOR_C360), not on
a companion — companions consume C360 via multi-org publish, they do not host
the C360 app record. The C360 prereq install is driven by step 2b.3, targeting
\$RESOLVED_ORG_FOR_C360 automatically. If you reached step 4 with a C360
template on the companion, one of the following is wrong:

  1. \$TEMPLATE_NAME_OR_ID was set to sfdc_internal__C360UnifiedSemanticModel
     when the user actually asked for a different allowlisted template.
  2. Step 2b was bypassed / short-circuited.

Re-invoke this skill with the caller template the user asked for and let
2b.3 handle the C360 prereq automatically.
MSG
  return 1 2>/dev/null || exit 1
fi
if [ "${ORG_ROLE:-UNKNOWN}" = "COMPANION" ] \
   && [ -n "${HOME_ORG_ALIAS:-}" ] \
   && [ "$INSTALL_TARGET_ORG" = "$HOME_ORG_ALIAS" ]; then
  cat >&2 <<MSG

REFUSING: Step 4 target-org drift detected — INSTALL_TARGET_ORG resolved to
\$HOME_ORG_ALIAS ($HOME_ORG_ALIAS) but \$ORG_ALIAS is $ORG_ALIAS (a COMPANION).
Consumer templates (SalesInsightsTN, ServiceInsights, Employee_Agent_Analytics,
Service_Agent_Analytics) install on the COMPANION, not on the HOME. The HOME
is the C360 publisher only. See "Install-target thumb rule" above.

If you truly meant to install this template on the HOME, re-invoke the skill
with \$ORG_ALIAS = $HOME_ORG_ALIAS (i.e. run it against the HOME alias
directly). Do NOT try to talk step 4 into targeting HOME from a COMPANION run.
MSG
  return 1 2>/dev/null || exit 1
fi

RESPONSE=$(sf api request rest "$API_BASE/apps" \
  --target-org "$INSTALL_TARGET_ORG" --method POST \
  --body "@$CREATE_APP_BODY_FILE" \
  --header "Content-Type: application/json")

APP_ID=$(echo "$RESPONSE" | jq -r '.id // .app.id // empty')
echo "New app id: $APP_ID"

rm -f "$CREATE_APP_BODY_FILE"
```

**Client-timeout fallback (sf-CLI default is 2 min).** `sf api request rest` blocks on the HTTP response even though the install itself is async. Long-running templates (ITSM, ServiceInsights, Billing Central) can exceed the client timeout even though the server has already accepted the install and started work. If `$APP_ID` comes back empty OR the CLI dies with "Command timed out after 2m 0s", recover the app id by diffing `/apps` against the baseline captured before the POST — this is unambiguous even when a stale same-named record exists:

```bash
if [ -z "$APP_ID" ]; then
  echo "POST timed out client-side — attempting to recover the app id from /apps."
  # Small backoff so the record has settled through the write path.
  sleep 5
  # Use `?type=App` (fixes S2-D) so we get installed apps, not templates. The
  # unfiltered /apps endpoint on some releases returns BOTH apps and templates
  # under the same key and matching on .name races the wrong record.
  APPS_JSON=$(sf api request rest "$API_BASE/apps?type=App" \
    --target-org "$ORG_ALIAS" --method GET)

  # ---- Primary recovery path: baseline diff (fixes S2-G) ------------------
  # Any id present now but NOT in $BASELINE_APP_IDS is the record this POST
  # created. This is robust to (a) name collisions with stale records that
  # existed before we started, and (b) concurrent operators — as long as the
  # NEW id's .name equals $APP_NAME it's ours.
  if [ -n "$BASELINE_APP_IDS" ]; then
    APP_ID=$(echo "$APPS_JSON" | jq -r \
      --argjson baseline "$BASELINE_APP_IDS" \
      --arg name "$APP_NAME" '
      (.apps // .items // .records // [])
      | map(select( (.id as $i | $baseline | index($i)) | not ))
      | map(select(.name == $name))
      | .[0].id // empty
    ')
    [ -n "$APP_ID" ] && echo "Recovered app id via baseline diff: $APP_ID"
  fi

  # ---- Secondary recovery path: name match (existing behavior) ------------
  # If baseline was empty (first run) or the diff produced nothing, fall back
  # to matching on .name alone. `name` is unique per org, so this still lands
  # on the right record in the common case.
  if [ -z "$APP_ID" ]; then
    APP_ID=$(echo "$APPS_JSON" | jq -r \
      --arg name "$APP_NAME" \
      '(.apps // .items // .records // []) | .[]? | select(.name == $name) | .id' \
      | head -n 1)
    [ -n "$APP_ID" ] && echo "Recovered app id via name match: $APP_ID"
  fi

  [ -z "$APP_ID" ] && echo "Could not recover app id — check the org UI or GET $API_BASE/apps?type=App directly, and follow any .nextPageUrl if the list is paginated."
fi
```

Match strategy: baseline-diff FIRST (unambiguous even with name collisions or concurrent operators), name-match as fallback. `templateSourceId` on the record may be the resolved template id (`0Nk…`) even when you POSTed the apiName, so equality on the raw input breaks — that's why we don't filter on it. Do NOT retry the POST — the original request is very likely still in flight server-side, and a retry that succeeds returns `DUPLICATE_VALUE`.

The response returns the new app record and a job/status pointer. **The install is async.** `create_app` completing successfully means the job was accepted, not that the app is fully installed. Capture the returned `id` verbatim — that's what step 5's poll and step 6's rollback need.

**Naming rules the platform enforces:**
- `name` must be a valid Salesforce identifier: `[A-Za-z][A-Za-z0-9_]*`, ≤ 40 chars, no double underscores, no reserved suffixes (`__c`, `__mdt`, etc.).
- `name` must be unique on the org — reusing an existing installed-app apiName returns `DUPLICATE_VALUE`.
- `label` is free-text but shows up in the app launcher; keep it short and human-readable.

**Common failures:**
- `JSON_PARSER_ERROR: Found unexpected object property: + userinputsforsingleclickdeploy` — you're using an old MCP-tool schema that leaks the wrong param name to the wire. Rename to `templateValues` at wire level. Wire rule B.
- `DUPLICATE_VALUE` — apiName is taken. Pick a new apiName or `delete_app` the existing one if user confirms.
- `BAD_REQUEST: variable name [dataSpaceApiName] ... not of expected type [String]` — wire rule C again.

### 5. Poll for install completion

Installs are async. Wire rule D applies — read `applicationStatus`, not `status`.

Wire-observed status vocabulary (as of 2026-08-24): `SuccessStatus`, `SuccessWithWarningsStatus`, `FailedStatus`, `InProgressStatus`, plus several in-flight variants that the platform emits at different phases of the chain — `NewStatus`, `QueuedStatus`, `PendingStatus`, `AwaitingActivationStatus`. Anything ending in `InProgressStatus`, `PendingStatus`, `QueuedStatus`, `NewStatus`, or `AwaitingActivationStatus` is in-flight and MUST keep the poll running; only `Success*` / `Failed*` are terminal. Treating an unknown suffix as terminal would break the poll on future in-flight variants — instead, default to KEEP-POLLING and require an explicit terminal-suffix match to break.

Failure detail fields also vary — the platform has shipped `failureReasons` (older), `failureReason` (singular), `installErrorMessage`, `errorMessage`, and `errors[].message` at different points. The dump below tries all of them and falls back to the raw payload so a `null` field never eats the actual error text.

```bash
POLL_INTERVAL=15
MAX_MINUTES=30
DEADLINE=$(( $(date +%s) + MAX_MINUTES * 60 ))

# Treat any status ending in one of these tokens as in-flight — future variants land here safely.
is_inflight() {
  case "$1" in
    *InProgressStatus|*PendingStatus|*QueuedStatus|*NewStatus|*AwaitingActivationStatus) return 0 ;;
    *) return 1 ;;
  esac
}

while true; do
  APP=$(sf api request rest "$API_BASE/apps/$APP_ID" \
    --target-org "$ORG_ALIAS" --method GET)
  APP_STATUS=$(echo "$APP" | jq -r '.applicationStatus // "Unknown"')
  echo "$(date '+%H:%M:%S') applicationStatus=$APP_STATUS"

  case "$APP_STATUS" in
    SuccessStatus)
      echo "Installed. Done."; break ;;
    SuccessWithWarningsStatus)
      echo "Installed with warnings:"
      # Dump the FULL app record — the platform has shipped .warnings, .installWarnings,
      # and .validationWarnings at different times; the fallback to `.` prints the raw
      # payload if none of the named fields carry the warning text.
      echo "$APP" | jq '{applicationStatus, warnings: (.warnings // .installWarnings // .validationWarnings // null), raw: .}'
      break ;;
    FailedStatus)
      # The failure-detail field has drifted across releases — try every known field
      # and print all non-null ones, then include the raw record as a belt-and-braces
      # so an unknown field name never surfaces as a bare `null`.
      echo "Install FAILED. Detail:"
      echo "$APP" | jq '{
        applicationStatus,
        failureReasons:      (.failureReasons      // null),
        failureReason:       (.failureReason       // null),
        installErrorMessage: (.installErrorMessage // null),
        errorMessage:        (.errorMessage        // null),
        errors:              (.errors              // null),
        raw:                 .
      }'
      break ;;
    Unknown|"")
      echo "Unexpected shape (no applicationStatus field):"
      echo "$APP" | jq '.'
      break ;;
    *)
      if is_inflight "$APP_STATUS"; then
        # In-flight variant (NewStatus, QueuedStatus, PendingStatus,
        # AwaitingActivationStatus, *InProgressStatus). Keep polling — the platform
        # can emit any of these before landing on a terminal Success*/Failed* state.
        :
      else
        # Truly unrecognized — dump and stop rather than looping forever.
        echo "Unrecognized status '$APP_STATUS' (neither terminal nor a known in-flight suffix). Dumping and stopping."
        echo "$APP" | jq '.'
        break
      fi
      ;;
  esac

  if [ "$(date +%s)" -ge "$DEADLINE" ]; then
    echo "Timed out after $MAX_MINUTES min at status=$APP_STATUS"
    break
  fi
  sleep "$POLL_INTERVAL"
done
```

Typical install duration: 3–7 min for single-DMO templates, 8–30 min for full-chain templates. Service Insights and Sales Insights TN are typically 8–15 min; Employee / Service Agent Analytics are chain-heavier and can run 15–25 min; C360 Semantic Model is typically 5–10 min. Set `MAX_MINUTES=30` (as above) for the allowlisted five.

### 6. Rollback on failure (optional but recommended)

If step 5 landed on `FailedStatus`, or the user changes their mind, delete the app:

```bash
# sf-CLI quirk: DELETE requires `--body '{}'` even though HTTP DELETE has no body.
# Omitting --body raises `SfError: No 'mode' found in 'body' entry` before the
# request is ever made. `{}` is the sentinel the CLI's HTTP wrapper expects.
sf api request rest "$API_BASE/apps/$APP_ID" \
  --target-org "$ORG_ALIAS" --method DELETE \
  --body '{}' \
  | jq '.'
```

`delete_app` is idempotent — deleting the same app twice is a no-op after the first success. Safe to retry on transient network faults. **Confirm with the user** before deleting an app that already reached `SuccessStatus` (they may be actively using it).

**Server-side propagation is async.** The DELETE returns 202/success quickly, but the app can take several minutes to fully unwind. Subsequent `GET /apps/{id}` returns `APPNOTFOUND` once it settles. If you're deleting to free a slot before a fresh install (e.g. `MAXAPPSEXCEEDED` on ITSM), poll `GET /apps/{id}` until `APPNOTFOUND` before retrying the create.

**DELETE returns HTTP 204 but the record refuses to unwind (active-flow blocker).** Wire-verified 2026-08-25 on a ServiceInsights install: the App Framework delete chain fans out to a `BulkDeleteAssets` job that walks every asset the failed install created — flow versions included. If ANY asset in that chain is a **flow version stuck in Active state**, the platform throws `CannotDeleteException: You cannot delete this flow version because it is active. Deactivate it, and try again.` inside the async job. The public DELETE call has ALREADY returned 204 because the request was accepted; the failure is server-side, in the background chain. `GET /apps/{id}` keeps returning the record indefinitely because no delete job ever completes.

**Diagnostic path (this is the ONLY reliable signal from the wire):**
1. Open the org UI: **Setup → App Hub** (search `app hub` in Setup). The stuck app appears with a `Failed` job named `BulkDeleteAssets` or `delete_tua`.
2. Expand the failed job — the right-hand pane shows `Failed to delete asset [301S…] reason [You cannot delete this flow version because it is active. Deactivate it, and try again.]`. The `301S…` prefix identifies a `Flow` sobject.
3. **Fix path:** In the org UI, navigate to **Setup → Flows**, find every flow whose API name matches an asset the template installed (Service Insights ships flows like `Contact_Reason_Data_Population`, `Case_Contact_Reason_Setup`, etc.), and click **Deactivate** on the active version. Confirm zero remaining `Active` versions.
4. Re-issue the DELETE (`sf api request rest "$API_BASE/apps/$STALE_ID" --method DELETE --body '{}' -i` — expect `HTTP/1.1 204` again). Within 30–60 s, `GET /apps?type=App` no longer returns the record.

**Wire-only detection is not possible in the current OAS.** Neither `GET /apps/{id}` nor `GET /apps/{id}/activities` surfaces the underlying `CannotDeleteException` in a machine-readable field — the only way to see it is the App Hub UI. When you observe DELETE-succeeded-but-record-persists for **more than ~5 minutes** after two attempts, assume active-flow (or another `CannotDelete*` asset) and route the user to App Hub with the exact steps above. Do NOT keep polling silently; the record will never unwind on its own.

**Why the fresh in-session FailedStatus deleted cleanly and the stale one didn't.** A fresh failure typically didn't get far enough down the create chain to touch flows — the asset set is thin, and DELETE unwinds seconds later. Stale FailedStatus records from a prior session often reached the "activate flows" step before failing, leaving active flows behind that block the delete-chain. Age of the record is a strong signal (5+ days old + won't unwind = suspect active flows first).

**Delete-by-name (fixes S2-H).** If you lost the app id — the create-app POST timed out client-side AND both baseline-diff and name-match recovery came back empty — the ONLY handle you have is the `name` the user supplied. Resolve the id from `/apps?type=App` and then delete:

```bash
# Usage: delete_app_by_name "$APP_NAME"
# Returns 0 on delete accepted (or when the app already didn't exist);
# returns 1 on ambiguous match (>1 app with the same .name) so the caller
# can escalate rather than delete the wrong record.
delete_app_by_name() {
  local target_name="$1"
  [ -z "$target_name" ] && { echo "delete_app_by_name: name required" >&2; return 2; }

  local apps_json id_count target_ids target_id
  apps_json=$(sf api request rest "$API_BASE/apps?type=App" \
    --target-org "$ORG_ALIAS" --method GET)

  target_ids=$(echo "$apps_json" | jq -r \
    --arg name "$target_name" \
    '(.apps // .items // .records // []) | .[]? | select(.name == $name) | .id')
  id_count=$(printf '%s\n' "$target_ids" | grep -c . || true)

  if [ "$id_count" = "0" ]; then
    echo "No app named '$target_name' found — nothing to delete." >&2
    return 0
  fi
  if [ "$id_count" != "1" ]; then
    echo "Ambiguous: $id_count apps named '$target_name' exist. Refusing to delete." >&2
    echo "Resolve manually via GET $API_BASE/apps?type=App and pick the correct id." >&2
    return 1
  fi

  target_id=$(printf '%s\n' "$target_ids" | head -n 1)
  echo "Deleting app '$target_name' (id=$target_id)..."
  sf api request rest "$API_BASE/apps/$target_id" \
    --target-org "$ORG_ALIAS" --method DELETE \
    --body '{}' \
    | jq '.'
}
```

Only use `delete_app_by_name` when the id is genuinely lost — id-based DELETE is always preferable. The name-based path is deliberately strict about ambiguity: if the same name resolves to more than one record (partial delete state, race with a concurrent operator), it refuses rather than picking one at random.

### 6b. Update an existing app (API-driven Reconfigure)

`PUT /app-framework/apps/{id}` is the API-driven equivalent of App Hub → tile → **Update** / **Reconfigure**. It re-runs the template's install chain against the existing app record, upgrading it to the template's *current* `templateVersion` and re-applying `templateValues`.

**Primary use-case for this skill: auto-remediating a 2b.5 C360 template-version mismatch on the HOME org** — instead of stopping the caller's install and printing the App Hub Reconfigure walkthrough, the skill can (when the caller has confirmed) drive the update itself against `$RESOLVED_ORG_FOR_C360`, poll to `SuccessStatus`, and then resume the caller's install without a UI hop. Wire rule I above spells out the body shape; the helper below packages it.

**Guardrails (do NOT skip these):**
- **HOME-only.** The PUT MUST target the org that owns the app record. On the C360-mismatch remediation path that is `$RESOLVED_ORG_FOR_C360` (== `$ORG_ALIAS` when `ORG_ROLE=HOME`; == `$HOME_ORG_ALIAS` when `ORG_ROLE=COMPANION`). A companion session cannot mutate a HOME's app — cross-org sessions do not exist.
- **Companion blast radius.** The HOME's C360 app is shared by every paired companion. When called from a companion, this helper MUST confirm with the caller before running — auto-remediating on their behalf mutates a shared resource for every other companion pointing at the same HOME. The default is REFUSE + surface App Hub instructions; only PUT if the caller has explicitly opted in for this invocation.
- **Reuse the step-2 builder for `templateValues`.** Do not hand-craft a different body — the same required-var filter + sentinel injection + `isTest` inject + `{{Variables.X.Y}}` resolver + data-space resolution + NumberType decimal coercion must apply, or the update chain will 400 with the same errors create would.
- **`templateSourceId` from the existing app record, NOT from an assumed constant.** Read it from `GET /apps/{id}` and pass it through verbatim. The C360 template apiName is stable across releases today, but hardcoding it in the helper is a footgun for the day another allowlisted template needs update-in-place too.
- **Do NOT include `label` or `name` in the body.** Those are create-time fields and are read-only on update.
- **Auth.** Same as create: caller needs `AppFrameworkManageTemplate` on the target org. If PUT returns 403, the caller (or an admin on their behalf) is missing the permset that carries it — same remediation as precondition 2.

```bash
# ---- 6b. Update an existing app -------------------------------------------
# Usage:
#   update_app "$APP_ID" "$TARGET_ORG_ALIAS" "$TEMPLATE_VALUES_JSON"
#
# $TEMPLATE_VALUES_JSON is the fully-built templateValues map from step 2
# (post required-filter, post isTest inject, post placeholder resolution, post
# NumberType decimal coercion). It's the SAME value that would go into the
# CREATE body's `templateValues` field — the update endpoint accepts it byte
# for byte.
#
# On success the function prints the app id, sets $UPDATED_APP_ID as a
# side-effect, and returns 0. The caller then polls $API_BASE/apps/$APP_ID
# with the same loop as step 5 until `applicationStatus` is terminal
# (SuccessStatus / SuccessWithWarningsStatus / FailedStatus).

update_app() {
  local app_id="$1"
  local target_org="$2"
  local template_values_json="$3"

  if [ -z "$app_id" ] || [ -z "$target_org" ]; then
    echo "update_app: app_id and target_org are required." >&2
    return 2
  fi
  # Default to `{}` if the caller passes an empty/blank templateValues — the
  # server accepts empty templateValues on update (nothing to change), same as
  # create. Keeps one code path.
  if [ -z "$template_values_json" ]; then
    template_values_json='{}'
  fi

  # Look up the current app record to (a) confirm it exists on this org and
  # (b) source the templateSourceId. Do NOT hardcode the apiName here — some
  # allowlisted templates live under different apiNames across releases.
  local current_app_json template_source_id current_status
  current_app_json=$(sf api request rest "$API_BASE/apps/$app_id" \
    --target-org "$target_org" --method GET 2>/dev/null || true)

  # `.templateSourceId` is the canonical field; some releases expose the same
  # value at `.templateApiName`. Prefer templateSourceId when both are present.
  template_source_id=$(echo "$current_app_json" | jq -r '
    .templateSourceId // .templateApiName // empty
  ')
  current_status=$(echo "$current_app_json" | jq -r '
    .applicationStatus // .status // empty
  ')

  if [ -z "$template_source_id" ]; then
    echo "update_app: could not resolve templateSourceId from GET /apps/$app_id on $target_org." >&2
    echo "Raw response follows:" >&2
    echo "$current_app_json" | jq '.' >&2 2>/dev/null || echo "$current_app_json" >&2
    return 1
  fi

  # Refuse the PUT if the app is currently mid-install. The server would 409
  # ("app is being modified"), but a clean up-front refusal keeps the message
  # actionable — poll to terminal first, THEN update.
  case "$current_status" in
    InProgressStatus|PendingStatus|NewStatus)
      echo "update_app: app $app_id on $target_org is in $current_status — refusing PUT." >&2
      echo "Wait for the app to reach a terminal status (Success*/Failed*) before updating." >&2
      return 1
      ;;
  esac

  # Compose the PUT body via jq so `--body @file` gets valid JSON regardless
  # of what shell interpolation might do to embedded quotes/backslashes.
  local update_body_file="${TMPDIR:-/tmp}/update_app_${app_id}.$$.json"
  jq -n \
    --arg tsid "$template_source_id" \
    --argjson tv "$template_values_json" \
    '{templateSourceId: $tsid, templateValues: $tv}' \
    > "$update_body_file"

  echo "PUT $API_BASE/apps/$app_id (target-org=$target_org, templateSourceId=$template_source_id) ..." >&2

  local put_response
  put_response=$(sf api request rest "$API_BASE/apps/$app_id" \
    --target-org "$target_org" --method PUT \
    --body "@$update_body_file")
  local rc=$?
  rm -f "$update_body_file"

  if [ "$rc" != "0" ]; then
    echo "update_app: PUT failed (rc=$rc). Raw response:" >&2
    echo "$put_response" >&2
    return 1
  fi

  echo "$put_response" | jq '.' >&2 2>/dev/null || echo "$put_response" >&2

  # Sanity: the response should carry the same app id. Surface a warning if not
  # — caller-side polling still works via the passed-in $app_id.
  local returned_id
  returned_id=$(echo "$put_response" | jq -r '.id // .app.id // empty')
  if [ -n "$returned_id" ] && [ "$returned_id" != "$app_id" ]; then
    echo "update_app: WARNING — response .id ($returned_id) != input app_id ($app_id)." >&2
  fi

  UPDATED_APP_ID="$app_id"
  return 0
}

# ---- Poll the update to terminal (reuse step 5's shape) --------------------
# The update runs asynchronously — after PUT returns, poll GET /apps/{id}
# until applicationStatus is terminal. Same wire rule D as step 5 (check
# .applicationStatus, not .status; treat *InProgress*/*Pending*/*New* as
# in-flight; treat Success*/Failed*/Cancelled as terminal).
poll_update_to_terminal() {
  local app_id="$1"
  local target_org="$2"
  local cap_secs="${3:-1800}"   # default 30 min

  local deadline status app_resp
  deadline=$(( $(date +%s) + cap_secs ))
  while [ "$(date +%s)" -lt "$deadline" ]; do
    app_resp=$(sf api request rest "$API_BASE/apps/$app_id" \
      --target-org "$target_org" --method GET 2>/dev/null || true)
    status=$(echo "$app_resp" | jq -r '.applicationStatus // .status // empty')
    case "$status" in
      SuccessStatus|SuccessWithWarningsStatus)
        echo "[6b] update SUCCEEDED: $app_id -> $status" >&2
        return 0
        ;;
      FailedStatus|CancelledStatus)
        echo "[6b] update TERMINAL FAILURE: $app_id -> $status" >&2
        echo "$app_resp" | jq '.failureReasons // .' >&2 2>/dev/null || echo "$app_resp" >&2
        return 1
        ;;
      InProgressStatus|PendingStatus|NewStatus|"")
        sleep 30
        ;;
      *)
        # Unknown / release-drift status — sleep and retry a few times before
        # treating as unknown-terminal.
        echo "[6b] unknown applicationStatus '$status' on $app_id — waiting." >&2
        sleep 30
        ;;
    esac
  done

  echo "[6b] update did not reach terminal status within ${cap_secs}s on $target_org." >&2
  return 1
}
```

**Auto-remediation hook in 2b.5.** When the `CMP=-1` branch fires on `ORG_ROLE=HOME` (or on `ORG_ROLE=COMPANION` with explicit opt-in — see below), 2b.5 AUTOMATICALLY calls `update_app "$INSTALLED_C360_APP_ID" "$RESOLVED_ORG_FOR_C360" '{}'` followed by `poll_update_to_terminal "$INSTALLED_C360_APP_ID" "$RESOLVED_ORG_FOR_C360" 1800` before printing any user-facing STOP message. Pass an empty `{}` for `templateValues` — `$TEMPLATE_VALUES_RAW` holds the CALLING template's values, which are the wrong body for a C360 app update (same zero-inputs shape as `install_c360_on_home_and_wait_for_sync`'s create body). On success, re-fetch `INSTALLED_TEMPLATE_VERSION`/`CURRENT_TEMPLATE_VERSION` against `$RESOLVED_ORG_FOR_C360`, re-run `compare_versions`, and — on parity — **also require that the updated C360 SDM be visible in the caller's Data Cloud before flipping `AUTO_UPDATE_PARITY_REACHED=true`**. HOME path: the SDM is local and readiness will re-read it directly, so no additional wait is needed. COMPANION path: the updated SDM must PROPAGATE from `$RESOLVED_ORG_FOR_C360` (== HOME) to `$ORG_ALIAS` (== caller) via multi-org sync — 2b.5 calls `wait_for_c360_sdm_visible "$ORG_ALIAS" 0 "COMPANION post-update propagation" "$RESOLVED_ORG_FOR_C360"` (UNBOUNDED, same discipline as the install-time wait per the user's "keep polling till the SDM is available" instruction). Only after the wait returns 0 does the parity flag flip. If `update_app` returns non-zero (auth, missing app record, mid-flight, wire error), or `poll_update_to_terminal` times out, or the post-update version re-fetch does not confirm parity, or the post-update SDM-visibility wait exits on auth error, fall through to the manual Option A/B STOP message + wait-for-parity poll (the update may still be catching up server-side; the loop will pick it up). Under bash `case` the `break` keyword only exits an enclosing loop, so the parity-reached signal MUST be a flag (`AUTO_UPDATE_PARITY_REACHED`) that guards the STOPPING + wait-for-parity `while` + refusal block via an `if` — NOT a `break` statement inside the `case`.

**COMPANION opt-in gate for 2b.5.** On `ORG_ROLE=COMPANION` the auto-update is refused by default because `$RESOLVED_ORG_FOR_C360` is a shared HOME. Two opt-in signals unlock the same PUT + poll code path: (1) `TABNEXT_ALLOW_SHARED_HOME_C360_UPDATE=1` in the environment — appropriate for scripted / unattended runs where the operator has pre-authorized the shared-HOME reconfigure across all paired companions; (2) an interactive TTY confirm — when both stdin and stderr are TTYs, 2b.5 prints a blast-radius warning and prompts "Proceed with shared-HOME C360 update? [y/N]" with a 60 s `read -t` timeout; anything except `y/Y/yes/YES/Yes` (including timeout, empty, or `n`) declines. Declined opt-in falls through to the standard STOP + wait-for-parity path. When the opt-in is granted, log lines carry `role=COMPANION opt-in=env|tty` so the transcript records how the shared-HOME reconfigure was authorized. Absent both signals (no env var + no TTY, e.g. CI without a pre-set env var), the default is refuse.

**Companion HOME-alias auto-resume in `resolve_c360_gate_orgs()`.** When 2b.0 classifies the caller as COMPANION but no local `sf` alias resolves for `HOME_ORG_ID_15`, the helper prints the full onboarding STOPPING message (my-domain URL / permissions / `sf org login web` command / verify-alias jq recipe) AND then enters a bounded auto-resume loop (30 s cadence, 15-min cap) that re-runs the `sf org list --json | jq` alias lookup. As soon as the admin completes the `sf org login web` in another terminal on the same laptop, the loop picks up the newly-registered alias and returns with `HOME_ORG_ALIAS` set — the current run continues into 2b.3/2b.4/2b.5 without a re-invoke. If the cap elapses, the helper refuses with an explicit "did not appear within 15 min" message and the caller must re-invoke (Step 2b.0 will then re-probe DataMultiOrgConnection). The 30 s cadence + 15 min cap is calibrated for the typical browser-login round-trip (30–90 s) and avoids wedging on a stuck admin.

The wait-for-parity poll loop remains the outer safety net — it handles the case where the caller declined the auto-update, the caller is on the companion path with no explicit opt-in, or the update was driven by another process (a separate operator clicking Update in App Hub concurrently). PUT is a *shortcut*, not a *substitute*.

## Fast path (optional) — use MCP tools if they're connected

**The allowlist gate applies to this path too.** Before invoking any MCP tool that installs, creates, or checks readiness on a template, run `resolve_allowed_template` on the user's input AND run the step 1 double-gate check (Path B id resolution + `IS_ALLOWED` re-check). MCP tools do NOT enforce the allowlist internally — they wrap the raw App-Framework endpoints, so a `templateSourceId` outside the allowlist will install just as easily via `mcp__tableau-next-apps-mcp-beta__create_app` as via a raw `sf api request rest` call. The gate lives in THIS skill, not in the tools.

If any of these MCP servers are connected AND healthy, the caller MAY substitute them for the `sf api request rest` calls in steps 1–6 (**after passing the allowlist gate**) to save time on argument construction. The wire-shape rules A–D above still apply verbatim — these tools are thin wrappers around the same endpoints and inherit the same server-side validation.

| Step | project-codey preset | tableau-next-apps-mcp / -beta preset |
|---|---|---|
| 1 | `mcp__project-codey__list_tabnext_app_templates` | `mcp__tableau-next-apps-mcp-beta__list_tabnext_app_templates` |
| 2 | `mcp__project-codey__fetch_template_required_variables` | `mcp__tableau-next-apps-mcp-beta__fetch_template_required_variables` |
| 3 | `mcp__project-codey__check_template_readiness` | `mcp__tableau-next-apps-mcp-beta__check_template_readiness` |
| 4 | `mcp__project-codey__create_app` | `mcp__tableau-next-apps-mcp-beta__create_app` |
| 5 | `mcp__project-codey__dispatch_readonly` GET `/apps/{id}` (MVP1 ships no `get_app_status` preset) | `mcp__tableau-next-apps-mcp-beta__get_app_status` |
| 6 | `mcp__project-codey__delete_app` | `mcp__tableau-next-apps-mcp-beta__delete_app` |

**MCP-tool caveats:**
- Both wrappers were audited and fixed on 2026-08-18 (Python `install_create_app.py` `"values"`→`"templateValues"`; Java `InstallCheckTemplateReadinessHandler` always wraps in `templateValues`; `drive_install_flow.py` / `drive_datakit_deploy.py` use bare-string `dataSpaceApiName`). If you're on those or later builds, wire rules B and C are honored transparently. If you're on an older `project-codey` MCP where `create_app` still advertises `userInputsForSingleClickDeploy`, invoke `mcp__project-codey__dispatch` directly with a POST body that uses the correct OAS key `templateValues` (wire rule B) instead of the preset.
- If ANY MCP tool call sits silent for > 90s with no progress, treat it as timed out and fall back to `sf api request rest` for the remainder of the flow. The whole reason this skill is self-contained is to survive that failure mode.

## End-to-end example (Service Insights — allowlisted)

```text
User: "install Service Insights on my org"

Skill (this skill, running self-contained):

  # 0. Discover API version
  $ API_VERSION=$(sf api request rest "/services/data" --target-org my-org --method GET \
       | jq -r '[.[] | .version | tonumber | floor] | max | "v\(.).0"')
  → v67.0   (or whatever the org actually supports)
  $ API_BASE="/services/data/$API_VERSION/app-framework"

  # 0a. Allowlist gate — resolve user input to a canonical apiName
  $ TEMPLATE_NAME_OR_ID=$(resolve_allowed_template "service insights")
  → sfdc_internal__ServiceInsights
  # If the user had asked for "install ITSM" or "install Billing Central", this
  # would have printed REFUSED and the skill would have stopped here.

  # 1. Confirm the template exists on this org + capture id
  $ sf api request rest "$API_BASE/templates" --target-org my-org --method GET \
       | jq --arg n "$TEMPLATE_NAME_OR_ID" '.templates[] | select(.name == $n)'
  → { id: "0Nk…", name: "sfdc_internal__ServiceInsights", label: "Service Insights", ... }
  Confirm with user: "Install Service Insights (sfdc_internal__ServiceInsights)?"

  # 2. Variables come from GET /configuration — .variables is an object map at the top
  #    of the response; required==true + always-inject isTest go into templateValues
  $ sf api request rest "$API_BASE/templates/sfdc_internal__ServiceInsights/configuration" \
       --target-org my-org --method GET
  → { variables: { "dataSpaceApiName": { defaultValue: null, required: true,
                                          variableType: {type: "DataSpaceType"}, ... },
                    ... },
      ...other configuration keys... }
  # Resolve data space name FIRST (wire rule G):
  $ DATA_SPACE_NAME=$(sf api request rest "/services/data/$API_VERSION/ssot/data-spaces" \
       --target-org my-org --method GET | jq -r '(.dataSpaces // [] | .[0].name) // "default"')
  → "default"   (or "Corp_Ds", whatever the org actually has)

  # Step 2's builder (required filter + type-aware sentinels + always-inject isTest + placeholder resolution
  #                   + NumberType float coercion in Pass 1b):
  #   ServiceInsights's dataSpaceApiName is DataSpaceType → object form (wire rule C)
  #   isTest injected unconditionally as false (wire rule E)
  #   TEMPLATE_VALUES = {"dataSpaceApiName":{"dataSpaceName":"default"},"isTest":false}

  # 3. Readiness — always wrap in templateValues (wire rule A)
  $ echo '{"templateValues":{"dataSpaceApiName":{"dataSpaceName":"default"},"isTest":false}}' > /tmp/rb.json
  $ sf api request rest "$API_BASE/templates/sfdc_internal__ServiceInsights/readiness" \
       --target-org my-org --method POST --body '@/tmp/rb.json' --header "Content-Type: application/json"
  → { Status: "Success" }

  # 4. Create app (confirm write with user first)
  #   - Pre-POST: check maxAppCount (ServiceInsights=5) and snapshot /apps?type=App baseline.
  $ cat > /tmp/cb.json <<'EOF'
  {"templateSourceId":"sfdc_internal__ServiceInsights","label":"Service Insights","name":"ServiceInsights_App","templateValues":{"dataSpaceApiName":{"dataSpaceName":"default"},"isTest":false}}
  EOF
  $ sf api request rest "$API_BASE/apps" \
       --target-org my-org --method POST --body '@/tmp/cb.json' --header "Content-Type: application/json"
  → { id: "1zA…", applicationStatus: "InProgressStatus" }

  # 5. Poll — is_inflight() keeps looping through NewStatus / QueuedStatus /
  #           PendingStatus / AwaitingActivationStatus / InProgressStatus.
  $ # (see step 5 for the full loop with terminal + in-flight handling)
```

Total wall-clock: 8–15 min for Service Insights, 8–15 min for Sales Insights TN, 15–25 min for Employee / Service Agent Analytics, 5–10 min for C360 Semantic Model. `MAX_MINUTES=30` is the recommended cap.

## Anti-patterns (do NOT do these)

- **Don't install a non-allowlisted template.** Scope is Service Insights, Sales Insights TN, Employee Agent Analytics, Service Agent Analytics, and C360 Semantic Model. If the user asks for anything else (ITSM, Billing Central, C360InsightsStarterApp, etc.), refuse with the message under "Allowlist gate" and stop. Do NOT silently substitute "the nearest match" — that's a correctness bug.
- **Don't offer alternatives outside the allowlist in the refusal.** The refusal message deliberately does not list "here's what we could install instead" — that would defeat the scope guard.
- **Don't skip the allowlist gate on an id path.** If the user passed `0Nk…`, resolve the id to `.name` first and re-check the allowlist. Skipping this makes the id path an escape hatch around the whole restriction.
- **Don't skip step 3 (readiness).** Templates without a `readiness.json` return `SuccessWithWarnings` and are safe to proceed; templates that DO ship `readiness.json` (SalesInsightsTN, ServiceInsights, Employee_Agent_Analytics, Service_Agent_Analytics, C360UnifiedSemanticModel, ...) return real failure reasons the user needs to see.
- **Don't skip step 2b (C360 dependency detection).** If a template extends `C360SemanticModel_c360` and the C360 app isn't installed, readiness alone WILL NOT catch it — the install will fail late, after minutes of downstream provisioning. Refuse pre-install with the "install C360 first" message.
- **Don't confuse `check_template_readiness` with chain-node walking.** `POST /readiness` only fires when `readiness.json` exists. Walking `create-chain.json` for `DataCloudRowCountReadiness` / `AccessExpressionReadiness` nodes and evaluating each against downstream Data Cloud APIs is a separate concern (MVP2). Don't imply this skill covers that.
- **Don't retry `create_app` on `DUPLICATE_VALUE`.** apiName is taken — either delete the existing app first, or pick a new apiName.
- **Don't call `delete_app` speculatively.** It's destructive on the installed app AND all workspace assets bound to it. Only call it as a rollback for a failed / unwanted install, and always re-confirm before deleting an app that already reached `SuccessStatus`.
- **Don't paste the readiness body inline via `--body '{"…"}'`.** The sf-CLI's argument parsing mangles nested-quote escaping. Always write to a tempfile and pass `--body '@/path/to/file.json'`. The `@` prefix parses the file as JSON.
- **Don't hardcode the `dataSpaceApiName` wire shape.** Wire rule C is template-dependent: dispatch on `variableType.type` from step 2 (`DataSpaceType` → object, `StringType` → bare string). Hardcoding either form breaks on the other family of templates.
- **Don't POST `templateValues` containing `{{Variables.X.Y}}` placeholders.** Wire rule F — resolve them client-side before sending. Step 2's builder does this; if you hand-build the map, run the placeholder-resolution pass.
- **Don't ignore `isTest` when the template declares it.** Wire rule E — unbound `isTest` silently returns `valueOnError` for every DMO readiness check and makes a green install look like a wall of "DMO not ready" failures.
- **Don't break the poll on the first unknown status.** Wire rule D + the poll loop: only `Success*`/`Failed*` are terminal; anything ending in `InProgressStatus`/`PendingStatus`/`QueuedStatus`/`NewStatus`/`AwaitingActivationStatus` is in-flight and MUST keep the poll running. Defaulting to break-on-unknown truncates real installs when the platform ships a new in-flight variant.
- **Don't skip the pre-POST baseline snapshot.** S2-G — if the create-app POST times out client-side, name-only recovery races against stale same-named records and concurrent operators. Snapshot `/apps?type=App` ids BEFORE the POST and diff after.
- **Don't skip the `?type=App` filter on recovery lists.** S2-D — unfiltered `/apps` on some releases returns both apps and templates under one key; matching on `.name` alone lands on the wrong record.
- **Don't skip the pre-POST `maxAppCount` check.** S2-I — hitting the cap surfaces as `MAXAPPSEXCEEDED` with no partial write, but you've already paid the client-timeout cost. Read `.maxAppCount` from the template metadata first and count installed apps of the same `templateSourceId`.
- **Don't poll `GET /apps/{id}` forever after a DELETE that returned 204.** If the record still exists ~5 minutes after the DELETE (especially for stale multi-day-old FailedStatus records), the async `BulkDeleteAssets` chain is stuck — commonly on an active-flow blocker (`CannotDeleteException`). This is INVISIBLE on the wire. Route the user to **Setup → App Hub** to read the exact error, then to **Setup → Flows** to deactivate the blocker. See step 6's active-flow-blocker section.
- **Don't confuse `maxAppCount` (org-wide) with the per-data-space cap.** Wire-verified 2026-08-25: `ServiceInsights.maxAppCount=5` but the template ALSO enforces 2-per-data-space, which the OAS does not publish. The pre-POST `maxAppCount` guard alone will happily let you POST into a data space that's already at its per-data-space cap; the platform then returns `applicationStatus=FailedStatus` with `Can't have more than [N] per dataspace [X] for this template`. Filter the count by data space when the template is known to enforce a per-data-space cap.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Skill refuses with "not supported" / "not on the allowlist" | User requested a template outside the Service Insights / Sales Insights TN / Employee Agent Analytics / Service Agent Analytics / C360 Semantic Model allowlist | This is intended behavior. For other templates, use `sf api request rest` directly or a different skill. Do NOT re-invoke this one with the same input hoping for a different answer. |
| Allowlist gate reports "AMBIGUOUS_AGENT_ANALYTICS" | User said "agent analytics" and both `Employee_Agent_Analytics` and `Service_Agent_Analytics` are candidates | Ask the caller which one. Re-invoke with the full apiName. |
| Step 1 rejects a `0Nk…` id with "not on the allowlist" | User supplied a raw template id whose `.name` isn't one of the five allowlisted apiNames | Intended. Rewrite the request in terms of one of the allowlisted apiNames, or use a different skill. |
| Step 2b refuses with "C360 app ... is NOT installed" | Selected template extends `C360SemanticModel_c360` but the C360 Semantic Model app is not installed on this org | Install C360 Semantic Model first via this skill (`install C360 Semantic Model`), wait for `SuccessStatus`, then re-invoke for the dependent template. |
| Pre-POST `maxAppCount` guard refuses with "$N already installed" | Template caps per-org installs (e.g. SalesInsightsTN=1, ServiceInsights=5) and the org is at the cap | Delete an existing installation via step 6 (or `delete_app_by_name` if you've lost the id), wait for `APPNOTFOUND`, then retry. |
| Poll loop keeps running on `QueuedStatus` / `PendingStatus` / `NewStatus` / `AwaitingActivationStatus` | Those ARE in-flight variants — the loop is behaving correctly | No action needed. Chain-heavy templates (Agent Analytics especially) commonly spend 30–90 s in each of these before landing on `InProgressStatus`. |
| Poll loop breaks with "Unrecognized status '<X>' … Dumping and stopping" | The platform emitted a status whose suffix isn't in the terminal or in-flight allow-lists | Read the dumped payload — it's either a real new terminal state (add to the terminal `case`) or a new in-flight variant (add its suffix to `is_inflight`). Don't retry until the vocabulary is updated. |
| Recovery via `delete_app_by_name` returns "Ambiguous: N apps named X" | Two records with the same `.name` (partial delete state, or the previous install kept its name across a re-run) | Refuses deliberately. Resolve manually via `GET $API_BASE/apps?type=App`, pick the correct id, delete by id. |
| `list_tabnext_app_templates` returns `.templates: []` | Tableau Next not enabled OR user lacks visibility | Route user to Tableau Next enablement — out of scope for this skill |
| Templates endpoint itself returns `NOT_FOUND` | Org doesn't have App-Framework Connect API rolled out at the discovered version | Confirm org is on a supported release (v67.0+); re-run the `GET /services/data` version discovery |
| `GET /services/data` discovery fails or `$API_VERSION` ends up empty | sf-CLI not authenticated, org unreachable, or piping/`jq` step failed | Fix auth first (`sf org list --json`); then re-run the discovery. Do NOT fall back to hardcoded `v67.0` in a shipping build. |
| `$API_VERSION` renders as `v68.0.0` (three-part, invalid) and every downstream call 404s | jq's `tonumber` on `"68.0"` returns the float `68.0` and the format `"v\(.).0"` renders it as `v68.0.0` | Add `\| floor` between `tonumber` and `max` in the jq pipeline. The sanity `case` on `$API_VERSION` catches it as a belt-and-braces. |
| Step 2 jq raises `Cannot use null (null) as object key` | Used `.variables[]?` on the new response shape — `.variables` is an OBJECT MAP, not an array | Iterate with `.variables | to_entries[]` and read `.key` + `.value.defaultValue`. See step 2. |
| Step 2 produced a `templateValues` containing optional variables (other than `isTest`) | Wrong client-side filter — `?required=true` isn't supported by the server | Filter with `select(.value.required == true or .key == "isTest")` in the jq pipeline. Required vars belong in `templateValues`; `isTest` is the one deliberate exception (wire rule E). |
| `create_app` POST times out client-side (`Command timed out after 2m 0s`) with no `APP_ID` returned | sf-CLI blocks on the HTTP response; long-running installs exceed its 2-min default | Do NOT retry the POST — the original is still running server-side. Use the step 4 recovery block: `GET $API_BASE/apps`, filter on `.name == $APP_NAME` across `(.apps // .items // .records)`, take the first `.id`. Filtering on `templateSourceId` breaks when the POST used the apiName but the record stores the resolved id. |
| Step 6 DELETE returns `SfError: No 'mode' found in 'body' entry` before hitting the server | sf-CLI's HTTP wrapper requires a body arg even on DELETE | Pass `--body '{}'` on the DELETE call. See step 6. |
| Step 6 DELETE succeeds but subsequent `GET /apps/{id}` still returns the app | Server-side propagation is async | Poll `GET /apps/{id}` until it returns `APPNOTFOUND`; that can take a few minutes. |
| Step 6 DELETE returned 204 but `GET /apps/{id}` still returns the app after 5+ minutes | The async `BulkDeleteAssets` chain is stuck — commonly on an **active flow version** the platform refuses to delete (`CannotDeleteException: You cannot delete this flow version because it is active`). Wire-invisible: neither `/apps/{id}` nor `/apps/{id}/activities` surfaces this. | Route the user to **Setup → App Hub**, expand the failed `BulkDeleteAssets` / `delete_tua` job to read the exact `301S…` asset id and reason, then to **Setup → Flows** to deactivate every active version of the flows the template installed. Re-issue the DELETE — it unwinds within 30–60 s. See step 6's active-flow-blocker section. |
| User keeps retrying DELETE, each time getting 204 but the record persists | Same active-flow blocker as above. Retrying the DELETE does nothing — the server accepted the request; the async chain is what's failing | Stop retrying. Go to App Hub, read the failure reason, deactivate the flow(s), then delete once more. |
| `create_app` returns `MAXAPPSEXCEEDED` | Template caps installed-apps-per-org (ITSM = 1) and you've hit the cap | Delete the existing app (step 6 + wait for `APPNOTFOUND`), then retry. |
| `create_app` immediately returns `applicationStatus=FailedStatus` with `failureMessage: Can't have more than [N] per dataspace [X] for this template` | Template enforces a per-data-space cap that is DISTINCT from the org-wide `maxAppCount`. The pre-POST `maxAppCount` guard doesn't catch this because the count aggregates across data spaces. Wire-verified 2026-08-25 on ServiceInsights (per-data-space cap = 2). | Either (a) delete an existing install IN that data space (step 6 + wait for `APPNOTFOUND`, watching for the active-flow blocker), or (b) re-invoke with the data space variable pointing to a different data space. |
| `check_template_readiness` returns `SERVER_UNAVAILABLE: Server too busy` | Transient platform load | Wait 5 s and retry the same call — it's idempotent. |
| Variables endpoint returns `NOT_FOUND` | Template apiName / id typo, or template unpublished on this org | Re-list; ask user to pick from what's actually available |
| `check_template_readiness` returns `Status: Failed` with DMO-missing reasons | Data Cloud DMO the template needs isn't mapped on the org | Route user to CRM connection setup / DMO mapping (out of scope) |
| `check_template_readiness` returns `JSON_PARSER_ERROR: Value does not match expected type` | Body was bare `{}` or wrapped in the wrong key | Wire rule A — wrap as `{"templateValues": {...}}`. See step 3. |
| `create_app` returns `JSON_PARSER_ERROR: Found unexpected object property: + userinputsforsingleclickdeploy` | Old MCP-tool schema leaks to wire | Wire rule B — rename to `templateValues`, or fall back to `sf api request rest`. |
| Readiness or create returns `BAD_REQUEST: variable name [dataSpaceApiName] ... not of expected type [String]` | Template declares `dataSpaceApiName` as `StringType` but you sent the object form | Wire rule C — dispatch on `variableType.type`. `StringType` → bare `$DATA_SPACE_NAME` (resolved via wire rule G). |
| Readiness or create returns `BAD_REQUEST: The variable name [dataSpaceApiName] with value [<X>] and type [String] is not of expected type [Object]` | Template declares `dataSpaceApiName` as `DataSpaceType` but you sent a bare string | Wire rule C — dispatch on `variableType.type`. `DataSpaceType` → object `{"dataSpaceName": $DATA_SPACE_NAME}` (resolved via wire rule G). |
| Readiness returns HTTP 400 `TEMPLATEPARSEERROR: Data space [default] ... is unknown` or `Data space [<X>] ... is unknown` | Hardcoded `"default"` or a stale data space name that the org doesn't have | Wire rule G — resolve via `GET /ssot/data-spaces` first, then substitute the actual apiName. Never hardcode `"default"`. |
| Readiness returns HTTP 400 `CDP not enabled` | Data Cloud isn't provisioned on the org | Route to admin — enable Data Cloud. Not fixable client-side; do NOT retry the install. |
| Any App-Framework call (templates / variables / readiness / apps) returns HTTP 403 `ACCESS_DENIED` / `INSUFFICIENT_ACCESS` and the endpoint itself resolves | Caller is missing the `AppFrameworkManageTemplate` user permission | Have an admin assign a permission set carrying `AppFrameworkManageTemplate` ("Manage App Templates") to the caller, then retry. Distinct from the empty-templates-list 403, which is a feature-gate (Tableau Next not provisioned). |
| Readiness or create returns HTTP 400 `The variable name [X] with value [N] must be one of the following values [5.0, 10.0, ...]` | Sent a bare integer (`360`) for a `NumberType` variable | Wire rule H — coerce every `NumberType` value to a decimal literal (`360.0`) before POSTing. Step 2's Pass 1b does this via Python (jq re-serializes floats as ints in most versions). |
| Readiness returns `BAD_REQUEST: Object [{{Variables.X.Y}}] in variable [Z] is unknown, not supported, or is invalid` | A `{{Variables.X.Y}}` placeholder in a variable default wasn't resolved before POSTing | Wire rule F — run the placeholder-resolution pass from step 2 (walk the map, substitute against the same map, iterate to fixed point) before sending. |
| Readiness reports every DMO "not ready" for DMOs the org demonstrably has | Template's readiness EL expression references an unbound variable (typically `Variables.isTest`); EL fails silently, falls back to each check's `valueOnError` (usually `-1`) | Wire rule E — bind `isTest: false` in `templateValues`. Step 2's builder does this automatically when the variable is declared. |
| Readiness reports an EL `AccessExpressionReadiness` check like `ServiceIncludedAppAccess = false` | Org lacks the license / permission entitlement the template requires | Route to org admin — enable the missing license (e.g. Service Cloud / Service Intelligence). Not fixable client-side; do NOT retry the install. |
| `create_app` returns `DUPLICATE_VALUE` | An app with this apiName already exists on the org | Pick a new apiName, or `delete_app` the existing one if user confirms |
| `create_app` succeeds but subsequent `GET /apps/{id}` shows `applicationStatus: FailedStatus` | Async install chain hit a downstream failure | Read `.failureReasons[]`; if user gives up, `delete_app` to clean up |
| `GET /apps/{id}` shows `status: null` | Status field is on `applicationStatus`, not `status` | Wire rule D — read `applicationStatus`. |
| Any step returns `INVALID_SESSION_ID` / `Session expired` | sf-CLI credentials aged out | Ask user to re-run `sf org login web` and retry |
| MCP tool call sits silent > 90s | project-codey / tableau-next-apps-mcp is unresponsive | Abandon the MCP call and re-run that step via `sf api request rest`. That's exactly why this skill is self-contained. |
| `sf api request rest ... --body '{...}'` returns "url required" | sf-CLI arg parser mangled the inline body | Write body to a tempfile and use `--body '@/path/to/file.json'` — the `@` prefix parses the file as JSON. |

## Design rationale (why self-contained)

Two MCP wrappers (project-codey and tableau-next-apps-mcp/-beta) drifted from the App-Framework wire shape and returned opaque `JSON_PARSER_ERROR` / `BAD_REQUEST` errors when their schemas didn't match the OAS. On 2026-08-18 an `sfdc_internal__itsm` install on a live Data-Cloud-enabled ITSM sandbox succeeded in ~5.5 min via `sf api request rest` after project-codey MCP silently timed out for 30 min. Both wrappers were subsequently fixed, but the lesson stuck: **the skill owns the workflow end-to-end and treats MCP tools as an accelerator, not a dependency.**

This mirrors the pattern established in `skills/connect-headless-360-mcp/SKILL.md` and `skills/einstein-org-setup/SKILL.md`: platform-facing workflow skills that chain N already-existing tools/actions AND retain a canonical fallback path via `sf api request rest`.

## Related skills / references

- `skills/connect-headless-360-mcp/SKILL.md` — one-shot setup of the platform MCP server the tools run through. If tool calls fail with "no such tool" or "server not connected", this is the setup path.
- `skills/mcp-server-development/SKILL.md` — how to add a new install preset tool (e.g. a future `wait_for_app_installed` MVP2 tool).
- `skills/codey-gap-triage/SKILL.md` — routes gaps this skill can't fix (chain-node validation, per-template readiness overrides).
- Memory: [[project_itsm_install_wire_shapes_2026_08_18]] — origin of wire rules A/B/C/D.
- Memory: [[project_install_tabnext_app_skill_self_contained_2026_08_18]] — self-contained rewrite + wire rules E/F additions (`isTest` EL binding, `{{Variables.X.Y}}` placeholder resolution, `dataSpaceApiName` template-dependent shape).
- Memory: [[project_codey_install_tabnext_app_skill_2026_08_17]] — MVP1 skill authoring history.
- Memory: [[project_codey_mcp_5tool_install_mvp1_2026_08_17]] — the five underlying MCP tools this skill can optionally use.
