# Stage 8.1 — remaining module review and repair plan

## Diagnostic result

All twelve assembled module slices were reviewed. Deterministic Factory surfaces
(`models`, `api`, and `api_irregular`) are structurally closed and do not require
behavioral generation notes. The remaining findings are concentrated in the
behavioral runtime and its composition.

| Module | Result | Finding |
|---|---|---|
| `registry_context` | `AMBIGUITY` | Archive reads and mutations have no declared repository/unit-of-work runtime boundary. |
| `holded_gateway` | `AMBIGUITY` | No concrete Holded HTTP client, credential/config boundary, or composition contract is available to the generated gateway. |
| `synchronization` | `AMBIGUITY` | No concrete authenticated VPS transport is declared; accepted reconciliation/catalogue/connection responsibilities are not lowered to contracts. |
| `plan_actual` | `AMBIGUITY` | Persistent match state has no runtime boundary, and accepted propose/record/unmatched operations are absent from the contract surface. |
| `holded_publication` | `AMBIGUITY` | Logical publication state has no repository/unit-of-work runtime boundary or bootstrap wiring. |
| `retention_release` | `AMBIGUITY` | The operation promises to record an immutable release decision, but `VpsReleaseDecision` is not persistent and no state boundary is declared. |
| `api_irregular` | `PASS` | Factory-owned irregular multipart seam is structurally closed; behavioral archive policy remains delegated. |
| `api` | `PASS` | Factory-owned router and handler lowering is structurally closed. |

The earlier `durable_archive` finding remains open: PostgreSQL archive access,
source-byte custody, cross-resource failure semantics, and composition are not
declared.

## Repair strategy

Repair the earliest affected state once, then propagate forward. Do not add
module-local ad-hoc database connections or environment reads to generation
notes.

### 1. Close deployment mechanisms and ownership

At the earliest design state that owns the fact, accept:

- one PostgreSQL runtime persistence/unit-of-work mechanism for stateful Cabinet
  modules;
- one Backend-owned local filesystem byte store for source artifacts;
- one authenticated VPS transport client;
- one Holded HTTP client with secret ownership and safe error translation;
- explicit startup configuration and fail-closed behavior for every concrete
  implementation.

Choose narrow ports so business modules retain decisions while adapters provide
only persistence, byte custody, and transport mechanisms.

### 2. Repair incomplete product/state surfaces

- `synchronization`: decide and lower catalogue publication, connection
  observation, ambiguous-outcome reconciliation, and any required conflict/status
  persistence.
- `plan_actual`: lower proposal, confirmed match decision, and unmatched-item
  operations; include `InvoiceLineEstimateMatch` and any immutable estimate or
  analysis evidence that the accepted behavior requires to survive restart.
- `retention_release`: classify `VpsReleaseDecision` as durable issued evidence
  and define how a still-applicable evaluation is rechecked atomically before the
  decision is recorded.
- Verify whether the currently candidate archive and status operations are
  required by accepted flows; either lower them or explicitly remove them from the
  first implementation scope.

### 3. Propagate through module and contract states

Define interface models and complete method contracts for the accepted ports,
then add concrete local implementations. Behavioral function contracts must
receive dependencies explicitly or be constructed as cohesive service objects;
the choice must be uniform and visible to Factory.

Add generation notes for:

- transaction scope and concurrency;
- retry and idempotency at remote mutation boundaries;
- database/byte-store compensation and recovery;
- credential secrecy and safe logging;
- startup failure when required configuration is absent.

### 4. Repair composition last among source states

Expand `bootstrap` so it constructs the PostgreSQL runtime, filesystem store, VPS
client, Holded client, domain services, and access-control backend, then supplies
the complete application dependency graph to `create_app`. Keep offline owner
administration separate from HTTP/MCP exposure.

### 5. Regenerate and repeat Stage 8.1

After propagation, rebuild all affected slices. Review in dependency order:

1. `durable_archive`;
2. `registry_context`;
3. `holded_gateway`;
4. `synchronization`;
5. `plan_actual`;
6. `holded_publication`;
7. `retention_release`;
8. `bootstrap`, `api_irregular`, and `api` integration.

Run full assembly, identity closure, deterministic-data validation, and module
slice hash refresh only after the semantic findings are closed.

## Accepted durable archive runtime decision

The product owner accepted the following local Linux lowering for the first
implementation. This closes the mechanism choice but does not close the module
review until the decision is propagated and the rebuilt slice passes.

- PostgreSQL is the authoritative metadata and recovery journal.
- Source bytes are held by one Backend-owned local filesystem store rooted at a
  required deployment-configured absolute path.
- A candidate file is written under a non-public staging name, flushed, reopened,
  and SHA-256 verified before it can be referenced by accepted archive metadata.
- The PostgreSQL unit of work records the candidate identity, expected final
  content-addressed location, and transition state in the same transaction as
  the archive mutation.
- Publication uses an atomic same-filesystem rename from staging to the final
  content-addressed path. A final path is never replaced by different bytes.
- A transaction failure before commit removes the candidate staging file. A
  failure after metadata commit remains a recoverable pending-publication
  operation; startup recovery verifies and finalizes it or records a safe
  failed state without exposing the replica as available.
- Archive reads treat a source replica as available only after both committed
  metadata and a reopened, hash-matching final file are present.
- Deletion and compensation never remove a previously accepted replica and
  never weaken immutable Card, incomplete-acceptance, or source-loss evidence.
- Cross-process races are resolved by PostgreSQL uniqueness/locking plus
  content-addressed final paths; check-then-act filesystem observations are not
  an authority boundary.
- Bootstrap must fail closed when the PostgreSQL URL or byte-store root is
  absent, relative, unusable, or located on a filesystem that cannot provide
  atomic rename between staging and final paths.

The generated behavioral module must receive narrow persistence/unit-of-work
and byte-custody dependencies explicitly. Adapters provide mechanisms only;
all archive acceptance, provenance, source-completeness, and recovery decisions
remain owned by `durable_archive`.

