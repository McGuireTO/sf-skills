# `/feedback` — how it's built

Short reference for the manual-only `/salesforce-development:feedback` command and the `feedback`
telemetry event it records. Work item: [W-24051169](https://gus.lightning.force.com/lightning/r/ADM_Work__c/a07EE00002jNnK0YAK/view)
carries the acceptance criteria; this doc carries the mechanics.

## What it does

`commands/feedback.md` (manual-only, `disable-model-invocation: true`) asks one plain conversational
question — a 1-5 satisfaction rating — and records it locally as a telemetry event. **The plugin
never transmits free text, paths, code, or org data, on its own or otherwise.**

- **Rating**: integer 1-5 (1 = not helpful at all, 5 = extremely helpful).
- The question is asked as ordinary chat text, not a structured multiple-choice tool — that kind of
  tool caps explicit options below what a 5-value rating scale needs.
- There is no theme picker and no external form: the whole interaction is the one in-chat question,
  and nothing ever opens a browser.

## The data model — one number

A submission is captured as a single `feedback` record (`_write_event("feedback", {"rating": ...},
payload)` in `sf_telemetry.py`). It's projected onto the O11y PDP shape as one `feedback.submitted`
event:

- `eventVolume` = the rating (numeric).
- `contextName` / `contextValue` = `""` — there is no categorical dimension for this event; rating
  alone is the whole signal.

`eventVolume` is O11y's PDP **sum** metric by construction — there's no average mode in the raw
transport. An average has to be computed downstream (sum ÷ count) by whoever builds the dashboard.

Like every other event type, this PDP shape is also derived onto the UIP/a4d pipeline
(`_to_a4d_event`), carrying the same coarse `org_bucket` (and raw `org_id` when live-resolved at
transmit time) as everything else. `feedback` is not UIP-exempt — it's just numeric only, on both
shapes, never free text.

## Guardrails (structural, not just convention)

- `_ALLOWLIST["feedback"] = {"rating"}` — any other key is dropped before the event ever reaches
  disk, regardless of what the capture call sends.
- `capture_event`'s `feedback` branch re-validates the rating; an out-of-range or non-int value
  drops the *whole* event rather than partially recording it.
  `test_free_text_comment_never_reaches_the_buffer` in `test_sf_telemetry.py` is the load-bearing
  regression test for this.
- Consent-gated identically to every other event (`SF_DISABLE_TELEMETRY`/`DO_NOT_TRACK`/`/telemetry
  off`) — no separate bypass for `feedback`.
- The capture call passes `session_id` (`$CLAUDE_CODE_SESSION_ID`) so it flushes with the rest of
  that session's events; `cmd_flush` also sweeps a session-less buffer on every flush as a
  belt-and-braces net in case some other caller ever omits it.

## Known open items (not code — decisions/approvals)

- **Telemetry/privacy-owner sign-off** — required on W-24051169 before merge; not yet recorded.
- **Free-text feedback** — raised in PM review as a possible future addition (a satisfaction rating
  plus an always-offered inline free-text field, logged directly and AI-sorted into themes later).
  Not approved or scoped yet; would need its own privacy/legal review since it would be the first
  unbounded-text field in this telemetry pipeline, and would still carry `org_bucket`/`org_id` like
  every other event. Tracked as an open question, not committed work.
- **Dashboard aggregation** — whoever builds the feedback dashboard should decide, and document,
  what they compute from `eventVolume`; not a plugin-side decision.
