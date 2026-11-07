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
    notes = lambda report: next(r for r in report["by_state"]["State 2"] if r["rule"].startswith("a note"))
    assert notes(then)["counts"] == {"ambient_time_note": 1} and notes(now)["outcome"] == "closed"
    assert _git(repo, "worktree", "list").count("\n") == 0          # the temporary worktree is gone


def test_a_raw_accepted_spec_reports_every_rule_it_cannot_check_as_not_checkable(tmp_path):
    spec = tmp_path / "accepted.json"
    _write(spec, _spec([TIME_NOTE]))
    report = design_diagnose.diagnose(spec, "spec", factory=tmp_path / "none")
    outcomes = {r["rule"]: r["outcome"] for rows in report["by_state"].values() for r in rows}
    assert outcomes["every model has one identity and one closure"] == "not_checkable"
    assert outcomes["every fresh timestamp has a source"] == "not_checkable"
    assert outcomes["every formal invariant is witnessed"] == "not_checkable"
    assert outcomes["every flow step is executed"] == "not_checkable"
    assert outcomes["a note that needs the time names its source"] == "open"      # what the spec can show, it shows
    assert report["summary"]["State 1"]["not_checkable"] == ["every model has one identity and one closure"]
    assert report["input"]["spec_sha256"] and report["input"]["kind"] == "spec"


def test_findings_are_layered_by_the_state_that_owns_the_rule(tmp_path):
    case = tmp_path / "demo"
    _write(case / "01_models.md", MODELS)
    _write(case / "50_public_apis.md", API)
    _write(case / "global_spec.json", _spec([TIME_NOTE]))
    report = design_diagnose.diagnose(case, "case", factory=tmp_path / "none")
    state1 = {r["rule"]: r for r in report["by_state"]["State 1"]}
    state2 = {r["rule"]: r for r in report["by_state"]["State 2"]}
    assert state1["every model has one identity and one closure"]["counts"] == {"missing_model_closure": 1}
    assert state2["every fresh timestamp has a source"]["counts"] == {"fresh_timestamp_without_source": 1}
    assert state2["a note that needs the time names its source"]["counts"] == {"ambient_time_note": 1}
    assert report["summary"]["State 2"]["open"] == 2


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
    assert report["factory"]["spec"]["outcome"] == "closed"                    # the validator sees nothing
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
