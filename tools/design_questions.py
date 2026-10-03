#!/usr/bin/env python3
"""Ask the generator's own model where the design texts would force it to guess.

    python tools/design_questions.py ask examples/<case> --state 1
    python tools/design_questions.py status examples/<case> --state 1

    python tools/design_questions.py ask examples/<case> --state 1 --since <git-ref>
    python tools/design_questions.py ask examples/<case> --state 1 --provider codex

`ask` runs one round (several independent reviews, grouped into topics; topics
raised by two reviews are judged) and keeps it under
examples/<case>/questions/state<N>/. `--since` reopens a state closed at that
git ref: the judge sees the change and may set aside topics about passages the
change did not touch. `status` exits 0 when the state is closed — two latest
rounds clear on the same texts, unchanged since — and 1 otherwise.
The method is skills/spec-authoring/QUESTIONS.md.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from questions_workbench import service
from questions_workbench.provider import CodexCliProvider, OpenAIProvider


def _human_round(summary: dict) -> str:
    lines = [
        f"State {summary['state']} {summary['round']}: reviews={summary['reviews']} "
        f"points={summary['points']} topics={len(summary['topics'])} "
        f"repeated={summary['repeated_topics']} blocking={summary.get('blocking_topics', '-')} "
        f"clear={str(summary.get('clear', not summary['repeated_topics'])).lower()} "
        f"closed={str(summary['closed']).lower()}"
    ]
    for topic in summary["topics"]:
        verdict = ""
        if "judgement" in topic:
            j = topic["judgement"]
            verdict = f" <{j['kind']}{'' if j['verified'] else ', UNVERIFIED: ' + j.get('failure', '')}{', BLOCKING' if j['blocking'] else ''}>"
        lines.append(f"  [{len(topic['runs'])}/{summary['reviews']}] {topic['topic']}{verdict}")
    return "\n".join(lines)


def _provider(args: argparse.Namespace):
    factory = CodexCliProvider if args.provider == "codex" else OpenAIProvider
    return factory(args.model, args.reasoning)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    ask = sub.add_parser("ask")
    ask.add_argument("case", type=Path)
    ask.add_argument("--state", type=int, required=True)
    ask.add_argument("--runs", type=int, default=service.DEFAULT_RUNS)
    ask.add_argument("--provider", choices=("openai", "codex"), default="openai",
                     help="codex asks through the Codex CLI login; its rounds are recorded under that provider")
    ask.add_argument("--model")
    ask.add_argument("--reasoning")
    ask.add_argument("--since", help="git ref at which a reopened state was closed")
    ask.add_argument("--json", action="store_true")
    stat = sub.add_parser("status")
    stat.add_argument("case", type=Path)
    stat.add_argument("--state", type=int, required=True)
    stat.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.command == "ask":
            summary = service.ask_round(args.case, args.state, _provider(args), args.runs, args.since)
            print(json.dumps(summary, ensure_ascii=False, indent=2) if args.json else _human_round(summary))
            return 0 if summary["closed"] else 1
        result = service.status(args.case, args.state)
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"State {result['state']} questions: closed={str(result['closed']).lower()} "
                  f"round={result['round']} provider={result.get('provider')} — {result['reason']}")
            for topic in result.get("repeated", []):
                print(f"  [{len(topic['runs'])}] {topic['topic']}")
        return 0 if result["closed"] else 1
    except (service.QuestionRoundError, ValueError, RuntimeError) as exc:
        print(f"design_questions: error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
