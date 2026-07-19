# Behavioral Notes

How to design effective classified notes for `global_spec.json`.

This document changes nothing in the factory specification language. The note
format, the mandatory prefix, and the closed class registry are defined
normatively in [SPEC_STANDARD.md](SPEC_STANDARD.md) (section `notes`). When to
write notes inside the authoring process is defined by
[SKILL.md](SKILL.md) State 7. This document covers the remaining question:
**what makes the text of a note actually constrain an implementation.**

Do not introduce new markers, sections, or schemas based on this document.

## What a note must achieve

A signature tells the factory what a function receives and returns. A note
must make the difference between a real implementation and a stub observable.

The governing test:

> Could `return None`, `return []`, `return {}`, an empty model, a constant
> success value, or a blind forwarding call satisfy every note of this
> function without contradiction?

If yes, the note set is decorative. Either strengthen it with observable
requirements or return to an earlier design state — a function whose behavior
cannot be pinned down is usually a function whose ownership or model layer is
not finished.

## Design principles

### 1. Constrain outcomes, not algorithms

A note states what must be observably true, not how to compute it.

```text
WEAK:   validate_working_diagram: [BEHAVIOR] MUST iterate over elements and
        then connections and append issues to a list
STRONG: validate_working_diagram: [ORCHESTRATION] MUST validate all elements
        before connections so connection findings can rely on a complete
        element index
```

The strong form still fixes the required ordering — but as a caller-visible
guarantee with its reason, not as pseudocode.

### 2. Name concrete evidence

Every load-bearing note should contain at least one token an implementation
can fail to honor: a field name, a config path, a rule name, an exception
type, a specific value, a sort key.

```text
WEAK:   create_diagram: [FIELD_ASSIGNMENT] MUST initialize the diagram
        correctly
STRONG: create_diagram: [FIELD_ASSIGNMENT] MUST set status to draft,
        current_revision to 0, and created_at/updated_at to the supplied
        created_at
```

Vague adjectives — *properly*, *correctly*, *appropriately*, *as needed*,
*reasonable*, *efficiently* — are banned. They cannot distinguish an
implementation from a stub, so they specify nothing.

### 3. Address data, do not inline it

Tables, allow-lists, thresholds, transitions, and taxonomies live in
`config`, `rules`, or `models`. A note references them addressably:

```text
WRONG:  change_diagram_status: [BEHAVIOR] draft may become active or
        archived; active may become archived; archived is terminal
RIGHT:  change_diagram_status: [RULE_REFERENCE] MUST enforce
        = rules.diagram_status_transitions
```

Inlined policy drifts from the declared policy the first time either is
edited. Every `= config.*`, `= rules.*`, `= models.*` reference must resolve
to an existing entry in the assembled spec.

### 4. Declare every symbol a note demands

If a note requires raising `ConflictError`, then `ConflictError` must exist —
in `models`, in `module_functions`, or in `imports`. A note that demands an
undeclared exception forces the factory to invent its shape and owner. The
same applies to any model or type a note mentions.

### 5. Negative space is part of the specification

`[FORBIDDEN_ACTION]` notes are not decoration; they close the shortcuts a
code generator would otherwise take. Write them wherever a plausible wrong
implementation exists:

```text
collect_connection_items: [FORBIDDEN_ACTION] MUST NOT derive physical length
from presentation layout
commit_revision: [FORBIDDEN_ACTION] MUST NOT call Object Card, MCP, LLM or
other external services while the transaction is open
```

A good forbidden-action note names a *specific tempting mistake*, not a
generic prohibition ("MUST NOT do anything wrong").

### 6. One primary class, chosen by dominant role

When a note mixes roles, pick the class whose loss would most change the
generated behavior. Do not split one coherent requirement into several notes
merely to satisfy classification, and never invent product-flavored classes
(`CIRCUIT_LOGIC`, `ESTIMATION_RULE`) — the registry in SPEC_STANDARD.md is
closed.

### 7. Full, unambiguous prefixes

Methods always use `ClassName.method_name`. A bare `__init__`, `to_dict`, or
`validate` prefix is unattributable. Module-wide requirements use the module
prefix and state a rule that genuinely applies to every function in it.

## Minimum semantic coverage by function role

Use the function's role (usually visible in its verb) to decide which note
classes the function cannot ship without. This mirrors the advisory S7/S8
checks in `tools/semantic_lint.py`.

| Role (typical verbs) | Notes it cannot ship without |
| --- | --- |
| Validator (`validate_*`) | failure semantics: which conditions produce which issues or exceptions (`[VALIDATION_ERROR]`, `[RETURN_SHAPE]`); otherwise an always-empty report passes |
| Normalizer (`normalize_*`) | the concrete value set it maps to **and** what it must preserve or must not change (`[DETERMINISM_OR_ORDERING]`, `[FORBIDDEN_ACTION]`); otherwise identity passes |
| Builder / assembler (`build_*`, `assemble_*`, `collect_*`) | the mandatory shape, projected fields, and provenance of the artifact (`[RETURN_SHAPE]`, `[FIELD_PROJECTION]`, `[PROVENANCE]`); otherwise an empty artifact passes |
| Resolver / reader (`resolve_*`, `get_*`, `list_*`) | precedence, source, ordering, and failure on missing input (`[VALIDATION_ERROR]`, `[DETERMINISM_OR_ORDERING]`); otherwise silently returning nothing passes |
| Mutator (`create_*`, `commit_*`, `transition_*`, `apply_*`) | effects, invariants, and boundaries: field assignments, enforced rules, authorization (`[FIELD_ASSIGNMENT]`, `[RULE_REFERENCE]`, `[SECURITY_BOUNDARY]`, `[ORCHESTRATION]`) |
| Use case / orchestrator | which owned operations it must delegate to, and the duplication it must not introduce (`[ORCHESTRATION]`, `[FORBIDDEN_ACTION]`, `[SECURITY_BOUNDARY]`) |
| Serializer / repository | the canonical model boundary and error translation (`[MODEL_REFERENCE]`, `[SCHEMA_CONSTRAINT]`, `[VALIDATION_ERROR]`) |

These are floors, not quotas. A function with one strong note beats a
function with five decorative ones.

## Anti-patterns

Reject a note when it:

- **restates the name** — `save_result: saves the result` adds nothing;
- **repeats the signature** — argument and return types already live in
  `contracts`;
- **narrates the implementation** — line-by-line pseudocode freezes accidents
  of one imagined implementation instead of requirements;
- **hides an undecided policy** — "choose the appropriate definition" means
  the precedence rule was never designed; return to rules, do not write the
  note;
- **promises the future** — "support additional formats later" belongs in a
  recorded open question, not in the specification;
- **cannot be violated** — if no incorrect-but-compiling implementation would
  contradict the note, delete it.

## Authoring workflow

1. Write notes only after contracts and ownership are stable (SKILL.md
   State 7). If a note forces a new model, rule, or owner into existence,
   stop and repair the earlier state first.
2. For each function, run the resistance test above and cover its role floor
   from the table.
3. Check every referenced exception, model, rule, and config path against the
   declared sections.
4. Run `python3 tools/semantic_lint.py <spec>` and read S2–S8 findings as
   advisory review comments, not as a gate; the canonical factory validators
   remain the authority on structure.

A note set is done when a motivated but lazy implementation — empty results,
identity transforms, blind forwarding, hand-rolled duplicates of domain logic
in transport handlers — necessarily contradicts at least one note.

## When the requirement belongs in `properties`

Do not keep a requirement only as prose when it is a total, side-effect-free
predicate over the function's `result`, arguments, and `self` for methods.
That form belongs in `properties.<function>` and can be checked with generated
inputs. Examples include non-empty validator findings under a precise invalid
condition, preservation of identity fields, bounds on normalized values, and
projection of required fields.

Keep the requirement as a note when checking it needs I/O, repository state,
authorization context, exception observation, transaction boundaries, clocks,
randomness, or orchestration evidence. Keep transition tables and policy data
in `rules`. State 7 records one of these as the invariant's primary landing in
`invariant_ledger.json`; supportive notes may still explain a property, but do
not count as a second primary landing.
