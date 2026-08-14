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
