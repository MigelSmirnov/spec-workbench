from __future__ import annotations

import json
import re
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
STANDARD = ROOT / "skills" / "spec-authoring" / "SPEC_STANDARD.md"


@pytest.mark.xfail(
    strict=True,
    reason=(
        "KNOWN GAP: adapters still use legacy string mappings and requires_cache hints. "
        "Do not remove this xfail until Factory stabilization allows adapters to move to "
        "the same closed structural call-argument DSL used by rules.http_router_backend/v1."
    ),
)
def test_adapters_use_closed_structural_call_argument_dsl() -> None:
    """Document the intentional temporary mismatch between adapters and §6.1.

    Target invariant:
    - adapter arguments are structured ref objects, never expression strings;
    - adapter ref kinds come from a closed registry;
    - cache/read-once semantics are normative structure, not an agent hint;
    - adapter arity can therefore be checked against canonical contracts.

    The current standard intentionally violates this while Factory's deterministic
    data-block transition is still being stabilized. This test must XPASS only when
    the standard has actually removed the legacy forms.
    """
    text = STANDARD.read_text(encoding="utf-8")
    section = re.search(r"## 3\. adapters\n(?P<body>.*?)(?=\n---\n\n## 4\.)", text, re.S)
    assert section is not None, "adapters section must remain explicitly specified"
    body = section.group("body")

    # Legacy free-string call expressions are incompatible with the closed ref DSL
    # required by §6.1. Their disappearance is the migration signal.
    forbidden_legacy_tokens = (
        '"mapping": ["file_bytes", "file.name"]',
        '"image": "arg0"',
        '"target_dpi": "literal:300"',
        '"requires_cache": true',
        "подсказка агенту",
    )
    assert not any(token in body for token in forbidden_legacy_tokens)

    # The replacement must be normative and structural, not merely different prose.
    assert '"ref"' in body
    assert "закрыт" in body.casefold()
    assert "contracts" in body
