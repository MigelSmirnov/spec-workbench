# Cabinet Backend — box classification pass

## Status

Experimental classification overlay for `agent/cabinet-vault-experiment`.

This document does **not** modify the accepted `examples/cabinet-backend` design,
`SPEC_STANDARD`, or the classical `agent/cabinet-backend-state-0` lowering. It
classifies accepted Cabinet semantics under the box hypothesis in `DIRECTION.md`.

The accepted case is evidence. Stage 8.1 Python classes are not presumed to be
durable product identity.

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

A second rule now applies to cross-box integration:

> **If a mapping is provably determined by two self-described surfaces, it is a
> disposable compiler artifact, not durable pairwise architecture. If it is not
> provable, return a semantic gap instead of guessing.**

A box describes its own meaning and required authority. It must not need a
neighbour's API, DTO, client, endpoint, or adapter merely to state its own input
contract.

## Product-wide result

The real Cabinet design already contains a substantial box-shaped semantic core:
immutable Card revisions, source-byte custody, durable acceptance, explicit
identity, project-catalogue and estimate observations, confirmed matching
decisions, Holded publication evidence, retention decisions, authorization rules,
and audit requirements.

The largest removable surface is the classical application lowering around that
core: service/repository classes, concrete PostgreSQL/filesystem classes,
FastAPI/app-state wiring, bootstrap composition, and permanent product clients.

The important split is:

```text
Cabinet-owned durable truth and allowed effects
vs.
agent-owned choice/orchestration across independent authorities
vs.
compiler-owned derivable transient plumbing
vs.
generic host lowering/mechanism
```

## Module classification

| Classical module/surface | Box classification | Experimental disposition |
| --- | --- | --- |
| `domain_models` | data/schema | Durable schemas, identity, lifecycle, value semantics. Python classes are lowering. |
| `access_control` | policy/invariant + generic host authority | Cabinet operation/resource rules survive. Authentication, grants, throttling, credential storage, revocation, and audit enforcement belong to the host kernel. |
| `durable_archive` | data/schema + policy + capability + deterministic composition | Strong Cabinet core. `DurableArchiveService`, UoW/repository classes, PostgreSQL and filesystem implementations are candidate lowerings of generic transaction/record/blob-vault primitives. |
| `synchronization` | split local evidence/policy + orchestration | Cabinet owns local truth/evidence. Discovery, remote delivery, retries, and cross-node composition do not justify permanent product clients. |
| `registry_context` | data/schema + deterministic capability + derivable cross-box projection | Cabinet needs authoritative project-catalogue observations and assignment-validation evidence. It does not need a Registry-shaped API/DTO/client surface. A compatible source manifest can be projected transiently by the derivability compiler. |
| `plan_actual` | data/schema + deterministic operators + bounded model operation | Immutable estimate observations, explicit match decisions, unmatched identities, and arithmetic remain. External fetching is composed. Calculation is deterministic; match proposal may be bounded/non-authoritative. |
| `holded_publication` | local policy/evidence + effect-state capability | Cabinet keeps eligibility, idempotency intent, attempt evidence, and settlement rules. The external mutation is separately composed and later settled from typed evidence. |
| `holded_gateway` | transport/external authority | HTTP/API-key/gateway classes are not Cabinet semantic core merely because the classical app needed them. |
| `retention_release` | policy + deterministic capability + effect control | The data-owning box decides its destructive effect. Cross-node coordination is orchestration. |
| routers/handlers | transport lowering | Thin transports over capabilities. No business ownership. |
| service classes | classical application lowering | May disappear when capabilities compile directly into host plans/lowerings. |
| repository/UoW classes | storage lowering | Replaceable by generic host record/transaction primitives where semantics permit. |
| bootstrap/app-state wiring | deployment lowering | Generic host loads compiled box + configuration + backends + grants. |

## Generic host authority

`authorize_operation` is not an agent-callable business capability. Authentication,
grant/resource-scope checking, effect authorization, disclosure checking, replay
bounds, and audit wrap every invocation in the host. An agent cannot provide an
`AuthorizationDecision` as proof of its own authority.

## Cabinet-native capabilities

Accepted operations that map directly or nearly directly to Cabinet capabilities
include:

- archive lookup and durable-acceptance verification;
- local source attachment/status;
- explicit incomplete-source acceptance and source-loss decisions;
- project-catalogue observation acceptance and assignment validation;
- explicit plan/actual match decisions;
- unmatched-item derivation;
- deterministic plan/actual calculation;
- local retention eligibility/effect decisions.

Their service/repository shapes are not capability identity.

## Cross-box operations that must be split

The classical callables below mix Cabinet semantics with knowledge of another
system and should not survive unchanged:

- `refresh_registry_context` becomes source capability -> **proved transient
  projection** -> Cabinet-owned `project.catalogue_observation.accept`-style
  capability. The agent chooses the composition; the compiler derives plumbing
  when the two manifests prove semantic/type/authority compatibility;
- `refresh_estimate_snapshot` should become estimate-source capability -> proved
  transient projection/transformation -> Cabinet-owned estimate observation;
- synchronization/catalogue publication/VPS connection/reconciliation split by
  authority and transport ownership;
- `create_holded_purchase` and `lookup_holded_purchase` are external
  capability/connector operations, not Cabinet capabilities;
- Holded publication keeps Cabinet prepare/evidence/settle truth while the actual
  external effect is composed separately.

No permanent `registry_client`, `presupro_client`, `holded_gateway`, or
Cabinet/VPS bridge is required by this model.

## Derivability result

The first executable probe is now in:

```text
experiments/cabinet-vault/tools/box_derivability.py
experiments/cabinet-vault/registry_project_box_v0.yaml
experiments/cabinet-vault/cabinet_registry_context_box_v0.yaml
tests/test_box_derivability.py
```

For v0, the compiler derives only exact projection. A target field must declare
its own `type`, `semantic`, and (when relevant) required `authority`. The source
must provide exactly one compatible field.

Field names do not prove meaning. The source can rename `id` to
`registry_project_key` and the mapping remains derivable because the semantic ID
is `project.identity`; conversely a same-name/same-type field without semantics
is rejected.

The Cabinet side is intentionally provider-agnostic. It requires
`project.catalogue.authority` rather than a Registry client/DTO dependency.

A successful report is executable by `apply_exact_projection`, making the
adapter a disposable compilation artifact. An unresolved report cannot execute.
Current gap codes distinguish missing target meaning, missing source semantics,
type mismatch, authority mismatch, ambiguity, and unsupported transformations.

This is the integration equivalent of the existing placeholder detector: a
compiler reaching for a guess is evidence that the durable specification still
contains an unresolved decision.

## Deterministic operators versus model operations

Already deterministic under the accepted design:

- exact identity/content-hash checks;
- immutable revision selection;
- source completeness and durable acceptance;
- exact-scope filtering/status derivation;
- project-catalogue observation merge rules;
- confirmed-match filtering/unmatched-set derivation;
- plan-vs-actual aggregation and variances;
- unit/currency/tax-basis precondition rejection;
- Holded idempotency/evidence state transitions;
- retention eligibility;
- transaction/lock/stage/hash/publish/recovery sequences whose ordering is
  already closed.

`propose_invoice_line_matches` remains the clearest bounded model candidate. Its
output is non-authoritative until an explicit Cabinet decision records a match.
No evidence requires an LLM for `calculate_plan_actual`.

## Generic local host requirements

The box path still needs reusable host primitives for:

1. principal authentication and bounded grants;
2. grant-filtered manifest discovery;
3. input/output validation;
4. capability/scope/effect/disclosure enforcement;
5. deterministic record mutation plus transaction/locking;
6. opaque source-byte vault stage/verify/publish/recovery;
7. protected configuration/credentials;
8. startup recovery;
9. audit/provenance;
10. thin MCP/tool/IPC/HTTP transport.

PostgreSQL and local filesystem remain valid first lowerings. Their class names
are not required in the Cabinet semantic language.

## First real Cabinet manifest slice

`cabinet_backend_box_v0.yaml` intentionally covers archive inspection and local
source custody. It is locally authoritative, has accepted integrity/concurrency/
recovery/disclosure rules, and requires no permanent external product client.

Cross-node transfer ingest remains deferred because the classical signature
contains transport-era replica evidence that should not be copied into a box
before the cross-box authority/effect protocol is classified.

## Classical implementation surface expected to disappear

If compilation succeeds, durable Cabinet definition should not require names such
as:

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
Postgres*
LocalFilesystemSourceByteStore
HttpxHoldedHttpClient
FastAPI router/handler ownership
app.state dependency wiring
product-specific bootstrap constructor graph
Registry/PresuPro/Holded integration clients
```

Equivalent indexes, transaction rules, byte-store constraints, and security
requirements still compile into host configuration/lowering where needed.

## Remaining experiment questions

1. **Semantic vocabulary.** How small can the reusable field semantics/authority/
   identity/revision vocabulary remain while still proving real mappings? Do not
   create a global ontology by default.
2. **Deterministic transformations.** Which transformations beyond
   `exact_project` deserve closed typed operators, and what declarations prove
   them safe?
3. **Inbound estimate observation.** Can a PresuPro-like source derive into a
   provider-agnostic Cabinet estimate contract without hidden currency, tax,
   lineage, or revision decisions?
4. **Cross-box effects.** What minimum prepare/execute/observe/settle protocol is
   needed for Holded-like mutations without allowing the agent to manufacture
   Cabinet success?
5. **Local/VPS topology.** Which VPS responsibilities are separate authority
   boxes versus transport around one semantic box?
6. **Compilation.** Which `SPEC_STANDARD` information compiles into box
   semantics/policy/capabilities and which fields are only application lowering?

## Next validation

The next derivability probe is the estimate path. It should exercise richer
semantic requirements before a general-purpose adapter framework is attempted:

```text
estimate-source self-description
        -> derivability detector/compiler
        -> Cabinet-owned estimate observation
        -> explicit match decisions
        -> deterministic plan/actual calculation
```

Every new semantic field should be justified by a concrete failed proof, not by
an attempt to model the whole business world in advance.
