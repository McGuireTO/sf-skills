---
name: experience-lex-engagement-configure
description: "Use this skill when users want to manage the Lightning Experience (LEX) Engagement tracking toggle. Trigger when users mention lex, engagement, lex engagement."
metadata:
  version: "1.0"
---

# Managing Lex Engagement

## When to Use This Skill

Manage the Lightning Experience (LEX) Engagement tracking toggle. This setup page allows an administrator to view the current engagement-tracking status and enable or disable it via a toggle switch. The page reads the initial on/off state from the server and writes status changes back. An agent would use this SOR to check whether LEX engagement tracking is active or to flip it on or off for a given source context.

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `getInitialStatus_1` | read | implemented | `GET /headless/invoke/platform/instrumentation/lex-engagement/get-initial-status` | — |
| `handleStatusChange_2` | write | implemented | `PATCH /headless/invoke/platform/instrumentation/lex-engagement/handle-status-change` | `getInitialStatus_1` |

### Read operations

#### `getInitialStatus_1`

Fetch the current engagement-tracking toggle state for the specified source. The returned value drives whether the toggle renders as checked or unchecked on page load (doInit).

**Call:** `GET /headless/invoke/platform/instrumentation/lex-engagement/get-initial-status`   — status: `implemented`

**Inputs:**

- `source` *(`String`)*

### Write operations

#### `handleStatusChange_2`

Persist the new engagement-tracking state when the admin flips the toggle. Sends the source identifier and the new boolean value (isToggled) to the server. Source: output of getInitialStatus_1 provides the context for which source is being toggled.

**Call:** `PATCH /headless/invoke/platform/instrumentation/lex-engagement/handle-status-change`   — status: `implemented`

**Inputs:**

- `source` *(`String`)*
- `isToggled` *(`boolean`)*

**Depends on:** `getInitialStatus_1`
