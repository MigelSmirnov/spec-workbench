# State 6 repair — concrete local access-control contracts

## Concrete backend

```python
PostgresAccessControlBackend.__init__(
    self,
    database_url: str,
    credential_pepper: str,
) -> None

PostgresAccessControlBackend.authenticate(
    self,
    credential: str,
) -> AuthenticatedPrincipalContext

PostgresAccessControlBackend.authorize(
    self,
    principal: AuthenticatedPrincipalContext,
    operation: str,
) -> AuthorizationDecision

PostgresAccessControlBackend.enroll_local_service(
    self,
    display_name: str,
    principal_kind: str,
    capabilities: tuple[str, ...],
) -> IssuedServiceCredential

PostgresAccessControlBackend.rotate_local_service_credential(
    self,
    principal_id: str,
) -> IssuedServiceCredential

PostgresAccessControlBackend.revoke_local_service_principal(
    self,
    principal_id: str,
) -> None
```

## Composition and offline administration

```python
create_local_app() -> FastAPI

enroll_local_agent(
    display_name: str,
    capabilities: tuple[str, ...],
) -> IssuedServiceCredential

rotate_local_agent_credential(
    principal_id: str,
) -> IssuedServiceCredential

revoke_local_agent(principal_id: str) -> None
```

`PostgresAccessControlBackend` is a concrete exported class and is not declared
as another `kind: interface`. `module:bootstrap` is the sole consumer of its
constructor and offline administration methods. Runtime request handling
continues to depend on the `AccessControlBackend` port.

