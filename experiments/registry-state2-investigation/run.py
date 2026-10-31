"""Run the experiment: witnesses on every text version, then bounded exploration.

    python experiments/registry-state2-investigation/run.py [--depth N]

Writes results/witnesses.json, results/witnesses.md, results/exploration.json,
results/exploration.md. Deterministic: the same commit gives the same files.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from collections import deque
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "model"))
from sandbox import (Event, alphabet, apply, check, initial, observe, rules_for, run, step)  # noqa: E402
from sources import VERSIONS  # noqa: E402

# Readings the texts leave open, each argued in model/TRACEABILITY.md. The
# default is the reading the experiment takes; every other value is run too,
# one dimension at a time.
INTERPRETATIONS = {
    "own_entry_is_change": (False, True),
    "a15_inv_presupposes": (True, False),
    "a14_inv_reading": ("at_commit", "literal"),
    "durable_counter": ("in_store", "outside_store"),
    "v0_counter": ("kept", "unstated"),
    "a05_covers_empty_erasure": (False, True),
    "id_formats_strict": (False, True),
}
DEFAULT = {k: v[0] for k, v in INTERPRETATIONS.items()}


def interp_variants():
    yield "default", dict(DEFAULT)
    for k, vals in INTERPRETATIONS.items():
        for v in vals[1:]:
            yield f"{k}={v}", {**DEFAULT, k: v}


def to_event(d: dict) -> Event:
    return Event(**d)


def check_expect(w, steps, expect) -> list[str]:
    obs = observe(w, None)
    log = obs["log"]
    bad = []
    if "answer_at" in expect:
        i, ans, *reason = expect["answer_at"]
        got = steps[i].checked
        if got.answer != ans or (reason and reason[0] not in got.reasons):
            bad.append(f"step {i}: answer {got.answer} {list(got.reasons)}, expected {ans} {reason}")
    if "log_actions" in expect and [e["action"] for e in log] != expect["log_actions"]:
        bad.append(f"log actions {[e['action'] for e in log]}, expected {expect['log_actions']}")
    if "log_conf" in expect and [e["confirmation_id"] for e in log] != expect["log_conf"]:
        bad.append(f"confirmation ids {[e['confirmation_id'] for e in log]}, expected {expect['log_conf']}")
    if "log_seqs" in expect and [e["seq"] for e in log] != expect["log_seqs"]:
        bad.append(f"sequence numbers {[e['seq'] for e in log]}, expected {expect['log_seqs']}")
    if "project" in expect:
        for k, v in expect["project"].items():
            if (obs["project"] or {}).get(k) != v:
                bad.append(f"project {k} = {(obs['project'] or {}).get(k)}, expected {v}")
    if expect.get("distinct_confirmation_ids"):
        confs = [e.conf for e in w.store.log if e.conf is not None]
        if len(confs) != len(set(confs)):
            bad.append("a confirmation id repeats")
    return bad


def describe(s) -> dict:
    d = {"event": s.event.label(), "verdict": s.verdict}
    if s.verdict == "conflict":
        d["conflict_sets"] = [list(c) for c in s.conflict_sets]
        d["resolution"] = s.resolution
        d["candidates"] = {o.label(): v for o, v in s.violations.items()}
    if s.verdict == "ambiguity":
        d["outcomes"] = [o.label() for o, _ in s.passing]
    if s.verdict == "out_of_store":
        d["outcomes_needing_outside_knowledge"] = [o.label() for o, _ in s.passing]
    return d


def run_witnesses() -> dict:
    data = json.loads((HERE / "witnesses" / "witnesses.json").read_text(encoding="utf-8"))
    out = {}
    for w in data["witnesses"]:
        evs = [to_event(e) for e in w["events"]]
        per = {}
        for vn, version in VERSIONS.items():
            per_interp = {}
            for iname, interp in interp_variants():
                world, steps = run(evs, version, interp)
                final = steps[-1]
                if final.verdict in ("conflict", "out_of_store"):
                    res = {"result": final.verdict.upper(), "at": len(steps) - 1, "step": describe(final)}
                else:
                    amb = [describe(s) for s in steps if s.verdict == "ambiguity"]
                    bad = check_expect(world, steps, w["expect"])
                    res = {"result": "AMBIGUOUS" if amb else ("PASS" if not bad else "FAIL")}
                    if amb:
                        res["ambiguities"] = amb
                        # every passing branch, to show the two outcomes
                        res["branches"] = []
                        for k in range(len([s for s in steps if s.verdict == "ambiguity"][0].passing)):
                            wk, sk = run(evs, version, interp, choose=lambda s, k=k: min(k, len(s.passing) - 1))
                            res["branches"].append({"log": observe(wk, None)["log"],
                                                    "expected_holds": not check_expect(wk, sk, w["expect"])})
                    if bad:
                        res["mismatch"] = bad
                    res["log"] = observe(world, None)["log"]
                per_interp[iname] = res
            per[vn] = per_interp
        out[w["id"]] = {"title": w["title"], "status": w["status"], "versions": per}
    return out


def explore(version: dict, interp: dict, depth: int, with_restore: bool) -> dict:
    rules = rules_for(version)
    events = alphabet(with_restore)
    start = initial()
    frontier = deque([(start, ())])
    seen = {start}
    findings: dict[tuple, dict] = {}
    states = transitions = 0
    for _ in range(depth):
        nxt = deque()
        while frontier:
            w, trace = frontier.popleft()
            for ev in events:
                transitions += 1
                s = step(w, ev, rules, version, interp)
                if s.verdict in ("conflict", "ambiguity", "out_of_store"):
                    if s.verdict == "conflict":
                        sig = (s.verdict, ev.kind, tuple(sorted(tuple(c) for c in s.conflict_sets)))
                    elif s.verdict == "ambiguity":
                        sig = (s.verdict, ev.kind, tuple(sorted(o.label() for o, _ in s.passing)) and
                               tuple(sorted({("entry" if o.entry else "none", o.conf) for o, _ in s.passing})))
                    else:
                        sig = (s.verdict, ev.kind)
                    if sig not in findings:
                        findings[sig] = {"trace": [e.label() for e in trace] + [ev.label()],
                                         "length": len(trace) + 1, **describe(s)}
                successors = list(s.passing)
                if s.verdict == "conflict":
                    # go on past a conflict with the outcomes that break the
                    # fewest passages: the implementations closest to the text
                    least = min(len(v) for v in s.violations.values())
                    successors = []
                    for o, v in s.violations.items():
                        if len(v) == least:
                            c = check(w, ev)
                            successors.append((o, apply(w, ev, c, o, version["numbering"], interp)))
                for o, post in successors:
                    if post not in seen:
                        seen.add(post)
                        states += 1
                        nxt.append((post, trace + (ev,)))
        frontier = nxt
    return {"depth": depth, "with_restore": with_restore, "states": states + 1,
            "transitions": transitions, "findings": list(findings.values())}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--depth", type=int, default=6)
    args = ap.parse_args()
    res_dir = HERE / "results"
    res_dir.mkdir(exist_ok=True)
    t0 = time.time()
    wres = run_witnesses()
    (res_dir / "witnesses.json").write_text(json.dumps(wres, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    exp = {}
    for vn, version in VERSIONS.items():
        exp[vn] = {}
        for iname, interp in interp_variants():
            for restore in (False, True):
                if restore and iname != "default" and not iname.startswith(("durable_counter", "v0_counter")):
                    continue
                exp[vn][f"{iname}{' +restore' if restore else ''}"] = explore(version, interp, args.depth, restore)
    (res_dir / "exploration.json").write_text(json.dumps(exp, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    write_markdown(wres, exp, res_dir, args.depth)
    print(f"done in {time.time() - t0:.1f}s")
    return 0


def write_markdown(wres, exp, res_dir, depth):
    vnames = list(VERSIONS)
    lines = ["# Witnesses × text versions (default readings)", "",
             "Generated by `run.py`. PASS: the texts of that version give the witness's expected outcome; "
             "FAIL: they give another; CONFLICT: no outcome satisfies every passage; AMBIGUOUS: several "
             "observably different outcomes satisfy them; OUT_OF_STORE: only a number Registry cannot know "
             "satisfies them.", "",
             "| witness | status | " + " | ".join(f"{v} `{VERSIONS[v]['sha']}`" for v in vnames) + " |",
             "|---|---|" + "---|" * len(vnames)]
    for wid, w in wres.items():
        cells = [w["versions"][v]["default"]["result"] for v in vnames]
        lines.append(f"| {wid} {w['title']} | {w['status']} | " + " | ".join(cells) + " |")
    lines += ["", "## Where a reading changes the result", "",
              "| witness | version | reading | default → this reading |", "|---|---|---|---|"]
    for wid, w in wres.items():
        for v in vnames:
            d = w["versions"][v]["default"]["result"]
            for iname, r in w["versions"][v].items():
                if iname != "default" and r["result"] != d:
                    lines.append(f"| {wid} | {v} | `{iname}` | {d} → {r['result']} |")
    lines += ["", "## Conflicts and ambiguities met by the witnesses (default readings)", ""]
    for wid, w in wres.items():
        for v in vnames:
            r = w["versions"][v]["default"]
            if r["result"] in ("CONFLICT", "OUT_OF_STORE"):
                st = r["step"]
                sets = "; ".join("{" + ", ".join(c) + "}" for c in st.get("conflict_sets", []))
                lines.append(f"- {wid} on {v}: {r['result']} at `{st['event']}`"
                             + (f" — minimal conflicting sets: {sets}" if sets else "")
                             + (f" — resolution: {st['resolution']}" if st.get("resolution") else ""))
            if r["result"] == "AMBIGUOUS":
                lines.append(f"- {wid} on {v}: AMBIGUOUS at `{r['ambiguities'][0]['event']}` — "
                             + " / ".join(r["ambiguities"][0]["outcomes"]))
    (res_dir / "witnesses.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    lines = [f"# Bounded exploration (depth {depth})", "",
             "Every sequence of events of the alphabet up to the depth, from an empty store, branching on "
             "every outcome the texts allow; states are deduplicated. Past a conflict, exploration goes on "
             "with the outcomes that break the fewest passages. Past an out-of-store step it goes on with the "
             "outcomes the texts allow. A finding is reported once per signature (kind, event, conflicting "
             "passages), with its shortest trace.", ""]
    for v in vnames:
        lines.append(f"## {v} `{VERSIONS[v]['sha']}` — {VERSIONS[v]['label']}")
        lines.append("")
        for key, e in exp[v].items():
            fs = e["findings"]
            head = f"- `{key}`: {e['states']} states, {e['transitions']} transitions, {len(fs)} finding(s)"
            lines.append(head)
            for f in fs:
                extra = ""
                if f["verdict"] == "conflict":
                    extra = (" — " + "; ".join("{" + ", ".join(c) + "}" for c in f["conflict_sets"])
                             + f" — resolution: {f['resolution']}")
                elif f["verdict"] == "ambiguity":
                    extra = " — " + " / ".join(f["outcomes"])
                lines.append(f"  - **{f['verdict']}** after {' → '.join(f['trace'])}{extra}")
        lines.append("")
    (res_dir / "exploration.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
