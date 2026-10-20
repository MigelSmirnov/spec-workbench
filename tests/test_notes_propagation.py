from __future__ import annotations

import json

from notes_workbench import propagation


def _project(tmp_path, *, source: str, notes: list[str], contracts=None, module_functions=None):
    (tmp_path / "80_notes.md").write_text(source, encoding="utf-8")
    spec = {
        "contracts": contracts or {},
        "module_functions": module_functions or {},
        "notes": notes,
    }
    (tmp_path / "global_spec.json").write_text(
        json.dumps(spec, indent=2) + "\n",
        encoding="utf-8",
    )
    return tmp_path


def _assembled_notes(project):
    return json.loads((project / "global_spec.json").read_text(encoding="utf-8"))["notes"]


def test_modal_repair_replaces_exact_canonical_note_and_preserves_modular_note(tmp_path):
    old = "parse: [BEHAVIOR] Return the parsed value.\n"
    new = "parse: [BEHAVIOR] MUST return the parsed value.\n"
    modular = "Parser.parse: [PROVENANCE] MUST preserve the source offset."
    project = _project(
        tmp_path,
        source=new,
        notes=["parse: [BEHAVIOR] Return the parsed value.", modular],
    )

    report = propagation.propagate(project, base_text=old)

    assert report["status"] == "applied"
    assert report["summary"]["replacements"] == 1
    assert _assembled_notes(project) == [
        "parse: [BEHAVIOR] MUST return the parsed value.",
        modular,
    ]


def test_new_canonical_note_is_inserted_without_rebuilding_other_notes(tmp_path):
    old = "first: [BEHAVIOR] MUST keep the first value.\n"
    new = (
        "first: [BEHAVIOR] MUST keep the first value.\n"
        "second: [BEHAVIOR] MUST keep the second value.\n"
    )
    modular = "Other.method: [BEHAVIOR] MUST remain untouched."
    project = _project(
        tmp_path,
        source=new,
        notes=["first: [BEHAVIOR] MUST keep the first value.", modular],
    )

    report = propagation.propagate(project, base_text=old)

    assert report["status"] == "applied"
    assert "second: [BEHAVIOR] MUST keep the second value." in _assembled_notes(project)
    assert modular in _assembled_notes(project)


def test_wrong_assembly_only_dependency_bindings_are_reconciled(tmp_path):
    old = "calculate: [BEHAVIOR] MUST calculate.\n"
    new = (
        old
        + "handle: [DEPENDENCY_BOUNDARY] MUST obtain the exact PlanActualService "
        "bound to request.app.state.plan_actual and pass it to calculate.\n"
    )
    wrong_archive = (
        "handle: [DEPENDENCY_BOUNDARY] MUST obtain the exact DurableArchiveService "
        "bound to request.app.state.archive and pass it to calculate."
    )
    wrong_gateway = (
        "handle: [DEPENDENCY_BOUNDARY] MUST obtain the exact HoldedGatewayService "
        "bound to request.app.state.holded_gateway and pass it to calculate."
    )
    project = _project(
        tmp_path,
        source=new,
        notes=[
            "calculate: [BEHAVIOR] MUST calculate.",
            wrong_archive,
            wrong_gateway,
        ],
        contracts={
            "create_app": (
                "(archive: DurableArchiveService, holded_gateway: HoldedGatewayService, "
                "plan_actual: PlanActualService) -> FastAPI"
            ),
            "handle": "(request: Request) -> None",
            "calculate": "(service: PlanActualService) -> None",
        },
        module_functions={"api": ["handle"], "plan_actual": ["calculate"]},
    )

    report = propagation.propagate(project, base_text=old)

    correct = (
        "handle: [DEPENDENCY_BOUNDARY] MUST obtain the exact PlanActualService "
        "bound to request.app.state.plan_actual and pass it to calculate."
    )
    notes = _assembled_notes(project)
    assert report["status"] == "applied"
    assert report["summary"]["dependency_binding_blocks_before"] == 2
    assert report["summary"]["dependency_binding_blocks_after"] == 0
    assert wrong_archive not in notes
    assert wrong_gateway not in notes
    assert correct in notes


def test_ambiguous_assembly_only_scope_class_fails_closed(tmp_path):
    old = ""
    new = "handle: [BEHAVIOR] MUST return the exact result.\n"
    existing = "handle: [BEHAVIOR] MUST return a cached result."
    project = _project(tmp_path, source=new, notes=[existing])

    report = propagation.propagate(project, base_text=old)

    assert report["status"] == "blocked"
    assert report["written"] is False
    assert _assembled_notes(project) == [existing]
    assert {item["code"] for item in report["findings"]} == {
        "ambiguous_scope_class_match",
        "canonical_note_not_closed",
    }


def test_check_mode_does_not_write(tmp_path):
    old = "parse: [BEHAVIOR] Return the parsed value.\n"
    new = "parse: [BEHAVIOR] MUST return the parsed value.\n"
    project = _project(
        tmp_path,
        source=new,
        notes=["parse: [BEHAVIOR] Return the parsed value."],
    )

    report = propagation.propagate(project, base_text=old, write=False)

    assert report["status"] == "drift"
    assert report["changed"] is True
    assert report["written"] is False
    assert _assembled_notes(project) == ["parse: [BEHAVIOR] Return the parsed value."]


def test_removed_canonical_note_is_deleted_by_exact_identity(tmp_path):
    old = (
        "keep: [BEHAVIOR] MUST keep the value.\n"
        "drop: [BEHAVIOR] MUST drop the value.\n"
    )
    new = "keep: [BEHAVIOR] MUST keep the value.\n"
    modular = "Other.drop: [BEHAVIOR] MUST remain."
    project = _project(
        tmp_path,
        source=new,
        notes=[
            "keep: [BEHAVIOR] MUST keep the value.",
            "drop: [BEHAVIOR] MUST drop the value.",
            modular,
        ],
    )

    report = propagation.propagate(project, base_text=old)

    assert report["status"] == "applied"
    assert _assembled_notes(project) == [
        "keep: [BEHAVIOR] MUST keep the value.",
        modular,
    ]


# --- stale propagated notes (collab letter 005) --------------------------------
#
# Propagation diffs 80_notes.md at the base revision against the working tree.
# A note that an earlier, uncommitted propagation wrote into global_spec.json is
# in neither of the two, so a second run never removed it: rewriting a note
# between two runs left both versions, and --check reported in_sync.

import subprocess

SIBLING = "show: [FIELD_PROJECTION] MUST show an attempt with every field copied."
V1 = "show: [FIELD_PROJECTION] MUST show every other record with every field copied."
V2 = "show: [FIELD_PROJECTION] MUST show each other record as its own handler shows it."


def _git(cwd, *args):
    subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True)


def _committed_case(tmp_path):
    """A case committed with one canonical note under show/[FIELD_PROJECTION]."""
    case = tmp_path / "case"
    case.mkdir()
    _project(case, source=SIBLING + "\n", notes=[SIBLING])
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "-c", "user.email=t@t", "-c", "user.name=t", "add", ".")
    _git(tmp_path, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "base")
    return case


def test_rewriting_a_note_between_two_uncommitted_runs_leaves_no_stale_version(tmp_path):
    case = _committed_case(tmp_path)

    (case / "80_notes.md").write_text(SIBLING + "\n" + V1 + "\n", encoding="utf-8")
    first = propagation.propagate(case, base_ref="HEAD")
    assert first["status"] == "applied"
    assert _assembled_notes(case) == [SIBLING, V1]

    (case / "80_notes.md").write_text(SIBLING + "\n" + V2 + "\n", encoding="utf-8")
    second = propagation.propagate(case, base_ref="HEAD")

    # Fails closed: before the fix this run wrote [SIBLING, V2, V1].
    assert second["status"] == "blocked"
    assert [f["note"] for f in second["findings"] if f["code"] == "stale_propagated_note"] == [V1]
    assert _assembled_notes(case) == [SIBLING, V1]

    third = propagation.propagate(case, base_ref="HEAD", prune_stale=True)

    assert third["status"] == "applied"
    assert third["summary"]["stale_notes"] == 1
    assert _assembled_notes(case) == [SIBLING, V2]
    assert propagation.propagate(case, base_ref="HEAD", write=False)["status"] == "in_sync"


def test_check_does_not_report_in_sync_while_a_stale_version_remains(tmp_path):
    case = _committed_case(tmp_path)
    # The state the defect left behind: both versions in the assembled notes.
    (case / "80_notes.md").write_text(SIBLING + "\n" + V2 + "\n", encoding="utf-8")
    spec = json.loads((case / "global_spec.json").read_text(encoding="utf-8"))
    spec["notes"] = [SIBLING, V1, V2]
    (case / "global_spec.json").write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")

    report = propagation.propagate(case, base_ref="HEAD", write=False)

    assert report["status"] != "in_sync"
    assert report["ready"] is False
    assert [f["note"] for f in report["findings"] if f["code"] == "stale_propagated_note"] == [V1]


def test_note_added_then_removed_before_commit_is_reported(tmp_path):
    case = _committed_case(tmp_path)
    extra = "show: [FIELD_PROJECTION] MUST show a draft with every field copied."
    (case / "80_notes.md").write_text(SIBLING + "\n" + extra + "\n", encoding="utf-8")
    assert propagation.propagate(case, base_ref="HEAD")["status"] == "applied"

    (case / "80_notes.md").write_text(SIBLING + "\n", encoding="utf-8")
    report = propagation.propagate(case, base_ref="HEAD", write=False)

    assert report["status"] == "blocked"
    assert [f["note"] for f in report["findings"] if f["code"] == "stale_propagated_note"] == [extra]


def test_assembled_note_of_another_scope_added_since_base_is_left_alone(tmp_path):
    case = _committed_case(tmp_path)
    modular = "Other.method: [BEHAVIOR] MUST remain untouched."
    spec = json.loads((case / "global_spec.json").read_text(encoding="utf-8"))
    spec["notes"] = [SIBLING, modular]
    (case / "global_spec.json").write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")

    report = propagation.propagate(case, base_ref="HEAD", write=False)

    assert report["status"] == "in_sync"
    assert report["findings"] == []
