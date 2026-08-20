# Cabinet Backend — box classification pass

## Status

Experimental classification overlay for `agent/cabinet-vault-experiment`.

This document does **not** modify the accepted `examples/cabinet-backend` design,
`SPEC_STANDARD`, or the classical `agent/cabinet-backend-state-0` lowering. It
classifies the already accepted Cabinet Backend semantics under the hypothesis in
`DIRECTION.md`:

> durable product truth should compile into a self-describing Cabinet box and a
> generic trusted host; cross-product orchestration belongs to the agent session.

The accepted Cabinet Backend case is deliberately treated as evidence, not as a
set of Python classes that must survive unchanged.

## Classification rule

Each accepted element is classified as one or more of:

```text
data/schema
policy/invariant
capability
deterministic operator/composition
model operation
storage/transport lowering
truly unresolved behavior
```

A class, module, repository, router, client, or service name is not durable merely
because Stage 8.1 needed it to make the classical application generation path
implementation-complete.

## Product-wide result

The real Cabinet design already contains a substantial box-shaped semantic core:
immutable Card revisions, source-byte custody, durable acceptance, explicit
identity, Registry and PresuPro observations, confirmed matching decisions,
Holded publication evidence, retention decisions, authorization rules, and audit
requirements.

The largest removable surface is the application lowering added around that
core: service classes, repository classes, concrete PostgreSQL classes, FastAPI
routers/app-state wiring, bootstrap composition, and permanent product-specific
clients.

The important split is not `domain` versus `infrastructure`. It is:

```text
Cabinet-owned durable truth and allowed effects
vs.
agent-owned transient composition across independent authorities
vs.
generic host lowering/mechanism
```

## Module classification

| Classical module/surface | Box classification | Experimental disposition |
| --- | --- | --- |
| `domain_models` | data/schema | Survives as durable schemas, identity, lifecycle, and value semantics. Python model classes are a lowering. |
| `access_control` | policy/invariant + generic host authority | Cabinet-specific operation/resource rules survive. Authentication, grant verification, throttling, credential storage, revocation, and audit enforcement belong to the trusted host kernel. `PostgresAccessControlBackend` and bootstrap wiring are not product semantics. |
| `durable_archive` | data/schema + policy/invariant + capability + deterministic composition | Strongest Cabinet-box core. Immutable revisions, durable acceptance, source integrity, missing/lost-source decisions, and disclosure remain Cabinet semantics. `DurableArchiveService`, `ArchiveUnitOfWork`, concrete PostgreSQL UoW, and filesystem store are classical lowerings of generic record/transaction/blob-vault primitives. |
| `synchronization` | split: local evidence/policy + agent/infrastructure orchestration | Cabinet may own durable acceptance and local transfer evidence. Discovery, remote delivery, connection observation, retries, and composition with another Cabinet/VPS authority should not require a permanent product client. The agent or infrastructure transport layer coordinates independent boxes. |
| `registry_context` | data/schema + deterministic capability; cross-box fetch moves to agent | Cabinet-owned `WorkObject`, Registry snapshots, and assignment-validation evidence remain. Registry polling/client/API knowledge disappears from Cabinet. Agent discovers Registry, obtains a typed result, maps it transiently, then invokes a Cabinet observation/merge capability. |
| `plan_actual` | data/schema + deterministic operators + bounded model operation | Immutable estimate snapshots, confirmed match decisions, unmatched identities, and plan-vs-actual arithmetic remain. Fetching PresuPro moves to agent composition. `calculate_plan_actual` is deterministic. `propose_invoice_line_matches` is the clearest current candidate for a bounded, non-authoritative model operation. |
| `holded_publication` | local policy/evidence + effect-state capability; external mutation moves to agent composition | Cabinet keeps publication eligibility, idempotency intent, attempt/evidence state, and settlement rules. A permanent Holded API client is not required inside Cabinet. Agent composes Cabinet state transitions with a separately discovered Holded capability and returns bounded typed observations for Cabinet verification/settlement. |
| `holded_gateway` | storage/transport lowering or separate external authority | Does not belong to the Cabinet semantic core merely because the classical app needed HTTP/API-key machinery. `HoldedHttpClient`, `HttpxHoldedHttpClient`, gateway service, API-key config, and remote response DTOs leave the Cabinet product surface unless Holded is intentionally wrapped as its own box/connector. |
| `retention_release` | policy/invariant + deterministic capability + effect control | Local evidence evaluation and deletion/release authority stay with the data-owning box. Cross-node coordination is agent orchestration; the box must still decide whether its own destructive effect is allowed. |
| HTTP/MCP routers and handlers | storage/transport lowering | Thin transports over the same capability surface. No business ownership. |
| service classes | classical application lowering | May disappear when capability semantics compile directly into generic host plans/lowerings. A service class is not required as a normative intermediate artifact. |
| repository/UoW classes | storage lowering | Replace with generic host record/transaction primitives plus compiled schema/index/locking requirements where expressible. Product-specific repository names need not survive. |
| `bootstrap` / app-state dependency injection | deployment lowering | Generic host loads a compiled box, host configuration, storage backends, and grants. Product-specific constructor graphs should not be durable semantics. |

## Callable disposition

### Generic host authority

`authorize_operation` is not an agent-callable business capability. Authentication,
grant/resource-scope checking, effect authorization, disclosure checking, replay
bounds, and security audit should wrap every capability invocation in the host.
An `AuthorizationDecision` therefore must not be supplied by an agent as proof of
its own authority.

### Cabinet-native capabilities

The following accepted operations map directly or nearly directly to Cabinet
capabilities:

- archive lookup and durable-acceptance verification;
- local source attachment and source-status observation;
- accepting explicit incomplete-source evidence;
- recording explicit source-loss decisions;
- Cabinet-owned Registry observation merge and assignment validation;
- persistence of explicit plan/actual match decisions;
- unmatched-item derivation;
- deterministic plan/actual calculation;
- local retention eligibility/effect decisions.

Their Python service/repository shapes are not part of the capability identity.

### Cross-box operations that must be split

The classical callables below mix Cabinet semantics with knowledge of another
system and therefore should not survive unchanged as Cabinet capabilities:

- `refresh_registry_context` — split into `Registry -> typed result`, transient
  agent mapping, then a Cabinet-owned observation/merge capability;
- `refresh_estimate_snapshot` — split into `PresuPro -> typed estimate result`,
  transient mapping, then Cabinet snapshot acceptance;
- `synchronize_invoice_work`, Registry catalogue publication, VPS connection
  observation, and transfer reconciliation — split by authority; transport and
  remote calls are not Cabinet business semantics;
- `create_holded_purchase` and `lookup_holded_purchase` — external Holded
  capabilities/connector operations, not Cabinet capabilities;
- `request_holded_publication` / reconciliation — retain Cabinet-owned
  preparation, idempotency, evidence, and settlement transitions but compose the
  actual Holded effect in the agent execution graph.

No permanent `registry_client`, `presupro_client`, `holded_gateway`, or
Cabinet/VPS bridge is required by this model.

## Deterministic operators versus model operations

### Deterministic now

The accepted design is already specific enough to lower these without an LLM:

- exact identity and content-hash checks;
- immutable revision selection;
- source completeness and durable-acceptance verification;
- exact-scope filtering and status derivation;
- Registry observation merge rules;
- confirmed-match filtering;
- unmatched-set derivation;
- plan-vs-actual aggregation and variances;
- unit/currency/tax-basis precondition rejection;
- Holded attempt/idempotency state transitions and bounded verification rules;
- retention eligibility checks;
- transaction, lock, staging, hash verification, atomic publication, and recovery
  sequences where the accepted rules already close their ordering.

### Bounded model operation candidate

`propose_invoice_line_matches` is the clearest current runtime model-semantic
operation. Similarity may propose a candidate but cannot confirm a match or
change authority. Its input and output must remain typed and bounded, and its
result remains non-authoritative until an explicit Cabinet match-decision
capability records a human/agent-approved decision.

No evidence currently requires an LLM for `calculate_plan_actual` itself.

## Generic local host requirements extracted from the classical design

The first real Cabinet box needs a host kernel with reusable primitives for:

1. principal authentication and bounded grants;
2. typed manifest discovery filtered by grant;
3. input/output schema validation;
4. capability, resource-scope, effect, and disclosure enforcement;
5. deterministic record selection/mutation and transaction/locking control;
6. an opaque source-byte vault with stage/verify/publish/recovery semantics;
7. protected configuration and credentials;
8. startup recovery for committed-but-unfinished local effects;
9. audit/provenance evidence for accepted requests, policy version, effects, and
   disclosed results;
10. thin MCP/tool/IPC/HTTP transports that do not own semantics.

PostgreSQL and a local filesystem remain valid first lowerings, but `Postgres*`,
`LocalFilesystem*`, FastAPI, and app-state injection are not required in the
Cabinet semantic language.

## First real manifest slice

The first manifest in `cabinet_backend_box_v0.yaml` intentionally covers
**archive inspection and local source custody** rather than the whole classical
application.

This slice is chosen because:

- it is a real accepted Cabinet use case;
- the authority and data are local to Cabinet;
- the classical design already closes integrity, concurrency, recovery, and
  disclosure constraints;
- it requires generic host record/transaction/blob-vault mechanisms but no
  permanent Registry, PresuPro, Holded, or VPS client;
- it exposes immediately whether service/repository/router classes are needed as
  durable product artifacts.

The slice deliberately does not redesign cross-node transfer ingestion yet. The
accepted classical transfer signature contains transport-era replica evidence;
changing that boundary before the cross-box authority protocol is classified
would invent semantics rather than extract them.

## Classical implementation surface expected to disappear

If compilation succeeds, these names should not be needed in the durable Cabinet
product definition merely to preserve accepted behavior:

```text
DurableArchiveService
PlanActualService
RegistryContextService
SynchronizationService
HoldedGatewayService

ArchiveUnitOfWork
PlanActualRepository
RegistryContextRepository
SynchronizationRepository
HoldedAttemptRepository

PostgresArchiveUnitOfWork
PostgresPlanActualRepository
PostgresRegistryContextRepository
PostgresSynchronizationRepository
PostgresAccessControlBackend
LocalFilesystemSourceByteStore
HttpxHoldedHttpClient

FastAPI router/handler ownership
app.state dependency wiring
product-specific bootstrap constructor graph
Registry/PresuPro/Holded integration clients
```

Equivalent storage indexes, transaction rules, byte-store constraints, and
security requirements may still compile into host configuration/lowering. What
is expected to disappear is their status as product-specific application
architecture.

## Truly unresolved experiment questions

1. **Inbound observations.** Define canonical Cabinet-owned typed observation
   schemas for Registry, PresuPro, Holded, and remote Cabinet evidence without
   importing another product's DTO/API identity into Cabinet.
2. **Cross-box effects.** Define the minimum prepare/execute/observe/settle
   protocol needed for effects such as Holded publication without giving the
   agent authority to manufacture Cabinet success.
3. **Local/VPS topology.** Decide which existing VPS responsibilities are a
   separate box versus infrastructure transport around the same semantic box.
4. **Model execution.** Define where bounded semantic model operations run and
   how grants, disclosure, provenance, and deterministic fallbacks constrain
   them.
5. **Compilation.** Identify which existing `SPEC_STANDARD` fields compile
   directly into box schemas/policies/capabilities and which application-oriented
   fields are merely one lowering.

These are experiment questions, not permission to reopen already accepted
Cabinet business semantics.

## Next validation

After the archive/source-custody slice, the highest-value next slice is
`plan_actual` because it exercises all three target mechanisms at once:

```text
external typed observation accepted into Cabinet
+ bounded semantic match proposal
+ deterministic confirmed-result calculation
```

It should be possible to implement that slice without a PresuPro client inside
Cabinet and without a permanent `PlanActualService`/repository architecture.
