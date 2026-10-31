"""Run the revision model: readings, open situations, witnesses, patch options.

    python experiments/registry-state2-authoring/run.py

Writes results/readings.md, results/open_situations.md, results/witnesses.md
and results/results.json. Deterministic.

A *text* is a set of fixed readings: the current text fixes none, a patch
option fixes those its wording settles. Under a text, a reading set is
*consistent* when every situation gets exactly one outcome; a situation is
*open* when consistent reading sets give it different outcomes.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "model"))
from revisions import READINGS, Situation, decide, reading_sets, situations  # noqa: E402

TEXTS = {
    "current": {},
    # Option A — what the patch proposes: a revision stated for a record that
    # has none is stale, at stage 5. Fixes A04 r2's reach and A04 r3's second
    # sentence; leaves the invariant's scope as it is (both readings agree).
    "option_A_stale": {"a04_r2": "all_records", "a04_r3_none": "caller_duty"},
    # Option B — the alternative for the owner: on a record without a
    # revision, no revision is checked; the invariant applies to records
    # that have one.
    "option_B_ignore": {"a04_r2": "records_with_revision", "a04_r3_none": "caller_duty",
                        "a04_inv": "this_action"},
}


def analyse(fixed: dict, sits: list[Situation]) -> dict:
    consistent, rejected = [], []
    for r in reading_sets(fixed):
        bad = [(s.label(), decide(s, r)[1]) for s in sits if decide(s, r)[0] is None]
        (rejected if bad else consistent).append({"readings": r, "first_conflict": bad[0] if bad else None,
                                                   "conflicts": len(bad)})
    per = {}
    for s in sits:
        outs = defaultdict(list)
        for c in consistent:
            outs[decide(s, c["readings"])[0]].append(c["readings"])
        per[s.label()] = {o: len(v) for o, v in outs.items()}
    return {"consistent": consistent, "rejected": rejected, "outcomes": per}


def main() -> int:
    sits = situations()
    out = {name: analyse(fixed, sits) for name, fixed in TEXTS.items()}
    wit = json.loads((HERE / "witnesses" / "witnesses.json").read_text(encoding="utf-8"))["witnesses"]
    wres = {}
    for w in wit:
        s = Situation(**{"conf": "fresh", **w["situation"]})
        row = {}
        for name in TEXTS:
            outs = sorted(out[name]["outcomes"][s.label()])
            if len(outs) == 1:
                o = outs[0]
                verdict = ("PASS" if w["expected"] == o else "FAIL") if w["expected"] else f"DECIDED: {o}"
            else:
                verdict = "OPEN: " + " | ".join(outs)
            row[name] = verdict
        wres[w["id"]] = {"title": w["title"], "status": w["status"], "preserve": w["preserve"], **row}
    res = HERE / "results"
    res.mkdir(exist_ok=True)
    (res / "results.json").write_text(json.dumps({"texts": out, "witnesses": wres}, ensure_ascii=False,
                                                 indent=1) + "\n", encoding="utf-8")

    # readings.md
    L = ["# Readings the texts admit", "",
         f"{len(sits)} situations; each reading set fixes one value of each of {len(READINGS)} readings "
         f"({2 ** len(READINGS)} sets). A set is rejected when some admissible situation gets no outcome "
         "under it; the passages that exclude the last candidates are named.", ""]
    for name in TEXTS:
        a = out[name]
        L.append(f"## {name}: {len(a['consistent'])} consistent, {len(a['rejected'])} rejected")
        L.append("")
        by = defaultdict(list)
        for rj in a["rejected"]:
            key = (rj["first_conflict"][0], tuple(rj["first_conflict"][1]))
            by[key].append(rj["readings"])
        for (lab, blame), rs in sorted(by.items()):
            common = {k: v for k, v in rs[0].items() if all(x[k] == v for x in rs)}
            L.append(f"- rejected ({len(rs)}): readings {common} — first conflict at `{lab}`, "
                     f"excluded by {', '.join(blame)}")
        L.append("")
    (res / "readings.md").write_text("\n".join(L) + "\n", encoding="utf-8")

    # open_situations.md
    L = ["# Situations the text leaves open", "",
         "Outcome → number of consistent reading sets that give it.", ""]
    for name in TEXTS:
        opens = {k: v for k, v in out[name]["outcomes"].items() if len(v) > 1}
        L.append(f"## {name}: {len(opens)} open of {len(sits)}")
        L.append("")
        for k, v in opens.items():
            L.append(f"- `{k}`: " + "; ".join(f"{o} ({n})" for o, n in sorted(v.items())))
        L.append("")
    (res / "open_situations.md").write_text("\n".join(L) + "\n", encoding="utf-8")

    # witnesses.md
    L = ["# Witnesses under the current text and the two patch options", "",
         "PASS/FAIL against an expected outcome (accepted witnesses); DECIDED: the outcome an option gives "
         "to an open witness; OPEN: outcomes still admitted.", "",
         "| witness | status | preserve | current | option A (stale) | option B (ignore) |",
         "|---|---|---|---|---|---|"]
    for wid, r in wres.items():
        L.append(f"| {wid} {r['title']} | {r['status']} | {'yes' if r['preserve'] else 'no'} | {r['current']} | "
                 f"{r['option_A_stale']} | {r['option_B_ignore']} |")
    broken = [f"{wid} under {t}" for wid, r in wres.items() if r["preserve"]
              for t in TEXTS if r[t] != "PASS"]
    L += ["", "Preserved witnesses not passing: " + (", ".join(broken) if broken else "none")]
    (res / "witnesses.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    sys.exit(main())
