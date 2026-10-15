# Debug — Headline Output Template

Verbatim skeleton and worked example for the **Headline** layer emitted by every run in `[[flow.recipes.testing.workflows.debug]]` Phase 2 → Loop body → step 2. Copy the skeleton exactly — same headers, same order, every section present even if a section is `None` (the one exception is `### Paused`, which appears only while a run is paused). Do not paraphrase headers, merge sections, or reorder.

## Headline skeleton (copy verbatim, fill in per run)

```markdown
### Summary
<One paragraph, business language. What the execution did end-to-end. No element-by-element narration. No `interviewId`, no debug log line numbers, no Aura wire shape.>

### Paused
<Emit ONLY while the run is paused (`interviewStatus` is `WAITING` or `ASYNC_WAITING`); omit this whole section otherwise. State the Wait element the run stopped at, then one bullet per entry in `waitEvents[]`: the event `name` and its resume time (`value`), or "platform event" when `value` is empty.>

### Inputs
<Bulleted list of the inputs that drove this run: `$Record` value / input variables / scheduled path / trigger context. One bullet per input. `None` if the flow takes no inputs.>

### Outputs
<Bulleted list of output variables and their final values. `None` if the flow has no output variables.>

### Governor limits
<Bulleted list of any governor-limit-relevant counters that were exercised (SOQL queries, DML rows, CPU time, etc.). `None if not applicable` for this flow shape.>

### What's next?
Deep dive into execution details? Refine inputs? Try a different scenario? Or save this run as a test?

Is there a specific part of the trace you'd like to focus on?
```

## Paused and resumed runs

- **`### Paused` is the one conditional section.** Every other section stays present even when its value is `None`. Place `### Paused` directly after `### Summary`.
- **While paused, replace the "What's next?" first line** with: `Resume at which wait event? Refine inputs? Or try a different scenario?` Saving as a test is not offered mid-pause.
- **After a resume, keep one cumulative headline.** `### Summary` covers the run so far, and the trace is the original legs plus the resumed leg. Do not emit a second, separate headline for the resumed leg.
- **When the resumed run finishes, drop `### Paused`** and use the normal "What's next?" text. If the user then saves, the run can only be saved as a test without assertions.

## Worked example (record-triggered flow on `Account`, one update, no faults)

```markdown
### Summary
The flow ran on Account `001XX000003DHPq` after an update. It evaluated the entry condition (`Rating` changed to `Hot`), then routed through the `Notify Owner` branch and queued a task assignment for the record owner. No fault paths taken; the flow completed successfully.

### Inputs
- `$Record`: Account `001XX000003DHPq` (Name: "Acme Corp", Rating: `Hot`, prior Rating: `Warm`)
- Trigger context: `RecordAfterSave`, update

### Outputs
- `taskCreated`: `true`
- `assignedTo`: `005XX000001Sv8YQAS`

### Governor limits
- SOQL queries: 1 / 100
- DML rows: 1 / 10,000

### What's next?
Deep dive into execution details? Refine inputs? Try a different scenario? Or save this run as a test?

Is there a specific part of the trace you'd like to focus on?
```

## Worked example (autolaunched flow paused at a Wait, then resumed)

First leg — the run stops at the Wait:

```markdown
### Summary
The flow started with `accountId` set to `001XX000003DHPq`, updated the account's Rating to `Hot`, and then stopped at the `Wait_For_Approval` element. It has not finished yet.

### Paused
The run is waiting at `Wait_For_Approval`. Resumable wait events:
- `Approved_Event`: resumes at 2026-10-14T09:00:00Z
- `Rejected_Event`: platform event

### Inputs
- `accountId`: `001XX000003DHPq`

### Outputs
None

### Governor limits
- SOQL queries: 1 / 100
- DML rows: 1 / 10,000

### What's next?
Resume at which wait event? Refine inputs? Or try a different scenario?

Is there a specific part of the trace you'd like to focus on?
```

After resuming on `Approved_Event` — one cumulative headline, no `### Paused`:

```markdown
### Summary
The flow updated the account's Rating to `Hot`, waited at `Wait_For_Approval`, and after resuming on `Approved_Event` created a follow-up task for the owner. It then completed successfully.

### Inputs
- `accountId`: `001XX000003DHPq`

### Outputs
- `taskCreated`: `true`

### Governor limits
- SOQL queries: 2 / 100
- DML rows: 2 / 10,000

### What's next?
Deep dive into execution details? Refine inputs? Try a different scenario? Or save this run as a test?

Is there a specific part of the trace you'd like to focus on?
```
