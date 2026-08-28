"""Regression checks for source-optional Invoice confirmation and transfer."""

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).parents[3] / "examples" / "cabinet-web-backend"


def _spec() -> dict:
    return json.loads((PROJECT_ROOT / "global_spec.json").read_text(encoding="utf-8"))


def _notes_for(function_name: str) -> str:
    prefix = f"{function_name}: "
    return " ".join(
        note.removeprefix(prefix)
        for note in _spec()["notes"]
        if note.startswith(prefix)
    )


def test_transfer_records_require_custody_only_for_a_stored_source() -> None:
    notes = _notes_for("derive_transfer_records")

    assert (
        "invoice.source.file_status equals = rules.invoice_workspace.stored_custody_status"
        in notes
    )
    assert "set both tuples empty" in notes
    assert "validator-accepted non-stored status" in notes


def test_missing_source_bytes_do_not_reject_invoice_confirmation() -> None:
    notes = _notes_for("confirm_invoice")

    assert "only a stored-source custody failure" in notes
    assert "absent bytes under a validator-accepted non-stored status do not reject confirmation" in notes


def test_state2_keeps_invoice_only_sync_and_allows_empty_source_membership() -> None:
    rules = (PROJECT_ROOT / "02_rules_sync_operations.md").read_text(encoding="utf-8")

    assert "never exports Provider, Client, Project" in rules
    assert "without stored source custody has an empty" in rules
    assert "absence of bytes does not omit the Card" in rules
