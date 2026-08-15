# State 6 repair — Holded publication runtime contracts

- `HoldedPublicationService.__init__(self, repository: HoldedPublicationRepository, archive: DurableArchiveService, gateway: HoldedGatewayService) -> None`
- `HoldedPublicationService.request_holded_publication(self, invoice_id: str, content_hash: str, authorization: AuthorizationDecision) -> HoldedPublication`
- `HoldedPublicationService.reconcile_holded_publication(self, publication_id: str, authorization: AuthorizationDecision) -> HoldedPublication`
- `HoldedPublicationService.get_holded_publication_status(self, publication_id: str) -> HoldedPublication`

Module functions remain façades with an explicit service first parameter.

- `HoldedPublicationRepository.begin(self) -> None`
- `HoldedPublicationRepository.commit(self) -> None`
- `HoldedPublicationRepository.rollback(self) -> None`
- `HoldedPublicationRepository.lock_publication(self, publication_id: str) -> None`
- `HoldedPublicationRepository.lock_invoice_revision(self, invoice_id: str, content_hash: str) -> None`
- `HoldedPublicationRepository.load_publication(self, publication_id: str) -> HoldedPublication | None`
- `HoldedPublicationRepository.load_by_invoice_revision(self, invoice_id: str, content_hash: str) -> HoldedPublication | None`
- `HoldedPublicationRepository.reserve_publication(self, publication: HoldedPublication) -> HoldedPublication`
- `HoldedPublicationRepository.save_transition(self, publication: HoldedPublication) -> None`
- `PostgresHoldedPublicationRepository.__init__(self, database_url: str) -> None`

- `create_app(access_control: AccessControlBackend, archive: DurableArchiveService, registry: RegistryContextService, holded_gateway: HoldedGatewayService, synchronization: SynchronizationService, plan_actual: PlanActualService, holded_publication: HoldedPublicationService) -> FastAPI`
