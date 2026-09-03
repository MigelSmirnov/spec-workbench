# Hidden-rule audit for the box compiler

## Why this exists

The parent Cabinet Backend Factory run exposed a class of underspecification that is easy to miss:

```text
deterministic compiler knows an architectural rule
but the specification language does not declare that rule
```

That is not successful determinism. It is a hidden-rule gap.

The interface-port ownership incident showed that a specification can pass its normal gates while a deterministic emitter still relies on an architectural invariant known only to its implementation.

The box experiment therefore treats three gap kinds separately:

```text
choice gap
  -> compiler cannot determine one answer

evidence gap
  -> answer may be understandable to a human but is not machine-provable

hidden-rule gap
  -> compiler has deterministic behavior that the declared language does not own
```

## Rule

> Compiler may implement the declared language. Compiler must not silently extend the language.

A deterministic fallback is not an acceptable repair for a failed deterministic precondition unless that fallback itself is explicitly part of the language contract.

## Machine-readable language

`box_language_v0.yaml` declares the current experimental compiler rules.

Each rule has:

- stable rule ID;
- machine-readable statement;
- compiler-tool owner;
- exact conformance-test node ID.

Examples include:

```text
BXL-DERIVE-003  field names are not mapping evidence
BXL-DERIVE-005  v0 exact projection requires exact declared type
BXL-DERIVE-006  required authority must match
BXL-DERIVE-007  semantic source must be unique
BXL-COMPOSE-002 derivability preflight completes before either box is invoked
BXL-COMPOSE-005 unresolved composition has no model/generated-code fallback
```

## Compiler binding

`experiments/cabinet-vault/tools/box_derivability.py` and `experiments/cabinet-vault/tools/box_composition.py` export their implemented rule IDs.

Their result artifacts also carry the applied rule IDs:

```text
DerivationReport.language_rules
CompositionPlan.language_rules
```

A proof is therefore explicit about the language rules under which it was produced.

## Audit gate

Run:

```bash
python experiments/cabinet-vault/tools/box_language_audit.py
```

or:

```bash
python experiments/cabinet-vault/tools/box_language_audit.py --json
```

The audit blocks when:

- compiler declares a rule absent from its language binding;
- language binding requires a rule absent from compiler declaration;
- a rule has no compiler owner;
- a rule has no conformance test;
- the named conformance-test function does not exist;
- a compiler source file differs from the reviewed blob fingerprint stored in the language binding.

The fingerprint rule is deliberate. Any compiler-code change forces an explicit language review before the gate can pass again. This catches a future deterministic rule added directly to Python even when the author forgets to add a new rule ID.

## Mandatory change discipline

Treat `python experiments/cabinet-vault/tools/box_language_audit.py` as a required gate before accepting any change to the box compiler or composition runtime.

A compiler fingerprint drift is not repaired by refreshing the fingerprint alone. Review the code change first and determine whether it:

1. implements an already-declared language rule without changing observable semantics; or
2. introduces or changes an architectural rule, in which case the language contract and its conformance case must change together.

If deterministic compilation was expected but its declared preconditions fail, fail closed and report the reason. Do not silently switch to model generation, generated code, a heuristic adapter, or another compilation mode.

## Conformance suite

`tests/test_box_language_conformance.py` exercises the observable behavior of every declared v0 rule.

It proves, among other things, that:

- named schemas are required;
- target meaning must be machine-addressable;
- field names are not semantic evidence;
- semantic identity, type, and required authority are exact in v0;
- ambiguity fails closed;
- undeclared transformations fail closed;
- unresolved derivations and compositions cannot execute;
- exact projection drops unrelated source fields;
- composition accepts no hand-written mapping argument;
- preflight completes before invoking either box;
- unresolved composition has no model/generated-code fallback.

`tests/test_box_language_audit.py` then adversarially proves that an unknown implementation rule, a missing implementation rule, or an unreviewed compiler source change blocks the language audit.

## What this does not claim

A source fingerprint is not semantic proof by itself. A reviewer could update a fingerprint without correctly updating language rules.

The intended protection is the combination:

```text
machine-readable rule IDs
+ rule/tool ownership
+ executable conformance cases
+ compiler source fingerprint
+ fail-closed audit
```

This makes hidden deterministic architecture visible and reviewable. It does not replace semantic review of a language change.

## Relationship to derivability

The derivability detector now distinguishes two different responsibilities:

```text
box manifests
  -> declare domain meaning and authority

box language
  -> declares universal compiler rules for proving compatibility

compiler
  -> implements those declared rules only
```

Domain decisions such as choosing Invoice Card V1 `net_amount` versus `gross_amount` still belong to the product specification. They must not migrate into `box_derivability.py` merely because a deterministic choice would be easy to code.

## Validated test evidence

Validated in a clean real checkout after synchronization to commit `5aed452` on 2026-08-20.

Main current experiment suite:

```text
53 passed, 1 warning in 1.11s
```

Built-in adversarial mutation/audit cases:

```text
3 passed, 1 warning in 0.32s
```

CLI audit result:

```json
{
  "status": "pass",
  "checked_tools": ["box_composition", "box_derivability"],
  "checked_rules": 15,
  "findings": []
}
```

The warnings were only inability to write `.pytest_cache` in a read-only checkout and did not affect test results. No external mutation framework such as `mutmut` is configured; the repository's built-in adversarial mutation gate was used.

This is real local-run evidence, not GitHub Actions CI evidence.
