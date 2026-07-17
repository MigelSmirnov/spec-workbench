# Hydraulic Diagram Service — historical compatibility rewrite proposal

> **Status: superseded as the default direction.** This document records the
> architecture rewrite considered while the Factory lacked named
> discriminated unions and Protocol-based ports. The Factory is now being
> extended to materialize the original architecture. Do not apply this rewrite
> merely to satisfy the legacy compiler profile. Reconsider individual ideas
> only as independent product architecture decisions.
>
> Panelforge is the positive baseline for the established deep-module,
> deterministic-model, assembler/linker, and verification pipeline. It does
> not exercise named unions or repository/UoW Protocol ports and therefore does
> not justify removing them from this case.
>
> Every recommendation and migration step below belongs to that discarded
> compatibility option. None of its “remove”, “replace”, or “rewrite” wording is
> a current Workbench requirement.

Status: proposal only. This document does not modify the accepted design-state
documents or `global_spec.json`.

Date: 2026-07-16

## Why this proposal exists

The current assembled specification is not handoff-ready:

- Factory validation returns `WARNINGS_ONLY` instead of `PASS`;
- `AuthoringCommand` and `TypedValue` use the unsupported invented model form
  `kind: discriminated_union`;
- deterministic model generation emits empty name-only classes for those two
  entries;
- assembler gates reject consumers that import the empty runtime
  `AuthoringCommand` class;
- application contracts expose custom Protocol types that the current Factory
  validator cannot classify as generated runtime models.

The Workbench handoff policy now requires validator exit code `0`, status
`PASS`, zero errors, and zero warnings. The project architecture therefore has
to use representations and dependency boundaries already supported by the
Factory.

## Constraints

The replacement must preserve product semantics:

- immutable diagram revisions and optimistic concurrency;
- typed properties with no arbitrary JSON payloads;
- atomic revision persistence;
- explicit authorization checks;
- Registry verification before creation when enabled;
- post-commit, non-blocking Registry index publication;
- deterministic estimation packages;
- no direct database writes from HTTP or MCP;
- no generated/build/product-code patching.

The replacement must not:

- add fake Pydantic models for Protocol classes;
- add fake third-party imports to silence validation;
- hide warnings with quoted annotations solely to exploit parser blindness;
- weaken the Factory validator;
- replace domain types with `Any` or uncontrolled `dict` payloads;
- introduce a new specification model `kind`.

## Proposed architecture

### 1. Client-held working draft instead of command union

Choose the client-held draft option that State 4 previously left open.

Remove:

- `AuthoringCommand`;
- the seven command-union variants from the public application boundary;
- `apply_authoring_command` and `apply_authoring_commands` dispatch;
- command discriminator logic.

Add one ordinary closed Pydantic model:

```text
WorkingDiagramDraft
  revision_base: int
  elements: list[DiagramElement]
  connections: list[DiagramConnection]
  layout: DiagramLayout
```

Primary operation:

```text
prepare_working_diagram(
  base_revision: DiagramRevision | None,
  draft: WorkingDiagramDraft,
  catalog: CatalogSnapshot,
) -> WorkingDiagramResult
```

The operation verifies the base revision, validates the entire submitted
engineering state and layout, and returns a complete immutable working result.
It is not a generic patch: every nested value is a declared Pydantic model.

Consequences:

- command ordering is no longer a server-domain concern;
- HTTP and MCP may offer ergonomic edit tools, but they must produce a complete
  `WorkingDiagramDraft` and call the same application operation;
- commit remains bound to `revision_base` and
  `expected_current_revision`;
- no named union or discriminator alias has to be materialized by the Factory.

### 2. Ordinary tagged scalar instead of `TypedValue` union

Use one supported ordinary frozen Pydantic model:

```text
TypedValue
  value_type: PropertyValueType
  string_value: str | None
  integer_value: int | None
  decimal_value: Decimal | None
  boolean_value: bool | None
```

Local model validation requires exactly one populated value field and requires
it to match `value_type`. `PropertyValue`, defaults, allowed values, grouping,
and estimation rules continue to use `TypedValue`.

This is more verbose than a discriminated Python union, but it is closed,
explicit, deterministic, and supported by the current Factory model language.

### 3. Explicit authorization data instead of injected authorizer Protocol

Remove `CapabilityAuthorizer` from contracts.

Add an ordinary boundary model:

```text
AuthorizationContext
  actor: ActorRef
  capabilities: set[str]
  resource_ids: set[str]
```

Add application policy:

```text
require_capability(
  authorization: AuthorizationContext,
  capability: str,
  resource_id: str | None,
) -> None
```

Authentication remains a transport/platform responsibility. Application use
cases still enforce authorization; they consume an explicit decision context
rather than an injected service object. Tokens and provider sessions never
enter the model.

### 4. DTO-based Registry boundary instead of injected gateway Protocol

Remove `ObjectGateway` from application contracts.

Use module-level adapter operations:

```text
load_object_snapshot(object_id: str) -> ObjectSnapshot
publish_diagram_index(index: DiagramIndexArtifact) -> bool
```

Creation receives an optional preloaded `ObjectSnapshot` and validates it when
object verification is enabled. Commit builds `DiagramIndexArtifact` after the
database transaction, then invokes publication. Publication failure is logged
and does not change the successful commit result.

Only `ObjectSnapshot` and `DiagramIndexArtifact` cross the integration
boundary. Registry HTTP clients, authentication headers, retries, and response
schemas remain private to the adapter module.

### 5. Functional persistence boundary instead of repository/UoW Protocols

Follow the Factory-proven `registry_sandbox` pattern: concrete persistence
functions accept an existing SQLAlchemy `Session` and explicit Pydantic
models.

Remove from the generated public type surface:

- `DiagramRepository`;
- `RevisionRepository`;
- `CatalogRepository`;
- `UnitOfWork`;
- repository objects passed through domain/application signatures.

Candidate persistence operations:

```text
get_diagram(session: Session, diagram_id: str) -> Diagram | None
save_diagram(session: Session, diagram: Diagram) -> None
list_diagrams_by_object(...) -> DiagramSummaryPage
get_revision(...) -> DiagramRevision | None
get_current_revision(...) -> DiagramRevision | None
list_revisions(...) -> DiagramRevisionSummaryPage
get_element_definition(...) -> ElementDefinition | None
get_connection_definition(...) -> ConnectionTypeDefinition | None
list_visible_definitions(...) -> CatalogSnapshot
save_element_definition(...) -> None
save_connection_definition(...) -> None
persist_revision_commit(
  session: Session,
  result: CommitRevisionResult,
  expected_current_revision: int,
) -> None
```

`persist_revision_commit` owns one short transaction that atomically checks the
current revision, appends the immutable snapshot, and advances the diagram
pointer. It performs no network I/O. Pure domain code prepares the
`CommitRevisionResult` before the transaction begins.

This deliberately couples the application infrastructure boundary to
SQLAlchemy while keeping domain models and domain policy independent from it.
It removes an unsupported runtime type layer without moving SQL into domain
modules.

### 6. Pure revision preparation plus atomic persistence

Replace the current `commit_revision(... repositories, unit_of_work)` domain
operation with:

```text
prepare_revision_commit(
  diagram: Diagram,
  expected_current_revision: int,
  working: WorkingDiagramResult,
  actor: ActorRef,
  change_source: ChangeSource,
  created_at: datetime,
  schema_version: int,
  change_summary: str | None,
) -> CommitRevisionResult
```

The function validates the expected revision and constructs the new immutable
revision plus advanced diagram without persistence. The application then calls
`persist_revision_commit` with the same expected revision. The database update
must repeat the concurrency check atomically; the pure check improves failure
clarity but does not replace the database guard.

### 7. Storage serializer boundary

Serializer inputs and outputs remain explicit at the model boundary. If the
Factory validator rejects `dict[str, object]`, use the existing accepted JSONB
boundary form `dict` only for serializer contracts, with notes requiring
canonical `model_dump(mode="json")` output and immediate `model_validate` on
load. Generic dictionaries remain forbidden everywhere else.

### 8. Standard-library scalar representation

The final rewrite must select a representation for `datetime` and `Decimal`
that the current Factory standard, deterministic model generator, validator,
and static gates all accept together. This proposal does not approve parser
evasion. Before assembly, prove the exact form with a minimal model and
consumer compile probe; if no supported form exists, redesign the wire values
as explicit timestamp/decimal-string value objects rather than accepting a
warning.

## Module changes

Remove:

```text
application_ports
```

Replace repository-class modules with focused persistence function units:

```text
database
persistence_diagrams
persistence_revisions
persistence_catalog
persistence_serializers
```

Add or rename:

```text
authorization_policy
registry_integration
working_diagram
```

Keep domain ownership modules:

```text
models
errors
catalog
diagram_policy
layout
revision
estimation_*
application_*
```

## Flow changes

### Create diagram

```text
transport loads ObjectSnapshot when verification is enabled
→ application checks AuthorizationContext
→ application validates ObjectSnapshot
→ domain creates Diagram
→ persistence saves Diagram using Session
```

### Prepare working diagram

```text
transport receives closed WorkingDiagramDraft
→ application loads explicit base revision and catalog
→ domain prepares complete working result
→ policy validates structure, properties, connections and layout
→ return WorkingDiagramResult
```

### Commit revision

```text
application authorization check
→ resolve exact definitions and commit-stage validation
→ pure prepare_revision_commit
→ atomic persist_revision_commit(Session, result, expected revision)
→ transaction closes
→ build and publish DiagramIndexArtifact best-effort
→ return successful CommitRevisionResult
```

## Required propagation if accepted

Update in this order:

1. `00_product.md` — Registry data boundary.
2. `10_models.md` — `TypedValue`, `WorkingDiagramDraft`,
   `AuthorizationContext`.
3. `20_rules.md` — authorization input and complete-draft validation policy.
4. `30_modules.md` — functional persistence and Registry modules.
5. `40_flows.md` — client-held draft and pure/atomic commit split.
6. `50_public_apis.md` — remove command union and Protocol ports.
7. `55_generation_units.md` — new persistence/working-state units.
8. `56_pydantic_modeling.md` and `57_pydantic_schemas.md` — supported ordinary
   model shapes only.
9. `58_postgresql_persistence.md` — Session-based functional operations.
10. `60_contracts.md` — exact signatures.
11. `70_notes.md` — behavioral constraints for replacement operations.
12. `global_spec.json` last.

## Acceptance gates

The proposal is complete only when all of these pass:

1. Workbench semantic lint has no unclassified blocking finding.
2. Factory canonical validator exits `0`, reports `PASS`, zero errors, zero
   warnings.
3. Spec Inspector reports `PASS`, `BLOCK=0`, `WARN=0`.
4. Deterministic models contain real fields for `TypedValue`,
   `WorkingDiagramDraft`, and `AuthorizationContext`; no name-only empty class.
5. Representative consumers compile for working-draft validation,
   authorization, persistence, and revision commit.
6. Full no-deploy assembler and linker pass.
7. Only after accepted source export and compile evidence may Route B begin.

## Open review decisions

- Whether HTTP/MCP authoring should expose only complete-draft submission or
  also transport-only convenience edit tools.
- Whether SQLAlchemy `Session` may appear directly in application use-case
  contracts or should remain inside persistence orchestration functions.
- Whether Registry loading is performed by transport wiring or by an
  application orchestration function that imports the adapter directly.
- The supported warning-free Factory representation for UTC timestamps and
  exact decimal quantities.
