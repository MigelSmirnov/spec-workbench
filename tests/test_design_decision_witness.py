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
        "kept_outside": 0, "errors": 1, "handoff_ready": False,
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


def test_design_lint_gate_is_a_workbench_witness(tmp_path):
    case, factory = _case(tmp_path, tag1="[witness: workbench:state2_rules_decisions]")
    report = design_decision_witness.coverage(case, factory)
    assert report["summary"]["witnessed"] == 1
    assert report["summary"]["errors"] == 0


def test_unknown_workbench_gate_blocks(tmp_path):
    case, factory = _case(tmp_path, tag1="[witness: workbench:state9_everything]")
    report = design_decision_witness.coverage(case, factory)
    assert report["summary"]["handoff_ready"] is False
    finding = report["findings"][0]
    assert finding["code"] == "witness_unresolved" and "state9_everything" in finding["message"]


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
    assert "set SPEC_WORKBENCH_FACTORY_ROOT" in report["findings"][0]["message"]


def test_missing_pyyaml_is_named_not_reported_as_absent_config(tmp_path, monkeypatch):
    case, factory = _case(
        tmp_path,
        tag1="[witness: verification:streaming_download_behavior]",
        check_names=["streaming_download_behavior"], notes=[],
    )
    monkeypatch.setattr(design_decision_witness, "yaml", None)
    report = design_decision_witness.coverage(case, factory)
    assert report["summary"]["handoff_ready"] is False
    assert "PyYAML is not installed" in report["findings"][0]["message"]


def test_real_case_stops_on_untagged_decisions(tmp_path):
    report = design_decision_witness.coverage(CABINET_WEB, ROOT.parent.parent / "code_factory")
    assert report["summary"]["decisions_with_invariants"] > 5
    assert report["summary"]["handoff_ready"] is False
    codes = {f["code"] for f in report["findings"]}
    assert codes <= {"decision_without_witness", "witness_unverifiable"}


KEPT_OUTSIDE_MD = """# State 2 — Rules

## Accepted decision A91 — a release fixes its dependencies

### Normative rules

1. A release names every dependency at an exact version with its digest.

### Formal invariants

{invariants}

### Required tests

1. Installing the release with a dependency whose digest differs fails.

### Consequence

What runs is what was verified.
"""


def _kept_outside_case(tmp_path: Path, invariants: str) -> tuple[Path, Path]:
    case, factory = _case(tmp_path, check_names=[], notes=[])
    (case / "02_rules.md").write_text(KEPT_OUTSIDE_MD.format(invariants=invariants), encoding="utf-8")
    return case, factory


def test_guarantee_kept_outside_the_case_needs_no_witness_and_is_listed(tmp_path):
    case, factory = _kept_outside_case(
        tmp_path, "None: kept by the release process, which the case does not manage.")
    report = design_decision_witness.coverage(case, factory)
    assert report["summary"]["decisions_with_invariants"] == 0
    assert report["summary"]["kept_outside"] == 1
    assert report["summary"]["handoff_ready"] is True
    [finding] = report["findings"]
    assert finding["code"] == "invariant_kept_outside" and finding["severity"] == "info"
    assert finding["decision"] == "A91" and "release process" in finding["message"]
    assert design_decision_witness.required_tests(case)["summary"]["decisions_with_invariants"] == 0


def test_bare_none_or_none_after_a_formula_is_still_an_invariant(tmp_path):
    for index, invariants in enumerate(
            ("None", "None:", "```text\nrunning = release\n```\nNone: kept by the release process.")):
        (tmp_path / str(index)).mkdir()
        case, factory = _kept_outside_case(tmp_path / str(index), invariants)
        report = design_decision_witness.coverage(case, factory)
        assert report["summary"]["kept_outside"] == 0, invariants
        assert [f["code"] for f in report["findings"]] == ["decision_without_witness"], invariants


def test_fenced_invariants_are_one_statement_per_identifier():
    """A binding is given the invariants its Required test names, not the
    whole fenced block: the judge cannot hold a test to an invariant the
    item does not claim (registry A17, 2026-11-24)."""
    section = """### Formal invariants

```text
serving => checks_passed(config)   -- A17-1
for secrets s1 != s2 in config:
    value(s1) != value(s2)   -- A17-2
```
"""
    statements = design_decision_witness.invariant_statements(section)
    assert statements == [
        "serving => checks_passed(config)   -- A17-1",
        "for secrets s1 != s2 in config:\n    value(s1) != value(s2)   -- A17-2",
    ]
    # outside a fence the items are the section's list items, as before
    assert design_decision_witness.invariant_statements(
        "### Formal invariants\n\n1. a -- X-1\n2. b -- X-2\n"
    ) == ["1. a -- X-1", "2. b -- X-2"]
    # a fenced block without identifiers stays one statement
    assert design_decision_witness.invariant_statements(
        "```text\ndownload_served -> memory_bounded\n```\n"
    ) == ["download_served -> memory_bounded"]
