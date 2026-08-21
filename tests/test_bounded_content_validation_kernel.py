from __future__ import annotations

from io import BytesIO

import pytest

from bounded_content_validation_kernel import (
    BoundedContentValidationKernel,
    ContentValidationError,
    ContentValidationRejected,
)
from bounded_content_validation_kernel_probe import run_probe


ACCEPTED = frozenset({"image/jpeg", "image/png", "application/pdf"})


def kernel(max_size_bytes: int = 1024 * 1024) -> BoundedContentValidationKernel:
    return BoundedContentValidationKernel(
        max_size_bytes=max_size_bytes,
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


def test_constructor_rejects_unsupported_parser_media_type():
    with pytest.raises(ContentValidationError, match="unsupported"):
        BoundedContentValidationKernel(
            max_size_bytes=100,
            accepted_media_types=frozenset({"text/plain"}),
        )


def test_declared_media_must_match_parser_observed_image_format():
    validator = kernel()
    jpeg = image_bytes("JPEG")

    assert validator.validate(jpeg, "image/jpeg").media_type == "image/jpeg"
    with pytest.raises(ContentValidationRejected):
        validator.validate(jpeg, "image/png")


def test_malformed_image_and_pdf_fail_closed():
    validator = kernel()
    jpeg = image_bytes("JPEG")

    with pytest.raises(ContentValidationRejected):
        validator.validate(jpeg[: max(4, len(jpeg) // 3)], "image/jpeg")
    with pytest.raises(ContentValidationRejected):
        validator.validate(b"%PDF-1.7\n1 0 obj\n<<>>\n", "application/pdf")


def test_valid_strict_pdf_is_accepted_without_media_guessing():
    validator = kernel()
    pdf = pdf_bytes()

    evidence = validator.validate(pdf, "application/pdf")
    assert evidence.media_type == "application/pdf"
    assert evidence.parser.startswith("pypdf/")
    with pytest.raises(ContentValidationRejected):
        validator.validate(pdf, "image/jpeg")


def test_size_limit_rejects_before_parser_success():
    validator = kernel(max_size_bytes=4)

    with pytest.raises(ContentValidationRejected, match="size"):
        validator.validate(b"12345", "application/pdf")


def test_full_bounded_content_validation_probe_passes():
    report = run_probe()

    assert report.status == "pass"
    assert [item.probe_id for item in report.results] == [
        "CONTENT-PROBE-001",
        "CONTENT-PROBE-002",
        "CONTENT-PROBE-003",
        "CONTENT-PROBE-004",
        "CONTENT-PROBE-005",
    ]
    assert {item.status for item in report.results} == {"PASS"}
