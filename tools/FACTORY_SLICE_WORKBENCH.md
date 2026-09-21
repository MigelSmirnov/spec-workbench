# Factory Slice Workbench

`factory_slice_workbench` asks the Factory what each module's generator will
actually receive, before the specification is exported.

Every other gate reads the assembled `global_spec.json`. The Factory does not
generate from that document. It normalizes it, cuts one local specification per
module with `tools/build_local_spec.py`, and builds the prompt from the cut. A
defect that exists only in the cut passes the validator, the inspector and
admission, and is met by a started Route B run — one defect per run, because a
run stops at the first module that fails.

Four stops of Cabinet Flow runs were of this kind:

- `models` was told to import `owner_authority.owner_statement`: the operation
  shared its name with a model field, and the slicer derives an import from any
  whole-word match in note or contract text;
- `store_continuity`, `operation_bindings` and `manifest_reader` were told to
  import a function whose name was one of their own contract parameters;
- nine modules carried the value of a `= rules.x` address, and the data/code
  seam (SPEC_STANDARD §15.9) refuses to build a prompt that contains a value;
- twenty-five changed data addresses reached no module and Route B preflight
  blocked with `affected_data_graph_incomplete`: the export had asked the Factory
  about the delta of two specifications, the route asks about the whole scope no
  passing run has carried.

## Public operation

`probe(source, factory_root, case_root=None)` copies the specification into a
temporary directory (the Factory normalizer writes a report beside its input),
runs the Factory's normalizer and slicer for every module, asks
`tools/data_code_seam.py` about every cut, and returns one report with all
findings and the denominators behind them. It writes nothing into the case or
the Factory. Authority stays with the Factory tools: the probe re-implements
none of their rules and only compares what they produce with the names the
specification already declares.

## Findings

All findings block.

- `models_imports_operation` — the cut of `models` imports anything but models;
- `import_shadows_own_parameter` — a module imports a function whose name is a
  parameter of a contract that module owns;
- `data_in_model_context` — the seam refuses the cut, with the addresses it names;
- `factory_slicer_missing`, `factory_normalization_failed`,
  `factory_slice_failed`, `factory_slices_empty`, `factory_seam_failed` — the
  Factory could not be asked;
- `changed_data_without_consumer` — when the Factory project is named: the data
  addresses Route B will resolve (the delta of this handoff **united with the scope
  of every accepted handoff no passing route has carried**, built by the export's
  own `project_change_scope` and `carry_pending_scope`) are given to the Factory's
  own `tools/spec_data_reachability.py`; an address that exists and reaches no
  module is reported, grouped by namespace (SPEC_STANDARD §15.3, §15.3.1). A
  missing address is a deletion the accepting delta classifies and is not reported.
  `factory_change_scope_refused` and `factory_reachability_failed` mean the Factory
  could not be asked.

The probe does not judge data the Factory does not ask about: a namespace nobody
consumes and nobody changed is reported by the Factory when it changes.

## Workflow

```bash
python tools/design_factory_slices.py examples/<case> --factory-root ../code_factory --project <factory_project>
python tools/design_factory_slices.py examples/<case> --factory-root ../code_factory --project <factory_project> --json
```

Stage 9 admission runs the same probe as `FA018`. Run it alone while authoring
notes and contracts: it needs no clean checkout and takes seconds per module.

## What it does not see

A name that is both a callable and a model field is reported only once the
Factory actually induces an import from it. Today's correct import of such a
callable is not a finding; the first note that lists the field in a module that
does not call the function will be.
