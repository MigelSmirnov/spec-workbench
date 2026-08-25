from __future__ import annotations

from copy import deepcopy

import pytest

from box_composition import compile_api_parameters, compile_composition, execute_composition
from box_derivability import BoxDerivabilityError, apply_exact_projection, derive_capability_mapping


def source_definition():
    return {
        "schemas": {
            "Empty": {"fields": {}},
            "SourceValue": {
                "fields": {
                    "source_id": {
                        "type": "str",
                        "semantic": "entity.identity",
                        "authority": "source.authority",
                    },
                    "extra": {
                        "type": "str",
                        "semantic": "source.extra",
                        "authority": "source.authority",
                    },
                }
            },
        },
        "capabilities": {
            "source.observe": {"input": "Empty", "output": "SourceValue", "effects": []}
        },
    }


def target_definition():
    return {
        "schemas": {
            "TargetInput": {
                "fields": {
                    "target_id": {
                        "type": "str",
                        "semantic": "entity.identity",
                        "authority": "source.authority",
                        "mapping": "exact",
                    }
                }
            },
            "TargetResult": {"fields": {"accepted": "bool"}},
        },
        "capabilities": {
            "target.accept": {
                "input": "TargetInput",
                "output": "TargetResult",
                "effects": ["write"],
            }
        },
    }


def derive(source=None, target=None):
    return derive_capability_mapping(
        source_definition() if source is None else source,
        "source.observe",
        target_definition() if target is None else target,
        "target.accept",
    )


def test_named_schema_contract_is_required():
    broken = source_definition()
    broken["capabilities"]["source.observe"]["output"] = "MissingSchema"
    with pytest.raises(BoxDerivabilityError, match="unknown schema"):
        derive(broken, target_definition())


def test_target_field_requires_machine_addressable_meaning():
    target = target_definition()
    target["schemas"]["TargetInput"]["fields"]["target_id"].pop("semantic")
    report = derive(source_definition(), target)
    assert report.status == "unresolved"
    assert [gap.code for gap in report.gaps] == ["TARGET_FIELD_NOT_SELF_DESCRIBING"]


def test_field_name_is_not_semantic_evidence():
    source = source_definition()
    fields = source["schemas"]["SourceValue"]["fields"]
    fields["target_id"] = fields.pop("source_id")
    fields["target_id"]["semantic"] = "different.meaning"
    report = derive(source, target_definition())
    assert report.status == "unresolved"
    assert report.gaps[0].code == "SEMANTIC_NOT_DECLARED"


def test_semantic_identity_must_match_exactly():
    source = source_definition()
    source["schemas"]["SourceValue"]["fields"]["source_id"]["semantic"] = "entity.identifier"
    report = derive(source, target_definition())
    assert report.gaps[0].code == "SEMANTIC_SOURCE_NOT_FOUND"


def test_exact_projection_requires_equal_type():
    source = source_definition()
    source["schemas"]["SourceValue"]["fields"]["source_id"]["type"] = "int"
    report = derive(source, target_definition())
    assert report.gaps[0].code == "TYPE_MISMATCH"


def test_required_authority_must_match():
    source = source_definition()
    source["schemas"]["SourceValue"]["fields"]["source_id"]["authority"] = "other.authority"
    report = derive(source, target_definition())
    assert report.gaps[0].code == "AUTHORITY_MISMATCH"


def test_semantic_source_must_be_unambiguous():
    source = source_definition()
    source["schemas"]["SourceValue"]["fields"]["second_id"] = deepcopy(
        source["schemas"]["SourceValue"]["fields"]["source_id"]
    )
    report = derive(source, target_definition())
    assert report.gaps[0].code == "AMBIGUOUS_SEMANTIC_SOURCE"


def test_v0_rejects_undeclared_transformation():
    target = target_definition()
    target["schemas"]["TargetInput"]["fields"]["target_id"]["mapping"] = "normalize"
    report = derive(source_definition(), target)
    assert report.gaps[0].code == "UNSUPPORTED_TRANSFORMATION"


def test_unresolved_derivation_cannot_execute():
    source = source_definition()
    source["schemas"]["SourceValue"]["fields"]["source_id"].pop("semantic")
    report = derive(source, target_definition())
    with pytest.raises(BoxDerivabilityError, match="cannot execute an unresolved mapping"):
        apply_exact_projection(report, {"source_id": "x"})


def test_projection_drops_unrequested_source_fields():
    report = derive()
    projected = apply_exact_projection(report, {"source_id": "x", "extra": "secret-ish"})
    assert projected == {"target_id": "x"}


def test_composition_api_has_no_handwritten_mapping_argument():
    assert compile_api_parameters() == (
        "source_definition",
        "source_capability",
        "target_definition",
        "target_capability",
    )


def _unresolved_plan():
    source = source_definition()
    source["schemas"]["SourceValue"]["fields"]["source_id"].pop("semantic")
    return compile_composition(source, "source.observe", target_definition(), "target.accept")


def test_unresolved_composition_invokes_neither_box():
    plan = _unresolved_plan()
    calls: list[str] = []
    with pytest.raises(BoxDerivabilityError):
        execute_composition(
            plan,
            lambda _cap, _args: calls.append("source") or {},
            lambda _cap, _args: calls.append("target") or {},
        )
    assert calls == []


def test_unresolved_composition_is_non_executable():
    plan = _unresolved_plan()
    assert plan.status == "unresolved"
    with pytest.raises(BoxDerivabilityError, match="cannot execute an unresolved composition"):
        execute_composition(plan, lambda _cap, _args: {}, lambda _cap, _args: {})


def test_derived_composition_executes_declared_three_node_order():
    plan = compile_composition(
        source_definition(), "source.observe", target_definition(), "target.accept"
    )
    calls: list[str] = []
    received: list[dict[str, object]] = []

    def source_invoke(_capability, _args):
        calls.append("source")
        return {"source_id": "abc", "extra": "drop-me"}

    def target_invoke(_capability, args):
        calls.append("target")
        received.append(args)
        return {"accepted": True}

    execution = execute_composition(plan, source_invoke, target_invoke)
    assert calls == ["source", "target"]
    assert received == [{"target_id": "abc"}]
    assert [step["operator"] for step in execution.trace] == [
        "invoke_capability",
        "exact_project",
        "invoke_capability",
    ]


def test_unresolved_composition_has_no_fallback_path():
    plan = _unresolved_plan()
    assert {node.operator for node in plan.nodes} == {"invoke_capability", "exact_project"}
    assert not hasattr(plan, "fallback")
    with pytest.raises(BoxDerivabilityError):
        execute_composition(plan, lambda _cap, _args: {}, lambda _cap, _args: {})
