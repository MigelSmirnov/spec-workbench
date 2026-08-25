# Cabinet Backend — deterministic interface declaration ownership review

## Scope

Route B for accepted Workbench commit `7a01f94` passed canonical validation and
the fresh Factory Spec Inspector, then stopped at the deterministic models
emitter. All eleven `kind: interface` declarations were physically owned by
their consuming domain modules even though SPEC_STANDARD v2 emits every
declaration from the `models` section through the deterministic `models.py`
producer.

This repair moves declaration ownership only:

- all eleven Protocol symbols are exported by `module:models`;
- each consuming runtime module imports its required Protocol from `models`;
- concrete adapter classes remain owned by their domain modules;
- implementation obligations, contracts, notes, policies, and public operations
  are unchanged.

State 3 records the distinction between deterministic type ownership and domain
policy/implementation responsibility.

## Deterministic review

All twelve assembled module packets pass
`design_module_review.py --review` with zero blocks:

- `models`: 87 contracts, 89 notes;
- `access_control`: 7 contracts, 14 notes;
- `durable_archive`: 31 contracts, 59 notes;
- `registry_context`: 18 contracts, 39 notes;
- `holded_gateway`: 20 contracts, 29 notes;
- `synchronization`: 31 contracts, 45 notes;
- `plan_actual`: 24 contracts, 46 notes;
- `holded_publication`: 17 contracts, 36 notes;
- `retention_release`: 15 contracts, 32 notes;
- `api_irregular`: 1 contract, 3 notes;
- `api`: 15 contracts, 24 notes;
- `bootstrap`: 4 contracts, 24 notes.

The candidate has no deterministic models-emission blockers and passes
Workbench assembly, Factory canonical validation, and Factory Spec Inspector
with `BLOCK=0` and `WARN=0`.

## Adversarial semantic review

Moving a Protocol declaration cannot transfer its repository, transport,
authorization, archive, publication, synchronization, or release policy to the
models module. The models module emits only typed Protocol surfaces. Services
continue to own decisions and concrete adapters continue to own SQL, filesystem,
credential, and HTTP mechanisms.

No caller changes its accepted dependency type, no port method changes
signature, and no local implementation obligation changes disposition.

## Result

- deterministic declaration ownership: `PASS`;
- domain modules: `PASS_INTERNAL_VARIATION`;
- router and bootstrap consumers: `PASS`.

The candidate is ready for a new committed Workbench handoff and a restarted
Route B from the new accepted specification SHA.
