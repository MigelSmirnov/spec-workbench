# Design index workflow

`tools/design_index.py` is a deterministic navigation aid for large design-state corpora. Source Markdown remains normative.

## Authoring grammar for addressable items

Use heading depth as the ownership boundary. An accepted decision owns only the
content beneath headings deeper than its own heading:

```markdown
# State 2 — Rules

## Accepted decision A10 — Preserve evidence

### Normative rules

### Formal invariants

### Required tests

### Consequence
```

Use `## Accepted decision` for a supporting decision without an explicit ID.
Keep its sections at `###` or deeper. A heading at the decision's level or above
closes the item; content under that heading is intentionally not absorbed by the
index.

Place at least one accepted-decision item in every normative State 2 document.
`design_lint` consumes the index and therefore cannot diagnose a document that
contains no indexed item at all.

Keep section titles unique within an item when tools must address them as
`ITEM + SECTION`. Qualify repeated local headings rather than teaching the
parser to infer parent context. Additional non-canonical sections are allowed.

Run the State 2 authoring check after structural edits:

```bash
python tools/design_lint.py examples/<case> --state 2
```

`section_not_nested` means the index found a decision but no owned child
sections. Fix the Markdown hierarchy; do not broaden the parser to reinterpret a
flat document.

## State 2 -> State 3 required loop

When a candidate responsibility is derived from State 2, use the following navigation loop before assigning ownership.

### 1. Expand

Discover every occurrence of the relevant domain name, model, external system, or policy term across the case study:

```bash
python tools/design_index.py examples/<case> --mentions <name>
```

This broad pass is intentionally noisy. Its purpose is to expose constraints or evidence outside the expected decision cluster.

A lexical occurrence is navigation evidence only. It does not create an architectural relation.

### 2. Inspect surprising context

For broad results that could affect the responsibility boundary, inspect their structural source context:

```bash
python tools/design_index.py examples/<case> --context <path>:<line> --radius 5
```

Do not inspect every occurrence mechanically. Inspect only occurrences that may change ownership, dependencies, forbidden responsibilities, or external constraints.

### 3. Narrow

Return to the normative source state and restrict the same term to indexed design items:

```bash
python tools/design_index.py examples/<case> \
  --mentions-in-items <name> \
  --state 2 \
  --kind decision
```

The narrow pass answers which State 2 decisions actually contain the term. It intentionally excludes unindexed discovery prose and unrelated documents.

### 4. Verify explicit relations

For decisions considered part of the responsibility candidate, inspect explicit incoming and outgoing links:

```bash
python tools/design_index.py examples/<case> --references A51
python tools/design_index.py examples/<case> --references A52
```

Explicit references are stronger evidence than lexical overlap, but they still do not automatically define a module boundary.

### 5. Propose responsibility

Only after expand -> optional context -> narrow -> references may the agent propose one primary enforcement owner or responsibility cluster.

The index must never infer module ownership automatically.

## Why both passes are required

Starting with only the narrow pass can hide important constraints outside State 2. Using only the broad pass creates too much noise and encourages accidental clustering by shared words.

The required loop preserves both properties:

```text
expand to avoid tunnel vision
-> inspect meaningful surprises
-> narrow to normative evidence
-> verify explicit relations
-> make the architectural judgment
```
