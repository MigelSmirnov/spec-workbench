from __future__ import annotations

import json
from pathlib import Path

import pytest

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

_HOST_CLOCK = {
    "kind": "system_clock_backend",
    "schema_version": 3,
    "backend": {"emitter": "python_host_clock_v1"},
    "wiring": {
        "module": "system_clock",
        "wall_clock_function": "now",
        "elapsed_clock_function": "monotonic_ns",
        "models_module": "kernel.models",
    },
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


def test_host_clock_owns_both_module_operations(tmp_path: Path) -> None:
    project = tmp_path / "clock"
    _write_clock(project, _HOST_CLOCK)
    (project / "global_spec.json").write_text(
        json.dumps({"rules": {"system_clock_backend": _HOST_CLOCK}}), encoding="utf-8"
    )

    backend = _clock(project)
    assert backend.deterministic_method_scopes(project) == {"now", "monotonic_ns"}
    assert backend.module_slice(project, "system_clock") == {
        "enabled": True,
        "backend_ir": _HOST_CLOCK,
        "deterministic_method_scopes": ["monotonic_ns", "now"],
    }


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


# ── keyed_file_spool: a fixed set of module functions plus emitter-defined errors ──

SPOOL_REQUIRED = {
    "spool_entry_name",
    "spool_attempt_prefix",
    "publish_spool_entry",
    "read_spool_entry",
    "discard_spool_attempt",
    "remove_spool_group",
    "remove_spool_temporaries",
}


def spool_ir(*, errors_module: str = "store_spool") -> dict:
    return {
        "kind": "keyed_file_spool_backend",
        "schema_version": 1,
        "backend": {"emitter": "python_keyed_file_spool_v1"},
        "wiring": {
            "module": "store_spool",
            "models_module": "kernel.models",
            "data_provider_module": "kernel.data_provider",
        },
        "area": {"directory_constant": "STORE_SPOOL_AREA_DIRECTORY"},
        "group": {"alphabet": "lowercase_hex", "length": 32},
        "key": {"model": "SpooledFileKey", "fields": {"group": "run_id"}},
        "attempt": {"model": "AttemptKey", "fields": {"group": "run_id"}},
        "ceilings": {"entry_bytes_max": "SPOOL_FILE_BYTES_MAX", "group_bytes_max": "SPOOL_RUN_BYTES_MAX"},
        "errors": {"module": errors_module, "refused": "SpoolRefusedError", "internal": "SpoolInternalError"},
        "layout": {},
    }


def write_spool(project: Path, backend_ir: dict, *, status: str = "closed",
                schema: str = "spec_workbench_keyed_file_spool_backend_closure.v1") -> None:
    project.mkdir(exist_ok=True)
    (project / "70_keyed_file_spool_closure.json").write_text(
        json.dumps({"schema_version": schema, "status": status, "backend_ir": backend_ir}),
        encoding="utf-8",
    )


def _spool(project: Path):
    return next(item for item in deterministic_backends(project) if item.id == "keyed_file_spool")


def test_spool_owns_its_required_functions_and_its_error_classes(tmp_path: Path) -> None:
    project = tmp_path / "spool"
    backend_ir = spool_ir()
    write_spool(project, backend_ir)
    (project / "global_spec.json").write_text(
        json.dumps({"rules": {"keyed_file_spool_backend": backend_ir}}), encoding="utf-8"
    )

    backend = _spool(project)
    owned = SPOOL_REQUIRED | {"SpoolRefusedError", "SpoolInternalError"}
    assert backend.structured_addresses(project) == {"rules.keyed_file_spool_backend"}
    assert backend.deterministic_method_scopes(project) == owned
    assert backend.module_slice(project, "store_spool") == {
        "enabled": True,
        "backend_ir": backend_ir,
        "deterministic_method_scopes": sorted(owned),
    }
    assert backend.module_slice(project, "store") is None


def test_spool_owns_an_optional_function_only_when_its_contract_is_declared(tmp_path: Path) -> None:
    project = tmp_path / "spool"
    write_spool(project, spool_ir(errors_module="kernel.errors"))
    contracts = {name: "(...)" for name in SPOOL_REQUIRED | {"list_spool_groups", "store_value"}}
    (project / "60_contracts.json").write_text(json.dumps({"contracts": contracts}), encoding="utf-8")

    # errors defined elsewhere are not the spool module's callables
    assert _spool(project).deterministic_method_scopes(project) == SPOOL_REQUIRED | {"list_spool_groups"}


@pytest.mark.parametrize("mutate", [
    lambda ir: ir.update(kind="system_clock_backend"),
    lambda ir: ir.pop("wiring"),
    lambda ir: ir["wiring"].update(module=""),
    lambda ir: ir.pop("errors"),
    lambda ir: ir["errors"].pop("module"),
    lambda ir: ir["errors"].update(refused=7),
    lambda ir: ir["errors"].update(refused="SpoolInternalError"),
])
def test_malformed_spool_ir_owns_nothing(tmp_path: Path, mutate) -> None:
    project = tmp_path / "spool"
    backend_ir = spool_ir()
    mutate(backend_ir)
    write_spool(project, backend_ir)

    backend = _spool(project)
    assert backend.authored_backend(project) is None
    assert backend.deterministic_method_scopes(project) == set()


@pytest.mark.parametrize("closure", [
    {"status": "open"},
    {"schema": "spec_workbench_system_clock_backend_closure.v1"},
])
def test_unclosed_spool_closure_owns_nothing(tmp_path: Path, closure: dict) -> None:
    project = tmp_path / "spool"
    write_spool(project, spool_ir(), **closure)

    assert _spool(project).deterministic_method_scopes(project) == set()


def test_spool_drifted_from_the_assembled_spec_owns_nothing(tmp_path: Path) -> None:
    project = tmp_path / "spool"
    write_spool(project, spool_ir())
    (project / "global_spec.json").write_text(
        json.dumps({"rules": {"keyed_file_spool_backend": spool_ir(errors_module="kernel.errors")}}),
        encoding="utf-8",
    )

    assert _spool(project).deterministic_method_scopes(project) == set()


def test_spool_mirror_equals_the_factory_emitter_tables() -> None:
    from factory_admission_workbench.service import _factory_contract_names
    from questions_workbench import documents
    from standard_backends import STANDARD_BACKENDS

    factory = documents.factory_root()
    contracts = next(item for item in STANDARD_BACKENDS if item.id == "keyed_file_spool").module_contracts
    tool = factory / contracts.factory_tool if factory is not None else None
    if tool is None or not tool.is_file():
        pytest.skip("no Factory checkout with the keyed_file_spool emitter")
    assert _factory_contract_names(tool, "REQUIRED_CONTRACTS") == set(contracts.required) == SPOOL_REQUIRED
    assert _factory_contract_names(tool, "OPTIONAL_CONTRACTS") == set(contracts.optional)
