from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CABINET = ROOT / "examples" / "cabinet-backend"


def _load(name: str) -> dict:
    return json.loads((CABINET / name).read_text(encoding="utf-8"))


def _resolve_config(spec: dict, address: str) -> object:
    parts = address.split(".")
    assert parts[0] == "config"
    value: object = spec["config"]
    for part in parts[1:]:
        assert isinstance(value, dict)
        value = value[part]
    return value


def test_completed_runtime_scope_has_closed_resources_and_bindings() -> None:
    closure = _load("60_runtime_closure_authoring.json")
    spec = _load("global_spec.json")
    resources = closure["runtime_resources"]
    implementations = closure["concrete_implementations"]
    contracts = spec["contracts"]

    assert closure["declaration_policy"]["undeclared_effects_are_errors"] is True
    assert set(closure["completed_scope"]) == {
        "module:access_control", "module:registry_context",
        "module:holded_gateway", "module:bootstrap",
    }
    assert {item["resource"] for item in implementations.values()} == set(resources)

    for resource in resources.values():
        assert spec["models"][resource["interface_model"]]["kind"] == "interface"
        assert resource["startup_optional"] is False
        for method in resource["method_contracts"]:
            assert method in contracts
        for config_ref in resource["required_config_refs"]:
            _resolve_config(spec, config_ref)

    for implementation in implementations.values():
        assert implementation["constructor_contract"] in contracts
        for config_ref in implementation["required_config_refs"]:
            _resolve_config(spec, config_ref)


def test_completed_behavioral_callables_have_effect_dispositions() -> None:
    closure = _load("60_runtime_closure_authoring.json")
    effects = closure["function_dispositions"]
    assert set(effects) == {
        "refresh_registry_context", "validate_card_assignment",
        "get_assignment_validation", "get_work_object",
        "create_holded_purchase", "lookup_holded_purchase",
    }
    for declaration in effects.values():
        assert declaration["disposition"] == "effects"
        assert declaration["resources"]
        for resource in declaration["resources"]:
            assert resource in closure["runtime_resources"]


def test_declared_durable_evidence_is_persistent() -> None:
    closure = _load("60_runtime_closure_authoring.json")
    spec = _load("global_spec.json")
    for model, evidence in closure["durable_evidence"].items():
        assert spec["persistence"][model]["class"] == evidence["persistence_class"]
        assert evidence["producer"] in spec["contracts"]


def test_completed_capabilities_have_one_final_disposition() -> None:
    closure = _load("60_runtime_closure_authoring.json")
    dispositions = closure["capability_dispositions"]
    assert len(dispositions) == len(set(dispositions))
    for item in dispositions.values():
        if item["disposition"] == "contracted":
            assert item["contract"] in _load("global_spec.json")["contracts"]
        else:
            assert item["disposition"] == "removed"
            assert item["decision_ref"] == "A73"


def test_local_linux_graph_closes_access_control_and_keeps_remaining_blockers_explicit() -> None:
    closure = _load("60_runtime_closure_authoring.json")
    bindings = closure["bindings"]
    constructors = _load("global_spec.json")["contracts"]
    for binding in bindings.values():
        assert binding["constructor"] in constructors
        for argument in binding["args"]:
            assert argument["source"] in {"binding", "config"}
            if argument["source"] == "config":
                _resolve_config(_load("global_spec.json"), argument["ref"])
    assert "access_control" in bindings
    assert all(item.get("resource") != "access_control" for item in closure["blockers"])
    assert closure["blockers"]
