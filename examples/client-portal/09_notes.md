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
- OCR confidence and internal OCR working fields are not required by the
  client view and are not accepted as financial truth without confirmation.
- Documents and photographs are referenced from their business records; their
  binary content remains outside the main record.
- Sensitive credentials, tokens, provider secrets, and environment values
  never enter Client Portal business data or these requirements.
- Dashboard totals are derived from owning records and remain traceable to
  their budget, expense, allocation, progress, and payment sources.
