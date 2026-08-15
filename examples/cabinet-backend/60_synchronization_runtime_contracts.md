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
- `SynchronizationRepository.reserve_synchronization(self, synchronization: InvoiceSynchronization) -> InvoiceSynchronization`
- `SynchronizationRepository.mark_transfer_issued(self, synchronization_id: str, issued_at: datetime) -> InvoiceSynchronization`
- `SynchronizationRepository.save_synchronization_outcome(self, outcome: SynchronizationOutcome) -> None`
- `SynchronizationRepository.load_sync_status(self, invoice_id: str, node_id: str) -> SynchronizationStatusObservation | None`
- `SynchronizationRepository.load_synchronization(self, synchronization_id: str) -> InvoiceSynchronization | None`
- `SynchronizationRepository.reserve_catalogue_publication(self, publication: RegistryCataloguePublication) -> RegistryCataloguePublication`
- `SynchronizationRepository.save_catalogue_acknowledgement(self, acknowledgement: VpsCatalogueAcknowledgement) -> None`
- `SynchronizationRepository.append_connection_observation(self, observation: VpsConnectionObservation) -> None`

Generic dictionaries and untyped save/query methods are forbidden.

## Concrete adapters and composition

- `PostgresSynchronizationRepository.__init__(self, database_url: str) -> None`
- `HttpxVpsSynchronizationTransport.__init__(self, base_url: str, node_credential: str, timeout_seconds: int, max_response_bytes: int) -> None`
- `create_app(access_control: AccessControlBackend, archive: DurableArchiveService, registry: RegistryContextService, holded_gateway: HoldedGatewayService, synchronization: SynchronizationService) -> FastAPI`

Constructors validate inputs but never read environment variables.
