---
name: industries-fsc-insurance-settings-configure
description: "Use this skill when users want to toggle FSC Insurance org preferences (17-key allowlist: FSCINSURANCE_CPQ, FSCINSURANCE_M2MRSHIPS, FSCINSURANCE_MPROD1POL, FSCINSURANCE_REPORT, FSCINSURANCE_CALCULATEPARENTPOLICYONLY, VLOCITY_POLICY_ADMINISTRATION_PREF, VLOCITY_CLAIM_MGMT_PREF, INSURANCE_SERVICE_EXCELLENCE, INSURA. Trigger when users mention fsc, insurance, settings, fsc insurance settings."
metadata:
  version: "1.0"
  accessCheck: "OldAccessCheck.USER_HAS_CUSTOMIZE_APPLICATION_OR_SYS_ADMIN"
---

# Querying Fsc Insurance Settings

## When to Use This Skill

Toggle FSC Insurance org preferences (17-key allowlist: FSCINSURANCE_CPQ, FSCINSURANCE_M2MRSHIPS, FSCINSURANCE_MPROD1POL, FSCINSURANCE_REPORT, FSCINSURANCE_CALCULATEPARENTPOLICYONLY, VLOCITY_POLICY_ADMINISTRATION_PREF, VLOCITY_CLAIM_MGMT_PREF, INSURANCE_SERVICE_EXCELLENCE, INSURANCE_EINSTEIN_PREF, DIGITALINSURANCE_POLICYRNWL, INSURANCE_COEXISTENCE, INSURANCE_TRANSACTION_DETAIL, INSURANCE_BILLING, ENFORCE_INSURANCE_UNIQUE_PRODUCT_CODE, INSURANCE_ENFORCE_UNIQUE_MEMBERS_AND_ASSETS, INSURANCE_DESIGN_ADVISOR, DIGITAL_INSURANCE_REVENUE_COEXISTENCE) and read the admin's access-check map (~22 keys: feature-license booleans + org-preference states + APIEnabled). Workflow: read getAccessCheckValues first to discover which prefs are toggleable in this org, then handlePrefEnable per change. Several prefs gate-check additional license/perm/state when value=true (Service Excellence, Einstein, Report, Vlocity Policy/Claim, Billing, Enforce Unique Members/Assets) and throw NoAccessException on failure. Requires Setup Admin plus at least one of FSC Insurance, FSC Insurance Claim Mgmt, or FSC Insurance Policy Admin license. Billing-context mapping is delegated to the billingContextSettings child component (separate controller, separate SOR) and is OUT OF SCOPE here.

## Workflow

Order: call getAccessCheckValues first — it returns an org-specific boolean map (org-conditional keys) showing which features/prefs are available; use it to decide which toggles are valid in this org before writing. Then call handlePrefEnable once per change. pref must be one of the 17-key allowlist (FSCINSURANCE_CPQ, FSCINSURANCE_M2MRSHIPS, FSCINSURANCE_MPROD1POL, FSCINSURANCE_REPORT, FSCINSURANCE_CALCULATEPARENTPOLICYONLY, VLOCITY_POLICY_ADMINISTRATION_PREF, VLOCITY_CLAIM_MGMT_PREF, INSURANCE_SERVICE_EXCELLENCE, INSURANCE_EINSTEIN_PREF, DIGITALINSURANCE_POLICYRNWL, INSURANCE_COEXISTENCE, INSURANCE_TRANSACTION_DETAIL, INSURANCE_BILLING, ENFORCE_INSURANCE_UNIQUE_PRODUCT_CODE, INSURANCE_ENFORCE_UNIQUE_MEMBERS_AND_ASSETS, INSURANCE_DESIGN_ADVISOR, DIGITAL_INSURANCE_REVENUE_COEXISTENCE) — any other value raises IllegalStateException; value is the boolean target state. Enabling several prefs (value=true) triggers cross-pref/license gates that throw NoAccessException on failure: INSURANCE_BILLING needs INSURANCE_TRANSACTION_DETAIL on; INSURANCE_EINSTEIN_PREF needs APIEnabled + EGPTINSURANCE_REC_SUMMARY + Einstein GPT; FSCINSURANCE_REPORT needs APIEnabled + INSURANCE_MPROD2POL; the VLOCITY_* prefs each need APIEnabled + the matching license; INSURANCE_SERVICE_EXCELLENCE needs Customize Application + Identity Verification + Person Accounts; INSURANCE_ENFORCE_UNIQUE_MEMBERS_AND_ASSETS needs INSURANCE_M2MRSHIPS. Disabling INSURANCE_TRANSACTION_DETAIL is rejected when the org holds that license. Requires Setup Admin + at least one FSC Insurance license. Billing-context mapping (the billingContextSettings child component) is a separate controller/skill and is OUT OF SCOPE here. Verified live against a live org: getAccessCheckValues returned the access map (HTTP 200).

## Critical Constraints

**Preconditions:**

- Caller must be Setup Admin (Customize Application or System Administrator). (check: `OldAccessCheck.USER_HAS_CUSTOMIZE_APPLICATION_OR_SYS_ADMIN`)
- Org must hold at least one FSC Insurance feature license: IndustriesInsurance, FSC Insurance Claim Mgmt, or FSC Insurance Policy Admin. (check: `IndustriesInsuranceAccessCheck.ORG_HAS_INSURANCE OR IndustriesPolicyadminAccessCheck.ORG_HAS_FSCINSURANCE_CLAIM_MGMT OR IndustriesPolicyadminAccessCheck.ORG_HAS_FSCINSURANCE_POLICY_ADMIN`)

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `getAccessCheckValues_2` | read | implemented | `GET /headless/invoke/industries/industries-insurance/insurance-settings-page/get-access-check-values` | — |
| `handlePrefEnable_1` | read | implemented | `PATCH /headless/invoke/industries/industries-insurance/insurance-settings-page/handle-pref-enable` | `getAccessCheckValues_2` |

### Read operations

#### `getAccessCheckValues_2`

Returns Map<String,Boolean> aggregating ~22 access-check keys: FSC Insurance feature-license booleans (FSCInsuranceCoverageMaster, FSCInsuranceM2MRships, FSCInsuranceMultiProd1Policy, FSCInsuranceReport, etc.), org-preference states (InsuranceDesignAdvisor, EnforceInsuranceUniqueProductCode, etc.), and APIEnabled. Three keys are conditional on the caller's licenses (VlocityPolicyAdministrationPref, VlocityPolicyClaimMgmtPref, EGPTInsuranceCmpntPref). Used on page load to gate which preference toggles to surface. Throws NoAccessException unless the caller is Setup Admin AND the org has at least one of ORG_HAS_INSURANCE / ORG_HAS_FSCINSURANCE_CLAIM_MGMT / ORG_HAS_FSCINSURANCE_POLICY_ADMIN.

**Call:** `GET /headless/invoke/industries/industries-insurance/insurance-settings-page/get-access-check-values`   — status: `implemented`

**Output:** Map<string,boolean> with these keys (controller body lines 226-272). Unconditional (20): FSCInsuranceCoverageMaster, FSCInsuranceM2MRships, FSCInsuranceMultiProd1Policy, FSCInsuranceReport, FSCInsuranceCalculateParentPolicyOnly, DigitalInsurancePolicyRnwl, InsuranceCoexistence, InsuranceTransactionDetail, InsuranceTransactionDetailAccessible, InsuranceBilling, InsuranceBillingAccessible, EnforceInsuranceUniqueProductCode, InsuranceEnforceUniqueMembersAndAssets, InsuranceDesignAdvisor, DigitalInsuranceRevenueCoexistence, DigitalInsuranceOnly, FSCInsuranceServiceConsole, APIEnabled, VlocityPolicyAdmin, VlocityClaimMgmt. Conditional: VlocityPolicyAdministrationPref (when org has FSC Insurance Policy Admin), VlocityPolicyClaimMgmtPref (when org has FSC Insurance Claim Mgmt), EGPTInsuranceCmpntPref (when EGPTINSURANCE_REC_SUMMARY perm + Einstein GPT enabled).

#### `handlePrefEnable_1`

Writes one named org preference via permAndPrefUtil.setOrgPref(_getPref(pref), value). Allowed pref keys (allowlist; unknown values throw IllegalStateException): FSCINSURANCE_CPQ, FSCINSURANCE_M2MRSHIPS, FSCINSURANCE_MPROD1POL, FSCINSURANCE_REPORT, FSCINSURANCE_CALCULATEPARENTPOLICYONLY, VLOCITY_POLICY_ADMINISTRATION_PREF, VLOCITY_CLAIM_MGMT_PREF, INSURANCE_SERVICE_EXCELLENCE, INSURANCE_EINSTEIN_PREF, DIGITALINSURANCE_POLICYRNWL, INSURANCE_COEXISTENCE, INSURANCE_TRANSACTION_DETAIL, INSURANCE_BILLING, ENFORCE_INSURANCE_UNIQUE_PRODUCT_CODE, INSURANCE_ENFORCE_UNIQUE_MEMBERS_AND_ASSETS, INSURANCE_DESIGN_ADVISOR, DIGITAL_INSURANCE_REVENUE_COEXISTENCE. Cross-pref gates fire when value=true and throw NoAccessException on failure: INSURANCE_BILLING requires INSURANCE_TRANSACTION_DETAIL pref ON; INSURANCE_EINSTEIN_PREF requires APIEnabled + EGPTINSURANCE_REC_SUMMARY + Einstein GPT; FSCINSURANCE_REPORT requires APIEnabled + INSURANCE_MPROD2POL license; VLOCITY_POLICY_ADMINISTRATION_PREF and VLOCITY_CLAIM_MGMT_PREF each require APIEnabled + matching license; INSURANCE_SERVICE_EXCELLENCE requires Customize Application + Identity Verification + Person Accounts; INSURANCE_ENFORCE_UNIQUE_MEMBERS_AND_ASSETS requires INSURANCE_M2MRSHIPS license. Disabling INSURANCE_TRANSACTION_DETAIL (value=false) is rejected when ORG_HAS_INSURANCE_TRANSACTION_DETAIL license is on. Returns void; controller throws ServiceException on setOrgPref failure carrying the first error message.

**Call:** `PATCH /headless/invoke/industries/industries-insurance/insurance-settings-page/handle-pref-enable`   — status: `implemented`

**Inputs:**

- `pref` *(`String`)*
- `value` *(`boolean`)*

**Depends on:** `getAccessCheckValues_2`
