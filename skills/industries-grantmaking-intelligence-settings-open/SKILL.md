---
name: industries-grantmaking-intelligence-settings-open
description: "Use this skill when users want to setup landing page for Grantmaking Intelligence — an Aura wrapper (setup_industries_npc:grantmakingDataCloudSetupWrapper) that composes two child components with no controller of its own, and no first-party API on this node today. Trigger when users mention grantmaking, intelligence, settings, grantmaking intelligence settings."
metadata:
  version: "1.0"
---

# Querying Grantmaking Intelligence Settings

## When to Use This Skill

Setup landing page for Grantmaking Intelligence — an Aura wrapper
(setup_industries_npc:grantmakingDataCloudSetupWrapper) that composes two
child components with no controller of its own, and no first-party API
on this node today. Agent-driven configuration is not available from
this skill.

What renders here:
  (1) an Intelligent App Hub panel (wave:intelligentAppHub) that
      lists CRM Analytics apps and lets an admin pin/schedule them;
      its backing controller lives with the insights/wave team, not
      NPC Cartwheel.
  (2) an Admin Setup Assistant container
      (industries_common:adminSetupAssistantContainer) — the same
      generic wizard shell used by CaseMgmtIntelligenceSettings.
      That shell is generic; it reads a per-page setup-config JSON
      registration owned by the industries-common team. No such
      registration currently exists for GrantmakingIntelligenceSettings
      (tried both the node-id and DataCloud-variant file names),
      so the container renders empty on this page today.

When an admin asks to configure Grantmaking Intelligence, the
productive action from a chat/agent context is to navigate them to
/lightning/setup/GrantmakingIntelligenceSettings/home and let them
interact with the embedded UI (schedule an app in the Intelligent App
Hub, or wait for the Admin Setup Assistant registration to arrive).
Do not fabricate step calls — no wire endpoint on this node returns
success today.

Access: six gates enforced at the setup-tree level — see preconditions.

## Critical Constraints

**Preconditions:**

- Caller must be an org admin — the setup-manifest access clause
requires an admin user. (check: `Org Admin`)
- Org must have Budget object access provisioned — setup-manifest
requires Budget.orgHasBudgetAccess. (check: `Budget org access`)
- Caller must have user-level Budget access — setup-manifest
requires Budget.userHasBudgetUserAccess. (check: `Budget user access`)
- Org must have Funding Award access provisioned — setup-manifest
requires IndustriesFundingAward.orgHasFundingAwardAccess. (check: `Funding Award access`)
- Org must have Data Cloud (CDP) or Genie enabled — setup-manifest
requires Data Cloud or Genie enabled. (check: `CDP or Genie enabled`)
- The Nonprofit Data Cloud setup feature gate must be enabled on
the org. Orgs without the gate rolled out do not see this setup
page. (check: `Nonprofit Data Cloud setup feature gate`)
