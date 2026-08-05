# Cabinet Backend — Decision Index

## Status

Navigation index for accepted architectural decisions.

This document is not normative.
Normative text is defined in the referenced specifications.

---

## Accepted decisions

### Invoice Card (A1–A9)

| ID | Decision | Primary document |
|----|----------|------------------|
| A1 | Supported Invoice Card contract | 02_rules.md |
| A2 | Backend accepts only confirmed Invoice Cards | 02_rules.md |
| A3 | Explicit acceptance without source bytes | 02_rules.md |
| A4 | Cabinet owns semantic duplicate detection | 02_rules.md |
| A5 | Backend never edits Invoice Card | 02_rules.md |

### Source Package (A10–A19)

| ID | Decision | Primary document |
|----|----------|------------------|
| A10 | Local source attachment through Backend | 02_rules.md |
| A11 | VPS retains working copies until manual release | 01_models.md / 02_rules.md |
| A12 | One Invoice Card owns one Source Package | 02_rules.md |

### Synchronization (A20–A29)

| ID | Decision | Primary document |
|----|----------|------------------|
| A20 | Local-initiated pull synchronization | 01_models.md |
| A21 | Synchronization Package is the transfer unit | 01_models.md |

### Registry (A30–A39)

| ID | Decision | Primary document |
|----|----------|------------------|
| A30 | Project completion remains manual | 01_models.md |
| A31 | Unknown project does not reject an invoice | 02_rules.md |
| A32 | Closed project is not an error | 02_rules.md |

### PresuPro (A40–A49)

| ID | Decision | Primary document |
|----|----------|------------------|
| A40 | Estimate snapshots are immutable | 02_rules.md |
| A41 | Unmatched purchases are a valid analytical state | 02_rules.md |
| A42 | PresuPro semantic analysis belongs to Cabinet | 02_rules.md |

### Holded (A50–A59)

| ID | Decision | Primary document |
|----|----------|------------------|
| A50 | Missing originals allowed for Client Portal but not Holded | 02_rules.md |

### Platform boundary (A60–A69)

| ID | Decision | Primary document |
|----|----------|------------------|
| A60 | Platform integrations belong to Cabinet Backend | 01_models.md |

---

## Rejected decisions

Reserved.

---

## Open questions

See:

- 03_open_questions.md

---

## Identifier policy

- **A** — Accepted decision
- **R** — Rejected decision
- **OQ** — Open question
- Accepted-decision identifiers are allocated by architectural area.
- Unused identifiers inside a range are reserved for future decisions in that area.
- Once allocated, an identifier remains stable even if the decision text or primary document changes.

| Range | Architectural area |
|-------|--------------------|
| A1–A9 | Invoice Card |
| A10–A19 | Source Package |
| A20–A29 | Synchronization |
| A30–A39 | Registry |
| A40–A49 | PresuPro |
| A50–A59 | Holded |
| A60–A69 | Platform boundary |
