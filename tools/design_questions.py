#!/usr/bin/env python3
"""Ask the generator's own model where the design texts would force it to guess.

    python tools/design_questions.py ask examples/<case> --state 1
    python tools/design_questions.py status examples/<case> --state 1

`ask` runs one round (several independent reviews, grouped into topics) and
keeps it under examples/<case>/questions/state<N>/. `status` exits 0 when the
latest round closed the state and the texts have not changed since, 1 otherwise.
The method is skills/spec-authoring/QUESTIONS.md.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from questions_workbench import service
from questions_workbench.provider import OpenAIProvider


def _human_round(summary: dict) -> str:
    lines = [
        f"State {summary['state']} {summary['round']}: reviews={summary['reviews']} "
        f"points={summary['points']} topics={len(summary['topics'])} "
        f"repeated={summary['repeated_topics']} closed={str(summary['closed']).lower()}"
    ]
    for topic in summary["topics"]:
        lines.append(f"  [{len(topic['runs'])}/{summary['reviews']}] {topic['topic']}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    ask = sub.add_parser("ask")
    ask.add_argument("case", type=Path)
    ask.add_argument("--state", type=int, required=True)
    ask.add_argument("--runs", type=int, default=service.DEFAULT_RUNS)
    ask.add_argument("--model")
    ask.add_argument("--reasoning")
    ask.add_argument("--json", action="store_true")
    stat = sub.add_parser("status")
    stat.add_argument("case", type=Path)
    stat.add_argument("--state", type=int, required=True)
    stat.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.command == "ask":
            summary = service.ask_round(args.case, args.state, OpenAIProvider(args.model, args.reasoning), args.runs)
            print(json.dumps(summary, ensure_ascii=False, indent=2) if args.json else _human_round(summary))
            return 0 if summary["closed"] else 1
        result = service.status(args.case, args.state)
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"State {result['state']} questions: closed={str(result['closed']).lower()} "
                  f"round={result['round']} — {result['reason']}")
            for topic in result.get("repeated", []):
                print(f"  [{len(topic['runs'])}] {topic['topic']}")
        return 0 if result["closed"] else 1
    except (service.QuestionRoundError, ValueError, RuntimeError) as exc:
        print(f"design_questions: error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
