"""A question round: several independent reviews, grouped, judged, kept with the case.

A topic raised by two or more reviews is judged (judge.py). A round is clear
when no judged topic blocks: no contradiction, no gap with an observable
consequence, and no judgement whose evidence failed its check. A state is
closed when its two latest rounds are clear on the same texts, and the texts
have not changed since. A topic raised by one review only is recorded and may
be closed or carried, but it does not keep the state open.

Rounds kept before the judge existed (no "judge" in the summary) keep their
own rule: closed when no topic was raised by two reviews.
"""
from __future__ import annotations

import difflib
import hashlib
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from . import documents, judge, prompts
from .provider import Provider

SCHEMA = "spec_workbench_question_round.v2"
DEFAULT_RUNS = 3
REPEATED = 2


class QuestionRoundError(ValueError):
    pass


def _json_object(text: str) -> dict[str, Any]:
    try:
        return json.loads(text[text.index("{"): text.rindex("}") + 1])
    except ValueError as exc:
        raise QuestionRoundError(f"the model did not answer with a JSON object: {exc}") from exc


def rounds_dir(case: Path, state: int) -> Path:
    return case / "questions" / f"state{state}"


def _next_round(case: Path, state: int) -> Path:
    base = rounds_dir(case, state)
    taken = [int(p.name.split("-")[1]) for p in base.glob("round-*") if p.name.split("-")[1].isdigit()]
    return base / f"round-{max(taken, default=0) + 1:02d}"


def _review(provider: Provider, instruction: str, text: str) -> dict[str, Any]:
    answer, usage = provider.complete(instruction, text)
    points = _json_object(answer).get("open_points")
    if not isinstance(points, list):
        raise QuestionRoundError("a review answered without open_points")
    return {"open_points": points, "usage": usage, "raw": answer}


def _group(provider: Provider, reviews: list[dict[str, Any]], keep_points: bool = False) -> list[dict[str, Any]]:
    points = {
        f"r{run}.{index:02d}": point
        for run, review in enumerate(reviews, 1)
        for index, point in enumerate(review["open_points"])
    }
    if not points:
        return []
    listing = "\n".join(
        f"{key}: [{point.get('subject', '')}] {point.get('question', '')}" for key, point in points.items()
    )
    groups = _json_object(provider.complete(prompts.GROUP, listing)[0]).get("groups") or []
    seen: set[str] = set()
    topics = []
    for group in groups:
        members = [m for m in group.get("members", []) if m in points and m not in seen]
        if members:
            seen.update(members)
            topics.append({"topic": str(group.get("topic", "")), "members": members})
    for key in points:  # a point the grouping dropped is a topic of its own
        if key not in seen:
            topics.append({"topic": str(points[key].get("question", "")), "members": [key]})
    for topic in topics:
        topic["runs"] = sorted({int(m[1:].split(".")[0]) for m in topic["members"]})
        topic["questions"] = [points[m].get("question", "") for m in topic["members"]]
        if keep_points:
            topic["points"] = [f"{points[m].get('text', '')} -> {points[m].get('question', '')}" for m in topic["members"]]
    return sorted(topics, key=lambda t: (-len(t["runs"]), t["topic"]))


def _texts_at(case: Path, names: list[str], ref: str) -> dict[str, str]:
    """The design texts as they were at git `ref` (absent files are empty)."""
    def git(*args: str) -> str:
        done = subprocess.run(["git", "-C", str(case), *args], capture_output=True, text=True)
        if done.returncode != 0:
            raise QuestionRoundError(f"git {' '.join(args)}: {done.stderr.strip()}")
        return done.stdout
    git("rev-parse", "--verify", f"{ref}^{{commit}}")
    prefix = git("rev-parse", "--show-prefix").strip()
    old = {}
    for name in names:
        done = subprocess.run(["git", "-C", str(case), "show", f"{ref}:{prefix}{name}"], capture_output=True, text=True)
        old[name] = done.stdout if done.returncode == 0 else ""
    return old


def _judge(provider: Provider, state: int, text: str, texts: list[tuple[int, str, str]],
           repeated: list[dict[str, Any]], old: dict[str, str] | None) -> dict[str, Any]:
    change = None
    if old is not None:
        change = "".join(
            "".join(difflib.unified_diff(old[name].splitlines(True), body.splitlines(True), name, name, n=2))
            for _, name, body in texts
        )
    items = []
    for index, topic in enumerate(repeated, 1):
        topic["id"] = f"T{index}"
        items.append({"id": topic["id"], "topic": topic["topic"], "points": topic.get("points", topic["questions"])})
    answer = provider.complete(prompts.judge_instruction(state, old is not None),
                               prompts.judge_input(text, items, change))[0]
    judgements = {j.get("id"): j for j in _json_object(answer).get("judgements") or [] if isinstance(j, dict)}
    body = "\n\n".join(b for _, _, b in texts)
    old_body = None if old is None else "\n\n".join(old.values())
    for topic in repeated:
        topic["judgement"] = judge.check(judgements.get(topic["id"]), state, body, old_body)
    return {"provider": provider.name, "raw": answer}


def _clear(summary: dict[str, Any]) -> bool:
    if "judge" not in summary:
        return not summary.get("repeated_topics")
    return summary.get("blocking_topics") == 0


def ask_round(case: Path, state: int, provider: Provider, runs: int = DEFAULT_RUNS,
              since: str | None = None) -> dict[str, Any]:
    """Run one question round for State `state` of `case` and keep it in the case.

    `since` names the git ref at which a reopened state was closed; the judge
    then sees the change since, and may judge a topic about an untouched passage
    as preexisting.
    """
    if runs < REPEATED:
        raise QuestionRoundError(f"a round needs at least {REPEATED} reviews to tell a repeated topic")
    docs = documents.design_documents(case, state)
    if not any(found_state == state for found_state, _ in docs):
        raise QuestionRoundError(f"{case.name} has no State {state} document")
    texts = [(s, p.name, p.read_text(encoding="utf-8")) for s, p in docs]
    instruction = prompts.ask_instruction(state, documents.question_scope(state))
    text = prompts.ask_input(texts)
    with ThreadPoolExecutor(max_workers=runs) as pool:
        reviews = list(pool.map(lambda _: _review(provider, instruction, text), range(runs)))
    topics = _group(provider, reviews, keep_points=True)
    repeated = [t for t in topics if len(t["runs"]) >= REPEATED]
    old = _texts_at(case, [name for _, name, _ in texts], since) if since else None
    judged = _judge(provider, state, text, texts, repeated, old) if repeated else {"provider": provider.name}
    for topic in topics:
        topic.pop("points", None)
    directory = _next_round(case, state)
    directory.mkdir(parents=True)
    for run, review in enumerate(reviews, 1):
        (directory / f"review-{run}.json").write_text(json.dumps(review, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    digests = {name: hashlib.sha256(body.encode("utf-8")).hexdigest() for _, name, body in texts}
    blocking = [t for t in repeated if t["judgement"]["blocking"]]
    previous = sorted(rounds_dir(case, state).glob("round-*/summary.json"))
    previous = [p for p in previous if p.parent != directory]
    before = json.loads(previous[-1].read_text(encoding="utf-8")) if previous else None
    clear = not blocking
    summary = {
        "schema_version": SCHEMA,
        "state": state,
        "round": directory.name,
        "provider": provider.name,
        "documents": digests,
        "reviews": runs,
        "points": [len(r["open_points"]) for r in reviews],
        "since": since,
        "judge": judged,
        "repeated_topics": len(repeated),
        "blocking_topics": len(blocking),
        "clear": clear,
        "closed": bool(clear and before and _clear(before) and before.get("documents") == digests),
        "topics": topics,
    }
    (directory / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return summary


def status(case: Path, state: int) -> dict[str, Any]:
    """The latest round of a state, and whether it closed the state."""
    rounds = sorted(rounds_dir(case, state).glob("round-*/summary.json"))
    if not rounds:
        return {"state": state, "round": None, "closed": False, "reason": "no question round yet"}
    summary = json.loads(rounds[-1].read_text(encoding="utf-8"))
    current = {
        path.name: hashlib.sha256(path.read_text(encoding="utf-8").encode("utf-8")).hexdigest()
        for _, path in documents.design_documents(case, state)
    }
    stale = current != summary["documents"]
    return {
        "state": state,
        "round": summary["round"],
        "closed": summary["closed"] and not stale,
        "stale": stale,
        "provider": summary.get("provider"),
        "reason": ("the design texts changed after the latest round" if stale
                   else ("two clear rounds on these texts" if "judge" in summary else "no topic raised by two reviews")
                   if summary["closed"]
                   else _open_reason(summary)),
        "repeated": [t for t in summary["topics"] if len(t["runs"]) >= REPEATED],
    }


def _open_reason(summary: dict[str, Any]) -> str:
    if "judge" not in summary:
        return f"{summary['repeated_topics']} topic(s) raised by two or more reviews"
    if summary["blocking_topics"]:
        return f"{summary['blocking_topics']} blocking topic(s): contradiction, consequential gap or unverified judgement"
    return "one clear round; the state closes after a second clear round on the same texts"
