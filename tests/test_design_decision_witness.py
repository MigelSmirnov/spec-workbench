from __future__ import annotations

import json
from pathlib import Path

import yaml

import design_decision_witness

ROOT = Path(__file__).resolve().parents[1]
CABINET_WEB = ROOT / "examples" / "cabinet-web-backend"

DECISION_MD = """# State 2 — Rules

## Accepted decision A90 — downloads stream and stay bounded

### Normative rules

1. Retrieval returns a bounded streaming response.

### Formal invariants

```text
download_served -> memory_bounded
```

### Required tests

1. Large downloads stream and never buffer fully.
   {tag1}
2. Unauthorized download is rejected.
   {tag2}

### Consequence

Custody stays a byte concern.
"""


def _case(tmp_path: Path, tag1: str = "", tag2: str = "",
          check_names: list[str] | None = None,
          notes: list[str] | None = None) -> tuple[Path, Path]:
    case = tmp_path / "case"
    case.mkdir()
    (case / "02_rules.md").write_text(DECISION_MD.format(tag1=tag1, tag2=tag2), encoding="utf-8")
    (case / "90_factory_target.json").write_text(json.dumps({
        "schema_version": "spec_workbench_factory_target.v1",
        "case": "case", "factory_project": "Demo",
    }), encoding="utf-8")
    if notes is not None:
        (case / "global_spec.json").write_text(json.dumps({"notes": notes}), encoding="utf-8")
    factory = tmp_path / "factory"
    if check_names is not None:
        config_dir = factory / "verification" / "configs"
        config_dir.mkdir(parents=True)
        (config_dir / "Demo.yaml").write_text(yaml.safe_dump({
            "checks": {"commands": [{"name": name, "command": ["true"]} for name in check_names]},
        }), encoding="utf-8")
    return case, factory


def test_invariants_without_any_witness_stop(tmp_path):
    case, factory = _case(tmp_path, check_names=[], notes=[])
    report = design_decision_witness.coverage(case, factory)
    assert report["summary"] == {
        "decisions_with_invariants": 1, "witnessed": 0, "unwitnessed": 1,
        "errors": 1, "handoff_ready": False,
    }
    assert [f["code"] for f in report["findings"]] == ["decision_without_witness"]
    assert report["findings"][0]["severity"] == "error"
    assert "name the accepted decision" in report["findings"][0]["hint"]
    assert report["findings"][0]["decision"] == "A90"


def test_resolvable_verification_and_note_witnesses_pass(tmp_path):
    case, factory = _case(
        tmp_path,
        tag1="[witness: verification:streaming_download_behavior]",
        tag2="[witness: note:serve_source_download]",
        check_names=["streaming_download_behavior"],
        notes=["serve_source_download: [TEST_EVIDENCE] MUST stream; verified by the behavior check."],
    )
    report = design_decision_witness.coverage(case, factory)
    assert report["summary"]["witnessed"] == 1
    assert report["summary"]["errors"] == 0
    assert report["findings"] == []


def test_claimed_but_absent_witness_blocks(tmp_path):
    case, factory = _case(
        tmp_path,
        tag1="[witness: verification:no_such_check]",
        check_names=["streaming_download_behavior"], notes=[],
    )
    report = design_decision_witness.coverage(case, factory)
    assert report["summary"]["handoff_ready"] is False
    finding = report["findings"][0]
    assert finding["code"] == "witness_unresolved" and "no_such_check" in finding["message"]


def test_note_witness_requires_test_evidence_marker(tmp_path):
    case, factory = _case(
        tmp_path,
        tag1="[witness: note:serve_source_download]",
        check_names=[],
        notes=["serve_source_download: [BEHAVIOR] MUST stream."],
    )
    report = design_decision_witness.coverage(case, factory)
    assert [f["code"] for f in report["findings"]] == ["witness_unresolved"]


def test_missing_factory_is_unverifiable_and_stops(tmp_path):
    case, factory = _case(
        tmp_path,
        tag1="[witness: verification:streaming_download_behavior]",
        check_names=None, notes=[],
    )
    report = design_decision_witness.coverage(case, tmp_path / "absent-factory")
    assert report["summary"]["handoff_ready"] is False
    assert [f["code"] for f in report["findings"]] == ["witness_unverifiable"]


def test_real_case_stops_on_untagged_decisions(tmp_path):
    report = design_decision_witness.coverage(CABINET_WEB, ROOT.parent.parent / "code_factory")
    assert report["summary"]["decisions_with_invariants"] > 5
    assert report["summary"]["handoff_ready"] is False
    codes = {f["code"] for f in report["findings"]}
    assert codes <= {"decision_without_witness", "witness_unverifiable"}
