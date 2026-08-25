from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SUPPORTED_STANDARD_VERSION = 2
REPORT_SCHEMA = "spec_workbench_language_gate.v1"


class SpecLanguageError(ValueError):
    """The specification language revision cannot be inspected safely."""


def _load_spec(project: Path) -> dict[str, Any]:
    path = project / "global_spec.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SpecLanguageError("missing global_spec.json") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise SpecLanguageError(f"invalid global_spec.json: {exc}") from exc
    if not isinstance(payload, dict):
        raise SpecLanguageError("global_spec.json must contain an object")
    return payload


def verify_payload(spec: Any, *, project_root: str) -> dict[str, Any]:
    """Verify language-version invariants for an already loaded spec object."""
    if not isinstance(spec, dict):
        raise SpecLanguageError("specification must contain an object")
    findings: list[dict[str, Any]] = []
    version = spec.get("standard_version")
    if not isinstance(version, int) or isinstance(version, bool):
        findings.append({
            "severity": "error",
            "code": "missing_standard_version",
            "message": "standard_version must be the supported integer specification-language revision",
        })
    elif version != SUPPORTED_STANDARD_VERSION:
        findings.append({
            "severity": "error",
            "code": "unsupported_standard_version",
            "message": (
                f"unsupported standard_version {version!r}; "
                f"expected {SUPPORTED_STANDARD_VERSION}"
            ),
        })

    if "adapters" in spec:
        findings.append({
            "severity": "error",
            "code": "legacy_adapters_section",
            "message": "SPEC_STANDARD v2 removed the top-level adapters section",
        })

    errors = sum(item["severity"] == "error" for item in findings)
    return {
        "schema_version": REPORT_SCHEMA,
        "project_root": project_root,
        "standard_version": version,
        "supported_standard_version": SUPPORTED_STANDARD_VERSION,
        "ready": errors == 0,
        "summary": {"errors": errors},
        "findings": findings,
    }


def verify(project: Path) -> dict[str, Any]:
    """Verify only language-version invariants owned by SPEC_STANDARD itself.

    Backend-specific IR validation deliberately belongs to the corresponding
    backend workbench. This gate prevents consumers from interpreting a spec
    under an implicit or unknown language revision.
    """
    return verify_payload(_load_spec(project), project_root=project.resolve().name)


__all__ = [
    "REPORT_SCHEMA",
    "SUPPORTED_STANDARD_VERSION",
    "SpecLanguageError",
    "verify",
    "verify_payload",
]
