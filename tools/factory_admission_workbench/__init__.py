from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from persistence_workbench import evaluate_codec_coverage

from factory_admission_workbench.service import check as _service_check


def _codec_evidence(source: Path) -> dict[str, Any]:
    payload = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return {
            "schema_version": "spec_workbench_codec_coverage.v1",
            "status": "invalid_source",
            "complete": False,
            "backend": None,
            "registry_resolved": False,
            "deterministic_modules": [],
            "llm_modules": [],
            "module_tables": [],
            "module_pairs": [],
            "unresolved_columns": [],
            "gaps": [],
        }
    return evaluate_codec_coverage(payload)


def _bind_target_lineage(report: dict[str, Any], codec_coverage: dict[str, Any]) -> None:
    for item in report.get("checks", []):
        if not isinstance(item, dict) or item.get("id") != "FA007":
            continue
        evidence = item.get("evidence")
        if not isinstance(evidence, dict) or evidence.get("action") not in {"noop", "accept_lineage"}:
            return
        lineage_path = evidence.get("lineage_path")
        if not isinstance(lineage_path, str):
            return
        path = Path(lineage_path)
        lineage: dict[str, Any] = {}
        if path.is_file():
            loaded = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                lineage = loaded
        lineage_codec = (lineage.get("inputs") or {}).get("codec_coverage")
        evidence["source_codec_coverage"] = codec_coverage
        evidence["lineage_codec_coverage"] = lineage_codec
        if evidence.get("action") == "noop" and lineage_codec != codec_coverage:
            evidence["action"] = "accept_lineage"
            evidence["lineage_fresh"] = False
            item["summary"] = (
                "Factory contains the exact source specification; export will adopt it into "
                "version- and codec-evidence-bound accepted lineage."
            )
        return


def check(**kwargs: Any) -> dict[str, Any]:
    """Run Stage 9 admission and attach nonblocking codec assurance evidence."""
    report = _service_check(**kwargs)
    source = Path(kwargs["source"]).resolve()
    codec_coverage = _codec_evidence(source)
    report["codec_coverage"] = codec_coverage
    _bind_target_lineage(report, codec_coverage)
    return report


__all__ = ["check"]
