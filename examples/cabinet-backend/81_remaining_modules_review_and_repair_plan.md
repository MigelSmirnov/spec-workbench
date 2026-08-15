# Stage 8.1 — remaining module review and repair plan

## Progress

| Module | Status | Current result |
|---|---|---|
| `durable_archive` | semantic surface repaired | Archive operations and evidence are lowered; shared runtime persistence and byte-store composition remain part of the cross-cutting repair. |
| `registry_context` | candidate runtime-closed | Repository resource, concrete local-Linux binding, effects, durable evidence, atomic group, capability dispositions, and composition arguments are declared in the candidate Runtime IR. |
| `holded_gateway` | candidate runtime-closed | Credential provider, HTTP/repository resources, concrete bindings, single-POST atomic strategy, durable lookup evidence, effects, and capability dispositions are declared. |
| `synchronization` | next | VPS transport and accepted reconciliation/catalogue responsibilities remain open. |
| `plan_actual` | pending | Persistent match operations and repository boundary remain open. |
| `holded_publication` | pending | Logical publication repository/UoW and composition remain open. |
| `retention_release` | pending | Durable release-decision recording and atomic recheck remain open. |
| `bootstrap` | in progress | Access control plus Registry/Holded constructor graph is explicit; remaining-module resources still block complete local-Linux closure. |

## Forward Runtime Closure preparation

`60_runtime_closure_authoring.json` records a candidate form of the proposed
Runtime Closure IR without changing the current `global_spec.json` schema. For
the completed Registry/Holded scope it includes mandatory callable effect
dispositions, resources, concrete constructors, config references, capability
dispositions, durable evidence, atomic strategies, and composition bindings.

The full profile intentionally remains `in_progress`: the concrete access-control
binding is accepted, while resources and effects of the remaining behavioral
modules stay explicit blockers rather than implicit generation work.

## Diagnostic result

The deterministic Factory surfaces (`models`, `api`, and `api_irregular`) are
structurally closed. Remaining findings are concentrated in the behavioral
runtime and composition. The earlier `durable_archive` finding also remains
open at the concrete runtime level: PostgreSQL archive access, source-byte
custody, cross-resource failure semantics, and full composition are not yet
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
