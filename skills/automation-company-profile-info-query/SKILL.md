---
name: automation-company-profile-info-query
description: "Use this skill when users want to read the org's company profile — name, address, primary contact, default locale, language, time zone, fiscal year start, and org type — by querying the Organization singleton sObject (read_company_profile step). Trigger when users mention company, profile, info, company profile info."
metadata:
  version: "1.0"
---

# Querying Company Profile Info

## When to Use This Skill

Read the org's company profile — name, address, primary contact, default locale, language, time zone, fiscal year start, and org type — by querying the Organization singleton sObject (read_company_profile step). An agent can report these settings without the admin opening the Setup page, provided the user has the "View Setup and Configuration" (ViewSetup) permission. To CHANGE any company-profile value, navigate to the Setup page via view_url and edit in the UI; write automation is intentionally out of scope for this skill.

## Critical Constraints

**Preconditions:**

- Reading the company profile requires the "View Setup and Configuration" (ViewSetup) user permission. Without it the running user cannot access Setup and the company-profile context is not meaningfully retrievable.
 (check: `USER_HAS_VIEW_SETUP`)

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `view_CompanyProfileInfo_1` | read | — | `CompanyProfileInfo.view` | — |
| `read_company_profile` | read | — | `GET /services/data/v66.0/query` | — |

### Read operations

#### `view_CompanyProfileInfo_1`

Navigate to the CompanyProfileInfo Setup page (no programmatic API). The agent should open view_url for the user to configure manually.

**Call:** `CompanyProfileInfo.view`

#### `read_company_profile`

Read the org's company profile — name, address, primary contact, default locale, language, time zone, fiscal year start, and org type — by querying the `Organization` singleton sObject via SOQL. The org has exactly one Organization record, so the query returns a single row. This lets an agent report company-profile settings WITHOUT the admin opening the Setup page. The `FROM Organization` clause is fixed by this step — only the SELECT field list is variable — so the read is always scoped to the Organization entity. Read-only: to CHANGE any of these values, navigate to the Setup page (view_CompanyProfileInfo_1) and edit in the UI — write automation for the company profile is intentionally out of scope for this skill.


**Call:** `GET /services/data/v66.0/query`

**Inputs:**

- `fields` *(`String`)* — Comma-separated SELECT field list for the Organization query. The `FROM Organization` clause is fixed by the step and is NOT part of this input — you choose the fields, never the object. Omit to use the default full company-profile field set below. Add or drop fields as the admin's question requires; note single-currency orgs do not expose DefaultCurrencyIsoCode (querying it errors on such orgs).

- `q` *(`string`)*
