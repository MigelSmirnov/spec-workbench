"""One judgement per check, kept by digest (owner review of #156, 2026-11-08).

A binding (``[witness: verification:<check>]`` in a Required tests item) claims
that a Factory check asserts the invariants its item names. Whether it does is
judged once per check, outside the document round:

- **Input**: the check's files with the Factory modules they import
  (``design_decision_witness.binding_material``), and every Required tests item
  bound to that check, across all decisions.
- **Question**: for each bound item, does the check assert the invariants the
  item names? ``asserts``, ``partial`` or ``does_not``, with the asserting lines
  quoted. A quote is checked mechanically against the files; an answer whose
  quotes are not found is ``unverified``.
- **Kept** under ``questions/checks/`` of the case, keyed by the sha256 of the
  check's declaration (argv, effective cwd and the rest: a subset run asserts
  less), of its files and of the bound items with the invariants they name,
  as stated. An item left unverified is asked again on the next judgement,
  the verified ones reused and the earlier attempt kept. It is judged again only when one of them
  changes; a judgement on other evidence is never the current one.
- **Not judged**: material that cannot be given whole (unreadable, or over
  ``INPUT_LIMIT``) is ``not_checked``, with the reason, never truncated.

The State 2 round receives the verdicts only (``verdicts``): one line per
binding with its digest and outcome. ``transition.check_witness_material``
stops on a binding without a current ``asserts``.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

SCHEMA = "spec_workbench_check_judgement.v1"
CHECKS_DIR = Path("questions") / "checks"
OUTCOMES = ("asserts", "partial", "does_not")
INPUT_LIMIT = 900_000  # characters one judgement request may carry, the provider's limit with room


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _norm(text: str) -> str:
    return " ".join(str(text).split())


def group(materials: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """witness -> the check: its files, every item bound to it, and whether it can be read whole."""
    checks: dict[str, dict[str, Any]] = {}
    for entry in materials:
        check = checks.setdefault(entry["witness"], {"witness": entry["witness"], "status": "available",
                                                     "reason": None, "files": [], "items": [],
                                                     "declaration": entry.get("declaration")})
        if entry["status"] != "available" and check["status"] == "available":
            check.update(status=entry["status"], reason=entry.get("reason"), unreadable=bool(entry.get("unreadable")))
        if not check["files"] and entry.get("files"):
            check["files"] = entry["files"]
        item = {"decision": entry["decision"], "item": entry["item"], "invariants": list(entry.get("invariants") or []),
                # the invariants as stated: a strengthened INV-001 under the same item is another question
                "statements": list(entry.get("statements") or [])}
        if item not in check["items"]:
            check["items"].append(item)
    for check in checks.values():
        check["items"].sort(key=lambda i: (i["decision"], i["item"]))
        check["digest"] = _sha(json.dumps({
            "declaration": check["declaration"],  # argv and cwd: a subset run asserts less
            "files": sorted((f["path"], f["sha256"]) for f in check["files"]),
            "items": [(i["decision"], i["item"], i["statements"]) for i in check["items"]],
        }, ensure_ascii=False))
    return checks


def _slug(witness: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", witness)


def record_path(case: Path, check: dict[str, Any]) -> Path:
    return Path(case) / CHECKS_DIR / _slug(check["witness"]) / f"{check['digest']}.json"


def current(case: Path, check: dict[str, Any]) -> dict[str, Any] | None:
    """The judgement kept for this check on exactly these files and items, or None."""
    path = record_path(case, check)
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return record if record.get("digest") == check["digest"] else None


INSTRUCTION = """You judge whether one Factory check asserts what the design claims it does.

Each Required tests item below binds this check to the invariants it names. For
each item, read the check's code (the files below, with the modules it imports)
and answer:

- "asserts": the code asserts every invariant the item names, as stated — a
  violating input is refused or detected, not merely the same function called;
- "partial": it asserts some of them, or a weaker form;
- "does_not": it asserts none of them.

Quote, verbatim from the files, the lines that assert ("asserts", "partial");
quotes are checked mechanically against the files, so copy them character for
character. Say in "why" what is asserted and what is not.

Answer with JSON only:
{"verdicts":[{"id":"I1","outcome":"asserts|partial|does_not","quotes":["<line from a file>"],"why":"<one or two sentences>"}]}"""


def judge_input(check: dict[str, Any]) -> str:
    items = "\n".join(f"I{n}: {i['decision']} binds {', '.join(i['invariants']) or 'its invariant'}: {i['item']}"
                      + "".join(f"\n    invariant: {s}" for s in i.get("statements") or [])
                      for n, i in enumerate(check["items"], 1))
    run = ""
    if check.get("declaration"):
        run = ("=== HOW THE CHECK IS RUN (its declaration in the Factory verification config) ===\n\n"
               + json.dumps(check["declaration"], ensure_ascii=False, indent=1) + "\n\n"
               "Judge what this run executes: arguments that select a subset leave the rest unasserted.\n\n")
    files = "\n\n".join(f"--- {f['path']} sha256 {f['sha256']}" + (" (imported by the check)" if f.get("imported") else "")
                        + f" ---\n{f['text']}" for f in check["files"])
    return (f"=== REQUIRED TESTS ITEMS BOUND TO {check['witness']} ===\n\n{items}\n\n{run}"
            f"=== THE CHECK ===\n\n{files}")


def _parse(answer: str) -> dict[str, Any]:
    start, end = answer.find("{"), answer.rfind("}")
    try:
        found = json.loads(answer[start:end + 1]) if start >= 0 else {}
    except ValueError:
        return {}
    return found if isinstance(found, dict) else {}


def _settled(record: dict[str, Any] | None) -> dict[tuple[str, str], dict[str, Any]]:
    """The verified verdicts of a kept judgement: they are reused, never asked again."""
    return {(v["decision"], v["item"]): v for v in (record or {}).get("verdicts") or []
            if v.get("outcome") in OUTCOMES}


def judge_check(case: Path, provider: Any, check: dict[str, Any],
                previous: dict[str, Any] | None = None) -> dict[str, Any]:
    """Judge one check now and keep the record; a check not readable whole is not judged.

    With ``previous`` (a kept judgement on the same digest with unverified
    items), only those items are asked again; its verified verdicts are reused
    and the earlier attempt is kept beside the new record.
    """
    base = {"schema_version": SCHEMA, "witness": check["witness"], "digest": check["digest"],
            "declaration": check.get("declaration"),
            "files": [{"path": f["path"], "sha256": f["sha256"]} for f in check["files"]],
            "items": check["items"]}
    if check["status"] != "available":
        return {**base, "status": "not_checked", "reason": check["reason"]}
    settled = _settled(previous)
    asked = [i for i in check["items"] if (i["decision"], i["item"]) not in settled]
    text = judge_input({**check, "items": asked})
    if len(text) + len(INSTRUCTION) > INPUT_LIMIT:
        return {**base, "status": "not_checked",
                "reason": f"{len(text)} characters exceed what one judgement is given whole ({INPUT_LIMIT})"}
    answer = provider.complete(INSTRUCTION, text)[0]
    given = {v.get("id"): v for v in _parse(answer).get("verdicts") or [] if isinstance(v, dict)}
    corpus = [_norm(f["text"]) for f in check["files"]]
    answers = {(i["decision"], i["item"]): given.get(f"I{n}") or {} for n, i in enumerate(asked, 1)}
    verdicts = []
    for item in check["items"]:
        key = (item["decision"], item["item"])
        if key in settled:
            verdicts.append(settled[key])
            continue
        found = answers[key]
        outcome = found.get("outcome")
        quotes = [q for q in found.get("quotes") or [] if isinstance(q, str) and q.strip()]
        missing = [q for q in quotes if not any(_norm(q) in body for body in corpus)]
        if outcome not in OUTCOMES:
            outcome, why = "unverified", f"no verdict among {OUTCOMES} for this item"
        elif outcome != "does_not" and (not quotes or missing):
            outcome, why = "unverified", ("the asserting lines are not quoted" if not quotes
                                          else f"quoted lines not found in the check: {missing[:2]}")
        else:
            why = str(found.get("why") or "")
        verdicts.append({**item, "outcome": outcome, "quotes": quotes, "why": why})
    record = {**base, "status": "judged", "provider": getattr(provider, "name", "?"), "verdicts": verdicts,
              "asked": [{"decision": i["decision"], "item": i["item"]} for i in asked], "raw": answer}
    path = record_path(case, check)
    path.parent.mkdir(parents=True, exist_ok=True)
    if previous is not None and path.is_file():  # keep the earlier attempt
        attempt = len(list(path.parent.glob(f"{check['digest']}.attempt-*.json"))) + 1
        path.rename(path.with_name(f"{check['digest']}.attempt-{attempt}.json"))
    path.write_text(json.dumps(record, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return record


def judge(case: Path, provider: Any, materials: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Judge every check that has no judgement on its current declaration, files and
    items, and ask again the items a kept judgement left unverified."""
    done = []
    for check in group(materials).values():
        kept = current(case, check)
        if kept is None:
            done.append(judge_check(case, provider, check))
        elif any(v.get("outcome") not in OUTCOMES for v in kept.get("verdicts") or []):
            done.append(judge_check(case, provider, check, previous=kept))
    return done


def verdicts(case: Path, materials: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """One row per binding: its check's digest and the current outcome, or not_checked and why."""
    checks = group(materials)
    rows = []
    for entry in materials:
        check = checks[entry["witness"]]
        row = {"decision": entry["decision"], "witness": entry["witness"], "item": entry["item"],
               "invariants": list(entry.get("invariants") or []), "digest": check["digest"]}
        if check["status"] != "available":
            rows.append({**row, "outcome": "not_checked", "reason": check["reason"]})
            continue
        record = current(case, check)
        found = next((v for v in (record or {}).get("verdicts") or []
                      if v["decision"] == entry["decision"] and v["item"] == entry["item"]), None)
        if found is None:
            rows.append({**row, "outcome": "not_checked",
                         "reason": "no judgement of this check on its current files and items "
                                   "(design_questions.py judge-checks)"})
        elif found["outcome"] == "unverified":
            rows.append({**row, "outcome": "not_checked", "reason": f"the judgement is unverified: {found['why']}"})
        else:
            rows.append({**row, "outcome": found["outcome"], "quotes": found["quotes"], "why": found["why"]})
    return rows
