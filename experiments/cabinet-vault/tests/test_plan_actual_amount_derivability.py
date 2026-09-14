from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from box_derivability import derive_capability_mapping, load_definition


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "experiments" / "cabinet-vault" / "presupro_pricing_contract_v0.yaml"
TARGET = ROOT / "experiments" / "cabinet-vault" / "cabinet_plan_actual_amount_requirement_v0.yaml"


def definitions():
    return load_definition(SOURCE), load_definition(TARGET)


def derive(source=None, target=None):
    if source is None or target is None:
        source, target = definitions()
    return derive_capability_mapping(
        source,
        "estimate.pricing.observe",
        target,
        "plan_actual.planned_item_amount.require",
    )


def test_currency_derives_but_item_planned_amount_and_basis_remain_unresolved():
    report = derive()

    assert report.status == "unresolved"
    assert [
        (step.source_path, step.target_path, step.semantic)
        for step in report.mapping
    ] == [
        (
            "PresuProPricingObservation.currency",
            "PlannedItemAmountRequirement.currency",
            "money.currency",
        )
    ]
    assert [(gap.code, gap.target_path, gap.semantic) for gap in report.gaps] == [
        (
            "SEMANTIC_SOURCE_NOT_FOUND",
            "PlannedItemAmountRequirement.planned_amount",
            "estimate.item.planned_amount",
        ),
        (
            "SEMANTIC_SOURCE_NOT_FOUND",
            "PlannedItemAmountRequirement.planned_amount_basis",
            "estimate.item.planned_amount_basis",
        ),
    ]


def test_aggregate_grand_total_cannot_substitute_for_item_amount_by_decimal_type():
    source, target = definitions()
    report = derive(source, target)

    candidates = {gap.target_path: gap.candidates for gap in report.gaps}
    assert candidates["PlannedItemAmountRequirement.planned_amount"] == ()
    assert source["schemas"]["PresuProPricingObservation"]["fields"]["grand_total"]["type"] == "Decimal"
    assert (
        source["schemas"]["PresuProPricingObservation"]["fields"]["grand_total"]["semantic"]
        == "estimate.aggregate.grand_total"
    )


def test_source_contract_explicitly_refuses_to_claim_canonical_item_total():
    source, _ = definitions()

    assert source["reconnaissance"]["facts"]["canonical_item_total"]["declared"] is False
    assert source["experiment_boundaries"]["canonical_item_total_declared"] is False
    assert source["experiment_boundaries"]["aggregate_total_may_stand_in_for_item_total"] is False


def test_explicit_item_amount_semantics_would_close_gap_without_compiler_change():
    source, target = definitions()
    completed = deepcopy(source)
    fields = completed["schemas"]["PresuProPricingObservation"]["fields"]
    fields["canonical_item_amount"] = {
        "type": "Decimal",
        "semantic": "estimate.item.planned_amount",
        "authority": "estimate.source.authority",
    }
    fields["canonical_item_amount_basis"] = {
        "type": "str",
        "semantic": "estimate.item.planned_amount_basis",
        "authority": "estimate.source.authority",
    }

    report = derive(completed, target)

    assert report.status == "derived"
    assert report.gaps == ()
    mapping = {step.target_path: step.source_path for step in report.mapping}
    assert (
        mapping["PlannedItemAmountRequirement.planned_amount"]
        == "PresuProPricingObservation.canonical_item_amount"
    )
    assert (
        mapping["PlannedItemAmountRequirement.planned_amount_basis"]
        == "PresuProPricingObservation.canonical_item_amount_basis"
    )
