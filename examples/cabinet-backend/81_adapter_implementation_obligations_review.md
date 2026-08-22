# Cabinet Backend — adapter implementation-obligation repair review

## Scope

Stage 9 admission proved that the assembled specification did not structurally
bind interface-typed dependencies to the local adapters already accepted in
States 1–6. The repair adds eleven local `implementation_obligations`, including
the previously ordinary-class Holded ports, and gives every concrete adapter the
complete method surface of its port. Ninety-five concrete callables are now
closed in the State 6 contract inventory, with 97 classified notes (some
constructors require two independent security and validation constraints).

The repair also closes the direct model-import surface required by those
contracts. It changes no product rule, lifecycle, external authority, public
operation, HTTP route, or persistence ownership.

## Deterministic review

The changed module packets pass `design_module_review.py --review` with zero
blocks and zero review prompts:

- `holded_gateway`: 33 contracts, 42 notes;
- `synchronization`: 47 contracts, 61 notes;
- `plan_actual`: 36 contracts, 58 notes;
- `holded_publication`: 26 contracts, 45 notes;
- `retention_release`: 22 contracts, 39 notes;
- `durable_archive`: 51 contracts, 79 notes;
- `registry_context`: 26 contracts, 47 notes;
- `api_irregular`: 1 contract, 3 notes;
- `api`: 15 contracts, 24 notes;
- `bootstrap`: 4 contracts, 24 notes.

The candidate passes Workbench assembly, Factory admission checks FA005 and
FA010, and Factory Spec Inspector with `BLOCK=0` and `WARN=0`.

## Adversarial semantic review

A concrete repository or transport method can no longer be emitted as a
constructor-only class, `pass`, `NotImplementedError`, a fabricated default,
or a forwarding placeholder without violating its exact concrete contract and
classified note.

Concrete notes intentionally mirror the already accepted interface behavior.
This introduces no second policy owner: the concrete class is the local
implementation of the same port obligation, while service modules retain all
business decisions.

The two Holded mechanism types are now explicit interfaces because their
accepted State 1 and State 3 evidence already describes them as narrow ports
with local implementations. Treating them as ordinary concrete base classes was
an assembly defect.

## Result

- `holded_gateway`: `PASS`;
- `synchronization`: `PASS_INTERNAL_VARIATION`;
- `plan_actual`: `PASS_INTERNAL_VARIATION`;
- `holded_publication`: `PASS_INTERNAL_VARIATION`;
- `retention_release`: `PASS_INTERNAL_VARIATION`;
- `durable_archive`: `PASS_INTERNAL_VARIATION`;
- `registry_context`: `PASS_INTERNAL_VARIATION`;
- `api_irregular`: `PASS`;
- `api`: `PASS`;
- `bootstrap`: `PASS`.

All remaining implementation freedom is internal SQL/HTTP organization that
preserves the accepted ports, transactions, idempotency, evidence, bounds, and
failure behavior.
