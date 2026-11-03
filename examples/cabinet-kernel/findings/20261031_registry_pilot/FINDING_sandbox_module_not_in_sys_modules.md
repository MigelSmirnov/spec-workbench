# Finding: a module that uses `dataclasses` with deferred annotations crashes in the sandbox

Observed on a local instance of the promoted Kernel tree:
- code-factory `projects/cabinet_kernel/cabinet_kernel` at `034b50c`;
- Python 3.12, pydantic 2.13.5, bubblewrap 0.9.0.

It was **not** checked on the owner's running Kernel (see `KERNEL_PILOT_REPORT.md`).

## What happens

The Kernel's in-sandbox runner (`cabinet_kernel/sandbox_runner.py`, runner
source, lines 736–749 at `034b50c`) loads the implementation in three steps:

```python
module_specification = importlib.util.spec_from_file_location("cabinet_sandbox_code", configuration["code_file"])
code_module = importlib.util.module_from_spec(module_specification)
module_specification.loader.exec_module(code_module)
```

It never enters the module in `sys.modules`. `dataclasses` processes a class
whose annotations are strings, as they are under `from __future__ import
annotations`, by looking up `sys.modules[cls.__module__].__dict__`. That lookup
gets `None`, so the class definition raises while the module loads, and the
execution is `crashed`.

## Reproduction

Through the Kernel: `finding/repro.py` issues slot `exp_kernel_dataclass_repro`
with one case and no expected output, submits two modules and tries each
(`finding/repro_result.json`):

| module | admission | trial outcome | failure_detail |
|---|---|---|---|
| `repro_module_no_future.py` — `@dataclass` without `from __future__ import annotations` | admitted | passed, `out = 3` | — |
| `repro_module.py` — the same with `from __future__ import annotations` | refused | crashed | `AttributeError: 'NoneType' object has no attribute '__dict__'` |

Without the Kernel: `run_local.py` loads a module the way the runner does.
With the shim removed, the same error appears at load time.

## Against the specification

Function rules A03 rules 2–3 (spec-workbench `agent/cabinet-kernel`,
`02_rules_functions.md`) say:
- the runtime is "one Python interpreter with its standard library";
- an implementation is "a Python module that defines a top-level function
  `run`".

Nothing says a module may not use `dataclasses` or postponed annotations, and
nothing says the module is not importable by its own name. A standard Python
import registers the module, so a reader of the specification would not
expect this crash. It is therefore either an implementation gap or an
unstated limit of the release. The specification should say which.

## Effect on authors

Agent code that uses `dataclasses` or `typing.get_type_hints` with postponed
annotations is refused at admission, with a message that does not name the
cause. Two workarounds exist:
- drop `from __future__ import annotations`;
- register a stub module under `__name__`. This pilot did that (adaptation 3).

## Not changed

The Kernel code, its specification and the deployment were not touched. The
finding is reported here only.
