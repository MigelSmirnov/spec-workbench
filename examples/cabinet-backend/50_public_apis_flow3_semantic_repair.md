# State 5 bounded repair — Flow 3 Registry assignment classification

This bounded repair restores accepted State 2 A34 semantics lost during compression into the State 5 public API. It introduces no new Registry status and does not change the `validate_card_assignment` contract.

## Superseded — `public_op:registry_context.validate_card_assignment` refinement

For an exact immutable Card revision and an accepted current Registry context:

- when the Card's referenced `project_id` resolves to the same current Registry project and that project is `active`, with no material identity/context conflict, the operation **must** return validation evidence with `result = "valid"`;
- when the referenced project is `archived`, the operation must return a non-valid review-required validation result and must not reinterpret `archived` as authoritative project completion or `late_project_cost`;
- when the referenced `project_id` is absent from the accepted current Registry observation, the operation must return a non-valid review-required validation result; absence does not authorize deletion or Card reassignment;
- when current Registry context cannot be accepted safely enough to classify the assignment, raise `RegistryContextUnavailableError` rather than fabricating `valid` or a synthetic current project;
- every validation record remains separate evidence for the exact immutable Card revision and never rewrites its object block.

The exact non-valid result among the existing `ObjectAssignmentValidation` vocabulary may reflect the observed reason (`project_missing`, `project_closed`/unavailable, `materially_changed`, or `inconclusive`) as long as it truthfully preserves the accepted Registry evidence. The implementation may not use `inconclusive` as a universal fallback when the accepted evidence deterministically establishes an exact active match.
