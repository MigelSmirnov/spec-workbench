# State 1 companion — run, trace, approval and proposal models

## Purpose

This document closes identity and data shape for execution under State 0
decisions D0-040, D0-041 and D0-042: the values that edges carry, the run and
its immutable per-node trace, the owner's approvals and standing grants, the
reconciliation of an undetermined outcome, and the proposals through which an
agent asks the owner to extend the vocabulary.

## Model M38 — StoredValue

### Meaning

One bounded, content-addressed value held by the kernel because an edge carried
it, a trial case contains it or a preview showed it.

Candidate fields:

- `value_digest`: identity, the digest of the canonical value bytes;
- `semantic_term_revision_ref`;
- `value_schema_ref`;
- `carriage`: `value`, or `byte_stream` for a trial fixture file, which is the
  only file the store ever holds and always has retention class `trial_corpus`;
- `size`; `media_type` when the carriage is `byte_stream`;
- `disclosure_class`: copied from the port that produced it;
- `retention_class`: `run_evidence`, `trial_corpus` or `approval_evidence`;
- `held_until`: absent for `trial_corpus`.

A StoredValue is never a business record. It is what passed through the kernel,
kept so that a run can be explained; the fact it describes lives in the
microservice that owns it. A file in flight is SpooledBytes (M46), not a
StoredValue; a file at rest belongs to its owning service and is named by a
SourceReference (M13).

### Identity

value

### Identity evidence

Substitution: equal digest is interchangeable, whichever run produced it, so an
identical value is held once. Continuity: a value never changes. Expiry removes
the bytes and leaves the digest in the records that named it.

### Source of truth

The kernel, from the validated output of a node or from an authored trial case.

### Lifecycle candidate

No independent lifecycle. Expiry under `held_until` is retention, not a state.

### Persistence candidate

Content-addressed area of the kernel's operational store.

### Open questions

None.

## Model M46 — SpooledBytes

### Meaning

One file produced by a `byte_stream` output port of a function node or an
operation node, held for the duration of one run so that it can be identified,
approved where an effect needs it, and handed to the next node.

Candidate fields:

- `run_id`;
- `content_digest`: computed by the kernel while receiving;
- `size`, `media_type`: as observed by the kernel from the bytes, not as claimed
  by the producing service, the producing function or a file name;
- `semantic_term_revision_ref`, `disclosure_class`: from the producing port;
- `produced_by`: the node execution that received them;
- `released_at`: when the spool entry was emptied.

Spooled bytes are delivered to a function node as a read-only file inside its
sandbox and to an operation node as the request body the binding declares. Over
the surface they are shown only to the owner, in an approval preview, and to an
agent only as digest, size, media type and class. What remains after release is
that description in the node executions that named them. A file that a trial
case needs is copied, deliberately, into the trial corpus as a StoredValue of
carriage `byte_stream` (M38, A07).

### Identity

value

### Identity evidence

Substitution: equal run and content digest are interchangeable; the same bytes
received twice within a run are held once. Continuity: the bytes never change;
release removes them and leaves their description.

### Source of truth

The kernel, from the bytes an operation node actually received.

### Lifecycle candidate

No independent lifecycle. Release at the run's terminal state is retention, not
a state.

### Persistence candidate

Run-scoped spool of the kernel host, outside the operational store's
content-addressed area and outside its backups' business meaning; size-bounded
per run by the kernel release.

### Open questions

None.

## Model M39 — ServiceTarget

### Meaning

The exact microservice instances one run is allowed to reach.

Candidate fields:

- `targets`: for each service the flow touches, the manifest instance name and
  its instance class — `local_dev`, `disposable_rig` or `production`;
- `installation_ref`: the kernel installation whose configuration selected
  them.

A kernel installation selects one instance per service. A flow, a run or an
agent cannot choose another. Rehearsing an effectful flow is done by an
installation whose targets are disposable rigs, never by a switch inside a
production installation.

### Identity

value

### Identity evidence

Substitution: equal targets and installation are interchangeable. Continuity:
resolved once when the run is created and never changed; a reconfigured
installation affects only later runs.

### Source of truth

The installation's configuration, resolved against the platform manifest.

### Lifecycle candidate

No independent lifecycle.

### Persistence candidate

Embedded in FlowRun.

### Open questions

None.

## Model M40 — FlowRun

### Meaning

One execution of one exact flow version on one set of inputs, from the request
until a truthful end.

Candidate fields:

- `run_id`: stable identity;
- `flow_activation_ref`, and through it the flow version and its proof;
- `pinned_slot_activations`: for every function node, the SlotActivation in
  force when the run was created;
- `service_target`: one ServiceTarget;
- `inputs`: one StoredValue or SourceReference per flow input port;
- `initiated_by`: ActorRef;
- `status`: `created`, `running`, `awaiting_approval`, `pending`, `succeeded`,
  `failed`, `refused` or `cancelled`;
- `waiting_on`: the node identities the run is stopped at, each with the
  reason — `owner_approval`, `service_unreachable`, `binding_suspended` or
  `outcome_unknown`; for `service_unreachable` and `outcome_unknown` the
  entry also stores `retry_ordinal` and `retry_not_before` as KernelInstant
  M47, while non-timed reasons leave both absent;
- `in_flight_effect_attempts`: for each non-read operation being invoked, the
  node, map index, attempt number and idempotency-key digest, recorded durably
  before the call and cleared only by the concluding NodeExecution. An entry
  found at restart is an effect whose outcome is unknown (A14, A18);
- `outputs`: one StoredValue per flow output port once produced;
- `created_at`, `ended_at`;
- `cancellation_reason`: the owner's bounded reason, present only on a run
  whose status is `cancelled`.

Everything a run executes is pinned when it is created. An activation, a
binding version or a vocabulary change made while the run waits does not alter
it.

### Identity

entity

### Identity evidence

Substitution: two runs are never interchangeable, even of the same flow version
on equal inputs; each has its own approvals, attempts and outcome. Continuity:
the run stays the same while it moves between running and waiting and while node
executions accumulate.

### Source of truth

The kernel's run registry.

### Lifecycle candidate

`created -> running`; `running <-> awaiting_approval`; `running <-> pending`;
`running -> succeeded | failed | refused`; any non-terminal state `-> cancelled`
by the owner. `succeeded` requires every node concluded `succeeded` or
`skipped_by_guard` and every non-optional flow output produced and validated.
`refused` means the owner denied an approval. `pending` means a required service
instance was unreachable, a binding is suspended or an effect's outcome is still
undetermined. No state is entered by default or by timeout of a wait.

### Persistence candidate

Durable entity of the kernel's operational store; survives restart and is
resumed from its recorded state.

### Open questions

None.

## Model M41 — NodeExecution

### Meaning

The immutable trace record of one concluded attempt to execute one node of one
run. It is the data that explains the run, not a log line about it.

Candidate fields:

- `node_execution_id`;
- `run_id`, `node_id`, `map_index` when the node maps, `attempt_number`;
- `executed_ref`: the Implementation for a function node, the
  OperationBindingVersion for an operation node;
- `runtime_revision_ref` and `enforced_bounds` for a function node;
- `service_instance` and `idempotency_key_digest` for an operation node;
- `approval_ref` or `grant_ref` when the node required the owner's authority;
- `input_value_refs`, `output_value_refs`: StoredValue digests per port;
- `input_validation`, `output_validation`: verdicts naming the violated port and
  rule;
- `denied_attempts`: as in TrialExecution;
- `resources_used`;
- `status`: `succeeded`, `contract_violation`, `denied_attempt`, `timeout`,
  `resource_exhausted`, `crashed`, `cleanup_failed`, `operation_refused`,
  `operation_failed`, `service_unreachable`, `outcome_unknown`,
  `skipped_by_guard` or `not_executed_upstream_failed`;
- `failure_reason`: closed refinement where the status needs one, such as
  `value_too_large` under `contract_violation` or `refused_by_owner` and
  `refused_by_service` under `operation_refused`;
- `failure_detail`: bounded text without secrets and without any value above
  `open` class;
- `started_at`, `ended_at`.

`succeeded` is written only after output validation. `operation_refused` records
a service's own refusal, such as a replay it rejects; `outcome_unknown` records
that the kernel cannot tell whether an effect happened.

### Identity

value

### Identity evidence

Substitution: equal execution identity is interchangeable; a repeated attempt is
another record with the next attempt number. Continuity: a record never changes,
and a later attempt or reconciliation never rewrites it.

### Source of truth

The kernel's executor and sandbox supervisor, never the executed code and never
the invoked service's free-text claim.

### Lifecycle candidate

No independent lifecycle.

### Persistence candidate

Durable, append-only evidence of the kernel's operational store.

### Open questions

None.

## Model M42 — EffectApproval

### Meaning

One continuing approval request for one exact effect that one run is about to
perform, from the immutable preview the kernel presents until the owner decides
and, when approved, until that authority is consumed by the one exact execution
it covers.

Candidate fields:

- `approval_id`: stable identity;
- `run_id`, `node_id`;
- `binding_version_ref`;
- `service_instance`;
- `preview_value_refs`: the StoredValues of the binding's preview ports,
  exactly as shown; for a mapped node, those of every element of the collection;
- `preview_digest`: digest over the binding version, the instance and the
  digests of all input values of the node — for a mapped node, of every
  element — not only the previewed ones;
- `status`: `pending`, `approved`, `denied` or `consumed`;
- `decided_by`: ActorRef of kind `owner`, and `decided_at`, present only
  after the `pending -> approved | denied` transition;
- `consumed_attempt_refs`: the exact run/node/map-index/attempt identities
  already authorized by this approval; empty before first use. For a non-mapped
  node it contains at most one item. For a mapped node it grows only within the
  previewed element set and the approval reaches `consumed` when every covered
  element attempt has taken its one authority.

The kernel invokes the operation only with inputs whose digest equals the
approved preview. A different input is a different effect and needs another
approval. One approval of a mapped node covers the complete mapped collection
shown in its preview and can be consumed only by the corresponding recorded
element attempts.

### Identity

entity

### Identity evidence

Substitution: two approval requests are never interchangeable, even with equal
previews, because each belongs to one run/node decision and one consumption
history. Continuity: the same approval remains identifiable while it moves from
`pending` to the owner's final decision and, when approved, while its exact
covered attempt set is consumed element by element. Its preview and digest
never change.

### Source of truth

`module:owner_authority` creates the pending approval from kernel-owned
evidence; only the owner changes `pending` to `approved` or `denied`; the
kernel alone records consumption when exact invocation authority is taken.

### Lifecycle candidate

`pending -> approved -> consumed` or `pending -> denied`. `denied` and
`consumed` are final. An approved approval whose input digest no longer
matches is not rewritten for the new input; it is unusable and a new pending
approval is required.

### Persistence candidate

Durable entity of the kernel's operational store. The pending preview, owner
decision and consumption state survive restart and are referenced by the
execution evidence they authorize.

### Open questions

None.

## Model M43 — StandingGrant

### Meaning

The owner's continuing approval for one exact effectful node of one exact flow
version to run without asking each time.

Candidate fields:

- `grant_id`: stable identity;
- `flow_version_ref`, `node_id`;
- `binding_version_ref`: the version pinned by that node;
- `owner_statement`: bounded text the owner approved, in plain words;
- `status`: `active` or `revoked`;
- `granted_by`: ActorRef of kind `owner`; `granted_at`, `revoked_at`;
- `revocation_reason`: the owner's bounded reason, absent while the grant is
  active; written once with `revoked_at` and never rewritten.

A grant names a flow version, so any edit of the flow leaves the new version
without it. A grant cannot name a `destructive` binding; such a node always
asks.

### Identity

entity

### Identity evidence

Substitution: two grants are never interchangeable; each node execution cites
the one it ran under. Continuity: the grant stays the same permission from
granting until revocation.

### Source of truth

The owner's action on the kernel surface.

### Lifecycle candidate

`active -> revoked`. Revocation is final. A grant whose binding is suspended
authorizes nothing while the suspension lasts.

### Persistence candidate

Durable entity of the kernel's operational store.

### Open questions

None.

## Model M44 — OutcomeReconciliation

### Meaning

The recorded determination of whether an effect with an unknown outcome actually
happened, made by reading the owning service.

Candidate fields:

- `reconciliation_id`;
- `node_execution_ref`: the execution whose status is `outcome_unknown`;
- `read_node_execution_ref`: the execution of the binding's outcome-read
  operation;
- `determination`: `effect_applied`, `effect_not_applied` or
  `still_undetermined`;
- `determined_at`.

`effect_applied` lets the run continue with the outputs read from the service.
`effect_not_applied` lets the node be attempted again under the same approval
only when the binding's replay is `safe`, `refuses` or `returns_existing`;
otherwise the node asks the owner again. The kernel never assumes either
answer.

### Identity

value

### Identity evidence

Substitution: equal reconciliation identity is interchangeable. Continuity: a
determination never changes; a later reading is another record.

### Source of truth

The kernel, from the validated output of the owning service's declared read
operation.

### Lifecycle candidate

No independent lifecycle.

### Persistence candidate

Durable evidence attached to the run.

### Open questions

None.

## Model M45 — VocabularyProposal

### Meaning

An agent's or the owner's request to extend the governed vocabulary with one
axis, term or relation, held apart from the vocabulary until the owner decides.

Candidate fields:

- `proposal_id`: stable identity;
- `proposal_kind`: `axis`, `term` or `relation`;
- `proposed_content`: the complete candidate definition of that kind;
- `plain_statement`: the question in the owner's words, such as "is the day the
  goods arrived the same thing as the day on the invoice?";
- `motivating_refs`: the flow proof finding or uncomposable output that exposed
  the gap;
- `agent_rationale`: the proposing agent's optional bounded rationale, kept
  apart from `plain_statement` and never shown as the owner's question;
- `status`: `proposed`, `accepted` or `rejected`;
- `proposed_by`: ActorRef; `decided_by`: ActorRef of kind `owner`;
- `proposed_at`, `decided_at`;
- `resulting_revision_ref`: the axis, term or relation revision created on
  acceptance.

A proposal is not composable. No edge may cite it; only the revision created by
its acceptance can be a composition basis.

### Identity

entity

### Identity evidence

Substitution: two proposals are never interchangeable, even with equal content,
because each records its own motivation and decision. Continuity: the proposal
stays the same request from submission to the owner's decision.

### Source of truth

The kernel's proposal registry; the decision is the owner's.

### Lifecycle candidate

`proposed -> accepted | rejected`. Both ends are final; a rejected idea returns
as a new proposal.

### Persistence candidate

Durable entity of the kernel's operational store.

### Open questions

None.

## Model M47 — KernelInstant

### Meaning

One kernel-owned wall-clock instant used only for operational lifecycle,
security, retry and retention timestamps. It is not a business temporal value
and never substitutes for TemporalValue M08.

Candidate fields:

- `epoch_us`: non-negative integer microseconds since
  `1970-01-01T00:00:00Z`, obtained by flooring the host wall-clock nanosecond
  reading to microseconds.

The representation is intentionally an integer: no naive `datetime`, local
timezone, floating-point epoch seconds or free-form ISO string is persisted as
the canonical kernel timestamp. Human-readable UTC rendering is a presentation
concern.

### Identity

value

### Identity evidence

Substitution: equal `epoch_us` values are interchangeable as the same
operational instant. Continuity: an instant never changes.

### Source of truth

Only `module:system_clock`. Production `now()` obtains one host wall-clock
sample with Python `time.time_ns()` and returns
`KernelInstant(epoch_us = sample_ns // 1_000)`. Tests inject a deterministic
clock and never consult the host wall clock.

### Lifecycle candidate

No independent lifecycle.

### Persistence candidate

Embedded anywhere the kernel records operational timestamps such as
`created_at`, `issued_at`, `submitted_at`, `decided_at`,
`activated_at`, `revoked_at`, `started_at`, `ended_at`,
`executed_at`, `determined_at` or a persisted retry/retention deadline.

### Open questions

None.

