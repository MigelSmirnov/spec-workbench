"""The fence: the workbench has no warnings and accepts no waivers.

A finding that is not an error is an undecided fact wearing a softer label.
The case does not proceed on undecided facts; every such finding stops the
case and tells the author what to decide. This module is the single place
where that policy lives: every report passes its findings through
``enforce`` before it counts them, so a tool cannot leave a warning behind.

    not decided -> decide.
"""
from __future__ import annotations

from typing import Any

SOFT_SEVERITIES = frozenset({"warning", "review", "warn", "advisory"})
STOP = "error"

HINTS: dict[str, str] = {
    "opaque_runtime_carrier": "give the carrier an interface with the typed operations its consumers need and record who implements it in implementation_obligations",
    "unreachable_repository": "name the interface the lowered repository implements (implementation_obligations, disposition local) or the contract that receives it",
    "module_surface_not_deep": "declare the hidden mechanism this module owns in State 3, or split it along the mechanism it hides",
    "contract_plan_open": "review the internal functions the mechanisms need and close the State 6 plan",
    "deep_module_declares_delegates": "a deep module owns its mechanism: remove the delegation or declare the module a facade",
    "facade_claims_hidden_mechanism": "a facade hides nothing: remove the mechanism claim or declare the module deep",
    "unplanned_flow": "declare the flow in the State 4 plan or remove it",
    "unplanned_public_op": "declare the operation in the State 5 plan or remove it",
    "owner_repeated_as_consumer": "a decision has one owner: remove the owner from its own consumer list",
    "decision_without_witness": "name the accepted decision that owns this fact, or record a new decision with an owner in State 2",
    "witness_unverifiable": "give the decision a verifiable witness: a check, a test, or a contract that carries the value",
    "interface_without_provider": "declare the provider class in the State 6 plan (the finding lists the entries) or return the port from a declared provider",
    "flow_capability_missing": "the flow names an operation the design does not declare: plan and contract it, or rewrite the flow step",
    "flow_capability_unreached": "the flow step is not wired: a route delegate or a note of the calling module must name this operation",
    "waiver_not_accepted": "a waiver is a decision nobody made: record the decision in State 2 and carry it in a contract, then delete the waiver",
    "review_not_passed": "read the module slice and record PASS, or split the mechanism that may vary",
    "instant_without_source": "say where the instant comes from: name the wall-clock accessor in the note of this function, or declare the source (clock, argument, stored, callee) in 70_value_flow_closure.json",
    "argument_without_sink": "say what the argument becomes: add the field to the constructed model, or declare the sink (field, derived, key, guard, forwarded) in 70_value_flow_closure.json",
    "known_collaborator_unreachable": "name the collaborator's operation in a note of this module so the module receives it, or remove the collaborator from State 3 Knows",
    "value_flow_lens_judged_nothing": "give the lens what it judges: declare rules.time_source_policy with its representation, and name the modules a module calls in backticks under State 3 Knows",
    "state1_fact_without_carrier": "the model closure is the one field list: give the fact a field of that name in the closure, or correct State 1 if the concept does not carry it",
    "named_field_without_carrier": "name the field the model closure declares, or add the field to the closure before a rule, flow or operation relies on it",
    "state1_model_without_named_facts": "say in State 1 which facts the concept carries (identity, status, relations, written-once facts) so the closure is checked against something",
    "declared_clock_not_named": "a clock the note does not name is not handed to the module: name the wall-clock accessor in the note of this function",
    "declared_callee_not_named": "name the callee in a note of the calling module so the module receives it",
    "declared_sink_unknown": "the declared sink does not exist in the design: add the model field or contract first, then declare it",
    "imports_candidate_undecided": "accept the symbol into the scope's uses with how it is used and why (basis), or reject it with a reason (65_imports.json)",
    "imports_scope_missing": "run design_imports.py <case> --draft and decide the new scope's candidates",
    "imports_scope_stale": "the contract or notes changed: re-read the scope's candidates, then record the new basis_sha256",
    "imports_weak_without_basis": "cite the note clause (note:<scope>#<n>) or the code (basis code) that makes the module use this type",
    "imports_knows_uncovered": "accept the symbol the module takes from this State 3 collaborator, or reject the edge (symbol *, candidate knows) with a reason",
    "imports_code_undeclared": "the accepted code names this symbol: accept it into the scope that uses it, or reject it with a reason if the new specification drops it",
    "imports_code_unused": "drop the use, or record code_outdated with the reason the code lags the specification",
    "imports_projection_drift": "do not edit imports.module_internal by hand: change the decision in 65_imports.json and run tools/design_spec_projection.py <case> --apply",
    "imports_factory_unavailable": "make the Factory reachable (--factory-root or SPEC_WORKBENCH_FACTORY_ROOT) with a slicer report that has --code-root",
    "fresh_timestamp_without_source": "name the time source State 2 decided in the contract: a datetime parameter, a clock port retained by __init__, or a declared time_source_policy authority; if the accepted design reads the clock in a form the standard cannot express, cite the gap (KNOWN_GAPS.md KG-002) instead of changing the service",
    "ambient_time_note": "the note needs the current time: give the function the source State 2 decided (a datetime parameter or the module's clock port); if the standard has no form for it, cite the gap (KNOWN_GAPS.md KG-002) instead of changing the service",
    "model_closure_absent": "write 60_model_closure_*.json: one record per State 1 model with its identity, and a contract_only file for the runtime models the contracts introduce",
    "invariant_without_required_test": "say in Required tests what must be shown for this invariant, naming it by its identifier",
    "invariant_without_witness": "bind the invariant to an existing check that asserts it ([witness: ...] on the Required tests line naming it), or keep it carried and say which check will be written",
    "witness_binding_ambiguous": "name, in the Required tests item that carries the tag, the invariants its check asserts",
    "witness_material_not_checked": "make the bound check's content readable (SPEC_WORKBENCH_FACTORY_ROOT, a command that names its files, at most the size a round is given whole) so the round can judge it, or remove the binding and carry it",
    "flow_reachability_not_checked": "assemble the router (design_spec_projection.py --apply) or close the router closure so the routes the flows start from can be read",
    "table_access_unnamed": "a note naming a record table names its access: spell the match in the row model's field vocabulary, or name the contract that owns it (NOTE_GATE.md 'Table access must be named')",
}


def hint_for(code: str | None, message: str | None) -> str:
    known = HINTS.get(code or "")
    if known:
        return f"not decided — decide: {known}"
    return f"not decided — decide: {message or code or 'this finding'}"


def enforce(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return the findings with every soft severity raised to a stop and a hint on each."""
    fenced: list[dict[str, Any]] = []
    for item in findings:
        if not isinstance(item, dict):
            fenced.append(item)
            continue
        severity = str(item.get("severity") or "").lower()
        raised = dict(item)
        if severity in SOFT_SEVERITIES:
            raised["severity"] = STOP
            raised["raised_from"] = severity
        if raised.get("severity") in {STOP, "block"} and "hint" not in raised:
            raised["hint"] = hint_for(raised.get("code"), raised.get("message"))
        fenced.append(raised)
    return fenced


def stops(findings: list[dict[str, Any]]) -> int:
    return sum(1 for item in findings if isinstance(item, dict) and item.get("severity") in {STOP, "block"})
