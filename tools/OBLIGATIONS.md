# Obligations — the engineering frontier, read-only

`tools/obligations` projects **what the already-decided artifacts oblige the
corpus to decide next**. It stores nothing: every run rebuilds a graph from
the authoring artifacts, the fenced deterministic reports
(`assembly_workbench.checks.CHECKS`) and the factory's dependency report, and
prints the frontier. It is not design truth, it has no `status: accepted`, it
writes no file.

    python tools/obligations examples/<case> next              the frontier
    python tools/obligations examples/<case> list              every obligation
    python tools/obligations examples/<case> focus module:<m>  one deep module, both directions
    python tools/obligations examples/<case> metrics           counts, addressability, registry gaps, factory parity
    … --json                                                   machine form
    … --factory-root <path> --factory-project <name>           parity inputs (default: sibling code_factory, best module overlap ≥ 0.8)

`authoring.py next` keeps its ladder. The two run side by side: the ladder
names a State, the frontier names obligations.

## Nodes and evidence edges

Nodes: `decision`, `model`, `interface`, `boundary`, `actor`, `outcome`,
`module`, `capability`, `flow`, `public_op`, `function`, `contract`. An
interface is technically `models.<X>: {kind: interface}`; in the graph it is
its own kind because its obligations differ (it needs a provider).

Edges are only facts the artifacts already state:

| edge | read from |
|---|---|
| decision → owner module | `30_trace.json` (`primary_owner`) |
| module → capability | `30_modules.md` capability names |
| flow → module, flow → capability | `40_flow_plan.json`, `40_flows.md` |
| public_op → capability, → flow, → caller | `50_api_plan.json` (callers may be `boundary:*`) |
| function → module, → public_op; contract → function | `60_contract_plan.json`, `60_contracts.json` |
| contract → model / interface | type names in the signature |
| module → module | `global_spec.json` `imports.module_internal` |
| actor, outcome | `00_product.md` headings under *Actors* / *Observable outcomes* |
| ingress | `70_router_closure.json` items |

## Obligations are derived, typed, addressed

Every obligation has a **type** from the closed registry
(`tools/obligations/registry.py`), an `addressed_to` node, an `about` node when
it names another node, and a `caused_by`. A deterministic-report finding is
mapped to a type by `FINDING_MAP`, then by the check that raised it; a code
that maps nowhere becomes `unclassified_finding` addressed to
`registry:obligations` — the registry's own obligation, visible in `metrics`.

The registry, first version:

| precedence | types |
|---|---|
| `defining` | `module_cut_undecided`, `decision_without_owner`, `model_without_design_source`, `model_identity_unresolved`, `contract_type_without_model`, `interface_without_provider`, `flow_capability_missing`, `data_placement_undecided` |
| `convergence` | `decision_without_witness`, `capability_unreachable`, `boundary_without_ingress`, `ingress_without_designed_caller`, `outcome_without_flow`, `dependency_not_designed`, `public_op_undecided`, `timestamp_without_time_source`, `contract_undecided`, `external_contract_undecided`, `language_undecided`, `notes_undecided` |
| `implementation` | `router_closure_unproven`, `persistence_closure_unproven` |
| `derived_cost` | `model_closure_radius` |

**The type decides scheduling, not the message.** Only `defining`
obligations block: a node whose definitional edge (`capability→module`,
`public_op→capability`, `public_op→flow`, `function→public_op`,
`contract→function`, `contract→model`) reaches a node with an open defining
obligation is SYSTEM-blocked. `convergence` obligations (unreached,
unwitnessed, undesigned edge) never block anyone; `implementation` never blocks
design; `derived_cost` is information.

`capability_unreachable` is addressed to the **caller** State 5 names (a
module or a boundary), with the capability as `about`: the module that owns
the capability has nothing to write; the caller has.

## Node state — two axes

    LOCAL   complete | open      — are there obligations addressed to me
    SYSTEM  settled  | blocked   — does a defining obligation upstream change my subject

    READY    = local open, system settled     → author it now
    BLOCKED  = system blocked                 → go close the blocker first
    SETTLED  = local complete, system settled

A contract with a finished signature whose parameter type is an interface with
no design source reads `LOCAL COMPLETE · SYSTEM BLOCKED · by interface:X`:
do not rewrite the contract, go close the interface.

`next` prints the frontier — several independent READY nodes, ordered by the
strongest precedence class they carry — not one answer. `focus module:<m>`
prints the module's own obligations, its owned nodes by state, its external
blockers, and the obligations elsewhere that name its nodes: a deep module
that nobody calls looks closed from the inside and is not.

## What it deliberately cannot see

Only named things carry obligations. A missing secret field, an undeclared
runtime variable, an error body without a code have no node until a boundary
obligation derives them from the route (`auth`, `response_mode`) and the
spec's `config`. That is the next evidence edge, not a message to add.
