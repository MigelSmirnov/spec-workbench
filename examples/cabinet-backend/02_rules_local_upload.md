# State 2 decision — local invoice source upload

## Status

Accepted supporting decision for `02_rules.md`.

## Decision

Local Cabinet Backend provides a minimal local HTML uploader for attaching invoice
photographs and PDFs after the confirmed Invoice Card has already been accepted.

The uploader is a service interface for the local computer. It is not part of the
public VPS Cabinet application and is not exposed to the Internet.

Codex or another authorised local agent and the HTML uploader must use the same
Backend attachment operation. Neither may write directly to PostgreSQL or copy
files into storage folders while bypassing Backend validation and provenance.

## User workflow

The local page allows the user to:

1. search for an invoice by invoice number, supplier, date, amount, or other
   available Card facts;
2. review matching invoices with enough context to distinguish them;
3. select exactly one invoice;
4. select one or more local photographs or PDF files;
5. submit the files for attachment;
6. see a clear success, duplicate, mismatch, or failure result.

A convenient implementation may preselect an invoice when search returns exactly
one clear result. The final attachment still targets the stable `invoice_id`, not
the human invoice number.

## Agent workflow

A local agent may perform the same operation in bulk, for example when instructed:

> Download new invoices and attach matching photographs from Downloads.

The agent may automatically attach a file only when it resolves the target to one
invoice with sufficiently strong evidence. Ambiguous matches require user choice
and must not modify any invoice before that choice.

## Normative rules

1. The HTML uploader binds only to a local or otherwise explicitly private
   interface.
2. It must not become a public Cabinet endpoint.
3. Both agent and HTML workflows call the same Backend attachment operation.
4. The operation records the selected `invoice_id`, actor, time, original
   filename, media type, calculated content hash, and attachment result.
5. Existing source-hash expectations remain authoritative when present.
6. A hash mismatch, unreadable file, unsupported file, or ambiguous invoice match
   is shown as a failure and does not replace existing source evidence.
7. Reattaching the same bytes to the same invoice and source is idempotent and
   must not create duplicate stored files.
8. Selecting an invoice by human-readable search is allowed; mutating by invoice
   number alone is not.
9. One upload may contain several files because one invoice may have several
   photographs or source documents.
10. A successfully attached and verified file removes the corresponding visible
    missing-source warning when no other required source remains missing.

## Required tests

1. A local user can find an invoice, select it, upload a photograph, and receive a
   success result.
2. Several invoices with the same invoice number are displayed as separate
   choices and no file is attached before one is selected.
3. A direct agent operation and the HTML uploader create equivalent attachment
   records through the same Backend operation.
4. A repeated upload of the same file does not create a duplicate binary replica.
5. A file whose hash conflicts with an expected source is rejected.
6. The uploader cannot bind to a public network interface under the default local
   configuration.
7. Uploading several valid photographs attaches all of them to the selected
   invoice and reports each result separately.

## Consequence

Invoice source recovery is usable without the VPS chat interface. The user may
ask a local agent to process files from a folder or use a simple browser page, but
all source files still enter the archive through one controlled Backend action.
