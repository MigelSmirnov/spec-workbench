#!/usr/bin/env python3
"""Cabinet Flow wall-clock source audit.

Design mode verifies that the project pins M47/A25 and does not expose a
caller-supplied "current UTC time" in State 5 Inputs.

Source mode additionally parses generated Python and enforces:
- host wall time is read only in the system_clock module;
- production system_clock.now() samples time.time_ns() exactly once;
- that sample is floored to integer epoch microseconds and wrapped in
  KernelInstant(epoch_us=...);
- local elapsed timeout measurement uses only time.monotonic_ns(), and only in
  sandbox_supervisor/service_transport implementation paths;
- float/performance/realtime alternatives are rejected.
"""
from __future__ import annotations

import argparse
import ast
import fnmatch
import re
import sys
from pathlib import Path

WALL_CALLS = {
    "time.time",
    "time.time_ns",
    "time.clock_gettime",
    "datetime.datetime.now",
    "datetime.datetime.utcnow",
    "datetime.date.today",
}
FORBIDDEN_DURATION_CALLS = {
    "time.monotonic",
    "time.perf_counter",
    "time.perf_counter_ns",
    "time.process_time",
    "time.process_time_ns",
}
ALLOWED_DURATION_CALL = "time.monotonic_ns"
DEFAULT_MONOTONIC_PATTERNS = ("*sandbox_supervisor*", "*service_transport*")


class Finding:
    def __init__(self, path: Path, line: int, message: str) -> None:
        self.path = path
        self.line = line
        self.message = message

    def render(self, root: Path) -> str:
        try:
            display = self.path.relative_to(root)
        except ValueError:
            display = self.path
        where = f"{display}:{self.line}" if self.line else str(display)
        return f"{where}: {self.message}"


def _section_inputs(text: str) -> list[tuple[int, str, str]]:
    lines = text.splitlines()
    current_op = ""
    result: list[tuple[int, str, str]] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        match = re.match(r"^## \`(public_op:[^\`]+)\`$", line)
        if match:
            current_op = match.group(1)
        if line == "### Inputs":
            start = i + 2
            j = start
            while j < len(lines) and not lines[j].startswith("### "):
                j += 1
            result.append((start + 1, current_op, "\n".join(lines[start:j])))
            i = j
            continue
        i += 1
    return result


def audit_design(project: Path) -> list[Finding]:
    findings: list[Finding] = []
    model_path = project / "01_models_runs.md"
    rules_path = project / "02_rules_runs.md"
    clock_path = project / "50_public_apis_system_clock.md"

    required = [
        (model_path, "## Model M47 — KernelInstant"),
        (model_path, "epoch_us"),
        (rules_path, "## Accepted decision A25 — kernel wall time has exactly one source"),
        (rules_path, "time.time_ns()"),
        (rules_path, "time.monotonic_ns()"),
        (clock_path, "KernelInstant M47"),
        (clock_path, "time.time_ns()"),
        (clock_path, "sample_ns // 1_000"),
    ]
    for path, token in required:
        if not path.is_file():
            findings.append(Finding(path, 0, "required design file is missing"))
            continue
        text = path.read_text(encoding="utf-8")
        if token not in text:
            findings.append(Finding(path, 0, f"required time-source contract token missing: {token!r}"))

    for path in sorted(project.glob("50_public_apis_*.md")):
        text = path.read_text(encoding="utf-8")
        for line, op, body in _section_inputs(text):
            lowered = body.lower()
            if "current utc time" in lowered:
                findings.append(
                    Finding(path, line, f"{op}: Inputs still accept or mention 'current UTC time'; owning module must call system_clock")
                )
    return findings


class Resolver(ast.NodeVisitor):
    def __init__(self) -> None:
        self.aliases: dict[str, str] = {}
        self.calls: list[tuple[ast.Call, str, str | None]] = []
        self.function_stack: list[str] = []

    def visit_Import(self, node: ast.Import) -> None:
        for item in node.names:
            local = item.asname or item.name.split(".")[0]
            self.aliases[local] = item.name

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module is None:
            return
        for item in node.names:
            if item.name == "*":
                continue
            local = item.asname or item.name
            self.aliases[local] = f"{node.module}.{item.name}"

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.function_stack.append(node.name)
        self.generic_visit(node)
        self.function_stack.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Call(self, node: ast.Call) -> None:
        self.calls.append((node, self.resolve(node.func), self.function_stack[-1] if self.function_stack else None))
        self.generic_visit(node)

    def resolve(self, node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return self.aliases.get(node.id, node.id)
        if isinstance(node, ast.Attribute):
            base = self.resolve(node.value)
            return f"{base}.{node.attr}" if base else node.attr
        return ""


def _matches(path: Path, root: Path, patterns: tuple[str, ...]) -> bool:
    rel = path.relative_to(root).as_posix()
    return any(fnmatch.fnmatch(rel, pattern) or fnmatch.fnmatch(path.name, pattern) for pattern in patterns)


def _system_clock_candidates(source_root: Path) -> list[Path]:
    return [
        p for p in source_root.rglob("*.py")
        if p.stem == "system_clock" or "system_clock" in p.parts
    ]


def _is_time_ns_call(node: ast.AST, resolver: Resolver) -> bool:
    return isinstance(node, ast.Call) and resolver.resolve(node.func) == "time.time_ns"


def _find_now_functions(tree: ast.AST) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
    return [
        n for n in ast.walk(tree)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == "now"
    ]


def _kernel_instant_return_contract(now_node: ast.AST, resolver: Resolver) -> bool:
    sample_names: set[str] = set()
    epoch_names: set[str] = set()

    for node in ast.walk(now_node):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets: list[ast.expr] = []
            value: ast.AST | None
            if isinstance(node, ast.Assign):
                targets = list(node.targets)
                value = node.value
            else:
                targets = [node.target]
                value = node.value
            if value is None:
                continue
            if _is_time_ns_call(value, resolver):
                for target in targets:
                    if isinstance(target, ast.Name):
                        sample_names.add(target.id)
            if (
                isinstance(value, ast.BinOp)
                and isinstance(value.op, ast.FloorDiv)
                and isinstance(value.right, ast.Constant)
                and value.right.value == 1000
                and isinstance(value.left, ast.Name)
                and value.left.id in sample_names
            ):
                for target in targets:
                    if isinstance(target, ast.Name):
                        epoch_names.add(target.id)

    for node in ast.walk(now_node):
        if not isinstance(node, ast.Return) or not isinstance(node.value, ast.Call):
            continue
        call = node.value
        func_name = resolver.resolve(call.func)
        if not (func_name == "KernelInstant" or func_name.endswith(".KernelInstant")):
            continue
        for kw in call.keywords:
            if kw.arg != "epoch_us":
                continue
            if isinstance(kw.value, ast.Name) and kw.value.id in epoch_names:
                return True
            if (
                isinstance(kw.value, ast.BinOp)
                and isinstance(kw.value.op, ast.FloorDiv)
                and isinstance(kw.value.right, ast.Constant)
                and kw.value.right.value == 1000
                and isinstance(kw.value.left, ast.Name)
                and kw.value.left.id in sample_names
            ):
                return True
    return False


def audit_source(
    source_root: Path,
    system_clock: Path | None,
    monotonic_patterns: tuple[str, ...],
) -> list[Finding]:
    findings: list[Finding] = []
    if system_clock is None:
        candidates = _system_clock_candidates(source_root)
        if len(candidates) != 1:
            findings.append(
                Finding(
                    source_root,
                    0,
                    f"expected exactly one system_clock Python module, found {len(candidates)}; pass --system-clock explicitly",
                )
            )
            return findings
        system_clock = candidates[0]
    else:
        system_clock = system_clock.resolve()

    parsed: dict[Path, tuple[ast.AST, Resolver]] = {}
    for path in sorted(source_root.rglob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, UnicodeDecodeError, SyntaxError) as exc:
            findings.append(Finding(path, getattr(exc, "lineno", 0) or 0, f"cannot parse Python source: {exc}"))
            continue
        resolver = Resolver()
        resolver.visit(tree)
        parsed[path.resolve()] = (tree, resolver)

        for node, call_name, function_name in resolver.calls:
            if call_name in WALL_CALLS:
                if path.resolve() != system_clock or call_name != "time.time_ns" or function_name != "now":
                    findings.append(
                        Finding(path, node.lineno, f"forbidden wall-clock call {call_name}; only system_clock.now may call time.time_ns")
                    )
            if call_name in FORBIDDEN_DURATION_CALLS:
                findings.append(
                    Finding(path, node.lineno, f"forbidden duration clock {call_name}; use time.monotonic_ns only where A25 permits")
                )
            if call_name == ALLOWED_DURATION_CALL and not _matches(path, source_root, monotonic_patterns):
                findings.append(
                    Finding(path, node.lineno, "time.monotonic_ns is allowed only in sandbox_supervisor/service_transport timeout code")
                )

    clock_entry = parsed.get(system_clock)
    if clock_entry is None:
        findings.append(Finding(system_clock, 0, "system_clock module is missing or could not be parsed"))
        return findings

    tree, resolver = clock_entry
    now_functions = _find_now_functions(tree)
    production_now: list[ast.FunctionDef | ast.AsyncFunctionDef] = []
    for candidate in now_functions:
        calls = [
            node for node in ast.walk(candidate)
            if isinstance(node, ast.Call) and resolver.resolve(node.func) == "time.time_ns"
        ]
        if calls:
            production_now.append(candidate)
            if len(calls) != 1:
                findings.append(
                    Finding(
                        system_clock,
                        candidate.lineno,
                        f"production system_clock.now must call time.time_ns exactly once, found {len(calls)}",
                    )
                )

    if len(production_now) != 1:
        findings.append(
            Finding(
                system_clock,
                0,
                f"expected exactly one concrete now() that samples time.time_ns, found {len(production_now)}",
            )
        )
        return findings

    now_node = production_now[0]
    if not _kernel_instant_return_contract(now_node, resolver):
        findings.append(
            Finding(
                system_clock,
                now_node.lineno,
                "production system_clock.now must floor the one time.time_ns sample by 1000 and return KernelInstant(epoch_us=...)",
            )
        )
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project", type=Path, help="Path to examples/cabinet-flow")
    parser.add_argument("--source-root", type=Path, help="Generated Python source tree to audit")
    parser.add_argument("--system-clock", type=Path, help="Exact generated system_clock.py path")
    parser.add_argument(
        "--monotonic-allow",
        action="append",
        default=[],
        help="Additional fnmatch pattern allowed to call time.monotonic_ns()",
    )
    args = parser.parse_args()

    project = args.project.resolve()
    findings = audit_design(project)
    if args.source_root:
        source_root = args.source_root.resolve()
        patterns = tuple(DEFAULT_MONOTONIC_PATTERNS) + tuple(args.monotonic_allow)
        findings.extend(audit_source(source_root, args.system_clock, patterns))

    if findings:
        for finding in findings:
            print(finding.render(project))
        print(f"FAIL: {len(findings)} time-source finding(s)")
        return 1

    mode = "design + source" if args.source_root else "design"
    print(f"PASS: Cabinet Flow time-source audit ({mode})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
