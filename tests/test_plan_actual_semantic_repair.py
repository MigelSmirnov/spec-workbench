from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
STATE1 = ROOT / "examples" / "cabinet-backend" / "01_models_plan_actual_monetary_gap.md"
STATE2 = ROOT / "examples" / "cabinet-backend" / "02_rules_plan_actual_semantic_gap.md"
PLANNED = ROOT / "experiments" / "cabinet-vault" / "cabinet_plan_actual_amount_requirement_v0.yaml"
ACTUAL = ROOT / "experiments" / "cabinet-vault" / "cabinet_plan_actual_actual_amount_requirement_v0.yaml"


def load_yaml(path: Path):
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_state2_monetary_decision_is_reopened_until_three_business_decisions_close():
    text = STATE2.read_text(encoding="utf-8")

    assert "**REOPENED" in text
    assert "PA-MONEY-001" in text
    assert "PA-MONEY-002" in text
    assert "PA-MONEY-003" in text
    assert "Full monetary PlanActual analysis" not in text or "fail" in text.lower()
    assert "may return to **ACCEPTED** only after" in text


def test_state1_refinement_forbids_reintroducing_total_aliases_as_semantic_proof():
    text = STATE1.read_text(encoding="utf-8")

    assert "OPEN SEMANTIC GAP" in text
    assert "must not treat an undifferentiated field named `total` as" in text
    assert "must not introduce `InvoiceLine.total` as a compatibility alias" in text
    assert "No answer is accepted yet" in text


def test_planned_target_references_reopened_design_state_not_accepted_alias_rule():
    manifest = load_yaml(PLANNED)
    baseline = manifest["source_baseline"]

    assert "accepted_rule" not in baseline
    assert baseline["state1_refinement"] == [
        "examples/cabinet-backend/01_models_plan_actual_monetary_gap.md"
    ]
    assert baseline["reopened_rule"] == [
        "examples/cabinet-backend/02_rules_plan_actual_semantic_gap.md"
    ]
    assert manifest["experiment_boundaries"]["basis_inference_allowed"] is False


def test_actual_target_keeps_net_and_gross_unselected_by_default():
    manifest = load_yaml(ACTUAL)
    baseline = manifest["source_baseline"]
    boundaries = manifest["experiment_boundaries"]

    assert "accepted_rule" not in baseline
    assert baseline["reopened_rule"] == [
        "examples/cabinet-backend/02_rules_plan_actual_semantic_gap.md"
    ]
    assert boundaries["net_selected_by_default"] is False
    assert boundaries["gross_selected_by_default"] is False
