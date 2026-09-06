# State 1 — Cabinet Flow domain models

## Status

**IN PROGRESS.** This first State 1 slice defines the semantic composition
foundation accepted after State 0. It does not declare the complete Cabinet Flow
runtime model set or authorize entry into State 2.

The immediate priority is the governed semantic vocabulary through which small
capabilities can be composed into question-specific flows. Box, capability,
flow, execution, source-custody and operational Card models remain required
State 1 work.

This state describes product meaning, identity, candidate fields, lifecycle and
persistence. It does not select Python classes, tables, modules, algorithms,
transport DTOs or generated-code layout.

## Modeling boundary

A semantic axis is a stable family of domain meaning, comparable to a dimension
or unit system. It is not a feature, field name, Python type or permission.

Sharing an axis proves only that two values belong to the same broad semantic
family. It does not prove that they may be connected. Invoice issue date and
delivery occurrence date are both temporal values but are not substitutable
business facts.

An automatically composable edge requires either:

- the exact accepted semantic-term revision and compatible value shape;
- or one accepted semantic-relation revision that explicitly connects the
  source term and target term.

Authority and disclosure compatibility remain independently required. Similar
field names, equal primitive types and an agent's interpretation are not
composition evidence.

## Initial governed semantic-axis registry

The first registry is deliberately small and is not an exhaustive field
taxonomy:

- `cabinet.axis.time`: event moment, local date or period;
- `cabinet.axis.place`: site, address or geographic point;
- `cabinet.axis.money`: amount with currency and monetary basis;
- `cabinet.axis.party`: stable counterparty reference and role;
- `cabinet.axis.work_scope`: project or physical work object;
- `cabinet.axis.source`: immutable evidence/source reference;
- `cabinet.axis.quantity`: quantity with dimension and unit.

Adding an axis is rare governed evolution of the domain vocabulary. A runtime
agent may identify and propose a missing axis, term or relation but cannot make
its proposal composable merely by naming or using it.

Supplier and contractor are roles of a party, not separate identities. Project
and work object are distinct reference kinds inside the work-scope axis.
Planned, actual and estimate meanings belong to semantic terms; they do not
replace monetary basis. Address, site reference and coordinates are distinct
place representations until an accepted resolution relates them.

## Model M01 — SemanticAxis

### Meaning

One continuing governed domain-meaning family used to classify semantic terms
and compatible value shapes.

Candidate fields:

- `axis_id`: stable namespaced identity;
- `display_name`;
- `meaning`: bounded human-readable definition;
- `value_family`: one accepted value-model family;
- `status`: `active` or `retired`;
- `current_revision_id`.

### Identity

entity

### Identity evidence

Substitution: different axis IDs are never interchangeable even when their
current definitions use the same value family. Continuity: one axis remains the
same governed meaning family while accepted revisions clarify its definition
or its status changes.

### Source of truth

The Cabinet Flow semantic registry accepted through human/release governance.

### Lifecycle candidate

`active -> retired`. Revision changes do not replace the stable axis identity.

### Persistence candidate

Durable governed registry entity.

### Open questions

None.

## Model M02 — SemanticAxisRevision

### Meaning

One immutable issued definition of a SemanticAxis at an exact accepted
revision.

Candidate fields:

- `axis_id`;
- `revision_id`: content-derived identity;
- `revision_number`;
- `meaning`;
- `value_family`;
- `qualifier_contract_ref`;
- `issued_at`;
- `accepted_by`: human/release provenance reference.

### Identity

value

### Identity evidence

Substitution: equal axis ID, revision identity, definition content and issuance
facts are interchangeable. Continuity: it has no mutable independent life; any
definition change issues another revision value.

### Source of truth

Issued from one accepted SemanticAxis registry revision.

### Lifecycle candidate

No independent lifecycle; immutable after issuance.

### Persistence candidate

Durable and embedded by reference wherever exact semantic meaning is pinned.

### Open questions

None.

## Model M03 — SemanticTerm

### Meaning

One stable named business meaning within a semantic axis, such as an invoice
issue date, delivery occurrence date or work-object site.

Candidate fields:

- `term_id`: stable namespaced identity;
- `axis_id`;
- `display_name`;
- `status`: `active` or `retired`;
- `current_revision_id`.

A term identifies what a value means, not the source field that happened to
carry it.

### Identity

entity

### Identity evidence

Substitution: different term IDs remain distinct even if they currently share
one primitive type and axis. Continuity: a term remains the same governed
business concept while its accepted description or representation constraints
are revised.

### Source of truth

The Cabinet Flow semantic registry accepted through human/release governance.

### Lifecycle candidate

`active -> retired`. A conflicting meaning creates another term rather than
silently changing identity.

### Persistence candidate

Durable governed registry entity.

### Open questions

None.

## Model M04 — SemanticTermRevision

### Meaning

One immutable issued meaning and shape expectation for an exact SemanticTerm
revision.

Candidate fields:

- `term_id`;
- `term_revision_id`: content-derived identity;
- `axis_revision_ref`;
- `meaning`;
- `value_schema_ref`;
- `required_qualifier_kind`;
- `subject_kind` when the meaning is about a referenced entity;
- `temporal_role` when the term describes an event or period;
- `issued_at`;
- `accepted_by`.

Fields that do not apply to the selected axis/value family are absent rather
than filled with generic metadata.

### Identity

value

### Identity evidence

Substitution: equal term, revision, axis, meaning, schema, qualifier and
issuance facts are interchangeable. Continuity: changing any accepted meaning
or shape condition issues another revision value.

### Source of truth

Issued from one accepted SemanticTerm registry revision.

### Lifecycle candidate

No independent lifecycle; immutable after issuance.

### Persistence candidate

Durable and pinned by capability contracts, relations and flow evidence.

### Open questions

None.

## Model M05 — SemanticPort

### Meaning

One immutable capability-contract input or output position whose data shape and
domain meaning are explicit enough for composition preflight.

Candidate fields:

- `contract_revision_ref`;
- `port_id`: stable only inside that contract revision;
- `direction`: `input` or `output`;
- `value_schema_ref`;
- `semantic_term_revision_ref` optional only for output;
- `cardinality`: `one`, `optional` or `many`;
- `required_authority_refs`;
- `disclosure_class`.

An input without a semantic term is not a composable public port. An output
without a term remains observable but becomes an UncomposableOutput at the
automatic graph boundary.

### Identity

value

### Identity evidence

Substitution: equal owning contract revision, port identity, direction, schema,
term, cardinality, authority and disclosure facts are interchangeable.
Continuity: a port has no identity outside its immutable contract revision;
changing it creates a new contract revision.

### Source of truth

The accepted immutable capability-contract revision.

### Lifecycle candidate

No independent lifecycle.

### Persistence candidate

Embedded in capability-contract revisions and copied by exact reference into
flow preflight and run evidence.

### Open questions

None.

## Model M06 — SemanticRelation

### Meaning

One continuing governed claim that a value with one exact semantic meaning may
satisfy or be transformed into another exact semantic meaning.

Candidate fields:

- `relation_id`: stable namespaced identity;
- `source_term_id`;
- `target_term_id`;
- `status`: `draft`, `active` or `retired`;
- `current_revision_id`.

The relation is explicit evidence. Sharing an axis or primitive type does not
create it.

### Identity

entity

### Identity evidence

Substitution: different relation IDs are not interchangeable because approval,
use and evidence remain attributable to one governed claim. Continuity: the
same relation remains identifiable across admitted revisions and status
changes.

### Source of truth

The Cabinet Flow semantic registry accepted through human/release governance.

### Lifecycle candidate

`draft -> active -> retired`. Reactivation policy belongs to State 2.

### Persistence candidate

Durable governed registry entity.

### Open questions

None.

## Model M07 — SemanticRelationRevision

### Meaning

One immutable exact rule for relating a source semantic term and shape to a
target semantic term and shape.

Candidate fields:

- `relation_id`;
- `relation_revision_id`: content-derived identity;
- `source_term_revision_ref`;
- `target_term_revision_ref`;
- `source_schema_ref`;
- `target_schema_ref`;
- `relation_kind`: `exact_identity`, `lossless_projection`,
  `role_binding`, `explicit_conversion` or `resolution`;
- `loss_class`: `none` or one named accepted loss classification;
- `required_capability_contract_ref` when execution is required;
- `required_authority_refs`;
- `issued_at`;
- `accepted_by`.

A relation requiring conversion or resolution cannot masquerade as an exact
projection.

### Identity

value

### Identity evidence

Substitution: equal relation identity, source and target revisions, shapes,
kind, loss, required capability, authority and issuance facts are
interchangeable. Continuity: any change issues another immutable revision.

### Source of truth

Issued from one accepted SemanticRelation registry revision.

### Lifecycle candidate

No independent lifecycle.

### Persistence candidate

Durable and pinned by accepted flow definitions and run evidence.

### Open questions

None.

## State 1 document map

- `01_models_semantic_values.md` defines the seven initial typed value
  families and the uncomposable-output boundary.

Later companion files will close the remaining State 0 runtime concepts without
renumbering or redefining the models above.

## State 1 evidence

This slice preserves and refines:

- the exact semantic-identity requirement and fail-closed behavior demonstrated
  by `experiments/cabinet-vault/box_language_v0.yaml`;
- Cabinet Backend evidence that amount, currency and monetary basis are jointly
  required for monetary comparison;
- the State 0 distinction between governed meaning and changeable capability
  implementation;
- the State 0 rule that unproven composition cannot fall back to model guessing
  or generated code.

## Remaining State 1 work

State 1 is not complete. Later State 1 slices must close identity and data shape
for at least:

- principal, actor provenance and delegated authority references;
- operational Cards and immutable Card revisions;
- original source, held-byte identity, custody and ingress observations;
- slot contract, implementation version, capability and capability binding;
- flow definition/version, node, run and bounded trace evidence;
- Box definition, CapabilityInvocation and HandoffPackage;
- effect intent, approval, application and result evidence;
- sandbox/admission observations and activation history;
- integration configuration identity and release-qualification evidence.

Those slices must reuse this semantic registry rather than introduce another
field-matching vocabulary.

## State 1 readiness assessment

This initial registry slice closes identity for its models. The overall State 1
gate remains intentionally open until the companion semantic values and
remaining runtime models are defined, indexed and linted with zero identity
errors.

State 2 rules, modules and contracts must not be authored as if this partial
model set were a complete design.
