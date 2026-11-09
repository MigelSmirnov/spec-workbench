#!/usr/bin/env python3
"""Ask the generator's own model where the design texts would force it to guess.

    python tools/design_questions.py ask examples/<case> --state 1
    python tools/design_questions.py status examples/<case> --state 1

    python tools/design_questions.py ask examples/<case> --state 1 --since <git-ref>
    python tools/design_questions.py ask examples/<case> --state 1 --provider codex
    python tools/design_questions.py dispose examples/<case> --state 1 --topic T3 \
        (--fixed <commit> | --carried <later state|generation|factory_checks|deploy> --what <text>
         | --accepted <reason>) [--round round-07] [--unit A5]
    python tools/design_questions.py carried examples/<case> [--to factory_checks]
    python tools/design_questions.py rejudge examples/<case> --state 7 --unit <module>

`ask` runs one round (several independent reviews, grouped into topics; topics
raised by two reviews are judged) and keeps it under
examples/<case>/questions/state<N>/. It reviews only the units that need a
round: never reviewed, or changed since their latest review (one round per
change). `--since` reopens a state closed at that git ref: the judge sees the
change and may set aside topics about passages the change did not touch.

`ask --probe OUT` asks State 7 over every generated module (or each
`--module`) on its current prompt, closed or not, and keeps the round in OUT,
outside the case: no round, closure or disposition is recorded and no
precedent is offered. It measures a change of the round's own instruction and
logs the input size of every request.

`dispose` records the author's disposition of a judged topic beside its round.
`rejudge` checks the kept judge answers of one unchanged State 7 module's
latest round again under the current judge rules (judge.RULES_VERSION and the
standard sections) and keeps the result as a new round that asks no model; the
earlier round stays as written. `status` names the modules it applies to.
`status` exits 0 when the state is closed — every unit's latest round on its
current text raised no open contradiction and every other judged topic of it
has a disposition (units closed by two clear rounds before 2026-11-08 stay
closed) — and its transition holds (skills/spec-authoring/TRANSITION_PROTOCOL.md:
what the state owns, checks and receives), and 1 otherwise; a closed round
never hides a blocking deterministic result. `carried` lists what the
dispositions carried to later layers.

State 7 is asked module by module on the prompts the Factory builds for the
generated modules (`--factory-root`, default SPEC_WORKBENCH_FACTORY_ROOT or the
sibling code_factory), from the case's assembled global_spec.json.
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
        f"deferred={summary.get('deferred_topics', 0)} "
        f"clear={str(summary.get('clear', not summary['repeated_topics'])).lower()} "
        f"closed={str(summary['closed']).lower()} "
        f"transition_ready={str(summary.get('transition_ready', True)).lower()}"
    ]
    if "scope" in summary:
        lines.append(f"  units: reviewed={len(summary['scope'])} blocked={summary['blocked_units'] or '-'} "
                     f"set_aside={summary['set_aside']} open_after={summary['open_units'] or '-'}")
    if summary.get("awaiting_disposition") or summary.get("contradiction_units"):
        lines.append(f"  awaiting disposition: {', '.join(summary.get('awaiting_disposition') or []) or '-'}; "
                     f"open contradiction in: {', '.join(summary.get('contradiction_units') or []) or '-'} "
                     "(dispose of the topics; a contradiction closes by a change and one round on it)")
    for topic in summary["topics"]:
        verdict = ""
        if "judgement" in topic:
            j = topic["judgement"]
            verdict = f" <{j['kind']}{'' if j['verified'] else ', UNVERIFIED: ' + j.get('failure', '')}{', BLOCKING' if j['blocking'] else ''}{', DEFERRED to ' + j['deferred_to'] if j.get('deferred_to') else ''}>"
        where = f" ({', '.join(topic['units'])})" if topic.get("units") else ""
        lines.append(f"  [{len(topic['runs'])}/{summary['reviews']}] {topic['topic']}{where}{verdict}")
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
    ask.add_argument("--provider", choices=("openai", "codex"), default="codex",
                     help="codex, the standard provider, asks through the Codex CLI login; its rounds are recorded under that provider")
    ask.add_argument("--model")
    ask.add_argument("--reasoning")
    ask.add_argument("--since", help="git ref at which a reopened state was closed")
    ask.add_argument("--factory-root", type=Path, help="the Factory that builds the State 7 prompts")
    ask.add_argument("--probe", metavar="OUT", type=Path,
                     help="State 7 only: ask every generated module (or --module) on its current prompt, closed or "
                          "not, and keep the round in OUT outside the case; it records no round and closes nothing")
    ask.add_argument("--module", action="append", help="with --probe: a module to ask (repeatable; default: all)")
    ask.add_argument("--json", action="store_true")
    checks = sub.add_parser("judge-checks", help="judge each bound check once, kept by digest (witness_judgement)")
    checks.add_argument("case", type=Path)
    checks.add_argument("--provider", choices=("openai", "codex"), default="codex")
    checks.add_argument("--model")
    checks.add_argument("--reasoning")
    checks.add_argument("--json", action="store_true")
    dispose = sub.add_parser("dispose", help="record the author's disposition of a judged topic")
    dispose.add_argument("case", type=Path)
    dispose.add_argument("--state", type=int, required=True)
    dispose.add_argument("--topic", required=True, help="the topic's id in the round (T3, or module:T1 in State 7)")
    dispose.add_argument("--round", dest="round_name", help="the round, e.g. round-07 (default: the latest)")
    dispose.add_argument("--unit", help="dispose of the topic for this unit only (default: every unit it concerns)")
    kind = dispose.add_mutually_exclusive_group(required=True)
    kind.add_argument("--fixed", metavar="COMMIT", help="the commit of the change that answers it")
    kind.add_argument("--carried", metavar="LAYER",
                      help="the receiving layer: a later state number, generation, factory_checks or deploy")
    kind.add_argument("--accepted", metavar="REASON", help="the author's reason to accept it as it stands")
    dispose.add_argument("--what", help="with --carried: what the receiving layer must decide")
    dispose.add_argument("--json", action="store_true")
    again = sub.add_parser("rejudge", help="check one unchanged module's kept verdicts under the current judge rules")
    again.add_argument("case", type=Path)
    again.add_argument("--state", type=int, required=True)
    again.add_argument("--unit", required=True, help="the unit (State 7: the module) whose latest round to check")
    again.add_argument("--factory-root", type=Path, help="the Factory that builds the State 7 prompts")
    again.add_argument("--json", action="store_true")
    listing = sub.add_parser("carried", help="list what the authors' dispositions carried to later layers")
    listing.add_argument("case", type=Path)
    listing.add_argument("--to", help="a state number, generation, factory_checks or deploy")
    listing.add_argument("--json", action="store_true")
    stat = sub.add_parser("status")
    stat.add_argument("case", type=Path)
    stat.add_argument("--state", type=int, required=True)
    stat.add_argument("--factory-root", type=Path, help="the Factory that builds the State 7 prompts")
    stat.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.command == "judge-checks":
            import design_decision_witness
            import witness_judgement

            materials = design_decision_witness.binding_material(args.case)
            done = witness_judgement.judge(args.case, _provider(args), materials)
            rows = witness_judgement.verdicts(args.case, materials)
            if args.json:
                print(json.dumps({"judged": len(done), "verdicts": rows}, ensure_ascii=False, indent=2))
            else:
                print(f"judged {len(done)} check(s) now; {len(rows)} binding(s):")
                for row in rows:
                    print(f"  {row['decision']} {row['witness']} [{row['outcome']}] "
                          f"{row.get('reason') or row.get('why') or ''}"[:200])
            return 0 if all(r["outcome"] == "asserts" for r in rows) else 1
        if args.command == "dispose":
            disposition = "fixed" if args.fixed else "carried" if args.carried else "accepted"
            entry = service.dispose(args.case, args.state, args.topic, disposition, round_name=args.round_name,
                                    unit=args.unit, ref=args.fixed, to=args.carried, what=args.what,
                                    reason=args.accepted)
            print(json.dumps(entry, ensure_ascii=False, indent=2) if args.json
                  else f"{entry['topic']}: {entry['disposition']}"
                       + (f" for {entry['unit']}" if entry.get("unit") else ""))
            return 0
        if args.command == "rejudge":
            summary = service.rejudge(args.case, args.state, args.unit, args.factory_root)
            if args.json:
                print(json.dumps(summary, ensure_ascii=False, indent=2))
            else:
                print(f"State {summary['state']} {summary['round']}: {args.unit} re-judged from "
                      f"{summary['rejudge']['of']} under judge rules v{summary['judge_rules']['version']}")
                for topic in summary["topics"]:
                    j, was = topic.get("judgement") or {}, (topic.get("rejudged") or {}).get("judgement") or {}
                    print(f"  {topic.get('id')}: {was.get('kind')}{' BLOCKING' if was.get('blocking') else ''}"
                          f" -> {j.get('kind')}{' BLOCKING' if j.get('blocking') else ''}")
                print(f"  {args.unit}: {'open' if args.unit in summary['open_units'] else 'closed'}; "
                      f"state closed={str(summary['closed']).lower()}")
            return 0 if args.unit not in summary["open_units"] else 1
        if args.command == "carried":
            to = None if args.to is None else (int(args.to.removeprefix("state")) if args.to.removeprefix("state").isdigit()
                                               else args.to)
            rows = service.carried_items(args.case, to)
            if args.json:
                print(json.dumps(rows, ensure_ascii=False, indent=2))
            else:
                for row in rows:
                    print(f"State {row['state']} {row['round']} {row['topic']}"
                          + (f" ({row['unit']})" if row.get("unit") else "")
                          + f" -> {row['to']}: {row['what']}")
            return 0
        if args.command == "ask" and args.probe is not None:
            summary = service.probe_round(args.case, args.state, _provider(args), args.probe, args.runs,
                                          args.factory_root, args.module)
            if args.json:
                print(json.dumps(summary, ensure_ascii=False, indent=2))
            else:
                for module, row in summary["modules"].items():
                    print(f"{module}: topics={row['topics']} blocking={row['blocking']} kinds={row['kinds']} "
                          f"prompt_chars={row['prompt_chars']}")
                print(f"probe kept in {args.probe}: blocking={summary['blocking_topics']}")
            return 0
        if args.command == "ask" and args.module:
            parser.error("--module needs --probe")
        if args.command == "ask":
            summary = service.ask_round(args.case, args.state, _provider(args), args.runs, args.since,
                                        args.factory_root)
            print(json.dumps(summary, ensure_ascii=False, indent=2) if args.json else _human_round(summary))
            return 0 if summary["closed"] and summary["transition_ready"] else 1
        result = service.status(args.case, args.state, args.factory_root, with_transition=True)
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"State {result['state']} questions: closed={str(result['closed']).lower()} "
                  f"ready={str(result['ready']).lower()} "
                  f"round={result['round']} provider={result.get('provider')} — {result['reason']}")
            for finding in result["transition"]["findings"][:20]:
                print(f"  transition [{finding.get('outcome', 'gate')}] {finding.get('code')}: "
                      f"{str(finding.get('message', ''))[:160]}")
            for key, row in (result.get("unit_status") or {}).items():
                parts = [f"needs a round: {row['needs_round']}"] if row.get("needs_round") else []
                if row.get("contradictions") or row.get("unverified"):
                    parts.append("contradiction " + ", ".join(row.get("contradictions", []) + row.get("unverified", [])))
                if row.get("awaiting"):
                    parts.append(f"awaiting disposition {', '.join(row['awaiting'])} ({row.get('round')})")
                if row.get("carried"):
                    parts.append("carried " + ", ".join(f"{c['topic']} -> {c['to']}" for c in row["carried"]))
                print(f"  {'closed' if row['closed'] else 'open  '} {key}: {'; '.join(parts)}")
            for row in result.get("carried_in") or []:
                print(f"  received from State {row['state']} {row['round']} {row['topic']}: {row['what']}")
            if result.get("closed_at") and result.get("needs_round"):
                print(f"  reopened since {result['closed_at']}: ask --since {result['closed_at']}")
        return 0 if result["ready"] else 1
    except (service.QuestionRoundError, ValueError, RuntimeError) as exc:
        print(f"design_questions: error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
