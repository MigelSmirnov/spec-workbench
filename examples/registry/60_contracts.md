# State 6 — Registry exact contracts

## Status

Draft of 2026-11-16. The function inventory is `60_contract_plan.json`, the
signatures `60_contracts.json`, the typed models `60_model_closure_domain.json`
(the twelve State 1 models, the vocabularies and the data provider's row
models) and `60_model_closure_values.json` (every model the contracts
introduce, `contract_only`). This document records why the contracts have the
shape they have and how State 6 closes what earlier states carried to it. It
adds no fact: every field is one State 1 lists or one a State 5 output names.

Before this state could be written, two gaps upstream were closed by the
owner's decisions of 2026-11-16 and reopened States 3 to 5: `configuration`
gives each secret to the module that uses it, which asks for it
(`give_service_tokens`, `give_owner_credential`); and the clock is emitted
from `system_clock_backend` v6, which owns exactly the wall and the elapsed
readings, so an action's today is `operations`' (`_today_of`).

## Shape of the contracts

- **A refusal is a value.** An operation that may refuse answers a
  `discriminated_union` of its result and `Refusal` — code, stage of A04 rule
  6, and every failure of that stage with its kind and path (State 5,
  "Stages"). The specification's exceptions carry no typed field, so a
  refusal raised would lose the kinds and paths every caller renders; a
  failure of the store's own transaction is the one refusal no module
  decides, `internal_error` (`transaction_failed`), answered by `store`.
- **One answer type for the surfaces.** `operations` answers
  `OperationAnswer`, one union over every answer a service or the owner
  reads and `RefusedAnswer`; `service_api` writes it in its wire format and
  `owner_interface` renders it. The ports that run an action's step answer it
  too.
- **Steps are ports.** The type language has no callable and no generic
  (SPEC_STANDARD §12), so "the step to run, which receives the transaction"
  (State 5) is the `TransactionStep` interface, "the request's step, which
  receives the admitted session" the `OwnerStep` interface;
  `operations` implements them (`ServiceCallStep`, `OwnerRequestStep`,
  `OwnerActionStep`). The transaction is the `StoreTransaction` interface,
  whose methods are the rows each record module reads and writes, in the
  orders A06 declares.
- **The store is a class.** A model field may not hold a connection, so the
  store this start opens is the `RegistryStore` class `store` owns; every
  store operation takes it.
- **Given values arrive as text.** A create or a correction carries its
  values as given (`GivenCustomerFacts`, `GivenProjectFacts`,
  `GivenPointer`); the record's module reads and checks them through
  `given_values` (A02) and turns them into the model's types itself
  (`_object_from_given`). A choice from a closed list arrives as text too, so
  that a value outside it is refused (A19 rule 3) rather than unreadable.
- **Types.** Identities are `str`, a UUID's text or, for an agent session,
  the identity Kernel names; instants are timezone-aware UTC `datetime`
  (L16; the clock's v6 reading); dates `date`; the floor area `Decimal`
  (fixed precision, SPEC_STANDARD §15.8); the monotonic reading `int`
  nanoseconds.
- **Erased forms are views.** A read of an anonymised project or an erased
  Customer answers a view of the same union, `AnonymisedProject` or
  `ErasedCustomer`, never a refusal (State 5, "Erased records answer").

## Formats State 6 declares

- **The service API's wire format** (`service_api`): a request is one JSON
  object, `{"operation": <name>, "inputs": {...}}`, the session Kernel names
  in the `Registry-Agent-Session` header beside the bearer token, never among
  the inputs (R0-53); an answer is one JSON object, the answer's fields or,
  for a refusal, `{"code", "stage", "failures": [{"kind", "path"}]}`.
- **The import file** (R0-72): one UTF-8 JSON object with the arrays
  `projects` (`project_id`, `name`, `address`, `status`, `customer_ref`,
  `created_at`, `updated_at`, `archived_at`), `rooms` (`room_id`,
  `project_id`, `name`, `created_at`) and `pointers` (`pointer_id`,
  `project_id`, `artifact_type`, `owner_service`, `version`, `status`, `uri`,
  `payload_ref`, `content_digest`, `created_at`, `superseded_at`); instants
  as ISO 8601 text with their offset. The v1 store keeps no archived or
  superseded instant and no digest: the export script (outside Registry)
  writes the instant of the change that archived or superseded a record, and
  no digest. Every value is read as text and checked by A16 rule 4;
  `ExportFile` keeps each record's position, so two records of one id and a
  record with no id are told apart.
- **A backup file** (A18): its first line is the record, one JSON object
  readable without the key — `record_version` (`BACKUP_RECORD_VERSION`, 1),
  `made_at`, `release_version`, `last_sequence_number`, `key_digest`; then
  the snapshot sealed with AES-256-GCM under a 256-bit key HKDF-SHA256
  derives from the backup key's UTF-8 bytes with `BACKUP_KEY_DERIVATION_INFO`,
  a random 96-bit nonce before the ciphertext, the record line as associated
  data. The key digest is `sha256:` and the lowercase hex SHA-256 of
  `BACKUP_KEY_DIGEST_DOMAIN`'s bytes, a zero byte and the key's UTF-8 bytes. A
  later algorithm is a later record version. This needs the `cryptography`
  package, pinned by digest as every dependency (A20).

## Carried to State 6, and how it is closed

| from | topic | closed by |
|---|---|---|
| State 2 round-68 T11 | the backup key's digest | "A backup file" above; the three constants in `70_data_provider_closure.json` |
| State 3 round-31 T6 | the data provider constants' exact values | `70_data_provider_closure.json`, unchanged but for the three backup constants |
| State 5 round-19 T1, round-26 T4 | environment variables to settings fields | `config.runtime_environment_variables` targets the fields of `RuntimeSettings`, one per item |
| State 5 round-19 T16 | `STORE_VERSION`, the temporary suffix | the data provider's `STORE_VERSION` 1 and `STORE_TEMPORARY_SUFFIX` `.new` |
| State 5 round-19 T17 | listener addresses | `ListenAddress` (`host` an IP address as text, `port` an `int` from `LISTEN_PORT_MIN` to `LISTEN_PORT_MAX`); the family is the host's address's |
| State 5 round-19 T19 | release and contract versions | the data provider's `RELEASE_VERSION` and `CONTRACT_VERSION`, strings fixed by each release |
| State 5 round-30 T1–T4, T6, T7, T9, T10 | `store.discard_new_store` | below |

`store.discard_new_store` answers `DiscardResult`: `removed` is true when
the store's pathname no longer names a file, and `failure` names the first
step that failed — closing the connection, a companion `-wal`, `-shm` or
`-journal`, or the store file — with its kind. The steps run in that order
and stop at the first failure (State 5). A path's type is read without
following a link: a link, a directory or any other non-regular object is left
as it is and is `not_regular_file`, which stops the rest; a path that does not
exist is nothing to remove and the next step follows; a type that cannot be
read, or a path that changes between its reading and its removal so that the
removal fails, is `type_unreadable` or `remove_failed`. After a failed close
the connection's state is unknown and nothing else is tried: the start stops
and the process ends, which releases it. Only the three suffixes of the
store's own name are ever removed, and only of a store this start made new;
a pre-existing store and its companions are never touched (A17 rule 2). A
non-regular object at the store's own pathname answers `removed: false`.
`instance_lifecycle` writes the failure's step and kind in the start's one
diagnostic, beside the listener that could not be opened, never a path's
content.

## Open

- `60_contract_plan.json` stays `open` until the State 6 transition checks
  close: the clock's `70_system_clock_closure.json` waits for the Factory's
  `system_clock_backend` v6; the model-closure and time-source checks read
  variants and read impacts as the Workbench's tools PR #186 makes them.
- States 3 to 5 reopened on 2026-11-16 need their question rounds before
  State 6 hands off.
