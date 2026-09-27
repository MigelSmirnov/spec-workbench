"""SPEC_STANDARD 15.3.1 and 15.4 held at authoring time, without the Factory."""
from __future__ import annotations

import json
from pathlib import Path

import design_stage6_data
from notes_workbench import gate


def _notes_project(tmp_path: Path, notes: str) -> Path:
    (tmp_path / "30_modules.md").write_text("## `module:parser`\n", encoding="utf-8")
    (tmp_path / "60_contracts.json").write_text(
        json.dumps({
            "schema_version": "spec_workbench_state6_contracts.v1",
            "contracts": {"parse": "(raw: str) -> str | None"},
        }),
        encoding="utf-8",
    )
    (tmp_path / "60_data_closure.json").write_text(
        json.dumps({
            "schema_version": "spec_workbench_state6_data_closure.v1",
            "placements": [
                {"address": "rules.parser.states"},
                {"address": "config.parser.timeout"},
            ],
        }),
        encoding="utf-8",
    )
    (tmp_path / "80_notes.md").write_text(notes, encoding="utf-8")
    return tmp_path


def _found(report: dict, code: str) -> list[dict]:
    return [item for item in report["findings"] if item["code"] == code]


def test_note_naming_a_value_by_array_position_is_blocked(tmp_path: Path) -> None:
    report = gate.coverage(_notes_project(
        tmp_path, "parse: [BEHAVIOR] MUST return `rules.parser.states[0]` for an empty input.\n"
    ))
    found = _found(report, "array_position_reference")
    assert len(found) == 1
    assert found[0]["severity"] == "block"
    assert "rules.parser.states[0]" in found[0]["message"]
    assert "SPEC_STANDARD 15.4" in found[0]["message"]
    assert report["summary"]["handoff_ready"] is False


def test_positional_reference_is_blocked_even_with_the_equals_form(tmp_path: Path) -> None:
    report = gate.coverage(_notes_project(
        tmp_path, "parse: [RULE_REFERENCE] MUST return = rules.parser.states[2] when the store is restored.\n"
    ))
    assert len(_found(report, "array_position_reference")) == 1


def test_data_address_without_equals_is_blocked(tmp_path: Path) -> None:
    report = gate.coverage(_notes_project(
        tmp_path, "parse: [BEHAVIOR] MUST refuse input longer than `config.parser.timeout` bytes.\n"
    ))
    found = _found(report, "undereferenced_data_address")
    assert [item["scope"] for item in found] == ["parse"]
    assert "config.parser.timeout" in found[0]["message"]
    assert "SPEC_STANDARD 15.3.1" in found[0]["message"]


def test_dereferenced_address_and_imported_constant_are_not_bare_addresses(tmp_path: Path) -> None:
    report = gate.coverage(_notes_project(
        tmp_path,
        "parse: [RULE_REFERENCE] MUST apply = rules.parser.states before returning.\n"
        "parse: [BEHAVIOR] MUST refuse input longer than the imported PARSER_TIMEOUT constant.\n"
        "parse: [BEHAVIOR] MUST keep the parsing rules. Config is read once.\n",
    ))
    assert _found(report, "undereferenced_data_address") == []
    assert _found(report, "array_position_reference") == []


def test_one_note_reports_each_bare_address_once(tmp_path: Path) -> None:
    report = gate.coverage(_notes_project(
        tmp_path,
        "parse: [BEHAVIOR] MUST compare with `config.parser.timeout` and again with `config.parser.timeout`, "
        "then apply `rules.parser.states`.\n",
    ))
    assert sorted(item["message"].split(" ", 1)[0] for item in _found(report, "undereferenced_data_address")) == [
        "config.parser.timeout", "rules.parser.states",
    ]


def _data_project(tmp_path: Path, *, constants: dict | None) -> Path:
    sections = {
        "config": {"store": {"database_file_name": "operational_store.sqlite", "retries": 3}},
        "rules": {"continuity": {"states": ["new_installation", "continuous", "restored"], "mode": "strict"}},
        "persistence": {},
        "properties": {},
        "determinism": {},
    }
    placements = [
        {"address": address, "source_refs": ["decision:A1"], "reason": "test"}
        for address in (
            "config.store.database_file_name", "config.store.retries",
            "rules.continuity.states", "rules.continuity.mode",
        )
    ]
    (tmp_path / "60_data_closure.json").write_text(
        json.dumps({
            "schema_version": "spec_workbench_state6_data_closure.v1",
            "sections": sections,
            "placements": placements,
            "unresolved": [],
        }),
        encoding="utf-8",
    )
    if constants is not None:
        (tmp_path / "70_data_provider_closure.json").write_text(
            json.dumps({"backend_ir": {"kind": "data_provider_backend", "constants": constants}}),
            encoding="utf-8",
        )
    return tmp_path


def _two_homes(report: dict) -> list[tuple[str, str]]:
    return sorted(
        (item["address"], item["symbol"]) for item in report["findings"] if item["code"] == "value_in_two_homes"
    )


def test_value_kept_both_in_rules_and_in_a_provider_constant_is_an_error(tmp_path: Path) -> None:
    report = design_stage6_data.lint(_data_project(tmp_path, constants={
        "STORE_CONTINUITY_STATES": {
            "value_type": "string_tuple", "value": ["new_installation", "continuous", "restored"],
        },
        "STORE_DATABASE_FILE_NAME": {"value_type": "string", "value": "operational_store.sqlite"},
        "STORE_CONTINUITY_RESTORED_STATE": {"value_type": "string", "value": "new_installation"},
    }))
    assert _two_homes(report) == [
        ("config.store.database_file_name", "STORE_DATABASE_FILE_NAME"),
        ("rules.continuity.states", "STORE_CONTINUITY_STATES"),
        ("rules.continuity.states[0]", "STORE_CONTINUITY_RESTORED_STATE"),
    ]
    message = next(item["message"] for item in report["findings"] if item["code"] == "value_in_two_homes")
    assert "SPEC_STANDARD 15.4" in message
    assert report["summary"]["errors"] >= 3


def test_short_scalars_that_merely_coincide_are_not_judged(tmp_path: Path) -> None:
    report = design_stage6_data.lint(_data_project(tmp_path, constants={
        "PARSER_MODE": {"value_type": "string", "value": "strict"},
        "RETRY_LIMIT": {"value_type": "positive_integer", "value": 3},
    }))
    assert _two_homes(report) == []


def test_value_that_lives_only_in_the_provider_is_clean(tmp_path: Path) -> None:
    report = design_stage6_data.lint(_data_project(tmp_path, constants={
        "HOST_COUNTER_FILE_NAME": {"value_type": "string", "value": "store_continuity_counter"},
    }))
    assert _two_homes(report) == []


def test_case_without_a_data_provider_is_not_judged(tmp_path: Path) -> None:
    assert _two_homes(design_stage6_data.lint(_data_project(tmp_path, constants=None))) == []
