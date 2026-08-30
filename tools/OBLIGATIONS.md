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
from obligation_workbench import build_graph, focus, frontier, list_obligations, metrics
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
`precedence_class`, `resolution_owner`, `status`, and `blocked_by`. One cause
may address many nodes; the view does not multiply it into independent defects.

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
