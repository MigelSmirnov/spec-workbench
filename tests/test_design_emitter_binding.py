from __future__ import annotations

import json
from pathlib import Path

import pytest

import design_emitter_binding

ROOT = Path(__file__).resolve().parents[1]
REAL_FACTORY = ROOT.parent.parent / "code_factory"


def _case(tmp_path: Path, spec: dict | None) -> Path:
    case = tmp_path / "case"
    case.mkdir()
    if spec is not None:
        (case / "global_spec.json").write_text(json.dumps(spec), encoding="utf-8")
    return case


def _fake_factory(tmp_path: Path, payload: dict) -> Path:
    factory = tmp_path / "factory"
    (factory / "tools").mkdir(parents=True)
    (factory / "tools" / "emitter_catalog.py").write_text(
        "import json, sys\n"
        f"print(json.dumps({payload!r}))\n"
        f"raise SystemExit({0 if payload.get('bound') else 1})\n",
        encoding="utf-8",
    )
    return factory


def test_unbound_port_blocks_and_carries_the_catalog_card(tmp_path):
    case = _case(tmp_path, {"implementation_obligations": {}})
    factory = _fake_factory(tmp_path, {
        "bound": False,
        "unbound_ports": [{
            "interface": "Clock", "concrete": "SystemClock", "module": "system_clock",
            "direction": "author rules.system_clock_backend per catalog_card.ir_skeleton",
            "catalog_card": {"rule_key": "system_clock_backend", "ir_skeleton": {"kind": "system_clock_backend"}},
        }],
    })
    report = design_emitter_binding.coverage(case, factory)
    assert report["summary"] == {
        "catalog_available": True, "unbound_ports": 1, "errors": 1, "handoff_ready": False,
    }
    finding = report["findings"][0]
    assert finding["code"] == "local_port_without_deterministic_backend"
    assert finding["catalog_card"]["ir_skeleton"]["kind"] == "system_clock_backend"


def test_bound_spec_is_ready(tmp_path):
    case = _case(tmp_path, {"implementation_obligations": {}})
    factory = _fake_factory(tmp_path, {"bound": True, "unbound_ports": []})
    report = design_emitter_binding.coverage(case, factory)
    assert report["summary"]["handoff_ready"] is True
    assert report["findings"] == []


def test_missing_factory_catalog_warns_but_does_not_block(tmp_path):
    case = _case(tmp_path, {"implementation_obligations": {}})
    report = design_emitter_binding.coverage(case, tmp_path / "no-factory")
    assert report["summary"]["handoff_ready"] is True
    assert report["summary"]["catalog_available"] is False
    assert [f["code"] for f in report["findings"]] == ["factory_catalog_unavailable"]


def test_case_without_assembled_spec_stands_aside(tmp_path):
    case = _case(tmp_path, None)
    factory = _fake_factory(tmp_path, {"bound": True, "unbound_ports": []})
    report = design_emitter_binding.coverage(case, factory)
    assert report["summary"]["handoff_ready"] is True
    assert report["findings"] == []


@pytest.mark.skipif(not (REAL_FACTORY / "tools" / "emitter_catalog.py").is_file(),
                    reason="sibling factory checkout without emitter catalog")
def test_real_factory_binder_flags_a_local_port_without_backend(tmp_path):
    case = _case(tmp_path, {
        "implementation_obligations": {"Clock": {"disposition": "local", "implementations": ["SystemClock"]}},
        "module_functions": {"system_clock": ["SystemClock"]},
        "rules": {},
    })
    report = design_emitter_binding.coverage(case, REAL_FACTORY)
    assert report["summary"]["catalog_available"] is True
    assert report["summary"]["unbound_ports"] == 1
    card = report["findings"][0]["catalog_card"]
    assert card["rule_key"] == "system_clock_backend"
    assert "ir_skeleton" in card
