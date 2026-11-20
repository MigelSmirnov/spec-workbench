"""workbench_state of the Workbench MCP gives the whole case beside its phase."""

from __future__ import annotations

import pytest

pytest.importorskip("mcp")

import authoring_pipeline  # noqa: E402
from workbench_mcp import server  # noqa: E402


def test_workbench_state_asks_for_the_diagnosis(monkeypatch: pytest.MonkeyPatch) -> None:
    asked = []

    def project_next(repo_root, project, *, with_diagnosis=False):
        asked.append((project, with_diagnosis))
        return {"authoring": {"phase": "imports_closure", "diagnosis": {"outcome": "open"}}}

    monkeypatch.setattr(authoring_pipeline, "project_next", project_next)
    answer = server.workbench_state("portal-deliverer")
    assert asked == [("portal-deliverer", True)]
    assert answer["authoring"]["diagnosis"] == {"outcome": "open"}
