# State 6 repair — Registry context runtime contracts

## Service

- RegistryContextService.__init__(self, repository: RegistryContextRepository, archive: DurableArchiveService) -> None
- RegistryContextService.refresh_registry_context(self, projects: tuple[RegistryProjectObservation, ...]) -> RegistryRefreshResult
- RegistryContextService.validate_card_assignment(self, invoice_id: str, content_hash: str) -> ObjectAssignmentValidation
- RegistryContextService.get_assignment_validation(self, invoice_id: str, content_hash: str) -> ObjectAssignmentValidation
- RegistryContextService.get_work_object(self, project_id: str) -> WorkObject

The existing module functions remain façade operations with an explicit RegistryContextService first parameter so deterministic handlers and cross-module calls retain stable callable names.

## Repository port

- RegistryContextRepository.begin(self) -> None
- RegistryContextRepository.commit(self) -> None
- RegistryContextRepository.rollback(self) -> None
- RegistryContextRepository.lock_catalogue(self) -> None
- RegistryContextRepository.list_work_objects(self) -> tuple[WorkObject, ...]
- RegistryContextRepository.upsert_work_objects(self, work_objects: tuple[WorkObject, ...]) -> None
- RegistryContextRepository.load_work_object(self, project_id: str) -> WorkObject | None
- RegistryContextRepository.save_assignment_validation(self, validation: ObjectAssignmentValidation) -> None
- RegistryContextRepository.load_assignment_validation(self, invoice_id: str, content_hash: str) -> ObjectAssignmentValidation | None

Generic query dictionaries and untyped save methods are forbidden.

## Concrete adapter

PostgresRegistryContextRepository.__init__(self, database_url: str) -> None
PostgresRegistryContextRepository.begin(self) -> None
PostgresRegistryContextRepository.commit(self) -> None
PostgresRegistryContextRepository.rollback(self) -> None
PostgresRegistryContextRepository.lock_catalogue(self) -> None
PostgresRegistryContextRepository.list_work_objects(self) -> tuple[WorkObject, ...]
PostgresRegistryContextRepository.upsert_work_objects(self, work_objects: tuple[WorkObject, ...]) -> None
PostgresRegistryContextRepository.load_work_object(self, project_id: str) -> WorkObject | None
PostgresRegistryContextRepository.save_assignment_validation(self, validation: ObjectAssignmentValidation) -> None
PostgresRegistryContextRepository.load_assignment_validation(self, invoice_id: str, content_hash: str) -> ObjectAssignmentValidation | None

The constructor validates connectivity but does not read environment variables or own Registry business policy.

`PostgresRegistryContextRepository` is owned by `registry_context_persistence`.
`merge_work_objects` was replaced by `list_work_objects` plus the keyed `upsert_work_objects`;
the merge itself is derived by `RegistryContextService.refresh_registry_context`
(`30_modules_persistence_boundary.md`).
