from __future__ import annotations

from pathlib import Path

import design_stage3


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _project(tmp_path: Path) -> Path:
    project = tmp_path / "demo"
    _write(
        project / "30_modules.md",
        """# State 3 — Module responsibilities

## `archive`

### Owns

- durable record preservation.

### Knows

- preservation semantics.

### Hides

- persistence sequencing.

### Must not own

- transport.

### Candidate public capabilities

```text
store_record
get_record
```

### Depth assessment

Deep archive module.
""",
    )
    return project


def test_module_keys_and_capabilities_are_stable_handoff(tmp_path: Path) -> None:
    payload = design_stage3.handoff(_project(tmp_path))

    assert payload["schema_version"] == "spec_workbench_state3_handoff.v2"
    assert payload["modules"] == [
        {
            "key": "module:archive",
            "name": "archive",
            "capabilities": ["get_record", "store_record"],
            "capability_refs": [
                {"key": "capability:archive.get_record", "name": "get_record"},
                {"key": "capability:archive.store_record", "name": "store_record"},
            ],
        }
    ]
    assert payload["capabilities"] == [
        {
            "key": "capability:archive.get_record",
            "name": "get_record",
            "module": "module:archive",
        },
        {
            "key": "capability:archive.store_record",
            "name": "store_record",
            "module": "module:archive",
        },
    ]


def test_get_accepts_full_or_short_module_key(tmp_path: Path) -> None:
    project = _project(tmp_path)

    short = design_stage3.get_module(project, "archive")
    full = design_stage3.get_module(project, "module:archive")

    assert short["key"] == "module:archive"
    assert full["key"] == "module:archive"
    assert short["capability_refs"][0]["key"] == "capability:archive.get_record"


def test_lint_requires_module_responsibility_sections(tmp_path: Path) -> None:
    project = _project(tmp_path)
    path = project / "30_modules.md"
    path.write_text(
        path.read_text(encoding="utf-8").replace("### Must not own\n\n- transport.\n\n", ""),
        encoding="utf-8",
    )

    report = design_stage3.lint(project)

    assert report["summary"]["errors"] == 1
    assert any(
        finding["code"] == "missing_module_section"
        and "Must not own" in finding["message"]
        for finding in report["findings"]
    )


def test_generic_module_name_is_error(tmp_path: Path) -> None:
    project = _project(tmp_path)
    path = project / "30_modules.md"
    path.write_text(
        path.read_text(encoding="utf-8").replace("`archive`", "`utils`"),
        encoding="utf-8",
    )

    report = design_stage3.lint(project)

    assert any(finding["code"] == "generic_module_name" for finding in report["findings"])


def test_capabilities_are_read_only_from_fenced_capability_section(tmp_path: Path) -> None:
    project = _project(tmp_path)
    path = project / "30_modules.md"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "### Owns\n", "### Owns\n\nincidental_identifier\n"
        ),
        encoding="utf-8",
    )

    module = design_stage3.get_module(project, "archive")

    assert module["capabilities"] == ("get_record", "store_record")
