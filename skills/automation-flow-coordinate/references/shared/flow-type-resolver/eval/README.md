# flow-type-resolver — evaluation & validation

Two independent checks guard this skill. They answer different questions.

## 1. `verify_supported_types.py` — is the supported set *correct*? (org-check)

Validates that every tuple in `taxonomy.json`'s authoritative `supportedTuples` set is
actually a valid flow type in the connected Salesforce org. This is the guarantee that
Project Codey never claims to support a flow type the platform rejects.

**Validity rules** (see `taxonomy.json.supportedTuples.$comment`):

- `processType` must be in `GET /flowbuilder/schema/process-types`.
- A triggered tuple's `triggerType` must be in
  `GET /flowbuilder/schema/trigger-types?processType=<pt>`.
- A **no-trigger** tuple (no `triggerType`) is valid **by absence** — the org's
  trigger-types list does not contain a `None` entry; a no-trigger flow simply omits the
  trigger. Membership of the `processType` is sufficient.
- `runInMode`, when declared, must be in `getFlowCapabilities.runInModes`.
- `recordTriggerType` is **advisory**: `getFlowCapabilities` returns `200` even for an
  invalid `recordTriggerType` (e.g. `RecordBeforeSave` + `Delete`), so the read endpoints do
  not gate it — it is enforced only at save-time. The script only sanity-checks it against
  `enums.recordTriggerType`.

**Run it:**

```bash
# from repo root, so test-agent/.env resolves
set -a; . test-agent/.env; set +a          # exports CORE_ORG_ALIAS
python3 contributed-skills/flow-agentic-ai/automation-flow-coordinate/references/shared/flow-type-resolver/eval/verify_supported_types.py
# or: python3 .../eval/verify_supported_types.py --org <alias> --api-version v68.0
```

Exits `0` if every supported tuple is valid; non-zero (listing each violation) otherwise.
It also prints, per processType, the org-supported triggers the taxonomy **intentionally
omits** — the supported set is a curated subset, not a mirror of everything the org allows,
so review that list when you change `supportedTuples`. Requires the `sf` CLI
(`sf api request rest`) and an authenticated org alias.

## 2. `score.py` — does the resolver *classify correctly*? (behavioral eval)

Scores the resolver's specCategory predictions (`predictions.jsonl`) against the curated
fixture (`prompts.jsonl`), normalizing through `taxonomy.json`'s alias map, and gates on
overall accuracy. See the header of `score.py`.

A fixture row can also set `"expectAsk": true|false`. On those rows the prediction's
`mustAsk` (missing counts as `false`) has to match too, so a prompt the resolver must ask
about is a miss if it is answered without asking, and the other way round. The `FT-CRM`
rows use this: a "CRM Triggered Flow" request that says "marketing" resolves with no
question, and one that does not is asked first.

```bash
python3 contributed-skills/flow-agentic-ai/automation-flow-coordinate/references/shared/flow-type-resolver/eval/score.py --gate 0.95
```

**What this does and does not prove.** `predictions.jsonl` is a **committed snapshot** of the
resolver's output for each fixture prompt — `score.py` reads it as-is and does **not**
re-run the resolver. So the gate catches a `taxonomy.json` alias/normalizer break (a
prediction that no longer maps to a known category) but **not** a live-classification
regression: if a taxonomy or reasoning-engine change would make the resolver classify a
prompt differently, that only shows up once you **regenerate `predictions.jsonl`** by
re-running the resolver over `prompts.jsonl` and re-scoring. Treat a green `score.py` as
"the committed predictions still normalize and clear the gate," not "the current resolver
still classifies these correctly."

Current score: **79/80 (98.8%)**. The lone miss is `FT-AUTO-003` — a button-invoked, flat
headless clone process (expected `Autolaunched`) that the resolver reads as `Screen`. It is
a documented hard case, kept in the fixture as an honest miss rather than hand-corrected in
`predictions.jsonl`.
