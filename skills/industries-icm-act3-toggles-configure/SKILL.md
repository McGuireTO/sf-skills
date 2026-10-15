---
name: industries-icm-act3-toggles-configure
description: "Act 3 of Health Cloud ICM setup — the five ordered ICM core preference toggles (Enhanced Care Plans, Integrated Care Management master, Care Task sharing, Care Gap Detection, MCG reveal), sequencing the operations already verified on the IntegratedCareManagementSettings setup-page node. Standalone reference for the icm-setup skill's third phase."
metadata:
  version: "1.0"
---

# Act 3 of 8 — ICM Core Feature Toggles

Part of the [`icm-setup`](../../SKILL.md) skill — the **third of eight acts**. Runs after
[Act 1](../act1-prereqs/SKILL.md) and [Act 2](../act2-discovery-framework/SKILL.md), and is
followed by [Act 4](../act4-record-page/SKILL.md) → [Act 5](../act5-genai-suggested-assessments/SKILL.md)
→ [Act 6](../act6-mcg-integration/SKILL.md) → Act 7 → Act 8.
Finishing these toggles is **not** finishing the skill: for an unqualified "set up ICM" request
you must continue through Acts 4 onward to Act 8. Only run Act 3 in isolation when the admin's ask is
explicitly narrow (e.g. "ICM's on, I just need Care Gaps").

## ⛔ Entry gate — should you even be starting here?

**STOP before running any toggle and check how you got here.** If you arrived at Act 3 because
the admin asked to "set up ICM" / "configure ICM" / "enable care management" with **no
narrowing qualifier**, you are in the wrong place: that request is the full 1→8 journey and
**must start at Act 1**, not here. Go back to the [router](../../SKILL.md), post the mandatory
pre-write plan, and begin at Act 1. Do **not** rationalize *"'do ICM setup' just means the
toggles"* — that exact reasoning caused a prior run to deliver a partial setup; it is the bug
this gate exists to stop.

You may run Act 3 as the entry point **only** when the admin's ask explicitly narrows to it —
e.g. "ICM is already on, I just need Care Gaps / Care Task sharing / MCG", or they explicitly
said Acts 1–2 are already done. If you cannot quote an explicit narrowing phrase from the
admin's request, do not run this Act in isolation — return to Act 1. Even when narrowing is
explicit, **read back all five toggle states before writing** and change only what's missing.

## Source of truth for the operations

This Act does **not** define its own step contract. Every operation named below already
exists, verified, on the **`IntegratedCareManagementSettings`** setup-page node (team
`health-cloud-han-solo`) — `describe` that node to read the authoritative contract.
Call those operations by id/controller method exactly as defined there. If you find yourself
re-deriving a route, param name, or verify pattern for one of the five toggles below, stop —
read the node instead. Duplicating the contract in two places is how they drift out of sync.

> **⚠️ Transport: use the customer-executable path on a real org.** Each
> toggle preference has no supported direct customer API of its own; the customer-executable
> primitive is a
> minimal `IndustriesSettings` MDAPI deploy + a **`Settings:Industries` Metadata-API retrieve** to
> read state back. On a real customer org **the underlying endpoint is unavailable and
> returns 404 — expected, not a failure.** Use the MDAPI-deploy +
> retrieve transport (the write operations are already on the node for every toggle). This is the
> parent skill's MDAPI fallback rule applied to the Act-3 toggles; a 404 here never means "the
> toggle can't be set." **Read the five toggle states with ONE retrieve, not five Tooling
> `Is*Enabled` queries** (parent *Transport & deploy discipline* rule 4) — the Tooling
> `SELECT … FROM IndustriesSettings` path server-errors on OrgFarm orgs and can hang to timeout; a
> single `Settings:Industries` retrieve returns every `enableX` element at once. Never read a Tooling
> error as "toggle off."
>
> **Split-deploy + batching discipline.** Toggle 1 (Enhanced Care Plans) must land and be confirmed
> **before** toggle 2 (it provisions the ICM Console app #2 depends on), and toggle 2 turns on
> `HCCareMgmt` — so deploy **#1 alone, confirm, then #2 alone, confirm.** Once #2 is confirmed
> effective, **toggles 3, 4, 5 (the generic-setter toggles keyed by `orgPref`) gate on the master,
> not on each other — deploy the three in ONE transaction** and verify all three with one retrieve
> (fall back to per-toggle deploys only if the combined deploy is rejected). **Full-run note
> (`full_run = true`):** this is parent *Full-run consolidation* Tier 3 — #1 arrives already batched
> with Act 2's items 2–7 in Tier 2b, then #2 alone, then #3–#5 together, plus Version-Aware Historical
> View. On a narrow standalone Act-3 ask, run the chain self-contained here.

## The five toggles, in required order

| # | Toggle (UI label) | Org preference | Write operation | Verify operation |
|---|---|---|---|---|
| 1 | Enhanced Care Plans — **FIRST** | `CarePlansPreference` | `enable-care-plans-preference` | `verify-enable-care-plans-preference` |
| 2 | Integrated Care Management (Automatic Sharing for Goal Assignment Records) | `IntegratedCareManagement` | `enable-integrated-care-management` | `verify-enable-integrated-care-management` |
| 3 | Automatic Sharing for Care Task Records | `careTaskSharingPreference` | `enable-care-task-sharing` | `verify-enable-care-task-sharing` |
| 4 | Care Gap Detection | `careGapPreference` | `enable-care-gap-detection` | `verify-enable-care-gap-detection` |
| 5 | MCG — reveal toggle | `mcgPreference` | `enable-mcg` | `verify-enable-mcg` |

**Why #1 must land before #2:** proven live, not inferred — enabling `CarePlansPreference`
provisions the **ICM Console app** that the ICM master toggle's effective behavior depends
on. The node encodes this with a `depends_on` chain where each write depends on the *prior
toggle's verify step* (not just its write) — preserve that discipline when driving this Act:
confirm state before advancing, don't fire all five writes back-to-back.

**Toggles 3-5 share one generic setter/getter** keyed by an `orgPref` string, while toggle 2
has its own dedicated setter/getter. This asymmetry is real, not an authoring
inconsistency.

**Toggle 5 (MCG) is a reveal toggle** — for an unqualified "set up ICM" it runs like the other
four (all five toggles run). Enabling it reveals the MCG option in the ICM Settings UI; it does
**not** set up the working Milliman integration — that is [Act 6](../act6-mcg-integration/SKILL.md).
See `../../references/mcg-integration-runbook.md` before an
admin assumes "MCG toggle on" means "MCG is set up." Only skip toggle 5 when the admin's ask is
explicitly narrow and excludes MCG.

## After the five toggles — enable Version-Aware Historical View (deferred out of Act 2)

**Version-Aware Historical View for Internal Assessments** — mdApiName
`enableViewInternalAssmtSetting`, `minMdApiVersion` 262 —
is a **Discovery Framework → General Settings** toggle (it lives on the Act 2 page), but its gate
is `(HealthCloud.orgHasHealthCloud && OrgPermissions.HCCareMgmt) || PublicSector.orgHasLPIFeature`.
On a Health Cloud org that means it needs **Care Management (`HCCareMgmt`) effective first** —
which is exactly what Act 3's toggle #2 (`IntegratedCareManagement`) turns on. Act 2 therefore
**defers it to here** rather than silently dropping it (a pre-`HCCareMgmt` deploy reports
"Changed" but never takes effect).

Enable it **after toggle #2 is confirmed effective** (its verify step has passed):

- Transport: minimal `IndustriesSettings` MDAPI deploy of `enableViewInternalAssmtSetting`, at
  the org's own API version (≥262), then a `Settings:Industries` retrieve to confirm it actually
  stuck (bundle it into the toggle-3–5 retrieve in a full run) — same discipline as the five toggles
  above. It is a pure on/off toggle once the gate is met (no extra config, no license beyond Care
  Management).
- What it does: lets users open completed Discovery-Framework internal assessments regardless of
  the current question version — the Lightning component renders historical responses in their
  original context.

If Act 3 is being run in isolation ("ICM's already on, I just need Care Gaps") and the admin did
not ask for this, treat it as optional — offer it, don't force it. For an unqualified full "set up
ICM" run, enable it here so it does not fall through the cracks between Act 2 and later acts.

## Why not the AdminSetup wizard-graph discovery contract?

The `IntegratedCareManagementSettings` setup-page node also documents the Industries
AdminSetup framework — a discovery call to find access-filtered `configurations[].steps[]`,
and a step-execution call to dispatch a discovered action.

**This skill does not use it.** That step-execution surface has no
supported customer-executable transport — external REST callers receive HTTP 404, and
its variants are not customer-reachable either. The
direct MDAPI-deploy + Tooling-read toggle path above is the customer transport and is what you
run. The AdminSetup surface remains documented on that node (status `proposed`) for internal
automation only; do not route customer setup through it.

## Preconditions (from the node)

- Health Cloud provisioned with Care Management capability.
- Running user has Industries Care Management setup access (View Setup / AccessSetup).
- Enhanced Care Plans enabled before the ICM master toggle (the ordering above).

## Act 3 end state — verify by diffing ONE retrieve; do not proceed on a partial

**Before marking Act 3 done, run the single `Settings:Industries` retrieve and assert EVERY row
below reads its expected state in that one response.** This adds **no** org round-trips — it is the
same retrieve you already made to verify the toggle batches; the only new work is comparing the
values you already hold. A "deploy reported Changed" is *not* evidence a toggle stuck (the
silent-drop pattern) — the read-back is. **Any row that reads OFF/absent on a full run → redeploy
just that pref at the org's own API version, re-retrieve, and only then continue.** This
completeness diff is what catches a skipped item or a silently-dropped deploy before it becomes a
re-test cycle.

| # | Toggle | Verify via | Expected (full run) |
|---|---|---|---|
| 1 | Enhanced Care Plans (`CarePlansPreference`) | `verify-enable-care-plans-preference` | ON |
| 2 | Integrated Care Management master (`IntegratedCareManagement`) | `verify-enable-integrated-care-management` | ON — turns on `HCCareMgmt` |
| 3 | Care Task sharing (`careTaskSharingPreference`) | `verify-enable-care-task-sharing` | ON |
| 4 | Care Gap Detection (`careGapPreference`) | `verify-enable-care-gap-detection` | ON |
| 5 | MCG reveal (`mcgPreference`) | `verify-enable-mcg` | ON — skip **only** on a narrow ask that excludes MCG |
| 6 | Version-Aware Historical View (`enableViewInternalAssmtSetting`) | its `Is*Enabled` element in the same retrieve | ON — **owned by this Act, not optional on a full run**; the row most often left OFF |

Row 6 is the one the deferred-from-Act-2 handoff most often drops (it reads OFF unless someone
runs the "After the five toggles" step above) — the diff makes that omission self-evident instead
of silent. **Narrow standalone Act-3 ask** ("ICM's already on, just Care Gaps"): rows the admin
explicitly excluded — and Version-Aware, if unrequested — may read OFF; that is expected, note it,
do **not** redeploy uninvited. On an unqualified full "set up ICM" run, **all six must read ON.**

**➡️ Next: continue to [Act 4](../act4-record-page/SKILL.md).** Unless the admin's ask was
explicitly narrow (just toggles / "ICM's already on"), the ICM setup is **not complete** until
Act 4's end state is reached. Do not report "ICM setup done" here.

## What Act 3 does not cover — these are expectation-setting notes, NOT stop signals

The items below are deferred *sub-features*. Mention them so the admin has accurate
expectations, then **keep going** — first any remaining Act 3 work, then Act 4. **Do not use
any of these as a reason to end the run after the toggles.**

- Care Gap Detection being ON does not mean care gaps will surface — Clinical Measures must be
  configured separately per clinical protocol (P1, out of scope for this skill). This is a
  note to relay, **not** a reason to stop; Act 4 still runs.
- MCG toggle 5 being ON does not mean MCG is integrated — see the MCG runbook reference before
  setting that expectation with an admin.

If you must stop early for a genuine blocker, say explicitly: "Acts 1–3 done; Act 4 not run
because &lt;blocker&gt;" — never imply the whole setup is complete when Act 4 has not run.

<!-- skill-validate: ignore-start -->
<!-- codey:operations start -->
## Operations Reference

Operations this skill uses — routing and dependency reference.

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `hchan-icms-verify-enable-care-plans-preference` | verify | — | `IndustriesSettings.query` | — |
| `hchan-icms-verify-enable-integrated-care-management` | verify | — | `IndustriesSettings.query` | — |
| `hchan-icms-verify-enable-care-task-sharing` | verify | — | `IndustriesSettings.query` | — |
| `hchan-icms-verify-enable-care-gap-detection` | verify | — | `IndustriesSettings.query` | — |
| `hchan-icms-verify-enable-mcg` | verify | — | `IndustriesSettings.query` | — |
<!-- codey:operations end -->
<!-- skill-validate: ignore-end -->
