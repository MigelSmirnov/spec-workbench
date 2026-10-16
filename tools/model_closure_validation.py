"""Closed form of ``kind: enum`` and its ``ordered`` flag, as the Factory checks it.

The Factory validator (``code-factory`` ``tools/type_resolver.py``,
``check_enum_declarations``) refuses these forms when the specification
reaches it. The Workbench applies the same rules with the same codes while the
models are still projected from the model closures, so the author meets the
refusal at State 8 and not after export (Q9-a, step B,
``tools/DATA_CLOSURE_PLAN_Q9A_ORDERED_ENUM.md`` §3.2).

- ``ordered`` is either absent or exactly ``true``, only on an enum, and only
  from standard_version 3.
- ``values`` of any enum is a non-empty list of distinct strings; its order is
  the only source of an ordered enum's order.
- An ordered enum names its members from ``values`` or a positional
  ``member_names`` list of the same length; ``members`` and a ``member_names``
  dict carry an order of their own. ``rank`` is reserved for the method the
  Factory emits.

A ``members``-only enum without ``values`` stays legal when it is not ordered.
"""

from __future__ import annotations

from typing import Any

from spec_language_workbench import SUPPORTED_STANDARD_VERSIONS

ORDERED_ENUM_MIN_VERSION = 3
ORDERED_ENUM_RESERVED_MEMBERS = frozenset({"rank"})


def allows_ordered_enum(version: Any) -> bool:
    return (
        type(version) is int
        and version in SUPPORTED_STANDARD_VERSIONS
        and version >= ORDERED_ENUM_MIN_VERSION
    )


def check_enum_declarations(models: Any, standard_version: Any) -> list[dict[str, str]]:
    """``{code, address, message}`` for every refused enum declaration."""
    findings: list[dict[str, str]] = []
    if not isinstance(models, dict):
        return findings

    def refuse(code: str, address: str, message: str) -> None:
        findings.append({"code": code, "address": address, "message": message})

    for name, model in models.items():
        if not isinstance(model, dict):
            continue
        where = f"models.{name}"
        is_enum = model.get("kind") == "enum"
        has_ordered = "ordered" in model
        if has_ordered and not is_enum:
            refuse("ordered_outside_enum", where, "`ordered` is defined only for kind: enum")
            continue
        if not is_enum:
            continue
        ordered = has_ordered and model["ordered"] is True
        if has_ordered and not ordered:
            refuse(
                "ordered_must_be_true", where,
                f"`ordered` is either absent or exactly true, not {model['ordered']!r}",
            )
        if ordered and not allows_ordered_enum(standard_version):
            refuse(
                "ordered_requires_standard_version_3", where,
                f"`ordered: true` requires standard_version {ORDERED_ENUM_MIN_VERSION} or later "
                f"(this spec declares {standard_version!r})",
            )

        values = model.get("values")
        if values is not None or "members" not in model:
            if not isinstance(values, list) or not values:
                refuse("enum_values_empty", where, "an enum declares a non-empty `values` list")
                values = []
            non_strings = [value for value in values if not isinstance(value, str)]
            if non_strings:
                refuse(
                    "enum_values_not_string", where,
                    f"enum values are strings; not strings: {', '.join(repr(v) for v in non_strings)}",
                )
            seen: set[str] = set()
            duplicates: list[str] = []
            for value in values:
                if isinstance(value, str):
                    if value in seen and value not in duplicates:
                        duplicates.append(value)
                    seen.add(value)
            if duplicates:
                refuse(
                    "enum_values_duplicate", where,
                    f"enum values are distinct; repeated: {', '.join(repr(v) for v in duplicates)}",
                )
        if not ordered:
            continue

        if "members" in model:
            refuse(
                "ordered_enum_members_forbidden", where,
                "an ordered enum takes its order from `values` only; `members` is not allowed",
            )
        member_names = model.get("member_names")
        if isinstance(member_names, dict):
            refuse(
                "ordered_enum_member_names_dict_forbidden", where,
                "an ordered enum names its members with a `member_names` list matched to `values` "
                "by position, not with a dict",
            )
        elif member_names is not None and (
            not isinstance(member_names, list) or len(member_names) != len(values or [])
        ):
            refuse(
                "ordered_enum_member_names_length", where,
                "an ordered enum's `member_names` is a list with exactly one name per entry of `values`",
            )
        reserved = sorted(
            {value for value in (values or []) if value in ORDERED_ENUM_RESERVED_MEMBERS}
            | {item for item in (member_names if isinstance(member_names, list) else [])
               if item in ORDERED_ENUM_RESERVED_MEMBERS}
        )
        if reserved:
            refuse(
                "ordered_enum_reserved_member", where,
                f"{', '.join(repr(r) for r in reserved)} is reserved for the generated "
                "`rank()` method of an ordered enum",
            )
    return findings


__all__ = [
    "ORDERED_ENUM_MIN_VERSION",
    "ORDERED_ENUM_RESERVED_MEMBERS",
    "allows_ordered_enum",
    "check_enum_declarations",
]
