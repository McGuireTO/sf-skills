---
name: industries-home-health-operating-hours-create
description: "Discover or create an OperatingHours record for a Home Health coverage calendar, then define its TimeSlot rows. Triggers on \"create Home Health operating hours\", \"set up coverage schedule\", or as a delegation target from `home-health-guided-setup-care-and-skill-setup` (Phase 3 steps 2-3)."
metadata:
  version: "1.0"
---

# Home Health — Create Operating Hours

Child skill extracted from `home-health-guided-setup` Phase 3 steps 2 (`CreateOperatingHours`) and 3 (`UpdateOperatingHours`), kept together because step 3 edits the record step 2 creates — not two independently dispatchable steps. `[data]`.

Org links: `OperatingHours` new-record page (help: https://sfdc.co/HomeHealthOperatingHours), then `/lightning/o/OperatingHours/home` to add time slots (help: https://sfdc.co/HomeHealthAddSlots).

Follow the shared **`sfs-sobject-create` customer-context pattern** — this step **`delegates_to: sfs-setup-experience/sfs-sobject-create`**: discover existing reusable calendars first (a typical org already has generic ones like "Base Calendar"/"Gold Appointments Calendar") before creating a new one. Never invent a timezone or schedule — ask.

**Step 1 — create the calendar.** Proven payload (replay with real values):
```text
POST {INST}/services/data/{API}/sobjects/OperatingHours
{ "Name":"<CALENDAR_NAME>", "TimeZone":"<IANA_TZ>" }
```
`TimeZone` must be a real IANA id (e.g. `America/Denver`) — ask the customer their site timezone, never default it.

**Step 2 — add TimeSlot rows (one per day-of-week block), child of the OperatingHours just created or discovered:**
```text
POST {INST}/services/data/{API}/sobjects/TimeSlot
{ "OperatingHoursId":"<LOOKUP:OperatingHours.Id>", "DayOfWeek":"Monday",
  "StartTime":"09:00:00.000Z", "EndTime":"17:00:00.000Z", "Type":"Normal" }
```
**GOTCHA: `StartTime`/`EndTime` are time-of-day in UTC** (`…Z` suffix) — the platform stores the wall-clock slot against the OperatingHours' own `TimeZone`; the `Z` is the accepted serialization, not a UTC conversion of the local time. `Type:"Normal"` is **FIXED**. One row per day (or per sub-block if the customer splits the day) — ask for the real coverage schedule, don't assume Mon-Fri 9-5.

## Return contract (for callers delegating to this skill)

Report back the OperatingHours Id (existing or newly created) and the TimeSlot rows written, keyed by calendar name, so `home-health-create-service-territory` can reference it.

## Companion references

- `health-cloud-revan/home-health-guided-setup-care-and-skill-setup` — combined Phase 3 + Phase 4 orchestrator.
- `health-cloud-revan/home-health-create-service-territory` — Phase 3 leaf — ServiceTerritory.
- `health-cloud-revan/home-health-guided-setup` — the root orchestrator (full 16-group Home Health wizard) that delegates to this skill.
- `sfs-setup-experience/sfs-sobject-create` — the canonical entity-create pattern (describe → query-existing → create).
