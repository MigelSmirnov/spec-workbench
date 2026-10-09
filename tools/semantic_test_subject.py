"""What one exported semantic test is about.

An entry of ``71_semantic_test_export.json`` names the design item its test
proves: a flow (``flow_id``, as cabinet-backend's flow scenarios) or an
accepted decision (``decision_id``, as a decision's witness tests, which
prove one decision's Required tests whatever flow exercises them). Exactly
one is given, so a reader never guesses which item a test answers to.

Export and Factory admission both check entries here, so the two never
disagree on what a valid entry is.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import design_index

SUBJECT_KEYS = ("flow_id", "decision_id")
DECISION_ID_RE = re.compile(r"A\d+")


def subject_errors(item: dict[str, Any], case_root: Path) -> list[str]:
    """Reasons the entry does not name exactly one existing subject; empty when it does."""
    path = item.get("path")
    given = [key for key in SUBJECT_KEYS if key in item]
    if len(given) != 1:
        return [f"semantic test {path} must name exactly one of flow_id, decision_id"]
    key = given[0]
    value = item[key]
    if not isinstance(value, str) or not value:
        return [f"semantic test {path} has an empty {key}"]
    if key == "decision_id":
        if not DECISION_ID_RE.fullmatch(value):
            return [f"semantic test {path}: decision_id {value!r} is not an accepted decision id (A<number>)"]
        found = design_index.get_item(case_root, value)
        if found is None or found.get("kind") != "decision":
            return [f"semantic test {path}: decision {value} is not an accepted decision of the case"]
    return []


def subject(item: dict[str, Any]) -> dict[str, str]:
    """The entry's subject as it is carried into the Factory handoff."""
    return {key: item[key] for key in SUBJECT_KEYS if key in item}
