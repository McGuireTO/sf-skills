---
name: crm-analytics-tableau-next-datacloud-validate
description: "Generic preflight check for Tableau Next / App-Framework template installs — verify Data Cloud is provisioned on the org and resolve the target data space apiName BEFORE a readiness/create call. Returns a PROCEED verdict (exporting the resolved $DATA_SPACE_NAME) or a STOP verdict with an actionable \"enable Data Cloud / create a data space\" message. Invoked by tableau-next-app-install's preflight — it turns the opaque late-stage `TEMPLATEPARSEERROR: Data space [X] is unknown` / `CDP not enabled` failures into an early, clear gate. Not user-invocable; this is a reusable building-block check, not a standalone workflow."
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

# tableau-next-datacloud-readiness

## What this does

A single **generic preflight check** any App-Framework template install can run: *is Data Cloud usable on this org, and what is the real data space apiName?*

App-Framework readiness/create bodies bind any `DataSpaceType` (or data-space-carrying `StringType`) variable to an **existing** data space name. A missing/invalid data space does NOT surface as a clean readiness `FailedStatus` — it fails variable-definition parsing FIRST, so the readiness POST returns an opaque `HTTP 400 TEMPLATEPARSEERROR: Data space [<X>] ... is unknown` (wire-verified 2026-08-19), or `HTTP 400 CDP not enabled` when Data Cloud is off entirely. Running this check up front converts that late, cryptic failure into an early, actionable STOP.

This is the executable form of the caller skill's **precondition 4** and **wire rule G**.

## Contract

**Inputs (must be set by the caller before invoking):**

| Var | Meaning |
|---|---|
| `$ORG_ALIAS` | sf-CLI alias of the target org |
| `$API_VERSION` | resolved API version, e.g. `v69.0` (from the caller's "Discover API version" step) |

**Outputs (exported back to the caller on PROCEED):**

| Var | Meaning |
|---|---|
| `$DATA_SPACE_NAME` | the resolved data space apiName to bind into every `DataSpaceType` / data-space-carrier variable — NEVER the literal `"default"` unless the org's data space is genuinely named `default` |
| `$DC_READINESS_VERDICT` | `PROCEED` or `STOP` |

**Verdict:**
- **PROCEED** — Data Cloud is provisioned and at least one data space exists; `$DATA_SPACE_NAME` is set. The caller may continue to variable-build / readiness / create.
- **STOP** — Data Cloud is off (403 / `CDP not enabled`) or no data space exists. The caller MUST halt the install and route the user to enablement. Do not attempt readiness/create — it will 400.

## Check

```bash
# Precondition: $ORG_ALIAS and $API_VERSION are set by the caller.
: "${ORG_ALIAS:?tableau-next-datacloud-readiness needs ORG_ALIAS}"
: "${API_VERSION:?tableau-next-datacloud-readiness needs API_VERSION}"

# Probe the data spaces endpoint. Capture body AND distinguish a Data-Cloud-off
# org (403 / empty) from a provisioned one. `2>/dev/null` drops the sf beta banner.
DS_JSON=$(sf api request rest "/services/data/$API_VERSION/ssot/data-spaces" \
  --target-org "$ORG_ALIAS" --method GET 2>/dev/null)

DS_COUNT=$(echo "$DS_JSON" | jq -r '(.dataSpaces // []) | length' 2>/dev/null)
DATA_SPACE_NAME=$(echo "$DS_JSON" | jq -r '(.dataSpaces // [] | .[0].name) // empty' 2>/dev/null)

if [ -n "$DATA_SPACE_NAME" ]; then
  DC_READINESS_VERDICT="PROCEED"
  echo "[tableau-next-datacloud-readiness] PROCEED — $DS_COUNT data space(s); using \"$DATA_SPACE_NAME\""
else
  DC_READINESS_VERDICT="STOP"
  cat >&2 <<'MSG'
[tableau-next-datacloud-readiness] STOP — Data Cloud is not usable on this org.
Either Data Cloud (CDP) is not provisioned, or no data space exists.
A template install that binds a DataSpaceType variable WILL fail on the readiness
POST with `TEMPLATEPARSEERROR: Data space [...] is unknown` or `CDP not enabled`.

Fix: have an admin enable Data Cloud and create/confirm a data space, then retry.
This check will not attempt the install.
MSG
fi

export DATA_SPACE_NAME DC_READINESS_VERDICT
```

## Notes

- **Never hardcode `"default"`.** Some orgs' sole data space is `Corp_Ds`, `Sales_Ds`, `Foundations_Corp_Ds`, etc. Posting `"default"` on such an org 400s with `TEMPLATEPARSEERROR: Data space [default] ... unknown`. The caller's Step-2 builder substitutes `$DATA_SPACE_NAME` (this check's output) into every data-space variable.
- **Idempotent + read-only.** This check makes exactly one `GET /ssot/data-spaces` call and mutates nothing. Safe to run standalone or as a preflight gate.
- **Scope.** This check answers "is Data Cloud usable + which data space." It does NOT validate that a specific template's DMOs are mapped/populated — that is the template `readiness.json` chain's job (the caller's Step 3), a separate concern.
