# Notes Propagation Workbench

State 7 Markdown is the authoring source. `global_spec.json` is the assembled
Factory input and must be updated last.

`design_notes.py --propagate` deterministically carries changes from canonical
inline notes in `80_notes.md` into `global_spec.json["notes"]`. It does not
rebuild the complete notes array from every `80_notes_*.md` file because modular
files may use context-dependent shorthand whose assembled scope is not
reversible from the Markdown alone.

## Commands

While `80_notes.md` has uncommitted changes relative to `HEAD`:

```bash
python tools/design_notes.py examples/<case> \
  --propagate --base-ref HEAD --check

python tools/design_notes.py examples/<case> \
  --propagate --base-ref HEAD
```

When the State 7 source change is already committed and its parent is the
pre-edit state:

```bash
python tools/design_notes.py examples/<case> \
  --propagate --base-ref HEAD^ --check

python tools/design_notes.py examples/<case> \
  --propagate --base-ref HEAD^
```

A different explicit Git revision may be supplied when the pre-edit source is
not `HEAD` or `HEAD^`.

## Safety model

The propagator:

- parses only canonical `scope: [CLASS] text` lines from `80_notes.md`;
- derives exact additions, removals, and replacements from the selected Git
  base revision;
- preserves assembled notes not owned by that canonical source;
- matches modal-only rewrites by normalized text;
- may replace assembly-only dependency bindings only when every conflicting
  candidate is already proven invalid by the notes dependency checker and the
  replacement is valid;
- fails closed on ambiguous same-scope/class matches;
- verifies that every current canonical note occurs exactly once after the
  proposed propagation;
- refuses a change that would increase Factory callable-coverage or dependency
  binding blockers.

`--check` never writes. It exits nonzero when propagation drift exists so it can
be used in CI. A blocked propagation is an operator/design issue and must not be
forced through by editing `global_spec.json` manually.

## Boundary

This tool updates only `global_spec.json["notes"]`. It does not:

- invent or rewrite note semantics;
- lower modular shorthand into qualified notes;
- change contracts, models, rules, router data, or module ownership;
- refresh Stage 8.1 slice hashes or review status;
- run assembly verification or Factory admission.

After propagation, run the notes language diagnostic, aggregate assembly gate,
and the required Stage 8.1 re-review/lineage refresh before Factory admission.
