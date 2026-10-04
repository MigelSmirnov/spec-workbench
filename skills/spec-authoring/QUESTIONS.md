# Questions before generation

A design state is closed when the model that will generate from it has nothing
left to guess about what that state decides. Gates check the form of a text; they
cannot see a decision nobody made. This method asks instead.

## Why the generator's own model

Cabinet Flow's build passed every gate and linker check while no end-to-end path
worked; three quarters of the audited defects were decisions nobody had made, and
ten generations of one module passed the gates with ten different meanings
(Factory `docs/CABINET_FLOW_SPEC_AUDIT_20260927.md`). Asked before generation,
the same model named 86% of those decisions, most in every run, and often wrote
down the very wrong value it later generated. Its open questions are the choices
it would otherwise make silently.

## A round

```bash
python tools/design_questions.py ask examples/<case> --state <N>
python tools/design_questions.py status examples/<case> --state <N>
```

`ask` gives the texts of States 0..N to several independent reviews (three by
default) with the state's `question_scope` from `authoring_sequence.json`, then
groups their open points into topics, and has every topic raised by two or more
reviews judged (below). The round is kept under
`examples/<case>/questions/state<N>/round-<k>/`: each review, and `summary.json`
with the texts' digests, every topic, how many reviews raised it and, for a
repeated topic, its judgement.

### Another model through the Codex CLI

`--provider codex` asks through `codex exec` under the operator's ChatGPT login
instead of the Responses API, for when the API cannot be used. That login does
not serve the generator's model (`gpt-5.3-codex`), so the round asks another one
(`gpt-5.6-sol` by default, `--model` to choose) and records it as
`codex-cli:<model>:<reasoning>`; `status` names the provider of the latest round.
Such a round finds real gaps, but not necessarily the ones the generator would
guess at: before a state is handed to the Factory, close it again with the
generator's own model.

## Judging a repeated topic

Repetition says that reviews agree a question exists, not that it matters: a
review always finds one more question, one level deeper (Cabinet Kernel, States
1 and 2 reopened on 2026-10-03: three rounds each, 2–4 new repeated topics every
time, about texts nobody had changed). So a separate judge call sorts each
repeated topic into one kind, and only two kinds keep a state open:

| kind | means | evidence the tool checks | blocks |
|---|---|---|---|
| `contradiction` | two passages say different things | two quotes, verbatim in the texts | yes |
| `consequential_gap` | two careful implementers build different behaviour that the owner, an agent, a caller or a service notices | the two behaviours and who notices | yes |
| `answered` | the texts already answer it | the answering quote, verbatim in the texts | no |
| `answered_later` | only with `--provider codex`: a later state's text already decides it | the deciding quote, verbatim in the later states' texts | no |
| `later_state` | it belongs to a later state | a state number after this one | no |
| `indifferent` | no one acts differently on any answer | the reason | no |
| `preexisting` | only with `--since`: about a passage the change did not touch | the quote, verbatim in both versions | no |

### Topics a later state already decides

The reviews read States 0..N only, so a question whose answer was written
later — an encoding in a State 7 note, a field in a State 6 contract — comes
back as a gap every round. The generator reads those later texts too, so it does
not guess there. Cabinet Kernel State 2 ran 66 rounds without closing, its
points per review flat at 66–95; on 2026-10-04 its two blocking topics (the
`idempotency_key_fields` of a `read` binding, the Content-Type of a JSON body)
were both already decided in State 7 notes, and answering them again in State 2
would have contradicted one of them.

With `--provider codex` the judge therefore also gets the top-level documents of
the states after N, as files under `later/` of its otherwise empty, read-only
directory. It searches them instead of receiving them whole, so the context of a
State 2 judge grows by what it reads, not by ~40k tokens of contracts and notes;
the reviews are unchanged. Their digests are kept in the round's `judge` as
`later_documents`; the state's closure still compares only States 0..N. A judge
that cannot read files (the Responses API) is not offered `answered_later`.

The judge is not trusted: a judgement whose evidence fails its check — a quote
not found character for character, a "later" state that is not later — blocks
like a gap. Closing what blocks is the work below; a non-blocking topic is
recorded in the round and, for `later_state`, must reach that state's texts as
a carried question.

## Closing a question

Ask first who uses what the question is about.

1. **Nobody uses it** — remove the obligation, the fact or the model. Refining
   what nobody reads grows the design; this is where a kernel turns into a broker.
2. **The texts already answer it** — write the answer where the reader of that
   state will find it: a pointer that stays in another document is not an answer.
3. **Nothing answers it** — add it as data or as a decision of the owning state,
   or, when it is a product choice, bring it to the owner with the options the
   review listed and a recommendation. Record the owner's answer as the owner's;
   a recommendation the owner has not confirmed is not a decision.

## When a state is closed

- **Stop rule.** A question belongs to a state only as its `question_scope`
  says. A question of a later state is recorded in the texts as carried to that
  state and is closed there; without this rule reviews descend forever into
  orders, encodings and formats.
- **Clear round.** No judged topic blocks.
- **Closure.** The two latest rounds are clear on the same texts, and the texts
  have not changed since (`status` compares digests). One clear round can be
  luck; two on the same texts show the questions have stopped mattering, not
  merely changed. A topic raised by one review is closed or carried when cheap,
  but does not hold the state open. Rounds kept before the judge existed keep
  their rule: closed when no topic was raised by two reviews.
- **Reopened state.** When a closed state is edited, re-close it with
  `ask --since <git-ref where it was closed>`: the judge sees the change and
  sets aside, as `preexisting`, topics about passages the change did not touch.
  A reopened state is checked for what the change did, not audited again from
  scratch.
- **A recurring kind of question asks for a convention.** When topics of one
  kind keep coming (which failure is named first, which bytes are counted),
  write one convention that answers the whole kind, not one fix per place;
  Cabinet Kernel States 3 and 5 converged only after that.
- **Recurrence is the test of a closure.** A question closed by the owner must
  not come back in the next round; when it does, the closure did not reach the
  text.

## Cost

A round is a few tens of thousands of tokens — far less than one generation run
of a module set. Rounds repeat until closed; on Cabinet Kernel State 1 the points
per review fell from 15 to 3–5 once the stop rule applied, and the tenth round
repeated nothing.
