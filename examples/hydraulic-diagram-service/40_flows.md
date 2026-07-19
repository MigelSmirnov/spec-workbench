# State 4 — Key system flows

## Goal

This state verifies that the module boundaries from State 3 can support real end-to-end behavior without moving business logic into HTTP, MCP, persistence, or generic orchestration code.

Each flow identifies:

- trigger and actor;
- transport boundary;
- application use case;
- participating domain modules;
- input and output models;
- persistence boundary;
- validation and failure ownership;
- observable result.

---

# 1. Create diagram

## Trigger

A visual editor, diagram-authoring agent, or trusted platform service creates a new hydraulic diagram for an external `object_id`.

## Input

```text
object_id
name
system_kinds (non-empty set)
actor
```

## Flow

```text
HTTP or MCP
→ application.create_diagram
→ optional object_gateway existence check
→ diagram.create_diagram
→ diagram status validation
→ DiagramRepository.save
→ return Diagram
```

## Module ownership

- `http_api` / `mcp_api`: parse and serialize only.
- `application`: orchestrates the use case.
- `object_gateway`: confirms the Registry project exists and is not archived when `object_verification_enabled` is true.
- `diagram`: creates the domain aggregate with `current_revision = 0`.
- `repositories`: persists the new diagram.

## Observable result

A stable diagram ID linked to the external object.

## Failures

- empty or invalid `system_kinds` → domain validation error;
- object not found → integration/application error when object verification is enabled;
- duplicate client idempotency key → return existing result or conflict according to later API policy;
- persistence failure → no partial diagram record.

## Placeholder resistance

The use case must not accept `diagram_data: dict` or create an empty generic record with unspecified semantics.

---

# 2. Load current diagram for editing

## Trigger

The visual editor or diagram-authoring agent opens a diagram.

## Flow

```text
HTTP or MCP
→ application.get_diagram_workspace
→ DiagramRepository.get
→ RevisionRepository.get_current
→ catalog.resolve_catalog_snapshot
→ return DiagramWorkspace
```

## Output concept

`DiagramWorkspace` is a transport-neutral application DTO containing:

```text
diagram
current_revision | None
referenced definitions
available catalog entries
```

The exact model is deferred to State 5.

## Ownership

- `application` assembles the workspace.
- `revision` loads the committed snapshot.
- `catalog` resolves exact referenced versions and currently available entries.
- frontend adapters translate the domain workspace into React Flow state outside the backend core.

## Failures

- diagram not found;
- revision pointer broken → integrity failure;
- referenced historical definition missing → catalog integrity failure.

## Invariant check

The backend returns domain data, not React Flow nodes and edges.

---

# 3. Apply authoring command to working state

## Trigger

Editor or diagram-authoring agent adds, updates, or removes an element or connection.

## Input concept

A typed authoring command such as:

```text
AddElement
SetElementProperty
RemoveElement
AddConnection
SetConnectionProperty
RemoveConnection
UpdateLayout
```

## Flow

```text
HTTP or MCP
→ application.apply_diagram_command
→ load base revision or working draft
→ catalog.resolve required definitions
→ diagram.apply command
→ diagram_policy validate affected entities
→ layout validate layout change when applicable
→ return updated working state and findings
```

## Ownership

- `diagram` owns mutation semantics.
- `diagram_policy` owns structural and compatibility validation.
- `catalog` supplies pinned definitions.
- `layout` owns layout normalization and validation.
- `application` loads dependencies and coordinates results.

## Persistence decision

Whether working drafts are persisted is still unresolved.

Two valid implementations remain:

```text
client-held draft + commit complete snapshot
```

or

```text
server-held working draft
```

The public authoring model must not depend on this storage choice.

## Failures

- unknown element definition;
- definition outside allowed scope;
- invalid property type;
- incompatible ports;
- already-connected single-use port;
- stale base revision;
- entity not found.

## Observable result

Updated working diagram state plus stable validation issues.

## Placeholder resistance

Do not use one generic `apply_patch(dict)` operation as the primary domain interface. Commands must have typed intent.

---

# 4. Commit new diagram revision

## Trigger

Editor or diagram-authoring agent submits a coherent working state.

## Input

```text
diagram_id
expected_current_revision
engineering snapshot
layout
actor
change_source
change_summary | None
```

## Flow

```text
HTTP or MCP
→ application.commit_diagram_revision
→ DiagramRepository.get
→ catalog.resolve exact definitions
→ diagram_policy.validate_revision_readiness
→ layout.validate_layout
→ revision.commit_revision
    → begin UnitOfWork
    → verify expected current revision
    → allocate next revision number
    → persist immutable snapshot
    → update Diagram.current_revision
    → commit transaction
→ return DiagramRevision
→ after transaction: refresh Registry index (non-blocking)
```

## Post-commit Registry publication

```text
commit transaction succeeded
→ registry gateway: publish/update hydraulic_diagram index artifact
  (payload: project's diagrams with current committed revisions)
→ on Registry failure: log and continue — the commit result is unaffected,
  the index catches up on the next successful publication
```

The publication runs strictly outside the UnitOfWork (the commit-stage
forbidden-action note already prohibits external calls inside the
transaction) and is discovery-only: consumers fetch actual data from this
service.

## Ownership

- `diagram_policy`: semantic readiness.
- `layout`: layout integrity.
- `revision`: concurrency, numbering, immutability, atomic commit.
- `repositories` / `UnitOfWork`: physical transaction.
- `application`: orchestration only, including post-commit index refresh.
- `registry gateway`: outbound artifact publication (same contained boundary
  as project verification).

## Failures

- validation findings block commit;
- missing authoring-required property;
- stale expected revision → revision conflict;
- missing referenced definition version;
- persistence transaction failure.

## Observable result

A new immutable revision and updated current revision pointer.

## Invariant check

No transport handler may assign revision numbers or update current revision directly.

---

# 5. Create agent-defined element draft

## Trigger

A diagram-authoring agent cannot find an appropriate existing element definition.

## Input

Two explicit parts of one definition record:

```text
engineering part (validated, drives connection and estimation semantics):
  name
  code
  category
  scope
  scope_ref
  ports (code, label, kind, medium, flow semantics, allowed connection types)
  property definitions (including required_for_estimation)
  estimation refs
  actor

presentation part (stored, sanitized, never interpreted):
  svg_markup
  default size
  port visual anchors
```

The drawing agent's SVG skill produces the presentation part; the engineering
part cannot be inferred from the drawing and must be supplied explicitly.

## Flow

```text
MCP or authorized HTTP
→ application.create_element_definition_draft
→ catalog.validate draft structure
→ catalog.validate requested scope
→ catalog validate visual asset inertness and configured byte limit
→ catalog.create draft version
→ CatalogRepository.save
→ return ElementDefinition(status=draft)
```

## Optional activation flow

```text
user or trusted service approval
→ application.transition_definition_status
→ catalog.validate transition and authority
→ catalog.activate definition
→ CatalogRepository.save
```

## Catalog bootstrap (seed) flow

The base global catalog enters through the same mechanism, not through code:

```text
catalog-admin import (HTTP or operational tool)
→ application.create definition draft (per definition, full validation)
→ catalog visual-asset validation (same helper as agent draft creation)
→ application.transition_definition_status (global activation,
  catalog-admin authority)
→ CatalogRepository.save
→ observable result: active global definitions with system provenance
```

No separate unvalidated bulk-load path exists; a seed definition that fails
validation is rejected exactly like an agent draft.

## Ownership

- `catalog`: all definition validation and lifecycle.
- `application`: capability and actor orchestration.
- `mcp_api`: agent-friendly schema only.

## Failures

- duplicate incompatible code;
- missing ports or invalid property definition;
- unsupported scope;
- missing `scope_ref`;
- unauthorized global activation;
- attempt to modify an active version in place.

## Observable result

A versioned scoped draft, not an arbitrary blob.

## Placeholder resistance

The agent must not submit executable code, raw arbitrary metadata, or a free-form SVG as the only definition. A submission with a presentation part but an empty engineering part (no ports, no properties, no estimation refs) is rejected, not silently accepted as a picture.

---

# 6. Build estimation-data package through HTTP

## Trigger

Estimator Service requests deterministic inputs for one diagram revision.

## Input

```text
diagram_id
revision | current
```

## Flow

```text
HTTP
→ application.build_diagram_estimation_data
→ revision.get_revision
→ catalog.resolve exact referenced versions
→ diagram_policy.validate_diagram_structure
→ estimation_data.build_estimation_data
→ return EstimationDataPackage
```

## Ownership

- `http_api`: route and serialization.
- `application`: loading and orchestration.
- `revision`: revision retrieval.
- `catalog`: exact definition resolution.
- `diagram_policy`: integrity validation.
- `estimation_data`: grouping, measurements, missing requirements, warnings, provenance.

## Output states

```text
complete
incomplete
invalid
```

## Failures and results

- diagram or revision not found → transport-neutral not-found result;
- missing historical definition → `invalid` or integrity failure;
- missing estimator-required properties → `incomplete`, not HTTP failure;
- broken connection references → `invalid`;
- internal persistence failure → service error.

## Observable result

Estimator Service receives one stable package contract with no prices or final estimate positions.

## Determinism check

HTTP adds no business fields or alternative grouping behavior.

---

# 7. Build and inspect estimation data through MCP

## Trigger

Estimator agent investigates a diagram before composing an estimate.

## Flow

```text
MCP tool: list_object_diagrams
→ application.list_object_diagrams

MCP tool: build_estimation_data
→ application.build_diagram_estimation_data
→ same flow as HTTP

MCP tool: inspect_estimation_source
→ application.get_revision_source_entity
→ revision.get_revision
→ catalog.get exact definition
→ return source entity details
```

## Ownership

- `mcp_api`: tool descriptions, input schemas, output serialization.
- all business behavior remains in `application` and domain modules.

## Agent interaction pattern

```text
get package
→ if complete: use package in estimator workflow
→ if incomplete: inspect missing requirements
→ inspect source entities
→ create DiagramChangeRequest or use authorized authoring tools
→ request package again
```

## Invariant check

MCP and HTTP package content must be semantically identical for the same input revision.

## Placeholder resistance

Do not add an MCP-only “smart package builder” that guesses missing values.

---

# 8. Create diagram change request from estimator agent

## Trigger

Estimator agent detects missing or inconsistent diagram data but lacks authoring capability.

## Flow

```text
MCP
→ application.create_diagram_change_request
→ validate diagram and base revision exist
→ change_requests.create_change_request
→ ChangeRequestRepository.save
→ return open request
```

## Later application flow

```text
authorized editor/agent reviews request
→ accept or reject
→ if accepted, translate into typed authoring commands
→ normal diagram authoring and commit flow
→ mark request applied with resulting revision
```

## Ownership

- `change_requests`: lifecycle and audit link.
- `diagram`: actual mutation.
- `revision`: resulting commit.
- `application`: coordination.

## Failures

- stale base revision;
- malformed requested change;
- unsupported operation;
- requester lacks read/request capability.

## Observable result

A traceable request, not a silent mutation.

---

# 9. List diagrams for an object

## Trigger

Estimator Service, estimator agent, or editor needs diagrams associated with an external object.

## Flow

```text
HTTP or MCP
→ application.list_object_diagrams
→ DiagramRepository.list_by_object_id
→ return paginated DiagramSummary list
```

## Ownership

- repository performs filtered retrieval;
- application applies capability and pagination policy;
- transport serializes.

## Output concept

`DiagramSummary` should contain only discovery data, for example:

```text
diagram_id
object_id
name
system_kinds
status
current_revision
updated_at
```

## Placeholder resistance

Do not return full revision snapshots in list operations.

---

# 10. Archive diagram

## Trigger

Authorized user or service retires a diagram.

## Flow

```text
HTTP or MCP authoring capability
→ application.change_diagram_status
→ DiagramRepository.get
→ diagram_policy.validate status transition
→ diagram.change_status
→ DiagramRepository.save
→ return Diagram
```

## Invariants

- archived diagrams remain readable;
- no new revisions are committed after archival in v1;
- historical estimation packages remain reproducible.

## Failures

- invalid transition;
- stale update version if diagram metadata uses optimistic concurrency;
- unauthorized action.

---

# 11. Error ownership map

## Domain validation issues

Owned by:

```text
catalog
diagram_policy
layout
```

Returned as stable issue codes plus entity references.

## Revision conflict

Owned by `revision` and translated by transport to conflict semantics.

## Not found

Detected by repository/application loading and translated by transport.

## Authorization

Enforced at application capability boundary using an external identity/authorization port.

Exact identity model remains unresolved.

## Integration failure

Owned by `object_gateway` adapter and mapped into an application integration error.

## Persistence failure

Owned by repository infrastructure; domain modules do not catch or reinterpret storage exceptions directly.

## Incomplete estimation data

Owned by `estimation_data` and returned as a normal `EstimationDataPackage(status=incomplete)`.

It is not a transport exception.

---

# 12. Data transition map

```text
CreateDiagramInput
→ Diagram

AuthoringCommand + base DiagramRevision + CatalogSnapshot
→ WorkingDiagramResult

WorkingDiagram + DiagramLayout + expected revision
→ DiagramRevision

DiagramRevision + exact CatalogSnapshot
→ EstimationDataPackage

MissingEstimationRequirement
→ DiagramChangeRequest
→ typed AuthoringCommand(s)
→ new DiagramRevision
```

This chain avoids untyped generic payloads between major stages.

---

# 13. Flow findings affecting earlier states

## New application DTOs needed

State 5 should define:

```text
DiagramWorkspace
DiagramSummary
WorkingDiagramResult
ValidationIssue
CatalogSnapshot
CommitRevisionResult
```

These are application/boundary models, not durable entities.

## Typed commands needed

State 5 should define a closed set of authoring command models rather than `dict` patches.

## Authorization port needed

State 3 should eventually include an identity/capability port. Exact user and tenant semantics remain deferred, but application use cases need a transport-neutral capability decision.

## Working draft storage remains open

Flows work with either client-held or server-held drafts. Contracts should preserve this flexibility without using generic patches.

---

# 14. Placeholder resistance review

Rejected flow placeholders:

- “save diagram” without expected revision and atomic commit;
- “agent adds element” without catalog scope and typed definition;
- “get data for estimator” without explicit revision and package status;
- “MCP handles estimation” with separate business logic;
- “fix missing data” through silent estimator-agent mutation;
- “validate before save” without naming owners and issue outputs;
- “load editor state” by returning raw React Flow JSON.

---

## State 4 readiness assessment

State 4 is sufficiently stable to begin public API design because:

- major flows terminate in concrete results;
- every business decision has a domain owner;
- HTTP and MCP share application behavior;
- errors and incomplete-data outcomes are distinguished;
- revision conflict and atomicity are explicit;
- agent-created definitions follow catalog governance;
- estimator-agent corrections preserve the read/write boundary;
- new DTO and command needs are identified without inventing function signatures yet.
