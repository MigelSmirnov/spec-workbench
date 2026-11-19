# State 2 decides required results — experiment of 2026-11-20

Status: prepared on `tools/state2-required-results`, **not confirmed**. The
replay below was judged by Claude reading the saved rounds, not by the
standard provider. The probe at the end is the confirmation, and it has not
been run.

## The question

State 2 authors slide from a disposition into mechanics. Is that the
author's failing, to be held by prompts, or does the round push them there?

## What was read

Portal Deliverer State 2 as kept on `agent/portal-deliverer` at `992fc684`:
59 rounds of 18–19 November 2026, 721 judged topics, 224 dispositions,
57 commits of `02_rules.md`. Every one of the 207 topics judged a blocking
`consequential_gap` was read twice: first by its title, then by the
reviewers' questions and the judge's `divergence`. Each got one class:

- **required result** — the two behaviours differ in an outcome, a refusal, a
  durable effect or a safety guarantee that a promise, an invariant or a
  constraint of States 0–2 tells apart, and the question can be put in the
  words of States 0–1;
- **how (later layer)** — the question needs the words of an implementation:
  the service's own files, locks, grammars, encodings, orders of steps,
  deployment;
- **how a test proves** — cases, instruments and assertions of a required
  test, beyond the result it must show;
- **free** — both behaviours keep every stated requirement.

Limits. One reader, no second opinion. The second reading changed 10 of 207
classes, so the counts are an order of magnitude, not a measurement. The
line between "the result a test must show" (State 2's) and "how the test
shows it" is the least firm of the four.

## What was found

| Class | Topics | fixed | carried | accepted |
|---|---|---|---|---|
| required result | 41 | 36 | 4 | 1 |
| how (later layer) | 94 | 52 | 42 | 0 |
| how a test proves | 53 | 16 | 37 | 0 |
| free | 19 | 16 | 2 | 1 |

- 41 of 207 blocking gaps (20%) were State 2's own work. 31 of them came in
  rounds 1–12; rounds 13–59 held 10 among 125.
- 84 of the 120 `fixed` dispositions put into the rules what the state does
  not own. `02_rules.md` grew from 22 141 to 44 862 characters and names file
  modes, a temporary-name prefix, `ImageOps.exif_transpose` and
  `tempfile.mkstemp`.
- The slide is local, not steady. Rounds 13–34 mostly carried. Rounds 35–39
  closed 22 topics by a fix, none of them a required result: Lanczos
  semantics, temporary-name collisions, a race of two folder creations. Each
  fix raised questions about itself (35 T14 → 36 T4 → 37 T9).
- The opposite failure exists too. Four required results left State 2 as a
  mechanism for State 6: an unlistable photo folder (3 T6), which
  modification time is paired with the delivered bytes (14 T6), and reading
  through a link swapped in during the call (14 T20, 29 T8). A title was
  carried, not the result every mechanism must keep.
- The judge gave `indifferent` 3 times in 721 topics and `later_state` 30
  times.

Why the judge could not sort them: its rule asks who would notice, and its
`divergence` always finds someone. "The owner and a later delivery observe
different durable folder contents" (37 T5). "The Portal client sees different
edge pixels" (35 T6). An observer exists for every difference.

Two other cases, the rounds named in QUESTIONS.md. client-portal State 2
rounds 82–90: 29 blocking gaps, none a required result (15 about how a check
proves, 14 about the deployment's advisory data). Cabinet Kernel rounds
80–82: 3 gaps, too few to say anything.

This case was written through the experiment (R0-04): a prototype answered
each layer. Its library calls and test names are in the State 2 text. A
prototype answers "what does this mechanism do", so at State 2 it should be
asked one thing only: whether a promise can be kept at all.

## What the branch changes

Only State 2, by a flag of its phase (`gap_needs_requirement`); every other
state builds the same instruction as before, character for character.

1. **Scope** (`authoring_sequence.json`). A required result a rule leaves
   open; how a result is reached is a point for the state that decides it.
   "The order or precedence of checks" is gone from it: the judge's own
   `later_state` text already gave orders of checks to a later state.
2. **Judge** (`questions_workbench/prompts.py`, `judge.py`). First whose
   question, by the words it needs; then whether a requirement, quoted
   verbatim in `requirement` and checked mechanically, is broken by one of the
   two behaviours. A quoted gap with no requirement is a `hypothesis`
   (recorded, not blocking, the author's to dispose of). A requirement not
   found verbatim blocks.
3. **Carrying** (`units.py`, `service.py`, `design_questions.py`). A
   `later_state` topic for which the judge quoted a requirement every way must
   keep takes a disposition. `dispose --carried` takes `--keeps`, found
   verbatim in the texts, and the receiving round reads it.
4. **Reading a fix** (`tools/design_change_vocabulary.py`). Reports the
   identifiers and implementation words a change added that States 0–1 do
   not name. On the 30 fix commits of this case: 0 of the 4 that answered
   only required results, 13 of the 20 that answered none, 5 of the 6 mixed.
   A report, not a gate.

Not changed: the reviewers' question. It stays "where would you have to
guess". The round is a first trial of generation, and noticing a choice early
is its purpose. What changes is what follows from a choice noticed.

## The probe

Run where the standard provider is. A probe records no round, closure or
disposition in the case.

```bash
git worktree add ../pd agent/portal-deliverer
git worktree add ../wb-main main
git worktree add ../wb-new tools/state2-required-results

# the same three units, old judge and new, on the text as it stands
(cd ../wb-main && python tools/design_questions.py ask ../pd/examples/portal-deliverer \
    --state 2 --probe /tmp/pd-state2-old --unit A2 --unit A3 --unit A6)
(cd ../wb-new && python tools/design_questions.py ask ../pd/examples/portal-deliverer \
    --state 2 --probe /tmp/pd-state2-new --unit A2 --unit A3 --unit A6)

# the text of the evening of 18 November (30 066 characters), before the slide
git worktree add ../pd-early 221ec850
(cd ../wb-new && python tools/design_questions.py ask ../pd-early/examples/portal-deliverer \
    --state 2 --probe /tmp/pd-state2-early)

# client-portal, the decisions of rounds 82-90
git worktree add ../cp agent/client-portal
(cd ../wb-new && python tools/design_questions.py ask ../cp/examples/client-portal \
    --state 2 --probe /tmp/cp-state2-new --unit A28 --unit A32)
```

A2, A3 and A6 hold most of the mechanics; A28 and A32 are the two decisions
client-portal ping-ponged on.

## What would confirm it

1. **Nothing real is lost.** No topic of the new probes judged `indifferent`,
   `later_state` without a requirement, or `hypothesis` is a required result
   by the definition above. This one decides; read every such topic. A real
   result let through costs more than a round too many.
2. **The share falls.** Blocking gaps of the new probe are a small part of
   those of the old one on the same units. The replay suggests about a
   fifth; anything near a half or more means the judge still finds a
   requirement for everything, and the rule needs another form.
3. **The requirement is a requirement.** The `requirement` of each blocking
   gap is a promise, invariant or constraint, not the vague passage itself
   quoted twice. If it is the same passage as the gap's quote in most topics,
   the check is passed without being met.
4. **The fix report stays quiet on real fixes.** Run it on the next fixes of
   a required result; it should report nothing.

If 1 fails, do not merge. If 2 or 3 fails, the order of the two questions may
still be worth keeping without the mechanical check.

## Every topic

Portal Deliverer State 2, blocking gaps in round order.

| # | Round | Topic | Class | Author's disposition |
|---|---|---|---|---|
| 1 | 01 T1 | Authoritative closed security-category set required for a complete review | required result | fixed |
| 2 | 01 T2 | Authority and synchronization mechanism for the stored-image size limit | required result | fixed |
| 3 | 01 T3 | Conditions and precedence for A1 file-status classification, including scan races | required result | fixed |
| 4 | 01 T4 | Connection-path validation, containment, symlink races, and failure outcomes | required result | fixed |
| 5 | 01 T5 | Exact dependency set and pinning scope, including transitive distributions | how (later layer) | fixed |
| 6 | 01 T6 | Exact ignored Syncthing and bookkeeping name patterns | required result | fixed |
| 7 | 01 T11 | HTTPS enforcement boundary, trusted proxy scheme, and loopback HTTP policy | required result | fixed |
| 8 | 01 T12 | OSV snapshot currency, advisory matching, and vulnerability-gate policy | how (later layer) | fixed |
| 9 | 01 T13 | Placement-call cardinality, duplicate items, and whole-call validation | required result | fixed |
| 10 | 01 T14 | Recursive scan scope and inclusion of subfolders or selected subtrees | required result | fixed |
| 11 | 01 T15 | Required evidence proving exactly one clock read per operation | required result | fixed |
| 12 | 01 T16 | Required evidence that all operations leave source folders entirely unchanged | required result | fixed |
| 13 | 01 T17 | Required evidence that authentication protects every operation except health | required result | fixed |
| 14 | 01 T18 | Required evidence that repeated placement writes nothing and creates no second record | required result | fixed |
| 15 | 01 T19 | Resolution of ambiguous or nonexistent Europe/Madrid camera times | required result | fixed |
| 16 | 01 T20 | Token-file encoding, entropy validation, whitespace, ownership, permissions, links, and ACLs | how (later layer) | fixed |
| 17 | 01 T22 | Accepted bearer Authorization syntax and authentication-failure response | how (later layer) | fixed |
| 18 | 01 T23 | Camera-time metadata fields, precedence, conflicts, and malformed values | required result | fixed |
| 19 | 01 T24 | Complete request-processing check precedence | how (later layer) | fixed |
| 20 | 01 T25 | Concurrent-caller winners, loser results, and required cross-process evidence | required result | fixed |
| 21 | 01 T26 | Cross-process project-lock authority, lifecycle, timeout, and recovery semantics | how (later layer) | fixed |
| 22 | 01 T28 | Detection and precedence of source_changed versus absent or not-ready sources | how (later layer) | fixed |
| 23 | 01 T32 | Exact deliverer-supplied intake_id and intake_source values | how (later layer) | fixed |
| 24 | 01 T33 | Mark-request identifier validation, refusal results, and check precedence | how (later layer) | fixed |
| 25 | 01 T34 | Per-item processing order, failure isolation, and call-aborting failures | required result | fixed |
| 26 | 01 T36 | Relative-path normalization, sort comparison, and duplicate-path representation | how (later layer) | fixed |
| 27 | 01 T37 | Required evidence that every generated publication body has client_visible false | required result | fixed |
| 28 | 01 T38 | Required evidence that responses expose no server paths and the Portal is never called | required result | fixed |
| 29 | 01 T39 | Required test evidence that XMP metadata is removed | required result | fixed |
| 30 | 01 T40 | UTC instant representation, serialization precision, and rounding | required result | fixed |
| 31 | 01 T42 | Which earlier open questions are closed or remain deliberately open | required result | fixed |
| 32 | 02 T2 | Accepted EXIF date grammar and handling of missing or invalid original-time offsets | how (later layer) | fixed |
| 33 | 02 T3 | Accepted identifier spellings, canonicalization, validation order, and malformed-identifier precedence | how (later layer) | carried → 6 |
| 34 | 02 T4 | Behavior when directory enumeration fails or a directory changes during traversal | required result | fixed |
| 35 | 02 T5 | Canonical token encoding and validation of token-file contents, type, ownership, and permissions | how (later layer) | carried → 6 |
| 36 | 02 T6 | Exact accepted versions and canonical names of direct dependencies | how (later layer) | carried → deploy |
| 37 | 02 T9 | Publication identity collisions between source hashes sharing the same prefix | required result | fixed |
| 38 | 02 T11 | Statuses, payloads, and refusal codes for malformed requests and unavailable project resources | how (later layer) | carried → 6 |
| 39 | 02 T14 | Validation, normalization, and exact ISO 8601 serialization of clock values | how (later layer) | carried → 6 |
| 40 | 02 T18 | Handling and constant-time comparison of missing, repeated, or whitespace-bearing Authorization headers | how (later layer) | carried → 6 |
| 41 | 02 T20 | Non-rounding conversion of filesystem modification times to microseconds | free | fixed |
| 42 | 02 T22 | Project-lock scope and whether the operation clock is read before or after lock acquisition | free | fixed |
| 43 | 02 T29 | Whether containment permits a path equal to the root | required result | fixed |
| 44 | 03 T1 | Execution paths required to test the clock read-count invariant | how a test proves | carried → factory_checks |
| 45 | 03 T2 | Lexical grammar, numeric ranges, and invalid-offset handling for camera timestamps | how (later layer) | carried → 6 |
| 46 | 03 T3 | Whether the resolved invoice subfolder must remain strictly inside the resolved root | required result | accepted |
| 47 | 03 T6 | Behavior when the photo-folder root cannot be listed | required result | carried → 6 |
| 48 | 03 T8 | Refusal precedence between an unconfirmed connection and an unavailable folder | free | carried → 6 |
| 49 | 03 T9 | Time-zone database version and behavior when Europe/Madrid rules are unavailable | how (later layer) | carried → deploy |
| 50 | 03 T11 | Which OSV vulnerability records count for installed versions | how (later layer) | carried → deploy |
| 51 | 04 T1 | A10 concurrency coverage and references for connection-change races | required result | fixed |
| 52 | 04 T6 | Failures classified as an unreadable connection record | how (later layer) | fixed |
| 53 | 04 T9 | Operation boundary and immutable single-read connection snapshot | how (later layer) | fixed |
| 54 | 04 T10 | Precedence among connection refusal conditions | free | fixed |
| 55 | 04 T11 | Required test coverage and assertions for unreadable connections | how a test proves | fixed |
| 56 | 04 T13 | Distinguishing an absent connection from an unreadable connection | how (later layer) | fixed |
| 57 | 04 T14 | Formal invariant and required-test placement for invalid or unreadable connections | required result | fixed |
| 58 | 04 T15 | Required live-reload test coverage for revoked confirmation | how a test proves | fixed |
| 59 | 04 T18 | Startup behavior when a connection record is unreadable | how (later layer) | fixed |
| 60 | 05 T1 | Decide whether resolved photo-folder checks occur during startup whole-file validation or per operation | how (later layer) | fixed |
| 61 | 05 T3 | Define atomic replacement and single-snapshot read semantics for the connections file | how (later layer) | fixed |
| 62 | 05 T4 | Define malformed project/source identifier validation, refusal granularity, and check ordering | how (later layer) | fixed |
| 63 | 05 T6 | Require no-record tests for all operations, unknown_project responses, and absence of side effects | how a test proves | fixed |
| 64 | 05 T10 | Define whole-file invalidity precedence when an unrelated record is invalid | how a test proves | fixed |
| 65 | 05 T15 | Define which requests must perform exactly one connections-file read | free | fixed |
| 66 | 08 T3 | Placement when an eligible ordinary file and an ignored conflict copy share the same hash | required result | fixed |
| 67 | 08 T5 | Case-equivalence rule for conflict-marker matching | required result | fixed |
| 68 | 08 T6 | Conflict-name evaluation timing and behavior during concurrent rename and placement | how (later layer) | fixed |
| 69 | 08 T7 | Required coverage combinations for the INV-18 witness test | how a test proves | fixed |
| 70 | 09 T1 | Exact event when a folder or file name is observed and fixed for an operation | how (later layer) | fixed |
| 71 | 09 T2 | How INV-18 proves the ordinary file, not the identical conflict copy, sourced the placement | how a test proves | fixed |
| 72 | 09 T9 | Whether INV-18 must verify that a failed placement performs no writes | how a test proves | fixed |
| 73 | 10 T3 | When directory-listing names become fixed during a scan, including incremental listing behavior | how (later layer) | fixed |
| 74 | 10 T6 | Required converse test for a listed conflict-copy name renamed to an ordinary name during the scan | how a test proves | fixed |
| 75 | 10 T7 | Scope of writes that INV-18 tests must prove absent | how a test proves | fixed |
| 76 | 11 T2 | Directory-listing semantics under concurrent creation, removal, and renaming | how (later layer) | fixed |
| 77 | 11 T10 | Scope of the writes-nothing prohibition, including transient and pre-existing-state writes | required result | fixed |
| 78 | 11 T12 | Exactly-once status when a file moves between folders during a scan | free | fixed |
| 79 | 12 T1 | Exact observation or lifecycle boundary at which path disappearance changes the scan or placement result | how (later layer) | fixed |
| 80 | 12 T5 | Observation used to classify failed subfolder descent as a symbolic-link change or another listing failure | free | accepted |
| 81 | 12 T6 | Opening mode and rejection classification when a listed file becomes a non-regular object | how (later layer) | fixed |
| 82 | 12 T11 | Whether once-only subfolder traversal is keyed by filesystem identity or listed path | free | fixed |
| 83 | 13 T1 | Canonical ISO 8601 serialization and type of marked_at | how (later layer) | carried → 6 |
| 84 | 13 T3 | Exact lexical rules for normalized and permitted delivery names | how (later layer) | fixed |
| 85 | 13 T4 | Exact responses, codes and precedence for malformed requests and invalid or unknown projects | how (later layer) | carried → 6 |
| 86 | 13 T5 | Failure precedence when a delivery target is or becomes non-regular or symbolic | how (later layer) | fixed |
| 87 | 13 T6 | Required proof that conflict-copy targets are never read, including race cases | how a test proves | carried → factory_checks |
| 88 | 13 T7 | Required proof that ineligible source targets are never read | how a test proves | carried → factory_checks |
| 89 | 13 T8 | Required test coverage and proof for preserving all source-folder content and metadata | how a test proves | carried → factory_checks |
| 90 | 13 T10 | Separate-process test coverage for cross-process delivery locking | how a test proves | carried → factory_checks |
| 91 | 13 T14 | Meaning and implementation of opening a file without waiting | how (later layer) | fixed |
| 92 | 13 T15 | Required proof that replay performs no writes or state changes of any kind | how a test proves | carried → factory_checks |
| 93 | 13 T17 | Whether modification time is truncated before plausibility comparison | free | fixed |
| 94 | 13 T18 | Which scan statuses receive a computed source_id | required result | fixed |
| 95 | 13 T19 | Clock-read acceptance boundary and required read-count tests | how a test proves | carried → factory_checks |
| 96 | 14 T2 | Required INV-02 test coverage and proof that rejected paths were never opened | how a test proves | carried → factory_checks |
| 97 | 14 T3 | Required clock-read-count tests for every INV-13 mark outcome | how a test proves | carried → factory_checks |
| 98 | 14 T6 | Which modification-time observation is paired with file bytes and how many reads are allowed | required result | carried → 6 |
| 99 | 14 T7 | Meaning of an unnormalised path or filename in the required tests | how a test proves | fixed |
| 100 | 14 T11 | Directory-listing boundary and inclusion of entries created during a scan | how (later layer) | carried → 6 |
| 101 | 14 T12 | Failure returned when path metadata cannot be obtained for reasons other than absence | how (later layer) | fixed |
| 102 | 14 T13 | How tests prove a new placement never reads a conflict copy | how a test proves | carried → factory_checks |
| 103 | 14 T15 | Scan observation order and which metadata observation determines size-based ordering | how (later layer) | carried → 6 |
| 104 | 14 T16 | When an atomic placement-record write becomes durable and how post-rename sync failures are handled | how (later layer) | carried → 6 |
| 105 | 14 T20 | Whether symbolic-link protection must cover every path component against races | required result | carried → 6 |
| 106 | 15 T1 | Required test case and observations for unreadable segment metadata and proof that the failing path is not opened | how a test proves | carried → factory_checks |
| 107 | 15 T2 | Metadata operation, fields, segments, and failures covered by rule 5 condition 1 | how (later layer) | carried → 6 |
| 108 | 15 T3 | Scope of the “opens no path” prohibition for final paths and ancestors | how (later layer) | carried → 6 |
| 109 | 15 T4 | Handling a readable intermediate path segment that is not a directory | how (later layer) | carried → 6 |
| 110 | 16 T1 | Classification of readable JSON records that violate the record schema | required result | fixed |
| 111 | 16 T2 | Distinguishing lock contention from project-lock acquisition failure | how (later layer) | fixed |
| 112 | 16 T3 | INV-20 damage test coverage and assertions that no new artifacts are created | how a test proves | carried → factory_checks |
| 113 | 16 T10 | Distinguishing an absent state record from an unreadable one | required result | fixed |
| 114 | 16 T11 | Formal no-state-change invariant, its persistence scope, and tests for lock or mark-write failures | how a test proves | carried → factory_checks |
| 115 | 17 T3 | Retry, interruption, cancellation, and failure rules for lock acquisition | how (later layer) | carried → 6 |
| 116 | 17 T4 | Validation and classification of structurally or semantically invalid state records | how (later layer) | carried → 6 |
| 117 | 17 T6 | Persistent-state assertions required to prove no unintended placements or marks | how a test proves | carried → factory_checks |
| 118 | 17 T8 | Required damaged-record test matrix across damage classes, record types, and operations | how a test proves | carried → factory_checks |
| 119 | 17 T15 | Whether a missing project lock file is created or treated as a failure | how (later layer) | carried → 6 |
| 120 | 20 T3 | Invariant and required tests proving failed or refused marks change no records or stored images | how a test proves | carried → factory_checks |
| 121 | 22 T2 | Whether structurally complete JSON with invalid field values or types counts as a damaged record requiring A6 rule 5 refusal | how (later layer) | carried → 6 |
| 122 | 22 T3 | How INV-02 tests prove delivery never opens or reads a failing path before rejection | how a test proves | carried → factory_checks |
| 123 | 22 T4 | How INV-19 tests prove a conflicting copy is never read before rejection | how a test proves | carried → factory_checks |
| 124 | 22 T5 | Source and timing of the file modification-time read | how (later layer) | carried → 6 |
| 125 | 23 T4 | Filesystem modification-time observation, read count, and snapshot consistency | how (later layer) | carried → 6 |
| 126 | 23 T5 | Required pre-state, outcome, and persistence assertions for the INV-06 recovery test | how a test proves | carried → factory_checks |
| 127 | 24 T1 | Accepted port syntax and range and handling of invalid values | how (later layer) | carried → 6 |
| 128 | 24 T2 | Accepted timezone setting values and handling of absent, empty, or invalid values | how (later layer) | carried → 6 |
| 129 | 24 T7 | Timezone use when converting camera timestamps, including DST edge cases and explicit offsets | how (later layer) | carried → deploy |
| 130 | 26 T6 | Define observation behavior when a file mutates during reading | how (later layer) | fixed |
| 131 | 27 T3 | Handling a zero-byte read when pre-read metadata reports a non-empty file | how (later layer) | fixed |
| 132 | 27 T4 | Whether scanning stops at the first byte beyond the source limit or continues to EOF | free | fixed |
| 133 | 28 T4 | Which metadata size observation the listing uses and whether it also establishes regular-file status | how (later layer) | fixed |
| 134 | 29 T3 | Required test evidence that condition-1-failing paths are never opened | how a test proves | carried → factory_checks |
| 135 | 29 T4 | Required test evidence that conflict copies are never read during new placement | how a test proves | carried → factory_checks |
| 136 | 29 T6 | Source of the file-modification fallback time and number of metadata readings during delivery | how (later layer) | fixed |
| 137 | 29 T7 | Disposition when a listed regular file becomes a non-regular object before metadata reading | how (later layer) | fixed |
| 138 | 29 T8 | Mechanism preventing symbolic-link replacement between checks and file opening | required result | carried → 6 |
| 139 | 29 T9 | Required test evidence that source-folder contents and directories are never mutated, even transiently | how a test proves | carried → factory_checks |
| 140 | 29 T11 | Whether empty or metadata-oversized named files must be opened and read | free | fixed |
| 141 | 30 T1 | Coverage and observation required to prove failing condition-1 paths are never opened | how a test proves | carried → factory_checks |
| 142 | 30 T2 | Opened-file modification-time sampling, precision, and UTC representation | how (later layer) | fixed |
| 143 | 30 T3 | Required observation proving that a new placement never reads a conflict copy | how a test proves | carried → factory_checks |
| 144 | 30 T6 | Required proof that removal or replacement preserves each earlier delivery artifact | how a test proves | carried → factory_checks |
| 145 | 30 T7 | Scope and proof requirements for the no-source-mutation test | how a test proves | carried → factory_checks |
| 146 | 30 T10 | Whether replayed placement must perform no writes or only preserve final durable state | how a test proves | carried → factory_checks |
| 147 | 31 T1 | Observable proof that a new placement never reads a conflict copy | how a test proves | carried → factory_checks |
| 148 | 31 T2 | Required result when post-open metadata reading fails | how (later layer) | fixed |
| 149 | 31 T3 | Scope and observable proof that delivery opens no path failing validation | how a test proves | carried → factory_checks |
| 150 | 31 T6 | Whether non-regular-file or open failure checks terminate processing before the mandatory read | how (later layer) | fixed |
| 151 | 31 T9 | Whether INV-01 tests must detect transient source-folder mutations during execution | how a test proves | carried → factory_checks |
| 152 | 31 T10 | Whether INV-07 replacement tests must verify the earlier placement record remains unchanged | how a test proves | carried → factory_checks |
| 153 | 31 T11 | Whether INV-12 tests must directly inspect exact durable record, image, and mark counts | how a test proves | carried → factory_checks |
| 154 | 32 T6 | Whether “read once” means one system call or a complete retrying logical read | required result | fixed |
| 155 | 34 T5 | Token-file loading failures, race handling, and Unicode whitespace parsing | how (later layer) | fixed |
| 156 | 34 T11 | Meaning of leaving no file after a pre-rename failure when a destination already exists | how (later layer) | fixed |
| 157 | 34 T14 | Safe opening and validation of an existing project lock-file entry | how (later layer) | fixed |
| 158 | 35 T4 | Rounding and minimum dimension for the non-limiting resized side | free | fixed |
| 159 | 35 T5 | Conversion of decoded non-RGB samples to RGB and the colour space used for image processing | free | fixed |
| 160 | 35 T6 | Exact Lanczos resizing semantics, including alpha handling, support, edges, coordinates, and quantization | free | fixed |
| 161 | 35 T12 | Arithmetic, alpha scale, and rounding for compositing transparent pixels onto white | free | fixed |
| 162 | 35 T13 | Creation mode and crash-time finality of temporary image and record files | how (later layer) | fixed |
| 163 | 35 T14 | Temporary-name selection and collision handling for abandoned temporary files | how (later layer) | fixed |
| 164 | 35 T15 | Whether symbolic links are forbidden only at the token path leaf or throughout the path | how (later layer) | fixed |
| 165 | 36 T4 | Temporary-name generation and collision handling during exclusive creation | how (later layer) | fixed |
| 166 | 36 T8 | Durability and failure handling for newly created folders | how (later layer) | fixed |
| 167 | 37 T1 | Handling a concurrent race when another process creates a required folder first | free | fixed |
| 168 | 37 T3 | Handling symbolic links and unexpected objects while traversing folders below the state folder | how (later layer) | fixed |
| 169 | 37 T5 | Retention, removal, or repair of directories left by failed or interrupted setup or writes | free | fixed |
| 170 | 37 T7 | Required creation, write, rename, and synchronization order for image folders and files | how (later layer) | fixed |
| 171 | 37 T9 | Temporary-name suffix generation, collision retry limit, and exhaustion result | how (later layer) | fixed |
| 172 | 38 T1 | Handling a concurrent folder-creation race | free | fixed |
| 173 | 38 T2 | Result and residual state when both a write and temporary-file cleanup fail | how (later layer) | fixed |
| 174 | 38 T3 | Concurrency tests required to prove unique durable placement and mark effects across processes | how a test proves | fixed |
| 175 | 38 T10 | Whether damaged-record tests must prove that no new durable artifacts were created | how a test proves | fixed |
| 176 | 39 T4 | Decide whether regular-file validation occurs before changing an existing lock entry's mode | how (later layer) | fixed |
| 177 | 39 T5 | Require a test demonstrating INV-12 for concurrent mark calls within one process | how a test proves | fixed |
| 178 | 39 T7 | Decide how to handle an existing non-empty regular lock file without corrupting its bytes | how (later layer) | fixed |
| 179 | 39 T10 | Specify durable-state assertions for the mark-concurrency test | how a test proves | fixed |
| 180 | 40 T8 | Record lookup behavior for symbolic-link or non-folder ancestor path components | how (later layer) | carried → 7 |
| 181 | 41 T1 | Placement and mark record addresses and filenames | how (later layer) | carried → 7 |
| 182 | 41 T2 | Project lock address derivation and collision-free filename | how (later layer) | carried → 7 |
| 183 | 41 T5 | Temporary-file naming, exclusive creation, collision, replacement, and cleanup rules | how (later layer) | carried → 7 |
| 184 | 41 T7 | Accepted time-zone identifiers, database version, and invalid-value behavior | how (later layer) | carried → deploy |
| 185 | 41 T10 | Missing-folder creation order, races, collisions, modes, and failures | how (later layer) | carried → 7 |
| 186 | 41 T13 | Whether no-write replay or failed-delivery paths may create locks or folders | required result | fixed |
| 187 | 41 T14 | Accepted EXIF date-time byte and text grammar | how (later layer) | carried → 7 |
| 188 | 41 T15 | Atomic replacement visibility for an existing destination file | how (later layer) | carried → 7 |
| 189 | 41 T19 | Required record file type and symbolic-link handling | how (later layer) | carried → 7 |
| 190 | 44 T2 | Recovery, refusal, and retained state after concurrent or partial project-lock creation | how (later layer) | carried → 7 |
| 191 | 44 T11 | Whether directory-entry and metadata mutations count as changing protected existing files or lock folders | how a test proves | carried → factory_checks |
| 192 | 44 T15 | Exact state required to remain unchanged in replacement and removal tests | how a test proves | carried → factory_checks |
| 193 | 44 T16 | How tests prove that conflict-copy contents are never read | how a test proves | carried → factory_checks |
| 194 | 44 T17 | Scope of evidence required to prove a replayed placement writes nothing | how a test proves | carried → factory_checks |
| 195 | 45 T7 | Outcome when store or proposed-path resolution fails | how (later layer) | fixed |
| 196 | 45 T9 | Required observations proving a new placement never reads a conflict copy | how a test proves | carried → factory_checks |
| 197 | 46 T1 | How to resolve and containment-check prospective stored-image paths whose folders or file do not yet exist | how (later layer) | carried → 7 |
| 198 | 46 T8 | Which A5 or A6 whole-request failures are M08 refusals rather than M06 failures, including authentication and its code | required result | fixed |
| 199 | 47 T4 | Which path components and links are resolved for containment, including not-yet-existing destinations | how (later layer) | carried → 7 |
| 200 | 48 T2 | Folders created during atomic writes, their creation stages, and crash-left empty folders | free | carried → 7 |
| 201 | 48 T10 | Whether PhotoPublication.photo_date must exactly preserve PreparedPhoto.taken_at | required result | fixed |
| 202 | 50 T11 | Define how tests prove the deliverer has no Portal calls or credentials | how a test proves | fixed |
| 203 | 52 T7 | Define how tests prove unconfirmed connections trigger no scanning | how a test proves | fixed |
| 204 | 59 T1 | Accepted RuntimeEnvironment spellings and invalid-value startup behavior | how (later layer) | carried → 6 |
| 205 | 59 T2 | Accepted port spellings, range validation, and invalid-value startup behavior | how (later layer) | carried → 6 |
| 206 | 59 T3 | Environment-variable absence rules and string-value preprocessing | how (later layer) | carried → 6 |
| 207 | 59 T4 | Authoritative time-zone database, version, and alias policy | how (later layer) | carried → deploy |
