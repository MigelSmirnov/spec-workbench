# State 5 — Cabinet Flow trial-corpus operations

The trial corpus is the append-only memory of a contract version. Cases are
immutable after creation; withdrawal is a final visible fact, and durable file
fixtures are StoredValues rather than live-run spool objects.

## `public_op:trial_corpus.add_trial_case`

### Owner

`module:trial_corpus` owns validation and insertion of one authored TrialCase
M24 into one exact contract version's corpus.

### Callers

`module:kernel_surface` calls it from the closed `author` operation after
authorizing an authoring actor and obtaining kernel-computed identity evidence.

### Inputs

The resolved ActorRef; exact contract-version reference; one complete typed set
of inputs using the contract's semantic-term revisions and schemas; optional
exact expected outputs; and, for a `byte_stream` input, one bounded fixture
stream accepted under the fixture ceiling. No externally supplied trial-case ID,
digest, port substitution or expected-output wildcard is accepted.

### Outputs

The immutable active TrialCase reference, its kernel-computed content identity
and the StoredValue references for its inputs/expected outputs. Repeating
identical content returns the existing case rather than creating a duplicate.

### Observable effect

Validated values and any fixture bytes are stored through
`module:value_store` with retention class `trial_corpus`, then exactly one
TrialCase may be appended. No implementation is executed and no admission or
activation changes.

### Enforces

Exact contract ports, term revisions, schemas and carriage; one value per
required input; bounded fixture size; expected outputs, when stated, conform to
the exact output ports; content-derived identity; immutable case content;
authoring actor visibility under its disclosure ceiling.

### Errors

Unknown/retired slot or contract, wrong term/schema/carriage, missing or extra
port, oversized fixture/value, unsupported media type, conflicting existing
content and durable-store failure are typed refusals with no partial case.

### State impact

One immutable active TrialCase and its retained StoredValue references may be
created idempotently. Existing cases, admissions and serving activation are
unchanged.

## `public_op:trial_corpus.capture_trial_case`

### Owner

`module:trial_corpus` owns conversion of one concluded real function execution
into immutable corpus evidence with origin `captured_from_run`.

### Callers

`module:kernel_surface` calls it from authoring repair flow or from the
owner-decision path when protected personal-data capture requires the owner.

### Inputs

The resolved ActorRef; exact slot/contract version and concluded function
NodeExecution reference; the selected execution inputs to preserve; optional
separately authored expected outputs are not inferred from a failure. The module
validates the execution through `module:trace_journal.slot_evidence`. Any live
file input is read from `module:run_spool.describe_file` while that run still
holds the exact digest.

### Outputs

One active TrialCase with origin `captured_from_run`, source NodeExecution
reference and immutable input StoredValue references. A failed execution is
captured without expected outputs; a correct expectation must be authored as
explicit corpus data.

### Observable effect

The exact execution inputs are copied into trial-corpus retention. A live spool
file, when present, is deliberately copied into a `byte_stream` StoredValue;
the original SpooledBytes remains owned by the run until normal release.

### Enforces

Source is a concluded function execution of the exact slot/contract; captured
values/digests equal execution evidence; no unrelated run facts are copied;
fixture bounds and port validation still apply; capturing a
`personal_data` file for installation-lifetime retention requires the active
owner; an agent cannot turn inaccessible content into a fixture by reference.

### Errors

Wrong slot/contract/execution, non-concluded or operation-node execution,
released/mismatched live file, unavailable value bytes, disclosure violation,
personal-data capture without owner, oversized fixture and transactional write
failure are refused without a partial case.

### State impact

One immutable TrialCase and retained value/fixture references may be appended.
After commit, the corpus module asks
`module:slot_activation.contract_health` to refresh derived serving health
from this exact captured failure; it does not change the serving activation.

## `public_op:trial_corpus.withdraw_trial_case`

### Owner

`module:trial_corpus` owns the final `active -> withdrawn` transition of one
TrialCase.

### Callers

`module:kernel_surface` calls it from authoring for an unprotected withdrawal
or from `owner_decide` when the case is protected.

### Inputs

The resolved ActorRef; exact active TrialCase; expected active state; bounded
withdrawal reason; and evidence whether the case has expected output and has
ever contributed to an admitted verdict.

### Outputs

The same TrialCase in final `withdrawn` status with actor, time and reason, or
a typed refusal. Its content and fixture identities remain immutable and visible
to later admission history.

### Observable effect

Exactly one case may become withdrawn. No case content is edited or deleted and
no previous AdmissionVerdict is rewritten.

### Enforces

Final one-way transition; compare-and-set; owner required when an
expected-output case ever contributed to an admitted verdict; an author cannot
withdraw its own blocking protected regression case; history remains visible.

### Errors

Unknown case, wrong contract, already withdrawn/conflicting repeat, stale state,
protected withdrawal by a non-owner and persistence failure are refused
atomically.

### State impact

Only the TrialCase status metadata changes to withdrawn. Existing verdicts,
activations, executions and retained historical references remain.

## `public_op:trial_corpus.copy_cases_to_version`

### Owner

`module:trial_corpus` owns explicit copying of still-valid corpus cases from an
earlier contract version into a new contract version.

### Callers

`module:kernel_surface` calls it from the closed authoring flow after the new
contract version exists.

### Inputs

The resolved authoring ActorRef; exact source and target contract versions of
the same slot; bounded selection of source active cases or the complete active
source corpus. No inheritance flag or implicit copy on contract creation is
accepted.

### Outputs

A deterministic report of copied target TrialCase references and skipped source
cases, each skip naming the target-port validation reason. Copied cases receive
target-version content identities; source cases are untouched.

### Observable effect

For each still-valid selected case, a new immutable case may be appended for
the target contract version while reusing identical StoredValue content by
digest where permitted.

### Enforces

The target version begins empty; every copied input and expected output
revalidates against the target ports, term revisions, schemas, carriage and
bounds; invalid cases are skipped explicitly rather than coerced; no withdrawn
case becomes active by accident.

### Errors

Unrelated slot versions, unknown source/target, retired target, invalid
selection and atomic storage failure are explicit. Per-case incompatibility is
reported as a skip, not silently transformed.

### State impact

Only new target-version TrialCases and necessary retention references are
appended. Source corpus, admission history and activations do not change.

## `public_op:trial_corpus.active_corpus`

### Owner

`module:trial_corpus` owns the authoritative current active-case snapshot for
one contract version.

### Callers

`module:admission` calls it to execute the complete corpus.
`module:slot_activation` calls it to establish admission freshness and derived
contract health. `module:kernel_surface` calls it when composing the bounded
slot inspection view.

### Inputs

The exact contract-version reference and a reader/disclosure context when
content is requested. Internal admission/activation callers receive exact
evidence references rather than an actor-controlled filter.

### Outputs

A deterministic ordered snapshot of every active TrialCase plus a content
identity/digest for that exact active set. Withdrawn cases are listed separately
when historical admission context requires them. Case values above a surface
reader's disclosure ceiling are reduced to digest-and-class views.

### Observable effect

None.

### Enforces

Complete active set for internal admission/health use; no caller-selected
omission; deterministic ordering and snapshot identity; disclosure ceiling on
surface reads; withdrawn cases never count as active but remain historical
facts.

### Errors

Unknown/retired contract, unauthorized surface reader, invalid cursor and
unreadable corpus evidence are explicit. Internal callers never receive a
partial corpus labelled complete.

### State impact

None.
