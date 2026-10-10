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
| `consequential_gap` | two careful implementers build different behaviour that the owner, an agent, a caller or a service notices | the two behaviours and who notices; any quote verbatim in the texts | yes, when it quotes a passage; deferred otherwise (below) |
| `answered` | the texts already answer it | the answering quote, verbatim in the texts | no |
| `answered_later` | only with `--provider codex`: a later state's text already decides it | the deciding quote, verbatim in the later states' texts | no |
| `later_state` | it belongs to a later state | a state number after this one | no |
| `judged_before` | the same question a recent round already judged non-blocking, on passages that have not changed | the prior judgement's id; its quotes still verbatim in the texts | no |
| `indifferent` | no one acts differently on any answer | the reason | no |
| `preexisting` | only with `--since`: about a passage the change did not touch | the quote, verbatim in both versions | no |

### A gap no passage speaks to

On Cabinet Kernel States 2 and 5 (2026-10-05) the last three waves each raised
one new topic, never asked before, always a `consequential_gap` with no quote
and no contradiction: sandbox standard streams, the MCP listener binding, the
manifest size, what `process_count` counts. Each was a real question, but an
implementation detail no design passage spoke to, and a state needs two clean
waves in a row, which a fresh such topic every wave makes unlikely.

So a `consequential_gap` that quotes no passage does not block a state up to
State 5. The round keeps it with `deferred_to` ("State 6 contracts or State 7
notes") and counts it in `deferred_topics`; it must be answered there before
the case is assembled. A gap that quotes a passage still blocks, and its quotes
must be found verbatim — a gap anchored in a text is a defect of that text. A
deferred judgement followed as `judged_before` stays deferred. A gap blocks a
state only when it quotes that state's own documents. A gap whose every quote
lies elsewhere — in earlier states, closed by their own rounds, or in the later
texts the judge searched (notes, contracts) — is a gap of those texts: it does
not block, and the round keeps it with `quoted_elsewhere` and `deferred_to`
"the states whose texts it quotes". A contradiction blocks wherever its
passages are (owner, 2026-10-06: Cabinet Kernel State 5 round 89 blocked on
five gaps quoting States 0–2 and the notes, none quoting State 5). The judge is told
to quote every passage that bears on the gap, so a gap is deferred only when the
texts are silent. Decided by the owner 2026-10-05.

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

### The same question gets the same answer

A judge call is a sample: on Cabinet Kernel State 2, rounds 67 and 68 judged
about fifteen repeated topics on old, untouched passages `preexisting`, and
round 69, on texts that differed in three sentences, judged seven of the same
topics contradictions or gaps. With that many topics, two clear rounds in a row
are a matter of luck, and editing the texts does not change the odds.

So the judge is shown the verified non-blocking judgements of the state's latest
three judged rounds (newest first, one per topic) whose quoted passages are all
still found verbatim, and may follow one as `judged_before`, naming it. A
judgement whose passages changed is not offered: on Cabinet Kernel State 5
round 104 a precedent quoting notes reworded by the Stage 8.1 modality repair
was offered, followed, and then refused as blocking. The tool accepts that only when the named judgement
was offered and every passage it quoted is still found verbatim — in the texts,
or for `answered_later` in the later states' texts; a judgement that followed a
precedent passes the original kind and quotes on. A topic whose passages
changed is judged afresh, and a blocking judgement is never a precedent.

The judge is not trusted: a judgement whose evidence fails its check — a quote
not found character for character, a "later" state that is not later — blocks
like a gap. Closing what blocks is the work below; a non-blocking topic is
recorded in the round and, for `later_state`, must reach that state's texts as
a carried question.

### Every state closes unit by unit

A review of a whole state of rules finds about fifty topics a round: on
Cabinet Kernel State 2 (21 decisions), rounds 80–82 of 2026-10-06 each blocked
on two new topics, never repeated, half of them misreadings, each about a
decision nobody had changed. Two clear rounds in a row over all of it are luck,
and a one-line edit to one decision reopened all 21.

So a state closes in units: one per accepted decision (`## Accepted decision
Axx` to the next level-2 heading), one per other level-2 section and per
document preamble, and `context` — whether the earlier states' texts and this
state agree. A round asks only about the units that are not closed: the
reviewers still read every text, but each point names its unit, and a point
about a closed unit is set aside (kept in the review, not grouped). A blocking
topic keeps open only the units its points name; one that names none keeps
every reviewed unit open. A unit is closed when the two latest rounds that
reviewed it were clear for it on its current text; the state is closed when
every unit is. Editing one section reopens that section; editing an earlier
state reopens `context`. Decided by the owner 2026-10-06 for State 2.

Until 2026-10-10 only State 2 was cut so; the other states closed as one text,
and any edit reopened all of it — Cabinet Kernel State 5 ran 107 rounds. Late
decisions therefore went around the rounds: decision 26 rewrote States 3–5,
nobody asked again, and the pipeline went on to assembly. Every state with a
round is now cut into units (owner, 2026-10-10), so a late edit costs a round
about what it changed, not a re-audit of the state.

**A closure kept before units is carried.** A state closed as one text before
this rule — its latest round closed it, or its two latest rounds were clear on
the same documents — counts as closed unit by unit on the text it closed on.
The round finds that text in the case's git history (the commit that kept the
closing round first), cuts it into units and treats each as closed on its
digest then; the first unit round records what it carried (`carried` in its
summary), so later calls need no search. After a late edit only the edited
units are open, and each is reviewed for its diff (below). A state that never
closed, or whose closed text git no longer holds, carries nothing: its first
two unit rounds review everything. A state already closing in units (State 2)
needs no carrying.

A unit that was closed and then edited is reviewed for its edit, not again
whole: the round finds the text it closed on in the case's git history, gives
the reviewers the diff, and asks only about the change and what it affects; a
point quoting an unchanged passage of that unit, more than three lines from the
change, is set aside. On 2026-10-07 a one-sentence edit reopened Cabinet Kernel
A18, and three reviewers given the whole decision raised new storage-hardening
topics every round — corrupt databases, hard links, link races — none about the
edit. A unit never closed, or whose closed text git no longer holds, is
reviewed whole (owner, 2026-10-08).

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
- **Closure.** Every unit's two latest reviews are clear for it on the same
  text, and that text has not changed since (`status` compares digests). One
  clear round can be luck; two on the same texts show the questions have
  stopped mattering, not merely changed. A topic raised by one review is
  closed or carried when cheap, but does not hold the state open. Rounds kept
  before the judge existed keep their rule: closed when no topic was raised by
  two reviews.
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
