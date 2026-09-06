# State 2 repair — durable archive cross-resource consistency

## Accepted decision A70 — PostgreSQL journal and local byte publication

### Normative rules

PostgreSQL is authoritative for archive metadata, publication recovery state,
and concurrency control. Source content is stored by one Backend-owned local
filesystem store under a required absolute deployment root.

A source candidate is written to a non-public staging reference, flushed,
reopened, and SHA-256 verified before archive metadata may reference it.
The metadata transaction records an `ArchiveBytePublication` and all related
archive changes atomically.

Final publication uses atomic same-filesystem rename to a content-addressed
path. Existing final content may be reused only when reopened bytes match the
expected hash and size; different bytes are never overwritten.

A failure before PostgreSQL commit removes the uncommitted staging candidate.
A failure after commit remains a recoverable `metadata_committed` publication.
Startup recovery must finalize or mark that publication failed. Until final
verification succeeds, archive reads must not report its replica as available.

### Formal invariants

1. Every available `SourceBinaryReplica` has one committed
   `ArchiveBytePublication(state="published")` with the same source identity,
   content hash, size, and final storage reference.
2. No `staged`, `metadata_committed`, or `failed` publication contributes
   to source completeness.
3. One content-addressed final reference never denotes two different hashes.
4. Retrying equivalent bytes produces one logical source replica and preserves
   previously accepted provenance.
5. Cleanup or compensation never deletes a previously published replica and
   never mutates immutable Card or decision evidence.
6. PostgreSQL uniqueness and row locking, not filesystem check-then-act, decide
   conflicting concurrent publication.
7. Staging and final locations must reside on a filesystem that supports atomic
   rename; startup fails closed otherwise.

### Required tests

- crash before metadata commit leaves no accepted metadata or visible bytes;
   [witness: verification:witness_A70]
- crash after commit and before rename is finalized by startup recovery;
- missing or hash-mismatched staged bytes produce a safe failed publication;
- concurrent equivalent requests converge on one logical result;
- concurrent conflicting bytes cannot both publish for one source identity;
- an existing different final file is never replaced;
- archive reads exclude every non-published publication;
- recovery and cleanup preserve all earlier immutable evidence.

### Consequence

`durable_archive` owns the cross-resource state machine. PostgreSQL and
filesystem adapters expose mechanisms only. Required deployment paths and
connection values belong to `config`; no behavioral function reads
environment variables or opens ad-hoc connections.
