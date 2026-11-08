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

When you can, give the point a witness: one history the texts allow — a
state the product can be in, the events in order with who acts, and the two
outcomes careful implementers could both read from the texts (or, for a
contradiction, the outcome each passage gives) and who would see the
difference. A point with a witness is judged even when no other review raises
it; a point without one is judged only when several reviews raise it.

Output strict JSON, nothing else:
{{"open_points":[{{"subject":"<model, decision, action or section>","kind":"<short kind>","text":"<the exact phrase that is silent, vague or contradictory>","question":"<the question the texts must answer>","options":["<option you see>"],"default_guess":"<what you would do if forced>","witness":{{"initial":"<state>","events":["<who does what>"],"outcomes":["<outcome one>","<outcome two>"],"observer":"<who sees the difference>"}}}}]}}
"witness" may be omitted."""

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


REFERENCING_UNIT = """- {key}: {title}
  This unit was closed and has not changed, but it names {names}, which
  changed since its closure (the diff is listed with {it}). Review only
  whether this unit still agrees with that change — a rule here that the
  change contradicts or leaves without its exception. Its other passages are
  closed; a point about one of them, away from what the change touches, is
  not asked for."""


def unit_scope(state: int, scope: list[tuple[str, str]], changed: dict[str, str] | None = None,
               referencing: dict[str, list[str]] | None = None) -> str:
    changed, referencing = changed or {}, referencing or {}

    def line(key: str, title: str) -> str:
        if key in changed:
            return CHANGED_UNIT.format(key=key, title=title, diff=changed[key])
        if key in referencing:
            names = referencing[key]
            return REFERENCING_UNIT.format(key=key, title=title, names=", ".join(names),
                                           it="it" if len(names) == 1 else "them")
        return f"- {key}: {title}"
    listing = "\n".join(line(key, title) for key, title in scope)
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


MODULE_OBLIGATIONS = """

Obligations this module's code takes part in, received from earlier states
(skills/spec-authoring/TRANSITION_PROTOCOL.md). They are deterministic results,
not part of the prompt: never quote them. For each one that concerns code this
module writes, check whether the prompt carries it out. When it does not,
report a point of kind "unmet_obligation": in "text" copy, verbatim from the
prompt, the contract or note of the function that should carry it, and in
"question" say what the note must state.
{listing}"""


def module_ask_instruction(state: int, scope: str, diff: str | None = None,
                           obligations: list[str] | None = None) -> str:
    instruction = MODULE_ASK.format(state=state, scope=scope)
    if obligations:
        instruction += MODULE_OBLIGATIONS.format(listing="\n".join(obligations))
    return instruction + (MODULE_CHANGE.format(diff=diff) if diff is not None else "")


MODULE_LAYER_JUDGE = """=== OBLIGATIONS THIS MODULE TAKES PART IN (deterministic results, not prompt text; never quote) ===

A topic about one of these is not judged answered unless the prompt carries it
out; these results say the design does not yet.
{listing}"""


def module_layer_judge(obligations: list[str]) -> str | None:
    return MODULE_LAYER_JUDGE.format(listing="\n".join(obligations)) if obligations else None


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
  verbatim.{contradiction_extra}
- "consequential_gap": the texts leave a choice open, and two careful
  implementers would build different behaviour that the owner, an agent, a
  caller or an external service would notice. Name the two behaviours and who
  notices in "divergence". Quote, verbatim, every passage of the texts that
  leaves the choice open or bears on it. {unquoted_gap}{witness_rule}
- "answered": the texts already answer the question. Quote the passage that
  answers it, verbatim.
{later_state}- "indifferent": any answer is acceptable, because no caller, owner or service
  acts differently on the difference. Say why in "why".{preexisting}{answered_later}{judged_before}

Quotes are checked mechanically against the texts: copy them character for
character, without ellipsis, at least a full clause. A quote not found in the
texts counts against your judgement, so never paraphrase. {unsure_rule}{state_files}

Output strict JSON, nothing else:
{{"judgements":[{{"id":"<topic id>","kind":"<kind>","quotes":["<verbatim passage>"],"later_state":<number or null>,"precedent":"<prior judgement id or null>","divergence":"<two behaviours and who notices, or empty>","why":"<one sentence>"{witness_schema}}}]}}"""

UNSURE_BLOCKING = """When unsure between a
blocking kind (contradiction, consequential_gap) and another, choose the
blocking one."""

UNSURE_WITNESS = """When unsure between a
blocking kind (contradiction, consequential_gap) and another, choose the
blocking one if you can give its witness; if you cannot, judge it a
hypothesis."""

WITNESS_RULE = """

A contradiction or a consequential_gap that quotes a passage blocks only with
a witness: one admissible history in which the texts give two different
outcomes. Give it in "witness": "initial" — a state the product can be in;
"events" — the actions in order, each with who does it; "outcomes" — the two
outcomes the texts allow (for a contradiction, the outcome each passage
gives); "observer" — who sees the difference; "basis" — passages of the
texts, verbatim, that make the history admissible (that these actions exist
and these actors may take them). A reviewer's witness, when the topic carries
one, is a draft to check, not evidence.
- "hypothesis": the reviews suspect a contradiction or a gap, but you cannot
  build a witness from the texts. Say what is missing in "why". It does not
  block; the next round's reviewers are asked for a witness."""

CONTRADICTION_BASES = """ In "bases", for each of the two passages, quote
  verbatim the passage of an earlier state (State 0 to State {before}) it rests
  on, or give "" when it rests on none: the side that rests on no earlier
  passage is usually the one to change."""

WITNESS_SCHEMA = ',"witness":{"initial":"","events":[""],"outcomes":["",""],"observer":"","basis":["<verbatim passage>"]},"bases":[{"passage":"<one side, verbatim>","rests_on":"<earlier-state passage, verbatim, or empty>"}]'

HYPOTHESES = """

Hypotheses of the previous round. These were raised without a witness and did
not block. Raise one again only with a witness (a history in which the texts
give two different outcomes); without one, do not repeat it.
{listing}"""


def hypotheses_note(hypotheses: list[tuple[str, str]]) -> str:
    """The previous round's hypotheses, put to this round's reviewers."""
    if not hypotheses:
        return ""
    return HYPOTHESES.format(listing="\n".join(f"- {topic} ({why})" if why else f"- {topic}"
                                               for topic, why in hypotheses))

STATE_FILES = """

What you are given. The text below is not the whole of States 0 to {state}:
it gives the units of State {state} the topics concern{change}, the units
holding a passage the reviews quote, and the earlier-state passages the topics
name. The full texts of States 0 to {state} are the files {files} in your
working directory. Search them (by the names, ids, fields and operations a
topic is about) before you judge: whether a passage the reviews did not quote
answers the topic, contradicts one they did, or makes it a question of
another state (answered, answered_later, a gap quoting only another state,
a contradiction). Quote from those files verbatim: every quote is checked
against the full texts."""

PREEXISTING_FILES = """
- "preexisting": only for a state reopened after it was closed. The texts it was
  closed with are the files {closed}; the change since, of each unit the topics
  concern, is given below with that unit. The topic concerns a passage the
  change did not touch and the change did not make it matter. Quote that
  passage verbatim; it must appear unchanged in both versions."""


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
                      precedents: bool = False, scope: str | None = None, witness: bool = False,
                      state_files: list[str] | None = None, closed_files: list[str] | None = None) -> str:
    """`witness`: a blocking kind needs a witness and a contradiction its
    bases (document states; State 7 keeps its own rule). `state_files`: the
    judge reads the round text as files and gets only the topics' units and
    passages inline (judge_context.py); `closed_files`, the texts a reopened
    state was closed with, likewise."""
    answered_later = ANSWERED_LATER.format(files=", ".join(later_files), state=state) if later_files else ""
    unquoted_gap = DEFERRED_GAP if state <= LAST_DEFERRING_STATE else ANSWERING_STATE_GAP.format(state=state)
    scope_rule = SCOPE_RULE.format(state=state, scope=scope) if scope else ""
    bases = CONTRADICTION_BASES.format(before=state - 1) if witness and state > 0 else ""
    preexisting = ""
    if reopened:
        preexisting = (PREEXISTING_FILES.format(closed=", ".join(closed_files)) if state_files and closed_files
                       else PREEXISTING)
    files = (STATE_FILES.format(state=state, files=", ".join(state_files),
                                change=", each with its change since the state was closed" if reopened else "")
             if state_files else "")
    return JUDGE.format(state=state, preexisting=preexisting, answered_later=answered_later,
                        judged_before=JUDGED_BEFORE if precedents else "", unquoted_gap=unquoted_gap,
                        later_state=LATER_STATE.format(state=state) if state < LAST_DESIGN_STATE else "",
                        scope_rule=scope_rule, contradiction_extra=bases,
                        witness_rule=WITNESS_RULE if witness else "",
                        unsure_rule=UNSURE_WITNESS if witness else UNSURE_BLOCKING,
                        witness_schema=WITNESS_SCHEMA if witness else "", state_files=files)


def judge_input(texts: str, topics: list[dict], change: str | None, precedents: list[dict] | None = None,
                layer: str | None = None) -> str:
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
    if layer:
        parts.append(layer)
    parts.append(f"=== TOPICS TO JUDGE ===\n\n{listing}")
    return "\n\n".join(parts)


LAYER = """

The transition of State {state} (skills/spec-authoring/TRANSITION_PROTOCOL.md).
Within the scope above, ask the protocol's five questions of the units under
review: are the inputs this state needs available; are the decisions it owns
made; can each be written in the standard; did the obligations earlier states
carried here close; and is every obligation it carries further a decided
execution with a receiving state and a check, never an open choice written as
"later". A choice deferred without being decided is a gap of this state.

This state owns:
{owns}
It received from earlier states (result now):
{received}
It carries further:
{carries}
Deterministic results now. They are not design text: never quote them. A point
they already state need not be raised, and no point may take a result that is
not closed or carried for a pass; "not_checked" means an input is missing:
{findings}

Ask about an earlier state only whether this state fulfils what it carried
here; its closed units are not audited again. A decision's "[witness: ...]" tag
binds an invariant to an existing check: it is not the history you give as a
point's witness. Whether a Required tests item says what would show the
invariant holds is a point of the state that owns the invariant. Unless
verdicts are listed below, whether a bound check asserts what its item names
is not a point of this round: it is judged per check after State 7, where the
witnesses are written, at the State 8 handoff."""


LAYER_JUDGE = """=== DETERMINISTIC RESULTS AT THIS TRANSITION (not design text; never quote) ===

A topic these results show open is not judged answered or indifferent, by
this state's texts or a later one's: the texts may say it, the check says it
does not hold.
{findings}"""

MAX_LAYER_LINES = 40


def _layer_lines(context: dict) -> tuple[str, str, str, str]:
    owns = "\n".join(f"- {item}" for item in context.get("owns") or []) or "- (nothing declared)"
    received = "\n".join(f"- [{r['outcome']}] {r['obligation']} (from {r['from']}, check {r['check']})"
                         for r in context.get("results") or []) or "- (nothing)"
    carries = "\n".join(f"- {c.get('obligation', '')} -> {c.get('to')} (confirmed by {c.get('check')})"
                        for c in context.get("carries") or []) or "- (nothing)"
    lines = [f"- [{r['outcome']}] {f.get('code')}: {f.get('message', '')}"
             for r in context.get("results") or [] if r["outcome"] not in ("closed", "carried")
             for f in r.get("findings") or []]
    lines += [f"- [gate] {f.get('code')}: {f.get('message', '')}" for f in context.get("gate_findings") or []]
    if len(lines) > MAX_LAYER_LINES:
        lines = lines[:MAX_LAYER_LINES] + [f"- … {len(lines) - MAX_LAYER_LINES} more"]
    return owns, received, carries, "\n".join(lines) or "- (none)"


VERDICTS = """

Verdicts on the bindings of the units under review. Each "[witness: ...]" tag
binds a Factory check to the invariants its item names; whether the check
asserts them is judged once per check, outside this round, and kept by the
digest of the check's files and bound items. These verdicts are not design
text: never quote them. A binding whose check does not assert, or asserts only
in part, what its item names claims what the check does not show: raise a point
on the decision's unit, quoting the Required tests item. A binding not checked
has no verdict: say so, and never treat it as sufficient.
{listing}"""


def _verdicts(context: dict, units: list[str] | None) -> str:
    rows = []
    for row in context.get("verdicts") or []:
        if units is not None and row["decision"] not in units:
            continue
        head = (f"- {row['decision']} binds {', '.join(row['invariants']) or 'its invariant'} to {row['witness']} "
                f"(check {row['digest'][:12]}): ")
        if row["outcome"] == "not_checked":
            rows.append(head + f"NOT CHECKED: {row.get('reason')}")
        else:
            rows.append(head + row["outcome"].upper().replace("_", " ") + (f" — {row['why']}" if row.get("why") else ""))
    return "\n".join(rows)


def layer_scope(context: dict | None, units: list[str] | None = None) -> str:
    """The transition block of a document round's instruction; "" without a context.
    `units`: the units under review, which the bindings' evidence is limited to."""
    if not context:
        return ""
    owns, received, carries, findings = _layer_lines(context)
    text = LAYER.format(state=context["state"], owns=owns, received=received, carries=carries, findings=findings)
    listing = _verdicts(context, units)
    reopened = context.get("evidence_reopened") or []
    note = EVIDENCE_REOPENED.format(units=", ".join(reopened)) if reopened else ""
    return text + (VERDICTS.format(listing=listing) if listing else "") + note


EVIDENCE_REOPENED = """

Units closed on their text whose evidence changed: {units}. The checks their
bindings name changed since they were closed (a file, a command or a digest),
while their text did not. Review them only for whether each binding still
asserts the invariants its item names on the verdicts above; their text is
closed otherwise."""


def layer_judge(context: dict | None, units: list[str] | None = None) -> str | None:
    if not context:
        return None
    text = LAYER_JUDGE.format(findings=_layer_lines(context)[3])
    listing = _verdicts(context, units)
    reopened = context.get("evidence_reopened") or []
    note = EVIDENCE_REOPENED_JUDGE.format(units=", ".join(reopened)) if reopened else ""
    return text + (VERDICTS.format(listing=listing) if listing else "") + note


EVIDENCE_REOPENED_JUDGE = """

Reopened because their evidence changed: {units}. Their text did not change,
but a check their bindings name did. Judge whether each binding still asserts
its invariants on the verdicts above; no earlier judgement of these units is
offered as a precedent, and an earlier "answered" stood on other evidence."""
