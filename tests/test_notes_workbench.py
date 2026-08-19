from __future__ import annotations

import json
from pathlib import Path

from notes_workbench import gate, note_parser, review, service

ROOT = Path(__file__).resolve().parents[1]
CABINET = ROOT / "examples" / "cabinet-backend"


def test_holded_publication_slice_is_bounded_and_has_obligations() -> None:
    payload = service.module_slice(CABINET, "holded_publication")
    assert payload["module"] == "module:holded_publication"
    assert payload["public_operations"]
    assert payload["flows"]
    assert payload["obligations"]
    assert all(item["module"] == "module:holded_publication" for item in payload["obligations"])


def test_unknown_module_is_rejected() -> None:
    try:
        service.module_slice(CABINET, "does_not_exist")
    except ValueError as exc:
        assert "unknown module" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_note_parser_returns_only_requested_module_symbols(tmp_path: Path) -> None:
    (tmp_path / "80_notes.md").write_text(
        "request_holded_publication: [BEHAVIOR] MUST do one thing.\n"
        "other_function: [BEHAVIOR] MUST do another thing.\n",
        encoding="utf-8",
    )
    notes = note_parser.parse(tmp_path, {"request_holded_publication"}, "holded_publication")
    assert [item["scope"] for item in notes] == ["request_holded_publication"]


def test_review_flags_exact_duplicate_and_stub() -> None:
    notes = [
        {"id":"note:a:1","text":"Handle errors"},
        {"id":"note:a:2","text":"Handle errors"},
    ]
    report = review.review(notes, [])
    codes = [item["code"] for item in report["findings"]]
    assert "suspected_stub" in codes
    assert "suspected_duplicate" in codes


def test_cabinet_canonical_notes_gate_is_handoff_ready() -> None:
    payload = gate.coverage(CABINET)
    assert payload["summary"]["handoff_ready"], payload["findings"]
