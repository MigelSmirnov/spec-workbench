# Client Portal Business Entities

## Status

**Requirements baseline; not a code-model design**

The names below describe business meaning only. They do not define classes,
schemas, persistence, or program contracts.

## Project Portal Context

- **Purpose:** identify the one project whose portal is being viewed.
- **Business data:** `project_id`, display name, status, address, customer
  reference, and Registry freshness timestamp.
- **Source:** Registry current project context.
- **Who may change it:** Registry only; Client Portal may refresh its local
  representation but may not edit authoritative values.
- **Temporal meaning:** current, not an independent historical project record.
- **Must not contain:** a portal-created project identity, fiscal client data,
  credentials, or an independently editable copy of Registry truth.

## Budget

- **Purpose:** provide the client-visible plan for one project.
- **Business data:** project identity, budget source, source provenance,
  currency, and ordered Budget Sections. Budget totals are derived from the
  sections.
- **Source:** `manual` in the MVP; approved PresuPro snapshot in the future.
- **Who may change it:** an authorized operator may edit a manual budget. A
  future imported approved snapshot is source-controlled and not silently
  editable as a manual plan.
- **Temporal meaning:** the current client-visible plan; retention and
  replacement of future approved versions remain open.
- **Must not contain:** actual expenses as planned amounts, mutable PresuPro
  state presented as approved, or factura state.

## Budget Section

- **Purpose:** group planned material and work amounts for client presentation
  and later expense/progress association.
- **Business data:** stable local identity, display name, display order,
  planned materials, planned work, and section provenance.
- **Source:** manual budget input or a future approved snapshot mapping.
- **Who may change it:** an authorized operator in manual mode; future import
  behavior depends on snapshot and migration policy.
- **Temporal meaning:** part of the current client-visible budget. Its identity
  remains stable when its display name changes.
- **Must not contain:** name as the sole identity, actual expense totals,
  completion percentage, or an assumed PresuPro section code.

## Expense

- **Purpose:** record one confirmed project expense.
- **Business data:** project, stable source-intake identity, supplier, document
  date, total amount, confirmation status, inclusion in totals, document
  reference, and creation and confirmation dates.
- **Source:** a confirmed external intake result or an authorized correction.
- **Who may change it:** external intake supplies the confirmed fact; an
  authorized operator may correct, include, or exclude it while the project is
  active.
- **Temporal meaning:** a historical financial fact; correction or exclusion
  must remain explicit and must not turn it into a planned-budget value.
- **Must not contain:** OCR confidence, raw OCR internals, derived project
  totals, invoice lifecycle, or duplicated document binaries.

## Expense Allocation

- **Purpose:** assign an expense amount to budget reporting areas.
- **Business data:** expense reference, target Budget Section or
  `Other expenses`, and manually assigned amount.
- **Source:** authorized operator decision.
- **Who may change it:** an authorized operator while the project is active.
- **Temporal meaning:** the current explicit distribution of a historical
  expense.
- **Must not contain:** a duplicated Expense or Document, an automatic
  proportional guess, or its own independent expense total.

One Expense may have one allocation, several manual allocations, or one
allocation to `Other expenses`.

## Document

- **Purpose:** let the client inspect evidence associated with an Expense.
- **Business data:** stable document reference, file reference, descriptive
  details, and association with one Expense.
- **Source:** external intake after operator confirmation.
- **Who may change it:** an authorized operator may correct descriptive data or
  visibility while the project is active.
- **Temporal meaning:** historical evidence.
- **Must not contain:** the binary file inside the business record, credentials,
  raw OCR working data, or one copy per allocation.

## Progress Photo

- **Purpose:** show visible evidence of project progress.
- **Business data:** project, stable source-intake identity, file reference,
  capture/publication date, optional Budget Section, optional caption, and
  client visibility.
- **Source:** external Telegram intake followed by operator selection and
  publication.
- **Who may change it:** an authorized operator may set association, caption,
  and visibility while the project is active.
- **Temporal meaning:** historical media evidence with current visibility.
- **Must not contain:** the image binary inside the business record, automatic
  progress estimates, financial totals, or Telegram credentials.

## Work Progress

- **Purpose:** record the operator's current completion percentage for each
  section that has planned work.
- **Business data:** project, Budget Section, manual completion percentage,
  update time, and update provenance.
- **Source:** authorized operator entry.
- **Who may change it:** an authorized operator while the project is active.
- **Temporal meaning:** current manual progress state; a progress-history
  requirement is not established by this baseline.
- **Must not contain:** completed work value or overall progress as manually
  editable fields, or progress inferred from photographs.

## Work Payment

- **Purpose:** record money received from the client for work.
- **Business data:** project, stable payment identity, amount, payment date,
  descriptive reference, and recording provenance.
- **Source:** authorized operator entry.
- **Who may change it:** an authorized operator while the project is active.
- **Temporal meaning:** a historical payment fact.
- **Must not contain:** a factura, accounting posting, bank transaction model,
  manually entered payment total, or completed-work value.

## Derived values

The following values are calculated views, not independent primary records:

- actual materials;
- remaining materials;
- completed work value;
- overall progress;
- payments total;
- performed ahead of payments;
- unused advance payment.

They must always be recomputable from Budget Sections, included confirmed
Expenses and their allocations, Work Progress, and Work Payments.
