# State 0 — Cabinet Backend product boundary

## Status

Draft corrected against the implemented Cabinet Invoice Card V1 and the
accepted purchase workflow.

## Product statement

Cabinet Backend is the durable operational core of Cabinet. An authorized user
or agent submits prepared working information; Cabinet validates and stores
structured Cards, relationships, sources, supplier purchases represented by
Invoice Cards, material lists, and their history in PostgreSQL.

The primary purchase workflow is simple: the user buys materials in a shop or
online, pays at the time of purchase, and saves the resulting invoice or
receipt as a Cabinet Invoice Card. One purchase may use more than one payment
method, for example cash and card. A purchase may be linked to one Cabinet Work
Object or remain explicitly unassigned.

The agent performs extraction, normalization, matching suggestions, and other
heuristic work. Cabinet Backend remains the authority that decides whether
submitted Cabinet data is valid, current, non-duplicated, and safe to persist.

## Product position

Cabinet Backend replaces the current repository-backed Card storage mechanism;
it does not replace the accepted Cabinet Card concept or the implemented
Invoice Card V1 fact model.

It is not:

- a generic document database;
- a second Registry;
- a second PresuPro;
- an accounting ledger;
- an accounts-payable system;
- an inventory or procurement workflow;
- a Client Portal database;
- a passive proxy that accepts arbitrary agent JSON.

## Actors

### Authorized user

Uses Cabinet through conversational or visual interfaces to:

- save and find working contacts, providers, documents, and lists;
- capture a material purchase from a receipt, invoice, PDF, photo, or message;
- review and correct extracted purchase facts;
- assign a purchase to one Work Object or leave it without an object;
- record the payment methods and amounts shown by the source;
- inspect purchases and material facts by Work Object;
- request later accounting or client-facing publication when eligible.

### Cabinet agent

Uses controlled Cabinet capabilities to:

- extract structured facts from text and source documents;
- search existing Cards before proposing creation;
- prepare new or updated Cards;
- propose but not silently confirm uncertain identity matches;
- prepare Invoice Card drafts from source evidence;
- propose a primary Work Object assignment;
- preserve an explicit unassigned state when no object is known;
- prepare payment transactions, including split cash/card settlement;
- request deterministic Cabinet validation and persistence;
- inspect accepted records, warnings, conflicts, and publication results.

Agent computations remain proposals or prepared inputs until Cabinet Backend
accepts them.

### Cabinet Web UI

Reads the same Cabinet data and submits the same domain actions as the agent.
It does not maintain an independent source of truth or implement separate
business rules.

### Platform services

Registry, PresuPro, Holded Gateway, and Client Portal interact through explicit
boundaries. None receives direct access to Cabinet tables.

## Sources of truth

| Concern | Authoritative owner | Cabinet treatment |
| --- | --- | --- |
| Cabinet Card identity, content, lifecycle, sources, and relationships | Cabinet | Validate and persist in PostgreSQL. |
| Cabinet Work Object identity and Cabinet-owned working context | Cabinet | May exist standalone and may later link to Registry. |
| Registry project UUID and current project context | Registry | Validate and retain an optional external link plus read-only projection. |
| Mutable presupuesto and estimate composition | PresuPro | Consume as plan input; never edit or silently call it approved. |
| Supplier purchase and Invoice Card facts | Cabinet | Preserve structured facts, source provenance, revisions, confirmation, primary object assignment, and payment evidence. |
| Material-list state and accepted purchase matches | Cabinet | Preserve accepted facts and relationships without inventing procurement states. |
| Holded accounting document and accounting state | Holded | Access only through Holded Gateway and retain typed external links or receipts. |
| Technical Holded delivery operation | Holded Gateway | Retain durable publication state and typed receipts. |
| Client-visible budget, expenses, allocations, progress, and customer payments | Client Portal | Send only through an agreed intake boundary. |

## Primary outcomes

### Store agent-prepared working knowledge

The agent can submit prepared, source-backed Cabinet information. Cabinet
returns either:

- an accepted Card or operation with stable identity and revision; or
- concrete validation, conflict, duplicate-candidate, authorization, or source
  errors.

Cabinet does not invent missing values, accept an untyped data envelope, or
claim persistence when a write failed.

### Maintain standalone and Registry-linked Work Objects

A Work Object is a Cabinet Card representing a working object or job context.
It may be created without Registry and remain fully identifiable inside
Cabinet.

A Work Object may later link to an existing Registry project. Registry owns the
external project UUID and current Registry context. Cabinet retains its own
Card identity, history, notes, contacts, purchases, and operational
relationships.

Linking to Registry must not replace the Cabinet Card identity or erase its
history. Registry data must not silently overwrite Cabinet-owned contact,
fiscal, or working information.

### Capture a purchase as one Invoice Card

One Invoice Card represents one supplier purchase or supplier invoice. It
preserves:

- supplier and buyer facts when available;
- invoice or receipt number and dates;
- normalized purchase lines and source wording;
- totals and payable amount;
- source and provenance;
- one primary object assignment;
- payment facts supported by evidence;
- draft, confirmed, or archived lifecycle state.

The user-facing term may be “purchase” or “material purchase” even though the
existing domain entity remains Invoice Card.

### Allow purchases without an object

The Invoice Card `object` block is required structurally, but both `card_id` and
`label` may be null. This represents an explicit purchase “without object”.

An unassigned purchase is valid and remains searchable, reviewable, and
assignable later. The absence of an object must not create a synthetic Work
Object.

The product distinguishes:

- not yet reviewed for object assignment;
- intentionally left without an object;
- assigned by free-form label;
- assigned to a Cabinet Work Object.

The exact representation of reviewed versus not-yet-reviewed belongs to later
domain-model work.

### Use one primary object per purchase in the first product

The first complete product stores one primary object assignment for each
Invoice Card. A purchase is either:

- linked to one Cabinet Work Object;
- described by one free-form object label; or
- explicitly unassigned.

Line-level distribution and one purchase across several Work Objects are not
part of the first complete product. They may be introduced later as separate,
mutable allocation records without changing the preserved source invoice
facts.

### Preserve immediate and split payment evidence

The normal product workflow assumes the purchase is paid at the time it is
made, whether in a physical shop or online.

One purchase may contain several payment transactions when the total was split
between methods, for example:

- cash;
- card;
- cash plus card.

The sum applied to a paid purchase must equal the payable amount. Cash evidence
may separately preserve the amount tendered and change returned.

Cabinet Invoice Card V1 already supports broader source-faithful statuses such
as `unknown`, `unpaid`, `partially_paid`, `paid`, and `refunded`. State 1 must
decide whether the backend preserves this complete accepted vocabulary while
the main product flow presents immediate full payment as the default.

The first complete product does not introduce:

- a payment shared by several Invoice Cards;
- bank reconciliation;
- accounts-payable scheduling;
- debt collection;
- a separate cross-invoice payment aggregate.

### Maintain living material lists and accepted purchase matches

The agent or user can create and update structured material requirements.
Accepted data remains linked to its Work Object, source, actor, and history.

Agent matching may propose which purchase lines satisfy which requirements.
Cabinet may preserve accepted matches and prepared purchased/remaining
quantities while checking referenced identities, revisions, and arithmetic.
It does not introduce ordered, delivered, stocked, or consumed states without
a concrete later workflow.

### Distinguish suggestions from confirmed relationships

The agent may return zero, one, or several supported Work Object or material
candidates. Cabinet keeps suggestion, confirmation, rejection, and explicit
unassignment distinguishable.

There is no unattended auto-confirmation in the accepted baseline.

### Publish eligible operations through Holded Gateway

An authorized actor may request accounting publication for an eligible Cabinet
operation.

Cabinet:

- makes the business eligibility decision;
- fixes the exact source revision used for publication;
- requests the operation through Holded Gateway;
- preserves the returned external identity, receipt, and reconciliation state;
- reports pending, rejected, failed, ambiguous, or successful outcomes;
- never treats a timeout as proof of either success or safe retry.

Holded Gateway owns technical Holded communication. The agent never sends a raw
Holded request using a production token.

### Compare plan and operational reality

Cabinet can provide accepted purchase lines and material-list facts alongside
PresuPro plan data for the same working context.

The agent or an application may calculate purchased/remaining quantities,
material matching, and explanations. Mutable PresuPro data is not presented as
an approved Client Portal budget.

### Prepare Client Portal delivery

Cabinet can prepare traceable operational facts for Client Portal once a typed
intake contract exists. Client Portal remains the owner of its Budget, Expense,
allocation, progress, payment, and visibility records.

The current boundary is capability-blocked for automatic publication because
the required PresuPro approval contract and final Client Portal intake contract
are not yet available.

## Inputs entering Cabinet

- prepared user or agent commands with actor and source provenance;
- photos, PDFs, scans, messages, and references to original sources;
- structured purchase and payment facts extracted from those sources;
- optional Cabinet Work Object references or free-form object labels;
- optional Registry project references and current Registry context;
- PresuPro plan data with source freshness;
- typed Holded Gateway receipts and reconciliation results;
- typed Client Portal acceptance or rejection when its contract exists.

## Observable outputs

- accepted Cards and operations with stable identity and revision;
- search results and explicit duplicate candidates;
- validation, stale-revision, authorization, relationship, or dependency
  failures;
- standalone or Registry-linked Work Object views;
- purchases assigned to one object or explicitly shown as without object;
- purchase lines, totals, payment methods, and payment evidence with provenance;
- suggested, confirmed, rejected, and superseded relationships;
- Holded publication status and external references;
- plan-versus-operational views with source freshness;
- Client Portal projection previews and later publication receipts.

## Persistent conceptual data

Cabinet persists in PostgreSQL:

- Cards and type-specific Cabinet content;
- Card relationships and their history;
- standalone Work Objects and optional Registry links;
- source references and provenance;
- Invoice Card facts, lifecycle, revisions, and evidence;
- one primary object assignment per Invoice Card;
- payment facts and transactions contained in Invoice Cards;
- material requirements and accepted purchase matches;
- agent/user decisions and revision conflicts;
- external entity links;
- publication intent, idempotency, status, and receipts.

The physical schema, ORM, indexes, migration mechanism, and binary object
storage are later-state decisions.

## External boundaries

### Registry

Registry is the sole creator and owner of Registry project UUIDs and current
Registry project context. Cabinet may link a standalone Work Object to a
Registry project after validating the exact UUID.

Registry linkage is optional for Cabinet Work Object existence. Archived or
missing Registry projects must not invalidate the historical Cabinet Card, but
may restrict new Registry-dependent actions.

### PresuPro

PresuPro owns estimate composition and approval. Cabinet consumes plan data
without directly reading or editing PresuPro storage.

### Holded Gateway

Holded Gateway owns Holded credentials and technical delivery behavior but no
Cabinet business decision. Cabinet and PresuPro are independent consumers.

### Client Portal

Client Portal owns its client-facing records and derived views. Cabinet
publishes through an explicit contract and never accesses Portal storage.

## Important failure and invalid outcomes

- submitted agent data is incomplete, unsupported, stale, or inconsistent with
  its cited source;
- a possible Card identity or duplicate remains ambiguous;
- a referenced Work Object is missing or changed;
- a Registry link is missing, archived for a Registry-dependent mutation,
  mismatched, or unavailable;
- an Invoice Card changed since the reviewed revision;
- payment transaction amounts do not reconcile with the payable amount;
- cash tendered, applied, and change amounts are inconsistent;
- a requested relationship conflicts with a newer confirmed decision;
- a material-list match references a missing entity, stale invoice revision,
  or quantity outside its source line;
- PresuPro data is unavailable, mutable, stale, or not linked;
- Holded Gateway rejects, times out, or reports an ambiguous result;
- Client Portal rejects a version, duplicate, authorization, or payload;
- a required downstream contract is not available.

No failure may become fabricated data, a silent merge, an invented Registry
UUID, an unconditional retry, or a false publication success.

## Explicit non-goals

Cabinet Backend does not:

- require Registry before a Cabinet Work Object can exist;
- create or independently edit Registry projects;
- edit or approve PresuPro estimates;
- act as a general ledger, banking integration, payroll system, or tax engine;
- manage cross-invoice payments or bank reconciliation;
- distribute one purchase across several Work Objects in the first product;
- own Holded credentials or raw transport behavior;
- let the agent call Holded directly with a production token;
- own Client Portal allocations, progress, customer payments, or visibility;
- implement procurement, inventory, delivery, or consumption workflows in the
  first scope;
- make raw OCR/provider responses its durable domain model;
- trust arbitrary untyped agent payloads;
- define shared MCP infrastructure in this case study;
- solve VPS, TLS, secret management, backup operations, or process supervision
  in State 0;
- define exact endpoints, tables, modules, or algorithms before later states.

## Accepted product decisions

1. Cabinet Backend owns Cabinet operational Cards and cross-Card
   relationships.
2. PostgreSQL is the selected durable Cabinet database.
3. A Cabinet Work Object may exist without Registry.
4. Registry UUID is canonical only for an optional Registry project link; it is
   not the identity of every Cabinet Work Object.
5. Linking a Work Object to Registry preserves Cabinet identity and history.
6. Agent/UI may perform heuristic computation, but Cabinet Backend owns
   deterministic validation and persistence.
7. One Invoice Card represents one supplier purchase or invoice.
8. One Invoice Card has one primary object assignment in the first complete
   product.
9. A purchase may be explicitly unassigned and later assigned.
10. Free-form object labels are valid when a Work Object is not yet identified.
11. Multi-object and line-level allocation are deferred and do not belong to
    Invoice Card V1 facts.
12. The normal purchase flow is immediate full payment.
13. Multiple payment transactions may represent split settlement such as cash
    plus card.
14. No separate cross-invoice payment model is introduced in the first scope.
15. Draft, confirmed, and archived are the Invoice Card lifecycle states; they
    are not procurement or delivery states.
16. Suggestions are distinct from confirmed links; there is no unattended
    auto-confirmation.
17. No ordered/delivered/consumed procurement lifecycle is introduced without
    a later concrete workflow.
18. Holded integration is a dedicated Gateway.
19. The agent initiates domain actions and never owns the production Holded
    token or raw provider transport.
20. Client Portal publication is explicit, versioned, and idempotent once the
    required external contracts exist.
21. Cabinet-owned contact and fiscal data remains independent from Registry
    projections.

## State 0 readiness assessment

The core product boundary is stable enough to begin State 1 after the remaining
questions in `open_questions.md` are classified as either domain-blocking or
later external-contract decisions.

State 1 must preserve the implemented Invoice Card V1 facts while correcting
the previous assumptions that every Work Object requires Registry and that one
purchase is distributed across several Work Objects in the first product.
