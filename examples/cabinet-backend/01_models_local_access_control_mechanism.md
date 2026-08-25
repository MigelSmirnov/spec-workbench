# State 1 repair — local access-control credential mechanism

The concrete access-control backend was one class mixing storage, the
credential mechanism, and policy. The persistence-boundary decision
(`30_modules_persistence_boundary.md`) splits it; the mechanism needs two
support values and one repository port.

## Model M77 — IssuedCredentialSecret

Result of issuing one service credential by the deterministic credential
mechanism.

Fields:

- `credential_id: str`;
- `token: str` — the presentable bearer token `credential_id.secret`, returned
  exactly once and never persisted;
- `secret_hash: str` — the Argon2id verifier of the peppered secret; the only
  part stored.

### Identity

value

### Identity evidence

Substitution: equal credential id, token, and verifier are the same issuance.
Continuity: a new issuance is a new value; the token is never recomputed from
the verifier.

---

## Model M78 — PresentedCredentialSecret

A bearer token split into its selector and secret before verification.

Fields:

- `credential_id: str`;
- `secret: str`.

### Identity

value

### Identity evidence

Substitution: equal selector and secret are the same presentation. Continuity:
parsing is pure and never touches storage.

---

## Runtime interface

`AccessControlRepository` is the narrow PostgreSQL port for principals,
credential verifiers, throttle state, and append-only audit evidence. It owns
no authentication or authorization policy; `LocalAccessControlService` owns
the rules and uses `credential_security` for every cryptographic step.
