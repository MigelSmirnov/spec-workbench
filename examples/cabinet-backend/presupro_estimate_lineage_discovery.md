# PresuPro estimate lineage discovery for Cabinet Backend

## Status

Factual reconnaissance record for PresuPro estimate identity, versions, and
lineage.

This document does not define new Cabinet Backend behavior. Its purpose is to
verify whether PresuPro exposes enough authoritative evidence to distinguish:

- a new revision of an existing estimate;
- a separate estimate for the same project;
- an accepted or frozen estimate;
- a replacement or superseding estimate.

Cabinet Backend must not infer lineage from similar content, project identity, or
timestamps alone.

---

## Discovery result — 2026-08-06

The current PresuPro contract does not expose authoritative estimate-family or
revision lineage.

The observed behavior is:

1. `Estimate.id` is the stable identity of one mutable PresuPro estimate record.
2. Editing preserves `Estimate.id` and `created_at`, changes `updated_at`, and
   overwrites the same SQLite row.
3. PresuPro does not retain the previous estimate content.
4. There is no estimate revision table, history table, content hash, revision
   number, family identifier, predecessor, replacement, supersession, or copy
   reference.
5. There is no duplicate or copy endpoint. A client may submit equivalent content
   under a new ID, but the result is indistinguishable from an independent
   estimate.
6. Multiple independent estimates may reference the same Registry project.
7. `accepted` and `archived` do not block editing.
8. The Backend accepts arbitrary status strings; the five named statuses are a
   frontend convention rather than a validated Backend lifecycle contract.
9. Conversion creates `invoice_ref` and sets `locked = true`. The storage layer
   then rejects content changes to that record.
10. XLSX export preserves current estimate identity, status, and timestamps but
    contains no lineage fields. No estimate-import path exists.

This corresponds to Outcome B for ordinary edits: stable estimate identity with
no revision history. It also corresponds to Outcome D for client-created copies:
copy and independent estimate are indistinguishable.

Therefore the existing PresuPro contract cannot provide explicit family,
predecessor, replacement, or supersession semantics. If Cabinet Backend requires
those semantics, PresuPro needs an accepted contract extension. `OQ-002` can be
resolved for the current contract only by explicitly accepting that Cabinet does
not infer lineage from shared project identity, similar content, or timestamps.

### Evidence baseline

```text
PresuPro project: PresuPro_sandbox
repository commit: ef80666906a1e1aabcfe6441b67f314b56976aeb
accepted base spec SHA-256:
4536ede04f8d87b6421fb3c2bcb31251479717814ce98063f41066d3ddf6872c
terminal verification run: 20260720_225003
terminal verdict: PASS
observed_at: 2026-08-06
```

The scoped PresuPro project files were clean at the repository commit above. An
untracked pre-existing research file was present but was not used as runtime
state and was not modified.

### Repository evidence

| Question | Observed fact | Evidence |
|----------|---------------|----------|
| Canonical identity | `Estimate.id` | `core/models.py`, `Estimate` |
| Client-supplied identity | Create request may supply `id`; duplicate existing ID returns HTTP `409` | `core/models.py`, `CreateEstimateRequest`; `backend/api/routes.py`, `create_estimate_endpoint` |
| Edit identity | Update constructs a replacement with the existing ID and `created_at` | `backend/services/estimates.py`, `estimate_from_request` |
| Persistence | `id` is the SQLite primary key; `ON CONFLICT(id)` updates the same row | `backend/storage/schema.py`; `backend/storage/estimates.py`, `upsert_estimate` |
| Revision history | No revision/history table or lineage columns exist | `backend/storage/schema.py` and runtime SQLite inspection |
| Duplicate workflow | No duplicate/copy route, service, frontend action, or MCP tool exists | `backend/api/routes.py`; `frontend/api.js`; `mcp/presupro_mcp_server.py` |
| Status values | Backend stores an unrestricted string; frontend lists `draft`, `sent`, `accepted`, `rejected`, `archived` | `core/models.py`, `Estimate.status`; `frontend/engine.js` |
| Lock | Conversion stores `invoice_ref` and `locked = true`; storage rejects later field changes | `backend/services/invoicing.py`; `backend/storage/estimates.py` |
| Export | Current ID, status, `created_at`, and `updated_at` are exported; lineage is absent | `backend/services/exporter.py` |

### Runtime experiment P1 — create and edit

An estimate with ID `est-lineage-e1` was created in an isolated temporary SQLite
database and then edited through the HTTP API.

Observed:

```text
create HTTP = 200
edit HTTP = 200
id preserved = true
created_at preserved = true
updated_at changed = true
content replaced = true
rows for estimate ID = 1
rows retaining old content = 0
history/revision tables = none
lineage columns = none
```

The old line content could not be reconstructed after the edit.

### Runtime experiment P2 — duplicate or copy

No dedicated duplicate operation exists.

Observed through the create API:

```text
repeat create with same ID = HTTP 409, "Estimate already exists"
same content with a new ID = HTTP 200
lineage fields on new estimate = none
```

The new-ID record is structurally identical to an independent estimate. PresuPro
does not record that it was copied.

### Runtime experiment P3 — multiple estimates in one project

Two estimates with different IDs were created against the same isolated Registry
project snapshot.

Observed:

```text
first create HTTP = 200
second create HTTP = 200
Registry project_id equal = true
estimate IDs distinct = true
family grouping = none
```

Registry project identity is therefore not estimate-family identity.

### Runtime experiment P4 — status and edit behavior

Observed:

```text
arbitrary status "frozen-by-probe" accepted = HTTP 200
accepted status stored = HTTP 200
edit after accepted = HTTP 200
accepted locked = false
archived status stored = HTTP 200
edit after archived = HTTP 200
archived locked = false
```

No tested status value froze the estimate by itself.

### Runtime experiment P5 — post-conversion lock

The existing conversion workflow was exercised with the Holded contact and
document calls replaced by isolated test doubles. No real Holded request was
made.

Observed:

```text
conversion from accepted = HTTP 200
invoice_ref stored = true
locked = true
content edit after lock = rejected
HTTP result of locked edit = 500
stored content changed = false
```

The storage rejection is `ValueError("Cannot modify locked estimate fields")`.
The update route does not currently map this storage error to a client-level
`409`, so the HTTP surface returns `500` even though persistence remains
unchanged.

### Runtime experiment P6 — export

An XLSX export was generated from an isolated estimate and its Summary worksheet
was inspected.

Observed:

```text
estimate_id present = true
status present = true
created_at present = true
updated_at present = true
version/revision/family/predecessor/copy/content_hash fields = none
estimate import endpoint or service = none
```

Export preserves only the current mutable record identity and timestamps. It does
not make the exported estimate an authoritative immutable revision.

### Test evidence

The complete PresuPro test suite passed after the reconnaissance:

```text
67 passed
46 deprecation warnings
```

The warnings concern FastAPI `on_event` deprecation and do not provide estimate
lineage evidence.

### Discovery limitations

- Runtime operations used temporary SQLite databases and synthetic project data.
- The Registry resolver was replaced with an isolated test snapshot.
- Holded calls in the conversion experiment were replaced with test doubles.
- No existing user estimate, PresuPro database, or Holded document was modified.
- No product code, canonical PresuPro spec, or Cabinet Backend normative rule was
  changed.

---

## Current accepted Cabinet Backend baseline

The following behavior is already accepted:

1. Every imported `EstimateSnapshot` is immutable.
2. A changed estimate creates a new snapshot.
3. Existing invoice-line matches remain pinned to the exact snapshot used when
   the match was confirmed.
4. Matches are never moved automatically to a newer estimate.
5. Cabinet owns semantic matching.
6. Cabinet Backend stores accepted snapshots and confirmed matching results.
7. A new estimate snapshot does not inherit confirmed matches automatically.

The open question is only how Cabinet Backend identifies estimate families and
version relationships from PresuPro evidence.

---

## Required repository reconnaissance

Inspect the accepted PresuPro project and record evidence from:

```text
models
schemas
database migrations
repositories
services
HTTP routes
frontend contracts
exports
tests
fixtures
```

Search specifically for:

```text
estimate_id
version
revision
estimate_family_id
parent_estimate_id
previous_estimate_id
replaces
supersedes
source_estimate_id
copied_from
duplicated_from
status
accepted
approved
frozen
locked
archived
created_at
updated_at
content_hash
```

Do not treat field names as semantic proof without checking their actual use.

---

## Identity questions

### Stable estimate identity

Determine:

1. What field is the canonical estimate identifier?
2. Who creates it?
3. Can a client supply it?
4. Does editing preserve the same identifier?
5. Does duplication create a new identifier?
6. Does conversion or acceptance create a new identifier?
7. Is the identifier stable across exports and API responses?

### Project relationship

Determine:

1. Can one project contain multiple independent estimates?
2. Is project identity sufficient to group estimates?
   Expected answer: no, unless PresuPro explicitly guarantees otherwise.
3. Can one estimate move between projects?
4. Can an estimate exist without a project?

---

## Version and lineage questions

Determine whether PresuPro exposes any authoritative relationship equivalent to:

```text
estimate_family_id
previous_estimate_id
parent_estimate_id
replaces_estimate_id
supersedes_estimate_id
revision_number
```

For each candidate field or behavior, verify:

- where it is stored;
- who writes it;
- whether it is immutable;
- whether it survives export/import;
- whether tests enforce its semantics;
- whether it distinguishes revision from duplication.

A numeric `version` field must not be accepted as estimate lineage until it is
confirmed that the field belongs to the estimate itself rather than to an export,
artifact, API schema, or unrelated document.

---

## Edit behavior

Run or inspect tests for the following sequence:

1. Create estimate E1.
2. Record its canonical identity and timestamps.
3. Edit one line.
4. Read the estimate again.
5. Determine whether:
   - the same record is overwritten;
   - a new revision record is created;
   - history is retained;
   - only `updated_at` changes;
   - a version or predecessor reference changes.

Record whether PresuPro can reconstruct the pre-edit content after the edit.

If old content is not retained, Cabinet Backend must snapshot it at import time.

---

## Duplication behavior

Verify the PresuPro copy or duplicate workflow, if one exists.

Determine:

1. whether duplication creates a new `estimate_id`;
2. whether the new estimate points to the source;
3. whether the relationship means revision, template copy, or independent estimate;
4. whether the user can duplicate across projects;
5. whether later edits preserve any source relationship.

A `copied_from` relationship must not automatically be interpreted as version
lineage.

---

## Acceptance and freezing behavior

Determine whether PresuPro has a state equivalent to:

```text
draft
accepted
approved
frozen
locked
converted
archived
```

For each real state:

- identify the exact stored value;
- identify the transition operation;
- determine whether editing remains possible afterward;
- determine whether a new estimate must be created for changes;
- determine whether the state is authoritative for Cabinet import.

Specifically verify whether conversion to an invoice or Holded document blocks
further estimate editing and whether that block is reversible.

---

## Runtime experiments

Use an isolated test project and record each operation.

### Experiment P1 — create and edit

```text
create estimate
read identity
edit one line
read again
compare identity, timestamps, version fields, and retained history
```

### Experiment P2 — duplicate

```text
duplicate estimate
compare source and copy identity
inspect parent/source links
edit the copy
verify whether the relationship remains
```

### Experiment P3 — multiple estimates in one project

```text
create two independent estimates for one project
verify how they are distinguished
verify whether any family grouping is present
```

### Experiment P4 — accept or lock

```text
move estimate through every supported lifecycle transition
verify edit permissions and stored status
```

### Experiment P5 — post-conversion behavior

```text
convert estimate through the existing PresuPro workflow
verify stored reference, lock state, and later edit behavior
```

### Experiment P6 — export and import

When export exists:

```text
export estimate
inspect identity and lineage fields
re-import or parse export
verify whether relationships survive
```

---

## Evidence record

For every experiment, preserve:

```text
experiment_id
repository commit
environment
operation
request or service call
estimate identity before
estimate identity after
project identity
status before
status after
timestamps
lineage fields
content changes
database rows
API response
test result
observed_at
```

Do not commit credentials, production data, or personal customer information.

---

## Possible outcomes

### Outcome A — explicit lineage exists

PresuPro exposes stable family and predecessor semantics.

Cabinet Backend may store those authoritative identifiers with each
`EstimateSnapshot`.

### Outcome B — stable estimate identity, no revision history

Editing preserves one `estimate_id`, but old content is overwritten.

Cabinet Backend must create immutable snapshots on every observed content change.
Snapshots may share the same PresuPro `estimate_id`, but no predecessor relation
may be claimed unless separately evidenced.

### Outcome C — new identity per revision, explicit predecessor absent

Cabinet Backend may store each identity independently but must not infer they are
versions of one family from project and content similarity.

A PresuPro contract extension may be required.

### Outcome D — duplication and revision are indistinguishable

Cabinet Backend must treat every new estimate identity as an independent estimate
unless a user or future PresuPro contract explicitly supplies lineage.

---

## Safe Cabinet Backend baseline derived from discovery

Under the verified current PresuPro contract:

1. Every imported estimate content becomes an immutable snapshot.
2. PresuPro estimate identity is preserved exactly as received.
3. A content change creates a new Cabinet Backend snapshot.
4. Cabinet Backend does not infer `estimate_family_id`.
5. Cabinet Backend does not infer predecessor or replacement relationships.
6. Two estimates for the same project remain independent.
7. Similar line content is not version evidence.
8. Confirmed invoice matches remain attached to their original snapshot.

---

## Questions answered by discovery

1. What is the canonical stable PresuPro estimate identifier?
2. Does editing preserve or replace that identifier?
3. Does PresuPro retain historical estimate content?
4. Can one project contain several independent estimates?
5. Is there an explicit estimate-family identifier?
6. Is there an explicit predecessor, replacement, or supersession link?
7. How is duplication represented?
8. What statuses prevent further editing?
9. Does conversion create or imply a frozen version?
10. Which identity and lineage fields survive export?

---

## Consequence

Cabinet Backend can safely preserve immutable estimate evidence today.

Accepted decision A43 in `02_rules.md` resolves OQ-002 for the current contract
by defining Cabinet-owned immutable snapshots and prohibiting inferred lineage.
Version-family semantics are not part of the current PresuPro contract; adding
them later requires an explicit, verified contract extension.
