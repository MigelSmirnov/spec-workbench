#!/usr/bin/env python3
"""Execute bounded_content_validation_kernel verification probes."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from io import BytesIO

from bounded_content_validation_kernel import (
    BoundedContentValidationKernel,
    ContentValidationNotReady,
    ContentValidationRejected,
)


PROBE_SCHEMA_VERSION = "spec_workbench_bounded_content_validation_kernel_probe.v0"
MAX_BYTES = 50 * 1024 * 1024
ACCEPTED = frozenset({"image/jpeg", "image/png", "application/pdf"})


@dataclass(frozen=True)
class ProbeResult:
    probe_id: str
    status: str
    message: str


@dataclass(frozen=True)
class ProbeReport:
    schema_version: str
    provider_id: str
    status: str
    results: tuple[ProbeResult, ...]


def _pass(probe_id: str, message: str) -> ProbeResult:
    return ProbeResult(probe_id, "PASS", message)


def _fail(probe_id: str, message: str) -> ProbeResult:
    return ProbeResult(probe_id, "FAIL", message)


def _image_bytes(fmt: str) -> bytes:
    from PIL import Image  # type: ignore

    buffer = BytesIO()
    Image.new("RGB", (8, 8), (30, 60, 90)).save(buffer, format=fmt)
    return buffer.getvalue()


def _pdf_bytes() -> bytes:
    from pypdf import PdfWriter  # type: ignore

    buffer = BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    writer.write(buffer)
    return buffer.getvalue()


def _kernel() -> BoundedContentValidationKernel:
    return BoundedContentValidationKernel(
        max_size_bytes=MAX_BYTES,
        accepted_media_types=ACCEPTED,
    )


def _probe_runtime_dependencies_and_bounds() -> ProbeResult:
    try:
        import PIL  # noqa: F401
        import pypdf  # noqa: F401
        from PIL import Image  # type: ignore

        if Image.MAX_IMAGE_PIXELS is None:
            return _fail(
                "CONTENT-PROBE-001",
                "Pillow decompression-bomb protection is disabled in the selected runtime",
            )
    except Exception as exc:  # pragma: no cover - runtime evidence
        return _fail(
            "CONTENT-PROBE-001",
            f"content-validation runtime dependency unavailable: {type(exc).__name__}: {exc}",
        )
    return _pass(
        "CONTENT-PROBE-001",
        "Pillow and pypdf imported and Pillow decompression-bomb protection is enabled",
    )


def _probe_valid_images_and_mime_binding() -> ProbeResult:
    kernel = _kernel()
    try:
        jpeg = _image_bytes("JPEG")
        png = _image_bytes("PNG")
        jpeg_evidence = kernel.validate(jpeg, "image/jpeg")
        png_evidence = kernel.validate(png, "image/png")
        if jpeg_evidence.media_type != "image/jpeg" or png_evidence.media_type != "image/png":
            return _fail("CONTENT-PROBE-002", "validated image evidence lost media identity")
        try:
            kernel.validate(jpeg, "image/png")
        except ContentValidationRejected:
            pass
        else:
            return _fail(
                "CONTENT-PROBE-002",
                "JPEG bytes were accepted under a conflicting declared PNG media type",
            )
    except Exception as exc:  # pragma: no cover - runtime evidence
        return _fail("CONTENT-PROBE-002", f"image validation failed: {type(exc).__name__}: {exc}")
    return _pass(
        "CONTENT-PROBE-002",
        "valid JPEG/PNG parsed successfully and parser-observed format had to match declared media type",
    )


def _probe_malformed_images_fail_closed() -> ProbeResult:
    kernel = _kernel()
    try:
        jpeg = _image_bytes("JPEG")
        png = _image_bytes("PNG")
        candidates = (
            (jpeg[: max(4, len(jpeg) // 3)], "image/jpeg"),
            (png[: max(8, len(png) // 2)], "image/png"),
        )
        for content, media_type in candidates:
            try:
                kernel.validate(content, media_type)
            except ContentValidationRejected:
                continue
            return _fail(
                "CONTENT-PROBE-003",
                f"truncated {media_type} content was accepted",
            )
    except Exception as exc:  # pragma: no cover - runtime evidence
        return _fail("CONTENT-PROBE-003", f"malformed-image probe failed: {type(exc).__name__}: {exc}")
    return _pass(
        "CONTENT-PROBE-003",
        "truncated JPEG and PNG inputs were rejected by bounded parser validation",
    )


def _probe_pdf_strict_validation_and_mime_binding() -> ProbeResult:
    kernel = _kernel()
    try:
        pdf = _pdf_bytes()
        evidence = kernel.validate(pdf, "application/pdf")
        if evidence.media_type != "application/pdf":
            return _fail("CONTENT-PROBE-004", "validated PDF evidence lost media identity")
        malformed = b"%PDF-1.7\n1 0 obj\n<< /Type /Catalog >>\n"
        try:
            kernel.validate(malformed, "application/pdf")
        except ContentValidationRejected:
            pass
        else:
            return _fail("CONTENT-PROBE-004", "structurally malformed PDF was accepted")
        try:
            kernel.validate(pdf, "image/jpeg")
        except ContentValidationRejected:
            pass
        else:
            return _fail("CONTENT-PROBE-004", "PDF bytes were accepted under JPEG media type")
    except Exception as exc:  # pragma: no cover - runtime evidence
        return _fail("CONTENT-PROBE-004", f"PDF validation failed: {type(exc).__name__}: {exc}")
    return _pass(
        "CONTENT-PROBE-004",
        "valid PDF passed strict structural parsing while malformed PDF and MIME mismatch failed closed",
    )


def _probe_envelope_limits_and_safety_guard() -> ProbeResult:
    try:
        small_kernel = BoundedContentValidationKernel(
            max_size_bytes=4,
            accepted_media_types=ACCEPTED,
        )
        try:
            small_kernel.validate(b"12345", "image/jpeg")
        except ContentValidationRejected:
            pass
        else:
            return _fail("CONTENT-PROBE-005", "oversized content reached parser acceptance")

        try:
            small_kernel.validate(b"1234", "text/plain")
        except ContentValidationRejected:
            pass
        else:
            return _fail("CONTENT-PROBE-005", "unsupported declared media type was accepted")

        from PIL import Image  # type: ignore

        previous = Image.MAX_IMAGE_PIXELS
        Image.MAX_IMAGE_PIXELS = None
        try:
            try:
                _kernel().validate(_image_bytes("PNG"), "image/png")
            except ContentValidationNotReady:
                pass
            else:
                return _fail(
                    "CONTENT-PROBE-005",
                    "image validation remained ready after decompression-bomb protection was disabled",
                )
        finally:
            Image.MAX_IMAGE_PIXELS = previous
    except Exception as exc:  # pragma: no cover - runtime evidence
        return _fail("CONTENT-PROBE-005", f"envelope/safety probe failed: {type(exc).__name__}: {exc}")
    return _pass(
        "CONTENT-PROBE-005",
        "size/media envelope failed closed before parsing and disabled image decompression guard blocked provider readiness",
    )


def run_probe() -> ProbeReport:
    first = _probe_runtime_dependencies_and_bounds()
    if first.status != "PASS":
        results = (first,) + tuple(
            ProbeResult(
                probe_id,
                "UNVERIFIED",
                "runtime dependency/safety prerequisite did not pass",
            )
            for probe_id in (
                "CONTENT-PROBE-002",
                "CONTENT-PROBE-003",
                "CONTENT-PROBE-004",
                "CONTENT-PROBE-005",
            )
        )
        return ProbeReport(PROBE_SCHEMA_VERSION, "bounded_content_validation_kernel", "block", results)

    results = (
        first,
        _probe_valid_images_and_mime_binding(),
        _probe_malformed_images_fail_closed(),
        _probe_pdf_strict_validation_and_mime_binding(),
        _probe_envelope_limits_and_safety_guard(),
    )
    status = "pass" if all(item.status == "PASS" for item in results) else "block"
    return ProbeReport(PROBE_SCHEMA_VERSION, "bounded_content_validation_kernel", status, results)


def main() -> int:
    report = run_probe()
    print(json.dumps(asdict(report), indent=2, sort_keys=True))
    return 0 if report.status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
