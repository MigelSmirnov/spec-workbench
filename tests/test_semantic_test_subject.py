from __future__ import annotations

import json
from pathlib import Path

import pytest

import export_to_factory
from factory_admission_workbench.model import CHECK_BLOCK, CHECK_PASS
from factory_admission_workbench.service import _semantic_check


DECISION = """# State 2

## Accepted decision A05 — a proof reports the first failure

### Normative rules

1. A proof checks one fixed order.
"""


def _case(tmp_path: Path, entries: list[dict[str, str]]) -> Path:
    case = tmp_path / "case"
    (case / "tests/semantic").mkdir(parents=True)
    (case / "02_rules.md").write_text(DECISION, encoding="utf-8")
    for entry in entries:
        (case / entry["path"]).write_text("def test_x():\n    pass\n", encoding="utf-8")
    (case / "71_semantic_test_export.json").write_text(
        json.dumps(
            {
                "schema_version": export_to_factory.SEMANTIC_EXPORT_SCHEMA,
                "status": "semantic_closed",
                "source_dir": "tests/semantic",
                "target_dir": "tests/semantic",
                "flows": entries,
            }
        ),
        encoding="utf-8",
    )
    (case / "global_spec.json").write_text("{}", encoding="utf-8")
    return case


FLOW = {"flow_id": "flow:accept_upload", "path": "tests/semantic/test_flow.py"}
WITNESS = {"decision_id": "A05", "path": "tests/semantic/test_a05.py"}


def test_flow_and_decision_subjects_export_and_carry_into_handoff(tmp_path: Path) -> None:
    case = _case(tmp_path, [FLOW, WITNESS])
    plan = export_to_factory.semantic_export_plan(case / "global_spec.json", "case")

    handoff = export_to_factory.export_semantic_tests(plan, tmp_path / "factory/projects/p", False)

    subjects = [{k: v for k, v in f.items() if k in ("flow_id", "decision_id")} for f in handoff["files"]]
    assert subjects == [{"flow_id": "flow:accept_upload"}, {"decision_id": "A05"}]
    assert _semantic_check(case).status == CHECK_PASS


@pytest.mark.parametrize(
    "entry, reason",
    [
        ({"path": "tests/semantic/test_none.py"}, "exactly one of flow_id, decision_id"),
        (
            {"flow_id": "flow:x", "decision_id": "A05", "path": "tests/semantic/test_both.py"},
            "exactly one of flow_id, decision_id",
        ),
        ({"decision_id": "A99", "path": "tests/semantic/test_a99.py"}, "not an accepted decision of the case"),
        ({"decision_id": "M01", "path": "tests/semantic/test_m01.py"}, "not an accepted decision id"),
        ({"flow_id": "", "path": "tests/semantic/test_empty.py"}, "empty flow_id"),
    ],
)
def test_entry_without_exactly_one_existing_subject_is_refused_by_export_and_admission(
    tmp_path: Path, entry: dict[str, str], reason: str
) -> None:
    case = _case(tmp_path, [entry])

    with pytest.raises(SystemExit, match=reason):
        export_to_factory.semantic_export_plan(case / "global_spec.json", "case")

    admission = _semantic_check(case)
    assert admission.status == CHECK_BLOCK
    assert any(reason in error for error in admission.evidence["errors"])
