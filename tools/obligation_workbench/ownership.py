from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from .model import EvidenceRef, SemanticClaim


@dataclass(frozen=True)
class OwnershipConflict:
    semantic_key: str
    canonical_owner: str | None
    conflicting_owners: tuple[str, ...]
    conflicting_expressions: tuple[str, ...]
    evidence: tuple[EvidenceRef, ...]
    implementation_mode: str | None
    irregular_reason: str | None


def find_ownership_conflicts(claims: tuple[SemanticClaim, ...]) -> tuple[OwnershipConflict, ...]:
    """Compare only claims sharing an explicit semantic key; never infer identity from text."""
    grouped: dict[str, list[SemanticClaim]] = defaultdict(list)
    for claim in claims:
        grouped[claim.semantic_key].append(claim)

    conflicts: list[OwnershipConflict] = []
    for semantic_key, items in sorted(grouped.items()):
        canonical = [item for item in items if item.canonical]
        if not canonical:
            continue
        canonical_owners = {item.semantic_owner for item in canonical}
        shared_groups = {item.shared_owner_group for item in canonical}
        if (
            len(canonical_owners) > 1
            and len(shared_groups) == 1
            and None not in shared_groups
        ):
            continue
        canonical_owner = next(iter(canonical_owners)) if len(canonical_owners) == 1 else None
        if canonical_owner is None:
            wrong = canonical
        else:
            wrong = [
                item
                for item in items
                if not item.canonical and item.semantic_owner != canonical_owner
            ]
        if not wrong:
            continue
        implementation_modes = {
            item.implementation_mode for item in canonical if item.implementation_mode is not None
        }
        reasons = {
            item.irregular_reason for item in canonical if item.irregular_reason is not None
        }
        implementation_mode = next(iter(implementation_modes)) if len(implementation_modes) == 1 else None
        conflicts.append(OwnershipConflict(
            semantic_key=semantic_key,
            canonical_owner=canonical_owner,
            conflicting_owners=tuple(sorted({item.semantic_owner for item in wrong})),
            conflicting_expressions=tuple(sorted({item.expressed_by for item in wrong})),
            evidence=tuple(sorted({ref for item in [*canonical, *wrong] for ref in item.evidence})),
            implementation_mode=implementation_mode,
            irregular_reason=(
                next(iter(reasons))
                if implementation_mode == "irregular" and len(reasons) == 1
                else None
            ),
        ))
    return tuple(conflicts)
