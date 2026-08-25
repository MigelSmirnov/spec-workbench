# Cabinet State 2 volume assessment

## Purpose

This document records a first-pass size and structure assessment of Cabinet Backend State 2.

It is intentionally **not** a semantic review and **not** a contradiction report. The next review pass should first compare State 2 against the formal requirements of `skills/spec-authoring/SKILL.md`, then inspect contradictions, omissions, and unresolved ownership.

Cabinet is treated here as a case study for a **general spec-workbench navigation/indexing tool**. Tool requirements must not depend on Cabinet-specific concepts such as invoices, Holded, Registry, PresuPro, uploads, or VPS retention.

## Corpus size

The current Cabinet case-study directory contains 23 Markdown files totaling approximately 341,288 bytes (~333 KiB).

State 2 is physically distributed across five files:

| File | Bytes | Share of State 2 |
|---|---:|---:|
| `02_rules.md` | 80,987 | 77.3% |
| `02_rules_import.md` | 13,280 | 12.7% |
| `02_rules_local_upload.md` | 3,787 | 3.6% |
| `02_rules_missing_original.md` | 3,632 | 3.5% |
| `02_rules_vps_retention.md` | 3,127 | 3.0% |
| **Total State 2** | **104,813** | **100%** |

State 2 therefore represents about 30.7% of the current Cabinet case-study text corpus.

The main observation is not only that State 2 is large. One logical design state is already distributed across several physical documents.

## Formal State 2 responsibility

According to the spec-authoring methodology, State 2 is responsible for invariants, rules, config, and constants. It must capture at least:

- data invariants;
- ownership and access invariants;
- valid state transitions;
- policy decisions;
- thresholds and routing rules;
- fallback policies;
- runtime knobs;
- limits, paths, timeouts, and feature switches;
- stable domain catalogs and enum-like values.

The methodology also requires deliberate classification between:

- `config` — runtime or product knobs that may change independently;
- `rules` — read-only domain or policy semantics;
- `models` — schemas, taxonomies, and structured contract data;
- `notes` — behavior that consumes the above rather than defining the data itself.

The formal readiness questions for State 2 are:

1. Is every invariant owned by a future responsibility rather than by “the whole system”?
2. Are state transitions explicit where lifecycle matters?
3. Are tables and allow-lists stored outside notes?
4. Can a value's section be justified by why and how it changes?

These questions should drive the next compliance pass.

## Observed structural density

### Main rules document

`02_rules.md` currently contains 20 explicitly named accepted decisions:

`A1`, `A2`, `A3`, `A4`, `A5`, `A6`, `A12`, `A13`, `A31`, `A32`, `A33`, `A34`, `A35`, `A40`, `A41`, `A42`, `A43`, `A51`, `A52`, `A61`.

The document spans several unrelated responsibility domains, including:

- Invoice Card acceptance;
- source-package semantics;
- Registry projection and project assignment;
- PresuPro snapshot and matching semantics;
- Holded publication and recovery;
- platform security and authorization.

Across the decisions that contain an explicit `Normative rules` numbered list, there are already at least 131 numbered rules. This lower bound excludes many normative clauses expressed under other headings such as formal invariants, retry policy, verification rules, authorization rules, recovery outcomes, status handling, and tests.

### Import rules document

`02_rules_import.md` is itself a substantial structured rule set rather than a small appendix. It contains major sections A–K and separately addresses:

- core invariants;
- Card lifecycle policy;
- manifest completeness and atomic acceptance;
- validation outcomes;
- quarantine;
- duplicate handling;
- synchronization/import/quarantine/receipt transitions;
- reconciliation and retention consequences;
- archive visibility and downstream eligibility;
- explicit State 3 enforcement-ownership handoff;
- remaining policy questions.

This file demonstrates that physical-file boundaries do not correspond cleanly to one semantic-item boundary.

### Supporting decisions

Three smaller files each contain an accepted supporting State 2 decision:

- local invoice source upload;
- missing-original handling;
- manual VPS retention release.

These documents contain normative rules, tests, states, restrictions, and open questions that interact with rules in the main document.

## Logical-volume estimate

A useful future index must not treat one Markdown file as one design item.

At minimum, the current State 2 corpus already contains several useful granularities:

1. **design state** — State 2;
2. **document** — one physical Markdown source;
3. **decision / policy block** — for example A52 marker-based Holded recovery;
4. **rule group** — for example retry policy or authorization invariants;
5. **individual normative clause / invariant / transition**;
6. **test expectation**;
7. **open question / open dependency**;
8. **relation** to a model, external system, lifecycle state, future responsibility, or another decision.

For navigation purposes, the important threshold has already been crossed: there are dozens of medium-sized semantic blocks and substantially more than one hundred individual normative statements. Reading by file plus grep is no longer a reliable representation of the design.

The precise number of atomic design items should **not** be fixed before defining the parser's addressability rules. Counting every bullet as an item would over-segment prose; counting every accepted decision as one item would under-segment large decisions such as A51, A52, and A61.

## Implication for the State 2 -> State 3 bridge

The methodology itself defines the important handoff question:

> Can each invariant be assigned to one primary enforcement owner?

A useful bridge therefore needs to make State 2 addressable enough that State 3 can assign responsibility without rereading the complete corpus.

A future tool should support queries conceptually equivalent to:

```text
list design items in state 2
show one item with source context
show items related to model X
show transitions concerning lifecycle Y
show policy/invariants with no State 3 owner
show all references to one decision
show items that depend on an unresolved question
show the source location for every result
```

This is a general spec-workbench capability, not a Cabinet-specific feature.

## General tool boundary

The first tool should be a deterministic structural index, not an AI reviewer.

Its responsibility should be:

```text
Markdown design-state documents
-> stable addressable items
-> typed relationships and source locations
-> compact query API
```

LLM reasoning remains outside the indexer and can use the index for compliance checks, contradiction search, ownership analysis, and later specification assembly.

A candidate generic item shape is:

```text
DesignItem
  id
  state
  kind
  title
  source_file
  source_range
  parent_id
  text
  explicit_refs[]
  relations[]
```

Candidate `kind` values should come from the methodology rather than from Cabinet, for example:

```text
model
invariant
policy
config
catalog
transition
open_question
responsibility
flow
public_operation
contract
behavioral_note
```

The exact schema is deliberately not accepted by this assessment; it is a direction for a later tool-design pass.

## Parser strategy to test first

Before adding authoring markup, test how far a deterministic Markdown parser can go using existing structure:

- heading hierarchy;
- accepted-decision headings;
- numbered normative lists;
- formal-invariant blocks;
- state-transition code blocks;
- Markdown tables;
- required-test sections;
- open-question/open-dependency sections;
- explicit identifiers such as `A52`, model names, and backticked symbols.

Only introduce additional authoring conventions if stable addressability cannot be obtained from the existing documents.

## Recommended next pass

The next assessment should remain formal rather than semantic:

1. build a State 2 requirement checklist directly from `skills/spec-authoring/SKILL.md`;
2. map every State 2 document/decision to those requirement categories;
3. identify requirements with no evidence or evidence that is only implicit;
4. record items that already contain an explicit State 3 ownership hint;
5. identify the minimum generic item granularity needed to perform that mapping without grep.

Only after that pass should the review search for contradictions, duplicated policy, inconsistent state transitions, and under-specified decisions.
