from __future__ import annotations

from persistence_workbench.slice import module_slice


def _spec() -> dict:
    return {
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
                "tables": [
                    {"table": "parents"},
                    {"table": "children"},
                    {"table": "unrelated"},
                ],
                "aggregates": [{
                    "aggregate": "ParentAggregate",
                    "root": {"table": "parents"},
                    "relations": [{"table": "children"}],
                }],
                "repositories": [{
                    "repository": "ParentRepository",
                    "module": "parent_repository",
                    "schema_function": "create_parent_schema",
                    "emission": "table",
                    "methods": [
                        {
                            "method": "get_parent",
                            "query": "get_by_key",
                            "table": "parents",
                        },
                        {
                            "method": "get_parent_aggregate",
                            "query": "get_aggregate_by_key",
                            "aggregate": "ParentAggregate",
                        },
                    ],
                }],
            }
        }
    }


def test_absent_backend_returns_disabled_slice() -> None:
    report = module_slice({"rules": {}}, "parent_repository")
    assert report == {
        "enabled": False,
        "module": "parent_repository",
        "repository": None,
        "tables": [],
        "aggregates": [],
        "deterministic_method_scopes": [],
    }


def test_module_slice_contains_only_referenced_persistence_ir() -> None:
    report = module_slice(_spec(), "parent_repository")
    assert report["enabled"] is True
    assert report["repository"]["repository"] == "ParentRepository"
    assert {row["table"] for row in report["tables"]} == {"parents", "children"}
    assert [row["aggregate"] for row in report["aggregates"]] == ["ParentAggregate"]
    assert report["deterministic_method_scopes"] == [
        "ParentRepository.get_parent",
        "ParentRepository.get_parent_aggregate",
    ]


def test_unowned_module_does_not_receive_other_repository_ir() -> None:
    report = module_slice(_spec(), "api")
    assert report["enabled"] is True
    assert report["repository"] is None
    assert report["tables"] == []
    assert report["aggregates"] == []
    assert report["deterministic_method_scopes"] == []
