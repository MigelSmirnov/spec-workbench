# State 3 — accepted autonomous runtime boundary revision

This revision propagates D0-006 and A17 without moving business decisions into
infrastructure. Existing application modules receive ports; they do not open
PostgreSQL connections, derive filesystem paths, or read deployment settings.

## `cabinet_persistence`

### Owns

`PostgresCabinetUnitOfWork`, schema creation/migration, PostgreSQL connection
and transaction lifetime, row/model codecs, exact locks, uniqueness
constraints, and plain typed reads/appends/field updates for all Cabinet
Web-owned master state.

### Knows

The closed table projections, identity keys, current selectors, immutable
evidence relations, and the `CabinetUnitOfWork` interface. It knows no business
meaning beyond what is necessary to preserve and retrieve exact typed facts.

### Must not own

Card lifecycle, validation, duplicate policy, authorization, idempotency
equivalence, source availability, transfer reconciliation, Registry acceptance,
retention, or any environment read.

### Hides

PostgreSQL driver usage, connection pooling, migrations, table and index names,
serialization, locks, and transaction cleanup.

### Candidate public capabilities

```text
create_cabinet_schema
```

### Depth assessment

kind: deep
hidden mechanism: one SQL unit-of-work over the closed table registry

One deep persistence module supplies a shared transaction authority for effects
that cross Card, journal, custody, and synchronization records. Its methods are
mechanical storage operations; application modules retain every transition and
truthfulness decision.

## `source_byte_store`

### Owns

`LocalFilesystemSourceByteStore`, private exclusive staging, file and directory
flush discipline, reopened size/SHA-256 verification, content-addressed final
references, same-filesystem atomic publication, safe staging removal, and
verified read streams beneath the configured root.

### Knows

Only opaque publication identifiers, expected content hashes and sizes, and
the `SourceByteStore` interface.

### Must not own

Card/source identity policy, metadata transactions, custody transitions,
release eligibility, synchronization, HTTP, or environment reads.

### Hides

Directory layout, modes, path confinement, symlink rejection, fsync, atomic
rename, and regular-file reopening.

### Candidate public capabilities

```text
recover_source_publications
```

### Depth assessment

kind: deep
hidden mechanism: confined content-addressed filesystem custody with atomic publication

The byte store is a narrow mechanism. PostgreSQL journal state and
`source_custody` decide when a verified candidate may become logically
available; a filesystem observation alone is never authority.

## `system_clock`

### Owns

Exactly the concrete `SystemClock` implementation of the `Clock` port.

### Knows

Only the `Clock` interface and the host timezone-aware UTC wall clock.

### Must not own

Business policy, persistence, configuration loading, scheduling, cached time,
or service construction.

### Hides

The per-call `datetime.now(timezone.utc)` wall-clock read behind the narrow
`Clock.now` interface.

### Candidate public capabilities

```text
SystemClock
```

### Depth assessment

kind: deep
hidden mechanism: deterministic binding of the process UTC wall clock to Clock

The adapter is deliberately separate from the composition root so services
depend only on `Clock`, while `bootstrap` constructs and shares one concrete
instance.

## `canonical_digest`

### Owns

Exactly the canonical digest recipes of the application, one function per
entry of `rules.canonical_digest_backend.recipes`: `request_hash`,
`catalogue_content_digest`, `manifest_hash`, `canonical_json_text_digest`,
`string_tuple_digest`.

### Knows

Only the closed procedure of `canonical_digest_backend/v1`: canonical JSON
(sorted keys, compact separators, `ensure_ascii` False, UTF-8) under SHA-256,
with the declared field exclusions and UTC normalization per recipe.

### Must not own

Which value is digested when, business policy, persistence, or any stored
record; the consumer names the recipe and supplies the exact value.

### Hides

Serialization, exclusion and datetime normalization of the digested value so
that no consumer module re-spells the procedure (the promoted tree carried
four spellings and a duck-typed `hasattr` before `model_dump`, 2026-09-05).

### Candidate public capabilities

```text
request_hash
catalogue_content_digest
manifest_hash
canonical_json_text_digest
string_tuple_digest
```

### Depth assessment

kind: deep
hidden mechanism: deterministic canonical serialization under one digest procedure

Emitted, never generated: a digest is a persisted key — data plus a witnessed
vector — and the A09 catalogue vector is reproduced by the emitter exactly.

## `bootstrap`

### Owns

The only environment/configuration read, construction of
`PostgresCabinetUnitOfWork`, `LocalFilesystemSourceByteStore`, and one shared
`SystemClock` supplied by `system_clock`, migration and
startup recovery before traffic, construction of all application services and
gateways, and delivery of the complete graph to `create_app`.

### Knows

Required PostgreSQL URL, credential pepper, private absolute storage root,
accepted migration version, and every explicit constructor dependency.

### Must not own

Business policy, HTTP operation selection, authorization decisions, source
availability decisions, synchronization scheduling, or fallback defaults for
missing protected configuration.

### Hides

Deployment configuration loading, adapter construction order, health startup
ordering, wiring of one shared timezone-aware UTC clock, and teardown.

### Candidate public capabilities

```text
create_cabinet_web_app
```

### Depth assessment

kind: deep
hidden mechanism: protected composition of the service graph from closed deployment settings

One composition root makes the runtime graph reviewable and prevents domain
modules from inventing adapters or silently coupling Web availability to the
intermittent local backend.

## Revised dependency direction

```text
bootstrap
  -> cabinet_persistence -> models
  -> source_byte_store -> models
  -> system_clock -> models.Clock
  -> application services -> models + CabinetUnitOfWork + Clock
  -> source_custody -> CabinetUnitOfWork + SourceByteStore
  -> gateways -> application services
  -> api.create_app

local backend (intermittent)
  -> sync_gateway only
  -/> bootstrap, PostgreSQL, filesystem, or ordinary Web operations
```
