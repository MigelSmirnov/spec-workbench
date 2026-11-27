import json

import pytest

from design_ownership_card import card


@pytest.fixture
def case(tmp_path):
    def write(name, content):
        (tmp_path / name).write_text(content if isinstance(content, str) else json.dumps(content))
    write("02_rules.md", "# State 2\n\n## Accepted decision A1 — Approval\n\n### Normative rules\n\n"
          "1. Require approval\n   of each request.\n2. Keep the evidence.\n")
    write("30_modules.md", "# State 3\n\n## `session`\n\n## `tables`\n\n## `ui`\n")
    write("30_trace.json", {"schema_version": "spec_workbench_trace_2_3.v1",
                            "decisions": {"A1": {"primary_owner": "module:session", "consumers": ["module:tables"]}}})
    write("70_data_provider_closure.json", {"schema_version": "spec_workbench_data_provider_backend_closure.v1",
          "status": "closed", "backend_ir": {"wiring": {"module": "tables"},
                                             "constants": {"ACTIONS": {"row_model": "ActionRow"}}}})
    write("65_imports.json", {"schema_version": "spec_workbench_imports.v1", "scopes": {
        "ui.show": {"uses": [{"provider": "tables", "symbol": "ACTIONS"}]},
        "session.ignore": {"rejected": [{"provider": "tables", "symbol": "ACTIONS"}]}}})
    return tmp_path


def test_card_keeps_decision_owner_supplier_and_importers_distinct(case):
    before = {p: p.read_bytes() for p in case.iterdir()}
    result = card(case, "a1", "tables", 1, "ACTIONS")
    assert result["decision"]["passage"] == "1. Require approval\n   of each request."
    assert result["recorded_ownership"]["primary_owner"] == "module:session"
    assert result["data_dependency"]["supplier"] == "tables"
    assert result["data_dependency"]["declared_importers"] == ["ui"]
    assert "proposed_ownership" not in result
    assert "ActionRow" in result["state1_question"]
    assert result["return_to"]["constant"] == "ACTIONS"
    proposal = card(case, "A1", "tables", owner_reason="Example for review")
    assert proposal["proposed_ownership"]["primary_owner"] == "module:tables"
    assert proposal["recorded_ownership"]["primary_owner"] == "module:session"
    assert {p: p.read_bytes() for p in case.iterdir()} == before


def test_missing_sources_and_invalid_selections(case):
    (case / "30_trace.json").unlink()
    (case / "65_imports.json").unlink()
    result = card(case, "A1", "tables", constant="ACTIONS")
    assert result["recorded_ownership"] is None
    assert result["data_dependency"]["declared_importers"] is None
    with pytest.raises(ValueError, match="No normative rule"):
        card(case, "A1", "tables", rule=3)
    with pytest.raises(ValueError, match="absent"):
        card(case, "A1", "tables", constant="UNKNOWN")
    with pytest.raises(ValueError, match="basis"):
        card(case, "A1", "tables", owner_reason=" ")
