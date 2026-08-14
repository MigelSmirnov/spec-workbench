# Task: deterministic runtime closure for the next specification assembler

## Status

Proposed work for the next assembler version.

## Problem

The current pipeline proves model/type closure, deterministic persistence
projection, contract closure, Router closure, and structural module-slice
completeness. It does not prove that the assembled application can construct and
execute every behavioral module.

The Cabinet Backend Stage 8.1 review demonstrated the missing class of proof:

- a module can own persistent records without receiving a repository or unit of
  work;
- a function can promise durable byte custody without having a byte-store
  boundary;
- a gateway can be structurally complete without a concrete HTTP client,
  credentials, or startup configuration;
- accepted module capabilities can disappear before contract lowering;
- a function can promise recorded evidence whose model is not classified for
  persistence;
- `bootstrap` can construct one dependency while the rest of the application
  graph remains unbound;
- every individual slice can have zero structural blocks while the full runtime
  is not executable.

Stage 8.1 correctly exposes these defects, but they should be reported by a
deterministic gate before human module review.

## Goal

Add a **runtime closure** phase that proves, without semantic guessing, that:

1. every accepted runtime effect is represented by a declared narrow boundary;
2. every required boundary has one concrete deployment binding;
3. every stateful behavioral module can access its declared persistent state;
4. every accepted capability required by the first implementation is lowered to
   a contract or explicitly excluded;
5. the composition root can construct the complete application dependency graph;
6. restart-surviving evidence is represented in deterministic persistence;
7. multi-resource transitions declare an accepted failure/recovery strategy.

The output must identify the earliest design state that owns each repair.

## Non-goals

- Do not generate repositories, clients, or business behavior in the workbench.
- Do not infer effects from verbs, prose, notes, function names, or model names.
- Do not treat note count as completeness evidence.
- Do not make Router, models, persistence codecs, or ordinary table handlers
  LLM-generated.
- Do not require every module to have a repository; pure and deterministic
  modules must remain valid.
- Do not prescribe dependency injection as function parameters versus cohesive
  service objects. The accepted spec must choose and expose one constructible
  form.

## Required normative IR

Extend `SPEC_STANDARD.md` with a closed, versioned structured block. The exact
final key names may change during standard review, but the IR must express the
following facts without free-form expressions.

### Runtime resources

Each resource declaration has:

- stable resource key;
- closed kind, initially `postgres_uow`, `byte_store`, `http_client`, or
  `credential_provider`;
- interface model and its method-contract keys;
- owning module;
- lifecycle (`application` or `operation`);
- required configuration references;
- whether startup may proceed without a binding.

Concrete implementations declare:

- implemented resource key;
- concrete constructor contract;
- deployment target/profile;
- required config references;
- implementation module.

### Function effects

Every behavioral callable may declare a closed set of effects:

- persistent models read;
- persistent models written;
- runtime resources used;
- remote mutation or remote read;
- secret access;
- atomic effect group, when more than one resource participates.

Effect declarations are references only. They contain no code, SQL, paths,
URLs, retry algorithms, or environment values.

### Capability disposition

Every State 3 capability must have one final disposition:

- `contracted` with an exact contract key;
- `deterministic_backend` with a supported backend owner;
- `deferred` with an accepted scope/decision reference;
- `removed` with an accepted repair reference.

An unclassified candidate capability is not allowed in a finalized module.

### Composition bindings

The composition root declares structural bindings from required interface/resource
keys to concrete constructors and constructor arguments. Argument sources use a
closed registry such as config reference, another binding, or deterministic
backend product. Free-form Python expressions are forbidden.

Bindings must cover both application startup and separately exposed offline
administration entry points.

### Atomic effect groups

A function that writes more than one independently failing resource declares one
closed strategy:

- one transactional resource boundary;
- staged write followed by atomic publication;
- durable outbox/reconciliation;
- compensating cleanup plus recoverable pending evidence;
- another future strategy added through a versioned backend registry.

The assembler validates structure and coverage. Behavioral details remain in
accepted decisions and generation notes.

## Deterministic checks

### RC001 — persistent access closure

If a behavioral function declares reads or writes of a persistent model, its
module must receive a resource whose interface contracts cover the required
access. A persistence classification alone is not runtime access.

### RC002 — external effect closure

Every byte-store, remote HTTP, credential, or other declared external effect must
reference a declared runtime resource.

### RC003 — concrete binding closure

Every required runtime resource reachable from an exported application operation
must resolve to exactly one concrete binding in the selected deployment profile.
Zero and multiple bindings are errors.

### RC004 — constructor graph closure

Starting at each composition-root export, recursively resolve constructor inputs.
Reject missing bindings, cycles without an accepted provider mechanism, type
mismatches, unused required constructors, and undeclared ambient globals.

### RC005 — configuration closure

Every concrete constructor's configuration reference must exist in deterministic
`config`. Secret-bearing resources must reference secret/credential configuration
owned by the proper boundary. Missing required configuration must have fail-closed
startup behavior.

### RC006 — capability lowering closure

Every State 3 capability has exactly one accepted disposition. A `contracted`
capability resolves to an owned canonical contract and export visibility compatible
with its callers.

### RC007 — durable evidence closure

Models explicitly declared as restart-surviving outputs or decision evidence must
be present in deterministic persistence. Conversely, the check must not infer
durability from prose.

### RC008 — multi-resource atomicity closure

A callable writing multiple independently failing resources must reference one
accepted atomic effect group and strategy. Absence is an error, not a review
prompt.

### RC009 — dependency visibility closure

Resource interfaces, constructor types, and dependency contracts must be present
in the appropriate internal imports/model context without leaking concrete
implementations into business callers.

### RC010 — deterministic surface exemption

Factory-owned model, persistence, Router, and registered irregular-adapter
surfaces pass without behavioral notes or invented runtime ports unless their
backend declaration itself requires a resource binding.

## Diagnostics

Diagnostics must be stable, machine-readable, and actionable:

```json
{
  "schema_version": "spec_workbench_runtime_closure.v1",
  "status": "blocked",
  "deployment_profile": "local_linux",
  "errors": [
    {
      "code": "RC003",
      "module": "holded_gateway",
      "symbol": "create_holded_purchase",
      "resource": "holded_http",
      "message": "required runtime resource has no concrete binding",
      "repair_state": 3,
      "evidence": ["module:holded_gateway", "contract:create_holded_purchase"]
    }
  ],
  "warnings": [],
  "modules": {}
}
```

Human-readable output must group defects by earliest repair state and then by
module. The tool must never report `ready` when errors exist.

## CLI and integration

Add:

```bash
python tools/design_runtime_closure.py examples/<case> --json
python tools/design_runtime_closure.py examples/<case> --profile local_linux
python tools/design_runtime_closure.py examples/<case> --module durable_archive --json
```

Pipeline position:

```text
State 6 contracts
-> deterministic data/type closure
-> runtime closure authoring
-> State 7 generation notes
-> final assembly
-> final runtime closure validation
-> Stage 8.1 module review
```

The authoring pass may report missing structured decisions. The final validation
pass consumes only assembled normative IR and is a hard gate for Factory export.
`design_assembly.py` and `export_to_factory.py` must refuse a ready/exportable
result when final runtime closure is blocked.

`design_module_review.py --slice` must include the module's resource requirements,
effect declarations, concrete bindings reachable from the selected composition
root, and runtime-closure diagnostics. It must continue to separate deterministic
facts from human semantic review.

## Required tests

Add unit and integration fixtures for at least:

1. pure module with no runtime resources — ready;
2. persistent model plus explicit repository/UoW binding — ready;
3. persistent classification without runtime access — `RC001`;
4. HTTP gateway without client binding — `RC002` or `RC003`;
5. required secret/config reference missing — `RC005`;
6. capability declared in State 3 but not lowered or deferred — `RC006`;
7. durable decision evidence absent from persistence — `RC007`;
8. database plus byte-store mutation without strategy — `RC008`;
9. complete staged database/filesystem design — ready;
10. missing bootstrap constructor input — `RC004`;
11. duplicate concrete bindings in one profile — `RC003`;
12. deterministic Router/irregular adapter without behavioral notes — ready;
13. final assembly blocked by runtime error;
14. Factory export blocked by runtime error;
15. module slice contains only relevant runtime closure evidence.

Create a Cabinet-derived regression fixture covering PostgreSQL archive access,
local filesystem source custody, Holded HTTP, VPS transport, release-decision
durability, and full local-Linux bootstrap construction.

## Acceptance criteria

The work is complete when:

- the new IR is normative, closed, versioned, and validated;
- runtime closure results are deterministic for identical inputs;
- all RC001–RC010 diagnostics have stable tests;
- final assembly and Factory export are hard-gated;
- module slices expose the proof without duplicating or interpreting it;
- existing pure and deterministic examples remain valid without artificial ports;
- the repaired Cabinet Backend can reach `ready` for `local_linux` only after all
  PostgreSQL, filesystem, VPS, Holded, config, and bootstrap bindings are closed;
- malformed or incomplete runtime IR fails explicitly rather than becoming an LLM
  prompt;
- documentation and authoring sequence describe how to repair the earliest state.

## Suggested implementation order

1. Accept the normative IR and schemas in `SPEC_STANDARD.md`.
2. Implement parser/model objects in a dedicated `runtime_closure_workbench`
   package.
3. Implement RC006 and RC007 cross-state checks.
4. Implement resource/effect and composition-graph checks RC001–RC005 and RC009.
5. Implement atomic-effect validation RC008 and deterministic exemption RC010.
6. Add CLI and machine-readable report.
7. Gate assembly and Factory export.
8. Enrich Stage 8.1 slices.
9. Migrate Cabinet Backend as the end-to-end regression case.
