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
- `HoldedPublicationRepository.insert_publication(self, publication: HoldedPublication) -> None`
- `HoldedPublicationRepository.update_publication(self, publication: HoldedPublication) -> None`
- `PostgresHoldedPublicationRepository.__init__(self, database_url: str) -> None`
- `PostgresHoldedPublicationRepository.begin(self) -> None`
- `PostgresHoldedPublicationRepository.commit(self) -> None`
- `PostgresHoldedPublicationRepository.rollback(self) -> None`
- `PostgresHoldedPublicationRepository.lock_publication(self, publication_id: str) -> None`
- `PostgresHoldedPublicationRepository.lock_invoice_revision(self, invoice_id: str, content_hash: str) -> None`
- `PostgresHoldedPublicationRepository.load_publication(self, publication_id: str) -> HoldedPublication | None`
- `PostgresHoldedPublicationRepository.load_by_invoice_revision(self, invoice_id: str, content_hash: str) -> HoldedPublication | None`
- `PostgresHoldedPublicationRepository.insert_publication(self, publication: HoldedPublication) -> None`
- `PostgresHoldedPublicationRepository.update_publication(self, publication: HoldedPublication) -> None`

- `create_app(access_control: AccessControlBackend, archive: DurableArchiveService, registry: RegistryContextService, holded_gateway: HoldedGatewayService, synchronization: SynchronizationService, plan_actual: PlanActualService, holded_publication: HoldedPublicationService) -> FastAPI`

`PostgresHoldedPublicationRepository` is owned by `holded_publication_persistence`.
`reserve_publication` and `save_transition` were replaced by the plain `insert_publication`
and `update_publication`; equivalence reuse and lifecycle-transition validity belong to
`HoldedPublicationService` (`30_modules_persistence_boundary.md`).
