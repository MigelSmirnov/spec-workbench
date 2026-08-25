from __future__ import annotations

import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


PROJECT_INDEX_FILE = "PROJECT_INDEX.json"
PRIMARY_STATES = (
    (0, "Product boundary"),
    (10, "Domain models"),
    (20, "Rules & invariants"),
    (30, "Module responsibilities"),
    (40, "System flows"),
    (50, "Public APIs"),
    (60, "Contracts"),
    (70, "Notes"),
)
READ_ORDER_CANDIDATES = (
    ("00_product.md", "01_product_boundary.md"),
    ("10_models.md", "01_models.md", "03_domain_models.md"),
    ("20_rules.md", "02_rules.md", "04_rules_and_invariants.md"),
    ("30_modules.md", "03_module_responsibilities.md", "05_module_responsibilities.md"),
    ("40_flows.md", "06_system_flows.md"),
    ("50_public_apis.md", "07_public_apis.md"),
    ("60_contracts.md", "60_contracts.json", "08_contracts.md"),
    ("70_notes.md", "80_notes.md", "09_notes.md"),
    ("global_spec.json",),
)


class NavigationError(RuntimeError):
    pass


@dataclass(frozen=True)
class Project:
    id: str
    title: str
    group: str | None
    canonical_ref: str
    path: str
    aliases: tuple[str, ...]
    summary: str


@dataclass(frozen=True)
class ProjectView:
    id: str
    title: str
    group: str | None
    canonical_ref: str
    resolved_ref: str
    path: str
    summary: str
    stage_code: int | None
    stage_name: str
    state_file: str | None
    assembled: bool
    next: str
    read_order: tuple[str, ...]


def _git(repo_root: Path, *args: str, check: bool = True) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and proc.returncode != 0:
        detail = proc.stderr.strip() or proc.stdout.strip()
        raise NavigationError(f"git {' '.join(args)} failed: {detail}")
    return proc.stdout


def _index_text(repo_root: Path) -> str:
    path = repo_root / PROJECT_INDEX_FILE
    if path.is_file():
        return path.read_text(encoding="utf-8")
    for ref in ("main", "origin/main"):
        text = _git(repo_root, "show", f"{ref}:{PROJECT_INDEX_FILE}", check=False)
        if text.strip():
            return text
    raise NavigationError(
        f"{PROJECT_INDEX_FILE} not found; run navigation from an updated main checkout"
    )


def load_index(repo_root: Path) -> dict[str, Any]:
    try:
        payload = json.loads(_index_text(repo_root))
    except json.JSONDecodeError as exc:
        raise NavigationError(f"invalid {PROJECT_INDEX_FILE}: {exc}") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("projects"), list):
        raise NavigationError(f"invalid {PROJECT_INDEX_FILE}: projects must be a list")
    return payload


def _project(item: dict[str, Any]) -> Project:
    missing = [key for key in ("id", "title", "canonical_ref", "path") if not item.get(key)]
    if missing:
        raise NavigationError(
            f"invalid {PROJECT_INDEX_FILE}: project missing {', '.join(missing)}"
        )
    return Project(
        id=str(item["id"]),
        title=str(item["title"]),
        group=str(item["group"]) if item.get("group") is not None else None,
        canonical_ref=str(item["canonical_ref"]),
        path=str(item["path"]).strip("/"),
        aliases=tuple(str(value) for value in item.get("aliases", [])),
        summary=str(item.get("summary", "")),
    )


def projects(repo_root: Path) -> list[Project]:
    return [_project(item) for item in load_index(repo_root)["projects"]]


def resolve_project(repo_root: Path, query: str) -> Project:
    needle = query.strip().casefold()
    rows = projects(repo_root)
    for row in rows:
        if any(needle == name.casefold() for name in (row.id, row.title, *row.aliases)):
            return row
    available = ", ".join(row.id for row in rows)
    raise NavigationError(f"unknown project {query!r}; available: {available}")


def _resolve_ref(repo_root: Path, ref: str) -> str:
    for candidate in (ref, f"origin/{ref}"):
        if _git(repo_root, "rev-parse", "--verify", f"{candidate}^{{commit}}", check=False).strip():
            return candidate
    remote_refs = _git(
        repo_root,
        "for-each-ref",
        "--format=%(refname:short)",
        "refs/remotes",
        check=False,
    )
    for candidate in remote_refs.splitlines():
        candidate = candidate.strip()
        short = candidate.split("/", 1)[1] if "/" in candidate else candidate
        if short == ref:
            return candidate
    raise NavigationError(
        f"canonical ref {ref!r} is not available locally; run 'git fetch --all --prune'"
    )


def _files(repo_root: Path, ref: str, path: str) -> list[str]:
    prefix = path.strip("/") + "/"
    out = _git(repo_root, "ls-tree", "-r", "--name-only", ref, "--", path, check=False)
    return [line[len(prefix):] for line in out.splitlines() if line.startswith(prefix)]


def _stage(files: list[str]) -> tuple[int | None, str, str | None, bool]:
    labels = dict(PRIMARY_STATES)
    primary: list[tuple[int, str]] = []
    for rel in files:
        name = Path(rel).name
        if len(name) >= 4 and name[:2].isdigit() and name[2] == "_" and name.endswith(".md"):
            code = int(name[:2])
            if code in labels:
                primary.append((code, rel))
    assembled = "global_spec.json" in files
    if primary:
        code, rel = max(primary, key=lambda item: item[0])
        return code, "Assembly complete" if assembled else labels[code], rel, assembled
    return None, "Assembly complete" if assembled else "No primary state", None, assembled


def _next(stage_code: int | None, assembled: bool) -> str:
    if assembled:
        return "done"
    if stage_code is None:
        return "00 Product boundary"
    for code, label in PRIMARY_STATES:
        if code > stage_code:
            return f"{code:02d} {label}"
    return "Assembly"


def _preferred(files: list[str], candidates: tuple[str, ...]) -> str | None:
    for basename in candidates:
        matches = [rel for rel in files if Path(rel).name == basename]
        if matches:
            return min(matches, key=lambda rel: (rel.count("/"), len(rel), rel))
    return None


def _read_order(path: str, files: list[str]) -> tuple[str, ...]:
    result: list[str] = []
    if "AGENTS.md" in files:
        result.append(f"{path}/AGENTS.md")
    for candidates in READ_ORDER_CANDIDATES:
        rel = _preferred(files, candidates)
        if rel is not None:
            full = f"{path}/{rel}"
            if full not in result:
                result.append(full)
    return tuple(result)


def project_view(repo_root: Path, project_or_query: Project | str) -> ProjectView:
    project = (
        resolve_project(repo_root, project_or_query)
        if isinstance(project_or_query, str)
        else project_or_query
    )
    resolved_ref = _resolve_ref(repo_root, project.canonical_ref)
    files = _files(repo_root, resolved_ref, project.path)
    if not files:
        raise NavigationError(
            f"project {project.id!r} path {project.path!r} not found on {project.canonical_ref!r}"
        )
    code, stage_name, state_file, assembled = _stage(files)
    return ProjectView(
        id=project.id,
        title=project.title,
        group=project.group,
        canonical_ref=project.canonical_ref,
        resolved_ref=resolved_ref,
        path=project.path,
        summary=project.summary,
        stage_code=code,
        stage_name=stage_name,
        state_file=f"{project.path}/{state_file}" if state_file else None,
        assembled=assembled,
        next=_next(code, assembled),
        read_order=_read_order(project.path, files),
    )


def list_projects(repo_root: Path) -> list[ProjectView]:
    return [project_view(repo_root, row) for row in projects(repo_root)]


def as_jsonable(view: ProjectView) -> dict[str, Any]:
    return asdict(view)
