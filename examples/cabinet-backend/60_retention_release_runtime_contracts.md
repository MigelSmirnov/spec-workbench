# State 6 repair — retention release runtime contracts

- `SynchronizationService.get_working_set_membership(self, project_id: str, working_set_id: str) -> VpsWorkingSetMembership`
- `get_working_set_membership(service: SynchronizationService, project_id: str, working_set_id: str) -> VpsWorkingSetMembership`

- `RetentionReleaseService.__init__(self, repository: RetentionReleaseRepository, archive: DurableArchiveService, synchronization: SynchronizationService) -> None`
- `RetentionReleaseService.evaluate_vps_release(self, project_id: str, working_set_id: str | None, authorization: AuthorizationDecision) -> VpsReleaseEvaluation`
- `RetentionReleaseService.request_manual_vps_release(self, evaluation: VpsReleaseEvaluation, authorization: AuthorizationDecision) -> VpsReleaseDecision`
- `RetentionReleaseService.get_retention_status(self, project_id: str, working_set_id: str) -> VpsReleaseDecision | None`

- `RetentionReleaseRepository.begin(self) -> None`
- `RetentionReleaseRepository.commit(self) -> None`
- `RetentionReleaseRepository.rollback(self) -> None`
- `RetentionReleaseRepository.lock_working_set(self, project_id: str, working_set_id: str) -> None`
- `RetentionReleaseRepository.save_evaluation(self, evaluation: VpsReleaseEvaluation) -> None`
- `RetentionReleaseRepository.load_decision(self, project_id: str, working_set_id: str) -> VpsReleaseDecision | None`
- `RetentionReleaseRepository.reserve_decision(self, decision: VpsReleaseDecision) -> VpsReleaseDecision`
- `PostgresRetentionReleaseRepository.__init__(self, database_url: str) -> None`
- `PostgresRetentionReleaseRepository.begin(self) -> None`
- `PostgresRetentionReleaseRepository.commit(self) -> None`
- `PostgresRetentionReleaseRepository.rollback(self) -> None`
- `PostgresRetentionReleaseRepository.lock_working_set(self, project_id: str, working_set_id: str) -> None`
- `PostgresRetentionReleaseRepository.save_evaluation(self, evaluation: VpsReleaseEvaluation) -> None`
- `PostgresRetentionReleaseRepository.load_decision(self, project_id: str, working_set_id: str) -> VpsReleaseDecision | None`
- `PostgresRetentionReleaseRepository.reserve_decision(self, decision: VpsReleaseDecision) -> VpsReleaseDecision`

- `create_app(access_control: AccessControlBackend, archive: DurableArchiveService, registry: RegistryContextService, holded_gateway: HoldedGatewayService, synchronization: SynchronizationService, plan_actual: PlanActualService, holded_publication: HoldedPublicationService, retention_release: RetentionReleaseService) -> FastAPI`
