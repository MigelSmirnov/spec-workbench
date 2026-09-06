from __future__ import annotations

import json
from pathlib import Path

from workbench_mcp import service

ROOT = Path(__file__).resolve().parents[1]
CABINET_WEB = ROOT / "examples" / "cabinet-web-backend"


def test_provenance_finds_decisions_surface_and_notes_for_a_contract() -> None:
    report = service.provenance(CABINET_WEB, "prepare_card_revision")
    assert report["surface"]["module"] == "module:card_workspace"
    assert report["module"] == "card_workspace"
    assert report["surface"]["signature"].startswith("(workspace: CardWorkspace")
    # trace ownership: card_workspace is the primary owner of at least one State 2 decision
    owner_decisions = [d for d in report["decisions"] if d.get("trace_role") == "owner" or d["kind"] == "decision"]
    assert owner_decisions, "a contract on a traced module must surface its owning decisions"
    assert any(d.get("body") for d in report["decisions"]), "an owning decision returns its authored body"
    assert any(note.startswith("prepare_card_revision:") for note in report["notes"])
    assert report["deliberate_design_signals"] is True


def test_provenance_for_unknown_name_is_empty_but_well_formed() -> None:
    report = service.provenance(CABINET_WEB, "no_such_name_anywhere")
    assert report["surface"] is None
    assert report["decisions"] == []
    assert report["referenced_in"] == []
    assert report["notes"] == []
    assert report["deliberate_design_signals"] is False


def test_provenance_for_module_name_reaches_trace_ownership() -> None:
    report = service.provenance(CABINET_WEB, "card_workspace")
    assert report["module"] == "card_workspace"
    owners = [d for d in report["decisions"] if d.get("trace_role") == "owner"]
    assert owners and all(d["body"] for d in owners)


def test_closure_splits_open_and_waived_and_carries_stage6(tmp_path: Path) -> None:
    report = service.closure(CABINET_WEB)
    assert set(report["summary"]) >= {"orphan_read_entity", "prose_closure_leak"}
    for finding in report["open_findings"]:
        assert finding["waived"] is False
    for finding in report["waived_findings"]:
        assert finding["waived"] is True and finding["waiver_reason"]
    assert "summary" in report["stage6_contracts"] or "skipped" in report["stage6_contracts"]


def test_closure_marks_waived_findings_with_reasons(tmp_path: Path) -> None:
    (tmp_path / "global_spec.json").write_text(json.dumps({
        "models": {"Ghost": {"identity": "entity", "fields": {"x": "str"}}},
        "contracts": {"read_ghost": "(a: str) -> Ghost"},
        "notes": [],
    }), encoding="utf-8")
    (tmp_path / "01_models.md").write_text("", encoding="utf-8")
    (tmp_path / "closure_gap_waivers.json").write_text(json.dumps({
        "waivers": [{"code": "orphan_read_entity", "model": "Ghost",
                     "reason": "produced by the peer system", "decided": "2026-08-29"}],
    }), encoding="utf-8")
    report = service.closure(tmp_path)
    assert report["open_findings"] == []
    assert [f["model"] for f in report["waived_findings"]] == ["Ghost"]
    assert report["waived_findings"][0]["waiver_reason"] == "produced by the peer system"


def test_notes_language_scope_filter_narrows_findings() -> None:
    full = service.notes_language(CABINET_WEB)
    scoped = service.notes_language(CABINET_WEB, scope="prepare_card_revision")
    assert scoped["filtered_to_scope"] == "prepare_card_revision"
    assert len(scoped["findings"]) <= len(full["findings"])


def test_design_context_returns_bounded_lines_with_item() -> None:
    report = service.provenance(CABINET_WEB, "prepare_card_revision")
    location = None
    for row in report["decisions"] + report["referenced_in"]:
        if row.get("location") and ":" in row["location"]:
            location = row["location"]
            break
    assert location, "provenance must return at least one PATH:LINE location"
    context = service.design_context(CABINET_WEB, location, radius=2)
    assert len(context["lines"]) <= 5
    assert context["path"] == location.rsplit(":", 1)[0]


def test_list_cases_maps_factory_projects(tmp_path: Path) -> None:
    # pure mapping logic over the repository itself: canonical refs exist here
    report = service.list_cases(ROOT)
    by_id = {row["id"]: row for row in report["cases"]}
    assert "cabinet-web-backend" in by_id
    assert by_id["cabinet-web-backend"]["factory_project"] == "Cabinet_web"
    assert service.resolve_case_for_factory_project(ROOT, "Cabinet_web") == "cabinet-web-backend"
