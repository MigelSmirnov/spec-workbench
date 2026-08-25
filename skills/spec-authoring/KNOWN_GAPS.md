# Known specification-language gaps

This file records intentionally deferred inconsistencies in the specification language. Entries here are not accepted design patterns; they are migration debt that remains visible while dependent tooling is being stabilized.

There are currently no deferred specification-language gaps recorded here.

KG-001 was closed by `SPEC_STANDARD` version 2: the legacy top-level `adapters`
section was removed, call-site shape differences became caller-owned
requirements, and versioned backend IR now uses the closed structural `ref`
dictionary defined in §6.0.
