#!/usr/bin/env python3
"""Deterministically identify one exact accepted media type using verified parsers."""
from __future__ import annotations

from bounded_content_validation_kernel import (
    BoundedContentValidationKernel,
    ContentValidationEvidence,
    ContentValidationRejected,
)


class BoundedMediaIdentificationError(ContentValidationRejected):
    """Raised when bytes do not identify as exactly one accepted parser relation."""


def identify_exact_media_type(
    content: bytes,
    *,
    validator: BoundedContentValidationKernel,
) -> ContentValidationEvidence:
    """Return parser evidence only when exactly one accepted media relation succeeds.

    This operation intentionally receives no filename, source kind, extension or
    caller-declared MIME. The configured validator supplies the closed accepted
    media set and the existing bounded parser implementations supply evidence.
    Provider-not-ready errors propagate rather than being converted into a media
    guess.
    """
    matches: list[ContentValidationEvidence] = []
    for media_type in sorted(validator.accepted_media_types):
        try:
            evidence = validator.validate(content, media_type)
        except ContentValidationRejected:
            continue
        matches.append(evidence)

    if not matches:
        raise BoundedMediaIdentificationError(
            "content does not match any accepted bounded parser relation"
        )
    if len(matches) != 1:
        raise BoundedMediaIdentificationError(
            "content matches more than one accepted bounded parser relation"
        )
    return matches[0]
