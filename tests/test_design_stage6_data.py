from __future__ import annotations

import json
from pathlib import Path

import design_stage6_data


ROOT = Path(__file__).resolve().parents[1]
CABINET = ROOT / "examples" / "cabinet-backend"


def test_cabinet_data_closure_is_structurally_valid() -> None:
    report = design_stage6_data.lint(CABINET)
    assert report["summary"]["errors"] == 0
    assert report["summary"]["placements"] == 111
    assert report["summary"]["structured_values"] == 111
    assert report["summary"]["persistence_models"] == 32
    assert report["summary"]["persistence_classes"] == {
        "derived": 0,
        "issued": 14,
        "master": 18,
        "mirrored": 0,
    }
    assert set(report["unresolved_topics"]) == {
        "determinism", "external_mirror_schema", "properties"
    }


def test_contract_dependent_persistence_backend_is_rejected_pre_contract(tmp_path: Path) -> None:
    payload = json.loads((CABINET / "60_data_closure.json").read_text(encoding="utf-8"))
    payload["sections"]["rules"]["persistence_backend"] = {
        "kind": "persistence_backend",
        "schema_version": 2,
    }
    payload["placements"].extend([
        {
            "address": "rules.persistence_backend.kind",
            "source_refs": ["test:persistence"],
            "reason": "test",
        },
        {
            "address": "rules.persistence_backend.schema_version",
            "source_refs": ["test:persistence"],
            "reason": "test",
        },
    ])
    (tmp_path / "60_data_closure.json").write_text(json.dumps(payload), encoding="utf-8")
    report = design_stage6_data.lint(tmp_path)
    assert any(
        item["code"] == "contract_dependent_backend_in_precontract_data"
        for item in report["findings"]
    )


def test_untraced_structured_value_is_rejected(tmp_path: Path) -> None:
    payload = json.loads((CABINET / "60_data_closure.json").read_text(encoding="utf-8"))
    payload["sections"]["rules"]["holded_publication"]["invented_retry_limit"] = 7
    (tmp_path / "60_data_closure.json").write_text(json.dumps(payload), encoding="utf-8")
    report = design_stage6_data.lint(tmp_path)
    assert any(
        item["code"] == "untraced_structured_value"
        and "rules.holded_publication.invented_retry_limit" in item["message"]
        for item in report["findings"]
    )


def test_placement_without_value_is_rejected(tmp_path: Path) -> None:
    payload = json.loads((CABINET / "60_data_closure.json").read_text(encoding="utf-8"))
    payload["placements"].append({
        "address": "config.network.timeout_seconds",
        "source_refs": ["source:missing"],
        "reason": "test",
    })
    (tmp_path / "60_data_closure.json").write_text(json.dumps(payload), encoding="utf-8")
    report = design_stage6_data.lint(tmp_path)
    assert any(item["code"] == "missing_placed_value" for item in report["findings"])


def test_unknown_persistence_class_is_rejected(tmp_path: Path) -> None:
    payload = json.loads((CABINET / "60_data_closure.json").read_text(encoding="utf-8"))
    payload["sections"]["persistence"]["StoredInvoiceCard"]["class"] = "mutable"
    (tmp_path / "60_data_closure.json").write_text(json.dumps(payload), encoding="utf-8")
    report = design_stage6_data.lint(tmp_path)
    assert any(item["code"] == "invalid_persistence_class" for item in report["findings"])


def test_mirrored_persistence_requires_remote(tmp_path: Path) -> None:
    payload = json.loads((CABINET / "60_data_closure.json").read_text(encoding="utf-8"))
    payload["sections"]["persistence"]["StoredInvoiceCard"]["class"] = "mirrored"
    (tmp_path / "60_data_closure.json").write_text(json.dumps(payload), encoding="utf-8")
    report = design_stage6_data.lint(tmp_path)
    assert any(item["code"] == "missing_mirrored_remote" for item in report["findings"])
