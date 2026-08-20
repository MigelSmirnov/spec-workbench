# Cabinet vault prototype

This experiment tests `CABINET_V0.md` with a minimal trusted runtime and then
applies the same architecture to the accepted real `examples/cabinet-backend`
design.

Read `DIRECTION.md` first when resuming the branch.

## What is durable

- box schemas and meaning;
- identity and authority requirements;
- capability definitions;
- disclosure/effect policy;
- data inside the box;
- audit/provenance requirements.

The agent does not receive a database connection, raw SQL capability, storage
paths, or box credentials.

## Spike 1 — coarse capability

`invoice.summary` accepts a project and optional date range. The trusted host
lowers that capability to a parameterized SQLite aggregate. Requests outside the
grant's project scope fail closed.

```bash
python tools/cabinet_host.py \
  experiments/cabinet-vault/cabinet_backend_invoice_summary.yaml \
  --project project-1
```

## Spike 2 — composable execution graph

`cabinet_backend_execution_graph.yaml` replaces the coarse operation with atomic
capabilities:

```text
invoice.select
  -> invoice.filter_confirmed
  -> invoice.filter_date
  -> invoice.aggregate_total
```

The agent composes the graph; the host owns every lowering. Opaque invoice-set
handles cannot escape the host. Graph preflight validates grants, argument
shape, literal/reference types, node references, output type, scope, and opaque
escape before data access.

```bash
python tools/cabinet_graph_host.py \
  experiments/cabinet-vault/cabinet_backend_execution_graph.yaml

pytest -q tests/test_cabinet_host.py tests/test_cabinet_graph_host.py
```

## Spike 3 — extract a real Cabinet box

`CABINET_BACKEND_CLASSIFICATION.md` returns to the accepted
`examples/cabinet-backend` design and classifies the real surface as data/schema,
policy, capability, deterministic composition, bounded model operation,
storage/transport lowering, or unresolved behavior.

`cabinet_backend_box_v0.yaml` is the first real manifest slice. It covers archive
inspection and local source custody and deliberately has no permanent Registry,
PresuPro, Holded, VPS, HTTP, ORM, repository, or service dependency in its
semantic surface.

The manifest keeps authorization, actor identity, decision IDs/timestamps, and
storage references host-owned. Source attachment is expressed as a deterministic
stage/verify/commit/publish/recovery sequence rather than a normative
`DurableArchiveService`/repository architecture.

```bash
pytest -q tests/test_cabinet_backend_box_manifest.py
```

## Spike 4 — derivability becomes an instrument

The integration rule is now executable:

> If a mapping is determined by the two self-described box surfaces, compile it
> as disposable plumbing. If the compiler must choose, return a semantic gap and
> repair the owning specification instead of guessing.

The first probe uses:

- `registry_project_box_v0.yaml` — source-side project-catalogue facts;
- `cabinet_registry_context_box_v0.yaml` — Cabinet-owned provider-agnostic
  project-catalogue observation contract;
- `tools/box_derivability.py` — deterministic proof/compiler;
- `tests/test_box_derivability.py` — success and fail-closed cases.

The Cabinet contract does **not** require a Registry API, DTO, client, adapter,
or even a Registry-named input schema. It requires meanings such as
`project.identity` and the authority role `project.catalogue.authority`.

For v0 a field mapping is derivable only when there is one unambiguous source
field with:

```text
same declared semantic id
+ exact type
+ required authority
```

Field names are not evidence. This deliberately derives mappings such as:

```text
RegistryProject.id
  -> ProjectCatalogueObservation.project_id
RegistryProject.name
  -> ProjectCatalogueObservation.display_name
RegistryProject.updated_at
  -> ProjectCatalogueObservation.catalogue_updated_at
```

A successful proof emits `exact_project` steps and can be executed through
`apply_exact_projection`. Extra source fields are not disclosed by that
projection. An unresolved proof cannot execute.

Structured gap codes currently include:

```text
TARGET_FIELD_NOT_SELF_DESCRIBING
SEMANTIC_NOT_DECLARED
SEMANTIC_SOURCE_NOT_FOUND
TYPE_MISMATCH
AUTHORITY_MISMATCH
AMBIGUOUS_SEMANTIC_SOURCE
UNSUPPORTED_TRANSFORMATION
```

So `mapping: normalize`, unit conversion, monetary reinterpretation, status
reinterpretation, or any other undeclared choice does not silently become model
behavior or adapter code.

Run the probe:

```bash
python tools/box_derivability.py \
  experiments/cabinet-vault/registry_project_box_v0.yaml \
  project.observe \
  experiments/cabinet-vault/cabinet_registry_context_box_v0.yaml \
  project.catalogue_observation.accept \
  --json

pytest -q tests/test_box_derivability.py
```

## Architectural rule under test

The split is now:

```text
Agent     -> chooses composition
Compiler  -> derives provable transient plumbing
Box       -> declares meaning, authority, policy, and allowed effects
Host      -> enforces authority and executes trusted lowerings
```

The long-lived artifact is the semantic contract. A pairwise adapter should be
throwaway output whenever its behavior is fully derivable from those contracts.

This changes integration growth from maintained pairwise bridges toward
independently testable box specifications plus disposable compositions. It does
not remove semantic complexity; it forces semantic decisions to live in the box
that owns them instead of accumulating in integration code.

## Next probe

The next high-value derivability case is a PresuPro-like estimate source into a
Cabinet-owned provider-agnostic estimate observation. That case should force the
detector to reveal which additional semantics are truly needed for identity,
revision/observation, currency and monetary basis, status/locking, content hash,
and lineage — without adding a global ontology up front.

After that, integrate the derived mapping IR with the execution-graph path and
continue toward compilation of the real archive/source manifest into a generic
host runtime.

## Not implemented yet

- signed grants, expiry, and replay protection;
- cryptographic key management;
- full schema-derived structural runtime validation;
- a deterministic transformation algebra beyond exact projection;
- multi-box discovery plus automatic insertion of derived mappings into the
  execution graph;
- compilation of the real archive/source manifest into the generic host;
- cross-box effect prepare/execute/observe/settle protocol;
- persistent audit storage.

The experiment branch is not covered by the current automatic Stage 8.1 CI
trigger. Do not treat the committed test files as CI-green until they are run in
a suitable checkout/runner.
