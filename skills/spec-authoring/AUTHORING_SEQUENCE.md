# Normative authoring sequence

This document fixes the authoring order used by Spec Workbench. It exists to
remove ambiguity between numbered design states, intermediate closure artifacts,
and deterministic Factory backends.

`SPEC_STANDARD.md` remains normative for the serialized `global_spec.json`
format. `SKILL.md` remains normative for the semantic meaning of numbered
states. This document is normative for **ordering and prerequisites**.

## Canonical order

```text
State 0  Product frame
  -> State 1  Models
  -> State 2  Rules / decisions
  -> State 3  Module responsibilities and capabilities
  -> State 4  Reviewed end-to-end flows
  -> State 5  Public module operations
  -> pre-contract structured data closure
  -> State 6  Exact contracts and internal functions
  -> deterministic HTTP per-route closure (when used)
  -> deterministic HTTP global context closure
  -> deterministic http_router_backend/v1 assembly
  -> State 7  Notes
  -> adapters / final specification assembly / validation (Stage 8)
  -> assembled module review (Stage 8.1)
  -> Factory admission and handoff (Stage 9)
  -> Factory Route B
```

The intermediate structured-data closure is **not State 6**. Existing artifacts
and schemas named `60_data_closure.json` / `spec_workbench_state6_data_*` are
retained for compatibility only; their numeric name does not redefine the
semantic state numbering in `SKILL.md`.

Likewise, `70_router_closure.json` and `70_router_context.json` are workbench
artifact names, not statements that Router Closure is semantic State 7. State 7
remains Notes.

## Required dependency chain for deterministic HTTP assembly

For projects using `rules.http_router_backend` the dependency chain is:

```text
reviewed State 4 flow
  -> State 5 owning public operation and exposure decision
  -> accepted structured data placement
  -> State 6 canonical operation + handler/wiring contracts
  -> contract-aware per-route Router Closure
  -> global wiring / principal / auth / error-policy closure
  -> deterministic http_router_backend/v1 assembly
  -> State 7 notes
  -> official deterministic Route B Factory emitter
```

### Invariants

1. Canonical Python signatures come only from `contracts` / State 6.
2. Router rows never create, infer, duplicate, or override canonical signatures.
3. Every externally exposed operation has exactly one canonical handler contract
   before its route row can be closed.
4. Legacy router code is evidence only; it cannot be the source of a new
   signature or a normative route by itself.
5. Pre-contract data closure may place already accepted config, persistence,
   rules, properties, or determinism facts, but it cannot consume the State 6
   number or fabricate contract-dependent values.
6. Per-route Router Closure is post-contract. A route may be designed only when
   its owning operation and handler contracts are stable enough to validate
   ownership, call arity and parameter paths.
7. Global Router context closure must declare every route auth policy, app-state
   binding, credential extractor, principal resolver and canonical exception
   mapping before final IR assembly.
8. Final `rules.http_router_backend` is assembled deterministically from closed
   authoring artifacts; the assembler does not make semantic decisions.
9. `http_router_backend` present but invalid is a defect. Do not remove it or
   silently fall back to an LLM router path.
10. Artifact filename prefixes are storage conventions, not semantic state
    authority. When a filename conflicts with this sequence, this sequence and
    `SKILL.md` win.

## Deterministic authoring entrypoint

Post-State-5 agents should ask the sequencer what comes next instead of choosing
between State 6 and Router Closure from filenames:

```bash
python tools/design_authoring_next.py examples/<case> --json
```

The sequencer is the ordering gate. It routes to:

- `design_stage6_data.py` when pre-contract structured data has deterministic
  errors;
- `design_stage6_contracts.py` until the explicit State 6 function plan is
  closed and every planned function has an exact signature;
- `design_router_authoring.py` for contract-aware per-route closure after the
  State 6 handoff is ready;
- `design_router_context.py` after per-route closure to finish backend wiring,
  principals/auth policies and error policy;
- State 7 notes only after the complete deterministic Router closure is ready.

`design_router_closure.py` and `router_workbench.service` are compatibility
low-level DSL/unit-test surfaces. They intentionally do **not** prove cross-state
readiness. Do not use them as the official authoring path.

Final normalized Router IR is a deterministic projection:

```bash
python tools/design_router_ir.py examples/<case> --handoff --json
```

The assembler requires both contract-aware route closure and global Router
context closure to be ready. It strips authoring-only `operation` keys and emits
the normative `rules.http_router_backend` shape without LLM inference.

## State 6 contract workbench

State 6 uses an explicit plan and catalog:

- `60_contract_plan.json` inventories public operations, internal functions,
  deterministic handler symbols, app-factory/auth symbols and stable ports;
- `60_contracts.json` stores canonical exact Python signatures;
- `60_exception_taxonomy.json` freezes canonical exception symbols and module
  ownership when deterministic transport needs them;
- `design_stage6_contracts.py --next` selects one unresolved function;
- `--coverage` / `--lint` validate plan ownership and signatures;
- `--handoff` is ready only when the function inventory is explicitly closed,
  every planned function is resolved, and every external operation has one
  canonical handler contract.

Public function seeds may be projected from accepted State 5 public operations
because their operation names and owners are already explicit. Internal/private
functions must never be invented by the tool: the author adds them explicitly
to the State 6 plan before setting its status to `closed`.

When the State 6 handoff is ready, the contract-aware Router semantic slice
contains both the canonical owning-operation contract and its canonical handler
contract. Router rows remain transport DSL and still must not duplicate either
Python signature.

## Deterministic Router closure artifacts

The current authoring split is explicit:

- `70_router_closure.json` — one resolved `table`/`irregular` decision per
  externally exposed operation, including method/path/auth/status and typed-ref
  orchestration for table routes;
- `70_router_context.json` — backend/emitter selection, app wiring, state
  bindings, credential extractors, principals, auth policies, projections and
  global exception→HTTP policy;
- `design_router_authoring.py` — validates route rows against State 6 contracts;
- `design_router_context.py` — fail-closed global context readiness;
- `design_router_ir.py` — deterministic final IR assembler.

An `irregular` handler remains a canonical State 6 symbol in its explicit
companion module. It is not free Python hidden in the route artifact.

## Compatibility note

The current Cabinet workbench introduced structured-data and Router Closure
artifacts while the tooling was evolving. Their filenames (`60_*`, `70_*`) must
not be used to infer the authoring order. Until they are migrated, tools and
agents must interpret them by purpose:

- `60_data_closure.json`: pre-contract structured-data preparation;
- State 6 authoring: exact contracts, canonical exceptions and internal
  functions;
- `70_router_closure.json`: post-contract per-route deterministic HTTP closure;
- `70_router_context.json`: post-route global deterministic HTTP closure;
- State 7 authoring: notes.

Any future orchestration tool must read the machine-readable companion
`authoring_sequence.json` rather than reconstructing order from filenames.

## Stage 9 — Factory admission and handoff

Stage 9 is an operational boundary, not a new semantic State and not an
extension of `global_spec.json`. It proves that the exact assembled artifact
accepted by Workbench is admissible to the current Factory checkout.

The read-only gate is mandatory:

```bash
python tools/design_factory_admission.py examples/<case> \
  --project <factory-project> --update-existing
```

It verifies the committed Workbench source, current Stage 8.1 slice hashes,
aggregate assembly, byte-identical `SPEC_STANDARD.md`, the real Factory
canonical validator, semantic test handoff, explicit target replacement intent,
and fingerprints of the Factory admission toolchain. It never writes to either
project.

Only a `READY_TO_EXPORT` report authorizes the mutation step:

```bash
python tools/export_to_factory.py --case <case> \
  --project <factory-project> --update-existing
```

The exporter executes the same admission service again, copies the canonical
specification and declared semantic tests, and writes both admission and handoff
receipts under the Factory project's `specs/working/` directory. Generated code,
deploy, verification and terminal OTK remain inside Factory Route B and are not
Stage 9 completion criteria.
