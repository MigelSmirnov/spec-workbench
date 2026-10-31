"""Recover and re-check one experimental result from a Kernel, by its MCP entrance.

    python reproduce.py --kernel URL --token-file FILE --slot SLOT \
        [--case-input-sha SHA | --index N] [--retry-in-kernel] --out DIR

Needs only the slot id and an agent token (no author right). Uses
`get_repair_view` (spec 50_public_apis: the one read that gives an agent the
current implementation's code), then:

1. writes the code, the contract version, the corpus and the trial executions
   to DIR, and prints the code's sha256 and the implementation id;
2. picks one case (by index in corpus order, or by the sha256 of its inputs'
   canonical JSON) and its latest trial execution;
3. re-executes the recovered code on the recovered inputs locally, loading
   the module as the Kernel's runner does (not in sys.modules), and compares
   both output ports with what the Kernel recorded;
4. with --retry-in-kernel, asks the Kernel to execute that case again
   (`try_implementation`, any agent) and compares that too.

Standard library + the Factory's kernel_client.py (--client-dir).
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path


def canon(v) -> str:
    v = json.loads(v) if isinstance(v, str) else v
    return json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def ports(shown):
    return {p["port"]: p["items"][0]["json_text"] for p in (shown or [])}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kernel", required=True)
    ap.add_argument("--token-file", required=True)
    ap.add_argument("--slot", required=True)
    ap.add_argument("--index", type=int, default=0)
    ap.add_argument("--case-input-sha")
    ap.add_argument("--retry-in-kernel", action="store_true")
    ap.add_argument("--out", required=True)
    ap.add_argument("--client-dir", default=str(Path(__file__).resolve().parents[3] / "code-factory" / "tools"
                                                / "kernel_scenarios"))
    a = ap.parse_args()
    sys.path.insert(0, a.client_dir)
    from kernel_client import KernelClient  # noqa: E402
    k = KernelClient(a.kernel, Path(a.token_file).read_text().strip())
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    view = k.call("get_repair_view", {"slot_id": a.slot})
    impl = view["implementation"]
    code = impl["code"]
    (out / "code.py").write_text(code, encoding="utf-8")
    (out / "repair_view.json").write_text(json.dumps(view, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    code_sha = hashlib.sha256(code.encode()).hexdigest()
    print("slot", a.slot)
    print("purpose:", view["slot"]["slot"]["purpose"])
    print("contract_version_id", view["contract_version"]["contract_version_id"])
    print("implementation_id", impl["implementation_id"], "code sha256", code_sha)
    print("corpus", len(view["corpus"]), "cases; trial executions shown", len(view["trial_executions"]))

    corpus = view["corpus"]
    if a.case_input_sha:
        pick = [c for c in corpus if hashlib.sha256(canon({p: json.loads(t) for p, t in ports(c["inputs"]).items()})
                                                    .encode()).hexdigest() == a.case_input_sha]
        if not pick:
            raise SystemExit("no case with those inputs")
        case = pick[0]
    else:
        case = corpus[a.index]
    inputs = {p: json.loads(t) for p, t in ports(case["inputs"]).items()}
    execs = [e for e in view["trial_executions"] if e["trial_case_id"] == case["trial_case_id"]]
    recorded = execs[-1] if execs else None
    print("case", case["trial_case_id"], "inputs:", canon(inputs)[:200])
    print("expected outputs stated:", case.get("expected_outputs") is not None)

    spec = importlib.util.spec_from_file_location("cabinet_sandbox_code", out / "code.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    local = mod.run(dict(inputs))
    report = {"slot": a.slot, "implementation_id": impl["implementation_id"], "code_sha256": code_sha,
              "trial_case_id": case["trial_case_id"], "inputs": inputs}
    if recorded:
        rec = ports(recorded["outputs"])
        report["recorded_execution"] = recorded["trial_execution_id"]
        report["recorded_outcome"] = recorded["outcome"]
        report["local_equals_recorded"] = all(canon(local[p]) == canon(rec[p]) for p in rec)
    if case.get("expected_outputs"):
        exp = ports(case["expected_outputs"])
        report["local_equals_expected"] = all(canon(local[p]) == canon(exp[p]) for p in exp)
    if a.retry_in_kernel:
        again = k.call("try_implementation", {"implementation_id": impl["implementation_id"],
                                              "trial_case_ids": [case["trial_case_id"]]})[0]
        report["kernel_retry_execution"] = again["trial_execution_id"]
        report["kernel_retry_outcome"] = again["outcome"]
        report["kernel_retry_equals_local"] = all(canon(local[p]) == canon(t) for p, t in ports(again["outputs"]).items())
    report["result_analysis"] = local["analysis"]
    (out / "report.json").write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k2: v for k2, v in report.items() if k2 not in ("inputs", "result_analysis")}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
