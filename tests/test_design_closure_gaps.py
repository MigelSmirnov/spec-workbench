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


def _time_case(tmp_path: Path, spec: dict, public_apis_md: str | None = None) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    make_case(tmp_path, spec)
    if public_apis_md is not None:
        (tmp_path / "50_public_apis.md").write_text(public_apis_md, encoding="utf-8")
    return tmp_path


def test_ambient_time_note_without_named_source_is_flagged(tmp_path):
    spec = {
        "models": {},
        "contracts": {"observe_thing": "(service: Svc, thing_id: str) -> str"},
        "module_functions": {"svc": ["observe_thing", "Svc"]},
        "notes": ["observe_thing: [PROVENANCE] MUST record UTC observation evidence for the thing."],
    }
    report = run(_time_case(tmp_path, spec))
    assert codes(report) == ["ambient_time_note"]
    assert report["findings"][0]["contract"] == "observe_thing"


def test_datetime_parameter_or_clock_port_silences_ambient_time_note(tmp_path):
    with_param = {
        "models": {},
        "contracts": {"observe_thing": "(service: Svc, thing_id: str, observed_at: datetime) -> str"},
        "module_functions": {"svc": ["observe_thing", "Svc"]},
        "notes": ["observe_thing: [PROVENANCE] MUST record UTC observation evidence at observed_at."],
    }
    assert codes(run(_time_case(tmp_path / "param", spec=with_param))) == []

    with_clock = {
        "models": {"Clock": {"kind": "interface"}},
        "contracts": {
            "observe_thing": "(service: Svc, thing_id: str) -> str",
            "Clock.now": "(self) -> datetime",
            "Svc.__init__": "(self, clock: Clock) -> None",
        },
        "module_functions": {"svc": ["observe_thing", "Svc"]},
        "notes": ["observe_thing: [PROVENANCE] MUST record UTC observation evidence via the retained clock."],
    }
    assert codes(run(_time_case(tmp_path / "clock", spec=with_clock))) == []


def test_timezone_awareness_boilerplate_is_not_ambient_time(tmp_path):
    spec = {
        "models": {},
        "contracts": {"observe_thing": "(service: Svc, thing_id: str) -> str"},
        "module_functions": {"svc": ["observe_thing", "Svc"]},
        "notes": ["Svc.__init__: [DEPENDENCY_BOUNDARY] every persisted or compared wall-clock timestamp "
                  "MUST be a timezone-aware UTC value and MUST NOT be a naive datetime."],
    }
    assert codes(run(_time_case(tmp_path, spec))) == []


FRESH_SPEC = {
    "models": {
        "Receipt": {"identity": "value", "fields": {"receipt_id": "str", "stamped_at": "datetime"}},
        "StampCommand": {"identity": "value", "fields": {"payload": "str"}},
    },
    "contracts": {
        "stamp_receipt": "(service: Journal, command: StampCommand) -> Receipt",
        "view_receipt": "(service: Journal, receipt_id: str) -> Receipt",
    },
    "module_functions": {"journal": ["stamp_receipt", "view_receipt", "Journal"]},
    "notes": [],
}
FRESH_MD = (
    "## `public_op:journal.stamp_receipt`\n\n### State impact\n\nMutates the journal.\n\n"
    "## `public_op:journal.view_receipt`\n\n### State impact\n\nRead-only.\n"
)


def test_fresh_timestamp_without_source_flags_only_mutating_operations(tmp_path):
    report = run(_time_case(tmp_path, FRESH_SPEC, FRESH_MD))
    assert codes(report) == ["fresh_timestamp_without_source"]
    assert report["findings"][0]["contract"] == "stamp_receipt"


def test_fresh_timestamp_fuse_needs_state_impact_evidence(tmp_path):
    # without 50_public_apis.md the typed fuse has no mutating/read-only evidence and stays silent
    assert codes(run(_time_case(tmp_path, FRESH_SPEC))) == []


def test_clock_port_in_init_silences_fresh_timestamp(tmp_path):
    spec = {
        **FRESH_SPEC,
        "models": {**FRESH_SPEC["models"], "Clock": {"kind": "interface"}},
        "contracts": {
            **FRESH_SPEC["contracts"],
            "Clock.now": "(self) -> datetime",
            "Journal.__init__": "(self, clock: Clock) -> None",
        },
    }
    assert codes(run(_time_case(tmp_path, spec, FRESH_MD))) == []
