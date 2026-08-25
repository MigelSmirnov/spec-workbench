"""Runtime acceptance oracle for Stage 7.1 Flow 4.

The Factory project supplies the ``semantic_runtime`` pytest fixture. The fixture
binds these implementation-independent scenarios to generated public operations
without changing the assertions below.
"""

from decimal import Decimal

import pytest


def test_matched_lines_use_accepted_sources_and_formulas(semantic_runtime):
    scenario = semantic_runtime.plan_actual_scenario(
        project_id="P1",
        estimate_items=[
            {
                "estimate_item_id": "E1",
                "quantity": Decimal("10"),
                "unit": "pcs",
                "total": Decimal("100.00"),
                "currency": "EUR",
                "monetary_basis": "gross",
            }
        ],
        invoice_lines=[
            {
                "invoice_line_id": "L1",
                "quantity": Decimal("4"),
                "unit": "pcs",
                "total": Decimal("48.00"),
                "currency": "EUR",
                "monetary_basis": "gross",
            },
            {
                "invoice_line_id": "L2",
                "quantity": Decimal("3"),
                "unit": "pcs",
                "total": Decimal("39.00"),
                "currency": "EUR",
                "monetary_basis": "gross",
            },
        ],
        confirmed_matches=[("L1", "E1"), ("L2", "E1")],
    )

    result = semantic_runtime.calculate_plan_actual(scenario.request)
    item = result.item("E1")

    assert item.planned_quantity == Decimal("10")
    assert item.actual_quantity == Decimal("7")
    assert item.quantity_variance == Decimal("-3")
    assert item.remaining_quantity == Decimal("3")
    assert item.planned_amount == Decimal("100.00")
    assert item.actual_amount == Decimal("87.00")
    assert item.amount_variance == Decimal("-13.00")
    assert set(item.matched_invoice_line_ids) == {"L1", "L2"}


def test_overspend_is_positive_and_remaining_quantity_may_be_negative(semantic_runtime):
    scenario = semantic_runtime.plan_actual_scenario(
        project_id="P1",
        estimate_items=[
            {
                "estimate_item_id": "E1",
                "quantity": Decimal("10"),
                "unit": "pcs",
                "total": Decimal("100.00"),
                "currency": "EUR",
                "monetary_basis": "gross",
            }
        ],
        invoice_lines=[
            {
                "invoice_line_id": "L1",
                "quantity": Decimal("13"),
                "unit": "pcs",
                "total": Decimal("125.00"),
                "currency": "EUR",
                "monetary_basis": "gross",
            }
        ],
        confirmed_matches=[("L1", "E1")],
    )

    result = semantic_runtime.calculate_plan_actual(scenario.request)
    item = result.item("E1")

    assert item.quantity_variance == Decimal("3")
    assert item.remaining_quantity == Decimal("-3")
    assert item.amount_variance == Decimal("25.00")
    assert result.project_amount_variance == Decimal("25.00")


def test_unmatched_actual_contributes_to_project_not_matched_item(semantic_runtime):
    scenario = semantic_runtime.plan_actual_scenario(
        project_id="P1",
        estimate_items=[
            {
                "estimate_item_id": "E1",
                "quantity": Decimal("10"),
                "unit": "pcs",
                "total": Decimal("100.00"),
                "currency": "EUR",
                "monetary_basis": "gross",
            }
        ],
        invoice_lines=[
            {
                "invoice_line_id": "L1",
                "quantity": Decimal("5"),
                "unit": "pcs",
                "total": Decimal("50.00"),
                "currency": "EUR",
                "monetary_basis": "gross",
            },
            {
                "invoice_line_id": "L-UNMATCHED",
                "quantity": Decimal("1"),
                "unit": "delivery",
                "total": Decimal("20.00"),
                "currency": "EUR",
                "monetary_basis": "gross",
            },
        ],
        confirmed_matches=[("L1", "E1")],
    )

    result = semantic_runtime.calculate_plan_actual(scenario.request)
    item = result.item("E1")

    assert item.actual_amount == Decimal("50.00")
    assert "L-UNMATCHED" in result.unmatched_invoice_line_ids
    assert result.matched_actual_amount == Decimal("50.00")
    assert result.unmatched_actual_amount == Decimal("20.00")
    assert result.project_actual_amount == Decimal("70.00")
    assert result.project_planned_amount == Decimal("100.00")
    assert result.project_amount_variance == Decimal("-30.00")
    assert result.has_estimate_item_for_invoice_line("L-UNMATCHED") is False


def test_incompatible_units_without_pinned_conversion_are_rejected(semantic_runtime):
    scenario = semantic_runtime.plan_actual_scenario(
        project_id="P1",
        estimate_items=[
            {
                "estimate_item_id": "E1",
                "quantity": Decimal("1"),
                "unit": "t",
                "total": Decimal("100.00"),
                "currency": "EUR",
                "monetary_basis": "gross",
            }
        ],
        invoice_lines=[
            {
                "invoice_line_id": "L1",
                "quantity": Decimal("1000"),
                "unit": "kg",
                "total": Decimal("100.00"),
                "currency": "EUR",
                "monetary_basis": "gross",
            }
        ],
        confirmed_matches=[("L1", "E1")],
        assumptions=[],
    )

    with pytest.raises(semantic_runtime.PlanActualPreconditionError):
        semantic_runtime.calculate_plan_actual(scenario.request)


def test_monetary_basis_mismatch_without_pinned_assumption_is_rejected(semantic_runtime):
    scenario = semantic_runtime.plan_actual_scenario(
        project_id="P1",
        estimate_items=[
            {
                "estimate_item_id": "E1",
                "quantity": Decimal("1"),
                "unit": "pcs",
                "total": Decimal("100.00"),
                "currency": "EUR",
                "monetary_basis": "net",
            }
        ],
        invoice_lines=[
            {
                "invoice_line_id": "L1",
                "quantity": Decimal("1"),
                "unit": "pcs",
                "total": Decimal("121.00"),
                "currency": "EUR",
                "monetary_basis": "gross",
            }
        ],
        confirmed_matches=[("L1", "E1")],
        assumptions=[],
    )

    with pytest.raises(semantic_runtime.PlanActualPreconditionError):
        semantic_runtime.calculate_plan_actual(scenario.request)


def test_identical_pinned_request_is_semantically_reproducible_and_does_not_invent_forecast(semantic_runtime):
    scenario = semantic_runtime.plan_actual_scenario(
        project_id="P1",
        estimate_items=[
            {
                "estimate_item_id": "E1",
                "quantity": Decimal("2"),
                "unit": "pcs",
                "total": Decimal("20.00"),
                "currency": "EUR",
                "monetary_basis": "gross",
            }
        ],
        invoice_lines=[
            {
                "invoice_line_id": "L1",
                "quantity": Decimal("1"),
                "unit": "pcs",
                "total": Decimal("10.00"),
                "currency": "EUR",
                "monetary_basis": "gross",
            }
        ],
        confirmed_matches=[("L1", "E1")],
        assumptions=[],
    )

    first = semantic_runtime.calculate_plan_actual(scenario.request)
    second = semantic_runtime.calculate_plan_actual(scenario.request)

    assert semantic_runtime.semantic_plan_actual_view(first) == semantic_runtime.semantic_plan_actual_view(second)
    assert first.has_forecast is False
    assert second.has_forecast is False
