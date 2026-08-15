# State 3 repair — Registry context runtime boundary

## Module: registry_context

Owns Registry catalogue projection, WorkObject lifecycle, assignment-validation evidence, exact lookup semantics, and concurrency decisions for Registry refresh and card assignment.

Depends on one narrow RegistryContextRepository mechanism. The module provides RegistryContextService as the cohesive boundary consumed by other modules.

The repository must not decide Registry status meaning, assignment eligibility, freshness, or validation outcomes. It provides PostgreSQL locking, reads, and typed persistence only.

Concrete local implementation: PostgresRegistryContextRepository.

## Module: bootstrap

Bootstrap constructs the PostgreSQL repository from the already required Cabinet database URL, constructs RegistryContextService, and injects it into api.create_app. It must not create a second database configuration or silently fall back to memory.

## Isolation rule

RegistryContextRepository is separate from ArchiveUnitOfWork. Sharing the deployment database and connection-pool mechanism does not merge transactions, schemas, persistence methods, or domain ownership.

RegistryContextService also receives DurableArchiveService to resolve the exact accepted immutable Card revision required by assignment validation. Registry context must not read archive persistence directly.
