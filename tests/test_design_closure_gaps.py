import json
from pathlib import Path

from tools.design_closure_gaps import run


def make_case(tmp_path: Path, spec: dict, models_md: str = "") -> Path:
    (tmp_path / "global_spec.json").write_text(json.dumps(spec), encoding="utf-8")
    (tmp_path / "01_models.md").write_text(models_md, encoding="utf-8")
    return tmp_path


def codes(report):
    return sorted(f["code"] for f in report["findings"])


def test_empty_model_orphan_entity_and_external_return_are_reported(tmp_path):
    spec = {
        "models": {
            "Empty": {"identity": "value", "fields": {}},
            "Ghost": {"identity": "entity", "fields": {"x": "str"}},
            "Stream": {"kind": "interface"},
        },
        "contracts": {
            "read_ghost": "(a: str) -> Ghost",
            "open_stream": "(a: str) -> Stream",
        },
        "implementation_obligations": {"Stream": {"disposition": "external"}},
        "notes": [],
    }
    report = run(make_case(tmp_path, spec))
    assert codes(report) == ["external_interface_returned", "model_without_fields", "orphan_read_entity"]


def test_prose_enumeration_without_enum_type_is_a_leak_and_withdrawn_sections_are_not(tmp_path):
    spec = {"models": {"Doc": {"identity": "entity", "fields": {"status": "str"}}}, "contracts": {}, "notes": []}
    md = (
        "## Model M1 — Doc\n\n"
        "- `status` — `open`, `closed`, or `cancelled`;\n\n"
        "## Withdrawn model M2 — Gone\n\n"
        "- `state` — `alpha`, `beta`, or `gamma`;\n"
    )
    report = run(make_case(tmp_path, spec, md))
    leaks = [f for f in report["findings"] if f["code"] == "prose_closure_leak"]
    assert len(leaks) == 1 and leaks[0]["field"] == "status"


def test_table_without_writer(tmp_path):
    spec = {
        "models": {}, "contracts": {}, "notes": [],
        "rules": {"persistence_backend": {"repositories": [{"methods": [
            {"method": "list_rows", "query": "list_by", "table": "rows"},
        ]}]}},
    }
    report = run(make_case(tmp_path, spec))
    assert codes(report) == ["table_without_writer"]


def test_admission_fa012_blocks_unwaived_findings_and_honours_waivers(tmp_path):
    import json as _json
    from factory_admission_workbench.service import _closure_gaps_check

    case = tmp_path
    (case / "global_spec.json").write_text(_json.dumps({
        "models": {"Ghost": {"identity": "entity", "fields": {"x": "str"}}},
        "contracts": {"read_ghost": "(a: str) -> Ghost"},
        "notes": [],
    }), encoding="utf-8")
    (case / "01_models.md").write_text("", encoding="utf-8")

    blocked = _closure_gaps_check(case)
    assert blocked.status == "BLOCK" and blocked.evidence["open_findings"]

    (case / "closure_gap_waivers.json").write_text(_json.dumps({
        "waivers": [{"code": "orphan_read_entity", "model": "Ghost",
                     "reason": "produced by the peer system; frozen jointly", "decided": "2026-08-24"}],
    }), encoding="utf-8")
    waived = _closure_gaps_check(case)
    assert waived.status == "PASS" and waived.evidence["waived"] == 1

    # a waiver without a reason must not silence anything
    (case / "closure_gap_waivers.json").write_text(_json.dumps({
        "waivers": [{"code": "orphan_read_entity", "model": "Ghost"}],
    }), encoding="utf-8")
    assert _closure_gaps_check(case).status == "BLOCK"
