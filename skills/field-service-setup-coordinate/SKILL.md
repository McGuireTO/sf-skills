---
name: field-service-setup-coordinate
description: "Use this skill to set up Salesforce Field Service — Work Types, Skills, Service Territories, Operating Hours, Scheduling Policy, Work Rules, Service Objectives, Data Capture Forms, FSL mobile forms, Pre-Work Brief, Mobile Branding, or any FSL setup, enablement, or configuration request. Entry point that identifies what the user wants to configure and routes to the right sub-workflow: Foundation Setup, Scheduling Policy, Data Capture Forms, Pre-Work Brief, or Mobile Branding."
metadata:
  version: "1.0"
---

## How It Works

This skill is the entry point for all Field Service setup. It identifies what the user wants to configure and routes to the correct sub-skill. It does not perform setup work itself.

## Phase 1 — Identify and Confirm

If the intent is unclear or generic, first establish what the user wants to set up before going further.

Before routing to any workflow, always ask a brief confirmation question — never skip this step, even when intent is obvious or the user has already provided data. Adapt the question naturally to context:

- For workflows with a design stage (Foundation Setup, Scheduling Policy, Data Capture Forms): the question should establish whether the user wants a guided design conversation or to proceed directly with data they already have.
- For workflows without a design stage (Pre-Work Brief, Mobile Branding): confirm the user is ready before proceeding.

One short question. Wait for the answer before delegating.

## Phase 2 — Route

Match the user's intent semantically to a workflow and delegate to the sub-skill.

| Workflow | Sub-skill | Note |
|---|---|---|
| **Foundation Setup** *(default)* | `sfs-setup-experience/sfs-foundation-setup-designer` → deploys via `sfs-sobject-create` | Always first; covers Work Types, Skills, Service Territories, Operating Hours |
| Scheduling Policy | `sfs-setup-experience/sfs-scheduling-policy-designer` → deploys via `sfs-sobject-create` | Ask if Foundation is done; if not, offer it first |
| Data Capture Forms | `sfs-mobile-core-experience/fs-data-capture-form-designer` → `fs-data-capture-form-deployer` | Ask if Foundation is done; if not, offer it first |
| Pre-Work Brief | `sfs-frontline-ai/fs-prework-brief-deployer` | Ask if Foundation is done; if not, offer it first |
| Mobile Branding | `sfs-mobile-core-experience/fs-mobile-branding` | Ask if Foundation is done; if not, offer it first |

## Conversational Tone

- Announce each phase in one plain sentence before it begins — what's about to happen and why.
- Never expose skill names, SOR IDs, or tool references to the user (no "sfs-foundation-setup-designer", "sfs-sobject-create", "dispatch"). Use plain labels: "Foundation Setup", "design interview", "creating your records".

## Key Principles

- This skill routes — it never does setup work itself.
- One workflow at a time; wait for explicit confirmation before the next.
- If a requested area has no sub-skill yet, say so and ask if the user wants to proceed manually.
- Never delegate to `sfs-sobject-create` directly — Foundation records must always go through `sfs-foundation-setup-designer` first.

<!-- skill-validate: ignore-start -->
<!-- codey:operations start -->
## Operations Reference

Operations this skill uses — routing and dependency reference.

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `delegate-foundation-setup-designer` | delegate | — | → `sfs-setup-experience/sfs-foundation-setup-designer` | — |
| `delegate-scheduling-policy-designer` | delegate | — | → `sfs-setup-experience/sfs-scheduling-policy-designer` | — |
| `delegate-data-capture-form-designer` | delegate | — | → `sfs-mobile-core-experience/fs-data-capture-form-designer` | — |
| `delegate-data-capture-form-deployer` | delegate | — | → `sfs-mobile-core-experience/fs-data-capture-form-deployer` | — |
| `delegate-prework-brief-deployer` | delegate | — | → `sfs-frontline-ai/fs-prework-brief-deployer` | — |
| `delegate-mobile-branding` | delegate | — | → `sfs-mobile-core-experience/fs-mobile-branding` | — |
<!-- codey:operations end -->
<!-- skill-validate: ignore-end -->
