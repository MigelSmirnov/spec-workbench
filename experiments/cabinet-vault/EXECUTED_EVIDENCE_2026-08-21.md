# Cabinet Vault — executed evidence 2026-08-21

## Environment

Executed in the user's real Termux checkout of:

```text
branch: agent/cabinet-vault-experiment
head before evidence run: 008d9fb
```

This is runtime evidence from the checked-out branch, not inferred CI status.

## Focused experiment suite

Command:

```bash
python -m pytest -q \
  tests/test_box_*.py \
  tests/test_cabinet_*.py \
  tests/test_estimate_derivability.py \
  tests/test_plan_actual_*.py \
  tests/test_generic_host_lowering_contract.py \
  tests/test_host_lowering_plan.py \
  tests/test_host_provider_verification.py
```

Observed result:

```text
114 passed in 2.25s
```

Disposition:

```text
PASS
```

This validates the focused experiment tooling and guards present at commit `008d9fb`. It does not verify the previously failed generated classical Cabinet Backend.

## Box language audit

Observed result:

```text
Box language audit: pass
Language: cabinet_box_language.v0
Tools: box_composition, box_derivability
Rules: 15
box_language_exit=0
```

Disposition:

```text
PASS
```

## Generated-backend boundary audit

Observed structural result:

```text
status = classified
issues = []
verification_gate = block
boundary_exit = 2
```

The required skipped semantic/runtime verification normalized to:

```text
declared = SKIP
effective = UNVERIFIED
```

Disposition:

```text
PASS for the boundary-audit guard
UNVERIFIED for the old generated backend
```

The non-zero audit exit is expected and required. It proves the old backend is not promoted to verified state merely because its failures can now be classified.

## Generic host lowering plan

Observed result:

```text
box_id = cabinet.local.archive
profile_id = local_postgres_filesystem_candidate.v0
status = compiled
gaps = []
verification_gate = block
runtime_dependencies = [psycopg, pydantic]
host_plan_exit = 2
```

All selected providers remained:

```text
UNVERIFIED
```

Disposition:

```text
PASS for structural relation/dependency closure
UNVERIFIED for provider runtime behavior
```

The explicit `psycopg` projection is present, closing the structural form of the dependency-projection failure observed in the classical generated backend. Runtime import and behavior still require provider probes.

## Patch integrity

Observed result:

```text
git diff --check
diff_check_exit=0
```

Disposition:

```text
PASS
```

## Current proof boundary

The experiment has now executed and passed its current structural guards.

The next gate cannot be advanced by editing status fields. It requires a concrete generic provider plus executed provider probes.

First target:

```text
postgres_record_kernel
```

Required evidence:

```text
RECORD-PROBE-001 psycopg imports in selected runtime
RECORD-PROBE-002 transaction commits atomically or rolls back
RECORD-PROBE-003 exact-resource lock serializes conflicting mutations
RECORD-PROBE-004 failed transaction publishes no partial metadata state
RECORD-PROBE-005 audit persistence is append-only
```

Only after those probes execute and pass may `postgres_record_kernel` move from `UNVERIFIED` to `PASS`.
