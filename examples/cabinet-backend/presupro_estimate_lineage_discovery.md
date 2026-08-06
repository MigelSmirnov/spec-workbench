# PresuPro estimate lineage discovery for Cabinet Backend

## Status

Factual reconnaissance plan for PresuPro estimate identity, versions, and lineage.

This document does not define new Cabinet Backend behavior. Its purpose is to
verify whether PresuPro exposes enough authoritative evidence to distinguish:

- a new revision of an existing estimate;
- a separate estimate for the same project;
- an accepted or frozen estimate;
- a replacement or superseding estimate.

Cabinet Backend must not infer lineage from similar content, project identity, or
timestamps alone.

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

## Minimum safe Cabinet Backend rule before discovery closes

Until authoritative PresuPro lineage is verified:

1. Every imported estimate content becomes an immutable snapshot.
2. PresuPro estimate identity is preserved exactly as received.
3. A content change creates a new Cabinet Backend snapshot.
4. Cabinet Backend does not infer `estimate_family_id`.
5. Cabinet Backend does not infer predecessor or replacement relationships.
6. Two estimates for the same project remain independent.
7. Similar line content is not version evidence.
8. Confirmed invoice matches remain attached to their original snapshot.

---

## Questions to close OQ-002

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

Version-family semantics must remain open until PresuPro provides explicit,
verified lineage or the product accepts a contract extension.
