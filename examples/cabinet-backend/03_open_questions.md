# Cabinet Backend --- Open Questions

## Status

This document records intentionally unresolved architectural questions.
Items remain here until an explicit Accepted or Rejected decision is
made.

------------------------------------------------------------------------

## OQ-001 --- PresuPro estimate versioning

**Status:** Open

**Current assumption**

-   Every imported `EstimateSnapshot` is immutable.
-   Cabinet Backend never edits an accepted snapshot.

**Needs verification**

-   Does PresuPro expose estimate versioning?
-   Is there a parent/child relationship between estimates?
-   Is there an estimate family identifier?

------------------------------------------------------------------------

## OQ-002 --- Registry project completion

**Status:** Open

**Current assumption**

-   Project completion remains a manual operation.
-   Cabinet Backend must not infer completion automatically.

**Needs verification**

-   Does Registry expose a formal completed/archived state?
-   Should that state be advisory or authoritative?

------------------------------------------------------------------------

## OQ-003 --- Registry catalogue contract

**Status:** Open

**Current assumption**

The published catalogue contains only the minimum data required for
object selection inside Cabinet.

**Needs verification**

-   Final field list.
-   Versioning strategy.
-   Refresh policy.

------------------------------------------------------------------------

## OQ-004 --- WorkObject synchronization

**Status:** Open

**Current assumption**

WorkObject belongs to the Cabinet web application and is created or
updated from the catalogue published by Cabinet Backend.

**Needs verification**

-   Exact synchronization contract.
-   Ownership of derived fields.

------------------------------------------------------------------------

## OQ-005 --- Holded reconciliation

**Status:** Open

**Current assumption**

A corrected invoice is not automatically republished.

**Needs verification**

-   Manual reconciliation workflow.
-   Possible future automation.

------------------------------------------------------------------------

## Rules

Open questions are not placeholders. No implementation may assume an
answer that has not been accepted.
