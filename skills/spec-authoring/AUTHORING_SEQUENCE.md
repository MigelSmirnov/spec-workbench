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
  -> deterministic persistence_backend/v2 closure (when used)
  -> deterministic HTTP per-route closure (when used)
  -> deterministic HTTP global context closure
  -> deterministic http_router_backend/v1 assembly
  -> State 7  Notes
  -> final specification assembly / validation (Stage 8)
  -> assembled module review (Stage 8.1)
  -> Factory admission and handoff (Stage 9)
  -> Factory Route B
```

The intermediate structured-data closure is **not State 6**. Existing artifacts
and schemas named `60_data_closure.json` / `spec_workbench_state6_data_*` are
retained for compatibility only; their numeric name does not redefine the
semantic state numbering in `SKILL.md`.

Likewise, `70_persistence_closure.json`, `70_router_closure.json`, and
`70_router_context.json` are workbench artifact names, not statements that any
of these closures are semantic State 7. State 7 remains Notes.

## Required dependency chain for deterministic persistence assembly

For projects using `rules.persistence_backend` the dependency chain is:

```text
reviewed State 4 flow and accepted structured persistence facts
  -> State 5 owning public operations
  -> State 6 canonical repository/schema-function contracts and module ownership
  -> post-contract Persistence Closure
  -> deterministic persistence_backend/v2 handoff
  -> State 7 notes for only the remaining LLM-owned callables
  -> official deterministic Route B persistence emitter
```

The complete `persistence_backend/v2` is **not** a pre-contract data value.
Tables and accepted storage facts may originate from earlier structured design
evidence, but repository classes, schema functions, and methods must bind to
canonical State 6 contracts. Therefore the full backend IR is authored only
after State 6 and is carried by `70_persistence_closure.json` until final spec
assembly projects its exact `backend_ir` into `rules.persistence_backend`.

Absence of `70_persistence_closure.json` means deterministic SQLite persistence
was not selected and the ordinary generation path remains valid. Once the file
exists, it is an explicit opt-in: an open or invalid closure blocks progress and
must never be repaired by deleting the backend or silently falling back to LLM
generation. `persistence_backend/v2` is currently SQLite-only; a PostgreSQL
repository design does not opt into it merely because the project has persisted
models.

### Persistence invariants

1. Canonical Python signatures come only from State 6 contracts.
2. Persistence Closure never creates, infers, duplicates, or overrides a Python signature.
3. A deterministic repository class, its schema function, and its declared backend-owned methods must resolve to the same canonical State 6 module ownership.
4. `begin`, `commit`, `rollback`, and `close` remain outside deterministic persistence backend ownership.
5. One persistence module owns one repository class plus its schema function; partial class emission and companion delegation are forbidden.
6. An irregular repository remains wholly on the ordinary generation path; an enabled invalid backend never silently falls back.
7. Final persistence IR is the exact deterministic handoff from the closed authoring artifact; final assembly does not invent repository semantics.

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
   project-policy rules, properties, or determinism facts, but it cannot consume
   the State 6 number, fabricate contract-dependent values, or contain the full
   contract-dependent `persistence_backend` IR.
6. Persistence Closure and per-route Router Closure are post-contract. Their rows
   may be designed only when the owning canonical contracts are stable enough to
   validate ownership, method/call identity, arity, and parameter paths.
7. Global Router context closure must declare every route auth policy, app-state
   binding, credential extractor, principal resolver and canonical exception
   mapping before final IR assembly.
8. Final `rules.http_router_backend` is assembled deterministically from closed
   authoring artifacts; the assembler does not make semantic decisions.
9. A deterministic backend present but invalid is a defect. Do not remove it or
   silently fall back to an LLM path.
10. Artifact filename prefixes are storage conventions, not semantic state
    authority. When a filename conflicts with this sequence, this sequence and
    `SKILL.md` win.

## Deterministic authoring entrypoint

Post-State-5 agents should ask the sequencer what comes next instead of choosing
between State 6 and deterministic backend closures from filenames:

```bash
python tools/design_authoring_next.py examples/<case> --json
```

The sequencer is the ordering gate. It routes to:

- `design_stage6_data.py` when pre-contract structured data has deterministic
  errors;
- `design_stage6_contracts.py` until the explicit State 6 function plan is
  closed and every planned function has an exact signature;
- `design_persistence_authoring.py` when optional post-contract
  `persistence_backend/v2` closure has been selected but is open or invalid;
- `design_router_authoring.py` for contract-aware per-route closure after the
  State 6 handoff and any enabled persistence closure are ready;
- `design_router_context.py` after per-route closure to finish backend wiring,
  principals/auth policies and error policy;
- State 7 notes only after all enabled deterministic backend closures are ready.

`design_router_closure.py`, `router_workbench.service`, and the structural
`persistence_workbench.validator` remain low-level DSL/unit-test surfaces. They
intentionally do **not** prove the complete cross-state authoring readiness by
themselves. Use the official authoring facades and sequencer for transitions.

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

When the State 6 handoff is ready, deterministic backend semantic slices may
bind only to these canonical symbols. Neither persistence nor router closure may
duplicate Python signatures.

## Deterministic Persistence Closure artifact

The optional persistence authoring split is explicit:

- `70_persistence_closure.json` — a small authoring wrapper with
  `schema_version`, `status`, and exact `backend_ir`;
- `backend_ir` — the normative `persistence_backend/v2` value that will be
  copied into `rules.persistence_backend` only after structural and State 6
  ownership validation succeeds;
- `design_persistence_authoring.py --coverage` — validates the closed v2 shape,
  repository/module ownership, schema-function contracts, method contracts, and
  backend-owned transaction restrictions;
- `--handoff` — emits `backend_ir` only when the closure is `closed` and has zero
  deterministic errors.

The closure does not invent SQLite applicability. Projects using PostgreSQL or
another unsupported storage backend remain on the ordinary generation path and
normally have no `70_persistence_closure.json`.

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
- `70_persistence_closure.json`: optional post-contract deterministic SQLite
  persistence closure; absence means the ordinary persistence generation path;
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
