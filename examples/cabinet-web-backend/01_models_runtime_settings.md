# State 1 — Cabinet Web Backend runtime settings models

## Model M134 — RuntimeEnvironment

Values: `development`, `test`, `production`.

### Identity

value

### Identity evidence

The value names one closed deployment environment. Equal environment values
are interchangeable and carry no runtime identity.

## Model M135 — RuntimeSettings

Fields: `environment: RuntimeEnvironment`, `database_url: str`,
`auth_failures_before_throttle: int`, `auth_throttle_seconds: int`,
`chatgpt_proposal_ttl_seconds: int`, `search_default_limit: int`,
`search_max_limit: int`, `upload_handoff_ttl_seconds: int`,
`upload_max_file_bytes: int`, `source_store_root_path: str`,
`credential_pepper: str`.

### Identity

value

### Identity evidence

One instance is the immutable typed runtime-configuration snapshot loaded
before application composition. Equal field values are interchangeable. The
model carries no environment-variable parsing behavior and no product policy
beyond the accepted typed fields.
