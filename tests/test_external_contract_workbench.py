from __future__ import annotations

import hashlib
import json
from pathlib import Path

from external_contract_workbench import canonical_value_sha, coverage, module_evidence
from factory_admission_workbench.service import _external_contract_check


ROOT = Path(__file__).resolve().parents[1]
CABINET = ROOT / "examples" / "cabinet-backend"


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _fixture(tmp_path: Path) -> Path:
    spec = {
        "config": {},
        "models": {},
        "rules": {"remote": {"origin": "https://api.example.test"}},
        "module_order": ["transport"],
    }
    _write_json(tmp_path / "global_spec.json", spec)
    artifact = tmp_path / "probe.json"
    artifact.write_text('{"result":"pass"}\n', encoding="utf-8")
    artifact_sha = "sha256:" + hashlib.sha256(artifact.read_bytes()).hexdigest()
    manifest = {
        "schema_version": "spec_workbench_external_contract_evidence.v1",
        "status": "closed",
        "contracts": [{
            "id": "remote-v1",
            "status": "active",
            "authority": "observed_runtime",
            "verified_by": "test operator",
            "subject": {
                "system": "Example API",
                "api_family": "v1",
                "environment": "test tenant",
            },
            "verified_at": "2026-08-06T20:35:05Z",
            "evidence": {
                "artifact": "probe.json",
                "sha256": artifact_sha,
                "run_id": "probe-1",
                "result": "pass",
            },
            "bindings": [{
                "address": "rules.remote.origin",
                "value_sha256": canonical_value_sha("https://api.example.test"),
            }],
            "modules": ["transport"],
            "supersedes": [],
            "superseded_by": None,
        }],
    }
    _write_json(tmp_path / "70_external_contract_evidence.json", manifest)
    return tmp_path


def _codes(report: dict) -> set[str]:
    return {finding["code"] for finding in report["findings"]}


def test_cabinet_external_contract_is_closed_and_content_addressed() -> None:
    report = coverage(CABINET)
    assert report["status"] == "closed"
    assert report["summary"] == {
        "contracts": 1,
        "active": 1,
        "superseded": 0,
        "bindings": 12,
        "errors": 0,
        "handoff_ready": True,
    }
    assert [item["id"] for item in module_evidence(CABINET, "holded_transport")] == [
        "holded-invoicing-v1-purchase-20260806"
    ]
    assert module_evidence(CABINET, "access_control") == []


def test_missing_manifest_is_explicitly_not_applicable(tmp_path: Path) -> None:
    report = coverage(tmp_path)
    assert report["status"] == "not_applicable"
    assert report["summary"]["handoff_ready"] is True


def test_required_external_contract_cannot_disappear_with_manifest(tmp_path: Path) -> None:
    _write_json(tmp_path / "70_transport_closure.json", {
        "external_contract_evidence_ids": ["remote-v1"]
    })
    report = coverage(tmp_path)
    assert report["status"] == "invalid"
    assert "missing_external_contract_manifest" in _codes(report)


def test_changed_verified_value_blocks_reassembly(tmp_path: Path) -> None:
    project = _fixture(tmp_path)
    spec = json.loads((project / "global_spec.json").read_text(encoding="utf-8"))
    spec["rules"]["remote"]["origin"] = "https://plausible-but-unverified.example.test"
    _write_json(project / "global_spec.json", spec)
    report = coverage(project)
    assert "verified_value_changed" in _codes(report)
    assert report["summary"]["handoff_ready"] is False


def test_changed_evidence_artifact_blocks_reassembly(tmp_path: Path) -> None:
    project = _fixture(tmp_path)
    (project / "probe.json").write_text('{"result":"different"}\n', encoding="utf-8")
    report = coverage(project)
    assert "evidence_sha_mismatch" in _codes(report)


def test_admission_fingerprints_manifest_artifact_and_run(tmp_path: Path) -> None:
    project = _fixture(tmp_path)
    check = _external_contract_check(project).to_dict()
    assert check["id"] == "FA011"
    assert check["status"] == "PASS"
    assert check["evidence"]["manifest_sha256"].startswith("sha256:")
    assert check["evidence"]["contracts"] == [{
        "id": "remote-v1",
        "status": "active",
        "verified_by": "test operator",
        "verified_at": "2026-08-06T20:35:05Z",
        "artifact": "probe.json",
        "artifact_sha256": "sha256:" + hashlib.sha256((project / "probe.json").read_bytes()).hexdigest(),
        "run_id": "probe-1",
    }]


def test_evidence_artifact_cannot_escape_project(tmp_path: Path) -> None:
    project = _fixture(tmp_path)
    manifest_path = project / "70_external_contract_evidence.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["contracts"][0]["evidence"]["artifact"] = "../outside.json"
    _write_json(manifest_path, manifest)
    assert "escaping_evidence_artifact" in _codes(coverage(project))


def test_supersession_must_be_reciprocal(tmp_path: Path) -> None:
    project = _fixture(tmp_path)
    manifest_path = project / "70_external_contract_evidence.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    old = dict(manifest["contracts"][0])
    old["id"] = "remote-v0"
    old["status"] = "superseded"
    old["superseded_by"] = "remote-v1"
    manifest["contracts"].append(old)
    _write_json(manifest_path, manifest)
    assert "nonreciprocal_supersession" in _codes(coverage(project))
