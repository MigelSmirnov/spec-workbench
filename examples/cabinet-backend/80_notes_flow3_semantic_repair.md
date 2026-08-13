# State 7 bounded repair — Flow 3 Registry assignment validation notes

This file refines `80_notes.md` for the Stage 7.1 Flow 3 repair. The contract and result models are unchanged.

# registry_context

validate_card_assignment: [RULE_REFERENCE] An exact current active project match with no material conflict must use the accepted positive result from = rules.registry_context.active_exact_match_result.
validate_card_assignment: [RULE_REFERENCE] An archived current project must remain review-required according to = rules.registry_context.archived_requires_review.
validate_card_assignment: [RULE_REFERENCE] Missing current project evidence must remain review-required according to = rules.registry_context.missing_requires_review.
validate_card_assignment: [RULE_REFERENCE] Archived Registry status must not be reinterpreted as completion; use = rules.registry_context.archived_means_completed.
validate_card_assignment: [BEHAVIOR] Do not use inconclusive or another review result as a universal fallback when accepted current Registry evidence deterministically establishes an exact active project match.
validate_card_assignment: [BEHAVIOR] Preserve the exact immutable Card assignment while recording current validation evidence separately; a later Registry observation may change validation evidence but never rewrite the Card object block.
validate_card_assignment: [VALIDATION_ERROR] Raise RegistryContextUnavailableError when current Registry context cannot be resolved or accepted safely enough to classify the assignment; do not fabricate a current project or positive validation.

refresh_registry_context: [BEHAVIOR] A complete refresh updates Registry-derived fields by stable project_id, preserves Cabinet-owned WorkObject fields, and does not delete or complete an existing WorkObject merely because the project is absent from a later observation.
get_assignment_validation: [BEHAVIOR] Return only recorded validation evidence for the exact Card revision and raise AssignmentValidationNotFoundError when none exists; do not synthesize validation from current Registry state on a read.
