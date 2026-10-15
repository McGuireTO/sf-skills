---
name: industries-fundraising-gift-entry-settings-configure
description: "Use this skill when users want to setup configuration for Nonprofit Cloud Fundraising's Gift Entry page. Trigger when users mention fundraising, gift, entry, settings, fundraising gift entry settings."
metadata:
  version: "1.0"
  accessCheck: "IndustriesFundraising.userIsFundraisingAdmin"
---

# Managing Fundraising Gift Entry Settings

## When to Use This Skill

Setup configuration for Nonprofit Cloud Fundraising's Gift Entry page. Three independent surfaces gated by the Fundraising Admin role + the Fundraising org-pref: (1) FieldMappingConfigItem rules that map donor gift fields to target object/field -- READ ONLY today (get-configuration-view); the batch-upsert/batch-delete writes are withheld (rejected), non-functional over the headless path -- see save-configuration-items / delete-configuration-items' rejection reasons; (2) the org-level Gift Entry Grid preference -- fully functional (read / toggle / verify); (3) named grid templates with the only-one-holds single-gift-default flag -- READ ONLY today (get-gift-entry-grid-templates); set-single-gift-default is withheld (rejected), non-functional over the headless path -- see its own rejection reason; delete-gift-entry-grid-template is navigate-only (permanently, not a rejection) -- it hands the user off to the Setup page rather than exposing a callable delete. Grid-template read additionally requires the same Gift Entry Grid customization feature gate as the grid-template writes.

## Workflow

Three independent surfaces; only the reads and the toggle are executable today. Field-mapping: get-configuration-view is the only executable step -- its batch-upsert (save-configuration-items) and batch-delete (delete-configuration-items) siblings are rejected, non-functional over the headless path. Grid org pref: is-enabled / toggle / verify -- fully functional, use freely. Templates: get-gift-entry-grid-templates is the only executable step -- its set-single-gift-default sibling is rejected, non-functional over the headless path. delete-gift-entry-grid-template is navigate-only (permanently, not merely rejected): it's rewritten in place to an api_type: setup_page hand-off with no callable op, since the Setup UI's delete confirmation is irreversibility-gated and its eligibility checks are client-side only.

Root cause of the rejected writes (live-org dispatch confirmed, 2026-08-26): every non-empty payload against the 4 object-argument writes fails with a request-validation error before any business logic runs -- a known deserialization defect in how those write operations bind their inbound payload, tracked for a fix; not a payload, gate, or schema mistake on the caller's side. The zero-arg reads and the boolean-arg toggle are unaffected and dispatch normally.

## Critical Constraints

**Preconditions:**

- User must have IndustriesFundraising userIsFundraisingAdmin access (check: `Fundraising Admin role`)

## Verification Checklist

After every write operation, confirm the effect by re-reading state:

- After `toggle-gift-entry-grid-org-preference`: call `verify-toggle-gift-entry-grid-org-preference` (`GET /headless/invoke/platform/fundraising-gift-entry-settings/is-gift-entry-grid-org-preference-enabled`)
- After (write): call `verify-delete-gift-entry-grid-template` (`GET /headless/invoke/platform/fundraising-gift-entry-settings/get-gift-entry-grid-templates`)

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `get-configuration-view` | read | proposed | `GET /headless/invoke/platform/fundraising-gift-entry-settings` | — |
| `is-gift-entry-grid-org-preference-enabled` | read | proposed | `GET /headless/invoke/platform/fundraising-gift-entry-settings/is-gift-entry-grid-org-preference-enabled` | — |
| `toggle-gift-entry-grid-org-preference` | write | proposed | `PATCH /headless/invoke/platform/fundraising-gift-entry-settings/toggle-gift-entry-grid-org-preference` | — |
| `verify-toggle-gift-entry-grid-org-preference` | verify | — | `GET /headless/invoke/platform/fundraising-gift-entry-settings/is-gift-entry-grid-org-preference-enabled` | `toggle-gift-entry-grid-org-preference` |
| `get-gift-entry-grid-templates` | read | proposed | `GET /headless/invoke/platform/fundraising-gift-entry-settings/get-gift-entry-grid-templates` | — |
| `delete-gift-entry-grid-template` | discovery | proposed | — | `get-gift-entry-grid-templates` |
| `verify-delete-gift-entry-grid-template` | verify | — | `GET /headless/invoke/platform/fundraising-gift-entry-settings/get-gift-entry-grid-templates` | — |

### Read operations

#### `get-configuration-view`

Get configuration view.

**Call:** `GET /headless/invoke/platform/fundraising-gift-entry-settings`   — status: `proposed`

**Output:** Returns `{settings: [row, ...]}` -- FieldMappingConfigItem rows scoped to ProcessType = GiftEntry (Tooling-backed, sourceFieldLabel system-enriched), NOT a MappingType filter. Empty array when no Fundraising-scoped mappings exist. Each row has exactly 7 properties: sourceFieldName, sourceFieldLabel, destinationObjectName, destinationFieldName, sequence (int), fieldMappingConfigId, id. NOTE: the response is `settings`, not `{fields, templates}` -- the field-mapping surface and the grid-template surface are separate reads; templates come from `get-gift-entry-grid-templates`.

#### `is-gift-entry-grid-org-preference-enabled`

Read the org-level Gift Entry Grid preference boolean. The preference lives in the Fundraising settings service; no Metadata OrgPreferenceSettings or Tooling/sObject exposes it.

**Call:** `GET /headless/invoke/platform/fundraising-gift-entry-settings/is-gift-entry-grid-org-preference-enabled`   — status: `proposed`

**Output:** Returns the org-level Gift Entry Grid preference as a bare boolean wrapped in the envelope: `{status_code: 200, body: true|false}`. The preference lives in the Fundraising settings service (no Metadata `OrgPreferenceSettings` type covers it), so this is the canonical read.

#### `get-gift-entry-grid-templates`

Get gift entry grid templates.

**Call:** `GET /headless/invoke/platform/fundraising-gift-entry-settings/get-gift-entry-grid-templates`   — status: `proposed`

**Output:** Returns `{templates: [row, ...]}` where each row carries `developerName`, `masterLabel`, `description`, `isSingleGiftDefault`, `isActive`. Only one row's `isSingleGiftDefault` is true at any time (only-one-holds invariant enforced by the controller when `set-single-gift-default` runs). OOTB template `Default` is always present and pre-set as the single-gift default on a stock org.

**Notes:** gate: Additionally feature-gated on the Gift Entry Grid customization feature -- the same access check covers this read too, not just the set-default/delete writes.

### Write operations

#### `toggle-gift-entry-grid-org-preference`

Toggle the org-level Gift Entry Grid preference (enable boolean). The preference lives in the Fundraising settings service; no Metadata OrgPreferenceSettings or Tooling/sObject exposes it.

**Call:** `PATCH /headless/invoke/platform/fundraising-gift-entry-settings/toggle-gift-entry-grid-org-preference`   — status: `proposed`

**Inputs:**

- `enable` *(`boolean`)* — Toggle the enable preference on or off.

**Notes:** envelope: Arg-taking method (boolean). Dispatches successfully on this org -- verified bidirectional (OFF->ON and ON->OFF), reversible, no confirmation gate. The object-argument writes (save-configuration-items, delete-configuration-items, set-single-gift-default, delete-gift-entry-grid-template) fail for an unrelated, genuine reason -- see each step's functional_defect note.

### Verify operations

#### `verify-toggle-gift-entry-grid-org-preference`

Verify the toggle's effect: re-call is-gift-entry-grid-org-preference-enabled and assert it returns the boolean just set. The companion read observes the same Fundraising service-layer state the toggle writes.

**Call:** `GET /headless/invoke/platform/fundraising-gift-entry-settings/is-gift-entry-grid-org-preference-enabled`

**Depends on:** `toggle-gift-entry-grid-org-preference`

#### `verify-delete-gift-entry-grid-template`

Re-call get-gift-entry-grid-templates and check which template currently carries the single-gift-default flag. delete-gift-entry-grid-template is navigate-only (never headlessly executable), so this read does not depend on it -- it just lists current templates independent of whether a human ever deletes one via the Setup page.

**Call:** `GET /headless/invoke/platform/fundraising-gift-entry-settings/get-gift-entry-grid-templates`

**Notes:** role_after_rejection: delete-gift-entry-grid-template is converted to a navigate-only setup_page hand-off (never headlessly executable -- see its description/source rationale), not merely rejected. This read remains useful standing alone: an agent can call it to list current templates and check which one carries the single-gift-default flag before routing a human through the Setup page to delete one.

### Other operations

#### `delete-gift-entry-grid-template`

Navigation-only -- do not attempt an API call; hand off to the Setup page (view_url) for a human admin to delete a custom Gift Entry Grid template themselves. There is no headlessly-callable version of this step: the Setup UI gates template deletion behind an explicit irreversibility confirmation ("...you can't recover it later...") and template-list eligibility (can't delete the current single-gift-default or the synthesized OOTB "Default" row) is enforced client-side only, in the Lightning grid-template component, not by the controller/service layer. A headless caller bypassing that UI would delete past the user's consent with no eligibility guard. This holds independent of, and would still hold after, the unrelated inbound-model deserialization defect that also currently breaks this step's underlying controller call (see notes.functional_defect) -- fixing that defect would not make this step safe to execute headlessly.

**Status:** `proposed`

**Depends on:** `get-gift-entry-grid-templates`

**Notes:** envelope: N/A -- navigate-only, no dispatch envelope. (Corrects the base SOR's note, which claimed OOTB templates are filtered pre-DML server-side -- they are not: eligibility is enforced client-side only, same as this step's description already explains; moot now regardless, since this step no longer dispatches.); functional_defect: Same root cause as the other object-argument writes -- a known deserialization defect that returns an error on every non-empty payload (tracked, fix pending). Moot for headless dispatch regardless -- this step is converted to navigate-only below on a separate, permanent basis, so that defect is not the operative reason it's non-executable.
