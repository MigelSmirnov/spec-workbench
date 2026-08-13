# Cabinet Backend — Stage 7.1 Flow 3 semantic review

Flow: `flow:refresh_registry_and_validate_assignment`

Status: **AMBIGUITY — repair required**

## Reconstructed accepted behavior

The accepted State 2/4 semantics are:

```text
complete Registry observation
        ↓
refresh Registry-derived projection by stable project_id
        ↓
preserve Cabinet-owned WorkObject state and objects absent from the observation
        ↓
validate exact immutable Card assignment against current Registry evidence
        ├─ exact current active project match → valid
        ├─ archived/unavailable/missing project → review-required non-valid evidence
        └─ unusable Registry context → RegistryContextUnavailableError
        ↓
record validation separately from immutable Card assignment
```

Registry is read-only from Cabinet. Absence from one later full poll is not deletion evidence. Validation evidence may change; the Card assignment may not.

## Adversarial ambiguity

### Interpretation A — active exact match validates

When the exact project referenced by the immutable Card revision exists in the accepted current Registry observation with status `active`, and no material identity/context conflict is present, `validate_card_assignment` emits `ObjectAssignmentValidation.result = "valid"`. Archived or absent projects produce non-valid review evidence.

### Interpretation B — unconditional review

`validate_card_assignment` always emits `inconclusive` or another review-required result, including for exact active project matches. It never rewrites the Card, never invents deletion, and therefore still satisfies the current State 5/7 wording that validation may produce explicit review-required evidence.

Interpretation B loses accepted A34 semantics: Registry `active` means available for normal automatic project assignment.

## Material difference

With an exact immutable Card assignment to project `P1` and a current accepted Registry observation containing `P1` as `active`, Interpretation A removes unnecessary review by producing `valid`; Interpretation B leaves the assignment perpetually review-required. This changes downstream observability and eligibility and is not implementation variation.

## Placeholder resistance

Status: **PLACEHOLDER_RISK** for `validate_card_assignment`.

An implementation that returns `inconclusive` for every resolvable assignment is a semantic skeleton that can satisfy the current compressed operation/notes while failing the accepted State 2 classification.

## Finding

```text
flow: flow:refresh_registry_and_validate_assignment
status: AMBIGUITY
material_alternative_found: yes
placeholder_implementation_found: yes
scenario_gaps:
  - R1 and R2 are derivable from refresh semantics.
  - R3 preserves Card immutability but does not force the accepted active/archived/missing classification.
  - R4 is already explicit for missing recorded validation evidence.
findings:
  - owner: structure
    scope: State 5 validation output semantics propagated to State 7 notes
    interpretation_A: exact current active project match produces valid assignment evidence
    interpretation_B: every assignment may remain review-required/inconclusive
    required_resolution: bind validation classification to accepted A34 Registry semantics without changing Registry or Card truth
```

## Earliest repair owner

State 2 A34 is already explicit and State 1 has a sufficient result vocabulary. Repair State 5 first and propagate the deterministic classification obligation to State 7 Notes.

`semantic_closed`: **no**, pending repair and rerun.
