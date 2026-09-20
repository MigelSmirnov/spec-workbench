# State 5 — Cabinet Flow run-spool operations

The run spool carries files only for the lifetime of one real flow run. It
identifies and bounds bytes without interpreting their business content, and it
never becomes durable custody or a trial-fixture store.

## `public_op:run_spool.receive_file`

### Owner

`module:run_spool` owns intake of one file produced during a run, including
digest computation, observed media type, per-file and per-run bounds, and
creation of SpooledBytes M46.

### Callers

`module:sandbox_supervisor` calls it while collecting a function-node file
output. `module:service_transport` calls it while streaming an operation-node
file response into the kernel.

### Inputs

The exact run, producing node/element and output-port identities; the bounded
byte stream; the target port's accepted media types and size ceiling; and the
output disclosure class already determined by the owning execution path. A
filename extension, caller-provided digest or caller-provided media type is not
accepted as evidence.

### Outputs

One SpooledBytes reference containing the run identity, content digest, observed
size, observed media type, disclosure class and producing node/port identity.

### Observable effect

Bytes are streamed into the run's private spool while digest, size and media
type are observed. The operation may create one temporary spool object; it does
not persist a StoredValue or business file.

### Enforces

The bytes belong to the named live run and producing execution; media type is
derived from content and accepted by the exact output port; the port-specific
limit and injected M48 `run_spool_file_bytes_max` both hold for one file, and
the injected M48 `run_spool_total_bytes_max` holds for the whole live run
during streaming; incomplete or excess input is discarded; no decoding,
rendering or parser-specific business interpretation occurs.

### Errors

Unknown or terminal run, stale producing execution, media mismatch, size
overflow, broken stream, digest/integrity failure and unavailable spool storage
are typed failures. A partial file never becomes SpooledBytes.

### State impact

At most one temporary run-spool object is created. Durable run and trace
records are written by their owning modules.

## `public_op:run_spool.deliver_file`

### Owner

`module:run_spool` owns bounded delivery of one existing SpooledBytes object
to the next execution boundary of the same run.

### Callers

`module:sandbox_supervisor` calls it to mount or stream a validated function
input into the disposable sandbox. `module:service_transport` calls it to
stream the declared request body of an operation node.

### Inputs

The exact SpooledBytes reference; same-run consuming node/element and input
port; the port's accepted media types and size ceiling; and a bounded
destination supplied by the sandbox or transport. Trial fixtures are not valid
inputs to this operation.

### Outputs

A delivery result containing the exact content digest, delivered byte count,
observed media type and completion status. No host spool path is returned.

### Observable effect

The existing bytes are streamed read-only to exactly one declared consumer
boundary. Delivery neither transfers custody nor removes the spool object.

### Enforces

Same run; exact source digest; target port accepts observed media type and size;
streamed delivery without unbounded buffering; no mutation of source bytes; no
redirect to an arbitrary host/path; and no use for trial fixtures or durable
business files.

### Errors

Missing/released spool object, run mismatch, invalid target port, media/size
mismatch, destination failure, short write/read and integrity mismatch are
typed failures. The caller receives no substitute or fallback bytes.

### State impact

None beyond bounded delivery evidence local to the spool. File lifetime is
unchanged.

## `public_op:run_spool.describe_file`

### Owner

`module:run_spool` owns the safe description and purpose-scoped read access
needed to preview or deliberately capture one live run file.

### Callers

`module:owner_authority` calls it when constructing an owner approval preview.
`module:trial_corpus` calls it when a concluded function execution is
explicitly captured as a trial case.

### Inputs

The exact live SpooledBytes reference; caller purpose `owner_preview` or
`trial_capture`; resolved actor/authority context when required; and the
expected run/node/port identity. Raw host paths are never accepted or returned.

### Outputs

The immutable descriptor: digest, size, observed media type, disclosure class
and producer identity. For an authorized purpose it also yields a bounded
read-only stream/lease over those exact bytes: full preview for the owner, or a
single capture stream for `module:trial_corpus`. Agents otherwise receive only
the metadata allowed by their disclosure ceiling.

### Observable effect

Description alone has none. A purpose-scoped stream may read the live bytes but
cannot mutate or extend their spool lifetime. Trial persistence occurs only
when `module:trial_corpus` stores the captured stream as a trial StoredValue.

### Enforces

Exact live-file identity; disclosure ceiling; owner-only full preview where
required; protected personal-data trial capture requires the owner decision
defined by A07; the stream is bounded to the named digest and cannot expose
another run's file or spool layout.

### Errors

Released or missing file, stale run/node reference, unauthorized preview or
protected capture, disclosure violation, integrity mismatch and unavailable
stream are explicit. Metadata is never fabricated from a filename.

### State impact

None in the spool. A later trial-corpus write is owned by
`module:trial_corpus` and `module:value_store`.

## `public_op:run_spool.release_run_files`

### Owner

`module:run_spool` owns final deletion of all SpooledBytes belonging to a run
that is terminal.

### Callers

`module:run_executor` calls it when a run reaches `succeeded`, `failed`,
`refused` or `cancelled`. The long-lived `boundary:kernel_process` also
calls it during `flow:expire_evidence` as an idempotent recovery sweep for
already-terminal runs.

### Inputs

The exact run identity and authoritative terminal-state evidence. The caller
cannot select individual files to preserve or delete, and no age threshold can
override non-terminal state.

### Outputs

A deterministic cleanup result with files/bytes removed and explicit failures;
repetition after complete cleanup returns an empty successful result.

### Observable effect

Every remaining spool object for the terminal run is deleted and its temporary
storage reclaimed. Durable descriptors already recorded in trace or approval
evidence remain.

### Enforces

Terminal run required; all-or-complete bounded cleanup for the run; no deletion
from a non-terminal run; no effect on trial fixtures, StoredValues or
service-owned files; idempotent restart recovery.

### Errors

Unknown run, non-terminal state, inconsistent ownership, unavailable spool
storage or incomplete deletion is explicit. A cleanup failure is never reported
as complete and may be retried by the maintenance sweep.

### State impact

Temporary SpooledBytes content for the terminal run is removed. Durable run,
trace, approval and value-store records are unchanged.
