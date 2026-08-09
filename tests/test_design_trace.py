from __future__ import annotations

import json
from pathlib import Path

import design_trace


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _project(tmp_path: Path) -> Path:
    project = tmp_path / "demo"
    _write(
        project / "02_rules.md",
        """# State 2 — Rules

## Accepted decision A1 — Runtime rule

### Normative rules

1. Do it.

## Accepted decision A2 — Release governance

### Normative rules

1. Govern it.
""",
    )
    _write(
        project / "30_modules.md",
        """# State 3 — Module responsibilities

## `archive`

### Trace inputs

- A1

### Owns

- archive behavior.

### Knows

- rule semantics.

### Hides

- sequencing.

### Must not own

- release governance.

### Candidate public capabilities

```text
store_record
```

### Depth assessment

Deep module.
""",
    )
    _write(
        project / "30_trace.json",
        json.dumps(
            {
                "schema_version": design_trace.TRACE_SCHEMA,
                "decisions": {
                    "A1": {
                        "primary_owner": "module:archive",
                        "consumers": [],
                    },
                    "A2": {
                        "disposition": "deployment_process",
                        "reason": "Owned by release governance.",
                        "consumers": [],
                    },
                },
            }
        ),
    )
    return project


def test_complete_trace_has_one_owner_or_disposition_per_state2_decision(tmp_path: Path) -> None:
    report = design_trace.analyze(_project(tmp_path))

    assert report["summary"] == {
        "state2_decisions": 2,
        "trace_entries": 2,
        "owned": 1,
        "dispositioned": 1,
        "unclaimed": 0,
        "errors": 0,
        "warnings": 0,
    }
    assert report["decisions"]["A1"]["primary_owner"] == "module:archive"
    assert report["decisions"]["A2"]["disposition"] == "deployment_process"


def test_unclaimed_decision_is_transition_error(tmp_path: Path) -> None:
    project = _project(tmp_path)
    path = project / "30_trace.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    del payload["decisions"]["A2"]
    path.write_text(json.dumps(payload), encoding="utf-8")

    report = design_trace.analyze(project)

    assert report["summary"]["unclaimed"] == 1
    assert any(f["code"] == "unclaimed_state2_decision" for f in report["findings"])


def test_unknown_primary_owner_is_error(tmp_path: Path) -> None:
    project = _project(tmp_path)
    path = project / "30_trace.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["decisions"]["A1"]["primary_owner"] = "module:missing"
    path.write_text(json.dumps(payload), encoding="utf-8")

    report = design_trace.analyze(project)

    assert any(f["code"] == "unknown_primary_owner" for f in report["findings"])


def test_disposition_requires_reason(tmp_path: Path) -> None:
    project = _project(tmp_path)
    path = project / "30_trace.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["decisions"]["A2"]["reason"] = ""
    path.write_text(json.dumps(payload), encoding="utf-8")

    report = design_trace.analyze(project)

    assert any(f["code"] == "missing_disposition_reason" for f in report["findings"])


def test_handoff_carries_stable_modules_capabilities_and_backward_trace(tmp_path: Path) -> None:
    payload = design_trace.handoff(_project(tmp_path))

    assert payload["schema_version"] == design_trace.HANDOFF_SCHEMA
    assert payload["modules"][0]["key"] == "module:archive"
    assert payload["capabilities"][0]["key"] == "capability:archive.store_record"
    assert payload["state2_trace"]["A1"]["primary_owner"] == "module:archive"
    assert payload["trace_summary"]["errors"] == 0
