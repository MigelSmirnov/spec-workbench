# Factory Slice Workbench

`factory_slice_workbench` asks the Factory what each module's generator will
actually receive, before the specification is exported.

Every other gate reads the assembled `global_spec.json`. The Factory does not
generate from that document. It normalizes it, cuts one local specification per
module with `tools/build_local_spec.py`, and builds the prompt from the cut. A
defect that exists only in the cut passes the validator, the inspector and
admission, and is met by a started Route B run — one defect per run, because a
run stops at the first module that fails.

Three stops of Cabinet Flow runs were of this kind:

- `models` was told to import `owner_authority.owner_statement`: the operation
  shared its name with a model field, and the slicer derives an import from any
  whole-word match in note or contract text;
- `store_continuity`, `operation_bindings` and `manifest_reader` were told to
  import a function whose name was one of their own contract parameters;
- nine modules carried the value of a `= rules.x` address, and the data/code
  seam (SPEC_STANDARD §15.9) refuses to build a prompt that contains a value.

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
- `data_provider_not_assembled`, `data_provider_constant_without_source`,
  `data_provider_source_unresolved`, `data_provider_lowering_drift` — a
  `70_data_provider_closure.json` that declares `lowered_from` is held to it:
  the assembled `rules.data_provider_backend` equals the closure, every constant
  names its `rules` or `config` address, and the constant still equals the value
  there. A record table lowered from a plain list is compared as that list.

A case whose values live only in the provider declares no `lowered_from` and is
not compared.

## Workflow

```bash
python tools/design_factory_slices.py examples/<case> --factory-root ../code_factory
python tools/design_factory_slices.py examples/<case> --factory-root ../code_factory --json
```

Stage 9 admission runs the same probe as `FA018`. Run it alone while authoring
notes and contracts: it needs no clean checkout and takes seconds per module.

## What it does not see

A name that is both a callable and a model field is reported only once the
Factory actually induces an import from it. Today's correct import of such a
callable is not a finding; the first note that lists the field in a module that
does not call the function will be.
