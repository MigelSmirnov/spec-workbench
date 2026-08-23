from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$", re.MULTILINE)
ALLOWED_MANIFEST_KEYS = {"schema_version", "name", "full_documents", "slices"}
ALLOWED_SLICE_KEYS = {"path", "headings"}


class FrontendContextError(RuntimeError):
    pass


@dataclass(frozen=True)
class FrontendSlice:
    path: Path
    headings: tuple[str, ...]


@dataclass(frozen=True)
class FrontendManifest:
    name: str
    full_documents: tuple[Path, ...]
    slices: tuple[FrontendSlice, ...]


def _within_repo(path: Path, repo_root: Path) -> bool:
    try:
        path.relative_to(repo_root)
        return True
    except ValueError:
        return False


def _resolve_repo_file(raw_path: str, *, repo_root: Path, suffix: str) -> Path:
    if not isinstance(raw_path, str) or not raw_path.strip():
        raise FrontendContextError("manifest path entries must be non-empty strings")

    candidate = (repo_root / raw_path).resolve()
    if not _within_repo(candidate, repo_root):
        raise FrontendContextError(f"frontend context path escapes repository: {raw_path}")
    if candidate.suffix.lower() != suffix:
        raise FrontendContextError(
            f"frontend context path must end with {suffix}: {raw_path}"
        )
    if not candidate.is_file():
        raise FrontendContextError(f"frontend context source not found: {raw_path}")
    return candidate


def _require_string_list(value: Any, *, field: str, allow_empty: bool) -> list[str]:
    if not isinstance(value, list):
        raise FrontendContextError(f"{field} must be a list")
    if not allow_empty and not value:
        raise FrontendContextError(f"{field} must not be empty")

    result: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise FrontendContextError(f"{field} entries must be non-empty strings")
        result.append(item.strip())

    if len(set(result)) != len(result):
        raise FrontendContextError(f"{field} must not contain duplicates")
    return result


def load_manifest(*, manifest_path: Path, repo_root: Path) -> FrontendManifest:
    repo_root = repo_root.resolve()
    manifest_path = manifest_path.resolve()
    if not _within_repo(manifest_path, repo_root):
        raise FrontendContextError("frontend manifest must be inside the repository")
    if manifest_path.suffix.lower() != ".json" or not manifest_path.is_file():
        raise FrontendContextError(f"frontend manifest not found: {manifest_path}")

    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise FrontendContextError(f"invalid frontend manifest JSON: {exc}") from exc

    if not isinstance(raw, dict):
        raise FrontendContextError("frontend manifest root must be an object")

    unknown = set(raw) - ALLOWED_MANIFEST_KEYS
    if unknown:
        raise FrontendContextError(
            "unknown frontend manifest fields: " + ", ".join(sorted(unknown))
        )

    if raw.get("schema_version") != 1:
        raise FrontendContextError("frontend manifest schema_version must be 1")

    name = raw.get("name")
    if not isinstance(name, str) or not name.strip():
        raise FrontendContextError("frontend manifest name must be a non-empty string")

    full_document_paths = _require_string_list(
        raw.get("full_documents", []),
        field="full_documents",
        allow_empty=True,
    )
    full_documents = tuple(
        _resolve_repo_file(path, repo_root=repo_root, suffix=".md")
        for path in full_document_paths
    )

    raw_slices = raw.get("slices", [])
    if not isinstance(raw_slices, list):
        raise FrontendContextError("slices must be a list")

    slices: list[FrontendSlice] = []
    for index, raw_slice in enumerate(raw_slices):
        field = f"slices[{index}]"
        if not isinstance(raw_slice, dict):
            raise FrontendContextError(f"{field} must be an object")
        unknown_slice = set(raw_slice) - ALLOWED_SLICE_KEYS
        if unknown_slice:
            raise FrontendContextError(
                f"unknown fields in {field}: " + ", ".join(sorted(unknown_slice))
            )

        raw_path = raw_slice.get("path")
        if not isinstance(raw_path, str) or not raw_path.strip():
            raise FrontendContextError(f"{field}.path must be a non-empty string")
        path = _resolve_repo_file(raw_path.strip(), repo_root=repo_root, suffix=".md")
        headings = tuple(
            _require_string_list(
                raw_slice.get("headings"),
                field=f"{field}.headings",
                allow_empty=False,
            )
        )
        slices.append(FrontendSlice(path=path, headings=headings))

    if not full_documents and not slices:
        raise FrontendContextError(
            "frontend manifest must include at least one full document or slice"
        )

    return FrontendManifest(
        name=name.strip(),
        full_documents=full_documents,
        slices=tuple(slices),
    )


def extract_heading_section(text: str, heading: str) -> str:
    """Extract one exact Markdown heading and its nested content.

    The section ends at the next heading of the same or higher level. Exact
    heading matching is deliberate: a renamed canonical model should break the
    frontend dependency manifest instead of being silently omitted.
    """

    matches = list(HEADING_RE.finditer(text))
    candidates = [match for match in matches if match.group(2).strip() == heading]
    if not candidates:
        raise FrontendContextError(f"frontend context heading not found: {heading}")
    if len(candidates) > 1:
        raise FrontendContextError(f"frontend context heading is ambiguous: {heading}")

    current = candidates[0]
    level = len(current.group(1))
    start = current.start()
    end = len(text)

    current_index = matches.index(current)
    for next_match in matches[current_index + 1 :]:
        if len(next_match.group(1)) <= level:
            end = next_match.start()
            break

    return text[start:end].rstrip() + "\n"


def validate_manifest_sections(manifest: FrontendManifest) -> None:
    for slice_spec in manifest.slices:
        text = slice_spec.path.read_text(encoding="utf-8")
        for heading in slice_spec.headings:
            extract_heading_section(text, heading)


def render_frontend_context(
    manifest: FrontendManifest,
    *,
    manifest_path: Path,
    repo_root: Path,
) -> str:
    repo_root = repo_root.resolve()
    manifest_rel = manifest_path.resolve().relative_to(repo_root).as_posix()
    lines = [
        "# Frontend context pack",
        "",
        f"Profile: `{manifest.name}`",
        f"Manifest: `{manifest_rel}`",
        "",
        "> Generated working context. Canonical Markdown sources remain authoritative.",
        "",
        "## Sources",
        "",
    ]

    for path in manifest.full_documents:
        rel = path.relative_to(repo_root).as_posix()
        lines.append(f"- `{rel}` — full document")

    for slice_spec in manifest.slices:
        rel = slice_spec.path.relative_to(repo_root).as_posix()
        for heading in slice_spec.headings:
            lines.append(f"- `{rel}` — heading `{heading}`")

    for path in manifest.full_documents:
        rel = path.relative_to(repo_root).as_posix()
        lines.extend(
            [
                "",
                "---",
                "",
                f"## Full source: `{rel}`",
                "",
                path.read_text(encoding="utf-8").rstrip(),
            ]
        )

    for slice_spec in manifest.slices:
        rel = slice_spec.path.relative_to(repo_root).as_posix()
        text = slice_spec.path.read_text(encoding="utf-8")
        for heading in slice_spec.headings:
            lines.extend(
                [
                    "",
                    "---",
                    "",
                    f"## Slice: `{rel}` → `{heading}`",
                    "",
                    extract_heading_section(text, heading).rstrip(),
                ]
            )

    return "\n".join(lines).rstrip() + "\n"


def build_frontend_context(
    *,
    manifest_path: Path,
    repo_root: Path,
) -> tuple[FrontendManifest, str]:
    manifest = load_manifest(manifest_path=manifest_path, repo_root=repo_root)
    validate_manifest_sections(manifest)
    return manifest, render_frontend_context(
        manifest,
        manifest_path=manifest_path,
        repo_root=repo_root,
    )


def _render_paths(manifest: FrontendManifest, *, repo_root: Path) -> str:
    lines: list[str] = []
    for path in manifest.full_documents:
        lines.append(path.relative_to(repo_root).as_posix())
    for slice_spec in manifest.slices:
        rel = slice_spec.path.relative_to(repo_root).as_posix()
        for heading in slice_spec.headings:
            lines.append(f"{rel}#{heading}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Build deterministic frontend working context from an explicit JSON "
            "manifest of canonical Markdown documents and headings."
        )
    )
    parser.add_argument(
        "--manifest",
        required=True,
        type=Path,
        help="repository-relative frontend context JSON manifest",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="write the generated context to a file instead of stdout",
    )
    parser.add_argument(
        "--paths-only",
        action="store_true",
        help="print only resolved source paths/headings after validation",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    manifest_path = args.manifest
    if not manifest_path.is_absolute():
        manifest_path = repo_root / manifest_path

    try:
        manifest, context = build_frontend_context(
            manifest_path=manifest_path,
            repo_root=repo_root,
        )
    except FrontendContextError as exc:
        parser.error(str(exc))

    output = _render_paths(manifest, repo_root=repo_root) if args.paths_only else context

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
