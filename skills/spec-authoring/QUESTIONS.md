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
groups their open points into topics. The round is kept under
`examples/<case>/questions/state<N>/round-<k>/`: each review, and `summary.json`
with the texts' digests, every topic and how many reviews raised it.

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
- **Closure.** The latest round raises no topic in two or more reviews, and the
  texts have not changed since that round (`status` compares digests). A topic
  raised by one review is closed or carried when cheap, but does not hold the
  state open.
- **Recurrence is the test of a closure.** A question closed by the owner must
  not come back in the next round; when it does, the closure did not reach the
  text.

## Cost

A round is a few tens of thousands of tokens — far less than one generation run
of a module set. Rounds repeat until closed; on Cabinet Kernel State 1 the points
per review fell from 15 to 3–5 once the stop rule applied, and the tenth round
repeated nothing.
