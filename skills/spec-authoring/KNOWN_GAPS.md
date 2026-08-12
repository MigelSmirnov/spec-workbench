# Known specification-language gaps

This file records intentionally deferred inconsistencies in the specification language. Entries here are not accepted design patterns; they are migration debt that remains visible while dependent tooling is being stabilized.

## KG-001 — `adapters` still use a legacy free-string mapping language

Status: deferred until the Factory transition to deterministic data blocks is stable.

The current `SPEC_STANDARD.md` section `## 3. adapters` predates the closed call-argument DSL introduced by `rules.http_router_backend/v1` in §6.1. It still permits mappings such as `"file.name"`, `"arg0"`, and `"literal:300"`, and describes `requires_cache: true` as an agent hint.

This is intentionally not being redesigned yet. Changing adapter semantics now would introduce another moving boundary while Factory behavior is still being stabilized.

The target invariant is nevertheless fixed:

- call-argument mapping must be structural rather than expression strings;
- argument/ref forms must come from a closed, versioned registry;
- read-once/cache semantics must be normative structure rather than an advisory hint;
- adapter arity and resolvable argument sources must be checkable against canonical `contracts` without interpreting free-form expressions.

`tests/test_known_gap_adapters_dsl.py` is an expected-failure contract test for this gap. It must remain `xfail(strict=True)` until the standard and dependent Factory tooling are migrated together. An XPASS is a signal to remove this debt record only after the structural adapter DSL is actually normative and validated.
