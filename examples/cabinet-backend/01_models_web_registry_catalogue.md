# State 1 refinement — Cabinet Web Registry catalogue boundary

## Scope

This refinement closes the identity boundary between Registry, Local Cabinet
Backend and Cabinet Web. It does not add Client, payment, procurement, logistics
or accounting Cards to Local Backend.

## RegistryProjectCatalogueEntry

One immutable projection of one Registry project observation.

Identity is the unchanged Registry project identity:

```text
project_id = Registry ProjectRecord.id
```

Fields:

- `project_id`;
- `display_name`;
- `address`;
- `status`;
- `registry_updated_at`.

Registry owns all five values. Equal display names or addresses do not establish
identity.

## RegistryCatalogueDelivery

One immutable, complete, ordered delivery from Local Cabinet Backend to Cabinet
Web. It contains:

- `contract_version = registry-catalogue-v1`;
- stable immutable `catalogue_id`;
- `generated_at`;
- `registry_observed_at`;
- SHA-256 `content_hash` over canonical ordered project entries;
- `project_count`;
- entries ordered by `project_id`.

The delivery is synchronization evidence and a transport value. It is not a
Cabinet Card and does not transfer ownership of Registry facts.

## CabinetWebProjectLink

A Cabinet Web-owned explicit relation between one Web Project Card and one
Registry `project_id`.

A missing relation is represented as `pending_registry_match`. Address,
customer name or contact hints may assist a human decision but never manufacture
a Registry identity.

Client details, payments, shopping lists, logistics, notes and derived statistics
remain Cabinet Web-owned and are not part of the Registry catalogue delivery.
