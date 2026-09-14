# Cabinet Backend — open questions

## Status

This document records decisions that are intentionally not resolved yet.

An entry here is not a placeholder and not an implementation TODO. It marks a
real dependency on another application's accepted contract, repository evidence,
or a later product decision.

Accepted behavior already defined in `01_models*.md` and `02_rules.md` remains
normative while these questions are open, except where a later design-state
refinement explicitly reopens an earlier decision after stronger source evidence.

---

## OQ-001 — Registry completion semantics

### Question

Should Registry expose a separate authoritative project-completion fact, distinct
from `active` and `archived`?

### Why it remains open

Registry discovery confirmed only `active` and `archived`. It does not reveal
whether an archived project was completed, cancelled, hidden administratively, or
archived for another reason.

### Current Cabinet Backend baseline

- `active` maps to normal project availability.
- `archived` maps to unavailable and requires review.
- a missing project maps to unavailable and requires review.
- `archived` is never interpreted as `completed`.
- no current Registry value produces `late_project_cost`.

### Required decision

- add a distinct Registry completion field or status and define its lifecycle; or
- keep completion outside Registry and identify its authoritative owner.

### Explicit non-decision

Cabinet Backend does not infer completion from `archived`, invoice timing,
project inactivity, or any other heuristic.

---

## OQ-002 — PresuPro estimate family and version lineage

**Status:** Resolved by accepted decision A43 in `02_rules.md`.

PresuPro exposes one stable mutable `Estimate.id` but no authoritative family,
predecessor, replacement, or revision lineage. Cabinet therefore stores every
observed content state as an immutable snapshot, permits several snapshots to
share one PresuPro estimate ID, treats different estimate IDs as independent,
and never infers lineage. See `presupro_estimate_lineage_discovery.md` for the
verified source behavior.

---

## OQ-003 — Registry catalogue exact field contract

**Status:** Resolved by accepted decision A34 in `02_rules.md`.

The compact catalogue contains `project_id`, `display_name`, `address`,
`status`, and `registry_updated_at`, projected from the full Registry project
list. See `registry_discovery.md` for the factual source contract and limitations.

---

## OQ-004 — Cabinet WorkObject catalogue application behavior

**Status:** Resolved by accepted decision A35 in `02_rules.md`.

Cabinet maintains at most one `WorkObject` for each observed Registry
`project_id`. Catalogue refreshes update only Registry-derived fields; Cabinet
fields, archived objects, and objects absent from a later catalogue remain
preserved. The projection is one-way and never writes to Registry.

---

## OQ-005 — Unverified Holded operations and revision reconciliation

### Question

Which Holded operations and status semantics can Cabinet Backend safely use after
the verified first purchase publication and create recovery defined by accepted
decisions A51 and A52?

### Current accepted constraints

- Holded publication is pinned to one exact confirmed Card revision;
- an invoice without required original evidence is not eligible for Holded;
- Cabinet Backend never edits an accepted Card revision;
- a later correction is a new confirmed Card revision;
- first publication uses exactly one POST followed by GET verification;
- every publication attempt has one stable marker and at most one automatic POST;
- ambiguous create recovery uses bounded list polling, exact marker matching, and
  GET verification without mutation;
- zero marker matches never authorize automatic retry;
- Holded-specific intermediate rounding does not rewrite Invoice Card totals.

### Remaining verification

Only the following Holded areas remain open in this question:

1. exact meaning of returned numeric status values;
2. PUT behavior and accounting consequences for an existing purchase;
3. purchase refund or rectification behavior and linkage to the source purchase;
4. attachment upload, listing, retrieval, and persistence behavior;
5. reconciliation of a later confirmed Invoice Card revision with an already
   published purchase.

### Explicit non-decisions

Until separately verified and accepted, Backend must not infer status semantics,
automatically update a purchase, create a refund, upload attachments, retry an
ambiguous POST, or reconcile a later Invoice Card revision by mutating Holded.

---

## OQ-006 — Additional Cabinet Card types in the local Backend

**Status:** Resolved by accepted decision A6 in `02_rules.md`.

The first Cabinet Backend implementation supports only `Invoice Card V1`.
Additional Cabinet Card types remain outside its offline, synchronization,
durability, and local-processing scope until each receives a separately accepted
contract.

---

## OQ-007 — Final authentication and authorization model

**Status:** Resolved by accepted decision A61 in `02_rules.md`.

Synchronization uses a unique per-installation node credential with
synchronization-only authority. Local mutations require an authenticated active
local user and the required role; agent actions use time-bounded local-user
delegation. Machine credentials, local identities, Holded credentials, roles,
sessions, and append-only audit evidence remain separate concerns.

---

## OQ-012 — PlanActual monetary comparison semantics

**Status:** Reopened after stronger source-contract evidence.

### Why it is open

The earlier accepted plan/actual decision used:

```text
planned_amount = EstimateItemSnapshot.total
actual_amount = InvoiceLine.total
```

Later factual probes established that neither alias is semantically closed:

- PresuPro does not currently expose one proved canonical per-item amount shared
  by the relevant representations;
- Invoice Card V1 has no `InvoiceLine.total`; it exposes distinct canonical
  `net_amount` and `gross_amount` values with different monetary/tax bases.

The owning refinements are:

```text
01_models_plan_actual_monetary_gap.md
02_rules_plan_actual_semantic_gap.md
```

The State 2 monetary decision is therefore reopened. Quantity semantics remain
accepted.

### Required product decisions

Flow 6 (VPS working-set release) is no longer an open question of this project:
A76 assigns the working set and release policy to Cabinet Web; cabinet_backend
exposes only its durable-acceptance evidence. The reciprocal wire fields are
frozen jointly before Cabinet Web State 6.

CardObjectAssignmentObservation is produced by Cabinet Web at capture, carried
inside the exact transfer package, and imported through
`registry_context.record_card_assignment_observation` by synchronization
(owner decision, 2026-08-23). `object.card_id` never maps implicitly to a
Registry project. Resolved.

PA-MONEY-001..003 were accepted by the owner on 2026-08-23
(`02_rules_plan_actual_semantic_gap.md`, "Accepted monetary decisions").

`PA-MONEY-001` must identify the authoritative planned item amount and its exact
monetary/tax basis.

`PA-MONEY-002` must choose the authoritative actual comparison amount from the
accepted Invoice Card V1 meanings (`net_amount` or `gross_amount`) and preserve
its source-owned basis.

`PA-MONEY-003` must define why the selected planned and actual values are directly
comparable or name explicit accepted evidence/assumptions for a deterministic
conversion.

### Current deterministic boundary

Until all three decisions are accepted:

- quantity-only PlanActual calculations may proceed when their unit preconditions
  are satisfied;
- full monetary PlanActual analysis is not semantically closed;
- no adapter, compiler, host, generated code, or model operation may choose the
  missing monetary meaning;
- missing monetary closure must fail explicitly rather than return a guessed or
  partially fabricated successful result.

### Explicit non-decisions

Cabinet does not currently:

- treat a PresuPro aggregate total as an item amount;
- select a Decimal source field by type equality;
- recreate `InvoiceLine.total`;
- default to Card `net_amount` or `gross_amount`;
- infer monetary basis from currency, locale, names, or integration context;
- perform implicit net/gross, tax-basis, or currency conversion.

---

## OQ-013 — Manual release of canonical working sets must work before the first object closes

**Status:** Open (owner decision 2026-09-15: release stays manual, per project).

### Why it is open

A11 here and the [Cabinet Web release rule](../cabinet-web-backend/02_rules_sync_operations.md)
keep the VPS working copies until the owner
explicitly releases the working set of one `project_id`, after the local
Backend has confirmed verified durable replicas of every required original.
The owner confirmed on 2026-09-15 that this is the intended shape: an object is
finite, its Invoices end, and release is the closing action — not an automatic
consequence of a receipt.

Two facts make the question urgent rather than academic:

- [Cabinet Web discovery](../cabinet-web-backend/02_rules_sync_operations.md) lists every ready manifest of every object until
  its working set is released; each local sync session re-pulls all of them.
  The cost is linear in the number of unreleased Invoices and ends only with
  release (2026-09-14: 13 Invoices, seconds).
- The [Cabinet Web admission rule](../cabinet-web-backend/02_rules_source_registration.md)
  (rule 9) refuses release for every canonical source set: the release command
  lacks the complete typed local verification its release rule requires. The
  local Backend already exposes that evidence
  (`durable_archive.verify_durable_acceptance`,
  `durable_archive.get_transfer_receipt`, A76), but no wire carries it into the
  release decision. When the first object closes, the owner cannot release it.

### What must be decided

1. The reciprocal wire: how the plugin asks this Backend, per manifest and per
   file hash, whether the replica is present, reopened and verified, and how
   that answer is bound to the exact release request (identity, replay,
   unknown outcome).
2. Which side owns the "released" transition of a working set and how
   discovery stops listing released manifests without deleting evidence the
   Backend has not confirmed.
3. Whether a receipt `accepted` may already remove a manifest from discovery
   while the bytes stay retained (a smaller change to the Cabinet Web discovery
   rule) — or whether discovery stays coupled to release.

### Not in question

- Automatic release after a receipt (rejected: release is the only irreversible
  loss point; the Backend's witnesses run on an in-memory unit of work and
  cannot vouch for persisted bytes).
- Filtering discovery by project (not designed; Cabinet Web discovery returns
  every available revision, the project assignment travels inside the package).

---

## OQ-014 — One injected clock for every module that produces a timestamp

**Status:** Open (owner decision 2026-09-15: close the class, do not keep repairing it).

### Why it is open

The case owns a system clock (`system_clock`, the `Clock` interface emitted by
`rules.system_clock_backend`), but only `registry_context` and
`holded_gateway` receive it. Seven modules read the wall clock themselves:

```text
access_control, durable_archive, holded_transport, synchronization,
catalogue_publication, plan_actual, holded_publication
```

Their only note about time is the boilerplate "every timestamp the service
produces is timezone-aware UTC; naive datetimes are never constructed". That
names a shape, not a source, so every regeneration invents the source anew
(`datetime.UTC`, `timezone.utc`, `utcnow()`). The Factory's static gate
`naive_datetime_now` catches the worst forms and a deterministic rewrite makes
the draft run (Route B 2026-09-14: two of four candidates were repaired this
way). The repair is honest about syntax and silent about design: the module
still ships a private clock no witness can stop or substitute, and the
"recurring clock problem" is the visible symptom of the unnamed source.

The ambient-time fuse of the workbench is deliberately narrow (the UTC
boilerplate does not count as an ambient effect), which is why these seven
modules pass admission today.

### What must be decided

1. Thread the `Clock` port into the seven modules the way `registry_context`
   holds it: an interface model in `imports.module_internal.<module>.models`,
   the port retained by the service constructor, and one note per service —
   the current time comes only from that port; the module never calls
   `datetime.now`, `utcnow` or `date.today`.
2. Change the Factory gate for a module that owns a clock port: a wall-clock
   read is a second time source and BLOCKS regeneration; the deterministic
   rewrite stays only for modules without a clock obligation.
3. Bootstrap wires the one `SystemClock` into every service (it already
   constructs it for `registry_context` and `holded_gateway`).
4. Cost and order: this is a contract and models change, so Route B regenerates
   the seven modules and bootstrap (about twice the 2026-09-14 run); schedule it
   as the next cabinet_backend spec run, before other note-level changes, so
   the clock class does not keep paying for every later regeneration.

### Not in question

- Keeping the deterministic rewrite as the closure: it fixes the AttributeError,
  not the unnamed source.
- Passing `observed_at` as a caller parameter instead of a port: the callers
  of these services are the sync session, the local API and the scheduler, and
  a caller-supplied time would only move the ambient read one layer up.

---

## Resolution protocol

When an open question is resolved:

1. verify the authoritative external contract or accept the product decision;
2. add the normative model clarification to State 1 or the deterministic rule to
   State 2;
3. add required tests and failure behavior;
4. replace the open entry with a short resolution reference rather than silently
   deleting the historical question.
