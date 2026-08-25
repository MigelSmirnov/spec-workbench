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


## Persistence-boundary refinement (later, authoritative)

`PostgresAccessControlBackend.*` contracts are replaced by:

- `LocalAccessControlService.__init__(self, repository: AccessControlRepository, credential_pepper: str) -> None`
  plus `authenticate`, `authorize`, `enroll_local_service`,
  `rotate_local_service_credential`, `revoke_local_service_principal` with the
  previous signatures;
- `AccessControlRepository` / `PostgresAccessControlRepository`: `begin`,
  `commit`, `rollback`, `lock_principal`, `lock_abuse_context`,
  `load_principal`, `insert_principal`, `update_principal_status`,
  `load_credential`, `list_credentials_for_principal`, `insert_credential`,
  `update_credential`, `load_throttle_state`, `upsert_throttle_state`,
  `insert_audit_record`; `create_access_control_schema(database_url: str)`;
- `issue_service_credential`, `parse_service_token`, `verify_service_secret`
  in `credential_security` (SPEC_STANDARD §6.6).
