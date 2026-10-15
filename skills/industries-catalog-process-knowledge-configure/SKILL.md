---
name: industries-catalog-process-knowledge-configure
description: "Use this skill when users want to cHILD of the create-unified-catalog-service-process orchestrator — one configuration pass over a service process that ALREADY EXISTS. Trigger when users mention configure, unified, catalog, service, process, knowledge, automation, connect, api, service-automation-connect-api."
metadata:
  version: "1.0"
  accessCheck: "IndustriesEpc.orgHasUnifiedCatalog"
---

# Managing Configure Unified Catalog Service Process Knowledge

## When to Use This Skill

CHILD of the create-unified-catalog-service-process orchestrator — one configuration pass over a service process that ALREADY EXISTS. Run standalone against an existing process (supply its catalogItemId), or as the phase that orchestrator routes to; for a NEW end-to-end process start at create-unified-catalog-service-process, which asks the creation fork FIRST.
Use this when an admin wants to add (or remove) the Knowledge articles shown on a service process that ALREADY EXISTS — e.g. "attach the reimbursement-policy article to this service process". DONE when the chosen articles read back in associatedArticles on the verify GET with the anchor still intact. Org-gated on Unified Catalog. This attaches EXISTING published articles; it does not author or publish an article. associatedArticles is a DELTA list: send ONLY the change — a new article as operationType:"Create", a removal as operationType:"Delete" carrying that article's association id — never re-send the already-attached ones (re-sending an attached article as "Create" is rejected 400 "already attached"). DETACH-TRAP handling and the delta-list rules are in agent_guidance and step assertions.

## Critical Constraints

**Preconditions:**

- Org must have Unified Catalog enabled.
 (check: `Unified Product Catalog enabled`)
- HARD CONSTRAINT — the service process must ALREADY EXIST and its catalogItemId (== productId) must be known before this workflow runs. The first step (resolve-catalog-item) GETs the item to confirm it exists and is usedFor=ServiceProcess before any write; a 404 there means the id is wrong or the process was never created — the process must be created first, then re-run here with its catalogItemId.
 (check: `process_exists_with_known_catalog_item_id`)
- HARD CONSTRAINT — each article to associate MUST be a real KnowledgeArticleId taken from the list step (list-knowledge-articles) for THIS org. Never guess or hand-construct an article id. Only PUBLISHED (Online) articles are listable/associable. List the eligible articles, let the user pick one or more, and bind those exact ids.
 (check: `attached_article_is_a_real_listed_id`)
- HARD CONSTRAINT — associatedArticles on patchCatalogItemGet is a DELTA list, NOT a full replacement. Send ONLY the entries that change; the articles already attached stay attached without being re-sent. To ADD an article, send just that one as operationType:"Create". To REMOVE one, send just that one as operationType:"Delete" carrying its association id (the associatedArticles[].id from resolve-catalog-item — a 1WK-prefix id; a Delete without that id is rejected). Do NOT re-send an already-attached article as "Create" — it is rejected 400 "This article is already attached to this record". (An already-attached article re-sent as "Update" does NOT error but CHURNS its association id — the 1WK id is replaced with a fresh one; the end set is unchanged but any 1WK id captured earlier goes stale. Never treat an association id as durable across a re-Update; always re-read it from a fresh GET before a Delete.) Confirm the final set on the verify GET.
 (check: `bind_sends_only_changed_articles`)
- HARD CONSTRAINT — patchCatalogItemGet overwrites the item's scalar identity: the bind MUST re-send the item's identity fields (targetObject, name, usedFor, isActive). Omitting targetObject CLEARS the anchor — it reads back absent on the next GET, not reset to a default, even after it was set at create time. The intakeForm block is ALSO a full overwrite: sending it with only {id, operationType:Update} preserves the container but WIPES the bound surface (intakeFormId + type disappear). When the item has an intake surface, the bind MUST re-send intakeForm.intakeFormId AND intakeForm.type alongside the container id, not just the id. The bind PATCH always carries the four identity fields and re-sends the FULL intakeForm (id + intakeFormId + type) when one exists; the verify GET confirms the anchor and intake surface are intact.
 (check: `bind_patch_resends_anchor_identity_fields`)

**Operational rules:**

- MUST-DO CONTRACT (read before executing — each rule is enforced by the named precondition/step; do NOT skip because the detail is further down):
  1. CONFIRM the process exists first — run resolve-catalog-item (GET) and capture its
     identity fields (name, usedFor, isActive, targetObject), its current intakeForm.id,
     and its CURRENT associatedArticles[] — each entry is {id, knowledgeArticleId}; the
     association id (1WK-prefix) is required to REMOVE that article later. A 404 means the
     catalogItemId is wrong; do NOT proceed.
     [precondition: process_exists_with_known_catalog_item_id]
  2. LIST the org's PUBLISHED (Online) Knowledge articles via list-knowledge-articles,
     present the COMPLETE set as numbered text (Title, KnowledgeArticleId), and let the
     user pick one or more. [precondition: attached_article_is_a_real_listed_id]
  3. BIND via patchCatalogItemGet sending ONLY the change — associatedArticles is a DELTA
     list, not a full replacement: send each NEWLY chosen article as operationType:"Create"
     (its knowledgeArticleId only); to REMOVE an article, send just that one as
     operationType:"Delete" carrying its association id from resolve-catalog-item. Do NOT
     re-send the already-attached articles — they stay attached, and re-sending an attached
     one as "Create" is rejected 400 "already attached".
     [precondition: bind_sends_only_changed_articles]
  4. The bind PATCH is a FULL overwrite of the ITEM's scalar identity — ALWAYS re-send
     targetObject + name + usedFor + isActive. The intakeForm block is ALSO a full overwrite:
     when the item has an intake surface, re-send the FULL block — intakeForm.id AND
     intakeForm.intakeFormId AND intakeForm.type (operationType:Update). Sending only {id}
     preserves the container but WIPES the bound surface. Omit intakeForm only
     when the item has no surface. Otherwise the anchor clears (reads back absent) and/or the intake surface
     detaches. (The identity overwrite and the associatedArticles delta are independent: the
     scalars are replaced, the article list is a delta.)
     [precondition: bind_patch_resends_anchor_identity_fields]
  5. VERIFY: GET the item and confirm associatedArticles contains the intended final set of
     knowledgeArticleIds AND targetObject is unchanged. [step: verify-articles]
- ASK MODALITY: for the article list (unbounded), list the COMPLETE set as numbered text (Title, KnowledgeArticleId, LastModifiedDate) and let the user type one or more selections; present smartly (match a named target locally; list small sets in full; narrow a large set with a typed name rather than dumping every row — the full set is already fetched). The list is a paged GraphQL query (first:2000 + pageInfo.hasNextPage/endCursor) — page through to completeness before asking. Only Online (published) articles appear; a draft/archived article will not be listed and cannot be associated until published.
TIMING: resolve → list → bind → verify. There is one write path; the add and remove semantics both flow through the associatedArticles[] delta on the bind — add sends a Create entry, remove sends a Delete entry carrying the association id.

## Verification Checklist

After every write operation, confirm the effect by re-reading state:

- After `resolve-catalog-item`, `bind-knowledge-articles`: call `verify-articles` (`GET /connect/service-automation/catalog/catalog-item/{catalogItemId}`)

## Operations Reference

Operations grouped by purpose. Use these as the building blocks for the workflows above.

### Summary

| Operation | Purpose | Status | Call | Depends on |
|-----------|---------|--------|------|------------|
| `resolve-catalog-item` | read | implemented | `GET /connect/service-automation/catalog/catalog-item/{catalogItemId}` | — |
| `list-knowledge-articles` | read | implemented | `queryKnowledgeArticles` | `resolve-catalog-item` |
| `bind-knowledge-articles` | write | implemented | `PATCH /connect/service-automation/catalog/catalog-item/{catalogItemId}` | `resolve-catalog-item`, `list-knowledge-articles` |
| `verify-articles` | verify | implemented | `GET /connect/service-automation/catalog/catalog-item/{catalogItemId}` | `resolve-catalog-item`, `bind-knowledge-articles` |

### Read operations

#### `resolve-catalog-item`

CONFIRM + CAPTURE — GET the existing service process to prove it exists and to capture the identity fields the later bind must re-send AND the CURRENT associatedArticles[]. Each associatedArticles entry is {id, knowledgeArticleId}: the id (1WK-prefix association id) is what a later Delete must carry to remove that article; the knowledgeArticleId tells you which articles are already attached so you don't try to re-add one (a re-add as "Create" is rejected 400 "already attached"). Fails fast (404) if the catalogItemId is wrong or the process was never created. Capture name, usedFor, isActive, targetObject (the anchor), the current intake surface (intakeForm.id AND intakeForm.intakeFormId + intakeForm.type — the bound Flow/OmniScript, NOT just the container id) and the current associatedArticles.


**Call:** `GET /connect/service-automation/catalog/catalog-item/{catalogItemId}`   — status: `implemented`

**Inputs:**

- `catalogItemId` *(`String`)* — The catalogItemId (== productId) of the EXISTING service process. If the user does not have it, the process must be created first before this workflow can run.

#### `list-knowledge-articles`

LIST — the org's PUBLISHED (Online) Knowledge articles via UIAPI GraphQL: Knowledge__kav filtered to PublishStatus=="Online". Present the COMPLETE set as numbered text (Title, KnowledgeArticleId, LastModifiedDate) and let the user pick one or more; page via pageInfo.endCursor (first:2000 + hasNextPage) — PRESENT smartly: if the user already NAMED the target, match it in the fetched set and show only the matches; if the set is small (≤ ~25) list it all as numbered text; if it is large, do NOT dump every row — show the most-recently-modified top slice (or ask a narrowing keyword) and invite the user to type a name to search (the full set is already fetched, so the local match stays exact). TARGETED LOOKUP: when the user has already NAMED the article, add a title predicate to the where filter — {Title: {like: "%<name>%"}}, AND-combined with the PublishStatus filter above — to fetch just the matches in ONE call instead of paging the whole list; fall back to the full paged listing only when no name was given or the filtered query returns nothing. The list is org-specific — take it from this call, never a fixed list. ID TO BIND: bind the node.KnowledgeArticleId.value (the kA0-prefix KnowledgeArticleId, the stable per-article id across versions), NOT node.Id (the per-version Knowledge__kav row id). associatedArticles.knowledgeArticleId expects the KnowledgeArticleId.


**Call:** `queryKnowledgeArticles`   — status: `implemented`

**Depends on:** `resolve-catalog-item`

### Write operations

#### `bind-knowledge-articles`

ASSOCIATE BIND — change the process's associatedArticles[] via patchCatalogItemGet. DELTA LIST: associatedArticles is a delta, not a full replacement — send ONLY the entries that change. To ADD each newly chosen article, send {knowledgeArticleId, operationType:"Create"}; to REMOVE an article, send {id: <its 1WK association id from resolve-catalog-item>, knowledgeArticleId, operationType:"Delete"}. Do NOT re-send the already-attached articles — they stay attached, and re-sending an attached one as "Create" is rejected 400 "This article is already attached to this record". A Delete without the association id is also rejected — carry the id from resolve-catalog-item.existing_associated_articles. DETACH TRAP: this PATCH is a full overwrite of the ITEM's scalar identity — it MUST also re-send the item's identity fields (targetObject, name, usedFor, isActive), sourced from resolve-catalog-item. The intakeForm block is ALSO a full overwrite: when the item has an intake surface, re-send the FULL block — intakeForm.id (container) AND intakeForm.intakeFormId (the bound Flow/OmniScript) AND intakeForm.type, all from resolve-catalog-item, with operationType:"Update". Sending only {id, operationType:Update} preserves the container but WIPES the bound surface (intakeFormId + type vanish). Omit the intakeForm block only if resolve-catalog-item returned no intake_surface_id. Omitting targetObject CLEARS the anchor (it reads back absent on the next GET, not reset to a default). (The scalar identity is replaced; the associatedArticles list is a delta — the two behave independently in the same PATCH.)


**Call:** `PATCH /connect/service-automation/catalog/catalog-item/{catalogItemId}`   — status: `implemented`

**Inputs:**

- `catalogItemId` *(`String`)* — The catalogItemId (== productId) of the process to associate the articles with.
- `associatedArticles` *(`Array`)* — The DELTA of articles to change — send ONLY changed entries, never the already-attached ones. To ADD an article: {knowledgeArticleId, operationType:"Create"}, where knowledgeArticleId is a chosen id from list-knowledge-articles.article_ids (kA0-prefix KnowledgeArticleId, never hand-constructed) that is NOT already in resolve-catalog-item.existing_article_ids. To REMOVE an article: {id, knowledgeArticleId, operationType:"Delete"}, where id is that article's association id (1WK-prefix) from resolve-catalog-item.existing_associated_articles. Re-sending an already-attached article as "Create" is rejected 400 "already attached"; a Delete missing the association id is also rejected.

  - **Source:** output of `list-knowledge-articles`, `resolve-catalog-item`
- `intakeContainerId` *(`String`)* — The existing intake container id (intakeForm.id) from resolve-catalog-item, carried forward as intakeForm.id (with operationType:"Update"). NOTE the container id alone is NOT enough — the intakeForm block is a full overwrite, so intakeSurfaceId + intakeSurfaceType below must also be re-sent or the bound surface is wiped. Omit the whole intakeForm block only when resolve-catalog-item returned no intake_surface_id.

  - **Source:** output of `resolve-catalog-item`
- `intakeSurfaceId` *(`String`)* — The bound intake surface id (intakeForm.intakeFormId — the Flow/OmniScript definition id) from resolve-catalog-item. MUST be re-sent alongside the container id: sending intakeForm with only {id} wipes the surface. Present only when the item has a surface.

  - **Source:** output of `resolve-catalog-item`
- `intakeSurfaceType` *(`String`)* — The bound intake surface type (intakeForm.type — "Flow" or "OmniScript") from resolve-catalog-item. Re-sent with intakeSurfaceId to preserve the bound surface.

  - **Source:** output of `resolve-catalog-item`
- `targetObject` *(`String`)* — The anchor object (a closed set — Case, Incident, or ServiceRequest) — re-sent on this identity-overwrite PATCH or the anchor CLEARS — it reads back absent on the next GET, not reset to a default (DETACH TRAP). Take the value from resolve-catalog-item, never a fixed assumption.

  - **Source:** output of `resolve-catalog-item`
- `name` *(`String`)* — The process name — re-sent to preserve identity on this identity-overwrite PATCH.
- `usedFor` *(`String`)* — The usedFor value (ServiceProcess) — re-sent to preserve identity.
- `isActive` *(`Boolean`)* — The isActive flag — re-sent to preserve identity.

**Depends on:** `resolve-catalog-item`, `list-knowledge-articles`

**Rollback:** To remove an article added here, re-invoke patchCatalogItemGet with that article as operationType:"Delete" carrying its association id (read it back from the bind response or a fresh GET), always re-sending the anchor identity fields AND the full intakeForm block (id + intakeFormId + type when a surface exists) — the rollback PATCH is the same full-overwrite, so anchor-only re-send would wipe the surface. Because the list is a delta, the other articles are untouched. The catalog-item resource has no DELETE method.

### Verify operations

#### `verify-articles`

Read the process back and confirm the intended articles are associated and the anchor held.


**Call:** `GET /connect/service-automation/catalog/catalog-item/{catalogItemId}`   — status: `implemented`

**Inputs:**

- `catalogItemId` *(`String`)* — The catalogItemId (== productId) of the process to verify.

**Depends on:** `resolve-catalog-item`, `bind-knowledge-articles`
