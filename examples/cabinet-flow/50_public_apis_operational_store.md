# State 5 — Cabinet Flow operational-store operations

The store exposes one bounded transactional unit of work to domain modules. It
enforces persistence shape, atomicity, append-only records and compare-and-set;
it never decides whether a domain mutation is allowed.

## `public_op:operational_store.begin_unit_of_work`

### Owner

`module:operational_store` owns creation of one isolated transactional unit of
work over kernel-owned durable records.

### Callers

In the State 4 flows, `module:semantic_vocabulary` uses it for idempotent seed
installation and `module:access_control` uses it for delegation issuance or
revocation. Other owning domain modules use the same boundary for their closed
mutations.

### Inputs

A closed purpose/record-family discriminator and a bounded correlation identity.
Compare-and-set is the owning function comparing an expected value with the
record it loaded inside the unit. No
SQL, table name, query, host path or business payload outside typed durable
M01–M49 kernel records is accepted.

### Outputs

One single-use `OperationalUnitOfWork` — the typed record port — scoped to the calling module and one
transaction, with read/write access only to declared kernel record kinds.

### Observable effect

The store establishes isolation and captures the expected versions/locks needed
for later atomic commit. No durable domain change is visible yet.

### Enforces

One active transaction per handle; declared durable record families only;
append-only record kinds cannot be updated/deleted; immutable versions remain
immutable; one writer at a time, so a loaded record cannot change before commit; credentials and business
facts are not persistable.

### Errors

Unavailable or unmigrated store, unknown record family, nested/reused handle,
and attempt to open unsupported persistence
are refused before a mutable transaction is exposed.

### State impact

No committed state. Implementation-level transaction/lock resources exist only
until commit or rollback.

## `public_op:operational_store.commit_unit_of_work`

### Owner

`module:operational_store` owns atomic validation and publication of one unit of
work.

### Callers

The domain module that successfully completed the operation begun through
`begin_unit_of_work`; State 4 explicitly uses it from
`module:semantic_vocabulary` and `module:access_control`.

### Inputs

The exact open unit of work and the typed record changes made through it. Domain
authorization or semantic validity is not supplied to or inferred by the
store.

### Outputs

A commit result containing the durable transaction identity and committed
record versions, or a typed conflict/failure with no partial publication.

### Observable effect

All staged kernel-record changes become durable and visible atomically, or none
do. Append-only records are inserted once; compare-and-set records change only
from their expected version.

### Enforces

Schema validity, referential persistence shape, append-only immutability,
compare-and-set, transaction isolation and all-or-nothing visibility. The store
never fabricates a successful commit after uncertain durability.

### Errors

Closed/reused handle, stale compare-and-set, uniqueness conflict, immutable
mutation, invalid record shape, unavailable durability and commit uncertainty
return typed failure; uncertain commit requires store-level recovery evidence,
not caller retry by assumption.

### State impact

Exactly the staged kernel-owned records become durable as one transaction. No
business-service state or file outside permitted trial fixtures is affected.

## `public_op:operational_store.rollback_unit_of_work`

### Owner

`module:operational_store` owns complete abandonment of one uncommitted unit of
work.

### Callers

`module:value_store` and `module:run_spool` use it when the retention sweep
cannot complete consistently; any domain module may use it after its own
pre-commit failure.

### Inputs

The exact open unit of work and a bounded internal failure category. No
request can use rollback to delete previously committed evidence.

### Outputs

A rollback confirmation that no staged change became visible, or an explicit
infrastructure failure requiring startup recovery before serving.

### Observable effect

All staged changes and transaction-local resources are discarded; previously
committed records are untouched.

### Enforces

Rollback applies only to the active uncommitted transaction, is idempotent for
the same completed rollback, cannot reverse a commit, and leaves no partially
visible retention or domain change.

### Errors

Unknown handle, handle committed under a concurrent outcome, rollback failure
and unavailable store are explicit. The kernel must not serve while transaction
outcome is uncertain.

### State impact

No committed domain state changes. Transaction-local staged state is removed.

## `public_op:operational_store.open_store`

### Owner

`module:operational_store` owns the one opening of the data directory (A30).

### Callers

`module:bootstrap`, once per process start, before any unit of work.

### Inputs

The data directory and installation identity from the loaded installation facts
and the host copy of the effect counter, or nothing when the host holds none.

### Outputs

Whether the store is a new installation, continuous or restored, and the
store's effect counter.

### Observable effect

The directory, the database file, the value area and the schema are created
when absent; the write-ahead journal is enabled. A new installation writes its
StoreContinuity M50 with counter zero and effects open. A restored store has
`effects_open` set false and the detection instant recorded.

### Enforces

A30 rules 3 and 6: one opening per process; `begin_unit_of_work` is refused
before it; an empty store with no host copy is new, equal counters are
continuous, anything else is restored. A store of another installation is
refused.

### Errors

Relative or unusable directory, schema that cannot be created, a store of
another installation and a second opening are typed startup refusals.

### State impact

At most the StoreContinuity M50 record.
