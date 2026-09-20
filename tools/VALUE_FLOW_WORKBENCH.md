# Value-flow closure

`python tools/design_value_flow.py examples/<case> --coverage [--json]`

Three questions every contract answers before anything is generated. They are
asked over State 6 contracts and models, State 7 notes, State 3 `Knows` and
State 5 impacts — no assembled `global_spec.json` is needed, so the check works
on a case that was never assembled, which is when an unclosed value is cheap.

| lens | question | finding |
|---|---|---|
| outputs | every required field of the canonical instant type in a returned record has a source | `instant_without_source` |
| inputs | every scalar argument of a constructing function has a sink | `argument_without_sink` |
| collaborators | every module State 3 says a module *knows* is reachable from that module's notes | `known_collaborator_unreachable` |

Nothing here is bound to a form of the project. The instant type is
`rules.time_source_policy.representation.type` from `60_data_closure.json`; the
accessor that hands it out is the wiring of `70_system_clock_closure.json`. A
case that declares no policy gets `outputs.enabled: false` with the reason — the
lens says it did not judge rather than reporting nothing found.

## What is resolved without an author

- **outputs** — a parameter of the instant type, or one single record parameter
  with the same-named instant field (a draft, the record being replaced; a
  *collection* of prior records does not carry the new instant); an operation
  State 5 makes read-only (`stored`); a note of the function that names the
  accessor (`clock`).
- **inputs** — a function is *constructing* when it stamps a clock-sourced
  instant, or is a public mutating operation whose instant is still open. Its
  record-typed arguments are judged through their own models; a scalar argument
  named like a field of the constructed model lands in that field.
- **collaborators** — an edge is a module named in backticks under State 3 `Knows`, or one a
  facade lists under `delegates to`. It is reachable when a note of the module names the
  collaborator or any of its contracted operations. Reachability is the module's, not the function's:
  imports are derived per module.

## The residue: `70_value_flow_closure.json`

```json
{
  "schema_version": "spec_workbench_value_flow_closure.v1",
  "status": "closed",
  "outputs": {"cancel_run": {"FlowRun.created_at": {"source": "stored"}}},
  "inputs": {
    "create_slot": {"name": {"sink": "derived", "to": "Slot.slot_id"}},
    "retire_slot": {"expected_status": {"sink": "guard"},
                    "reason": {"sink": "forwarded", "to": "record_node_execution"}}
  }
}
```

`source`: `clock` (the note must name the accessor), `argument` (`via` a
parameter that carries the instant), `stored`, `callee` (`via` a contract that
returns such a record and that a note of the module names).
`sink`: `field` (`to` a field of the constructed model), `derived` and `key`
(`to` any declared `Model.field`), `guard`, `forwarded` (`to` a contract a note
of the module names).

A declaration is checked against the design, never trusted: declaring
`{"sink": "field", "to": "Slot.name"}` while `Slot` has no `name` is
`declared_sink_unknown` — the decision to add the field is made in State 1, not
hidden in the closure. A declaration nothing asks for is
`value_flow_declaration_stale`. There are no waivers.

## Denominators

The report carries, per lens, how much it judged: `pairs`, `by_source`,
`constructing_functions`, `edges`. A lens that judged nothing over a non-empty design has not
passed, it has not run: no declared instant type, or no collaborator named for any module, is
`value_flow_lens_judged_nothing` and stops the case.

## Not covered

- An *optional* instant a function sets (`ended_at`, `revoked_at`).
- A property the note lists in prose for a model that does not have it
  (`carriage` on a draft whose carriage is implicit). That needs note structure
  the workbench does not have yet; the Factory's `model_attribute_unknown`
  catches it at the first draft of the module.
- The phase is not wired into `design_authoring_next.py` yet: run it by hand
  after State 7 and before assembly.
