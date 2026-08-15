# Factory Admission Workbench — Stage 9

Stage 9 proves that one exact, committed Workbench specification can become the
accepted canonical specification of one Factory project. It does not generate
or deploy product code.

## Boundaries

- `factory_admission_workbench` owns read-only checks and the versioned report.
- `design_factory_admission.py` is the normative operator-facing gate.
- `export_to_factory.py` owns the explicit mutation and reuses the same gate.
- Factory Route B starts only after the handoff and is outside Stage 9.

The Factory bootstrap may normalize JSON whitespace. Admission therefore binds
semantic equality with the Factory canonical JSON hash and records both source
and target file hashes. Declared semantic test files remain byte-exact.

## Commands

```bash
python tools/design_factory_admission.py examples/<case> \
  --project <factory-project> --update-existing --json

python tools/export_to_factory.py --case <case> \
  --project <factory-project> --update-existing --check

python tools/export_to_factory.py --case <case> \
  --project <factory-project> --update-existing
```

`--check` and `design_factory_admission.py` never write to Factory. Do not use
`--allow-dirty-source` for an accepted handoff; that flag exists only for
diagnostic and migration work and produces an explicit warning.

## Checks

- `FA001` — committed, clean Workbench source;
- `FA002` — closed Stage 8.1 ledger with current slice hashes, when present;
- `FA003` — aggregate Workbench assembly readiness;
- `FA004` — byte-identical Workbench and Factory `SPEC_STANDARD.md`;
- `FA005` — PASS from the real Factory canonical validator, bound to the source;
- `FA006` — closed, byte-addressable semantic-test handoff, when declared;
- `FA007` — target create/no-op or explicit replacement authorization;
- `FA008` — Factory admission-tool fingerprints and checkout state.

Only `READY_TO_EXPORT` authorizes export. A successful export writes
`spec_workbench_factory_admission.json`, `spec_workbench_validation.json`,
`spec_workbench_handoff.json`, and the Factory-compatible accepted
`spec_editor_manifest.json` under the project's `specs/working/`. The historical
manifest name represents accepted deterministic spec lineage; its producer and
route identify the external Stage 9 handoff rather than `spec_ops`.

## Completion

Stage 9 is complete when the Factory canonical JSON is semantically identical
to the validated source, semantic tests were copied byte-exact, receipts bind
the source commit and both repositories' hashes, and Factory state reports that
exact accepted specification as the input to Route B. Terminal OTK is not a
Stage 9 requirement.
