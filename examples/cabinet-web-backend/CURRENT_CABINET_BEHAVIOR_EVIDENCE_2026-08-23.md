# Current Cabinet_web behavior evidence

Date: 2026-08-23
Repository: `MigelSmirnov/Cabinet_web`
Commit: `d3fac8e5d2b85c12904cba24060717b84e2757c2`

## Purpose

This is State-0 evidence for behavior already implemented by Cabinet_web. It
does not invent replacement semantics for the new server backend. The backend
and ChatGPT plugin must preserve these observable application outcomes.

## Existing interaction direction

The accepted Cabinet documents state that conversation is the primary write
interface. The assistant searches existing Cards, extracts only supported
facts, prepares or writes structured Cards, reports what was saved, preserves
unknown facts, and reports when original binary bytes were not stored.

## Implemented Invoice outcomes

The current application operations cover:

- search and get, including an explicit not-found result;
- draft preparation with normalization, stable identities, validation issues,
  and duplicate candidates;
- draft creation with a saved Card and revision/content hash;
- draft update protected by the expected content hash;
- explicit confirmation and archive transitions;
- payment and source-evidence recording;
- operation-scoped idempotent replay and recovery;
- structured rejection of invalid input, stale revision, duplicate target,
  duplicate candidates without acknowledgement, and unacknowledged warnings.

Duplicate discovery never merges or writes automatically. A cancelled or
withheld confirmation leaves the draft unconfirmed. Source metadata never
claims that conversation bytes were stored when they were not.

Relevant evidence:

- `docs/02-tools/TOOLS_MODEL.md`;
- `docs/02-tools/INVOICE_WORKFLOW.md`;
- `docs/02-tools/INVOICE_TOOLS_MODEL.md`;
- `docs/03-implementation/INVOICE_IMPLEMENTATION_STATUS.md`;
- `tools/invoice_*_service.py`;
- `tests/test_invoice_*`.

## Existing estimate and shopping-list outcomes

The estimate tool validates the accepted estimate, derives a shopping list,
attaches an estimate by returning an updated Project Card value, and derives a
project summary. Invalid estimate arithmetic is rejected. Derivation does not
silently persist or confirm a Card mutation.

Relevant evidence:

- `docs/02-tools/ESTIMATE_MCP_MODEL.md`;
- `tools/estimate_tool.py`;
- `tests/test_estimate_tool.py`;
- `tests/test_shopping_list.py`.

## Verification

The repository's own `make check` command passed at the pinned commit:

```text
85 tests passed
Python compileall passed
three JSON schemas parsed successfully
generated Cabinet catalogue valid and current
```

The test set explicitly covers not-found reads, no-match/filtered searches,
invalid inputs, duplicate candidates, idempotent replay, stale revisions,
concurrent update exclusion, warning acknowledgement, source-storage truth,
estimate arithmetic rejection, and shopping-list consistency.

