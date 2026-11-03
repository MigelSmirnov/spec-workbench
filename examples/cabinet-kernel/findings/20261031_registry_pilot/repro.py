"""Reproduce: a module using dataclasses with deferred annotations crashes in
the Kernel's sandbox, the same module without `from __future__ import
annotations` succeeds.

    python repro.py --kernel URL --author-token-file FILE

Issues slot exp_kernel_dataclass_repro (new, experimental), one case n=3
without expected outputs, submits both modules, and tries each.
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ap = argparse.ArgumentParser()
ap.add_argument("--kernel", required=True)
ap.add_argument("--author-token-file", required=True)
ap.add_argument("--client-dir", default=str(HERE.parents[3] / "code-factory" / "tools" / "kernel_scenarios"))
a = ap.parse_args()
sys.path.insert(0, a.client_dir)
from kernel_client import KernelClient  # noqa: E402

k = KernelClient(a.kernel, Path(a.author_token_file).read_text().strip())
cv = k.call("issue_contract_version", {
    "slot_id": "exp_kernel_dataclass_repro",
    "purpose": "EXPERIMENT: reproduces a sandbox-runner finding (dataclasses with deferred annotations). Not a product function.",
    "inputs": [{"name": "n", "direction": "input", "value_schema": '{"type":"integer"}', "carriage": "value",
                "cardinality": "one", "disclosure_class": "open"}],
    "outputs": [{"name": "out", "direction": "output", "value_schema": '{"type":"integer"}', "carriage": "value",
                 "cardinality": "one"}],
    "resource_bounds": {"wall_time_ms": 10000, "memory_bytes": 134217728, "output_bytes": 1024, "process_count": 1}})
cvid = cv["contract_version"]["contract_version_id"]
case = k.call("add_trial_case", {"contract_version_id": cvid,
                                 "inputs": [{"payload_kind": "json", "port": "n", "json_text": "3"}]})
res = {"contract_version_id": cvid, "trial_case_id": case["trial_case"]["trial_case_id"]}
for name in ("repro_module_no_future.py", "repro_module.py"):
    sub = k.call("submit_implementation", {"contract_version_id": cvid, "code": (HERE / name).read_text()})
    iid = sub["implementation"]["implementation_id"]
    ex = k.call("try_implementation", {"implementation_id": iid, "trial_case_ids": []})[0]
    res[name] = {"implementation_id": iid, "verdict": sub["verdict"]["verdict"], "outcome": ex["outcome"],
                 "failure_detail": (ex.get("failure_detail") or {}).get("text"),
                 "outputs": {p["port"]: p["items"][0].get("json_text") for p in (ex.get("outputs") or [])}}
print(json.dumps(res, indent=1))
(HERE / "repro_result.json").write_text(json.dumps(res, indent=1) + "\n")
