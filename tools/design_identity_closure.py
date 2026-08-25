from __future__ import annotations

import argparse
import json
from pathlib import Path
from identity_workbench import inspect_model, inventory, verify
from identity_workbench.model import IdentityWorkbenchError

def lint(project: Path):
    """Compatibility alias for callers of the original checker."""
    return verify(project)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect and verify model identity closure."
    )
    parser.add_argument("project", type=Path)
    operation = parser.add_mutually_exclusive_group()
    operation.add_argument("--inventory", action="store_true")
    operation.add_argument("--get", metavar="MODEL")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    try:
        report = inventory(args.project) if args.inventory else (
            inspect_model(args.project, args.get) if args.get else verify(args.project)
        )
    except IdentityWorkbenchError as error:
        parser.error(str(error))
    if args.as_json or args.inventory or args.get:
        print(json.dumps(report, indent=2))
    else:
        summary = report["summary"]
        print(
            "Identity closure: "
            f"{summary['assembled_runtime_models']} assembled runtime models, "
            f"{summary['errors']} errors"
        )
        for finding in report["findings"]:
            print(f"ERROR {finding['code']} [{finding['model']}] - {finding['message']}")
    return 1 if report["findings"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
