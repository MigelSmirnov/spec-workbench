# State 3 bounded repair — Flow 6 retention release proof completeness

This bounded State 3 repair closes the Stage 7.1 ambiguity recorded in `71_flow_6_semantic_review.md` without changing module boundaries or public signatures.

## `module:retention_release` orchestration ownership

For one manual release evaluation, `module:retention_release` owns resolving the exact affected VPS working set and proving that the supplied/obtained durable evidence covers **every required release obligation in that set**.

An allowed evaluation requires all of the following:

1. the affected working-set identity and membership are exact and stable for the evaluation;
2. every invoice/source obligation whose VPS working replica would be released is represented in the evaluated coverage set;
3. every required local durable replica obligation has authoritative positive evidence from `module:durable_archive`;
4. no required obligation is missing, unverified, inconsistent, stale, or uncovered;
5. synchronization/replica observations required by the accepted release policy are consistent with that exact set;
6. Registry status contributes no deletion authority.

`module:retention_release` may aggregate and compare evidence identities, but it must not manufacture durable proof. `module:durable_archive` remains the sole owner of authoritative local durable verification, and `module:synchronization` remains the owner of transport/replica observations.

A subset of positive durable evidence never authorizes release of a larger working set.
