---
name: flow-resource-variable
license: LICENSE.txt has complete terms
description: "Use this skill when creating, editing, or asking about Flow variables, including collection variables, variable data types, input/output availability, default values, and the isExternallyAccessible setting. TRIGGER when: user asks to create a variable, declare a collection, set input/output availability, or configure variable data types. DO NOT TRIGGER when the user needs a formula or constant (use flow-resource-formula or flow-resource-constant)."
metadata:
  version: "1.0"
  related-skills: flow-value-rules, flow-formula-expression, flow-resource-constant
---

# Flow Variables

## Reference File Index

| File | Purpose |
|---|---|
| `examples/sobject-collection.json` | SObject collection variable |
| `examples/apex-collection.json` | Apex collection variable with output |
| `examples/currency-with-default.json` | Currency variable with default value |
| `examples/number-counter.json` | Number counter variable |
| `examples/wrong-both-types.json` | WRONG: Both objectType and apexClass set |
| `examples/wrong-collection-default.json` | WRONG: Collection with default value |
| `examples/wrong-currency-scale-zero.json` | WRONG: Currency with scale=0 |
| `examples/wrong-scale-exceeds-limit.json` | WRONG: Scale exceeds maximum of 17 |
| `examples/wrong-missing-scale.json` | WRONG: Missing required scale field |

## Overview
A variable is a named container that holds a value during a flow's execution. Variables can hold a single value or a collection (list) of values. They can be passed in from outside the flow (input), passed back out when the flow finishes (output), or used purely inside the flow.

## When to Use
Use a variable when you need to store, modify, or pass data within a flow. Use a collection variable when you need to work with multiple records or values of the same type. Use input/output settings to share data between flows or with calling code.

## Required Properties
| Property | Description | Constraints |
|---|---|---|
| Name (API Name) | Developer-facing unique identifier | Max 80 characters; must follow API naming rules |
| Data Type | The type of data the variable holds | Must be one of the supported types listed below; cannot be changed after creation |

## Optional Properties
| Property | Description | Default |
|---|---|---|
| Description | Human-readable explanation of the variable's purpose | Empty string |
| Collection | Whether the variable holds multiple values of the same type | false |
| Default Value | The initial value assigned to the variable | null (none) |
| Scale | Decimal places for Number and Currency types (range: 0-17) | Metadata default when omitted: 0; recommended for Currency: 2 (see Key Rules) |
| Object Type (subtype) | The Salesforce object or Apex class when Data Type is Record or Apex | null |
| Available for Input | Lets external callers pass a value in when the flow starts | false |
| Available for Output | Exposes the variable's value to callers after the flow runs | false |
| Externally Accessible | Controls whether the variable is exposed at all in capability-triggered flows | Depends on flow trigger type (true for most flows; false for automatic-input capability-triggered flows) |

## Data Types Supported
All of the following data types are supported for variables:

- **String** — text values
- **Number** — numeric values; supports a decimal scale
- **Currency** — monetary values; supports a decimal scale
- **Boolean** — true/false
- **Date** — a calendar date
- **DateTime** — date plus time
- **Time** — time of day (only available when the org has Time data type support and the flow process/trigger type supports it)
- **Picklist** — a single picklist value (no default value allowed)
- **Multi-Select Picklist** — multiple picklist values (no default value allowed)
- **Record (SObject)** — a Salesforce object record; requires selecting the Object Type; no default value allowed
- **Apex** — an Apex-defined type; requires selecting the Apex Class; the Apex class must be global or accessible from Flow context; no default value allowed; supports field access via dot-notation (e.g., `varWrapper.fieldName`)

## Collection Variables
Any data type can be used as a collection variable by checking "Allow multiple values (collection)". Key constraints:
- Collection variables **cannot have a default value**, regardless of data type.
- Collection variables with Record or Apex types behave like lists of records/objects.
- When `isCollection` is true, the `defaultValue` field is always ignored.

## Default Value Constraints
Default values are only available for these types on **non-collection** variables:
- String, Number, Currency, Boolean, Date, DateTime, Time

Default values are **NOT** available for:
- Picklist
- Multi-Select Picklist
- Record (SObject)
- Apex
- Any collection variable

The default value can be a literal or a reference to another resource (a value object).

## Input / Output Availability
- **Available for Input (isInput)** — the variable can be populated from the outside when the flow is invoked. Changing this setting on an existing variable that is already used as an input may cause runtime errors in calling flows.
- **Available for Output (isOutput)** — the variable's value is returned to the caller after the flow ends. Changing this or renaming an output variable on an existing flow may break calling flows.
- A warning is shown in the editor when you rename a variable or change its input/output settings if it was previously marked as input or output.
- Both can be true simultaneously (the variable is both readable and writable from outside the flow).

## isExternallyAccessible
- Controls whether the variable appears at all in external access contexts.
- Defaults to `true` for most flow types.
- Defaults to `false` specifically for capability-triggered flows that use automatic (non-manual) input configuration. In that case the variable is hidden from external callers unless the org has `optionalCapabilities` enabled and the flow is set to manual input.
- This is separate from `isInput`/`isOutput` — `isExternallyAccessible` gates visibility; `isInput`/`isOutput` control the direction.

## Validation Rules & Constraints
- Data Type must be set (cannot be null or undefined).
- When Data Type is Record (SObject) or Apex, the subtype (Object Type or Apex Class) is also required.
- Default value, if provided, must pass the resource-picker validation for the variable's data type.
- The data type **cannot be changed** after a variable has been saved (editor disables the picker in edit mode).
- API name max length is 80 characters. A variable has no label, only its API name: a `<label>` in `<variables>` fails the save.

## Common Patterns
- Store a record retrieved via Get Records into a Record variable to reuse its field values later.
- Use a collection Record variable as the target when Get Records returns multiple records.
- Mark a String variable as both input and output to pass data in, process it, and return the result.
- For scale guidance on Number/Currency variables, see the `scale` rule in the Metadata Shape > Key rules section.
- A Boolean variable is useful as a flag to track whether a condition was ever met during the flow.
- Use Apex collection variables as Transform element outputs when mapping SObject records to custom wrapper classes.

## Aura/Server Functions
- `getFlowInputOutputVariables` — retrieves the input and output variable definitions for a referenced flow (used when configuring subflow variable assignments)

## Metadata Shape

Variables live in `metadata.variables[]`. Each entry:

| Field | Type | Required | Notes |
|---|---|---|---|
| `name` | string | yes | dev-name; unique within the flow; ≤ 80 chars; ASCII alphanumeric + underscore |
| `description` | string | no | empty string by default |
| `dataType` | string | yes | `String`, `Number`, `Currency`, `Date`, `DateTime`, `Boolean`, `Picklist`, `Multipicklist`, `SObject`, `Apex` |
| `isCollection` | boolean | no | default `false` |
| `isInput` | boolean | no | default `false` — "Available for input" |
| `isOutput` | boolean | no | default `false` — "Available for output" |
| `scale` | number | **required** for `Number`/`Currency` | decimal places (0-17); **must not be null** — default to `0` if unspecified |
| `objectType` | string | conditional | ONLY when `dataType` = `"SObject"` |
| `apexClass` | string | conditional | ONLY when `dataType` = `"Apex"` |
| `value` | value object | no | optional default value |

### Key rules

- `dataType` must use exact Metadata API casing. Note: Multi-Select Picklist is `"Multipicklist"` (capital M, lowercase p) — NOT `"MultiPicklist"` or `"MultiSelectPicklist"`, which are rejected with a deserialization error.
- `objectType` is set if and only if `dataType === "SObject"`. `apexClass` is set if and only if `dataType === "Apex"`. **Never set both** — they are mutually exclusive.
- `scale` is required for `Number` and `Currency` (range: 0-17) — omitting it (null) causes a save warning that blocks activation. **Always set scale explicitly:** use `scale: 2` for Currency (standard financial precision), `scale: 0` for Number counters/IDs, `scale: 4-6` for scientific calculations. If the caller hasn't specified precision, default to `0` as a technical fallback, but note that `scale: 0` is rarely appropriate for Currency types as it truncates fractional amounts.
- `value` (default) is a value object (see `../../shared/value-rules.md` for complete value object rules). Omit the `value` field entirely when there is no default. Collection variables and SObject/Apex/Picklist variables cannot have a default value.
- `isCollection: true` is required when the variable will hold multiple rows (e.g. output of a `recordLookup` without `getFirstRecordOnly`, or an accumulator inside a `Loop`). An Assignment with `operator: "Add"` requires the target variable to be a collection OR a Number/Currency (for increment operations).
- `isInput: true` / `isOutput: true` variables define this flow's subflow contract. A calling flow's `inputAssignments[].name` must match an `isInput: true` variable in the called flow.
- When using Apex variables, verify the Apex class exists in the org before declaring the variable. The class must be global or accessible from the Flow context.
- Access fields on SObject or Apex variables using dot-notation: `varAccount.Name` or `varWrapper.orderNumber`.
- Declare only the variables that other elements reference. Speculative declarations bloat the flow and cause confusion.
- Variables don't have connectors and cannot throw.

### Save-time rejections

- `Variable '<name>' has both objectType and apexClass`
- `objectType '<name>' is not a valid sObject`
- `Variable '<name>' dataType requires objectType` (SObject without `objectType`)
- `In field: apexClass - no ApexClass named '<name>' found` (Apex variable with invalid class)
- `Variable '<name>' value type mismatch with dataType`
- `Can not construct instance of ...FlowDataType from String value 'MultiPicklist'` (wrong casing; use `Multipicklist`)
- `Cannot use Add operator on a non-collection variable` (Note: Add works on Number/Currency for increment operations)
- `Variable '<name>' has scale exceeding limit of 17` (scale > 17)
- `Element {http://soap.sforce.com/2006/04/metadata}label invalid at this location in type FlowVariable` (a `<label>` in a variable; remove it)

## Common Errors

**Both objectType and apexClass set**
See `examples/wrong-both-types.json`. Error: `Variable 'invalidVariable' has both objectType and apexClass`. These fields are mutually exclusive.

**Collection with default value**
See `examples/wrong-collection-default.json`. The `value` field is ignored; collections cannot have defaults and will be uninitialized.

**Currency with scale=0**
See `examples/wrong-currency-scale-zero.json`. While technically valid, `scale: 0` truncates fractional monetary amounts (e.g., $10.50 becomes $10). Always use `scale: 2` for standard financial precision unless you specifically need whole-dollar amounts.

**Scale exceeds limit**
See `examples/wrong-scale-exceeds-limit.json`. Error: `Variable 'preciseNumber' has scale exceeding limit of 17`. Maximum scale is 17.

**Missing scale for Currency/Number**
See `examples/wrong-missing-scale.json`. Activation blocked until `scale` is set. Default to `scale: 0` if unspecified.
