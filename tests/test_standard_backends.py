from __future__ import annotations

import json
from pathlib import Path

from project_extensions import deterministic_backends


def _write_case(tmp_path: Path) -> tuple[Path, dict]:
    project = tmp_path / "case"
    project.mkdir()
    backend = {
        "kind": "canonical_digest_backend",
        "schema_version": 1,
        "backend": {"emitter": "python_canonical_json_digest_v1"},
        "wiring": {"module": "canonical_digest"},
        "recipes": {
            "request_hash": {
                "input": "model",
                "exclude_fields": [],
                "datetime_normalization": "utc",
            },
            "string_tuple_digest": {"input": "string_tuple"},
        },
    }
    (project / "70_canonical_digest_closure.json").write_text(
        json.dumps(
            {
                "schema_version": "spec_workbench_canonical_digest_backend_closure.v1",
                "status": "closed",
                "backend_ir": backend,
            }
        ),
        encoding="utf-8",
    )
    (project / "global_spec.json").write_text(
        json.dumps({"rules": {"canonical_digest_backend": backend}}),
        encoding="utf-8",
    )
    return project, backend


def test_standard_canonical_digest_backend_needs_no_project_module(tmp_path: Path) -> None:
    project, backend_ir = _write_case(tmp_path)
    backends = deterministic_backends(project)
    matches = [backend for backend in backends if backend.id == "canonical_digest"]
    assert len(matches) == 1
    backend = matches[0]

    assert backend.structured_addresses(project) == {
        "rules.canonical_digest_backend",
        "rules.canonical_digest_backend.recipes",
        "rules.canonical_digest_backend.recipes.request_hash",
        "rules.canonical_digest_backend.recipes.string_tuple_digest",
    }
    assert backend.deterministic_method_scopes(project) == {
        "request_hash",
        "string_tuple_digest",
    }
    assert backend.module_slice(project, "canonical_digest") == {
        "enabled": True,
        "backend_ir": backend_ir,
        "deterministic_method_scopes": ["request_hash", "string_tuple_digest"],
    }
    assert backend.module_slice(project, "other") is None


def test_standard_backend_fails_closed_on_projection_drift(tmp_path: Path) -> None:
    project, _ = _write_case(tmp_path)
    spec_path = project / "global_spec.json"
    payload = json.loads(spec_path.read_text(encoding="utf-8"))
    payload["rules"]["canonical_digest_backend"]["recipes"]["request_hash"]["exclude_fields"] = ["id"]
    spec_path.write_text(json.dumps(payload), encoding="utf-8")

    backend = next(
        item for item in deterministic_backends(project)
        if item.id == "canonical_digest"
    )
    assert backend.structured_addresses(project) == set()
    assert backend.deterministic_method_scopes(project) == set()
    assert backend.module_slice(project, "canonical_digest") is None
