# Cabinet Backend --- Accepted Follow-up Rules

## Status

This document contains accepted State 2 decisions that are intended to
be merged into `02_rules.md`.

------------------------------------------------------------------------

## A8 --- Semantic duplicate detection

-   Cabinet performs semantic duplicate detection.
-   Cabinet Backend protects only against technical duplication.
-   Backend never performs a second heuristic duplicate search.

------------------------------------------------------------------------

## A9 --- Immutable Estimate Snapshots

-   Every imported Estimate Snapshot is immutable.
-   Any change creates a new snapshot.
-   Existing matches remain linked to the original snapshot.

------------------------------------------------------------------------

## A10 --- Unmatched purchases

-   An invoice line may legitimately have no Estimate match.
-   This is an analytical state, not a data error.
-   Cabinet performs semantic analysis.
-   Cabinet Backend stores the confirmed result.

------------------------------------------------------------------------

## A11 --- Source Package

-   One Invoice Card owns one logical Source Package.
-   A Source Package may contain one or many files.
-   Additional originals may be attached later.
-   Late attachments never modify the accepted Invoice Card.

------------------------------------------------------------------------

## A15 --- Backend never edits Invoice Card

-   Invoice Card revisions are immutable.
-   Backend decisions (project assignment, publication, reconciliation)
    are stored separately.
-   A changed Card always arrives as a new confirmed revision from
    Cabinet.

------------------------------------------------------------------------

## A16 --- Unknown project

-   Missing Registry project does not reject the invoice.
-   The invoice is preserved.
-   The project assignment requires manual review.

------------------------------------------------------------------------

## A17 --- Closed project

-   Closed projects may legitimately receive later invoices.
-   A closed project is not itself an error.
-   Registry status is preserved for later analytics.
