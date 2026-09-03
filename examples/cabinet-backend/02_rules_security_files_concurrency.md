# State 2 — file and concurrency security rules

## Accepted decision A64 — source files remain non-executable Backend-owned artifacts

State 0 decision A60 identifies photographs, PDFs, filenames, media declarations,
and external storage references as untrusted boundary input. Models M05, M10, and
M11 define immutable content identity, source ownership, and replica custody. A61
remains the authorization authority; A62 remains the interpreted-input authority.

### Normative rules

1. The current product accepts source payloads only through the already accepted
   photograph and PDF attachment/import boundaries. A generic file-upload or public
   byte-retrieval surface is not accepted by this decision.
2. Before normal persistence, Backend enforces a finite configured size limit and a
   closed set of accepted media/type/content checks. A filename, extension, or
   caller-declared media type alone is not acceptance evidence.
3. Unsupported, unreadable, malformed, or resource-exhausting payloads are rejected
   or isolated and cannot acquire a normal archived or verified replica state.
4. Accepted source bytes are data, never executable authority. Parsing and preview
   operate under bounded resources, and payload content cannot select commands,
   templates, interpreters, storage paths, or query structure as required by A62.
5. A source filename is display/provenance metadata only. Backend derives storage
   keys and paths and keeps source bytes outside public or client-controlled roots.
6. Every stored or accessed source is scoped to the exact `invoice_id`, `source_id`,
   Cabinet node, and storage zone represented by M10 and M11. Knowledge of any such
   stable identifier is not authorization proof.
7. Browser and agent clients receive neither filesystem paths nor direct storage
   authority. Any current source-file access occurs only through an exact Backend
   operation authorized under A61. A future byte-download API requires its own
   accepted retrieval and disclosure decision.
8. A failed or partial store/process operation cannot mark the source available,
   verified, or sufficient to clear missing-source status.

### Formal invariants

```text
source_available_or_verified
-> payload_accepted AND content_identity_verified AND replica_committed

filename_or_external_reference -/> storage_path
payload_bytes -/> executable_or_query_structure
stable_source_identifier_known -/> source_access_authorized
```

### Required tests

1. A disallowed type, oversized payload, content/type mismatch, malformed document,
   [witness: verification:witness_A64]
   or bounded-processing failure never produces a normal verified replica.
2. Traversal-like and absolute filenames remain metadata and cannot affect the
   Backend-selected storage location.
3. Source content cannot select an executable, interpreter, template, or query
   structure.
4. Access using only an `invoice_id`, `source_id`, replica ID, or storage reference
   is rejected without authorization for the exact entity and operation.
5. A client response does not disclose a Backend filesystem path or direct storage
   credential.

### Consequence

The accepted local-upload decision owns the product operation and allowed source
selection. A64 closes payload acceptance, path ownership, execution treatment,
storage isolation, and current retrieval authorization without choosing a State 3
module or numeric deployment limits.

## Accepted decision A65 — source attachment is atomic under concurrent calls

The existing local-upload decision already defines one Backend attachment operation
and idempotent replay by exact invoice, source, and content identity. This decision
defines the security invariant that operation must preserve under concurrency. The
separate import decision remains authoritative for atomic manifest acceptance.

### Normative rules

1. The accepted Backend source-attachment operation is the atomic transition
   boundary; this names a product operation, not a future implementation module.
2. Concurrent or repeated requests with the same `(invoice_id, source_id,
   content_hash)` have one logical result and cannot create duplicate source or
   replica evidence.
3. A request for the same exact source identity with conflicting bytes or content
   hash is rejected and cannot replace the accepted content.
4. Distinct source identities for one invoice may commit independently because the
   accepted product supports multi-photo source packages.
5. For one attachment, its source record, verified replica record, source status,
   and missing-source warning become visible as one accepted transition. Partial
   visibility cannot claim success or clear the warning.
6. Missing-source status is recomputed only from committed required-source state.
   A losing or retried concurrent call cannot clear it prematurely.
7. Conflict handling and retry cannot allocate an extra logical source identity,
   overwrite accepted evidence, or mutate the immutable Invoice Card.

### Formal invariants

```text
count(logical attachment for invoice_id, source_id, content_hash) <= 1

same source_id AND different accepted content_hash -> conflict

missing_source_cleared
-> every required source has a committed verified replica
```

### Required tests

1. Two concurrent identical attachments return the same logical outcome and leave
   [witness: verification:witness_A65]
   one source/replica result.
2. Two concurrent conflicting payloads for one source identity cannot both commit.
3. Concurrent attachments for two distinct expected source IDs may both commit
   without overwriting each other.
4. Failure between byte handling and metadata/status handling leaves no visible
   successful partial attachment and does not clear the missing-source warning.
5. Retrying after a conflict or interrupted attempt neither duplicates evidence nor
   edits the accepted Invoice Card.

### Consequence

A65 closes the attachment read-check-mutate race at State 2. Atomicity ownership for
manifest import stays with the accepted import decision; implementation lowering is
deferred and no State 3 owner is introduced.
