from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

from project_navigation import NavigationError, list_projects, project_view


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


class WorkbenchError(RuntimeError):
    pass


@dataclass(frozen=True)
class CaseState:
    case: str
    ref: str
    stage_code: int | None
    stage_name: str
    state_file: str | None
    assembled: bool
    numbered_docs: int


@dataclass(frozen=True)
class RepoStatus:
    branch: str
    commit: str
    dirty: bool
    current_cases: list[CaseState]
    other_cases: list[CaseState]


def _git(repo_root: Path, *args: str, check: bool = True) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and proc.returncode != 0:
        detail = proc.stderr.strip() or proc.stdout.strip()
        raise WorkbenchError(f"git {' '.join(args)} failed: {detail}")
    return proc.stdout


def find_repo_root(start: Path | None = None) -> Path:
    start = (start or Path.cwd()).resolve()
    return Path(_git(start, "rev-parse", "--show-toplevel").strip()).resolve()


def current_branch(repo_root: Path) -> str:
    branch = _git(repo_root, "branch", "--show-current").strip()
    return branch or "(detached HEAD)"


def current_commit(repo_root: Path) -> str:
    return _git(repo_root, "rev-parse", "--short", "HEAD").strip()


def is_dirty(repo_root: Path) -> bool:
    return bool(_git(repo_root, "status", "--porcelain").strip())


def known_refs(repo_root: Path) -> list[str]:
    local = [
        line.strip()
        for line in _git(
            repo_root, "for-each-ref", "--format=%(refname:short)", "refs/heads"
        ).splitlines()
        if line.strip()
    ]
    remote = [
        line.strip()
        for line in _git(
            repo_root, "for-each-ref", "--format=%(refname:short)", "refs/remotes"
        ).splitlines()
        if line.strip() and not line.strip().endswith("/HEAD")
    ]
    result = list(local)
    local_names = set(local)
    for ref in remote:
        short = ref.split("/", 1)[1] if "/" in ref else ref
        if short not in local_names and ref not in result:
            result.append(ref)
    branch = current_branch(repo_root)
    if branch != "(detached HEAD)" and branch not in result:
        result.insert(0, branch)
    return sorted(dict.fromkeys(result), key=lambda ref: (0 if ref == "main" else 1, ref))


def _case_tree_oid(repo_root: Path, ref: str, case: str) -> str | None:
    return _git(repo_root, "rev-parse", f"{ref}:examples/{case}", check=False).strip() or None


def _case_files_from_ref(repo_root: Path, ref: str, case: str) -> list[str]:
    prefix = f"examples/{case}/"
    out = _git(
        repo_root,
        "ls-tree",
        "-r",
        "--name-only",
        ref,
        "--",
        f"examples/{case}",
        check=False,
    )
    return [line.strip()[len(prefix):] for line in out.splitlines() if line.strip().startswith(prefix)]


def _case_names_from_ref(repo_root: Path, ref: str) -> list[str]:
    direct = _git(
        repo_root,
        "ls-tree",
        "-d",
        "--name-only",
        f"{ref}:examples",
        check=False,
    )
    names = [line.strip().rstrip("/") for line in direct.splitlines() if line.strip()]
    if names:
        return sorted(dict.fromkeys(names))
    out = _git(repo_root, "ls-tree", "-d", "--name-only", ref, "--", "examples", check=False)
    prefix = "examples/"
    fallback = [
        line.strip()[len(prefix):].split("/", 1)[0]
        for line in out.splitlines()
        if line.strip().startswith(prefix)
    ]
    return sorted(dict.fromkeys(fallback))


def _case_dirty(repo_root: Path, case: str) -> bool:
    return bool(_git(repo_root, "status", "--porcelain", "--", f"examples/{case}").strip())


def _working_case_names(repo_root: Path) -> list[str]:
    examples = repo_root / "examples"
    return sorted(p.name for p in examples.iterdir() if p.is_dir()) if examples.is_dir() else []


def _working_case_files(repo_root: Path, case: str) -> list[str]:
    case_dir = repo_root / "examples" / case
    if not case_dir.is_dir():
        return []
    return sorted(p.relative_to(case_dir).as_posix() for p in case_dir.rglob("*") if p.is_file())


def _stage_from_files(files: list[str]) -> tuple[int | None, str, str | None, int]:
    labels = dict(PRIMARY_STATES)
    numbered: list[tuple[int, str]] = []
    for rel in files:
        name = Path(rel).name
        if len(name) >= 4 and name[:2].isdigit() and name[2] == "_" and name.lower().endswith(".md"):
            numbered.append((int(name[:2]), rel))
    primary = [(code, rel) for code, rel in numbered if code in labels]
    if primary:
        code, rel = max(primary, key=lambda item: item[0])
        return code, labels[code], rel, len(numbered)
    return None, "No primary state", None, len(numbered)


def case_state_from_files(case: str, ref: str, files: list[str]) -> CaseState:
    code, name, state_file, numbered_docs = _stage_from_files(files)
    assembled = "global_spec.json" in files
    return CaseState(
        case=case,
        ref=ref,
        stage_code=code,
        stage_name="Assembly complete" if assembled else name,
        state_file=state_file,
        assembled=assembled,
        numbered_docs=numbered_docs,
    )


def list_cases(repo_root: Path, *, include_worktree: bool = True) -> list[CaseState]:
    """Exhaustive history view. Normal discovery uses PROJECT_INDEX.json instead."""
    result: list[CaseState] = []
    if include_worktree:
        branch = current_branch(repo_root)
        label = f"{branch} (worktree)"
        for case in _working_case_names(repo_root):
            result.append(case_state_from_files(case, label, _working_case_files(repo_root, case)))

    current = current_branch(repo_root)
    current_case_trees: dict[str, str] = {}
    if include_worktree and current != "(detached HEAD)":
        for case in _working_case_names(repo_root):
            if not _case_dirty(repo_root, case):
                tree_oid = _case_tree_oid(repo_root, current, case)
                if tree_oid:
                    current_case_trees[case] = tree_oid

    grouped: dict[tuple[str, str], tuple[CaseState, list[str]]] = {}
    for ref in known_refs(repo_root):
        if include_worktree and ref == current:
            continue
        for case in _case_names_from_ref(repo_root, ref):
            tree_oid = _case_tree_oid(repo_root, ref, case)
            if tree_oid is None or current_case_trees.get(case) == tree_oid:
                continue
            row = case_state_from_files(case, ref, _case_files_from_ref(repo_root, ref, case))
            key = (case, tree_oid)
            if key not in grouped:
                grouped[key] = (row, [ref])
            else:
                grouped[key][1].append(ref)

    for row, refs in grouped.values():
        refs = sorted(dict.fromkeys(refs), key=lambda ref: (0 if ref == "main" else 1, ref))
        result.append(
            CaseState(
                case=row.case,
                ref=", ".join(refs),
                stage_code=row.stage_code,
                stage_name=row.stage_name,
                state_file=row.state_file,
                assembled=row.assembled,
                numbered_docs=row.numbered_docs,
            )
        )
    result.sort(key=lambda item: (item.case, item.ref))
    return result


def next_primary_state(state: CaseState) -> str:
    if state.assembled:
        return "done"
    if state.stage_code is None:
        return "00 Product boundary"
    for code, label in PRIMARY_STATES:
        if code > state.stage_code:
            return f"{code:02d} {label}"
    return "Assembly"


def repo_status(repo_root: Path) -> RepoStatus:
    branch = current_branch(repo_root)
    rows = list_cases(repo_root, include_worktree=True)
    current_ref = f"{branch} (worktree)"
    current_rows = [row for row in rows if row.ref == current_ref]
    current_names = {row.case for row in current_rows}
    other_rows = [row for row in rows if row.ref != current_ref and row.case not in current_names]
    return RepoStatus(
        branch=branch,
        commit=current_commit(repo_root),
        dirty=is_dirty(repo_root),
        current_cases=current_rows,
        other_cases=other_rows,
    )


def _print_case_table(rows: list[CaseState]) -> None:
    if not rows:
        print("No case studies found.")
        return
    headers = ("CASE", "REF", "STAGE", "NEXT")
    data = [(row.case, row.ref, row.stage_name, next_primary_state(row)) for row in rows]
    widths = [max(len(headers[i]), *(len(str(row[i])) for row in data)) for i in range(len(headers))]
    print("  ".join(headers[i].ljust(widths[i]) for i in range(len(headers))))
    print("  ".join("-" * widths[i] for i in range(len(headers))))
    for row in data:
        print("  ".join(str(row[i]).ljust(widths[i]) for i in range(len(headers))))


def _print_project_table(rows) -> None:
    if not rows:
        print("No working projects indexed.")
        return
    headers = ("PROJECT", "CANONICAL REF", "PATH", "STAGE")
    data = [(row.id, row.canonical_ref, row.path, row.stage_name) for row in rows]
    widths = [max(len(headers[i]), *(len(str(row[i])) for row in data)) for i in range(len(headers))]
    print("  ".join(headers[i].ljust(widths[i]) for i in range(len(headers))))
    print("  ".join("-" * widths[i] for i in range(len(headers))))
    for row in data:
        print("  ".join(str(row[i]).ljust(widths[i]) for i in range(len(headers))))


def print_list(repo_root: Path, *, as_json: bool) -> None:
    rows = list_projects(repo_root)
    if as_json:
        print(json.dumps([asdict(row) for row in rows], indent=2))
        return
    _print_project_table(rows)
    print("\nSelect a project, then run:")
    print("  python tools/workbench.py show <project>")


def print_show(repo_root: Path, query: str, *, as_json: bool) -> None:
    row = project_view(repo_root, query)
    if as_json:
        print(json.dumps(asdict(row), indent=2))
        return
    print(f"Project:       {row.title} ({row.id})")
    print(f"Canonical ref: {row.canonical_ref}")
    if row.resolved_ref != row.canonical_ref:
        print(f"Resolved ref:  {row.resolved_ref}")
    print(f"Path:          {row.path}")
    print(f"Stage:         {row.stage_name}")
    print(f"Next:          {row.next}")
    if row.summary:
        print(f"Summary:       {row.summary}")
    print("\nRead in order:")
    for item in row.read_order:
        print(f"  {item}")
    print("\nWork on this project with:")
    print(f"  git switch {row.canonical_ref}")


def print_status(repo_root: Path, *, as_json: bool) -> None:
    status = repo_status(repo_root)
    if as_json:
        print(json.dumps({
            "branch": status.branch,
            "commit": status.commit,
            "dirty": status.dirty,
            "current_cases": [asdict(row) for row in status.current_cases],
            "other_cases": [asdict(row) for row in status.other_cases],
        }, indent=2))
        return
    print(
        f"Spec Workbench  branch={status.branch}  commit={status.commit}  "
        f"worktree={'dirty' if status.dirty else 'clean'}"
    )
    print("\nCurrent checkout:")
    _print_case_table(status.current_cases)
    if status.other_cases:
        print("\nCases available on other refs (exhaustive history view):")
        _print_case_table(status.other_cases)
    print("\nFor normal project discovery use:")
    print("  python tools/workbench.py list")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Repository entry point for Spec Workbench.")
    sub = parser.add_subparsers(dest="command")

    listing = sub.add_parser("list", help="list curated working projects")
    listing.add_argument("--json", action="store_true", help="emit machine-readable JSON")

    show = sub.add_parser("show", help="resolve one indexed project")
    show.add_argument("project", help="project id, title, or indexed alias")
    show.add_argument("--json", action="store_true", help="emit machine-readable JSON")

    status = sub.add_parser("status", help="show exhaustive checkout/history status")
    status.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    command = args.command or "list"
    as_json = getattr(args, "json", False)
    try:
        repo_root = find_repo_root()
        if command == "list":
            print_list(repo_root, as_json=as_json)
        elif command == "show":
            print_show(repo_root, args.project, as_json=as_json)
        elif command == "status":
            print_status(repo_root, as_json=as_json)
        else:
            parser.error(f"unknown command: {command}")
    except (WorkbenchError, NavigationError) as exc:
        print(f"workbench: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
