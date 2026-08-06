# Cabinet Backend — Initial Cabinet Card Scope

## Status

Accepted clarification for `02_rules.md`.

This rule defines the Cabinet Card types supported by the first Cabinet Backend
implementation.

The initial scope is intentionally narrow.

---

## Accepted decision — Invoice Card V1 only

The first Cabinet Backend implementation supports exactly one Cabinet Card type:

```text
Invoice Card V1
```

No other Cabinet Card type is included in the initial offline, synchronization,
durability, or local-processing scope.

---

## Normative rules

1. Cabinet Backend accepts only the currently accepted `Invoice Card V1`
   contract.
2. Other Cabinet Card types must not be interpreted as Invoice Cards.
3. Unsupported Card types must not create partial local records.
4. Unsupported Card types must not enter the durable Cabinet Backend archive.
5. Unsupported Card types must not be included in normal synchronization
   packages for the first implementation.
6. Cabinet Backend must not invent replacement schemas for unsupported Card
   types.
7. Cabinet Backend must not infer lifecycle, identity, revision, attachment, or
   synchronization semantics for unsupported Card types.
8. Support for an additional Card type requires a separate accepted contract.
9. Adding one Card type does not implicitly add related Card types.
10. The absence of local Backend support does not prevent Cabinet from using those
    Card types inside the VPS application.

---

## Explicitly out of scope

The following candidate Card types are not supported by the first Cabinet Backend
implementation:

```text
ProviderCard
ContactCard
MaterialListCard
MaterialListItem
DocumentCard
project-linked notes
project-linked relationships
```

This list is descriptive, not exhaustive.

Any Cabinet Card type other than `Invoice Card V1` is unsupported until
separately accepted.

---

## Unsupported Card behavior

When synchronization encounters an unsupported Card type, Backend must produce a
deterministic result such as:

```text
unsupported_card_type
```

The result must preserve enough safe evidence to diagnose the synchronization
attempt, including where available:

```text
declared_card_type
declared_card_version
source_package_id
observed_at
```

The unsupported payload must not be silently discarded when it arrived through
an auditable synchronization boundary, but it must not be promoted into the
accepted Card archive.

---

## Requirements for adding a Card type

A new Cabinet Card type may enter Backend scope only after its accepted contract
defines:

1. canonical schema;
2. validator;
3. stable logical identity;
4. immutable revision identity;
5. draft and confirmed lifecycle;
6. source-file semantics;
7. synchronization eligibility;
8. local durability requirements;
9. conflict and retry behavior;
10. dependencies on Registry, PresuPro, Holded, or Client Portal;
11. required authorization;
12. required tests and deterministic rejection behavior.

A field resemblance to an existing Card is not sufficient.

---

## Synchronization package rule

The first synchronization package may contain:

```text
Invoice Card V1 revisions
their accepted source-package evidence
related technical synchronization metadata
```

It must not include unsupported Cabinet Card payloads as accepted business
records.

A future synchronization package version may extend the supported type set only
through a separate accepted decision.

---

## Formal invariants

Supported type set:

```text
supported_card_types = { Invoice Card V1 }
```

Acceptance:

```text
card_type != Invoice Card V1
-> unsupported_card_type
```

No speculative model:

```text
unsupported Card type
-> no accepted local domain record
```

Scope extension:

```text
new Card support
-> separate accepted contract and tests
```

---

## Required tests

1. A valid confirmed Invoice Card V1 enters normal Backend validation.
2. An unknown Card type returns `unsupported_card_type`.
3. A known but unsupported Cabinet Card type returns
   `unsupported_card_type`.
4. An unsupported Card does not create an accepted local business record.
5. An unsupported Card does not alter an existing Invoice Card.
6. Diagnostic evidence preserves the declared type and version.
7. Similar fields do not cause an unsupported Card to be interpreted as an
   Invoice Card.
8. Synchronization remains deterministic when the same unsupported payload is
   observed repeatedly.

---

## Resolution of OQ-006

`OQ-006` is resolved for the first Cabinet Backend implementation:

- only `Invoice Card V1` is supported;
- all additional Cabinet Card types remain outside the first implementation;
- each future Card type requires its own accepted schema, lifecycle,
  synchronization, durability, and authorization contract.

---

## Consequence

The first Cabinet Backend implementation remains focused on one complete,
verified business flow rather than partially supporting several undefined Card
types.

Cabinet may continue using additional Card types on the VPS without implying
local Backend support.
