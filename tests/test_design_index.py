from __future__ import annotations

from pathlib import Path

import design_index
import pytest


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


def test_indexes_state1_model_as_first_class_item_without_graph_edges(
    tmp_path: Path,
) -> None:
    project = tmp_path / "demo"
    _write(
        project / "01_models.md",
        """# State 1 — Models

## Model M12 — StoredInvoiceCard

### Meaning

Archive root.

### Identity

entity

### Identity evidence

Two observations can describe the same logical invoice.
""",
    )

    item = design_index.get_item(project, "m12")

    assert item is not None
    assert item["kind"] == "model"
    assert item["state"] == 1
    assert item["explicit_id"] == "M12"
    assert item["explicit_refs"] == []
    assert [section["title"] for section in item["sections"]] == [
        "Meaning",
        "Identity",
        "Identity evidence",
    ]
    assert [entry["key"] for entry in design_index.list_items(
        project, state=1, kind="model"
    )] == ["M12"]


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


def test_broad_then_focused_mentions_preserve_expand_narrow_loop(tmp_path: Path) -> None:
    project = tmp_path / "demo"
    _write(
        project / "02_rules.md",
        """# State 2 — Rules

## Accepted decision A51 — Publish

Holded publication behavior.
""",
    )
    _write(
        project / "discovery.md",
        """# Runtime discovery

Holded returned an undocumented field during reconnaissance.
""",
    )

    broad = design_index.find_mentions(project, "Holded")
    focused = design_index.find_mentions_in_items(
        project,
        "Holded",
        state=2,
        kind="decision",
    )

    assert [(m.path, m.item_key) for m in broad] == [
        ("02_rules.md", "A51"),
        ("discovery.md", None),
    ]
    assert [(m.path, m.item_key) for m in focused] == [
        ("02_rules.md", "A51"),
    ]


def test_query_helpers_keep_explicit_graph_separate_from_navigation(tmp_path: Path) -> None:
    project = tmp_path / "demo"
    _write(
        project / "02_rules.md",
        """# State 2 — Rules

## Accepted decision A10 — Preserve source evidence

A10 delegates retention policy to A11.

### Normative rules

SourcePackage remains immutable.

## Accepted decision A11 — Retention

Retention has one owner.
""",
    )

    listed = design_index.list_items(project, state=2, kind="decision")
    assert [item["key"] for item in listed] == ["A10", "A11"]
    assert design_index.get_item(project, "a10")["title"].startswith("Accepted decision A10")

    refs = design_index.get_references(project, "A11")
    assert refs["outgoing"] == []
    assert refs["incoming"] == ["A10"]

    context = design_index.context_at(project, "02_rules.md:9", radius=1)
    assert context.item_key == "A10"
    assert context.heading_path[-1] == "Normative rules"
    assert context.start_line == 8
    assert context.end_line == 10
    assert any("SourcePackage" in line for line in context.lines)


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


def test_parses_case_insensitive_state_and_open_question_beyond_first_line(
    tmp_path: Path,
) -> None:
    project = tmp_path / "demo"
    _write(
        project / "07_questions.md",
        """---
title: Questions
---

# sTaTe 7 — Questions

## Open question OQ-12 — Retention window

How long should evidence remain available?
""",
    )

    index = design_index.build_index(project)

    assert len(index["items"]) == 1
    assert index["items"][0]["key"] == "OQ-12"
    assert index["items"][0]["kind"] == "open_question"
    assert index["items"][0]["state"] == 7


def test_reports_one_based_item_and_section_ranges(tmp_path: Path) -> None:
    project = tmp_path / "demo"
    _write(
        project / "02_rules.md",
        """# State 2

## Accepted decision A1 — One

Body.

### First section
First body.

### Second section
Second body.

## Accepted decision A2 — Two
""",
    )

    items = {item["key"]: item for item in design_index.build_index(project)["items"]}

    assert items["A1"]["source"]["start_line"] == 3
    assert items["A1"]["source"]["end_line"] == 12
    assert items["A1"]["sections"] == [
        {
            "title": "First section",
            "level": 3,
            "start_line": 7,
            "end_line": 9,
        },
        {
            "title": "Second section",
            "level": 3,
            "start_line": 10,
            "end_line": 12,
        },
    ]


def test_heading_path_replaces_same_level_sibling(tmp_path: Path) -> None:
    project = tmp_path / "demo"
    _write(
        project / "02_rules.md",
        """# State 2

## Accepted decision A1 — One

### First section

First body.

### Second section

Needle appears here.
""",
    )

    mentions = design_index.find_mentions(project, "Needle")

    assert len(mentions) == 1
    assert mentions[0].heading_path == (
        "State 2",
        "Accepted decision A1 — One",
        "Second section",
    )


def test_case_sensitive_mentions_preserve_columns_text_and_overlaps(
    tmp_path: Path,
) -> None:
    project = tmp_path / "demo"
    _write(
        project / "02_rules.md",
        """# State 2

## Accepted decision A1 — One

  ZZZ
""",
    )

    mentions = design_index.find_mentions(project, "Z", case_sensitive=True)

    assert [mention.column for mention in mentions] == [3, 4, 5]
    assert [mention.text for mention in mentions] == ["ZZZ", "ZZZ", "ZZZ"]
    assert design_index.find_mentions(project, "z", case_sensitive=True) == []


def test_list_filters_distinguish_states_and_item_kinds(tmp_path: Path) -> None:
    project = tmp_path / "demo"
    _write(
        project / "02_rules.md",
        """# State 2

## Accepted decision A1 — State two decision

## Open question OQ-1 — State two question
""",
    )
    _write(
        project / "03_rules.md",
        """# State 3

## Accepted decision A2 — State three decision
""",
    )

    assert [item["key"] for item in design_index.list_items(project, state=2)] == [
        "A1",
        "OQ-1",
    ]
    assert [
        item["key"] for item in design_index.list_items(project, kind="open_question")
    ] == ["OQ-1"]


def test_public_contract_rejects_empty_mentions_and_versions_index(
    tmp_path: Path,
) -> None:
    project = tmp_path / "demo"
    project.mkdir()

    with pytest.raises(ValueError, match="term must not be empty"):
        design_index.find_mentions(project, "")

    assert design_index.build_index(project)["schema_version"] == (
        "spec_workbench_design_index.v1"
    )


def test_references_separate_resolved_and_unresolved_targets(tmp_path: Path) -> None:
    project = tmp_path / "demo"
    _write(
        project / "02_rules.md",
        """# State 2

## Accepted decision A10 — Source owner

A10 delegates retention to A11 and leaves OQ-404 unresolved.

## Accepted decision A11 — Retention owner

Retention has one owner.
""",
    )

    references = design_index.get_references(project, "a10")

    assert references is not None
    assert references["key"] == "A10"
    assert references["outgoing"] == ["A11", "OQ-404"]
    assert [item["key"] for item in references["resolved_outgoing"]] == ["A11"]
    assert references["unresolved_outgoing"] == ["OQ-404"]
    assert design_index.get_references(project, "A999") is None
