from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from box_derivability import derive_capability_mapping, load_definition


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "experiments" / "cabinet-vault" / "invoice_card_v1_line_monetary_contract_v0.yaml"
TARGET = ROOT / "experiments" / "cabinet-vault" / "cabinet_plan_actual_actual_amount_requirement_v0.yaml"


def definitions():
    return load_definition(SOURCE), load_definition(TARGET)


def derive(source=None, target=None):
    if source is None or target is None:
        source, target = definitions()
    return derive_capability_mapping(
        source,
        "invoice_line.monetary.observe",
        target,
        "plan_actual.actual_line_amount.require",
    )


def test_currency_derives_but_abstract_actual_amount_remains_unresolved():
    report = derive()

    assert report.status == "unresolved"
    assert [
        (step.source_path, step.target_path, step.semantic)
        for step in report.mapping
    ] == [
        (
            "InvoiceCardV1LineMonetaryObservation.currency",
            "ActualLineAmountRequirement.currency",
            "money.currency",
        )
    ]
    assert [(gap.code, gap.target_path, gap.semantic) for gap in report.gaps] == [
        (
            "SEMANTIC_SOURCE_NOT_FOUND",
            "ActualLineAmountRequirement.actual_amount",
            "invoice.line.actual_amount",
        ),
        (
            "SEMANTIC_SOURCE_NOT_FOUND",
            "ActualLineAmountRequirement.actual_amount_basis",
            "invoice.line.actual_amount_basis",
        ),
    ]


def test_invoice_card_v1_exposes_two_distinct_amounts_and_no_generic_total():
    source, _ = definitions()
    fields = source["schemas"]["InvoiceCardV1LineMonetaryObservation"]["fields"]

    assert "total" not in fields
    assert fields["net_amount"]["semantic"] == "invoice.line.net_amount"
    assert fields["net_amount_basis"]["source"]["value"] == "post_discount_tax_exclusive"
    assert fields["gross_amount"]["semantic"] == "invoice.line.gross_amount"
    assert fields["gross_amount_basis"]["source"]["value"] == "tax_inclusive"
    assert source["experiment_boundaries"]["generic_line_total_declared"] is False


def test_explicit_net_actual_semantics_close_mapping_without_compiler_change():
    source, target = definitions()
    net_target = deepcopy(target)
    fields = net_target["schemas"]["ActualLineAmountRequirement"]["fields"]
    fields["actual_amount"]["semantic"] = "invoice.line.net_amount"
    fields["actual_amount_basis"]["semantic"] = "invoice.line.net_amount_basis"

    report = derive(source, net_target)

    assert report.status == "derived"
    assert report.gaps == ()
    mapping = {step.target_path: step.source_path for step in report.mapping}
    assert mapping["ActualLineAmountRequirement.actual_amount"].endswith(".net_amount")
    assert mapping["ActualLineAmountRequirement.actual_amount_basis"].endswith(".net_amount_basis")


def test_explicit_gross_actual_semantics_close_mapping_without_compiler_change():
    source, target = definitions()
    gross_target = deepcopy(target)
    fields = gross_target["schemas"]["ActualLineAmountRequirement"]["fields"]
    fields["actual_amount"]["semantic"] = "invoice.line.gross_amount"
    fields["actual_amount_basis"]["semantic"] = "invoice.line.gross_amount_basis"

    report = derive(source, gross_target)

    assert report.status == "derived"
    assert report.gaps == ()
    mapping = {step.target_path: step.source_path for step in report.mapping}
    assert mapping["ActualLineAmountRequirement.actual_amount"].endswith(".gross_amount")
    assert mapping["ActualLineAmountRequirement.actual_amount_basis"].endswith(".gross_amount_basis")
