---
name: automotive-cloud-sales-concierge-foundation-coordinate
description: "Set up the Automotive Sales Concierge Agent end to end in a new org. Configure Automotive Sales Concierge from scratch. Stand up the Automotive Sales Concierge foundation completely. This is the single top-level orchestrator that runs all setup Acts in dependency order — Act 0 (enable Automotive Cloud org preferences + assign permission sets), Act 1 (create and activate the Automotive Sales Concierge NGA agent), and Act 2 (ground the agent's search infrastructure: DPE, CBSF, FlexiPages) — headlessly and API-first. TRIGGER when the user wants to \"set up the Automotive Sales Concierge\", \"setup Automotive Sales Concierge end to end\", \"help me setup Automotive Sales Concierge Agent\", \"stand up the Automotive Sales Concierge agent in this org\", \"configure the Automotive Sales Concierge foundation\", or otherwise asks for the whole multi-act Automotive Sales Concierge setup rather than a single narrow step. DO NOT TRIGGER when the user asks for exactly one specific toggle, one specific act, or for non-setup work (creating data, running DPE jobs, messaging channels)."
metadata:
  version: "1.0"
---

# Automotive Sales Concierge Foundation — Orchestrator

Stand up the **setup layer** of the Automotive Sales Concierge steel thread by running its
enablement **Acts in a fixed, dependency-respecting order**, headlessly and API-first, against a
live org. This skill is the single entry point a user (or a higher-level agent) invokes to get the
whole foundation in place; it delegates the actual mutations to focused sub-skills and rolls their
results into one report.

**Scope: foundation setup + agent creation + search infrastructure grounding.** The Acts this
orchestrator runs cover setup activities (enabling org preferences / feature toggles, assigning
permission sets), agent lifecycle (creating the agent from the NGA template, verifying its structure,
activating it), and grounding the agent's search infrastructure (Act 2): cloning + activating DPE
definitions, configuring Criteria-Based Search & Filter (CBSF) for 3 searchable objects, and
deploying CBSF FlexiPages — delegated sequentially to `mfg-spartans/dpe-clone-activate`,
`mfg-knights/CriteriaBasedSearchAndFilter`, and `mfg-knights/activate-flexipage-via-action-override`.
Creating business data, **running** the Data Pipelines (DPE) jobs, and configuring messaging channels
are **not** part of this orchestrator; they are separate downstream skills invoked after the agent is
live.

---

## What this orchestrator runs today

| Order | Act | Sub-skill | What it does |
|---|---|---|---|
| 1 | **Act 0 — Enable the Foundation** | `enable-automotive-sales-concierge-foundation` | Enables the Agentforce platform prerequisites (Einstein GPT Platform, Agent Platform, Einstein Copilot) then turns on the Automotive Cloud org preferences (Automotive Cloud, Scheduler, Agents, Appraisals, CBSF, Appraisal Mgmt, Partner Lead Mgmt, Industries Field Service, Quotes) via the Metadata API at `/services/data/v<apiVersion>/headless/metadata`; hands off the legally-gated Automotive Generative AI preference to the user for UI enablement (HARD STOP — waits for user confirmation); and assigns the foundation permission sets. |
| 2 | **Act 1 — Create & Activate the Agent** | `create-automotive-sales-concierge-agent` | Creates the Automotive Sales Concierge agent from the pre-installed NGA template (`AutoGenAi__AutomotiveSalesConcierge`) via NextGen Authoring (NGA) bundle creation — resolving the template's agentScript, creating an NGA bundle, publishing, and activating. Verifies the subagent structure and all 13 expected actions are present, and activates the agent version so it is live for sales reps. |
| 3 | **Act 2 — Ground the Agent's Search Infrastructure** | `ground-agent-data-pipelines` | Grounds the Sales Concierge's search infrastructure via 3 delegates in sequence: (1) `mfg-spartans/dpe-clone-activate` clones + activates 3 DPE definitions; (2) `mfg-knights/CriteriaBasedSearchAndFilter` creates SearchCriteriaConfiguration + mappings + SearchableObjDataSyncInfo for 3 searchable objects (VehDefSearchableField, DealerProdtSearchableField, DealerVehDefSearchableField); (3) `mfg-knights/activate-flexipage-via-action-override` deploys RecordPage FlexiPages with the CBSF component and activates them inside the Automotive app. A thin delegator: Act 2 owns only the domain data (which templates, which objects, which fields) and sequences the delegates with data threading (DPE 9N1 Ids → CBSF DataSyncJobId; CBSF DeveloperName → FlexiPage searchConfigs). |

Today the orchestrator runs **three Acts (Act 0 → Act 1 → Act 2)**. Act 0 is the foundation every later
Act depends on; Act 1 creates and activates the agent that Act 0 made possible; Act 2 grounds that
agent's search infrastructure — cloning DPE definitions, configuring CBSF search for 3 searchable
objects, and deploying the CBSF FlexiPages inside the Automotive app. Shipping the orchestrator with
this ordered-run contract means future Acts slot in without re-plumbing.

## What this orchestrator is designed to run next

The orchestrator is built to grow. Future setup Acts become **additional sub-skills** under this
workflow, and this skill runs them **in order, after their dependencies succeed**.

CBSF enablement (previously planned as a separate Act 3) has been folded into Act 2 as delegate 2
(`mfg-knights/CriteriaBasedSearchAndFilter`) — the CBSF delegate owns its own pref enablement +
PSL assignment as its first steps, so no separate Act is needed.

When a new Act's sub-skill is added under `source/skills/<act-slug>/`, add a row to the ordered
table above and insert it at the correct position in the **Run Order** below. The dependency rule is
absolute: **an Act runs only after every Act it depends on has completed successfully.**

---

## Run Order (how the orchestrator executes)

Execute the Acts strictly in the order listed in "What this orchestrator runs today", top to
bottom. For each Act:

1. **Preflight the shared runtime once, up front.** Resolve and confirm the target org and the
   target user via `dispatch` (see the sub-skill's step 1 — `GET /services/data/` for API version,
   `GET /services/data/v<apiVersion>/chatter/users/me` for user identity). Capture `username`,
   `apiVersion`, `userId`. If the identity call fails with an auth error, STOP and ask the user to
   re-authenticate the MCP server connection before running any Act. Pass this resolved context
   to every Act so no Act re-resolves it.
2. **Delegate to the Act's sub-skill.** Hand off to the sub-skill for that Act and let it own its
   own workflow, verification, and reporting. Do not re-implement an Act's mechanics in this
   orchestrator — the sub-skill is the single source of truth for how that Act is performed.
   Follow the sub-skill's instructions exactly as written, including any interactive pauses
   (e.g. the GenAI UI handoff in Act 0 step 6 — this is a deliberate HARD STOP that waits for
   user confirmation before resuming; it is NOT a failure or block).
3. **Gate on the Act's outcome before continuing.**
   - **Success** → proceed to the next Act.
   - **Partial success with reported gaps** (e.g. a license-gated preference reads back `false`
     after write — such as Einstein Copilot or Industries Field Service) → the sub-skill will report
     the gap and continue. This is NOT a block — proceed to the next Act.
   - **Blocked** (a prerequisite the Act cannot satisfy headlessly AND that downstream Acts depend
     on — e.g. the Einstein GPT Platform PSL missing, which blocks Agent Platform) → **STOP the
     ordered run.** Do not start a dependent Act on top of an incomplete foundation. Report exactly
     what blocked it, with the failing API response, and what a later Act now cannot rely on.
   - **Hard failure** → STOP, report, do not continue.
4. **Accumulate results** for the consolidated report (see Output Expectations).

Because every Act is idempotent, re-running the orchestrator after fixing a blocker is always safe —
already-enabled preferences and already-assigned permission sets are no-ops.

---

## Rules / Constraints

| Constraint | Rationale |
|---|---|
| Foundation + agent creation + DPE grounding only | This orchestrator runs enablement Acts (preferences + permission sets), agent lifecycle Acts (create + activate from NGA template), and DPE-grounding Acts (clone + activate the DPE definitions the agent needs, via delegation). It never creates business data, **runs** Data Pipelines jobs, registers `SearchableObjDataSyncInfo`, or configures messaging channels — those are separate downstream skills. |
| Fixed, dependency-respecting order | Later Acts assume Act 0's foundation is in place. Running out of order (or continuing past a blocked Act) produces a half-configured org that fails silently later. |
| Delegate, don't duplicate | Each Act's mechanics live in its sub-skill. The orchestrator sequences and reports; it does not re-encode deploy payloads or REST calls. |
| Resolve shared runtime once, pass it down | Resolve org / user / API version at the orchestrator level and hand it to every Act. No Act should re-resolve or hardcode it. |
| Headless only (one documented exception) | No browser, no manual Setup clicks — same rule every Act follows, with exactly one exception: the Automotive Generative AI legal-consent preference (Act 0, step 6) requires a UI handoff where the skill STOPS and WAITS for the user to confirm they've toggled it on in Setup. If nothing else headless works, STOP and explain. |
| Stop on block, never cascade a failure | A dependent Act must not start on an incomplete foundation. Halt the run and report. |

---

## Adding a new Act (contributor note)

To extend this orchestrator with another setup Act:

1. Author the new Act as a sub-skill at
   `contributed-skills/auto-avengers/automotive-sales-concierge-foundation-orchestrator/source/skills/<act-slug>/SKILL.md`
   (same shape as `enable-automotive-sales-concierge-foundation/`).
2. Add it to the ordered tables above, and insert it at the correct dependency position in the Run
   Order.
3. Re-run the skill-onboarding harness. The harness treats each sub-skill as its own delegating
   sibling and refreshes this parent's delegation edges automatically — you do not hand-wire the
   parent-to-child link.

Keep each Act narrow and setup-scoped. If a capability needs data creation, pipeline execution, or
agent deployment, it is not an Act of this orchestrator — it belongs to a downstream skill.

---

## Output Expectations

Report, in order:
1. **Org** — alias, username, API version (resolved once, shared across Acts).
2. **Run plan** — the ordered list of Acts to run this invocation (today: Act 0 → Act 1 → Act 2).
3. **Per-Act result** — for each Act, its own before/after summary and status
   (Success / Blocked / Failed).
4. **Consolidated foundation state** — is the Automotive Sales Concierge foundation fully enabled?
   If not, which Act stopped the run and why (with the specific blocker named).
5. **Next step** — if fully enabled, the setup foundation is ready for the downstream (non-setup)
   Acts; if blocked, the exact entitlement/license the user must obtain before re-running.

---

## Delegated Sub-Skills

| Act | Sub-skill directory | Read for details |
|---|---|---|
| Act 0 — Enable the Foundation | `source/skills/enable-automotive-sales-concierge-foundation/` | That sub-skill's `SKILL.md` (fully self-contained) |
| Act 1 — Create & Activate the Agent | `source/skills/create-automotive-sales-concierge-agent/` | That sub-skill's `SKILL.md` (fully self-contained) |
| Act 2 — Ground the Agent's Search Infrastructure | `source/skills/ground-agent-data-pipelines/` | That sub-skill's `SKILL.md` (thin delegator) + its `constants.json`; delegates sequentially to `mfg-spartans/dpe-clone-activate` (DPE), `mfg-knights/CriteriaBasedSearchAndFilter` (CBSF config), and `mfg-knights/activate-flexipage-via-action-override` (FlexiPage deploy) |

<!-- skill-validate: ignore-start -->
<!-- codey:operations start -->
## Operations Reference

Operations this skill uses — routing and dependency reference.

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `preflight-api-version` | read | — | `GET /services/data/` | — |
| `preflight-resolve-user` | read | — | `GET /services/data/v<apiVersion>` | `preflight-api-version` |
| `delegate-automotive-sales-concierge-foundation-orchestrator-enable-automotive-sales-concierge-foundation` | delegate | — | → `auto-avengers/automotive-sales-concierge-foundation-orchestrator-enable-automotive-sales-concierge-foundation` | `preflight-resolve-user` |
| `delegate-automotive-sales-concierge-foundation-orchestrator-create-automotive-sales-concierge-agent` | delegate | — | → `auto-avengers/automotive-sales-concierge-foundation-orchestrator-create-automotive-sales-concierge-agent` | `delegate-automotive-sales-concierge-foundation-orchestrator-enable-automotive-sales-concierge-foundation` |
| `delegate-automotive-sales-concierge-foundation-orchestrator-ground-agent-data-pipelines` | delegate | — | → `auto-avengers/automotive-sales-concierge-foundation-orchestrator-ground-agent-data-pipelines` | `delegate-automotive-sales-concierge-foundation-orchestrator-create-automotive-sales-concierge-agent` |
<!-- codey:operations end -->
<!-- skill-validate: ignore-end -->
