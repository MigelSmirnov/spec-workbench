"""The two instructions of a round: ask, then group what was asked."""
from __future__ import annotations

ASK = """You review a design BEFORE the next states, modules and code exist.
You receive the accepted design texts up to State {state}. Later, other agents will
write the next states and the code from these texts alone; whatever the texts leave
open, they will decide silently, and different agents will decide differently.

List every point where continuing from these texts would force a guess.

Scope of State {state} — report a point only if it belongs here:
{scope}

Two texts that contradict each other always belong here. Points the texts list on
purpose as carried to a later state do not.

Do not propose designs as settled. Report only genuine gaps, not style.
Output strict JSON, nothing else:
{{"open_points":[{{"subject":"<model, decision, action or section>","kind":"<short kind>","text":"<the exact phrase that is silent, vague or contradictory>","question":"<the question the texts must answer>","options":["<option you see>"],"default_guess":"<what you would do if forced>"}}]}}"""

UNIT_SCOPE = """

Units under review. State {state} closes unit by unit: the units listed below are
not closed yet, and every other part of State {state} is closed. Report points only
about these units — a gap in one of them, or a contradiction between one of them
and any other text. Every point carries one more member, "unit": the key of the
unit it is about, exactly as listed. A point about anything else is not asked for
and is set aside.

{listing}"""


CHANGED_UNIT = """- {key}: {title}
  This unit was closed and has changed since. Review only this change and what
  it affects — a gap the change opens, or a contradiction it makes with any
  text. Its unchanged passages were closed; a point about one of them, away
  from the change, is set aside.
```diff
{diff}```"""


def unit_scope(state: int, scope: list[tuple[str, str]], changed: dict[str, str] | None = None) -> str:
    changed = changed or {}
    listing = "\n".join(CHANGED_UNIT.format(key=key, title=title, diff=changed[key]) if key in changed
                        else f"- {key}: {title}" for key, title in scope)
    return UNIT_SCOPE.format(state=state, listing=listing)



MODULE_ASK = """You are the model that will generate the module below. You receive exactly
the prompt the Factory will give you to generate it: its imports, its contracts,
the contracts and constants it may use, its models and its notes. You will
write the module from this prompt alone.

List every place where this prompt contradicts itself — where you could not
obey one passage without breaking another:

{scope}

Read the prompt as the code you would write from it: for every function you
must define, does any note allow or require what the IMPORTS list, a contract,
a model's fields or a constant do not hold, or what another note forbids or
decides differently? Report only such contradictions, each with both passages
copied character for character from the prompt. Do not report what the prompt
leaves open, style, or designs you would prefer.
Output strict JSON, nothing else:
{{"open_points":[{{"subject":"<function, class, note or section of the prompt>","kind":"contradiction","text":"<the first passage, verbatim>","other_text":"<the passage it contradicts, verbatim>","question":"<which of the two must change, or how they are reconciled>"}}]}}"""


MODULE_CHANGE = """

This prompt was reviewed and closed before, and has changed since. Review only
this change and what it affects — a guess the change forces, or a contradiction
it makes with any other part of the prompt. The unchanged passages were closed;
a point about one of them, away from the change, is set aside.
```diff
{diff}```"""


def module_ask_instruction(state: int, scope: str, diff: str | None = None) -> str:
    instruction = MODULE_ASK.format(state=state, scope=scope)
    return instruction + (MODULE_CHANGE.format(diff=diff) if diff is not None else "")


def module_input(module: str, prompt: str) -> str:
    return f"=== the Factory's prompt for generating `{module}` ===\n\n{prompt}"


GROUP = """You receive the open points of several independent reviews of the same
design texts. Group the points that ask about the same missing decision, even
when worded differently. A point belongs to exactly one group; a point unlike any
other is a group of its own.

Output strict JSON, nothing else:
{"groups":[{"topic":"<one line naming the missing decision>","members":["<point id>"]}]}"""


def ask_instruction(state: int, scope: str) -> str:
    return ASK.format(state=state, scope=scope)


def ask_input(documents: list[tuple[int, str, str]]) -> str:
    return "\n\n".join(f"=== {name} (State {state}) ===\n\n{text}" for state, name, text in documents)

JUDGE = """You judge the topics that several independent reviews of the same design
texts raised about State {state}. A review always finds one more question; your
task is to tell the questions that must change the texts before the next state
from those that need not.{scope_rule} Judge each topic by exactly one kind:

- "contradiction": two passages of the texts say different things. Quote both,
  verbatim.
- "consequential_gap": the texts leave a choice open, and two careful
  implementers would build different behaviour that the owner, an agent, a
  caller or an external service would notice. Name the two behaviours and who
  notices in "divergence". Quote, verbatim, every passage of the texts that
  leaves the choice open or bears on it. {unquoted_gap}
- "answered": the texts already answer the question. Quote the passage that
  answers it, verbatim.
{later_state}- "indifferent": any answer is acceptable, because no caller, owner or service
  acts differently on the difference. Say why in "why".{preexisting}{answered_later}{judged_before}

Quotes are checked mechanically against the texts: copy them character for
character, without ellipsis, at least a full clause. A quote not found in the
texts counts against your judgement, so never paraphrase. When unsure between a
blocking kind (contradiction, consequential_gap) and another, choose the
blocking one.

Output strict JSON, nothing else:
{{"judgements":[{{"id":"<topic id>","kind":"<kind>","quotes":["<verbatim passage>"],"later_state":<number or null>,"precedent":"<prior judgement id or null>","divergence":"<two behaviours and who notices, or empty>","why":"<one sentence>"}}]}}"""

PREEXISTING = """
- "preexisting": only for a state reopened after it was closed. The texts it was
  closed with, and the change since, are given below. The topic concerns a
  passage the change did not touch and the change did not make it matter. Quote
  that passage verbatim; it must appear unchanged in both versions."""


ANSWERED_LATER = """
- "answered_later": a later state's text already decides it, so the generator,
  which reads that text too, does not guess. The later states' texts are the
  files {files}; search them (by the names, fields and operations the topic
  is about) before you judge a topic a consequential_gap. Quote the deciding
  passage verbatim from those files. Never for a contradiction: two passages up
  to State {state} that disagree are not reconciled by a later text."""


JUDGED_BEFORE = """
- "judged_before": the topic asks the same question as one of the PRIOR
  JUDGEMENTS below — non-blocking judgements of this state's latest rounds —
  and neither the change since nor the passages that judgement quotes changed
  it. Name that judgement's id in "precedent". The same question on the same
  texts deserves the same answer: prefer this to judging such a topic afresh,
  and judge afresh only when the texts the topic is about have changed."""


DEFERRED_GAP = """A gap with no passage at all — the
  texts never speak to the matter — is recorded for State 6 contracts or
  State 7 notes instead of blocking, so quote whenever a passage exists."""

ANSWERING_STATE_GAP = """A gap with no passage at all — the
  texts never speak to the matter — blocks too: State {state} is where it must
  be answered. Quote whenever a passage exists."""

LATER_STATE = """- "later_state": the question belongs to a later state — it is outside the
  scope of State {state} given above (rules and their required tests, module
  ownership, flows, operations, orders of checks, encodings, formats, schemas,
  signatures, field types and notes each have their own later state). Name
  that state's number in "later_state". Never for a contradiction.
"""

SCOPE_RULE = """

The scope of State {state} — the stop rule its reviewers were given, and the
only questions State {state} must answer:
{scope}

A topic outside this scope does not keep State {state} open, however real the
gap: it belongs to the later state that owns it, and that state's own round
asks it there."""

# The last state a gap without a passage is deferred from (judge.LAST_DEFERRING_STATE).
LAST_DEFERRING_STATE = 5
LAST_DESIGN_STATE = 7


def judge_instruction(state: int, reopened: bool, later_files: list[str] | None = None,
                      precedents: bool = False, scope: str | None = None) -> str:
    answered_later = ANSWERED_LATER.format(files=", ".join(later_files), state=state) if later_files else ""
    unquoted_gap = DEFERRED_GAP if state <= LAST_DEFERRING_STATE else ANSWERING_STATE_GAP.format(state=state)
    scope_rule = SCOPE_RULE.format(state=state, scope=scope) if scope else ""
    return JUDGE.format(state=state, preexisting=PREEXISTING if reopened else "", answered_later=answered_later,
                        judged_before=JUDGED_BEFORE if precedents else "", unquoted_gap=unquoted_gap,
                        later_state=LATER_STATE.format(state=state) if state < LAST_DESIGN_STATE else "",
                        scope_rule=scope_rule)


def judge_input(texts: str, topics: list[dict], change: str | None, precedents: list[dict] | None = None) -> str:
    listing = "\n\n".join(
        f"{t['id']}: {t['topic']}\n" + "\n".join(f"  - {p}" for p in t["points"]) for t in topics
    )
    parts = [texts]
    if change is not None:
        parts.append(f"=== CHANGE SINCE THE STATE WAS CLOSED (unified diff) ===\n\n{change or '(no change)'}")
    if precedents:
        prior = "\n\n".join(
            f"{p['id']} ({p['round']}, {p['kind']}): {p['topic']}\n"
            + "\n".join(f"  quote: {q}" for q in p["quotes"])
            + (f"\n  why: {p['why']}" if p.get("why") else "")
            for p in precedents
        )
        parts.append(f"=== PRIOR JUDGEMENTS (non-blocking, verified) ===\n\n{prior}")
    parts.append(f"=== TOPICS TO JUDGE ===\n\n{listing}")
    return "\n\n".join(parts)
