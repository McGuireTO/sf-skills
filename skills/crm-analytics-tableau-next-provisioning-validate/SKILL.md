---
name: crm-analytics-tableau-next-provisioning-validate
description: "Generic preflight check for Tableau Next / App-Framework template installs — verify Tableau Next / App-Framework is provisioned and reachable on the org BEFORE attempting an install. Confirms `GET /app-framework/templates` returns a non-empty list (not empty, not a 403 INSUFFICIENT_ACCESS on the endpoint itself, not NOT_FOUND). Returns a PROCEED verdict (exporting the fetched $TEMPLATES_JSON so the caller need not re-fetch) or a STOP verdict routing the user to Tableau Next enablement. Not user-invocable; this is a reusable building-block check, not a standalone workflow."
metadata:
  version: "1.0"
  cliTools:
  - tool:
    - "jq"
    semver: ">=1.6"
  - tool:
    - "sf"
    semver: ">=2.0.0"
---

# tableau-next-readiness

## What this does

A single **generic preflight check** any App-Framework template install can run: *is Tableau Next / App-Framework actually provisioned on this org?*

If `GET $API_BASE/templates` returns an empty list, an `INSUFFICIENT_ACCESS` on the endpoint itself (not the caller's row-level access), or `NOT_FOUND`, then Tableau Next / App-Framework is not provisioned — no template install can succeed and this is not something an install skill can fix. Running this check up front produces a clear "enable Tableau Next" STOP instead of a confusing empty-templates or 403 mid-flow.

This is the executable form of the caller skill's **precondition 3**.

## Contract

**Inputs (must be set by the caller before invoking):**

| Var | Meaning |
|---|---|
| `$ORG_ALIAS` | sf-CLI alias of the target org |
| `$API_BASE` | resolved App-Framework base, e.g. `/services/data/v69.0/app-framework` (from the caller's "Discover API version" step) |

**Outputs (exported back to the caller on PROCEED):**

| Var | Meaning |
|---|---|
| `$TEMPLATES_JSON` | the full `GET $API_BASE/templates` payload — the caller reuses it in Step 1 (allowlist re-check + presence check) rather than re-fetching |
| `$TN_READINESS_VERDICT` | `PROCEED` or `STOP` |

**Verdict:**
- **PROCEED** — the templates endpoint returned a non-empty list; `$TEMPLATES_JSON` is populated. The caller may continue to enumerate/allowlist.
- **STOP** — empty list, 403 on the endpoint, or NOT_FOUND. Tableau Next / App-Framework isn't provisioned (or the caller lacks visibility). The caller MUST halt and route the user to Tableau Next enablement (out of scope for an install skill).

## Check

```bash
# Precondition: $ORG_ALIAS and $API_BASE are set by the caller.
: "${ORG_ALIAS:?tableau-next-readiness needs ORG_ALIAS}"
: "${API_BASE:?tableau-next-readiness needs API_BASE}"

# Probe the templates endpoint. `2>/dev/null` drops the sf beta banner; a 403 /
# NOT_FOUND surfaces as an error payload that yields count 0 below.
TEMPLATES_JSON=$(sf api request rest "$API_BASE/templates" \
  --target-org "$ORG_ALIAS" --method GET 2>/dev/null)

TPL_COUNT=$(echo "$TEMPLATES_JSON" | jq -r '(.templates // []) | length' 2>/dev/null)

if [ -n "$TPL_COUNT" ] && [ "$TPL_COUNT" -gt 0 ] 2>/dev/null; then
  TN_READINESS_VERDICT="PROCEED"
  echo "[tableau-next-readiness] PROCEED — $TPL_COUNT templates visible on this org."
else
  TN_READINESS_VERDICT="STOP"
  cat >&2 <<'MSG'
[tableau-next-readiness] STOP — Tableau Next / App-Framework is not provisioned
on this org (the templates endpoint returned an empty list, a 403 on the endpoint
itself, or NOT_FOUND).

No App-Framework template can install here. Fix: route the user to Tableau Next
enablement (out of scope for the install skill). This check will not proceed.
MSG
fi

export TEMPLATES_JSON TN_READINESS_VERDICT
```

## Notes

- **Distinguish the two 403s.** An empty list / 403 *on the templates endpoint itself* is a feature gate (Tableau Next not provisioned) — that's what this check catches. A 403 `ACCESS_DENIED` / `INSUFFICIENT_ACCESS` on readiness/create with the endpoint resolving is instead a missing `AppFrameworkManageTemplate` user permission (the caller's precondition 2) — a different remediation, out of this check's scope.
- **Idempotent + read-only.** One `GET /templates` call, mutates nothing. The caller reuses `$TEMPLATES_JSON` so the normal split path makes this call exactly once.
- **Scope.** This check answers "is Tableau Next provisioned + reachable." It does NOT check whether a specific template is on the allowlist or present — that is the caller's Step 1.
