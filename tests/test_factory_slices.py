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
        "changed_addresses_asked": 0,
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


def _factory_with_project(tmp_path: Path, *, previous_spec: dict, carried: list[str] | None) -> Path:
    """A Factory that already holds the project, with a delta tool and a reachability resolver.

    The fake resolver calls an address reachable exactly when some note names it
    with `= <address>`; the fake delta reports `_changed_addresses` of the new spec.
    """
    root = _factory(tmp_path)
    _write(root / "SPEC_STANDARD.md", "standard")
    _write(root / "tools/validate_spec.py", "")
    _write(root / "tools/bootstrap_project.py", "")
    _write_json(root / "project_index/structure.json", {
        "projects_dir": "projects",
        "files": {"global_spec": "specs/base/global_spec.json"},
        "dirs": {"working": "specs/working"},
    })
    _write(
        root / "tools/project_spec_delta.py",
        """import argparse, json
p = argparse.ArgumentParser()
p.add_argument('--project'); p.add_argument('--old-spec'); p.add_argument('--new-spec')
a = p.parse_args()
new = json.load(open(a.new_spec, encoding='utf-8'))
print(json.dumps({'status': 'pass', 'changed_modules': ['store'],
                  'changed_addresses': new.get('_changed_addresses', []), 'unresolved_addresses': []}))
""",
    )
    _write(
        root / "tools/spec_data_reachability.py",
        """def resolve_data_addresses(spec, changed):
    text = ' '.join(spec.get('notes') or [])
    out = []
    for address in changed:
        cursor, found = spec, True
        for segment in address.split('.'):
            if isinstance(cursor, dict) and segment in cursor:
                cursor = cursor[segment]
            else:
                found = False
        if not found:
            out.append({'address': address, 'reason': 'address_missing'})
        elif ('= ' + address) not in text:
            out.append({'address': address, 'reason': 'no_module_consumer'})
    return {'unresolved_addresses': out}
""",
    )
    canonical = root / "projects/demo/specs/base/global_spec.json"
    _write_json(canonical, previous_spec)
    if carried is not None:
        import hashlib
        sha = hashlib.sha256(canonical.read_bytes()).hexdigest()
        _write_json(root / "projects/demo/specs/working/spec_editor_manifest.json", {
            "accepted": True, "status": "pass",
            "outputs": {"base_spec_sha256_after": sha},
            "change_summary": {"changed_addresses": carried},
        })
    return root


def _reach(tmp_path: Path, spec: dict, *, carried: list[str] | None, project: str | None = "demo") -> dict:
    factory = _factory_with_project(tmp_path, previous_spec=_spec(), carried=carried)
    source = tmp_path / "case/global_spec.json"
    _write_json(source, spec)
    return probe(source, factory, None, project)


RULES = {"store_layout": {"file_name": "db.sqlite", "mode": "strict"}, "retention": {"days": "30"}}


def test_changed_address_with_a_consumer_is_ready(tmp_path: Path) -> None:
    report = _reach(
        tmp_path,
        _spec(rules=RULES, notes=["open_store: [RULE_REFERENCE] MUST use = rules.store_layout.file_name"],
              _changed_addresses=["rules.store_layout.file_name"]),
        carried=None,
    )
    assert report["findings"] == []
    assert report["summary"]["changed_addresses_asked"] == 1


def test_address_carried_from_an_uncarried_handoff_is_asked_too(tmp_path: Path) -> None:
    # This handoff changes nothing in data; the previous accepted one, which no
    # passing route carried, changed two addresses that no module consumes now.
    report = _reach(
        tmp_path,
        _spec(rules=RULES, notes=[], _changed_addresses=[]),
        carried=["rules.store_layout.file_name", "rules.store_layout.mode", "rules.retention.days"],
    )
    assert _codes(report) == [("changed_data_without_consumer", ""), ("changed_data_without_consumer", "")]
    by_namespace = {item["namespace"]: item["addresses"] for item in report["findings"]}
    assert by_namespace == {
        "rules.retention": ["rules.retention.days"],
        "rules.store_layout": ["rules.store_layout.file_name", "rules.store_layout.mode"],
    }
    assert "SPEC_STANDARD 15.3" in report["findings"][0]["message"]
    assert report["summary"]["changed_addresses_asked"] == 3


def test_deleted_address_is_not_an_orphan(tmp_path: Path) -> None:
    report = _reach(
        tmp_path, _spec(rules={}, notes=[], _changed_addresses=[]), carried=["rules.store_layout.file_name"]
    )
    assert report["findings"] == []
    assert report["summary"]["changed_addresses_asked"] == 1


def test_without_a_project_nothing_is_asked(tmp_path: Path) -> None:
    report = _reach(
        tmp_path, _spec(rules=RULES, notes=[], _changed_addresses=["rules.retention.days"]),
        carried=None, project=None,
    )
    assert report["findings"] == []
    assert report["summary"]["changed_addresses_asked"] == 0


def test_project_the_factory_does_not_hold_yet_is_not_asked(tmp_path: Path) -> None:
    report = _reach(
        tmp_path, _spec(rules=RULES, notes=[], _changed_addresses=["rules.retention.days"]),
        carried=None, project="brand-new",
    )
    assert report["findings"] == []
    assert report["summary"]["changed_addresses_asked"] == 0


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
