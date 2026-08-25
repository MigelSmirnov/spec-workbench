from __future__ import annotations

import json
from pathlib import Path

from persistence_workbench import coverage


def _backend() -> dict:
    return {
        "kind": "persistence_backend",
        "schema_version": 2,
        "backend": {"engine": "sqlite", "emitter": "sqlite_sync_v2"},
        "conventions": {
            "assert_open": "inside_try",
            "guard_reraise": "unchanged",
            "codec_naming": "row_to_snake_model",
            "primary_key_not_null": "always",
        },
        "tables": [{
            "table": "records",
            "table_name_ref": "config.storage.records_table",
            "model": "Record",
            "read_by": "legacy_reader",
            "columns": [{
                "column": "record_id",
                "field": "record_id",
                "storage": "text",
                "nullable": False,
                "check": None,
                "element_model": None,
            }],
            "primary_key": ["record_id"],
            "unique": [],
        }],
        "aggregates": [],
        "repositories": [{
            "repository": "RecordRepository",
            "module": "record_repository",
            "schema_function": "create_record_schema",
            "emission": "table",
            "methods": [{
                "method": "get_record",
                "query": "get_by_key",
                "table": "records",
                "filter": {"record_id": "opaque"},
                "select": ["record_id"],
            }],
        }],
    }


def _project(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    project.mkdir()
    backend = _backend()
    spec = {
        "standard_version": 2,
        "config": {
            "role": "data",
            "schema_version": 1,
            "storage": {"records_table": "records"},
        },
        "models": {
            "role": "data",
            "schema_version": 1,
            "Record": {
                "identity": "entity",
                "fields": {"record_id": "str"},
            },
        },
        "rules": {"persistence_backend": backend},
        "contracts": {
            "create_record_schema": "() -> None",
            "RecordRepository.get_record": "(self, record_id: str) -> Record | None",
        },
        "module_functions": {
            "record_repository": ["RecordRepository", "create_record_schema"],
            "legacy_reader": [],
        },
    }
    (project / "global_spec.json").write_text(json.dumps(spec), encoding="utf-8")
    (project / "70_persistence_closure.json").write_text(
        json.dumps({
            "schema_version": "spec_workbench_persistence_closure.v1",
            "status": "closed",
            "backend_ir": backend,
        }),
        encoding="utf-8",
    )
    return project


def _resolver(domain_type: str, explicit_storage: str | None, element_model: str | None) -> str:
    assert domain_type == "str"
    assert explicit_storage == "text"
    assert element_model is None
    return "text"


def test_registry_absence_is_nonblocking_incomplete_evidence(tmp_path: Path) -> None:
    report = coverage(_project(tmp_path))
    assert report["ready"] is True
    assert report["codec_coverage"]["complete"] is False
    assert report["codec_coverage"]["registry_resolved"] is False
    assert any(item["code"] == "codec_registry_unavailable" for item in report["findings"])
    assert not any(item["code"] == "codec_coverage_gap" for item in report["findings"])


def test_shared_pair_gap_is_warning_and_does_not_block_handoff(tmp_path: Path) -> None:
    report = coverage(_project(tmp_path), storage_resolver=_resolver)
    assert report["ready"] is True
    assert report["summary"]["handoff_ready"] is True
    assert report["codec_coverage"]["complete"] is False
    assert report["codec_coverage"]["registry_resolved"] is True
    gaps = report["codec_coverage"]["gaps"]
    assert gaps == [{
        "deterministic_module": "record_repository",
        "llm_module": "legacy_reader",
        "pairs": [{"domain_type": "str", "storage": "text"}],
    }]
    finding = next(item for item in report["findings"] if item["code"] == "codec_coverage_gap")
    assert finding["severity"] == "warning"
