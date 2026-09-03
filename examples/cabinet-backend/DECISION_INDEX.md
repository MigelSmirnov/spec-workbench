# Cabinet Backend — Decision Index

## Status

Human-facing navigation index for accepted architectural decisions.

This document is not normative. Normative text is defined in the referenced design-state specifications.

For machine-readable State 2 → State 3 ownership coverage and handoff, `30_trace.json` is authoritative and must be validated through `tools/design_trace.py`. This index must not be interpreted as State 4 simply because it previously used a `04_` filename prefix.

---

## Decision navigation

### Invoice Card

| ID | Decision | Primary document |
|----|----------|------------------|
| A1 | Supported Invoice Card contract | 02_rules.md |
| A2 | Draft exclusion at eligibility gates (border rejection superseded by A77) | 02_rules.md |
| A3 | Explicit acceptance without source bytes | 02_rules.md |
| A4 | Cabinet owns semantic duplicate detection | 02_rules.md |
| A5 | Backend never edits Invoice Card | 02_rules.md |
| A6 | Initial Cabinet Card scope is Invoice Card V1 only | 02_rules.md |

### Source Package

| ID | Decision | Primary document |
|----|----------|------------------|
| A10 | Local source attachment through Backend | 02_rules.md |
| A11 | VPS retains working copies until manual release | 01_models.md / 02_rules.md |
| A12 | One Invoice Card owns one Source Package | 02_rules.md |
| A13 | Partial Source Package acceptance | 02_rules.md |

### Synchronization

| ID | Decision | Primary document |
|----|----------|------------------|
| A20 | Local-initiated pull synchronization | 01_models.md |
| A77 | A20 governs import admission; A2 border rejection superseded | 02_rules_import_admission.md |

### Registry

| ID | Decision | Primary document |
|----|----------|------------------|
| A31 | Unknown project does not reject an invoice | 02_rules.md |
| A32 | Closed project is not an error | 02_rules.md |
| A33 | Project status does not reject an invoice | 02_rules.md |
| A34 | Minimal Registry catalogue | 02_rules.md |
| A35 | One-way WorkObject projection | 02_rules.md |

### PresuPro

| ID | Decision | Primary document |
|----|----------|------------------|
| A40 | Estimate snapshots are immutable | 02_rules.md |
| A41 | Unmatched purchases are a valid analytical state | 02_rules.md |
| A42 | PresuPro semantic analysis belongs to Cabinet | 02_rules.md |
| A43 | Cabinet-owned PresuPro estimate snapshot semantics | 02_rules.md |

### Holded

| ID | Decision | Primary document |
|----|----------|------------------|
| A50 | Missing originals allowed for Client Portal but not Holded | 02_rules.md |
| A51 | Create one Holded purchase and verify it by GET | 02_rules.md |
| A52 | Marker-based Holded purchase create recovery | 02_rules.md |

### Platform boundary and security

| ID | Decision | Primary document |
|----|----------|------------------|
| A60 | Platform integrations belong to Cabinet Backend | 01_models.md |
| A61 | Separate machine and local-user identities | 02_rules.md |

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
