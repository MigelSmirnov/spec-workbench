# State 5 — Cabinet Flow semantic-vocabulary operations

A25 clock contract: every operational timestamp written by this module is KernelInstant M47 obtained from its injected `module:system_clock.now` at the atomic event it owns. No public operation accepts caller-, gateway- or surface-supplied current time.

The semantic vocabulary is the governed registry of meaning. Accepted axes,
terms and relations have stable identities and immutable revisions; proposals
are not composition evidence, and only the installation seed or an owner
decision may create governed meaning.

## `public_op:semantic_vocabulary.seed_vocabulary`

### Owner

`module:semantic_vocabulary` owns installation of the exact built-in semantic
seed for a new kernel registry.

### Callers

`module:bootstrap` calls it during fail-closed startup inside the durable
startup unit of work.

### Inputs

No request-authored vocabulary content. The operation uses only the
installation/kernel-release seed bundle shipped with the running release,
including its exact axis, term and relation definitions and revision content.

### Outputs

A deterministic seed result naming every installed governed entry/revision, or
an explicit no-op when the semantic registry is already initialized. No
"latest" external vocabulary source is consulted.

### Observable effect

When and only when the governed registry is empty, the exact release seed is
installed atomically. On an already initialized registry, no semantic entry is
created, revised, retired or reactivated.

### Enforces

Seed provenance is the installed release; revisions are immutable;
content-derived revision identities are deterministic; the seed cannot be
extended or overridden by host configuration, request data or service content;
partial seed installation is impossible.

### Errors

Malformed or internally inconsistent release seed, unsupported value-family or
schema reference, duplicate conflicting seed identity and transactional failure
refuse startup. An incomplete registry is never reported ready.

### State impact

On first initialization only, the seed's stable vocabulary entries and their
immutable revisions are created atomically. Later startup calls do not mutate
the registry.

## `public_op:semantic_vocabulary.term_revision`

### Owner

`module:semantic_vocabulary` owns authoritative lookup of one governed
SemanticTerm and its immutable revision evidence.

### Callers

`module:slot_registry` calls it while issuing contract ports.
`module:operation_bindings` calls it while validating typed service ports.
`module:flow_proof` calls it while proving exact edge semantics.
`module:kernel_surface` calls it for bounded vocabulary inspection.

### Inputs

One exact namespaced term identity and, when historical evidence is required,
an optional exact term-revision identity. Free-text meaning, primitive type,
field name and "closest" semantic match are never lookup keys.

### Outputs

The exact immutable SemanticTermRevision, its owning term and axis identities,
and current active/retired status of both stable entities; or an explicit
absence. Without an explicit revision identity, the current issued revision is
returned. Historical issued revisions remain readable after retirement.

### Observable effect

None.

### Enforces

Only accepted or seeded revisions are returned; proposals are never returned as
terms; revision content is immutable; callers creating new contracts, bindings
or proofs can distinguish an active term on an active axis from historical
retired evidence; no fuzzy or schema-only equivalence is inferred.

### Errors

Malformed identity, unknown term/revision, revision belonging to another term,
corrupt revision chain and unavailable registry are explicit. Absence is not
filled from a proposal or inferred from a similar term.

### State impact

None.

## `public_op:semantic_vocabulary.find_relation`

### Owner

`module:semantic_vocabulary` owns exact lookup of governed semantic relations
between two exact term revisions.

### Callers

`module:flow_proof` calls it when an edge does not use identical term
revisions and needs an explicit accepted relation basis.
`module:kernel_surface` calls it during vocabulary-gap inspection.

### Inputs

Exact source and target SemanticTermRevision references and an optional closed
relation-kind filter. Text labels, shared axis, primitive shape and field names
are not relation evidence.

### Outputs

A deterministic ordered set of active SemanticRelationRevision records whose
source and target revisions match exactly, including relation kind, source and
target schemas, loss class and required slot when applicable. If none exists,
the result is explicitly empty.

### Observable effect

None.

### Enforces

Only seeded/owner-accepted active relation entities participate in new
composition; proposed or retired relations are excluded; source/target term
revisions and schemas must match the issued relation exactly; no reverse,
transitive or resemblance relation is invented.

### Errors

Unknown term revision, malformed pair, inconsistent relation evidence and
unavailable registry are explicit. An empty exact relation set is not an error
and never triggers implicit conversion.

### State impact

None.

## `public_op:semantic_vocabulary.submit_proposal`

### Owner

`module:semantic_vocabulary` owns durable VocabularyProposal M45 submission
without adding the proposed meaning to the governed registry.

### Callers

`module:kernel_surface` calls it from the closed `author` operation after
authoring permission has been resolved.

### Inputs

The resolved ActorRef; proposal kind `axis`, `term` or `relation`; the
complete candidate governed content for a new entry or revision; exact
motivating FlowProof finding or UncomposableOutput references; and optional
bounded agent rationale kept separate from the owner-facing statement. A caller
may propose a governed stable namespaced entry identity where the candidate kind
requires one, but may not supply a revision identity, accepted status or owner
decision.

### Outputs

One durable VocabularyProposal in `proposed` state with stable proposal
identity, complete proposed content, motivating references and a deterministic
plain owner-facing statement obtained from
`module:owner_authority.owner_statement`.

### Observable effect

Exactly one proposal may be appended. No SemanticAxis, SemanticTerm,
SemanticRelation or revision becomes usable from submission alone.

### Enforces

Proposal content is structurally complete for its kind; referenced existing
entities/revisions are exact; motivation is attributable; agent text cannot
replace the kernel-generated owner statement; content equal to an already active
accepted revision is refused with that revision reference; proposal is never a
port or edge basis.

### Errors

Unsupported proposal kind, malformed candidate, unknown motivating evidence,
invalid referenced semantic entity, duplicate of an active accepted revision,
owner-statement generation failure and transactional failure refuse submission
without changing governed meaning.

### State impact

One proposed VocabularyProposal may be appended. Governed entries and revisions
remain unchanged.

## `public_op:semantic_vocabulary.decide_proposal`

### Owner

`module:semantic_vocabulary` owns the atomic owner decision over one exact
VocabularyProposal and the resulting revision issuance on acceptance.

### Callers

`module:kernel_surface` calls it only from the closed owner-decision operation
for the active owner.

### Inputs

The active owner ActorRef; exact proposed VocabularyProposal; expected
`proposed` status; decision `accepted` or `rejected`; and the exact
kernel-generated owner-statement digest bound to the proposed content. No
modified candidate content is accepted at decision time.

### Outputs

For rejection, the same proposal in final `rejected` state. For acceptance,
the proposal in final `accepted` state plus exactly one newly issued immutable
axis/term/relation revision and its stable governed entry reference. If the
proposal revises an existing entry, its current-revision pointer advances to
that issued revision; earlier revisions remain immutable.

### Observable effect

Acceptance atomically creates the new governed entry when needed or issues one
new revision of an existing entry, advances its current revision and links
`resulting_revision_ref` from the proposal. Rejection creates no governed
meaning.

### Enforces

Active owner only; proposal is decided once; exact candidate and owner
statement; no duplicate of an active accepted revision; new revision identity
is content-derived by the vocabulary module; acceptance is all-or-nothing;
rejection cannot later be reopened.

### Errors

Non-owner or suspended owner, stale/already-decided proposal, changed statement
or content, duplicate accepted content, invalid semantic references and
transaction failure are refused without a partial revision or proposal state
change.

### State impact

The proposal makes one final transition. Acceptance may create/update one
stable governed vocabulary entry and append exactly one immutable revision;
rejection changes only proposal decision metadata.

## `public_op:semantic_vocabulary.retire_entry`

### Owner

`module:semantic_vocabulary` owns final retirement of one governed stable
SemanticAxis, SemanticTerm or SemanticRelation entity.

### Callers

`module:kernel_surface` calls it only from the closed owner-decision operation
for the active owner.

### Inputs

The active owner ActorRef; exact stable vocabulary entry identity and kind;
expected `active` status; current revision identity; and a bounded owner
reason. A revision itself is not deleted or retired independently.

### Outputs

The same stable entry in final `retired` status with retirement evidence, or
a typed refusal. Every issued revision remains readable and immutable.

### Observable effect

Exactly one stable vocabulary entity may transition `active -> retired`.
There is no cascading rewrite of child terms, relations, revisions, FlowProofs
or Runs.

### Enforces

Owner only; final compare-and-set transition; new contracts, binding versions
and proofs cannot newly cite a retired term/relation, and cannot cite a term
whose owning axis is retired; existing proofs and pinned runs retain the exact
historical revision basis they already recorded; retirement never reactivates
or replaces another entry.

### Errors

Non-owner or suspended owner, unknown entry, wrong kind, stale current revision,
already-retired entry, conflicting repeat and persistence failure are refused
atomically.

### State impact

Only the stable vocabulary entity's retirement metadata changes. Issued
revisions, proposals, proofs, contract versions, binding versions and existing
runs remain immutable.
