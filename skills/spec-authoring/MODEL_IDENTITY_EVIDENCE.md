# Model identity evidence

Use this procedure for every State 1 runtime model. Identity is a product
meaning decision, not a persistence or implementation guess.

## Closure sequence

For one model, record the following in order:

```text
State 1 model
↓
Meaning
↓
Substitution test
↓
Continuity test
↓
identity = value | entity
↓
Source of truth
↓
Lifecycle candidate
↓
Persistence candidate
↓
Open question / BLOCK
```

### Meaning

State what the model represents in product language and why the runtime needs
it. Do not justify identity from a database key, DTO shape, class name, or an
existing implementation.

### Substitution test

Ask whether one equal instance can replace another everywhere without changing
product meaning, provenance, or obligations.

- If yes, `value` is a candidate.
- If no because the system must still distinguish the instances, `entity` is a
  candidate.

### Continuity test

Ask whether the same logical thing remains the same thing while its allowed
state changes over time.

- If no independent continuity matters, `value` is a candidate.
- If product behavior follows one continuing thing across change, `entity` is
  a candidate and requires stable identity.

### Identity

Record exactly one classification in the model's `Identity` section:

```text
value
```

or:

```text
entity
```

Record the product evidence from both tests in `Identity evidence`. The lint
checks only that the classification and evidence are explicit; a human decides
whether the evidence supports the choice.

If the product requirements do not determine `value` or `entity`, write
`UNRESOLVED` explicitly and add a concrete `BLOCK:` question under `Open
questions`. Do not continue to State 2 until the question is answered and the
model is classified.

### Source of truth

Name the authority for the model's meaning and identity. Distinguish an
external authority, a Backend-owned record, an immutable observation, and a
calculated projection. Mirroring data does not transfer authority.

### Lifecycle candidate

Record only lifecycle states or transitions already implied by product
requirements. A value normally has no independent lifecycle. Keep uncertain
policy for State 2 rather than inventing it here.

### Persistence candidate

Record whether the model is a candidate for durable persistence, temporary
runtime use, or calculation on demand. Persistence does not prove entity
identity, and lack of persistence does not prove value identity.

### Open question / BLOCK

Use `None.` only when identity closure has no remaining product question. Use
`BLOCK: <question>` when the answer can change `value` versus `entity`, its
identity source, or continuity. Prose containing `UNRESOLVED` is never closure.

## State 2 consequences

State 2 must preserve these consequences and verify their rules and
invariants:

```text
value
→ no independent identity, history, or mutation

entity
→ stable identity

mirrored
→ entity

issued
→ snapshot semantics
```

`mirrored` means the runtime keeps a local representative of an externally
identified thing while the external system remains authoritative. `issued`
means a fact was emitted for a particular observation or version; later source
changes produce another snapshot rather than mutating the issued fact.
