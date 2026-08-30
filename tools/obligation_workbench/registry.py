from __future__ import annotations

from dataclasses import dataclass


PRECEDENCE = ("defining", "convergence", "implementation", "diagnostic")


@dataclass(frozen=True)
class ObligationRule:
    kind: str
    precedence_class: str
    resolution_owner: str
    category: str = "engineering"

    def __post_init__(self) -> None:
        if self.precedence_class not in PRECEDENCE:
            raise ValueError(f"{self.kind}: unsupported precedence {self.precedence_class!r}")


def _rule(kind: str, precedence: str, owner: str, category: str = "engineering") -> ObligationRule:
    return ObligationRule(kind, precedence, owner, category)


RULES = {
    item.kind: item
    for item in (
        _rule("module_cut_undecided", "defining", "state3:modules"),
        _rule("decision_without_owner", "defining", "state3:trace"),
        _rule("model_without_design_source", "defining", "state1:models"),
        _rule("model_identity_unresolved", "defining", "state1:models"),
        _rule("interface_without_provider", "defining", "state6:implementation_obligations"),
        _rule("contract_type_without_model", "defining", "state1:models"),
        _rule("flow_capability_missing", "defining", "state3:modules"),
        _rule("data_placement_undecided", "defining", "pre_contract:data_closure"),
        _rule("duplicate_semantic_ownership", "defining", "canonical_semantic_owner"),
        _rule("cross_call_identity_undefined", "defining", "state6:contracts"),
        _rule("derived_identifier_semantics_undefined", "defining", "state1:models"),
        _rule("downstream_semantic_conflict", "defining", "downstream_expression"),
        _rule("protocol_assumption_not_backed_by_contract", "defining", "state6:contracts"),
        _rule("decision_without_witness", "convergence", "state2:decisions"),
        _rule("capability_unreachable", "convergence", "state5:public_operations"),
        _rule("boundary_without_ingress", "convergence", "state5:public_operations"),
        _rule("route_without_designed_boundary", "convergence", "state5:public_operations"),
        _rule("boundary_auth_principal_unresolved", "convergence", "router_context"),
        _rule("boundary_input_contract_missing", "convergence", "state6:contracts"),
        _rule("boundary_error_contract_missing", "convergence", "router_context"),
        _rule("outcome_without_flow", "convergence", "state4:flows"),
        _rule("outcome_flow_mapping_unresolved", "convergence", "state4:flows"),
        _rule("flow_not_planned", "convergence", "state4:flows"),
        _rule("dependency_not_designed", "convergence", "state3:modules"),
        _rule("runtime_config_binding_missing", "convergence", "composition:runtime_config"),
        _rule("public_op_undecided", "convergence", "state5:public_operations"),
        _rule("fresh_timestamp_without_source", "convergence", "state6:contracts"),
        _rule("contract_undecided", "convergence", "state6:contracts"),
        _rule("external_contract_undecided", "convergence", "state6:contracts"),
        _rule("language_undecided", "convergence", "state7:notes"),
        _rule("notes_undecided", "convergence", "state7:notes"),
        _rule("router_closure_unproven", "implementation", "router_closure"),
        _rule("persistence_closure_unproven", "implementation", "persistence_closure"),
        _rule("production_entrypoint_not_exercised", "implementation", "verification:deployment_topology"),
        _rule("structured_lowering_candidate", "diagnostic", "tool:lowering_advisory", "tool"),
        _rule("codec_registry_unavailable", "diagnostic", "tool:persistence_backend_registry", "tool"),
        _rule("unclassified_finding", "diagnostic", "tool:obligation_registry", "tool"),
    )
}


FINDING_MAP = {
    "missing_hides_section": "module_cut_undecided",
    "missing_capabilities": "module_cut_undecided",
    "missing_module_section": "module_cut_undecided",
    "depth_undeclared": "module_cut_undecided",
    "depth_undeclared_wide_surface": "module_cut_undecided",
    "duplicate_module_key": "module_cut_undecided",
    "unknown_module_ref": "module_cut_undecided",
    "module_surface_not_deep": "module_cut_undecided",
    "missing_state1_model": "model_without_design_source",
    "state1_identity_mismatch": "model_identity_unresolved",
    "missing_model_closure": "model_identity_unresolved",
    "closure_identity_mismatch": "model_identity_unresolved",
    "invalid_state1_identity": "model_identity_unresolved",
    "invalid_closure_identity": "model_identity_unresolved",
    "invalid_assembled_identity": "model_identity_unresolved",
    "flow_capability_unreached": "capability_unreachable",
    "flow_capability_missing": "flow_capability_missing",
    "unknown_capability_ref": "flow_capability_missing",
    "unplanned_flow": "flow_not_planned",
    "interface_without_provider": "interface_without_provider",
    "fresh_timestamp_without_source": "fresh_timestamp_without_source",
    "codec_registry_unavailable": "codec_registry_unavailable",
    "missing_external_operation": "boundary_without_ingress",
    "missing_operation_contract": "boundary_input_contract_missing",
    "missing_handler_contract": "boundary_input_contract_missing",
    "handler_contract_mismatch": "boundary_input_contract_missing",
    "unknown_handler_path_parameter": "boundary_input_contract_missing",
    "unknown_handler_parameter_ref": "boundary_input_contract_missing",
    "missing_credential_extractors": "boundary_auth_principal_unresolved",
    "invalid_credential_extractor": "boundary_auth_principal_unresolved",
    "unknown_extractor_function": "boundary_auth_principal_unresolved",
    "unresolved_extractor_header": "boundary_auth_principal_unresolved",
    "unresolved_extractor_exception": "boundary_auth_principal_unresolved",
    "invalid_principals": "boundary_auth_principal_unresolved",
    "unknown_principal_resolver": "boundary_auth_principal_unresolved",
    "invalid_auth_policies": "boundary_auth_principal_unresolved",
    "unknown_auth_policy_principal": "boundary_auth_principal_unresolved",
    "unknown_route_auth_policy": "boundary_auth_principal_unresolved",
    "invalid_error_policy": "boundary_error_contract_missing",
    "invalid_error_body": "boundary_error_contract_missing",
    "missing_error_mapping": "boundary_error_contract_missing",
}


REPORT_FALLBACK = {
    "data": "data_placement_undecided",
    "contracts": "contract_undecided",
    "external_contracts": "external_contract_undecided",
    "language": "language_undecided",
    "notes": "notes_undecided",
    "router": "router_closure_unproven",
    "router_context": "router_closure_unproven",
    "persistence": "persistence_closure_unproven",
}


def classify(report: str, code: str) -> ObligationRule:
    kind = FINDING_MAP.get(code) or REPORT_FALLBACK.get(report) or "unclassified_finding"
    return RULES[kind]


def is_defining(kind: str) -> bool:
    return RULES[kind].precedence_class == "defining"
