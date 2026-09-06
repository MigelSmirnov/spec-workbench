"""Closed registry of obligation types and precedence classes.

The type of an obligation — not the text of the check that raised it — decides
how the scheduler treats it.  A check may add codes freely; every code must map
here, and a code that maps nowhere becomes an ``unclassified_finding``
addressed to this registry, so a growing tail of string diagnostics is itself
an obligation and not a silent drift.

Precedence classes:

- ``defining``       — the node's own definition is undecided; dependents that
                       reference it through a definitional edge are BLOCKED.
- ``convergence``    — the node is defined; the system around it has not
                       converged (unreached, unwitnessed, undesigned edge).
                       Never blocks another node.
- ``implementation`` — a deterministic closure (router, persistence, binding)
                       cannot be proven yet.  Never blocks design nodes.
- ``derived_cost``   — informational: what closing a node will cost elsewhere.
"""
from __future__ import annotations

from dataclasses import dataclass

PRECEDENCE: tuple[str, ...] = ("defining", "convergence", "implementation", "derived_cost")


@dataclass(frozen=True)
class ObligationType:
    code: str
    precedence: str
    addressed_kinds: tuple[str, ...]
    hint: str
    derived_by: str  # "check:<name>" for deterministic-report findings, "projection" for graph-derived

    def __post_init__(self) -> None:
        if self.precedence not in PRECEDENCE:
            raise ValueError(f"{self.code}: unknown precedence class {self.precedence!r}")


def _t(code: str, precedence: str, kinds: str, hint: str, derived_by: str) -> ObligationType:
    return ObligationType(code, precedence, tuple(kinds.split()), hint, derived_by)


TYPES: dict[str, ObligationType] = {
    t.code: t
    for t in (
        # ---- defining ------------------------------------------------------------
        _t("module_cut_undecided", "defining", "module",
           "decide the State 3 cut: sections, hidden mechanism, capability names", "check:modules"),
        _t("decision_without_owner", "defining", "decision",
           "assign the primary owner module, or record a disposition with its reason, in 30_trace.json", "projection"),
        _t("model_without_design_source", "defining", "model interface",
           "declare in State 1 and 60_model_closure_*.json; it lives only in global_spec.json", "projection"),
        _t("model_identity_unresolved", "defining", "model interface",
           "decide value/entity identity consistently across State 1, closure and assembly", "check:identity"),
        _t("contract_type_without_model", "defining", "contract",
           "the signature names a type that is not a closed model or interface", "projection"),
        _t("interface_without_provider", "defining", "contract module",
           "plan the provider class and its operations under the owning module", "check:contracts"),
        _t("flow_capability_missing", "defining", "flow",
           "the flow names a capability no module declares", "check:flows"),
        _t("data_placement_undecided", "defining", "model",
           "decide the storage placement of the leaf address", "check:data"),
        # ---- convergence ---------------------------------------------------------
        _t("decision_without_witness", "convergence", "decision",
           "tag a required test with [witness: verification:<name>] or [witness: note:<scope>]", "check:witness"),
        _t("capability_unreachable", "convergence", "module boundary",
           "make the capability reachable from its designed caller: a route, or a call the notes oblige", "check:flows"),
        _t("boundary_without_ingress", "convergence", "boundary",
           "no route carries the public operation this boundary is designed to call", "projection"),
        _t("ingress_without_designed_caller", "convergence", "boundary",
           "a route serves an operation whose State 5 callers do not include this boundary", "projection"),
        _t("outcome_without_flow", "convergence", "outcome",
           "no flow's Outcomes section proves this State 0 observable outcome", "projection"),
        _t("dependency_not_designed", "convergence", "module",
           "the factory infers a module dependency the architecture never declared: declare it or move the symbol", "projection"),
        _t("public_op_undecided", "convergence", "public_op",
           "the public operation lacks flow evidence, a caller or a matching capability", "check:contracts"),
        _t("timestamp_without_time_source", "convergence", "contract",
           "a mutating operation produces a timestamp with no declared time source", "check:contracts"),
        _t("contract_undecided", "convergence", "contract function",
           "the contract plan or signature is not decided", "check:contracts"),
        _t("external_contract_undecided", "convergence", "contract",
           "external contract evidence is missing or stale", "check:external_contracts"),
        _t("language_undecided", "convergence", "note",
           "a note or rule carries undecided language", "check:language"),
        _t("notes_undecided", "convergence", "function",
           "a contract scope lacks a note or its note fails the gate", "check:notes"),
        # ---- implementation ------------------------------------------------------
        _t("router_closure_unproven", "implementation", "public_op",
           "the router closure cannot be proven for this operation yet", "check:router"),
        _t("persistence_closure_unproven", "implementation", "module",
           "the persistence closure cannot be proven yet", "check:persistence"),
        # ---- derived cost --------------------------------------------------------
        _t("model_closure_radius", "derived_cost", "model interface",
           "contracts in N modules reference this model; closing it regenerates them", "projection"),
        # ---- registry -----------------------------------------------------------
        _t("unclassified_finding", "convergence", "registry",
           "a deterministic report raised a code this registry does not map: classify it", "projection"),
    )
}

# Deterministic-report finding codes → obligation type.  Many-to-one on purpose.
FINDING_MAP: dict[str, str] = {
    # modules (State 3 lint)
    "missing_hides_section": "module_cut_undecided",
    "missing_capabilities": "module_cut_undecided",
    "missing_module_section": "module_cut_undecided",
    "depth_undeclared": "module_cut_undecided",
    "depth_undeclared_wide_surface": "module_cut_undecided",
    "duplicate_module_key": "module_cut_undecided",
    "unknown_module_ref": "module_cut_undecided",
    # witness / flows
    "decision_without_witness": "decision_without_witness",
    "witness_unresolved": "decision_without_witness",
    "flow_capability_unreached": "capability_unreachable",
    "flow_capability_missing": "flow_capability_missing",
    # contracts (State 6)
    "interface_without_provider": "interface_without_provider",
    "fresh_timestamp_without_source": "timestamp_without_time_source",
    # persistence
    "codec_registry_unavailable": "persistence_closure_unproven",
}

# A finding whose code is not in FINDING_MAP falls back by the check that raised it.
CHECK_FALLBACK: dict[str, str] = {
    "modules": "module_cut_undecided",
    "identity": "model_identity_unresolved",
    "data": "data_placement_undecided",
    "contracts": "contract_undecided",
    "external_contracts": "external_contract_undecided",
    "language": "language_undecided",
    "notes": "notes_undecided",
    "router": "router_closure_unproven",
    "persistence": "persistence_closure_unproven",
    "witness": "decision_without_witness",
    "flows": "capability_unreachable",
}


def classify(check: str, finding_code: str) -> ObligationType:
    """Map a deterministic-report finding to its obligation type; never raises."""
    code = FINDING_MAP.get(finding_code) or CHECK_FALLBACK.get(check) or "unclassified_finding"
    return TYPES[code]


def blocks(obligation_type: ObligationType) -> bool:
    return obligation_type.precedence == "defining"
