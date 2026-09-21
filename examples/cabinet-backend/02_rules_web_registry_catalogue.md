# State 2 refinement — Cabinet Web Registry catalogue rules

## Accepted decision — Backend publishes identity context, not Web business data

1. Registry remains authoritative for project identity and current Registry
   fields.
2. Local Cabinet Backend performs the already accepted full Registry observation
   and publishes one complete compact catalogue to Cabinet Web.
3. Publication direction is one-way:
   `Registry -> Local Cabinet Backend -> Cabinet Web`.
4. Cabinet Web never writes Registry-owned project fields back through this
   contract.
5. The V1 entry contains exactly `project_id`, `display_name`, `address`,
   `status`, and `registry_updated_at`.
6. Entries are ordered by stable `project_id`; duplicate IDs invalidate the
   whole delivery.
7. The receiver validates the complete envelope, count and canonical content hash
   before making a new snapshot visible. Partial acceptance is forbidden.
8. Repeating the same `catalogue_id` with the same content hash is idempotent.
   Reusing it with different content is a contract conflict.
9. Absence from a later full observation is not proof of deletion and must not
   silently delete Cabinet Web working data.
10. Cabinet Web stores its Project Card relation separately from the Registry
    snapshot.
11. An existing Web Project Card without a confirmed `project_id` remains
    visible as `pending_registry_match`.
12. Matching by address, title, client or contact is advisory only. An ambiguous
    parser or agent must ask for a decision rather than guess or fail the
    catalogue import.
13. Client contacts, received money, work/material allocation, shopping lists,
    purchases, logistics and Web analytics are excluded from this delivery and
    remain owned by Cabinet Web.
14. Invoice archive, accounting and Holded behavior are unchanged by this
    contract.

## Compatibility

An unsupported `contract_version`, invalid field set, invalid status, bad hash,
duplicate ID, unordered entry set or count mismatch rejects the complete
delivery with a deterministic outcome. The previously accepted Web snapshot
remains available.

## Security

Catalogue delivery uses the existing synchronization-only authenticated node
boundary. Local human, local agent and accounting credentials cannot substitute
for that identity. The receiver enforces payload-size and project-count limits
at the transport adapter without truncating a valid business delivery.
