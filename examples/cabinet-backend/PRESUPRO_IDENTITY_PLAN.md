# PresuPro identity stabilization plan

## Status

Accepted compatibility plan for Cabinet Backend State 1 and future PresuPro work.

## Current limitation

Current PresuPro provides an opaque `Estimate.id`, but does not provide:

- a stable ID for `EstimateZone`;
- a stable ID for `EstimateItem`;
- an estimate revision number;
- an estimate content hash.

Zones and items are stored as mutable ordered lists. Updating an estimate may replace the complete zone structure. Therefore a zone index, item index, name, or `material_id` is not durable identity.

## Cabinet Backend baseline

This limitation does not block the first Cabinet Backend release.

Cabinet Backend must capture an immutable `EstimateSnapshot` and compute its own canonical snapshot hash. A temporary match locator contains:

- `estimate_id`;
- Cabinet snapshot hash;
- `zone_index`;
- `item_index`;
- Cabinet-computed zone and item fingerprints;
- the copied comparable fields required to explain and reproduce the match.

The locator is valid only inside the pinned snapshot. Cabinet must not silently move a confirmed match to a later PresuPro estimate merely because an index, name, or material reference appears similar.

When PresuPro changes, Cabinet may propose a replacement match, but acceptance requires an explicit decision according to State 2 policy.

## Planned PresuPro stabilization

PresuPro should later add:

- persistent `zone_id` for every estimate zone;
- persistent `item_id` for every estimate item;
- explicit estimate `revision` or canonical `content_hash`;
- preservation of zone and item IDs when names, quantities, prices, ordering, or other mutable fields change;
- new IDs only for genuinely new zones or items;
- removal or tombstone semantics for genuinely deleted zones and items.

## Compatibility requirement

Adding stable PresuPro identities must not invalidate historical Cabinet data.

After stabilization:

- new snapshots and matches store PresuPro IDs when available;
- historical matches remain readable through their snapshot hash, indexes, fingerprints, and copied evidence;
- migration may enrich a historical reference only when identity can be established without guessing;
- ambiguous historical references remain snapshot-local and must not be auto-linked.

## Priority

This work is planned and recommended, but it is not a blocker for the first Cabinet Backend release. It should be completed before relying on automatic long-lived rematching across frequently edited estimates.
