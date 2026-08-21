from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pytest
import yaml

from bounded_content_validation_kernel import (
    BoundedContentValidationKernel,
    ContentValidationEvidence,
    ContentValidationRejected,
)
from bounded_media_identification import (
    BoundedMediaIdentificationError,
    identify_exact_media_type,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "experiments" / "cabinet-vault" / "cabinet_web_source_media_lowering_v1.yaml"
EVIDENCE = ROOT / "experiments" / "cabinet-vault" / "CABINET_WEB_ATTACH_CANARY_RUNTIME_EVIDENCE.md"
ACCEPTED = frozenset({"image/jpeg", "image/png", "application/pdf"})


def load_contract():
    value = yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def validator() -> BoundedContentValidationKernel:
    return BoundedContentValidationKernel(
        max_size_bytes=1024 * 1024,
        accepted_media_types=ACCEPTED,
    )


def image_bytes(fmt: str) -> bytes:
    from PIL import Image

    buffer = BytesIO()
    Image.new("RGB", (4, 4), (1, 2, 3)).save(buffer, format=fmt)
    return buffer.getvalue()


def pdf_bytes() -> bytes:
    from pypdf import PdfWriter

    buffer = BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    writer.write(buffer)
    return buffer.getvalue()


def test_identification_uses_parser_evidence_without_filename_kind_or_mime_input():
    kernel = validator()
    assert identify_exact_media_type(image_bytes("JPEG"), validator=kernel).media_type == "image/jpeg"
    assert identify_exact_media_type(image_bytes("PNG"), validator=kernel).media_type == "image/png"
    assert identify_exact_media_type(pdf_bytes(), validator=kernel).media_type == "application/pdf"


def test_identification_rejects_content_that_matches_no_accepted_parser():
    with pytest.raises(BoundedMediaIdentificationError, match="does not match"):
        identify_exact_media_type(b"not an accepted image or pdf", validator=validator())


def test_identification_rejects_ambiguous_multiple_parser_successes(monkeypatch):
    kernel = validator()

    def ambiguous_validate(content: bytes, media_type: str) -> ContentValidationEvidence:
        if media_type in {"image/jpeg", "image/png"}:
            return ContentValidationEvidence(
                media_type=media_type,
                content_hash="0" * 64,
                size_bytes=len(content),
                parser=f"test:{media_type}",
            )
        raise ContentValidationRejected("not this parser")

    monkeypatch.setattr(kernel, "validate", ambiguous_validate)
    with pytest.raises(BoundedMediaIdentificationError, match="more than one"):
        identify_exact_media_type(b"ambiguous", validator=kernel)


def test_contract_forbids_web_metadata_from_becoming_media_authority():
    contract = load_contract()
    assert contract["lowering"]["caller_values_do_not_select_parser"] is True
    assert set(contract["source_context"]["non_authoritative_for_exact_media_identity"]) == {
        "source.kind",
        "source.file_ref",
        "filename",
        "extension",
        "caller_declared_mime",
    }
    assert set(contract["forbidden_fallbacks"]) >= {
        "map_photo_to_JPEG",
        "map_scan_to_PDF",
        "trust_filename_extension",
        "trust_caller_MIME",
        "choose_first_parser_when_multiple_succeed",
        "write_detected_media_type_into_confirmed_Card",
    }


def test_contract_uses_only_existing_verified_parser_provider():
    contract = load_contract()
    parser = contract["lowering"]["verified_parser_provider"]
    implementation = contract["lowering"]["implementation"]
    assert parser == {
        "path": "tools/bounded_content_validation_kernel.py",
        "blob_sha": "4d236d1332935577d81c78b332e5082fb1e6ae91",
    }
    assert implementation["path"] == "tools/bounded_media_identification.py"
    assert implementation["blob_sha"] == "19d2c6c66d90984fae59b0658fbb30320a95bea2"


def test_media_design_and_end_to_end_binding_are_verified_without_rewriting_old_runtime():
    contract = load_contract()
    resolution = contract["runtime_binding_resolution"]
    effect = contract["interop_effect"]

    assert contract["status"] == "verified_by_runtime_canary"
    assert resolution["status"] == "PASS"
    assert resolution["existing_verified_runtime_unmodified"] is True
    assert resolution["runtime_evidence"]["workflow_run_id"] == 32507028221
    assert resolution["runtime_evidence"]["result"] == "PASS"
    assert EVIDENCE.is_file()

    assert effect["finding"] == "CW-MEDIA-001"
    assert effect["exact_identification_design"] == "RESOLVED"
    assert effect["exact_identification_focused_tests"] == "PASS"
    assert effect["end_to_end_attach_binding"] == "PASS"
    assert effect["real_Cabinet_web_data_canary_allowed"] is True
    assert effect["real_Cabinet_web_data_canary_executed"] is False
