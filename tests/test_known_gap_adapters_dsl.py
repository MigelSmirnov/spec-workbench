from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STANDARD = ROOT / "skills" / "spec-authoring" / "SPEC_STANDARD.md"


def test_adapters_use_closed_structural_call_argument_dsl() -> None:
    """Keep the version 2 replacement for legacy adapters normative."""
    text = STANDARD.read_text(encoding="utf-8")
    assert re.search(r"^## 3\. adapters$", text, re.M) is None

    forbidden_legacy_tokens = (
        '"mapping": ["file_bytes", "file.name"]',
        '"image": "arg0"',
        '"target_dpi": "literal:300"',
        '"requires_cache": true',
        "подсказка агенту",
    )
    assert not any(token in text for token in forbidden_legacy_tokens)

    assert "Несовпадение форм на стыке вызова" in text
    assert "Владелец такой ноты — caller/callsite" in text
    assert "### 6.0 Закрытый словарь backend IR" in text
    assert '{"ref": "parameter", "path": ["invoice_id"]}' in text
    assert "строковый микро-синтаксис запрещены" in text
