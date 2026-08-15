# Stage 8.1 review — `durable_archive`

## Result

`AMBIGUITY`

The assembled slice is structurally complete (`7` contracts, `27` generation
notes, no structural blocks), and its archive policy is sufficiently explicit.
The module is nevertheless not implementation-complete for the required local
Linux deployment.

## Closed behavior

- manifest acceptance and idempotent replay;
- immutable Card revision preservation;
- classified rejection and quarantine outcomes;
- incomplete-source acceptance and source-loss history;
- per-file attachment outcomes, integrity checks, and concurrency rules;
- authoritative durable-acceptance and archive reads.

## Unresolved implementation boundary

The deterministic persistence projection defines stored record classes and their
storage representation. It does not provide a runtime repository, transaction,
or unit-of-work object to the generated behavioral functions.

The module also owns source-byte custody while hiding physical layout, but no
filesystem/blob-store port or concrete local implementation is declared. In
particular, `attach_local_source` receives bytes and must atomically establish a
`SourceBinaryReplica.storage_reference`, yet its contract has no declared means
to store or verify those bytes.

Consequently the Factory has no unique accepted answer for:

1. how behavioral functions read and mutate the PostgreSQL archive records;
2. how source bytes are written, reopened, verified, and removed after a failed
   metadata transaction;
3. how database and byte-store effects implement the accepted no-partial-success
   invariant;
4. which concrete implementations bootstrap supplies on local Linux.

## Required repair direction

Return to the earliest affected design state and declare narrow runtime ports for
archive persistence/unit-of-work and source-byte custody, concrete PostgreSQL and
local-filesystem implementations, and their bootstrap composition. Keep archive
acceptance policy inside `durable_archive`; adapters must provide mechanisms only.

After propagation through contracts and generation notes, rebuild this slice and
repeat the Stage 8.1 review.

## Repair implementation checkpoint

Status: **STALE — semantic repair assembled; deterministic slice rerun required**.

The accepted repair now declares:

- ArchiveBytePublication as the durable PostgreSQL recovery journal entity;
- ArchiveUnitOfWork and SourceByteStore as narrow mechanism ports;
- PostgresArchiveUnitOfWork and LocalFilesystemSourceByteStore as concrete local
  Linux implementations;
- DurableArchiveService as the single cohesive dependency received explicitly
  by behavioral consumers;
- staged, flushed, reopened and hash-verified candidates;
- one metadata transaction for journal plus archive mutation;
- content-addressed same-filesystem atomic publication;
- pre-commit cleanup and post-commit startup recovery;
- fail-closed bootstrap and app-state injection;
- typed unit-of-work methods for every accepted archive mutation.

Connector-side closure checks found and repaired two assembly defects:

1. duplicate ownership of the interface symbols between models and
   durable_archive;
2. an incomplete unit-of-work surface that originally covered recovery but not
   all existing archive mutations.

The current assembly has no duplicate symbol owners, no dependency edge to a
symbol outside its provider, no unowned contract, and all three interfaces have
method contracts. Consumer review also removed unnecessary archive parameters
from get_sync_status and refresh_estimate_snapshot and added explicit app-state
wiring notes to every real archive consumer.

Do not change this record to PASS until design_module_review.py rebuilds the
exact durable_archive slice, structural review reports zero blocks, the new
slice SHA-256 is stored in 81_module_review_status.json, and the rebuilt packet
passes the manual adversarial review.

