# State 6 repair — synchronization runtime contracts

## Service and façades

- `SynchronizationService.__init__(self, repository: SynchronizationRepository, transport: VpsSynchronizationTransport, archive: DurableArchiveService) -> None`
- `SynchronizationService.synchronize_invoice_work(self, selection: SynchronizationWorkSelection, node: CabinetNodeIdentity) -> SynchronizationOutcome`
- `SynchronizationService.get_sync_status(self, invoice_id: str, node_id: str) -> SynchronizationStatusObservation`
- `SynchronizationService.reconcile_transfer_outcome(self, synchronization_id: str) -> SynchronizationOutcome`
- `SynchronizationService.publish_registry_catalogue(self, delivery: RegistryCatalogueDelivery) -> RegistryCataloguePublication`
- `SynchronizationService.observe_vps_connection(self) -> VpsConnectionObservation`

Module functions remain thin façades with an explicit `SynchronizationService`
first parameter.

## Transport port

- `VpsSynchronizationTransport.transfer_invoice(self, selection: SynchronizationWorkSelection, node: CabinetNodeIdentity) -> VpsInvoiceTransferPackage`
- `VpsSynchronizationTransport.reconcile_transfer(self, synchronization_id: str) -> VpsTransferReconciliationEvidence`
- `VpsSynchronizationTransport.publish_catalogue(self, delivery: RegistryCatalogueDelivery) -> VpsCatalogueAcknowledgement`
- `VpsSynchronizationTransport.observe_connection(self) -> VpsConnectionObservation`

## Repository port

- `SynchronizationRepository.begin(self) -> None`
- `SynchronizationRepository.commit(self) -> None`
- `SynchronizationRepository.rollback(self) -> None`
- `SynchronizationRepository.lock_synchronization(self, synchronization_id: str) -> None`
- `SynchronizationRepository.insert_synchronization(self, synchronization: InvoiceSynchronization) -> None`
- `SynchronizationRepository.update_synchronization(self, synchronization: InvoiceSynchronization) -> None`
- `SynchronizationRepository.list_synchronizations_for_invoice(self, invoice_id: str, target_node_id: str) -> tuple[InvoiceSynchronization, ...]`
- `SynchronizationRepository.load_synchronization(self, synchronization_id: str) -> InvoiceSynchronization | None`
- `SynchronizationRepository.load_synchronization_by_idempotency(self, invoice_id: str, target_node_id: str, idempotency_key: str) -> InvoiceSynchronization | None`
- `SynchronizationRepository.insert_catalogue_publication(self, publication: RegistryCataloguePublication) -> None`
- `SynchronizationRepository.load_catalogue_publication_by_idempotency(self, catalogue_id: str, target_node_id: str, idempotency_key: str) -> RegistryCataloguePublication | None`
- `SynchronizationRepository.update_catalogue_publication(self, publication: RegistryCataloguePublication) -> None`
- `SynchronizationRepository.insert_connection_observation(self, observation: VpsConnectionObservation) -> None`

Generic dictionaries and untyped save/query methods are forbidden.

## Concrete adapters and composition

- `PostgresSynchronizationRepository.__init__(self, database_url: str) -> None`
- `PostgresSynchronizationRepository.begin(self) -> None`
- `PostgresSynchronizationRepository.commit(self) -> None`
- `PostgresSynchronizationRepository.rollback(self) -> None`
- `PostgresSynchronizationRepository.lock_synchronization(self, synchronization_id: str) -> None`
- `PostgresSynchronizationRepository.insert_synchronization(self, synchronization: InvoiceSynchronization) -> None`
- `PostgresSynchronizationRepository.update_synchronization(self, synchronization: InvoiceSynchronization) -> None`
- `PostgresSynchronizationRepository.list_synchronizations_for_invoice(self, invoice_id: str, target_node_id: str) -> tuple[InvoiceSynchronization, ...]`
- `PostgresSynchronizationRepository.load_synchronization(self, synchronization_id: str) -> InvoiceSynchronization | None`
- `PostgresSynchronizationRepository.load_synchronization_by_idempotency(self, invoice_id: str, target_node_id: str, idempotency_key: str) -> InvoiceSynchronization | None`
- `PostgresSynchronizationRepository.insert_catalogue_publication(self, publication: RegistryCataloguePublication) -> None`
- `PostgresSynchronizationRepository.load_catalogue_publication_by_idempotency(self, catalogue_id: str, target_node_id: str, idempotency_key: str) -> RegistryCataloguePublication | None`
- `PostgresSynchronizationRepository.update_catalogue_publication(self, publication: RegistryCataloguePublication) -> None`
- `PostgresSynchronizationRepository.insert_connection_observation(self, observation: VpsConnectionObservation) -> None`
- `create_app(access_control: AccessControlBackend, archive: DurableArchiveService, registry: RegistryContextService, holded_gateway: HoldedGatewayService, synchronization: SynchronizationService) -> FastAPI`

Constructors validate inputs but never read environment variables.

`PostgresSynchronizationRepository` is owned by `synchronization_persistence`. Guarded
reservation, issuance, outcome, and acknowledgement methods were replaced by plain
inserts, field updates, and idempotency lookups; reuse, issuance authority, and
transition validity belong to `SynchronizationService`. `load_sync_status` was later replaced
(see below).

`load_sync_status` was replaced by `list_synchronizations_for_invoice`; `get_sync_status`
composes the observation from the latest attempt (`30_modules_persistence_boundary.md`).

`HttpxVpsSynchronizationTransport` was removed: `VpsSynchronizationTransport` is `disposition: external`. The VPS
(`cabinet-dev`) exposes no synchronization API yet — only static JSON and an MCP tunnel — so no wire
contract can be closed. `create_local_app(vps_transport: VpsSynchronizationTransport) -> FastAPI` receives the implementation from the
composition boundary; it returns to the Factory as a deterministic transport backend once the VPS
sync API exists and is evidenced (`30_modules_persistence_boundary.md`, open items).
