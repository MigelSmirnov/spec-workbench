# State 8 — `global_spec.json` assembly

## Status

**Assembly complete and canonical validation clean.** The assembled file is
`../global_spec.json`. It serializes States 0–7 without adding product
behavior.

## Assembly inventory

```text
models:       104 (26 closed enums + 78 concrete Pydantic shapes)
contracts:    318
notes:        337 classified strings
properties:   21 functions / 29 expressions
determinism:  47 explicit decisions
modules:      20
invariants:   55 / 55 owned and landed
```

The confirmed runtime defaults are serialized: fixed staff/viewer sessions,
existence-hiding self-service password reset, staff TTL 12 hours, viewer TTL
30 days, verification TTL 72 hours, email-change TTL 24 hours, reset TTL 60
minutes, five challenge issues per account/hour, and Argon2id. Deployment-only
Registry URL, email gateway URL, and binary byte limit are represented by
required environment-variable names rather than fabricated values.

## Backward corrections exposed by assembly

1. State 1 now lists every `AuditEntityKind` value derived from the accepted
   audit action catalog and existing entities.
2. State 3 generation order places `authorization_guard` before identity
   modules, matching the already accepted dependency graph.
3. Factory-safe config/rules keys avoid secret-like words while preserving the
   accepted policies (`credential_*`, `project_guard_sequence`, and
   `verification_envelope_policy`).
4. The HTTP boundary now materializes as `api/router.py`: top-level endpoint
   functions and an exact unversioned route catalog replace the accidental
   `PortalApi` class and `api/runtime` path without changing domain behavior.

## Validation evidence

Passed:

```text
python -m json.tool global_spec.json
python tools/semantic_lint.py global_spec.json \
  --invariants spec/invariant_ledger.json --strict
  -> 0 errors, 0 warnings

tools.type_resolver.validate_spec_types(global_spec.json)
  -> 0 findings
```

Canonical Factory command:

```text
python tools/validate_spec.py global_spec.json --json
```

Result after the Factory resolver migration: `PASS`, exit code 0, zero errors
and zero warnings. The canonical validator now applies the shared §13 origin
resolver to ordinary model/enum specs as well as union/interface specs.

The exact machine-readable result is saved as
`spec/canonical_validation_report.json`.

Regression evidence in the Factory covers stdlib-bound types and module-owned
classes for an ordinary model spec. No fake model, interface, union, or product
semantic change was added to Client Portal.

## Readiness

The assembly is coherent; strict Workbench/type checks and canonical Factory
validation are clean. State 9 no-deploy compatibility probing may proceed.
