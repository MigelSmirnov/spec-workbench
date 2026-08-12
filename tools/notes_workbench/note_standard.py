from __future__ import annotations

NOTE_CLASSES = frozenset({
    "BEHAVIOR",
    "CONFIG_REFERENCE",
    "MODEL_REFERENCE",
    "RULE_REFERENCE",
    "FORBIDDEN_ACTION",
    "SCHEMA_CONSTRAINT",
    "VALIDATION_ERROR",
    "RETURN_SHAPE",
    "FIELD_ASSIGNMENT",
    "FIELD_PROJECTION",
    "DETERMINISM_OR_ORDERING",
    "PROVENANCE",
    "SECURITY_BOUNDARY",
    "PATH_OR_ARTIFACT_POLICY",
    "DEPENDENCY_BOUNDARY",
    "TEST_EVIDENCE",
    "FALLBACK",
    "ORCHESTRATION",
})

REFERENCE_CLASS_PREFIX = {
    "CONFIG_REFERENCE": "config",
    "MODEL_REFERENCE": "models",
    "RULE_REFERENCE": "rules",
}

# These combinations are not automatically contradictions. They are cheap,
# deterministic signals that two notes on the same address may compete for the
# same behavioral outcome and therefore require author review before handoff.
SUSPICIOUS_CLASS_PAIRS = {
    frozenset({"VALIDATION_ERROR", "FALLBACK"}): "failure_outcome_overlap",
    frozenset({"FORBIDDEN_ACTION", "BEHAVIOR"}): "behavior_prohibition_overlap",
    frozenset({"FORBIDDEN_ACTION", "ORCHESTRATION"}): "orchestration_prohibition_overlap",
}

SINGLETON_CLASSES = frozenset({"RETURN_SHAPE"})
