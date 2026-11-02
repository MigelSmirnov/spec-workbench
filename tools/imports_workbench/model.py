from __future__ import annotations

TABLE_SCHEMA = "spec_workbench_imports.v1"
REPORT_SCHEMA = "spec_workbench_imports_report.v1"
TABLE_FILE = "65_imports.json"
TARGET_FILE = "90_factory_target.json"
# The Factory emits the models module deterministically; it imports nothing of the project.
MODELS_MODULE = "models"

# How a scope uses a symbol (IMPORTS_WORKBENCH.md §3).
USES_AS = ("creates", "inspects", "calls", "reads", "annotates")

# Candidate sources (§5) and their strength.
STRUCTURAL = "structural"
STRONG = "strong"
WEAK = "weak"
EVIDENCE = "evidence"
CANDIDATE_STRENGTH = {
    "contract": STRUCTURAL,
    "note_mention": STRONG,
    "note_call": STRONG,
    "field_name": WEAK,
    "variant": WEAK,
    "code_used": EVIDENCE,
}
KNOWS = "knows"

# Coverage of the code evidence (§8).
AVAILABLE = "available"
UNAVAILABLE = "unavailable"
NOT_APPLICABLE = "not_applicable"

FINDING_MESSAGES = {
    "imports_table_missing": "65_imports.json is missing: run design_imports.py <case> --draft and decide every candidate",
    "imports_table_invalid": "65_imports.json does not have the imports table shape",
    "imports_scope_missing": "a contract (or the module itself) has no scope in the table",
    "imports_scope_unknown": "the table has a scope the design does not have",
    "imports_candidate_undecided": "a candidate is neither in uses nor in rejected",
    "imports_scope_stale": "the contract or notes of the scope changed after it was decided",
    "imports_symbol_unknown": "the symbol is not an export of any module of the specification",
    "imports_provider_wrong": "the symbol is not an export of the named provider",
    "imports_edge_forbidden": "the import goes against the module order of State 3 (a provider must come earlier) or names the module itself",
    "imports_use_invalid": "a use row needs symbol, provider, an `as` from the closed set and a basis",
    "imports_basis_invalid": "the basis names a note that is not a note of this scope, or has an unknown form",
    "imports_rejection_without_reason": "a rejection needs a reason",
    "imports_weak_without_basis": "a weak candidate (field name, union variant) is accepted only on a note clause of the scope or on the code",
    "imports_knows_uncovered": "a module from State 3 Knows gave no symbol to the module and its edge is not rejected",
    "imports_code_undeclared": "the module's code names a project symbol that is neither in uses nor rejected",
    "imports_code_unused": "the symbol is in uses but the module's code does not name it; record code_outdated with a reason if the code lags the specification",
    "imports_factory_unavailable": "the case has a Factory target, but the Factory or its report is unavailable",
}


class ImportsError(Exception):
    """The case cannot be read for the imports closure."""
