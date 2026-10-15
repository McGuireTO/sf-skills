---
name: experience-notifications-configure
description: "Use this skill when users want to use this skill to enable or disable in-app notifications and push notifications for the entire org in Lightning Experience and Salesforce mobile app. Trigger when users mention notifications, settings, notifications settings."
metadata:
  version: "1.0"
  cliTools:
  - tool:
    - "sf"
    semver: ">=2.0.0"
---

# Managing Notifications Settings

## When to Use This Skill

Use this skill to enable or disable in-app notifications and push notifications for the entire org in Lightning Experience and Salesforce mobile app. Two settings available: (1) Enable in-app notifications checkbox, (2) Enable push notifications checkbox. Both are org-level settings that apply to all users.

## Workflow

The factory-synthesized Connect API operations (NotificationsSettings.getConfiguration / NotificationsSettings.updateConfiguration) do not exist. This page uses Metadata API for both reads and writes.

Programmatic access via Metadata API:

Field names verified via live org testing: enableNotifications (in-app notifications), enableMobileAppPushNotifications (push notifications).

## Critical Constraints

**Operational rules:**

- READ: Retrieve the NotificationsSettings metadata type:
- sf project retrieve start --metadata NotificationsSettings
- Returns NotificationsSettings.settings-meta.xml with <enableNotifications> and <enableMobileAppPushNotifications>
- WRITE: Deploy the NotificationsSettings metadata type:
- Create a NotificationsSettings.settings-meta.xml file:
  <NotificationsSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <enableNotifications>true|false</enableNotifications>
    <enableMobileAppPushNotifications>true|false</enableMobileAppPushNotifications>
  </NotificationsSettings>
- Deploy via: sf project deploy start --source-dir <dir> (requires SFDX project structure)

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `get_NotificationsSettings_config_1` | read | — | `sf project retrieve start` | — |
| `update_NotificationsSettings_config_1` | write | — | `sf project deploy start` | — |

### Read operations

#### `get_NotificationsSettings_config_1`

Read current org-level notification settings (in-app enabled, push enabled). Retrieve NotificationsSettings metadata type to get enableNotifications and enableMobileAppPushNotifications values.

**Call:** `sf project retrieve start`

### Write operations

#### `update_NotificationsSettings_config_1`

Update org-level notification settings (enable or disable in-app notifications and/or push notifications). Deploy NotificationsSettings metadata type with enableNotifications and/or enableMobileAppPushNotifications.

**Call:** `sf project deploy start`

**Inputs:**

- `enableNotifications` — In-app notifications toggle (Lightning Experience + mobile app). Boolean field in NotificationsSettings metadata. Set to true to enable, false to disable.
  - schema: `{'type': 'boolean'}`
- `enableMobileAppPushNotifications` — Mobile push notifications toggle. Boolean field in NotificationsSettings metadata. Set to true to enable, false to disable.
  - schema: `{'type': 'boolean'}`

**Output:** Metadata deploy result. Success confirms the notification toggles were applied org-wide. Changes take effect immediately.
