"""A question round: several independent reviews, grouped, judged, kept with the case.

A topic raised by two or more reviews is judged (judge.py). A round is clear
when no judged topic blocks: no contradiction, no gap with an observable
consequence, and no judgement whose evidence failed its check. A topic raised
by one review only is recorded and may be closed or carried, but it does not
keep the state open.

Every state closes unit by unit (units.py): a unit is closed when its two
latest reviews were clear for it on its current text, and the state when every
unit is. A state closed as one text before units existed (its two latest
rounds clear on the same documents) carries that closure to each of its units
on the text it closed on, found in the case's git history; a later edit then
reopens only the units it touched.

State 7 is asked module by module: each review gets the prompt the Factory
builds for one generated module (factory_slice_workbench.module_prompts), from
the case's assembled specification.

Rounds kept before the judge existed (no "judge" in the summary) keep their
own rule: clear when no topic was raised by two reviews.
"""
from __future__ import annotations

import difflib
import hashlib
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from . import documents, judge, prompts, units
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
        named = sorted({str(points[m]["unit"]) for m in topic["members"] if points[m].get("unit")})
        if named:
            topic["units"] = named
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
    for summary in [s for s in judged if "judge" in s][-PRECEDENT_ROUNDS:][::-1]:
        for topic in summary.get("topics", []):
            judgement = topic.get("judgement") or {}
            if not judgement.get("verified") or judgement.get("blocking") or topic["topic"] in seen:
                continue
            source = judgement.get("precedent") or judgement
            seen.add(topic["topic"])
            found.append({"id": f"P{len(found) + 1}", "round": source.get("round", summary["round"]),
                          "topic": topic["topic"], "kind": source["kind"],
                          "quotes": list(source.get("quotes") or []), "why": source.get("why", ""),
                          **({"deferred_to": source["deferred_to"]} if source.get("deferred_to") else {})})
    return found


def _judge(provider: Provider, state: int, text: str, texts: list[tuple[int, str, str]],
           repeated: list[dict[str, Any]], old: dict[str, str] | None,
           later: dict[str, str] | None = None,
           precedents: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Judge the repeated topics. `later` maps the later states' documents to
    their texts; a provider that reads files gets them as files to search, so
    the judge can find a topic already decided below without receiving them
    whole. Other providers judge without them. `precedents` are the state's
    prior non-blocking judgements, which the judge may follow for the same
    question on unchanged passages."""
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
    later = later if later and getattr(provider, "reads_files", False) else None
    later_files = [f"{LATER_DIR}/{name}" for name in sorted(later)] if later else None
    # Offer only a precedent the judge can still follow. One whose quoted
    # passages changed invites `judged_before`, which `judge.check` then rejects
    # as blocking; such a topic is judged afresh (QUESTIONS.md).
    current = "\n\n".join(b for _, _, b in texts)
    later_text = "\n\n".join(later.values()) if later else None
    precedents = [p for p in precedents or [] if judge.precedent_holds(p, current, later_text)]
    try:
        scope = documents.question_scope(state)
    except documents.QuestionScopeError:
        scope = None
    instruction = prompts.judge_instruction(state, old is not None, later_files, bool(precedents), scope)
    judge_text = prompts.judge_input(text, items, change, precedents)
    if later:
        answer = provider.complete_with_files(instruction, judge_text, later)[0]
    else:
        answer = provider.complete(instruction, judge_text)[0]
    judgements = {j.get("id"): j for j in _json_object(answer).get("judgements") or [] if isinstance(j, dict)}
    body = "\n\n".join(b for _, _, b in texts)
    old_body = None if old is None else "\n\n".join(old.values())
    for topic in repeated:
        topic["judgement"] = judge.check(judgements.get(topic["id"]), state, body, old_body,
                                         "\n\n".join(later.values()) if later else None,
                                         {p["id"]: p for p in precedents or []},
                                         "\n\n".join(b for s, _, b in texts if s == state))
    result = {"provider": provider.name, "raw": answer}
    if later:
        result["later_documents"] = {name: hashlib.sha256(body.encode("utf-8")).hexdigest()
                                     for name, body in later.items()}
    return result


def _summaries(case: Path, state: int) -> list[dict[str, Any]]:
    paths = sorted(rounds_dir(case, state).glob("round-*/summary.json"), key=_round_number)
    return [json.loads(p.read_text(encoding="utf-8")) for p in paths]


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
                    case: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    """States 0-6: every review reads the texts of States 0..N, asked about the open units."""
    instruction = prompts.ask_instruction(state, documents.question_scope(state))
    instruction += prompts.unit_scope(state, [(key, read.units[key]["title"]) for key in scope],
                                      {key: diff for key, (diff, _) in changed.items()})
    text = prompts.ask_input(read.texts)
    with ThreadPoolExecutor(max_workers=runs) as pool:
        reviews = list(pool.map(lambda _: _review(provider, instruction, text), range(runs)))
    for review in reviews:
        _set_aside(review, scope, changed, read.units)
    topics = _group(provider, reviews, keep_points=True)
    repeated = [t for t in topics if len(t["runs"]) >= REPEATED]
    later = {p.name: p.read_text(encoding="utf-8") for _, p in documents.later_documents(case, state)}
    judged = (_judge(provider, state, text, read.texts, repeated, old, later, _precedents(case, state)) if repeated
              else {"provider": provider.name})
    return reviews, topics, repeated, judged


def _module_round(provider: Provider, state: int, runs: int, read: StateTexts, scope: list[str],
                  changed: dict[str, tuple[str, list[str]]], old: dict[str, str] | None,
                  case: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    """State 7: each review reads one module's prompt, as its generator would."""
    scope_text = documents.question_scope(state)

    def one(job: tuple[str, int]) -> dict[str, Any]:
        module = job[0]
        diff = changed[module][0] if module in changed else None
        review = _review(provider, prompts.module_ask_instruction(state, scope_text, diff),
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
    precedents = _precedents(case, state)
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
                                               again, module_old, None, precedents)
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
    still_open = units.closed(previous_summaries, read.units)
    scope = [key for key in read.units if not still_open[key]]
    if not scope:
        raise QuestionRoundError(f"every unit of State {state} is closed on its current text; nothing to ask")
    changed = _changed_units(case, read.texts, state, scope, read.units, previous_summaries)
    old = _old_texts(case, state, [name for _, name, _ in read.texts], since, factory_root)
    asked = _module_round if state == documents.MODULE_STATE else _document_round
    reviews, topics, repeated, judged = asked(provider, state, runs, read, scope, changed, old, case)
    for topic in topics:
        topic.pop("points", None)
    directory = _next_round(case, state)
    directory.mkdir(parents=True)
    for index, review in enumerate(reviews, 1):
        name = (f"review-{review['unit']}-{(index - 1) % runs + 1}.json" if "unit" in review
                else f"review-{index}.json")
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
        "state": state,
        "round": directory.name,
        "provider": provider.name,
        "documents": read.digests,
        "reviews": runs,
        "points": [len(r["open_points"]) for r in reviews],
        "since": since,
        "judge": judged,
        "repeated_topics": len(repeated),
        "blocking_topics": len(blocking),
        "deferred_topics": len(deferred),
        "clear": not blocking,
        "closed": False,
        "units": {key: unit["digest"] for key, unit in read.units.items()},
        "scope": scope,
        "changed_units": sorted(changed),
        "blocked_units": units.blocked(repeated, scope),
        "set_aside": [len(r["set_aside"]) for r in reviews],
        "topics": topics,
    }
    if previous_summaries and str(previous_summaries[0].get("round")).startswith(CARRIED):
        first = previous_summaries[0]
        summary["carried"] = {"from": first["carried_from"], "ref": first["ref"], "units": first["units"]}
    open_after = units.closed(previous_summaries + [summary], read.units)
    summary["closed"] = all(open_after.values())
    summary["open_units"] = [key for key, done in open_after.items() if not done]
    (directory / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return summary


def _closed_at(case: Path, state: int, summaries: list[dict[str, Any]]) -> str | None:
    """The git ref the state was last closed at, for `ask --since`: the commit
    that kept the latest closing round, or that held a carried closure's texts."""
    for summary in reversed(summaries):
        if str(summary.get("round", "")).startswith(CARRIED):
            return summary.get("ref") or "HEAD"
        if summary.get("closed"):
            ref = _added_at(case, rounds_dir(case, state) / summary["round"] / "summary.json")
            if ref:
                return ref
    return None


def status(case: Path, state: int, factory_root: Path | None = None) -> dict[str, Any]:
    """Whether the state is closed on its current texts, unit by unit."""
    rounds = _summaries(case, state)
    latest = rounds[-1] if rounds else None
    base = {"state": state, "round": latest["round"] if latest else None,
            "provider": latest.get("provider") if latest else None}
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
    done = units.closed(summaries, read.units)
    open_units = [key for key, value in done.items() if not value]
    changed = [key for key in open_units if units.closed_digest(summaries, key) is not None]
    return {
        **base,
        "closed": not open_units,
        "stale": stale,
        "carried": str(summaries[0].get("round", "")).startswith(CARRIED),
        "reason": ("every unit closed by two clear rounds on its current text" if not open_units
                   else f"{len(open_units)} of {len(done)} unit(s) open: {', '.join(open_units)}"),
        "open_units": open_units,
        "changed_units": changed,
        "units": len(done),
        "closed_at": _closed_at(case, state, summaries),
        "repeated": repeated,
    }


def _open_reason(summary: dict[str, Any]) -> str:
    if "judge" not in summary:
        return f"{summary['repeated_topics']} topic(s) raised by two or more reviews"
    if summary["blocking_topics"]:
        return f"{summary['blocking_topics']} blocking topic(s): contradiction, consequential gap or unverified judgement"
    return "one clear round; the state closes after a second clear round on the same texts"
