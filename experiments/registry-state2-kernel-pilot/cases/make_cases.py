"""Write the exact input cases of the pilot, from the previous experiment's witnesses.

    python experiments/registry-state2-kernel-pilot/cases/make_cases.py

cases/probe_cases.json    — slot exp_registry_audit_probe: every hypothesis,
                            contested ones included, WITHOUT expected outputs.
cases/accepted_cases.json — slot exp_registry_audit_accepted: only witnesses
                            whose expectation the current text (V6) accepts,
                            run on V6 with the default readings. Their expected
                            outputs are filled in by run_local.py from the
                            local control, and checked against the witness's
                            own expectation before they are used.
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
WIT = HERE.parents[1] / "registry-state2-investigation" / "witnesses" / "witnesses.json"
TRACE = {"kind": "trace"}


def case(cid, version, events, interp=None, setup=None, mode=None, why=""):
    return {"case": cid, "why": why, "inputs": {
        "version": version, "interpretation": interp or {}, "initial": {"setup_events": setup or []},
        "events": events, "mode": mode or TRACE}}


def main():
    wit = {w["id"]: w for w in json.loads(WIT.read_text(encoding="utf-8"))["witnesses"]}
    w01 = wit["W01"]["events"]
    probe = [
        case("p01_V0_empty_erasure", "V0", w01, why="historical defect: the draft's empty erasure (fd254d08)"),
        case("p02_V1_empty_erasure", "V1", w01, why="round 4 T12 text: rule 6 against the A15 invariant and R0-66"),
        case("p03_V4_empty_erasure", "V4", w01, why="round 11 T9 text: rule 6 against R0-66 only"),
        case("p04_V5_empty_erasure", "V5", w01, why="historical partial fix: A14 rule 5 left behind (round 12 T7)"),
        case("p05_H1_empty_erasure", "H1", w01, why="constructed partial fix: only A15 rule 6 changed"),
        case("p06_V6_empty_erasure", "V6", w01, why="the fixed text"),
        case("p07_V5_own_entry_is_change", "V5", w01, {"own_entry_is_change": True},
             why="reading-dependent: V5 consistent when the erasure's own entry counts as a change"),
        case("p08_V6_a14_literal", "V6", wit["W02"]["events"], {"a14_inv_reading": "literal"},
             why="reading-dependent: A14's equivalence read over the current log"),
        case("p09_V3a_failed_number", "V3a", wit["W16"]["events"], why="round 7 T4: ambiguity after a failed change"),
        case("p10_V1_restore", "V1", wit["W15"]["events"], why="round 2 T24: numbering across a restore"),
        case("p11_V6_restore", "V6", wit["W15"]["events"], why="R0-89: numbering per store history"),
        case("p12_V6_explore", "V6", [], mode={"kind": "explore", "depth": 4, "with_restore": True},
             why="bounded search on the current text, depth 4 with restore"),
        case("p13_V1_explore", "V1", [], mode={"kind": "explore", "depth": 4, "with_restore": True},
             why="bounded search on V1: finds the empty erasure and the restore conflicts unaided"),
        case("p14_V6_a05_covers", "V6", w01, {"a05_covers_empty_erasure": True},
             why="rejected reading: an empty erasure as an A05 repeat"),
    ]
    accepted = []
    for wid in ["W01", "W02", "W03", "W04", "W05", "W06", "W07", "W08", "W09", "W10", "W11"]:
        w = wit[wid]
        assert w["status"] == "accepted", wid
        accepted.append({**case(f"a_{wid}", "V6", w["events"], why=f"{wid} {w['title']} (accepted)"),
                         "witness_expect": w["expect"]})
    (HERE / "probe_cases.json").write_text(json.dumps(probe, indent=1) + "\n", encoding="utf-8")
    (HERE / "accepted_cases.json").write_text(json.dumps(accepted, indent=1) + "\n", encoding="utf-8")
    print(len(probe), "probe cases;", len(accepted), "accepted cases")


if __name__ == "__main__":
    main()
