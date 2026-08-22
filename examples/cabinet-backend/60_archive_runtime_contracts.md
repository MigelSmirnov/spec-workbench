# State 6 repair — durable archive runtime contracts

## Service construction

DurableArchiveService.__init__(self, unit_of_work: ArchiveUnitOfWork, byte_store: SourceByteStore) -> None

Both dependencies are required. There is no nullable, default, in-memory, or module-global fallback.

## Service operations

- DurableArchiveService.accept_transfer_manifest(self, manifest: InvoiceTransferManifest, card_revision: StoredInvoiceCardRevision, source_replicas: tuple[SourceBinaryReplica, ...]) -> InvoiceTransferReceipt
- DurableArchiveService.verify_durable_acceptance(self, invoice_id: str, content_hash: str | None = None) -> DurableAcceptanceVerification
- DurableArchiveService.attach_local_source(self, invoice_id: str, files: tuple[LocalSourceFile, ...], authorization: AuthorizationDecision, expected_sources: tuple[ContentReference, ...] = ()) -> SourceAttachmentBatchResult
- DurableArchiveService.get_source_status(self, invoice_id: str) -> SourceStatus
- DurableArchiveService.get_archived_invoice(self, invoice_id: str, content_hash: str | None = None) -> StoredInvoiceCardRevision
- DurableArchiveService.accept_incomplete_source_evidence(self, decision: IncompleteSourceAcceptance, authorization: AuthorizationDecision) -> SourceStatus
- DurableArchiveService.record_source_loss(self, decision: SourceLossDecision, authorization: AuthorizationDecision) -> SourceStatus
- DurableArchiveService.recover_pending_publications(self) -> None

## Unit-of-work port

- ArchiveUnitOfWork.begin(self) -> None
- ArchiveUnitOfWork.commit(self) -> None
- ArchiveUnitOfWork.rollback(self) -> None
- ArchiveUnitOfWork.lock_invoice(self, invoice_id: str) -> None
- ArchiveUnitOfWork.load_card_revision(self, invoice_id: str, content_hash: str | None = None) -> StoredInvoiceCardRevision | None
- ArchiveUnitOfWork.load_source_replicas(self, invoice_id: str) -> tuple[SourceBinaryReplica, ...]
- ArchiveUnitOfWork.load_pending_publications(self) -> tuple[ArchiveBytePublication, ...]
- ArchiveUnitOfWork.insert_publication(self, publication: ArchiveBytePublication) -> None
- ArchiveUnitOfWork.update_publication_state(self, publication: ArchiveBytePublication) -> None
- ArchiveUnitOfWork.load_publication(self, publication_id: str) -> ArchiveBytePublication | None
- ArchiveUnitOfWork.load_transfer_receipt(self, invoice_id: str, content_hash: str | None = None) -> InvoiceTransferReceipt | None
- ArchiveUnitOfWork.load_source_binaries(self, invoice_id: str) -> tuple[SourceBinary, ...]
- ArchiveUnitOfWork.insert_transfer_manifest(self, manifest: InvoiceTransferManifest) -> None
- ArchiveUnitOfWork.insert_card_revision(self, card_revision: StoredInvoiceCardRevision) -> None
- ArchiveUnitOfWork.update_card_revision_succession(self, card_revision: StoredInvoiceCardRevision) -> None
- ArchiveUnitOfWork.insert_source_replicas(self, source_replicas: tuple[SourceBinaryReplica, ...]) -> None
- ArchiveUnitOfWork.insert_transfer_receipt(self, receipt: InvoiceTransferReceipt) -> None
- ArchiveUnitOfWork.insert_source_binary(self, source: SourceBinary) -> None
- ArchiveUnitOfWork.load_invoice_card(self, invoice_id: str) -> StoredInvoiceCard | None
- ArchiveUnitOfWork.upsert_invoice_card(self, card: StoredInvoiceCard) -> None
- ArchiveUnitOfWork.insert_incomplete_source_acceptance(self, decision: IncompleteSourceAcceptance) -> None
- ArchiveUnitOfWork.insert_source_loss_decision(self, decision: SourceLossDecision) -> None

The accepted archive transitions additionally require typed load_transfer_receipt, load_source_binaries, save_transfer_acceptance, save_source_attachment, save_incomplete_source_acceptance, and save_source_loss_decision methods using their exact existing domain models. Generic save(object), query(dict), or policy-bearing repository methods are forbidden.

## Byte-store port

- SourceByteStore.stage(self, publication_id: str, content: bytes, expected_hash: str, expected_size: int) -> str
- SourceByteStore.verify(self, storage_reference: str, expected_hash: str, expected_size: int) -> bool
- SourceByteStore.publish(self, staging_reference: str, final_reference: str, expected_hash: str, expected_size: int) -> None
- SourceByteStore.remove_staging(self, staging_reference: str) -> None

Storage references are opaque store-created values and are never accepted from HTTP, MCP, manifest, or local-agent input.

## Concrete construction

- PostgresArchiveUnitOfWork.__init__(self, database_url: str) -> None
- PostgresArchiveUnitOfWork.begin(self) -> None
- PostgresArchiveUnitOfWork.commit(self) -> None
- PostgresArchiveUnitOfWork.rollback(self) -> None
- PostgresArchiveUnitOfWork.lock_invoice(self, invoice_id: str) -> None
- PostgresArchiveUnitOfWork.load_card_revision(self, invoice_id: str, content_hash: str | None = None) -> StoredInvoiceCardRevision | None
- PostgresArchiveUnitOfWork.load_source_replicas(self, invoice_id: str) -> tuple[SourceBinaryReplica, ...]
- PostgresArchiveUnitOfWork.load_pending_publications(self) -> tuple[ArchiveBytePublication, ...]
- PostgresArchiveUnitOfWork.insert_publication(self, publication: ArchiveBytePublication) -> None
- PostgresArchiveUnitOfWork.update_publication_state(self, publication: ArchiveBytePublication) -> None
- PostgresArchiveUnitOfWork.load_publication(self, publication_id: str) -> ArchiveBytePublication | None
- PostgresArchiveUnitOfWork.load_transfer_receipt(self, invoice_id: str, content_hash: str | None = None) -> InvoiceTransferReceipt | None
- PostgresArchiveUnitOfWork.load_source_binaries(self, invoice_id: str) -> tuple[SourceBinary, ...]
- PostgresArchiveUnitOfWork.insert_transfer_manifest(self, manifest: InvoiceTransferManifest) -> None
- PostgresArchiveUnitOfWork.insert_card_revision(self, card_revision: StoredInvoiceCardRevision) -> None
- PostgresArchiveUnitOfWork.update_card_revision_succession(self, card_revision: StoredInvoiceCardRevision) -> None
- PostgresArchiveUnitOfWork.insert_source_replicas(self, source_replicas: tuple[SourceBinaryReplica, ...]) -> None
- PostgresArchiveUnitOfWork.insert_transfer_receipt(self, receipt: InvoiceTransferReceipt) -> None
- PostgresArchiveUnitOfWork.insert_source_binary(self, source: SourceBinary) -> None
- PostgresArchiveUnitOfWork.load_invoice_card(self, invoice_id: str) -> StoredInvoiceCard | None
- PostgresArchiveUnitOfWork.upsert_invoice_card(self, card: StoredInvoiceCard) -> None
- PostgresArchiveUnitOfWork.insert_incomplete_source_acceptance(self, decision: IncompleteSourceAcceptance) -> None
- PostgresArchiveUnitOfWork.insert_source_loss_decision(self, decision: SourceLossDecision) -> None
- LocalFilesystemSourceByteStore.__init__(self, root_path: str) -> None
- LocalFilesystemSourceByteStore.stage(self, publication_id: str, content: bytes, expected_hash: str, expected_size: int) -> str
- LocalFilesystemSourceByteStore.verify(self, storage_reference: str, expected_hash: str, expected_size: int) -> bool
- LocalFilesystemSourceByteStore.publish(self, staging_reference: str, final_reference: str, expected_hash: str, expected_size: int) -> None
- LocalFilesystemSourceByteStore.remove_staging(self, staging_reference: str) -> None

Constructors validate mechanism prerequisites but do not read environment variables.

## Bootstrap composition

create_local_app() constructs both adapters, constructs DurableArchiveService, completes recovery, constructs the other accepted dependencies, and supplies the service to api.create_app.

`PostgresArchiveUnitOfWork` is owned by `durable_archive_persistence`. Guarded publication
transitions and multi-model writes were replaced by plain per-model appends, field updates,
and exact reads (`insert_publication`, `update_publication_state`, `load_publication`,
`insert_transfer_manifest`, `insert_card_revision`, `update_card_revision_succession`,
`insert_source_replicas`, `insert_transfer_receipt`, `insert_source_binary`,
`load_invoice_card`, `upsert_invoice_card`). `rules.archive_byte_publication` transitions and
acceptance equivalence belong to `durable_archive` (`30_modules_persistence_boundary.md`).
