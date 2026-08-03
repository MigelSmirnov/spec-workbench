# State 2 decision — manual VPS retention release

## Accepted decision

Cabinet VPS keeps working copies of Invoice Cards, photographs, PDFs, and related project evidence after successful synchronization to Local Backend.

Release or removal of the VPS copies remains a manual Cabinet action in the current baseline.

Cabinet does not infer project completion from inactivity, invoice history, synchronization success, or analytics state. It also does not yet derive this decision automatically from Registry.

## Normative rules

1. Successful synchronization to Local Backend does not delete or schedule deletion of the corresponding VPS evidence.
2. VPS evidence remains available until the user explicitly requests release or archival of the project working set.
3. The manual action must identify the Registry `project_id` or the exact Cabinet working set being released.
4. Before any VPS source bytes are deleted, Local Backend must confirm that the corresponding required source replicas are present and verified in durable local storage.
5. A project cannot be released automatically merely because it appears closed, inactive, or completed in cached Registry data.
6. Registry integration for project completion remains an open compatibility question. If Registry already owns an accepted completion or archive state, a later State 2 decision may use it as a signal, but not as an implicit deletion command.
7. Even after a future Registry integration, irreversible VPS deletion must remain explicit unless a separate accepted policy changes this rule.

## User-facing behavior

The baseline operation is equivalent to:

```text
Archive or release VPS copies for project <project_id>
```

The system must show what will be affected and whether all required originals are safely stored in Local Backend before proceeding.

## Required tests

1. Successful synchronization leaves the VPS working copy intact.
2. Registry status changes alone do not delete VPS files.
3. A manual release is blocked when required local source replicas are missing or unverified.
4. A manual release may proceed after durable local verification.
5. Repeating the same release request does not recreate or duplicate deletion records.

## Open Registry check

The Registry repository or specification was not available through the connected GitHub installation during this decision. The presence and semantics of a Registry project-completion function therefore remain unverified and must be checked before designing automatic integration.
