# State 1 repair — durable archive runtime evidence

## Accepted model — ArchiveBytePublication

Purpose: durable recovery evidence for one attempt to publish verified source
bytes into Backend-owned local custody.

Identity: entity, preserved by `publication_id`.

Fields:

- `publication_id: str`;
- `source_id: str`;
- `invoice_id: str`;
- `content_hash: str`;
- `size_bytes: int`;
- `staging_reference: str`;
- `final_reference: str`;
- `state: str`;
- `created_at: datetime`;
- `updated_at: datetime`;
- `failure_code: str | None`.

Lifecycle:

```text
staged -> metadata_committed -> published
       -> failed
metadata_committed -> failed
```

Only `published` authorizes a `SourceBinaryReplica` to be reported as
available. A failed or pending publication remains recovery evidence and is not
normal archive truth.

The record is mutable only through the bounded publication lifecycle. It does
not replace immutable Card revisions, source provenance, incomplete-source
acceptances, or source-loss decisions.

## Accepted boundary types

The runtime requires two narrow mechanism boundaries:

- archive persistence/unit-of-work for locking and atomic metadata changes;
- source-byte custody for staging, reopening, hash verification, atomic
  same-filesystem publication, and safe staging cleanup.

These boundaries do not own archive acceptance, completeness, provenance,
quarantine, or recovery policy. Those decisions remain in
`module:durable_archive`.

## Placeholder resistance

A generic repository, arbitrary path string, or `dict` transaction context is
not sufficient. The later contracts must make the publication lifecycle and
byte-custody operations explicit enough that an implementation cannot report
availability without committed metadata and verified final bytes.
