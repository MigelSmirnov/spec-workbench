# State 6 repair — Holded gateway runtime contracts

## Service

- HoldedGatewayService.__init__(self, repository: HoldedAttemptRepository, http_client: HoldedHttpClient) -> None
- HoldedGatewayService.create_holded_purchase(self, payload: HoldedPurchaseAttemptPayload, publication_attempt_id: str) -> HoldedPublicationAttempt
- HoldedGatewayService.lookup_holded_purchase(self, attempt_marker: str, document_id: str | None = None) -> HoldedPurchaseLookupEvidence

Existing module functions remain façades with an explicit `HoldedGatewayService` first parameter.

## HTTP port

- HoldedHttpClient.create_purchase(self, payload: HoldedPurchaseAttemptPayload) -> HoldedTransportResponse
- HoldedHttpClient.list_purchases(self, page: int) -> HoldedPurchaseListPage
- HoldedHttpClient.get_purchase(self, document_id: str) -> HoldedTransportResponse

## Attempt repository port

- HoldedAttemptRepository.begin(self) -> None
- HoldedAttemptRepository.commit(self) -> None
- HoldedAttemptRepository.rollback(self) -> None
- HoldedAttemptRepository.lock_attempt(self, publication_attempt_id: str) -> None
- HoldedAttemptRepository.load_attempt(self, publication_attempt_id: str) -> HoldedPublicationAttempt | None
- HoldedAttemptRepository.load_attempt_by_marker(self, attempt_marker: str) -> HoldedPublicationAttempt | None
- HoldedAttemptRepository.reserve_attempt(self, attempt: HoldedPublicationAttempt) -> HoldedPublicationAttempt
- HoldedAttemptRepository.mark_request_issued(self, publication_attempt_id: str, issued_at: datetime) -> HoldedPublicationAttempt
- HoldedAttemptRepository.append_attempt_outcome(self, attempt: HoldedPublicationAttempt) -> None
- HoldedAttemptRepository.append_lookup_evidence(self, attempt_marker: str, evidence: HoldedPurchaseLookupEvidence) -> None

Generic query dictionaries and untyped save methods are forbidden.

## Concrete adapters

- PostgresHoldedAttemptRepository.__init__(self, database_url: str) -> None
- PostgresHoldedAttemptRepository.begin(self) -> None
- PostgresHoldedAttemptRepository.commit(self) -> None
- PostgresHoldedAttemptRepository.rollback(self) -> None
- PostgresHoldedAttemptRepository.lock_attempt(self, publication_attempt_id: str) -> None
- PostgresHoldedAttemptRepository.load_attempt(self, publication_attempt_id: str) -> HoldedPublicationAttempt | None
- PostgresHoldedAttemptRepository.load_attempt_by_marker(self, attempt_marker: str) -> HoldedPublicationAttempt | None
- PostgresHoldedAttemptRepository.reserve_attempt(self, attempt: HoldedPublicationAttempt) -> HoldedPublicationAttempt
- PostgresHoldedAttemptRepository.mark_request_issued(self, publication_attempt_id: str, issued_at: datetime) -> HoldedPublicationAttempt
- PostgresHoldedAttemptRepository.append_attempt_outcome(self, attempt: HoldedPublicationAttempt) -> None
- PostgresHoldedAttemptRepository.append_lookup_evidence(self, attempt_marker: str, evidence: HoldedPurchaseLookupEvidence) -> None
- HttpxHoldedHttpClient.__init__(self, base_url: str, api_key: str, timeout_seconds: int, max_response_bytes: int, max_recovery_pages: int) -> None
- HttpxHoldedHttpClient.create_purchase(self, payload: HoldedPurchaseAttemptPayload) -> HoldedTransportResponse
- HttpxHoldedHttpClient.list_purchases(self, page: int) -> HoldedPurchaseListPage
- HttpxHoldedHttpClient.get_purchase(self, document_id: str) -> HoldedTransportResponse

Constructors validate inputs but do not read environment variables.

## Composition

- create_local_app() constructs both adapters and `HoldedGatewayService`.
- create_app(access_control: AccessControlBackend, archive: DurableArchiveService, registry: RegistryContextService, holded_gateway: HoldedGatewayService) -> FastAPI

The service is bound into application state and supplied explicitly to Holded publication calls.
