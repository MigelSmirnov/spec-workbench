#!/usr/bin/env python3
"""NEXT ENGINEERING OBLIGATIONS — read-only frontier over the design artifacts.

    python tools/obligations <case> next            the frontier: READY nodes and what blocks the rest
    python tools/obligations <case> list            every obligation, flat
    python tools/obligations <case> focus <node>    one node (a module: its own, its owned, what names it)
    python tools/obligations <case> metrics         counts, addressability, registry gaps, factory parity

Nothing is written.  ``authoring.py next`` keeps its ladder; this prints the
engineering frontier beside it.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1]
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from obligations import projection as proj  # noqa: E402


def _print_obligation(o: dict, indent: str = "      ") -> None:
    about = f"  about {o['about']}" if o.get("about") else ""
    print(f"{indent}{o['type']:34s} [{o['precedence']}]  caused_by {o['caused_by']}{about}")
    print(f"{indent}  → {o['hint']}")


def _render_frontier(payload: dict) -> None:
    s = payload["summary"]
    print(f"NEXT ENGINEERING OBLIGATIONS — {payload['project_root']}")
    print(f"READY {s['ready']}   BLOCKED {s['blocked']}   SETTLED {s['settled']}   obligations {s['obligations']}\n")
    print("READY")
    for node in payload["ready"]:
        print(f"  {node['node']}")
        for o in node["obligations"][:4]:
            _print_obligation(o)
        if len(node["obligations"]) > 4:
            print(f"      … {len(node['obligations']) - 4} more")
    print("\nBLOCKED")
    for node in payload["blocked"]:
        print(f"  {node['node']:56s} LOCAL {node['local'].upper():8s} SYSTEM BLOCKED  by {', '.join(node['blocked_by'])}")


def _render_focus(payload: dict) -> None:
    node = payload["node"]
    print(f"FOCUS {node['node']}   LOCAL {node['local'].upper()}   SYSTEM {node['system'].upper()}")
    print(" local obligations:")
    for o in node["obligations"]:
        _print_obligation(o, "   ")
    if payload["owned"]["counts"]:
        print(f" owned nodes: {payload['owned']['counts']}")
        for owned in payload["owned"]["open"]:
            print(f"   {owned['node']:54s} {owned['state']}")
            for o in owned["obligations"][:2]:
                _print_obligation(o, "        ")
            if owned["blocked_by"]:
                print(f"        blocked_by {owned['blocked_by']}")
    print(f" external blockers: {payload['external_blockers']}")
    print(f" named by others: {len(payload['named_by_others'])}")
    for o in payload["named_by_others"][:12]:
        print(f"   {o['addressed_to']:34s} {o['type']:28s} about {o['about']}")


def _render_list(payload: dict) -> None:
    for o in payload["obligations"]:
        print(f"{o['precedence']:14s} {o['type']:34s} {o['addressed_to']}")
        print(f"               caused_by {o['caused_by']}  → {o['hint']}")


def _render_metrics(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="obligations", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("project", type=Path)
    parser.add_argument("command", choices=("list", "next", "focus", "metrics"))
    parser.add_argument("node", nargs="?", help="node key for focus, e.g. module:effect_journal")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--factory-root", type=Path)
    parser.add_argument("--factory-project")
    args = parser.parse_args(argv)
    if not args.project.is_dir():
        print(f"obligations: error: project directory not found: {args.project}", file=sys.stderr)
        return 2
    if args.command == "focus" and not args.node:
        print("obligations: error: focus needs a node key", file=sys.stderr)
        return 2
    projection = proj.project(args.project, factory_root=args.factory_root, factory_project=args.factory_project)
    if args.command == "next":
        payload = proj.frontier(projection); render = _render_frontier
    elif args.command == "list":
        payload = proj.listing(projection); render = _render_list
    elif args.command == "metrics":
        payload = proj.metrics(projection); render = _render_metrics
    else:
        try:
            payload = proj.focus(projection, args.node)
        except KeyError:
            print(f"obligations: error: unknown node {args.node}", file=sys.stderr)
            return 2
        render = _render_focus
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        render(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
