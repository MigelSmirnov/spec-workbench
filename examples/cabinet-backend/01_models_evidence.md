# State 1 companion — Cabinet Backend model evidence

## Status

Evidence and source check for candidate fields in `01_models.md`.

This document distinguishes:

- accepted Cabinet contract facts;
- accepted product decisions;
- Backend-owned design choices;
- external facts that require local-platform inspection;
- State 2 policy questions.

A field is not considered grounded merely because it sounds plausible.

## Evidence classes

- `CABINET_ACCEPTED` — established by the implemented Cabinet Invoice Card V1 contract.
- `PRODUCT_ACCEPTED` — established in `00_product.md` and confirmed product discussion.
- `BACKEND_DESIGN` — a State 1 concept introduced to satisfy the accepted product boundary.
- `LOCAL_EVIDENCE_REQUIRED` — exact shape or capability must be inspected in local-platform repositories.
- `STATE2_POLICY` — data shape is known enough, but transitions or acceptance semantics remain to be decided.

---

# A. Accepted Card and archive

| Model or field | Evidence class | Source or next action |
| --- | --- | --- |
| Invoice Card `id`, `card_version`, `status`, lines, totals, payment, object, source, provenance | `CABINET_ACCEPTED` | Cabinet Invoice Card V1 schema, validator, and merged PR #3. |
| Card content revision by SHA-256 hash | `CABINET_ACCEPTED` | Cabinet optimistic-concurrency and canonical hashing behavior. |
| Complete Card JSON retained by Backend | `PRODUCT_ACCEPTED` | Backend is durable Cabinet archive and must not lose accepted Card fields. |
| `StoredInvoiceCard` archive identity | `BACKEND_DESIGN` | Required to group accepted content revisions under one logical Card ID. |
| `StoredInvoiceCardRevision` immutable payload record | `BACKEND_DESIGN` | Required for history, provenance, matching, publication, and reconciliation. |
| Accepted validator version and compatibility behavior | `STATE2_POLICY` | Decide whether Backend embeds, imports, or contract-tests a validator implementation. |
| Draft versus confirmed archive acceptance | `STATE2_POLICY` | Product permits draft work on VPS; durable local acceptance policy remains open. |
| Duplicate candidate signals | `CABINET_ACCEPTED` plus `STATE2_POLICY` | Cabinet reports candidates; State 2 must decide which findings block import or require acknowledgement. |

---

# B. Source binaries

| Model or field | Evidence class | Source or next action |
| --- | --- | --- |
| Card `source.source_id`, `kind`, `file_ref`, `file_status`, note | `CABINET_ACCEPTED` | Invoice Card V1 source block. |
| Binary hash, media type, byte size, storage reference | `BACKEND_DESIGN` | Required for durable binary verification without redefining Card metadata. |
| VPS and local binary replicas | `PRODUCT_ACCEPTED` | Originals exist first on VPS and later in durable local storage. |
| Mandatory source bytes for acceptance | `STATE2_POLICY` | Decide behavior for `file_status = not_stored`, missing files, and later `invoice_attach_source`. |
| Binary storage technology and path scheme | Later implementation state | Not a State 1 model fact. |

---

# C. Registry project catalogue

| Model or field | Evidence class | Source or next action |
| --- | --- | --- |
| Registry owns project identity and current project context | `PRODUCT_ACCEPTED` | `00_product.md`. |
| `WorkObject.id = Registry ProjectRecord.id` | `PRODUCT_ACCEPTED` | Confirmed product boundary. |
| Versioned compact catalogue copied to VPS | `PRODUCT_ACCEPTED` | Required for normal offline Cabinet operation. |
| `project_id` exact type and serialization | `LOCAL_EVIDENCE_REQUIRED` | Inspect Registry models/contracts and examples. |
| Project display name field | `LOCAL_EVIDENCE_REQUIRED` | Inspect Registry canonical project representation. |
| Address or compact location fields | `LOCAL_EVIDENCE_REQUIRED` | Inspect Registry; do not invent flattened address fields. |
| Project lifecycle/status vocabulary | `LOCAL_EVIDENCE_REQUIRED` | Inspect Registry enums and transitions. |
| Customer reference availability and type | `LOCAL_EVIDENCE_REQUIRED` | Inspect Registry project/customer relationship. |
| Registry version, update timestamp, or content hash | `LOCAL_EVIDENCE_REQUIRED` | Determine available concurrency/freshness evidence. |
| Complete-list or filtered-list capability | `LOCAL_EVIDENCE_REQUIRED` | Determine how active projects are queried and whether pagination/filtering exists. |
| Catalogue freshness warning/block threshold | `STATE2_POLICY` | Product policy, not a Registry fact. |
| Changes causing `needs_attention` | `STATE2_POLICY` informed by local evidence | Requires known Registry states before policy can be finalized. |

---

# D. VPS-to-local synchronization and import

| Model or field | Evidence class | Source or next action |
| --- | --- | --- |
| Stable invoice ID survives transfer | `PRODUCT_ACCEPTED` | `00_product.md`. |
| Authenticated, encrypted, idempotent transfer | `PRODUCT_ACCEPTED` | `00_product.md`. |
| Manifest, synchronization, import, quarantine, receipt separation | `BACKEND_DESIGN` | Prevents network delivery from impersonating durable archive acceptance. |
| Idempotency key and manifest hash | `BACKEND_DESIGN` | Needed to resolve retries without duplicate invoices. |
| Exact network transport and discovery | Later state plus local evidence | Deployment and transport choice is intentionally not State 1. |
| Atomicity of Card payloads and source bytes | `STATE2_POLICY` | Define durable acceptance and quarantine transitions. |
| `unknown_outcome` reconciliation | `STATE2_POLICY` | Define status-query or repeated-command semantics. |
| VPS retention after accepted receipt | `STATE2_POLICY` | Requires retention and backup rules. |

---

# E. PresuPro estimates and matching

| Model or field | Evidence class | Source or next action |
| --- | --- | --- |
| PresuPro owns mutable estimate composition | `PRODUCT_ACCEPTED` | `00_product.md` and `SOURCE.md`. |
| Cabinet keeps immutable observed estimate snapshots | `BACKEND_DESIGN` | Required for repeatable matches and analysis. |
| Estimate-to-project relationship | `LOCAL_EVIDENCE_REQUIRED` | Inspect PresuPro project/estimate contracts. |
| `estimate_id` exact type | `LOCAL_EVIDENCE_REQUIRED` | Inspect PresuPro canonical model. |
| Estimate status vocabulary | `LOCAL_EVIDENCE_REQUIRED` | Inspect actual enum and lifecycle. |
| Stable estimate version, update timestamp, or content hash | `LOCAL_EVIDENCE_REQUIRED` | Determine available version evidence. |
| Zone identifiers and hierarchy | `LOCAL_EVIDENCE_REQUIRED` | Inspect whether stable IDs exist or fingerprints are necessary. |
| Estimate item identifiers | `LOCAL_EVIDENCE_REQUIRED` | Inspect stable IDs and update behavior. |
| Quantity, unit, unit price, waste, margin, discount, IVA, totals fields | `LOCAL_EVIDENCE_REQUIRED` | Confirm exact names, types, optionality, and calculation ownership. |
| Selecting the relevant estimate when several exist | `STATE2_POLICY` informed by local evidence | Requires actual relationship and status model. |
| Match invalidation after estimate change | `STATE2_POLICY` informed by local evidence | Requires stable identity/version facts first. |

---

# F. Holded Gateway

| Model or field | Evidence class | Source or next action |
| --- | --- | --- |
| Cabinet owns publication eligibility | `PRODUCT_ACCEPTED` | `00_product.md`. |
| Gateway owns credentials, HTTP behavior, retries, and reconciliation | `PRODUCT_ACCEPTED` | `SOURCE.md`. |
| Business publication separate from technical attempts | `BACKEND_DESIGN` | Prevents retries from creating duplicate publication intents. |
| Existing Gateway command and receipt shape | `LOCAL_EVIDENCE_REQUIRED` if implementation exists | Inspect Gateway repository or confirm that it is not yet implemented. |
| Correction after successful publication | `STATE2_POLICY` informed by Gateway evidence | Must not be invented before command/reconciliation capabilities are known. |

---

# G. Codex reconnaissance request

The following task can be given to Codex on the local platform.

## Objective

Inspect the actual local-platform repositories and return evidence needed to close Cabinet Backend State 1 and prepare State 2. Do not propose a new architecture and do not modify code.

## Repositories or projects to inspect

- Registry / `registry_sandbox`;
- PresuPro / `PresuPro_sandbox`;
- Holded Gateway, only if an implementation or specification already exists;
- local platform composition/configuration only where needed to identify supported read boundaries.

## Registry questions

1. Identify the canonical project model and exact type/format of project ID.
2. List exact fields suitable for a compact offline Cabinet catalogue: display name, address/location context, project status, customer reference, timestamps, and version evidence.
3. List the exact project status vocabulary and meanings.
4. Show how all relevant projects can be read: function/API/command, filters, pagination, and default ordering.
5. Determine whether the system exposes update timestamps, revision numbers, ETags, or deterministic content hashes.
6. Provide file paths and short code excerpts or model definitions supporting every answer.

## PresuPro questions

1. Identify the canonical estimate model and exact estimate ID type.
2. Show how an estimate links to Registry `project_id` or another project identity.
3. Explain what happens when several estimates exist for one project and list available statuses or approval states.
4. Identify exact zone and estimate-item models, including stable IDs if present.
5. List exact fields and types for quantity, unit, unit price, waste, margin, discount, IVA, and totals.
6. Identify available version evidence: revision, update time, content hash, or equivalent.
7. Show the supported read operation for obtaining complete estimate details for one project.
8. Provide file paths and supporting excerpts for every answer.

## Holded Gateway questions

1. Confirm whether a Gateway implementation/specification exists.
2. If it exists, identify publication command, idempotency support, outcome statuses, technical receipt, ambiguity handling, reconciliation, and correction support.
3. Identify which component owns credentials and transport retries.
4. Provide file paths and supporting excerpts.

## Local-platform boundary questions

1. Identify how Cabinet Backend can call Registry and PresuPro while the platform is online: in-process import, HTTP, CLI, database access, message bus, or another existing boundary.
2. Identify service discovery/configuration already used by the platform.
3. Do not recommend VPS transport or deployment technology; only report existing local capabilities and constraints.

## Required output format

Return:

1. concise findings grouped by Registry, PresuPro, Holded Gateway, and local boundary;
2. a table of exact field names, types, optionality, and authoritative owner;
3. exact repository file paths and line references;
4. unresolved or contradictory findings;
5. explicit statements where a requested capability does not exist.

Do not fill gaps with guesses. Mark unsupported assumptions as unknown.

---

## State 1 evidence result

State 1 is structurally coherent, but exact Registry and PresuPro projection fields remain intentionally unclosed until local evidence is returned. These are external-contract unknowns, not permission to use generic dictionaries or speculative fields.
