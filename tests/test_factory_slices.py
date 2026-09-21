from __future__ import annotations

import json
from pathlib import Path

from factory_admission_workbench.service import _factory_slices_check
from factory_slice_workbench import probe


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_json(path: Path, payload: object) -> None:
    _write(path, json.dumps(payload, indent=2) + "\n")


def _factory(tmp_path: Path, *, seam: bool = True) -> Path:
    """A Factory whose slicer cuts what the test specification tells it to.

    ``_slice_imports`` and ``_slice_rules`` of the specification stand for what
    the real slicer derives from note and contract text.
    """
    root = tmp_path / "code_factory"
    _write(
        root / "tools/normalize_spec.py",
        """import json, sys
from pathlib import Path
spec = json.load(open(sys.argv[1], encoding='utf-8'))
if spec.get('_normalizer_rejects'):
    raise SystemExit('unresolved reference')
spec['modules'] = {name: {} for name in spec.get('module_functions', {})}
open(sys.argv[2], 'w', encoding='utf-8').write(json.dumps(spec))
(Path(sys.argv[1]).parent / 'normalization_report.json').write_text('{}', encoding='utf-8')
""",
    )
    _write(
        root / "tools/build_local_spec.py",
        """import json, sys
from pathlib import Path
module, spec_path, _call_graph, out_dir = sys.argv[1:5]
spec = json.load(open(spec_path, encoding='utf-8'))
if module in spec.get('_slicer_rejects', []):
    raise SystemExit(f'cannot cut {module}')
local_spec = {
    'standard_version': 2,
    'module_name': module,
    'imports': {'internal': spec.get('_slice_imports', {}).get(module, {})},
    'rules': spec.get('_slice_rules', {}).get(module, {}),
}
(Path(out_dir) / f'{module}.json').write_text(json.dumps(local_spec), encoding='utf-8')
""",
    )
    if seam:
        _write(
            root / "tools/data_code_seam.py",
            """def data_in_model_context_defects(local_spec):
    return [f'rules.{key}' for key in sorted(local_spec.get('rules') or {})]
""",
        )
    return root


def _spec(**extra: object) -> dict:
    return {
        "standard_version": 2,
        "contracts": {
            "confirm": "(owner: ActorRef, owner_statement: str) -> Continuity",
            "owner_statement": "(request: StatementRequest) -> Statement",
            "open_store": "(data_directory: str) -> StoreOpening",
        },
        "module_functions": {
            "models": ["Continuity"],
            "authority": ["owner_statement"],
            "continuity": ["confirm"],
            "store": ["open_store"],
        },
        "rules": {},
        **extra,
    }


def _probe(tmp_path: Path, spec: dict, *, seam: bool = True, case: Path | None = None) -> dict:
    source = (case or tmp_path / "case") / "global_spec.json"
    _write_json(source, spec)
    return probe(source, _factory(tmp_path, seam=seam), case)


def _codes(report: dict) -> list[tuple[str, str]]:
    return sorted((item["code"], item["module"]) for item in report["findings"])


def test_clean_cuts_are_ready_and_counted(tmp_path: Path) -> None:
    report = _probe(
        tmp_path,
        _spec(_slice_imports={
            "continuity": {"app.models": ["Continuity"], "app.authority": ["generate_statement"]},
        }),
    )
    assert report["ready"] is True
    assert report["findings"] == []
    assert report["summary"] == {
        "modules_declared": 4,
        "modules_sliced": 4,
        "imports_examined": 1,
        "seam_checked": 4,
        "constants_compared": 0,
    }


def test_probe_leaves_nothing_beside_the_source(tmp_path: Path) -> None:
    _probe(tmp_path, _spec())
    assert sorted(path.name for path in (tmp_path / "case").iterdir()) == ["global_spec.json"]


def test_models_importing_an_operation_is_blocked(tmp_path: Path) -> None:
    report = _probe(
        tmp_path, _spec(_slice_imports={"models": {"app.authority": ["owner_statement"]}})
    )
    assert report["ready"] is False
    assert _codes(report) == [("models_imports_operation", "models")]
    assert report["findings"][0]["symbols"] == ["owner_statement"]


def test_import_named_like_an_own_parameter_is_blocked(tmp_path: Path) -> None:
    report = _probe(
        tmp_path,
        _spec(_slice_imports={
            "continuity": {"app.authority": ["owner_statement"]},
            # the same import in a module that has no such parameter is an ordinary call
            "store": {"app.authority": ["owner_statement"]},
        }),
    )
    assert _codes(report) == [("import_shadows_own_parameter", "continuity")]
    assert report["findings"][0]["symbol"] == "owner_statement"


def test_value_in_a_cut_is_blocked_with_its_addresses(tmp_path: Path) -> None:
    report = _probe(
        tmp_path,
        _spec(_slice_rules={"store": {"store_layout": {"file": "db.sqlite"}}, "continuity": {}}),
    )
    assert _codes(report) == [("data_in_model_context", "store")]
    assert report["findings"][0]["addresses"] == ["rules.store_layout"]


def test_every_stop_is_reported_in_one_pass(tmp_path: Path) -> None:
    report = _probe(
        tmp_path,
        _spec(
            _slice_imports={
                "models": {"app.authority": ["owner_statement"]},
                "continuity": {"app.authority": ["owner_statement"]},
            },
            _slice_rules={"store": {"store_layout": "x"}},
        ),
    )
    assert _codes(report) == [
        ("data_in_model_context", "store"),
        ("import_shadows_own_parameter", "continuity"),
        ("models_imports_operation", "models"),
    ]


def test_module_the_slicer_cannot_cut_is_blocked(tmp_path: Path) -> None:
    report = _probe(tmp_path, _spec(_slicer_rejects=["store"]))
    assert _codes(report) == [("factory_slice_failed", "store")]
    assert report["summary"]["modules_sliced"] == 3
    assert "cannot cut store" in report["findings"][0]["detail"]


def test_normalizer_refusal_is_blocked(tmp_path: Path) -> None:
    report = _probe(tmp_path, _spec(_normalizer_rejects=True))
    assert _codes(report) == [("factory_normalization_failed", "")]


def test_factory_without_a_slicer_is_blocked(tmp_path: Path) -> None:
    source = tmp_path / "case/global_spec.json"
    _write_json(source, _spec())
    report = probe(source, tmp_path / "no-factory")
    assert _codes(report) == [("factory_slicer_missing", "")]


def test_factory_without_a_seam_still_checks_imports(tmp_path: Path) -> None:
    report = _probe(
        tmp_path,
        _spec(_slice_imports={"models": {"app.authority": ["owner_statement"]}}),
        seam=False,
    )
    assert _codes(report) == [("models_imports_operation", "models")]
    assert report["summary"]["seam_checked"] == 0


def _provider_case(tmp_path: Path, *, rule_value: object, lowered_from: object) -> tuple[Path, dict]:
    case = tmp_path / "case"
    backend = {
        "kind": "data_provider_backend",
        "schema_version": 1,
        "wiring": {"module": "data_provider"},
        "constants": {
            "STORE_FILE_NAME": {"value_type": "string", "value": "db.sqlite"},
            "RESTORED_STATE": {"value_type": "string", "value": "restored"},
            "DELAYS": {
                "value_type": "record_tuple",
                "row_model": "DelayRule",
                "value": [
                    {"failure_count": 2, "delay_seconds": 4},
                    {"failure_count": 1, "delay_seconds": 0},
                ],
            },
        },
    }
    _write_json(case / "70_data_provider_closure.json", {"lowered_from": lowered_from, "backend_ir": backend})
    spec = _spec(rules={
        "store_layout": {"file": rule_value, "states": ["new", "continuous", "restored"]},
        "throttle": {"delays": [0, 4]},
        "data_provider_backend": backend,
    })
    return case, spec


LOWERED_FROM = {
    "STORE_FILE_NAME": "rules.store_layout.file",
    "RESTORED_STATE": "rules.store_layout.states[2]",
    "DELAYS": "rules.throttle.delays",
}


def test_lowering_equal_to_its_sources_is_ready(tmp_path: Path) -> None:
    case, spec = _provider_case(tmp_path, rule_value="db.sqlite", lowered_from=LOWERED_FROM)
    report = _probe(tmp_path, spec, case=case)
    assert report["findings"] == []
    assert report["summary"]["constants_compared"] == 3


def test_lowering_drift_names_the_constant_and_its_address(tmp_path: Path) -> None:
    case, spec = _provider_case(tmp_path, rule_value="store.sqlite", lowered_from=LOWERED_FROM)
    report = _probe(tmp_path, spec, case=case)
    assert _codes(report) == [("data_provider_lowering_drift", "data_provider")]
    assert report["findings"][0]["symbol"] == "STORE_FILE_NAME"
    assert report["findings"][0]["address"] == "rules.store_layout.file"


def test_constant_without_a_source_and_unresolved_source_are_blocked(tmp_path: Path) -> None:
    lowered = {"STORE_FILE_NAME": "rules.store_layout.absent", "DELAYS": "rules.throttle.delays"}
    case, spec = _provider_case(tmp_path, rule_value="db.sqlite", lowered_from=lowered)
    report = _probe(tmp_path, spec, case=case)
    assert _codes(report) == [
        ("data_provider_constant_without_source", "data_provider"),
        ("data_provider_source_unresolved", "data_provider"),
    ]


def test_closure_that_is_not_the_assembled_backend_is_blocked(tmp_path: Path) -> None:
    case, spec = _provider_case(tmp_path, rule_value="db.sqlite", lowered_from=LOWERED_FROM)
    spec["rules"]["data_provider_backend"] = {"kind": "data_provider_backend", "constants": {}}
    report = _probe(tmp_path, spec, case=case)
    assert ("data_provider_not_assembled", "data_provider") in _codes(report)


def test_provider_without_declared_sources_is_not_compared(tmp_path: Path) -> None:
    case, spec = _provider_case(tmp_path, rule_value="other", lowered_from=None)
    report = _probe(tmp_path, spec, case=case)
    assert report["findings"] == []
    assert report["summary"]["constants_compared"] == 0


def test_admission_check_reports_not_applicable_pass_and_block(tmp_path: Path) -> None:
    factory = _factory(tmp_path)
    empty = tmp_path / "empty/global_spec.json"
    _write_json(empty, {"standard_version": 2, "contracts": {}})
    assert _factory_slices_check(factory, empty, None).status == "NOT_APPLICABLE"

    clean = tmp_path / "clean/global_spec.json"
    _write_json(clean, _spec())
    passed = _factory_slices_check(factory, clean, None)
    assert (passed.check_id, passed.status) == ("FA018", "PASS")
    assert passed.evidence["summary"]["modules_sliced"] == 4

    broken = tmp_path / "broken/global_spec.json"
    _write_json(broken, _spec(_slice_rules={"store": {"store_layout": "x"}}))
    blocked = _factory_slices_check(factory, broken, None)
    assert blocked.status == "BLOCK"
    assert [item["code"] for item in blocked.evidence["findings"]] == ["data_in_model_context"]
