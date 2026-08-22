from __future__ import annotations

import argparse
import re
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote


MARKDOWN_LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
STATE_FILE_RE = re.compile(r"^(\d{2})_[^/]+\.md$")
EXTERNAL_PREFIXES = ("http://", "https://", "mailto:", "tel:")


class ContextPackError(RuntimeError):
    pass


@dataclass(frozen=True)
class ContextDocument:
    path: Path
    depth: int


def _within_repo(path: Path, repo_root: Path) -> bool:
    try:
        path.relative_to(repo_root)
        return True
    except ValueError:
        return False


def _clean_link_target(raw: str) -> str | None:
    target = raw.strip()
    if not target or target.startswith("#") or target.startswith(EXTERNAL_PREFIXES):
        return None

    if target.startswith("<") and ">" in target:
        target = target[1 : target.index(">")]
    else:
        # Markdown allows an optional title after the URL. Repository paths with
        # literal spaces should be URL encoded, which keeps this split safe.
        target = target.split(maxsplit=1)[0]

    target = unquote(target.split("#", 1)[0].split("?", 1)[0])
    return target or None


def extract_local_markdown_links(
    text: str,
    *,
    source_path: Path,
    repo_root: Path,
) -> list[Path]:
    """Resolve local Markdown links in source order.

    External links and anchors are ignored. A local Markdown link that escapes
    the repository or points to a missing file is an error: context links are
    part of the authoring contract and must not silently rot.
    """

    repo_root = repo_root.resolve()
    source_path = source_path.resolve()
    result: list[Path] = []
    seen: set[Path] = set()

    for match in MARKDOWN_LINK_RE.finditer(text):
        target = _clean_link_target(match.group(1))
        if target is None:
            continue

        candidate = (source_path.parent / target).resolve()
        if candidate.is_dir():
            candidate = candidate / "README.md"

        if candidate.suffix.lower() != ".md":
            continue
        if not _within_repo(candidate, repo_root):
            raise ContextPackError(
                f"local context link escapes repository: {source_path} -> {target}"
            )
        if not candidate.is_file():
            raise ContextPackError(
                f"missing local Markdown context: {source_path} -> {target}"
            )
        if candidate not in seen:
            seen.add(candidate)
            result.append(candidate)

    return result


def _state_rank(path: Path) -> int | None:
    match = STATE_FILE_RE.match(path.name)
    return int(match.group(1)) if match else None


def _resolve_case_dir(case: Path, repo_root: Path) -> Path:
    candidate = case if case.is_absolute() else repo_root / case
    candidate = candidate.resolve()
    if not _within_repo(candidate, repo_root) or not candidate.is_dir():
        raise ContextPackError(f"case directory not found inside repository: {case}")
    return candidate


def _resolve_state(state: Path, case_dir: Path, repo_root: Path) -> Path:
    candidate = state if state.is_absolute() else case_dir / state
    candidate = candidate.resolve()
    if not _within_repo(candidate, repo_root) or not candidate.is_file():
        raise ContextPackError(f"state document not found inside repository: {state}")
    if candidate.suffix.lower() != ".md":
        raise ContextPackError(f"state document must be Markdown: {candidate}")
    return candidate


def seed_documents(case_dir: Path, state_path: Path) -> list[Path]:
    """Return case README plus the current and all earlier numbered states."""

    seeds: list[Path] = []
    readme = case_dir / "README.md"
    if readme.is_file():
        seeds.append(readme.resolve())

    rank = _state_rank(state_path)
    if rank is not None:
        prior_states = sorted(
            p.resolve()
            for p in case_dir.glob("[0-9][0-9]_*.md")
            if (_state_rank(p) is not None and _state_rank(p) <= rank)
        )
        seeds.extend(prior_states)
    else:
        seeds.append(state_path.resolve())

    if state_path.resolve() not in seeds:
        seeds.append(state_path.resolve())

    return list(dict.fromkeys(seeds))


def discover_context(
    *,
    case_dir: Path,
    state_path: Path,
    repo_root: Path,
    max_depth: int = 2,
) -> list[ContextDocument]:
    if max_depth < 0:
        raise ContextPackError("max_depth must be >= 0")

    repo_root = repo_root.resolve()
    queue: deque[ContextDocument] = deque(
        ContextDocument(path=path, depth=0)
        for path in seed_documents(case_dir, state_path)
    )
    result: list[ContextDocument] = []
    seen: set[Path] = set()

    while queue:
        document = queue.popleft()
        path = document.path.resolve()
        if path in seen:
            continue
        seen.add(path)
        result.append(ContextDocument(path=path, depth=document.depth))

        if document.depth >= max_depth:
            continue

        text = path.read_text(encoding="utf-8")
        for linked in extract_local_markdown_links(
            text,
            source_path=path,
            repo_root=repo_root,
        ):
            if linked not in seen:
                queue.append(ContextDocument(linked, document.depth + 1))

    return result


def render_context_pack(
    documents: list[ContextDocument],
    *,
    repo_root: Path,
    case_dir: Path,
    state_path: Path,
) -> str:
    repo_root = repo_root.resolve()
    lines = [
        "# Spec Workbench context pack",
        "",
        f"Case: `{case_dir.resolve().relative_to(repo_root).as_posix()}`",
        f"State: `{state_path.resolve().relative_to(repo_root).as_posix()}`",
        "",
        "## Sources",
        "",
    ]

    for document in documents:
        rel = document.path.relative_to(repo_root).as_posix()
        lines.append(f"- `{rel}` (link depth {document.depth})")

    for document in documents:
        rel = document.path.relative_to(repo_root).as_posix()
        lines.extend(
            [
                "",
                "---",
                "",
                f"## Source: `{rel}`",
                "",
                document.path.read_text(encoding="utf-8").rstrip(),
            ]
        )

    return "\n".join(lines).rstrip() + "\n"


def build_context_pack(
    *,
    case: Path,
    state: Path,
    repo_root: Path,
    max_depth: int = 2,
) -> tuple[list[ContextDocument], str]:
    repo_root = repo_root.resolve()
    case_dir = _resolve_case_dir(case, repo_root)
    state_path = _resolve_state(state, case_dir, repo_root)
    documents = discover_context(
        case_dir=case_dir,
        state_path=state_path,
        repo_root=repo_root,
        max_depth=max_depth,
    )
    return documents, render_context_pack(
        documents,
        repo_root=repo_root,
        case_dir=case_dir,
        state_path=state_path,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Build one deterministic authoring context pack from a case README, "
            "the current/prior numbered states, and recursively linked local Markdown."
        )
    )
    parser.add_argument("--case", required=True, type=Path, help="case directory")
    parser.add_argument(
        "--state",
        required=True,
        type=Path,
        help="current Markdown state file, relative to the case directory",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=2,
        help="recursive local Markdown-link depth (default: 2)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="write the pack to a file instead of stdout",
    )
    parser.add_argument(
        "--paths-only",
        action="store_true",
        help="print only resolved context paths",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    try:
        documents, pack = build_context_pack(
            case=args.case,
            state=args.state,
            repo_root=repo_root,
            max_depth=args.max_depth,
        )
    except ContextPackError as exc:
        parser.error(str(exc))

    if args.paths_only:
        output = "\n".join(
            document.path.relative_to(repo_root).as_posix()
            for document in documents
        ) + "\n"
    else:
        output = pack

    if args.output:
        output_path = args.output
        if not output_path.is_absolute():
            output_path = repo_root / output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output, encoding="utf-8")
    else:
        print(output, end="")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
