# State 0 — Cabinet Backend product boundary

## Status

Draft for product review after the Cabinet product-boundary correction.

## Product statement

Cabinet Backend is the durable operational core of Cabinet. An authorized user
or agent sends prepared working information; Cabinet validates and stores
structured Cards, relationships, sources, ready Invoice Cards, material lists,
agent-prepared allocations, invoice payment facts, and their history in
PostgreSQL. Cabinet links this operational knowledge to Registry projects,
consumes PresuPro plan data, publishes eligible accounting operations through
Holded Gateway, and prepares traceable downstream data for Client Portal.

The agent performs organisational and heuristic work. Cabinet Backend remains
the authority that decides whether submitted Cabinet data is valid, current,
non-duplicated, and safe to persist.

## Product position

Cabinet Backend replaces the current repository-backed storage mechanism; it
does not replace the accepted Cabinet Card concept.

It is not:

- a generic document database;
- a second Registry;
- a second PresuPro;
- an accounting system;
- a Client Portal database;
- a passive proxy that accepts arbitrary agent JSON.

## Actors

### Authorized user

Uses Cabinet through conversational or visual interfaces to:

- save and find working contacts, providers, documents, and lists;
- review agent-prepared information;
- confirm or correct relationships;
- inspect work by project;
- confirm invoices and their prepared project/material relationships;
- request accounting or client-facing publication.

### Cabinet agent

Uses controlled Cabinet capabilities to:

- extract structured facts from text and source documents;
- search existing Cards before proposing creation;
- prepare new or updated Cards;
- propose but not silently confirm uncertain identity matches;
- propose project, provider, material, and purchasing relationships;
- prepare complete Invoice Cards, allocations, material-list matches, and
  derived purchased/remaining quantities;
- request deterministic Cabinet validation and persistence;
- inspect accepted records, validation failures, conflicts, and publication
  results.

Agent computations are proposals or prepared inputs until Cabinet Backend
accepts them.

### Cabinet Web UI

Reads the same Cabinet data and submits the same domain actions as the agent.
It does not maintain an independent source of truth or implement separate
business rules.

### Platform services

Registry, PresuPro, Holded Gateway, and Client Portal interact through explicit
boundaries described below. None receives direct access to Cabinet tables.

## Sources of truth

| Concern | Authoritative owner | Cabinet treatment |
| --- | --- | --- |
| Registry project UUID and current project context | Registry | Validate and retain a linked reference plus read-only current projection. |
| Cabinet Work Object operational relationships | Cabinet | Own Cabinet-specific links to Cards, invoices, material lists, and accepted allocations. |
| Mutable presupuesto and estimate composition | PresuPro | Consume as plan input; never edit or silently call it approved. |
| Cabinet Card identity, content, lifecycle, sources, and relationships | Cabinet | Validate and persist in PostgreSQL. |
| Supplier invoice facts and Cabinet invoice lifecycle | Cabinet | Preserve structured facts, source provenance, revisions, and confirmation. |
| Supplier, carrier, subcontractor, and working-contact knowledge | Cabinet | Maintain Cards that may be incomplete and enriched over time. |
| Material-list state and accepted purchase matches | Cabinet | Preserve agent-prepared facts and relationships without inventing a procurement workflow. |
| Holded accounting document and accounting payment state | Holded | Access only through Holded Gateway and retain typed external links/receipts. |
| Technical Holded delivery operation | Holded Gateway | Retain durable publication state and consume typed receipts. |
| Client-visible budget, expenses, allocations, progress, and customer payments | Client Portal | Send only through an agreed intake boundary; never edit Portal storage directly. |

## Primary outcomes

### Store agent-prepared working knowledge

The agent can submit prepared, source-backed Cabinet information. Cabinet
returns either:

- an accepted Card or operation with stable identity and revision; or
- concrete validation, conflict, duplicate-candidate, authorization, or source
  errors.

Cabinet does not invent missing values, accept an untyped data envelope, or
claim persistence when the write failed.

### Maintain Work Object Cards linked to Registry

An authorized actor can create or refresh a Cabinet Work Object only from an
existing active Registry project. Cabinet stores the Registry UUID as
canonical external identity and adds Cabinet-owned operational relationships.

Changing Registry name, address, or status does not replace the Cabinet Card
identity or erase its operational history. Cabinet does not create a competing
Registry project UUID or a standalone Work Object. An invoice or note may
remain unassigned without creating a Work Object.

Cabinet Contact data, including fiscal and communication details, remains
Cabinet-owned and is never overwritten from Registry `customer_ref`.

### Maintain providers and project participants

Cabinet can preserve and enrich working knowledge about:

- material suppliers;
- shops;
- carriers and delivery providers;
- subcontractors and adjacent trades;
- customers and other work contacts.

One Card may participate in several work relationships without its phone
number, title, or role becoming its identity. Uncertain duplicate candidates
are presented rather than silently merged.

### Maintain living material lists and accepted purchase matches

The agent or user can create and update structured material requirements.
Accepted data remains linked to its Work Object, source, actor, and history.

Agent matching may propose which invoice lines satisfy which requirements.
The agent also calculates purchased and remaining quantities. Cabinet persists
the accepted relationships and prepared quantities, checks referenced
identities, revisions, arithmetic consistency, and conflicts, but does not
perform semantic matching or introduce an ordered/delivered/consumed workflow.

### Preserve invoices without forcing a project

A valid Cabinet Invoice Card may remain:

- not yet reviewed for project association; or
- reviewed and intentionally left unassigned.

This is a normal state. A future purchase such as a reusable tool may be linked
to a Work Object later.

The Cabinet `object` field is a matching hint only. The agent may use it to
propose Registry-linked Work Objects, but confirmation requires an authorized
Cabinet action.

### Distinguish suggestions from confirmed relationships

The agent may return zero, one, or several supported project or material
candidates. Cabinet keeps suggestion, confirmation, rejection, and explicit
unassignment distinguishable.

There is no unattended auto-confirmation in the accepted baseline. A human or
an authorized agent acting for the user confirms the relationship.

### Store one invoice across several Work Objects

One original Invoice Card may contain material or service purchases for several
Registry-linked Work Objects.

The agent prepares the distribution at invoice-line, quantity, or amount level.
Cabinet stores the accepted distribution, verifies that it refers to the exact
invoice revision and existing Work Objects, rejects over-allocation, and
preserves reassignment history. Cabinet does not calculate the semantic
distribution itself.

### Store invoice payment facts without a separate payment system

Cabinet preserves payment status, transactions, and evidence already present
in the ready Invoice Card. These facts remain traceable to the invoice source
and revision.

The first complete scope does not introduce a separate cross-invoice payment
aggregate, bank reconciliation, accounts-payable workflow, or a rule that one
payment may close several invoices. Cabinet is not a general ledger and does
not create accounting entries by writing directly to Holded.

### Publish eligible operations through Holded Gateway

An authorized actor may request accounting publication for a Cabinet operation
that has reached an eligible Cabinet state.

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

Cabinet can provide accepted invoice allocations and material-list facts
alongside PresuPro plan data for the same Registry project.

The agent calculates purchased/remaining quantities, material matching, and
higher-level explanations. Cabinet preserves accepted inputs and results,
exact source references, and freshness required to expose stale or incomplete
comparisons. Mutable PresuPro data is not presented as an approved Client
Portal budget.

### Prepare Client Portal delivery

Cabinet can prepare traceable operational facts for Client Portal once a typed
intake contract exists. Client Portal remains the owner of its Budget,
Expenses, allocations, progress, payments, and visibility rules.

The current boundary is capability-blocked for automatic publication because:

- PresuPro does not yet expose the required approved immutable presupuesto
  publication contract;
- Client Portal does not yet expose the final Cabinet intake contract.

Cabinet may expose an internal preview but must not claim a successful Portal
publication while these contracts are absent.

## Inputs entering Cabinet

- prepared user or agent commands with actor and source provenance;
- original-source references and structured extracted facts;
- active project references, validation results, and current context from
  Registry;
- mutable or later approved PresuPro plan data with source freshness;
- typed Holded Gateway receipts and reconciliation results;
- typed Client Portal acceptance or rejection when its contract exists.

## Observable outputs

- accepted Cards and operations with stable identity and revision;
- search results and explicit duplicate candidates;
- validation, stale-revision, authorization, relationship, or dependency
  failures;
- Work Object views containing Cabinet-owned operational relationships;
- unreviewed, intentionally unassigned, suggested, confirmed, and superseded
  relationship outcomes;
- accepted invoice allocations, material-list matches, and invoice payment
  facts with provenance;
- Holded publication status and external references;
- plan-versus-operational views with source freshness;
- Client Portal projection previews and later publication receipts.

## Persistent conceptual data

Cabinet persists in PostgreSQL:

- Cards and type-specific Cabinet content;
- Card relationships and their history;
- Work Object operational state linked to Registry UUID;
- source references and provenance;
- invoice facts, lifecycle, revisions, and evidence;
- material requirements and accepted agent-prepared purchase matches;
- invoice-to-Work-Object allocations and their history;
- payment facts contained in ready Invoice Cards;
- agent/user decisions and revision conflicts;
- external entity links;
- publication intent, idempotency, status, and receipts.

The physical schema, ORM, indexes, migration mechanism, and binary object
storage are later-state decisions.

## External boundaries

### Registry

Registry is the sole creator and current owner of project UUID and current
project context. New Cabinet links require server-side validation of the exact
UUID. Archived projects remain readable; new operational mutations under an
archived project are rejected.

### PresuPro

PresuPro owns estimate composition and approval. Cabinet consumes plan data
without directly reading PresuPro storage. Missing, standalone, mutable, stale,
or unavailable plan data remains explicit.

### Holded Gateway

Holded Gateway is a separate platform integration boundary. It owns Holded
credentials and technical delivery behavior but no Cabinet business decision.
Cabinet and PresuPro are independent consumers and do not proxy Holded
operations through each other.

### Client Portal

Client Portal owns its client-facing records and derived views. Cabinet
publishes through an explicit contract and never accesses Portal storage.

## Important failure and invalid outcomes

- submitted agent data is incomplete, unsupported, stale, or inconsistent with
  its cited source;
- a possible Card identity or duplicate remains ambiguous;
- Registry project is missing, archived for mutation, mismatched, or
  unavailable;
- an invoice or relationship changed since the reviewed revision;
- a requested relationship conflicts with a newer confirmed decision;
- an allocation or material-list match references a missing entity, stale
  invoice revision, or an amount/quantity outside its source line;
- PresuPro data is unavailable, mutable, stale, or not linked to the project;
- Holded Gateway rejects the operation, times out, returns an identity
  mismatch, or reports an ambiguous result requiring reconciliation;
- Client Portal rejects a version, duplicate, authorization, or payload;
- a required downstream contract is not available.

No failure may become fabricated data, a silent merge, an invented project
UUID, an unconditional retry, or a false publication success.

## Explicit non-goals

Cabinet Backend does not:

- create or independently edit Registry projects;
- edit or approve PresuPro estimates;
- act as a general ledger, banking integration, payroll system, or tax engine;
- own Holded credentials or raw transport behavior;
- let the agent call Holded directly with a production token;
- own Client Portal allocations, progress, customer payments, or visibility;
- implement procurement, inventory, delivery, consumption, bank
  reconciliation, or cross-invoice payment workflows in the first scope;
- make raw OCR/provider responses its durable domain model;
- trust arbitrary untyped agent payloads;
- define shared MCP infrastructure in this case study;
- solve VPS, TLS, secret management, backup operations, or process supervision
  in State 0;
- define exact endpoints, tables, modules, or algorithms before later states.

## Accepted product decisions

1. Cabinet Backend, not a separate cost-integration application, owns Cabinet
   operational Cards and cross-Card relationships.
2. PostgreSQL is the selected durable Cabinet database.
3. Registry UUID is the only canonical platform-project identity.
4. Cabinet Work Objects add operational knowledge without duplicating Registry
   truth and exist only for validated Registry projects.
5. Agent/UI may perform heuristic computation, but Cabinet Backend owns
   deterministic validation and persistence.
6. A valid invoice may remain unassigned; unreviewed and intentionally
   unassigned are distinct.
7. Suggestions are distinct from confirmed links; there is no unattended
   auto-confirmation.
8. Draft invoices may participate in a clearly preliminary review, but only
   confirmed eligible facts contribute to accepted operational totals or
   external publication.
9. Reassociation preserves history and cannot silently rewrite already
   published downstream facts.
10. One Invoice Card may be distributed across several Work Objects; the agent
    prepares the distribution and Cabinet validates and stores it.
11. Purchased/remaining calculations and semantic material matching belong to
    the agent; Cabinet stores accepted prepared results and validates their
    identities, revisions, and arithmetic consistency.
12. Cabinet stores payment facts contained in Invoice Card and does not
    introduce a separate cross-invoice payment model in the first scope.
13. No ordered/delivered/consumed procurement lifecycle is introduced without
    a later concrete workflow.
14. Holded integration is a dedicated Gateway; Cabinet and PresuPro never
    serve as temporary Holded proxies for each other.
15. The agent initiates domain actions and never owns the production Holded
    token or raw provider transport.
16. Client Portal publication is explicit, versioned, and idempotent once the
    required external contracts exist.
17. Cabinet-owned contact and fiscal data remains independent from Registry
    `customer_ref`.

## State 0 readiness assessment

The corrected ownership boundary satisfies the State 0 exit gate and is stable
enough to begin State 1. Remaining questions in `open_questions.md` are
localized external-contract or infrastructure decisions and do not need to
block Cabinet's core domain-model work.
