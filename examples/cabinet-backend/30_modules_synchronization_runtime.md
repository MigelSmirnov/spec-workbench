# State 3 repair — synchronization runtime boundary

## Module: synchronization

The module exposes one cohesive `SynchronizationService` constructed from:

- `SynchronizationRepository`;
- `VpsSynchronizationTransport`;
- the exact `DurableArchiveService` used by local composition.

Concrete local implementations are `PostgresSynchronizationRepository` and
`HttpxVpsSynchronizationTransport`.

The service owns durable transfer reservation, authenticated delivery,
unknown-outcome reconciliation, catalogue publication, and connection
observations. It delegates exact delivered packages to `durable_archive` and
never promotes transport evidence to archive acceptance.

## Module: bootstrap

Bootstrap validates synchronization configuration, constructs both concrete
adapters and one service, and supplies that service to application composition.

No generated business module may read environment variables, create an ad-hoc
client/repository, or discover another archive runtime.
