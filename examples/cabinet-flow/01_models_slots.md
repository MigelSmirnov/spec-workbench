# State 1 companion — slot, implementation, trial and activation models

## Purpose

This document closes identity and data shape for the pluggable function of
State 0 decisions D0-034, D0-036 and D0-037: the slot and its immutable contract
versions, the immutable implementation identified by the digest of its content,
the sandbox runtime it runs under, the trial corpus and trial evidence, the
deterministic admission verdict and the activation that selects what runs.

Ports are the SemanticPort of `01_models.md` (M05). Nothing here introduces
another way to type data.

## Model M19 — Slot

### Meaning

One continuing named place for replaceable pure behavior. The slot is the name
an agent, a flow author and a trace reader use for "this step", across every
contract version and implementation it will ever have.

Candidate fields:

- `slot_id`: stable namespaced identity, never reused;
- `purpose`: bounded human-readable statement of the one responsibility;
- `status`: `active` or `retired`;
- `created_by`: ActorRef;
- `created_at`.

### Identity

entity

### Identity evidence

Substitution: two slots are never interchangeable, even with identical current
contracts, because flows, traces and trial corpora refer to one of them.
Continuity: the slot stays the same while contract versions are issued,
implementations are replaced and its status changes.

### Source of truth

The kernel's slot registry, written only through the kernel surface.

### Lifecycle candidate

`active -> retired`. A retired slot accepts no new contract version,
implementation or activation. Flow versions that pin it keep running with what
they pinned.

### Persistence candidate

Durable entity of the kernel's operational store.

### Open questions

None.

## Model M20 — SlotContractVersion

### Meaning

One immutable issued contract of a slot: exactly what a function receives and
returns, and within which bounds it must finish.

Candidate fields:

- `slot_id`;
- `contract_version_id`: content-derived identity computed by the kernel;
- `version_number`: ordinal inside the slot;
- `input_ports`: SemanticPort values with direction `input`;
- `output_ports`: SemanticPort values with direction `output`;
- `resource_bounds`: one ResourceBounds;
- `runtime_revision_ref`: the exact SandboxRuntimeRevision the contract is
  written for;
- `issued_by`: ActorRef;
- `issued_at`.

A contract declares no configuration, service, secret, import list or effect. A
function has none of them (D0-034), so there is nothing to declare and nothing
to police.

### Identity

value

### Identity evidence

Substitution: equal slot, ports, bounds and runtime revision yield the same
content-derived identity and are interchangeable; issuing the same content twice
returns the existing version. Continuity: a version never changes. Any
difference is another version, and flows pinning the earlier one are untouched.

### Source of truth

Issued by the kernel from an authoring request, after it verifies that every
port names an accepted semantic-term revision and a known value schema.

### Lifecycle candidate

No independent lifecycle; immutable after issuance.

### Persistence candidate

Durable, referenced by implementations, trial cases, activations, flow nodes and
trace records.

### Open questions

None.

## Model M21 — ResourceBounds

### Meaning

The closed set of limits under which one function execution must complete.

Candidate fields:

- `wall_time_limit`;
- `cpu_time_limit`;
- `memory_limit`;
- `output_size_limit`;
- `process_count_limit`.

Every field is required. The kernel release fixes an upper ceiling for each; a
contract may request less and never more.

### Identity

value

### Identity evidence

Substitution: equal limits are interchangeable. Continuity: bounds have no life
of their own; different limits belong to another contract version.

### Source of truth

The authoring request, clamped by the ceilings of the kernel release.

### Lifecycle candidate

No independent lifecycle.

### Persistence candidate

Embedded in SlotContractVersion and copied into trial and node-execution
evidence as the limits actually enforced.

### Open questions

None.

## Model M22 — SandboxRuntimeRevision

### Meaning

One exact, immutable execution environment for functions: the language, its
interpreter and the fixed set of pure libraries available inside the sandbox.

Candidate fields:

- `runtime_id`: stable name of the runtime line;
- `runtime_revision_id`: digest of the sealed environment image;
- `language`;
- `available_libraries`: names and exact versions;
- `status`: `offered` or `withdrawn`;
- `released_with`: the kernel release that introduced it.

The environment has no network stack, no clock, no entropy source, no
environment variables and no writable path outside one scratch directory that is
destroyed with it.

### Identity

value

### Identity evidence

Substitution: equal image digest is interchangeable. Continuity: a revision
never changes; adding or upgrading a library is another revision, and contracts
written for the earlier one keep running under it.

### Source of truth

The kernel release. No agent and no owner action adds a runtime revision.

### Lifecycle candidate

No independent lifecycle for the revision's content. `status` records only
whether new contract versions may still select it; executions of already pinned
versions continue under a withdrawn revision.

### Persistence candidate

Durable, referenced by contract versions, trial executions and node executions.

### Open questions

None.

## Model M23 — Implementation

### Meaning

One immutable body of code that claims to realize one slot contract version.

Candidate fields:

- `implementation_id`: digest of the content, computed by the kernel over the
  code bytes and the contract version it targets;
- `contract_version_ref`;
- `code_ref`: bounded content-addressed reference to the code bytes;
- `entry_point`: the single callable the sandbox invokes;
- `submitted_by`: ActorRef;
- `submitted_at`;
- `rationale`: bounded text stating what gap or failure it answers, with the
  trace references that motivated it.

An author never supplies the identity. Two submissions of the same bytes for the
same contract version are the same implementation.

### Identity

value

### Identity evidence

Substitution: equal content-derived identity is interchangeable, whoever
submitted it and whenever. Continuity: an implementation never changes; an edit
is another implementation. It is never deleted, so every past run stays
explainable.

### Source of truth

The kernel, from the submitted bytes.

### Lifecycle candidate

No independent lifecycle. Whether it may run is stated by AdmissionVerdict and
SlotActivation, not by a mutable status on the implementation.

### Persistence candidate

Durable, referenced by trial executions, admission verdicts, activations and
node executions.

### Open questions

None.

## Model M24 — TrialCase

### Meaning

One member of a contract version's trial corpus: a typed input, and optionally
the exact output that every implementation of that contract version must
produce for it.

Candidate fields:

- `trial_case_id`: content-derived identity over contract version, inputs and
  expected outputs;
- `contract_version_ref`;
- `inputs`: one bounded value per input port, each carrying the port's exact
  semantic-term revision;
- `expected_outputs`: optional; when present, one bounded value per output port;
- `origin`: `authored` or `captured_from_run`, with the node-execution reference
  when captured;
- `status`: `active` or `withdrawn`;
- `added_by`: ActorRef; `added_at`;
- `withdrawn_by`, `withdrawn_at`, `withdrawal_reason` when withdrawn.

The corpus only grows. A failing real execution can be captured as a trial case,
which is how a repaired slot stays repaired.

### Identity

entity

### Identity evidence

Substitution: trial cases with different content are never interchangeable;
submitting identical content returns the existing case. Continuity: the case
stays the same corpus member while its status moves from active to withdrawn.

### Source of truth

The kernel's trial corpus, written through the kernel surface.

### Lifecycle candidate

`active -> withdrawn`. Withdrawal is final, carries a reason and an actor, and
stays visible in every later admission verdict of that contract version.

### Persistence candidate

Durable entity of the kernel's operational store.

### Open questions

None.

## Model M25 — TrialExecution

### Meaning

The immutable evidence of executing one exact implementation on one exact trial
case inside the sandbox.

Candidate fields:

- `trial_execution_id`;
- `implementation_ref`;
- `trial_case_ref`;
- `runtime_revision_ref`;
- `enforced_bounds`: ResourceBounds;
- `input_digest`, `output_digest`;
- `input_validation`, `output_validation`: verdict with the violated port and
  rule when not conforming;
- `expected_output_match`: `matched`, `mismatched` or `not_stated`;
- `denied_attempts`: each with a closed kind — `network`, `filesystem`,
  `process`, `clock`, `entropy` or `environment` — and a bounded detail;
- `resources_used`;
- `outcome`: `conforming`, `contract_violation`, `expected_output_mismatch`,
  `denied_attempt`, `timeout`, `resource_exhausted`, `crashed` or
  `cleanup_failed`;
- `executed_at`.

`conforming` is recorded only when validation passed, no attempt was denied, the
bounds held, any expected output matched and the environment was destroyed
completely. It is never a default.

### Identity

value

### Identity evidence

Substitution: equal execution identity is interchangeable. Two executions of the
same implementation on the same case are distinct evidence even with equal
outcomes. Continuity: the record never changes.

### Source of truth

The kernel's sandbox supervisor, never the executed code.

### Lifecycle candidate

No independent lifecycle.

### Persistence candidate

Durable evidence, referenced by admission verdicts.

### Open questions

None.

## Model M26 — AdmissionVerdict

### Meaning

The kernel's deterministic decision whether one implementation may be activated,
taken over the complete active trial corpus of its contract version.

Candidate fields:

- `admission_id`;
- `implementation_ref`;
- `considered_trial_executions`: one reference per active trial case;
- `withdrawn_trial_cases`: cases excluded because withdrawn, with reasons;
- `verdict`: `admitted` or `refused`;
- `refusal_reasons`: closed set — `empty_corpus`, `missing_trial_execution`,
  `non_conforming_trial` with the execution reference, `runtime_withdrawn` or
  `slot_retired`;
- `decided_at`.

An empty active corpus refuses. No human or agent can record, override or waive
a verdict; a different verdict requires different evidence.

### Identity

value

### Identity evidence

Substitution: equal admission identity is interchangeable. A later verdict over
a grown corpus is another verdict, not a revision of this one. Continuity: the
record never changes.

### Source of truth

The kernel, computed from trial executions.

### Lifecycle candidate

No independent lifecycle.

### Persistence candidate

Durable evidence, referenced by activations.

### Open questions

None.

## Model M27 — SlotActivation

### Meaning

The immutable record that, from one moment, one contract version is served by
one admitted implementation.

Candidate fields:

- `activation_id`;
- `contract_version_ref`;
- `implementation_ref`;
- `admission_ref`: an `admitted` verdict for that implementation;
- `previous_activation_ref`: absent for the first activation of the contract
  version;
- `activated_by`: ActorRef;
- `activated_at`;
- `reason`: bounded text, required when the activation returns to an earlier
  implementation.

The implementation currently serving a contract version is the one named by its
latest activation. Rollback is a new activation naming an earlier admitted
implementation; nothing is deleted or reopened.

### Identity

value

### Identity evidence

Substitution: equal activation identity is interchangeable. Two activations of
the same implementation at different times are distinct facts of the slot's
history. Continuity: the record never changes; being superseded is a fact about
a later record, not a change of this one.

### Source of truth

The kernel, which records an activation only for an implementation holding an
`admitted` verdict over the corpus as it stands at that moment.

### Lifecycle candidate

No independent lifecycle.

### Persistence candidate

Durable, referenced by flow runs to pin what each function node executed.

### Open questions

None.
