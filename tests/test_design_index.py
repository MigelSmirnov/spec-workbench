from __future__ import annotations

from pathlib import Path

import design_index


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_indexes_explicit_decision_and_child_sections(tmp_path: Path) -> None:
    project = tmp_path / "demo"
    _write(
        project / "02_rules.md",
        """# State 2 — Rules

## Accepted decision A10 — Preserve source evidence

Text referencing A11 and OQ-004.

### Normative rules

1. Preserve bytes.

### Formal invariants

```text
source_is_immutable = true
```

## Accepted decision A11 — Retention

No explicit relation back.
""",
    )

    index = design_index.build_index(project)
    items = {item["key"]: item for item in index["items"]}

    assert set(items) == {"A10", "A11"}
    assert items["A10"]["state"] == 2
    assert items["A10"]["explicit_refs"] == ["A11", "OQ-004"]
    assert [section["title"] for section in items["A10"]["sections"]] == [
        "Normative rules",
        "Formal invariants",
    ]
    assert items["A11"]["explicit_refs"] == []


def test_same_keyword_does_not_create_relation(tmp_path: Path) -> None:
    project = tmp_path / "demo"
    _write(
        project / "02_rules.md",
        """# State 2 — Rules

## Accepted decision A51 — Publish to Holded

Holded publication behavior.

## Accepted decision A61 — Security

Holded credentials are protected.
""",
    )

    index = design_index.build_index(project)
    items = {item["key"]: item for item in index["items"]}

    assert items["A51"]["explicit_refs"] == []
    assert items["A61"]["explicit_refs"] == []


def test_mentions_keep_heading_and_item_context_without_relation(tmp_path: Path) -> None:
    project = tmp_path / "demo"
    _write(
        project / "02_rules.md",
        """# State 2 — Rules

## Accepted decision A51 — Publish

### Retry safety

Holded create is not assumed idempotent.

## Accepted decision A61 — Security

### Secret handling

Holded credentials are separate.
""",
    )

    mentions = design_index.find_mentions(project, "Holded")

    assert [(m.item_key, m.heading_path[-1]) for m in mentions] == [
        ("A51", "Retry safety"),
        ("A61", "Secret handling"),
    ]
    assert [m.line for m in mentions] == [7, 13]

    index = design_index.build_index(project)
    items = {item["key"]: item for item in index["items"]}
    assert items["A51"]["explicit_refs"] == []
    assert items["A61"]["explicit_refs"] == []


def test_supporting_decision_without_id_gets_source_key(tmp_path: Path) -> None:
    project = tmp_path / "demo"
    _write(
        project / "02_rules_retention.md",
        """# State 2 decision — manual retention release

## Accepted decision

Copies remain until explicit release.
""",
    )

    index = design_index.build_index(project)
    items = index["items"]

    assert len(items) == 1
    assert items[0]["state"] == 2
    assert items[0]["explicit_id"] is None
    assert items[0]["key"] == "source:02_rules_retention.md#accepted-decision"


def test_duplicate_explicit_ids_are_reported(tmp_path: Path) -> None:
    project = tmp_path / "demo"
    _write(project / "a.md", "# State 2\n\n## Accepted decision A1 — One\n")
    _write(project / "b.md", "# State 2\n\n## Accepted decision A1 — Two\n")

    index = design_index.build_index(project)

    assert index["diagnostics"]["duplicate_keys"] == ["A1"]
