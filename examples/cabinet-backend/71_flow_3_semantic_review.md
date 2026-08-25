# Cabinet Backend — Stage 7.1 Flow 3 semantic review

Flow: `flow:refresh_registry_and_validate_assignment`

Status: **semantic_closed**

## Reconstructed accepted behavior

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

Registry remains read-only from Cabinet. Absence from one later full poll is not deletion evidence. Validation evidence may change while the Card assignment remains immutable.

## Original finding

The initial compressed State 5/7 wording allowed an implementation to return `inconclusive` or another review-required result for every assignment, including exact current active matches. That materially contradicted accepted State 2 A34 semantics, where Registry `active` means available for normal automatic assignment.

## Repair applied

The bounded repairs in `50_public_apis_flow3_semantic_repair.md` and `80_notes_flow3_semantic_repair.md` now require:

- exact current active project match with no material conflict → `ObjectAssignmentValidation.result = "valid"`;
- archived or missing current project → truthful non-valid review-required evidence;
- archived is never reinterpreted as authoritative completion or `late_project_cost`;
- unusable Registry context → `RegistryContextUnavailableError` rather than guessed classification;
- validation evidence remains separate from and cannot rewrite the immutable Card assignment;
- `get_assignment_validation` returns recorded evidence only and raises `AssignmentValidationNotFoundError` when none exists.

No contract or model change was required.

## Rerun of semantic scenarios

### R1 — refresh is one-way and preserves Cabinet-owned state

**PASS.** Registry-derived fields refresh by stable `project_id`; Cabinet-owned fields remain preserved and no Registry write-back is permitted.

### R2 — absence from later Registry response does not imply deletion

**PASS.** Existing WorkObjects absent from a later accepted full observation remain preserved; absence alone cannot delete or mark them completed.

### R3 — changed Registry evidence cannot rewrite Card assignment

**PASS.** Active exact matches validate; archived/missing/changed evidence may change review classification, but the immutable Card assignment is unchanged.

### R4 — missing validation is not guessed from current Registry state

**PASS.** `get_assignment_validation` is a read of recorded evidence and raises `AssignmentValidationNotFoundError` when no accepted evidence exists.

## Adversarial ambiguity rerun

Question: can a materially different implementation keep every resolvable exact active assignment permanently `inconclusive` while satisfying the repaired slice?

**No.** That would violate the explicit active-match classification requirement.

Remaining choices such as persistence indexing, refresh implementation, and the exact existing non-valid result used for truthful archived/missing evidence are internal variations as long as the observable review semantics remain preserved.

Classification: **PASS_INTERNAL_VARIATION**.

## Placeholder resistance rerun

- universal `inconclusive` → fails repaired notes;
- empty/default validation → fails exact evidence and classification requirements;
- rewriting the Card to match current Registry → fails immutability boundary;
- deleting absent WorkObjects → fails refresh semantics;
- synthesizing a read result in `get_assignment_validation` → fails recorded-evidence rule.

Result: **PASS**.

## Final gate

```text
flow: flow:refresh_registry_and_validate_assignment
status: semantic_closed
material_alternative_found: no
placeholder_implementation_found: no
scenario_gaps: []
```

`semantic_closed`: **yes**
