# Cabinet Vault Experiment — Direction

## Read this first

This document is the session handoff and architectural north star for branch
`agent/cabinet-vault-experiment`.

Do not restart the discussion from the question "should Cabinet Backend be a
classical application?". The working hypothesis is already stronger:

> Cabinet Backend should be tested as a locally running, self-describing data
> box compiled from specification, not as a product-specific backend application.

`SPEC_STANDARD` remains the language used by the Factory. The experiment asks
which parts of that language form a more fundamental semantic/data language that
can compile into a box and a generic host.

## Core architecture

A box is a durable semantic, data, and authority boundary.

A box owns:

- schemas and identity;
- data and storage locality;
- invariants and lifecycle;
- capabilities;
- authorization and effect policy;
- disclosure policy;
- provenance and audit requirements.

A box MUST NOT know other product boxes by address, API, DTO, or dependency.

There is no permanent `Registry -> Cabinet`, `PresuPro -> Portal`, or
`Cabinet -> PresuPro` integration layer.

## The agent is the integration layer

Cross-product work belongs to the agent session, not to either box.

Example user intent:

> Register a new client in Registry and add a client card to Cabinet.

The desired runtime model is:

```text
User
  -> Agent
      -> discover Registry capabilities and schemas
      -> Registry.customer.create(...)
      -> receive typed RegistryCustomer result
      -> construct a transient typed mapping
      -> discover Cabinet capabilities and schemas
      -> Cabinet.contact.create(...)
```

Registry does not know Cabinet exists.
Cabinet does not know Registry exists.
The mapping is not a permanent adapter owned by either product.

The same applies to PresuPro, Client Portal, project designers, PDF generation,
and future boxes.

## Agent responsibilities versus box responsibilities

The agent owns transient:

- intent interpretation;
- discovery;
- routing between boxes;
- orchestration;
- composition of capabilities;
- typed field mapping/adaptation;
- optional bounded semantic/model operations;
- construction of an execution graph for the current task.

The box/host owns durable:

- data authority;
- authentication and grants;
- type/schema validation;
- capability semantics;
- policy enforcement;
- transaction/effect control;
- deterministic lowering;
- storage access;
- protected source files and credentials;
- disclosure boundaries;
- audit/provenance.

The agent decides HOW allowed operations are composed.
The boxes decide WHAT is allowed.

## No permanent cross-box adapters

Do not introduce product-specific code such as:

```text
registry_client.py
presupro_adapter.py
portal_sync_service.py
cabinet_registry_bridge.py
```

merely because one user task uses multiple products.

Prefer a transient typed graph such as:

```text
PresuPro.estimate.get
  -> filter/project/map
  -> PDF.generate
  -> ClientPortal.content.put
```

The graph belongs to the agent execution/session. Boxes remain independent.

Physical endpoint discovery is infrastructure, not product semantics. Business
specifications SHOULD refer to box identity/capability, not hard-coded network
addresses.

## Determinism target

The main experiment is NOT "let an LLM generate arbitrary backend code".

The target is the opposite: move as much behavior as possible into a closed,
typed, deterministic capability algebra and deterministic lowerings.

Preferred order:

1. deterministic typed operator/capability;
2. deterministic composition of operators;
3. bounded model/LLM operation with typed input and output when semantic
   interpretation is genuinely required;
4. sandboxed ephemeral generated code only as a last escape hatch.

If behavior can be expressed as typed operators such as select, filter,
project, map, derive, aggregate, validate, mutate, or publish, a generated
project-specific function should be treated as unnecessary implementation
surface and potentially as a missing language feature.

## Relationship to current SPEC_STANDARD / Factory work

Do not discard the existing Cabinet Backend design work.

Reuse accepted product and design decisions for:

- models;
- identity;
- invariants;
- lifecycle;
- persistence semantics;
- authority/access control;
- provenance;
- business behavior.

Then classify each existing application-oriented element as one of:

```text
data/schema
policy/invariant
capability
deterministic operator/composition
model operation
storage/transport lowering
truly unresolved behavior
```

The experiment tests whether modules, routers, service classes, repositories,
and integration clients are merely one classical application lowering rather
than the durable product definition.

## Cabinet Backend target

Do not continue toward a large local `Cabinet_backend` application by default.

The target shape under test is:

```text
Cabinet box specification
        -> deterministic compilation
        -> Local Cabinet Host
             - schemas/manifest
             - auth/grants
             - typed capability checker
             - policy engine
             - deterministic execution/lowering
             - PostgreSQL/storage backend
             - source-file vault
             - transactions
             - audit/provenance
             - thin MCP/tool/IPC transport
```

The local host may be long-lived trusted infrastructure. Product-specific
application orchestration should not automatically become long-lived code.

## Cabinet_web boundary

Do not rewrite or migrate `Cabinet_web` as part of this experiment.

`Cabinet_web` is already deployed on VPS and is being built as a user/Web/agent
surface. Treat it as an existing consumer and source of real Cabinet domain
contracts when useful.

The current experiment concerns the future local Cabinet Backend shape.

## Current implemented spikes

The branch now contains:

- `CABINET_V0.md` — conceptual self-describing box model;
- `cabinet_backend_invoice_summary.yaml` — one coarse capability example;
- `cabinet_backend_execution_graph.yaml` — atomic typed capability graph;
- `tools/cabinet_host.py` — minimal trusted deterministic host;
- `tools/cabinet_graph_host.py` — graph execution with opaque intermediate
  handles and typed preflight validation;
- focused tests for grant/scope/type/output boundaries;
- `CABINET_BACKEND_CLASSIFICATION.md` — classification pass over the accepted
  real `examples/cabinet-backend` design, including the split between durable
  Cabinet semantics, generic-host mechanisms, and agent-owned cross-box work;
- `cabinet_backend_box_v0.yaml` — first real Cabinet manifest slice for archive
  inspection and local source custody;
- `tests/test_cabinet_backend_box_manifest.py` — manifest boundary tests that
  reject permanent external dependencies and agent-supplied authority/storage
  references.

The graph spike demonstrates the intended split:

```text
Agent owns composition.
Host owns data, authority, lowering, and disclosure.
```

The real-design classification adds a stronger result:

```text
accepted Cabinet semantics do not imply that
Service + Repository + Router + product-specific Client
must remain durable product architecture.
```

The first real manifest intentionally binds authentication/authorization, actor
identity, decision identity/timestamps, and storage references inside the host.
An agent cannot manufacture authority by including an `AuthorizationDecision`,
filesystem path, or store reference in its request.

The archive/source-custody slice does not yet include cross-node transfer ingest.
That boundary is deliberately deferred because the classical transfer signature
contains transport-era replica evidence. Do not copy that VPS integration shape
into the box before the cross-box authority/effect protocol is classified.

## Classification result to preserve

The accepted real design currently classifies approximately as follows:

- `domain_models` -> durable data/schema;
- `access_control` -> Cabinet policy plus generic host auth/grant/audit kernel;
- `durable_archive` -> Cabinet-native data/policy/capabilities plus generic
  transaction/record/blob-vault lowering;
- `registry_context` -> Cabinet-owned observations/assignment validation, but
  Registry fetch/poll/client moves to transient agent composition;
- `plan_actual` -> immutable observations/decisions + deterministic calculation;
  semantic match proposal is the clearest bounded model-operation candidate;
- `holded_publication` -> Cabinet-owned eligibility/idempotency/evidence/settlement
  state, while the actual external Holded call belongs in agent composition;
- `holded_gateway` -> external connector/authority or transport infrastructure,
  not Cabinet semantic core;
- `synchronization` -> split local evidence/policy from remote delivery and
  cross-node orchestration;
- `retention_release` -> data-owning box decides its own destructive effect;
  cross-node coordination belongs to the agent;
- service/repository/Postgres/FastAPI/bootstrap/client classes -> classical
  storage/transport/deployment lowering unless a semantic requirement proves
  otherwise.

`calculate_plan_actual` is already deterministic under the accepted rules. Do
not introduce an LLM there. If a model is used for plan/actual, constrain it to a
typed, non-authoritative proposal operation whose result requires an explicit
recorded match decision before it can affect confirmed calculation.

## Next work when resuming

Do not return to the completed inventory/classification pass and do not expand
the toy graph DSL for its own sake.

The next useful work is to make the **real** box path executable and to exercise
a cross-box semantic case:

1. validate/compile `cabinet_backend_box_v0.yaml` into a small generic host IR or
   runtime surface without reintroducing `DurableArchiveService`, repository
   classes, or router ownership as normative architecture;
2. prove one archive/source capability against a generic record/blob-vault
   lowering while keeping storage references and authority host-owned;
3. extract a `plan_actual` box slice from accepted decisions:
   - accept a Cabinet-owned typed estimate observation rather than embedding a
     PresuPro client/DTO dependency;
   - keep semantic match proposal typed, bounded, and non-authoritative;
   - record explicit match decisions as Cabinet truth;
   - lower confirmed plan/actual calculation deterministically;
4. define the smallest cross-box prepare/execute/observe/settle protocol needed
   for external effects, using Holded publication as the adversarial case;
5. classify local/VPS topology so transport evidence is not confused with
   durable acceptance authority;
6. compare generated/required implementation surface against the classical
   `agent/cabinet-backend-state-0` path and record which application artifacts
   actually disappear;
7. use real Invoice/Card behavior from `Cabinet_web` as an additional contract
   validation without rewriting or migrating `Cabinet_web`.

The current branch CI does not automatically run for
`agent/cabinet-vault-experiment`; the existing Stage 8.1 workflow is scoped to
the classical branch/PR flow. Therefore do not claim the new manifest tests are
green unless they have actually been executed in a suitable environment.

## Success condition

The experiment succeeds if a useful local Cabinet can be deployed as:

```text
generic host + compiled Cabinet box + local data/storage
```

while agents can combine it with Registry, PresuPro, Client Portal, generators,
and future design tools without any of those products containing permanent
knowledge of one another.
