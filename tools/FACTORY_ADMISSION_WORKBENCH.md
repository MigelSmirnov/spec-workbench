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

`--check` and `design_factory_admission.py` never write to Factory.
`--allow-dirty-source` admits nothing: under the fence a dirty checkout blocks
even when the flag is given; the flag only labels a run as diagnostic. A
`closure_gap_waivers.json` blocks admission outright — a waiver is a decision
nobody made.

## Checks

- `FA001` — committed, clean Workbench source;
- `FA002` — closed Stage 8.1 ledger with current slice hashes, when present;
- `FA003` — aggregate Workbench assembly readiness;
- `FA004` — byte-identical Workbench and Factory `SPEC_STANDARD.md`;
- `FA005` — PASS from the real Factory canonical validator, bound to the source;
- `FA006` — closed, byte-addressable semantic-test handoff, when declared;
- `FA007` — target create/no-op or explicit replacement authorization;
- `FA008` — Factory admission-tool fingerprints and checkout state.
- `FA017` — runtime carriers: no model whose every field is `object` crosses a
  function signature, and every repository lowered from
  `rules.persistence_backend` is reachable — named as the `local`
  implementation of an interface or mentioned by another contract.

- `FA018` — the Factory's own local specifications: `normalize_spec.py` and
  `build_local_spec.py` cut every module in a temporary directory, the
  data/code seam is asked about every cut, and a declared data-provider
  lowering is held to its sources. See `FACTORY_SLICE_WORKBENCH.md`.

`FA017` is unconditional on purpose. `FA010` and the port gates before it react
to an interface the author chose to write; a case with no interface at all makes
each of them report "not applicable", and the first Cabinet Flow runs were
admitted that way with the store, the secrets and the channel credential hidden
behind `payload: object`. The generator then kept records in module-level dicts
and never reached the emitted repository. The check reads only the projected
spec and names the carrier and the functions that use it.

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
