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
- ArchiveUnitOfWork.save_publication(self, publication: ArchiveBytePublication) -> None
- ArchiveUnitOfWork.mark_publication_published(self, publication_id: str, updated_at: datetime) -> ArchiveBytePublication
- ArchiveUnitOfWork.mark_publication_failed(self, publication_id: str, failure_code: str, updated_at: datetime) -> ArchiveBytePublication

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
- PostgresArchiveUnitOfWork.save_publication(self, publication: ArchiveBytePublication) -> None
- PostgresArchiveUnitOfWork.mark_publication_published(self, publication_id: str, updated_at: datetime) -> ArchiveBytePublication
- PostgresArchiveUnitOfWork.mark_publication_failed(self, publication_id: str, failure_code: str, updated_at: datetime) -> ArchiveBytePublication
- PostgresArchiveUnitOfWork.load_transfer_receipt(self, invoice_id: str, content_hash: str | None = None) -> InvoiceTransferReceipt | None
- PostgresArchiveUnitOfWork.load_source_binaries(self, invoice_id: str) -> tuple[SourceBinary, ...]
- PostgresArchiveUnitOfWork.save_transfer_acceptance(self, manifest: InvoiceTransferManifest, card_revision: StoredInvoiceCardRevision, source_replicas: tuple[SourceBinaryReplica, ...], receipt: InvoiceTransferReceipt) -> None
- PostgresArchiveUnitOfWork.save_source_attachment(self, source: SourceBinary, replica: SourceBinaryReplica, publication: ArchiveBytePublication) -> None
- PostgresArchiveUnitOfWork.save_incomplete_source_acceptance(self, decision: IncompleteSourceAcceptance) -> None
- PostgresArchiveUnitOfWork.save_source_loss_decision(self, decision: SourceLossDecision) -> None
- LocalFilesystemSourceByteStore.__init__(self, root_path: str) -> None
- LocalFilesystemSourceByteStore.stage(self, publication_id: str, content: bytes, expected_hash: str, expected_size: int) -> str
- LocalFilesystemSourceByteStore.verify(self, storage_reference: str, expected_hash: str, expected_size: int) -> bool
- LocalFilesystemSourceByteStore.publish(self, staging_reference: str, final_reference: str, expected_hash: str, expected_size: int) -> None
- LocalFilesystemSourceByteStore.remove_staging(self, staging_reference: str) -> None

Constructors validate mechanism prerequisites but do not read environment variables.

## Bootstrap composition

create_local_app() constructs both adapters, constructs DurableArchiveService, completes recovery, constructs the other accepted dependencies, and supplies the service to api.create_app.
