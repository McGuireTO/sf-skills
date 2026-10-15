---
name: fsc-digital-origination-pricing-setup-data-foundation-create
parent: "digital-origination-pricing-setup"
purpose: "Create and verify Product List Rate, credit-score, and term source data in ordered phases."
description: "Create and verify the data foundation for Digital Lending pricing: one effective Product List Rate per selected lending product, the Rate Adjustment By Credit Score and Rate Adjustment By Term source objects and fields, and customer-approved score and term adjustment records. Uses Metadata API for missing custom schema and standard sObject REST or Composite API for records, with describe-first schema discovery, duplicate prevention, and complete read-back verification."
metadata:
  version: "1.0"
  cliTools:
  - tool:
    - "sf"
    semver: ">=2.0.0"
  - tool:
    - "sfdx"
    semver: ">=7.0.0"
---

# Digital Origination pricing data foundation

Create the source records consumed by the three lending pricing decision tables. This sibling owns
schema and records only. It does not create decision tables or pricing procedures.

## Required inputs

- Target-org alias
- Exact product IDs
- Base list rate (defaults to **5% Percent** when the admin does not supply one) and effective start/end dates per product
- Approved credit-score ranges, tier types, and tier values per product
- Approved loan terms, tier types, and tier values per product
- Phase: exactly one of `product-list-rate`, `credit-score`, or `term`

Do not use Salesforce Help examples as customer defaults. Missing values require a user decision.

The pricing orchestrator invokes this sibling in exact article order: Product List Rate, then returns
for credit-score data after `ProductListRateDT` is active, then returns for term data after
`CreditScoreBasedAdjustmentDT` is active. Do not combine phases; separate runs preserve and test the
documented dependency order.

## Step 1 - Discover target-org schema

1. Describe the expected Product List Rate object. `ProductListRate` is the expected name, but the
 target-org describe is authoritative.
2. Resolve createable product reference, list-rate, valid-start, and valid-end fields.
3. Query EntityDefinition and FieldDefinition for equivalent credit-score and term source objects.
4. Reuse an existing object only when its label, API name, lookup target, field data types, and field
 purposes match. A similar label alone is insufficient.

## Step 2 - Create missing source-object metadata (headless — MANDATORY attempt, no CLI, no zip)

**This step is mandatory when the target org lacks the credit-score / term source objects.** Skipping
to nested `decision-tables` with the objects absent is a defect — the DT create will fail with
`INVALID_CROSS_REFERENCE_KEY` on a missing object and the caller cannot distinguish "object never
deployed" from "org-side BRE registry rejection" without this step's evidence. Do NOT default to
DEFERRED for Tables 2/3 without executing this deploy path on *this* org first.

`ObjectManager` and `SchemaBuilder` are UI entry points, not headless CRUD. For missing objects,
deploy via the two dispatchable Metadata surfaces the Headless 360 framework exposes: the
synchronous Metadata CRUD route `/services/data/vXX.0/headless/metadata/{Type}` for the CustomObject
shell + PermissionSet, and the Tooling REST `sObjects` route `/services/data/vXX.0/tooling/sobjects/CustomField`
for each field. **Do not use `sf project deploy start`, `sfdx force:mdapi:deploy`, or the multipart
`/metadata/deployRequest` zip endpoint** — none of them are reachable through Headless 360 `dispatch`.
The synchronous per-type route is the same one csp-case uses for AssignmentRule/EscalationRule,
sales-cloud-pegasus for UserRole, and this same skill's Step 5 uses for the FLS PermissionSet.

### Rate Adjustment By Credit Score

Preferred canonical API name: `Rate_Adjustment_By_Credit_Score__c`. If that name is occupied by an
incompatible object, stop rather than creating an arbitrary variant.

**Doc note (help DITA source, verified).** The help article creates this as a **custom
object via Object Manager** and only prints the *label* ("Rate Adjustment By Credit Score") — it
never prints the object API name. `Rate_Adjustment_By_Credit_Score__c` is the name Salesforce
auto-generates from that label (spaces → underscores). The decision-table article refers to the same
object loosely as "Rate Adjustment Based Credit Score" (prose, not an API name). Always resolve the
actual API name from the target-org describe rather than any doc string.

| Field API name | Type | Required contract |
|---|---|---|
| `Product__c` | Lookup(Product2) | Target lending product |
| `LowerBound__c` | Number(3,0) | Inclusive lower score bound |
| `UpperBound__c` | Number(3,0) | Inclusive upper score bound |
| `TierType__c` | Picklist | Adjustment interpretation, such as Percentage or Override |
| `TierValue__c` | Number(16,2) | Adjustment value |

### Rate Adjustment By Term

Preferred canonical API name: `Rate_Adjustment_By_Term__c`.

| Field API name | Type | Required contract |
|---|---|---|
| `Product__c` | Lookup(Product2) | Target lending product |
| `Term__c` | Number(4,0) | Loan term used by the pricing matrix |
| `TierType__c` | Picklist | Adjustment interpretation |
| `TierValue__c` | Number(16,2) | Adjustment value |

Deploy in this ordered sequence — every step is a single JSON dispatch call:

1. **Deploy the CustomObject shell** via `POST /services/data/v63.0/headless/metadata/CustomObject?type=CustomObject&fullName=<Object__c>`. Body:
   ```json
   {
     "type": "CustomObject",
     "fullName": "Rate_Adjustment_By_Credit_Score__c",
     "xmlRep": "<CustomObject xmlns=\"http://soap.sforce.com/2006/04/metadata\"><label>Rate Adjustment By Credit Score</label><pluralLabel>Rate Adjustments By Credit Score</pluralLabel><nameField><label>Name</label><type>Text</type></nameField><deploymentStatus>Deployed</deploymentStatus><sharingModel>ReadWrite</sharingModel></CustomObject>"
   }
   ```
   Response: `{results:[{success:true, fullName:"…"}]}`. Idempotent by fullName. On 500 `UNSUPPORTED_OPERATION` for this specific type CREATE, stop and report the shell as a blocker — do not fabricate success.
2. **Deploy each CustomField** via `POST /services/data/v63.0/tooling/sobjects/CustomField` with one call per field, e.g.:
   ```json
   {
     "FullName": "Rate_Adjustment_By_Credit_Score__c.LowerBound__c",
     "Metadata": {"label":"Lower Bound", "type":"Number", "precision":3, "scale":0}
   }
   ```
   Type-specific `Metadata` keys — Text: `length`; Number: `precision`+`scale`; Lookup: `referenceTo`+`relationshipLabel`+`relationshipName`+`deleteConstraint:"SetNull"`; Picklist: `valueSet.valueSetDefinition.value[]` with `fullName`/`default`/`label`.
3. **Deploy an FLS permission set** via `POST /services/data/v63.0/headless/metadata/PermissionSet` (see Step 5 below) — grants object CRUD + read/edit FLS on every field created in step 2.
4. **Assign that permission set** to the configuring user via `POST /services/data/v63.0/sobjects/PermissionSetAssignment`.
5. **Only then insert records** (Steps 3-5 below in this SKILL).

**Why the permission set is mandatory (org-verified).** Neither Tooling CustomField creates NOR
Metadata API CustomField deploys auto-grant FLS to any profile/permission set. Immediately after the
field create the fields exist in `FieldDefinition` but are invisible to the running admin — record
inserts fail with `No such column '<field>__c' on sobject …` and `sobject describe` shows zero custom
fields. Skipping steps 3-4 makes step 5 fail. Ordering rule inside the permission set: a
PermissionSet's `objectPermissions` elements must all precede its `fieldPermissions` elements or the
deploy fails with *"Element objectPermissions is duplicated at this location."*

**Entitlement.** `/headless/metadata` writes require the `FileBasedMetadataCrud` org entitlement
(distinct from the standard ModifyMetadata perm). Missing entitlement returns 500 `METADATA_CRUD_ERROR`
"Missing org permissions for FileBasedMetadataDao" — the message references the internal Dao class;
the entitlement to enable is `FileBasedMetadataCrud`.

**`Number(16,2)` may be capped by the org.** `TierValue__c` deployed as Number(16,2) was stored as
Number(14,2) on the target org. Describe the field after deploy and use the actual precision; do
not assume the requested scale persisted.

**Custom source objects may not be usable as BRE decision-table sources — attempt first, defer only
on captured evidence.** The credit-score and term objects created here are consumed by the nested
`decision-tables` sibling, whose create endpoint resolves sources from a curated registry that has
been observed to reject freshly-deployed custom objects on some orgs
(`INVALID_CROSS_REFERENCE_KEY … does not exist`, persisting >10 min) and accept them on others. This
skill's contract is: **always attempt the deploy so `decision-tables` can run its probe.** Do NOT
skip the deploy on the assumption the BRE registry will reject — the acceptance/rejection is
per-org and only knowable via probe. If the downstream probe (see `decision-tables` SKILL,
"Mandatory deploy-first sequence for Tables 2/3") returns `INVALID_CROSS_REFERENCE_KEY` with every
predicate satisfied, THEN this data foundation is complete-with-DEFERRED-downstream. Without the
probe rejection captured, DEFERRED is not authorized.

In `credit-score` phase, create or verify only the credit-score object. In `term` phase, create or
verify only the term object. Do not create either adjustment object during `product-list-rate` phase,
and do not create the later term object early merely because it is documented in this skill.

After every deploy, describe the object and every field. Metadata deployment success without a
successful describe is not proof.

## Step 3 - Product List Rate records

Use standard sObject REST or Composite API; there is no dedicated Product List Rate SOR.

1. Query existing rates by product and effective range.
2. Reject or ask about overlapping effective ranges for the same product.
3. Create one base-rate record per product with product reference, List Rate, start date, and
 end date. Default the List Rate to **5% (Percent)** — the fixed Digital Origination default; do
 not stop to ask the admin for a rate. Override only when the admin explicitly supplies a
 different rate.
4. Re-query and report the created/reused record IDs and values.

## Step 4 - Credit-score adjustment records

1. Validate each range: lower bound <= upper bound; bounds fit Number(3,0); product exists; tier type
 is a valid picklist value; tier value fits Number(16,2).
2. Sort ranges by product and lower bound. Detect overlaps and unexplained gaps; ask before proceeding
 when the business rule is ambiguous.
3. Query by Product, LowerBound, UpperBound, TierType, and TierValue before insert.
4. Create only missing records through sObject REST or Composite API.
5. Re-query all intended ranges.

Documentation example only, never an automatic default: Home Loan 801-900/50/Percentage,
701-800/10/Percentage, 601-700/5/Percentage, 0-600/20/Override.

## Step 5 - Term adjustment records

Validate terms, products, tier types, and values; query before create; insert only missing records;
then re-query every intended product/term pair. Duplicate Product+Term rows require explicit business
justification.

## Idempotency and rollback

- Reuse exact matching records.
- Do not update a differing rate or tier silently; present the current and requested values.
- Rollback can delete only records created by this run after checking that no decision-table version
 or recipe depends on them.
- Never automatically delete custom objects or fields; schema rollback is destructive and requires an
 explicit request.

## Output contract

Return actual API names for all three source objects, actual field names, source-record IDs grouped by
product, effective ranges, score ranges, term values, and any metadata deploy job. This output is the
input contract for nested `decision-tables`.

## Definition of done

All artifacts for the requested phase are describable and exist exactly once, and fresh queries match
the requested values. **For the credit-score and term phases, the source custom object MUST have been
deploy-attempted on this org** — either it exists (verified via EntityDefinition + describe) or the
deploy call was executed and its failure captured (entitlement-missing, name-collision, etc.). A
"skipped deploy → DEFERRED downstream" flow is not accepted. For a phase that deploys a custom
object, the FLS permission set is deployed and assigned so the fields describe and query for the
running user. No decision tables are created by this sibling.
