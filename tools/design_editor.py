#!/usr/bin/env python3
"""Byte-preserving structural edits for design-state Markdown.

The editor delegates all item and section addressing to ``design_index``.  It
does not interpret prose or infer semantic changes.  Its public workflow is:

``plan_edit`` -> ``render_unified_diff`` -> optional ``apply_plan``.

Content files contain the exact UTF-8 Markdown bytes to splice.  Section and
item replacements therefore include their heading.  Append inserts bytes at
the end of an existing section, while insert adds a complete new section after
an existing section.
"""
from __future__ import annotations

import argparse
import difflib
import os
import stat
import sys
import tempfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Sequence

import design_index


Operation = Literal[
    "replace-section",
    "append-section",
    "insert-section",
    "replace-item",
]


class DesignEditorError(Exception):
    """An edit could not be planned or safely applied."""


@dataclass(frozen=True)
class AddressSnapshot:
    """Structural facts that must remain valid across an edit."""

    item_key: str
    source_path: str
    section_signatures: tuple[tuple[str, int], ...]
    all_item_keys: tuple[str, ...]


@dataclass(frozen=True)
class EditPlan:
    """A deterministic byte splice against one indexed Markdown fragment."""

    project: Path
    operation: Operation
    item_key: str
    section_title: str | None
    path: Path
    relative_path: str
    before: bytes
    after: bytes
    target_start: int
    target_end: int
    new_target_end: int
    file_mode: int
    address_snapshot: AddressSnapshot


def _build_valid_index(project: Path) -> dict[str, object]:
    try:
        index = design_index.build_index(project)
    except Exception as exc:
        raise DesignEditorError(f"design index could not be built: {exc}") from exc
    duplicates = index["diagnostics"]["duplicate_keys"]
    if duplicates:
        joined = ", ".join(duplicates)
        raise DesignEditorError(f"design index has duplicate item keys: {joined}")
    return index


def _resolve_item(
    index: dict[str, object],
    requested_key: str,
) -> dict[str, object]:
    exact_matches = [
        entry for entry in index["items"] if entry["key"] == requested_key
    ]
    explicit_matches = [
        entry
        for entry in index["items"]
        if entry["explicit_id"] is not None
        and entry["explicit_id"].casefold() == requested_key.casefold()
    ]
    matches = exact_matches or explicit_matches
    if not matches:
        raise DesignEditorError(f"design item not found: {requested_key}")
    if len(matches) != 1:
        raise DesignEditorError(f"design item is ambiguous: {requested_key}")
    return matches[0]


def _resolve_section(
    item: dict[str, object],
    requested_title: str,
) -> dict[str, object]:
    matches = [
        section
        for section in item["sections"]
        if section["title"] == requested_title
    ]
    if not matches:
        raise DesignEditorError(
            f"section not found in {item['key']}: {requested_title}"
        )
    if len(matches) != 1:
        raise DesignEditorError(
            f"section is ambiguous in {item['key']}: {requested_title}"
        )
    return matches[0]


def _source_path(project: Path, relative_path: str) -> Path:
    path = (project / relative_path).resolve()
    if not path.is_relative_to(project) or not path.is_file():
        raise DesignEditorError(
            f"indexed source is not a file inside the project: {relative_path}"
        )
    return path


def _line_offsets(data: bytes) -> tuple[list[int], list[int]]:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise DesignEditorError("design document is not valid UTF-8") from exc
    lines = text.splitlines(keepends=True)
    starts: list[int] = []
    ends: list[int] = []
    offset = 0
    for line in lines:
        starts.append(offset)
        offset += len(line.encode("utf-8"))
        ends.append(offset)
    return starts, ends


def _byte_range(data: bytes, start_line: int, end_line: int) -> tuple[int, int]:
    starts, ends = _line_offsets(data)
    if start_line < 1 or end_line < start_line or end_line > len(starts):
        raise DesignEditorError(
            f"indexed line range is outside the source: {start_line}-{end_line}"
        )
    return starts[start_line - 1], ends[end_line - 1]


def _snapshot(index: dict[str, object], item: dict[str, object]) -> AddressSnapshot:
    return AddressSnapshot(
        item_key=item["key"],
        source_path=item["source"]["path"],
        section_signatures=tuple(
            (section["title"], section["level"])
            for section in item["sections"]
        ),
        all_item_keys=tuple(entry["key"] for entry in index["items"]),
    )


def assert_locality(plan: EditPlan) -> None:
    """Prove that only the addressed byte fragment changed."""
    if plan.before[: plan.target_start] != plan.after[: plan.target_start]:
        raise DesignEditorError("edit changed bytes before the target fragment")
    if plan.before[plan.target_end :] != plan.after[plan.new_target_end :]:
        raise DesignEditorError("edit changed bytes after the target fragment")


def plan_edit(
    project: Path,
    operation: Operation,
    item_key: str,
    content: bytes,
    *,
    section_title: str | None = None,
) -> EditPlan:
    """Resolve an address and return an immutable byte-splice plan."""
    if operation not in {
        "replace-section",
        "append-section",
        "insert-section",
        "replace-item",
    }:
        raise DesignEditorError(f"unsupported operation: {operation}")
    if operation == "replace-item" and section_title is not None:
        raise DesignEditorError("replace-item does not accept a section")
    if operation != "replace-item" and section_title is None:
        raise DesignEditorError(f"{operation} requires a section")
    try:
        content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise DesignEditorError("content file is not valid UTF-8") from exc

    project = project.resolve()
    if not project.is_dir():
        raise DesignEditorError(f"project directory not found: {project}")
    index = _build_valid_index(project)
    item = _resolve_item(index, item_key)
    path = _source_path(project, item["source"]["path"])
    before = path.read_bytes()

    if operation == "replace-item":
        target_start, target_end = _byte_range(
            before,
            item["source"]["start_line"],
            item["source"]["end_line"],
        )
        replacement = content
    else:
        section = _resolve_section(item, section_title)
        section_start, section_end = _byte_range(
            before,
            section["start_line"],
            section["end_line"],
        )
        if operation == "replace-section":
            target_start, target_end = section_start, section_end
        else:
            target_start = target_end = section_end
        replacement = content

    after = before[:target_start] + replacement + before[target_end:]
    plan = EditPlan(
        project=project,
        operation=operation,
        item_key=item["key"],
        section_title=section_title,
        path=path,
        relative_path=item["source"]["path"],
        before=before,
        after=after,
        target_start=target_start,
        target_end=target_end,
        new_target_end=target_start + len(replacement),
        file_mode=stat.S_IMODE(path.stat().st_mode),
        address_snapshot=_snapshot(index, item),
    )
    assert_locality(plan)
    return plan


def render_unified_diff(plan: EditPlan) -> str:
    """Render a preview without changing the filesystem."""
    before = plan.before.decode("utf-8").splitlines(keepends=True)
    after = plan.after.decode("utf-8").splitlines(keepends=True)
    return "".join(
        difflib.unified_diff(
            before,
            after,
            fromfile=f"a/{plan.relative_path}",
            tofile=f"b/{plan.relative_path}",
            lineterm="\n",
        )
    )


def _atomic_replace(path: Path, data: bytes, mode: int) -> None:
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            os.fchmod(handle.fileno(), mode)
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        try:
            directory_descriptor = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(directory_descriptor)
            finally:
                os.close(directory_descriptor)
        except OSError:
            # The replace is already atomic. Some filesystems do not support
            # directory fsync; that must not be reported as a failed replace.
            pass
    finally:
        temporary.unlink(missing_ok=True)


def _is_subsequence(
    expected: tuple[tuple[str, int], ...],
    actual: tuple[tuple[str, int], ...],
) -> bool:
    cursor = iter(actual)
    return all(any(candidate == item for candidate in cursor) for item in expected)


def _validate_applied_structure(plan: EditPlan) -> None:
    index = _build_valid_index(plan.project)
    keys = tuple(entry["key"] for entry in index["items"])
    if Counter(keys) != Counter(plan.address_snapshot.all_item_keys):
        raise DesignEditorError("edit created, deleted, or renamed a design item")

    matches = [entry for entry in index["items"] if entry["key"] == plan.item_key]
    if len(matches) != 1:
        raise DesignEditorError(f"edited item is no longer unique: {plan.item_key}")
    item = matches[0]
    if item["source"]["path"] != plan.address_snapshot.source_path:
        raise DesignEditorError(f"edited item moved to another file: {plan.item_key}")

    before_sections = plan.address_snapshot.section_signatures
    after_sections = tuple(
        (section["title"], section["level"])
        for section in item["sections"]
    )
    if plan.operation in {"replace-section", "append-section"}:
        if after_sections != before_sections:
            raise DesignEditorError(
                f"{plan.operation} changed section structure; use insert-section to create a section"
            )
    elif plan.operation == "insert-section":
        if len(after_sections) <= len(before_sections):
            raise DesignEditorError("insert-section did not create a section")
        if not _is_subsequence(before_sections, after_sections):
            raise DesignEditorError("insert-section changed existing section structure")
        titles_before = Counter(title for title, _ in before_sections)
        titles_after = Counter(title for title, _ in after_sections)
        introduced_ambiguity = any(
            count > 1 and count > titles_before[title]
            for title, count in titles_after.items()
        )
        if introduced_ambiguity:
            raise DesignEditorError("insert-section created an ambiguous section title")


def apply_plan(plan: EditPlan) -> None:
    """Atomically apply, re-index, and roll back a structurally invalid edit."""
    assert_locality(plan)
    try:
        current = plan.path.read_bytes()
    except OSError as exc:
        raise DesignEditorError(f"could not re-read target before apply: {exc}") from exc
    if current != plan.before:
        raise DesignEditorError("target changed after the edit was planned")

    try:
        _atomic_replace(plan.path, plan.after, plan.file_mode)
    except OSError as exc:
        raise DesignEditorError(f"atomic write failed: {exc}") from exc

    try:
        _validate_applied_structure(plan)
    except Exception as validation_error:
        try:
            _atomic_replace(plan.path, plan.before, plan.file_mode)
        except Exception as rollback_error:
            raise DesignEditorError(
                f"post-apply validation failed ({validation_error}); rollback also failed: {rollback_error}"
            ) from rollback_error
        if isinstance(validation_error, DesignEditorError):
            raise validation_error
        raise DesignEditorError(
            f"post-apply validation failed: {validation_error}"
        ) from validation_error


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path, help="Directory containing design Markdown")
    subparsers = parser.add_subparsers(dest="operation", required=True)

    for operation in ("replace-section", "append-section"):
        command = subparsers.add_parser(
            operation,
            help=(
                "replace a complete indexed section fragment"
                if operation == "replace-section"
                else "append exact bytes to an indexed section"
            ),
        )
        command.add_argument("item")
        command.add_argument("section")
        command.add_argument(
            "--content-file",
            type=Path,
            required=True,
            help="Exact UTF-8 Markdown bytes to splice",
        )
        command.add_argument(
            "--apply",
            action="store_true",
            help="Apply atomically after printing the diff (default: dry-run)",
        )

    insert = subparsers.add_parser(
        "insert-section",
        help="insert a complete new section after an indexed section",
    )
    insert.add_argument("item")
    insert.add_argument("after_section")
    insert.add_argument(
        "--content-file",
        type=Path,
        required=True,
        help="Complete new UTF-8 Markdown section, including its heading",
    )
    insert.add_argument(
        "--apply",
        action="store_true",
        help="Apply atomically after printing the diff (default: dry-run)",
    )

    replace_item = subparsers.add_parser(
        "replace-item",
        help="replace a complete indexed item fragment",
    )
    replace_item.add_argument("item")
    replace_item.add_argument(
        "--content-file",
        type=Path,
        required=True,
        help="Complete UTF-8 Markdown item, including its heading",
    )
    replace_item.add_argument(
        "--apply",
        action="store_true",
        help="Apply atomically after printing the diff (default: dry-run)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        content = args.content_file.read_bytes()
        section_title = getattr(args, "section", None)
        if args.operation == "insert-section":
            section_title = args.after_section
        plan = plan_edit(
            args.project,
            args.operation,
            args.item,
            content,
            section_title=section_title,
        )
        diff = render_unified_diff(plan)
        if diff:
            print(diff, end="" if diff.endswith("\n") else "\n")
        if args.apply:
            apply_plan(plan)
            print(f"applied {args.operation} to {plan.item_key}", file=sys.stderr)
        return 0
    except (OSError, DesignEditorError) as exc:
        print(f"design_editor: error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
