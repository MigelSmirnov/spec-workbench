from __future__ import annotations

import json

from notes_workbench import gate


def _project(tmp_path, notes: str):
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
                {"address": "rules.parser.parse_policy"},
                {"address": "config.parser.timeout"},
            ],
        }),
        encoding="utf-8",
    )
    (tmp_path / "80_notes.md").write_text(notes, encoding="utf-8")
    return tmp_path


def _codes(report):
    return {item["code"] for item in report["findings"]}


def test_gate_accepts_addressed_classified_notes(tmp_path):
    project = _project(
        tmp_path,
        "parse: [RULE_REFERENCE] MUST apply = rules.parser.parse_policy before returning.\n"
        "parser: [DEPENDENCY_BOUNDARY] MUST keep parsing policy outside transport code.\n",
    )
    report = gate.coverage(project)
    assert report["summary"] == {"notes": 2, "blocks": 0, "reviews": 0, "handoff_ready": True}


def test_gate_blocks_unknown_scope_class_and_dangling_reference(tmp_path):
    project = _project(
        tmp_path,
        "missing: [BEHAVIOR] MUST return a normalized value.\n"
        "parse: [PROJECT_RULE] MUST use the project rule.\n"
        "parse: [RULE_REFERENCE] MUST use = rules.parser.unknown_policy.\n",
    )
    report = gate.coverage(project)
    assert {"unknown_note_scope", "unknown_note_class", "unresolved_structured_reference"} <= _codes(report)
    assert report["summary"]["handoff_ready"] is False


def test_gate_blocks_semantic_stub(tmp_path):
    project = _project(tmp_path, "parse: [VALIDATION_ERROR] handle errors appropriately\n")
    report = gate.coverage(project)
    assert "semantic_stub" in _codes(report)
    assert report["summary"]["blocks"] == 1


def test_reference_class_requires_matching_namespace(tmp_path):
    project = _project(tmp_path, "parse: [CONFIG_REFERENCE] MUST use = rules.parser.parse_policy.\n")
    report = gate.coverage(project)
    assert "missing_required_reference" in _codes(report)


def test_gate_requires_review_for_competing_failure_outcomes(tmp_path):
    project = _project(
        tmp_path,
        "parse: [VALIDATION_ERROR] MUST raise ValueError when recovery is impossible.\n"
        "parse: [FALLBACK] MUST retry extraction once after the initial parse fails.\n",
    )
    report = gate.coverage(project)
    assert "suspicious_note_class_pair" in _codes(report)
    assert report["summary"]["reviews"] == 1
    assert report["summary"]["handoff_ready"] is False


def test_gate_requires_review_for_multiple_return_shapes(tmp_path):
    project = _project(
        tmp_path,
        "parse: [RETURN_SHAPE] MUST return the normalized string on success.\n"
        "parse: [RETURN_SHAPE] MUST return None when no content is available.\n",
    )
    report = gate.coverage(project)
    assert "duplicate_singleton_class" in _codes(report)
    assert report["summary"]["handoff_ready"] is False


def test_gate_does_not_silently_ignore_malformed_note(tmp_path):
    project = _project(tmp_path, "handle errors appropriately\n")
    report = gate.coverage(project)
    assert "invalid_note_shape" in _codes(report)
    assert report["summary"]["notes"] == 0
    assert report["summary"]["handoff_ready"] is False
