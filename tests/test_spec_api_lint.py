from __future__ import annotations

import spec_api_lint


def _spec() -> dict:
    return {
        "contracts": {
            "get_invoice": "(invoice_id: str) -> str",
            "attach_source": "(invoice_id: str, payload: bytes) -> str",
            "ArchiveClient.fetch": "(self, invoice_id: str) -> str",
        },
        "notes": [],
        "imports": {
            "internal": {
                "archive": ["get_invoice", "attach_source", "ArchiveClient"],
            },
            "module_internal": {
                "api": {
                    "archive": ["get_invoice", "attach_source"],
                }
            },
        },
        "module_functions": {
            "archive": ["get_invoice", "attach_source", "ArchiveClient", "_helper"],
        },
        "module_order": ["archive"],
        "module_paths": {"archive": "core/archive"},
        "default_module": "archive",
    }


def _codes(report: dict) -> set[str]:
    return {finding["code"] for finding in report["findings"]}


def test_valid_compiler_owned_api_exposure_manifest_passes() -> None:
    report = spec_api_lint.lint(_spec())
    assert report["summary"] == {"errors": 0, "exposed_operations": 2, "providers": 1}
    assert report["findings"] == []


def test_project_owned_api_declarations_are_rejected() -> None:
    spec = _spec()
    spec["module_functions"]["api"] = ["endpoint"]
    spec["module_paths"]["api"] = "api"
    spec["module_order"].append("api")
    spec["default_module"] = "api"
    spec["imports"]["internal"]["api"] = ["endpoint"]
    spec["notes"].append("api: [ORCHESTRATION] register endpoint")
    report = spec_api_lint.lint(spec)
    codes = _codes(report)
    assert {
        "api_project_module_declared",
        "api_project_path_declared",
        "api_project_order_declared",
        "api_is_default_module",
        "api_internal_export_declared",
        "api_module_note_declared",
    } <= codes


def test_domain_module_cannot_depend_on_api() -> None:
    spec = _spec()
    spec["imports"]["module_internal"]["archive"] = {"api": ["endpoint"]}
    report = spec_api_lint.lint(spec)
    assert "project_module_depends_on_api" in _codes(report)


def test_exposure_must_resolve_to_public_owned_function_contract() -> None:
    spec = _spec()
    spec["imports"]["module_internal"]["api"]["archive"] = [
        "_helper",
        "ArchiveClient",
        "missing",
        "get_invoice",
        "get_invoice",
    ]
    report = spec_api_lint.lint(spec)
    codes = _codes(report)
    assert "api_private_symbol_exposed" in codes
    assert "api_symbol_not_public_export" in codes
    assert "api_symbol_not_function_contract" in codes
    assert "api_class_symbol_exposed" in codes
    assert "api_symbol_not_owned_by_provider" in codes
    assert "api_duplicate_exposure" in codes


def test_unknown_provider_is_rejected() -> None:
    spec = _spec()
    spec["imports"]["module_internal"]["api"]["missing_provider"] = ["get_invoice"]
    report = spec_api_lint.lint(spec)
    assert "api_unknown_provider" in _codes(report)
