# State 2 — Registry artifact pointer rules: vocabulary, publication, withdrawal

Draft of 2026-10-31. The rules of artifact pointers (M05) that State 0 carried
here: publication as one transaction (L07), who publishes and withdraws
(R0-88), and the declared vocabulary and what a change of it does (R0-33).

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

## Accepted decision A08 — the agent and the owner link; services do not publish

### Normative rules

1. A pointer is published and withdrawn by Cabinet Kernel for the agent, on a
   project of its session's set (R0-46, A10), or by the owner (R0-88).
2. No service token has the right to publish or withdraw (A09); a service is
   refused whatever type it names.
3. The pointer names the owner service the declared vocabulary fixes for its
   type (R0-33); the caller does not choose it.
4. The pointer records its publisher: Kernel for the agent naming the session,
   or the owner (M05). A withdrawal records its principal the same way.
5. Any declared type may be published and withdrawn by either; a type the
   specification does not declare is refused as an unknown type (R0-33).
6. A pointer the import brought in is withdrawn as any other.

### Formal invariants

```text
publish or withdraw accepted => caller in {Kernel for a session s with
                                project in granted(s), owner}
pointer.owner_service = owner_service(pointer.type)
```

### Required tests

1. PresuPro calling 'publish an artifact pointer' is refused.
2. Kernel publishes an `estimate` for session S; the pointer names PresuPro as
   its owner service and Kernel for S as its publisher.
3. Kernel withdrawing a pointer on a project outside its session's set is
   answered as not found (A10).
4. The owner withdraws a pointer Kernel published; the withdrawal records the
   owner.

### Consequence

Every pointer is a link someone on the agent's checked path or the owner made
(R0-88); the owner service always says where the document lives.

## Accepted decision A22 — one declared type; the vocabulary changes only by a release

Carried from State 0: "the declared artifact vocabulary and what a change of it
does to existing pointers" (R0-33). The owner accepted it on 2026-10-31 with
R0-88.

### Normative rules

1. The first release declares one type: `estimate`, owner service PresuPro
   (R0-88). The v1 types (L08) are not declared.
2. The declared types are part of the specification and of the release; a
   running instance reads them from its release, never from its configuration
   or its store (R0-33).
3. A release that adds a type accepts publishes of it from that release on.
4. A release that removes a type keeps every pointer of it: they stay in the
   history and are listed and read as before, with their status as it was.
5. After the removal, publishing that type and 'read the latest artifact of a
   type' for it are refused as an unknown type, and withdrawing a pointer of it
   is refused.
6. A type never changes its owner service; a move is a removal and a new type.
7. An import file holding a pointer of an undeclared type is refused as a
   malformed record (A16).

### Formal invariants

```text
declared_types(first release) = {estimate -> PresuPro}
pointers are never removed or rewritten by a vocabulary change
publish(t) or latest(t) with t not declared => unknown type
```

### Required tests

1. Publishing `wall_plan` is refused as an unknown type.
2. After a release without a type, its pointers are still listed by 'list
   artifacts' with their statuses.
3. 'Read the latest artifact of a type' for a removed type is refused as an
   unknown type, not answered as none published.

### Consequence

The manifest and the implementation agree on the vocabulary (R0-33, R0-78);
history survives any change of it.
