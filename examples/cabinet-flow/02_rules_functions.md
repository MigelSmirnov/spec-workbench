# State 2 — Cabinet Flow function, sandbox and admission rules

## Accepted decision A05 — identity is computed from content by the kernel

### Normative rules

1. `contract_version_id` M20, `implementation_id` M23, `trial_case_id` M24,
   `binding_version_id` M30 and `flow_version_id` M32 are digests the kernel
   computes over a canonical serialization of the record's defining content.
   Author, time and free-text rationale are never part of that content.
2. An authoring request that carries an identity is refused. Identity is never
   accepted from a caller, copied from a file or derived from a name.
3. Submitting content whose identity already exists returns the existing record
   and creates nothing. Authoring is therefore safe to repeat.
4. The canonical serialization is fixed per record kind and versioned with the
   kernel release. A change of serialization is a migration that preserves every
   issued identity; it never re-identifies an existing record.
5. An issued version and a submitted implementation are never edited or
   deleted. Retirement of a slot, flow or binding stops new use and removes
   nothing.
6. Code bytes of an implementation are stored once under their digest and are
   readable only by the sandbox supervisor and, within A22, by an authoring
   agent of that slot.

### Formal invariants

```text
identity(record) = digest(canonical(defining_content(record)))
author, time, rationale NOT IN defining_content

same_defining_content -> same_identity -> one_record
caller_supplied_identity -> refused
issued OR submitted -> never_mutated AND never_deleted
```

### Required tests

1. The same implementation bytes submitted by two delegations at different times
   yield one implementation.
2. A submission carrying its own `implementation_id` is refused.
3. Two contract versions differing only in one resource bound have different
   identities.
4. Re-issuing identical contract content returns the existing version and the
   slot's version count is unchanged.
5. No surface operation edits or deletes an issued version or a submitted
   implementation.

### Consequence

"Which code ran" has one answer that nobody can assert or forge, which is what
the sketch implementation lacked.

## Accepted decision A06 — every function execution is isolated and bounded

### Normative rules

1. A function executes only inside a disposable environment created by the
   sandbox supervisor from one SandboxRuntimeRevision M22, in trial and in real
   runs alike. There is no in-process, trusted or fast path.
2. The environment contains the runtime, the implementation's code, and the
   validated input values of that one execution. It contains no network
   interface, no clock, no entropy source, no environment variable, no
   credential, no handle to the kernel's store and no path to another
   execution's data.
3. The only writable location is one scratch directory inside the environment,
   limited in size and destroyed with it.
4. Input is delivered and output is collected by the supervisor over one
   bounded channel. Output larger than `output_size_limit` is a failure, not a
   truncation.
5. ResourceBounds M21 of the contract version, clamped by the release ceilings,
   are enforced from outside the environment. Exceeding wall time is `timeout`;
   exceeding CPU time, memory or process count is `resource_exhausted`.
6. Every attempt to use something absent — a socket, a path outside scratch, a
   subprocess beyond the limit, the clock, entropy, the environment — is denied,
   recorded as a denied attempt with its kind, and makes the execution fail as
   `denied_attempt` even if the code then returns a conforming output.
7. Completion includes destroying the environment and every descendant process.
   If destruction cannot be confirmed the execution is `cleanup_failed`, its
   output is discarded, and the supervisor refuses further executions until the
   leak is cleared.
8. Because a function has no clock and no entropy, the same implementation on
   the same input under the same runtime revision yields the same output. A
   differing output on re-execution is a kernel defect and is recorded as one.
9. Nothing the code prints, raises or writes is interpreted by the kernel. Only
   the collected output, validated against the contract, has meaning.

### Formal invariants

```text
function_executed -> inside_disposable_environment
environment_contents = {runtime, code, validated_inputs}

denied_attempt_count > 0 -> status != succeeded
bounds_exceeded -> status IN {timeout, resource_exhausted}
cleanup_unconfirmed -> status = cleanup_failed AND output_discarded

same(implementation, input, runtime_revision) -> same(output)
```

### Required tests

1. Code that opens a socket, reads a path outside scratch, reads the clock,
   reads an environment variable or requests entropy fails as `denied_attempt`
   with the matching kind, including when it swallows the error and returns a
   conforming output.
2. A busy loop ends as `timeout`; an allocation loop and a fork loop end as
   `resource_exhausted`; the host stays healthy and no descendant process
   survives.
3. An output one byte over the limit fails and is not truncated.
4. Two executions in parallel cannot observe each other's input, scratch or
   output.
5. Re-executing a succeeded node execution under its pinned runtime reproduces
   the same output digest.
6. A simulated cleanup failure discards the output and stops the supervisor from
   accepting further executions.

Negative fixtures are bounded and synthetic. They never risk a real fork bomb,
decompression bomb or secret.

### Consequence

The agent's code is untrusted forever and that costs nothing: a function can
compute and do nothing else, in trial and in production by the same mechanism.

## Accepted decision A07 — the trial corpus only grows

### Normative rules

1. Every contract version has a trial corpus of TrialCase M24 records. A case's
   inputs carry the exact term revisions and schemas of the contract's input
   ports and are validated when the case is added; a non-conforming case is
   refused.
2. A case may state expected outputs. When it does, an implementation conforms
   on that case only if its validated outputs equal them by digest.
3. Any concluded function NodeExecution M41 may be captured as a case with
   origin `captured_from_run`. Capturing a failed execution records its inputs
   without expected outputs; an authoring actor may then state the correct
   expected outputs as a further case.
4. A case is never edited. A wrong case is withdrawn with a reason and an
   actor; the withdrawal is final and listed in every later admission verdict of
   that contract version.
5. Withdrawing a case that states expected outputs requires the owner when that
   case has ever contributed to an `admitted` verdict. An agent cannot clear its
   own path by withdrawing the case its code fails.
6. Trial values are StoredValues with retention class `trial_corpus` and follow
   A03: an agent sees only cases at or below its disclosure ceiling, and sees
   digest and class for the rest.
7. A new contract version starts with an empty corpus. Cases of an earlier
   version are copied to it only by an explicit request, and only those that
   still validate against the new ports.

### Formal invariants

```text
case_added -> inputs_validate_against_contract_ports
case_content -> immutable
case.status: active -> withdrawn   (final)

withdraw(case) AND case.has_expected AND case.contributed_to_admission
-> actor_kind = owner
```

### Required tests

1. A case with an input of the wrong term revision is refused.
2. A failed production execution is captured; the repaired implementation must
   pass it to be admitted.
3. An agent's withdrawal of an expected-output case that contributed to an
   admission is refused; the owner's is accepted and appears in the next
   verdict.
4. An agent below the case's disclosure class receives the digest and class
   only.
5. Copying cases to a new contract version skips those that no longer validate
   and reports them.

### Consequence

A slot that was repaired stays repaired. The corpus is the slot's memory, and no
author can quietly shorten it.

## Accepted decision A08 — admission is a deterministic verdict over the whole corpus

### Normative rules

1. A trial request executes one implementation on every active case of its
   contract version under A06 and records one TrialExecution M25 per case.
2. AdmissionVerdict M26 is `admitted` only when the active corpus is non-empty,
   every active case has a TrialExecution of this implementation under the
   contract's runtime revision, and every one of them has outcome `conforming`.
3. Any other situation is `refused` with every applicable reason:
   `empty_corpus`, `missing_trial_execution`, `non_conforming_trial` naming the
   execution, `runtime_withdrawn` or `slot_retired`.
4. Admission requires no human. A function is pure by construction, so there is
   no effect for a human to weigh, and a human's approval is never accepted in
   place of evidence.
5. No actor records, edits, overrides or waives a verdict. The way to a
   different verdict is different evidence.
6. A verdict speaks for the corpus as it stood. It is not revised when the
   corpus later grows; A09 governs what growth means for an implementation
   already serving.

### Formal invariants

```text
admitted
<-> active_corpus != empty
    AND for_all active_case: exists trial_execution(implementation, case)
        with outcome = conforming AND runtime = contract.runtime_revision

verdict_recorded_by = kernel
human_approval -/> admitted
```

### Required tests

1. An implementation for a contract version with no cases is refused as
   `empty_corpus`.
2. One non-conforming case among many refuses admission and names that
   execution.
3. A trial interrupted before every case ran yields `missing_trial_execution`,
   not a partial admission.
4. No surface operation lets the owner or an agent set a verdict.
5. The same implementation and corpus yield the same verdict on repetition.

### Consequence

The agent gets an answer in the time it takes to run the corpus, with no human
in the loop, because nothing it can write is able to do harm.

## Accepted decision A09 — activation selects by hash; rollback is another activation

### Normative rules

1. A SlotActivation M27 is recorded only for an implementation whose latest
   AdmissionVerdict is `admitted` and was computed over the corpus as it stands
   at the moment of activation. A stale admission is re-evaluated first.
2. Activation is compare-and-set on `previous_activation_ref`. Of two concurrent
   activations of one contract version, one is recorded and the other is refused
   with the current activation's identity.
3. An agent with authoring delegation may activate. Activating a function
   changes no authority: whether a flow's effects may happen is decided on its
   operation nodes under A11 through A13.
4. The implementation serving a contract version is the one named by its latest
   activation. A contract version with no activation serves nothing, and a flow
   node pinning it is refused at run creation as `slot_unserved`.
5. Rollback is a new activation naming an earlier implementation, with a
   required reason. The earlier implementation must be admitted over the present
   corpus; an implementation that fails a case captured since cannot be returned
   to.
6. When the corpus grows and the serving implementation fails the new case, the
   activation stands and the contract version is marked `known_failing` with the
   failing case. It keeps serving, because on every other input it is exactly as
   correct as before, and withdrawing it would break every flow that pins it.
   `known_failing` is visible to every agent reading the slot and is cleared
   only by activating an implementation admitted over the grown corpus.
7. A run pins, at creation, the SlotActivation of every function node. A later
   activation never changes a run already created.

### Formal invariants

```text
activation_recorded
-> admitted(implementation, corpus_at_activation_time)

serving(contract_version) = latest_activation(contract_version).implementation

rollback -> new_activation AND reason_present
         AND admitted(earlier_implementation, present_corpus)

serving_fails_new_case -> known_failing AND still_serving
run.pinned_activations -> fixed_at_creation
```

### Required tests

1. Activating an implementation admitted before a new case was added triggers
   re-evaluation and is refused when it fails that case.
2. Two concurrent activations leave exactly one recorded.
3. A rollback without a reason is refused; with a reason, to an implementation
   failing a newer case, it is refused.
4. Capturing a failing case marks the contract version `known_failing`, leaves
   flows running, and the mark clears on activating a repaired implementation.
5. A run created before an activation executes the earlier implementation to the
   end.
6. Creating a run of a flow that pins an unserved contract version is refused.

### Consequence

Changing behavior is one record, and undoing it is one record. Nothing is
redeployed, and every past run still names exactly what it executed.
