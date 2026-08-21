# State 6 refinement — Registry catalogue delivery contract

## Boundary values

```python
class RegistryProjectCatalogueEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    project_id: str
    display_name: str
    address: str | None
    status: Literal["active", "archived"]
    registry_updated_at: datetime


class RegistryCatalogueDelivery(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    contract_version: Literal["registry-catalogue-v1"]
    catalogue_id: str
    generated_at: datetime
    registry_observed_at: datetime
    content_hash: str
    project_count: int
    projects: tuple[RegistryProjectCatalogueEntry, ...]


class VpsCatalogueAcknowledgement(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    catalogue_id: str
    content_hash: str
    outcome: Literal[
        "accepted",
        "already_accepted",
        "rejected_contract",
        "catalogue_identity_conflict",
    ]
    accepted_at: datetime | None
    error_code: str | None
```

Local validation requires timezone-aware timestamps, non-empty identifiers and
display names, unique entries ordered by `project_id`, exact count, accepted
status values and a lowercase SHA-256 hash matching the canonical project tuple.

## Existing Backend operation

```python
SynchronizationService.publish_registry_catalogue(
    self,
    delivery: RegistryCatalogueDelivery,
) -> RegistryCataloguePublication
```

uses:

```python
VpsSynchronizationTransport.publish_catalogue(
    self,
    delivery: RegistryCatalogueDelivery,
) -> VpsCatalogueAcknowledgement
```

The transport adapter owns authentication, request limits, timeout and response
translation. It must not construct, filter, match or partially accept catalogue
business data.

## Cabinet Web receiver requirement

Cabinet Web exposes a receiver adapter over one transport-independent acceptance
operation equivalent to:

```python
accept_registry_catalogue(
    delivery: RegistryCatalogueDelivery,
) -> VpsCatalogueAcknowledgement
```

The acceptance operation owns validation, catalogue-ID idempotency, atomic
snapshot visibility and projection rebuild. HTTP or MCP wrappers remain thin.
Cabinet Web Card linking and statistics are explicitly outside the Backend
contract.
