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
- `size`;
- `disclosure_class`: copied from the port that produced it;
- `retention_class`: `run_evidence`, `trial_corpus` or `approval_evidence`;
- `held_until`: absent for `trial_corpus`.

A StoredValue is never a business record. It is what passed through the kernel,
kept so that a run can be explained; the fact it describes lives in the
microservice that owns it. Source bytes such as a photo are never stored here:
an edge carries a SourceReference (M13) and the bytes stay with the owning
service.

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
- `waiting_on`: the node identities the run is stopped at, with the reason —
  `owner_approval`, `service_unreachable`, `binding_suspended` or
  `outcome_unknown`;
- `in_flight_effect_attempts`: for each non-read operation being invoked, the
  node, map index, attempt number and idempotency-key digest, recorded durably
  before the call and cleared only by the concluding NodeExecution. An entry
  found at restart is an effect whose outcome is unknown (A14, A18);
- `outputs`: one StoredValue per flow output port once produced;
- `created_at`, `ended_at`.

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

The owner's recorded decision about one exact effect that one run is about to
perform.

Candidate fields:

- `approval_id`;
- `run_id`, `node_id`;
- `binding_version_ref`;
- `service_instance`;
- `preview_value_refs`: the StoredValues of the binding's preview ports, exactly
  as shown; for a mapped node, those of every element of the collection;
- `preview_digest`: digest over the binding version, the instance and the
  digests of all input values of the node — for a mapped node, of every
  element — not only the previewed ones;
- `decision`: `approved` or `denied`;
- `decided_by`: ActorRef, always of kind `owner`;
- `decided_at`.

The kernel invokes the operation only with inputs whose digest equals the
approved preview. A different input is a different effect and needs another
approval. One approval of a mapped node covers the whole collection it listed.

### Identity

value

### Identity evidence

Substitution: equal approval identity is interchangeable. Approvals of equal
previews in different runs are distinct decisions. Continuity: a decision never
changes and is never reused by another node execution.

### Source of truth

The owner's action on the kernel surface.

### Lifecycle candidate

No independent lifecycle.

### Persistence candidate

Durable evidence, referenced by the node execution it authorized.

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
- `granted_by`: ActorRef of kind `owner`; `granted_at`, `revoked_at`.

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
