#!/usr/bin/env python3
"""Imports closure: imports.module_internal from the author's decisions.

    python tools/design_imports.py examples/<case> --draft [--factory-root <dir>]
    python tools/design_imports.py examples/<case> --coverage [--json] [--factory-root <dir>]

``--draft`` writes (or extends) 65_imports.json: a scope for every contract
and every module, the contract's signature types in ``uses``, every other
candidate in ``pending``. Nothing else is accepted for the author.

``--coverage`` is the gate (tools/IMPORTS_WORKBENCH.md §7): every candidate
decided, no stale scope, every use resolvable and allowed by the module order,
weak candidates only on a cited note or the code, and — when the case has a
Factory target — the accepted code's own project imports agree with ``uses``.
The Factory checkout is --factory-root, SPEC_WORKBENCH_FACTORY_ROOT or a
sibling code_factory; a target without a reachable Factory blocks.

Exit codes: 0 ready (or draft written); 1 findings; 2 usage or input error.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from imports_workbench import service
from imports_workbench.model import ImportsError


def _render(report: dict) -> str:
    summary = report["summary"]
    lines = [
        f"Imports closure: {summary['scopes_decided']}/{summary['scopes']} scopes decided; "
        f"pending={summary['pending']}; stale={summary['stale']}; code_evidence={summary['code_evidence']}; "
        f"errors={summary['errors']}; handoff_ready={str(summary['handoff_ready']).lower()}; "
        f"strict_ready={str(summary['strict_ready']).lower()}"
    ]
    if report["code_evidence"].get("reason"):
        lines.append(f"  code evidence: {report['code_evidence']['reason']}")
    for module, reason in report["out_of_scope"].items():
        lines.append(f"  not judged: {module} — {reason}")
    for item in report["findings"]:
        detail = item.get("candidate") or {k: item[k] for k in ("symbol", "provider") if k in item}
        lines.append(f"{item['severity'].upper()} {item['code']} {item['subject']} - {item['message']}"
                     + (f" {json.dumps(detail, ensure_ascii=False, sort_keys=True)}" if detail else ""))
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("case", type=Path)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--draft", action="store_true")
    action.add_argument("--coverage", action="store_true")
    parser.add_argument("--factory-root", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if not args.case.is_dir():
        print(f"design_imports: error: case directory not found: {args.case}", file=sys.stderr)
        return 2
    try:
        if args.draft:
            result = service.draft(args.case, args.factory_root)
            if args.json:
                print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
            else:
                print(f"{result['table']}: {result['scopes']} scopes; {result['pending']} candidates pending")
            return 0
        report = service.coverage(args.case, args.factory_root)
    except ImportsError as exc:
        print(f"design_imports: error: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        print(_render(report), end="")
    return 0 if report["summary"]["handoff_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
