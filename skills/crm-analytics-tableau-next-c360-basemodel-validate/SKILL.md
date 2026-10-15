---
name: crm-analytics-tableau-next-c360-basemodel-validate
description: "Generic, app-agnostic prerequisite gate invoked by the tableau-next-app-install skill BEFORE readiness. Detects whether the caller template extends the shared C360 Semantic Model base model (sfdc_internal__C360UnifiedSemanticModel / C360SemanticModel_c360) and enforces a mandatory 3-step check — SDM presence in Data Cloud, installed C360 app in SuccessStatus, and installed-vs-current templateVersion parity — resolving the HOME/COMPANION multi-org role and auto-remediating (HOME) or refusing a shared-HOME mutation (COMPANION). Returns PROCEED or REFUSE/STOP. Not user-invocable on its own; it is a building block for any Tableau Next / App Framework install that has a C360 base-model dependency."
metadata:
  version: "1.0"
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

# tableau-next-c360-basemodel-gate

## What this does

This is a **generic prerequisite gate** extracted verbatim from the `tableau-next-app-install` skill (its Step 2b) so it can be reused by any app install that depends on the shared C360 Semantic Model. The primary skill **invokes this gate in the same shell session, before its readiness (Step 3) and create (Step 4) steps.**

**Contract**
- **Inputs (already set by the caller in this shell):** `$ORG_ALIAS` (the org the user named), `$TEMPLATE_NAME_OR_ID` (the caller template), and `$API_BASE` / `$API_VERSION` (resolved by the primary's "Discover API version" step). The C360 template apiName is `sfdc_internal__C360UnifiedSemanticModel`.
- **Behavior:** resolve HOME/COMPANION role → detect the C360 base-model dependency in the caller template's `/assets` → run the 3-step verification (SDM presence → installed C360 app `SuccessStatus` / `SuccessWithWarningsStatus` → templateVersion parity). HOME auto-remediates a missing/stale C360 inline; COMPANION refuses a shared-HOME mutation unless explicitly opted in (`TABNEXT_ALLOW_SHARED_HOME_C360_UPDATE=1` or a TTY `y`).
- **Outputs left in the shell for the caller** (the primary's Step-4 target-org guard and Step-6b update path read these): `$ORG_ROLE` (HOME / COMPANION / UNKNOWN), `$RESOLVED_ORG_FOR_C360` (= `$ORG_ALIAS` on HOME, = `$HOME_ORG_ALIAS` on COMPANION), and `$HOME_ORG_ALIAS`.
- **Verdict:** **PROCEED** (all clear — the caller continues to readiness) or **REFUSE / STOP** (the caller must halt and surface the message verbatim).

This gate is **self-contained**: it carries its own copies of the `update_app` and `poll_update_to_terminal` helpers (used by the 2b.5 templateVersion auto-remediation path). They are byte-identical to the same-named helpers in the primary skill's Step 6b, duplicated here so this gate runs standalone without sourcing the primary's later steps. **Define them first — run the `bash` block immediately below — then run the gate logic that follows.**

## Helper functions (define these BEFORE running the gate — used by 2b.5 auto-remediation)

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

### 2b. Detect C360 Semantic Model base-model dependency (REQUIRED — do NOT skip)

Some allowlisted templates ship SDMs that **extend** the shared `C360SemanticModel_c360` semantic model (a.k.a. `sfdc_internal__C360UnifiedSemanticModel`). If the C360 app isn't already installed on the org — OR is installed at a stale `templateVersion` — the extending SDMs cannot resolve their base model and the install will fail late, after `POST /apps` has already spent minutes provisioning downstream assets. Detect this dependency BEFORE readiness and refuse cleanly.

**How the dependency shows up on the wire:**
- `GET /app-framework/templates/{id}/assets` returns the template's declared assets. Each entry has an `assetType`.
- **The response wrapper key has drifted three ways across releases**: `.assets`, `.templateAssets`, and (v68.0+, wire-verified 2026-08-26) `.templatedAssets`. Coalesce ALL three when reading the list — filtering on the first two alone silently falls through to `[]` on v68 and every downstream SemanticModel scan produces zero hits.
- **Each entry's SDM content is NOT at the top of the entry — it's a stringified JSON blob under `.body`**, with quotes HTML-entity-encoded as `&quot;` (wire-verified 2026-08-26 on `sfdc_internal__SalesInsightsTN`). You MUST html-decode then JSON-parse `.body` before `baseModels` is reachable. Reading `.baseModels` on the top-level asset entry returns null on v68.0+.
- **`baseModels` is an ARRAY OF OBJECTS on v68.0+, not an array of strings.** Wire-verified 2026-08-26 shape: `"baseModels": [{"apiName": "C360SemanticModel_c360", "label": "C360 Semantic Model"}]`. Older releases emit the string form (`"baseModels": ["C360SemanticModel_c360"]`) or a bare `"baseModel": "C360SemanticModel_c360"`. Handle both — a `type == "string"` filter silently drops every object entry on v68 and produces a false-negative C360 detection.
- The base-model apiName the platform uses is `C360SemanticModel_c360` (the SDM name inside the C360 app), NOT the template apiName `sfdc_internal__C360UnifiedSemanticModel`. Match on both — the field name and casing have varied across releases.

> **Anti-pattern (wire-verified 2026-08-25):** the `/app-framework/apps` list endpoint honors ONLY `templateSourceId` as a server-side filter. `applicationStatus` is silently IGNORED as a query param — the server returns the unfiltered set. **Do NOT** put `applicationStatus` in the URL. Always filter client-side with `jq`.

**Gate logic — 3-step verification: SDM presence → installed app SuccessStatus → templateVersion match (MANDATORY):**

The 3-step gate is non-bypassable when the caller template declares a C360 base-model dependency (2b.2). In particular, 2b.5's templateVersion parity compare is a **HARD gate** — an unreadable installed version, or an unreadable current template version, refuses the install with actionable remediation. Do NOT silently proceed when either operand is missing: `SuccessStatus` on the downstream install is not proof that parity was actually observed, and templates can pin their C360 dependency by apiName only, so a stale-C360 install may fail late during base-model resolution without a clean upstream signal.

The parity compare is scoped to (a) the *installed C360 app's* `templateVersion` on `$RESOLVED_ORG_FOR_C360` — read from `GET /app-framework/apps?templateSourceId=sfdc_internal__C360UnifiedSemanticModel` under `.templateVersion` (with `.templateInfo.templateVersion` / `.installedTemplate.templateVersion` as release-drift fallbacks) — and (b) the *C360 template's* current `templateVersion` — read from `GET /app-framework/templates/sfdc_internal__C360UnifiedSemanticModel` under `.releaseInfo.templateVersion` (with `.templateVersion` / `.release.templateVersion` as older aliases). The **CALLER template's own version** (e.g. `sfdc_internal__ServiceInsights` v4.4) is intentionally NOT part of this compare — the C360 base-model is a shared cross-template dependency, so only its own installed-vs-current matters.


```bash
# Skip this step entirely when the user is installing C360 itself — a template
# doesn't depend on itself.
if [ "$TEMPLATE_NAME_OR_ID" != "sfdc_internal__C360UnifiedSemanticModel" ]; then

  # =========================================================================
  # 2b HELPERS - HOME/COMPANION role resolution + inline C360 install on Home
  # =========================================================================
  # Wire signals (verified 2026-08-27 on v68.0 pc-rnd):
  #   ROLE = SOQL against DataMultiOrgConnection
  #     0 rows                  -> HOME (standalone or Home side of no pairing)
  #     >=1 row OrgType='HOME'  -> COMPANION; the row describes the FAR END of
  #                                the connection, so OrgType=HOME means "the
  #                                other side is a Home" -> this org is the LOB.
  #                                Home id in ConnectedOrg (fallback
  #                                ConnectedParentOrg).
  #     >=1 row OrgType='LOB'   -> HOME (paired publisher); each LOB row
  #                                describes a companion consuming from this
  #                                org. This org IS the Home.
  #   /ssot/tenant-info, /connect/tenants, PlatformTenant, DataCloudTenant, and
  #   TnCompanionOrgAssignment are all NOT_FOUND on v68.0. Do NOT gate on them.
  #
  # INSUFFICIENT_ACCESS on DataMultiOrgConnection is a HARD REFUSE, not a
  # fall-back to HOME. A false-HOME classification would skip the companion
  # auto-install branch and mislead the operator.

  c360_log() {
    # $1 = state name, $2 = org alias in scope
    echo "[2b state=$1 org=${2:-<none>}]" >&2
  }

  # ---- resolve_c360_gate_orgs ---------------------------------------------
  # Sets ORG_ROLE in {HOME, COMPANION, UNKNOWN}, HOME_ORG_ID_15, HOME_ORG_ALIAS,
  # RESOLVED_ORG_FOR_C360 (= $ORG_ALIAS on HOME, = $HOME_ORG_ALIAS on COMPANION).
  # Returns 0 on success, 1 on unrecoverable classification failure.
  resolve_c360_gate_orgs() {
    ORG_ROLE=""
    HOME_ORG_ID_15=""
    HOME_ORG_ALIAS=""
    RESOLVED_ORG_FOR_C360="$ORG_ALIAS"

    local q_json err_name total lob_row home_row home_id_raw
    q_json=$(sf data query --target-org "$ORG_ALIAS" --json \
      --query "SELECT Id, OrgType, ConnectionStatus, ConnectedOrg, ConnectedParentOrg, TenantKey FROM DataMultiOrgConnection" \
      2>&1 || true)

    err_name=$(echo "$q_json" | jq -r '.name // .result[0].errorCode // empty' 2>/dev/null)
    case "$err_name" in
      INSUFFICIENT_ACCESS_OR_READONLY|INSUFFICIENT_ACCESS|ACCESS_DENIED)
        ORG_ROLE="UNKNOWN"
        cat >&2 <<MSG

REFUSING: cannot determine HOME/COMPANION role for $ORG_ALIAS - the running
user lacks read access to DataMultiOrgConnection ($err_name).

Action required - one of:
  1. Grant read on DataMultiOrgConnection to the running user in $ORG_ALIAS.
  2. Re-invoke with --home-org-alias <alias> to pin the COMPANION path.

MSG
        return 1
        ;;
      INVALID_TYPE|sf:INVALID_TYPE|SOBJECT_NOT_FOUND|NoSuchEntity*)
        echo "NOTE: DataMultiOrgConnection not queryable on $ORG_ALIAS ($err_name) - treating as HOME (standalone)." >&2
        ORG_ROLE="HOME"
        ;;
      INVALID_SESSION_ID|INVALID_AUTH_HEADER|INVALID_JWT_FORMAT)
        ORG_ROLE="UNKNOWN"
        echo "REFUSING: auth session stale while probing role on $ORG_ALIAS ($err_name). Refresh with 'sf org login web --alias $ORG_ALIAS' and retry." >&2
        return 1
        ;;
      "")
        total=$(echo "$q_json" | jq -r '.result.totalSize // ((.result.records // []) | length) // 0' 2>/dev/null)
        total=${total:-0}
        if [ "$total" = "0" ]; then
          ORG_ROLE="HOME"
        else
          # DataMultiOrgConnection.OrgType describes the FAR END of each
          # connection, not the local org:
          #   OrgType='HOME' -> paired to a HOME -> local org is COMPANION
          #   OrgType='LOB'  -> paired to a LOB  -> local org is HOME
          # On the COMPANION branch, the HOME's id is in ConnectedOrg
          # (fallback ConnectedParentOrg on releases that use the parent field).
          home_row=$(echo "$q_json" | jq -c '.result.records[]? | select(.OrgType == "HOME")' 2>/dev/null | head -n1)
          lob_row=$(echo "$q_json" | jq -c '.result.records[]? | select(.OrgType == "LOB")' 2>/dev/null | head -n1)
          if [ -n "$home_row" ]; then
            ORG_ROLE="COMPANION"
            home_id_raw=$(echo "$home_row" | jq -r '.ConnectedOrg // .ConnectedParentOrg // empty' 2>/dev/null)
          elif [ -n "$lob_row" ]; then
            ORG_ROLE="HOME"
          else
            echo "NOTE: DataMultiOrgConnection returned $total row(s) but no HOME/LOB OrgType - role indeterminate." >&2
            ORG_ROLE="UNKNOWN"
          fi
        fi
        ;;
      *)
        echo "REFUSING: DataMultiOrgConnection probe on $ORG_ALIAS returned $err_name - role indeterminate." >&2
        ORG_ROLE="UNKNOWN"
        return 1
        ;;
    esac

    if [ "$ORG_ROLE" = "HOME" ]; then
      RESOLVED_ORG_FOR_C360="$ORG_ALIAS"
      c360_log "PROBE_ROLE=HOME" "$ORG_ALIAS"
      return 0
    fi

    if [ "$ORG_ROLE" = "UNKNOWN" ]; then
      return 1
    fi

    if [ -z "$home_id_raw" ]; then
      cat >&2 <<MSG

REFUSING: $ORG_ALIAS is classified as a COMPANION (a DataMultiOrgConnection
row reports OrgType='HOME', i.e. the paired org is a HOME) but neither
ConnectedOrg nor ConnectedParentOrg was populated.
Re-invoke with --home-org-alias <alias>.

MSG
      return 1
    fi

    HOME_ORG_ID_15="${home_id_raw:0:15}"

    local orgs home_alias
    orgs=$(sf org list --json 2>/dev/null || true)
    if [ -z "$orgs" ]; then
      echo "REFUSING: 'sf org list --json' returned empty body - cannot resolve HOME_ORG_ALIAS for $HOME_ORG_ID_15." >&2
      return 1
    fi

    home_alias=$(echo "$orgs" | jq -r --arg id15 "$HOME_ORG_ID_15" '
      [ (.result.nonScratchOrgs // []),
        (.result.scratchOrgs    // []),
        (.result.devHubs        // []),
        (.result.sandboxes      // []),
        (.result.other          // []) ]
      | add // []
      | map(select(((.orgId // "") | tostring | .[0:15]) == $id15))
      | .[0]
      | (.aliases // [])[0] // .alias // .username // empty
    ' 2>/dev/null)

    if [ -z "$home_alias" ] || [ "$home_alias" = "null" ]; then
      cat >&2 <<MSG

STOPPING install of $TEMPLATE_NAME_OR_ID on companion $ORG_ALIAS:
no local sf CLI auth found for the HOME org paired with this companion.

WHY THIS IS BLOCKING
--------------------
$ORG_ALIAS is a COMPANION (LOB) org. Its C360 Semantic Model dependency
lives on the paired HOME org, not here. Steps 2b.3, 2b.4 and 2b.5 must
run App-Framework REST calls against the HOME:
    GET /app-framework/templates/sfdc_internal__C360UnifiedSemanticModel
    GET /app-framework/apps?templateSourceId=sfdc_internal__C360UnifiedSemanticModel
The companion's session token cannot be reused against the HOME - Salesforce
sessions are scoped to the org that issued them. Without a HOME-scoped
sf CLI alias on this machine, the 2b gate cannot verify the SDM presence
or run the templateVersion parity check, and this skill will not proceed
blind.

HOME ORG IDENTIFIERS (from DataMultiOrgConnection on $ORG_ALIAS)
----------------------------------------------------------------
  HOME org id (18-char)        : ${home_id_raw:-<unresolved>}
  HOME org id (15-char)        : $HOME_ORG_ID_15
  Companion (this org, caller) : $ORG_ALIAS
  Pairing status               : as reported by DataMultiOrgConnection

REQUIRED - GET THE FOLLOWING FROM THE HOME ORG ADMIN
----------------------------------------------------
Ask the admin of HOME org $HOME_ORG_ID_15 for these THREE things. The
admin never has to share a password, security token, or 2FA code - the
web login flow keeps their credentials on their side of the screen:

  (1) HOME org's my-domain login URL
      Exact form:  https://<subdomain>.my.<pod>.salesforce.com
      Example:     https://acme-home.my.pc-rnd.salesforce.com
      The org id alone is NOT enough - Salesforce has no public
      org-id -> my-domain reverse lookup, so the admin must supply this.

  (2) A permitted login user on the HOME
      Confirm the user the admin will log in as carries:
        - AppFrameworkManageTemplate  (Manage App Templates perm)
        - Tableau Next enabled on the HOME
        - Data Cloud provisioned on the HOME
      Read-only 2b.5 (templates + apps GETs) works with just
      "View Setup and Configuration" + Tableau-Next perms, but pin
      AppFrameworkManageTemplate anyway in case a downstream step
      needs to trigger a Reconfigure.

  (3) The admin's ~60 seconds at this terminal
      They come to this laptop, run ONE command (below), complete the
      browser login on their side, and walk away. No secret leaves
      their control; the sf CLI stores a HOME-scoped refresh token
      keyed to the alias.

ONCE (1)-(3) ARE READY - RUN THIS COMMAND (Option A)
----------------------------------------------------
  sf org login web \\
    --instance-url https://<HOME-my-domain>.my.<pod>.salesforce.com \\
    --alias <home-alias>

Suggested alias naming (kept stable across future skill invocations):
    home_${HOME_ORG_ID_15}
  e.g.
    sf org login web \\
      --instance-url https://acme-home.my.pc-rnd.salesforce.com \\
      --alias home_$HOME_ORG_ID_15

The browser opens, the admin logs in on the HOME, and the CLI stores a
HOME-scoped refresh token under that alias. The alias is then usable by
every subsequent sf api request rest --target-org <home-alias> call in
this skill - no further admin involvement per run.

VERIFY THE ALIAS BEFORE RE-INVOKING
-----------------------------------
  sf org list --json | jq -r --arg id15 "$HOME_ORG_ID_15" '
    [ (.result.nonScratchOrgs // []),
      (.result.scratchOrgs    // []),
      (.result.devHubs        // []),
      (.result.sandboxes      // []),
      (.result.other          // []) ]
    | add
    | map(select(((.orgId // "") | tostring | .[0:15]) == \$id15))
    | .[0]
    | {alias: ((.aliases // [])[0] // .alias // .username), orgId, instanceUrl}'
The row should show alias + orgId starting with $HOME_ORG_ID_15 + the
HOME instance URL you supplied.

WHY OPTION A AND NOT A RAW BEARER TOKEN
---------------------------------------
Option B (admin pastes a HOME sf org display access token) works for a
one-shot check but the token expires (~2 hours on pc-rnd) and cannot be
refreshed by this skill without prompting the admin again. Option C
(client_credentials via a Connected App on the HOME) is only worth the
setup if this workflow becomes unattended / repeating. Option A - the
web login - is the right default for interactive skill runs: no shared
secret in shell history, refresh token stays on this laptop, and every
future run just names the alias.

This skill will now WAIT (up to 15 min, re-checking every 30 s) for the
HOME alias to appear in \`sf org list --json\`. Run the login command in
another terminal on this same machine; the skill picks up the alias the
moment it lands and continues automatically with 2b.3 / 2b.4 / 2b.5
against the HOME - no re-invoke required.

If the wait times out, the skill will REFUSE and exit; re-run once the
alias exists (Step 2b.0 will re-probe DataMultiOrgConnection and continue).

Ctrl-C to abort and re-run later.

MSG
      # Bounded auto-resume: re-check the sf CLI alias table every 30 s for
      # up to 15 min. If the HOME alias appears mid-wait, continue in this
      # same run (no re-invoke required). If it doesn't, refuse and exit
      # so a subsequent invocation picks up where this one left off.
      # Rationale: the STOPPING message asks the admin to run a single
      # 'sf org login web' in another terminal on this laptop. Round-trip
      # is typically 30-90 s (browser popup + click-through), so a 15-min
      # cap is generous but bounded - a stuck run is preferable to an
      # unbounded background wait.
      local resume_deadline resume_iter=0 resume_orgs
      resume_deadline=$(( $(date +%s) + 900 ))
      while [ "$(date +%s)" -lt "$resume_deadline" ]; do
        resume_iter=$(( resume_iter + 1 ))
        sleep 30
        resume_orgs=$(sf org list --json 2>/dev/null || true)
        if [ -z "$resume_orgs" ]; then
          echo "[resolve_c360_gate_orgs auto-resume iter=$resume_iter] 'sf org list --json' returned empty body - retrying." >&2
          continue
        fi
        home_alias=$(echo "$resume_orgs" | jq -r --arg id15 "$HOME_ORG_ID_15" '
          [ (.result.nonScratchOrgs // []),
            (.result.scratchOrgs    // []),
            (.result.devHubs        // []),
            (.result.sandboxes      // []),
            (.result.other          // []) ]
          | add // []
          | map(select(((.orgId // "") | tostring | .[0:15]) == $id15))
          | .[0]
          | (.aliases // [])[0] // .alias // .username // empty
        ' 2>/dev/null)
        if [ -n "$home_alias" ] && [ "$home_alias" != "null" ]; then
          echo "[resolve_c360_gate_orgs auto-resume iter=$resume_iter] HOME alias '$home_alias' registered for $HOME_ORG_ID_15 - continuing in this run." >&2
          break
        fi
        echo "[resolve_c360_gate_orgs auto-resume iter=$resume_iter] HOME alias for $HOME_ORG_ID_15 not yet present - waiting." >&2
      done

      if [ -z "$home_alias" ] || [ "$home_alias" = "null" ]; then
        cat >&2 <<MSG

REFUSING: HOME alias for $HOME_ORG_ID_15 did not appear within 15 min
on $ORG_ALIAS. Complete the 'sf org login web ... --alias ...' command
from the STOPPING message above, then re-invoke this skill on $ORG_ALIAS.
Step 2b.0 will re-probe DataMultiOrgConnection, find the newly-registered
HOME alias, and continue with 2b.3 / 2b.4 / 2b.5 against the HOME.

MSG
        return 1
      fi
    fi

    HOME_ORG_ALIAS="$home_alias"
    RESOLVED_ORG_FOR_C360="$HOME_ORG_ALIAS"
    c360_log "PROBE_ROLE=COMPANION home=$HOME_ORG_ALIAS(id $HOME_ORG_ID_15)" "$ORG_ALIAS"
    return 0
  }

  # ---- wait_for_c360_sdm_visible ------------------------------------------
  # Poll a target org's /ssot/semantic/models/C360SemanticModel_c360 endpoint
  # (with fall-through to the older /ssot/semantic-models/ path per the same
  # discipline as 2b.3's SDM presence probe) until the C360 SDM resolves. The
  # /apps install reaching SuccessStatus/SuccessWithWarningsStatus is NOT
  # sufficient to conclude the SDM is available:
  #   HOME (self-install / standalone): SDM materialization on the publisher
  #     is typically fast (seconds) once the install lands, but backing
  #     Data Cloud metadata rolls out asynchronously. Callers of this skill
  #     (2b.4/2b.5, readiness) depend on the SDM being resolvable, so we
  #     block on visibility here rather than let a downstream step false-fail.
  #   COMPANION (cross-org publish): the SDM must PROPAGATE from HOME to the
  #     companion's Data Cloud via multi-org sync; observed window varies from
  #     minutes to hours depending on pairing state and platform backlog.
  # POLLING DISCIPLINE — pass cap_secs=0 (or omit) for UNBOUNDED polling: the
  # loop runs until the SDM appears, an auth error surfaces, or the caller
  # kills the run. Both current callers (HOME self-install, COMPANION
  # propagation) pass 0 per user instruction "keep polling till the SDM is
  # available." A positive cap_secs is honored as a bounded probe (kept for
  # future callers that need one — e.g. a health check). Auth errors mid-poll
  # (INVALID_SESSION_ID / INVALID_AUTH_HEADER / INVALID_JWT_FORMAT) always
  # surface immediately with a refresh-auth refusal - a stale token would
  # otherwise poll forever against a broken session.
  # Args:
  #   $1 = target sf org alias to probe
  #   $2 = cap seconds (0 = unbounded; positive = bounded probe)
  #   $3 = short role tag for log lines ("HOME self-install" / "COMPANION propagation")
  #   $4 = publisher org (for the failure-mode message; equals $1 on HOME path,
  #        equals $HOME_ORG_ALIAS on COMPANION path)
  wait_for_c360_sdm_visible() {
    local target="$1" cap_secs="$2" role_tag="$3" publisher="$4"
    local sdm_url_primary="/services/data/$API_VERSION/ssot/semantic/models/C360SemanticModel_c360"
    local sdm_url_alt="/services/data/$API_VERSION/ssot/semantic-models/C360SemanticModel_c360"
    local sdm_resp sdm_err sdm_name
    local unbounded=1 deadline=0
    if [ -n "$cap_secs" ] && [ "$cap_secs" -gt 0 ] 2>/dev/null; then
      unbounded=0
      deadline=$(( $(date +%s) + cap_secs ))
    fi
    if [ "$unbounded" -eq 1 ]; then
      echo "[2b state=WAIT_FOR_SDM $role_tag target=$target] polling C360 SDM visibility (unbounded - polling until SDM appears; auth expiry or Ctrl-C exits)." >&2
    else
      echo "[2b state=WAIT_FOR_SDM $role_tag target=$target] polling C360 SDM visibility (cap $((cap_secs/60))m)." >&2
    fi
    while :; do
      if [ "$unbounded" -eq 0 ] && [ "$(date +%s)" -ge "$deadline" ]; then
        break
      fi
      sdm_resp=$(sf api request rest "$sdm_url_primary" \
        --target-org "$target" --method GET 2>/dev/null || true)
      sdm_err=$(echo "$sdm_resp" | jq -r '.[0]?.errorCode // .errorCode // empty' 2>/dev/null)
      if [ -z "$sdm_resp" ] || echo "$sdm_err" | grep -qE '^(URL_NOT_FOUND|NOT_FOUND|UNSUPPORTED_API_VERSION)$'; then
        sdm_resp=$(sf api request rest "$sdm_url_alt" \
          --target-org "$target" --method GET 2>/dev/null || true)
        sdm_err=$(echo "$sdm_resp" | jq -r '.[0]?.errorCode // .errorCode // empty' 2>/dev/null)
      fi
      case "$sdm_err" in
        INVALID_SESSION_ID|INVALID_AUTH_HEADER|INVALID_JWT_FORMAT)
          cat >&2 <<MSG

REFUSING: auth session expired mid-poll on $target while waiting for
C360 SDM visibility ($role_tag: $sdm_err). Refresh the org auth
('sf org login web --alias $target') and re-invoke this skill.

MSG
          return 1
          ;;
      esac
      sdm_name=$(echo "$sdm_resp" | jq -r '.name // .apiName // .semanticModel.name // .semanticModel.apiName // empty' 2>/dev/null)
      if [ -n "$sdm_name" ]; then
        c360_log "WAIT_FOR_SDM visible ($role_tag)" "$target"
        return 0
      fi
      sleep 30
    done
    # Cap elapsed (bounded probe only — unbounded path never reaches here).
    # Emit a role-appropriate refusal — HOME self-install "did not
    # materialize" vs COMPANION "did not propagate from HOME" carry different
    # remediations, so the caller passes the right role_tag.
    if [ "$target" = "$publisher" ]; then
      cat >&2 <<MSG

REFUSING: C360 was installed on $target (SuccessStatus) but the C360 SDM
did NOT materialize in $target's Data Cloud within $((cap_secs/60)) minutes.
Verify Data Cloud is fully provisioned on $target (Setup -> Data Cloud
Setup), then re-invoke this skill on $target.

MSG
    else
      cat >&2 <<MSG

REFUSING: C360 was installed on HOME $publisher (SuccessStatus) but the
C360 SDM did NOT propagate to companion $target within $((cap_secs/60))
minutes. Check DataMultiOrgConnection.ConnectionStatus on both $publisher
and $target, verify tenants share the same TenantKey, then re-invoke.

MSG
    fi
    return 1
  }

  # ---- install_c360_on_home_and_wait_for_sync -----------------------------
  # Role-parametric C360 install:
  #   ORG_ROLE=COMPANION -> install on $HOME_ORG_ALIAS, then UNBOUNDED-poll
  #                         $ORG_ALIAS for SDM propagation via
  #                         wait_for_c360_sdm_visible (30 min /apps install
  #                         cap + unbounded SDM-visibility wait).
  #   ORG_ROLE=HOME      -> install on $ORG_ALIAS itself, then UNBOUNDED-poll
  #                         $ORG_ALIAS for local SDM materialization via
  #                         wait_for_c360_sdm_visible (30 min /apps install
  #                         cap + unbounded SDM-visibility wait). SuccessStatus
  #                         on /apps is NECESSARY but not SUFFICIENT — the SDM
  #                         must be resolvable in Data Cloud before 2b.4/2b.5
  #                         continue.
  # NEVER shells out to a nested skill invocation. Idempotent w.r.t. an existing
  # install: DUPLICATE_VALUE / ITEM_ALREADY_EXISTS / APP_ALREADY_INSTALLED on
  # the POST short-circuits to the SDM-visibility wait step (both roles).
  # Caps: 30 min on /apps poll; UNBOUNDED on the SDM-visibility wait (both
  # roles). The user's instruction is "keep polling till the SDM is available"
  # — the wait terminates only on SDM visibility, auth expiry, or Ctrl-C.
  install_c360_on_home_and_wait_for_sync() {
    # Publisher (where the C360 app is created) is the resolved C360 org:
    #   RESOLVED_ORG_FOR_C360 = $ORG_ALIAS  (HOME role)   -> self-install
    #   RESOLVED_ORG_FOR_C360 = $HOME_ORG_ALIAS (COMPANION) -> home-install
    local home="${RESOLVED_ORG_FOR_C360:-$HOME_ORG_ALIAS}"
    local caller="$ORG_ALIAS"
    local c360="sfdc_internal__C360UnifiedSemanticModel"
    local body_file create_file create_resp new_app_id post_err status app_resp
    local install_deadline=$(( $(date +%s) + 1800 ))
    local sync_deadline

    c360_log "INSTALL_C360_HOME start" "$home"

    body_file=$(mktemp /tmp/c360_home_body.XXXXXX)
    cat > "$body_file" <<'JSON'
{"templateValues": {}}
JSON

    sf api request rest "$API_BASE/templates/$c360/readiness" \
      --target-org "$home" --method POST --body "@$body_file" \
      >/dev/null 2>&1 || true

    create_file=$(mktemp /tmp/c360_home_create.XXXXXX)
    cat > "$create_file" <<JSON
{
  "template": {"name": "$c360"},
  "appLabel": "C360 Semantic Model",
  "templateValues": {}
}
JSON

    create_resp=$(sf api request rest "$API_BASE/apps" \
      --target-org "$home" --method POST --body "@$create_file" 2>/dev/null || true)
    rm -f "$body_file" "$create_file"

    post_err=$(echo "$create_resp" | jq -r '.[0]?.errorCode // .errorCode // empty' 2>/dev/null)
    new_app_id=$(echo "$create_resp" | jq -r '.id // .appId // .applicationId // empty' 2>/dev/null)

    if [ -n "$post_err" ]; then
      case "$post_err" in
        DUPLICATE_VALUE|ITEM_ALREADY_EXISTS|APP_ALREADY_INSTALLED)
          # An existing Home C360 app is present, but it may be InProgressStatus
          # (still installing) or FailedStatus (prior attempt broke). Blindly
          # entering the SDM-visibility wait in either state would time out
          # and refuse with a misleading "SDM did NOT materialize/propagate"
          # message. Look up the existing app, decide based on its
          # applicationStatus:
          #   SuccessStatus / SuccessWithWarningsStatus -> SDM-visibility wait
          #   InProgressStatus                          -> enter the 30-min poll
          #   FailedStatus                              -> refuse immediately
          echo "NOTE: C360 already installed on HOME $home ($post_err) - inspecting existing app state before SDM-visibility wait." >&2
          local existing_resp existing_status existing_id
          existing_resp=$(sf api request rest \
            "$API_BASE/apps?templateSourceId=$c360" \
            --target-org "$home" --method GET 2>/dev/null || true)
          existing_id=$(echo "$existing_resp" | jq -r '
            (.apps // .items // .records // [])
            | map(select(
                (.templateSourceId == "sfdc_internal__C360UnifiedSemanticModel") or
                (.templateApiName  == "sfdc_internal__C360UnifiedSemanticModel")
              ))
            | .[0].id // .[0].appId // .[0].applicationId // empty
          ' 2>/dev/null)
          existing_status=$(echo "$existing_resp" | jq -r '
            (.apps // .items // .records // [])
            | map(select(
                (.templateSourceId == "sfdc_internal__C360UnifiedSemanticModel") or
                (.templateApiName  == "sfdc_internal__C360UnifiedSemanticModel")
              ))
            | .[0].applicationStatus // .[0].status // empty
          ' 2>/dev/null)
          case "$existing_status" in
            SuccessStatus|SuccessWithWarningsStatus)
              echo "NOTE: existing HOME C360 app on $home is $existing_status - proceeding to SDM-visibility wait." >&2
              new_app_id=""
              ;;
            InProgressStatus)
              if [ -n "$existing_id" ]; then
                echo "NOTE: existing HOME C360 app on $home ($existing_id) is InProgressStatus - joining the 30-min poll." >&2
                new_app_id="$existing_id"
              else
                echo "REFUSING: HOME C360 app on $home is InProgressStatus but its id could not be resolved from /apps. Wait for it to reach SuccessStatus and re-invoke on $caller." >&2
                return 1
              fi
              ;;
            FailedStatus)
              echo "REFUSING: existing HOME C360 app on $home (id: ${existing_id:-<unknown>}) is at FailedStatus. Delete or reconfigure it in Setup -> Installed Apps on $home, then re-invoke this skill on $caller." >&2
              return 1
              ;;
            "")
              echo "NOTE: POST /apps reported $post_err but no C360 app was resolvable on HOME $home. Proceeding to SDM-visibility wait - readiness on $caller will surface any real failure." >&2
              new_app_id=""
              ;;
            *)
              echo "NOTE: existing HOME C360 app on $home reports applicationStatus=$existing_status - treating as non-terminal, proceeding to SDM-visibility wait." >&2
              new_app_id=""
              ;;
          esac
          ;;
        *)
          cat >&2 <<MSG

REFUSING: POST /apps for C360 on HOME $home failed with $post_err.
Install C360 manually on Home (Setup -> App Manager -> New App ->
"C360 Semantic Model") then re-invoke this skill on $caller.

MSG
          return 1
          ;;
      esac
    elif [ -z "$new_app_id" ]; then
      echo "REFUSING: POST /apps for C360 on HOME $home returned no id. Raw response:" >&2
      echo "$create_resp" | jq . >&2 2>/dev/null || echo "$create_resp" >&2
      return 1
    fi

    if [ -n "$new_app_id" ]; then
      echo "[2b state=INSTALL_C360_HOME org=$home] C360 app id=$new_app_id - polling (cap 30m)." >&2
      local poll_err
      while [ "$(date +%s)" -lt "$install_deadline" ]; do
        app_resp=$(sf api request rest "$API_BASE/apps/$new_app_id" \
          --target-org "$home" --method GET 2>/dev/null || true)
        # Auth session may have gone stale mid-poll (JWT expiry, token revoked).
        # Surface it immediately instead of grinding through the full 30-min
        # deadline with an empty .applicationStatus and refusing with a
        # misleading "did not reach SuccessStatus" message.
        poll_err=$(echo "$app_resp" | jq -r '.[0]?.errorCode // .errorCode // empty' 2>/dev/null)
        case "$poll_err" in
          INVALID_SESSION_ID|INVALID_AUTH_HEADER|INVALID_JWT_FORMAT)
            cat >&2 <<MSG

REFUSING: auth session expired mid-poll on HOME $home while waiting for the
C360 install (app $new_app_id) to reach SuccessStatus ($poll_err).
Refresh the org auth ('sf org login web --alias $home') and re-invoke this
skill on $caller.

MSG
            return 1
            ;;
        esac
        # Wire rule D: applicationStatus is canonical; .status is legacy.
        status=$(echo "$app_resp" | jq -r '.applicationStatus // .status // empty' 2>/dev/null)
        case "$status" in
          SuccessStatus|SuccessWithWarningsStatus)
            c360_log "INSTALL_C360_HOME reached=$status" "$home"
            break
            ;;
          FailedStatus)
            echo "REFUSING: HOME C360 install reached FailedStatus (app $new_app_id on $home). Inspect /apps/$new_app_id and remediate before retry." >&2
            return 1
            ;;
        esac
        sleep 30
      done
      case "$status" in
        SuccessStatus|SuccessWithWarningsStatus) : ;;
        *)
          echo "REFUSING: HOME C360 install on $home did not reach SuccessStatus within 30 min (last: ${status:-<empty>}, app $new_app_id)." >&2
          return 1
          ;;
      esac
    fi

    # SDM visibility wait — role-parametric.
    # On HOME/standalone the caller IS the publisher, so the SDM must
    # materialize locally in Data Cloud after the install lands. SuccessStatus
    # on /apps is necessary but NOT sufficient: downstream 2b.4/2b.5 and
    # readiness look up the SDM directly via /ssot, so we must confirm the
    # SDM is resolvable there before returning. Materialization is typically
    # seconds after Success but Data Cloud metadata rollout is asynchronous;
    # per user instruction the wait is UNBOUNDED (cap_secs=0) — it polls
    # every 30s until the SDM appears, or until an auth error / Ctrl-C exits.
    #
    # On COMPANION the SDM must propagate cross-org from HOME to CALLER via
    # multi-org sync. Publish latency depends on pairing state and platform
    # backlog and is not reliably bounded, so per user instruction the wait
    # is UNBOUNDED here too (cap_secs=0). Same helper, same discipline, target
    # is the caller org (not the publisher).
    if [ "$home" = "$caller" ]; then
      if wait_for_c360_sdm_visible "$caller" 0 "HOME self-install" "$home"; then
        c360_log "SELF_INSTALL_C360 done - SDM visible on $caller" "$caller"
        return 0
      fi
      return 1
    fi

    if wait_for_c360_sdm_visible "$caller" 0 "COMPANION propagation" "$home"; then
      return 0
    fi
    return 1
  }

  # ---- 2b.1: fetch the template's declared assets --------------------------
  # Response shape follows AppFrameworkTemplateAssetCollectionRepresentation:
  # entries under `.assets[]` (older), `.templateAssets[]` (older still), or
  # `.templatedAssets[]` (v68.0+, wire-verified 2026-08-26). Each entry carries
  # `assetType` and (for SemanticModel entries) a stringified `body` containing
  # the SDM definition. `baseModels` lives INSIDE that body — not on the entry.
  ASSETS_JSON=$(sf api request rest \
    "$API_BASE/templates/$TEMPLATE_NAME_OR_ID/assets" \
    --target-org "$ORG_ALIAS" --method GET 2>/dev/null)

  # Empty stdout on /assets is NOT "endpoint returned nothing" — it typically
  # means the sf CLI hit an auth failure and wrote the error to stderr (which
  # is suppressed here). Refuse loudly so we do not silently bypass 2b.3-2b.5.
  if [ -z "$ASSETS_JSON" ]; then
    cat >&2 <<MSG

REFUSING: /app-framework/templates/$TEMPLATE_NAME_OR_ID/assets returned an
empty body on $ORG_ALIAS while probing C360 dependency. This almost always
means the sf CLI session is stale or the org is unreachable.

Refresh the org auth ("sf org login web --alias $ORG_ALIAS") and re-invoke
this skill. Do NOT retry blindly — silently proceeding here would bypass the
entire C360 dependency gate and let a doomed install kick off.

MSG
    return 1 2>/dev/null || exit 1
  fi

  # jq-shape-tolerant errorCode probe: some releases return the error as an
  # ARRAY `[{errorCode:...}]`, others as an OBJECT `{errorCode:...}`. Plain
  # `.[0].errorCode` raises "Cannot index object with number" on the object
  # form, which the `//` operator does NOT catch — use the `?` operator so
  # the failed index yields null and the second alternative fires.
  ASSETS_HAS_ERROR=$(echo "$ASSETS_JSON" | jq -r '.[0]?.errorCode // .errorCode // empty' 2>/dev/null)

  # Auth errors on /assets MUST refuse (same as 2b.3/2b.4). Do not let a stale
  # token on the very first probe silently disable the whole gate.
  case "$ASSETS_HAS_ERROR" in
    INVALID_SESSION_ID|INVALID_AUTH_HEADER|INVALID_JWT_FORMAT)
      cat >&2 <<MSG

REFUSING: auth session expired while probing $TEMPLATE_NAME_OR_ID's declared
assets on $ORG_ALIAS. Refresh the org auth ("sf org login web --alias
$ORG_ALIAS") and re-invoke this skill.

MSG
      return 1 2>/dev/null || exit 1
      ;;
  esac

  # Non-auth error on /assets — release doesn't ship /assets, or 403 on the
  # endpoint itself. Log a NOTE and proceed; readiness at step 3 is the last
  # line of defense.
  if [ -n "$ASSETS_HAS_ERROR" ]; then
    echo "NOTE: /assets endpoint returned $ASSETS_HAS_ERROR — skipping C360 dependency check." >&2
    C360_REQUIRED="false"
  else
    # ---- 2b.2: scan SemanticModel assets for C360 base-model references ----
    # Wire-verified 2026-08-26 (v68.0), three coordinated drifts require Python
    # rather than jq for a correct scan:
    #   (a) Response wrapper: coalesce `.assets` / `.templateAssets` /
    #       `.templatedAssets` — v68 uses the third.
    #   (b) Each SemanticModel entry stores its SDM as a stringified,
    #       HTML-entity-encoded (`&quot;`) JSON blob under `.body`. `baseModels`
    #       is INSIDE that parsed body, not on the entry itself.
    #   (c) `baseModels` on v68 is an array of {apiName, label} objects, not
    #       strings. Older releases emit strings and bare `baseModel`. Extract
    #       `.apiName`/`.name` from dict entries in addition to raw string
    #       entries — a `type == "string"` filter drops the C360 ref silently.
    # Match against the SDM name AND the C360 template apiName — release drift
    # has emitted both.
    C360_HITS=$(echo "$ASSETS_JSON" | python3 -c '
import sys, json, html
raw = sys.stdin.read()
try:
    data = json.loads(raw)
except Exception:
    sys.exit(0)
assets = (data.get("assets")
          or data.get("templateAssets")
          or data.get("templatedAssets")
          or [])
targets = {"C360SemanticModel_c360", "sfdc_internal__C360UnifiedSemanticModel"}

def extract_refs(v):
    """Yield apiName-or-string base-model refs from any baseModels/baseModel value."""
    if v is None:
        return
    if isinstance(v, str):
        yield v
    elif isinstance(v, dict):
        for k in ("apiName", "name", "templateApiName", "baseModelApiName"):
            val = v.get(k)
            if isinstance(val, str):
                yield val
                break
    elif isinstance(v, list):
        for e in v:
            yield from extract_refs(e)

def refs_from_container(obj):
    """Collect base-model refs from an SDM dict (top-level AND .definition)."""
    out = []
    if not isinstance(obj, dict):
        return out
    for k in ("baseModels", "baseModel"):
        out.extend(extract_refs(obj.get(k)))
    d = obj.get("definition")
    if isinstance(d, dict):
        for k in ("baseModels", "baseModel"):
            out.extend(extract_refs(d.get(k)))
    return out

hits = []
for entry in assets:
    if not isinstance(entry, dict):
        continue
    if entry.get("assetType") != "SemanticModel":
        continue
    # Try the entry itself first (older releases stored SDM inline).
    refs = refs_from_container(entry)
    # Then parse the stringified, HTML-encoded body (v68+ shape).
    body = entry.get("body")
    if isinstance(body, str) and body.strip():
        try:
            parsed = json.loads(html.unescape(body))
            refs.extend(refs_from_container(parsed))
        except Exception:
            pass
    if any(r in targets for r in refs):
        name = (entry.get("templatedAssetName")
                or entry.get("apiName")
                or entry.get("name")
                or entry.get("fileName")
                or "<unnamed SemanticModel>")
        hits.append(name)

for h in hits:
    print(h)
')

    if [ -n "$C360_HITS" ]; then
      C360_REQUIRED="true"
      echo "C360 dependency detected in $TEMPLATE_NAME_OR_ID. Extending SDMs:" >&2
      echo "$C360_HITS" | sed 's/^/  - /' >&2
    else
      C360_REQUIRED="false"
    fi
  fi

  # =========================================================================
  # If C360_REQUIRED, run the 3-step gate: 2b.3 → 2b.4 → 2b.5
  # Route-resolution runs FIRST so 2b.3/2b.4/2b.5 know which org to probe:
  #   - HOME caller: RESOLVED_ORG_FOR_C360 = $ORG_ALIAS (existing behavior)
  #   - COMPANION caller: RESOLVED_ORG_FOR_C360 = $HOME_ORG_ALIAS
  # 2b.3 (SDM presence) ALWAYS targets $ORG_ALIAS in both roles - Home->
  # Companion propagation IS the actionable signal we're gating on.
  # 2b.4 and 2b.5 target $RESOLVED_ORG_FOR_C360 (Home on companion path).
  # =========================================================================
  if [ "$C360_REQUIRED" = "true" ]; then

    if ! resolve_c360_gate_orgs; then
      # Helper already emitted an actionable refusal to stderr.
      return 1 2>/dev/null || exit 1
    fi

    # ---- 2b.3: SDM presence check on THIS org ------------------------------
    # The C360 Semantic Model must be resolvable in this org's Data Cloud
    # BEFORE we bother checking installed apps or versions. If the SDM isn't
    # visible here, the org's Data Cloud has no C360 publisher — the user has
    # to install C360 in the Home org that publishes to this Data Cloud.
    #
    # Note: $API_BASE ends in /app-framework — the semantic-models endpoint is
    # under /ssot, so we construct the URL fresh instead of reusing $API_BASE.
    #
    # Defense-in-depth: /ssot has historically been served at two path prefixes
    # across releases: /ssot/semantic/models/{name} (current) and older nested
    # forms like /ssot/semantic-models/{name}. We try the canonical path first,
    # then fall through to a reasonable alternate if the first path 404s at the
    # route level (URL_NOT_FOUND / NOT_FOUND at path, not on the SDM name).
    SDM_URL_PRIMARY="/services/data/$API_VERSION/ssot/semantic/models/C360SemanticModel_c360"
    SDM_URL_ALT="/services/data/$API_VERSION/ssot/semantic-models/C360SemanticModel_c360"

    SDM_RESP=$(sf api request rest "$SDM_URL_PRIMARY" \
      --target-org "$ORG_ALIAS" --method GET 2>/dev/null || true)

    # jq shape-tolerant errorCode probe — see note on 2b.1.
    SDM_ERROR=$(echo "$SDM_RESP" | jq -r '.[0]?.errorCode // .errorCode // empty' 2>/dev/null)

    # Alt-path retry: fires when the PRIMARY URL is unreachable at the route
    # level (empty body → likely gateway 4xx/5xx; OR the primary responded with
    # a route-not-found error code). Older orgs served /ssot/semantic-models/
    # instead of /ssot/semantic/models/.
    if [ -z "$SDM_RESP" ] || echo "$SDM_ERROR" | grep -qE '^(URL_NOT_FOUND|NOT_FOUND|UNSUPPORTED_API_VERSION)$'; then
      SDM_RESP=$(sf api request rest "$SDM_URL_ALT" \
        --target-org "$ORG_ALIAS" --method GET 2>/dev/null || true)
      SDM_ERROR=$(echo "$SDM_RESP" | jq -r '.[0]?.errorCode // .errorCode // empty' 2>/dev/null)
    fi

    # If the error is INVALID_SESSION_ID / INVALID_AUTH_HEADER, the sf CLI's
    # cached access token is stale — nudge the user to refresh and abort this
    # step, don't misinterpret it as "SDM missing."
    case "$SDM_ERROR" in
      INVALID_SESSION_ID|INVALID_AUTH_HEADER|INVALID_JWT_FORMAT)
        cat >&2 <<MSG

REFUSING: auth session expired while checking the C360 SDM presence on
$ORG_ALIAS. Refresh the org auth ("sf org login web --alias $ORG_ALIAS")
and re-invoke this skill.

MSG
        return 1 2>/dev/null || exit 1
        ;;
    esac

    # Permission / feature-gate errors on /ssot are NOT "SDM missing" — they
    # mean the caller can't reach the endpoint. Degrade to unknown with a
    # targeted NOTE so the user has an actionable message, not the misleading
    # "install C360 in the Home org" refusal.
    if echo "$SDM_ERROR" | grep -qE '^(INSUFFICIENT_ACCESS|API_DISABLED_FOR_ORG|FUNCTIONALITY_NOT_ENABLED|ACCESS_DENIED)$'; then
      echo "NOTE: /ssot/semantic/models returned $SDM_ERROR on $ORG_ALIAS — caller lacks Data Cloud read perms or Data Cloud is disabled. Skipping SDM presence check; readiness will surface any real base-model failure." >&2
      SDM_PRESENT="unknown"
    # Route-level path-not-found (both endpoints unreachable) — degrade cleanly.
    elif echo "$SDM_ERROR" | grep -qE '^(URL_NOT_FOUND|NOT_FOUND|UNSUPPORTED_API_VERSION)$'; then
      echo "NOTE: /ssot semantic-models endpoint unreachable at $API_VERSION — skipping C360 SDM presence check." >&2
      SDM_PRESENT="unknown"
    elif [ -z "$SDM_ERROR" ] && [ -n "$SDM_RESP" ] && [ "$(echo "$SDM_RESP" | jq -r 'type' 2>/dev/null)" = "object" ]; then
      # Sanity: the response must actually look like the requested SDM. Some
      # releases return `{name, apiName, ...}`, others `{semanticModel: {...}}`.
      SDM_NAME_FIELD=$(echo "$SDM_RESP" | jq -r '.name // .apiName // .semanticModel.name // .semanticModel.apiName // empty' 2>/dev/null)
      if [ -n "$SDM_NAME_FIELD" ]; then
        SDM_PRESENT="true"
      else
        SDM_PRESENT="false"
      fi
    else
      # Empty body OR any other non-classified error → treat as "SDM missing"
      # from this org's perspective. This is the branch that fires the
      # "publish C360 from the Home org" refusal below.
      SDM_PRESENT="false"
    fi

    if [ "$SDM_PRESENT" = "false" ]; then
      case "$ORG_ROLE" in
        COMPANION)
          # AUTO path: install C360 on the resolved HOME_ORG_ALIAS, then poll
          # $ORG_ALIAS for SDM propagation. Bounded ~50 min total (30 install
          # + 20 sync). On success SDM_PRESENT flips true and 2b.4/2b.5 continue.
          echo "[2b state=PROBE_SDM_FALSE role=COMPANION] SDM absent on $ORG_ALIAS - auto-installing on HOME $HOME_ORG_ALIAS." >&2
          if install_c360_on_home_and_wait_for_sync; then
            SDM_PRESENT="true"
          else
            # Helper already printed the exact-failure refusal.
            return 1 2>/dev/null || exit 1
          fi
          ;;
        HOME|*)
          # AUTO path (standalone / paired-HOME): caller IS the publisher, so
          # install C360 on THIS org. Bounded 30 min /apps poll + 10 min SDM
          # visibility poll on the same org. SuccessStatus on /apps is NOT the
          # same as "SDM materialized" - Data Cloud metadata rollout is
          # asynchronous, so we explicitly wait for the SDM to be resolvable
          # via /ssot before returning. There is no cross-org propagation
          # on this branch (companion sync doesn't apply).
          echo "[2b state=PROBE_SDM_FALSE role=HOME] SDM absent on $ORG_ALIAS - auto-installing C360 on the same org (standalone HOME) and waiting for SDM visibility." >&2
          if install_c360_on_home_and_wait_for_sync; then
            SDM_PRESENT="true"
          else
            # Helper already printed the exact-failure refusal.
            return 1 2>/dev/null || exit 1
          fi
          ;;
      esac
    fi

    # ---- 2b.4: installed C360 app on THIS org + its templateVersion --------
    # WIRE FACT (verified 2026-08-25): /app-framework/apps ignores
    # applicationStatus as a query param. Only templateSourceId is a valid
    # server-side filter. We MUST filter status client-side.
    #
    # Wrapper drift: the list body has been served under `.apps`, `.items`,
    # and `.records` across releases. Coalesce all three.
    #
    # Target-org routing: on COMPANION path, the installed C360 app lives on
    # HOME - probing the companion returns zero rows and would false-refuse.
    # $RESOLVED_ORG_FOR_C360 already reflects this (= $ORG_ALIAS on HOME,
    # = $HOME_ORG_ALIAS on COMPANION).
    c360_log "PROBE_INSTALLED" "$RESOLVED_ORG_FOR_C360"
    APPS_RESP=$(sf api request rest \
      "$API_BASE/apps?templateSourceId=sfdc_internal__C360UnifiedSemanticModel" \
      --target-org "$RESOLVED_ORG_FOR_C360" --method GET 2>/dev/null || true)

    # Empty body → treat as "no installed C360 app" but log the wire anomaly.
    if [ -z "$APPS_RESP" ]; then
      echo "WARN: /apps returned empty body while checking C360 install state — treating as not-installed." >&2
      APPS_RESP='{}'
    fi

    APPS_ERROR=$(echo "$APPS_RESP" | jq -r '.[0]?.errorCode // .errorCode // empty' 2>/dev/null)
    case "$APPS_ERROR" in
      INVALID_SESSION_ID|INVALID_AUTH_HEADER|INVALID_JWT_FORMAT)
        cat >&2 <<MSG

REFUSING: auth session expired while checking installed C360 app on
$RESOLVED_ORG_FOR_C360 (role: $ORG_ROLE; caller: $ORG_ALIAS). Refresh the
org auth ('sf org login web --alias $RESOLVED_ORG_FOR_C360') and re-invoke.

MSG
        return 1 2>/dev/null || exit 1
        ;;
    esac

    # First: count SuccessStatus C360 app entries — this is the "is C360
    # installed at all on this org?" signal. Separate from "can we read its
    # templateVersion?" — release drift on the version-field path is NOT the
    # same failure mode as "no successful install."
    INSTALLED_COUNT=$(echo "$APPS_RESP" | jq -r '
      (.apps // .items // .records // [])
      | map(select(
          (.templateSourceId == "sfdc_internal__C360UnifiedSemanticModel") or
          (.templateApiName  == "sfdc_internal__C360UnifiedSemanticModel")
        ))
      | map(select(
          ((.applicationStatus // .status // "") == "SuccessStatus") or
          ((.applicationStatus // .status // "") == "SuccessWithWarningsStatus")
        ))
      | length
    ')

    if [ "${INSTALLED_COUNT:-0}" = "0" ]; then
      cat >&2 <<MSG

REFUSING: $TEMPLATE_NAME_OR_ID extends the C360 Semantic Model, and the
C360 SDM is visible in $ORG_ALIAS's Data Cloud, but there is no
successfully-installed C360 Semantic Model app on $RESOLVED_ORG_FOR_C360
(role: $ORG_ROLE; caller: $ORG_ALIAS) - no entry with applicationStatus
in (SuccessStatus, SuccessWithWarningsStatus).

Either the C360 app install is still in progress, or it FailedStatus'd,
or C360 has only been published from another org (not installed here).

Action required (on $RESOLVED_ORG_FOR_C360):
  Option A — Install / re-install C360 on $RESOLVED_ORG_FOR_C360:
    1. Setup -> App Manager -> New App -> select
       "C360 Semantic Model" (or re-invoke this skill with template name
       "C360 Semantic Model" against $RESOLVED_ORG_FOR_C360).
    2. Wait for applicationStatus in (SuccessStatus,
       SuccessWithWarningsStatus) - typically 5-10 min.
    3. Re-invoke this skill for $TEMPLATE_NAME_OR_ID on $ORG_ALIAS.

  Option B — Wait for in-flight install:
    1. Setup -> Installed Apps -> "C360 Semantic Model" on
       $RESOLVED_ORG_FOR_C360 - check status.
    2. Re-invoke once the app reaches SuccessStatus /
       SuccessWithWarningsStatus (and, for COMPANION path, the SDM has
       propagated to $ORG_ALIAS).

MSG
      return 1 2>/dev/null || exit 1
    fi

    # Extract the successfully-installed C360 app's templateVersion.
    # `templateVersion` has historically lived at the top level of each app
    # entry; on older releases it was nested under `.templateInfo.templateVersion`
    # or `.installedTemplate.templateVersion`. Coalesce all three.
    INSTALLED_TEMPLATE_VERSION=$(echo "$APPS_RESP" | jq -r '
      (.apps // .items // .records // [])
      | map(select(
          (.templateSourceId == "sfdc_internal__C360UnifiedSemanticModel") or
          (.templateApiName  == "sfdc_internal__C360UnifiedSemanticModel")
        ))
      | map(select(
          ((.applicationStatus // .status // "") == "SuccessStatus") or
          ((.applicationStatus // .status // "") == "SuccessWithWarningsStatus")
        ))
      | map(.templateVersion
            // .templateInfo.templateVersion
            // .installedTemplate.templateVersion
            // empty)
      | map(select(. != null and . != ""))
      | .[0] // empty
    ')

    # Also capture the installed C360 app's id. Needed by 2b.5's auto-update
    # branch (PUT /apps/{id} via step 6b's update_app). Same filter as above
    # so we pick the app whose version we just extracted.
    INSTALLED_C360_APP_ID=$(echo "$APPS_RESP" | jq -r '
      (.apps // .items // .records // [])
      | map(select(
          (.templateSourceId == "sfdc_internal__C360UnifiedSemanticModel") or
          (.templateApiName  == "sfdc_internal__C360UnifiedSemanticModel")
        ))
      | map(select(
          ((.applicationStatus // .status // "") == "SuccessStatus") or
          ((.applicationStatus // .status // "") == "SuccessWithWarningsStatus")
        ))
      | map(.id // .appId // .applicationId // empty)
      | map(select(. != null and . != ""))
      | .[0] // empty
    ')

    # ---- 2b.5: MANDATORY C360 templateVersion parity check ------------------
    # The user requirement (2026-08-31): whenever the CALLING template declares
    # a C360 SDM base-model dependency (2b.2), this skill MUST verify that the
    # installed C360 app's templateVersion is in parity with the C360 template
    # version published on the org - installed >= current. There is NO soft-
    # degrade / silent-skip path. If either side of the compare is unreadable,
    # we refuse with actionable remediation rather than proceeding blind.
    #
    # This mirrors the SDM-presence gate (2b.3) in shape: mandatory,
    # non-bypassable, and always emits a clear user-facing verdict.
    if [ -z "$INSTALLED_TEMPLATE_VERSION" ]; then
      # C360 app IS installed ($INSTALLED_COUNT >= 1) but every candidate
      # templateVersion path is empty. Historically this branch soft-degraded
      # to WARN + proceed; per the mandatory-parity policy it now refuses.
      # Rationale: proceeding on an unreadable installed version can silently
      # install $TEMPLATE_NAME_OR_ID against a stale C360, which fails late
      # during base-model resolution after minutes of downstream provisioning.
      cat >&2 <<MSG

REFUSING: $TEMPLATE_NAME_OR_ID extends the C360 Semantic Model, but this
skill could NOT read the installed C360 app's templateVersion on
$RESOLVED_ORG_FOR_C360 (role: $ORG_ROLE; caller: $ORG_ALIAS).

  C360 apps in terminal-success state on $RESOLVED_ORG_FOR_C360: $INSTALLED_COUNT
  Installed C360 templateVersion:                                   <unreadable>
  Fields probed:  .templateVersion, .templateInfo.templateVersion,
                  .installedTemplate.templateVersion   (all empty)

MANDATORY C360 TEMPLATE-VERSION PARITY CHECK cannot proceed without both
versions. This is not a soft-skip - $TEMPLATE_NAME_OR_ID was built against
the current C360 SDM, and installing against an unknown-version C360 app
risks a late base-model-resolution failure.

Action required (run on $RESOLVED_ORG_FOR_C360, then re-invoke this skill):

  1. Inspect the raw /apps response and find where templateVersion lives:
       sf api request rest \\
         '$API_BASE/apps?templateSourceId=sfdc_internal__C360UnifiedSemanticModel' \\
         --target-org $RESOLVED_ORG_FOR_C360 --method GET | jq

  2. If templateVersion exists under a new path, file a bug and share the
     wire shape so 2b.4's coalesce chain can be extended.

  3. Fallback: reconfigure the installed C360 app via
     App Hub -> C360 App tile -> chevron -> Update. The Reconfigure re-lands
     templateVersion in the canonical top-level field.

MSG
      return 1 2>/dev/null || exit 1
    fi
    echo "Installed C360 templateVersion on $RESOLVED_ORG_FOR_C360 (role: $ORG_ROLE): $INSTALLED_TEMPLATE_VERSION" >&2

    # The template's *current* version lives at
    # GET /app-framework/templates/{apiName} -> .releaseInfo.templateVersion.
    # Some older releases also expose it as top-level .templateVersion; coalesce.
    # Target-org routing: on COMPANION, the template metadata that matters
    # is the one on the HOME org (the version the shared C360 was installed
    # against). $RESOLVED_ORG_FOR_C360 already routes correctly.
    c360_log "PROBE_TEMPLATE" "$RESOLVED_ORG_FOR_C360"
    C360_TEMPLATE_RESP=$(sf api request rest \
      "$API_BASE/templates/sfdc_internal__C360UnifiedSemanticModel" \
      --target-org "$RESOLVED_ORG_FOR_C360" --method GET 2>/dev/null || true)

    # Empty-body guard: sf CLI's `2>/dev/null || true` swallows auth-error stderr
    # and returns empty stdout on stale JWT. The jq errorCode probe on empty
    # input yields empty (misses the auth case), and CURRENT_TEMPLATE_VERSION
    # extraction below also yields empty - which would misroute the operator
    # into the "current version unreadable" refusal (whose remediation is
    # inspect-wire-shape, NOT `sf org login web`). Mirror the /assets handler's
    # empty-body branch and refuse with an auth-refresh remediation here.
    if [ -z "$C360_TEMPLATE_RESP" ]; then
      cat >&2 <<MSG

REFUSING: GET $API_BASE/templates/sfdc_internal__C360UnifiedSemanticModel
returned an empty body on $RESOLVED_ORG_FOR_C360 (role: $ORG_ROLE; caller:
$ORG_ALIAS). sf CLI typically writes the auth error to stderr in this case;
an expired session on the /templates GET is the most common cause.

Refresh the org auth and re-invoke:
  sf org login web --alias $RESOLVED_ORG_FOR_C360

MSG
      return 1 2>/dev/null || exit 1
    fi

    # Auth-error probe on the template GET - mirrors the /apps handler above.
    # Without this, an expired session mid-2b.5 would leave CURRENT_TEMPLATE_VERSION
    # empty and route into the "current version unreadable" refusal below, which
    # is the WRONG remediation for an auth problem.
    C360_TEMPLATE_ERROR=$(echo "$C360_TEMPLATE_RESP" | jq -r '.[0]?.errorCode // .errorCode // empty' 2>/dev/null)
    case "$C360_TEMPLATE_ERROR" in
      INVALID_SESSION_ID|INVALID_AUTH_HEADER|INVALID_JWT_FORMAT)
        cat >&2 <<MSG

REFUSING: auth session expired while fetching the current C360 template
metadata on $RESOLVED_ORG_FOR_C360 (role: $ORG_ROLE; caller: $ORG_ALIAS).
Refresh the org auth ('sf org login web --alias $RESOLVED_ORG_FOR_C360')
and re-invoke.

MSG
        return 1 2>/dev/null || exit 1
        ;;
    esac

    CURRENT_TEMPLATE_VERSION=$(echo "$C360_TEMPLATE_RESP" | jq -r '
      .releaseInfo.templateVersion
      // .templateVersion
      // .release.templateVersion
      // empty
    ')

    if [ -z "$CURRENT_TEMPLATE_VERSION" ]; then
      # Historically this branch soft-degraded to WARN + proceed. Under the
      # mandatory-parity policy it now refuses - the compare cannot run
      # without a right-hand side, and proceeding blind risks a late base-
      # model-resolution failure identical to the installed-version-empty
      # branch above.
      cat >&2 <<MSG

REFUSING: $TEMPLATE_NAME_OR_ID extends the C360 Semantic Model, but this
skill could NOT read the current C360 template version from
GET $API_BASE/templates/sfdc_internal__C360UnifiedSemanticModel on
$RESOLVED_ORG_FOR_C360 (role: $ORG_ROLE; caller: $ORG_ALIAS).

  Installed C360 templateVersion:                    $INSTALLED_TEMPLATE_VERSION
  Current   C360 templateVersion (template metadata): <unreadable>
  Fields probed: .releaseInfo.templateVersion, .templateVersion,
                 .release.templateVersion       (all empty)

MANDATORY C360 TEMPLATE-VERSION PARITY CHECK cannot proceed without both
versions. Do NOT interpret this as "C360 is up to date" - we simply cannot
tell.

Action required (run on $RESOLVED_ORG_FOR_C360, then re-invoke this skill):

  1. Inspect the raw /templates response:
       sf api request rest \\
         '$API_BASE/templates/sfdc_internal__C360UnifiedSemanticModel' \\
         --target-org $RESOLVED_ORG_FOR_C360 --method GET | jq

  2. If templateVersion has moved to a new path, share the wire shape so
     2b.5's coalesce chain can be extended.

  3. If the /templates endpoint itself is failing (403, 404, feature-gate),
     resolve the underlying access issue before retrying.

MSG
      return 1 2>/dev/null || exit 1
    fi
    echo "Current  C360 templateVersion on $RESOLVED_ORG_FOR_C360 (role: $ORG_ROLE): $CURRENT_TEMPLATE_VERSION" >&2

      # Portable numeric-tuple compare. templateVersion has been seen in
      # multiple shapes across releases:
      #   "4.0", "4.1", "10.0"    (2-part)
      #   "4.0.0", "4.1.2"        (3-part)
      #   "4.0.0.1"               (4-part, rare)
      # A plain string compare fails ("10.0" < "4.0" lexicographically) and
      # `sort -V` is GNU-only (not on stock macOS `sort`). We roll a pure-bash
      # n-tuple compare with an awk fallback so we don't depend on GNU coreutils.
      compare_versions() {
        # Returns:  -1  if $1 <  $2
        #            0  if $1 == $2
        #            1  if $1 >  $2
        local a="$1" b="$2"
        # Split on '.' into arrays, pad the shorter with zeros so "4.0" cmp "4.0.0" == 0.
        local -a A B
        IFS='.' read -r -a A <<< "$a"
        IFS='.' read -r -a B <<< "$b"
        local n=${#A[@]}
        (( ${#B[@]} > n )) && n=${#B[@]}
        local i ai bi
        for (( i=0; i<n; i++ )); do
          ai=${A[i]:-0}
          bi=${B[i]:-0}
          # Strip any non-digit suffix (e.g. "4.0-beta") — take the leading int only.
          ai=${ai%%[!0-9]*}; bi=${bi%%[!0-9]*}
          ai=${ai:-0};       bi=${bi:-0}
          if (( 10#$ai < 10#$bi )); then echo -1; return; fi
          if (( 10#$ai > 10#$bi )); then echo  1; return; fi
        done
        echo 0
      }

      # awk fallback — used if the bash function above hits a shell we don't
      # trust (e.g. someone runs this under `sh` with no arrays). Same semantics.
      compare_versions_awk() {
        awk -v a="$1" -v b="$2" '
          BEGIN {
            na = split(a, A, ".");
            nb = split(b, B, ".");
            n = (na > nb) ? na : nb;
            for (i = 1; i <= n; i++) {
              ai = (i <= na) ? A[i] : 0;
              bi = (i <= nb) ? B[i] : 0;
              # strip non-digit suffix
              gsub(/[^0-9].*$/, "", ai);
              gsub(/[^0-9].*$/, "", bi);
              if (ai == "") ai = 0;
              if (bi == "") bi = 0;
              ai += 0; bi += 0;
              if (ai < bi) { print -1; exit }
              if (ai > bi) { print  1; exit }
            }
            print 0
          }'
      }

      # Prefer the pure-bash function; if BASH isn't set (e.g. sourced from sh),
      # fall back to awk.
      if [ -n "${BASH_VERSION:-}" ]; then
        CMP=$(compare_versions "$INSTALLED_TEMPLATE_VERSION" "$CURRENT_TEMPLATE_VERSION")
      else
        CMP=$(compare_versions_awk "$INSTALLED_TEMPLATE_VERSION" "$CURRENT_TEMPLATE_VERSION")
      fi

      case "$CMP" in
        0)
          echo "C360 dependency satisfied — installed templateVersion matches current ($INSTALLED_TEMPLATE_VERSION)." >&2
          ;;
        -1)
          # ORG_ROLE=HOME  -> caller IS the resource owner. No shared-blast-
          #                   radius concern. AUTO-REMEDIATE inline via
          #                   PUT /apps/{id} (step 6b update_app + poll).
          #                   On success, set AUTO_UPDATE_PARITY_REACHED=true
          #                   which skips the STOP + wait-for-parity block
          #                   and lets the install proceed to readiness.
          #                   On failure, fall through to the STOP + wait-
          #                   for-parity path below (UI fallback).
          # ORG_ROLE=COMPANION -> $RESOLVED_ORG_FOR_C360 is a shared HOME.
          #                   Auto-updating from a companion's context
          #                   mutates a resource other companions depend on.
          #                   REFUSE the auto-update by default. Caller can
          #                   opt in explicitly via the env var
          #                       TABNEXT_ALLOW_SHARED_HOME_C360_UPDATE=1
          #                   or, when running under a TTY, by answering "y"
          #                   to a one-time confirm prompt. Opt-in runs the
          #                   same PUT + poll code path as HOME. If opt-in
          #                   is absent (or the TTY prompt is declined),
          #                   STOP and drop into the wait-for-parity loop
          #                   expecting an out-of-band Reconfigure.
          local AUTO_UPDATE_PARITY_REACHED=""
          local COMPANION_OPT_IN=""
          if [ "$ORG_ROLE" = "COMPANION" ]; then
            if [ "${TABNEXT_ALLOW_SHARED_HOME_C360_UPDATE:-}" = "1" ]; then
              COMPANION_OPT_IN="env"
              echo "[2b.5 auto-update role=COMPANION] TABNEXT_ALLOW_SHARED_HOME_C360_UPDATE=1 detected - opting in to shared-HOME auto-update on $RESOLVED_ORG_FOR_C360." >&2
            elif [ -t 0 ] && [ -t 2 ]; then
              # TTY prompt. Bounded by a 60 s read timeout so a stalled
              # terminal never wedges the run. Default is NO on empty /
              # non-y input to preserve the "refuse-by-default" invariant.
              cat >&2 <<MSG

CONFIRM SHARED-HOME AUTO-UPDATE (COMPANION $ORG_ALIAS)
------------------------------------------------------
The installed C360 app on HOME $RESOLVED_ORG_FOR_C360 is at
templateVersion $INSTALLED_TEMPLATE_VERSION but the current C360
template ships at $CURRENT_TEMPLATE_VERSION. Continuing the install
of $TEMPLATE_NAME_OR_ID on $ORG_ALIAS requires this to be updated.

$RESOLVED_ORG_FOR_C360 is a HOME shared by every companion paired to
it - reconfiguring the C360 app there will affect ALL of them, not
just this companion. Before proceeding, confirm that ALL companion
consumers (not just $ORG_ALIAS) are OK with the C360 update.

Type 'y' + Enter within 60 s to proceed with the auto-update via
PUT /apps/{id} on $RESOLVED_ORG_FOR_C360. Anything else (or timeout)
declines and drops into the wait-for-parity loop below.

MSG
              local companion_reply=""
              # `read -t 60` returns non-zero on timeout; guard with `|| true`
              # so `set -e`-like shells don't abort the whole skill.
              read -r -t 60 -p "Proceed with shared-HOME C360 update? [y/N]: " companion_reply </dev/tty 2>/dev/null || true
              case "${companion_reply:-}" in
                y|Y|yes|YES|Yes)
                  COMPANION_OPT_IN="tty"
                  echo "[2b.5 auto-update role=COMPANION] TTY opt-in confirmed - proceeding with shared-HOME auto-update on $RESOLVED_ORG_FOR_C360." >&2
                  ;;
                *)
                  echo "[2b.5 auto-update role=COMPANION] TTY opt-in declined (reply='${companion_reply:-<timeout>}'). Falling through to wait-for-parity." >&2
                  ;;
              esac
            else
              echo "[2b.5 auto-update role=COMPANION] no TTY and TABNEXT_ALLOW_SHARED_HOME_C360_UPDATE!=1 - refusing shared-HOME auto-update by default. Falling through to wait-for-parity." >&2
            fi
          fi

          if [ "$ORG_ROLE" = "HOME" ] || [ -n "$COMPANION_OPT_IN" ]; then
            # AU_ROLE_TAG carries the acting role + opt-in mode for logs so
            # a shared-HOME COMPANION opt-in is distinguishable from a
            # standard HOME self-update in the transcript.
            local AU_ROLE_TAG="role=$ORG_ROLE"
            [ -n "$COMPANION_OPT_IN" ] && AU_ROLE_TAG="role=COMPANION opt-in=$COMPANION_OPT_IN"
            if [ -z "$INSTALLED_C360_APP_ID" ]; then
              echo "[2b.5 auto-update $AU_ROLE_TAG] WARN: INSTALLED_C360_APP_ID is empty - cannot drive PUT /apps/{id}. Falling through to wait-for-parity." >&2
            else
              echo "[2b.5 auto-update $AU_ROLE_TAG] driving PUT /apps/$INSTALLED_C360_APP_ID on $RESOLVED_ORG_FOR_C360 to upgrade C360 templateVersion $INSTALLED_TEMPLATE_VERSION -> $CURRENT_TEMPLATE_VERSION." >&2
              # C360 install accepts an empty templateValues on update — same
              # shape as the auto-installer's create body. TEMPLATE_VALUES_RAW
              # is the CALLING template's values, which is the wrong body for
              # the C360 app's update. Pass '{}' explicitly to reuse the same
              # zero-inputs shape as install_c360_on_home_and_wait_for_sync.
              if update_app "$INSTALLED_C360_APP_ID" "$RESOLVED_ORG_FOR_C360" '{}' \
                 && poll_update_to_terminal "$INSTALLED_C360_APP_ID" "$RESOLVED_ORG_FOR_C360" 1800; then
                echo "[2b.5 auto-update $AU_ROLE_TAG] PUT + poll succeeded - re-fetching versions to confirm parity." >&2
                # Re-fetch the installed version. Current version is refetched
                # against the same target-org for symmetry.
                local reup_apps reup_tpl reup_installed reup_current reup_cmp
                reup_apps=$(sf api request rest \
                  "$API_BASE/apps?templateSourceId=sfdc_internal__C360UnifiedSemanticModel" \
                  --target-org "$RESOLVED_ORG_FOR_C360" --method GET 2>/dev/null || true)
                reup_installed=$(echo "$reup_apps" | jq -r '
                  (.apps // .items // .records // [])
                  | map(select(
                      ((.applicationStatus // .status // "") | test("^Success(Status|WithWarningsStatus)$"))
                      and (
                        (.templateSourceId == "sfdc_internal__C360UnifiedSemanticModel") or
                        (.templateApiName  == "sfdc_internal__C360UnifiedSemanticModel")
                      )
                    ))
                  | .[0]
                  | (.templateVersion // .templateInfo.templateVersion // .installedTemplate.templateVersion // empty)
                ')
                reup_tpl=$(sf api request rest \
                  "$API_BASE/templates/sfdc_internal__C360UnifiedSemanticModel" \
                  --target-org "$RESOLVED_ORG_FOR_C360" --method GET 2>/dev/null || true)
                reup_current=$(echo "$reup_tpl" | jq -r '
                  .releaseInfo.templateVersion // .templateVersion // .release.templateVersion // empty
                ')
                if [ -n "$reup_installed" ] && [ -n "$reup_current" ]; then
                  if [ -n "${BASH_VERSION:-}" ]; then
                    reup_cmp=$(compare_versions "$reup_installed" "$reup_current")
                  else
                    reup_cmp=$(compare_versions_awk "$reup_installed" "$reup_current")
                  fi
                  case "$reup_cmp" in
                    0|1)
                      echo "[2b.5 auto-update $AU_ROLE_TAG] parity reached after PUT: installed=$reup_installed current=$reup_current." >&2
                      # On COMPANION, the updated C360 SDM must PROPAGATE
                      # from HOME to CALLER before readiness on $ORG_ALIAS
                      # can bind against it. Wait unbounded (same discipline
                      # as the install-time SDM-visibility wait, per the
                      # user's "keep polling till the SDM is available"
                      # instruction). HOME path skips this — the SDM is
                      # local and readiness will re-read it directly.
                      if [ "$ORG_ROLE" = "COMPANION" ]; then
                        echo "[2b.5 auto-update $AU_ROLE_TAG] blocking on updated C360 SDM propagation to companion $ORG_ALIAS before proceeding." >&2
                        if wait_for_c360_sdm_visible "$ORG_ALIAS" 0 "COMPANION post-update propagation" "$RESOLVED_ORG_FOR_C360"; then
                          echo "[2b.5 auto-update $AU_ROLE_TAG] updated C360 SDM visible on companion $ORG_ALIAS. Proceeding to readiness." >&2
                          INSTALLED_TEMPLATE_VERSION="$reup_installed"
                          CURRENT_TEMPLATE_VERSION="$reup_current"
                          CMP="$reup_cmp"
                          AUTO_UPDATE_PARITY_REACHED="true"
                        else
                          # Auth-error refusal only — the wait is unbounded
                          # so no cap-elapsed path exists. Do NOT flip the
                          # parity flag; the "$AUTO_UPDATE_PARITY_REACHED"
                          # != "true" guard below fires the standard STOPPING
                          # + wait-for-parity path so the operator can refresh
                          # auth on the companion and let the resume gate
                          # pick up parity + visibility together.
                          echo "[2b.5 auto-update $AU_ROLE_TAG] SDM-visibility wait errored out (auth). Falling through to wait-for-parity." >&2
                        fi
                      else
                        echo "[2b.5 auto-update $AU_ROLE_TAG] HOME path — SDM is local, skipping post-update visibility wait. Proceeding to readiness." >&2
                        INSTALLED_TEMPLATE_VERSION="$reup_installed"
                        CURRENT_TEMPLATE_VERSION="$reup_current"
                        CMP="$reup_cmp"
                        AUTO_UPDATE_PARITY_REACHED="true"
                      fi
                      ;;
                    *)
                      echo "[2b.5 auto-update $AU_ROLE_TAG] PUT completed but installed=$reup_installed still < current=$reup_current. Falling through to wait-for-parity." >&2
                      ;;
                  esac
                else
                  echo "[2b.5 auto-update $AU_ROLE_TAG] PUT completed but versions unreadable (installed='${reup_installed:-<empty>}' current='${reup_current:-<empty>}'). Falling through to wait-for-parity." >&2
                fi
              else
                echo "[2b.5 auto-update $AU_ROLE_TAG] PUT or poll failed - falling through to manual Option A/B + wait-for-parity." >&2
              fi
            fi
          fi

          # STOP + wait-for-parity + refusal only fire when auto-update did
          # NOT reach parity (COMPANION path always, or HOME path when the
          # PUT / poll / version-refetch failed).
          if [ "$AUTO_UPDATE_PARITY_REACHED" != "true" ]; then
          if [ "$ORG_ROLE" = "COMPANION" ]; then
            cat >&2 <<MSG

NOTE (COMPANION BLAST RADIUS): $RESOLVED_ORG_FOR_C360 is a HOME org shared
by every companion paired to it - reconfiguring or reinstalling the C360
app there will affect ALL of them, not just this companion ($ORG_ALIAS).
Coordinate with the HOME org owner and every other companion consumer
before executing Option A/B below.

MSG
          fi
          cat >&2 <<MSG

STOPPING install of $TEMPLATE_NAME_OR_ID: C360 template-version mismatch.

  Installed C360 templateVersion on $RESOLVED_ORG_FOR_C360: $INSTALLED_TEMPLATE_VERSION
  Current   C360 templateVersion (template metadata):        $CURRENT_TEMPLATE_VERSION
  Role: $ORG_ROLE   Caller: $ORG_ALIAS

$TEMPLATE_NAME_OR_ID was built against the current C360 SDM - installing
against a stale C360 would fail base-model resolution during downstream
SDM provisioning. This skill will NOT proceed until the installed C360
templateVersion on $RESOLVED_ORG_FOR_C360 matches (or exceeds) the current
template version.

API-DRIVEN RECONFIGURE (Option 0):

  When ORG_ROLE=HOME the skill already attempted this automatically before
  printing this message - the PUT /apps/{id} either failed, its poll timed
  out, or the post-update version re-fetch did not confirm parity. Reasons
  and remediation are captured in the "[2b.5 auto-update role=HOME]" log
  lines above. Fall through to Option A / Option B.

  When ORG_ROLE=COMPANION the auto-update was skipped because
  $RESOLVED_ORG_FOR_C360 is a shared HOME and reconfiguring from a
  companion's context mutates a resource other companions depend on.
  Two opt-in paths exist if you HAVE authorized the shared-HOME update:

    (a) Re-run this skill on $ORG_ALIAS with the env var set:
          TABNEXT_ALLOW_SHARED_HOME_C360_UPDATE=1
        2b.5 will drive PUT /apps/{id} against $RESOLVED_ORG_FOR_C360 the
        same way it does on a HOME caller - no App Hub click-through.

    (b) Re-run this skill on $ORG_ALIAS under an interactive TTY. 2b.5
        will prompt "Proceed with shared-HOME C360 update? [y/N]" (60 s
        read timeout, default N) and, on 'y', drive the same PUT + poll.

  Otherwise coordinate with the HOME org owner (or an admin authorized on
  that HOME) to run the update out-of-band via Option A / Option B, or
  invoke this skill from the HOME alias directly (which auto-remediates
  without an opt-in signal).

  API primitives (for reference / manual invocation on the HOME):

    update_app "\$INSTALLED_C360_APP_ID" "\$RESOLVED_ORG_FOR_C360" "{}"
    poll_update_to_terminal "\$INSTALLED_C360_APP_ID" "\$RESOLVED_ORG_FOR_C360" 1800

  See step 6b for the helper implementations and wire rule I for the PUT
  body shape.

REQUIRED - USER ACTION IN THE UI (default when Option 0 is not authorized):

  Option A (preferred - Reconfigure via App Hub):
    1. Log in to $RESOLVED_ORG_FOR_C360.
    2. Setup -> App Hub  (Quick Find: "App Hub").
    3. Locate the "C360 App" tile.
    4. Click the right-arrow / chevron on the tile to open the app detail.
    5. Click "Update" (or "Reconfigure" if that is the label your release
       shows) and follow the wizard to upgrade to templateVersion
       $CURRENT_TEMPLATE_VERSION.
    6. Wait until the app's applicationStatus returns to SuccessStatus /
       SuccessWithWarningsStatus. The App Hub tile shows the status inline.

  Option B (fallback - Delete + Reinstall, only if Option A is unavailable
  for your release):
    1. App Hub on $RESOLVED_ORG_FOR_C360 -> C360 App tile -> Delete.
    2. App Hub -> New App -> C360 Semantic Model -> Install.
    3. Wait for applicationStatus == SuccessStatus.

This skill is now polling $RESOLVED_ORG_FOR_C360 every 60s for parity
(cap 60 min). It will resume the $TEMPLATE_NAME_OR_ID install
automatically as soon as the installed templateVersion is >= current.
Ctrl-C to abort and re-run later.

MSG
          # Bounded poll waiting for the user's out-of-band Reconfigure to
          # land. Re-fetch both /apps and /templates each iteration - the
          # current template version can drift forward mid-poll if a
          # platform release rolls; parity is defined as installed >=
          # current at each observation.
          local parity_deadline poll_installed_ver poll_current_ver poll_cmp
          local poll_apps_resp poll_tpl_resp poll_iter=0
          parity_deadline=$(( $(date +%s) + 3600 ))
          while [ "$(date +%s)" -lt "$parity_deadline" ]; do
            poll_iter=$(( poll_iter + 1 ))
            sleep 60

            poll_apps_resp=$(sf api request rest \
              "$API_BASE/apps?templateSourceId=sfdc_internal__C360UnifiedSemanticModel" \
              --target-org "$RESOLVED_ORG_FOR_C360" --method GET 2>/dev/null || true)
            poll_installed_ver=$(echo "$poll_apps_resp" | jq -r '
              (.apps // .items // .records // [])
              | map(select(
                  ((.applicationStatus // .status // "") | test("^Success(Status|WithWarningsStatus)$"))
                  and (
                    (.templateSourceId == "sfdc_internal__C360UnifiedSemanticModel") or
                    (.templateApiName  == "sfdc_internal__C360UnifiedSemanticModel")
                  )
                ))
              | .[0]
              | (.templateVersion // .templateInfo.templateVersion // .installedTemplate.templateVersion // empty)
            ' 2>/dev/null)

            poll_tpl_resp=$(sf api request rest \
              "$API_BASE/templates/sfdc_internal__C360UnifiedSemanticModel" \
              --target-org "$RESOLVED_ORG_FOR_C360" --method GET 2>/dev/null || true)
            poll_current_ver=$(echo "$poll_tpl_resp" | jq -r '
              .releaseInfo.templateVersion // .templateVersion // .release.templateVersion // empty
            ' 2>/dev/null)

            if [ -z "$poll_installed_ver" ] || [ -z "$poll_current_ver" ]; then
              echo "[2b.5 wait-for-parity iter=$poll_iter] versions unreadable (installed='${poll_installed_ver:-<empty>}' current='${poll_current_ver:-<empty>}') - continuing." >&2
              continue
            fi

            if [ -n "${BASH_VERSION:-}" ]; then
              poll_cmp=$(compare_versions "$poll_installed_ver" "$poll_current_ver")
            else
              poll_cmp=$(compare_versions_awk "$poll_installed_ver" "$poll_current_ver")
            fi

            case "$poll_cmp" in
              0|1)
                cat >&2 <<MSG

[2b.5 wait-for-parity] parity reached at iter=$poll_iter:
  installed=$poll_installed_ver  current=$poll_current_ver
Resuming install of $TEMPLATE_NAME_OR_ID on $ORG_ALIAS.

MSG
                INSTALLED_TEMPLATE_VERSION="$poll_installed_ver"
                CURRENT_TEMPLATE_VERSION="$poll_current_ver"
                CMP="$poll_cmp"
                break
                ;;
              *)
                echo "[2b.5 wait-for-parity iter=$poll_iter] still stale: installed=$poll_installed_ver current=$poll_current_ver - waiting." >&2
                ;;
            esac
          done

          if [ "$CMP" != "0" ] && [ "$CMP" != "1" ]; then
            cat >&2 <<MSG

REFUSING: C360 templateVersion parity was NOT reached within 60 min on
$RESOLVED_ORG_FOR_C360.
  Last installed: ${poll_installed_ver:-$INSTALLED_TEMPLATE_VERSION}
  Last current:   ${poll_current_ver:-$CURRENT_TEMPLATE_VERSION}
Complete the App Hub Reconfigure (Option A above) or Delete + Reinstall
(Option B), then re-invoke this skill for $TEMPLATE_NAME_OR_ID on
$ORG_ALIAS.

MSG
            return 1 2>/dev/null || exit 1
          fi
          fi  # close the AUTO_UPDATE_PARITY_REACHED guard
          ;;
        1)
          # Installed > current. This is unusual — the installed app is AHEAD
          # of what the template metadata currently advertises. Can happen if
          # the template metadata is being rolled forward and this org already
          # received an early publish. Warn but allow.
          cat >&2 <<MSG

WARNING: installed C360 templateVersion ($INSTALLED_TEMPLATE_VERSION) is
AHEAD of the current C360 template version ($CURRENT_TEMPLATE_VERSION)
advertised by $RESOLVED_ORG_FOR_C360 (role: $ORG_ROLE; caller: $ORG_ALIAS).
This is unusual but not a hard failure - continuing with the install. If
the downstream install fails on base-model resolution, roll the C360 app
back to $CURRENT_TEMPLATE_VERSION on $RESOLVED_ORG_FOR_C360.

MSG
          ;;
      esac

    echo "[2b state=PROCEED role=$ORG_ROLE parity=OK installed=$INSTALLED_TEMPLATE_VERSION current=$CURRENT_TEMPLATE_VERSION] MANDATORY C360 template-version parity check PASSED - SDM on $ORG_ALIAS, C360 app on $RESOLVED_ORG_FOR_C360 at templateVersion $INSTALLED_TEMPLATE_VERSION (>= current template $CURRENT_TEMPLATE_VERSION) - proceeding to readiness." >&2
  fi
fi
```

**Detection invariants:**
- Run this step BEFORE step 3 (readiness) and BEFORE step 4 (create). Readiness alone will NOT catch the C360 dependency — it validates DMOs and access expressions declared in the template's `readiness.json`, not cross-template SDM base-model resolution or version drift.
- The 3-step gate is ordered by increasing specificity: SDM present in Data Cloud (2b.3) → C360 app installed here in `SuccessStatus` (2b.4) → installed `templateVersion` matches current (2b.5). Any earlier failure short-circuits.
- Match on BOTH the C360 SDM name (`C360SemanticModel_c360`) AND the C360 template apiName (`sfdc_internal__C360UnifiedSemanticModel`) — release drift in the `baseModels` field has emitted both forms.
- Match on BOTH `baseModels` (array) AND `baseModel` (string) AND their `.definition.*` nested variants — same drift.
- **`/assets` response wrapper key drifts across three names: `.assets` / `.templateAssets` / `.templatedAssets`.** v68.0 uses the third — coalescing only the first two silently falls through to `[]` and produces a false-negative C360 detection. Wire-verified 2026-08-26 (miss on `sfdc_internal__SalesInsightsTN` before this fix).
- **Each SemanticModel entry stores its SDM as a stringified, HTML-entity-encoded JSON blob under `.body`** — NOT as a nested object on the entry itself. To read `baseModels` you MUST `html.unescape(body)` then `json.loads` first. Reading `.baseModels` on the top-level asset entry returns null on v68.0+.
- **`baseModels` on v68.0+ is an array of `{apiName, label}` objects, not strings.** Wire-verified 2026-08-26: `"baseModels": [{"apiName": "C360SemanticModel_c360", "label": "C360 Semantic Model"}]`. Extract `.apiName` (or `.name` / `.templateApiName`) from dict entries; keep string handling for older releases. A `type == "string"` filter drops every object entry silently.
- The 2b.2 scan uses Python (not jq) because it must combine three transformations that are hard to express safely in jq: response-key coalesce, `html.unescape` + `json.loads` on `.body`, and object-vs-string extraction from `baseModels`. jq shape-tolerance on nested string blobs is a footgun; Python is cheaper.
- The `/apps` list endpoint honors ONLY `templateSourceId` as a server-side filter. **Never** include `applicationStatus` in the query string — the server ignores it and returns the unfiltered set, which is a footgun if you assumed it was filtered. Always filter status with `jq` client-side, matching `SuccessStatus` OR `SuccessWithWarningsStatus` for the version-compare gate — both are terminal-success states (matches what `install_c360_on_home_and_wait_for_sync` accepts; wire-verified: `1zAVF0000000Ez32AE` legitimately lands at `SuccessWithWarningsStatus`). An `InProgressStatus` or `FailedStatus` install is not a real installed version and must not be used to seed `INSTALLED_TEMPLATE_VERSION`.
- The `/apps` response has been served under `.apps`, `.items`, and `.records` across releases — coalesce all three.
- `templateVersion` on the installed app has been top-level, nested under `.templateInfo`, and nested under `.installedTemplate` across releases — coalesce all three.
- The template's *current* version lives at `.releaseInfo.templateVersion` (top-level `.templateVersion` and `.release.templateVersion` are older aliases) — coalesce.
- Version compare MUST be numeric-tuple, not string. `"10.0"` string-compares as less than `"4.0"`, which would silently misclassify a fresh install as stale. Bash uses a pure n-tuple compare (arrays + `10#$n` decimal-force); shells without arrays fall back to an equivalent `awk` implementation. Do NOT use `sort -V` — it's GNU-only, missing from stock macOS `sort`.
- Multi-dot forms (`4.0`, `4.0.0`, `4.0.0.1`) compare by padding the shorter with zeros so `4.0` cmp `4.0.0` returns equal.
- Skip the entire gate when the user is installing C360 itself (`$TEMPLATE_NAME_OR_ID == "sfdc_internal__C360UnifiedSemanticModel"`) — a template doesn't depend on itself.
- The `/ssot/semantic/models/{name}` endpoint has an older nested variant (`/ssot/semantic-models/{name}`). We try the canonical path first and fall through to the alternate on an empty body OR when the primary responds with `URL_NOT_FOUND` / `NOT_FOUND` / `UNSUPPORTED_API_VERSION` — this covers both route-not-found and gateway-blank shapes.
- Auth errors (`INVALID_SESSION_ID`, `INVALID_AUTH_HEADER`, `INVALID_JWT_FORMAT`) mid-check are surfaced explicitly at EVERY probe (2b.1 `/assets`, 2b.3 `/ssot`, 2b.4 `/apps`) and abort the step — they must NOT be misread as "SDM missing" or "app not installed." An empty body from `/assets` refuses with the same auth-refresh remediation because `sf` typically wrote the auth error to stderr (suppressed).
- All errorCode probes use `.[0]?.errorCode // .errorCode // empty` (with the `?` operator) so both array-shape and object-shape error payloads route through the same `case` statement. Plain `.[0].errorCode` throws `Cannot index object with number` on the object shape and `//` does NOT catch it, so the auth-error branch becomes unreachable.
- Non-auth, non-route SDM errors (`INSUFFICIENT_ACCESS`, `API_DISABLED_FOR_ORG`, `FUNCTIONALITY_NOT_ENABLED`, `ACCESS_DENIED`) degrade to `SDM_PRESENT=unknown` with a targeted NOTE — NOT to the "install C360 in the Home org" refusal (whose remediation would be wrong for a permissions/feature-gate problem).
- 2b.4 splits `INSTALLED_COUNT` (any terminal-success C360 app? — matches `SuccessStatus` OR `SuccessWithWarningsStatus`, same set the auto-installer accepts) from `INSTALLED_TEMPLATE_VERSION` (can we read its version?). Count == 0 → refuse "not installed". Filtering strictly on `SuccessStatus` would produce a false refusal immediately after the auto-installer legitimately lands on `SuccessWithWarningsStatus` (wire-verified 2026-08-26 with app id `1zAVF0000000Ez32AE`).
- **MANDATORY C360 TEMPLATE-VERSION PARITY CHECK (2b.5).** Whenever `C360_REQUIRED=true` (i.e. 2b.2 detected a C360 base-model dependency in the caller template's `/assets`), the parity check is non-bypassable. Both operands MUST be readable: `INSTALLED_TEMPLATE_VERSION` from the installed C360 app on `$RESOLVED_ORG_FOR_C360` AND `CURRENT_TEMPLATE_VERSION` from `/templates/sfdc_internal__C360UnifiedSemanticModel`. Neither has a soft-degrade path — an unreadable operand on either side refuses with an actionable "how to inspect the wire and where to file a bug" remediation. The gate is scoped to the *installed C360 app's* templateVersion vs the C360 *template's* current version — the CALLER template's own version (e.g. `sfdc_internal__ServiceInsights` v4.4) is NOT part of this compare. Historical soft-degrade branches (WARN + proceed on either empty version) were removed 2026-08-31 after wire evidence showed a template can pin its C360 dep by apiName only, so `SuccessStatus` on downstream install is not proof that parity was actually observed; skipping the compare hides real drift.
- **Auth errors on the /templates GET refuse with an auth-refresh message, NOT the "current version unreadable" refusal.** 2b.5 probes `.errorCode` on the /templates response before extracting `CURRENT_TEMPLATE_VERSION` so an expired session doesn't get misclassified as "template metadata missing" — which would route the user to a wire-shape investigation when the fix is `sf org login web`.
- **HOME vs COMPANION role is the ONLY thing that determines which org 2b.4 and 2b.5 probe.** `$RESOLVED_ORG_FOR_C360` equals `$ORG_ALIAS` when `ORG_ROLE=HOME` and `$HOME_ORG_ALIAS` when `ORG_ROLE=COMPANION`. 2b.3 (SDM presence) ALWAYS targets `$ORG_ALIAS` in both roles — Home→Companion propagation IS the actionable signal we're gating on.
- **Role probe uses `DataMultiOrgConnection` SOQL (Id, OrgType, ConnectionStatus, ConnectedOrg, ConnectedParentOrg, TenantKey).** Wire-verified 2026-08-26 on v68.0: this is the only canonical signal. `/ssot/tenant-info`, `/connect/tenants`, `/connect/data-cloud/setup`, `PlatformTenant`/`DataCloudTenant`/`TnCompanionOrgAssignment` sObjects are all NOT_FOUND on v68.0 and MUST NOT be used.
- **OrgType classification** (release drift permitted): `OrgType` describes the FAR END of the connection, not the local org. 0 rows → HOME (standalone). ≥1 row `OrgType=HOME` → COMPANION (the paired org is a HOME, so this org is the LOB); Home id lives in `ConnectedOrg` (falls back to `ConnectedParentOrg`). ≥1 row `OrgType=LOB` → HOME (each LOB row is a companion consuming from this org — this org IS the publisher). Any other picklist value → UNKNOWN + refuse. Wire-verified 2026-08-27 on Companion_Org_shared_By_Chhaya_1 (1 row, OrgType=HOME → COMPANION) and Home_Org_shared_By_Chhaya_1 (2 rows, both OrgType=LOB → HOME). PRIOR VERSIONS OF THIS SKILL HAD THIS RULE INVERTED — the SOQL row semantics were misread as "OrgType describes the local org."
- **`INSUFFICIENT_ACCESS`/`ACCESS_DENIED` on the role probe MUST NOT be silently coerced to HOME** — a false-HOME classification would skip the companion auto-install branch and misroute 2b.4/2b.5. Route to `ORG_ROLE=UNKNOWN` and refuse with an actionable remediation (grant read on `DataMultiOrgConnection`, or pin `--home-org-alias`). `INVALID_TYPE`/`SOBJECT_NOT_FOUND` (feature not shipped on this release) IS safe to coerce to HOME.
- **HOME_ORG_ALIAS is resolved via `sf org list --json`** matched on the first 15 chars of `ConnectedOrg` (fallback `ConnectedParentOrg`; sf CLI emits both 15- and 18-char ids across releases; normalize before comparing). If no local sf auth exists for the resolved Home id, the skill prints a full Option-A onboarding message: (1) request the HOME my-domain URL from the HOME admin (org id alone is not enough — Salesforce has no public org-id → my-domain reverse lookup), (2) confirm the login user carries `AppFrameworkManageTemplate` + Tableau Next + Data Cloud, (3) admin runs `sf org login web --instance-url https://<HOME-my-domain>.my.<pod>.salesforce.com --alias home_<15-char-home-id>` at this terminal. Then, INSTEAD OF exiting, `resolve_c360_gate_orgs` enters a bounded auto-resume poll (30 s cadence, 15 min cap) that re-checks `sf org list --json` for the alias. As soon as the admin completes the login in another terminal, the same skill run picks up the alias and continues into 2b.3/2b.4/2b.5 — no re-invoke required. If the 15-min cap elapses, the helper refuses with a "did not appear within 15 min" message and expects a re-run. Password/2FA never leave the admin's side; the CLI stores a HOME-scoped refresh token keyed to the alias. Option B (paste a HOME sf-org-display access token) and Option C (client_credentials via a Connected App) are documented in the STOPPING message as fallbacks but Option A is the default because the token doesn't expire mid-run and no shared secret ends up in shell history. Never guess a HOME URL from the org id or `TenantKey` — always ask the admin.
- **2b.3 SDM-absent auto-install is role-parametric — HOME self-installs, COMPANION cross-org-installs on the paired HOME. BOTH roles then block on C360 SDM visibility before returning.** The single helper `install_c360_on_home_and_wait_for_sync` uses `$RESOLVED_ORG_FOR_C360` as the publisher (== `$ORG_ALIAS` when `ORG_ROLE=HOME`, == `$HOME_ORG_ALIAS` when `ORG_ROLE=COMPANION`). It inlines /readiness → POST /apps → /apps/{id} poll on the publisher (30-min cap). After the /apps install lands in `SuccessStatus`/`SuccessWithWarningsStatus`, the helper delegates to `wait_for_c360_sdm_visible` — a role-parametric SDM-visibility poll against `/ssot/semantic/models/C360SemanticModel_c360` (with fall-through to `/ssot/semantic-models/…` for release drift) that returns 0 the moment the SDM is resolvable, 1 on auth error. **Both roles poll UNBOUNDED** (cap_secs=0): the wait terminates only on SDM visibility, auth expiry (INVALID_SESSION_ID / INVALID_AUTH_HEADER / INVALID_JWT_FORMAT → refuse immediately with a refresh-auth message), or the caller killing the run (Ctrl-C). **HOME/standalone**: target = `$ORG_ALIAS`; SuccessStatus on /apps is necessary but NOT sufficient because Data Cloud metadata rollout is asynchronous, so we block on local SDM materialization before returning. **COMPANION**: target = `$ORG_ALIAS`; cross-org publish flow, SDM must propagate from HOME — latency is not reliably bounded (pairing state and platform backlog dependent), so we poll until it appears. This matches the user's instruction "keep polling till the SDM is available" for both standalone and companion. `wait_for_c360_sdm_visible` still accepts a positive `cap_secs` for future callers that need a bounded probe (kept as an optional argument), but the current install-time callers pass 0. The 2b.3 `HOME|*)` branch invokes the same helper (no separate refusal path — a standalone Home is auto-provisioned exactly like a companion's Home). It does NOT shell out to a nested skill invocation. Wire rule D applies: `applicationStatus`, not `status`.
- **Terminal Home-install states that count as success:** `SuccessStatus` AND `SuccessWithWarningsStatus`. `FailedStatus` refuses immediately with the Home-org app id. Wall-clock timeout refuses with the last observed `applicationStatus`.
- **The Home /apps POST is idempotent w.r.t. an existing install:** `DUPLICATE_VALUE`/`ITEM_ALREADY_EXISTS`/`APP_ALREADY_INSTALLED` short-circuit to the SDM-visibility wait step (`wait_for_c360_sdm_visible`, UNBOUNDED for both HOME and COMPANION at install time — polling continues until the SDM is resolvable). 2b.5 (running against Home) will still catch a stale version and refuse — the idempotency is safe.
- **Version mismatch (2b.5, `CMP=-1`) auto-remediation policy is asymmetric by role, with an explicit COMPANION opt-in.** On `ORG_ROLE=HOME` the caller IS the resource owner — no shared blast radius — so 2b.5 AUTO-DRIVES `update_app` + `poll_update_to_terminal` against `$RESOLVED_ORG_FOR_C360` (== `$ORG_ALIAS`) inline before considering any user-facing STOP, and proceeds to readiness the moment a post-update version re-fetch confirms parity (see wire rule I + step 6b + the `AUTO_UPDATE_PARITY_REACHED` flag). On the COMPANION opt-in path, after parity is confirmed on the HOME, 2b.5 additionally BLOCKS on the updated C360 SDM propagating to `$ORG_ALIAS` via an UNBOUNDED `wait_for_c360_sdm_visible` call before flipping the parity flag — otherwise readiness on the companion could race the cross-org publish and false-fail. On `ORG_ROLE=COMPANION` the resolved org is a shared HOME whose C360 app publishes to every paired companion; auto-updating from a companion's context mutates a resource other companions depend on, so 2b.5 REFUSES the auto-update by default. Two explicit opt-in signals unlock the same PUT + poll path on the COMPANION side: (1) env var `TABNEXT_ALLOW_SHARED_HOME_C360_UPDATE=1` for unattended / scripted runs, (2) an interactive TTY prompt ("Proceed with shared-HOME C360 update? [y/N]", 60 s read timeout, default N) when stdin+stderr are both TTYs. Both preserve the "refuse by default" invariant — silence, timeout, or non-`y` reply falls through to wait-for-parity. When auto-update did NOT reach parity (COMPANION without opt-in, COMPANION opt-in declined, or any auto-update whose PUT / poll / version re-fetch failed), 2b.5 STOPS the install, prints Option A/B App Hub / Setup instructions, and enters a bounded wait-for-parity loop polling `/apps` + `/templates` every 60s (cap 60 min) until the installed `templateVersion >=` current — from an out-of-band Reconfigure (Setup → App Hub → **C360 App** tile → chevron → **Update**) landing. It resumes the install automatically once parity is reached; refuses cleanly if the cap is exceeded. The current template version is re-fetched each iteration — parity is defined by the *current* observation, so a mid-poll release roll that advances the template version does not falsely trip the resume gate.

**Failure modes:**
- **2b.3 SDM absent — auto-install kicks in, no user-facing refusal.** On COMPANION the helper installs C360 on `$HOME_ORG_ALIAS` and then polls `$ORG_ALIAS` UNBOUNDED for propagation (5–15 min typical but not capped — the wait terminates only on SDM visibility, auth expiry, or Ctrl-C). On HOME (paired or standalone) it self-installs on `$ORG_ALIAS` and polls `$ORG_ALIAS` UNBOUNDED for local SDM materialization before returning. Only the /apps install poll is capped (30 min); the SDM-visibility wait is uncapped in both roles per the user's "keep polling till the SDM is available" instruction. If the /apps install itself fails, the skill refuses — see the `REFUSING: POST /apps for C360 on HOME ... failed` / `... reached FailedStatus` / `... did not reach SuccessStatus within 30 min` failure modes below.
- **`REFUSING: ... no successfully-installed C360 Semantic Model app`** (2b.4 fail) — SDM is visible via publish, but the resolved C360 org (HOME on companion path, self on HOME path) has no C360 app entry with `applicationStatus` in (`SuccessStatus`, `SuccessWithWarningsStatus`). Install (or wait for in-flight install) on that org.
- **`STOPPING install of ...: C360 template-version mismatch`** (2b.5 fail, installed `<` current) — install halts and the skill enters a bounded wait-for-parity loop (60s poll, cap 60 min). Remediate via **App Hub Update/Reconfigure** (Setup → App Hub → **C360 App** tile → chevron → Update, follow the wizard) or Delete + Reinstall (App Hub → **C360 App** tile → Delete → New App → C360 Semantic Model). The skill resumes automatically as soon as installed `templateVersion >=` current; if the cap elapses it refuses with the last observed versions and expects a re-run.
- **`REFUSING: ... could NOT read the installed C360 app's templateVersion`** (2b.5 mandatory-parity fail — installed version unreadable) — count of terminal-success C360 apps on `$RESOLVED_ORG_FOR_C360` is ≥1 but every candidate field (`.templateVersion`, `.templateInfo.templateVersion`, `.installedTemplate.templateVersion`) is empty. Inspect the raw `/apps` response to locate the version under a new path, file a bug so 2b.4's coalesce chain can be extended, or run App Hub → C360 App tile → Update to re-land the version in the canonical field.
- **`REFUSING: ... could NOT read the current C360 template version`** (2b.5 mandatory-parity fail — current version unreadable) — the `/templates/sfdc_internal__C360UnifiedSemanticModel` response has empty `releaseInfo.templateVersion` (and the older aliases `.templateVersion` / `.release.templateVersion`). Inspect the raw template response to find the new location, or resolve the underlying access issue (403/404/feature-gate) before retrying.
- **`WARNING: installed C360 templateVersion ... is AHEAD of current`** (2b.5 warn, installed `>` current) — allowed to proceed; the installed app is ahead of the template metadata. Roll back only if downstream base-model resolution actually fails.
- **`/assets` returns empty body** — refused with the "session may be stale" auth-refresh message. Silently proceeding here would bypass the entire C360 gate; empty stdout from `sf` almost always means an auth error written to stderr (suppressed).
- **`/assets` returns `INVALID_SESSION_ID` / `INVALID_AUTH_HEADER` / `INVALID_JWT_FORMAT`** — refused with the auth-refresh message (same handler as 2b.3/2b.4).
- **`/assets` returns HTTP 404 / `NOT_FOUND`** — endpoint not available at this API version. Log the NOTE and proceed; readiness will surface any real base-model failure.
- **`/assets` returns HTTP 403 `ACCESS_DENIED`** — caller lacks `AppFrameworkManageTemplate`. Same remediation as the other App-Framework 403s (see preconditions).
- **C360 scan silently reports "no dependency" on a template that clearly extends C360** (e.g. Sales Insights TN, whose `SalesInsights` SDM has `baseModels: [{apiName: "C360SemanticModel_c360"}]`) — the scanner was matching an outdated wire shape (top-level `.assets` + string `baseModels`). Fixed 2026-08-26: 2b.2 now coalesces `.templatedAssets`, parses `.body` (html-unescape + JSON.parse), and extracts `.apiName` from dict entries. If you see this regress again, verify the wrapper key and `baseModels` element type via a raw `sf api request rest ... /assets | head -50` and update 2b.2's Python scanner.
- **`/ssot/semantic/models` returns `URL_NOT_FOUND` / `UNSUPPORTED_API_VERSION`** — the endpoint is unreachable at the discovered `$API_VERSION`. The gate degrades to `SDM_PRESENT=unknown` (a NOTE, not a refusal) and defers to readiness.
- **`/apps` returns empty body while checking C360 install state** — logged as `WARN` and treated as not-installed (2b.4 will refuse cleanly rather than crash on empty JSON).
- **`INVALID_SESSION_ID` / auth mid-check** — refused with an explicit "refresh the org auth" message. Do NOT silently continue past an auth error, because a downstream 401 would look like "SDM missing" or "app not installed" and mislead the user.
- **`REFUSING: cannot determine HOME/COMPANION role for $ORG_ALIAS`** — `DataMultiOrgConnection` SOQL returned `INSUFFICIENT_ACCESS` / `ACCESS_DENIED`. Grant read on `DataMultiOrgConnection` to the running user in `$ORG_ALIAS`, OR re-invoke with `--home-org-alias <alias>` to pin the COMPANION path explicitly.
- **`REFUSING: $ORG_ALIAS is classified as a COMPANION ... but ... could not resolve the Home org id`** — the DataMultiOrgConnection row with `OrgType=HOME` (meaning the paired far end is a Home, i.e. this org is a companion) lacks both `ConnectedOrg` AND `ConnectedParentOrg`. Re-invoke with `--home-org-alias <alias>` or ask an admin to repair the record.
- **`STOPPING install of <template> on companion <caller>: no local sf CLI auth found for the HOME org paired with this companion`** — the resolved Home org has no matching alias in `sf org list --json`, so 2b.3 / 2b.4 / 2b.5 cannot run their HOME-side App-Framework calls YET. The STOPPING message prints the HOME org id (both 15- and 18-char forms), the three things to request from the HOME admin (my-domain URL, permitted login user with `AppFrameworkManageTemplate`, ~60 s at this terminal), the exact `sf org login web --instance-url https://<HOME-my-domain>.my.<pod>.salesforce.com --alias home_<15-char-home-id>` command to run (Option A), a suggested stable alias (`home_<15-char-home-id>`), the verify-alias `sf org list --json | jq …` recipe, and a short comparison of Option B (token paste) / Option C (client_credentials) so the admin can pick the friction level. Nothing in the skill can synthesize HOME credentials from a companion session — the message deliberately never asks for the admin's password/2FA. After printing the STOPPING message, `resolve_c360_gate_orgs()` does NOT `return 1` immediately — it enters a bounded auto-resume poll (30 s cadence, 15-min hard cap) that re-runs `sf org list --json` and re-attempts the id-15 match. As soon as the HOME admin completes the `sf org login web ... --alias ...` command in another terminal, the next 30-s tick finds the alias and 2b.0 continues INSIDE THE SAME SKILL RUN into 2b.3/2b.4/2b.5 — no user-side re-invoke required. Only if the 15-min cap elapses without the alias appearing does the helper refuse hard with a "HOME alias did not appear within 15 min" message and expect the caller to re-invoke the skill; when re-invoked, 2b.0 re-probes `DataMultiOrgConnection` and picks up the newly-registered alias automatically.
- **`REFUSING: POST /apps for C360 on HOME <home> failed with <errorCode>`** — the auto-install POST on the Home org returned a non-idempotent error. Install C360 manually on Home and re-invoke. `DUPLICATE_VALUE`/`ITEM_ALREADY_EXISTS`/`APP_ALREADY_INSTALLED` do NOT trigger this — they short-circuit to the SDM-visibility wait step instead.
- **`REFUSING: HOME C360 install reached FailedStatus (app <id> on <home>)`** — the auto-install poll observed `applicationStatus == FailedStatus`. Inspect `/apps/<id>` on Home and remediate before retry.
- **`REFUSING: HOME C360 install on <home> did not reach SuccessStatus within 30 min`** — the auto-install poll timed out. Last observed `applicationStatus` is logged. Extend the poll or investigate the Home-org install trace.
- **`REFUSING: C360 was installed on HOME <home> (SuccessStatus) but the C360 SDM did NOT propagate to companion <caller> within N minutes`** — ONLY emitted when a future caller invokes `wait_for_c360_sdm_visible` with a positive `cap_secs`. The default install-time COMPANION path polls UNBOUNDED per user instruction, so this refusal does NOT fire on the standard install flow. If you see it: pairing exists but publish flow is stalled. Check `DataMultiOrgConnection.ConnectionStatus` on both sides and verify `TenantKey` matches. Emitted by `wait_for_c360_sdm_visible` when the target is different from the publisher (COMPANION propagation branch).
- **`REFUSING: C360 was installed on <org> (SuccessStatus) but the C360 SDM did NOT materialize in <org>'s Data Cloud within N minutes`** — ONLY emitted when a future caller invokes `wait_for_c360_sdm_visible` with a positive `cap_secs`. The default install-time HOME/standalone path polls UNBOUNDED per user instruction, so this refusal does NOT fire on the standard install flow. If you see it: /apps reached Success but the SDM has not yet appeared in `/ssot/semantic/models/C360SemanticModel_c360`. Data Cloud metadata rollout is asynchronous; verify Data Cloud is fully provisioned on the org (Setup → Data Cloud Setup), then re-invoke the skill. Emitted by `wait_for_c360_sdm_visible` when the target equals the publisher (HOME self-install branch).
- **Version mismatch on COMPANION path — companion blast-radius NOTE preceding the standard `installed templateVersion ... stale` refusal** — because `$RESOLVED_ORG_FOR_C360` is a shared HOME, the reconfigure/delete+reinstall action must be coordinated with the HOME owner and every other companion consumer. By default 2b.5 does NOT auto-remediate on the COMPANION path (unlike the HOME path, which auto-drives the update inline). Explicit opt-in via `TABNEXT_ALLOW_SHARED_HOME_C360_UPDATE=1` or an interactive TTY `y` reply unlocks the same `update_app` + `poll_update_to_terminal` path — this is the caller's authorization to reconfigure the shared HOME on behalf of every paired companion.

