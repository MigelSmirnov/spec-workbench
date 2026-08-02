# Cabinet Backend — open product questions

## Status

Open State 0 decisions. No model, endpoint, table, or implementation is implied.

## Decisions that may remain open during early model work

1. Which original source binaries are stored by Cabinet, and which binary
   storage service owns them?
2. What PresuPro event produces an approved immutable presupuesto for
   downstream publication?
3. How are PresuPro zones and items mapped to Cabinet material requirements and
   later Client Portal Budget Sections?
4. What exact Cabinet facts and corrections does Client Portal accept?
5. Is Client Portal delivery push, pull, or artifact-based?
6. What production authentication and service-authorization model applies to
    users, agents, Cabinet, Registry, PresuPro, Holded Gateway, and Client
    Portal?
7. Does Holded Gateway need a separate deployable and database from its first
    release, or may it be one independently owned platform module deployed
    beside other services without direct table access?
