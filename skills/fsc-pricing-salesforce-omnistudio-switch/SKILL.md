---
name: fsc-pricing-salesforce-omnistudio-switch
parent: "digital-origination-pricing-setup"
purpose: "Repoint versioned Digital Lending OmniStudio components to Salesforce Pricing."
description: "Switch Digital Lending OmniStudio components from the default Product Configurator path to the explicit Salesforce Pricing path. Creates new versions of DigitalLendingApplicantIntake and DigitalLendingApplicantIntakeSecured, replaces DigitalLendingOfferConfigurator with DigitalLendingViewOffer, and creates new DigitalLendingConfirmOffer and DigitalLendingConfirmOfferAAE card versions that replace DigitalLending_PricingEngineOfferConfiguratorFinalOffer with DigitalLending_PricingEngineFinalOffer. Reuses approved OmniStudio Phoenix and LiveCards operations, preserves existing active versions, and verifies every component tree or builder JSON before activation."
metadata:
  version: "1.0"
---

# Switch Digital Origination OmniStudio components to Salesforce Pricing

Use this sibling only when the admin explicitly selects **Salesforce Pricing**. Product Configurator
is the Digital Lending default and requires no component repointing.

## Preconditions

- Target-org alias confirmed
- Digital Lending sample/application components installed
- OmniStudio Admin and Salesforce Pricing access verified
- Source and target component names below resolve uniquely
- Current active versions captured for rollback

If any component is missing, do not create a look-alike component. Report the missing package artifact.

## Required changes

| Component | Type | Remove | Add |
|---|---|---|---|
| `DigitalLendingApplicantIntake` | OmniScript | `DigitalLendingOfferConfigurator` | `DigitalLendingViewOffer` |
| `DigitalLendingApplicantIntakeSecured` | OmniScript | `DigitalLendingOfferConfigurator` | `DigitalLendingViewOffer` |
| `DigitalLendingConfirmOffer` | FlexCard/LiveCard | `DigitalLending_PricingEngineOfferConfiguratorFinalOffer` | `DigitalLending_PricingEngineFinalOffer` |
| `DigitalLendingConfirmOfferAAE` | FlexCard/LiveCard | `DigitalLending_PricingEngineOfferConfiguratorFinalOffer` | `DigitalLending_PricingEngineFinalOffer` |

Never edit the current active version in place.

## OmniScript operations

Use approved SOR
`connect-api/omni-studio-phoenix/omnistudio-connect-api__sfdc.omnistudio.connect.api_oas_67.0`:

- `get-fetch-omni-process-list` (`getFetchOmniProcessList`) - find process/version IDs
- `get-fetch-omni-process-data` (`getFetchOmniProcessData`) - read full process tree
- `post-clone-omni-process` (`postCloneOmniProcess`) - clone OmniScript/Integration Procedure
- `post-omniscript-delete-element` (`postOmniscriptDeleteElement`) - delete by element name and
  OmniScript ID
- `post-omniscript-insert-element` (`postOmniscriptInsertElement`) - insert element with
  parent/order/type/designer name
- `post-omniscript-build-json`, `save-bp` (`saveBP`), `lwc-prep` (`lwcPrep`) - build, persist, and
  compile as supported
- `post-upsert-omni-process` (`postUpsertOmniProcess`) - persist and explicitly set `isActive` after
  the cloned version has been verified

### Workflow for each intake OmniScript

1. Find all versions and identify the active source version.
2. Read the complete element tree. Locate `DigitalLendingOfferConfigurator` and capture parent ID,
   order, type, properties, and neighboring elements.
3. Verify `DigitalLendingViewOffer` exists and determine the correct insert contract.
4. Clone the source process. Confirm the clone is a new, inactive working version.
5. Delete `DigitalLendingOfferConfigurator` from the clone only.
6. Insert `DigitalLendingViewOffer` at the captured parent and order; preserve branch/navigation data.
7. Build, save, and compile. Re-read the clone and verify exactly one target element and no removed
   element remain.
8. Activate only after the new version validates, using `post-upsert-omni-process` with the complete
   verified process definition and `isActive=true`; never send a partial upsert. Re-read `isActive`.
   Preserve the former active version for rollback.

`post-clone-omni-process` is the closest headless primitive to New Version; harness-verify version and
activation semantics in the target org. If it cannot safely create a new version, use the OmniScript
Designer New Version checkpoint.

## FlexCard/LiveCard operations

Use approved-but-draft SOR
`connect-api/omni-studio-orion/industries-livecards-connect-api`:

- `list-card-versions` (`listCardVersions`)
- `get-card-version` (`getCardVersion`)
- `create-card-version` (`createCardVersion`)
- `update-card-version` (`updateCardVersion`)
- `validate-card` (`validateCard`)
- `compare-versions` (`compareVersions`)

### Workflow for each confirmation card

1. Resolve the card and active version. Confirm it is DynamicUiCard/LiveCard-backed; do not assume all
   classic FlexCards use this API.
2. Read complete builder JSON and locate the old Integration Procedure reference.
3. Create a new version.
4. Read-modify-write only the Integration Procedure reference; preserve all unrelated JSON, data
   sources, actions, styling, and visibility rules.
5. Validate the card and re-read it. Confirm old reference count is zero and new reference count is
   exactly one at the intended location.
6. Compare old/new versions and report the minimal diff.
7. The current LiveCards input schemas expose builder JSON/version creation but no activation write,
   even though reads expose `isActive`. Always use the FlexCard UI to activate the verified new version,
   then re-run `list-card-versions` and require `isActive=true`.

If the component is not compatible with LiveCards APIs or the draft SOR fails, use the full UI
checkpoint: OmniStudio -> FlexCards -> card -> New Version -> Edit -> remove old IP -> add
`DigitalLending_PricingEngineFinalOffer` -> validate/save. Whether created through API or UI, activation
is a required UI checkpoint until a typed activation input is available. Resume with a read-back.

## Idempotency and rollback

- If an inactive version already contains the exact desired change, validate and reuse it.
- Never create repeated new versions on every rerun.
- OmniScript rollback uses the complete prior definition with `post-upsert-omni-process` and
  `isActive=true` after verification. FlexCard rollback uses the UI to reactivate the captured previous
  version, followed by `list-card-versions` read-back.
- Do not modify source IPs or target OmniScripts; only update references in cloned consumers.

## Output contract

For each component, report component ID, old active version, new version, validation state, activation
state, removed reference, new reference, and rollback version. Pass this evidence to
nested `pricing-procedure` for the Salesforce Pricing branch.

## Definition of done

All four newly versioned components are valid and active with only the intended reference changes,
and the prior active versions remain available for rollback. Any UI checkpoint not yet verified means
partial completion.
