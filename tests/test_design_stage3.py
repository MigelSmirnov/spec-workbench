from __future__ import annotations

from pathlib import Path

import design_stage3
import pytest


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
            "depth": {},
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


@pytest.mark.parametrize(
    ("section", "block"),
    [
        ("Owns", "### Owns\n\n- durable record preservation.\n\n"),
        ("Knows", "### Knows\n\n- preservation semantics.\n\n"),
        ("Must not own", "### Must not own\n\n- transport.\n\n"),
        ("Depth assessment", "### Depth assessment\n\nDeep archive module.\n"),
    ],
)
def test_lint_requires_module_responsibility_sections(
    tmp_path: Path, section: str, block: str
) -> None:
    project = _project(tmp_path)
    path = project / "30_modules.md"
    path.write_text(
        path.read_text(encoding="utf-8").replace(block, ""),
        encoding="utf-8",
    )

    report = design_stage3.lint(project)

    # The fixture never declares structured depth, so the depth invariant
    # contributes its own error alongside the missing section.
    assert report["summary"]["errors"] == 2
    assert any(
        finding["code"] == "missing_module_section"
        and section in finding["message"]
        for finding in report["findings"]
    )


def test_duplicate_module_key_is_error(tmp_path: Path) -> None:
    project = _project(tmp_path)
    path = project / "30_modules.md"
    module_text = path.read_text(encoding="utf-8").split("## `archive`", 1)[1]
    path.write_text(
        path.read_text(encoding="utf-8") + "\n## `archive`" + module_text,
        encoding="utf-8",
    )

    report = design_stage3.lint(project)

    assert any(finding["code"] == "duplicate_module_key" for finding in report["findings"])


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
            "### Owns\n",
            "### Owns\n\n```text\nincidental_owned_identifier\n```\n",
        ).replace(
            "### Candidate public capabilities\n",
            "### Candidate public capabilities\n\nincidental_unfenced_identifier\n",
        ),
        encoding="utf-8",
    )

    module = design_stage3.get_module(project, "archive")

    assert module["capabilities"] == ("get_record", "store_record")


def _depth(project: Path, replacement: str) -> None:
    path = project / "30_modules.md"
    path.write_text(path.read_text(encoding="utf-8").replace("Deep archive module.\n", replacement), encoding="utf-8")


def _codes(report: dict) -> list[tuple[str, str]]:
    return sorted((f["severity"], f["code"]) for f in report["findings"])


def test_undeclared_depth_is_an_error_even_on_a_narrow_surface(tmp_path: Path) -> None:
    project = _project(tmp_path)
    report = design_stage3.lint(project)
    assert ("error", "depth_undeclared") in _codes(report)
    assert report["summary"]["errors"] >= 1
    assert "invariant" in next(
        f["message"] for f in report["findings"] if f["code"] == "depth_undeclared"
    )


def test_wide_surface_without_depth_declaration_is_an_error(tmp_path: Path) -> None:
    project = _project(tmp_path)
    path = project / "30_modules.md"
    names = "\n".join(f"op_{i}" for i in range(design_stage3.WIDE_SURFACE_CAPABILITIES))
    path.write_text(path.read_text(encoding="utf-8").replace("store_record\nget_record", names), encoding="utf-8")
    report = design_stage3.lint(project)
    assert ("error", "depth_undeclared_wide_surface") in _codes(report)
    assert "shared entity name is not cohesion" in next(
        f["message"] for f in report["findings"] if f["code"] == "depth_undeclared_wide_surface"
    )


def test_deep_module_names_its_hidden_mechanism(tmp_path: Path) -> None:
    project = _project(tmp_path)
    _depth(project, "kind: deep\nhidden mechanism: append-only record ledger with idempotent replay\n")
    report = design_stage3.lint(project)
    assert report["summary"]["errors"] == 0
    assert not any(f["code"].startswith("depth_") for f in report["findings"])
    module = design_stage3.parse_modules(project)[0]
    assert module.depth == {"kind": "deep", "hidden_mechanism": "append-only record ledger with idempotent replay"}
    assert design_stage3.handoff(project)["modules"][0]["depth"]["kind"] == "deep"


def test_deep_module_without_mechanism_is_an_error(tmp_path: Path) -> None:
    project = _project(tmp_path)
    _depth(project, "kind: deep\n")
    assert ("error", "hidden_mechanism_missing") in _codes(design_stage3.lint(project))


def test_facade_must_name_known_delegates(tmp_path: Path) -> None:
    project = _project(tmp_path)
    _depth(project, "- **kind**: facade\n- **delegates to**: `ledger`, `archive`\n")
    codes = _codes(design_stage3.lint(project))
    assert ("error", "facade_delegate_unknown") in codes
    assert ("error", "facade_delegates_to_itself") in codes
    bare = _project(tmp_path / "bare")
    _depth(bare, "kind: facade\n")
    assert ("error", "facade_delegates_missing") in _codes(design_stage3.lint(bare))


def test_facade_with_declared_delegates_is_clean(tmp_path: Path) -> None:
    project = _project(tmp_path)
    path = project / "30_modules.md"
    path.write_text(
        path.read_text(encoding="utf-8").replace("Deep archive module.\n", "kind: facade\ndelegates to: `ledger`\n")
        + """
## `ledger`

### Owns

- the record ledger.

### Knows

- ledger invariants.

### Hides

- ordering.

### Must not own

- transport.

### Candidate public capabilities

```text
append
```

### Depth assessment

kind: deep
hidden mechanism: append-only ledger
""",
        encoding="utf-8",
    )
    report = design_stage3.lint(project)
    assert report["summary"]["errors"] == 0
    assert not any(f["code"].startswith(("depth_", "facade_", "hidden_")) for f in report["findings"])


def test_invalid_depth_kind_is_an_error(tmp_path: Path) -> None:
    project = _project(tmp_path)
    _depth(project, "kind: shallow-ish\n")
    assert ("error", "invalid_depth_kind") in _codes(design_stage3.lint(project))
