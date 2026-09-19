# State 1 — Cabinet Flow kernel models

## Status

**COMPLETE for the kernel of State 0 (2026-09-19).** This document defines the
governed semantic vocabulary through which function nodes and operation nodes
are composed (D0-038). Its companions define every other kernel model; the
document map below lists them.

The vocabulary models M01–M07 are kernel models. The vocabulary's content — the
axes listed below and every term and relation — is data of the first
application, seeded at installation and extended only through accepted
VocabularyProposals (M45).

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

Disclosure compatibility remains independently required (D0-047). Similar field
names, equal primitive types and an agent's interpretation are not composition
evidence.

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

The kernel's semantic registry. An entry exists only by installation seed or by
the owner's acceptance of a VocabularyProposal (M45).

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
- `accepted_by`: ActorRef of kind `owner`, or the installation seed.

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

The kernel's semantic registry. An entry exists only by installation seed or by
the owner's acceptance of a VocabularyProposal (M45).

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

Durable and pinned by ports, relations, flow proofs and stored values.

### Open questions

None.

## Model M05 — SemanticPort

### Meaning

One immutable input or output position of a slot contract version, an operation
binding version or a flow version, whose data shape and domain meaning are
explicit enough for flow proof.

Candidate fields:

- `owner_ref`: the SlotContractVersion, OperationBindingVersion or FlowVersion
  the port belongs to;
- `port_id`: stable only inside that owner;
- `direction`: `input` or `output`;
- `value_schema_ref`;
- `semantic_term_revision_ref` optional only for output;
- `cardinality`: `one`, `optional` or `many`;
- `disclosure_class`: `open`, `business_confidential` or `personal_data`. On an
  input port it is the highest class the port accepts. On an operation binding's
  output port it is declared. On a function's output port it is never authored:
  the kernel derives it as the highest class among the values the execution
  received, so code cannot launder a value into a lower class.

An input without a semantic term is not a port. An output without a term remains
observable but becomes an UncomposableOutput and feeds no edge.

### Identity

value

### Identity evidence

Substitution: equal owner, port identity, direction, schema, term, cardinality
and disclosure facts are interchangeable. Continuity: a port has no identity
outside its immutable owner; changing it creates a new version of that owner.

### Source of truth

The immutable contract version, binding version or flow version that owns it.

### Lifecycle candidate

No independent lifecycle.

### Persistence candidate

Embedded in its owner and cited by exact reference in flow proofs and node
executions.

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
- `status`: `active` or `retired`;
- `current_revision_id`.

A relation that is only proposed is a VocabularyProposal (M45) and is not in
this registry. The relation is explicit evidence. Sharing an axis or primitive type does not
create it.

### Identity

entity

### Identity evidence

Substitution: different relation IDs are not interchangeable because approval,
use and evidence remain attributable to one governed claim. Continuity: the
same relation remains identifiable across admitted revisions and status
changes.

### Source of truth

The kernel's semantic registry. An entry exists only by installation seed or by
the owner's acceptance of a VocabularyProposal (M45).

### Lifecycle candidate

`active -> retired`. Retirement is final; the same claim returns only through a
new accepted proposal. A flow version already proven on a relation revision
keeps that proof.

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
- `required_slot_ref` when execution is required: the slot whose function
  performs the conversion or resolution, which then appears as a node on the
  path and never as a bare edge;
- `issued_at`;
- `accepted_by`.

A relation requiring conversion or resolution cannot masquerade as an exact
projection.

### Identity

value

### Identity evidence

Substitution: equal relation identity, source and target revisions, shapes,
kind, loss, required slot and issuance facts are interchangeable. Continuity: any change issues another immutable revision.

### Source of truth

Issued from one accepted SemanticRelation registry revision.

### Lifecycle candidate

No independent lifecycle.

### Persistence candidate

Durable and pinned by accepted flow definitions and run evidence.

### Open questions

None.

## State 1 document map

- `01_models_semantic_values.md` — M08–M15: the seven initial typed value
  families and the uncomposable-output boundary.
- `01_models_authority.md` — M16–M18: the owner, agent delegation and the actor
  reference.
- `01_models_slots.md` — M19–M27: slot, contract version, resource bounds,
  sandbox runtime, implementation, trial case, trial execution, admission
  verdict and slot activation.
- `01_models_flows.md` — M28–M37: manifest operation reference, operation
  binding and version, flow, flow version, node, edge, constant, proof and
  flow activation.
- `01_models_runs.md` — M38–M45: stored value, service target, run, node
  execution, effect approval, standing grant, outcome reconciliation and
  vocabulary proposal.

## State 1 evidence

This slice preserves and refines:

- the exact semantic-identity requirement and fail-closed behavior demonstrated
  by `experiments/cabinet-vault/box_language_v0.yaml`;
- Cabinet Backend evidence that amount, currency and monetary basis are jointly
  required for monetary comparison;
- the State 0 distinction between governed meaning and replaceable function
  implementation;
- the State 0 rule that unproven composition cannot fall back to model guessing
  or generated code.

## Deliberately absent models

The superseded State 0 required models that the kernel does not have. Their
absence is a decision, not a gap:

- Card, Card revision, source custody and ingress observation are facts of the
  microservices that own them (D0-042); the kernel holds a SourceReference.
- Capability, capability binding, CapabilityInvocation, HandoffPackage and Box
  are replaced by the two node kinds of D0-034 and the operation binding of
  D0-035. Transfer between microservices is outside the kernel.
- Effect intent does not exist: a function produces data and an operation node
  performs the effect (D0-034).
- Configuration, service handle, import list and secret have no model because a
  function has none of them.
- Roles, users and invitations have no model because there is one trusted
  entrance (D0-046).

## State 1 readiness assessment

Models M01 through M45 have explicit identity, substitution and continuity
evidence, source of truth, lifecycle and persistence candidates, and no open
question. State 2 may be authored.

State 2 states as rules what these models only make possible; see the
`02_rules_*.md` documents, decisions A01 through A24.
