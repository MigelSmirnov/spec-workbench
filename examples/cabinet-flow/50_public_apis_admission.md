# State 5 — Cabinet Flow admission operations

Admission exposes orchestration and evidence lookup, not a caller-controlled
decision. `decide_admission` remains a hidden step of `module:admission`: no
surface or peer module can record, edit, override or waive a verdict.

## `public_op:admission.run_trial`

### Owner

`module:admission` owns complete-corpus trial orchestration and the
deterministic AdmissionVerdict required by A08.

### Callers

`module:kernel_surface` calls it from an authorized `request_trial` operation.
The ActorRef authorizes the request but is not an input to the verdict.

### Inputs

Exact contract-version and implementation references. The module resolves the
active corpus from `module:trial_corpus`, the contract's exact sandbox runtime
and bounds, and the immutable implementation bytes. A caller cannot select or
omit cases, supply expected outcomes, choose a runtime, or provide a verdict.

### Outputs

One immutable AdmissionVerdict reference plus the ordered references to every
TrialExecution considered. The verdict is `admitted` only for a non-empty
corpus with one conforming execution for every active case under the contract's
runtime revision; otherwise it is `refused` with every applicable closed
reason.

### Observable effect

The operation executes every active case in a fresh disposable sandbox,
appends one TrialExecution per attempted case, then internally derives and
appends one kernel-authored AdmissionVerdict. It never activates an
implementation.

### Enforces

One exact implementation, contract and runtime; a snapshot of the complete
active corpus; strict input and output validation; expected-output comparison
by digest; no partial admission; no human approval or agent assertion as
evidence; deterministic ordering and complete refusal reasons.

### Errors

An empty corpus yields `empty_corpus`; an interrupted or absent case execution
yields `missing_trial_execution`; any non-conforming execution is named by
`non_conforming_trial`; withdrawn runtime and retired slot produce their closed
reasons. Infrastructure failure that prevents a complete verdict refuses
closed and cannot fabricate `admitted`.

### State impact

Append-only TrialExecution records and exactly one immutable AdmissionVerdict
are created. Corpus membership, contracts, implementation bytes, slot
activation and human authority remain unchanged.

## `public_op:admission.current_admission`

### Owner

`module:admission` owns authoritative lookup of the latest immutable verdict
and its exact evidence scope.

### Callers

`module:slot_activation` calls it immediately before activation or rollback to
verify that the target implementation is admitted over the corpus as it stands.

### Inputs

Exact contract-version and implementation references. No caller-selected
verdict, case set, status override or fallback is accepted.

### Outputs

The latest AdmissionVerdict for the exact pair, including its active-corpus
snapshot identity, runtime revision, execution references and all refusal
reasons; or an explicit result that no verdict exists. It never returns an
implicit success.

### Observable effect

None. The operation reads immutable admission evidence and does not re-run a
trial, revise a verdict or activate an implementation.

### Enforces

Exact contract/implementation matching, immutable verdict identity, corpus and
runtime provenance, and the distinction between an earlier admitted verdict
and freshness for the current active corpus. Corpus growth never rewrites an
old verdict.

### Errors

Unknown contract or implementation, mismatched pair, absent verdict and
unreadable evidence are explicit typed results or refusals. The operation never
substitutes the most recent verdict of another implementation or treats missing
evidence as admitted.

### State impact

None.

