"""Compare the Kernel's outputs with the local control, case by case.

    python experiments/registry-state2-kernel-pilot/compare.py --label <label>

Probe slot: the Kernel's trial-execution outputs (json_text) against
results/local_bundle.json, both re-encoded as sorted, compact JSON and compared
as bytes. Accepted slot: the admission verdict already compared every output
digest with the expected one. Writes results/comparison_<label>.json and
results/comparison_<label>.md.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def canon(text_or_value):
    v = json.loads(text_or_value) if isinstance(text_or_value, str) else text_or_value
    return json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def summary(analysis: dict) -> str:
    if analysis["kind"] == "explore":
        kinds = {}
        for f in analysis["findings"]:
            kinds[f["verdict"]] = kinds.get(f["verdict"], 0) + 1
        return f"explore depth {analysis['depth']}: {analysis['states']} states; findings {kinds or 'none'}"
    steps = analysis["steps"]
    last = steps[-1] if steps else {}
    s = analysis["classification"]
    if last.get("verdict") == "conflict":
        s += " at `" + last["event"] + "`: " + "; ".join("{" + ", ".join(c) + "}" for c in last["conflict_sets"][:3])
        s += f" (resolution {last['resolution']})"
    if last.get("verdict") in ("ambiguity", "out_of_store"):
        s += " at `" + last["event"] + "`: " + " / ".join(last["outcomes"])
    amb = [x for x in steps if x["verdict"] == "ambiguity"]
    if amb and last.get("verdict") != "ambiguity":
        s += " — ambiguity at `" + amb[0]["event"] + "`: " + " / ".join(amb[0]["outcomes"])
    return s


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    a = ap.parse_args()
    local = json.loads((HERE / "results" / "local_bundle.json").read_text())
    kern = json.loads((HERE / "results" / f"kernel_{a.label}.json").read_text())
    probe_cases = {c["case"]: c for c in json.loads((HERE / "cases" / "probe_cases.json").read_text())}
    rows, diffs = [], []
    for case, ex in kern["slots"]["exp_registry_audit_probe"]["executions"].items():
        same = all(canon(ex["outputs"][p]) == canon(local[case][p]) for p in ("observation", "analysis"))
        if not same:
            diffs.append(case)
        rows.append({"case": case, "kernel_outcome": ex["outcome"], "equal_to_local": same,
                     "wall_time_ms": ex["resources_used"]["wall_time_ms"],
                     "memory_bytes": ex["resources_used"]["memory_bytes"],
                     "result": summary(json.loads(ex["outputs"]["analysis"])),
                     "why": probe_cases[case]["why"]})
    acc = kern["slots"]["exp_registry_audit_accepted"]["verdict"]
    res = {"label": a.label, "probe": rows, "probe_differences": diffs,
           "accepted_slot_verdict": acc}
    (HERE / "results" / f"comparison_{a.label}.json").write_text(json.dumps(res, indent=1, ensure_ascii=False) + "\n")
    L = [f"# Kernel ({a.label}) against the local control", "",
         f"Probe slot: {len(rows)} cases, {len(rows) - len(diffs)} equal to the local bundle byte for byte "
         f"(sorted compact JSON of both output ports).", "",
         f"Accepted slot: admission verdict `{acc['verdict']}` over {len(acc['trial_executions'])} cases with "
         "expected outputs (the Kernel compared every output digest).", "",
         "| case | Kernel execution | = local | wall ms | model result (what the hypothesis gives) |",
         "|---|---|---|---|---|"]
    for r in rows:
        L.append(f"| {r['case']} | {r['kernel_outcome']} | {'yes' if r['equal_to_local'] else 'NO'} | "
                 f"{r['wall_time_ms']} | {r['result']} |")
    (HERE / "results" / f"comparison_{a.label}.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))
    return 1 if diffs else 0


if __name__ == "__main__":
    raise SystemExit(main())
