# State 6 repair — plan/actual runtime contracts

## Service and façades

- `PlanActualService.__init__(self, repository: PlanActualRepository, archive: DurableArchiveService, registry: RegistryContextService) -> None`
- `PlanActualService.refresh_estimate_snapshot(self, observation: PresuProEstimateObservation) -> EstimateSnapshot`
- `PlanActualService.propose_invoice_line_matches(self, invoice_id: str, content_hash: str, estimate_snapshot_id: str) -> tuple[InvoiceLineMatchProposal, ...]`
- `PlanActualService.record_match_decision(self, decision: InvoiceLineEstimateMatch) -> InvoiceLineEstimateMatch`
- `PlanActualService.get_unmatched_items(self, project_id: str, estimate_snapshot_id: str) -> UnmatchedPlanActualItems`
- `PlanActualService.calculate_plan_actual(self, request: PlanActualRequest) -> PlanActualAnalysis`

Module functions remain façades with an explicit `PlanActualService` first parameter.

## Repository

- `PlanActualRepository.begin(self) -> None`
- `PlanActualRepository.commit(self) -> None`
- `PlanActualRepository.rollback(self) -> None`
- `PlanActualRepository.lock_estimate(self, presupro_estimate_id: str) -> None`
- `PlanActualRepository.lock_invoice_line(self, invoice_id: str, content_hash: str, invoice_line_id: str) -> None`
- `PlanActualRepository.load_snapshot(self, snapshot_id: str) -> EstimateSnapshot | None`
- `PlanActualRepository.load_snapshot_by_content(self, presupro_estimate_id: str, content_hash: str) -> EstimateSnapshot | None`
- `PlanActualRepository.save_snapshot(self, snapshot: EstimateSnapshot) -> None`
- `PlanActualRepository.save_proposals(self, proposals: tuple[InvoiceLineMatchProposal, ...]) -> None`
- `PlanActualRepository.load_match_decisions(self, match_ids: tuple[str, ...]) -> tuple[InvoiceLineEstimateMatch, ...]`
- `PlanActualRepository.insert_match_decision(self, decision: InvoiceLineEstimateMatch) -> None`
- `PlanActualRepository.update_match_status(self, decision: InvoiceLineEstimateMatch) -> None`
- `PlanActualRepository.list_matches_for_line(self, invoice_id: str, content_hash: str, invoice_line_id: str) -> tuple[InvoiceLineEstimateMatch, ...]`
- `PlanActualRepository.list_matches_for_snapshot(self, estimate_snapshot_id: str, status: str) -> tuple[InvoiceLineEstimateMatch, ...]`

- `PostgresPlanActualRepository.__init__(self, database_url: str) -> None`
- `PostgresPlanActualRepository.begin(self) -> None`
- `PostgresPlanActualRepository.commit(self) -> None`
- `PostgresPlanActualRepository.rollback(self) -> None`
- `PostgresPlanActualRepository.lock_estimate(self, presupro_estimate_id: str) -> None`
- `PostgresPlanActualRepository.lock_invoice_line(self, invoice_id: str, content_hash: str, invoice_line_id: str) -> None`
- `PostgresPlanActualRepository.load_snapshot(self, snapshot_id: str) -> EstimateSnapshot | None`
- `PostgresPlanActualRepository.load_snapshot_by_content(self, presupro_estimate_id: str, content_hash: str) -> EstimateSnapshot | None`
- `PostgresPlanActualRepository.save_snapshot(self, snapshot: EstimateSnapshot) -> None`
- `PostgresPlanActualRepository.save_proposals(self, proposals: tuple[InvoiceLineMatchProposal, ...]) -> None`
- `PostgresPlanActualRepository.load_match_decisions(self, match_ids: tuple[str, ...]) -> tuple[InvoiceLineEstimateMatch, ...]`
- `PostgresPlanActualRepository.insert_match_decision(self, decision: InvoiceLineEstimateMatch) -> None`
- `PostgresPlanActualRepository.update_match_status(self, decision: InvoiceLineEstimateMatch) -> None`
- `PostgresPlanActualRepository.list_matches_for_line(self, invoice_id: str, content_hash: str, invoice_line_id: str) -> tuple[InvoiceLineEstimateMatch, ...]`
- `PostgresPlanActualRepository.list_matches_for_snapshot(self, estimate_snapshot_id: str, status: str) -> tuple[InvoiceLineEstimateMatch, ...]`
- `create_app(access_control: AccessControlBackend, archive: DurableArchiveService, registry: RegistryContextService, holded_gateway: HoldedGatewayService, synchronization: SynchronizationService, plan_actual: PlanActualService) -> FastAPI`

`PostgresPlanActualRepository` is owned by `plan_actual_persistence`. `save_match_decision`
was replaced by `insert_match_decision`, `update_match_status`, and `list_matches_for_line`;
`load_match_decisions` no longer fails on absent identities. The single-active-confirmation
invariant and pinned-identity completeness belong to `PlanActualService`
(`30_modules_persistence_boundary.md`).

`list_active_matches` was replaced by `list_matches_for_snapshot(estimate_snapshot_id, status)`;
the active status and the project restriction belong to `PlanActualService`.
