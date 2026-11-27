"""Open a State 2 decision form at an existing accepted decision, preview or apply it."""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

import design_editor
import design_index


def required(form, key, hint):
    text = form.get(key)
    if not isinstance(text, str) or not text.strip() or len(text.splitlines()) != 1:
        raise ValueError(f"{key}: {hint}")
    return text.strip()


def open_form(case, anchor):
    index = design_index.build_index(case)
    items = {item["key"]: item for item in index["items"]}
    item = items.get(anchor.upper())
    if not item or item["kind"] != "decision" or item["state"] != 2 or not item["explicit_id"]:
        raise ValueError("Choose an indexed State 2 decision from design_index.py --list --state 2 --kind decision")
    loc = item["source"]
    raw = (case / loc["path"]).read_bytes()
    lines = raw.decode().splitlines()
    excerpt = lines[loc["start_line"] - 1:loc["end_line"]]
    level = len(excerpt[0]) - len(excerpt[0].lstrip("#"))
    if level >= 6:
        raise ValueError("Choose a decision whose heading allows child sections")

    def next_id(prefix, width):
        numbers = [int(key[len(prefix):]) for key in items if re.fullmatch(prefix + r"\d+", key)]
        return f"{prefix}{max(numbers, default=0) + 1:0{width}d}"

    return {
        "anchor": item["key"], "revision": hashlib.sha256(raw).hexdigest(),
        "source_location": f"{loc['path']}:{loc['start_line']}", "source_text": "\n".join(excerpt),
        "prompts": {
            "situation": "When can the disputed outcomes occur?",
            "outcome": "Which result may each participant observe? A mechanism can permit several answers.",
            "source_quote": "Quote the accepted fact supporting this outcome. If it leaves the choice open, select question.",
            "guarantee": "What promise survives every permitted implementation?",
            "observation": "What would demonstrate that promise? Describe the observation before choosing a test mechanism.",
            "consequence": "Who owns this obligation and what follows from it?",
            "owner_question": "What choice must the owner make? State the competing outcomes.",
        },
        "disposition": None, "situation": None, "source_quote": None, "outcome": None,
        "guarantee": None, "observation": None, "consequence": None, "owner_question": None,
        "choices": ["decision", "question"],
        "decision_id": next_id("A", 2), "question_id": next_id("OQ-", 3),
    }, level


def render(form, current, level):
    situation = required(form, "situation", current["prompts"]["situation"])
    title = "#" * level
    section = title + "#"
    source = current["anchor"]
    if form.get("disposition") == "question":
        key = form["question_id"]
        question = required(form, "owner_question", current["prompts"]["owner_question"])
        return key, f"{title} Open question {key}\n\nContext: {source}. {situation}\n\nQuestion for owner: {question}\n"
    if form.get("disposition") != "decision":
        raise ValueError("disposition: choose decision for a supported outcome or question to ask its owner")
    key = form["decision_id"]
    quote = required(form, "source_quote", current["prompts"]["source_quote"])
    if quote not in current["source_text"]:
        raise ValueError(f"source_quote: select an exact passage of {source}, or save a question for the owner")
    outcome, guarantee, observation, consequence = [
        required(form, k, current["prompts"][k]) for k in ("outcome", "guarantee", "observation", "consequence")]
    invariant = f"INV-{key}-1"
    return key, (f"{title} Accepted decision {key}\n\nSource: {source} — {quote}\n\n"
                 f"{section} Normative rules\n\n1. {situation} {outcome}\n\n"
                 f"{section} Formal invariants\n\n- {invariant}: {guarantee}\n\n"
                 f"{section} Required tests\n\n1. {invariant}: {observation}\n\n"
                 f"{section} Consequence\n\n- {consequence}\n")


def run(args):
    if args.command == "template":
        print(json.dumps(open_form(args.case, args.anchor)[0], ensure_ascii=False, indent=2))
        return
    form = json.loads(args.form.read_text(encoding="utf-8"))
    current, level = open_form(args.case, form["anchor"])
    key, body = render(form, current, level)
    old = design_index.get_item(args.case, key)
    if old:
        src = old["source"]
        lines = (args.case / src["path"]).read_text().splitlines()
        if (src["path"] == current["source_location"].rsplit(":", 1)[0]
                and "\n".join(lines[src["start_line"]-1:src["end_line"]]).rstrip() == body.rstrip()):
            print(f"{key} already recorded.")
            return
        raise ValueError(f"{key} is occupied; regenerate the form")
    id_field = "question_id" if form["disposition"] == "question" else "decision_id"
    if key != current[id_field] or form["revision"] != current["revision"]:
        raise ValueError("The design changed. Reopen the form and review its source.")
    plan = design_editor.plan_sibling(args.case, current["anchor"], key, ("\n\n" + body + "\n").encode())
    if hashlib.sha256(plan.before).hexdigest() != form["revision"]:
        raise ValueError("The target changed while planning; reopen the form")
    print(design_editor.render_unified_diff(plan), end="")
    if args.command == "apply":
        design_editor.apply_plan(plan)
        print(f"Recorded {key} in {plan.relative_path}. Return to {current['anchor']}.")


def main(argv=None):
    cli = argparse.ArgumentParser(description=__doc__)
    commands = cli.add_subparsers(dest="command", required=True)
    for command in ("template", "preview", "apply"):
        p = commands.add_parser(command)
        p.add_argument("case", type=Path)
        if command == "template":
            p.add_argument("anchor", help="accepted State 2 decision providing context")
        else:
            p.add_argument("form", type=Path)
    try:
        run(cli.parse_args(argv))
    except (ValueError, KeyError, OSError, TypeError, design_editor.DesignEditorError) as exc:
        print(f"state2-form: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
