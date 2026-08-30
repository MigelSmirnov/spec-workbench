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
