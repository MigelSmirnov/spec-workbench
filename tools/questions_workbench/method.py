"""The method a round was asked under, and what a change of method leaves behind.

A round's blocking topics are the questions the method of that day found. When
the method changes — its instructions, its scope or what its judge lets block —
the next round asks under other rules, and a blocking topic the new rules no
longer ask simply stops coming back. On Cabinet Kernel State 7 (2026-10-10)
round-01 raised, in three reviews of three, what `installation` does on a
platform without no-follow opening; the same hour State 7 was changed to ask
only for contradictions, round-01 was marked "to be asked again", and nobody
looked at its 445 gaps. The units closed, the specification was accepted, and
Route B met the very guess round-01 had named (`hasattr(os, "O_NOFOLLOW")`).

So every round keeps the digest of its method, and when two consecutive rounds
of a state were asked under different methods, every blocking topic of the
earlier one needs a disposition before the state can close: what became of it.
Rounds kept before the digest existed have none and are not compared.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from . import documents, prompts

# Bump when a change of the code — judge.check, what counts as blocking, which
# topics are judged — changes what a round lets block without changing the
# instructions the digest already covers.
REVISION = 1
DISPOSITIONS = "dispositions.json"
SCHEMA = "spec_workbench_question_dispositions.v1"
# What became of a blocking topic of a round asked under a superseded method.
KINDS = {
    "fixed": "the texts were changed to answer it",
    "owner": "the owner answered it; the answer stands in the texts",
    "convention": "a convention of the case answers it with its whole kind",
    "carried": "it was carried to the texts or state that answers it",
    "asked_again": "the new method still asks it, and its rounds judge it",
    "not_needed": "nobody uses what it asks about",
}
NEEDS_WHERE = {"fixed", "owner", "convention", "carried"}


class DispositionError(ValueError):
    pass


def digest(state: int, sequence_path: Path = documents.SEQUENCE) -> str:
    """The digest of the method State `state` is asked under: its question
    scope, the instructions of its reviews and its judge, and REVISION."""
    scope = documents.question_scope(state, sequence_path)
    ask = (prompts.module_ask_instruction(state, scope) if state == documents.MODULE_STATE
           else prompts.ask_instruction(state, scope))
    judge = prompts.judge_instruction(state, False, None, False, scope)
    payload = json.dumps([REVISION, state, ask, judge], ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def topic_key(summary: dict[str, Any], topic: dict[str, Any]) -> str:
    return f"{summary['round']}:{topic['id']}"


def superseded(summaries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """The blocking topics of every round followed by a round asked under
    another method, as {key, round, topic, units}."""
    found = []
    asked = [s for s in summaries if s.get("method")]
    for earlier, later in zip(asked, asked[1:]):
        if earlier["method"] == later["method"]:
            continue
        for topic in earlier.get("topics") or []:
            if (topic.get("judgement") or {}).get("blocking") and topic.get("id"):
                found.append({"key": topic_key(earlier, topic), "round": earlier["round"],
                              "topic": topic["topic"], "units": topic.get("units") or []})
    return found


def dispositions_path(rounds_dir: Path) -> Path:
    return rounds_dir / DISPOSITIONS


def load(rounds_dir: Path) -> dict[str, dict[str, str]]:
    path = dispositions_path(rounds_dir)
    if not path.is_file():
        return {}
    return dict(json.loads(path.read_text(encoding="utf-8")).get("topics") or {})


def undisposed(summaries: list[dict[str, Any]], rounds_dir: Path) -> list[dict[str, Any]]:
    """Blocking topics left behind by a change of method that have no disposition."""
    done = load(rounds_dir)
    return [t for t in superseded(summaries) if t["key"] not in done]


def dispose(rounds_dir: Path, summaries: list[dict[str, Any]], keys: list[str], kind: str,
            why: str, where: str | None = None) -> dict[str, dict[str, str]]:
    """Record what became of blocking topics a change of method left behind."""
    if kind not in KINDS:
        raise DispositionError(f"unknown disposition {kind!r}; one of {', '.join(sorted(KINDS))}")
    if not why.strip():
        raise DispositionError("a disposition needs the reason (--why)")
    if kind in NEEDS_WHERE and not (where or "").strip():
        raise DispositionError(f"a {kind!r} disposition names where the answer stands (--where)")
    left = {t["key"] for t in superseded(summaries)}
    unknown = [k for k in keys if k not in left]
    if unknown:
        raise DispositionError(f"not a blocking topic of a round asked under a superseded method: {', '.join(unknown)}")
    done = load(rounds_dir)
    for key in keys:
        done[key] = {"as": kind, "why": why.strip(), **({"where": where.strip()} if where else {})}
    path = dispositions_path(rounds_dir)
    path.write_text(json.dumps({"schema_version": SCHEMA, "topics": dict(sorted(done.items()))},
                               ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return done
