---
description: Record a quick 1-5 satisfaction rating as local usage telemetry. Manual-only — never dispatched by the model.
argument-hint: "[optional: a number 1-5]"
disable-model-invocation: true
allowed-tools:
  - Bash(${CLAUDE_PLUGIN_ROOT}/scripts/sf-context:*)
---

Collect a quick satisfaction rating about this plugin as usage telemetry. Like every other event
this plugin captures, the rating is buffered locally first, then sent later — at session end,
through your connected org, the same pipeline as the rest of this plugin's telemetry — subject to
your telemetry settings. This command never sends free text, paths, code, or org data anywhere; the
rating is the only thing that goes out.

No matter which outcome below this ends on — ineligible, recorded, skipped, error, or given up
after retries — finish with one more line: "Want to share more than a number? Open an issue:
https://github.com/forcedotcom/sf-skills/issues/new"

1. **Check eligibility first, before asking anything:**
   ```bash
   "${CLAUDE_PLUGIN_ROOT}/scripts/sf-context" feedback-eligibility
   ```
   This prints `{"eligible": true}` or `{"eligible": false, "reason": "<reason>"}` and captures
   nothing by itself. If `eligible` is `false`, do NOT ask for a rating — tell the user plainly why
   none would be recorded right now, then stop:
   - `telemetry_disabled` → "Your rating wouldn't be recorded because telemetry is turned off."
   - `not_sf_project` → "Your rating wouldn't be recorded because this isn't a Salesforce DX
     project — feedback capture is scoped to project work like the rest of this plugin's telemetry."
   - any other reason (e.g. `unavailable`) → "Your rating can't be recorded right now."

2. **If eligible, ask for a 1-5 rating** (1 = not helpful at all, 5 = extremely helpful), in the
   chat as a plain question — do NOT use a structured multiple-choice/selection tool for this: a
   1-5 scale is 5 explicit values, at or past what that kind of tool allows as explicit options, so
   reaching for it here can fail outright. If the user's arguments ($ARGUMENTS) already state a
   number in that range, use it directly and skip the question — no need to narrate that it was
   already supplied, just move straight to recording it.

   Validate before moving on: if $ARGUMENTS or the user's chat reply isn't an integer 1-5 (e.g.
   `0`, `-100`, "not sure"), don't send it to `feedback-record` — ask again for a valid number
   instead. Give up after **3 total attempts** (the initial ask plus 2 re-asks) — don't loop
   forever. If the 3rd attempt is still invalid, say "No worries — skipping the rating for now.
   Run `/salesforce-development:feedback` again anytime." and stop without calling
   `feedback-record`. Same if the user says something like "never mind"/"skip"/"cancel" at any
   point — stop immediately, don't spend the remaining attempts.

3. **Record the rating** with a single literal command — no pipe, no shell variable expansion,
   substituting only the actual numeric rating for `<rating>`:
   ```bash
   "${CLAUDE_PLUGIN_ROOT}/scripts/sf-context" feedback-record <rating>
   ```
   This reads the session id itself and is consent-gated and fail-silent like every other telemetry
   capture in this plugin (it honors `SF_DISABLE_TELEMETRY`/`DO_NOT_TRACK` and the
   `/salesforce-development:telemetry off` setting). It prints exactly one of:
   - `{"result": "recorded"}` — the rating was actually written to the local telemetry buffer.
   - `{"result": "skipped", "reason": "<reason>"}` — nothing was written (same reason vocabulary
     as step 1, plus `"unavailable"` for a transient failure).
   - `{"result": "error", "reason": "invalid_rating"}` — the argument wasn't a bare integer 1-5.

4. **Tell the user exactly what that result was — never assume success:**
   - `recorded` → one concise line, e.g. "Thanks — your rating of **4/5** was recorded."
   - `skipped` → a short, accurate explanation using the reason (same wording as step 1's mapping,
     or "Your rating wasn't recorded — telemetry is unavailable right now." for `unavailable`).
   - `error` → should be rare, since step 2 already validates the number before it ever reaches
     this command — but if it happens anyway, say "That wasn't a valid 1-5 rating, so nothing was
     recorded." and stop; don't silently substitute a number and resubmit on your own.
