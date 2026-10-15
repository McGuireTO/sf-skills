# Reference Resolution

How to translate raw flow metadata into the plain-English fragments
the output contract expects. This file covers five kinds of
resolution:

1. **Id resolution** — turning the user's reference into an id that
   `GET /services/data/vXX.0/flowbuilder/flow/{id}` accepts.
2. **FEROV resolution** — turning a Field-or-Element-Referenced-or-
   Value into a readable phrase.
3. **Formula resolution** — interpreting formula resources by
   their expression, not their name.
4. **Cross-element resolution** — turning a `targetReference` into
   the destination element's type + label.
5. **Record names** — naming the records a step's literal inputs point
   to (a send's sender, consent subscription, or content) when the flow
   was read from the org.

## 1. Id resolution

Use `GET /services/data/vXX.0/flowbuilder/flow/{id}` with a FlowVersion id (`301xxx`), FlowDefinition id
(`300xxx`), custom Flow API name, or standard Flow namespaced durable version
id. The tool resolves definition ids and custom API names to the Active version,
or the latest version when none is Active. A standard durable id's `-N` suffix
selects that exact standard Flow version.

| Input the user gave you | Translation step | Final tool call |
|---|---|---|
| `301AB000000XYZ123` | No translation. | `dispatch_readonly(method: "GET", url: "/services/data/vXX.0/flowbuilder/flow/301AB000000XYZ123")` |
| `300AB000000XYZ123` (FlowDefinition id) | No separate translation call. The retrieval tool resolves Active/latest internally. | `dispatch_readonly(method: "GET", url: "/services/data/vXX.0/flowbuilder/flow/300AB000000XYZ123")` |
| Custom Flow API name (e.g. `My_Flow`) | Preserve the exact API name. The tool resolves Active/latest. | `dispatch_readonly(method: "GET", url: "/services/data/vXX.0/flowbuilder/flow/My_Flow")` |
| Namespaced custom Flow API name (e.g. `acme__My_Flow`) | Preserve the namespace and exact API name. The tool resolves Active/latest. | `dispatch_readonly(method: "GET", url: "/services/data/vXX.0/flowbuilder/flow/acme__My_Flow")` |
| Standard Flow namespaced durable version id (e.g. `SvcCopilotTmpl__AddCaseComment-1`) | Preserve the complete durable id, including the `-N` version suffix. | `dispatch_readonly(method: "GET", url: "/services/data/vXX.0/flowbuilder/flow/SvcCopilotTmpl__AddCaseComment-1")` |
| Flow label (e.g. `Lead Routing`) | Labels are not accepted. Do not convert spaces to underscores or guess an API name. | Ask for the exact API name, a `301xxx` FlowVersion id, or the complete Flow definition as Flow JSON or Salesforce Metadata API XML. |
| Element definition pasted as Flow JSON or Salesforce Metadata API XML | No id needed; summarize from the provided definition; loopback / downstream label resolution will be partial, so apply the low-confidence prefix. | No MCP call. |
| Complete Flow definition pasted as Flow JSON or Salesforce Metadata API XML | No id needed; use directly for read-only summarization. | No MCP call. |

### Name handling and unsupported-reference fallback

If the user identifies a Flow by a custom API name or a standard namespaced
durable version id:

- Trim surrounding whitespace.
- Pass the remaining identifier to `GET /services/data/vXX.0/flowbuilder/flow/{id}` exactly once.
- Do not change capitalization, add/remove a namespace, or remove a durable
  version suffix.
- Do not call `GET /services/data/vXX.0/flowbuilder/flow/{flowDefinitionId}/versions`; `GET /services/data/vXX.0/flowbuilder/flow/{id}` performs the required
  Active/latest resolution for custom API names.

If the input contains spaces or is otherwise presented as a display label, do
not derive an API name from it. Ask for the exact API name instead.

Do not call Salesforce DX, run SOQL, choose a version independently, or call
`GET /services/data/vXX.0/flowbuilder/flow/{flowDefinitionId}/versions` to retrieve the Flow. Pass supported identifiers
directly to `GET /services/data/vXX.0/flowbuilder/flow/{id}` and use the returned Flow JSON as the source of
facts. The only other reads are the Send Email / Send SMS record-name lookups in section 5.

If the user injected a flow context (e.g. Flow Builder panel context with a
`flowId` or `flowVersionId`), prefer it over re-asking when it is a `301xxx`
FlowVersion id or a `300xxx` FlowDefinition id. Route every other injected
reference through the same explicit cases in the table above.

If the user supplied an unsupported Flow reference, or supported retrieval
fails, stop and offer the supported ways to continue:

> I can't retrieve the Flow `<input>` from the supplied reference yet. To
> continue, please provide one of these:
>
> 1. The exact custom Flow API name, including its namespace when applicable.
> 2. The standard Flow's namespaced durable version id, including its `-N`
>    version suffix.
> 3. The FlowVersion id (the `301…` id) or FlowDefinition id (the `300…` id).
> 4. The complete Flow definition as either Flow JSON or Salesforce Metadata API
>    XML.

Metadata API XML is accepted as read-only summarization input only. Save
operations require the Flow MCP JSON schema.

Never invent an id. Never expose the resolved `300xxx` or `301xxx` id
in the rendered summary.

## 2. FEROV resolution

A FEROV (Field-or-Element-Referenced-Or-Value) appears in
`conditions[].rightValue` and a few other places. Its shape:

```json
{
  "stringValue":   "...",   // literal string
  "numberValue":   123,     // literal number
  "booleanValue":  true,    // literal boolean
  "dateValue":     "...",   // literal date
  "dateTimeValue": "...",   // literal datetime
  "elementReference": "<name>"  // reference to another element/variable/formula
}
```

Exactly one of the seven keys is set per FEROV.

### Translation table

| FEROV shape | Operator | Renders as |
|---|---|---|
| `{ booleanValue: true }` | `EqualTo` | "is true" |
| `{ booleanValue: false }` | `EqualTo` | "is false" / "is not blank" / context-dependent |
| `{ stringValue: "Closed Won" }` | `EqualTo` | `"is Closed Won"` (translate to natural English; drop quotes) |
| `{ numberValue: 100000 }` | `GreaterThan` | `"exceeds $100,000"` (currency context — render with $ if the LHS is `Amount` / `Revenue` / `Price`; render plain if LHS is `Score`, `Count`, etc.) |
| `{ numberValue: 14 }` | (with a "days ago" left side) | `"more than 14 days ago"` |
| `{ dateValue: "2026-06-30" }` | `EqualTo` | `"is June 30, 2026"` |
| `{ elementReference: "Lead_Id" }` | `IsNull == false` | `"<Lead Id> is populated"` |
| `{ elementReference: "Account.Type" }` | `EqualTo` + `stringValue: "Enterprise"` | `"the account type is Enterprise"` |

### Operator translation

| Salesforce operator | English |
|---|---|
| `EqualTo` | "is" / "is equal to" |
| `NotEqualTo` | "is not" |
| `GreaterThan` | "exceeds" / "is more than" |
| `GreaterThanOrEqualTo` | "is at least" |
| `LessThan` | "is less than" |
| `LessThanOrEqualTo` | "is at most" |
| `StartsWith` | "begins with" |
| `EndsWith` | "ends with" |
| `Contains` | "contains" |
| `IsNull` (with `booleanValue: true`) | "is blank" |
| `IsNull` (with `booleanValue: false`) | "is populated" / "is not blank" |
| `In` (with collection) | "is one of" |

If the operator is one not in this table, fall back to a generic
phrasing ("matches the configured value") — do **not** quote the
operator name.

### API-name to readable-noun

When the LHS is a field reference, prefer the field's *label* if
the metadata gives one. If not, transform the API name:

- `StageName` → "Stage"
- `Account.Industry` → "the account's industry"
- `Lead_Score__c` → "Lead Score"
- `IsActive` → "Active"
- `Custom_Field__c` → "Custom Field"

Drop the `__c` suffix. Convert snake_case to space-separated
title-case. Strip object prefixes when the context is unambiguous.

## 3. Formula resolution

A formula resource referenced in a condition (`elementReference`
points to a `formulas` entry):

1. Look up the formula by name in `flow.formulas[]`.
2. Read its `expression`.
3. Interpret the *expression*, not the formula's `name` (names go
   stale).

### Examples

| Formula name | Expression | Renders as |
|---|---|---|
| `IsHighValue` | `{!Opportunity.Amount} > 100000` | "the opportunity amount exceeds $100,000" |
| `IsStaleNegotiation` | `({!Opportunity.LastModifiedDate} < (TODAY() - 14)) && {!Opportunity.StageName} = "Negotiation"` | "the opportunity is in Negotiation and has not been modified in more than 14 days" |
| `LooksGood` | `{!Account.Type} = "Enterprise" && {!Account.AnnualRevenue} > 5000000` | "the account is an Enterprise account with annual revenue above $5,000,000" |

### When the expression cannot be interpreted confidently

- Expression is missing from the metadata.
- Expression nests other formulas to a depth that interpretation
  would be a guess.
- Expression uses an unfamiliar custom function (`MyHelper__c(…)`).

In any of those cases:

- Refer to the formula by its name only:

> "a formula condition called <Formula_Name>"

- Apply the low-confidence prefix to the intent paragraph (per
  `confidence-rules.md`).

Do **not** quote the formula's expression. Do **not** speculate
about what it evaluates.

## 4. Cross-element resolution (downstream)

When a path's `connector.targetReference` points to another
element, look up that element in the flow JSON and resolve to
`{ type, label }`:

```text
target.type = "actionCall" / "recordCreate" / "recordUpdate" /
              "subflow" / "screen" / "decision" / "loop" /
              "assignment" / "recordLookup" / "recordDelete" / …
target.label = element.label || element.name
```

### Translation table

| target.type | Phrasing |
|---|---|
| `actionCall` | "triggers the <label> action" / "calls <label>" |
| `recordCreate` | "creates a <objectLabel> record" |
| `recordUpdate` | "updates the <objectLabel> record" |
| `recordLookup` | "retrieves <objectLabel> records" |
| `recordDelete` | "deletes the <objectLabel> record" |
| `subflow` | "kicks off the <label> subflow" |
| `assignment` | "updates the <label> assignment" / "sets <label>" |
| `decision` | "routes through the <label> decision" |
| `screen` | "shows the <label> screen" |
| `loop` | "iterates through <label>" |
| `wait` | "waits for <label>" |

If multiple actions follow on a path (the immediate target is an
assignment that connects onward to an actionCall, etc.), describe
the sequence at a high level — pick a verb that captures the net
effect, not every step:

> "updates the opportunity record, then sends an email
> notification"

If a target's label is the API name with no human-readable label,
render the API name in plain English (snake_case → title-case).

### Loopback detection

A loopback exists when any element in the flow has a connector
(direct or indirect) whose `targetReference` points back to the
Decision being summarized. Walk the connector graph:

```text
loopback_sources = [
  e for e in flow.elements
  if any(connector.targetReference == decision.name
         for connector in e.connectors_outgoing)
]
```

If `loopback_sources` is non-empty, append the loopback note (per
`output-contract.md`). Name the most user-relevant source — usually
the action element that the loop returns through, not an
intermediate assignment. If multiple loopback sources are equally
relevant, list up to two: "after <A> and <B>".

## 5. Record names behind literal Ids

A step's literal inputs can hold record Ids or a CMS content reference.
On a Send Email Message action, `senderId` is a User (`005…`) or an
org-wide email address (`0D2…`),
`communicationSubscriptionId` a CommSubscription (`0Xl…`),
`commSubscriptionChannelTypeId` a CommSubscriptionChannelType (`0eB…`),
and `contentId` the email, as
`marketing--<workspace>.sfdc_cms__email--<API name>`. On Send SMS
Message, `senderId` is a MessagingChannel (`0Mj…`) and `contentId` an
SMS content. Never show the Id or the content reference. When the user
asks which email, sender, or subscription a step uses, "a configured
user" doesn't answer the question.

**Flow read from the org** (`GET /services/data/vXX.0/flowbuilder/flow/{id}`):
the Ids are that org's. Look up each of these Send Email Message and Send
SMS Message inputs the summary names (no other Ids), with one
read-only query each (`dispatch_readonly(method: "GET", url:
"/services/data/vXX.0/query", queryParams: { q: "<query>" })`), and use
its name:

| Record | Query | Name to use |
|---|---|---|
| User (`005…`) | `SELECT Name FROM User WHERE Id = '<Id>'` | `Name` |
| OrgWideEmailAddress (`0D2…`) | `SELECT DisplayName, Address FROM OrgWideEmailAddress WHERE Id = '<Id>'` | `DisplayName` (`Address`) |
| SenderEmailAddress (`35a…`) | `SELECT DisplayName FROM SenderEmailAddress WHERE Id = '<Id>'` | `DisplayName` |
| CommSubscription (`0Xl…`) | `SELECT Name FROM CommSubscription WHERE Id = '<Id>'` | `Name` |
| CommSubscriptionChannelType (`0eB…`) | `SELECT Name FROM CommSubscriptionChannelType WHERE Id = '<Id>'` | `Name` |
| MessagingChannel (`0Mj…`) | `SELECT MasterLabel FROM MessagingChannel WHERE Id = '<Id>'` | `MasterLabel` (an SMS sender's phone number) |
| CMS content (the part of `contentId` after the last `--` is the content's API name) | `SELECT Id, Name FROM ManagedContent WHERE ApiName = '<API name>'` | `Name`, the content's title |

- Only when the user asks what the message says: read it from
  `GET /services/data/vXX.0/connect/cms/contents/<the ManagedContent Id>`
  (`contentBody.subjectLine` is the subject line).
- When a lookup returns no row or fails, describe the record by its
  role ("the configured sender") and go on. Never show the Id instead.
- These lookups only read. They don't change which flow version is
  summarized.

**Flow pasted as XML or JSON:** the pasted definition is the only
source of facts, and its Ids may come from another org, so make no
lookups. Describe each record by its role ("a specific sender user",
"the configured email content"), and don't name a record the
definition doesn't name.

Other identifiers in a step aren't record Ids: a journey's Id, a
business unit's MID, or an `mceBuSelector`. Use the names the step
already carries.
