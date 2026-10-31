# State 2 — Registry artifact pointer rules: vocabulary, publication, withdrawal

Draft of 2026-10-31. The rules of artifact pointers (M05) that State 0 carried
here: publication as one transaction (L07) and who publishes and withdraws.
Which types are declared, and what a change of the vocabulary does to existing
pointers, is open (OQ-19).

## Accepted decision A07 — publication is one transaction

L07: v1 supersedes the previous pointer and inserts the new one in separate
commits, and two concurrent publishes of one type answer 500.

### Normative rules

1. Publishing a pointer assigns its version, marks the type's published
   pointer `superseded` with its instant, and stores the new pointer
   `published` — all in one transaction, or none of it (R0-17, R0-35).
2. Publishes of one type on one project are serialised: of two concurrent
   ones, each sees the other's result, and both are accepted with consecutive
   versions.
3. At every moment a project has at most one `published` pointer of a type.
4. Withdrawing marks the pointer `withdrawn` with its instant and principal in
   one transaction; it never makes an earlier version `published` (R0-14).
5. Publishing and withdrawing on an archived project are refused (R0-17);
   reading stays open.
6. A publish gives `uri`, `payload_ref` or both, each not blank (A02); its
   digest is stored as given, never computed or checked (R0-33).

### Formal invariants

```text
for each project p and type t:
  count(pointer of p, t with status published) <= 1
  versions of p, t are 1..n without gaps or repeats
publish(p, t) accepted:
  new.version = max(version of p, t) + 1 (or 1)
  previous published of p, t becomes superseded in the same transaction
```

### Required tests

1. Two concurrent publishes of `estimate` on one project make versions n+1 and
   n+2, the first `superseded`, the second `published`; neither answers an
   internal error.
2. A failure after the version is assigned leaves no superseded pointer and no
   new one.
3. After withdrawing the published pointer, 'read the latest artifact of a
   type' answers that none is published.
4. Publishing on an archived project is refused.

### Consequence

L07's partial state and internal error are gone; the history is gap-free.

## Accepted decision A08 — publishing and withdrawing as the token allows

### Normative rules

1. A producer service publishes only types whose owner service is the service
   its token names (R0-33); Cabinet Kernel publishes only its own types, for
   the agent, on a project of its session's set (R0-46, A10).
2. The owner publishes for any owner service: the pointer names the type's
   owner service, and its publisher is the owner (M05).
3. A pointer is withdrawn by the service that owns its type — Kernel for the
   agent only on its session's projects — or by the owner (R0-14).
4. A pointer the import brought in is withdrawn as any other: by its type's
   owner service or by the owner.
5. A type the specification does not declare is refused as an unknown type;
   a declared type not owned by the calling service is refused (R0-33).

### Formal invariants

```text
publish(t) by service s accepted => owner_service(t) = s
publish(t) by owner accepted   => pointer.owner_service = owner_service(t)
withdraw(x) by service s accepted => owner_service(x.type) = s
```

### Required tests

1. PresuPro publishing a type owned by another service is refused.
2. The owner publishes an `estimate`; the pointer names PresuPro as its owner
   service and the owner as its publisher.
3. Kernel withdrawing a pointer on a project outside its session's set is
   answered as not found (A10).

### Consequence

The pointer's owner service is always the type's (R0-33); the publisher
records who actually published (M05).

## Open question OQ-19 — the declared artifact types and a change of them

Carried from State 0: "the declared artifact vocabulary and what a change of it
does to existing pointers" (R0-33). Raised 2026-10-31; the owner takes it
separately from the other State 2 answers.

- Which types the first release declares, and the one owner service of each.
  The v1 sets (L08) are `wall_plan`, `plumbing_plan`, `electrical_plan`,
  `tiling_plan`, `estimate` and the services `walls`, `plumbing`,
  `electrical`, `tiling`, `presupro`, unrelated to each other; `estimate` by
  PresuPro and the types Cabinet Kernel publishes are in use today (State 1,
  "Declared vocabularies").
- What a release that removes a type does to its pointers. Proposed: they stay
  in the history, listed and read as before; publishing the type and 'read the
  latest artifact of a type' for it are refused as an unknown type. A type
  never changes its owner service: a move is a removal and a new type.
