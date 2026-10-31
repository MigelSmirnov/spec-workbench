# Kernel objects created by the pilot, and what is left behind

All objects are in the **local** Kernel instance:
- code: code-factory `projects/cabinet_kernel/cabinet_kernel` @ `034b50c`;
- store: `<scratchpad>/kernel-local/data`, listening on `127.0.0.1:8930`.

The owner's running Kernel was not reached, and nothing was created there.

Kernel records are append-only (spec A01 rule 6). These objects cannot be
deleted through the interface. They are reported here so the owner can recognise
them. The local instance lives in this session's container and is discarded
with it.

## Slots

| slot | purpose (abridged) | contract_version_id | current implementation | corpus |
|---|---|---|---|---|
| `exp_registry_audit_probe` | EXPERIMENT; the model over synthetic data; probe cases **without** expected outputs: hypotheses, not product expectations; no flow uses it | `44eaa094ce73cab35794111375942ce003b2201ec113378ce22ae01d4493d988` | `a72c8bfb03248ad932f45cbe6bfd3872c3fb8e3f3eadae0cd176947442ad361c` (admitted, activated) | 14 cases (`cases/probe_cases.json`) |
| `exp_registry_audit_accepted` | EXPERIMENT; the same model; only witnesses the current text (V6) accepts, **with** expected outputs | `3623731a414f7666b88409de336d652ccd18043a1ae38bfb8eadda523fd27688` | `8f0fc5c98b615c4eb9d77117cbfe07e5cc0f45eb117ad016101f50679869ddec` (admitted, activated) | 11 cases (`cases/accepted_cases.json`) |
| `exp_kernel_dataclass_repro` | EXPERIMENT; reproduces the finding | `18c53b62f169c33a8f7e481eed9d71576bf4a6b66d2ca0479a705b79b2814637` | `301c1229…e3b3` (admitted, activated) | 1 case |

## Implementations

| implementation_id | slot | code | verdict |
|---|---|---|---|
| `f1b0ca05187b7732bf09b160d752fdac9f814585bbbe2ab4e93005ce7f962fbd` | probe | the bundle without adaptation 3 | refused: `failing_case`, `crashed` (the finding) |
| `66c5d10f5db027b34fe79ae586c1a8efb82851f233796ab020116ffa0431c043` | accepted | the same | refused: `failing_case`, `crashed` |
| `a72c8bfb…d361c` | probe | `adapter/kernel_function.py`, sha256 `b320078e…b3e4b6` | admitted |
| `8f0fc5c9…9ddec` | accepted | the same code | admitted: every expected output digest matched |
| `301c1229…` / `ab16d627…` | dataclass repro | `finding/repro_module_no_future.py` / `finding/repro_module.py` | admitted / refused (crashed) |

All trial case and execution identities are in `kernel/local-034b50c/ids.json`
and `kernel/local-034b50c/trace.json`. The answers are verbatim, without
tokens.

## Not created

No binding, flow, flow version, flow activation, run, approval or grant. No
effectful object at all. No existing slot was named.

## Activations

`submit_implementation` admits and activates in the same request (spec A04
rule 4). It cannot be split.

- Each experimental slot therefore has one activation of its admitted
  implementation.
- A refused implementation records a verdict and activates nothing.
- These activations serve nothing: no flow references the slots.
