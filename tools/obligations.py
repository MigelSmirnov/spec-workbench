#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from obligation_workbench import build_graph, focus, frontier, list_obligations, metrics


def _render_list(payload: dict) -> None:
    for item in payload["obligations"]:
        targets = ", ".join(item["addressed_to"]) or item["resolution_owner"]
        print(f"{item['status']:7s} {item['precedence_class']:14s} {item['kind']:38s} {targets}")
        print(f"        caused_by {item['caused_by']}")


def _render_next(payload: dict) -> None:
    summary = payload["summary"]
    print(f"ENGINEERING FRONTIER — {payload['project_root']}")
    print(f"READY {summary['ready']}  BLOCKED {summary['blocked']}  SETTLED {summary['settled_nodes']}")
    print("\nREADY")
    for item in payload["READY"]:
        print(f"  {item['id']}  {item['kind']}  -> {', '.join(item['addressed_to']) or item['resolution_owner']}")
        print(f"    caused_by {item['caused_by']}")
    print("\nBLOCKED")
    for item in payload["BLOCKED"]["obligations"]:
        print(f"  {item['id']}  {item['kind']}  by {', '.join(item['blocked_by'])}")
    for item in payload["BLOCKED"]["nodes"]:
        print(f"  {item['node']}  locally_complete={str(item['locally_complete']).lower()}  by {', '.join(item['blocked_by'])}")
    print(f"\nSETTLED\n  nodes {payload['SETTLED']['count']}")


def _render_focus(payload: dict) -> None:
    state = payload["state"]
    print(
        f"FOCUS {payload['focus']}  locally_complete={str(state['locally_complete']).lower()} "
        f"globally_settled={str(state['globally_settled']).lower()}"
    )
    for section in ("OWNED", "INCOMING", "OUTGOING", "NOT_OWNED"):
        print(f"\n{section}")
        for item in payload[section]["obligations"]:
            print(f"  {item['kind']}  {item['id']}")
            if item.get("semantic_owner"):
                print(f"    semantic_owner {item['semantic_owner']}")
        for edge in payload[section].get("evidence_edges", []):
            print(f"  {edge['source']} -> {edge['target']}  [{edge['kind']}]")
        for claim in payload[section].get("semantic_claims", []):
            print(
                f"  {claim['semantic_key']}  owner={claim['semantic_owner']} "
                f"mode={claim['implementation_mode'] or 'unresolved'}"
            )
            if claim.get("irregular_reason"):
                print(f"    irregular_reason {claim['irregular_reason']}")
    print("\nBLOCKERS")
    for item in payload["BLOCKERS"]:
        print(f"  {item['kind']}  {item['id']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only engineering-obligation projection.")
    parser.add_argument("case", type=Path)
    operation = parser.add_mutually_exclusive_group(required=True)
    operation.add_argument("--list", action="store_true", dest="list_")
    operation.add_argument("--next", action="store_true")
    operation.add_argument("--focus", metavar="NODE")
    operation.add_argument("--metrics", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--factory-root", type=Path)
    parser.add_argument("--factory-project")
    args = parser.parse_args(argv)
    try:
        projection = build_graph(
            args.case,
            factory_root=args.factory_root,
            factory_project=args.factory_project,
        )
        if args.list_:
            payload, renderer = list_obligations(projection), _render_list
        elif args.next:
            payload, renderer = frontier(projection), _render_next
        elif args.focus:
            payload, renderer = focus(projection, args.focus), _render_focus
        else:
            payload, renderer = metrics(projection), lambda value: print(json.dumps(value, ensure_ascii=False, indent=2))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"obligations: error: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        renderer(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
