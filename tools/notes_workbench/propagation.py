"""Propagate canonical State 7 notes into an assembled ``global_spec.json``.

The assembled specification may contain notes lowered from modular State 7
sources whose authored shorthand is not reversible. This module therefore owns
only one narrow propagation path: exact inline notes authored in ``80_notes.md``.

Changes are derived from an explicit Git base revision (or injected base text in
tests), then applied to ``global_spec.json[\"notes\"]`` while preserving unrelated
assembled notes. Ambiguous matches fail closed.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

from notes_workbench import language
from notes_workbench.note_parser import NOTE_RE


SCHEMA_VERSION = "spec_workbench_notes_propagation.v1"
DEFAULT_SOURCE = "80_notes.md"
DEFAULT_ASSEMBLED = "global_spec.json"


class NotesPropagationError(ValueError):
    pass


def _finding(code: str, message: str, **fields: Any) -> dict[str, Any]:
    return {"severity": "block", "code": code, "message": message, **fields}


def _canonical_notes(text: str) -> list[str]:
    notes: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        match = NOTE_RE.match(line)
        if not match:
            continue
        notes.append(
            f"{match.group('scope')}: [{match.group('class')}] "
            f"{match.group('text').strip()}"
        )
    duplicates = sorted(note for note, count in Counter(notes).items() if count > 1)
    if duplicates:
        raise NotesPropagationError(
            "80_notes.md contains exact duplicate canonical notes; propagation "
            "requires unique inline note identities: " + ", ".join(duplicates)
        )
    return notes


def _note_key(note: str) -> tuple[str, str] | None:
    match = NOTE_RE.match(note.strip())
    if not match:
        return None
    return match.group("scope"), match.group("class")


def _modal_normalized(note: str) -> tuple[str, str, str] | None:
    match = NOTE_RE.match(note.strip())
    if not match:
        return None
    text = language.POSITIVE_MODAL_RE.sub("", match.group("text"))
    text = re.sub(r"\s+", " ", text).strip().casefold()
    return match.group("scope"), match.group("class"), text


def _notes_hash(notes: list[str]) -> str:
    encoded = json.dumps(notes, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _repo_root(project: Path) -> Path:
    result = subprocess.run(
        ["git", "-C", str(project), "rev-parse", "--show-toplevel"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or "not inside a Git worktree"
        raise NotesPropagationError(f"cannot resolve Git repository root: {message}")
    return Path(result.stdout.strip()).resolve()


def _read_base_source(project: Path, base_ref: str) -> str:
    if not base_ref.strip():
        raise NotesPropagationError("base_ref must be non-empty")
    root = _repo_root(project)
    source = (project / DEFAULT_SOURCE).resolve()
    try:
        relative = source.relative_to(root)
    except ValueError as exc:
        raise NotesPropagationError(
            f"{source} is outside Git repository {root}"
        ) from exc
    result = subprocess.run(
        ["git", "-C", str(root), "show", f"{base_ref}:{relative.as_posix()}"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or "git show failed"
        raise NotesPropagationError(
            f"cannot read {relative.as_posix()} from {base_ref}: {message}"
        )
    return result.stdout


def _load_spec(project: Path) -> dict[str, Any]:
    path = project / DEFAULT_ASSEMBLED
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise NotesPropagationError(f"assembled specification not found: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise NotesPropagationError(f"invalid assembled specification {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise NotesPropagationError("assembled specification must be a JSON object")
    notes = payload.get("notes")
    if not isinstance(notes, list) or not all(isinstance(item, str) for item in notes):
        raise NotesPropagationError("assembled specification 'notes' must be a list of strings")
    return payload


def _dependency_blocks(spec: dict[str, Any], note: str) -> list[dict[str, Any]]:
    probe = {
        "contracts": spec.get("contracts"),
        "notes": [note],
    }
    return [
        item
        for item in language.dependency_bindings(probe)
        if item.get("severity") == "block"
    ]


def _indices(items: list[str], value: str) -> list[int]:
    return [index for index, item in enumerate(items) if item == value]


def _same_key_indices(items: list[str], key: tuple[str, str]) -> list[int]:
    return [
        index
        for index, item in enumerate(items)
        if _note_key(item) == key
    ]


def _insertion_index(assembled: list[str], current: list[str], note: str) -> int:
    position = current.index(note)
    for previous in reversed(current[:position]):
        found = _indices(assembled, previous)
        if len(found) == 1:
            return found[0] + 1
    for following in current[position + 1 :]:
        found = _indices(assembled, following)
        if len(found) == 1:
            return found[0]
    return len(assembled)


def _prepare(
    project: Path,
    *,
    base_ref: str,
    base_text: str | None,
) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    source_path = project / DEFAULT_SOURCE
    try:
        current_text = source_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise NotesPropagationError(f"canonical notes source not found: {source_path}") from exc

    old_text = base_text if base_text is not None else _read_base_source(project, base_ref)
    old = _canonical_notes(old_text)
    current = _canonical_notes(current_text)
    old_set = set(old)
    current_set = set(current)

    spec = _load_spec(project)
    before = list(spec["notes"])
    working = list(before)
    operations: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []

    removed = [note for note in old if note not in current_set]
    added = [note for note in current if note not in old_set]
    paired_removed: set[str] = set()

    old_key_counts = Counter(_note_key(note) for note in old)
    current_key_counts = Counter(_note_key(note) for note in current)

    for new_note in added:
        if len(_indices(working, new_note)) == 1:
            operations.append({"kind": "already_present", "note": new_note})
            continue
        if len(_indices(working, new_note)) > 1:
            findings.append(_finding(
                "duplicate_assembled_note",
                "New canonical note already occurs more than once in assembled notes.",
                note=new_note,
            ))
            continue

        key = _note_key(new_note)
        if key is None:
            findings.append(_finding(
                "invalid_canonical_note",
                "Canonical note cannot be parsed during propagation.",
                note=new_note,
            ))
            continue

        old_candidates = [
            note
            for note in removed
            if note not in paired_removed and _note_key(note) == key
        ]
        normalized_matches = [
            note
            for note in old_candidates
            if _modal_normalized(note) == _modal_normalized(new_note)
            and len(_indices(working, note)) == 1
        ]
        if len(normalized_matches) == 1:
            old_note = normalized_matches[0]
            index = _indices(working, old_note)[0]
            working[index] = new_note
            paired_removed.add(old_note)
            operations.append({
                "kind": "replace",
                "reason": "modal_normalized_match",
                "index": index,
                "old": old_note,
                "new": new_note,
            })
            continue

        if (
            len(old_candidates) == 1
            and old_key_counts[key] == 1
            and current_key_counts[key] == 1
            and len(_indices(working, old_candidates[0])) == 1
        ):
            old_note = old_candidates[0]
            index = _indices(working, old_note)[0]
            working[index] = new_note
            paired_removed.add(old_note)
            operations.append({
                "kind": "replace",
                "reason": "unique_canonical_scope_class",
                "index": index,
                "old": old_note,
                "new": new_note,
            })
            continue

        same_key = _same_key_indices(working, key)
        normalized_assembled = [
            index
            for index in same_key
            if _modal_normalized(working[index]) == _modal_normalized(new_note)
        ]
        if len(normalized_assembled) == 1:
            index = normalized_assembled[0]
            old_note = working[index]
            working[index] = new_note
            operations.append({
                "kind": "replace",
                "reason": "assembled_modal_normalized_match",
                "index": index,
                "old": old_note,
                "new": new_note,
            })
            continue

        preserved = [
            index for index in same_key if working[index] in current_set
        ]
        if preserved:
            index = _insertion_index(working, current, new_note)
            working.insert(index, new_note)
            operations.append({
                "kind": "insert",
                "reason": "additional_canonical_note_for_existing_scope_class",
                "index": index,
                "new": new_note,
            })
            continue

        if same_key:
            candidate_notes = [working[index] for index in same_key]
            candidate_blocks = [_dependency_blocks(spec, note) for note in candidate_notes]
            new_blocks = _dependency_blocks(spec, new_note)
            if all(candidate_blocks) and not new_blocks:
                index = min(same_key)
                for candidate_index in reversed(same_key):
                    del working[candidate_index]
                working.insert(index, new_note)
                operations.append({
                    "kind": "reconcile_dependency",
                    "reason": "replace_blocking_assembly_only_bindings",
                    "index": index,
                    "removed": candidate_notes,
                    "new": new_note,
                })
                continue

            findings.append(_finding(
                "ambiguous_scope_class_match",
                "Cannot safely decide whether existing assembled notes with the same "
                "scope/class are modular evidence or stale assembly-only notes.",
                scope=key[0],
                note_class=key[1],
                new_note=new_note,
                candidates=candidate_notes,
            ))
            continue

        index = _insertion_index(working, current, new_note)
        working.insert(index, new_note)
        operations.append({
            "kind": "insert",
            "reason": "new_canonical_note",
            "index": index,
            "new": new_note,
        })

    for old_note in removed:
        if old_note in paired_removed:
            continue
        found = _indices(working, old_note)
        if len(found) == 1:
            index = found[0]
            del working[index]
            operations.append({
                "kind": "delete",
                "reason": "removed_from_canonical_source",
                "index": index,
                "old": old_note,
            })
        elif len(found) > 1:
            findings.append(_finding(
                "duplicate_stale_assembled_note",
                "Removed canonical note occurs more than once in assembled notes.",
                note=old_note,
                occurrences=len(found),
            ))

    for note in current:
        count = len(_indices(working, note))
        if count != 1:
            findings.append(_finding(
                "canonical_note_not_closed",
                "Every current canonical inline note must occur exactly once after propagation.",
                note=note,
                occurrences=count,
            ))

    after_spec = dict(spec)
    after_spec["notes"] = working
    coverage_before = len(language.factory_coverage(spec))
    coverage_after = len(language.factory_coverage(after_spec))
    dependency_before = len([
        item for item in language.dependency_bindings(spec)
        if item.get("severity") == "block"
    ])
    dependency_after = len([
        item for item in language.dependency_bindings(after_spec)
        if item.get("severity") == "block"
    ])
    if coverage_after > coverage_before:
        findings.append(_finding(
            "factory_coverage_regression",
            "Propagation would increase Factory callable coverage blockers.",
            before=coverage_before,
            after=coverage_after,
        ))
    if dependency_after > dependency_before:
        findings.append(_finding(
            "dependency_binding_regression",
            "Propagation would increase dependency-binding blockers.",
            before=dependency_before,
            after=dependency_after,
        ))

    changes = [
        item for item in operations if item["kind"] != "already_present"
    ]
    changed = working != before
    report = {
        "schema_version": SCHEMA_VERSION,
        "project": project.name,
        "base_ref": base_ref,
        "status": "blocked" if findings else "drift" if changed else "in_sync",
        "ready": not findings,
        "changed": changed,
        "written": False,
        "summary": {
            "canonical_notes_base": len(old),
            "canonical_notes_current": len(current),
            "assembled_notes_before": len(before),
            "assembled_notes_after": len(working),
            "changes": len(changes),
            "replacements": sum(
                item["kind"] in {"replace", "reconcile_dependency"} for item in changes
            ),
            "insertions": sum(item["kind"] == "insert" for item in changes),
            "deletions": sum(item["kind"] == "delete" for item in changes),
            "blocks": len(findings),
            "factory_coverage_blocks_before": coverage_before,
            "factory_coverage_blocks_after": coverage_after,
            "dependency_binding_blocks_before": dependency_before,
            "dependency_binding_blocks_after": dependency_after,
            "base_notes_sha256": _notes_hash(old),
            "current_notes_sha256": _notes_hash(current),
            "assembled_notes_before_sha256": _notes_hash(before),
            "assembled_notes_after_sha256": _notes_hash(working),
        },
        "operations": operations,
        "findings": findings,
    }
    return report, spec, working


def plan(
    project: Path,
    *,
    base_ref: str = "HEAD",
    base_text: str | None = None,
) -> dict[str, Any]:
    report, _spec, _working = _prepare(
        project, base_ref=base_ref, base_text=base_text
    )
    return report


def propagate(
    project: Path,
    *,
    base_ref: str = "HEAD",
    write: bool = True,
    base_text: str | None = None,
) -> dict[str, Any]:
    report, spec, working = _prepare(
        project, base_ref=base_ref, base_text=base_text
    )
    if not report["ready"] or not write or not report["changed"]:
        return report

    spec["notes"] = working
    path = project / DEFAULT_ASSEMBLED
    path.write_text(
        json.dumps(spec, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    report["written"] = True
    report["status"] = "applied"
    return report
