"""A question round: several independent reviews, grouped, kept with the case.

A state is closed when the latest round has no topic raised by two or more of
its reviews. A topic raised by one review only is recorded and may be closed or
carried, but it does not keep the state open.
"""
from __future__ import annotations

import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from . import documents, prompts
from .provider import Provider

SCHEMA = "spec_workbench_question_round.v1"
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


def _group(provider: Provider, reviews: list[dict[str, Any]]) -> list[dict[str, Any]]:
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
    return sorted(topics, key=lambda t: (-len(t["runs"]), t["topic"]))


def ask_round(case: Path, state: int, provider: Provider, runs: int = DEFAULT_RUNS) -> dict[str, Any]:
    """Run one question round for State `state` of `case` and keep it in the case."""
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
    topics = _group(provider, reviews)
    repeated = [t for t in topics if len(t["runs"]) >= REPEATED]
    directory = _next_round(case, state)
    directory.mkdir(parents=True)
    for run, review in enumerate(reviews, 1):
        (directory / f"review-{run}.json").write_text(json.dumps(review, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    summary = {
        "schema_version": SCHEMA,
        "state": state,
        "round": directory.name,
        "provider": provider.name,
        "documents": {name: hashlib.sha256(body.encode("utf-8")).hexdigest() for _, name, body in texts},
        "reviews": runs,
        "points": [len(r["open_points"]) for r in reviews],
        "closed": not repeated,
        "repeated_topics": len(repeated),
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
        "reason": ("the design texts changed after the latest round" if stale
                   else "no topic raised by two reviews" if summary["closed"]
                   else f"{summary['repeated_topics']} topic(s) raised by two or more reviews"),
        "repeated": [t for t in summary["topics"] if len(t["runs"]) >= REPEATED],
    }
