# State 6 — contract-only types and ports

## Status

These declarations complete exact-contract authoring without adding product
behavior. `PlanActualRequest` lowers the canonical State 1 value model that
pins already accepted evidence. `AccessControlBackend` is the narrow runtime
port required by deterministic HTTP authentication/authorization wiring.

---

## `PlanActualRequest`

Identity: value, as established by State 1 model M55.

Fields:

- `invoice_revisions: tuple[InvoiceCardRevisionReference, ...]`;
- `project_id: str`;
- `estimate_snapshot_id: str`;
- `match_ids: tuple[str, ...]`;
- `assumption_ids: tuple[str, ...]`.

The DTO carries identities only. `module:plan_actual` resolves the referenced
accepted records and rejects missing, stale, incompatible, or unconfirmed
references. It never accepts embedded mutable invoice/estimate replacements.

---

## `AccessControlBackend`

Kind: interface.

This is the runtime port held by deterministic HTTP app state. It belongs to the
`access_control` boundary and contains no product policy of its own; the concrete
implementation enforces the already accepted authentication, revocation,
capability, and audit rules.

Canonical method contracts are declared in `60_contracts.json`:

- `AccessControlBackend.authenticate`;
- `AccessControlBackend.authorize`.

The port is the only State 6 dependency introduced specifically for Router
wiring. Other module persistence/transport mechanics remain hidden inside their
deep module contracts until separate accepted evidence requires an exported
interface.

---

## Router framework symbols

The deterministic HTTP backend uses the framework types `FastAPI` and `Request`
as external contract types for the physical `api` / `api_irregular` adapter
modules. These are transport types, not domain models, and must be bound by the
final third-party imports required by `http_router_backend/v1`.
