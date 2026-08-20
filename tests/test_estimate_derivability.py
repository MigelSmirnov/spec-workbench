from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from box_composition import compile_composition, execute_composition
from box_derivability import BoxDerivabilityError, derive_capability_mapping, load_definition


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "experiments" / "cabinet-vault" / "presupro_estimate_box_v0.yaml"
TARGET = ROOT / "experiments" / "cabinet-vault" / "cabinet_estimate_context_box_v0.yaml"


def definitions():
    return load_definition(SOURCE), load_definition(TARGET)


def derive(source=None, target=None):
    if source is None or target is None:
        source, target = definitions()
    return derive_capability_mapping(
        source,
        "estimate.observe",
        target,
        "estimate.observation.accept",
    )


def test_accepted_estimate_surface_exposes_real_monetary_proof_obligations():
    report = derive()

    assert report.status == "unresolved"
    assert [step.target_path for step in report.mapping] == [
        "EstimateObservationInput.source_estimate_id",
        "EstimateObservationInput.project_id",
        "EstimateObservationInput.source_updated_at",
        "EstimateObservationInput.status",
        "EstimateObservationInput.locked",
        "EstimateObservationInput.canonical_content",
    ]
    assert [(gap.code, gap.target_path, gap.semantic) for gap in report.gaps] == [
        (
            "SEMANTIC_SOURCE_NOT_FOUND",
            "EstimateObservationInput.currency",
            "money.currency",
        ),
        (
            "SEMANTIC_SOURCE_NOT_FOUND",
            "EstimateObservationInput.monetary_basis",
            "money.monetary_tax_basis",
        ),
    ]


def test_unresolved_estimate_mapping_cannot_run_and_neither_box_is_called():
    source, target = definitions()
    plan = compile_composition(
        source,
        "estimate.observe",
        target,
        "estimate.observation.accept",
    )
    calls: list[str] = []

    def source_invoke(_capability, _args):
        calls.append("source")
        return {}

    def target_invoke(_capability, _args):
        calls.append("target")
        return {}

    with pytest.raises(BoxDerivabilityError, match="cannot execute an unresolved composition"):
        execute_composition(plan, source_invoke, target_invoke)
    assert calls == []


def test_declaring_missing_source_semantics_closes_gap_without_compiler_change():
    source, target = definitions()
    completed = deepcopy(source)
    fields = completed["schemas"]["PresuProEstimateObservation"]["fields"]
    fields["currency"] = {
        "type": "str",
        "semantic": "money.currency",
        "authority": "estimate.source.authority",
    }
    fields["basis"] = {
        "type": "str",
        "semantic": "money.monetary_tax_basis",
        "authority": "estimate.source.authority",
    }

    report = derive(completed, target)

    assert report.status == "derived"
    assert report.gaps == ()
    mapping = {step.target_path: step.source_path for step in report.mapping}
    assert mapping["EstimateObservationInput.currency"] == "PresuProEstimateObservation.currency"
    assert mapping["EstimateObservationInput.monetary_basis"] == "PresuProEstimateObservation.basis"


def test_cabinet_estimate_contract_is_provider_agnostic_and_forbids_inference():
    _, target = definitions()

    semantic_surface = str(target["schemas"]) + str(target["capabilities"])
    assert "PresuPro" not in semantic_surface
    assert target["external_dependencies"] == []
    assert target["experiment_boundaries"]["currency_inference_allowed"] is False
    assert target["experiment_boundaries"]["monetary_basis_inference_allowed"] is False
