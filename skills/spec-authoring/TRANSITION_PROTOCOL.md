# Transition protocol

A state is handed to the next one only when what it owns is decided, and what
earlier states left for it is done. Until 2026-11-07 the Workbench checked that
each state was well formed *as that state* and ran the rules of the standard
once, at assembly. On client-portal (issue #147) every gate and every question
round of States 0–7 was green, and assembly then reported 270 messages, all of
them rules of the standard about decisions of States 1, 2, 4 and 6. Coverage
was not the failure; timing was. This protocol moves each rule to the
transition of the layer that owns it.

It adds no gate per way of going wrong. A check exists only for a rule of the
standard; the protocol decides **where** it runs, not what it checks.

## The five questions

Every transition asks the same five questions, made concrete by the `layer`
block of its phase in `authoring_sequence.json`:

1. **Inputs.** Are the materials this layer needs available? An input the
   layer needs now and does not have stops the transition.
2. **Own decisions.** Are the decisions this layer owns (`layer.owns`) made and
   recorded?
3. **Expressible.** Can each decision be written in the standard and checked by
   the Workbench? If not, it is a Workbench gap, not an author defect.
4. **Received obligations.** Did the obligations earlier layers carried here
   (`layer.receives`, computed from their `carries`) close?
5. **Carried obligations.** What does this layer leave for later, to which
   layer, and what will confirm it there (`layer.carries`: `to`, `check`)?

`python tools/authoring.py next <project> --json` returns the `layer` of the
current phase. After a phase's own gate passes, the sequencer runs the phase's
`checks` and every check carried to it (`tools/transition.py --phase <id>`),
and stops at that phase when one does not close.

## Four outcomes

| outcome | means | stops the transition |
|---|---|---|
| `closed` | the decision is recorded and confirmed at the level available now | no |
| `carried` | a determined obligation, with a receiving layer and a check that will confirm it | no |
| `not_checked` | an input the check needs does not exist | yes when the input is needed now; it is never a pass |
| `workbench_gap` | the standard has no form for the decision, or the tool cannot check the evidence that exists | yes; routed to the Workbench, never repaired by changing the design's behaviour |

Only the **execution** of a decision may be carried. An open choice written as
"to be decided in State 6" is not carried: it is a decision of this layer that
was not made, and the round judges it a gap of this layer.

A Workbench gap is recorded in `KNOWN_GAPS.md` with the finding codes it makes
uncloseable; a case cites it in the decision it affects as
`[known_gap: KG-nnn]`. Its findings keep stopping, marked `workbench_gap`, until
the standard's owner decides the form. Citing a gap never hides a finding.

## The four rules of #147

| rule of the standard | owned by | confirmed at | check | needs |
|---|---|---|---|---|
| every model has one identity and one closure | State 1: meaning and identity (who mints it, from what) | State 6 handoff | `model_closure` | State 1, `60_model_closure_*.json`, `60_contracts.json` |
| every fresh timestamp has a source | State 2: where time comes from, its representation, readings per operation | State 6 handoff (contracts), State 7 handoff (notes) | `time_source`, `ambient_time` | model closure; notes |
| every formal invariant is witnessed | State 2: the invariant and the test that would show it | State 2 handoff (described), witness phase (bound) | `invariant_tests`, `decision_witness` | Required tests; the Factory verification config; the assembled notes |
| every flow step is executed | State 4: the steps and who executes each | State 6 handoff (declared, contracted), State 7 handoff (called) | `flow_steps`, `flow_reachability` | plan and contracts; notes, router, backend closures |

### Models and closure

State 1 decides what a model means and whether it is a value or an entity. Its
typed field list is the model closure, written with the State 6 contracts. At
the State 6 handoff every State 1 model has a closure record of the same
identity, and every `contract_only` record — a runtime model with no State 1
meaning — is justified by a contract that introduces it. A case with no closure
file is `not_checked`: the identity, field-carrier and time-source checks of
State 6 all read the closure, and a check that sees no models finds nothing.
On client-portal the State 6 contract lint was green until the closure was
written, then raised 35 `fresh_timestamp_without_source`.

### Time source

State 2 decides the source and the meaning of time: who reads the clock, in
which representation the product keeps an instant, and how many readings one
operation takes. State 6 shows how each consumer obtains it: a `datetime`
parameter, a clock port retained by `__init__`, or a declared
`rules.time_source_policy` authority. For a design that keeps offset-naive UTC
instants and reads them from module-level functions, SPEC_STANDARD §6.9
version 4 is the form: one imported operation, one reading per call. Its
consumers are the modules that depend on it (imports, or State 3 `Knows`
before imports are decided). Do not replace the accepted behaviour with a
clock port to satisfy the check (KG-002, closed by that form).

An operation that does not read the clock may return a timestamp its callee
made: the viewer entry endpoint returns the session whose `expires_at` the
access operation computed. Each datetime field it returns is judged
on its own, through the calls the design obliges (a note naming the callee,
or a call a deterministic backend emits — the edges of flow reachability,
contracted functions only, never a class). A field is supplied when the
operation calls the clock function itself, or when a callee returns a field
of that name and either makes time (a mutating public operation, or one whose
note needs the current time) in a module with a source, or is itself supplied
with it. A value travels back only through what a call returns: a validation
returning `bool` that reads the clock supplies nothing, a read returning a
stored timestamp makes no fresh one, and a callee making another timestamp
(the audit's `occurred_at`) is not this one's source. A field no call supplies
stays open; a note that needs the current time itself is satisfied only by a
call that returns it (the clock, or a function returning bare `datetime`).
Delegation the names cannot show is a question for the round, not a wider
match. Do not import
the clock into a module that does not read it to satisfy the check.

### Invariant evidence

Three things share the word "witness" and are kept apart:

- the **described test** — the Required tests item that says what must be shown
  for an invariant. It is a State 2 decision; `invariant_tests` checks at the
  State 2 handoff that every formal invariant, by its identifier when it has
  one, is named by a Required tests item.
- the **binding** — `[witness: verification:<check>]`, `note:<scope>` or
  `workbench:<check>` in a Required tests item, naming an existing check that
  asserts the invariants *that item names* (a Required tests list item with
  its continuation lines). It is carried to
  `decision_witness_resolution`, where `decision_witness` confirms that the
  check exists. One tag does not stand for the decision's other invariants; a
  tag in an item that names none of several invariants binds nothing
  (`witness_binding_ambiguous`). A decision with several formal invariants
  gives each an identifier once it binds a check: a word label in the item
  ("closed-once") is not an address the Workbench can check, and an invariant
  without an identifier is reported (`invariant_without_identifier`).
- the **defect witness** of a question round — a history in which the texts give
  two outcomes. It proves a defect; it never proves an invariant.

Whether a bound check really asserts its invariant is a judgement, asked in the
State 2 round on the check's content: the round is given, read-only, the files
the check's command names in the Factory checkout, the assembled
[TEST_EVIDENCE] notes of a `note:` scope, or the implementation of a
`workbench:` gate (resolved through the assembly check table to the code it
delegates to, or to `design_lint` for a lint gate), each with its sha256, and
keeps those digests as the basis of its result (`layer.materials`).
A check's material is the files its command names and the Factory modules
they import, with the `__init__.py` of every package on the way (its own
support modules; not the product under test in `projects/`). A round is given
each file once, by sha256, and only for the bindings that need judging now.
Evidence comes first: a unit whose checks are not the ones its last review
judged gets all its bindings, whatever its text did. A unit never closed gets
all of them too. A unit reopened by an edit gets the bindings the edit
provably concerns — an edited Required tests item, or the items naming an
edited identified invariant — and all of them for any other edit, since a
normative change may change what the checks must show. A unit asked only
because it names a changed decision gets none. When the material does not fit one input
(`ROUND_MATERIAL_BUDGET`), the round is split into passes, each with its own
reviews and judge over its share of bindings, the first also asking about the
texts; nothing is cut.
The basis is kept per decision unit too (`unit_evidence`): when a bound check
changes — a file, the command, a digest — while the decision's text does not,
exactly that decision reopens and is reviewed for whether its bindings still
hold on the new evidence, until two clear reviews on it close it again
(`evidence_changed` in `status`). A judgement of such a unit is a precedent
only on the evidence it was judged on: on changed evidence, or with no
recorded basis, it is not offered to the judge, and the judge is told the unit
reopened for its evidence. Rounds kept before the basis was recorded are
taken as they stand for closure, not as precedents for bound decisions. A binding whose content
cannot be read whole is `not_checked` (`witness_material`, a State 2 check): its
sufficiency is not judged, and it is never taken as sufficient. On client-portal 28 of 32 decisions were bound to existing
checks; A7, A15, A20 and A32 have none. A binding found by reading check code
is evidence; a binding to a check that does not assert the invariant is a
false claim.

### Flow execution

State 4 names the steps of each flow and the operation (capability) that
executes each step. At the State 6 handoff every named capability is planned
and contracted — that needs no notes. At the State 7 handoff each step is
called by what runs the flow: a route delegate, a note of the calling operation
(bare, `Class.method`, or `param.method` through the caller's own contract), or
a deterministic backend that emits the call (SPEC_STANDARD 6.12: the
unit-of-work store's `begin` creates its accessors' schemas, the bootstrap store
the schemas of the repositories it writes). A call a backend emits needs no
note; do not write one to satisfy the analyser.

## Question rounds at a transition

A round is asked with its layer (`questions_workbench`): the reviewers and the
judge are given what the layer owns, the obligations it received and their
results, the obligations it carries, and the deterministic findings of its gate.
A State 7 round reads one module's Factory prompt, unchanged, and its
instruction adds the received obligations that module takes part in: a flow
step nothing calls in a flow the module executes, a note of the module that
needs the current time without its source, and every result not checked. A
reviewer reports an obligation the prompt does not carry out as
`unmet_obligation`; the judge sees the same list. Such a topic does not block
the round (State 7 rounds block on contradictions); the obligation keeps
blocking through its deterministic check.

A judgement cannot answer a topic against a listed finding, and a round that
closes does not make a blocking result disappear: `design_questions.py status`
reports `closed` for the rounds and `ready` for the transition, and exits 1
unless both hold.

The focus narrows from the general to the particular without losing the
earlier layers: in States 0–5 a review reads the prompt of its layer — the
open units, and of the earlier layers the passages they depend on, verbatim
(QUESTIONS.md, `ask`) — and asks about an earlier layer only whether this
layer fulfils what it carried here; a closed unit is not audited again. The unit rule of QUESTIONS.md stands: a fix reopens the
units it edits, and the deterministic context of a round is not part of any
unit's text, so a changed finding reopens nothing.

## Diagnosing a revision

The transitions stop a case at the first layer that does not hold. To see every
rule of the standard at once — before a migration starts, or on an old ref —
use the revision diagnosis (issue #147, second direction):

```bash
python tools/design_diagnose.py --case examples/<case> [--ref <git ref>]
python tools/design_diagnose.py --spec <accepted global_spec.json> [--ref <git ref>]
    [--factory-root <code_factory>] [--code-root <implementation root>] [--json]
```

It reads the revision from a temporary worktree, runs every check of the two
Workbench registries (the assembly checks and the transition checks) and
groups their findings by the state or phase that owns each rule (`State 1: 160 identity
· State 2: 44 time source, 32 witness · …`). A rule whose inputs the revision
does not hold — identity without State 1, flows without State 4, fresh
timestamps without State 5 — is `not_checkable`, never omitted and never a
pass; a check that fails to run is an `error` row and hides no other result.
The report names the Workbench that produced it: commit, uncommitted changes,
and the digests of the tools it loaded, of the sequence and of the standard.

Time is reported as two obligations, because a wall-clock source says nothing
about a monotonic one: the wall-clock requirements and the elapsed-time
requirements the notes and contracts show, each against its declared sources
(policy authorities, the clock backend's operations, the modules that import
them). The report states what it analysed; a requirement it did not detect is
not proof that none exists.

The Factory's two time checks stay apart from the Workbench's and from each
other, each with the Factory commit and tool digests: its validator on the
specification (`--factory-root`), and its time-source gate on an implementation
(`--code-root`, with the digest of every file scanned). Without code the gate
is `not_checked`; the specification's results stand regardless. On
client-portal with `system_clock_backend/v4`, a policy without `elapsed_time`
passes the validator and fails only the gate on live code, while elapsed
authority at `transport_guard` fails the validator (KG-003): only the two
results side by side show both.
