"""Local control: the same inputs through the original model and through the bundle.

    python experiments/registry-state2-kernel-pilot/run_local.py

1. Bundle: loads adapter/kernel_function.py in a fresh module and calls
   run(inputs) for every case, exactly as the Kernel's runner would (a dict
   per port in, a dict per port out). Results: results/local_bundle.json.
2. Control: the previous experiment's own model (its sandbox.py and
   sources.py, imported from there, not from the bundle) on the trace cases,
   compared step by step with the bundle (verdicts, conflict sets, final log).
   An exploration case is compared on its finding signatures.
3. Accepted cases: the bundle's outputs become the expected outputs of
   cases/accepted_cases.json, but only after the witness's own expectation
   (from the previous experiment) is checked against them.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PREV = HERE.parent / "registry-state2-investigation"


def canonical(v) -> str:
    return json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def load_bundle():
    """Load the bundle as the Kernel's runner does (sandbox_runner.py at
    034b50c): spec_from_file_location, module_from_spec, exec_module — and
    NOT entered in sys.modules. The first version of this control registered
    the module and so hid the Kernel's crash (ADAPTATIONS.md, adaptation 3)."""
    spec = importlib.util.spec_from_file_location("cabinet_sandbox_code", HERE / "adapter" / "kernel_function.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def control(case):
    sys.path.insert(0, str(PREV / "model"))
    sys.path.insert(0, str(PREV))
    import sandbox as S  # noqa: E402  the original model
    from sources import VERSIONS  # noqa: E402
    import run as R  # noqa: E402  the original runner
    inp = case["inputs"]
    interp = {**R.DEFAULT, **inp["interpretation"]}
    version = VERSIONS[inp["version"]]
    if inp["mode"]["kind"] == "explore":
        e = R.explore(version, interp, inp["mode"]["depth"], inp["mode"]["with_restore"])
        return {"findings": sorted((f["verdict"], f["trace"][-1]) for f in e["findings"]), "states": e["states"]}
    evs = [S.Event(**x) for x in inp["initial"]["setup_events"] + inp["events"]]
    w, steps = S.run(evs, version, interp)
    n = len(inp["initial"]["setup_events"])
    return {"verdicts": [s.verdict for s in steps[n:]],
            "conflict_sets": [[list(c) for c in s.conflict_sets] for s in steps[n:] if s.verdict == "conflict"],
            "final_log": S.observe(w, None)["log"] if steps[-1].verdict not in ("conflict", "out_of_store") else None}


def bundle_view(out, case):
    a = out["analysis"]
    if case["inputs"]["mode"]["kind"] == "explore":
        return {"findings": sorted((f["verdict"], f["trace"][-1]) for f in a["findings"]), "states": a["states"]}
    return {"verdicts": [s["verdict"] for s in a["steps"]],
            "conflict_sets": [s["conflict_sets"] for s in a["steps"] if s["verdict"] == "conflict"],
            "final_log": out["observation"]["final"]["log"] if out["observation"]["final"] else None}


def check_witness(expect, out):
    final = out["observation"]["final"]
    if final is None:
        return ["stopped on a conflict"]
    log, bad = final["log"], []
    if "log_actions" in expect and [e["action"] for e in log] != expect["log_actions"]:
        bad.append("log_actions")
    if "log_conf" in expect and [e["confirmation_id"] for e in log] != expect["log_conf"]:
        bad.append("log_conf")
    if "log_seqs" in expect and [e["seq"] for e in log] != expect["log_seqs"]:
        bad.append("log_seqs")
    if "answer_at" in expect:
        i, ans, *reason = expect["answer_at"]
        got = out["observation"]["answers"][i]
        if got[1] != ans or (reason and reason[0] not in got[2]):
            bad.append("answer_at")
    for k, v in expect.get("project", {}).items():
        if (final["project"] or {}).get(k) != v:
            bad.append(f"project.{k}")
    return bad


def main() -> int:
    mod = load_bundle()
    probe = json.loads((HERE / "cases" / "probe_cases.json").read_text())
    accepted = json.loads((HERE / "cases" / "accepted_cases.json").read_text())
    results, mismatches = {}, []
    for c in probe + accepted:
        out = mod.run(dict(c["inputs"]))
        results[c["case"]] = {"observation": canonical(out["observation"]), "analysis": canonical(out["analysis"])}
        ctl, bv = control(c), bundle_view(out, c)
        if canonical(ctl) != canonical(bv):
            mismatches.append({"case": c["case"], "control": ctl, "bundle": bv})
    for c in accepted:
        out = {k: json.loads(v) for k, v in results[c["case"]].items()}
        bad = check_witness(c["witness_expect"], out)
        if bad:
            mismatches.append({"case": c["case"], "witness_expectation_failed": bad})
        c["expected_outputs"] = {"observation": out["observation"], "analysis": out["analysis"]}
    (HERE / "cases" / "accepted_cases.json").write_text(json.dumps(accepted, indent=1) + "\n", encoding="utf-8")
    (HERE / "results" / "local_bundle.json").write_text(json.dumps(results, indent=1, ensure_ascii=False) + "\n",
                                                        encoding="utf-8")
    (HERE / "results" / "local_vs_control.json").write_text(json.dumps(
        {"cases": len(probe) + len(accepted), "mismatches": mismatches}, indent=1) + "\n", encoding="utf-8")
    print(f"{len(probe)} probe + {len(accepted)} accepted cases; bundle vs control mismatches: {len(mismatches)}")
    for m in mismatches:
        print(" ", json.dumps(m)[:400])
    return 1 if mismatches else 0


if __name__ == "__main__":
    sys.exit(main())
