# State 2 — Runtime composition

## Accepted decision A72 — local Linux composition is explicit and fail-closed

### Normative rules

1. `module:bootstrap` is the sole composition root for the `local_linux`
   application profile.
2. Deterministic config stores non-secret values and secret key names only;
   reusable secret values are resolved through `CredentialProvider`.
3. The credential provider receives a closed allow-list containing only the
   PostgreSQL DSN and Holded API key names required by this profile.
4. Registry and Holded repositories share the declared PostgreSQL deployment
   mechanism while exposing separate narrow business-module ports.
5. All required resources are constructed before `create_app`; any missing
   config, credential, constructor input, migration, or connectivity prerequisite
   refuses startup.
6. No business module reads environment variables, selects constructors, or
   substitutes fallback resources.
7. Application-lifecycle resources are constructed once and disposed by the
   composition root.

### Local Linux configuration

```text
postgres_dsn_secret_key = CABINET_POSTGRES_DSN
holded_api_key_secret_key = HOLDED_V1_API_KEY
holded_base_url = https://api.holded.com/api/invoicing/v1
holded_connect_timeout_seconds = 30
holded_read_timeout_seconds = 30
holded_recovery_poll_interval_seconds = 2
holded_recovery_max_wait_seconds = 30
```

These are deployment defaults and may change through deterministic config without
changing business semantics. Secret values are not specification data.

### Formal invariants

```text
required binding count per resource and profile = 1
business_module_environment_access = false
secret_value_in_deterministic_config = false
create_app_before_required_resources = false
```

### Required tests

1. Missing PostgreSQL DSN or Holded key refuses startup.
2. Duplicate or cyclic bindings refuse assembly.
3. The Holded key cannot be requested by Registry code.
4. Concrete constructors receive only declared config/binding arguments.
5. Successful construction supplies every declared `create_app` dependency once.

### Consequence

The deployment graph becomes deterministic evidence rather than hidden bootstrap
code or ambient environment behavior.

---

## Accepted decision A73 — candidate capability disposition for repaired runtime modules

### Normative rules

1. The first implementation contracts these `registry_context` capabilities:
   `refresh_registry_context`, `get_work_object`, `validate_card_assignment`, and
   `get_assignment_validation`.
2. `build_registry_catalogue` is removed as a separate public capability. Its
   accepted catalogue projection is an internal responsibility of
   `refresh_registry_context`; exposing the pipeline step would leak sequencing.
3. The first implementation contracts `create_holded_purchase` and
   `lookup_holded_purchase`.
4. `get_holded_attempt_result` is removed as a separate gateway capability.
   Committed attempt history is consumed internally through the repository port;
   external callers use logical publication/reconciliation operations.
5. `build_local_linux_application` is a contracted offline composition export and
   is never an HTTP/MCP business operation.

### Formal invariants

```text
final candidate capability without disposition = false
public internal-pipeline capability = false
bootstrap exposed as business route = false
```

### Required tests

1. Every candidate capability in the three repaired modules has exactly one
   contracted or removed disposition.
2. Removed capabilities have no contract/export/route.
3. Contracted capabilities resolve to one owned canonical contract.

### Consequence

Runtime closure can distinguish deliberately narrow module APIs from capability
loss during contract lowering.

---
