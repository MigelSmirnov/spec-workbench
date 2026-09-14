from __future__ import annotations

from pathlib import Path

import pytest

from context_pack import (
    ContextPackError,
    build_context_pack,
    discover_context,
    extract_local_markdown_links,
)


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_context_pack_includes_readme_prior_states_and_linked_docs(tmp_path: Path):
    repo = tmp_path
    case = repo / "examples" / "demo"
    router = write(repo / "PLATFORM_ROUTER.md", "# Router\n")
    write(
        case / "README.md",
        "# Demo\n\n[Router](../../PLATFORM_ROUTER.md)\n",
    )
    state0 = write(case / "00_product.md", "# Product\n")
    state10 = write(case / "10_models.md", "# Models\n")

    docs = discover_context(
        case_dir=case,
        state_path=state10,
        repo_root=repo,
        max_depth=2,
    )

    assert [d.path for d in docs] == [
        (case / "README.md").resolve(),
        state0.resolve(),
        state10.resolve(),
        router.resolve(),
    ]


def test_context_pack_follows_links_recursively_without_cycles(tmp_path: Path):
    repo = tmp_path
    case = repo / "examples" / "demo"
    readme = write(case / "README.md", "[A](a.md)\n")
    a = write(case / "a.md", "[B](b.md)\n")
    b = write(case / "b.md", "[A](a.md)\n")
    state = write(case / "00_product.md", "# Product\n")

    docs = discover_context(
        case_dir=case,
        state_path=state,
        repo_root=repo,
        max_depth=3,
    )

    assert [d.path for d in docs] == [
        readme.resolve(),
        state.resolve(),
        a.resolve(),
        b.resolve(),
    ]


def test_external_links_and_non_markdown_links_are_ignored(tmp_path: Path):
    repo = tmp_path
    source = write(
        repo / "docs" / "source.md",
        "[Web](https://example.com/x.md)\n[Code](tool.py)\n[Anchor](#section)\n",
    )

    assert extract_local_markdown_links(
        source.read_text(encoding="utf-8"),
        source_path=source,
        repo_root=repo,
    ) == []


def test_missing_local_markdown_link_is_an_error(tmp_path: Path):
    repo = tmp_path
    source = write(repo / "docs" / "source.md", "[Missing](missing.md)\n")

    with pytest.raises(ContextPackError, match="missing local Markdown context"):
        extract_local_markdown_links(
            source.read_text(encoding="utf-8"),
            source_path=source,
            repo_root=repo,
        )


def test_local_link_may_not_escape_repository(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    outside = write(tmp_path / "outside.md", "# Outside\n")
    source = write(repo / "docs" / "source.md", f"[Outside](../../{outside.name})\n")

    with pytest.raises(ContextPackError, match="escapes repository"):
        extract_local_markdown_links(
            source.read_text(encoding="utf-8"),
            source_path=source,
            repo_root=repo,
        )


def test_rendered_pack_contains_source_boundaries(tmp_path: Path):
    repo = tmp_path
    case = repo / "examples" / "demo"
    write(case / "README.md", "# Demo\n")
    state = write(case / "00_product.md", "# Product\n")

    docs, pack = build_context_pack(
        case=Path("examples/demo"),
        state=Path("00_product.md"),
        repo_root=repo,
    )

    assert len(docs) == 2
    assert "## Source: `examples/demo/README.md`" in pack
    assert "## Source: `examples/demo/00_product.md`" in pack
    assert "# Product" in pack
