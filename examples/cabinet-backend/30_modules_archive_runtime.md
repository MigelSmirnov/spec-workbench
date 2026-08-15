# State 3 repair — durable archive runtime boundaries

## Module: durable_archive

Owns:

- archive acceptance and source-completeness decisions;
- the A70 cross-resource publication state machine;
- PostgreSQL transaction scope and locking requirements;
- compensation and startup recovery decisions;
- conversion of persistence/byte-custody failures into safe archive outcomes.

Exports remain the existing narrow archive capabilities. Callers must not
coordinate a database transaction and filesystem operation themselves.

Depends on:

- `ArchiveUnitOfWork`, a narrow metadata transaction port;
- `SourceByteStore`, a narrow byte-custody port.

Concrete local implementations owned by this module:

- `PostgresArchiveUnitOfWork`;
- `LocalFilesystemSourceByteStore`;
- `DurableArchiveService`, which composes both ports and exposes the accepted
  archive capabilities.

Must not own:

- HTTP or multipart parsing;
- authentication policy;
- VPS or Holded transport;
- deployment environment lookup;
- arbitrary filesystem paths supplied by callers.

## Module: bootstrap

Owns construction only:

- read the required PostgreSQL URL and source-store root from the declared
  environment-variable names;
- validate the root is absolute, private, writable, and supports atomic rename
  between staging and final directories;
- construct the PostgreSQL unit of work, filesystem store, and
  `DurableArchiveService`;
- run publication recovery before exposing the application;
- fail startup on missing configuration, failed recovery, or unusable storage;
- inject the service into application composition.

Bootstrap must not decide whether evidence is acceptable, complete, quarantined,
lost, or available.

## Dependency rule

Behavioral consumers receive the cohesive `DurableArchiveService` boundary
explicitly. No generated module may recover this dependency through a module
global, service locator, implicit singleton, direct environment read, or
ad-hoc database/filesystem construction.
