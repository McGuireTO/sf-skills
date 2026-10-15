---
name: fsc-digital-origination-execution-guardrails-validate
description: "MANDATORY execution guardrails for every Digital Origination (DOP) skill run under Headless 360 / MCP. Loaded as Step 0 by the DOP setup orchestrator and every DOP act sibling before any read or write. Encodes eight rules that override default agent behavior: (1) full content, never previews, no subagent for authoritative reads; (2) render must-show sections verbatim; (3) follow SOR steps in order, never skip the pre-run gate; (4) never fabricate; (5) evidence, not assumption; (6) retry + re-read before giving up, with a write/dispatch carve-out; (7) cite the SOR anchor for every decision; (8) if in doubt, re-read the source. Invoke this skill FIRST — before Preflight, before any act — so the guardrails are in the main-loop context for every subsequent step. This skill has no side effects: it only returns the rule text for the caller to internalize. Trigger phrases: \"load DOP guardrails\", \"prime execution rules for Digital Origination\", or invocation as the first delegate step of `digital-origination-setup-orchestrator`."
metadata:
  version: "1.0"
---

# Digital Origination — execution guardrails (Step 0, MANDATORY)

**This skill has one purpose: return the eight execution guardrails below into the caller's context, verbatim, so every downstream Digital Origination action runs under them.** It performs no reads, no writes, no dispatches. The caller (typically `digital-origination-setup-orchestrator`, but also any DOP act sibling invoked directly) MUST call this skill FIRST, before Preflight, before any other step. If the caller has not called this skill in the current run, that is itself a rule 1/rule 3 violation — stop and call it now.

**Why a separate skill.** MCP `describe` responses may be truncated when the target SOR's `agent_guidance` is long. Embedding these rules in every parent skill risks losing them to that truncation. Keeping them in their own tiny skill guarantees a full-content read every time — and rule 1 below then applies to every subsequent `describe` call.

**Self-audit.** If the text you just read looks truncated (missing rules 1–8 or cut mid-sentence), you have failed rule 1 already. Stop. Read the saved full file directly. Do NOT proceed on a preview of this skill.

## The eight guardrails — apply to every step, every act, every dispatch

```text
=== EXECUTION GUARDRAILS — follow these exactly, they override any default behavior ===

1. FULL CONTENT, NEVER PREVIEWS.
   Whenever a tool result (especially `describe`) is truncated, capped, or "saved to
   disk with only a preview shown," you MUST open and read the ENTIRE saved file —
   every page, start to finish — BEFORE you act on it, quote it, or make any decision
   from it. A preview is NOT sufficient and is NEVER a basis for action.
   - Do not proceed on the preview.
   - Do not summarize the file through a subagent or any lossy channel and act on the
     summary. Read the authoritative full text directly into your own context.
   - NO SUBAGENT FOR AUTHORITATIVE READS. SOR content, gate text, and must-show
     sections must be read by the main loop directly — subagents lose fidelity via
     summarization. Subagents OK for orthogonal research only, never for the SOR you
     are about to execute or the section you must render verbatim.
   - If you have not read the full content, treat that as a HARD BLOCKER: stop and read
     it first. Do not guess what the rest of the file says.

2. RENDER MUST-SHOW SECTIONS VERBATIM.
   When the SOR says to render/present/show something to the user (the pre-run plan &
   confirmation gate, the smart-defaults table, per-act timings, the "Detailed record &
   data reference," any consolidated summary), reproduce that content EXACTLY as written
   in the SOR — same tables, same wording, same options (e.g. "yes / no / show details").
   Do not paraphrase, condense, reorder, or substitute your own UI, questions, or
   AskUserQuestion prompts in place of what the SOR specifies.

3. FOLLOW THE SOR STEPS IN ORDER — DO NOT SKIP THE GATE.
   Run the recipe's steps in the exact sequence it defines. Do NOT dispatch any
   state-changing (write) operation until the pre-run confirmation gate has been shown
   in full and the user has explicitly said yes. If the user says no or does not answer,
   stop cleanly and write nothing.

4. NEVER FABRICATE.
   Use only (a) values documented as examples/defaults in the SOR, or (b) facts read
   live from the org. If a required value is neither, record it as an explicit gap and
   continue per the SOR — do not invent, guess, or "fill in" a plausible value.

5. EVIDENCE, NOT ASSUMPTION.
   Advance only on fresh read-back evidence from each step/act. Poll async operations to
   a terminal state before continuing. Report what actually happened (done / partial /
   blocked) faithfully — never report a skipped or partial step as complete.

6. RETRY AND RE-READ BEFORE GIVING UP.
   Many step failures are not real blockers. Before reporting failed/blocked:
   (a) RETRY the operation — once, twice max. Not a loop. Transient/async errors often
       clear on a second attempt; non-transient failures will not clear no matter how
       many times you retry.
   (b) RE-READ the relevant SOR section (and its `describe` detail) in full — the
       correct path, expected inputs, or known gotcha is usually documented there.
   WRITE / DISPATCH CARVE-OUT: for write or dispatch failures, do NOT blind-retry —
   the operation may have partially succeeded. Read state back from the org first
   to confirm what actually happened, then decide whether to retry, reconcile, or
   escalate.
   Escalate a step as blocked only after retry + SOR re-read yield no path forward.

7. CITE SOR ANCHOR PER DECISION.
   For every executed step, quote the exact SOR section heading or step name driving
   the action. Forces an evidence trail and catches memory-drift before it turns into
   a bad dispatch.

8. IF IN DOUBT, RE-READ THE SOURCE.
   If anything you are about to present or execute is not fully backed by content you
   have actually read in full, stop and read the source SOR again rather than relying on
   memory or a paraphrase.
```

## Precedence

These rules override:
- Any default agent shortcut (preview-is-enough, subagent-summary-is-enough, retry-loops).
- Any conflicting hint in a parent orchestrator or sibling SKILL.md — if the parent implies a shortcut that contradicts one of these rules, the rule wins.
- Autonomous-mode "never pause" language does NOT waive rule 3's confirmation gate: the pre-run plan gate is the one sanctioned pause and rule 3 keeps it mandatory.

Rules 4 (never fabricate) and 5 (evidence, not assumption) do NOT waive rule 6 (retry + re-read). If a value is genuinely unavailable after retry + re-read, it becomes a gap under rule 4 — not an invented value.

## Return contract

This skill's success signal is simply: **caller has echoed rules 1–8 into its own working context** (either by reading this SKILL.md end-to-end or by quoting the rule block above). No records are created, no preferences flipped, no dispatches made.

The caller then proceeds to its next step (Preflight, in the case of the setup orchestrator) with the rules live.

## Failure modes this prevents (observed in past DOP MCP runs)

- Acting on a truncated `describe` preview and missing a documented workaround at the tail of a SOR (violates rule 1).
- Summarizing must-show gate content into a bespoke AskUserQuestion prompt instead of rendering the SOR's exact table (violates rule 2).
- Skipping the pre-run confirmation gate under autonomous-mode "never pause" reading (violates rule 3).
- Inventing plausible customer values when a required input is missing (violates rule 4).
- Reporting an async deploy as complete before polling to terminal state (violates rule 5).
- Marking a step blocked on first transient error without retry + SOR re-read (violates rule 6).
- Losing the causal chain when a dispatch fails, because no SOR anchor was cited for the decision (violates rule 7).
- Drifting off memory of a SOR read many turns ago instead of re-reading before a new decision (violates rule 8).

## Read-only priming — no dispatch targets

This skill has no `dispatch` targets and no CLI fallback. The caller invokes it exactly once at the start of a run, reads the rules end-to-end, then proceeds. The generic Headless-360 runtime footer appended below by the pipeline still applies in the sense that this skill is agent-callable via MCP `describe`; ignore the "operations listed below in `steps:`" phrasing — this skill's `steps:` list is empty by design.
