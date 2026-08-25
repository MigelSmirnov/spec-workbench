# State 2 — Evening synchronization and operations rules

## Reciprocal wire lock with `cabinet_backend`

The accepted local Backend is the wire authority for the first release. Cabinet
Web MUST use its exact typed transfer shapes rather than a Web-local projection:

```text
VpsInvoiceTransferPackage:
  synchronization: InvoiceSynchronization
  manifest: InvoiceTransferManifest
  card_revision: StoredInvoiceCardRevision
  source_replicas: tuple[SourceBinaryReplica, ...]
  assignment_observation: CardObjectAssignmentObservation | None

InvoiceTransferManifest:
  manifest_id, invoice_id, card_revisions, source_references,
  manifest_version, generated_at, manifest_hash

InvoiceTransferReceipt:
  synchronization_id, import_id, idempotency_key, invoice_id, manifest_hash,
  result, accepted_card_hashes, accepted_source_hashes, receipt_at,
  safe_error_code
```

`manifest_version` is a string wire value; `card_revisions` is a tuple whose
first-release cardinality is exactly one. Receipt fields are plural hash tuples
and use `receipt_at`; singular `accepted_card_hash`, `received_at`, or a local
integer manifest version are not wire-compatible aliases. The package is the
typed JSON metadata plus streamed binary source parts; a free-form text blob or
base64 payload is forbidden.

## Producer path: confirmed Invoice to VPS working set

`confirm_invoice` MUST atomically create or idempotently retain one immutable
`InvoiceWorkingSetItem` and its `InvoiceTransferManifest` for the exact
confirmed Card revision and verified source membership. This is the producer
edge consumed by `discover_invoice_work`; discovery MUST read this durable set,
not an empty in-memory catalogue. A changed Card revision or source set creates
a new manifest/item and never mutates an issued one.

The producer records the exact `CardObjectAssignmentObservation` when available,
carried unchanged in the package. Missing explicit Registry provenance remains
`label_only`, `unassigned`, or `needs_review`; it is never inferred during
discovery or packaging.

## Accepted decision A08 — local Backend pulls one exact immutable Invoice package

### Normative rules

1. Only an authenticated active M17 local Backend node initiates the evening
   connection. Cabinet Web never calls into the local network.
2. Work discovery returns only exact available M03 Invoice revisions and source
   membership observed through M27. Every item contains `invoice_id`, exact Card
   revision/content hash, `manifest_id`/hash, ordered source
   IDs/hashes/sizes/media types, and a bounded continuation cursor; it never
   exports Provider, Client, Project, shopping-list, estimate, or unrelated
   project data. The local Backend pulls by the returned `manifest_id`.
3. M21 binds exactly one complete canonical Invoice Card revision, manifest
   version/hash, required source identities, and every included byte
   hash/size/media type. `len(card_revisions) = 1` is a first-release reciprocal
   invariant even if the local representation remains tuple-shaped.
4. One changed Card revision or source content set requires another manifest;
   an issued manifest never mutates.
5. M22 records issue to the exact node and idempotency scope before bytes are
   exposed. Delivery or HTTP success never means local durable acceptance.
6. Only an exact M23 receipt issued by local `cabinet_backend` for the same
   manifest/hash can acknowledge accepted or already-accepted local custody.
7. `quarantined`, `rejected`, and `unknown` remain truthful non-complete results.
   An uncertain response is reconciled by exact issuance/receipt identity.
8. Incompatible accepted revisions produce M28; neither node chooses a winner
   by arrival time or overwrites the other revision.
9. Contract/version incompatibility fails before package issue and exposes a
   bounded upgrade-required outcome.
10. JSON metadata is bounded separately from byte content. Source bytes are
    streamed as bounded binary parts, never base64-encoded inside JSON. The
    local consumer writes each part to private temporary staging, verifies its
    declared hash before acceptance, and only then creates its own local
    `storage_reference`; no VPS path or storage credential crosses the wire.
11. The request timeout is 120 seconds. Compatibility, discovery, and status
    reads may use shorter operation-specific budgets, but a timeout after
    issuance is `outcome_unknown` and permits only read-only reconciliation—no
    automatic pull retry or second logical issuance.
12. M29 is produced by Cabinet Web for the exact Invoice revision and travels
    unchanged inside the package. Only an explicitly owner-selected
    `project_id` with exact catalogue/snapshot provenance is assigned; otherwise
    the observation stays `label_only`, `unassigned`, or `needs_review`. Neither
    transport nor local acceptance derives a project mapping from Card ID or
    label.

### Formal invariants

```text
invoice_package_issued
-> authenticated_active_local_node
   AND manifest_hash_verified
   AND len(manifest.card_revisions) = 1
   AND exact_card_revision_available

local_acceptance_visible
-> receipt.manifest_hash = issuance.manifest_hash
   AND receipt.result in {accepted, already_accepted}

transport_success -/> durable_local_acceptance
revision_disagreement -/> last_write_wins
wire_source_part -/> storage_reference_or_vps_path_or_storage_credential
timeout_after_issuance -/> automatic_retry
card_id_or_label -/> registry_project_assignment
```

### Required tests

1. Non-Invoice Card data never appears in discovery or transfer packages.
2. Changed source/Card content cannot reuse an incompatible manifest identity.
3. Repeated package pull returns the same logical issuance and exact bytes.
4. Mismatched, malformed, or wrong-node receipts cannot acknowledge issuance.
5. Timeout produces unknown state and read-only reconciliation, not duplicate
   issue.
6. Contract mismatch exposes no package.
7. Discovery returns stable exact manifest/source metadata and a bounded cursor;
   pulling a changed or unlisted manifest fails closed.
8. Streamed source parts reject size/hash mismatch before local durable import,
   and JSON contains no base64 bytes or storage reference.
9. Assignment observation round-trips unchanged; missing explicit Registry
   provenance never becomes an assigned `project_id`.

### Consequence

Cabinet Web remains the authoritative daytime source while local Backend alone
decides durable local import and archive acceptance.

## Accepted decision A09 — Registry catalogue publication is atomic and monotonic

### Normative rules

1. Only an authenticated active local Backend node may submit M24.
2. One delivery uses the fixed negotiated contract version
   `cabinet-web-sync-v1` and the exact backend wire shape: catalogue ID,
   complete M18 snapshots in canonical `project_id` order, source/target nodes,
   idempotency identity, and creation time. Contract version is negotiated at
   the connection boundary; it is not invented as an extra payload field.
   Snapshot count and catalogue content identity are derived from the complete
   ordered snapshots and their immutable M19 identities. Cabinet Web validates
   identity, ordering, negotiated version, and completeness before acceptance.
3. Idempotent replay of the same publication/catalogue returns the existing M25
   acknowledgement. Conflicting reuse is rejected.
4. Cabinet Web commits the complete M20 replica and current-catalogue selection
   atomically. A partial catalogue is never current.
5. A catalogue older than the current accepted source observation cannot
   replace it. Equal catalogue identity with different content is rejected.
6. Registry project facts remain externally owned snapshots. Cabinet Web does
   not rewrite M09 ProjectCard master facts or infer project completion/deletion
   from Registry status.
7. Catalogue age and last successful publication remain visible while local
   Backend is offline; stale does not mean invalid or currently reachable.

### Formal invariants

```text
catalogue_current
-> complete_delivery_verified AND replica_committed

incoming_observation_older_than_current -/> replace_current
registry_snapshot -/> project_card_master_authority
registry_status -/> automatic_release_or_deletion
```

### Required tests

1. Partial, malformed, hash-mismatched, and incompatible catalogues cannot
   become current.
2. Exact replay returns the prior acknowledgement without duplicate replica.
3. Conflicting replay and older publication are rejected.
4. Reader sees either the prior complete catalogue or the new complete
   catalogue, never a partial mixture.
5. Registry status changes do not delete Cards or source bytes.

### Consequence

Cabinet Web gains an offline Registry view without becoming Registry or coupling
its own Project Card lifecycle to the intermittent local system.

## Accepted decision A10 — VPS working copies require explicit safe release

### Normative rules

1. Successful local synchronization does not delete, expire, or schedule
   deletion of Cabinet Web Cards, source bytes, manifests, or transfer evidence.
2. Release is an explicit owner-confirmed action for an exact working set or
   exact listed Card/source members. Inactivity and Registry status are never
   release authority.
3. Before source-byte release, Cabinet Web requires M23 accepted/already-accepted
   evidence for the exact manifest, with the exact Card content hash present in
   `accepted_card_hashes` and every manifest source content hash present in
   `accepted_source_hashes`. It also requires local
   `DurableAcceptanceVerification` for that Invoice with `accepted = true`, a
   non-empty `evidence_id`, and `required_source_ids` exactly equal to
   `verified_source_ids` and to the manifest source membership.
4. The user sees the exact affected members, missing verification, and retained
   history before confirmation.
5. Release removes only eligible VPS working bytes. Canonical Card/revision,
   logical source metadata, hashes, receipts, and release evidence remain.
6. Repeated release is idempotent. Failed or partial release cannot report
   complete and must remain safely retryable.
7. Backup coverage remains required for every accepted Card/source whose loss
   would break current custody or next pull. Restore verification follows A13.

### Formal invariants

```text
vps_source_bytes_released
-> explicit_owner_confirmation
   AND exact_local_durable_verification
   AND receipt.result in {accepted, already_accepted}
   AND receipt.manifest_hash = issuance.manifest_hash
   AND manifest.card_content_hash in receipt.accepted_card_hashes
   AND manifest.source_hashes subset_of receipt.accepted_source_hashes
   AND durable_verification.accepted
   AND durable_verification.evidence_id present
   AND durable_verification.required_source_ids
       = durable_verification.verified_source_ids
       = manifest.source_ids
   AND release_evidence_committed

synchronization_success -/> automatic_deletion
registry_status -/> automatic_deletion
```

### Required tests

1. Successful synchronization leaves all VPS working copies present.
2. Release without exact local durable verification is blocked.
3. Registry closed/archived status alone changes no custody state.
4. Release preserves Card, source identity, hashes, receipts, and audit evidence.
5. Repeated release returns the same logical result.
6. Missing Card hash, any source hash, exact source-ID equality, or durable
   evidence ID blocks every affected byte from release.

### Consequence

The first release favors recoverability over automatic storage cleanup.

## Accepted decision A11 — authentication abuse, secrets, and recovery fail closed

### Normative rules

1. Human browser, ChatGPT plugin, local node, and operator boundaries use
   separate credentials that cannot substitute for one another.
2. ChatGPT tools are served only through the existing authenticated private
   plugin tunnel and map to the configured single owner principal. Failure to
   establish that tunnel identity exposes no Cabinet tool or data; there is no
   anonymous or directly public MCP fallback.
3. Reusable credentials live only in protected host/tunnel configuration or a
   dedicated credential store. They never enter repositories, Cards, source
   files, prompts, tool arguments visible to the model, URLs, logs, traces,
   errors, receipts, backups without secret protection, or exported evidence.
4. Stored credential verifiers are one-way and credential comparison is
   timing-safe. Plaintext machine/plugin credential material is shown or
   injected only at enrollment/runtime and is never durably recoverable.
5. Every credential supports explicit rotation and revocation without changing
   M02/M17 business identity. Rotation activates the replacement and revokes
   the prior credential atomically.
6. Authentication failures are counted in a bounded abuse context without
   storing the attempted secret. A13 throttling applies equally to malformed,
   unknown, disabled, and revoked credentials.
7. Machine credentials have no password-recovery flow. Compromise requires
   revocation/rotation and re-enrollment. Human Basic Auth recovery is an
   operator action at the protected host boundary and does not expose the old
   secret.
8. An active local-node credential is reusable until rotation or revocation;
   replay cannot create a second logical mutation because every mutation is
   bound to A04/A08/A09 idempotency. Read replay grants no capability beyond
   that same active node scope.
9. Startup fails closed when required credentials, protected configuration,
   durable state, TLS expectations, or contract compatibility are unavailable.
10. Authentication/authorization failures are auditable with principal/channel,
   operation class, time, and bounded code, never secret material.

### Formal invariants

```text
authenticated_request
-> active_credential AND active_principal

credential_rotation
-> replacement_active AND prior_credential_revoked

reusable_secret -/> business_data_or_log_or_prompt_or_export
startup_dependency_missing -> not_ready
```

### Required tests

1. Unknown, malformed, disabled, rotated, and revoked credentials fail with
   equivalent bounded disclosure and throttling.
2. Channel credentials cannot authenticate across boundaries.
3. Rotation immediately rejects the prior credential without changing
   principal/node identity.
4. Secret scanning of source, logs, errors, artifacts, and responses finds no
   reusable credential.
5. Missing protected configuration prevents readiness and protected actions.

### Consequence

The single-user product stays operationally simple without collapsing all
authority into one reusable secret.
