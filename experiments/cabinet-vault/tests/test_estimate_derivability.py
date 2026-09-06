from __future__ import annotations

from pathlib import Path

from box_composition import compile_composition, execute_composition
from box_derivability import derive_capability_mapping, load_definition


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "experiments" / "cabinet-vault" / "presupro_estimate_box_v0.yaml"
TARGET = ROOT / "experiments" / "cabinet-vault" / "cabinet_estimate_context_box_v0.yaml"


def definitions():
    return load_definition(SOURCE), load_definition(TARGET)


def derive():
    source, target = definitions()
    return derive_capability_mapping(
        source,
        "estimate.observe",
        target,
        "estimate.observation.accept",
    )


def test_estimate_observation_mapping_is_now_fully_derived():
    report = derive()

    assert report.status == "derived"
    assert report.gaps == ()
    assert [step.target_path for step in report.mapping] == [
        "EstimateObservationInput.source_estimate_id",
        "EstimateObservationInput.project_id",
        "EstimateObservationInput.source_updated_at",
        "EstimateObservationInput.status",
        "EstimateObservationInput.locked",
        "EstimateObservationInput.canonical_content",
        "EstimateObservationInput.currency",
    ]
    mapping = {step.target_path: step.source_path for step in report.mapping}
    assert mapping["EstimateObservationInput.currency"] == "PresuProEstimateObservation.currency"


def test_currency_is_declared_as_verified_source_contract_constant():
    source, _ = definitions()
    currency = source["schemas"]["PresuProEstimateObservation"]["fields"]["currency"]

    assert currency["semantic"] == "money.currency"
    assert currency["authority"] == "estimate.source.authority"
    assert currency["source"] == {
        "kind": "contract_constant",
        "contract": "config.app.currency",
        "value": "EUR",
    }


def test_compiled_estimate_composition_passes_only_proven_observation_fields():
    source, target = definitions()
    plan = compile_composition(
        source,
        "estimate.observe",
        target,
        "estimate.observation.accept",
    )
    received: list[dict[str, object]] = []

    def source_invoke(_capability, _args):
        return {
            "estimate_id": "est-17",
            "project_id": "project-4",
            "updated_at": "2026-08-20T18:00:00Z",
            "status": "accepted",
            "locked": False,
            "canonical_content": "{\"id\":\"est-17\"}",
            "currency": "EUR",
            "observed_at": "2026-08-20T18:01:00Z",
            "provider_only_debug_value": "must not cross",
        }

    def target_invoke(capability, args):
        assert capability == "estimate.observation.accept"
        received.append(args)
        return {"accepted": True}

    execution = execute_composition(plan, source_invoke, target_invoke)

    assert execution.result == {"accepted": True}
    assert received == [
        {
            "source_estimate_id": "est-17",
            "project_id": "project-4",
            "source_updated_at": "2026-08-20T18:00:00Z",
            "status": "accepted",
            "locked": False,
            "canonical_content": "{\"id\":\"est-17\"}",
            "currency": "EUR",
        }
    ]


def test_generic_observation_contract_does_not_invent_plan_actual_basis():
    _, target = definitions()

    semantic_surface = str(target["schemas"]) + str(target["capabilities"])
    assert "PresuPro" not in semantic_surface
    assert "monetary_basis" not in target["schemas"]["EstimateObservationInput"]["fields"]
    assert target["external_dependencies"] == []
    assert target["experiment_boundaries"]["currency_inference_allowed"] is False
    assert target["experiment_boundaries"]["plan_actual_monetary_basis_inference_allowed"] is False
