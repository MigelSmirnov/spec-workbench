"""Run the pilot through a Cabinet Kernel, by its MCP entrance only.

    python experiments/registry-state2-kernel-pilot/run_kernel.py \
        --kernel http://127.0.0.1:<port> --author-token-file <file> --label <label>

Uses the Factory's own client (code-factory tools/kernel_scenarios/
kernel_client.py, standard library only); the path is given by
--client-dir (default: the code-factory checkout beside spec-workbench).
Tokens are read from files and never printed or written.

What it does, in this order — nothing else is touched:

1. issue_contract_version for two NEW experimental slots:
   exp_registry_audit_probe    (every hypothesis; cases without expected outputs)
   exp_registry_audit_accepted (accepted V6 witnesses; cases with expected outputs)
2. add_trial_case for every case of cases/probe_cases.json and
   cases/accepted_cases.json (append-only corpora; equal cases are returned,
   not duplicated).
3. submit_implementation of adapter/kernel_function.py to each slot. The
   Kernel runs admission over the slot's corpus and, if admitted, activates
   the implementation in THAT slot (spec A04 rules 2-4). Both slots are new
   and no flow uses them, so the activation serves nothing.
4. try_implementation on the probe slot: one trial execution per case, with
   its outputs shown (disclosure class `open`).
5. Reads back what the Kernel keeps: get_slot, get_contract_version,
   get_implementation, list_records of trial cases, executions and verdicts
   (activations are not a listable record type; get_slot shows the current one).

Writes kernel/<label>/ids.json (every object identity), kernel/<label>/
trace.json (requests' operation names and the answers, verbatim) and
results/kernel_<label>.json (outputs per case).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

SLOT_PROBE = "exp_registry_audit_probe"
SLOT_ACCEPTED = "exp_registry_audit_accepted"
PURPOSE = {
    SLOT_PROBE: ("EXPERIMENT (spec-workbench experiments/registry-state2-kernel-pilot): a pure model of "
                 "Registry State 2 audit rules over synthetic data. Probe cases carry no expected outputs: "
                 "they are hypotheses under study, not product expectations. Not a product function; no flow "
                 "uses it."),
    SLOT_ACCEPTED: ("EXPERIMENT (spec-workbench experiments/registry-state2-kernel-pilot): the same model; its "
                    "cases are only witnesses the current Registry text (V6) accepts, with expected outputs. "
                    "Not a product function; no flow uses it."),
}
IN_PORTS = [("events", '{"type":"array"}'), ("initial", '{"type":"object"}'),
            ("interpretation", '{"type":"object"}'), ("mode", '{"type":"object"}'),
            ("version", '{"type":"string"}')]
OUT_PORTS = [("analysis", '{"type":"object"}'), ("observation", '{"type":"object"}')]
BOUNDS = {"wall_time_ms": 30000, "memory_bytes": 268435456, "output_bytes": 1048576, "process_count": 1}


def port(name, schema, direction):
    p = {"name": name, "direction": direction, "value_schema": schema, "carriage": "value",
         "cardinality": "one"}
    if direction == "input":
        p["disclosure_class"] = "open"
    return p


def payloads(values: dict):
    return [{"payload_kind": "json", "port": k,
             "json_text": json.dumps(v, ensure_ascii=False, separators=(",", ":"), sort_keys=True)}
            for k, v in sorted(values.items())]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kernel", required=True)
    ap.add_argument("--author-token-file", required=True)
    ap.add_argument("--label", required=True, help="where this kernel is: e.g. local-034b50c")
    ap.add_argument("--client-dir", default=str(HERE.parents[2] / "code-factory" / "tools" / "kernel_scenarios"))
    a = ap.parse_args()
    sys.path.insert(0, a.client_dir)
    from kernel_client import KernelClient, KernelRefusal  # noqa: E402

    token = Path(a.author_token_file).read_text().strip()
    k = KernelClient(a.kernel, token)
    trace, ids = [], {"kernel": a.kernel, "label": a.label}

    def call(op, args):
        try:
            ans = k.call(op, args)
            trace.append({"op": op, "answer": ans})
            return ans
        except KernelRefusal as r:
            trace.append({"op": op, "refused": {"code": r.code, "reason": r.reason}})
            raise

    code = (HERE / "adapter" / "kernel_function.py").read_text(encoding="utf-8")
    ids["code_sha256"] = hashlib.sha256(code.encode()).hexdigest()
    corpora = {SLOT_PROBE: json.loads((HERE / "cases" / "probe_cases.json").read_text()),
               SLOT_ACCEPTED: json.loads((HERE / "cases" / "accepted_cases.json").read_text())}
    out = {"label": a.label, "slots": {}}
    for slot, cases in corpora.items():
        cv = call("issue_contract_version", {
            "slot_id": slot, "purpose": PURPOSE[slot],
            "inputs": [port(n, s, "input") for n, s in IN_PORTS],
            "outputs": [port(n, s, "output") for n, s in OUT_PORTS],
            "resource_bounds": BOUNDS})
        cvid = cv["contract_version"]["contract_version_id"]
        sl = {"contract_version_id": cvid, "cases": {}}
        for c in cases:
            req = {"contract_version_id": cvid, "inputs": payloads(c["inputs"])}
            if "expected_outputs" in c:
                req["expected_outputs"] = payloads(c["expected_outputs"])
            added = call("add_trial_case", req)
            sl["cases"][c["case"]] = added["trial_case"]["trial_case_id"]
        sub = call("submit_implementation", {"contract_version_id": cvid, "code": code})
        sl["implementation_id"] = sub["implementation"]["implementation_id"]
        sl["verdict"] = sub["verdict"]
        sl["activation"] = sub.get("activation")
        out["slots"][slot] = sl
    # trial executions with outputs, on the probe slot
    pr = out["slots"][SLOT_PROBE]
    tried = call("try_implementation", {"implementation_id": pr["implementation_id"], "trial_case_ids": []})
    by_case = {v: k2 for k2, v in pr["cases"].items()}
    pr["executions"] = {}
    for ex in tried:
        outs = {p["port"]: p["items"][0].get("json_text") for p in (ex.get("outputs") or [])}
        pr["executions"][by_case[ex["trial_case_id"]]] = {
            "trial_execution_id": ex["trial_execution_id"], "outcome": ex["outcome"],
            "outputs": outs, "resources_used": ex["resources_used"]}
    # read back
    for slot in corpora:
        call("get_slot", {"slot_id": slot})
        call("get_contract_version", {"contract_version_id": out["slots"][slot]["contract_version_id"]})
        call("get_implementation", {"implementation_id": out["slots"][slot]["implementation_id"]})
    # activations are not listable (data_provider.LISTABLE_RECORD_TYPES); get_slot shows the current one
    for rt in ("trial_case", "trial_execution", "admission_verdict"):
        call("list_records", {"record_type": rt, "page_size": 200})
    d = HERE / "kernel" / a.label
    d.mkdir(parents=True, exist_ok=True)
    ids.update({s: {kk: vv for kk, vv in v.items() if kk in ("contract_version_id", "implementation_id", "cases")}
                for s, v in out["slots"].items()})
    (d / "ids.json").write_text(json.dumps(ids, indent=1) + "\n", encoding="utf-8")
    (d / "trace.json").write_text(json.dumps(trace, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    (HERE / "results" / f"kernel_{a.label}.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n",
                                                             encoding="utf-8")
    for s, v in out["slots"].items():
        print(s, v["verdict"]["verdict"], (v["verdict"].get("reason") or ""), "activation:", bool(v["activation"]))
    print("probe executions:", {c: e["outcome"] for c, e in pr["executions"].items()})
    return 0


if __name__ == "__main__":
    sys.exit(main())
