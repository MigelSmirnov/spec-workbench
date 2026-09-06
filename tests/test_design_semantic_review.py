from __future__ import annotations

from pathlib import Path

from semantic_review import flow_slice


def test_flow_slice_collects_only_participating_contracts_and_notes(tmp_path, monkeypatch):
    flow = {
        "key": "flow:publish",
        "module_refs": ["module:publication", "module:gateway"],
        "capability_refs": [
            "capability:publication.request_publication",
            "capability:gateway.create_remote",
        ],
    }

    monkeypatch.setattr(flow_slice.design_stage4, "get_flow", lambda project, key: flow)
    monkeypatch.setattr(
        flow_slice.slice_builder,
        "build",
        lambda project, module: {
            "module": module,
            "public_operations": (
                [{"key": "public_op:publication.reconcile_publication"}]
                if module == "module:publication" else []
            ),
        },
    )
    monkeypatch.setattr(
        flow_slice,
        "_load_contracts",
        lambda project: {
            "request_publication": "() -> Publication",
            "create_remote": "() -> Attempt",
            "reconcile_publication": "() -> Publication",
            "unrelated": "() -> None",
        },
    )
    monkeypatch.setattr(flow_slice, "_load_exceptions", lambda project: {"exceptions": ["PublicationError"]})
    monkeypatch.setattr(
        flow_slice.gate,
        "coverage",
        lambda project: {
            "notes": [
                {"scope": "request_publication", "class": "BEHAVIOR", "text": "request"},
                {"scope": "create_remote", "class": "BEHAVIOR", "text": "create"},
                {"scope": "unrelated", "class": "BEHAVIOR", "text": "ignore"},
            ]
        },
    )

    payload = flow_slice.build(tmp_path, "publish")

    assert payload["flow"]["key"] == "flow:publish"
    assert payload["participating_scopes"] == [
        "create_remote",
        "reconcile_publication",
        "request_publication",
    ]
    assert set(payload["contracts"]) == {
        "create_remote",
        "reconcile_publication",
        "request_publication",
    }
    assert {note["scope"] for note in payload["notes"]} == {"create_remote", "request_publication"}
    assert payload["review_protocol"]["allowed_results"] == ["PASS", "AMBIGUITY"]


def test_flow_slice_rejects_unknown_flow(tmp_path, monkeypatch):
    monkeypatch.setattr(flow_slice.design_stage4, "get_flow", lambda project, key: None)

    try:
        flow_slice.build(tmp_path, "missing")
    except ValueError as exc:
        assert "unknown flow: flow:missing" in str(exc)
    else:
        raise AssertionError("unknown flow must fail closed")
