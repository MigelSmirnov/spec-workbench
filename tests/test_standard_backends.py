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


def test_standard_holded_transport_backend_needs_no_project_module(tmp_path: Path) -> None:
    project = tmp_path / "holded"
    project.mkdir()
    backend_ir = {
        "kind": "holded_transport_backend",
        "schema_version": 1,
        "backend": {"emitter": "python_httpx_holded_purchase_v1"},
        "wiring": {
            "module": "holded_transport",
            "concrete_class": "HttpxHoldedHttpClient",
            "interface": "HoldedHttpClient",
            "models_module": "cabinet_backend.models",
        },
        "protocol": {"origin": "https://api.holded.com"},
        "payload": {},
        "responses": {},
    }
    (project / "70_holded_transport_closure.json").write_text(
        json.dumps(
            {
                "schema_version": "spec_workbench_holded_transport_backend_closure.v1",
                "status": "closed",
                "backend_ir": backend_ir,
            }
        ),
        encoding="utf-8",
    )
    (project / "global_spec.json").write_text(
        json.dumps({"rules": {"holded_transport_backend": backend_ir}}),
        encoding="utf-8",
    )

    backend = next(
        item for item in deterministic_backends(project)
        if item.id == "holded_transport"
    )
    assert backend.structured_addresses(project) == {
        "rules.holded_transport_backend"
    }
    assert backend.deterministic_method_scopes(project) == {
        "HttpxHoldedHttpClient.__init__",
        "HttpxHoldedHttpClient.create_purchase",
        "HttpxHoldedHttpClient.list_purchases",
        "HttpxHoldedHttpClient.get_purchase",
    }
    assert backend.module_slice(project, "holded_transport") == {
        "enabled": True,
        "backend_ir": backend_ir,
        "deterministic_method_scopes": [
            "HttpxHoldedHttpClient.__init__",
            "HttpxHoldedHttpClient.create_purchase",
            "HttpxHoldedHttpClient.get_purchase",
            "HttpxHoldedHttpClient.list_purchases",
        ],
    }


_EPOCH_CLOCK = {
    "kind": "system_clock_backend",
    "schema_version": 2,
    "backend": {"emitter": "python_host_epoch_clock_v1"},
    "wiring": {"module": "system_clock", "function": "now", "models_module": "kernel.models"},
    "time": {"policy": "rules.time_source_policy", "read": "per_call"},
}


def _write_clock(project: Path, backend_ir: dict, *, status: str = "closed") -> None:
    project.mkdir()
    (project / "70_system_clock_closure.json").write_text(
        json.dumps(
            {
                "schema_version": "spec_workbench_system_clock_backend_closure.v1",
                "status": status,
                "backend_ir": backend_ir,
            }
        ),
        encoding="utf-8",
    )


def _clock(project: Path):
    return next(item for item in deterministic_backends(project) if item.id == "system_clock")


def test_epoch_clock_owns_its_one_module_operation(tmp_path: Path) -> None:
    project = tmp_path / "clock"
    _write_clock(project, _EPOCH_CLOCK)
    (project / "global_spec.json").write_text(
        json.dumps({"rules": {"system_clock_backend": _EPOCH_CLOCK}}), encoding="utf-8"
    )

    backend = _clock(project)
    assert backend.structured_addresses(project) == {"rules.system_clock_backend"}
    assert backend.deterministic_method_scopes(project) == {"now"}
    assert backend.module_slice(project, "system_clock") == {
        "enabled": True,
        "backend_ir": _EPOCH_CLOCK,
        "deterministic_method_scopes": ["now"],
    }
    assert backend.module_slice(project, "run_executor") is None


def test_class_clock_owns_its_concrete_methods(tmp_path: Path) -> None:
    project = tmp_path / "clock"
    backend_ir = {
        "kind": "system_clock_backend",
        "schema_version": 1,
        "backend": {"emitter": "python_system_utc_clock_v1"},
        "wiring": {
            "module": "system_clock",
            "concrete_class": "SystemClock",
            "interface": "Clock",
            "models_module": "app.models",
        },
        "time": {
            "source": "system_utc",
            "representation": "timezone_aware_utc_datetime",
            "read": "per_call",
        },
    }
    _write_clock(project, backend_ir)
    (project / "global_spec.json").write_text(
        json.dumps({"rules": {"system_clock_backend": backend_ir}}), encoding="utf-8"
    )

    assert _clock(project).deterministic_method_scopes(project) == {
        "SystemClock.__init__",
        "SystemClock.now",
    }


def test_closed_closure_counts_before_the_first_assembly(tmp_path: Path) -> None:
    project = tmp_path / "clock"
    _write_clock(project, _EPOCH_CLOCK)

    assert not (project / "global_spec.json").exists()
    assert _clock(project).deterministic_method_scopes(project) == {"now"}


def test_open_closure_never_counts(tmp_path: Path) -> None:
    project = tmp_path / "clock"
    _write_clock(project, _EPOCH_CLOCK, status="open")

    assert _clock(project).deterministic_method_scopes(project) == set()


def test_assembled_spec_without_the_backend_fails_closed(tmp_path: Path) -> None:
    project = tmp_path / "clock"
    _write_clock(project, _EPOCH_CLOCK)
    (project / "global_spec.json").write_text(json.dumps({"rules": {}}), encoding="utf-8")

    assert _clock(project).deterministic_method_scopes(project) == set()
