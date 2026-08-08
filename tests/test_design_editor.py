from __future__ import annotations

import os
import stat
from dataclasses import replace
from pathlib import Path

import pytest

import design_editor


DOCUMENT = (
    b"# State 2\r\n"
    b"\r\n"
    b"## Accepted decision A51 \xe2\x80\x94 Publish\r\n"
    b"\r\n"
    b"Intro.\r\n"
    b"\r\n"
    b"### Consequence\r\n"
    b"Old consequence.\r\n"
    b"\r\n"
    b"### Rules\r\n"
    b"Keep bytes.\r\n"
    b"\r\n"
    b"## Accepted decision A52 \xe2\x80\x94 Next\r\n"
    b"Tail without EOF newline."
)


def _project(tmp_path: Path, document: bytes = DOCUMENT) -> tuple[Path, Path]:
    project = tmp_path / "demo"
    path = project / "02_rules.md"
    path.parent.mkdir(parents=True)
    path.write_bytes(document)
    return project, path


def test_replace_section_changes_only_indexed_byte_range(tmp_path: Path) -> None:
    project, path = _project(tmp_path)
    replacement = b"### Consequence\r\nNew consequence.\r\n\r\n"

    plan = design_editor.plan_edit(
        project,
        "replace-section",
        "A51",
        replacement,
        section_title="Consequence",
    )

    design_editor.assert_locality(plan)
    assert plan.before[: plan.target_start] == plan.after[: plan.target_start]
    assert plan.before[plan.target_end :] == plan.after[plan.new_target_end :]
    assert plan.after == DOCUMENT.replace(
        b"### Consequence\r\nOld consequence.\r\n\r\n",
        replacement,
    )
    assert path.read_bytes() == DOCUMENT


def test_locality_assertion_rejects_prefix_and_suffix_corruption(
    tmp_path: Path,
) -> None:
    project, _ = _project(tmp_path)
    plan = design_editor.plan_edit(
        project,
        "replace-section",
        "A51",
        b"### Consequence\r\nNew.\r\n\r\n",
        section_title="Consequence",
    )
    bad_prefix = replace(plan, after=b"X" + plan.after[1:])
    bad_suffix = replace(
        plan,
        after=(
            plan.after[: plan.new_target_end]
            + b"X"
            + plan.after[plan.new_target_end + 1 :]
        ),
    )

    with pytest.raises(design_editor.DesignEditorError, match="before the target"):
        design_editor.assert_locality(bad_prefix)
    with pytest.raises(design_editor.DesignEditorError, match="after the target"):
        design_editor.assert_locality(bad_suffix)


def test_replace_section_inside_large_item_preserves_both_neighbors(
    tmp_path: Path,
) -> None:
    large_prefix = b"".join(
        f"Prefix evidence {number}.\n".encode() for number in range(300)
    )
    large_suffix = b"".join(
        f"Suffix evidence {number}.\n".encode() for number in range(300)
    )
    before_neighbor = b"## Accepted decision A50 -- Before\nUntouched before.\n\n"
    target_heading = b"## Accepted decision A51 -- Large decision\n\n"
    target_section = b"### Consequence\nOld consequence.\n\n"
    after_neighbor = b"## Accepted decision A52 -- After\nUntouched after."
    document = (
        b"# State 2\n\n"
        + before_neighbor
        + target_heading
        + large_prefix
        + target_section
        + large_suffix
        + after_neighbor
    )
    project, path = _project(tmp_path, document)
    replacement = b"### Consequence\nNew consequence.\n\n"
    plan = design_editor.plan_edit(
        project,
        "replace-section",
        "A51",
        replacement,
        section_title="Consequence",
    )

    design_editor.apply_plan(plan)

    after = path.read_bytes()
    assert after[: plan.target_start] == document[: plan.target_start]
    assert after[plan.new_target_end :] == document[plan.target_end :]
    assert before_neighbor in after
    assert after.endswith(after_neighbor)


def test_append_section_applies_atomically_without_normalizing_file(
    tmp_path: Path,
) -> None:
    project, path = _project(tmp_path)
    os.chmod(path, 0o640)
    addition = b"Additional consequence.\r\n\r\n"
    plan = design_editor.plan_edit(
        project,
        "append-section",
        "A51",
        addition,
        section_title="Consequence",
    )

    design_editor.apply_plan(plan)

    assert plan.target_start == DOCUMENT.index(b"### Rules")
    assert path.read_bytes() == (
        DOCUMENT[: plan.target_start] + addition + DOCUMENT[plan.target_end :]
    )
    assert stat.S_IMODE(path.stat().st_mode) == 0o640
    assert not list(path.parent.glob(f".{path.name}.*.tmp"))


def test_insert_section_creates_structure_after_addressed_section(
    tmp_path: Path,
) -> None:
    project, path = _project(tmp_path)
    inserted = b"### Evidence\r\nSource is retained.\r\n\r\n"
    plan = design_editor.plan_edit(
        project,
        "insert-section",
        "A51",
        inserted,
        section_title="Consequence",
    )

    design_editor.apply_plan(plan)

    data = path.read_bytes()
    assert data[: plan.target_start] == DOCUMENT[: plan.target_start]
    assert data[plan.new_target_end :] == DOCUMENT[plan.target_end :]
    assert data[plan.target_start : plan.new_target_end] == inserted


def test_replace_item_preserves_following_document_and_missing_eof_newline(
    tmp_path: Path,
) -> None:
    project, path = _project(tmp_path)
    replacement = (
        b"## Accepted decision A51 \xe2\x80\x94 Publish\r\n"
        b"\r\n"
        b"Replacement item.\r\n"
        b"\r\n"
    )
    plan = design_editor.plan_edit(
        project,
        "replace-item",
        "a51",
        replacement,
    )

    design_editor.apply_plan(plan)

    assert path.read_bytes() == (
        DOCUMENT[: plan.target_start] + replacement + DOCUMENT[plan.target_end :]
    )
    assert path.read_bytes().endswith(b"Tail without EOF newline.")


@pytest.mark.parametrize(
    ("section", "message"),
    [
        ("Missing", "section not found"),
        ("Repeated", "section is ambiguous"),
    ],
)
def test_section_addressing_fails_closed(
    tmp_path: Path,
    section: str,
    message: str,
) -> None:
    document = (
        b"# State 2\n\n"
        b"## Accepted decision A1 -- One\n\n"
        b"### Repeated\nFirst.\n\n"
        b"### Repeated\nSecond.\n"
    )
    project, path = _project(tmp_path, document)

    with pytest.raises(design_editor.DesignEditorError, match=message):
        design_editor.plan_edit(
            project,
            "replace-section",
            "A1",
            b"### Repeated\nNew.\n",
            section_title=section,
        )

    assert path.read_bytes() == document


def test_duplicate_item_keys_fail_before_planning(tmp_path: Path) -> None:
    project, first = _project(
        tmp_path,
        b"# State 2\n\n## Accepted decision A1 -- One\n",
    )
    second = project / "other.md"
    second.write_bytes(b"# State 2\n\n## Accepted decision A1 -- Duplicate\n")
    before = first.read_bytes()

    with pytest.raises(design_editor.DesignEditorError, match="duplicate item keys"):
        design_editor.plan_edit(project, "replace-item", "A1", b"replacement")

    assert first.read_bytes() == before


def test_unknown_item_fails_without_changing_document(tmp_path: Path) -> None:
    project, path = _project(tmp_path)

    with pytest.raises(design_editor.DesignEditorError, match="item not found"):
        design_editor.plan_edit(
            project,
            "replace-item",
            "A999",
            b"## Accepted decision A999 -- Unknown\n",
        )

    assert path.read_bytes() == DOCUMENT


def test_invalid_utf8_content_fails_during_planning(tmp_path: Path) -> None:
    project, path = _project(tmp_path)

    with pytest.raises(design_editor.DesignEditorError, match="not valid UTF-8"):
        design_editor.plan_edit(
            project,
            "replace-item",
            "A51",
            b"\xff",
        )

    assert path.read_bytes() == DOCUMENT


def test_indexed_source_outside_project_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project, path = _project(tmp_path)
    outside = tmp_path / "outside.md"
    outside.write_bytes(b"## Accepted decision A1 -- Outside\n")
    fake_index = {
        "items": [
            {
                "key": "A1",
                "kind": "decision",
                "title": "Accepted decision A1 -- Outside",
                "state": 2,
                "source": {
                    "path": "../outside.md",
                    "start_line": 1,
                    "end_line": 1,
                },
                "explicit_id": "A1",
                "explicit_refs": [],
                "sections": [],
            }
        ],
        "diagnostics": {"duplicate_keys": []},
    }
    monkeypatch.setattr(design_editor, "_build_valid_index", lambda _: fake_index)

    with pytest.raises(design_editor.DesignEditorError, match="inside the project"):
        design_editor.plan_edit(
            project,
            "replace-item",
            "A1",
            b"## Accepted decision A1 -- Replacement\n",
        )

    assert path.read_bytes() == DOCUMENT
    assert outside.read_bytes() == b"## Accepted decision A1 -- Outside\n"


def test_source_key_addresses_supporting_decision(tmp_path: Path) -> None:
    document = (
        b"# State 2 decision -- manual retention release\n\n"
        b"## Accepted decision\n\n"
        b"Copies remain until explicit release.\n\n"
        b"### Consequence\n"
        b"Old consequence."
    )
    project, path = _project(tmp_path, document)
    source_key = "source:02_rules.md#accepted-decision"
    replacement = b"### Consequence\nNew consequence."
    plan = design_editor.plan_edit(
        project,
        "replace-section",
        source_key,
        replacement,
        section_title="Consequence",
    )

    design_editor.apply_plan(plan)

    assert plan.item_key == source_key
    assert path.read_bytes().endswith(replacement)


def test_replace_last_item_keeps_missing_eof_newline_exactly(tmp_path: Path) -> None:
    document = b"# State 2\n\n## Accepted decision A1 -- Last\nOld without newline."
    project, path = _project(tmp_path, document)
    replacement = b"## Accepted decision A1 -- Last\nNew without newline."
    plan = design_editor.plan_edit(
        project,
        "replace-item",
        "A1",
        replacement,
    )

    design_editor.apply_plan(plan)

    assert path.read_bytes() == b"# State 2\n\n" + replacement
    assert not path.read_bytes().endswith(b"\n")


def test_apply_rolls_back_when_reindex_finds_duplicate_key(tmp_path: Path) -> None:
    project, path = _project(tmp_path)
    plan = design_editor.plan_edit(
        project,
        "replace-item",
        "A51",
        b"## Accepted decision A52 -- Duplicate after apply\r\n",
    )

    with pytest.raises(design_editor.DesignEditorError, match="duplicate item keys"):
        design_editor.apply_plan(plan)

    assert path.read_bytes() == DOCUMENT


def test_apply_rolls_back_item_rename_without_duplicate_key(tmp_path: Path) -> None:
    project, path = _project(tmp_path)
    plan = design_editor.plan_edit(
        project,
        "replace-item",
        "A51",
        b"## Accepted decision A53 -- Renamed\r\n",
    )

    with pytest.raises(
        design_editor.DesignEditorError,
        match="created, deleted, or renamed",
    ):
        design_editor.apply_plan(plan)

    assert path.read_bytes() == DOCUMENT


def test_apply_rolls_back_when_operation_changes_wrong_structure(
    tmp_path: Path,
) -> None:
    project, path = _project(tmp_path)
    plan = design_editor.plan_edit(
        project,
        "append-section",
        "A51",
        b"### Created by the wrong operation\r\nNo.\r\n\r\n",
        section_title="Consequence",
    )

    with pytest.raises(
        design_editor.DesignEditorError,
        match="use insert-section to create a section",
    ):
        design_editor.apply_plan(plan)

    assert path.read_bytes() == DOCUMENT


def test_insert_rolls_back_when_content_does_not_create_section(
    tmp_path: Path,
) -> None:
    project, path = _project(tmp_path)
    plan = design_editor.plan_edit(
        project,
        "insert-section",
        "A51",
        b"Plain text is not a section.\r\n",
        section_title="Consequence",
    )

    with pytest.raises(design_editor.DesignEditorError, match="did not create"):
        design_editor.apply_plan(plan)

    assert path.read_bytes() == DOCUMENT


def test_insert_rolls_back_when_existing_section_structure_changes(
    tmp_path: Path,
) -> None:
    project, path = _project(tmp_path)
    inserted = (
        b"### New one\r\nOne.\r\n"
        b"### New two\r\nTwo.\r\n"
        b"### New three\r\nThree.\r\n"
        b"## Plain boundary\r\n"
    )
    plan = design_editor.plan_edit(
        project,
        "insert-section",
        "A51",
        inserted,
        section_title="Consequence",
    )

    with pytest.raises(
        design_editor.DesignEditorError,
        match="changed existing section structure",
    ):
        design_editor.apply_plan(plan)

    assert path.read_bytes() == DOCUMENT


def test_insert_rolls_back_when_new_section_title_is_ambiguous(
    tmp_path: Path,
) -> None:
    project, path = _project(tmp_path)
    plan = design_editor.plan_edit(
        project,
        "insert-section",
        "A51",
        b"### Rules\r\nDuplicate title.\r\n\r\n",
        section_title="Consequence",
    )

    with pytest.raises(design_editor.DesignEditorError, match="ambiguous section"):
        design_editor.apply_plan(plan)

    assert path.read_bytes() == DOCUMENT


def test_apply_rejects_a_stale_plan_without_overwriting_new_bytes(
    tmp_path: Path,
) -> None:
    project, path = _project(tmp_path)
    plan = design_editor.plan_edit(
        project,
        "replace-section",
        "A51",
        b"### Consequence\r\nNew.\r\n\r\n",
        section_title="Consequence",
    )
    concurrently_changed = DOCUMENT + b"\r\nConcurrent edit."
    path.write_bytes(concurrently_changed)

    with pytest.raises(design_editor.DesignEditorError, match="changed after"):
        design_editor.apply_plan(plan)

    assert path.read_bytes() == concurrently_changed


def test_cli_defaults_to_dry_run_and_prints_unified_diff(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    project, path = _project(tmp_path)
    content = tmp_path / "new-consequence.md"
    content.write_bytes(b"### Consequence\r\nPreview only.\r\n\r\n")

    exit_code = design_editor.main(
        [
            str(project),
            "replace-section",
            "A51",
            "Consequence",
            "--content-file",
            str(content),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "--- a/02_rules.md" in captured.out
    assert "+++ b/02_rules.md" in captured.out
    assert "-Old consequence." in captured.out
    assert "+Preview only." in captured.out
    assert captured.err == ""
    assert path.read_bytes() == DOCUMENT


def test_cli_apply_uses_atomic_replace(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project, path = _project(tmp_path)
    content = tmp_path / "new-consequence.md"
    replacement = b"### Consequence\r\nApplied.\r\n\r\n"
    content.write_bytes(replacement)
    real_replace = os.replace
    replacements: list[tuple[Path, Path]] = []

    def record_replace(source: str | Path, destination: str | Path) -> None:
        replacements.append((Path(source), Path(destination)))
        real_replace(source, destination)

    monkeypatch.setattr(design_editor.os, "replace", record_replace)

    exit_code = design_editor.main(
        [
            str(project),
            "replace-section",
            "A51",
            "Consequence",
            "--content-file",
            str(content),
            "--apply",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert len(replacements) == 1
    assert replacements[0][1] == path
    assert replacements[0][0].parent == path.parent
    assert "applied replace-section to A51" in captured.err
    assert replacement in path.read_bytes()
