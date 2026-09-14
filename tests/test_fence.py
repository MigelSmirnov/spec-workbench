from __future__ import annotations

from pathlib import Path

import fence
import flow_closure
from assembly_workbench.model import CHECK_ORDER

ROOT = Path(__file__).resolve().parents[1]
CABINET = ROOT / "examples" / "cabinet-backend"


def test_enforce_raises_every_soft_finding_to_a_stop_with_a_hint():
    findings = fence.enforce([
        {"severity": "warning", "code": "module_surface_not_deep", "message": "m: 9 of 10 public"},
        {"severity": "review", "code": "duplicate_note", "message": "twice"},
        {"severity": "error", "code": "unplanned_contract", "message": "f"},
        {"severity": "info", "code": "note", "message": "just saying"},
    ])
    assert [f["severity"] for f in findings] == ["error", "error", "error", "info"]
    assert findings[0]["raised_from"] == "warning" and findings[1]["raised_from"] == "review"
    assert findings[0]["hint"] == "not decided — decide: declare the hidden mechanism this module owns in State 3, or split it along the mechanism it hides"
    assert findings[1]["hint"] == "not decided — decide: twice"
    assert findings[2]["hint"].startswith("not decided — decide: ")
    assert "hint" not in findings[3]
    assert fence.stops(findings) == 3


def test_assembly_runs_the_witness_and_flow_checks():
    assert CHECK_ORDER[-2:] == ("witness", "flows")


def test_flow_closure_stops_on_capabilities_nothing_reaches():
    report = flow_closure.coverage(CABINET)
    assert report["summary"]["flows"] > 0 and report["summary"]["capability_references"] > 0
    assert report["summary"]["handoff_ready"] is False
    codes = {f["code"] for f in report["findings"]}
    assert codes <= {"flow_capability_unreached", "flow_capability_missing"} and codes
    assert all(f["severity"] == "error" and f["hint"].startswith("not decided — decide:") for f in report["findings"])
    assert all(f["capability"].startswith("capability:") and f["flow"] for f in report["findings"])
