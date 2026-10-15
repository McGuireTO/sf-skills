---
name: experience-record-discovery-query
description: "Read-only method for finding, listing, looking up, filtering, or identifying Salesforce records and setup entities through Headless-360. Before loading as a fallback, discover a task recipe for the requested result, even for a list or count constrained by a condition or relationship. If one fits, describe and follow it; use this skill only when none fits, or after a chosen recipe needs an entity resolved to its Id or API name. Covers Enterprise-vs-Tooling routing, SOSL-vs-SOQL selection, and proving a negative. Do not use for writes."
metadata:
  version: "1.0"
---

# Finding records and metadata (record discovery)

**Scope check.** Before loading this skill as a fallback, discover a recipe
for the requested task, including requests phrased as a list or count of
records matching a condition or relationship. If a recipe fits, describe and
follow it. Use this skill only when no recipe fits, or when a chosen recipe
needs an entity resolved as an input. Discover and describe the task recipe
before asking for a missing or masked identifier. A query or evidence list may
support the recipe, but it is not by itself an answer to the task.

When the user asks to find, list, look up, or filter records or setup entities
("show me all …", "find the … named …", "which … have …"), resolve it through
the Headless-360 tools — never from memory of Salesforce schema.

**Step 1 — Identify the entity type.** Before calling any discovery or query tool,
check whether the user supplied only a bare category term. For bare
"permissions", "licenses", "rules", "apps", or "agents" (including singular
forms), ASK which specific kind they mean; several Salesforce entities fit each
term. Do not select an API name or query one of them. A qualifier that identifies
a kind (for example, "permission set licenses", "validation rules", "connected
apps", or "Agentforce agents") resolves directly; it is not a bare category.
Otherwise map the user's term to a Salesforce API name. Proceed only when confident:
you can state the exact API name and no other object — including a closely related
object in the same family (an assignment, license, or group variant) — is a plausible
match. Recognizing the concept isn't the same as being confident which object to
query: "permission sets" has several real, queryable variants (PermissionSet,
PermissionSetAssignment, PermissionSetGroup, PermissionSetLicense). That family
overlap, not just an unfamiliar acronym, is reason enough to fetch rather than guess.
Otherwise — an unfamiliar acronym, synonym, colloquialism, or a term with a plausible
rival object — fetch `describe({"id": "ref:record-discovery/assets/object-synonyms"})`
before choosing an API name; do not ask instead of fetching. Use these exact arguments:

```json
{"id": "ref:record-discovery/assets/object-synonyms"}
```

This is an H360 reference artifact, not a file in this skill: do not use
`skill read` for `assets/object-synonyms`, and use the `id` string exactly as
shown above. The artifact has a known id, so it does not require `discover`
first. If the
reference does not resolve the term and more than one entity plausibly
matches, ASK. Never guess an API name that could silently query the wrong
entity.

**Step 2 — Infer the API family, then try it and flip once if wrong.** Do NOT read
describe-global to learn the family, and do NOT keep a memorized Tooling list. Decide
the family by what the entity *is*:
- **Tooling** = *definitions of code or schema* — Apex (class/trigger), Flow /
  FlowDefinition, ValidationRule, WorkflowRule, CustomField, FlexiPage, WebLink,
  EntityDefinition. "The metadata that defines how the org is built."
- **Enterprise** = *records and anything with rows you query, assign, or own* — this
  covers ordinary data (Account, Contact, `*__c`, …) **and** the admin/config objects
  that store rows: PermissionSet, PermissionSetGroup, Profile, User, UserRole, Group,
  RecordType, licenses, ConnectedApplication, TabDefinition. These *feel* like setup
  but are Enterprise — route them to Enterprise first.
- Mnemonic: **a definition of code or schema → Tooling; anything with rows you'd query,
  assign, or own → Enterprise.**
- **Query your inferred family first; flip ONCE on a clean miss.** A wrong family
  returns `400 sObject type not supported`. On that error, retry the same query on the
  other family's path. If the *other* path also errors, the problem is the API name,
  not the family — stop flipping: re-resolve the name (Step 1) or do ONE basic describe,
  then report. One flip, never a back-and-forth.
- **Do not infer absence from a failed or incomplete read.** An unsupported-entity
  error or a metadata parent response that omits named children does not prove
  there are no matches. Follow the bounded error-recovery steps below; if the
  available tools cannot enumerate the requested items, say that you could not
  verify the result instead of reporting zero.
- If an entity appears in BOTH families, prefer the Enterprise API.
- **Query the entity resolved in Step 1 — never substitute a related object.**
  For "my" / "assigned to me", filter rather than switch FROM: if the entity
  has no direct owner field, filter via a subquery against its
  assignment/ownership object — `WHERE Id IN (SELECT <ParentField> FROM
  <AssignmentObject> WHERE <AssigneeField> = ...)` — querying that object
  only to supply the filter, never as the result itself.
- Reuse the exact API version segment the tools return in their paths; never
  invent or change a version number.

**Step 3 — Resolve the name field by a cheap ladder, not an up-front describe.**
Do NOT describe the entity first just to learn its name field — a full describe
floods context and is unnecessary on almost every turn. Instead assume the field
is `Name` and query it. If the query errors with `400 No such column 'Name'`,
retry once with `MasterLabel`. Only if THAT also errors — the rare double miss
(e.g. ValidationRule needs `ValidationName`, ExternalClientApplication needs
`DeveloperName`) — do ONE basic sObject describe to read the true name/label
field, then query with it. Most entities resolve at `Name` or `MasterLabel`, so
you pay the describe only on the outliers. A wrong name field errors cleanly
(`400 No such column`), which is exactly what makes this ladder safe — you always
get a signal to step down. Never open with a full `/describe` or a
describe-global for this.

**Step 4 — Choose the search and run it (read-only).** First decide predicate
vs semantic — it determines which search to use. SOSL is NOT Enterprise-only; it
works across many families but does not cover every entity (most Tooling/setup
*definition* entities are not in the SOSL index), whereas SOQL works on anything
queryable. So:
- **By name / identifier (predicate)** — the user names a specific record
  ("the … named X", "the … called X", a specific identifier). **Try SOSL first,
  regardless of family** — a single SOSL search covers all the entity's name fields
  at once, so on entities it covers you skip the Step-3 name-field ladder entirely.
    - **If SOSL errors** (e.g. the entity is not SOSL-searchable — a Tooling
      definition type returns an invalid-RETURNING-type error), **fall back to SOQL**:
      route by the inferred family (Step 2, flip once on a family error) and match with
      `WHERE <labelField> LIKE '%…%'`, where `<labelField>` comes from the Step-3
      ladder (`Name` → `MasterLabel` → describe).
    - **If SOSL returns zero rows, that is a valid "none found" — stop.** Do NOT fall
      back to SOQL on an empty SOSL result; only a SOSL *error* triggers the fallback.
      (Known limitation: SOSL indexing is not synchronous, so a just-created record can
      be briefly invisible to SOSL and read as "none found." Narrow edge in a read flow;
      accepted.)
- **By description / free-text meaning (semantic)** — the user describes a topic
  rather than naming a record ("… that mention X", "… related to X", "… about X").
  **Do NOT use SOSL for these — use SOQL directly.** Route by the inferred family
  (Step 2) and build a `WHERE … LIKE` against the entity's descriptive text fields,
  resolving the field via the Step-3 ladder. SOSL is only for by-name lookups; using
  it for a topic query wastes a round-trip and often errors.
- **By count or other aggregate ("how many …", "total …", "average …")** — build
  the aggregate SOQL (`COUNT()`, `SUM()`, `AVG()`, etc.) for the entity, route by
  the inferred family (Step 2) exactly like any other SOQL, and `dispatch` it
  through that family's query path. Whatever you report in Step 5 is the value
  that path actually returned — there is no render-time query execution, so never
  hand an un-dispatched query string to a rendering tool and call that "running" it.
- Pass the query string through the tool's query-parameter map (q), never
  inline in the URL path — an inline query is rejected before it reaches the org.
- If a query errors, read the error and fix the specific cause (wrong field,
  wrong family, wrong path) — do not re-issue the same shape hoping for a
  different result. Two failed attempts on one entity means describe it once
  and correct the field/path before trying a third.

**Bound the result.** For a list, select only fields you will display and cap
the search or query at 25 rows.

**Tooling query recipes (reference).** For the
Tooling entities below, query the tooling query path (`/services/data/vXX.X/tooling/query`,
SOQL only) with the given SELECT and filter on the name field. These are correct as
written — do NOT first try the Enterprise `/query` path, and do NOT fall back to a heavy
endpoint (the UI tabs endpoint `/services/data/vXX/tabs`, the Metadata API read path,
or a per-type describe / describe-global) — they return visual/metadata blobs and are
never needed for find/list/count. If a thin query returns fewer fields than you want,
add fields to the SELECT — do not switch to a heavier endpoint.

| API name | Tooling SELECT (filter on name field with LIKE '%term%') |
  |---|---|
| TabDefinition (custom tabs) | `SELECT Id, Label, Name FROM TabDefinition WHERE IsCustom = true AND Label LIKE '%…%'` — Enterprise `/query` path, NOT tooling (CustomTabDefinition is NOT a queryable type in this org) |
| ValidationRule | `SELECT Id, ValidationName, Active, EntityDefinition.DeveloperName FROM ValidationRule WHERE ValidationName LIKE '%…%'` |
| FlexiPage | `SELECT Id, DeveloperName, MasterLabel, Type FROM FlexiPage WHERE MasterLabel LIKE '%…%'` |
| WebLink | `SELECT Id, Name, PageOrSobjectType FROM WebLink WHERE Name LIKE '%…%'` |
| ApexClass | `SELECT Id, Name, ApiVersion FROM ApexClass WHERE Name LIKE '%…%'` |
| ApexTrigger | `SELECT Id, Name, TableEnumOrId, Status FROM ApexTrigger WHERE Name LIKE '%…%'` |
| FlowDefinition | `SELECT Id, DeveloperName, ActiveVersionId FROM FlowDefinition WHERE DeveloperName LIKE '%…%'` |
| WorkflowRule | `SELECT Id, Name, TableEnumOrId FROM WorkflowRule WHERE Name LIKE '%…%'` |
| EntityDefinition (custom objects) | `SELECT Id, DeveloperName, QualifiedApiName, Label FROM EntityDefinition WHERE QualifiedApiName LIKE '%\_\_c'` |

**Custom objects — escape the `__c` suffix.** To list custom objects, query
EntityDefinition on the tooling path filtering on the API-name suffix `__c`. In SOQL `_`
is a single-char wildcard, so you MUST backslash-escape the two underscores to match a
LITERAL `__c`: write `WHERE QualifiedApiName LIKE '%\_\_c'`. (Unescaped `'%__c'` matches
any object ending "<anychar><anychar>c" — e.g. dozens of system *Metric objects — an
inflated, wrong answer.) Many orgs have zero custom objects; returning none is correct.

**Name-field matching (optimization — an OR-set can save a step).** The single
record-name field can silently miss label matches. When you already know the entity's
candidate name fields (e.g. the directory was fetched and gave a name-field hint), you
MAY search them as an OR-set in one query —
`WHERE (Name LIKE '%…%' OR Label LIKE '%…%' OR MasterLabel LIKE '%…%')`, limited to that
entity's fields — instead of stepping through the Step-3 ladder. This is an optional
speed-up, not required: the ladder alone is sufficient and correct.

**Describe-once backstop (only after the flip and the ladder are exhausted).** Family is
handled by infer + flip-once (Step 2) and the name field by the ladder (Step 3). Only when
BOTH have failed — the query errored on both family paths, or stepped past `MasterLabel` —
do ONE live basic sObject describe (`GET …/tooling/sobjects/<X>` or the Enterprise
equivalent, ~1.3 KB) to read the true family/name field, then retry once. Never describe
blindly up front, and never fall back to a full `/describe` or a describe-global.

**Step 5 — Present results.** Always render with `show_details` — never plain prose,
and never the generic `render_lightning_types` tool (its `type` values are for other
callers' registered Lightning types, none of which apply here; a fabricated type name
silently hangs the chat). This applies just as much when there's no list of records to
show — an aggregate result, a status, a single fact — as when there is: put whatever
you're reporting in `show_details`'s `summary`, with `fields` left empty if there's
nothing to break out. An empty `fields` array is never a reason to reach for
`render_lightning_types` instead.

For an open-ended "tell me everything about X" request, follow a **fixed** plan so
the result is the same every time — do not improvise how much to pull:
1. Resolve the record once (Steps 1–4).
2. Read that one record's own fields (a single record read / describe). Present
   those.
3. **Stop there.** Do NOT enumerate related child records — assignments, member
   permissions, field-permissions, usages, dependencies — as part of "everything
   about." Those vary wildly in volume and make the answer unstable.
4. If related data is likely relevant, **name the categories** available (e.g.
   "I can also pull its assigned users, object permissions, or field permissions")
   and offer to fetch them — let the user pick, rather than pulling a variable
   amount unprompted.

If more than one entity or record plausibly matches the request, show the
candidates and ask the user which they meant — never silently pick one. If
nothing matches, say so and offer to broaden the search.

You are read-only in this flow: never create, update, freeze, or delete a record
as part of discovery. If the user's next step is a change, follow the
confirm-before-write rule from your base instructions.

<!-- skill-validate: ignore-start -->
<!-- codey:operations start -->
## Operations Reference

Operations this skill uses — routing and dependency reference.

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `sosl-name-search` | read | — | `GET /services/data/v68.0/search` | — |
| `soql-query-enterprise` | read | — | `GET /services/data/v68.0/query` | — |
| `soql-query-tooling` | read | — | `GET /services/data/v68.0/tooling/query` | — |
| `sobject-basic-info` | read | — | `GET /services/data/v68.0/sobjects/{sobjectApiName}` | — |
| `tooling-sobject-basic-info` | read | — | `GET /services/data/v68.0/tooling/sobjects/{sobjectApiName}` | — |
| `read-record-by-id` | read | — | `GET /services/data/v68.0/sobjects/{sobjectApiName}/{recordId}` | `sosl-name-search` |
<!-- codey:operations end -->
<!-- skill-validate: ignore-end -->
