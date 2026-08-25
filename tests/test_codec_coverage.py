from __future__ import annotations

from persistence_workbench.codec_coverage import CODEC_COVERAGE_SCHEMA, evaluate_codec_coverage


def _spec(*, reader: str = "legacy_reader", storage: str | None = "text") -> dict:
    return {
        "standard_version": 2,
        "models": {
            "role": "data",
            "schema_version": 1,
            "Record": {
                "identity": "entity",
                "fields": {"record_id": "str | None"},
            },
        },
        "rules": {
            "persistence_backend": {
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
                    "read_by": reader,
                    "columns": [{
                        "column": "record_id",
                        "field": "record_id",
                        "storage": storage,
                        "nullable": True,
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
            },
        },
    }


def _test_registry(domain_type: str, explicit_storage: str | None, element_model: str | None) -> str:
    assert element_model is None
    if domain_type != "str":
        raise KeyError(domain_type)
    if explicit_storage not in (None, "text"):
        raise ValueError("unsupported pair")
    return "text"


def test_no_backend_is_codec_not_applicable() -> None:
    report = evaluate_codec_coverage({"standard_version": 2, "rules": {}})
    assert report["schema_version"] == CODEC_COVERAGE_SCHEMA
    assert report["status"] == "not_applicable"
    assert report["complete"] is True
    assert report["gaps"] == []


def test_backend_registry_absence_fails_closed_without_guessing_pairs() -> None:
    spec = _spec()
    report = evaluate_codec_coverage(spec)
    assert report["status"] == "incomplete"
    assert report["complete"] is False
    assert report["registry_resolved"] is False
    assert report["module_pairs"] == []
    assert report["gaps"] == []
    assert report["unresolved_columns"] == [{
        "table": "records",
        "column": "record_id",
        "field": "record_id",
        "domain_type": "str",
        "storage": "text",
        "reason": "backend_registry_unavailable",
    }]


def test_backend_registry_derives_omitted_unique_storage() -> None:
    spec = _spec(reader="record_repository", storage=None)
    report = evaluate_codec_coverage(spec, storage_resolver=_test_registry)
    assert report["status"] == "complete"
    assert report["complete"] is True
    assert report["registry_resolved"] is True
    assert report["unresolved_columns"] == []
    assert report["module_pairs"] == [{
        "module": "record_repository",
        "pairs": [{"domain_type": "str", "storage": "text"}],
    }]
    assert report["gaps"] == []


def test_shared_resolved_pair_reports_deterministic_to_llm_gap() -> None:
    spec = _spec()
    report = evaluate_codec_coverage(spec, storage_resolver=_test_registry)
    assert report["status"] == "incomplete"
    assert report["complete"] is False
    assert report["deterministic_modules"] == ["record_repository"]
    assert report["llm_modules"] == ["legacy_reader"]
    assert report["gaps"] == [{
        "deterministic_module": "record_repository",
        "llm_module": "legacy_reader",
        "pairs": [{"domain_type": "str", "storage": "text"}],
    }]


def test_registry_rejects_pair_without_silent_fallback() -> None:
    spec = _spec(storage="json")
    report = evaluate_codec_coverage(spec, storage_resolver=_test_registry)
    assert report["complete"] is False
    assert report["gaps"] == []
    assert report["unresolved_columns"][0]["reason"] == "backend_pair_unresolved"
    assert "unsupported pair" in report["unresolved_columns"][0]["detail"]
