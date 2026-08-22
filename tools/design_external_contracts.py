from __future__ import annotations

import argparse
import json
from pathlib import Path

from external_contract_workbench import coverage


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify content-addressed external-contract evidence.")
    parser.add_argument("project", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = coverage(args.project)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        summary = report["summary"]
        print(
            f"External contracts: status={report['status']}; "
            f"contracts={summary['contracts']}; bindings={summary['bindings']}; "
            f"errors={summary['errors']}; ready={str(summary['handoff_ready']).lower()}"
        )
        for finding in report["findings"]:
            print(f"- {finding['code']}: {finding['message']}")
    return 0 if report["summary"]["handoff_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
