#!/usr/bin/env python3
"""Value-flow closure: every value a contract must produce, consume or fetch has somewhere to come from.

Judged over State 6 contracts and models, State 7 notes and State 3 collaborators,
before any assembly:

    outputs        a required instant of a result has a source
    inputs         a scalar argument of a constructing function has a sink
    collaborators  a module this module is said to know is reachable from its notes
    carriers       every fact State 1 claims and every field a rule, flow or operation names is in the model closure

    python tools/design_value_flow.py examples/<case> --coverage [--json]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from value_flow_workbench import ValueFlowError, coverage


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("project", type=Path)
    parser.add_argument("--coverage", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if not args.project.is_dir():
        print(f"design_value_flow: error: project directory not found: {args.project}", file=sys.stderr)
        return 2
    try:
        report = coverage(args.project)
    except ValueFlowError as exc:
        print(f"design_value_flow: error: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        summary = report["summary"]
        out, inp, col = summary["outputs"], summary["inputs"], summary["collaborators"]
        print(f"Value flow: functions={summary['functions_judged']} errors={summary['errors']} "
              f"handoff_ready={str(summary['handoff_ready']).lower()}")
        if out["enabled"]:
            print(f"  outputs        {out['pairs'] - out['unresolved']} of {out['pairs']} instants sourced {out['by_source']}")
        else:
            print(f"  outputs        not judged: {out['reason']}")
        print(f"  inputs         {inp['resolved']} of {inp['pairs']} scalar arguments of {inp['constructing_functions']} constructing functions have a sink")
        print(f"  collaborators  {col['reachable']} of {col['edges']} known collaborators reachable")
        car = summary["carriers"]
        print(f"  carriers       {car['facts']} State 1 facts of {car['state1_models']} models and {car['references']} "
              f"named fields checked against the closure; {car['without_carrier']} without a carrier")
        for finding in report["findings"]:
            print(f"  ✗ [{finding['code']}] {finding['message']}")
    return 1 if report["summary"]["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
