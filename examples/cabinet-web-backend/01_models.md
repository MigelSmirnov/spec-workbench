# State 1 — Cabinet Web Backend domain models

## Status

Accepted State 1 baseline derived from accepted State 0 and the implemented
Cabinet_web application at commit
`d3fac8e5d2b85c12904cba24060717b84e2757c2`.

This state defines domain meaning, identity, authority, lifecycle candidates,
and persistence candidates. It does not select Python classes, HTTP or MCP
schemas, database tables, repositories, storage paths, or transport algorithms.

## Modeling boundary

The server preserves the existing Provider, Client, Project, and Invoice Card
meanings. It does not replace them with a generic Card payload. The server adds
only the runtime concepts already required by State 0: authenticated actor
provenance, idempotent Cabinet effects, original-source custody, Invoice pull
evidence, and the compact Registry catalogue replica.

The local `cabinet_backend` models remain externally owned. Equal names in the
two applications mean an intentionally shared boundary concept only when this
state says so explicitly.

## Model M01 — ActorReference

### Meaning

Immutable provenance describing which accepted interaction caused a Cabinet
read or change, without embedding a credential or ChatGPT account object.

Candidate fields:

- `actor_type`: `human`, `agent`, `service`, `operator`, or `system`;
- `principal_id`;
- `channel`: `chatgpt_plugin`, `browser`, `local_backend`, or `operator`;
- `interaction_id` optional;
- `display_label` optional.

### Identity

value

### Identity evidence

Substitution: equal actor, principal, channel, and interaction facts carry the
same provenance meaning. Continuity: authentication state is not managed by
this value; a later interaction creates another value.

### Source of truth

The authenticated Cabinet Web application boundary that accepted the action.

### Lifecycle candidate

No independent lifecycle; issued as immutable provenance.

### Persistence candidate

Embedded in durable Card revisions, effect records, upload evidence, and
synchronization evidence when provenance is required.

### Open questions

None.

## Model M02 — CabinetPrincipal

### Meaning

The stable server-side subject to which Cabinet Web authorizes capabilities.
The first release has one human owner principal, distinct machine principals
for participating local Backend nodes, and a protected operator boundary.

Candidate fields:

- `principal_id`;
- `principal_kind`: `cabinet_owner`, `local_backend_node`, or `operator`;
- `status`: `active` or `revoked`;
- `created_at`;
- `revoked_at` optional.

Credential material, Basic Auth secrets, tunnel secrets, and tokens are not
fields of this entity.

### Identity

entity

### Identity evidence

Substitution: two principal IDs are never interchangeable even if their current
capabilities match. Continuity: the same principal remains identifiable while
its status and authorized capability set change.

### Source of truth

Cabinet Web's protected principal enrollment and revocation boundary. The
single human principal may be reached through ChatGPT plugin or browser
authentication, but neither channel creates a second business user.

### Lifecycle candidate

`active -> revoked`.

### Persistence candidate

Durable server security record; credentials are stored separately as protected
configuration or credential records selected in State 2.

### Open questions

None.

## Model M03 — CardRevisionReference

### Meaning

An immutable pin to one exact accepted revision of a Cabinet-owned Card.

Candidate fields:

- `card_id`;
- `card_type`;
- `content_hash`;
- `card_format_version` when the Card type defines one;
- `observed_status`;
- `observed_at`.

### Identity

value

### Identity evidence

Substitution: equal Card ID, type, content hash, format version, status, and
observation facts are interchangeable. Continuity: a later Card revision
produces another value.

### Source of truth

Derived from the exact accepted canonical Card content.

### Lifecycle candidate

No independent lifecycle.

### Persistence candidate

Embedded wherever an exact Card revision must be reviewed, updated, uploaded,
transferred, acknowledged, or audited.

### Open questions

None.

## Model M04 — ValidationIssue

### Meaning

One structured, user-visible problem or warning found while preparing or
validating existing Cabinet data.

Candidate fields:

- `severity`: `error` or `warning`;
- `code`;
- `field_path` optional;
- `message`;
- `expected` optional scalar display value;
- `actual` optional scalar display value.

### Identity

value

### Identity evidence

Substitution: equal issue facts are interchangeable in a validation result.
Continuity: an issue has no continuing identity and is recalculated for an
exact input revision.

### Source of truth

The accepted type-specific Cabinet validator or deterministic derivation.

### Lifecycle candidate

No independent lifecycle.

### Persistence candidate

Returned on demand and optionally embedded in exact revision/effect evidence;
never the source of truth for Card facts.

### Open questions

None.

## State 1 document map

- `01_models_cards.md` — existing Cabinet-owned Cards and issued project
  artifacts;
- `01_models_ingress.md` — plugin effects and original-source custody;
- `01_models_sync.md` — Invoice pull and Registry catalogue boundary models.

## State 1 readiness assessment

The model set is ready for State 2 rule authoring when the State 1 gate remains
clean because:

- every existing Cabinet Card type in the accepted State 0 inventory has a
  distinct entity model and source of truth;
- Card identity, Card revision identity, logical source identity, and exact
  source-byte identity are distinct;
- ChatGPT/browser actor provenance is distinct from authentication principal
  and from reusable credentials;
- an idempotent Cabinet effect is distinct from the Card revision it changes;
- upload authorization is distinct from source custody and from Card source
  identity;
- Registry project facts remain external snapshots and do not become Project
  Card master data;
- Invoice package issuance is distinct from local durable acceptance receipt;
- Registry catalogue delivery is distinct from the accepted VPS replica and
  acknowledgement;
- unknown transfer outcome and incompatible-revision conflict have durable
  identities rather than generic status prose;
- every runtime model has explicit value/entity identity evidence, authority,
  lifecycle candidate, persistence candidate, and no hidden identity question.

Deterministic State 1 gate result:

```text
models                 29
identity errors         0
warnings                0
open questions          0
placeholder findings    0
STATE 1                 PASS
```
