---
name: communications-tmf-integrate
description: "One-stop, zero-code-search reference for calling and extending Comms Cloud's TMF621 (Trouble Ticket Management) and TMF629 (Customer Management) TM Forum Open APIs — /connect/comms/troubleticket and /connect/comms/customermanagement. Trigger this skill for ANY of: calling or listing/creating/updating/deleting trouble tickets or customers via these APIs; asking what endpoints, params, request/response fields, or sub-resources (note, attachment, channel, relatedParty, engagedParty, agreement, account, etc.) exist; hitting the route directly against /connect/comms/troubleticket/v5/troubleticket or /connect/comms/customermanagement/v4/customer; questions about TMF/Comms TMF API access (CommsCloud / CommsCloudTMFAPI org permission); and — for extensibility scenarios only — writing or reviewing an Apex class that implements comms_apex_ext.ICommsGET/POST/PATCH/DELETE or the entity-specific ITroubleTicketManagementGET/POST/PATCH/DELETE / ICustomerManagementGET/POST/ PATCH/DELETE interfaces, or any of their hooks (transformRequest, configureDefaultValidations, applyCustomValidations, customiseGraphQLQuery, customiseMutationPayload, handlePostOperation), custom sub-resource registration, or deploying that Apex to an org (Setup UI, or the Metadata REST API / Tooling API). Gives exact endpoint tables, payload shapes, hook signatures, validation defaults, and a worked example — plus a built-in policy that only triggers Apex-writing/deployment when the user has explicitly asked for an extensibility scenario, always surfacing the generated class for user confirmation, always asking explicitly before deploying, and always checking for/confirming override of any existing implementor class before deploying. Never proposes or makes a schema change (new fields/objects/etc.) for TMF621/TMF629 work — always prefers extensibility when a customization is possible, explicitly tells the customer whether their request is achievable via extensibility, and says so plainly when it is not achievable within this scope. Use for keyword matches like \"TMF621\", \"TMF629\", \"trouble ticket API\", \"customer management API\", \"Comms TMF API\", or any comms_apex_ext.* interface/hook name, even if the user doesn't name the skill directly. Owned by: Comms Cloud Arches"
metadata:
  version: "1.0"
  cliTools:
  - tool:
    - "sf"
    semver: ">=2.0.0"
---

# TMF621 (Trouble Ticket) & TMF629 (Customer Management) — Complete API + Extensibility Guide

This skill is organized into parts:

- **Part 1 — Prerequisites** (org access, auth, API version) — read first, applies to everything.
- **Part 2 — Concepts common to both APIs** (extensible pipeline, pagination, filtering/sorting mechanism).
- **Part 3 — Extensibility framework** (common to both APIs) — only for extensibility scenarios.
- **Part 4 — TMF621 Trouble Ticket** (API-specific: endpoints, payloads, fields).
- **Part 5 — TMF629 Customer Management** (API-specific: endpoints, payloads, fields).
- **Part 6 — End-to-end execution checklist.**

| TMF API | Backing SObject |
|---|---|
| TMF621 Trouble Ticket Management | `Case` (+ `CaseTroubleTicket` extension fields for severity) |
| TMF629 Customer Management | `Account` (+ `Contact`, `Contract`) |

---

## Mandatory verification gate — read this before writing any Apex

**Never write or deploy an Apex extensibility class unless the user has clearly
asked for extensibility.** Plain "call this API" / "list trouble tickets" /
"create a customer" requests should be served entirely with Parts 4/5 (endpoint
routes) — no Apex, no deployment, nothing to confirm.

> **MUST — API version prerequisite for ALL extensibility scenarios (v67+):**
> Extensibility is only supported on orgs whose latest supported Salesforce API
> version is **`67.0` or above**. **Before running any extensibility scenario**
> (writing, deploying, or reasoning about an Apex extensibility class, or any of
> the hooks in Part 3), you **must** first discover the org's latest supported
> API version per §1.3 (`GET .../services/data/`). If the highest version the
> org reports is **below `67.0`, extensibility will not work** — stop
> immediately, tell the user their org's API version is below the required
> minimum (`67.0`), and do **not** write or deploy any Apex extensibility class.
> This check is mandatory and applies on top of every other step in this gate.
> (Plain, non-extensibility API calls in Parts 4/5 are not subject to this floor
> — they use the org's own latest version per §1.3.)

Follow this exact sequence whenever a request could involve extensibility:

1. **Determine intent first.** Only treat a request as an extensibility
   scenario if the user explicitly says so — e.g. "extend", "customize",
   "add a field to the response", "validate X before create", "override the
   response", "add a custom sub-resource", "write an Apex class for
   TMF621/TMF629", or similar. If the request is ambiguous (could be answered
   with the plain default endpoint, or you're not sure whether they want
   default behavior vs. custom behavior), **stop and ask the user directly**
   — e.g. "Do you want the default API behavior, or should I write an
   extensibility Apex class to customize this?" Do not guess, and do not
   default to writing Apex just because it's possible.
2. **Never make a schema change — ask the user to make it themselves.** Do not
   create/modify custom fields, objects, record types, page layouts, or any
   other metadata schema element to satisfy a TMF621/TMF629 request — Apex
   extensibility (Part 3) is the only sanctioned customization mechanism for
   this scope. If a request needs new schema (e.g. "store this extra value
   somewhere," "add a field to track X," or an extensibility class that
   references a field/object that doesn't exist yet), **do not create it
   yourself.** Tell the user exactly what schema they need to add (the object,
   field name, type), and ask them to make that schema change on their own.
   Make clear that **once they have added the schema, the request can then be
   supported via extensibility** — and only proceed with the Apex once the
   schema exists. Do not make any org changes on your own.
3. **Within TMF scope, always prefer extensibility when a customization is
   needed, and explicitly tell the customer whether their ask is achievable
   via extensibility.** For any request that isn't satisfied by the plain
   default endpoint, check whether one of the 6 hooks (§3.2) — or a custom
   sub-resource registration (§3.7) — can achieve it using fields/objects that
   already exist. If yes, say so explicitly and propose the extensibility
   approach. If the request truly cannot be done via extensibility alone,
   **tell the customer plainly that it is out of scope for extensibility**
   rather than improvising a workaround — do not silently fall back to a
   schema change or an out-of-scope mechanism. Two distinct cases to state
   explicitly to the user:
   - **Needs a schema change:** if the only thing blocking it is missing schema
     (a field/object that doesn't exist), say so, and per rule 2 ask the user
     to add that schema themselves — then it becomes supportable via
     extensibility. Do not add the schema yourself.
   - **Genuinely out of scope:** if it needs data or behavior outside what the
     6 Apex hooks can reach (even with schema in place), tell the user plainly
     that it is not possible within this skill's scope, and do not attempt a
     workaround.
4. **Write the Apex class.** Once — and only once — the user confirms they
   want an extensibility scenario, write the Apex class following Part 3
   (correct interface from §3.1, correct hook signatures from §3.2, no-op the
   hooks you don't need). Show the full class to the user.
5. **After posting the Apex, explicitly prompt the user to correct anything
   before deploying.** Right after you show the class, ask a direct question
   like: "Here's the class — do you want to correct anything before I deploy
   it? Tell me what to change and I'll update it." Make clear the user can hand
   back edits or corrections, and that you will apply them **before** any
   deployment. Do not deploy on the same turn you first show the code. Wait for
   explicit confirmation ("yes / looks good / deploy it") before proceeding. If
   the user gives corrections, apply them, show the revised class, and ask
   again — repeat until the user is satisfied.
6. **Always explicitly ask the user whether they want you to deploy it** —
   even after they've confirmed the class is correct, deployment is a separate
   decision from correctness. Do not deploy just because the code was
   approved; ask something like "Should I deploy this to the org now?" and
   wait for a clear yes.
7. **Check for an existing implementor before deploying, and confirm any
   override.** Per §3.9, only one concrete class may implement a given
   `comms_apex_ext.*` interface at a time — deploying a second one causes
   every call for that verb+entity to fail with a discovery error.
   Before deploying, check (or ask the user to check) whether a class already
   implements the target interface (e.g. via Setup → Apex Classes, or a
   Tooling API query against `ApexTypeImplementor`:
   `GET /services/data/vXX.0/tooling/query/?q=SELECT+ClassName+FROM+ApexTypeImplementor+WHERE+InterfaceName='<Interface>'`).
   If one exists, tell the user its name
   and **explicitly confirm they want to replace/deactivate it** before
   proceeding — do not silently overwrite or leave both active.
8. **Deploy only after both confirmations (step 6 and step 7)**, using §3.11.
9. After deployment, re-hit the relevant route from §4.4/§5.4 (or ask the
   user to) to confirm the customized behavior actually shows up in the live
   response.
10. **Never create test data in the org on your own.** Testing an extensibility
    class often needs sample records (a `Case`/trouble ticket, an
    `Account`/customer, related `Contact`/`Contract`/`Asset`, attachments,
    etc.). **Do not create, insert, POST, or otherwise write any data to the
    org to test the Apex** — no `POST` create calls, no `sf data create`, no
    anonymous-Apex `insert`, nothing. First **ask the user** whether they want
    you to create the data needed to exercise the class, tell them exactly what
    you would create, and **wait for explicit confirmation**. Prefer testing
    against records the user already has (ask for an existing `{id}`). Only
    create records if the user clearly says to, and only the specific records
    they approved.

---

# Part 1 — Prerequisites (both APIs)

Org access, authentication, and API-version discovery. No code changes required.

## 1.1 Access check & required permissions

Both API families are gated by a single access check that either org permission
satisfies — having `CommsCloud` or `CommsCloudTMFAPI` enabled is sufficient.

To call **any** endpoint in this skill, the calling user's org must have
`CommsCloud` or `CommsCloudTMFAPI` org permission enabled, and the calling user
needs standard CRUD/FLS access to the underlying object (`Case` for TMF621,
`Account`/`Contact`/`Contract` for TMF629) — this is a Connect API resource, so
ordinary Salesforce sharing and field-level security apply on top of the TMF
access check.

## 1.2 Authentication (External Client App + token)

Authentication is standard Salesforce session/OAuth: send a `Bearer`/session
token in the `Authorization` header, exactly like any other Connect (`/services/data/vXX.0/connect/...`) REST call.

**Before executing any endpoint below, the org needs an External Client App so
Claude can authenticate and call these APIs on the user's behalf** (External
Client Apps are Salesforce's current, recommended replacement for the legacy
Connected App framework).

**All External Client App details live in a dedicated reference — read it before
doing any auth/app work:** the bundled reference sample **external-client-app-setup**
in the skill's references bundle. It is the single source of truth for:

- listing/reusing an existing External Client App (Metadata API) and the
  admin prerequisites — don't create a duplicate;
- the inputs & defaults for creating a new app (defaults applied automatically;
  ask for all inputs only if the user wants to customize);
- the default OAuth scopes and policies (incl. the Client Credentials run-as
  user requirement);
- revealing/storing the Consumer Key & Secret;
- obtaining an access token; and
- after setup, asking the user whether to use this app to run the TMF APIs and,
  if so, doing everything needed to make the calls work through it (token →
  access check → version discovery → smoke test → the real request).

In short: confirm you already hold a live token for the target org; if not,
follow that reference to reuse or create the app and obtain a token. **Do not
attempt any API call until both the External Client App exists and you hold a
live access token for it.**

## 1.3 Discover the org's latest supported API version

**Verify the APIs are reachable by discovering the org's latest supported
Salesforce API version, and use that same latest version in every call in this
skill.** Call `GET https://<your-instance>.my.salesforce.com/services/data/`
(no version segment, with the `Bearer` token). It returns the list of every
API version the org supports; take the **highest** `version` value from the
response (e.g. `"67.0"`) and use it as the `v<API_VERSION>.0` / `vXX.0` segment
in **every** method throughout this skill — the TMF endpoint calls (Parts 4/5),
the Tooling API and Metadata REST API deploys (§3.11), the `ApexTypeImplementor`
query, and any other REST call. Do not mix versions across calls. A `200` here
confirms the token and instance URL are valid and tells you the exact API
version to use; if this call fails, fix auth (§1.2) before going further. Always
use a version the org actually reports — never hard-code a version the org may
not have.

## 1.4 Base URL pattern

Every endpoint in this skill is called as:

```text
https://<your-instance>.my.salesforce.com/services/data/v<API_VERSION>.0<path-from-tables-below>
```

Example: for TMF621's list endpoint, `<path-from-tables-below>` is
`/connect/comms/troubleticket/v5/troubleticket`, so the full URL is:

```text
https://myorg.my.salesforce.com/services/data/v67.0/connect/comms/troubleticket/v5/troubleticket
```

The `v5` / `v4` segment in the path is the **TMF resource version** (a separate,
independent version token baked into the URL itself — not the same as the
Salesforce API version `v67.0` in the outer path, which comes from §1.3). Always
use the exact TMF version segment shown in the tables below; using the wrong one
silently 404s or routes to the legacy (non-extensible) handler.

---

# Part 2 — Concepts common to both APIs

## 2.1 The extensible pipeline is always on

Every endpoint in Parts 4/5 (except legacy fallbacks with no handler mapping)
runs through the **extensible** code path — meaning every request, even one with
zero customization, passes through the Apex extensibility pipeline described in
Part 3. There is nothing you need to configure to "turn on" extensibility; it is
always active, and there is no separate "legacy" endpoint you need to avoid — the
framework transparently prefers the extensible handler for the versions listed in
Parts 4/5. Apex customization is purely additive/optional (§3.9 explains
discovery: if no Apex class implements the interface, the framework just uses
defaults).

## 2.2 Pagination (bounds & per-API defaults)

Both list/GET endpoints accept `offset` (int), `pageLimit` (int), and `pageinfo`
(bool — return `totalPageSize`/`currentPage`). Bounds are enforced consistently
for **both APIs**:

- `pageLimit` max is **2000**; a larger value → HTTP 400 `"Page limit cannot exceed 2000"`.
- `offset + pageLimit` must be **≤ 100,000** (it's the *sum*, not the product); exceeding it → HTTP 400 `"Pagination is supported only for 100,000 records…"`.
- `offset < 0` is clamped to `0`; `pageLimit ≤ 0` falls back to the default.
- **Default `pageLimit` is per-API** (applied whenever the caller omits it — the API never returns "all records" unbounded): CustomerManagement = **10**, TroubleTicket = **1000**, base default = 100.

## 2.3 Filtering & sorting — how it works

The mechanism is identical for both APIs; only the named field mappings differ
(see §4.5 for TMF621, §5.5 for TMF629):

- **Filtering is not a fixed allow-list.** Filters are passed as dynamic query
  params (e.g. `?Status=New`) straight into a GraphQL `where` clause — filtering
  is allowed on any valid Salesforce field. Each API also has a small **named
  TMF-field mapping** whose TMF aliases work for filtering, sorting, and
  `fields=` selection; any other raw Salesforce field name on the backing object
  also works.
- **`sort=` query param** is available at minVersion 264. Besides the flat
  named/raw fields, a short whitelist of nested (dotted) 1:1-relationship sort
  paths is allowed per API.
- **Multi-record/child connections are not sortable** via the parent list
  (e.g. notes, attachments, status history, child accounts, contracts) — they
  are GraphQL connections, not scalar columns.
- The Workbench artifact param `t` is explicitly stripped, and any filter with a
  `null` field name or `null` value is silently dropped.
- **A bad filter field fails silently as an empty result — not an error.** The
  raw field name is dropped **untranslated** into the GraphQL `where` clause, so
  it must be a valid, GraphQL-queryable field on the backing object. If you pass
  a field that doesn't exist (or isn't queryable), the GraphQL layer errors and
  the API **returns an empty result set rather than a 4xx**. So an empty list can
  mean "no matching records" **or** "you filtered on a field name that doesn't
  exist" — warn the user of this when a filter unexpectedly returns nothing.

### 2.3.1 When a user wants to filter by a field that isn't an out-of-the-box named filter

If a user asks to filter by something not in the named filter/mapping table
(§4.5/§5.5), **ask them which exact field they mean**, then follow this decision
flow — do not guess:

1. **Is it a field that exists directly on the backing object** (`Case` for
   TMF621, `Account` for TMF629)? Confirm the field is really present on that
   object (ask the user, or check the org schema — do not assume). If yes:
   - **No extensibility needed.** Tell the user they can filter by the raw
     Salesforce field name directly as a query param — e.g.
     `?Origin=Phone` (TMF621) or `?Industry=Telecom` (TMF629). It works out of
     the box (verified: unmapped field names pass straight into the `where`
     clause). Only offer extensibility if they *also* want to expose it under a
     different TMF-facing name (see step 2).
2. **Do they want to filter under a custom/renamed TMF name, or the field is on
   a related/child object** (not a scalar column on the backing object)? Then it
   needs **extensibility** (`customiseGraphQLQuery` — add a filter to the right
   node, or map the incoming name). If feasible:
   - Confirm feasibility, then **ask the customer which Salesforce field they
     want that TMF filter name mapped to**, and write the extensibility class
     using that mapping (per the mandatory gate + §3.4). Substitute their real
     field/relationship API names.
3. **Is the field NOT present on the entity at all** (no such field on the
   object, and not reachable via a relationship the hooks can query)? Then
   **plainly tell the user it cannot be done because the field itself does not
   exist on that entity** — do not invent a workaround, and (per rule 2) do not
   create the field yourself. If they want it, they must add the schema first
   (then it becomes filterable per step 1).

---

# Part 3 — Extensibility framework (common to both APIs)

This is the **only** mechanism intended for customization: an Apex class
implementing a well-known interface, deployed to the org. There is no Java code
change, no config file, no registry entry needed — the framework discovers your
Apex class by its **interface name** at request time. Only enter this part for
an extensibility scenario, and only after the mandatory gate at the top of this
skill.

## 3.1 The interface family tree

```text
comms_apex_ext.ICommsExtensible                (base — declares transformRequest, configureDefaultValidations,
                                                  applyCustomValidations, customiseGraphQLQuery, handlePostOperation
                                                  — ALL 5 methods, inherited by every verb below, GET included)
 ├── comms_apex_ext.ICommsGET                    extends ICommsExtensible (no extra methods)
 │    ├── comms_apex_ext.ITroubleTicketManagementGET   extends ICommsGET   ← implement for TMF621 GET
 │    └── comms_apex_ext.ICustomerManagementGET        extends ICommsGET   ← implement for TMF629 GET
 ├── comms_apex_ext.ICommsPOST                   extends ICommsExtensible (+ customiseMutationPayload)
 │    ├── comms_apex_ext.ITroubleTicketManagementPOST  extends ICommsPOST  ← implement for TMF621 POST
 │    └── comms_apex_ext.ICustomerManagementPOST       extends ICommsPOST  ← implement for TMF629 POST
 ├── comms_apex_ext.ICommsPATCH                  extends ICommsExtensible (+ customiseMutationPayload)
 │    ├── comms_apex_ext.ITroubleTicketManagementPATCH extends ICommsPATCH ← implement for TMF621 PATCH
 │    └── comms_apex_ext.ICustomerManagementPATCH      extends ICommsPATCH ← implement for TMF629 PATCH
 └── comms_apex_ext.ICommsDELETE                 extends ICommsExtensible (+ customiseMutationPayload)
      ├── comms_apex_ext.ITroubleTicketManagementDELETE extends ICommsDELETE ← implement for TMF621 DELETE
      └── comms_apex_ext.ICustomerManagementDELETE      extends ICommsDELETE ← implement for TMF629 DELETE
```

**Important — `customiseGraphQLQuery` is declared on the base `ICommsExtensible`
interface, not added by `ICommsGET`.** That means it is inherited by every
verb's interface, including POST/PATCH/DELETE. Apex requires implementing
every method an interface declares or inherits, so a POST/PATCH/DELETE Apex
class **must** also implement `customiseGraphQLQuery` (no-op it by returning
`null` — see §3.2) or the class will fail to compile. In practice it only has
real effect on GET, since POST/PATCH/DELETE don't run a query — but it still
must be present in the class body for any verb.

**Rule of thumb: pick exactly one interface per HTTP verb you want to customize**,
implement it in a single Apex class (a class *can* implement more than one of
these interfaces at once, e.g. both GET and POST, if you want one class to
handle multiple verbs — see the "combined pattern" example in §3.8). **All 5
methods declared on `ICommsExtensible` must be implemented for every verb**
(plus `customiseMutationPayload` for POST/PATCH/DELETE), even if you just want
to no-op them — return the "do nothing" value shown per hook below.

There is **no sub-resource-specific interface** — sub-resource requests
(`GET .../{id}/{subResource}`) are routed through the *same* `ICommsGET`
implementation as the plain single-entity GET; you distinguish sub-resource
requests inside your hooks by checking `context.get("subResourceName")` /
registering custom sub-resource mappings (§3.7).

## 3.2 Every hook method, in call order

The framework calls your hooks in this fixed pipeline order for every request.
**If you don't implement a behavior for a hook, return the pass-through/no-op
value shown — do not return `null` unless explicitly allowed, as some hooks
treat `null` as "no data to merge" rather than "no-op".**

| Order | Hook | Verbs | Signature | Purpose | No-op return |
|---|---|---|---|---|---|
| 1 | `transformRequest` | GET/POST/PATCH/DELETE | `Map<String,Object> transformRequest(Map<String,Object> context)` | First hook called. Mutate the request context before anything else runs — e.g. resolve an external ID to a Salesforce Id, inject custom flags/params used by later hooks. | `return context;` |
| 2 | `configureDefaultValidations` | GET/POST/PATCH/DELETE | `Map<String,Boolean> configureDefaultValidations(Map<String,Boolean> defaultValidationConfiguration, Map<String,Object> context)` | Turn built-in field validators on/off per request (§3.6). | `return defaultValidationConfiguration;` (or `new Map<String,Boolean>()` to accept framework defaults unchanged) |
| 3 | `applyCustomValidations` | GET/POST/PATCH/DELETE | `Map<String,Object> applyCustomValidations(Map<String,Object> context)` | Run your own validation logic. To **fail** the request, return a map shaped like the error example below; the framework throws and the HTTP call gets a 400. | `return null;` |
| 4a | `customiseGraphQLQuery` | GET/POST/PATCH/DELETE (declared on base `ICommsExtensible`; only has functional effect on GET, but must still be implemented for every verb) | `Map<String,Object> customiseGraphQLQuery(Map<String,Object> graphQLAsMap, Map<String,Object> context)` | Add/remove fields, add/merge filters, set sort order on the query the framework is about to run. | `return null;` |
| 4b | `customiseMutationPayload` | POST/PATCH/DELETE only | `Map<String,Object> customiseMutationPayload(Map<String,Object> mutationGraphQLPayload, Map<String,Object> context)` | Add extra fields/values to the create/update/delete mutation before it executes. | `return null;` |
| 5 | (framework executes the GraphQL query/mutation — not customizable) | — | — | — | — |
| 6 | `handlePostOperation` | GET/POST/PATCH/DELETE (called on every verb, but the returned payload override is only applied on GET — see §3.3) | `Map<String,Object> handlePostOperation(Map<String,Object> graphQLQueryResultAsMap, Map<String,Object> constructedTMFResponse, Map<String,Object> context)` | Last hook. Inspect the raw GraphQL result and/or the TMF-shaped response the framework built, and on GET optionally **replace it entirely**. | `return null;` |

Note `applyCustomValidations` and `handlePostOperation` share the same name
across GET/POST/PATCH/DELETE (defined once on the base `ICommsExtensible`), so
implementing a POST class means implementing them for the POST flow, etc. — the
framework calls whichever concrete class is currently active for that verb.

Hook methods may be declared **either `global static` or as instance
(`global`/`public`) methods** — the framework instantiates your class and then
invokes the method, so both styles compile and run. The examples
below use `global static`; instance methods work identically.

Quick "which hook do I use" index:

| Goal | Hook(s) |
|---|---|
| Resolve an external id (CaseNumber, AccountNumber) to a Salesforce Id | `transformRequest` |
| Enforce a custom business rule / access check before running | `applyCustomValidations` |
| Role-based data filtering (block, then trim what's returned) | `applyCustomValidations` + `handlePostOperation` |
| Add fields / server-side filter / sort to a GET query | `customiseGraphQLQuery` |
| Add fields to a create/update mutation | `customiseMutationPayload` |
| Enrich or restructure the response (calculated fields, GET-only full override) | `handlePostOperation` |

`transformRequest` receives (and must return) the same `context` map passed to
every later hook. The framework reads two keys back out of it after the call:
`context.get('id')` (a `String`) overwrites the path id used for the rest of
the request, and `context.get('requestBody')` (a `Map`) overwrites the request
body — this is how you resolve an alternate identifier (e.g. an external
account/order number) to a Salesforce Id before any query or mutation runs:

```java
global static Map<String, Object> transformRequest(Map<String, Object> context) {
    String rawId = (String) context.get('id');
    if (rawId != null && !rawId.startsWith('001')) {   // not already a Salesforce Account Id
        List<Account> matches = [SELECT Id FROM Account WHERE AccountNumber = :rawId LIMIT 1];
        if (!matches.isEmpty()) {
            context.put('id', matches[0].Id);
        }
    }
    return context;
}
```

## 3.3 `handlePostOperation` — the two response-shaping outcomes

`handlePostOperation` is the most commonly used hook. It always receives:

- `graphQLQueryResultAsMap` — the raw GraphQL response (`{"data": {"uiapi": {"query": {...}}}}` shape for GET, or `{"data": {"uiapi": {<alias>: {...}}}}` for mutations).
- `constructedTMFResponse` — the TMF-shaped payload the framework already built (e.g. `{"id": "...", "name": "...", "href": "..."}` for single-record GET, or `{"recordList": [...]}` for list GET).
- `context` — the (possibly already transformed) request context.

Return one of:

**A. No change** — return `null`. The framework's `constructedTMFResponse` is used as-is.

**B. Full override** — return:
```java
new Map<String, Object>{
    'payloadOverwritten' => true,
    'updatedPayload' => myModifiedResponseMap   // must be a complete replacement, not a diff
}
```
When `payloadOverwritten=true`, the framework serializes exactly `updatedPayload`
back to the caller as the response body (surfaced as the `updatedPayload` field
on the output representation — see §4.2/§5.2). This is how the reference example
in §3.8 renames `id`→`salesforce_id` and injects an extra field.

**This override only works on GET.** `handlePostOperation`'s return value is
only read back and applied on the GET path. On POST, PATCH,
and DELETE the framework still *calls* your `handlePostOperation` (so
side-effecting logic — logging, firing a platform event, calling out to another
system — still runs), but the map you return is discarded; there is no
supported way to overwrite the POST/PATCH/DELETE response body from this hook.
If you need to change what a mutation returns, do it via `customiseMutationPayload`
(§3.5) before the mutation runs, not via `handlePostOperation` after.

## 3.4 `customiseGraphQLQuery` — instruction map shape (GET)

Return a map with a `nodes` list; each entry targets one GraphQL query node by
its `path` alias (`troubleTicket` for TMF621, `troubleTicket`/`customerAccount`
depending on handler — check the raw query in `graphQLAsMap.get("query")` to
find the exact alias for the entity you're customizing):

```java
global static Map<String, Object> customiseGraphQLQuery(Map<String,Object> querySpec, Map<String,Object> context) {
    return new Map<String, Object>{
        'nodes' => new List<Object>{
            new Map<String, Object>{
                'path' => 'troubleTicket',                       // GraphQL alias to target
                'addFields' => new List<String>{ 'IsClosed { value }' },   // extra fields to select
                'addFilters' => new Map<String, Object>{
                    'clearExistingFilters' => false,              // false = merge with existing filters
                    'filterGraphQlSnippet' => '{ IsClosed: { eq: true } }'
                },
                'orderBy' => new Map<String, Object>{
                    'clearExistingOrderBy' => true,               // true = replace any client-requested sort
                    'orderGraphQlSnippet' => '{ Subject: { order: ASC } }'
                }
            }
        }
    };
}
```

`addFields` entries are raw GraphQL field-selection snippets appended under the
targeted node — use `{ value }` suffix for scalar fields per UI API convention
(e.g. `'IsClosed { value }'`, not just `'IsClosed'`).

## 3.5 `customiseMutationPayload` — instruction map shape (POST/PATCH/DELETE)

```java
global static Map<String, Object> customiseMutationPayload(Map<String,Object> mutationGraphQLPayload, Map<String,Object> context) {
    return new Map<String, Object>{
        'nodes' => new List<Object>{
            new Map<String, Object>{
                'path' => 'customerAccount',                      // mutation alias to target, e.g. AccountCreate/AccountUpdate/AccountDelete
                'addFields' => new Map<String, Object>{             // for mutations, addFields is a map of field->value, not a list
                    'Industry' => 'Technology',
                    'Revenue' => 5000000,
                    'Status' => 'Active'
                }
            }
        }
    };
}
```

A mutation node supports these keys (all optional except `path`):

| Key | Shape | Effect |
|---|---|---|
| `addFields` | `Map<String,Object>` (field→value) | Adds brand-new fields/values to the mutation input for that node. |
| `modifyInput` | `Map` with `inputModifications` / `addInputFields` / `removeInputFields` | Rewrite fields already in the input. `inputModifications` (field→new value) overwrites values the caller sent — e.g. `{'Name' => 'Updated ' + originalName}`; `removeInputFields` is a `List<String>` of fields to drop. |
| `insertGraphQlSnippet` | `String` (raw GraphQL) | Inject an extra mutation node — e.g. create a related custom-object record. Use `@{alias}` to reference the id of another node created in the same mutation (e.g. `Account__c: "@{customerAccount}"`). |
| `updateGraphQlSnippet` | `String` (raw GraphQL) | Same, for an update sub-mutation. |

Example — overwrite the caller-supplied `Name` and create a related record in one call:
```java
global static Map<String, Object> customiseMutationPayload(Map<String,Object> request, Map<String,Object> context) {
    Map<String,Object> body = (Map<String,Object>) context.get('requestBody');
    String name = body == null ? null : (String) body.get('name');
    if (String.isBlank(name)) { return new Map<String, Object>(); }   // no-op → return empty map, not null
    return new Map<String, Object>{
        'nodes' => new List<Object>{
            new Map<String, Object>{
                'path' => 'customerAccount',
                'modifyInput' => new Map<String, Object>{
                    'inputModifications' => new Map<String, Object>{ 'Name' => 'Updated ' + name }
                }
            },
            new Map<String, Object>{
                'path' => 'customerAccount.extCustomer',
                'insertGraphQlSnippet' => 'extCustomer: ExtCustomer__cCreate(input: { ExtCustomer__c: { Name: "'
                    + name.replace('\\', '\\\\').replace('"', '\\"')
                    + '", Account__c: "@{customerAccount}" } }) { Record { Id } }'
            }
        }
    };
}
```

## 3.6 Built-in field validators you can toggle with `configureDefaultValidations`

Each API has its own set of named boolean validators; pass a map with the names
you want to flip. Any name you omit keeps the framework's default for that verb
(shown below — POST defaults to all `true`, PATCH defaults to all `false`).

**`configureDefaultValidations` only has an effect on POST/PATCH/DELETE.** On
GET the hook is still invoked (so it must be implemented), but the map you
return is ignored — GET ships an empty default validation spec and never runs
these named validators. Use `applyCustomValidations` (§3.2) if you need to
reject a GET request.

**TMF621 (TroubleTicket)** — validator names: `mandatoryFieldsValidation`
(requires `description`, `severity`, `ticketType`), `relatedPartyValidation`
(each `relatedParty` entry needs non-blank `id` and `referredType` ∈
{`Account`,`Contact`}), `relatedEntityValidation` (each `relatedEntity` entry
needs non-blank `id` and `referredType` == `Asset`).
- POST default: `{mandatoryFieldsValidation: true, relatedPartyValidation: true, relatedEntityValidation: true}`
- PATCH default: `{mandatoryFieldsValidation: false, relatedPartyValidation: false, relatedEntityValidation: false}`

**TMF629 (Customer)** — validator names: `mandatoryFieldsValidation`,
`engagedPartyValidation`, `contactMediumValidation`, `accountValidation`.
- POST default: `{mandatoryFieldsValidation: true, engagedPartyValidation: true, contactMediumValidation: true, accountValidation: true}`
- PATCH default: `{mandatoryFieldsValidation: false, engagedPartyValidation: false, contactMediumValidation: false, accountValidation: false}`

Example — disable the mandatory-fields check on TMF621 POST:
```java
global static Map<String, Boolean> configureDefaultValidations(
        Map<String, Boolean> defaultValidationConfiguration, Map<String, Object> context) {
    Map<String, Boolean> updated = new Map<String, Boolean>(defaultValidationConfiguration);
    updated.put('mandatoryFieldsValidation', false);
    return updated;
}
```

To **fail** a request from `applyCustomValidations` instead, return
`validationStatus`/`validationMessage`/`validationDetails` as **top-level**
keys (no extra wrapper) — this is exactly what the framework reads back when it
invokes `applyCustomValidations`:
```java
global static Map<String, Object> applyCustomValidations(Map<String, Object> context) {
    Boolean isBad = /* your check */ false;
    if (isBad) {
        return new Map<String, Object>{
            'validationStatus' => 'fail',
            'validationMessage' => 'Custom validation failure',
            'validationDetails' => new Map<String, Object>{
                'statusCode' => 'BAD_REQUEST',
                'errorCode' => 'BAD_REQUEST'
            }
        };
    }
    return null;
}
```
`validationStatus` is checked case-insensitively against `"fail"`; on a match
the framework throws and the call gets a 400 with `validationMessage` (default
`"Validation failed"`) and `validationDetails` in the error body.

## 3.7 Registering a brand-new custom sub-resource (no Java change)

Do this entirely from `transformRequest` on your `*GET` implementation: put a
`customSubResourceMappings` entry into the context, keyed by the sub-resource
name you want exposed in the URL, describing the SOQL-level relationship:

```java
global static Map<String, Object> transformRequest(Map<String, Object> context) {
    context.put('customSubResourceMappings', new Map<String, Object>{
        'opportunities' => new Map<String, Object>{
            'sfChildObjectName' => 'Opportunity',
            'sfParentLookupField' => 'AccountId',
            'sfRelationshipName' => 'Opportunities'
        }
    });
    return context;
}
```

Then in `customiseGraphQLQuery`, inject the raw GraphQL connection snippet for
that relationship (`insertGraphQlSnippet` instruction), and in
`handlePostOperation`, read `context.get("isCustomSubResource")` /
`context.get("customSubResourceRawRecords")` and build the TMF JSON yourself
(the framework defers all shaping of custom sub-resources to your Apex — it
only knows how to shape the built-in ones listed in §4.3/§5.3).

## 3.8 Worked examples & pattern sketches — adapt, don't copy verbatim

> **⚠️ Read before using anything in §3.8.x.** The Apex classes in §3.8, §3.8.1,
> and §3.8.2 are **illustrative samples to learn the mechanics from — they are
> NOT the source of truth and NOT copy-paste-ready.** They encode field names,
> object names, validation rules, and business logic that were invented for the
> example, not derived from the user's org. **Do not deploy any of them as-is.**
>
> When a user asks for an extensibility class:
> 1. **First understand what the user actually wants** — which verb (GET/POST/
>    PATCH/DELETE), which entity (TMF621 vs TMF629), which hooks, what fields/
>    objects/rules in *their* org, and what the desired behavior is. Ask if it's
>    ambiguous (per the mandatory verification gate at the top of this skill).
> 2. **Then write a fresh class tailored to that request**, using these samples
>    only as a reference for the correct interface (§3.1), hook signatures
>    (§3.2), return-value contracts (§3.3–§3.6), and the `'nodes'`/`addFields`/
>    `insertGraphQlSnippet`/`@{alias}` mechanics. Substitute the user's real
>    field/object API names — never keep the sample placeholders.
> 3. **Verify and deploy** per the §3.11 workflow, then re-hit the endpoint to
>    confirm the behavior.
>
> The source of truth is always the framework code and the user's org schema —
> not these snippets.

### 3.8.0 Full worked example — combine multiple patterns in one class

This is a complete, deployable-shaped Apex class for **TMF621 GET** that (1) adds
an extra field to the response, (2) filters server-side, (3) sorts, and (4)
renames a response field — demonstrating that all four extensibility axes can be
combined freely in one class. **Adapt the field names and logic to the user's
org before deploying (see the §3.8 banner).**

**Full source:** the bundled reference sample **TroubleTicketCombinedPattern**
— read that file in the skill's references/apex-samples bundle for the complete class. It implements
`comms_apex_ext.ITroubleTicketManagementGET`, targets the `troubleTicket` query
node in `customiseGraphQLQuery` (adds `IsClosed { value }`, a
`clearExistingFilters=false` filter, and an `orderBy`), and in
`handlePostOperation` unwraps the `data → uiapi → query → troubleTicket → edges`
shape to rename `id` → `salesforce_id` and copy `IsClosed` onto each record via a
`payloadOverwritten`/`updatedPayload` override.

Deploy this class to your org (Setup → Apex Classes, or via the Metadata REST
API / Tooling API — see §3.11), then simply call the TMF621 GET/list endpoints
as shown in §4.4 — no additional registration step. The framework finds it
automatically (see §3.9).

### 3.8.1 Pattern sketch — advanced TMF629 GET (external-key resolution + supplementary SOQL + custom sub-resources)

> **⚠️ Pattern sketch, not a verified drop-in.** Every construct below was
> checked against the framework contract (hook signatures, the `'nodes'` /
> `clearExistingFilters` / `filterGraphQlSnippet` keys, the alias-based `path`,
> the `data → uiapi → query → customerAccount → edges` shape, the
> `payloadOverwritten`/`updatedPayload` contract, the filter fields
> `fieldName`/`value`, and the case-insensitive `"fail"` check).
> **It has NOT been compiled or deployed to an org**, so treat it as an
> illustrative composition, not copy-paste-ready code. Before using it, follow
> the §3.11 workflow: deploy it, hit `GET /connect/comms/customermanagement/v4/customer/{id}`,
> and confirm the enrichment actually appears — then fix whatever the live run
> surfaces. Field/relationship API names (`AccountNumber`, `Opportunities`,
> `Contract.ContractNumber`) are placeholders; substitute your org's real ones.

This sketch composes three patterns the earlier examples only show in isolation:

1. **`transformRequest`** — accept a business key (`AccountNumber`) in the
   `{id}`/filter slot and rewrite the filter's `value` to the real `Account` Id
   (the framework maps a path `{id}` into a filter whose `fieldName` is `Id`).
2. **`customiseGraphQLQuery`** — add scalar fields plus a related child
   connection (`Opportunities`) to the `customerAccount` node.
3. **`handlePostOperation`** — run supplementary SOQL the GraphQL query can't
   express (latest `ContractNumber` per account), then inject a brand-new
   `relatedOpportunities` sub-resource and drop an OOTB field — handling **both**
   the list (`recordList`) and single-record (`id`) response shapes.

**Full source:** the bundled reference sample **CustomerManagementAdvancedGet**
— read that file in the skill's references/apex-samples bundle for the complete class, including the private `enrichRecord` /
`extractOpportunities` / `graphQLValue` helpers.

**Two things this sketch deliberately does NOT do** (both were present in a
source doc but are wrong against the code, so don't reintroduce them):
`customiseGraphQLQuery` must return `'nodes'` (a `'spec'` key is silently
ignored); and a transformation `path` must be a GraphQL **alias**
(`customerAccount`), never a dotted `uiapi.query.Account` — structural fields
(`uiapi`, `query`, `edges`, `node`, `pageInfo`) are stripped during path
resolution. The filter object provided to `transformRequest` also has **only**
the keys `fieldName`, `operator`, `value`, and `dataType` — there is no
`soqlcondition`/`rawValue` sub-map to mutate.

### 3.8.2 Pattern sketch — advanced TMF629 POST (custom validations + related-record mutation + side-effect DML)

> **⚠️ Pattern sketch, not a verified drop-in** (see the §3.8 banner — adapt to
> the user's request/org, don't copy verbatim). Every construct below was
> checked against the framework contract (the `customiseMutationPayload`
> `'nodes'` shape with **`addFields` as a `Map`**; per-node
> `insertGraphQlSnippet`; the `@{customerAccount}` back-reference; the
> `validationStatus: "fail"` case-insensitive reject; and the POST
> post-processing flow). **It has NOT been compiled or deployed.**
> Field/relationship API names
> (`NumberOfEmployees`, `Website`, `MyChild__c`, etc.) are placeholders —
> substitute the user's real ones. Deploy and hit
> `POST /connect/comms/customermanagement/v4/customer` per §3.11 before trusting it.

**Two POST-specific gotchas this sketch exists to teach — both differ from GET:**

- **`handlePostOperation`'s return value is IGNORED for POST/PATCH/DELETE.**
  The framework calls the hook but discards its result — there is **no
  `payloadOverwritten`/`updatedPayload` response-override for mutations** (that
  only works on GET, §3.3). On a mutation, `handlePostOperation` is only useful
  for **side effects** (extra DML). Anything you `return` vanishes.
- **The hook's 2nd parameter is the REQUEST BODY on a mutation, not the TMF
  response.** For GET it's the constructed TMF response; for POST/PATCH/DELETE
  the framework passes the request body map as the 2nd parameter. Name it
  accordingly.

Also note: for a **mutation**, `addFields` is a **`Map`** (field → value); for a
**query** (`customiseGraphQLQuery`, §3.4) `addFields` is a **`List`** of field
strings. Same key name, different shape per hook.

**Full source:** the bundled reference sample **CustomerManagementAdvancedPost**
— read that file in the skill's references/apex-samples bundle for the complete class, including the `customiseMutationPayload`
node list (extra `Account` fields + a `MyChild__cCreate` snippet back-referencing
`@{customerAccount}`), the side-effect `insert Opportunity` in
`handlePostOperation`, and the `escape` helper.

> **Governor-limit caution.** `applyCustomValidations` runs SOQL and
> `handlePostOperation` runs DML on **every** POST. Keep these minimal and
> bulk-safe; a heavy hook multiplies per request and can blow limits under load.

## 3.9 How your Apex class gets discovered — no registry to update

There is **no file, XML, or metadata entry to register your Apex class**. At
request time the framework:

1. Takes the interface name for the current verb+entity (e.g.
   `comms_apex_ext.ITroubleTicketManagementGET`).
2. Queries the org's compiled Apex metadata (`ApexTypeImplementor`) for
   **concrete classes that implement that interface**.
3. If exactly one is found → uses it.
4. If none is found → skips all Apex hooks; the endpoint behaves with pure
   framework defaults (this is why every endpoint in Parts 4/5 works even with
   zero Apex deployed).
5. If more than one concrete class implements the same interface → the request
   **fails** with a discovery error. Only ever have one active
   implementor per interface. If you need to swap implementations, delete/deactivate
   the old one before deploying the new one.

This means: to extend behavior, you only ever need to **write and deploy one
Apex class per verb you want to customize** — nothing else in the platform
needs to change.

## 3.10 Permissions on your Apex extension classes

Every `comms_apex_ext.*` interface is guarded so that it is only invocable in
orgs that already pass the base TMF access check from §1.1 (i.e. have the
`CommsCloud` or `CommsCloudTMFAPI` org permission), and has a minimum API
version of `260` (`262` for the TroubleTicket family). This means you do not
need to grant any additional permission specifically for the extensibility
classes themselves.

## 3.11 Deploying your extensibility Apex class to the org

**Before deploying, confirm both:** (a) the user explicitly wants you to
deploy now (not just that the code looks correct), and (b) whether an existing
class already implements the target interface — if so, get explicit
confirmation to override/deactivate it. See the mandatory gate steps 6 and 7 at
the top of this skill.

**Also re-confirm the org meets the v67+ prerequisite** from the mandatory gate
before deploying — if the org's latest supported API version (§1.3) is below
`67.0`, extensibility will not work; stop and tell the user rather than
deploying.

**API version floor for extensibility Apex: `67.0` minimum.** Every
extensibility class's `apiVersion` (in its `.cls-meta.xml`, or in any
Metadata/Tooling API call used to deploy it) must be set to **`67.0` or
higher** — never lower. This applies only to the Apex class's own API version;
it does not change the TMF resource version segments (`v5`/`v4`) or the
outer Connect API version used when *calling* the endpoints in Parts 4/5.

Your extensibility class is deployed **straight into the target Salesforce org**
— it is ordinary customer-facing Apex, not part of this Bazel repo, and it does
not go through any Bazel build/CI pipeline. **Prefer the API-based deploys
(Option A, then Option B); fall back to the Setup UI (Option C) only if neither
API deploy is available or both fail.** Use the org's authenticated `Bearer`
token (Part 1) on every REST call below, and substitute `vXX.0` with the org's
**latest** supported API version discovered in §1.3 (the same version used for
every other call in this skill):

**Option A (preferred) — Tooling API, for a scripted single-class create/update:** POST the class to the Tooling API's `ApexClass` sobject endpoint. The `Body` is the full class source and `ApiVersion` must be `67.0` or higher (per the floor above):

```text
POST https://<MyDomainName>.my.salesforce.com/services/data/vXX.0/tooling/sobjects/ApexClass
Authorization: Bearer <access_token>
Content-Type: application/json

{ "Body": "<full Apex class source>", "ApiVersion": 67.0, "Status": "Active" }
```

To **replace** an existing class, you cannot directly `PATCH` an `ApexClass` in production-like orgs — instead use the Tooling API `MetadataContainer` + `ApexClassMember` + `ContainerAsyncRequest` deploy sequence, or use Option B. A `200`/`201` returning the new record `Id` means the compile succeeded; a compile error comes back as a `400` with the error body — report it and offer to fix.

**Option B — Metadata REST API deploy, for a scripted multi-component or replace-in-place deploy (CI, admin scripts):** package the class + its `.cls-meta.xml` (with `<apiVersion>67.0</apiVersion>` or higher) and a `package.xml` into a base64-encoded zip and POST it to the Metadata REST `deployRequest` endpoint:

```text
POST https://<MyDomainName>.my.salesforce.com/services/data/vXX.0/metadata/deployRequest
Authorization: Bearer <access_token>
Content-Type: application/json

{ "deployOptions": { "singlePackage": true }, "file": "<base64-encoded zip>" }
```

Poll `GET /services/data/vXX.0/metadata/deployRequest/<id>?includeDetails=true` until `deployResult.status` is `Succeeded` (or `Failed`, with component errors in the details). The `.cls-meta.xml` sets the class's own `apiVersion` (must be `67.0`+):
```xml
<?xml version="1.0" encoding="UTF-8"?>
<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <status>Active</status>
</ApexClass>
```

**Option C (last resort) — Setup UI, only when no API-based deploy is available (no scripted/token access) or both API options above have failed:**

1. In the target org, go to **Setup → (Quick Find) Apex Classes**.
2. Click **New**.
3. Paste the full class body (the exact code shown to and confirmed by the user in step 2/3 of the workflow above).
4. Click **Save**. Any compile errors are shown inline — report them back to the user and offer to fix before retrying.
5. The class is active immediately; no separate activation step, and no Java/Bazel-side change is needed for it to take effect — the framework discovers it automatically (§3.9) on the very next API call.

After any of these, always confirm the deployment actually changed behavior by re-calling the relevant endpoint from §4.4/§5.4 and comparing the response to what was expected from the new Apex logic — a successful deploy does not by itself prove the customization is wired correctly (e.g. wrong interface name, or more than one class implementing the same interface per §3.9 rule 5, would deploy cleanly but fail or no-op at request time).

---

# Part 4 — TMF621 Trouble Ticket Management (API-specific)

## 4.1 Endpoint reference (complete)

TMF resource version segment: **`v5`** (this is the only version wired to a live handler; earlier `v4`/legacy paths have no handler mapping and will error).

| # | Method | Path | Purpose | Query / body params |
|---|---|---|---|---|
| 1 | POST | `/connect/comms/troubleticket/v5/troubleticket` | Create a new trouble ticket | Body = TroubleTicket JSON (§4.2) |
| 2 | GET | `/connect/comms/troubleticket/v5/troubleticket` | List trouble tickets (paginated) | `offset` (int), `pageLimit` (int), `fields` (comma list), `sort` (string, e.g. `name`, `-name`), `pageinfo` (bool — return `totalPageSize`/`currentPage`), plus any dynamic filter query params. Pagination bounds/defaults: §2.2. |
| 3 | GET | `/connect/comms/troubleticket/v5/troubleticket/{id}` | Retrieve a single trouble ticket | `fields` (comma list to limit returned fields) |
| 4 | PATCH | `/connect/comms/troubleticket/v5/troubleticket/{id}` | Partially update a trouble ticket | Body = partial TroubleTicket JSON — only fields present are updated |
| 5 | DELETE | `/connect/comms/troubleticket/v5/troubleticket/{id}` | Delete a trouble ticket | none |
| 6 | GET | `/connect/comms/troubleticket/v5/troubleticket/{id}/{subResource}` | Paginate a child collection of one ticket (TMF621 §4.6 nested-resource pattern) | `offset`, `pageLimit`, `pageinfo`; `{subResource}` = one of the 8 values in §4.3 |

**`{id}` is the `CaseNumber`, not the raw Salesforce `Case` Id.** For endpoints
3–6 the path parameter is the human-readable ticket number (e.g. `00001002`),
which the GET/PATCH/DELETE handlers resolve to the internal Salesforce Id via a
`CaseNumber` lookup. Passing a raw `500…` `Case` Id in the URL will not match.

(Every request always runs through the extensible pipeline — see §2.1.)

## 4.2 Request/response payload shape (TroubleTicket)

**Request body fields (all optional unless required by validators — see §3.6):**

| Field | Type | Notes |
|---|---|---|
| `name` | string | Ticket subject/name |
| `description` | string | Free text |
| `status` | string | e.g. `New`, `InProgress`, `Resolved`, `Closed` — maps to Case Status |
| `ticketType` | string | TMF ticket type |
| `priority` | string | e.g. `High`/`Medium`/`Low` |
| `severity` | string | Comes from `CaseTroubleTicket.Severity` extension field, not `Case` directly. On POST, the `CaseTroubleTicket` extension record (which backs `severity`, `externalIdentifier`, `requestedResolutionDate`, `expectedResolutionDate`) is created **only if `severity` is set**; if `severity` is omitted, those other extension fields are dropped even when supplied |
| `channel` | object | On create, only `channel.name` is read and written to `Case.Origin`; any `channel.id`/`referredType` sent in the body is ignored |
| `expectedResolutionDate` | ISO date string | |
| `requestedResolutionDate` | ISO date string | |
| `relatedParty` | wrapper: `{ "list": [ { "partyOrPartyRole": { "id": "...", "referredType": "Account"\|"Contact" } } ] }` | Related Account/Contact references — but `Case` has only one `AccountId` and one `ContactId`, so at most one Account and one Contact persist |
| `relatedEntity` | wrapper: `{ "list": [ { "entity": { "id": "...", "referredType": "Asset" } } ] }` | Related Asset references — `Case` has only one `AssetId`, so at most one Asset persists |
| `note` | wrapper: `{ "list": [ { "text": "..." } ] }` | Notes to attach — each becomes a `CaseComment` (`text` → `CommentBody`) |
| `attachment` | wrapper: `{ "list": [ { "url": "...", "name": "...", "description": "..." } ] }` | Files to attach — each creates a `ContentVersion` + `ContentDocumentLink` |
| `troubleTicketRelationship` | wrapper: `{ "list": [ { "id": "..." } ] }` | Parent-ticket link — **only the first list entry** is used (its `id` → `Case.ParentId`) |
| `externalIdentifier` | wrapper: `{ "list": [ { "id": "..." } ] }` | External system ID — **only the first list entry** is used (its `id` → `CaseTroubleTicket.ExternalId`) |

**Example POST body:**

```json
{
  "name": "VoIP call drops",
  "description": "Customer reports repeated dropped calls on VoIP line",
  "status": "New",
  "ticketType": "Service Issue",
  "priority": "High",
  "severity": "Critical",
  "relatedParty": {
    "list": [
      { "partyOrPartyRole": { "id": "001xx000003GYrsAAG", "referredType": "Account" } }
    ]
  },
  "relatedEntity": {
    "list": [
      { "entity": { "id": "02ixx0000004CvzAAE", "referredType": "Asset" } }
    ]
  }
}
```

**Response body fields** — superset of the
request fields, plus: `id`, `href`, `creationDate`, `lastUpdate`,
`statusChangeDate`, `resolutionDate`, `statusChangeHistory` (list),
`updatedPayload` (only present if Apex extensibility overwrote the response —
see §3.3). List endpoints wrap results as
`{ "recordList": [ ... ], "totalPageSize": N, "currentPage": N }`.

**Response quirks to be aware of:**
- `id`, `@type`, and `href` are **always** returned, even when a `fields=`
  filter is supplied that omits them — they are hard-coded as mandatory.
- `channel.id` is a **hard-coded literal `"1"`** in every response — it is not a
  real Salesforce Id. Only `channel.name` (from `Case.Origin`) carries real data.
- Note `author` is the raw Salesforce **`CreatedById`** (a user Id), not a
  display name.
- Attachment `mimeType` is a **hard-coded literal string `"MimeType"`**, not the
  real file MIME type — do not rely on it.
- `statusChangeHistory` is **read-only**: it is derived from `Case.Histories`
  filtered to `Field == 'Status'`, each entry has `@type == "StatusChange"`, and
  it cannot be set via POST/PATCH.

## 4.3 Sub-resource pagination (endpoint #6)

`GET /connect/comms/troubleticket/v5/troubleticket/{id}/{subResource}` implements
TMF621 §4.6's nested-collection pattern. Supported built-in `{subResource}` values
(case-insensitive in the URL, matched lowercase internally):

| `{subResource}` value | Backing relationship | Maps to |
|---|---|---|
| `note` | `Case.CaseComments` | `CaseComment` |
| `attachment` | `Case.ContentDocumentLinks` | `ContentDocumentLink` |
| `statuschangehistory` | `Case.Histories` | `CaseHistory` |
| `relatedentity` | `Asset` reference | `Asset` |
| `troubleticketrelationship` | `Case.Parent` | Parent `Case` |
| `relatedparty` | Combined Account + Contact references | (special-cased, not a plain relationship) |
| `channel` | `Case.Origin` | (special-cased scalar field; `channel.id` is always the literal `"1"`, `channel.name` = `Origin`) |
| `externalidentifier` | `CaseTroubleTicket` | (requires an auxiliary query) |

Response shape matches the list endpoint: `{ "recordList": [...], "totalPageSize": N, "currentPage": N }`.
Apex extensibility (via `transformRequest`, see Part 3) can register **additional,
completely custom sub-resource names** at runtime that aren't in this table —
see §3.7.

## 4.4 API routes — TMF621, zero customization

Call these directly against `https://<your-instance>.my.salesforce.com/services/data/v<API_VERSION>.0<path>` per Part 1. No Apex required for any of these.

| Purpose | Method | Path | Body |
|---|---|---|---|
| List (first page, 10 per page) | GET | `/connect/comms/troubleticket/v5/troubleticket?offset=0&pageLimit=10&pageinfo=true` | — |
| Create | POST | `/connect/comms/troubleticket/v5/troubleticket` | `{"name":"VoIP call drops","description":"Repeated drops","status":"New","priority":"High"}` |
| Retrieve by id | GET | `/connect/comms/troubleticket/v5/troubleticket/00001002` | — |
| Partial update | PATCH | `/connect/comms/troubleticket/v5/troubleticket/00001002` | `{"status":"Resolved"}` |
| Delete | DELETE | `/connect/comms/troubleticket/v5/troubleticket/00001002` | — |
| Sub-resource: paginate notes on a ticket | GET | `/connect/comms/troubleticket/v5/troubleticket/00001002/note?offset=0&pageLimit=5` | — |

(`{id}` in these routes is the `CaseNumber`, e.g. `00001002` — see §4.1.)

**Troubleshooting a failing GET:** if a TMF621 GET (list, retrieve-by-id, or a
sub-resource page) fails, first **show the user the actual error text from the
response body verbatim** — do not paraphrase or guess at the cause. Then, if the
failure looks like an access/field error, ask the user to **enable FLS
read/edit on the calling user's profile or permission set for all `Case` fields**
(this API is a Connect resource, so ordinary field-level security applies on top
of the TMF access check in §1.1 — a field the caller can't read will break the
underlying query). Confirm the FLS change and re-run the same route before
investigating anything else.

## 4.5 Filtering and sorting fields — TMF621

See §2.3 for how filtering/sorting works generically. The named TMF-field
mapping below — these TMF names work for filtering, sorting, and `fields=`
selection; any other raw Salesforce `Case` field name (e.g. `Origin`,
`AccountId`, `ClosedDate`) also works for filtering/sorting even though it has no
TMF alias (filtering allows any valid Salesforce field, not just the aliases
below).

**If a user wants to filter by a field not in the table below, follow the
decision flow in §2.3.1** (confirm it's on `Case` → raw param, no extensibility;
custom name/related object → extensibility with a mapping; not on the entity →
say it can't be done). And note the empty-result gotcha from §2.3: a filter on a
non-existent field returns an **empty list, not an error**.

**Supported filter fields (TMF name → Salesforce field):**

| TMF name | Salesforce field |
|---|---|
| `name` | `Subject` |
| `id` | `CaseNumber` |
| `description` | `Description` |
| `status` | `Status` |
| `tickettype` | `Type` |
| `priority` | `Priority` |

Plus any raw Salesforce `Case` field name passed directly as a query param.

**Not supported for filtering:**
- `t` — a Workbench artifact param, explicitly stripped.
- Any filter with a `null` field name or `null` value is silently dropped.

**Supported sort fields (`sort=` query param, minVersion 264):**
- The same flat mapping as filtering: `name`, `id`, `description`, `status`,
  `tickettype`, `priority`, plus any raw Salesforce `Case` field name.
- Nested (dotted) 1:1-relationship sort paths, explicitly whitelisted:

  | TMF dotted sort path | Salesforce path |
  |---|---|
  | `relatedEntity.name` | `Asset.Name` |
  | `troubleTicketRelationship.id` | `Parent.CaseNumber` |
  | `troubleTicketRelationship.name` | `Parent.Subject` |

**Not supported for sorting:** multi-record/child connections —
`note`, `attachment`, `statusChangeHistory` — since these are not sortable via
the parent list.

### Full TMF621 field mapping reference — use this when writing extensibility hooks

Primary backing SObject is `Case` (+ `CaseTroubleTicket` for `severity`). Use
these mappings inside `transformRequest`/`customiseGraphQLQuery`/`handlePostOperation`
when you need to translate between a TMF field/sub-resource name and the
underlying Salesforce field, or vice versa.

**1. Flat TMF name → Salesforce field (filtering, sorting, `fields=`):**

| TMF field | Salesforce field |
|---|---|
| `name` | `Subject` |
| `id` | `CaseNumber` |
| `description` | `Description` |
| `status` | `Status` |
| `tickettype` | `Type` |
| `priority` | `Priority` |

**2. `severity` — special case, not in the flat mapping table (table 1):**

| TMF field | Salesforce entity.field |
|---|---|
| `severity` | `CaseTroubleTicket.Severity` — fetched via an auxiliary GraphQL query, not from `Case` directly |

**3. TMF sub-resource name → identifier → backing relationship:**

| TMF sub-resource | Identifier | Backing relationship |
|---|---|---|
| `channel` | `channel` | `Case.Origin` (scalar) |
| `attachment` | `attachment` | `Case.ContentDocumentLinks` |
| `note` | `note` | `Case.CaseComments` |
| `relatedEntity` | `relatedEntity` | `Asset` reference |
| `relatedParty` | `relatedParty` | Account + Contact references (special-cased) |
| `troubleTicketRelationship` | `troubleTicketRelationship` | `Case.Parent` |
| `externalIdentifier` | `externalIdentifier` | `CaseTroubleTicket` (auxiliary query) |
| `statusChangeHistory` | `statusChangeHistory` | `Case.Histories` |

**4. Dotted sort path → Salesforce relationship path:**

| TMF dotted path | Salesforce path |
|---|---|
| `relatedentity.name` | `Asset.Name` |
| `troubleticketrelationship.id` | `Parent.CaseNumber` |
| `troubleticketrelationship.name` | `Parent.Subject` |

**5. Salesforce fields returned when the caller omits `fields=`:**

`Subject`, `Id`, `Description`, `Status`, `Type`, `Priority`, `Origin`,
`AccountId`, `ContactId`, `CaseNumber`, `CreatedDate`, `LastModifiedDate`,
`ClosedDate`, `ParentId`, `AssetId`.

Any raw Salesforce `Case` field not listed in table 1 also works for
filtering/sorting/`fields=` — these maps are TMF-friendly aliases, not a
restriction (§2.3).

## 4.6 PATCH update semantics — TMF621

PATCH is partial: **a field omitted from the request body is left unchanged.**
Beyond that, per-field behavior differs:

| TMF field | Salesforce target | PATCH behavior |
|---|---|---|
| `name`, `description`, `status`, `ticketType`, `priority` | `Case.Subject`/`Description`/`Status`/`Type`/`Priority` | Set to the new value if present. |
| `channel` | `Case.Origin` | Set to `channel.name` if `channel` present and `name` non-empty. |
| `relatedParty` | `Case.AccountId`, `Case.ContactId` | **Replace.** First Account in list → `AccountId`, first Contact → `ContactId`. Empty list `[]` → **clears both to null**. Omitted → no change. |
| `relatedEntity` | `Case.AssetId` | **Replace.** First Asset → `AssetId`. Empty list `[]` → **clears to null**. Omitted → no change. |
| `troubleTicketRelationship` | `Case.ParentId` | First item `id` → `ParentId` when list is non-empty. |
| `note` | `CaseComment` | **Append-only.** Each entry with non-empty `text` creates a new `CaseComment`; existing notes are never removed. Notes are always created via SOQL, not GraphQL. |
| `attachment` | `ContentVersion` + `ContentDocumentLink` | **Append-only.** Each entry with non-empty `url` creates a new attachment; existing attachments are never removed. |
| `severity`, `externalIdentifier`, `requestedResolutionDate`, `expectedResolutionDate` | `CaseTroubleTicket` extension | **Update-or-create.** If a `CaseTroubleTicket` already exists for the Case → update it; otherwise create one. Dates are converted to ISO-8601 DateTime. |

The `{id}` in the PATCH URL is the `CaseNumber`, resolved to the Salesforce Case
Id before the mutation runs (§4.1).

---

# Part 5 — TMF629 Customer Management (API-specific)

## 5.1 Endpoint reference (complete)

TMF resource version segment: **`v4`** — this is the only version wired to the current extensible handler path for every verb below. (A `v6` segment exists in the handler routing table for GET, but only keyed to the deprecated, non-extensible legacy resource capped at Salesforce API version 258, not to the current extensible resource — it is not covered by any functional test and should not be used. Always use `v4`.)

| # | Method | Path | Purpose | Query / body params |
|---|---|---|---|---|
| 1 | POST | `/connect/comms/customermanagement/v4/customer` | Create a customer (creates an `Account`, and optionally a related `Contact` as `engagedParty`) | Body = Customer JSON (§5.2) |
| 2 | GET | `/connect/comms/customermanagement/v4/customer` | List customers (paginated) | `offset`, `pageLimit`, `fields`, `sort`, `pageinfo`, plus dynamic filter query params. Pagination bounds/defaults: §2.2. |
| 3 | GET | `/connect/comms/customermanagement/v4/customer/{id}` | Retrieve a single customer by `Account` Id | `fields` |
| 4 | PATCH | `/connect/comms/customermanagement/v4/customer/{id}` | Partially update a customer | Body = partial Customer JSON |
| 5 | DELETE | `/connect/comms/customermanagement/v4/customer/{id}` | Delete a customer (`Account`) | none |
| 6 | GET | `/connect/comms/customermanagement/v4/customer/{id}/{subResource}` | Paginate a child collection (TMF630 §4.6 nested-resource pattern — TMF629 borrows TMF630's generic customer sub-resource convention) | `offset`, `pageLimit`, `pageinfo`; `{subResource}` = one of the 3 values in §5.3 |

(Every request always runs through the extensible pipeline — see §2.1.)

## 5.2 Request/response payload shape (Customer)

**Request body fields:**

| Field | Type | Notes |
|---|---|---|
| `name` | string | Customer/Account name |
| `status` | string | Account status |
| `type` | string | Customer type |
| `engagedParty` | object: `{ "referredType": "Contact"\|"Individual", "name": "...", "id": null }` | The primary contact person. **Mandatory on POST** (POST requires both `name` and `engagedParty`); the object itself must carry a `name` or an `id`. On POST **without** `id`, a new `Contact` is created from `name` → `Contact.LastName`; on POST **with** `id`, the existing `Contact` is linked/updated. |
| `contactMedium` | wrapper: `{ "list": [ { "mediumType": "...", "characteristic": { ... } } ] }` | Phone/email/fax contact points. **Only `Email`, `Phone`, `Fax` mediumTypes are honored** — any other value is silently ignored. If the **same mediumType appears more than once**, only one value persists (backed by a map keyed on the Salesforce field — last write wins). Each entry needs a non-blank `mediumType` and `characteristic` or the request fails (`contactMediumValidation`). |
| `account` | wrapper: `{ "list": [ { "id": "...", "name": "..." } ] }` | Related/child account references. Each entry needs **both `id` and `name`** (`accountValidation`), and every referenced account **must already exist** — matched via `Id CONTAINS` + `Name CONTAINS` against existing `Account`s; any that don't match fail the request with `ACCOUNT_NOT_PRESENT`. |

**Example POST body:**

```json
{
  "name": "Sample",
  "type": "Enterprise",
  "engagedParty": {
    "referredType": "Contact",
    "name": "Sean Forbes",
    "id": null
  }
}
```

**Response body fields**: `id`, `href`,
`type`, `name`, `agreement` (list of related `Contract`s), `account` (list of
related child `Account`s), `engagedParty` (single Account-Contact relation
object), `contactMedium` (list), `updatedPayload` (present only if Apex
extensibility overwrote the response — see §3.3). The `engagedParty.role` in the
response defaults to the literal `"Individual"` when there is no
`AccountContactRelation` role to draw from.

## 5.3 Sub-resource pagination (endpoint #6)

`GET /connect/comms/customermanagement/v4/customer/{id}/{subResource}`. Built-in values:

| `{subResource}` value | Backing relationship | Maps to |
|---|---|---|
| `account` | `Account.ChildAccounts` | Child `Account` |
| `engagedparty` (alias: `contact`) | `Account.Contacts` | `Contact` |
| `agreement` | `Account.Contracts` | `Contract` |

Same response shape as the list endpoint. As with TMF621, Apex extensibility
can register additional custom sub-resource names at runtime (§3.7) — for
example, exposing `Account.Opportunities` as a brand-new `opportunities`
sub-resource this way, with zero Java changes.

## 5.4 API routes — TMF629, zero customization

Call these directly against `https://<your-instance>.my.salesforce.com/services/data/v<API_VERSION>.0<path>` per Part 1. No Apex required for any of these.

| Purpose | Method | Path | Body |
|---|---|---|---|
| List | GET | `/connect/comms/customermanagement/v4/customer?offset=0&pageLimit=10&pageinfo=true` | — |
| Create | POST | `/connect/comms/customermanagement/v4/customer` | `{"name":"Sample","type":"Enterprise","engagedParty":{"referredType":"Contact","name":"Sean Forbes","id":null}}` |
| Retrieve by id | GET | `/connect/comms/customermanagement/v4/customer/001xx000003GYrsAAG` | — |
| Partial update | PATCH | `/connect/comms/customermanagement/v4/customer/001xx000003GYrsAAG` | `{"status":"Active"}` |
| Delete | DELETE | `/connect/comms/customermanagement/v4/customer/001xx000003GYrsAAG` | — |
| Sub-resource: paginate related contacts (engagedParty) | GET | `/connect/comms/customermanagement/v4/customer/001xx000003GYrsAAG/engagedparty?offset=0&pageLimit=5` | — |

## 5.5 Filtering and sorting fields — TMF629

Same mechanism as TMF621 (§2.3 / §4.5): filtering is not a fixed allow-list.
TMF629 uses the same filter field-name pass-through as TMF621 — the underlying
filter logic drops the field name straight into the `where` clause with no
allow-list check (only `t`/null skipped). The table below is the named TMF-field
mapping (TMF name → Salesforce field); any other raw Salesforce `Account` field
name also works for filtering/sorting.

**If a user wants to filter by a field not in the table below, follow the
decision flow in §2.3.1** (confirm it's on `Account` → raw param, no
extensibility; custom name/related object → extensibility with a mapping; not on
the entity → say it can't be done). Same empty-result gotcha as §2.3: a filter on
a non-existent field returns an **empty list, not an error**.

**Supported filter fields (TMF name → Salesforce field):**

| TMF name | Salesforce field |
|---|---|
| `name` | `Name` |
| `id` | `Id` |

Plus any raw Salesforce `Account` field name passed directly as a query param.

**Not supported for filtering:**
- `t` — same Workbench artifact param, explicitly stripped.
- Any filter with a `null` field name or `null` value is silently dropped.

**Supported sort fields (`sort=` query param, minVersion 264):**
- `name`, `id`, plus any raw Salesforce `Account` field name.
- One nested (dotted) sort path is whitelisted:

  | TMF dotted sort path | Salesforce path |
  |---|---|
  | `parentAccount.name` | `Parent.Name` |

**Not supported for sorting:** multi-record sub-resources — `account` (child
accounts), `agreement` (contracts), `contactMedium`, `engagedParty` — these are
GraphQL connections and, like TMF621's `note`/`attachment`/`statusChangeHistory`,
are not sortable via the parent list.

### Full TMF629 field mapping reference — use this when writing extensibility hooks

Primary backing SObject is `Account`. Use these mappings inside
`transformRequest`/`customiseGraphQLQuery`/`handlePostOperation` when you need to
translate between a TMF field/sub-resource name and the underlying Salesforce
field, or vice versa.

**1. Flat TMF name → Salesforce field (filtering, sorting, `fields=`):**

| TMF field | Salesforce field |
|---|---|
| `name` | `Name` |
| `id` | `Id` |

**2. TMF sub-resource name → identifier:**

| TMF sub-resource | Identifier |
|---|---|
| `account` | `account` |
| `agreement` | `agreement` |
| `contactmedium` | `contactmedium` |
| `engagedparty` | `engagedparty` |

**3. Dotted sort path → Salesforce relationship path:**

| TMF dotted path | Salesforce path |
|---|---|
| `parentaccount.name` | `Parent.Name` |

**4. Salesforce fields returned when caller omits `fields=`:**

`Name`, `Id`, `ParentId`.

**5. TMF sub-resource → GraphQL relationship → backing SObject → parent lookup field, used for `GET .../{id}/{subResource}`:**

| TMF sub-resource | GraphQL relationship (alias) | Backing SObject | Parent lookup field |
|---|---|---|---|
| `account` | `ChildAccounts` (`childAccounts`) | `Account` | `ParentId` |
| `engagedparty` (alias: `contact`) | `Contacts` (`engagedParty`) | `Contact` | `AccountId` |
| `agreement` | `Contracts` (`agreements`) | `Contract` | `AccountId` |

**6. Parent-side relationship node (feeds the `account` array field alongside `ChildAccounts`):**

| GraphQL relationship (alias) | Backing SObject | Purpose |
|---|---|---|
| `Parent` (`parentAccount`) | `Account` | Direct (non-connection) relationship; parent + child records both populate the TMF `account` array field |

**7. `contactmedium` and `engagedparty` share the same underlying GraphQL node:**

Both pull from the same `Contacts` relationship (alias `engagedParty`), just
shaped differently on the way out:
- If `contactmedium` was requested → contact records convert into the TMF
  `contactMedium` field.
- If `engagedparty` was requested → the first contact record converts into the
  TMF `engagedParty` field.
- Both can be requested together — they populate independently from the same
  underlying `Contact` rows.

**8. `contactMedium.mediumType` → Salesforce field (used when constructing the mutation payload on POST):**

| TMF `mediumType` | Salesforce field |
|---|---|
| `PHONE` | `Phone` |
| `EMAIL` | `Email` |
| `FAX` | `Fax` |

**9. `account` wrapper (POST request body) — construction/match logic:**

| TMF field | Salesforce entity | Match logic |
|---|---|---|
| `account.list[].id` / `.name` | `Account` | Matched via `Id CONTAINS` + `Name CONTAINS` filters against existing `Account` records — every referenced account must already exist or the request fails with `ACCOUNT_NOT_PRESENT` |

Any raw Salesforce `Account` field not listed in table 1 also works for
filtering/sorting/`fields=` — these maps are TMF-friendly aliases, not a
restriction (§2.3).

**Sub-resource pagination — no `sort=`/`fields=` support:** `GET .../{id}/{subResource}`
only accepts `offset`, `pageLimit`, `pageinfo` — there is no caller-facing sort
or field-selection parameter on this endpoint. Default order is unsorted/Id-order unless an Apex
`customiseGraphQLQuery` hook injects a `where`/`orderBy` argument onto the
specific sub-resource's GraphQL node (matched by alias, e.g. `childAccounts`,
`agreements`, `engagedParty`) — this is the *only* way to sort or filter a
sub-resource collection.

## 5.6 PATCH update semantics — TMF629

PATCH is partial: a field omitted from the body is left unchanged. Patchable
fields and their behavior:

| TMF field | Salesforce target | PATCH behavior |
|---|---|---|
| `name` | `Account.Name` | Set to the new value if present. |
| `account` | `Account` (child links) | Each entry needs `id`+`name` and must match an existing Account (same `CONTAINS` rule / `ACCOUNT_NOT_PRESENT` failure as POST). |
| `contactMedium` | `Contact.Email`/`Phone`/`Fax` | Applied to the engaged-party contact. Only `Email`/`Phone`/`Fax` honored; a `characteristic: {}` for a mediumType effectively clears that medium. |
| `engagedParty` | `Contact` link | **Supported on PATCH**, but **`engagedParty.id` is required**. The currently-linked contact(s) are delinked when the new `id` differs, then the contact identified by `id` is linked/updated. |

**Note:** `engagedParty` **is supported on PATCH** as described above, despite
older documentation that may suggest otherwise.

---

# Part 6 — End-to-end execution checklist

1. **Confirm you hold a valid OAuth/session bearer token for the target org.** Check that the token is live and not expired. If you already have one, skip step 2 and go straight to step 3.
2. **If not, follow the bundled reference sample `external-client-app-setup` in the skill's references bundle, per §1.2.** In short: first list the org's existing External Client Apps via the Metadata API and reuse a suitable one; only create a new app if none exists — using the defaults unless the user asks to customize, applying the default configuration incl. the Client Credentials run-as user, having the user reveal and store the Consumer Key/Secret in the approved secret manager, then obtaining an access token via a standard OAuth 2.0 flow (web-server/user-agent for interactive use, Client Credentials with the run-as user, or JWT bearer via `POST /services/oauth2/token` for headless/CI). Do not proceed to step 3 until you hold a live token for the target org.
3. Confirm your org has `CommsCloud` or `CommsCloudTMFAPI` org permission enabled (ask a Salesforce admin, or check Setup → Feature Settings if you have access).
4. **Discover the org's latest supported Salesforce API version.** Call `GET https://<your-instance>.my.salesforce.com/services/data/` with the `Bearer` token and take the highest `version` from the response; use it as the `v<API_VERSION>.0` segment in the base URL (per §1.3). A `200` confirms auth and the correct version to use; never hard-code a version the org may not report.
5. Pick your TMF resource version segment: TMF621 → `v5`; TMF629 → `v4` (this is separate from the Salesforce API version from step 4).
6. **Verify the endpoint is actually accessible in the org** before doing any real work: call the plain list/GET endpoint (§4.4 #1 or §5.4 #1) with `pageLimit=1` and no filters. A `200` with a (possibly empty) `recordList` confirms the org permission (§1.1), the access check, and FLS/sharing all line up. A `403`/`INSUFFICIENT_ACCESS` means the org permission (`CommsCloud`/`CommsCloudTMFAPI`) isn't enabled or the user lacks object access — stop and fix that before proceeding. A `404` means the wrong TMF version segment was used (double-check step 5).
7. Call the endpoint route directly using the tables in §4.4/§5.4 — this works out of the box, zero Apex needed.
8. **Only if you explicitly want custom behavior** (extra fields, filtering, validation, response reshaping) — per the mandatory gate at the top of this skill: **first confirm the org's latest supported API version (step 4) is `67.0` or above — extensibility does not work below `67.0`; if the org is below it, stop and tell the user rather than writing any Apex.** Then confirm you actually want an extensibility scenario, pick the one interface from §3.1 matching your verb+API, write one Apex class implementing every method on it (no-op the ones you don't need per §3.2's "No-op return" column), show it and get it confirmed, deploy it per §3.11, and call the same endpoint again — your customization takes effect automatically with no further wiring.

<!-- skill-validate: ignore-start -->
<!-- codey:operations start -->
## Operations Reference

Operations this skill uses — routing and dependency reference.

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `tmf-list-troubletickets` | read | — | `GET /services/data/v{V}/connect/comms/troubleticket/v5/troubleticket` | — |
| `tmf-get-troubleticket` | read | — | `GET /services/data/v{V}/connect/comms/troubleticket/v5/troubleticket/{caseNumber}` | `tmf-list-troubletickets` |
| `tmf-get-troubleticket-subresource` | read | — | `GET /services/data/v{V}/connect/comms/troubleticket/v5/troubleticket/{caseId}/{subresource}` | `tmf-resolve-case-id` |
| `tmf-resolve-case-id` | read | — | `POST /services/data/v{V}/graphql` | — |
| `tmf-create-troubleticket` | write | — | `POST /services/data/v{V}/connect/comms/troubleticket/v5/troubleticket` | — |
| `tmf-update-troubleticket` | write | — | `PATCH /services/data/v{V}/connect/comms/troubleticket/v5/troubleticket/{caseNumber}` | `tmf-get-troubleticket` |
| `tmf-delete-troubleticket` | write | — | `DELETE /services/data/v{V}/connect/comms/troubleticket/v5/troubleticket/{caseNumber}` | — |
| `cust-list-customers` | read | — | `GET /services/data/v{V}/connect/comms/customermanagement/v4/customer` | — |
| `cust-create-customer` | write | — | `POST /services/data/v{V}/connect/comms/customermanagement/v4/customer` | — |
| `cust-get-customer` | read | — | `GET /services/data/v{V}/connect/comms/customermanagement/v4/customer/{accountId}` | `cust-list-customers` |
| `cust-patch-customer` | write | — | `PATCH /services/data/v{V}/connect/comms/customermanagement/v4/customer/{accountId}` | `cust-get-customer` |
| `cust-get-customer-subresource` | read | — | `GET /services/data/v{V}/connect/comms/customermanagement/v4/customer/{accountId}/{subresource}` | `cust-list-customers` |
| `cust-delete-customer` | write | — | `DELETE /services/data/v{V}/connect/comms/customermanagement/v4/customer/{accountId}` | — |
| `apex-deploy-toolingapi` | write | — | `POST /services/data/v{V}/tooling/sobjects/ApexClass` | — |
| `apex-deploy-metadataapi` | write | — | `/headless/metadata` | — |
| `apex-conflict-check` | — | — | — | — |
<!-- codey:operations end -->
<!-- skill-validate: ignore-end -->
