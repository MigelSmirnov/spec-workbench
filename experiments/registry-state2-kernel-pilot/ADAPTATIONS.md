# Adaptations of the Registry model to the Kernel interface

The model is `experiments/registry-state2-investigation/model/sandbox.py` at
commit `868ce840`:
- sha256 of the file `ff2f934c…b8ae`;
- `VERSIONS` from `model/sources.py` of the same commit.

`adapter/build.py` assembles `adapter/kernel_function.py` from them. Every
change between the model and the code the Kernel runs is listed below. None of
them changes a rule, a reading, a reduction or a default.

| # | adaptation | why the Kernel needs it | effect on meaning |
|---|---|---|---|
| 1 | One file: `sandbox.py` + the `VERSIONS` literal (extracted with `ast`) + `entry.py` | an implementation is one Python module (A03 r3); no other file is mounted | none: the text is concatenated, and `diff` shows only rows 2 and 3 |
| 2 | `run(inputs)`: five input ports (`version`, `interpretation`, `initial`, `events`, `mode`) and two output ports (`observation`, `analysis`) | an implementation is `run(dict) -> dict`, one entry per port (A03 r3) | none: `entry.py` calls the model's own `rules_for`, `step`, `initial`, `observe`, `alphabet`, `apply`, `check`; the exploration is the previous `run.py`'s `explore`, copied |
| 3 | Two lines after `from __future__ import annotations` register a stub module under `__name__` in `sys.modules` | the runner does not register the module, and `dataclasses` crashes without that (finding) | none: the stub is an empty namespace that nothing of the model reads |
| 4 | The initial state is given as `initial.setup_events`: the admissible history that reaches it | the model has no constructor for an arbitrary state; a history keeps the state reachable | none: the same as the previous experiment's witnesses ("initial" + setup events) |
| 5 | The readings default to the previous experiment's defaults; unknown readings, versions, modes or event fields raise | an input error must be distinguishable from a model result | none for valid input; an invalid input makes the execution `crashed`, never a false finding |
| 6 | Exploration depth 4 (instead of the previous 6) in the two `explore` cases | the release ceiling `wall_time_ms` is 30 000 ms per execution (A20) | a smaller bound, stated in the case; depth 4 with restore took 191 ms in the Kernel, so depth 6 also fits (the local depth-6 run of the previous experiment took ~2–4 s for V6) |

What the adapter returns:
- **A conflict or an ambiguity is a result, not an error.** The function
  succeeds (`passed` without expected outputs) and reports the conflict in
  `analysis.classification` and `analysis.steps[*].conflict_sets`.
- **Only a malformed input or a fault of the model ends `crashed`.**
- **Nothing outside the inputs is read.** No Registry operation, no clock, no
  randomness: the model never used any, and the Kernel's traps would have
  reported `sandbox_violation`.

Not adapted:
- `sandbox.py` is not edited;
- no rule was simplified to fit a bound: the largest output in this pilot (the
  V6 exploration) is far below `stored_value_bytes_max` (1 MiB).
