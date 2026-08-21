# Cabinet_web embedded invoice discovery — 2026-08-21

## Result

A real invoice candidate exists in `Cabinet_web/main`, but it is not stored as its own Invoice Card.

Reviewed upstream:

```text
repository: MigelSmirnov/Cabinet_web
ref: main
commit: d4419e3b948d49bd85a99a0941a350a73494cd27
```

## Candidate

Stable document identity currently used by the surrounding Cards:

```text
invoice-f260001
```

Client Card:

```text
data/cards/client-uliana-kolpacheva-20260815/card.json
```

contains a source entry with:

```text
id: invoice-f260001
media_type: application/pdf
document_type: invoice
document_number: F260001
document_date: 2026-08-12
file_status: pending
```

Project Card:

```text
data/cards/project-uliana-floor-20260815/card.json
```

contains invoice-owned financial facts under `financials.invoices[]`:

```text
id: invoice-f260001
number: F260001
date: 2026-08-12
status: paid
net_amount: 900
tax_amount: 189
total_amount: 1089
line_items: present
source_id: invoice-f260001
```

The same project Card also contains payment linkage to `invoice-f260001`.

## Architectural classification

This is not `MISSING_REAL_INPUT`.

The invoice exists as real Cabinet data, but invoice identity/source identity and invoice facts are embedded in Client/Project Cards instead of being owned by the accepted Invoice Card V1 contract.

Current classification:

```text
REAL-CANARY-DATA-001: RESOLVED_AS_FALSE_NEGATIVE
CW-INVOICE-OWNERSHIP-001: BLOCK
class: EMBEDDED_INVOICE_NOT_NORMALIZED_TO_INVOICE_CARD
```

The accepted Cabinet_web architecture says Card Contracts own Invoice Card V1 and repository-data owns repository-backed Card files under `data/cards`. Therefore the repair belongs in Cabinet_web Card/data ownership, not in a backend adapter.

## Required repair

Create a dedicated Invoice Card:

```text
data/cards/invoice-f260001/card.json
```

using only truthful facts available from the embedded Client/Project data and the real source document. Do not invent missing supplier, buyer, quantity, unit, payment-method, source-byte, or provenance facts merely to satisfy the schema.

Invoice identity and source identity must be separate:

```text
invoice.id        = invoice-f260001
source.source_id  = a stable source-* identity owned by the Invoice Card
```

The current Client source `id: invoice-f260001` must not be treated as both identities permanently.

After the Invoice Card is accepted, Client/Project Cards should retain only the relationships/projections that their own contracts actually own. They must not remain competing owners of canonical invoice financial facts.

## Real-data canary consequence

Do not send the embedded Project/Client representation directly to `cabinet_backend` as if it were Invoice Card V1.

The next eligible canary target is `invoice-f260001` only after:

1. it exists as a tracked clean Invoice Card V1 under `data/cards/invoice-f260001/card.json`;
2. the Card is confirmed;
3. its stable `source.source_id` is present;
4. the original PDF bytes corresponding to that source identity are available;
5. the reviewed Cabinet_web validator accepts the Card.

Then use the existing `cabinet-web-sync-v1 -> invoice.archive.accept_revision -> invoice.source.attach` path without changing backend semantics.
