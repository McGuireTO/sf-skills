---
name: marketing-e360-email-archiving-configure
description: "Use this skill when users want to setup for org-level 360 Email Archiving. Trigger when users mention e360email, archiving, e360email archiving."
metadata:
  version: "1.0"
  accessCheck: "(Gater.EnableEmailArchiving) || (OrgPermissions.TrustedServiceArchiveAddon)"
---

# Managing E360 Email Archiving

## When to Use This Skill

Setup for org-level 360 Email Archiving. Reads/writes two UDD org prefs (EmailArchivingEnabled, EmailArchiveOverrideAtIA) and surfaces the TrustedServiceArchiveAddon license flag (gates UI write-interactivity). Server invariants — archiving=false force-disables the IA override; IA-override=true is silently rejected (returns iaOverrideEnabled=false) when archiving is off. Three steps: read state, toggle archiving, toggle IA override. No public Connect/Tooling/Metadata path; these are internal provisioning prefs.

## Workflow

Read get-initial-load-config first to snapshot isArchivingEnabled, iaOverrideEnabled, and isTrustedServiceArchiveAddOnEnabled. Then mutate: update-email-archiving-enabled-pref toggles archiving (enabled=false ALSO force-disables the IA override server-side — expect iaOverrideEnabled=false in the echo); set-archive-override-at-ia-pref toggles the IA override but silently no-ops enabled=true while archiving is off. Both writes echo authoritative post-change state (success + isArchivingEnabled/iaOverrideEnabled), so the outcome is in-band — no blind write. DETECTION RULE: success=true does NOT prove the IA-override flip landed — set-archive-override-at-ia-pref returns success=true even on the silent-no-op branch, so check the echoed iaOverrideEnabled (not success); if it is still false after sending enabled=true, archiving is off (enable archiving first, then retry). Optionally re-read get-initial-load-config as a confirmation-of-commitment. NOTE: when isTrustedServiceArchiveAddOnEnabled is false the writes still execute but have no storage backend (no real archiving effect).

## Critical Constraints

**Preconditions:**

- Caller must satisfy View Email Archive access — the @ServiceComponentAccessGuard on the email archiving setup operation; gates all three steps. (check: `View Email Archive access`)
- Org should have the TrustedServiceArchiveAddon Salesforce Archive add-on permission. When off, get-initial-load-config still succeeds and returns isTrustedServiceArchiveAddOnEnabled=false but the page renders a banner and the two write steps become non-interactive in the UI; programmatic writes still execute, but archiving has no underlying storage backend. (check: `OrgPermissions.TrustedServiceArchiveAddon`)
- The EnableEmailArchiving feature gater must be on for the org. Off-gater orgs do not surface the setup page (compound expression in EngagementMessaging.accessChecks.xml line 179). (check: `Gater.EnableEmailArchiving`)

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `get-initial-load-config` | read | implemented | `GET /headless/invoke/platform/e360-email-archiving` | — |
| `update-email-archiving-enabled-pref` | write | proposed | `PATCH /headless/invoke/platform/e360-email-archiving/update-email-archiving-enabled-pref` | — |
| `set-archive-override-at-ia-pref` | write | proposed | `PATCH /headless/invoke/platform/e360-email-archiving/set-archive-override-at-iapref` | — |

### Read operations

#### `get-initial-load-config`

Read archiving state. Returns success, isArchivingEnabled, iaOverrideEnabled, isTrustedServiceArchiveAddOnEnabled (license flag; when false the UI is read-only but programmatic writes still execute without storage backend).

**Call:** `GET /headless/invoke/platform/e360-email-archiving`   — status: `implemented`

**Output:** Object with success (boolean), isArchivingEnabled (boolean — current EmailArchivingEnabled pref), iaOverrideEnabled (boolean — current EmailArchiveOverrideAtIA pref), isTrustedServiceArchiveAddOnEnabled (boolean — TrustedServiceArchiveAddon org permission flag; when false the page is read-only).

### Write operations

#### `update-email-archiving-enabled-pref`

Toggle EmailArchivingEnabled. Side effect — enabled=false also force-disables EmailArchiveOverrideAtIA. Returns success plus post-change isArchivingEnabled and iaOverrideEnabled.

**Call:** `PATCH /headless/invoke/platform/e360-email-archiving/update-email-archiving-enabled-pref`   — status: `proposed`

**Inputs:**

- `enabled` *(`boolean`)* — Whether d is enabled.

**Output:** Object with success (boolean), isArchivingEnabled (boolean — post-change EmailArchivingEnabled), iaOverrideEnabled (boolean — post-change EmailArchiveOverrideAtIA, force-disabled when enabled=false was sent).

#### `set-archive-override-at-ia-pref`

Toggle EmailArchiveOverrideAtIA. Server silent-no-ops enabled=true when archiving is off — returns success plus iaOverrideEnabled=false rather than flipping. Disabling (enabled=false) is always honored.

**Call:** `PATCH /headless/invoke/platform/e360-email-archiving/set-archive-override-at-iapref`   — status: `proposed`

**Inputs:**

- `enabled` *(`boolean`)* — Whether d is enabled.

**Output:** Object with success (boolean) and iaOverrideEnabled (boolean — post-change EmailArchiveOverrideAtIA, forced false when archiving was off). The success flag is true even on the silent-no-op branch (enabled=true while archiving off) — caller must check iaOverrideEnabled to detect rejection.
