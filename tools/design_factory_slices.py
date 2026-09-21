#!/usr/bin/env python3
"""Pre-export probe: cut every module with the Factory's own slicer and ask its data/code seam."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from factory_slice_workbench import probe


def main(argv: list[str] | None = None) -> int:
    workbench_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", type=Path)
    parser.add_argument(
        "--factory-root", type=Path, default=workbench_root.parent / "code_factory"
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    case_root = args.case.resolve()
    source = case_root / "global_spec.json"
    if not source.is_file():
        print(f"design_factory_slices: error: source specification not found: {source}", file=sys.stderr)
        return 2
    report = probe(source, args.factory_root, case_root)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        summary = report["summary"]
        print(
            f"Factory slices: {summary['modules_sliced']} of {summary['modules_declared']} modules cut; "
            f"{summary['imports_examined']} induced imports examined; "
            f"{summary['seam_checked']} slices asked at the data/code seam; "
            f"{summary['constants_compared']} lowered constants compared; "
            f"findings={len(report['findings'])}; ready={str(report['ready']).lower()}"
        )
        for item in report["findings"]:
            scope = f" {item['module']}" if item.get("module") else ""
            print(f"BLOCK {item['code']}{scope} - {item['message']}")
    return 0 if report["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
