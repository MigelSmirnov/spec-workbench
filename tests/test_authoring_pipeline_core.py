from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import authoring_pipeline
import design_authoring_next


ROOT = Path(__file__).resolve().parents[1]
SEQUENCE = ROOT / "skills" / "spec-authoring" / "authoring_sequence.json"


def test_machine_sequence_covers_promoted_state0_through_state5_tools():
    payload = json.loads(SEQUENCE.read_text(encoding="utf-8"))
    assert payload["machine_source_of_truth"] is True
    assert payload["principles"]["mcp_must_wrap_same_pipeline_api"] is True
    assert [phase["id"] for phase in payload["phases"]] == [
        "state0_product_frame",
        "state1_models",
        "state2_rules_decisions",
        "state3_module_responsibilities",
        "state2_to_state3_trace",
        "state4_reviewed_flows",
        "state5_public_module_operations",
        "pre_contract_structured_data_closure",
        "state6_exact_contracts",
        "deterministic_record_construction_closure",
        "deterministic_persistence_closure",
        "deterministic_http_router_closure",
        "deterministic_http_router_context_closure",
        "deterministic_http_router_ir_assembly",
        "deterministic_backend_binding",
        "state7_notes",
        "decision_witness_resolution",
        "imports_closure",
        "state8_assembly",
        "stage8_1_module_review",
        "stage9_factory_admission",
    ]
    for phase in payload["phases"]:
        if phase["status"] != "available":
            continue
        for key in ("inspect_tool", "edit_tool", "gate_tool"):
            tool = phase.get(key)
            if tool:
                assert (ROOT / tool).is_file(), f"missing {key} for {phase['id']}: {tool}"


def test_empty_case_routes_to_state0(tmp_path: Path):
    result = design_authoring_next.next_step(tmp_path)
    assert result["phase"] == "state0_product_frame"
    assert result["blocked"] is False
    assert "--json" not in result["action"]["args"]  # design_index emits JSON by default


def test_product_frame_without_state1_remains_manual_state0(tmp_path: Path, monkeypatch):
    (tmp_path / "00_product.md").write_text("# State 0 — Product frame\n", encoding="utf-8")
    monkeypatch.setattr(
        design_authoring_next.design_lint,
        "lint_project",
        lambda project, state: SimpleNamespace(
            summary=SimpleNamespace(models=0, decisions=0, errors=0, warnings=0)
        ),
    )
    result = design_authoring_next.next_step(tmp_path)
    assert result["phase"] == "state0_product_frame"
    assert result["summary"] == {"manual_review_required": True}


def test_started_state1_without_models_routes_to_state1(tmp_path: Path, monkeypatch):
    (tmp_path / "00_product.md").write_text("# State 0 — Product frame\n", encoding="utf-8")
    (tmp_path / "10_models.md").write_text("# State 1 — Models\n", encoding="utf-8")
    monkeypatch.setattr(
        design_authoring_next.design_lint,
        "lint_project",
        lambda project, state: SimpleNamespace(
            summary=SimpleNamespace(models=0, decisions=0, errors=0, warnings=0)
        ),
    )
    result = design_authoring_next.next_step(tmp_path, display_path="examples/demo")
    assert result["phase"] == "state1_models"
    assert result["action"]["tool"] == "tools/design_lint.py"
    assert result["action"]["args"][:3] == ["examples/demo", "--state", "1"]


def test_ready_states_continue_into_post_state5_chain(
    tmp_path: Path, monkeypatch
):
    (tmp_path / "00_product.md").write_text("# State 0 — Product frame\n", encoding="utf-8")
    (tmp_path / "30_trace.json").write_text("{}\n", encoding="utf-8")
    (tmp_path / design_authoring_next.design_stage6_data.DEFAULT_FILE).write_text("{}\n", encoding="utf-8")

    def lint_project(project, state):
        if state == 1:
            summary = SimpleNamespace(models=1, decisions=0, errors=0, warnings=0)
        else:
            summary = SimpleNamespace(models=0, decisions=1, errors=0, warnings=0)
        return SimpleNamespace(summary=summary)

    monkeypatch.setattr(design_authoring_next.design_lint, "lint_project", lint_project)
    monkeypatch.setattr(
        design_authoring_next.design_stage3,
        "lint",
        lambda project: {"summary": {"modules": 1, "errors": 0, "warnings": 0}, "findings": []},
    )
    monkeypatch.setattr(
        design_authoring_next.design_trace,
        "analyze",
        lambda project: {"summary": {"errors": 0, "warnings": 0}, "findings": []},
    )
    monkeypatch.setattr(
        design_authoring_next.design_stage4,
        "lint",
        lambda project: {"summary": {"flows": 1, "errors": 0, "warnings": 0}, "findings": []},
    )
    monkeypatch.setattr(
        design_authoring_next.design_stage5,
        "lint",
        lambda project: {"summary": {"operations": 1, "errors": 0, "warnings": 0}, "findings": []},
    )

    monkeypatch.setattr(
        design_authoring_next.design_stage6_data,
        "lint",
        lambda project: {"summary": {"errors": 1, "warnings": 0}, "findings": []},
    )
    # This test is about the deterministic chain; question rounds are gated in test_design_questions_gates.py.
    monkeypatch.setattr(design_authoring_next, "_question_gate", lambda *args: None)
    result = design_authoring_next.next_step(tmp_path)
    assert result["phase"] == "pre_contract_structured_data_closure"
    assert result["blocked"] is True
    assert result["action"]["tool"] == "tools/design_stage6_data.py"
    assert "Cabinet" not in result["reason"]


def test_transport_api_delegates_to_same_sequencer(tmp_path: Path, monkeypatch):
    view = SimpleNamespace(
        id="demo",
        title="Demo",
        canonical_ref="agent/demo",
        resolved_ref="origin/agent/demo",
        path="examples/demo",
    )
    monkeypatch.setattr(authoring_pipeline.project_navigation, "project_view", lambda root, query: view)
    monkeypatch.setattr(authoring_pipeline, "_materialize", lambda root, ref, target: target.mkdir(parents=True))
    monkeypatch.setattr(authoring_pipeline, "_remove_worktree", lambda root, target: None)

    def next_step(case_root, *, display_path=None):
        assert display_path == "examples/demo"
        return {
            "schema_version": design_authoring_next.SCHEMA,
            "phase": "state1_models",
            "blocked": False,
            "reason": "demo",
            "action": {"tool": "tools/design_lint.py", "args": [display_path], "command": "ignored"},
            "summary": {},
            "findings": [],
        }

    monkeypatch.setattr(authoring_pipeline.design_authoring_next, "next_step", next_step)
    result = authoring_pipeline.project_next(tmp_path, "demo")
    assert result["project"]["id"] == "demo"
    assert result["authoring"]["phase"] == "state1_models"
    assert result["authoring"]["action"]["execution"] == "pipeline_managed_project_checkout"
    assert result["authoring"]["action"]["command"] is None


def _report(ready: bool, codes=()):
    return {"summary": {"handoff_ready": ready, "pending": len(codes)},
            "findings": [{"code": code, "severity": "error"} for code in codes]}


def test_imports_closure_stands_between_witnesses_and_assembly(tmp_path: Path, monkeypatch):
    sequence = design_authoring_next.load_sequence()
    calls = []
    monkeypatch.setattr(design_authoring_next.imports_closure, "coverage",
                        lambda project: calls.append(project) or _report(False, ["imports_table_missing"]))

    missing = design_authoring_next._imports_step(sequence, tmp_path, "examples/case")
    assert missing["phase"] == "imports_closure" and missing["blocked"] is False
    assert missing["action"]["tool"] == "tools/design_imports.py"
    assert "--draft" in missing["reason"]

    monkeypatch.setattr(design_authoring_next.imports_closure, "coverage",
                        lambda project: _report(False, ["imports_candidate_undecided"]))
    open_ = design_authoring_next._imports_step(sequence, tmp_path, "examples/case")
    assert open_["blocked"] is True and open_["findings"][0]["code"] == "imports_candidate_undecided"

    monkeypatch.setattr(design_authoring_next.imports_closure, "coverage", lambda project: _report(True))
    assert design_authoring_next._imports_step(sequence, tmp_path, "examples/case") is None
    assert calls == [tmp_path]


def test_an_unreadable_case_blocks_the_imports_phase(tmp_path: Path, monkeypatch):
    def refuse(project):
        raise design_authoring_next.ImportsError("the projector cannot build the specification")

    monkeypatch.setattr(design_authoring_next.imports_closure, "coverage", refuse)
    step = design_authoring_next._imports_step(design_authoring_next.load_sequence(), tmp_path, "x")
    assert step["blocked"] is True and "cannot read the case" in step["reason"]
