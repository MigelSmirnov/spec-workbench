#!/usr/bin/env python3
"""Generic bounded content-validation provider for closed JPEG/PNG/PDF inputs."""
from __future__ import annotations

import hashlib
import warnings
from dataclasses import dataclass
from io import BytesIO
from typing import FrozenSet


class ContentValidationError(RuntimeError):
    pass


class ContentValidationNotReady(ContentValidationError):
    pass


class ContentValidationRejected(ContentValidationError):
    pass


@dataclass(frozen=True)
class ContentValidationEvidence:
    media_type: str
    content_hash: str
    size_bytes: int
    parser: str


class BoundedContentValidationKernel:
    """Validate declared media against parser-observed structure under explicit bounds."""

    SUPPORTED_MEDIA_TYPES: FrozenSet[str] = frozenset(
        {"image/jpeg", "image/png", "application/pdf"}
    )

    def __init__(self, *, max_size_bytes: int, accepted_media_types: FrozenSet[str]):
        if not isinstance(max_size_bytes, int) or max_size_bytes <= 0:
            raise ContentValidationError("max_size_bytes must be a positive integer")
        if not accepted_media_types:
            raise ContentValidationError("accepted_media_types must not be empty")
        if not accepted_media_types.issubset(self.SUPPORTED_MEDIA_TYPES):
            raise ContentValidationError("accepted_media_types include unsupported parser format")
        self.max_size_bytes = max_size_bytes
        self.accepted_media_types = accepted_media_types

    @staticmethod
    def _pillow():
        try:
            import PIL  # type: ignore
            from PIL import Image, ImageFile  # type: ignore
        except ImportError as exc:  # pragma: no cover - runtime dependent
            raise ContentValidationNotReady("Pillow is required for JPEG/PNG validation") from exc
        if Image.MAX_IMAGE_PIXELS is None:
            raise ContentValidationNotReady(
                "Pillow decompression-bomb protection must remain enabled"
            )
        return PIL, Image, ImageFile

    @staticmethod
    def _pypdf():
        try:
            import pypdf  # type: ignore
            from pypdf import PdfReader  # type: ignore
        except ImportError as exc:  # pragma: no cover - runtime dependent
            raise ContentValidationNotReady("pypdf is required for PDF validation") from exc
        return pypdf, PdfReader

    def _check_envelope(self, content: bytes, declared_media_type: str) -> None:
        if not isinstance(content, bytes):
            raise ContentValidationRejected("content must be bytes")
        if declared_media_type not in self.accepted_media_types:
            raise ContentValidationRejected("declared media type is not accepted")
        if len(content) == 0:
            raise ContentValidationRejected("empty content is not accepted")
        if len(content) > self.max_size_bytes:
            raise ContentValidationRejected("content exceeds configured size limit")

    def _validate_image(self, content: bytes, declared_media_type: str) -> str:
        PIL, Image, ImageFile = self._pillow()
        expected_format = "JPEG" if declared_media_type == "image/jpeg" else "PNG"
        prior_truncated = ImageFile.LOAD_TRUNCATED_IMAGES
        ImageFile.LOAD_TRUNCATED_IMAGES = False
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", Image.DecompressionBombWarning)
                with Image.open(BytesIO(content), formats=[expected_format]) as image:
                    if image.format != expected_format:
                        raise ContentValidationRejected(
                            "parser-observed image format does not match declared media type"
                        )
                    image.verify()
                with Image.open(BytesIO(content), formats=[expected_format]) as image:
                    if image.format != expected_format:
                        raise ContentValidationRejected(
                            "parser-observed image format changed across verification"
                        )
                    image.load()
        except ContentValidationRejected:
            raise
        except Exception as exc:
            raise ContentValidationRejected(
                f"malformed or unsafe {declared_media_type} content"
            ) from exc
        finally:
            ImageFile.LOAD_TRUNCATED_IMAGES = prior_truncated
        return f"Pillow/{PIL.__version__}:{expected_format}"

    def _validate_pdf(self, content: bytes) -> str:
        pypdf, PdfReader = self._pypdf()
        reader = None
        try:
            reader = PdfReader(BytesIO(content), strict=True)
            if reader.is_encrypted:
                raise ContentValidationRejected(
                    "encrypted PDF cannot be validated as readable source content"
                )
            _ = reader.root_object
            _ = len(reader.pages)
        except ContentValidationRejected:
            raise
        except Exception as exc:
            raise ContentValidationRejected("malformed PDF content") from exc
        finally:
            if reader is not None:
                try:
                    reader.close()
                except Exception:
                    pass
        return f"pypdf/{pypdf.__version__}:strict"

    def validate(self, content: bytes, declared_media_type: str) -> ContentValidationEvidence:
        self._check_envelope(content, declared_media_type)
        if declared_media_type in {"image/jpeg", "image/png"}:
            parser = self._validate_image(content, declared_media_type)
        elif declared_media_type == "application/pdf":
            parser = self._validate_pdf(content)
        else:  # defensive: constructor/envelope already close the set
            raise ContentValidationRejected("no parser relation for declared media type")
        return ContentValidationEvidence(
            media_type=declared_media_type,
            content_hash=hashlib.sha256(content).hexdigest(),
            size_bytes=len(content),
            parser=parser,
        )
