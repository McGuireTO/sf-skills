---
name: flow-end
description: "FlowEnd (End node) metadata shape — the explicit terminal node that a terminating branch's connector targets. Covers the ends[] entry fields, WHEN an explicit End is emitted (GENERATE on AUTO_LAYOUT_CANVAS at apiVersion >= 68.0) versus the implicit omit-the-connector end, the never-on-Free-Form exclusion, and the per-branch-or-shared End topology (each terminating branch may have its own End or converge on a shared End — both valid). Load when emitting or reading End nodes in a flow payload. See shared/anti-patterns.md item 38 for why a shared End does not break auto-layout and why a fault pointed directly at an End is silently dropped (advisory, not a defect)."
metadata:
  version: "1.0"
  related-skills: flow-connector, flow-node, flow-metadata-schema
---

# FlowEnd — Explicit End Node

An **End** is a terminal node: the node a terminating branch's connector points
at when the branch stops the flow. End nodes live in the top-level **`ends[]`**
array of the flow metadata (a sibling of `assignments`, `decisions`, etc. — see
`shared/flow-metadata-schema.md`). Each entry defines one End.

In a `.flow-meta.xml` each End is one `<ends>` element (plural, the same name as
the JSON key) holding `<name>`, `<locationX>` and `<locationY>`. An `<end>`
element fails the deploy with `Error parsing file: Element
{http://soap.sforce.com/2006/04/metadata}end invalid at this location in type Flow`.

An End is a `FlowNode` subclass (`FlowEnd` — see `shared/node/node.md`): it takes
`name`, optional `label`/`description`, `locationX`/`locationY`, and the optional
`group` back-reference (see [The `group` attribute](#the-group-attribute)). It has
**no connector of any kind** — nothing flows out of an End.

There are **two** ways a branch can terminate in a flow, and which one to use is
decided entirely by the rule below:

- **Explicit End** — an `ends[]` entry, targeted by one or more connectors
  (`"connector": { "targetReference": "END_ELEMENT_1" }`; several non-fault
  connectors may converge on one End — a valid shared End). **Stored in metadata.**
- **Implicit end** — the branch's last element simply omits its `connector`. The
  End is *not* serialized; the platform infers it.

---

## When to emit an explicit End (the deciding rule)

> **GENERATE, `AUTO_LAYOUT_CANVAS`, resolved `apiVersion` ≥ 68.0 → emit an
> explicit End per terminating branch.** This is the default on a 68-capable org.
> Explicit End nodes became storable metadata in API version 68.0; on such an org
> the author recipe stores ends in metadata rather than relying on the implicit
> omit-the-connector form, matching how Flow Builder itself serializes an
> auto-layout flow.

The resolved `apiVersion` is `max(apiVersionsList)` from `GET /services/data/vXX.0/flowbuilder/flow/version-info`
(currently 68) — see `recipes/author/author.md` Phase 3 step 3 and
`shared/flow-properties/flow-properties.md` § apiVersion. Emit the implicit end
(omit the connector) instead in every other case:

| Situation | Terminating branch → |
|---|---|
| GENERATE, `AUTO_LAYOUT_CANVAS`, `apiVersion` ≥ 68.0 | **explicit End** (`ends[]` entry, one connector into it) |
| GENERATE, `apiVersion` < 68.0 (org max below 68) | implicit end (omit the connector) — explicit ends are not storable |
| **Free-Form (`FREE_FORM_CANVAS`, or no `CanvasMode` PMV → opens Free-Form)** | **NEVER emit `ends[]`** — Free-Form flows do not support explicit End nodes. Omit the connector. |
| EVOLVE (edit of a retrieved flow) | **preserve the source's `ends[]` verbatim**; add explicit Ends only for the terminating branches you introduce, and only if the source is auto-layout (see § EVOLVE) |

**The rule is persistence-independent.** It applies to any flow the skill emits at
v68+ auto-layout — the flow MCP save JSON payload *and* a `.flow-meta.xml` written
to the project for a metadata deploy. A metadata deploy (e.g. `sf project deploy`)
stores the flow **verbatim**: it does not synthesize End nodes, so any missing
`ends[]` stays missing on the org and on the next retrieve. If the skill writes
metadata XML instead of calling the save endpoint, it must still author the
`<ends>` elements and point each terminating branch's connector at one.

**Free-Form is a hard exclusion.** Never generate `ends[]` for a Free-Form flow,
and never add an End when rewriting a retrieved Free-Form source. Canvas mode is
carried by the `CanvasMode` process metadata value; a flow with no `CanvasMode`
PMV opens Free-Form (see `shared/anti-patterns.md` item 37), so it is treated as
Free-Form for this rule.

**Implicit termination is NOT Free-Form.** Whether `ends[]` is stored has **no
bearing** on canvas mode — canvas mode is set *only* by the `CanvasMode` PMV.
Below 68.0 (and any time a branch terminates by omitting its connector), the flow
is **still `AUTO_LAYOUT_CANVAS`** and still emits the `CanvasMode` PMV; it just
terminates implicitly instead of storing End nodes. Do **not** reason "no `ends[]`
⇒ the flow opens in Free-Form" — that is false, and it is never a reason to drop
the `CanvasMode` PMV or to stop treating the flow as auto-layout. A sub-68
auto-layout flow with omitted connectors opens in Auto-Layout exactly like a v68+
one; the only difference is the End nodes are inferred rather than stored.

Emitting a dedicated per-branch End under this rule is **not** fabrication — it is
the v68+ auto-layout GENERATE default. The "never fabricate End elements"
guidance in `shared/anti-patterns.md` item 38 applies to the cases where an
explicit End is *not* called for (below 68.0, Free-Form, or EVOLVE preservation),
not to this default.

---

## `ends[]` entry fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `name` | string | yes | Unique dev-name; matches `[A-Za-z][A-Za-z0-9_]*`, ≤ 80 chars. Flow Builder names these `END_ELEMENT_1`, `END_ELEMENT_2`, … — follow that convention. Numbers need not be contiguous, but every End's `name` must be **unique** within the flow and is the value the terminating branch's `connector.targetReference` points at. |
| `label` | string | no | Usually omitted / `null` — Flow Builder does not label End nodes. |
| `description` | string | no | Usually omitted / `null`. |
| `locationX` | number | yes | Canvas X. Use `0` for auto-layout flows (see `shared/node/node.md`). |
| `locationY` | number | yes | Canvas Y. Use `0` for auto-layout flows. |
| `group` | string | conditional | Present only when the End sits inside a group boundary; omitted otherwise. See [The `group` attribute](#the-group-attribute). |

An End entry has **no `connector`, no `faultConnector`, and no other outgoing
field** — it is a sink. It is reached, never left.

---

## The `group` attribute

`group` is the generic FlowNode membership back-reference (`shared/node/node.md`
§ `group`): the `name` of the group container an element sits inside, present only
when the element falls within a group boundary and omitted otherwise. An End is a
FlowNode, so it carries `group` on exactly the same terms as any other element.

For a net-new flow this attribute does not arise on its own — the author recipe
does not generate group containers, so a generated End carries **no** `group`. It
shows up only when **preserving** a retrieved source (EVOLVE) that already places
an End inside a group: keep the source's `group` value verbatim, exactly as you
preserve the rest of the `ends[]` entry. Do not add, remove, or re-derive a
`group` on an End.

```jsonc
"ends": [
  { "name": "END_ELEMENT_1", "locationX": 0, "locationY": 0 },                 // no group
  { "name": "END_ELEMENT_2", "group": "Group_1", "locationX": 0, "locationY": 0 } // preserved from source
]
```

---

## Referential integrity — connectors and `ends[]` are co-emitted

An explicit End has **two halves that must be emitted together**:

1. the terminating element's `connector` (or `defaultConnector` / `nextValueConnector` / `noMoreValuesConnector`) whose `targetReference` is the End's `name`, and
2. the matching entry in the top-level `ends[]` array with that exact `name`.

**Emit both or neither.** If you decide a branch terminates at an explicit End
(the v68+ auto-layout default), you MUST both point its connector at
`END_ELEMENT_n` **and** add `{ "name": "END_ELEMENT_n", ... }` to `ends[]`. A
connector that targets an End with no matching `ends[]` entry fails the save with
**"`<EndName>` not found"** (e.g. `End_Main not found`) — the same
lookup-by-dev-name failure as a dangling connector (`shared/anti-patterns.md`
item 14).

**The fix for "`<EndName>` not found" is to ADD the missing `ends[]` entry — never
to remove the connector.** Removing the connector deletes the terminating branch
and silently changes the flow's behavior; the branch still needs to end. The
`ends[]` array is the last thing built (`recipes/author/author.md` Build Order
step 6), so a wired-but-undefined End is the classic slip — the pre-save check
(author.md Phase 3 step 4) verifies every End target resolves.

The invariant is **bidirectional**: every End-targeting connector resolves to an
`ends[]` entry with that exact name, and every `ends[]` entry is targeted by at
least one connector (no orphan Ends, no dangling End references). A shared End —
one entry targeted by 2+ non-fault connectors — is valid; see § Topology rules.

**Do not misdiagnose "`<EndName>` not found" as a version cap.** It is a
referential-integrity error, never evidence that the org lacks v68 or that ends
are unsupported. The org's ends support is decided **only** by the verified
`max(apiVersionsList)` from `GET /services/data/vXX.0/flowbuilder/flow/version-info` (resolved up front — see
`recipes/author/author.md` Phase 3 step 3), never inferred from a save failure. On
this error, do NOT lower `apiVersion`, drop `ends[]`, switch the branch to implicit
termination, or claim the flow "opens in Free-Form" — add the missing `ends[]`
entry and re-save at the same version.

## Topology rules (auto-layout)

These match `shared/anti-patterns.md` item 38 — the rule is that in v68 ALC every
terminating branch reaches an explicit End; how connectors converge is flexible:

1. **Every terminating branch reaches an explicit End.** On GENERATE with
   `AUTO_LAYOUT_CANVAS` at resolved `apiVersion` ≥ 68.0, co-emit the connector
   and its matching `ends[]` entry. This includes the easy-to-miss termini: a
   loop `noMoreValuesConnector`, a loop `nextValueConnector` (body) terminus, a
   Decision `defaultConnector` terminus, and any decision rule/outcome terminus.
2. **A shared End is valid; so is one End per branch.** Two or more **non-fault**
   connectors converging on one `ends[]` entry is a legal, Flow-Builder-native
   auto-layout shape (e.g. a Decision default and another outcome both ending at
   one End). One dedicated End per branch is equally valid. Neither is mandated —
   never "split" a shared End, never flag one as a defect. (Implicit ends can't
   be shared: an omitted connector targets nothing.)
3. **A `faultConnector` into an End is silently dropped, not fatal.** A fault
   whose direct target is an End — or an empty/unwired fault — is removed on
   reload; the flow stays `AUTO_LAYOUT_CANVAS` and does **not** fall back to
   Free-Form. The only real cost is silent loss of that error path, so when you
   want faults handled, route each to a real handler (a `Log_Error` /
   `Handle_Fault` Assignment, `customErrors`, or an error screen) that reaches
   *its own* End. A fault may also validly terminate at an End through a handler.

See `shared/anti-patterns.md` item 38 for the full behavior, and item 34 for the
orthogonal runtime concern (a fault rejoining a continuation that assumes success).
Mid-graph convergence on a *continuing* element is legal and never flagged.

#### Worked example — a Flow-Builder auto-layout flow with five Ends (`a_new_flow_to_test`)

A real `AUTO_LAYOUT_CANVAS` flow at `apiVersion 68.0`, authored and re-opened
cleanly in Flow Builder, shows every terminating-branch kind reaching an explicit
End — including a **shared End** and a **fault that reaches an End through a
handler**:

```text
Get_Cases  connector→Copy_1_of_Loop_Cases   faultConnector→Action_1   (fault → handler chain)
Action_1   connector→END_ELEMENT_6          faultConnector→Action_2
Action_2   connector→END_ELEMENT_7                                     (fault chain terminates at an End)
Assignment_3  connector→END_ELEMENT_4                                  (loop-body terminus via nextValue)
Decision_2 defaultConnector→END_ELEMENT_2                             ┐ shared End: default + Outcome_2
           Outcome_1→END_ELEMENT_5                                     │  both target END_ELEMENT_2
           Outcome_2→END_ELEMENT_2                                     ┘
ends[]: END_ELEMENT_2, _4, _5, _6, _7   (END_ELEMENT_2 targeted twice — a valid shared End)
```

Takeaways: (1) `END_ELEMENT_2` is reached by two non-fault connectors and is
perfectly valid — do NOT split it. (2) The `Get_Cases`/`Action_1` faults route to
handler actions that themselves reach Ends; a fault pointed *directly* at an End
(or left empty) is simply dropped on reload, not a round-trip breaker — directly
verified by round-tripping a flow whose `faultConnector` targets an `END_ELEMENT`:
the fault is removed and the flow stays `AUTO_LAYOUT_CANVAS`. (3)
Each Decision outcome, the loop-body assignment, and each action terminus all reach
an explicit End — that is the v68 obligation. (The source's `InvalidDraft` status
came from empty element configs — an empty `Assignment_3` and `operator:None`
outcomes — not from the End topology.)

---

## EVOLVE

On an edit of a retrieved flow, **preserve the source's `ends[]` verbatim** —
never inject ends into, remove ends from, or restructure the end topology of an
edited flow. "Preserve the existing `ends[]`" means keep each inherited End for
the branch that already single-targets it — it does **not** mean fanning new
branches or faults into an inherited End. Give each **new** terminating branch
you add its **own** dedicated End (auto-layout sources only), and route new
faults to a dedicated handler. Never add ends to a retrieved Free-Form source.
See `shared/connector/connector.md` § End topology (auto-layout) EVOLVE worked
example and `shared/anti-patterns.md` item 38 § EVOLVE note.

---

## JSON structure

**Explicit End targeted by a terminating branch (auto-layout, v68+):**
```jsonc
// terminating element
{ "name": "Set_Result", "connector": { "targetReference": "END_ELEMENT_1" } }
// ...
"ends": [ { "name": "END_ELEMENT_1", "locationX": 0, "locationY": 0 } ]
```

**Implicit end (< v68, Free-Form, or org max below 68) — no `ends[]` entry:**
```jsonc
{ "name": "Set_Result" }   // no connector; End is inferred, not serialized
```

See `end/examples/` for runnable fragments.

---

## See Also

- `shared/connector/connector.md` — § End topology (auto-layout): the connector
  side of the same rule, and the EVOLVE worked example.
- `shared/node/node.md` — `FlowEnd` is a `FlowNode` subclass; the generic `group`
  membership attribute.
- `shared/anti-patterns.md` item 38 — a shared End is valid (does not break
  auto-layout) and a fault pointed directly at an End is silently dropped on
  reload (advisory, not a defect); item 37 — the `CanvasMode` PMV that decides
  auto-layout vs. Free-Form.
- `shared/flow-metadata-schema.md` — the top-level `ends[]` array key.
