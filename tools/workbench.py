from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


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
    out = _git(start, "rev-parse", "--show-toplevel")
    return Path(out.strip()).resolve()


def current_branch(repo_root: Path) -> str:
    branch = _git(repo_root, "branch", "--show-current").strip()
    return branch or "(detached HEAD)"


def current_commit(repo_root: Path) -> str:
    return _git(repo_root, "rev-parse", "--short", "HEAD").strip()


def is_dirty(repo_root: Path) -> bool:
    return bool(_git(repo_root, "status", "--porcelain").strip())


def known_refs(repo_root: Path) -> list[str]:
    local_raw = _git(
        repo_root,
        "for-each-ref",
        "--format=%(refname:short)",
        "refs/heads",
    )
    remote_raw = _git(
        repo_root,
        "for-each-ref",
        "--format=%(refname:short)",
        "refs/remotes",
    )
    local = [line.strip() for line in local_raw.splitlines() if line.strip()]
    remote = [
        line.strip()
        for line in remote_raw.splitlines()
        if line.strip() and not line.strip().endswith("/HEAD")
    ]

    result = list(local)
    local_names = set(local)
    for ref in remote:
        short = ref.split("/", 1)[1] if "/" in ref else ref
        if short in local_names:
            continue
        if ref not in result:
            result.append(ref)

    branch = current_branch(repo_root)
    if branch != "(detached HEAD)" and branch not in result:
        result.insert(0, branch)

    def ref_key(ref: str) -> tuple[int, str]:
        return (0 if ref == "main" else 1, ref)

    return sorted(dict.fromkeys(result), key=ref_key)


def _case_tree_oid(repo_root: Path, ref: str, case: str) -> str | None:
    out = _git(
        repo_root,
        "rev-parse",
        f"{ref}:examples/{case}",
        check=False,
    ).strip()
    return out or None


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
    result = []
    for line in out.splitlines():
        line = line.strip()
        if line.startswith(prefix):
            result.append(line[len(prefix):])
    return result


def _case_names_from_ref(repo_root: Path, ref: str) -> list[str]:
    out = _git(
        repo_root,
        "ls-tree",
        "-d",
        "--name-only",
        ref,
        "--",
        "examples",
        check=False,
    )
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

    prefix = "examples/"
    fallback = []
    for line in out.splitlines():
        line = line.strip()
        if line.startswith(prefix):
            fallback.append(line[len(prefix):].split("/", 1)[0])
    return sorted(dict.fromkeys(fallback))


def _case_dirty(repo_root: Path, case: str) -> bool:
    out = _git(
        repo_root,
        "status",
        "--porcelain",
        "--",
        f"examples/{case}",
    )
    return bool(out.strip())


def _working_case_names(repo_root: Path) -> list[str]:
    examples = repo_root / "examples"
    if not examples.is_dir():
        return []
    return sorted(p.name for p in examples.iterdir() if p.is_dir())


def _working_case_files(repo_root: Path, case: str) -> list[str]:
    case_dir = repo_root / "examples" / case
    if not case_dir.is_dir():
        return []
    return sorted(
        p.relative_to(case_dir).as_posix()
        for p in case_dir.rglob("*")
        if p.is_file()
    )


def _stage_from_files(files: list[str]) -> tuple[int | None, str, str | None, int]:
    numbered: list[tuple[int, str]] = []
    for rel in files:
        name = Path(rel).name
        if len(name) < 4 or not name[:2].isdigit() or name[2] != "_":
            continue
        if not name.lower().endswith(".md"):
            continue
        numbered.append((int(name[:2]), rel))

    primary = []
    labels = dict(PRIMARY_STATES)
    for code, rel in numbered:
        if code in labels:
            primary.append((code, rel))

    if primary:
        code, rel = max(primary, key=lambda item: item[0])
        return code, labels[code], rel, len(numbered)

    return None, "No primary state", None, len(numbered)


def case_state_from_files(case: str, ref: str, files: list[str]) -> CaseState:
    code, name, state_file, numbered_docs = _stage_from_files(files)
    assembled = "global_spec.json" in files
    stage_name = "Assembly complete" if assembled else name
    return CaseState(
        case=case,
        ref=ref,
        stage_code=code,
        stage_name=stage_name,
        state_file=state_file,
        assembled=assembled,
        numbered_docs=numbered_docs,
    )


def list_cases(repo_root: Path, *, include_worktree: bool = True) -> list[CaseState]:
    result: list[CaseState] = []

    if include_worktree:
        branch = current_branch(repo_root)
        label = f"{branch} (worktree)"
        for case in _working_case_names(repo_root):
            result.append(
                case_state_from_files(
                    case,
                    label,
                    _working_case_files(repo_root, case),
                )
            )

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
            if tree_oid is None:
                continue
            if current_case_trees.get(case) == tree_oid:
                continue
            row = case_state_from_files(
                case,
                ref,
                _case_files_from_ref(repo_root, ref, case),
            )
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
    codes = [code for code, _ in PRIMARY_STATES]
    labels = dict(PRIMARY_STATES)
    if state.stage_code is None:
        return "00 Product boundary"
    for code in codes:
        if code > state.stage_code:
            return f"{code:02d} {labels[code]}"
    return "Assembly"


def repo_status(repo_root: Path) -> RepoStatus:
    branch = current_branch(repo_root)
    rows = list_cases(repo_root, include_worktree=True)
    current_ref = f"{branch} (worktree)"
    current_rows = [row for row in rows if row.ref == current_ref]

    current_names = {row.case for row in current_rows}
    other_rows = [
        row
        for row in rows
        if row.ref != current_ref and row.case not in current_names
    ]
    return RepoStatus(
        branch=branch,
        commit=current_commit(repo_root),
        dirty=is_dirty(repo_root),
        current_cases=current_rows,
        other_cases=other_rows,
    )


def _print_table(rows: list[CaseState]) -> None:
    if not rows:
        print("No case studies found.")
        return
    headers = ("CASE", "REF", "STAGE", "NEXT")
    data = [
        (
            row.case,
            row.ref,
            row.stage_name,
            next_primary_state(row),
        )
        for row in rows
    ]
    widths = [
        max(len(headers[i]), *(len(str(row[i])) for row in data))
        for i in range(len(headers))
    ]
    print("  ".join(headers[i].ljust(widths[i]) for i in range(len(headers))))
    print("  ".join("-" * widths[i] for i in range(len(headers))))
    for row in data:
        print("  ".join(str(row[i]).ljust(widths[i]) for i in range(len(headers))))


def print_list(repo_root: Path, *, as_json: bool) -> None:
    rows = list_cases(repo_root)
    if as_json:
        print(json.dumps([asdict(row) for row in rows], indent=2))
        return
    _print_table(rows)


def print_status(repo_root: Path, *, as_json: bool) -> None:
    status = repo_status(repo_root)
    if as_json:
        payload = {
            "branch": status.branch,
            "commit": status.commit,
            "dirty": status.dirty,
            "current_cases": [asdict(row) for row in status.current_cases],
            "other_cases": [asdict(row) for row in status.other_cases],
        }
        print(json.dumps(payload, indent=2))
        return

    print(
        f"Spec Workbench  branch={status.branch}  commit={status.commit}  "
        f"worktree={'dirty' if status.dirty else 'clean'}"
    )
    print()
    print("Current checkout:")
    _print_table(status.current_cases)
    if status.other_cases:
        print()
        print("Cases available on other refs:")
        _print_table(status.other_cases)
    print()
    print("Commands:")
    print("  python tools/workbench.py list")
    print("  python tools/workbench.py status --json")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Repository entry point for Spec Workbench."
    )
    sub = parser.add_subparsers(dest="command")

    status = sub.add_parser("status", help="show checkout and case-study status")
    status.add_argument("--json", action="store_true", help="emit machine-readable JSON")

    listing = sub.add_parser("list", help="list case studies across known git refs")
    listing.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    command = args.command or "status"
    as_json = getattr(args, "json", False)

    try:
        repo_root = find_repo_root()
        if command == "list":
            print_list(repo_root, as_json=as_json)
        elif command == "status":
            print_status(repo_root, as_json=as_json)
        else:
            parser.error(f"unknown command: {command}")
    except WorkbenchError as exc:
        print(f"workbench: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
