from __future__ import annotations

import json
from pathlib import Path

import pytest

from frontend_context import (
    FrontendContextError,
    build_frontend_context,
    extract_heading_section,
    load_manifest,
)


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def write_manifest(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_extract_heading_section_includes_nested_headings_only() -> None:
    text = (
        "# Doc\n\n"
        "## Target\n\n"
        "body\n\n"
        "### Nested\n\n"
        "nested body\n\n"
        "## Next\n\n"
        "other\n"
    )

    section = extract_heading_section(text, "Target")

    assert "## Target" in section
    assert "### Nested" in section
    assert "nested body" in section
    assert "## Next" not in section


def test_missing_heading_fails_closed() -> None:
    with pytest.raises(FrontendContextError, match="heading not found"):
        extract_heading_section("# Doc\n\n## Present\n", "Missing")


def test_duplicate_heading_is_ambiguous() -> None:
    text = "# Doc\n\n## Same\nA\n\n## Same\nB\n"

    with pytest.raises(FrontendContextError, match="heading is ambiguous"):
        extract_heading_section(text, "Same")


def test_manifest_rejects_unknown_fields(tmp_path: Path) -> None:
    repo = tmp_path
    write(repo / "FRONTEND_EDITOR.md", "# Frontend\n")
    manifest_path = write_manifest(
        repo / "examples" / "demo" / "frontend_context.json",
        {
            "schema_version": 1,
            "name": "demo",
            "full_documents": ["FRONTEND_EDITOR.md"],
            "slices": [],
            "unexpected": True,
        },
    )

    with pytest.raises(FrontendContextError, match="unknown frontend manifest fields"):
        load_manifest(manifest_path=manifest_path, repo_root=repo)


def test_manifest_source_may_not_escape_repository(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    outside = write(tmp_path / "outside.md", "# Outside\n")
    manifest_path = write_manifest(
        repo / "frontend_context.json",
        {
            "schema_version": 1,
            "name": "demo",
            "full_documents": [f"../{outside.name}"],
            "slices": [],
        },
    )

    with pytest.raises(FrontendContextError, match="escapes repository"):
        load_manifest(manifest_path=manifest_path, repo_root=repo)


def test_build_frontend_context_includes_full_docs_and_exact_slices(tmp_path: Path) -> None:
    repo = tmp_path
    write(repo / "FRONTEND_EDITOR.md", "# Frontend\n\nShared boundary.\n")
    source = write(
        repo / "examples" / "demo" / "10_models.md",
        "# Models\n\n## `Wall`\n\nwall fields\n\n## `Opening`\n\nopening fields\n",
    )
    manifest_path = write_manifest(
        repo / "examples" / "demo" / "frontend_context.json",
        {
            "schema_version": 1,
            "name": "demo-editor",
            "full_documents": ["FRONTEND_EDITOR.md"],
            "slices": [
                {
                    "path": "examples/demo/10_models.md",
                    "headings": ["`Wall`"],
                }
            ],
        },
    )

    manifest, context = build_frontend_context(
        manifest_path=manifest_path,
        repo_root=repo,
    )

    assert manifest.name == "demo-editor"
    assert manifest.full_documents == ((repo / "FRONTEND_EDITOR.md").resolve(),)
    assert source.resolve() == manifest.slices[0].path
    assert "Shared boundary." in context
    assert "## `Wall`" in context
    assert "wall fields" in context
    assert "## `Opening`" not in context


def test_build_frontend_context_fails_when_manifest_heading_rots(tmp_path: Path) -> None:
    repo = tmp_path
    write(repo / "examples" / "demo" / "10_models.md", "# Models\n\n## `WallV2`\n")
    manifest_path = write_manifest(
        repo / "frontend_context.json",
        {
            "schema_version": 1,
            "name": "demo-editor",
            "full_documents": [],
            "slices": [
                {
                    "path": "examples/demo/10_models.md",
                    "headings": ["`Wall`"],
                }
            ],
        },
    )

    with pytest.raises(FrontendContextError, match="heading not found"):
        build_frontend_context(manifest_path=manifest_path, repo_root=repo)
