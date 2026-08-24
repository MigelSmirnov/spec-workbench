# Stage 8.1 — runtime boundary review

Date: 2026-08-24

Status: **AMBIGUITY**

Product decision update (2026-08-24): the owner accepted PostgreSQL as the
authoritative Cabinet Web metadata store and a mandatory protected local VPS
filesystem store for original bytes. The exact decision is recorded as D0-006,
A17, and `70_runtime_closure.json`. The module results remain `AMBIGUITY` until
that decision is lowered through repository/unit-of-work, byte-store, and
composition contracts and the rebuilt slices are reviewed.

Lowering update: the protected local filesystem mechanism is now closed as a
Factory-owned deterministic `source_byte_store_backend`; PostgreSQL v3
authoring is open and currently proves only the `CabinetEffect` table and
effect-journal repository methods. It intentionally remains `open`: the other
master projections, per-request unit-of-work factory, source-publication
journal, and composition root are not yet closed.

## Result

The assembled specification is not ready for implementation.  Its business
rules are substantive, but the final module slices do not close the runtime
mechanisms needed to preserve those rules across requests and process
restarts.  A generator can therefore satisfy the visible Python contracts
with materially different storage, transaction, and dependency behaviour.

This is a specification revision.  It is not eligible for bounded generation
repair.

## Finding 1 — accepted durable backend is not yet lowered

Fourteen models are classified as `master`, while
`rules.persistence_backend` is absent and the persistence authoring workbench
is disabled for this case.  Stateful services receive a generic
`database_url`, but no accepted repository, unit-of-work, transaction,
concurrency, migration, or restart-recovery contract is lowered into their
module slices.

The omission was deliberate in the earlier product document, not an implicit
SQLite decision. It is now superseded for runtime implementation by accepted
decisions D0-006 and A17: PostgreSQL owns metadata and the protected local VPS
filesystem owns original bytes. `VPS_RUNTIME_DISCOVERY_2026-08-22.md` remains
correct that the Client Portal's one-worker SQLite pattern must not be copied.
The open defect is propagation: final contracts and backend IR still expose the
old generic `database_url` service boundary.

Affected modules:

- `access_control`;
- `effect_journal`;
- `card_workspace`;
- `invoice_workspace`;
- `project_workspace`;
- `source_custody`;
- `invoice_exchange`;
- `registry_replica`;
- `runtime_control`.

Earliest return point: State 0/2 must accept the deployment and failure-policy
decision.  State 6 must then lower it into a structured persistence backend,
narrow repositories/unit-of-work contracts, and explicit startup
configuration.  State 8 assembly is rebuilt only after those sources close.

## Finding 2 — stateful repository operations are only partly lowered

The cross-module application graph is now explicit. `chatgpt_interaction`,
`web_gateway`, and `sync_gateway` receive the exact service and operation
contracts they orchestrate. Stateful services receive an external
`CabinetUnitOfWorkFactory`; each operation opens a fresh UoW, so singleton HTTP
services cannot share an active PostgreSQL transaction.

The remaining gap is the UoW surface. Effect-journal storage is closed, but
access control, Card revision history, source custody/publication journal,
transfer evidence, Registry replicas, and runtime recovery do not yet have
their typed repository methods and deterministic projections.

Affected modules:

- all still-ambiguous stateful modules listed in the Stage 8.1 ledger;
- `cabinet_persistence` until its post-contract closure is complete.

State 3 dependency ownership is repaired. State 6 must now complete the typed
repository operations and projections. Domain modules remain forbidden from
reading deployment configuration or constructing persistence/transport
adapters themselves.

## Finding 3 — atomic effects cannot be implemented from the slice

The accepted flows require atomic or recoverable coordination across effect
reservation, Card revision mutation, source custody, transfer issuance, and
receipt/reconciliation.  The final slices contain the behavioral rules but no
shared transaction boundary or declared compensation/recovery protocol.  In
particular, the `invoice_workspace` flow calls for coordination with
`effect_journal` and `card_workspace`, while its lowered dependency map is
empty.

Earliest return point: State 2 owns the failure and truthfulness policy; State
5 owns the end-to-end effect boundaries; State 6 owns the repository/unit-of-
work contracts that make those boundaries executable.

## Closed slices

- `models`: **PASS** for the deterministic model surface.
- `capability_policy`: **PASS_INTERNAL_VARIATION**; its closed capability rules
  do not require a durable adapter.
- `api`: **PASS** for the deterministic router/handler lowering.  This does not
  constitute application bootstrap or runtime-persistence closure.

## Required revision sequence

1. Accept a VPS persistence mechanism and its operational constraints; do not
   infer SQLite from the Client Portal evidence.
2. Accept the source-byte store and the database/file atomicity and recovery
   policy.
3. Define narrow repositories and unit-of-work ownership for the fourteen
   master models, including uniqueness, concurrency, migration, and restart
   behaviour.
4. Restore the behavioral module dependency graph and add an explicit
   composition/bootstrap boundary.
5. Recheck the cross-resource flows, then rebuild contracts, persistence IR,
   notes, and `global_spec.json`.
6. Rebuild and manually review every affected module slice.  Only then may the
   Stage 8.1 ledger become `closed` and Factory admission be retried.
