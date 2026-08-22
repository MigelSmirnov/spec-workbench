# State 7 repair — Registry context runtime notes

RegistryContextService requires the exact supplied repository and has no nullable, module-global, in-memory, or service-locator fallback.

A Registry refresh holds the catalogue lock, lists the stored WorkObjects, derives the typed WorkObject merge according to accepted Registry rules, upserts it in one PostgreSQL transaction, and returns a result describing that committed observation. Failure rolls back and preserves the previous committed catalogue.

Assignment validation reads the exact accepted invoice revision and current WorkObject evidence through declared dependencies, persists one immutable ObjectAssignmentValidation result, and never fabricates a positive outcome for unavailable or ambiguous context.

Repository transaction operations use one connection and transaction per service operation. Catalogue locking serializes competing full replacements. Typed load operations return None for absence; façade operations translate absence to the already accepted safe errors.

The concrete PostgreSQL repository treats the database URL as secret and never logs it. Bootstrap reuses the declared Cabinet database URL, constructs one RegistryContextService, binds it in application state, and fails startup when construction fails.

Assignment validation resolves the exact accepted immutable Card revision through the supplied DurableArchiveService; invoice IDs and hashes alone are not treated as evidence.
