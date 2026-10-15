---
name: fsc-document-checklist-settings-configure
description: "Use this skill when users want to toggle four FSC org prefs allowlisted by DOCUMENT_CHECKLIST_PREF enum: deleteDCIWithFiles, dciCustomSharing, dciOptimizedSharing, dciAI. Trigger when users mention document, checklist, settings, document checklist settings."
metadata:
  version: "1.0"
---

# Managing Document Checklist Settings

## When to Use This Skill

Toggle four FSC org prefs allowlisted by DOCUMENT_CHECKLIST_PREF enum: deleteDCIWithFiles, dciCustomSharing, dciOptimizedSharing, dciAI. Read returns all four as Map<String,Boolean>; write sets one by name (unknown names silently no-op). Requires admin + View Setup. Setup UI exposes only 2 of 4 toggles; agent drives all 4 programmatically. AURA-IS-CANONICAL: Metadata API + Tooling sObject DocumentChecklistSettings carry only 2 of 4 prefs in v66+ WSDLs; substituting drops dciOptimizedSharing + dciAI writes/reads.

## Workflow

Two-step read/write of the four DOCUMENT_CHECKLIST_PREF org prefs (deleteDCIWithFiles, dciCustomSharing, dciOptimizedSharing, dciAI). getDocumentChecklistPrefs returns all four as a Map<String,Boolean>; savePref sets one by name (pref matches the enum case-insensitively) and returns void. Critical: savePref responds 200/success even when the write does NOT take — an unknown pref name is a silent no-op, and an allowlisted pref whose underlying feature is not entitled is also silently ignored. Never treat the 200 as confirmation; always re-read via getDocumentChecklistPrefs to verify the toggle actually persisted. Observed against a live org: deleteDCIWithFiles, dciCustomSharing, and dciOptimizedSharing each toggled and read back correctly, but dciAI accepted the call and stayed false — it is gated by a dependent AI entitlement that this org lacks, so in orgs without that entitlement dciAI cannot be enabled here. The Setup UI surfaces only 2 of the 4 toggles; the agent can drive the rest programmatically, subject to that per-pref entitlement gate. Requires admin + View Setup (checkAccess throws 'noAccess' otherwise) and the org must have the FSC / Document Checklist surface available.

## Critical Constraints

**Preconditions:**

- Caller must be an admin user with View Setup permission. Controller's checkAccess() throws AuraHandledException 'noAccess' otherwise. (check: `setupUtil.hasViewSetup() && administrator access`)
- Document Checklist feature must be available in the org (FSC product surface). The controller lives in ui-document-checklist-components; orgs without FSC entitlement do not surface this Setup page.

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `getDocumentChecklistPrefs_1` | read | implemented | `GET /headless/invoke/platform/document-checklist-settings` | — |
| `savePref_2` | write | implemented | `PATCH /headless/invoke/platform/document-checklist-settings/save-pref` | `getDocumentChecklistPrefs_1` |

### Read operations

#### `getDocumentChecklistPrefs_1`

Read all four DocumentChecklist prefs as Map<String,Boolean> keyed by prefName: deleteDCIWithFiles, dciCustomSharing, dciOptimizedSharing, dciAI. AURA-IS-CANONICAL — Metadata/Tooling cover only 2 of 4 fields.

**Call:** `GET /headless/invoke/platform/document-checklist-settings`   — status: `implemented`

### Write operations

#### `savePref_2`

Toggle one allowlisted pref by name. `pref` case-insensitively matches DOCUMENT_CHECKLIST_PREF; unknown silently no-ops. Returns void. AURA-IS-CANONICAL — Metadata/Tooling drop dciOptimizedSharing + dciAI writes.

**Call:** `PATCH /headless/invoke/platform/document-checklist-settings/save-pref`   — status: `implemented`

**Inputs:**

- `pref` *(`String`)*
- `enabled` *(`boolean`)*

**Depends on:** `getDocumentChecklistPrefs_1`
