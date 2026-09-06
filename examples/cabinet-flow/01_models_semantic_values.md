# State 1 companion — semantic value families

## Purpose

This document defines the seven initial typed value families referenced by the
Cabinet Flow semantic-axis registry and the boundary for a valid result that is
not automatically composable.

The models carry exact semantic-term revisions. They do not make values
compatible merely because their primitive representations match.

## Model M08 — TemporalValue

### Meaning

One typed temporal coordinate carrying an exact temporal semantic term.

Candidate fields:

- `semantic_term_revision_ref`;
- `representation`: `instant`, `local_date` or `interval`;
- exactly one closed representation:
  - `instant_utc` plus original offset when known;
  - `local_date` plus timezone or a timezone-unknown marker;
  - `start` and `end` with boundary inclusion;
- `precision`;
- `source_fact_ref`.

Creation time is not substituted for event time. A local date is not silently
promoted to an instant.

### Identity

value

### Identity evidence

Substitution: equal term, representation, temporal value, precision, timezone
facts and source-fact reference are interchangeable. Continuity: it describes
one issued observation and does not mutate when the source later changes.

### Source of truth

The accepted source fact or deterministic derivation named by
`source_fact_ref`.

### Lifecycle candidate

No independent lifecycle; a changed observation creates another value.

### Persistence candidate

Embedded in structured results, Cards, capability inputs/outputs and evidence
when the exact temporal fact must be preserved.

### Open questions

None.

## Model M09 — PlaceValue

### Meaning

One typed place coordinate carrying an exact place semantic term.

Candidate fields:

- `semantic_term_revision_ref`;
- `representation`: `work_site_ref`, `postal_address` or `geo_point`;
- exactly one closed representation:
  - stable work-object/site reference;
  - structured postal-address value and country;
  - latitude, longitude and coordinate reference system;
- `precision_or_scope`;
- `source_fact_ref`.

An address, site reference and coordinate are not equal merely because they
refer to a place. Resolution requires an accepted relation and, when needed, a
capability.

### Identity

value

### Identity evidence

Substitution: equal term, representation, place facts, precision and source
reference are interchangeable. Continuity: the value is one observation or
reference; correction or re-resolution creates another value.

### Source of truth

The referenced work object, accepted address fact or accepted resolver
evidence.

### Lifecycle candidate

No independent lifecycle.

### Persistence candidate

Embedded where exact location meaning or resolution evidence is needed.

### Open questions

None.

## Model M10 — MonetaryValue

### Meaning

One monetary fact whose currency, monetary/tax basis and business semantic term
are explicit.

Candidate fields:

- `semantic_term_revision_ref`;
- `amount`: exact decimal;
- `currency`: accepted currency code;
- `monetary_basis`: accepted basis identity such as `net` or `gross`;
- `source_fact_ref`;
- `accepted_assumption_ref` optional when a declared comparison depends on
  an independently accepted assumption.

Plan, actual and estimate roles belong to the semantic term. They do not replace
currency or monetary/tax basis. Equal decimals are not proof of monetary
comparability.

### Identity

value

### Identity evidence

Substitution: equal term, decimal amount, currency, basis, source and accepted
assumption facts are interchangeable. Continuity: it is an immutable issued
fact; source revision or accepted conversion produces another value.

### Source of truth

The accepted Invoice, estimate, payment or deterministic derivation referenced
by the value. Existing Cabinet Backend MonetaryBasis evidence is preserved
rather than generalized into an unqualified total.

### Lifecycle candidate

No independent lifecycle.

### Persistence candidate

Embedded in Cards, analyses, plans, estimates, capability data and evidence.

### Open questions

None.

## Model M11 — PartyReference

### Meaning

One exact reference to a stable counterparty identity in a declared authority,
with the role relevant to the current fact.

Candidate fields:

- `semantic_term_revision_ref`;
- `party_id`;
- `identity_authority`;
- `party_role`: `supplier`, `contractor`, `client` or another accepted
  governed role;
- `revision_ref` optional when exact party facts must be pinned;
- `source_fact_ref`.

A display name, email or supplier string is not party identity. One party may
hold more than one role without becoming several parties.

### Identity

value

### Identity evidence

Substitution: equal term, party identity, authority, role, revision and source
facts are interchangeable as references. Continuity belongs to the referenced
party entity, not to this issued reference value.

### Source of truth

The Cabinet party Card or explicitly accepted external identity authority.

### Lifecycle candidate

No independent lifecycle.

### Persistence candidate

Embedded wherever a capability, Card, flow or analysis refers to a party.

### Open questions

None.

## Model M12 — WorkScopeReference

### Meaning

One exact reference to the project or physical work object relevant to a fact.

Candidate fields:

- `semantic_term_revision_ref`;
- `scope_kind`: `project` or `work_object`;
- `scope_id`;
- `identity_authority`;
- `revision_ref` optional when exact scope facts must be pinned;
- `source_fact_ref`.

A project and a physical work object are distinct kinds even when one currently
contains only one object.

### Identity

value

### Identity evidence

Substitution: equal term, kind, authority, scope identity, revision and source
facts are interchangeable as references. Continuity belongs to the referenced
project or work-object entity.

### Source of truth

The Cabinet project or work-object Card named by the reference.

### Lifecycle candidate

No independent lifecycle.

### Persistence candidate

Embedded in Cards, plans, estimates, capabilities, flows and evidence.

### Open questions

None.

## Model M13 — SourceReference

### Meaning

One exact reference to accepted source evidence without copying its bytes into
ordinary graph data.

Candidate fields:

- `semantic_term_revision_ref`;
- `source_id`;
- `content_digest`;
- `media_type`;
- `source_revision_ref` when the source description is revisioned;
- `bounded_access_capability_ref` optional;
- `provenance_ref`.

A filename, Syncthing path or caller-supplied digest is not source identity.

### Identity

value

### Identity evidence

Substitution: equal term, source identity, accepted digest, media type,
revision, access reference and provenance are interchangeable. Continuity
belongs to the source entity; different accepted bytes or source revision
produce another reference value.

### Source of truth

The trusted Cabinet Flow source registry and immutable held-byte evidence.

### Lifecycle candidate

No independent lifecycle.

### Persistence candidate

Embedded in Cards, capability inputs, HandoffPackages, flows and evidence.

### Open questions

None.

## Model M14 — QuantityValue

### Meaning

One measured, estimated or invoiced quantity whose physical dimension, unit and
business semantic term are explicit.

Candidate fields:

- `semantic_term_revision_ref`;
- `amount`: exact decimal;
- `dimension_id`;
- `unit_id`;
- `precision`;
- `source_fact_ref`;
- `accepted_conversion_ref` optional.

Equal numbers or similar unit labels do not establish comparability. Unit
conversion requires an accepted exact relation or conversion capability.

### Identity

value

### Identity evidence

Substitution: equal term, amount, dimension, unit, precision, source and
conversion facts are interchangeable. Continuity: it is an immutable issued
fact; correction or conversion creates another value.

### Source of truth

The accepted Invoice line, estimate item, work observation or deterministic
derivation referenced by the value.

### Lifecycle candidate

No independent lifecycle.

### Persistence candidate

Embedded in line items, estimates, plans, analyses and capability data.

### Open questions

None.

## Model M15 — UncomposableOutput

### Meaning

A bounded reference to a valid capability output that lacks sufficient accepted
semantic evidence for automatic graph composition but may still be returned to
the user.

Candidate fields:

- `run_id`;
- `node_id`;
- `output_schema_ref`;
- `content_digest`;
- `bounded_result_ref`;
- `reason`: `missing_semantic_term`, `unregistered_term`,
  `incompatible_shape`, `ambiguous_relation` or
  `insufficient_authority`.

It does not wrap an untyped generic payload. The underlying output remains
validated by its declared schema.

### Identity

value

### Identity evidence

Substitution: equal run, node, schema, digest, bounded result reference and
reason are interchangeable. Continuity: it records one exact output
classification and never becomes composable by mutation; later accepted
semantics create another classification.

### Source of truth

The trusted composition preflight or runtime boundary evaluating one exact
validated capability output.

### Lifecycle candidate

No independent lifecycle.

### Persistence candidate

Returned to the user and retained with run evidence when needed to explain a
composition gap.

### Open questions

None.

## Composition example — delivery and weather

A delivery capability may expose temporal term
`construction.delivery.occurred_on` and place term
`construction.work_object.site`. A weather capability may require
`weather.query_on` and `weather.query_place`.

These ports are not connected merely because they use date and place value
families. Composition requires accepted SemanticRelation revisions proving the
intended role bindings. An address-to-coordinate step additionally requires an
accepted place-resolution relation and its required capability.

An invoice issue date cannot substitute for delivery occurrence merely because
both are local dates. If the required relation is absent, preflight returns an
explicit semantic gap and invokes neither side.

The weather result may still be shown to the user. It may continue through
another graph edge only when its output port has an accepted semantic term and
the next edge is independently derivable.

## Capability granularity consequence

Baseline capabilities should be shaped around complete, independently testable
semantic transformations rather than existing application modules.

This does not require one capability per scalar field. A capability may return a
cohesive structured result when its fields form one bounded semantic outcome.
Trivial helpers and private calculations do not become slots merely to increase
graph granularity.

## Slice readiness

Models M08 through M15 have explicit value identity, substitution evidence,
continuity evidence, source of truth, lifecycle and persistence candidates.

This companion closes only the initial semantic value families. The overall
State 1 gate remains open as recorded in `01_models.md`.
