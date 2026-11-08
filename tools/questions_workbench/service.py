"""A question round: several independent reviews, grouped, judged, kept with the case.

A topic raised by two or more reviews is judged (judge.py). A topic raised
by one review only is recorded, but it asks nothing of the author.

Every state closes unit by unit (units.py), by ONE round per change (owner
decision 2026-11-08, #147): a unit is closed when the latest round on its
current text raised no open contradiction against it and every other judged
topic of that round that concerns it has an author disposition — ``fixed``,
``carried`` or ``accepted``, kept in ``dispositions.json`` beside the round
(``dispose``). The state is closed when every unit is. Units closed by two
clear rounds before this rule stay closed. A state closed as one text before
units existed carries that closure to each of its units on the text it closed
on, found in the case's git history; a later edit then reopens only the units
it touched.

State 7 is asked module by module: each review gets the prompt the Factory
builds for one generated module (factory_slice_workbench.module_prompts), from
the case's assembled specification.

Rounds kept before the judge existed (no "judge" in the summary) keep their
own rule: clear when no topic was raised by two reviews.

In the document states (0-5) a blocking topic needs a witness (judge.py). A
topic raised by one review is judged too when that review gave it a witness;
the judge's hypotheses — topics it could not give a witness — are put to the
next round's reviewers. A unit that was closed and names a decision changed
since its own closure is reviewed again for that change. Each passage of an
earlier state a judgement quotes is kept with the commit and date that
introduced it.
"""
from __future__ import annotations

import difflib
import hashlib
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from . import documents, judge, judge_context, layer_prompt, prompts, units
from .provenance import QuoteProvenance
from .provider import LATER_DIR, Provider

PROMPTS_DIR = "prompts"
MODULE_WORKERS = 6

SCHEMA = "spec_workbench_question_round.v2"
DEFAULT_RUNS = 3
REPEATED = 2
PRECEDENT_ROUNDS = 3


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


class ReviewFailed(QuestionRoundError):
    """A review whose answer was not a JSON object with open_points, twice."""

    def __init__(self, reason: str, answers: list[str]):
        super().__init__(reason)
        self.answers = answers


REVIEW_ATTEMPTS = 2


def _review(provider: Provider, instruction: str, text: str) -> dict[str, Any]:
    """One review. An answer that is not a JSON object with open_points is
    asked again once: one malformed answer must not lose a round whose other
    reviews answered (#147). A second failure raises ReviewFailed, which keeps
    both answers; a provider error is not retried here."""
    answers = []
    for _ in range(REVIEW_ATTEMPTS):
        answer, usage = provider.complete(instruction, text)
        answers.append(answer)
        try:
            points = _json_object(answer).get("open_points")
        except QuestionRoundError as exc:
            reason = str(exc)
            continue
        if isinstance(points, list):
            return {"open_points": points, "usage": usage, "raw": answer,
                    **({"retried": answers[:-1]} if len(answers) > 1 else {})}
        reason = "a review answered without open_points"
    raise ReviewFailed(f"{reason} ({len(answers)} attempts)", answers)


def _failed_review(exc: ReviewFailed) -> dict[str, Any]:
    """A review recorded as failed: its answers kept, no point taken from it."""
    return {"failed": str(exc), "answers": exc.answers, "open_points": []}


def _valid_reviews(reviews: list[dict[str, Any]], what: str) -> None:
    """A round goes on without a failed review only while REPEATED reviews answered."""
    valid = sum(1 for r in reviews if "failed" not in r)
    if valid < REPEATED:
        reasons = "; ".join(r["failed"] for r in reviews if "failed" in r)
        raise QuestionRoundError(f"{what}: only {valid} of {len(reviews)} reviews answered, "
                                 f"and a round needs {REPEATED} ({reasons})")


def _review_or_failed(provider: Provider, instruction: str, text: str) -> dict[str, Any]:
    try:
        return _review(provider, instruction, text)
    except ReviewFailed as exc:
        return _failed_review(exc)


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
        named = sorted({str(points[m]["unit"]) for m in topic["members"] if points[m].get("unit")})
        if named:
            topic["units"] = named
        witnessed = [m for m in topic["members"] if _has_witness(points[m])]
        if witnessed:
            topic["witnessed_by"] = witnessed
        if keep_points:
            topic["points"] = [f"{points[m].get('text', '')} -> {points[m].get('question', '')}"
                               + (f" | breaks SPEC_STANDARD §{points[m].get('section', '')}: {points[m]['rule']}"
                                  if points[m].get("rule") else "")
                               + (f" | reviewer's witness: {json.dumps(points[m]['witness'], ensure_ascii=False)}"
                                  if _has_witness(points[m]) else "")
                               for m in topic["members"]]
            # the passages the points quote, which the judge is given inline (judge_context.py)
            topic["quoted"] = [q for m in topic["members"] for q in judge_context.topic_quotes(points[m])]
    return sorted(topics, key=lambda t: (-len(t["runs"]), t["topic"]))


def _has_witness(point: Any) -> bool:
    """A reviewer's witness: an initial state, events and two different outcomes."""
    witness = point.get("witness") if isinstance(point, dict) else None
    if not isinstance(witness, dict):
        return False
    outcomes = [o for o in witness.get("outcomes") or [] if isinstance(o, str) and o.strip()]
    return (bool(str(witness.get("initial") or "").strip()) and bool(witness.get("events"))
            and len(set(outcomes)) >= 2)


def _judged(topics: list[dict[str, Any]], witness: bool) -> list[dict[str, Any]]:
    """The topics a round judges: raised by two or more reviews, or — where a
    blocking topic needs a witness — by one review that gave a witness."""
    return [t for t in topics if len(t["runs"]) >= REPEATED or (witness and t.get("witnessed_by"))]


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


def _round_number(path: Path) -> int:
    part = path.parent.name.split("-")[1]
    return int(part) if part.isdigit() else 0


def _precedents(case: Path, state: int) -> list[dict[str, Any]]:
    """The verified non-blocking judgements of the state's latest judged rounds,
    newest first, one per topic. A judgement that itself followed a precedent
    passes that precedent's kind and quotes on."""
    rounds = sorted(rounds_dir(case, state).glob("round-*/summary.json"), key=_round_number)
    found: list[dict[str, Any]] = []
    seen: set[str] = set()
    judged = [json.loads(p.read_text(encoding="utf-8")) for p in rounds]
    evidence_of = {s["round"]: s.get("unit_evidence") or {} for s in judged if "round" in s}
    for summary in [s for s in judged if "judge" in s][-PRECEDENT_ROUNDS:][::-1]:
        for topic in summary.get("topics", []):
            judgement = topic.get("judgement") or {}
            if (not judgement.get("verified") or judgement.get("blocking") or topic["topic"] in seen
                    or judgement.get("kind") == judge.HYPOTHESIS):
                continue  # a hypothesis is an open question, not an answer to follow
            source = judgement.get("precedent") or judgement
            seen.add(topic["topic"])
            origin = source.get("round", summary["round"])
            found.append({"id": f"P{len(found) + 1}", "round": origin,
                          "topic": topic["topic"], "kind": source["kind"],
                          "quotes": list(source.get("quotes") or []), "why": source.get("why", ""),
                          "units": list(topic.get("units") or []),
                          # the evidence the original judgement stood on, per unit
                          "unit_evidence": dict(evidence_of.get(origin, summary.get("unit_evidence") or {})),
                          **({"deferred_to": source["deferred_to"]} if source.get("deferred_to") else {})})
    return found


def _evidence_holds(precedent: dict[str, Any], evidence: dict[str, str], scope: list[str]) -> bool:
    """A precedent about a unit whose bindings have evidence holds only on the
    evidence it was judged on. A judgement with no recorded basis for such a
    unit, or on another basis, is not offered: on changed evidence the same
    question is judged afresh. A topic naming no unit concerns every unit under
    review."""
    units = precedent.get("units") or scope
    recorded = precedent.get("unit_evidence") or {}
    return all(recorded.get(unit) == evidence[unit] for unit in units if unit in evidence)


def _judge(provider: Provider, state: int, text: str, texts: list[tuple[int, str, str]],
           repeated: list[dict[str, Any]], old: dict[str, str] | None,
           later: dict[str, str] | None = None,
           precedents: list[dict[str, Any]] | None = None,
           witness: bool = False, case: Path | None = None, layer: str | None = None,
           scope: list[str] | None = None, sections: list[dict[str, str]] | None = None) -> dict[str, Any]:
    """Judge the repeated topics. `later` maps the later states' documents to
    their texts; `precedents` are the state's prior non-blocking judgements,
    which the judge may follow for the same question on unchanged passages.

    What the judge reads depends on the provider (owner decision 2026-11-08, #147):

    - a provider that reads files (`reads_files`), in a document state with the
      round's `scope` given, gets inline only the topics, the units they
      concern with their diff, the passages they quote or name, the precedents
      and the layer block (judge_context.py); the full texts of States 0..N,
      the later documents and the texts a reopened state was closed with are
      files it searches;
    - any other provider, and State 7 (whose text is one module's prompt), gets
      the round text `text` inline as before, the change since `old` whole,
      and no later documents.

    Either way judge.check finds every quote in the full texts, which it gets
    here from `texts`, never from what the judge was shown. `sections` are the
    state's SPEC_STANDARD sections the reviewers were given: the judge gets
    them too, and a violation's rule is found in them."""
    standard = prompts.standard_text(sections) if sections else None
    for index, topic in enumerate(repeated, 1):
        topic["id"] = f"T{index}"
    items = [{"id": t["id"], "topic": t["topic"], "points": t.get("points", t["questions"])} for t in repeated]
    reads_files = bool(getattr(provider, "reads_files", False))
    searched = reads_files and scope is not None and state != documents.MODULE_STATE
    later = later if later and reads_files else None
    later_files = [f"{LATER_DIR}/{name}" for name in sorted(later)] if later else None
    # Offer only a precedent the judge can still follow. One whose quoted
    # passages changed invites `judged_before`, which `judge.check` then rejects
    # as blocking; such a topic is judged afresh (QUESTIONS.md).
    current = "\n\n".join(b for _, _, b in texts)
    later_text = "\n\n".join(later.values()) if later else None
    precedents = [p for p in precedents or [] if judge.precedent_holds(p, current, later_text)]
    try:
        question_scope = documents.question_scope(state)
    except documents.QuestionScopeError:
        question_scope = None
    files: dict[str, str] = {}
    if searched:
        selected = judge_context.select(texts, state, repeated, scope or [], old, later)
        files = selected.files
        state_files = [f"{judge_context.STATES_DIR}/{name}" for _, name, _ in texts]
        closed_files = ([f"{judge_context.CLOSED_DIR}/{name}" for _, name, _ in texts]
                        if old is not None else None)
        instruction = prompts.judge_instruction(state, old is not None, later_files, bool(precedents),
                                                question_scope, witness, state_files, closed_files,
                                                standard=standard is not None)
        judge_text = prompts.judge_input(judge_context.render(selected, state), items, None, precedents, layer,
                                         standard)
    else:
        change = None
        if old is not None:
            change = "".join(
                "".join(difflib.unified_diff(old[name].splitlines(True), body.splitlines(True), name, name, n=2))
                for _, name, body in texts
            )
        instruction = prompts.judge_instruction(state, old is not None, later_files, bool(precedents),
                                                question_scope, witness, standard=standard is not None)
        judge_text = prompts.judge_input(text, items, change, precedents, layer, standard)
        files = {f"{LATER_DIR}/{name}": body for name, body in later.items()} if later else {}
    if files:
        answer = provider.complete_with_files(instruction, judge_text, files)[0]
    else:
        answer = provider.complete(instruction, judge_text)[0]
    judgements = {j.get("id"): j for j in _json_object(answer).get("judgements") or [] if isinstance(j, dict)}
    body = "\n\n".join(b for _, _, b in texts)
    old_body = None if old is None else "\n\n".join(old.values())
    earlier = "\n\n".join(b for s, _, b in texts if s < state) if state > 0 else None
    for topic in repeated:
        topic["judgement"] = judge.check(judgements.get(topic["id"]), state, body, old_body,
                                         "\n\n".join(later.values()) if later else None,
                                         {p["id"]: p for p in precedents or []},
                                         "\n\n".join(b for s, _, b in texts if s == state),
                                         witness_required=witness, earlier_texts=earlier, standard=standard)
    if case is not None and state > 0:
        provenance = QuoteProvenance(case, [(s, n, b) for s, n, b in texts if s < state])
        for topic in repeated:
            found = provenance.of_judgement(topic["judgement"])
            if found:
                topic["judgement"]["provenance"] = found
    result = {"provider": provider.name, "raw": answer, "inline_characters": len(judge_text)}
    if searched:
        result["searched_files"] = sorted(files)
    if later:
        result["later_documents"] = {name: hashlib.sha256(body.encode("utf-8")).hexdigest()
                                     for name, body in later.items()}
    return result


DISPOSITIONS_FILE = "dispositions.json"
DISPOSITIONS_SCHEMA = "spec_workbench_topic_dispositions.v1"
DISPOSITION_KINDS = ("fixed", "carried", "accepted")
# Layers past the design states a topic may be carried to (besides a later state).
CARRY_LAYERS = ("generation", "factory_checks", "deploy")
ASSEMBLY_STATE = 8  # State 8 assembly: the last state a topic may be carried to by number


def _dispositions(directory: Path) -> list[dict[str, Any]]:
    path = directory / DISPOSITIONS_FILE
    if not path.is_file():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [d for d in payload.get("dispositions") or [] if isinstance(d, dict)]


def _summaries(case: Path, state: int) -> list[dict[str, Any]]:
    """The rounds of a state, oldest first, each with the author's dispositions
    of its topics (`dispositions`, read from beside its summary)."""
    paths = sorted(rounds_dir(case, state).glob("round-*/summary.json"), key=_round_number)
    found = []
    for path in paths:
        summary = json.loads(path.read_text(encoding="utf-8"))
        summary["dispositions"] = _dispositions(path.parent)
        found.append(summary)
    return found


def _git_out(case: Path, *args: str) -> str | None:
    done = subprocess.run(["git", "-C", str(case), *args], capture_output=True, text=True)
    return done.stdout if done.returncode == 0 else None


def _unit_text_at(case: Path, texts: list[tuple[int, str, str]], state: int, key: str,
                  digest: str, depth: int = 400, hints: list[str] | None = None) -> str | None:
    """The text a unit had when its digest was `digest`; None when nothing
    holds it. A State 7 unit is found among the prompts kept with the rounds;
    any other unit in the case's git history of the documents it is cut from,
    `hints` (commits known to hold the closed texts) first."""
    if state == documents.MODULE_STATE:
        for path in sorted(rounds_dir(case, state).glob(f"round-*/{PROMPTS_DIR}/{key}.txt"),
                           key=lambda p: -_round_number(p.parent)):
            text = path.read_text(encoding="utf-8")
            if units._digest(text) == digest:
                return text
        return None
    names = [name for _, name, _ in texts]
    listed = _git_out(case, "log", f"-{depth}", "--format=%H", "--", *names)
    if listed is None:
        return None
    commits = [*(hints or []), *[c for c in listed.split() if c not in (hints or [])]]
    for commit in commits:
        try:
            old = _texts_at(case, names, commit)
        except QuestionRoundError:
            continue
        found = units.units([(s, name, old[name]) for s, name, _ in texts], state)
        if found.get(key, {}).get("digest") == digest:
            return found[key]["text"]
    return None


def _changed_units(case: Path, texts: list[tuple[int, str, str]], state: int, scope: list[str],
                   current: dict[str, dict[str, str]], summaries: list[dict[str, Any]]) -> dict[str, tuple[str, list[str]]]:
    """For each unit under review that was closed on another text: its diff since
    then and the regions of its current text the change touches."""
    changed = {}
    hints = [s["ref"] for s in summaries if s.get("ref")]
    for key in scope:
        digest = units.closed_digest(summaries, key)
        if digest is None or digest == current[key]["digest"]:
            continue
        old = _unit_text_at(case, texts, state, key, digest, hints=hints)
        if old is not None:
            changed[key] = units.change_regions(old, current[key]["text"])
    return changed


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _added_at(case: Path, path: Path) -> str | None:
    """The commit that added a kept file, or None when it is not committed."""
    try:
        relative = path.resolve().relative_to(case.resolve())
    except ValueError:
        return None
    found = _git_out(case, "log", "-1", "--format=%H", "--diff-filter=A", "--", str(relative))
    return found.strip() or None if found else None


def _texts_with_digests(case: Path, digests: dict[str, str], hint: str | None,
                        depth: int = 1000) -> tuple[list[tuple[int, str, str]], str | None] | None:
    """The documents whose sha256 digests are `digests`, as (state, name, text),
    and the commit that holds them (None: the working tree does); None when no
    commit of the case's history does."""
    names = sorted(digests)

    def read(texts: dict[str, str]) -> list[tuple[int, str, str]] | None:
        if any(_sha(texts.get(name, "")) != digests[name] for name in names):
            return None
        found = []
        for name in names:
            state = documents.text_state(texts[name])
            if state is None:
                return None
            found.append((state, name, texts[name]))
        return sorted(found, key=lambda item: (item[0], item[1]))

    here = {name: (case / name).read_text(encoding="utf-8") for name in names if (case / name).is_file()}
    if len(here) == len(names) and (found := read(here)) is not None:
        return found, None
    listed = _git_out(case, "log", f"-{depth}", "--format=%H", "--", *names) or ""
    commits = [*([hint] if hint else []), *[c for c in listed.split() if c != hint]]
    for commit in commits:
        try:
            old = _texts_at(case, names, commit)
        except QuestionRoundError:
            continue
        if (found := read(old)) is not None:
            return found, commit
    return None


CARRIED = "carried:"


def _synthetic(record: dict[str, Any]) -> list[dict[str, Any]]:
    carried = {"round": f"{CARRIED}{record['from'][-1]}", "carried_from": record["from"], "ref": record["ref"],
               "units": dict(record["units"]), "scope": list(record["units"]), "blocked_units": [], "clear": True}
    return [carried, dict(carried)]


def _carried(case: Path, state: int, summaries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Two synthetic clear reviews of every unit, on the text a state closed on
    as one text before units existed; [] when there is no such closure, when
    the state closed unit by unit from the start (State 2), or when git no
    longer holds that text. The first unit round keeps what it carried, so
    later calls need no git search."""
    with_units = [s for s in summaries if "units" in s]
    for summary in with_units:
        if isinstance(summary.get("carried"), dict):
            return _synthetic(summary["carried"])
    if with_units:
        return []
    if not summaries or not summaries[-1].get("documents"):
        return []
    last = summaries[-1]
    # Closed by its own rule (rounds kept before the judge close on one round),
    # or by two clear rounds on the same documents.
    two_clear = (len(summaries) >= 2 and _clear(summaries[-2]) and _clear(last)
                 and summaries[-2].get("documents") == last["documents"])
    if not (last.get("closed") or two_clear):
        return []
    found = _texts_with_digests(case, last["documents"],
                                _added_at(case, rounds_dir(case, state) / last["round"] / "summary.json"))
    if found is None:
        return []
    texts, ref = found
    closed_units = units.units(texts, state)
    closing = [s["round"] for s in summaries[-2:]] if two_clear else [last["round"]]
    return _synthetic({"from": closing, "ref": ref,
                       "units": {key: unit["digest"] for key, unit in closed_units.items()}})


class StateTexts:
    """What a round of one state reads: its texts, its units, and the digests
    a round keeps."""

    def __init__(self, texts: list[tuple[int, str, str]], current: dict[str, dict[str, str]],
                 digests: dict[str, str]):
        self.texts, self.units, self.digests = texts, current, digests


def _spec_out_of_sync(case: Path) -> str | None:
    """Why the assembled specification does not hold the current design texts,
    or None when it does: the State 8 projection and the notes of 80_notes.md."""
    from notes_workbench import propagation
    from spec_projection_workbench import verify
    from spec_projection_workbench.model import SpecProjectionError

    spec_path = case / documents.SPEC_FILE
    if not spec_path.is_file():
        return f"{documents.SPEC_FILE} is not assembled"
    try:
        projection = verify(case)
    except (SpecProjectionError, ValueError, OSError) as exc:
        return f"the State 8 projection cannot be verified: {exc}"
    if not projection["ready"] or not projection["in_sync"]:
        return f"{documents.SPEC_FILE} is out of sync with the design ({projection['summary']['changes']} change(s))"
    notes_path = case / propagation.DEFAULT_SOURCE
    if notes_path.is_file():
        spec_notes = set(json.loads(spec_path.read_text(encoding="utf-8")).get("notes") or [])
        missing = [n for n in propagation._canonical_notes(notes_path.read_text(encoding="utf-8"))
                   if n not in spec_notes]
        if missing:
            return f"{len(missing)} note(s) of {propagation.DEFAULT_SOURCE} are not in {documents.SPEC_FILE}"
    return None


def _prompts_of(spec_path: Path, factory_root: Path | None) -> dict[str, str]:
    from factory_slice_workbench import FactoryPromptError, module_prompts

    if factory_root is None:
        raise QuestionRoundError(
            "State 7 is asked on the prompts the Factory builds, and no Factory was found: place "
            f"code_factory beside this repository or name it in {documents.FACTORY_ROOT_ENV}")
    try:
        return module_prompts(spec_path, factory_root)
    except FactoryPromptError as exc:
        raise QuestionRoundError(f"the Factory's prompts cannot be built: {exc}") from exc


def state_texts(case: Path, state: int, factory_root: Path | None = None) -> StateTexts:
    """The texts and units of State `state`. Raises QuestionRoundError when the
    state has no document, or for State 7, when its prompts cannot be built."""
    docs = documents.design_documents(case, state)
    if not any(found_state == state for found_state, _ in docs):
        raise QuestionRoundError(f"{case.name} has no State {state} document")
    if state != documents.MODULE_STATE:
        texts = [(s, p.name, p.read_text(encoding="utf-8")) for s, p in docs]
        return StateTexts(texts, units.units(texts, state), {name: _sha(body) for _, name, body in texts})
    reason = _spec_out_of_sync(case)
    if reason is not None:
        raise QuestionRoundError(
            f"State 7 is asked on the Factory's prompts, built from {documents.SPEC_FILE}, and {reason}: "
            f"run `python tools/design_spec_projection.py {case} --apply` (and propagate the notes) first")
    found = _prompts_of(case / documents.SPEC_FILE, factory_root or documents.factory_root())
    if not found:
        raise QuestionRoundError("the Factory generates no module of this specification: nothing to ask")
    texts = [(state, module, prompt) for module, prompt in found.items()]
    current = units.module_units(found)
    return StateTexts(texts, current, {key: unit["digest"] for key, unit in current.items()})


def unit_summaries(case: Path, state: int) -> list[dict[str, Any]]:
    """The summaries a state's units close by: its rounds, after the carried
    closure of a state closed as one text before units existed."""
    summaries = _summaries(case, state)
    return _carried(case, state, summaries) + summaries


def _norm(text: str) -> str:
    return " ".join(str(text).split())


def _set_aside(review: dict[str, Any], scope: list[str], changed: dict[str, tuple[str, list[str]]] | None = None,
               current: dict[str, dict[str, str]] | None = None) -> None:
    """Keep the points about a unit under review; a point naming another unit is
    set aside, recorded in the review but not grouped. A point naming no unit is
    kept and, when it blocks, keeps every unit under review open. A point on a
    unit reviewed for its change, quoting a passage of that unit away from the
    change, is set aside too."""
    changed, current = changed or {}, current or {}
    kept, aside = [], []
    for point in review["open_points"]:
        unit = point.get("unit") if isinstance(point, dict) else None
        if unit and unit not in scope:
            aside.append(point)
        elif unit in changed and _away_from_change(point, current[unit]["text"], changed[unit][1]):
            aside.append({**point, "set_aside_because": "an unchanged passage of a unit reviewed for its change"})
        else:
            if isinstance(point, dict) and not unit:
                point["unit"] = units.UNKNOWN
            kept.append(point)
    review["open_points"], review["set_aside"] = kept, aside


def _away_from_change(point: dict[str, Any], unit_text: str, regions: list[str]) -> bool:
    quoted = _norm(point.get("text") or "")
    if len(quoted) < 12 or quoted not in _norm(unit_text):
        return False  # quotes another text, or nothing checkable: keep it
    return not any(quoted in _norm(region) for region in regions)


def _clear(summary: dict[str, Any]) -> bool:
    if "judge" not in summary:
        return not summary.get("repeated_topics")
    return summary.get("blocking_topics") == 0


def _old_texts(case: Path, state: int, names: list[str], since: str | None,
               factory_root: Path | None) -> dict[str, str] | None:
    """The texts as they were at `since`: the documents, or for State 7 the
    Factory's prompts built from the specification of that ref."""
    if since is None:
        return None
    if state != documents.MODULE_STATE:
        return _texts_at(case, names, since)
    import tempfile

    spec = _texts_at(case, [documents.SPEC_FILE], since)[documents.SPEC_FILE]
    if not spec:
        raise QuestionRoundError(f"{documents.SPEC_FILE} does not exist at {since}")
    with tempfile.TemporaryDirectory(prefix="design-questions-since-") as temp:
        path = Path(temp) / documents.SPEC_FILE
        path.write_text(spec, encoding="utf-8")
        old = _prompts_of(path, factory_root or documents.factory_root())
    return {name: old.get(name, "") for name in names}


def _document_round(provider: Provider, state: int, runs: int, read: StateTexts, scope: list[str],
                    changed: dict[str, tuple[str, list[str]]], old: dict[str, str] | None,
                    case: Path, referencing: dict[str, list[str]] | None = None,
                    layer: dict[str, Any] | None = None
                    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    """States 0-6: every review reads the texts of States 0..N, asked about the open units,
    with the transition of the state (TRANSITION_PROTOCOL.md): what it owns, receives and
    carries, and the deterministic results of its gate and checks."""
    sections = documents.standard_sections(state)
    base = prompts.ask_instruction(state, documents.question_scope(state), sections)
    base += prompts.unit_scope(state, [(key, read.units[key]["title"]) for key in scope],
                               {key: diff for key, (diff, _) in changed.items()}, referencing)
    base += prompts.hypotheses_note(_previous_hypotheses(case, state))
    if state <= layer_prompt.LAST_STATE:
        # the prompt of the layer, not the texts of States 0..N (owner decision 2026-11-08)
        selection = layer_prompt.select(read.texts, state, read.units, scope, changed, referencing)
        text = layer_prompt.render(selection, read.texts, state)
        base += layer_prompt.note(selection, state)
    else:
        text = prompts.ask_input(read.texts)
    later = {p.name: p.read_text(encoding="utf-8") for _, p in documents.later_documents(case, state)}
    evidence = (layer or {}).get("unit_evidence") or {}
    precedents = [p for p in _precedents(case, state) if _evidence_holds(p, evidence, scope)]
    instruction = base + prompts.layer_scope(layer, scope)
    with ThreadPoolExecutor(max_workers=runs) as pool:
        reviews = list(pool.map(lambda _: _review_or_failed(provider, instruction, text), range(runs)))
    _valid_reviews(reviews, f"State {state}")
    for review in reviews:
        _set_aside(review, scope, changed, read.units)
    topics = _group(provider, reviews, keep_points=True)
    repeated = _judged(topics, witness=True)
    judged = (_judge(provider, state, text, read.texts, repeated, old, later, precedents,
                     witness=True, case=case, layer=prompts.layer_judge(layer, scope), scope=scope,
                     sections=sections) if repeated
              else {"provider": provider.name})
    return reviews, topics, repeated, judged


def _previous_hypotheses(case: Path, state: int) -> list[tuple[str, str]]:
    """The hypotheses of the state's latest round: topics judged without a witness."""
    summaries = _summaries(case, state)
    if not summaries:
        return []
    return [(t["topic"], (t.get("judgement") or {}).get("witness_missing") or (t.get("judgement") or {}).get("why", ""))
            for t in summaries[-1].get("topics", [])
            if (t.get("judgement") or {}).get("kind") == judge.HYPOTHESIS]


def _module_round(provider: Provider, state: int, runs: int, read: StateTexts, scope: list[str],
                  changed: dict[str, tuple[str, list[str]]], old: dict[str, str] | None,
                  case: Path, referencing: dict[str, list[str]] | None = None,
                  layer: dict[str, Any] | None = None, probe: bool = False
                  ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    """State 7: each review reads one module's prompt, as its generator would, and is
    asked against the obligations received at State 7 that the module takes part in.
    A `probe` offers the judge no precedent: every topic is judged afresh."""
    scope_text = documents.question_scope(state)
    sections = documents.standard_sections(state)

    import transition

    # received obligations, limited to each module (transition.module_obligations);
    # the Factory prompt itself stays as the Factory builds it
    obligations = {module: transition.module_obligations(case, layer or {}, module) for module in scope}

    def one(job: tuple[str, int]) -> dict[str, Any]:
        module = job[0]
        diff = changed[module][0] if module in changed else None
        review = _review_or_failed(provider,
                                   prompts.module_ask_instruction(state, scope_text, diff, obligations[module],
                                                                  sections),
                                   prompts.module_input(module, read.units[module]["text"]))
        review["unit"] = module
        for point in review["open_points"]:
            if isinstance(point, dict):
                point["unit"] = module
        _set_aside(review, [module], changed, read.units)
        return review

    jobs = [(module, run) for module in scope for run in range(runs)]
    with ThreadPoolExecutor(max_workers=min(MODULE_WORKERS, len(jobs))) as pool:
        reviews = list(pool.map(one, jobs))
    for module in scope:
        _valid_reviews([r for r in reviews if r["unit"] == module], f"State {state} module {module}")
    precedents = [] if probe else _precedents(case, state)
    topics: list[dict[str, Any]] = []
    repeated: list[dict[str, Any]] = []
    judged: dict[str, Any] = {"provider": provider.name, "modules": {}}
    for module in scope:
        mine = _group(provider, [r for r in reviews if r["unit"] == module], keep_points=True)
        for topic in mine:
            topic["units"] = [module]
        # a State 7 topic is a contradiction quoted on both sides and checked
        # mechanically, so one review is enough to judge it
        again = list(mine)
        if again:
            text = prompts.module_input(module, read.units[module]["text"])
            module_old = None if old is None else {module: old.get(module, "")}
            judged["modules"][module] = _judge(provider, state, text, [(state, module, read.units[module]["text"])],
                                               again, module_old, None, precedents,
                                               layer=prompts.module_layer_judge(obligations[module]),
                                               sections=sections)
            for topic in again:
                topic["id"] = f"{module}:{topic['id']}"
        topics += mine
        repeated += again
    return reviews, topics, repeated, judged


def ask_round(case: Path, state: int, provider: Provider, runs: int = DEFAULT_RUNS,
              since: str | None = None, factory_root: Path | None = None) -> dict[str, Any]:
    """Run one question round for State `state` of `case` and keep it in the case.

    `since` names the git ref at which a reopened state was closed; the judge
    then sees the change since, and may judge a topic about an untouched passage
    as preexisting. `factory_root` is the Factory that builds the State 7
    prompts (default: SPEC_WORKBENCH_FACTORY_ROOT or the sibling checkout).
    """
    if runs < REPEATED:
        raise QuestionRoundError(f"a round needs at least {REPEATED} reviews to tell a repeated topic")
    read = state_texts(case, state, factory_root)
    previous_summaries = unit_summaries(case, state)
    evidence = unit_evidence(case, state)
    before = units.states(previous_summaries, read.units, evidence)
    # One round per change: a round reviews only the units that need one —
    # never reviewed, changed since their latest review, or with evidence that
    # changed. A unit waiting for dispositions or for the fix of a
    # contradiction is not asked again on the same text.
    scope = [key for key in read.units if before[key]["needs_round"]]
    if not scope:
        if all(value["closed"] for value in before.values()):
            raise QuestionRoundError(f"every unit of State {state} is closed on its current text; nothing to ask")
        raise QuestionRoundError(_nothing_to_ask(state, before))
    changed = _changed_units(case, read.texts, state, scope, read.units, previous_summaries)
    # a unit reviewed on its text whose bound checks changed is asked about the new evidence
    evidence_reopened = [key for key in scope if before[key]["needs_round"] == units.EVIDENCE_CHANGED]
    # a closed unit that names a decision changed since its closure is asked
    # again, for that change only
    referencing = (units.referencing(read.units, list(changed), scope)
                   if state != documents.MODULE_STATE else {})
    if referencing:
        scope = [key for key in read.units if key in scope or key in referencing]
    old = _old_texts(case, state, [name for _, name, _ in read.texts], since, factory_root)
    asked = _module_round if state == documents.MODULE_STATE else _document_round
    judge_checks(case, state, provider)  # each bound check judged once, kept by digest
    layer = layer_context(case, state)
    layer["evidence_reopened"] = evidence_reopened
    layer["unit_evidence"] = evidence or {}
    reviews, topics, repeated, judged = asked(provider, state, runs, read, scope, changed, old, case, referencing,
                                              layer)
    for topic in topics:
        topic.pop("points", None)
        topic.pop("quoted", None)
    directory = _next_round(case, state)
    directory.mkdir(parents=True)
    names = [f"review-{review['unit']}-{(index - 1) % runs + 1}.json" if "unit" in review
             else f"review-{index}.json" for index, review in enumerate(reviews, 1)]
    for name, review in zip(names, reviews):
        (directory / name).write_text(json.dumps(review, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    if state == documents.MODULE_STATE:
        kept = directory / PROMPTS_DIR
        kept.mkdir()
        for key in scope:
            (kept / f"{key}.txt").write_text(read.units[key]["text"], encoding="utf-8")
    blocking = [t for t in repeated if t["judgement"]["blocking"]]
    deferred = [t for t in repeated if t["judgement"].get("deferred_to")]
    summary = {
        "schema_version": SCHEMA,
        "closure": units.CLOSURE_RULE,
        "state": state,
        "round": directory.name,
        "provider": provider.name,
        "documents": read.digests,
        "reviews": runs,
        "points": [len(r["open_points"]) for r in reviews],
        # a review whose answer was not valid JSON twice (#147): kept, no point taken from it
        "failed_reviews": [{"review": name, "reason": r["failed"]} for name, r in zip(names, reviews)
                           if "failed" in r],
        "since": since,
        "judge": judged,
        "repeated_topics": len(repeated),
        "witness_singletons": sum(1 for t in repeated if len(t["runs"]) < REPEATED),
        "hypothesis_topics": sum(1 for t in repeated if t["judgement"].get("kind") == judge.HYPOTHESIS),
        "blocking_topics": len(blocking),
        "deferred_topics": len(deferred),
        "clear": not blocking,
        "closed": False,
        "units": {key: unit["digest"] for key, unit in read.units.items()},
        "scope": scope,
        "changed_units": sorted(changed),
        "referenced_by_change": referencing,
        "blocked_units": units.blocked(repeated, scope),
        "set_aside": [len(r["set_aside"]) for r in reviews],
        "topics": topics,
        "layer": layer_record(layer),
        "unit_evidence": {key: evidence[key] for key in scope if key in (evidence or {})},
        "evidence_reopened": evidence_reopened,
        "transition_ready": layer["ready"],
    }
    if previous_summaries and str(previous_summaries[0].get("round")).startswith(CARRIED):
        first = previous_summaries[0]
        summary["carried"] = {"from": first["carried_from"], "ref": first["ref"], "units": first["units"]}
    after = units.states(previous_summaries + [summary], read.units, evidence)
    summary["closed"] = all(value["closed"] for value in after.values())
    summary["open_units"] = [key for key, value in after.items() if not value["closed"]]
    # what this round asks of the author: topics to dispose, units whose contradiction needs a fix
    summary["awaiting_disposition"] = sorted({t for key in scope for t in after[key]["awaiting"]})
    summary["contradiction_units"] = [key for key in scope if after[key]["contradictions"] or after[key]["unverified"]]
    (directory / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return summary


def judge_checks(case: Path, state: int, provider: Provider) -> list[dict[str, Any]]:
    """Judge the bound checks that have no judgement on their current files and
    items, at a state where witness_material closes (transition.judges_witnesses;
    State 2 only carries it). The judgement itself does not depend on the
    state: `design_questions.py judge-checks` makes it for any case."""
    import design_decision_witness
    import transition
    import witness_judgement

    if not transition.judges_witnesses(transition.load_sequence(), state):
        return []
    return witness_judgement.judge(case, provider, design_decision_witness.binding_material(case))


def unit_evidence(case: Path, state: int) -> dict[str, str] | None:
    """unit -> the digest of the evidence its decision's bindings rest on
    (design_decision_witness.evidence_basis), at a state where witness_material
    closes. Elsewhere None: units close on their text alone, so a changed check
    reopens none of them, and neither does an evidence digest a round recorded
    before the owner decision of 2026-11-08 (State 2 only describes the test)."""
    import design_decision_witness
    import transition

    if not transition.judges_witnesses(transition.load_sequence(), state):
        return None
    try:
        return design_decision_witness.evidence_basis(design_decision_witness.binding_material(case))
    except Exception:  # unreadable evidence is reported by witness_material; it closes nothing new
        return {}


def layer_context(case: Path, state: int) -> dict[str, Any]:
    """The transition a round of `state` is asked with (transition.round_context).

    Kept apart from the texts: it is not cut into units and changes no digest,
    so a deterministic result that changes reopens no unit.
    """
    import transition

    try:
        return transition.round_context(case, state)
    except Exception as exc:  # never report a transition clean that could not be read
        return {"state": state, "owns": [], "carries": [], "results": [], "ready": False,
                "gate_findings": [{"code": "transition_not_checked", "severity": "error",
                                   "message": f"the transition of State {state} could not be read ({exc})"}]}


def layer_record(layer: dict[str, Any]) -> dict[str, Any]:
    """What a round keeps of its transition: enough to say what the reviewers were shown."""
    return {"ready": layer["ready"],
            "results": [{"check": r["check"], "from": r["from"], "outcome": r["outcome"],
                         "findings": len(r.get("findings") or [])} for r in layer.get("results") or []],
            "gate_findings": len(layer.get("gate_findings") or []),
            # the verdicts the round was given: which check judgement, by digest
            "verdicts": [{"decision": v["decision"], "witness": v["witness"], "digest": v["digest"],
                          "outcome": v["outcome"]} for v in layer.get("verdicts") or []],
            # what the authors of earlier states carried here by a disposition
            "carried_in": [{"state": c["state"], "round": c["round"], "topic": c["topic"]}
                           for c in layer.get("carried_in") or []],
            "digest": _sha(json.dumps(layer, sort_keys=True, ensure_ascii=False, default=str))}


def _closed_at(case: Path, state: int, summaries: list[dict[str, Any]]) -> str | None:
    """The git ref the state was last closed at, for `ask --since`: the latest
    commit of the round that closed every unit of its text (with the author's
    dispositions, kept in the same directory), or that held a carried
    closure's texts."""
    for index in range(len(summaries) - 1, -1, -1):
        summary = summaries[index]
        if str(summary.get("round", "")).startswith(CARRIED):
            return summary.get("ref") or "HEAD"
        digests = summary.get("units") or {}
        closing = summary.get("closed") or (digests and all(
            units.unit_state(summaries[:index + 1], key, digest)["closed"] for key, digest in digests.items()))
        if closing:
            directory = rounds_dir(case, state) / summary["round"]
            found = _git_out(case, "log", "-1", "--format=%H", "--", str(directory.resolve()))
            ref = (found or "").strip() or _added_at(case, directory / "summary.json")
            if ref:
                return ref
    return None


def status(case: Path, state: int, factory_root: Path | None = None, with_transition: bool = False) -> dict[str, Any]:
    """Whether the state is closed on its current texts, unit by unit.

    With `with_transition`, also whether its transition holds: `closed` is the
    rounds' verdict, `ready` adds what closes at the state (TRANSITION_PROTOCOL.md),
    so a round that closed never hides a blocking deterministic result."""
    result = _status(case, state, factory_root)
    if with_transition:
        layer = layer_context(case, state)
        result["transition"] = {**layer_record(layer), "findings": [
            {"check": r["check"], "from": r["from"], "outcome": r["outcome"], **f}
            for r in layer["results"] if r["outcome"] not in ("closed", "carried") for f in r.get("findings") or []
        ] + [{"check": "gate", **f} for f in layer["gate_findings"] if f.get("severity") in ("error", "block")]}
        result["ready"] = bool(result["closed"]) and layer["ready"]
        if result["closed"] and not layer["ready"]:
            result["reason"] += "; the rounds closed, but the transition does not hold (see transition)"
    return result


def _status(case: Path, state: int, factory_root: Path | None = None) -> dict[str, Any]:
    rounds = _summaries(case, state)
    latest = rounds[-1] if rounds else None
    base = {"state": state, "round": latest["round"] if latest else None,
            "provider": latest.get("provider") if latest else None,
            "carried_in": carried_items(case, to=state)}
    try:
        read = state_texts(case, state, factory_root)
    except QuestionRoundError as exc:
        return {**base, "closed": False, "reason": str(exc), "open_units": [], "units": 0, "repeated": []}
    keys = list(read.units)
    if not rounds:
        return {**base, "closed": False, "reason": "no question round yet", "open_units": keys,
                "units": len(keys), "closed_at": None, "repeated": []}
    summaries = unit_summaries(case, state)
    stale = read.digests != latest["documents"]
    repeated = [t for t in latest["topics"] if len(t["runs"]) >= REPEATED]
    if not any("units" in s for s in summaries):
        # Rounds kept before units, which never closed the state: the next round reviews every unit.
        return {**base, "closed": False, "stale": stale, "open_units": keys, "units": len(keys),
                "closed_at": None, "repeated": repeated,
                "reason": ("the design texts changed after the latest round" if stale else _open_reason(latest))
                          + "; the state never closed, so every unit is open"}
    evidence = unit_evidence(case, state)
    per_unit = units.states(summaries, read.units, evidence)
    open_units = [key for key, value in per_unit.items() if not value["closed"]]
    changed = [key for key in open_units if per_unit[key]["needs_round"] == units.CHANGED]
    return {
        **base,
        "closed": not open_units,
        "stale": stale,
        "carried": str(summaries[0].get("round", "")).startswith(CARRIED),
        "reason": _units_reason(per_unit),
        "open_units": open_units,
        "changed_units": changed,
        # reviewed on their text, reopened because the checks their bindings name changed
        "evidence_changed": [key for key in open_units if per_unit[key]["needs_round"] == units.EVIDENCE_CHANGED],
        # per unit: what keeps it open, and what its latest round carried on (owner decision 2026-11-08)
        "unit_status": {key: _unit_row(value) for key, value in per_unit.items()
                        if not value["closed"] or value["carried"]},
        "needs_round": [key for key in open_units if per_unit[key]["needs_round"]],
        "contradictions": {key: per_unit[key]["contradictions"] + per_unit[key]["unverified"]
                           for key in open_units if per_unit[key]["contradictions"] or per_unit[key]["unverified"]},
        "awaiting_disposition": {key: per_unit[key]["awaiting"] for key in open_units if per_unit[key]["awaiting"]},
        "closed_by": {rule: sum(1 for v in per_unit.values() if v["rule"] == rule)
                      for rule in ("two_clear_rounds", units.CLOSURE_RULE)},
        "units": len(per_unit),
        "closed_at": _closed_at(case, state, summaries),
        "repeated": repeated,
    }


def _unit_row(value: dict[str, Any]) -> dict[str, Any]:
    return {k: value[k] for k in ("closed", "rule", "round", "needs_round", "contradictions", "unverified",
                                  "awaiting", "carried") if value[k] not in (None, [], False) or k == "closed"}


def _units_reason(per_unit: dict[str, dict[str, Any]]) -> str:
    open_units = [key for key, value in per_unit.items() if not value["closed"]]
    if not open_units:
        return ("every unit closed on its current text: its latest round raised no open contradiction, "
                "and every topic of it has a disposition (or it closed by two clear rounds before 2026-11-08)")
    parts = []
    rounds = [k for k in open_units if per_unit[k]["needs_round"]]
    fixes = [k for k in open_units if per_unit[k]["contradictions"]]
    waiting = [k for k in open_units if per_unit[k]["awaiting"]]
    if rounds:
        parts.append(f"{len(rounds)} need a round ({', '.join(rounds)})")
    if fixes:
        parts.append(f"{len(fixes)} hold an open contradiction, closed by a change of the text and one round on it "
                     f"({', '.join(fixes)})")
    if waiting:
        topics = len({t for k in waiting for t in per_unit[k]["awaiting"]})
        parts.append(f"{len(waiting)} wait for the author's disposition of {topics} topic(s) "
                     f"({', '.join(waiting)}): design_questions.py dispose")
    return f"{len(open_units)} of {len(per_unit)} unit(s) open: " + "; ".join(parts)


def _nothing_to_ask(state: int, per_unit: dict[str, dict[str, Any]]) -> str:
    """Why a round would ask nothing although the state is open: one round per change."""
    return (f"no unit of State {state} needs a round: its text has not changed since its latest review. "
            + _units_reason(per_unit) + ". Dispose of the topics, or change the text a contradiction quotes; "
            "a second round on the same text is not asked (owner decision 2026-11-08, #147)")


def _open_reason(summary: dict[str, Any]) -> str:
    if "judge" not in summary:
        return f"{summary['repeated_topics']} topic(s) raised by two or more reviews"
    if summary["blocking_topics"]:
        return f"{summary['blocking_topics']} blocking topic(s): contradiction, consequential gap or unverified judgement"
    return "a clear round"


# ---------------------------------------------------------------- dispositions

def _topic(summary: dict[str, Any], topic_id: str) -> tuple[str, dict[str, Any]] | None:
    for index, topic in enumerate(summary.get("topics") or [], 1):
        if str(topic.get("id") or f"#{index}") == topic_id:
            return topic_id, topic
    return None


def _carry_target(state: int, to: str) -> int | str:
    """A receiving layer from the closed set: a later state, or generation,
    factory_checks, deploy."""
    text = str(to).strip().lower().removeprefix("state").strip()
    if text.isdigit():
        number = int(text)
        if not state < number <= ASSEMBLY_STATE:
            raise QuestionRoundError(f"carried to State {number}: a topic of State {state} is carried to a later "
                                     f"state (State {state + 1} to {ASSEMBLY_STATE}) or to {', '.join(CARRY_LAYERS)}")
        return number
    if text in CARRY_LAYERS:
        return text
    raise QuestionRoundError(f"carried to {to!r}: the receiving layer is a later state number or one of "
                             f"{', '.join(CARRY_LAYERS)}")


def _fix_ref(case: Path, directory: Path, ref: str) -> str:
    """The commit a `fixed` disposition references: it exists, changes the
    case, and does not precede the round it answers."""
    commit = (_git_out(case, "rev-parse", "--verify", f"{ref}^{{commit}}") or "").strip()
    if not commit:
        raise QuestionRoundError(f"fixed: {ref!r} is not a commit of the case's history")
    touched = _git_out(case, "diff-tree", "--no-commit-id", "--name-only", "-r", "--root", commit, "--",
                       str(case.resolve()))
    if not (touched or "").strip():
        raise QuestionRoundError(f"fixed: commit {commit[:12]} changes nothing in {case.name}")
    kept = _added_at(case, directory / "summary.json")
    if kept and subprocess.run(["git", "-C", str(case), "merge-base", "--is-ancestor", kept, commit],
                               capture_output=True).returncode != 0:
        raise QuestionRoundError(f"fixed: commit {commit[:12]} does not follow the round it answers ({kept[:12]})")
    return commit


def dispose(case: Path, state: int, topic_id: str, disposition: str, *, round_name: str | None = None,
            unit: str | None = None, ref: str | None = None, to: str | None = None, what: str | None = None,
            reason: str | None = None) -> dict[str, Any]:
    """Record the author's disposition of one topic of a round (owner decision
    2026-11-08, #147): `fixed` with the commit of the change, `carried` to a
    later state or to generation, factory_checks or deploy with what it must
    decide there, or `accepted` with the author's reason. A contradiction takes
    none: it closes by a change of the text and a round on it. Kept in
    questions/state<N>/round-<k>/dispositions.json; returns the entry."""
    summaries = _summaries(case, state)
    if not summaries:
        raise QuestionRoundError(f"State {state} has no question round")
    if round_name is None:
        summary = summaries[-1]
    else:
        summary = next((s for s in summaries if s.get("round") == round_name), None)
        if summary is None:
            raise QuestionRoundError(f"State {state} has no round {round_name}")
    found = _topic(summary, topic_id)
    if found is None:
        raise QuestionRoundError(f"{summary['round']} of State {state} has no topic {topic_id}")
    _, topic = found
    need = units.topic_need(topic, summary)
    if need == units.CONTRADICTION:
        kind = (topic.get("judgement") or {}).get("kind") or "contradiction"
        raise QuestionRoundError(f"{topic_id} is a {kind.replace('_', ' ')}: it takes no disposition and closes "
                                 "when a round on the changed text no longer raises it")
    if need is None:
        raise QuestionRoundError(f"{topic_id} needs no disposition: "
                                 f"{(topic.get('judgement') or {}).get('kind') or 'it was not judged'}")
    concerned = units.topic_units(topic, list(summary.get("scope") or []))
    if unit is not None and unit not in concerned:
        raise QuestionRoundError(f"{topic_id} does not concern unit {unit!r}; it concerns {', '.join(concerned)}")
    directory = rounds_dir(case, state) / summary["round"]
    entry: dict[str, Any] = {"topic": topic_id, "topic_text": topic.get("topic", ""),
                             **({"unit": unit} if unit else {}), "disposition": disposition}
    if disposition == "fixed":
        if not (ref or "").strip():
            raise QuestionRoundError("fixed needs --ref: the commit of the change")
        entry["ref"] = _fix_ref(case, directory, ref)
    elif disposition == "carried":
        if to is None or not (what or "").strip():
            raise QuestionRoundError("carried needs --to (the receiving layer) and --what (what it must decide)")
        entry["to"], entry["what"] = _carry_target(state, to), what.strip()
    elif disposition == "accepted":
        if not (reason or "").strip():
            raise QuestionRoundError("accepted needs --reason: the author's reason")
        entry["reason"] = reason.strip()
    else:
        raise QuestionRoundError(f"unknown disposition {disposition!r}; one of {', '.join(DISPOSITION_KINDS)}")
    kept = [d for d in _dispositions(directory) if (d.get("topic"), d.get("unit")) != (topic_id, unit)]
    kept.append(entry)
    payload = {"schema_version": DISPOSITIONS_SCHEMA, "state": state, "round": summary["round"],
               "dispositions": kept}
    (directory / DISPOSITIONS_FILE).write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n",
                                               encoding="utf-8")
    return entry


def carried_items(case: Path, to: int | str | None = None) -> list[dict[str, Any]]:
    """Every topic the author carried to a later layer, across the states'
    rounds: {state, round, topic, topic_text, unit, to, what}. With `to`, only
    those carried to that layer (a state number, or generation, factory_checks,
    deploy)."""
    base = case / "questions"
    if not base.is_dir():
        return []
    found = []
    for directory in sorted(base.glob("state*/round-*"), key=lambda p: (p.parent.name, _round_number(p / "x"))):
        state_name = directory.parent.name.removeprefix("state")
        if not state_name.isdigit():
            continue
        for entry in _dispositions(directory):
            if entry.get("disposition") != "carried" or (to is not None and entry.get("to") != to):
                continue
            found.append({"state": int(state_name), "round": directory.name,
                          **{k: entry.get(k) for k in ("topic", "topic_text", "unit", "to", "what")}})
    return found


class _SizeLog:
    """A provider that records the input size of every request it passes on:
    what a round costs, per review, grouping and judgement."""

    def __init__(self, provider: Provider):
        self.provider, self.name, self.requests = provider, provider.name, []
        self.reads_files = bool(getattr(provider, "reads_files", False))

    def _log(self, instruction: str, text: str, files: dict[str, str] | None = None) -> None:
        kind = ("judge" if instruction.startswith("You judge") else
                "group" if instruction.startswith("You receive the open points") else "review")
        module = text.split("`", 2)[1] if text.startswith("=== the Factory's prompt for generating `") else None
        if kind == "judge" and "=== the Factory's prompt for generating `" in text:
            module = text.split("=== the Factory's prompt for generating `", 1)[1].split("`", 1)[0]
        self.requests.append({"kind": kind, "module": module, "instruction_chars": len(instruction),
                              "text_chars": len(text), "file_chars": sum(len(b) for b in (files or {}).values()),
                              "total_chars": len(instruction) + len(text)
                              + sum(len(b) for b in (files or {}).values())})

    def complete(self, instruction: str, text: str) -> tuple[str, dict[str, Any]]:
        self._log(instruction, text)
        return self.provider.complete(instruction, text)

    def complete_with_files(self, instruction: str, text: str, files: dict[str, str]) -> tuple[str, dict[str, Any]]:
        self._log(instruction, text, files)
        return self.provider.complete_with_files(instruction, text, files)  # type: ignore[attr-defined]


PROBE_SCHEMA = "spec_workbench_question_probe.v1"


def probe_round(case: Path, state: int, provider: Provider, out: Path, runs: int = DEFAULT_RUNS,
                factory_root: Path | None = None, modules: list[str] | None = None) -> dict[str, Any]:
    """A State 7 round over the named generated modules, or all of them, on
    their current prompts whether they are closed or not, kept in `out`, never
    in the case: it records no round, no closure and no disposition, offers no
    precedent and judges no bound check. It measures what a round would raise
    now, after a change of the round's own instruction, and logs the input
    size of every request."""
    if state != documents.MODULE_STATE:
        raise QuestionRoundError(f"a probe asks State {documents.MODULE_STATE} module by module; "
                                 f"State {state} is asked by `ask`")
    if runs < REPEATED:
        raise QuestionRoundError(f"a round needs at least {REPEATED} reviews to tell a repeated topic")
    out = Path(out)
    if out.exists() and any(out.iterdir()):
        raise QuestionRoundError(f"{out} is not empty: a probe writes into a directory of its own")
    if out.resolve().is_relative_to(case.resolve()):
        raise QuestionRoundError("a probe is kept outside the case: it must not read as a round")
    read = state_texts(case, state, factory_root)
    unknown = sorted(set(modules or []) - set(read.units))
    if unknown:
        raise QuestionRoundError(f"not generated modules of State {state}: {', '.join(unknown)}")
    scope = [key for key in read.units if not modules or key in modules]
    logged = _SizeLog(provider)
    layer = layer_context(case, state)
    reviews, topics, repeated, judged = _module_round(logged, state, runs, read, scope, {}, None, case, None,
                                                      layer, probe=True)
    for topic in topics:
        topic.pop("points", None)
        topic.pop("quoted", None)
    out.mkdir(parents=True, exist_ok=True)
    (out / PROMPTS_DIR).mkdir()
    for key in scope:
        (out / PROMPTS_DIR / f"{key}.txt").write_text(read.units[key]["text"], encoding="utf-8")
    for index, review in enumerate(reviews):
        name = f"review-{review['unit']}-{index % runs + 1}.json"
        (out / name).write_text(json.dumps(review, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    blocking = [t for t in repeated if t["judgement"]["blocking"]]
    per_module = {}
    for key in scope:
        mine = [t for t in topics if key in (t.get("units") or [])]
        kinds: dict[str, int] = {}
        for topic in mine:
            kind = (topic.get("judgement") or {}).get("kind") or "not judged"
            kinds[kind] = kinds.get(kind, 0) + 1
        per_module[key] = {"topics": len(mine), "blocking": sum(1 for t in mine if t in blocking), "kinds": kinds,
                           "prompt_chars": len(read.units[key]["text"])}
    summary = {
        "schema_version": PROBE_SCHEMA,
        "state": state,
        "provider": provider.name,
        "reviews": runs,
        "scope": scope,
        "units": {key: read.units[key]["digest"] for key in scope},
        "standard_sections": [s["section"] for s in documents.standard_sections(state)],
        "judge": judged,
        "modules": per_module,
        "blocking_topics": len(blocking),
        "topics": topics,
        "requests": logged.requests,
        "failed_reviews": [{"unit": r.get("unit"), "reason": r["failed"]} for r in reviews if "failed" in r],
    }
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return summary
