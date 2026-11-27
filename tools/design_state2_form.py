"""State 2 form at an accepted decision.

The author saves a proposal for review or a question for the owner; nothing the
author writes becomes a requirement. A reviewer reads the proposal and accepts
it into the specification, or rejects it.
"""
import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path

import authoring_form as forms
import design_editor
import design_index
import design_trace

TOOL = "design_state2_form.py"
PROPOSALS = Path("proposals") / "state2"
SCHEMA = "spec_workbench_state2_proposal.v1"
ANSWERS = ("title", "situation", "source_quote", "outcome", "guarantee", "observation", "consequence")
# Words that usually name how a result is achieved. A cue for the reader, never a refusal.
MECHANISM = re.compile(r"\b(lock\w*|mutex\w*|semaphore\w*|transaction\w*|queue\w*|retr(?:y|ies)\w*|cach\w+|thread\w*|"
                       r"serializ\w+|блокиров\w*|мьютекс\w*|транзакци\w*|очеред\w*|кэш\w*)", re.IGNORECASE)
PROMPTS = {
    "title": "Name the promise in a few words; it becomes the decision's heading if a reviewer accepts it.",
    "situation": "When can the disputed outcomes occur?",
    "outcome": "Which result may each participant observe? A mechanism can permit several answers.",
    "source_quote": ("Quote the accepted fact supporting this outcome, on one line: where the source wraps, "
                     "join the lines with a space. If it leaves the choice open, select question."),
    "guarantee": "What promise survives every permitted implementation?",
    "observation": "What would demonstrate that promise? Describe the observation before choosing a test mechanism.",
    "consequence": "Who owns this obligation and what follows from it?",
    "owner_question": "What choice must the owner make? State the competing outcomes.",
}


def required(form, key):
    text = form.get(key)
    if not isinstance(text, str) or not text.strip() or len(text.splitlines()) != 1:
        raise ValueError(f"{key}: {PROMPTS[key]}")
    return text.strip()


def check_hint(situation):
    return (f"In the situation you described — “{situation}” — which result must each participant see? "
            "Describe what can be checked, not how it is achieved.")


def anchor_item(case, anchor):
    index = design_index.build_index(case)
    items = {item["key"]: item for item in index["items"]}
    item = items.get(anchor.upper())
    if not item or item["kind"] != "decision" or item["state"] != 2 or not item["explicit_id"]:
        raise ValueError("Choose an indexed State 2 decision from design_index.py --list --state 2 --kind decision")
    loc = item["source"]
    lines = (case / loc["path"]).read_text(encoding="utf-8").splitlines()
    excerpt = lines[loc["start_line"] - 1:loc["end_line"]]
    level = len(excerpt[0]) - len(excerpt[0].lstrip("#"))
    if level >= 6:
        raise ValueError("Choose a decision whose heading allows child sections")
    return item, items, "\n".join(excerpt), level


def next_id(keys, prefix, width):
    numbers = [int(key[len(prefix):]) for key in keys if re.fullmatch(re.escape(prefix) + r"\d+", key)]
    return f"{prefix}{max(numbers, default=0) + 1:0{width}d}"


def records(case):
    folder = case / PROPOSALS
    return {path.stem: json.loads(path.read_text(encoding="utf-8")) for path in sorted(folder.glob("P-*.json"))}


def open_form(case, anchor):
    item, items, text, level = anchor_item(case, anchor)
    loc = item["source"]
    read = forms.read_set(case, [case / loc["path"]])
    reopen = forms.command(TOOL, "template", case, item["key"])
    return {
        "anchor": item["key"], "read_set": read, "revision": forms.revision(read),
        "source_location": f"{loc['path']}:{loc['start_line']}", "source_text": text,
        "prompts": PROMPTS,
        "disposition": None, **{key: None for key in ANSWERS}, "owner_question": None,
        "choices": ["proposal", "question"],
        "proposal_id": next_id(records(case), "P-", 3), "question_id": next_id(items, "OQ-", 3),
        "return_to": forms.return_address(case, item["key"], reopen),
    }, level, text


def quoted(quote, source_text, anchor):
    # The source is hard-wrapped; a quote is one line, so compare with whitespace collapsed.
    if " ".join(quote.split()) not in " ".join(source_text.split()):
        raise ValueError(f"source_quote: select an exact passage of {anchor}, or save a question for the owner")


def proposal_record(form, current, source_text):
    answers = {key: required(form, key) for key in ANSWERS}
    quoted(answers["source_quote"], source_text, current["anchor"])
    cues = sorted({word.lower() for key in ("outcome", "guarantee", "observation")
                   for word in MECHANISM.findall(answers[key])})
    return {"schema_version": SCHEMA, "id": current["proposal_id"], "status": "pending",
            "anchor": current["anchor"], "source_location": current["source_location"], **answers,
            "mechanism_cues": cues, "review": None}


def decision_body(record, key, level, reviewer=None):
    title, section = "#" * level, "#" * (level + 1)
    invariant = f"INV-{key}-1"
    accepted = f"Accepted from proposal {record['id']}; reviewer: {reviewer}.\n\n" if reviewer else ""
    return (f"{title} Accepted decision {key} — {record['title']}\n\n"
            f"Source: {record['anchor']} — {record['source_quote']}\n\n{accepted}"
            f"{section} Normative rules\n\n1. {record['situation']} {record['outcome']}\n\n"
            f"{section} Formal invariants\n\n- {invariant}: {record['guarantee']}\n\n"
            f"{section} Required tests\n\n1. {invariant}: {record['observation']}\n\n"
            f"{section} Consequence\n\n- {record['consequence']}\n")


def cue_lines(record):
    lines = []
    if record["mechanism_cues"]:
        lines.append(f"Cue: the answer names a mechanism ({', '.join(record['mechanism_cues'])}). A mechanism can "
                     "permit several results; the promise is the result.")
    lines.append("Check: " + check_hint(record["situation"]))
    return lines


def save_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def author(args):
    case = args.case
    form = json.loads(args.form.read_text(encoding="utf-8"))
    current, level, source_text = open_form(case, form["anchor"])
    refresh = current["return_to"]["reopen"]
    disposition = form.get("disposition")
    if disposition == "decision":
        raise ValueError("disposition: an author saves a proposal for review, not a decision; choose proposal")
    if disposition not in current["choices"]:
        raise ValueError("disposition: choose proposal for an outcome the source supports, or question to ask the owner")
    if disposition == "proposal":
        record = proposal_record({**form}, {**current, "proposal_id": form.get("proposal_id")}, source_text)
        saved = records(case)
        same = next((key for key, old in saved.items()
                     if {**old, "id": None, "status": None, "review": None}
                     == {**record, "id": None, "status": None, "review": None}), None)
        if same:
            print(f"{same} already saved ({saved[same]['status']}).")
            return
        forms.require_current(form.get("read_set"), current["read_set"], refresh)
        if record["id"] != current["proposal_id"]:
            raise forms.StaleForm(f"stale form: {record['id']} was taken by another proposal after this form was "
                                  f"generated. Nothing was written. Generate a fresh form and preview again: {refresh}")
        target = (PROPOSALS / f"{record['id']}.json").as_posix()
        print(forms.will_write(case, {target: f"new draft {record['id']} for review"}))
        print("The specification files are not changed: a draft is not a requirement until a reviewer accepts it.")
        print(f"Draft, as it would read if accepted (its A number is assigned then):\n")
        print(decision_body(record, "A__", level))
        print("\n".join(cue_lines(record)))
        if args.command == "apply":
            save_json(case / target, record)
            print(f"Saved {record['id']} in {target}.")
            print("Reviewer reads it with: " + forms.command(TOOL, "review", case, record["id"]))
            print(forms.returning(current["return_to"]))
        return
    key = form.get("question_id")
    situation, question = required(form, "situation"), required(form, "owner_question")
    body = (f"{'#' * level} Open question {key}\n\nContext: {current['anchor']}. {situation}\n\n"
            f"Question for owner: {question}\n")
    old = design_index.get_item(case, key) if isinstance(key, str) else None
    if old:
        src = old["source"]
        lines = (case / src["path"]).read_text(encoding="utf-8").splitlines()
        if "\n".join(lines[src["start_line"] - 1:src["end_line"]]).rstrip() == body.rstrip():
            print(f"{key} already recorded.")
            return
    forms.require_current(form.get("read_set"), current["read_set"], refresh)
    if key != current["question_id"]:
        raise forms.StaleForm(f"stale form: {key} was taken by another question after this form was generated. "
                              f"Nothing was written. Generate a fresh form and preview again: {refresh}")
    plan = design_editor.plan_sibling(case, current["anchor"], key, ("\n\n" + body + "\n").encode())
    print(forms.will_write(case, {plan.relative_path: f"open question {key} after {current['anchor']}"}))
    print(design_editor.render_unified_diff(plan), end="")
    if args.command == "apply":
        design_editor.apply_plan(plan)
        print(f"Recorded {key} in {plan.relative_path}.")
        print(forms.returning(current["return_to"]))


def load(case, proposal):
    record = records(case).get(proposal.upper())
    if not record:
        raise ValueError(f"No proposal {proposal} in {PROPOSALS.as_posix()}; list them with "
                         + forms.command(TOOL, "review", case))
    return record


def acceptance(case, record, reviewer=None):
    """What accepting would write, and a token naming exactly what the reviewer saw."""
    item, items, text, level = anchor_item(case, record["anchor"])
    quoted(record["source_quote"], text, record["anchor"])
    key = next_id(items, "A", 2)
    plan = design_editor.plan_sibling(case, record["anchor"], key,
                                      ("\n\n" + decision_body(record, key, level, reviewer) + "\n").encode())
    path = case / PROPOSALS / f"{record['id']}.json"
    token = "-".join([hashlib.sha256(path.read_bytes()).hexdigest()[:12],
                      hashlib.sha256(plan.before).hexdigest()[:12], key])
    return key, plan, token


def review(args):
    case = args.case
    if not args.proposal:
        saved = records(case)
        if not saved:
            print(f"No proposals in {PROPOSALS.as_posix()}.")
        for key, record in sorted(saved.items(), key=lambda pair: (pair[1]["status"] != "pending", pair[0])):
            note = {"pending": "draft, not in the specification",
                    "accepted": f"accepted as {(record['review'] or {}).get('accepted_as')}",
                    "rejected": f"rejected: {(record['review'] or {}).get('reason')}"}[record["status"]]
            cue = f"; names a mechanism ({', '.join(record['mechanism_cues'])})" if record["mechanism_cues"] else ""
            print(f"{key} [{record['status']}] at {record['anchor']} — {record['title']} ({note}{cue})")
        if any(record["status"] == "pending" for record in saved.values()):
            print("Open one: " + forms.command(TOOL, "review", case, "P-ID"))
        return
    record = load(case, args.proposal)
    print(f"Proposal {record['id']} [{record['status']}] at {record['anchor']} ({record['source_location']}).")
    if record["status"] != "pending":
        print(json.dumps(record["review"], ensure_ascii=False))
        return
    print("Saved by the author as a draft. It is not part of the specification.")
    print("\n".join(cue_lines(record)))
    try:
        key, plan, token = acceptance(case, record, "REVIEWER")
    except ValueError as exc:
        print(f"It cannot be accepted as it stands: {exc}")
        print("Reject it with a reason: " + forms.command(TOOL, "reject", case, record["id"], "--reviewer", "NAME",
                                                          "--reason", "TEXT"))
        return
    print(forms.will_write(case, {plan.relative_path: f"accepted decision {key} after {record['anchor']}",
                                  (PROPOSALS / (record['id'] + '.json')).as_posix(): "status accepted"}))
    print(design_editor.render_unified_diff(plan), end="")
    print("Accept exactly this: " + forms.command(TOOL, "accept", case, record["id"], "--reviewer", "NAME",
                                                  "--reviewed", token))
    print("Reject: " + forms.command(TOOL, "reject", case, record["id"], "--reviewer", "NAME", "--reason", "TEXT"))


def decide(args):
    case = args.case
    record = load(case, args.proposal)
    reviewer = args.reviewer.strip()
    if not reviewer or len(reviewer.splitlines()) != 1:
        raise ValueError("--reviewer: name who takes this decision")
    again = forms.command(TOOL, "review", case, record["id"])
    if record["status"] != "pending":
        print(f"{record['id']} is already {record['status']}: {json.dumps(record['review'], ensure_ascii=False)}")
        return
    path = case / PROPOSALS / f"{record['id']}.json"
    back = forms.return_address(case, record["anchor"], forms.command(TOOL, "template", case, record["anchor"]))
    if args.command == "reject":
        if not args.reason.strip():
            raise ValueError("--reason: say what the author should change or ask")
        save_json(path, {**record, "status": "rejected", "review": {"reviewer": reviewer, "reason": args.reason.strip()}})
        print(f"Rejected {record['id']}; the specification is unchanged. The author sees the reason in the list.")
        print(forms.returning(back))
        return
    key, plan, token = acceptance(case, record, reviewer)
    if args.reviewed != token:
        seen, now = args.reviewed.split("-"), token.split("-")
        parts = [name for name, old, new in zip(("the proposal", "the source file", "the next decision number"),
                                                seen + [""] * 3, now) if old != new]
        raise forms.StaleForm(f"stale review: {' and '.join(parts) or 'the review token'} changed after your review, so "
                              f"what you read is not what would be written. Nothing was written. Review again: {again}")
    design_editor.apply_plan(plan)
    save_json(path, {**record, "status": "accepted", "review": {"reviewer": reviewer, "accepted_as": key}})
    print(f"Accepted {record['id']} as {key} in {plan.relative_path}; it is now part of the specification.")
    if (case / design_trace.DEFAULT_TRACE_FILE).exists():
        print(f"{key} has no owner in {design_trace.DEFAULT_TRACE_FILE} yet: design_trace.py --check reports it "
              "as unclaimed until State 3 assigns a primary owner or a disposition.")
    print(forms.returning(back))


def run(args):
    if args.command == "template":
        print(json.dumps(open_form(args.case, args.anchor)[0], ensure_ascii=False, indent=2))
    elif args.command in ("preview", "apply"):
        author(args)
    elif args.command == "review":
        review(args)
    else:
        decide(args)


def main(argv=None):
    cli = argparse.ArgumentParser(description=__doc__)
    commands = cli.add_subparsers(dest="command", required=True)
    for command in ("template", "preview", "apply"):
        p = commands.add_parser(command, help="author: " + command)
        p.add_argument("case", type=Path)
        if command == "template":
            p.add_argument("anchor", help="accepted State 2 decision providing context")
        else:
            p.add_argument("form", type=Path)
    p = commands.add_parser("review", help="reviewer: list proposals, or read one with what accepting would write")
    p.add_argument("case", type=Path)
    p.add_argument("proposal", nargs="?")
    for command in ("accept", "reject"):
        p = commands.add_parser(command, help=f"reviewer: {command} a proposal")
        p.add_argument("case", type=Path)
        p.add_argument("proposal")
        p.add_argument("--reviewer", required=True)
        if command == "accept":
            p.add_argument("--reviewed", required=True, help="the token printed by review")
        else:
            p.add_argument("--reason", required=True)
    try:
        run(cli.parse_args(argv))
    except (ValueError, KeyError, OSError, TypeError, design_editor.DesignEditorError) as exc:
        print(f"state2-form: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
