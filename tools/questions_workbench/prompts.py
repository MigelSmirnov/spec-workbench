"""The two instructions of a round: ask, then group what was asked."""
from __future__ import annotations

# The review instruction of a document state says three things (owner
# decision 2026-11-08, #147 comment 6721261089): what the layer decides, what
# changed, and what it receives. Lists of what not to ask were removed where
# the layer's scope already excludes it; they signalled an unclear boundary.
ASK = """You review State {state} of a design before the later states and the code are
written from it. Whatever it leaves open, later agents decide silently, each
differently. List every point where continuing from it forces a guess.

The points of State {state}:
{scope}
A contradiction requires incompatible obligations in the same admissible
history: obeying one breaks the other. Different levels of detail alone are
not a contradiction; what the texts carry on purpose to a later state is not.

A point may carry a witness: one history the texts allow — a state the product
can be in, the events in order with who acts, the two outcomes careful
implementers could both read from the texts (for a contradiction, the outcome
each passage gives), and who sees the difference. A point with a witness is
judged even when no other review raises it.

Output strict JSON, nothing else:
{{"open_points":[{{"subject":"<model, decision, action or section>","kind":"<short kind>","text":"<the exact phrase that is silent, vague or contradictory>","question":"<the question the texts must answer>","options":["<option you see>"],"default_guess":"<what you would do if forced>","witness":{{"initial":"<state>","events":["<who does what>"],"outcomes":["<outcome one>","<outcome two>"],"observer":"<who sees the difference>"}}}}]}}
"witness" may be omitted."""

UNIT_SCOPE = """

What changed. State {state} closes unit by unit; these units are under review,
the rest of it is closed. Each point names its "unit", exactly as listed; a
point about another unit is set aside.
{listing}"""


CHANGED_UNIT = """- {key}: {title} — changed since its latest review. Review this change and what
  it affects; a point on an unchanged passage away from it is set aside.
```diff
{diff}```"""


REFERENCING_UNIT = """- {key}: {title} — unchanged, but it names {names}, which changed (the diff is
  listed with {it}). Review only whether it still agrees with that change."""


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
decides differently? Report each contradiction with both passages
copied character for character from the prompt. Do not report what the prompt
leaves open, style, or designs you would prefer; the one other kind of point
is a violation of the standard, asked below.
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


MODULE_NOTES_ONLY = """

The rules below are the rules the module's notes are written by. The notes are
the requirement lines of the prompt, each `<function, Class.method or
module>: [CLASS] …`; they are the only text of the prompt authored in the
design. Every other passage — imports, contracts, model surfaces, the static
gate contract, the records built for this module and the closing generation
instructions — is the Factory's own text, the same for every module: never
report it as a standard_violation. A note that contradicts it is still a
contradiction."""


def module_ask_instruction(state: int, scope: str, diff: str | None = None,
                           obligations: list[str] | None = None,
                           sections: list[dict[str, str]] | None = None,
                           carried: list[dict] | None = None) -> str:
    instruction = MODULE_ASK.format(state=state, scope=scope)
    if sections:
        instruction += MODULE_NOTES_ONLY + standard_ask(sections, "the notes of the prompt")
    if obligations:
        instruction += MODULE_OBLIGATIONS.format(listing="\n".join(obligations))
    instruction += carried_context(carried)
    return instruction + (MODULE_CHANGE.format(diff=diff) if diff is not None else "")


MODULE_LAYER_JUDGE = """=== OBLIGATIONS THIS MODULE TAKES PART IN (deterministic results, not prompt text; never quote) ===

A topic about one of these is not judged answered unless the prompt carries it
out; these results say the design does not yet.
{listing}"""


MODULE_NOTES_JUDGE = """=== THIS MODULE'S NOTES (the design text of the prompt) ===

Only these lines of the prompt are notes, authored in the case. Every other
passage of the prompt — its imports, contracts, model surfaces, the static gate
contract, the records built for the module and the closing instructions — is
the Factory's own text, written for every module. A rule of the SPEC_STANDARD
sections is a rule for these notes: a passage outside them is never a
standard_violation (it is checked: such a judgement is recorded as the
generator's text and asks nothing). A note that contradicts the Factory's text
is still a contradiction.
{listing}"""


def module_layer_judge(obligations: list[str], notes: list[str] | None = None,
                       carried: list[dict] | None = None) -> str | None:
    blocks = []
    if obligations:
        blocks.append(MODULE_LAYER_JUDGE.format(listing="\n".join(obligations)))
    if notes is not None:
        blocks.append(MODULE_NOTES_JUDGE.format(listing="\n".join(notes) or "(none)"))
    if carried:
        blocks.append(carried_context(carried))
    return "\n\n".join(blocks) or None


def notes_in_prompt(notes: list[str], prompt: str) -> list[str]:
    """The specification's notes the prompt carries, in specification order: the
    module's notes as its generator reads them. Found as text, whitespace and
    code marks aside (judge._norm), so no section header of the Factory's
    prompt is relied on."""
    from .judge import _norm

    body = _norm(prompt)
    return [note for note in notes if _norm(note) and _norm(note) in body]


def module_input(module: str, prompt: str) -> str:
    return f"=== the Factory's prompt for generating `{module}` ===\n\n{prompt}"


GROUP = """You receive the open points of several independent reviews of the same
design texts. Group the points that ask about the same missing decision, even
when worded differently. A point belongs to exactly one group; a point unlike any
other is a group of its own.

Output strict JSON, nothing else:
{"groups":[{"topic":"<one line naming the missing decision>","members":["<point id>"]}]}"""


def ask_instruction(state: int, scope: str, sections: list[dict[str, str]] | None = None) -> str:
    from . import documents

    boundary = REVIEW_BOUNDARY if documents.gap_needs_requirement(state) else ""
    return ASK.format(state=state, scope=scope) + boundary + standard_ask(sections, "the texts of State {state}".format(state=state))


REVIEW_BOUNDARY = """

Keep the broad task: notice where the generator will have to choose. Separate
a missing decision of this stage from a choice owned by a later layer. For a
later-layer question, name its owner in "decision_owner" (a later state number,
generation, factory_checks or deploy), give the options, their consequences
in "consequences", and the already accepted requirement every option must
preserve, quoted verbatim in "requirement". Do not demand its implementation
here. If no such requirement exists, say so; do not invent one.
State 2 owns required results, refusals, invariants and constraints, including
precedence when it expresses a required guarantee. It does not own every
order of steps or the mechanism by which a test or deployment proves a rule.
State 5 owns obligations between modules: what callers supply and may rely
on in results, failures and effects. Exact contract forms, serialization and
hidden procedures belong to later layers unless they express an already
required boundary guarantee. Technical vocabulary alone decides no owner.
If a product choice is missing, report its question, options and consequences
for the owner instead of presuming that both outcomes are permitted.
"""


# The rules a state is written by are SPEC_STANDARD's own sections, the ones
# its phase lists in `docs` (authoring_sequence.json), given verbatim (owner
# decision 2026-11-08, #147 comment 6724353913): the reviewer quotes the rule
# it finds broken, the judge finds both quotes mechanically. No list of our own.
STANDARD_ASK = """

Violations of the standard. {Reviewed} must be written by the rules of the
SPEC_STANDARD sections below, given verbatim — the sections this state lists
as its rules. List also every passage of {reviewed} that breaks a rule of
these sections, as a point of kind "standard_violation": in "text" copy the
passage verbatim from {reviewed}; in "rule" copy, verbatim from the sections
below, the rule it breaks (at least a full clause, without ellipsis); in
"section" give that section's number; in "question" say what the passage must
become. Both quotes are checked mechanically. Report only a rule these
sections state; not a rule you would add. Such a point, in the same
"open_points" list:
{{"subject":"<function, note, unit or section>","kind":"standard_violation","text":"<the passage, verbatim>","rule":"<the rule, verbatim from the sections below>","section":"<its number>","question":"<what the passage must become>"}}

{sections}"""


def standard_text(sections: list[dict[str, str]] | None) -> str:
    """The sections as given to a reviewer and the judge: each headed by its
    number and why the phase lists it, then its text verbatim."""
    return "\n\n".join(f"=== SPEC_STANDARD {s['title']} — {s['why']} ===\n\n{s['text']}"
                        for s in sections or [])


def standard_ask(sections: list[dict[str, str]] | None, reviewed: str) -> str:
    if not sections:
        return ""
    return STANDARD_ASK.format(reviewed=reviewed, Reviewed=reviewed[:1].upper() + reviewed[1:],
                               sections=standard_text(sections))


def ask_input(documents: list[tuple[int, str, str]]) -> str:
    return "\n\n".join(f"=== {name} (State {state}) ===\n\n{text}" for state, name, text in documents)

JUDGE = """You judge the topics that several independent reviews of the same design
texts raised about State {state}. A review always finds one more question; your
task is to tell the questions that must change the texts before the next state
from those that need not.{scope_rule} Judge each topic by exactly one kind:

- "contradiction": two obligations are incompatible in the same admissible
  history: obeying one breaks the other. Mere difference in detail is not
  enough. Quote both verbatim and explain the incompatibility in "why".
  {contradiction_extra}{standard_kind}
{gap_kind} Quote, verbatim, every passage of the texts that
  leaves the choice open or bears on it. {unquoted_gap}{witness_rule}
- "answered": the texts already answer the question. Quote the passage that
  answers it, verbatim.
{later_state}{indifferent_kind}{preexisting}{answered_later}{judged_before}

Quotes are checked mechanically against the texts: copy them character for
character, without ellipsis, at least a full clause. A quote not found in the
texts counts against your judgement, so never paraphrase. {unsure_rule}{requirement_order}{state_files}

Output strict JSON, nothing else:
{{"judgements":[{{"id":"<topic id>","kind":"<kind>","quotes":["<verbatim passage>"],"later_state":<number or null>,"precedent":"<prior judgement id or null>","divergence":"<two behaviours and who notices, or empty>","why":"<one sentence>"{requirement_schema}{witness_schema}{standard_schema}}}]}}"""

GAP_NOTICED = """- "consequential_gap": the texts leave a choice open, and two careful
  implementers would build different behaviour that the owner, an agent, a
  caller or an external service would notice. Name the two behaviours and who
  notices in "divergence"."""

INDIFFERENT_NOTICED = """- "indifferent": any answer is acceptable, because no caller, owner or service
  acts differently on the difference. Say why in "why"."""

GAP_REQUIREMENT = """- "consequential_gap": the choice belongs to State {state}, and an outcome
  breaks an accepted requirement. Quote that promise, invariant, constraint
  or boundary obligation verbatim in "requirement". In "divergence", explain
  which outcome violates it; an observer of a difference is not sufficient."""

INDIFFERENT_REQUIREMENT = """- "indifferent": both outcomes are permitted by the accepted obligations.
  Explain why in "why"; absence of a requirement quote alone does not establish
  freedom or resolve a missing product decision."""

REQUIREMENT_ORDER = """

For a topic that is not a contradiction or a standard violation, judge in
this strict order:
1. Establish the decision owner from the phase's purpose, question_scope and
   layer obligations. Record it in "decision_owner". Importance does not make
   a question belong to the current stage. Use the semantic obligation, not
   a blacklist of words: authorization or refusal precedence may be a required
   result even though it names an order.
2. If it belongs to State {state}, establish whether its outcomes must be
   distinguished: consequential_gap needs the quoted requirement and an
   explanation of which outcome breaks it. If both outcomes are allowed,
   indifferent. Do not require all implementation choices to be settled here.
3. If a necessary choice belongs later, use later_state, with its receiving
   state number or generation/factory_checks/deploy in "later_state". Preserve
   the options, consequences and any accepted guarantee in "requirement";
   without a guarantee explain why the later layer still needs to decide it.
4. If the product decision itself is absent, use hypothesis with
   "owner_question": the question to the product owner, options and
   consequences. Do not invent a requirement, classify the silence as
   indifferent, or automatically defer it to contracts or deployment.
A gap without its requirement remains an unresolved hypothesis for the author,
not evidence of permitted freedom. A missing or invalid quote never proves a
topic harmless. Contradictions and standard violations keep their own rules.
"""

REQUIREMENT_SCHEMA = ',"decision_owner":"<owning state number or named layer>","requirement":"<accepted obligation, verbatim, or empty>","options":["<option>","<alternative>"],"consequences":["<consequence>"],"owner_question":"<missing product decision to ask the owner, or empty>"'

LATER_REQUIREMENT = """- "later_state": the decision belongs to a later layer. Set "later_state"
  to a later state number (through 8), or generation, factory_checks, deploy.
  Preserve the options and consequences, and quote in "requirement" any
  already accepted obligation all implementations must preserve. Never use
  this to carry away an undecided guarantee of the current stage.
"""

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

Hypotheses of the previous round, raised without a witness. Raise one again
only with a witness.
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

STANDARD_KIND = """
- "standard_violation": a passage of the texts breaks a rule of the
  SPEC_STANDARD sections given below (the rules of this state). Quote the
  passage verbatim in "quotes", copy the rule verbatim from those sections in
  "rule", and give its section number in "section". Judge it only on a rule
  the sections state; a passage the rule does not reach is another kind. It
  blocks like a contradiction."""

STANDARD_SCHEMA = ',"rule":"<the rule, verbatim from the SPEC_STANDARD sections, or empty>","section":"<its number, or empty>"'


# The last state a gap without a passage is deferred from (judge.LAST_DEFERRING_STATE).
LAST_DEFERRING_STATE = 5
LAST_DESIGN_STATE = 7


def judge_instruction(state: int, reopened: bool, later_files: list[str] | None = None,
                      precedents: bool = False, scope: str | None = None, witness: bool = False,
                      state_files: list[str] | None = None, closed_files: list[str] | None = None,
                      standard: bool = False, requirement: bool = False) -> str:
    """`standard`: the round gives the state's SPEC_STANDARD sections, and a
    passage that breaks one of their rules is judged a standard_violation.
    `witness`: a blocking kind needs a witness and a contradiction its
    bases (document states; State 7 keeps its own rule). `state_files`: the
    judge reads the round text as files and gets only the topics' units and
    passages inline (judge_context.py); `closed_files`, the texts a reopened
    state was closed with, likewise."""
    answered_later = ANSWERED_LATER.format(files=", ".join(later_files), state=state) if later_files else ""
    unquoted_gap = ("Do not infer a later-layer mechanism from silence alone." if requirement else
                    DEFERRED_GAP if state <= LAST_DEFERRING_STATE else ANSWERING_STATE_GAP.format(state=state))
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
                        later_state=(LATER_REQUIREMENT if requirement else LATER_STATE.format(state=state)) if state < LAST_DESIGN_STATE else "",
                        scope_rule=scope_rule, contradiction_extra=bases,
                        witness_rule=WITNESS_RULE if witness else "",
                        unsure_rule=UNSURE_WITNESS if witness else UNSURE_BLOCKING,
                        gap_kind=GAP_REQUIREMENT.format(state=state) if requirement else GAP_NOTICED,
                        indifferent_kind=INDIFFERENT_REQUIREMENT if requirement else INDIFFERENT_NOTICED,
                        requirement_order=REQUIREMENT_ORDER.format(state=state) if requirement else "",
                        requirement_schema=REQUIREMENT_SCHEMA if requirement else "",
                        witness_schema=WITNESS_SCHEMA if witness else "", state_files=files,
                        standard_kind=STANDARD_KIND if standard else "",
                        standard_schema=STANDARD_SCHEMA if standard else "")


def judge_input(texts: str, topics: list[dict], change: str | None, precedents: list[dict] | None = None,
                layer: str | None = None, standard: str | None = None) -> str:
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
    if standard:
        parts.append("=== THE RULES OF THIS STATE: SPEC_STANDARD SECTIONS, VERBATIM (not design text; "
                     f"a rule is quoted from here) ===\n\n{standard}")
    parts.append(f"=== TOPICS TO JUDGE ===\n\n{listing}")
    return "\n\n".join(parts)


LAYER = """

What State {state} decides (it owns):
{owns}
What it receives from earlier states: the passages given below, verbatim, and
these obligations (result now):
{received}
What it carries further, decided there, not here:
{carries}
Deterministic results at its handoff. They are not design text: never quote
them; one not closed or carried is never a pass, and "not_checked" means an
input is missing:
{findings}
A choice written as "later" without being decided is a gap of this state."""


LAYER_JUDGE = """=== DETERMINISTIC RESULTS AT THIS TRANSITION (not design text; never quote) ===

A topic these results show open is not judged answered or indifferent, by
this state's texts or a later one's: the texts may say it, the check says it
does not hold.
{findings}{witness}"""

WITNESS_CARRIED_JUDGE = """

Of an invariant's test, this state answers only whether its Required tests item
says what must be shown. A topic asking which existing check an item is bound
to, or whether a bound check asserts it, is later_state 8: the binding and its
assertion are carried and judged per check after State 7, at the State 8
handoff."""

MAX_LAYER_LINES = 40


def carried_lines(carried: list[dict] | None) -> list[str]:
    return [f"- [carried by the author] {c['what']} (State {c['state']} {c['round']} {c['topic']})"
            + (f" Every option must preserve: {'; '.join(c['keeps'])}." if c.get("keeps") else "")
            + (f" Options: {c['options']}." if c.get("options") else "")
            + (f" Consequences: {c['consequences']}." if c.get("consequences") else "")
            for c in carried or []]


def carried_context(carried: list[dict] | None) -> str:
    if not carried:
        return ""
    return ("\n\nAuthor-carried choices received at this stage (context, not Factory prompt text). "
            "For each, establish whether this module participates; shared words do not establish that. "
            "Preserve the accepted guarantee when resolving the choice. These instructions do not add "
            "new kinds of State 7 findings; judge the module's prompt under its existing scope.\n"
            + "\n".join(carried_lines(carried)))


def _layer_lines(context: dict) -> tuple[str, str, str, str]:
    owns = "\n".join(f"- {item}" for item in context.get("owns") or []) or "- (nothing declared)"
    received = "\n".join([f"- [{r['outcome']}] {r['obligation']} (from {r['from']}, check {r['check']})"
                          for r in context.get("results") or []]
                         + carried_lines(context.get("carried_in"))) or "- (nothing)"
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
    listing = _verdicts(context, units)
    text = LAYER_JUDGE.format(findings=_layer_lines(context)[3],
                              witness="" if listing or context.get("state", 0) >= LAST_DESIGN_STATE
                              else WITNESS_CARRIED_JUDGE)
    reopened = context.get("evidence_reopened") or []
    note = EVIDENCE_REOPENED_JUDGE.format(units=", ".join(reopened)) if reopened else ""
    return text + (VERDICTS.format(listing=listing) if listing else "") + note


EVIDENCE_REOPENED_JUDGE = """

Reopened because their evidence changed: {units}. Their text did not change,
but a check their bindings name did. Judge whether each binding still asserts
its invariants on the verdicts above; no earlier judgement of these units is
offered as a precedent, and an earlier "answered" stood on other evidence."""
