# State 2 → State 3 tooling check — A51/A52

## Purpose

This is a tooling experiment, not further Cabinet product design.

The check validates whether `tools/design_index.py` gives enough evidence to
review one State 3 responsibility candidate without either missing an important
constraint or pulling unrelated responsibility into the module.

Candidate under test:

```text
holded_purchase_publication
```

Seed decisions:

```text
A51 — create one Holded purchase and verify it by GET
A52 — marker-based Holded purchase create recovery
```

## Explicit-relation result

A51 explicitly delegates ambiguous create recovery to A52.

A52 explicitly requires the business verification rules from A51.

This is sufficient structural evidence to treat A51 and A52 as one candidate
responsibility cluster for review. The conclusion does not depend on the shared
word `Holded`.

## Lexical-navigation result

A lexical search for `Holded` also reaches A61 (`separate machine and local-user
identities`). A61 defines authorization and credential constraints relevant to
publication:

- Holded publication is a local authenticated operation;
- `accounting` or `administrator` authorization is required;
- Holded API credentials are separate from synchronization credentials;
- those credentials authorize only the dedicated Holded gateway.

This is an important dependency/boundary constraint, but it is not evidence that
A61 belongs inside `holded_purchase_publication`.

The experiment therefore confirms the intended separation:

```text
explicit relation graph -> candidate ownership evidence
lexical mention lookup  -> places worth reading for boundary constraints
```

A lexical occurrence must not become an architectural relation automatically.

## Candidate responsibility result

The current `holded_purchase_publication` candidate remains appropriately narrow.

It may own:

- one logical purchase-create attempt;
- ambiguous-create recovery;
- GET/read-back verification;
- publication/reconciliation outcome classification.

It must not absorb:

- authentication and role policy;
- credential storage or rotation;
- the general Holded gateway/client;
- unrelated Holded status semantics;
- future update, refund, attachment, approval, or payment behavior.

No second State 3 module is required for this experiment.

## Tooling gap discovered

`--mentions` currently searches the whole case-study Markdown corpus. On a large
case this can mix design-state decisions with discovery notes and other evidence.
For the State 2 → State 3 route, the agent should be able to ask for lexical
mentions constrained to indexed design items, for example:

```bash
python tools/design_index.py examples/<case> --mentions Holded --state 2 --kind decision
```

The desired semantics are:

- `--state` / `--kind` filter the enclosing indexed item for mention results;
- unowned occurrences outside an indexed item are excluded when either filter is
  present;
- filtering changes navigation output only and never creates relations.

Until that filter exists, the existing `--mentions` output remains useful but can
be noisy on large projects.

## Check outcome

The experiment validates the current architecture of the tool:

1. deterministic decision extraction is useful for State 2 → State 3;
2. incoming/outgoing explicit references provide strong cluster evidence;
3. lexical mentions expose important boundary constraints without asserting
   ownership;
4. one real navigation gap was found: scoped mention filtering;
5. further Cabinet State 3 authoring is not required to justify this finding.
