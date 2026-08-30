# Read-only obligation graph

`tools/obligations.py` projects the current engineering frontier from existing
Spec Workbench evidence. It is an index and scheduler view, not a design state,
gate, or accepted artifact. Every invocation rebuilds the graph in memory and
writes nothing.

```text
State 0–7 artifacts + trace + existing reports + deterministic closures
                               +
                    Factory merged dependency graph
                               ↓
                     evidence nodes and edges
                               ↓
                    engineering obligations
                               ↓
              frontier / module focus / metrics
```

## Module boundary

The public transport-neutral API is:

```python
from obligation_workbench import SemanticClaim, build_graph, focus, frontier, list_obligations, metrics
```

- `build_graph(...)` invokes existing stage/report Python APIs and constructs a
  fresh in-memory `Projection`.
- `list_obligations(...)`, `frontier(...)`, `focus(...)`, and `metrics(...)`
  are pure views over that projection.
- `tools/obligations.py` is only argument parsing and text/JSON rendering.

Internal dependencies point inward:

```text
CLI → service → evidence/report/factory adapters → model
              → derivation + precedence scheduler → model
views → model
```

The package has no persistence adapter. Adding one would violate its contract.

## Evidence model

Supported node kinds are `actor`, `outcome`, `boundary`, `decision`, `model`,
`interface`, `module`, `capability`, `flow`, `public_op`, `function`, and
`contract`. Interfaces remain SPEC models physically, but are projected as a
separate semantic kind.

Edges carry exact evidence references. Existing stage parsers and coverage APIs
are reused for States 2–6. The small State 0 adapter reads actor/outcome items
and explicit boundary headings, including direct children of a boundary section;
a heading alone does not imply an ingress requirement. An outcome is connected
to a flow only by an exact `outcome:*`
reference in reviewed State 4 evidence. When the current artifacts cannot state
that mapping, the projection emits `outcome_flow_mapping_unresolved`; it never
uses title similarity.

`global_spec.json` may supply projection-only nodes and explicit
`imports.module_internal` parity edges. It never becomes authoring provenance:
a projected model/interface without an indexed State 1 model item produces
`model_without_design_source`.

## Obligation and precedence

Every obligation has a deterministic `id`, `kind`, one or more
`addressed_to` nodes, mandatory `caused_by`, evidence refs,
`precedence_class`, `resolution_owner`, optional evidence-backed
`semantic_owner`, `implementation_mode`, `status`, and `blocked_by`. One cause
may address many nodes; the view does not multiply it into independent defects.

`resolution_owner` says which authoring/runtime surface must perform the repair.
`semantic_owner` says which architecture owner is allowed to decide the
semantics. They are deliberately independent: a downstream artifact may own the
repair while the decision remains owned by an upstream boundary.

Only `defining` obligations propagate blocking through edges marked
definitional. `convergence` obligations such as reachability and undesigned
dependencies remain actionable and never freeze the subject they are meant to
repair. Node state therefore has two independent axes:

```text
locally_complete   — no open obligation is addressed to this node
globally_settled   — no local/incoming work remains and no defining prerequisite
                     can still change its subject
```

A complete contract may consequently remain system-blocked by a missing model
or interface source without being reopened locally.

Module focus aggregates the module and its owned capability/public/function/
contract nodes. Incoming requirements therefore keep a locally complete module
from appearing settled, while only defining prerequisites place it in BLOCKED.

## Semantic ownership

The projection compares ownership only when evidence supplies the same explicit
`semantic_key`; it never joins prose through embeddings, keyword similarity, or
NOTE_CLASS equality. A canonical claim and a downstream claim for the same key
under different owners produce one `duplicate_semantic_ownership` obligation
with `ownership_status: wrong_owner`.

Multiple canonical owners are a conflict unless every claim names the same
explicit `shared_owner_group`. Shared ownership is therefore evidence, not an
inference from cooperation or a common flow.

`wrong_owner` means that the downstream expression has been given freedom to
re-decide semantics owned elsewhere. Its repair is to return the decision to
the canonical owner. It does not by itself prescribe deleting a note or any
other particular textual edit.

The optional in-memory `semantic_claims` argument to `build_graph(...)` lets an
existing structured report transport such claims without adding a persisted
Workbench registry. Claims are diagnostic evidence and are rebuilt on every
run, like the rest of the projection.

Module focus has five work sections: `OWNED`, `INCOMING`, `OUTGOING`,
`NOT_OWNED`, and `BLOCKERS`. `NOT_OWNED` contains obligations addressed to a
local expression whose semantic owner is external, plus external semantic
claims that the module may rely on but must not redefine.

## Implementation mode

Structured closure evidence may project `implementation_mode` as
`deterministic`, `irregular`, or `llm`. HTTP router `emission: table` maps to
`deterministic`; `emission: irregular` maps to `irregular` and preserves the
declared free-form `irregular_reason` as evidence. Irregular mode is an accepted
architecture decision, not an obligation or readiness failure.

The same model can represent persistence closure selecting the ordinary LLM
path for an entire repository/module because one method is irregular. No such
claim is inferred until the persistence report exposes that selection as
structured evidence; `irregular_reason` remains free text, not a closed enum.

The Cabinet Web upload route is consequently projected as an irregular
transport decision owned by `boundary:web_gateway`. Its reason includes
multipart streaming, handoff-secret and CSRF handling, and bounded content
identification. Structured State 5 flow/caller evidence makes that decision an
external assumption of `module:source_custody`, so it appears under
`NOT_OWNED`. The current note text has no explicit semantic key, however, so the
projection does not claim that its content-identification prose is identical to
the router decision and does not emit a real-case ownership conflict from text
alone.

`structured_lowering_candidate` is reserved as a non-blocking diagnostic for a
future report that can prove a structured-data-to-deterministic-transformation
shape. The obligation layer does not infer it from `irregular_reason`, and this
change adds no emitter or persisted lowering registry.

## Recovery regression vocabulary

The registry reserves the following obligation kinds so future structured gates
can report them without changing the transport model:

- `cross_call_identity_undefined` — a value crosses calls without an accepted
  identity/propagation rule;
- `derived_identifier_semantics_undefined` — an identifier is generated but its
  source and stable meaning are not designed;
- `downstream_semantic_conflict` — a downstream expression contradicts an
  authoritative accepted decision such as `decision:A06`;
- `runtime_config_binding_missing` — composition or deployment omits a required
  runtime binding or alias;
- `protocol_assumption_not_backed_by_contract` — generated code assumes `with`,
  `async with`, `await`, or iteration semantics absent from the interface and
  contracts;
- `production_entrypoint_not_exercised` — verification bypasses the production
  composition/entrypoint topology.

These are modelled classes, not new detectors. Until an existing report emits
structured evidence, the projection does not manufacture them from generated
code or prose.

## Factory parity

Parity uses Factory's existing `merged_dependency_graph` implementation. It
reports Workbench explicit edges, Factory merged edges, compiler-derived
`X → models` edges filtered as `model_context`, and the remaining
`dependency_not_designed` relations. The latter requests an architectural
explanation; it never prescribes adding an import.

`codec_registry_unavailable` is a tool-level obligation with no fabricated
design-node address.

## CLI

```bash
python tools/obligations.py examples/<case> --list [--json]
python tools/obligations.py examples/<case> --next [--json]
python tools/obligations.py examples/<case> --focus module:<name> [--json]
python tools/obligations.py examples/<case> --metrics [--json]
```

Use `--factory-root` or `SPEC_WORKBENCH_FACTORY_ROOT` when the Factory checkout
is not discoverable beside the case checkout. `90_factory_target.json` supplies
the exact Factory project unless `--factory-project` is passed.
