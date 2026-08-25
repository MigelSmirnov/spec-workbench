from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
CASE = ROOT / "examples" / "cabinet-web-backend"
NOTE_RE = re.compile(
    r"^(?P<scope>[A-Za-z_][A-Za-z0-9_.]*):\s*\[(?P<class>[A-Z_]+)\]\s*(?P<text>.+)$"
)


def _json(name: str) -> dict[str, object]:
    return json.loads((CASE / name).read_text(encoding="utf-8"))


def _notes() -> dict[str, list[tuple[str, str]]]:
    result: dict[str, list[tuple[str, str]]] = {}
    for raw in (CASE / "80_notes.md").read_text(encoding="utf-8").splitlines():
        match = NOTE_RE.fullmatch(raw.strip())
        if match:
            result.setdefault(match["scope"], []).append(
                (match["class"], match["text"])
            )
    return result


def test_invoice_mutation_commands_carry_actor_provenance() -> None:
    models = _json("60_model_closure_domain.json")["models"]
    for name in (
        "ArchiveInvoiceCommand",
        "AttachInvoiceSourceCommand",
        "ConfirmInvoiceCommand",
    ):
        assert models[name]["fields"]["actor"] == "ActorReference"


def test_duplicate_stable_order_resolves_against_candidate_models() -> None:
    data = _json("60_data_closure.json")["sections"]
    models = _json("60_model_closure_domain.json")["models"]
    paths = data["rules"]["invoice_duplicate_matching"]["stable_order"]

    for path in paths:
        model_name = "InvoiceDuplicateCandidate"
        for field in path.split("."):
            field_type = models[model_name]["fields"][field]
            model_name = field_type.removesuffix(" | None")


def test_card_revision_supports_caller_owned_atomic_uow() -> None:
    contracts = _json("60_contracts.json")["contracts"]
    assert contracts["prepare_card_revision"] == (
        "(workspace: CardWorkspace, command: CardRevisionCommitCommand) "
        "-> CanonicalCardRevision"
    )
    assert contracts["commit_card_revision_in_unit_of_work"] == (
        "(workspace: CardWorkspace, unit_of_work: CabinetUnitOfWork, "
        "command: CardRevisionCommitCommand) -> CardRevisionCommitResult"
    )

    spec = _json("global_spec.json")
    assert "commit_card_revision_in_unit_of_work" in spec["imports"]["internal"][
        "card_workspace"
    ]
    invoice_imports = spec["imports"]["module_internal"]["invoice_workspace"]
    assert "commit_card_revision_in_unit_of_work" in invoice_imports["card_workspace"]
    assert {
        "InvoiceCardRevisionReference",
        "InvoiceTransferManifest",
        "InvoiceWorkingSetRecord",
        "SourceContentReference",
        "SourceCustodyRecord",
    } <= set(invoice_imports["models"])


def test_invoice_notes_close_security_orchestration_and_result_mapping() -> None:
    notes = _notes()
    mutation_scopes = (
        "create_invoice_draft",
        "update_invoice_draft",
        "confirm_invoice",
        "record_invoice_payment",
        "attach_invoice_source_metadata",
        "archive_invoice",
    )
    for scope in mutation_scopes:
        classes = {note_class for note_class, _ in notes[scope]}
        assert {"SECURITY_BOUNDARY", "ORCHESTRATION", "RETURN_SHAPE"} <= classes

    confirmation = " ".join(text for _, text in notes["confirm_invoice"])
    for required in (
        "commit_card_revision_in_unit_of_work",
        "same UoW",
        "InvoiceTransferManifest",
        "InvoiceWorkingSetRecord",
        "rolls back",
    ):
        assert required in confirmation


def test_invoice_runtime_policy_closes_validation_and_confirmation_derivations() -> None:
    rules = _json("60_data_closure.json")["sections"]["rules"]["invoice_workspace"]

    assert rules["card_type"] == "invoice"
    assert rules["lifecycle"] == {
        "draft": "draft",
        "confirmed": "confirmed",
        "archived": "archived",
    }
    assert rules["manifest_hash_algorithm"] == "sha256_canonical_json_v1"
    assert rules["manifest_hash_fields"] == [
        "invoice_id",
        "manifest_version",
        "generated_at",
        "card_revisions",
        "source_references",
    ]
    assert rules["stored_custody_status"] == "stored"
    assert rules["working_set_status"] == "available"
    assert len(rules["validation_checks"]) == len(rules["validation_issue_order"])


def test_invoice_read_and_validation_notes_name_executable_uow_calls() -> None:
    notes = _notes()
    duplicate_text = " ".join(text for _, text in notes["find_invoice_duplicates"])
    assert "list_current_card_references_by_type" in duplicate_text
    assert "load_card_revision" in duplicate_text
    assert "candidate_field_sources" in duplicate_text

    validation_text = " ".join(text for _, text in notes["validate_invoice"])
    assert "validation_checks" in validation_text
    assert "InvoiceDuplicateCandidateInput" in validation_text
    assert "find_invoice_duplicates exactly once" in validation_text


def test_invoice_workspace_constructor_has_exact_dependency_assignments() -> None:
    constructor_notes = _notes()["InvoiceWorkspace.__init__"]
    assert {note_class for note_class, _ in constructor_notes} >= {
        "DEPENDENCY_BOUNDARY",
        "FIELD_ASSIGNMENT",
    }
    text = " ".join(note for _, note in constructor_notes)
    assert "unit_of_work_factory" in text
    assert "card_workspace" in text
    assert "database URL" in text
