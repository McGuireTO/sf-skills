# Changelog

All notable changes to this plugin are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this plugin adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] — 2026-10-16

### Added

- `salesforce-test-drive` now supports Codex, and so does every plugin it can require. On Codex, a
  drive can recommend and install any Salesforce marketplace plugin, then resume in a new session.
  Claude Code behavior is unchanged.

## [0.1.1] — 2026-10-02

### Changed

- The test-drive engine now installs `agentforce-adlc` from the Salesforce marketplace with the
  same one-step confirmation as any other Salesforce plugin. The external-source confirmation
  step only applies to plugins hosted outside this marketplace.
- The plugin now declares its dependency on `salesforce-development`, whose skills the test drives
  use for the build.

## [0.1.0] — 2026-09-02

### Added

- Initial release. Pick a curated end-to-end build from a menu with `/salesforce-test-drive:start`
  and watch it run start to finish against your own org.
- The first drive, **Service help agent**, builds an Agentforce service agent that answers
  customer questions, manages support cases, and hands off to a human, then deploys it as a
  website chat widget.
- The engine checks your toolchain and setup, helps you connect or provision an org (including a
  free Agentforce Developer Edition), installs any plugin a drive needs, and only pauses for the
  choices that matter. Drives use the skills from `salesforce-development`, which this plugin
  depends on.
- If you start a drive and come back later, the plugin offers to resume where you left off instead
  of starting over.
