# Cabinet Backend — PresuPro Estimate Snapshot Semantics

## Status

Accepted clarification for `02_rules.md`.

This rule is based on the factual reconnaissance recorded in
`presupro_estimate_lineage_discovery.md`.

It defines how Cabinet Backend preserves PresuPro estimate content when PresuPro
does not expose authoritative revision-family or predecessor semantics.

---

## Verified PresuPro facts

The current PresuPro contract behaves as follows:

1. `Estimate.id` is the stable identity of one mutable PresuPro estimate record.
2. Editing preserves `Estimate.id` and `created_at`.
3. Editing changes `updated_at`.
4. Editing overwrites the same stored estimate record.
5. PresuPro does not retain previous estimate content.
6. PresuPro exposes no estimate revision table, history table, content hash,
   family identifier, predecessor, replacement, supersession, or copy reference.
7. A new estimate with equivalent content and a different ID is indistinguishable
   from an independent estimate.
8. Multiple independent estimates may reference the same Registry project.
9. Status values such as `accepted` and `archived` do not themselves block edit.
10. Conversion creates `invoice_ref`, sets `locked = true`, and prevents later
    content modification.
11. Export preserves only the current estimate identity, status, and timestamps.
12. Export does not preserve lineage because no lineage exists in the current
    PresuPro contract.

---

## Accepted decision — Cabinet-owned immutable snapshots

Cabinet Backend preserves every observed PresuPro estimate content state as an
immutable `EstimateSnapshot`.

PresuPro remains authoritative for the current mutable estimate record.
Cabinet Backend becomes authoritative for the immutable evidence it has already
accepted.

---

## Snapshot identity

Every `EstimateSnapshot` must contain at least:

```text
snapshot_id
presupro_estimate_id
content_hash
observed_at
presupro_updated_at
project_id
status
locked
content
```

The exact storage model belongs to the implementation specification.

### Stable source identity

`presupro_estimate_id` preserves the exact PresuPro `Estimate.id`.

Several Cabinet Backend snapshots may share the same
`presupro_estimate_id`.

```text
one PresuPro Estimate.id -> zero or more immutable EstimateSnapshots
```

---

## Snapshot creation

Cabinet Backend creates a new snapshot when the accepted PresuPro estimate
content differs from the latest stored snapshot for the same
`presupro_estimate_id`.

Comparison must use canonical content hashing or an equivalent deterministic
content comparison.

A change in `updated_at` alone is not sufficient when the content is unchanged.

A content change is sufficient even when PresuPro preserves the same
`Estimate.id`.

---

## Idempotency

Repeating import of the same canonical estimate content must not create a
duplicate snapshot.

```text
same presupro_estimate_id
and same canonical content_hash
-> same logical EstimateSnapshot
```

Operational import attempts may be recorded separately.

---

## No inferred lineage

Cabinet Backend must not infer any of the following:

```text
estimate_family_id
previous_estimate_id
next_estimate_id
replaces_estimate_id
supersedes_estimate_id
copied_from_estimate_id
revision_number
```

These relationships do not exist in the verified PresuPro contract.

Cabinet Backend must not infer lineage from:

- shared Registry project;
- similar or identical line content;
- nearby timestamps;
- supplier overlap;
- estimate naming;
- user-visible numbering;
- one estimate being created after another.

---

## Different PresuPro IDs

Different `presupro_estimate_id` values always represent independent estimates
for Cabinet Backend unless a future accepted PresuPro contract explicitly
provides lineage.

This remains true when:

- both estimates belong to the same project;
- both contain identical lines;
- one appears to be a manual copy of the other.

---

## Snapshot sequence

Cabinet Backend may order snapshots observed for the same
`presupro_estimate_id` by local observation time and PresuPro `updated_at`.

This order is an observation sequence only.

It must not be described as authoritative PresuPro revision lineage.

Allowed terminology:

```text
earlier observed snapshot
later observed snapshot
```

Disallowed terminology without a future contract:

```text
parent revision
child revision
official version 2
superseding estimate
replacement estimate
```

---

## Matching behavior

Confirmed invoice-line matches remain pinned to the exact
`EstimateSnapshot.snapshot_id` used when the match was accepted.

A later snapshot for the same `presupro_estimate_id` must not:

- move existing matches;
- rewrite existing matches;
- inherit existing matches automatically;
- invalidate the old snapshot;
- delete analytical history.

A later snapshot may be used for new matching decisions only.

---

## Locked and converted estimates

When PresuPro reports:

```text
locked = true
```

Cabinet Backend preserves that fact in the snapshot.

A lock indicates that PresuPro currently rejects later content modification for
that estimate record.

The lock does not create missing revision lineage and does not turn prior mutable
states into PresuPro-authored historical revisions.

---

## Status handling

Cabinet Backend stores the raw PresuPro status value.

Because the Backend accepts arbitrary status strings and the five common values
are frontend conventions, Cabinet Backend must not infer lifecycle guarantees
from status alone.

In particular:

```text
status = accepted
```

does not prove immutability.

```text
status = archived
```

does not prove immutability.

Only verified `locked = true` is accepted as evidence that PresuPro currently
blocks content edits.

---

## Formal invariants

Snapshot immutability:

```text
EstimateSnapshot content never changes after acceptance
```

Same-record history:

```text
multiple snapshots may share one presupro_estimate_id
```

Independent identities:

```text
different presupro_estimate_id values -> independent estimates
```

No inferred family:

```text
estimate_family_id is absent unless supplied by a future accepted contract
```

Match stability:

```text
confirmed match -> exact immutable snapshot_id
```

---

## Required tests

1. First import of an estimate creates one immutable snapshot.
2. Re-import of identical content does not create a duplicate snapshot.
3. Editing PresuPro content under the same `Estimate.id` creates a new snapshot.
4. The previous snapshot remains unchanged and queryable.
5. A timestamp-only change with identical content does not require a new logical
   snapshot.
6. Two estimates with different IDs remain independent even when content is
   identical.
7. Two estimates for one project are not grouped into one family.
8. A later snapshot does not inherit confirmed invoice-line matches.
9. Existing matches remain linked to the original snapshot.
10. Raw status is preserved without assuming immutability.
11. `locked = true` is preserved without inventing predecessor or revision
    semantics.
12. Export metadata does not create lineage that PresuPro does not provide.

---

## Resolution of OQ-002

`OQ-002` is resolved for the current PresuPro contract as follows:

- Cabinet Backend stores immutable snapshots for each observed content state;
- snapshots may share the same PresuPro estimate ID;
- different PresuPro estimate IDs are independent estimates;
- Cabinet Backend does not model estimate family, predecessor, replacement, or
  supersession semantics;
- explicit lineage requires a future accepted PresuPro contract extension.

---

## Consequence

Cabinet Backend preserves reliable historical estimate evidence without
pretending that PresuPro supplies version-family semantics.

The design remains safe under PresuPro's current mutable-record model and can be
extended later if PresuPro introduces explicit lineage.
