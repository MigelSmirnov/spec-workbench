# Client Portal Cross-Cutting Requirements Notes

## Status

**Requirements baseline; not classified implementation notes**

- All financial and progress calculations must be deterministic for the same
  accepted source records.
- Financial values use decimal money semantics with explicit currency and
  domain-defined rounding; binary floating-point behavior is not a business
  contract.
- Client Portal never guesses a missing amount, allocation, percentage,
  currency, or source value.
- Missing or unavailable data is shown explicitly and is not replaced by zero
  unless zero is a confirmed business value.
- Client-facing language does not expose internal microservice, adapter,
  storage, OCR, or provider implementation names.
- Holded document format is not a Client Portal contract.
- OCR Service is an external microservice; Telegram bot is only an intake
  interface and does not own recognition logic.
- Client Portal depends only on the versioned normalized OCR-service contract,
  not on a provider, model, or provider-specific response.
- OCR confidence, source-page handling, page order, provider-specific fields,
  and raw model responses remain OCR-service concerns and do not become Portal
  Expense fields.
- Client Portal accepts only confirmed recognition results and requires a
  stable recognized-document reference for idempotent Expense creation.
- Project selection, Expense confirmation, and Budget Section allocation are
  not inferred from OCR.
- Accounting, Holded, and reuse by other applications are outside the current
  OCR integration.
- Documents and photographs are referenced from their business records; their
  binary content remains outside the main record.
- Sensitive credentials, tokens, provider secrets, and environment values
  never enter Client Portal business data or these requirements.
- Dashboard totals are derived from owning records and remain traceable to
  their budget, expense, allocation, progress, and payment sources.
