"""The revision diagnosis (issue #147, second direction, and its addendum of 2026-11-07).

Every rule check on any revision, layered by owning state; a rule without its
inputs is not_checkable; wall-clock and elapsed-time obligations apart; the
Factory's checks of the specification and of an implementation kept apart, each
with what it read.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

import design_diagnose

MODELS = "# State 1 — Demo models\n\n## Model M01 — Thing\n\n### Identity\n\nentity\n"
API = "# State 5 — Public operations\n\n## `public_op:things.record_thing`\n\n### State impact\n\nWrites one Thing.\n"


def _write(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload if isinstance(payload, str) else json.dumps(payload, indent=1), encoding="utf-8")


def _spec(notes: list[str], *, rules: dict | None = None, imports: dict | None = None) -> dict:
    spec = {
        "standard_version": 2,
        "contracts": {"record_thing": "(name: str) -> Thing", "admit_entry": "(client: str) -> bool"},
        "module_functions": {"models": ["Thing"], "things": ["record_thing"], "guard": ["admit_entry"]},
        "module_paths": {"models": "app/models", "things": "app/things", "guard": "app/guard"},
        "models": {"Thing": {"identity": "entity", "fields": {"name": "str", "created_at": "datetime"}}},
        "notes": notes,
        "rules": rules or {},
    }
    if imports is not None:
        spec["imports"] = {"module_internal": imports}
    return spec


GUARD_NOTE = "admit_entry: [BEHAVIOR] MUST measure the entry window with a monotonic reading."
TIME_NOTE = "record_thing: [OBSERVABLE_OUTCOME] MUST stamp the thing with the current time."


# ---------------------------------------------- inputs: any ref, a raw spec

def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), "-c", "user.email=t@t", "-c", "user.name=t", *args],
                          check=True, capture_output=True, text=True).stdout.strip()


def test_a_case_is_read_as_it_was_at_the_given_ref(tmp_path):
    repo = tmp_path / "repo"
    case = repo / "examples" / "demo"
    _write(case / "01_models.md", MODELS)
    _write(case / "global_spec.json", _spec([TIME_NOTE]))
    _git(repo, "init", "-q")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "first")
    first = _git(repo, "rev-parse", "HEAD")
    _write(case / "global_spec.json", _spec([]))
    _git(repo, "commit", "-qam", "notes removed")
    now = design_diagnose.diagnose(case, "case", factory=tmp_path / "none")
    then = design_diagnose.diagnose(case, "case", ref=first, factory=tmp_path / "none")
    assert then["input"]["commit"] == first
    gaps = lambda report: [r for rows in report["by_state"].values() for r in rows if r["check"] == "closure_gaps"]
    time = lambda report: [r["counts"] for r in gaps(report) if r["owner"] == "State 2"]
    assert time(then) == [{"ambient_time_note": 1}] and time(now) == []
    assert _git(repo, "worktree", "list").count("\n") == 0          # the temporary worktree is gone


def test_a_raw_accepted_spec_reports_every_rule_it_cannot_check_as_not_checkable(tmp_path):
    spec = tmp_path / "accepted.json"
    _write(spec, _spec([TIME_NOTE]))
    report = design_diagnose.diagnose(spec, "spec", factory=tmp_path / "none")
    rows = {(r["registry"], r["check"], r["owner"]): r for rows in report["by_state"].values() for r in rows}
    for name in ("identity", "witness", "flows", "contracts", "notes", "imports", "fields", "modules"):
        row = next(r for (registry, check, _), r in rows.items() if registry == "assembly" and check == name)
        assert row["outcome"] == "not_checkable" and row["reason"].startswith("the revision has no"), name
    assert rows[("assembly", "closure_gaps", "State 2")]["outcome"] == "open"   # what the spec can show, it shows
    assert "identity" in report["summary"]["State 1"]["not_checkable"]
    assert report["input"]["spec_sha256"] and report["input"]["kind"] == "spec"


def test_findings_are_layered_by_the_state_that_owns_the_rule(tmp_path):
    case = tmp_path / "demo"
    _write(case / "01_models.md", MODELS)
    _write(case / "50_public_apis.md", API)
    _write(case / "global_spec.json", _spec([TIME_NOTE]))
    report = design_diagnose.diagnose(case, "case", factory=tmp_path / "none")
    state1 = {r["check"]: r for r in report["by_state"]["State 1"]}
    state2 = {r["check"]: r for r in report["by_state"]["State 2"]}
    assert state1["identity"]["counts"] == {"missing_model_closure": 1}
    assert state2["closure_gaps"]["counts"] == {"ambient_time_note": 1, "fresh_timestamp_without_source": 1}
    assert report["summary"]["State 2"]["open"]["assembly"] == 2


# ---------------------------------------------- wall clock and elapsed time apart

V4 = {"kind": "system_clock_backend", "schema_version": 4, "backend": {"emitter": "python_host_naive_utc_clock_v1"},
      "wiring": {"module": "clock", "function": "utc_now"},
      "time": {"policy": "rules.time_source_policy", "read": "per_call", "representation": "naive_utc_datetime"}}
V5 = {"kind": "system_clock_backend", "schema_version": 5,
      "backend": {"emitter": "python_host_naive_utc_and_elapsed_clock_v1"},
      "wiring": {"module": "clock", "wall_clock_function": "utc_now", "elapsed_clock_function": "monotonic_seconds"},
      "time": {"policy": "rules.time_source_policy", "read": "per_call", "representation": "naive_utc_datetime"}}


def _policy(elapsed: list[str] | None) -> dict:
    policy = {"kind": "time_source_policy", "schema_version": 1,
              "wall_clock": {"authority_modules": ["clock"], "allowed_primitives": ["datetime.datetime.now"],
                             "single_host_source": True, "samples_per_read": 1}}
    if elapsed is not None:
        policy["elapsed_time"] = {"authority_modules": elapsed, "allowed_primitives": ["time.monotonic"],
                                  "samples_per_read": 1, "persisted": False}
    return policy


def _time(tmp_path, rules, imports) -> dict:
    spec = tmp_path / "accepted.json"
    data = _spec([TIME_NOTE, GUARD_NOTE], rules=rules, imports=imports)
    data["module_functions"]["clock"] = ["utc_now"] + (["monotonic_seconds"] if rules["system_clock_backend"] is V5 else [])
    _write(spec, data)
    return design_diagnose.diagnose(spec, "spec", factory=tmp_path / "none")["time"]


def test_a_wall_clock_backend_does_not_cover_an_elapsed_requirement(tmp_path):
    # evidence variant 1: v4 and no elapsed_time
    time = _time(tmp_path, {"system_clock_backend": V4, "time_source_policy": _policy(None)},
                 {"things": {"clock": ["utc_now"]}})
    assert time["wall"]["outcome"] == "closed" and time["wall"]["declared"]["consumers"] == ["things"]
    assert time["elapsed"]["outcome"] == "open"
    assert [(f["code"], f["module"]) for f in time["elapsed"]["findings"]] == [
        ("elapsed_requirement_without_source", "guard")]
    assert time["elapsed"]["requirements"][0]["evidence"] == "monotonic"


def test_an_elapsed_authority_no_backend_emits_is_shown(tmp_path):
    # evidence variant 2: elapsed authority held by the guard itself
    time = _time(tmp_path, {"system_clock_backend": V4, "time_source_policy": _policy(["guard"])},
                 {"things": {"clock": ["utc_now"]}})
    assert [(f["code"], f["module"]) for f in time["elapsed"]["findings"]] == [
        ("elapsed_authority_without_backend", "guard")]


def test_a_v5_clock_imported_by_the_guard_covers_both(tmp_path):
    time = _time(tmp_path, {"system_clock_backend": V5, "time_source_policy": _policy(["clock"])},
                 {"things": {"clock": ["utc_now"]}, "guard": {"clock": ["monotonic_seconds"]}})
    assert time["wall"]["outcome"] == "closed" and time["elapsed"]["outcome"] == "closed"
    assert time["elapsed"]["declared"]["backend_operation"] == "clock.monotonic_seconds"


def test_the_bounds_of_the_analysis_are_stated(tmp_path):
    time = _time(tmp_path, {"system_clock_backend": V4, "time_source_policy": _policy(None)}, {})
    assert any("not proof that none exists" in bound for bound in time["analysis_bounds"])


# ---------------------------------------------- the Factory's checks, apart

def test_without_a_factory_or_code_both_factory_checks_are_not_checked(tmp_path):
    spec = tmp_path / "accepted.json"
    _write(spec, _spec([TIME_NOTE]))
    report = design_diagnose.diagnose(spec, "spec", factory=tmp_path / "none", code_root=None)
    assert report["factory"]["spec"]["outcome"] == "not_checked"
    assert report["factory"]["code"]["outcome"] == "not_checked"
    assert "not a passed check" in report["factory"]["code"]["reason"]
    # and the specification's own results are still shown
    assert any(r["outcome"] == "open" for rows in report["by_state"].values() for r in rows)


def _fake_factory(root: Path, validator_findings: list[dict], gate_report: dict) -> Path:
    _write(root / "tools" / "validate_spec.py",
           "import json, sys\nout = sys.argv[sys.argv.index('--out') + 1]\n"
           f"json.dump({{'status': 'FAIL', 'findings': {validator_findings!r}}}, open(out, 'w'))\n")
    _write(root / "tools" / "python_time_source_gate.py", f"import json\nprint(json.dumps({gate_report!r}))\n")
    _write(root / "tools" / "time_source_policy.py", "")
    return root


def test_the_factory_results_carry_what_they_read(tmp_path):
    factory = _fake_factory(tmp_path / "factory", [
        {"severity": "error", "subcategory": "local_implementation_requires_deterministic_backend",
         "message": "capability='elapsed_clock_authority', module='guard'"},
        {"severity": "error", "subcategory": "unrelated", "message": "x"}],
        {"verdict": "BLOCK", "findings": [{"code": "undeclared_elapsed_clock_access", "module": "guard"}]})
    code = tmp_path / "code"
    _write(code / "app" / "guard.py", "import time\n")
    spec = tmp_path / "accepted.json"
    _write(spec, _spec([GUARD_NOTE]))
    report = design_diagnose.diagnose(spec, "spec", factory=factory, code_root=code)
    checked = report["factory"]["spec"]
    assert checked["outcome"] == "open" and checked["errors"] == 2
    assert [f["subcategory"] for f in checked["time_findings"]] == ["local_implementation_requires_deterministic_backend"]
    assert set(checked["factory"]["tool_sha256"]) == {"validate_spec.py", "python_time_source_gate.py",
                                                      "time_source_policy.py"}
    gate = report["factory"]["code"]
    assert gate["outcome"] == "open" and gate["findings"][0]["code"] == "undeclared_elapsed_clock_access"
    assert list(gate["code"]["files"]) == ["guard"] and len(gate["code"]["files"]["guard"]["sha256"]) == 64


# ---------------------------------------------- the evidence, with the real Factory

REAL = design_diagnose.factory_root(None)
real = pytest.mark.skipif(REAL is None or not (REAL / "tools" / "python_time_source_gate.py").is_file(),
                          reason="no Factory checkout (SPEC_WORKBENCH_FACTORY_ROOT or sibling code_factory)")


def _real_variant(tmp_path: Path, elapsed: list[str] | None, guard_source: str) -> dict:
    """client-portal's two v4 policies (#147, 2026-11-07 15:23) on a small spec and tree."""
    sys.path.insert(0, str(REAL))
    try:
        from tools.generate_system_clock_draft import emit_module
    finally:
        sys.path.remove(str(REAL))
    data = _spec([TIME_NOTE, GUARD_NOTE], rules={"system_clock_backend": V4, "time_source_policy": _policy(elapsed)},
                 imports={"things": {"clock": ["utc_now"]}})
    data["contracts"]["utc_now"] = "() -> datetime"
    data["module_functions"]["clock"] = ["utc_now"]
    data["module_paths"]["clock"] = "app/clock"
    if elapsed:
        data["rules"]["time_source_policy"]["elapsed_time"] = {"authority_modules": elapsed,
                                                               "allowed_primitives": ["time.monotonic"]}
    spec = tmp_path / "accepted.json"
    _write(spec, data)
    code = tmp_path / "code"
    _write(code / "app" / "clock.py", emit_module(data, "clock"))
    _write(code / "app" / "things.py", "from app.clock import utc_now\n\ndef record_thing(name):\n    return utc_now()\n")
    _write(code / "app" / "guard.py", guard_source)
    return design_diagnose.diagnose(spec, "spec", factory=REAL, code_root=code)


GUARD_READS_HOST = "import time\n\ndef admit_entry(client):\n    return time.monotonic() > 0\n"


@real
def test_variant_1_v4_without_elapsed_time_is_caught_by_the_code_gate_and_the_coverage(tmp_path):
    report = _real_variant(tmp_path, None, GUARD_READS_HOST)
    assert report["factory"]["spec"]["time_outcome"] == "closed"               # the validator sees nothing of time
    assert [(f["module"], f["code"]) for f in report["factory"]["code"]["findings"]] == [
        ("guard", "undeclared_elapsed_clock_access")]                          # the gate on live code does
    assert [f["code"] for f in report["time"]["elapsed"]["findings"]] == ["elapsed_requirement_without_source"]
    assert report["factory"]["code"]["factory"]["commit"]


@real
def test_variant_2_elapsed_authority_at_the_guard_is_caught_by_the_validator_and_the_coverage(tmp_path):
    report = _real_variant(tmp_path, ["guard"], GUARD_READS_HOST)
    findings = report["factory"]["spec"]["time_findings"]
    assert [f["subcategory"] for f in findings] == ["local_implementation_requires_deterministic_backend"]
    assert "elapsed_clock_authority" in findings[0]["message"]
    assert report["factory"]["code"]["outcome"] == "closed"                    # the gate on code passes
    assert [f["code"] for f in report["time"]["elapsed"]["findings"]] == ["elapsed_authority_without_backend"]


@real
def test_without_code_the_validator_result_stands_and_the_code_is_not_checked(tmp_path):
    report = _real_variant(tmp_path, ["guard"], GUARD_READS_HOST)
    spec = tmp_path / "accepted.json"
    again = design_diagnose.diagnose(spec, "spec", factory=REAL, code_root=None)
    assert again["factory"]["code"]["outcome"] == "not_checked"
    assert again["factory"]["spec"]["time_findings"] == report["factory"]["spec"]["time_findings"]


# ---------------------------------------------- review 5813845419 of #151

def test_every_registered_check_is_in_the_coverage(tmp_path):
    from assembly_workbench.checks import CHECKS
    import transition

    spec = tmp_path / "accepted.json"
    _write(spec, _spec([TIME_NOTE]))
    report = design_diagnose.diagnose(spec, "spec", factory=tmp_path / "none")
    assert report["coverage"]["assembly"] == sorted(CHECKS)
    assert report["coverage"]["transition"] == sorted(transition.CHECKS)
    owners = {r["owner"] for rows in report["by_state"].values() for r in rows}
    assert "unresolved" not in owners


def test_a_contract_violation_outside_the_four_groups_is_shown_under_its_owner(tmp_path):
    case = tmp_path / "demo"
    _write(case / "01_models.md", MODELS)
    _write(case / "global_spec.json", _spec([]))
    _write(case / "60_contract_plan.json", {"schema_version": "spec_workbench_state6_contract_plan.v1", "status": "closed",
                                            "functions": [{"function": "record_thing", "module": "module:things",
                                                           "visibility": "internal"}]})
    _write(case / "60_contracts.json", {"schema_version": "spec_workbench_state6_contracts.v1",
                                        "contracts": {"record_thing": "not a signature"}})
    _write(case / "50_api_plan.json", {"schema_version": "spec_workbench_state5_plan.v1", "operations": []})
    report = design_diagnose.diagnose(case, "case", factory=tmp_path / "none")
    contracts = next(r for r in report["by_state"]["State 6"] if r["check"] == "contracts")
    assert contracts["outcome"] == "open" and "invalid_signature_shape" in contracts["counts"]


def test_a_check_that_fails_to_run_is_its_own_error_and_hides_nothing(tmp_path):
    spec = _spec([GUARD_NOTE, TIME_NOTE], rules={"system_clock_backend": V4, "time_source_policy": _policy(None)},
                 imports={"things": {"clock": ["utc_now"]}})
    case = tmp_path / "demo"
    _write(case / "01_models.md", MODELS)
    _write(case / "global_spec.json", spec)
    _write(case / "60_model_closure_core.json", "{ not json")
    report = design_diagnose.diagnose(case, "case", factory=tmp_path / "none")
    identity = next(r for r in report["by_state"]["State 1"] if r["check"] == "identity")
    assert identity["outcome"] == "error" and "could not run" in identity["reason"]
    assert "identity" in report["summary"]["State 1"]["error"]
    assert [f["code"] for f in report["time"]["elapsed"]["findings"]] == ["elapsed_requirement_without_source"]
    assert any(r["check"] == "closure_gaps" for rows in report["by_state"].values() for r in rows)


def test_a_validator_error_outside_time_makes_the_factory_spec_check_open(tmp_path):
    factory = _fake_factory(tmp_path / "factory", [
        {"severity": "error", "subcategory": "contract_unknown_type", "category": "contracts",
         "message": "contracts.record_thing names Unknown"}], {"verdict": "PASS", "findings": []})
    spec = tmp_path / "accepted.json"
    _write(spec, _spec([]))
    report = design_diagnose.diagnose(spec, "spec", factory=factory)
    checked = report["factory"]["spec"]
    assert checked["outcome"] == "open" and checked["time_outcome"] == "closed"
    assert [f["subcategory"] for f in checked["findings"]] == ["contract_unknown_type"]
    assert "contract_unknown_type: contracts.record_thing names Unknown" in design_diagnose.human(report)


def test_an_inconsistent_validator_result_is_not_a_pass(tmp_path):
    factory = tmp_path / "factory"
    _write(factory / "tools" / "validate_spec.py",
           "import json, sys\nout = sys.argv[sys.argv.index('--out') + 1]\n"
           "json.dump({'status': 'FAIL', 'findings': []}, open(out, 'w'))\nsys.exit(1)\n")
    spec = tmp_path / "accepted.json"
    _write(spec, _spec([]))
    checked = design_diagnose.diagnose(spec, "spec", factory=factory)["factory"]["spec"]
    assert checked["outcome"] == "error" and "no error finding" in checked["reason"]


def test_the_report_names_the_workbench_that_produced_it(tmp_path):
    spec = tmp_path / "accepted.json"
    _write(spec, _spec([]))
    workbench = design_diagnose.diagnose(spec, "spec", factory=tmp_path / "none")["workbench"]
    assert workbench["commit"] and isinstance(workbench["dirty"], bool)
    assert "tools/design_diagnose.py" in workbench["tool_sha256"]
    assert "tools/design_closure_gaps.py" in workbench["tool_sha256"]
    assert len(workbench["sequence_sha256"]) == 64 and len(workbench["standard_sha256"]) == 64


# ---------------------------------------------- review 5813967614: one Factory checkout

RULES_WITH_BINDING = """# State 2 — Demo rules

## Accepted decision A01 — things are counted

### Normative rules

A thing is counted once.

### Formal invariants

- INV-001: a thing is counted once

### Required tests

- INV-001: refused when counted twice. [witness: verification:counts_once]
"""


def _verification_factory(root: Path, with_check: bool) -> Path:
    import yaml

    commands = [{"name": "counts_once", "cwd": "../..", "command": ["python", "verification/counts_once.py"]}]
    _write(root / "verification" / "configs" / "Demo.yaml",
           yaml.safe_dump({"checks": {"commands": commands if with_check else []}}))
    _write(root / "verification" / "counts_once.py", "assert counted_once()\n")
    _write(root / "tools" / "validate_spec.py",
           "import json, sys\nout = sys.argv[sys.argv.index('--out') + 1]\n"
           "json.dump({'status': 'PASS', 'findings': []}, open(out, 'w'))\n")
    return root


def test_the_chosen_factory_is_the_one_every_witness_check_reads(tmp_path, monkeypatch):
    chosen = _verification_factory(tmp_path / "factory_a", with_check=True)
    other = _verification_factory(tmp_path / "factory_b", with_check=False)
    monkeypatch.setenv("SPEC_WORKBENCH_FACTORY_ROOT", str(other))
    case = tmp_path / "demo"
    _write(case / "02_rules.md", RULES_WITH_BINDING)
    _write(case / "90_factory_target.json", {"factory_project": "Demo"})
    _write(case / "global_spec.json", _spec([]))
    report = design_diagnose.diagnose(case, "case", factory=chosen)
    rows = {(r["registry"], r["check"]): r for r in report["by_state"]["State 2"]}
    assert rows[("assembly", "witness")]["outcome"] == "closed"            # A defines counts_once, B does not
    assert rows[("transition", "decision_witness")]["outcome"] == "closed"
    assert rows[("transition", "witness_material")]["outcome"] == "closed"
    for key in [("assembly", "witness"), ("transition", "decision_witness"), ("transition", "witness_material")]:
        assert rows[key]["factory_root"] == str(chosen)
    assert report["factory"]["spec"]["factory"]["root"] == str(chosen)
    # and the other way round: B chosen, the check is unresolved there, whatever the environment says
    monkeypatch.setenv("SPEC_WORKBENCH_FACTORY_ROOT", str(chosen))
    report = design_diagnose.diagnose(case, "case", factory=other)
    rows = {(r["registry"], r["check"]): r for r in report["by_state"]["State 2"]}
    unresolved = {"witness_unresolved": 1, "invariant_without_witness": 1}
    assert rows[("assembly", "witness")]["counts"] == unresolved
    assert rows[("transition", "decision_witness")]["counts"] == unresolved
    assert rows[("transition", "witness_material")]["outcome"] == "not_checkable"


def test_with_no_factory_chosen_or_found_no_check_finds_one_elsewhere(tmp_path, monkeypatch):
    monkeypatch.delenv("SPEC_WORKBENCH_FACTORY_ROOT", raising=False)
    monkeypatch.setattr(design_diagnose, "factory_root", lambda explicit: None)
    case = tmp_path / "demo"
    _write(case / "02_rules.md", RULES_WITH_BINDING)
    _write(case / "90_factory_target.json", {"factory_project": "Demo"})
    report = design_diagnose.diagnose(case, "case")
    rows = {(r["registry"], r["check"]): r for r in report["by_state"]["State 2"]}
    assert rows[("transition", "decision_witness")]["outcome"] == "not_checkable"
    assert rows[("transition", "decision_witness")]["factory_root"] is None
