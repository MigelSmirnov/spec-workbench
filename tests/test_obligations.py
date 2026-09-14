"""Obligations: read-only projection, closed registry, precedence by type."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from obligations import projection as proj
from obligations import registry

ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / "examples" / "cabinet-web-backend"


def _snapshot(directory: Path) -> dict[str, str]:
    return {str(p.relative_to(directory)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(directory.rglob("*")) if p.is_file()}


@pytest.fixture(scope="module")
def projected():
    return proj.project(CASE)


def test_registry_is_closed_and_every_mapping_lands_in_it():
    for code, kind in registry.TYPES.items():
        assert kind.code == code
        assert kind.precedence in registry.PRECEDENCE
        assert kind.derived_by.startswith(("check:", "projection"))
    for target in {*registry.FINDING_MAP.values(), *registry.CHECK_FALLBACK.values()}:
        assert target in registry.TYPES
    assert registry.classify("nowhere", "never_seen_code").code == "unclassified_finding"
    assert registry.classify("flows", "flow_capability_unreached").code == "capability_unreachable"
    assert registry.blocks(registry.TYPES["module_cut_undecided"])
    assert not registry.blocks(registry.TYPES["capability_unreachable"])


def test_projection_writes_nothing():
    before = _snapshot(CASE)
    proj.project(CASE)
    assert _snapshot(CASE) == before


def test_every_obligation_is_typed_and_addressed(projected):
    assert projected.obligations
    for obligation in projected.obligations:
        assert obligation.type in registry.TYPES
        assert obligation.addressed_to in projected.graph.nodes, obligation
    assert not [o for o in projected.obligations if o.type == "unclassified_finding"]


def test_only_defining_obligations_block(projected):
    defining = {n for n, s in projected.states.items() if any(registry.blocks(registry.TYPES[o.type]) for o in s.obligations)}
    for state in projected.states.values():
        for blocker in state.blocked_by:
            assert blocker in defining, (state.key, blocker)
        if state.state == "READY":
            assert not state.blocked_by and state.obligations


def test_capability_unreachable_is_addressed_to_the_caller(projected):
    unreached = [o for o in projected.obligations if o.type == "capability_unreachable"]
    assert unreached
    for obligation in unreached:
        assert obligation.about and obligation.about.startswith("capability:")
        assert obligation.addressed_to.startswith(("module:", "boundary:"))
        assert obligation.addressed_to != obligation.about


def test_frontier_is_several_independent_nodes(projected):
    payload = proj.frontier(projected)
    assert payload["summary"]["ready"] >= 2
    assert len(payload["ready"]) == payload["summary"]["ready"]
    precedence = [min(registry.PRECEDENCE.index(o["precedence"]) for o in n["obligations"]) for n in payload["ready"]]
    assert precedence == sorted(precedence)


def test_blocked_contract_reads_local_complete_system_blocked(projected):
    blocked = [s for s in projected.states.values() if s.kind == "contract" and s.state == "BLOCKED"]
    assert blocked
    assert any(s.local == "complete" for s in blocked)


def test_focus_shows_both_directions(projected):
    payload = proj.focus(projected, "module:effect_journal")
    assert payload["node"]["node"] == "module:effect_journal"
    assert payload["named_by_others"], "callers that must reach effect_journal capabilities"
    assert all(o["about"].startswith("capability:effect_journal.") for o in payload["named_by_others"])
    with pytest.raises(KeyError):
        proj.focus(projected, "module:does_not_exist")


def test_metrics_report_addressability_and_registry_gaps(projected):
    payload = proj.metrics(projected)
    assert payload["addressability"]["addressed"] == payload["addressability"]["total"]
    assert payload["unclassified"] == []
    assert set(payload["by_precedence"]) <= set(registry.PRECEDENCE)
    assert "available" in payload["factory"]


def test_cli_next_json_and_focus_error():
    run = subprocess.run([sys.executable, str(ROOT / "tools" / "obligations"), str(CASE), "next", "--json"], capture_output=True, text=True, check=True)
    payload = json.loads(run.stdout)
    assert payload["schema_version"] == "spec_workbench_obligations_frontier.v1"
    missing = subprocess.run([sys.executable, str(ROOT / "tools" / "obligations"), str(CASE), "focus"], capture_output=True, text=True)
    assert missing.returncode == 2
