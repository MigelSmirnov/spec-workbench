# State 5 — Cabinet Flow slot-activation operations

Slot activation selects which admitted implementation serves one immutable
contract version. Selection is append-only and compare-and-set; rollback is
another activation. Contract health is derived from immutable evidence and is
not a second mutable source of truth.

## `public_op:slot_activation.activate_implementation`

### Owner

`module:slot_activation` owns append-only selection of one implementation for
one exact contract version under A09.

### Callers

`module:kernel_surface` calls it from the fixed `activate` operation after
the actor is authorized for implementation activation.

### Inputs

The resolved ActorRef; exact contract-version and implementation references;
the expected current/previous SlotActivation for compare-and-set; and no
caller-authored admission verdict or health flag. The operation resolves the
exact contract and owning-slot status through
`module:slot_registry.contract_version`, exact implementation metadata through
`module:slot_registry.implementation_record`, the latest immutable verdict
from `module:admission.current_admission`, and the exact current active-corpus
snapshot from `module:trial_corpus.active_corpus`.

### Outputs

One new immutable SlotActivation M27 containing the contract version,
implementation, fresh admitted-verdict reference, previous activation,
activating ActorRef and time; or a typed refusal carrying the actual current
activation when compare-and-set loses.

### Observable effect

Exactly one activation record may be appended. The selected implementation
becomes the one returned by `serving_activation` for new Runs. Existing Runs
keep the SlotActivation they already pinned.

### Enforces

Implementation belongs to the exact contract version; slot/contract is not
retired; latest verdict is `admitted`; that verdict covers the active corpus
as it stands now and the required runtime revision; expected previous
activation matches exactly; actor has authoring activation permission; no flow
authority or service-effect permission is created by activation.

### Errors

Absent/refused admission, corpus growth making the verdict stale, mismatched
implementation/contract, retired slot, unavailable corpus evidence, stale
compare-and-set and persistence failure are typed refusals. Stale admission is
never treated as current; the caller must obtain fresh trial evidence before
selection.

### State impact

One immutable SlotActivation may be appended. Implementations,
AdmissionVerdicts, TrialCases, earlier activations and already-created Runs are
unchanged.

## `public_op:slot_activation.rollback_activation`

### Owner

`module:slot_activation` owns rollback as a new immutable activation naming an
earlier implementation.

### Callers

`module:kernel_surface` calls it from the fixed `activate` operation when the
request explicitly names rollback and supplies the bounded reason.

### Inputs

The resolved ActorRef; exact contract version; earlier implementation to return
to; expected current SlotActivation; non-empty bounded reason; and no request to
delete or reopen activation history.

### Outputs

A new SlotActivation naming the earlier implementation, its fresh admitted
verdict over the present active corpus, the immediately previous activation and
the rollback reason; or a typed refusal.

### Observable effect

One new activation becomes current. No earlier record is mutated or deleted and
no running flow instance is repinned.

### Enforces

All normal activation rules plus mandatory reason; target implementation has a
fresh `admitted` verdict over the present corpus; an implementation known to
fail a newer active case cannot be restored; compare-and-set prevents competing
rollback/activation from both winning.

### Errors

Missing/oversized reason, target never belonging to the contract, stale or
refused admission, newer failing-case evidence, lost compare-and-set, retired
slot and transactional failure are explicit refusals.

### State impact

Exactly one immutable SlotActivation may be appended. History remains complete.

## `public_op:slot_activation.serving_activation`

### Owner

`module:slot_activation` owns the authoritative answer to which
SlotActivation currently serves one contract version.

### Callers

`module:run_executor` calls it while creating a Run so the exact activation is
pinned before execution. `module:kernel_surface` calls it when composing slot
inspection for an authenticated reader.

### Inputs

The exact contract-version reference and, for a surface read, the resolved
ActorRef/disclosure context. A caller cannot ask for "latest implementation"
without the activation record or substitute another hash.

### Outputs

The latest immutable SlotActivation and its implementation/admission references,
or an explicit `unserved` result when no activation exists. Surface output is
bounded and contains no implementation body unless separately permitted by the
owning authoring view.

### Observable effect

None.

### Enforces

Latest activation by exact contract version; immutable selection history; no
fallback to most recently submitted or admitted implementation; a contract with
no activation serves nothing.

### Errors

Unknown/retired contract, unauthorized surface inspection and unreadable
activation evidence are explicit. Absence of activation is `unserved`, never
an inferred default.

### State impact

None.

## `public_op:slot_activation.contract_health`

### Owner

`module:slot_activation` owns the deterministic derived health view of the
currently serving implementation under A09.

### Callers

`module:kernel_surface` calls it while composing slot inspection and repair
views.

### Inputs

The exact contract-version reference and reader/disclosure context. The module
resolves the current serving activation, latest admission evidence, exact active
corpus from `module:trial_corpus.active_corpus`, and bounded immutable
slot-scoped execution evidence from `module:trace_journal.slot_evidence`.
There is no caller-authored `known_failing` flag.

### Outputs

A bounded view containing the serving SlotActivation when present; whether its
latest admitted verdict is fresh for the exact current corpus; a boolean
`known_failing`; and, only when true, the exact active case/execution evidence
that proves the serving implementation fails that regression. If corpus growth
has made admission stale but no failure is yet evidenced, the view reports that
freshness fact without inventing failure.

### Observable effect

None. Health is recomputed from immutable activation, corpus, admission and
execution evidence on each read; no mutable health record is written.

### Enforces

`known_failing` requires concrete evidence tied to the currently serving
implementation and an active case; stale admission alone is not called failure;
withdrawn cases do not establish current failure; a later activation admitted
over the grown corpus yields no inherited failing flag; serving selection is
never changed by health inspection.

### Errors

Unknown contract, unreadable serving/admission/corpus/trace evidence,
inconsistent references and unauthorized inspection are explicit. Missing
evidence cannot be converted to healthy or failing by guess.

### State impact

None.
