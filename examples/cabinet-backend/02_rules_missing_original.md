# State 2 decision — missing original invoice source

## Accepted decision A50 — missing original invoice source

Local Cabinet Backend distinguishes a usable confirmed Invoice Card from a Card
whose original photograph or PDF is durably available.

A source may be temporarily missing and expected later, or it may be explicitly
recorded as permanently lost. Loss of the original does not delete the accepted
Card or erase the working decisions already made from it.

### User-visible states

For source completeness, an invoice is presented as one of:

- `complete` — all required original photographs or PDFs are stored and verified
  locally;
- `awaiting_source` — one or more required originals are currently missing but may
  still be attached later;
- `source_lost` — an authorised user has explicitly confirmed that one or more
  required originals cannot be recovered.

Moving an invoice to `source_lost` is an explicit, auditable action. It records
who confirmed the loss, when it was confirmed, the affected source references,
and an optional explanation.

### Allowed use

An accepted confirmed Card in `awaiting_source` or `source_lost` remains available
for:

- Cabinet and Local Backend search;
- assignment to a Registry project;
- comparison with purchase and material lists;
- internal project analytics;
- plan-versus-actual calculations, with a visible source warning;
- publication to `client_portal`, with a visible indication that the original is
  missing when the portal contract exposes source completeness.

### Holded restriction

An Invoice Card is not eligible for Holded publication unless every original
source required for that Card is stored in the Local Backend and verified.

Therefore:

```text
source_completeness = complete
```

is a mandatory Holded eligibility condition.

Neither `awaiting_source` nor `source_lost` can be overridden for Holded
publication. Recovering and verifying the original changes source completeness to
`complete`; it does not require rewriting the accepted Card payload.

### Client Portal rule

Missing original source does not block publication to `client_portal`.

The portal publication must carry or derive the source-completeness state so that
`source_lost` is not presented as if documentary evidence were available. The
exact visual presentation belongs to the Client Portal contract.

### Invariants

For every successful Holded publication:

```text
publication.invoice_id = invoice.invoice_id
and invoice.source_completeness = complete
and all required source replicas are verified in local_durable storage
```

For every invoice marked `source_lost`:

```text
source_loss_decision exists
and source_loss_decision.invoice_id = invoice.invoice_id
and source_loss_decision.actor exists
and source_loss_decision.decided_at exists
```

Marking a source as lost cannot remove:

- the accepted Invoice Card revision;
- project assignment history;
- accepted PresuPro matches;
- analytics history;
- provenance or earlier source-transfer evidence.

### Required tests

1. A complete confirmed invoice may be published to Holded.
2. An invoice awaiting an original cannot be published to Holded.
3. An invoice whose original is declared lost cannot be published to Holded.
4. Both incomplete states remain usable in internal analytics with a warning.
5. Both incomplete states may be published to Client Portal with source status
   preserved.
6. Attaching and verifying the missing original changes an invoice from
   `awaiting_source` to `complete`.
7. A `source_lost` invoice may return to `complete` if the original is later found
   and verified; the earlier loss decision remains in history.
