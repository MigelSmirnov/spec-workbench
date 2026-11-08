"""The exploring review of State 2 (issue #159, owner's priority: the agentic "почемучка").

A review of State 2 is not one request over a mechanically chosen package. The
reviewer gets the task and questions of its layer, the open units with their
diff, the current bases and the deterministic results — and a read-only
workspace it explores with tools: the snapshot of States 0..2 and of the
phase's methodology documents, navigated by ``nav.py`` (design_navigate:
table of contents, R0-* and other identifiers, reading by key, explicit
references, lexical search), and the check verdicts of #158. The initial
selection is navigation, never the boundary of what it may read.

What comes back is checked by tools, not trusted:

- every point names its basis — a section key or identifier and a verbatim
  quote — and the quote must be found in that section of this snapshot;
- a review that did not finish (it says so, or names questions it could not
  settle, or its answer is unreadable) is ``not_checked``: the round is not
  clean, whatever the other reviews say;
- the trace of what it ran and read is kept with the review, with the
  snapshot id, so the round can be reproduced and audited.

The reviews stay independent, and the topics they find are judged apart, as in
every round. Fixing a requirement is a separate action on its owning layer:
the exploration is read-only.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from . import documents

EXPLORING_STATES = frozenset({2})
WORKSPACE_DOCS = "docs"
METHODOLOGY = "methodology"
NAVIGATOR = Path(__file__).resolve().parents[1] / "design_navigate.py"
ROOT = Path(__file__).resolve().parents[2]


def phase_documents(state: int) -> list[tuple[str, str]]:
    """(path, why) of the methodology documents the state's phases name (authoring_sequence ``docs``)."""
    sequence = json.loads(documents.SEQUENCE.read_text(encoding="utf-8"))
    found: list[tuple[str, str]] = []
    for phase in sequence["phases"]:
        if phase.get("semantic_state") == state:
            for doc in phase.get("docs") or []:
                entry = (doc["path"], doc.get("why", "") + (f" (section: {doc['section']})" if doc.get("section") else ""))
                if entry not in found:
                    found.append(entry)
    return found


def build_workspace(root: Path, texts: list[tuple[int, str, str]], state: int,
                    layer: dict[str, Any] | None) -> dict[str, Any]:
    """Write the reviewer's read-only workspace under ``root``; return what it holds."""
    import design_navigate

    docs = [(f"{WORKSPACE_DOCS}/{name}", doc_state, body) for doc_state, name, body in texts if doc_state <= state]
    methodology = []
    for path, why in phase_documents(state):
        source = ROOT / path
        if source.is_file():
            methodology.append((f"{METHODOLOGY}/{source.name}", None, source.read_text(encoding="utf-8"), why))
    snapshot = design_navigate.write_snapshot(root, docs + [(n, s, t) for n, s, t, _ in methodology])
    shutil.copyfile(NAVIGATOR, root / "nav.py")
    (root / "verdicts.json").write_text(json.dumps((layer or {}).get("verdicts") or [], ensure_ascii=False, indent=1),
                                        encoding="utf-8")
    results = {"results": (layer or {}).get("results") or [], "gate_findings": (layer or {}).get("gate_findings") or []}
    (root / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return {"snapshot": snapshot, "documents": [name for name, _, _ in docs],
            "methodology": [(name, why) for name, _, _, why in methodology]}


EXPLORE = """

How to review. You are not limited to the text above: it is where to start.
Your working directory is a read-only snapshot (id {snapshot}) of the texts of
States 0..{state} under docs/ and the methodology of this layer under
methodology/:
{methodology}
Explore it with `python3 nav.py <command>` (JSON answers, each with the
snapshot id):
- `toc [DOCUMENT]` — documents, sections and nested sections, the text before
  the first heading;
- `ids [PREFIX]` — written identifiers (R0-*, decisions A*, models M*, INV-*)
  and the section defining each;
- `read KEY` — a section or an identifier's section, verbatim, with its lines;
- `refs KEY` — what the section names and which sections name what it defines;
- `search TEXT` — lexical occurrences (search results, not dependencies);
- `verdicts [DECISION]` — whether each bound check asserts its invariants.
You may also read the files directly. A missing reference proves nothing:
when the meaning of a requirement matters, read it.

Work from the general to the particular: first, are the requirements this
layer owns complete and is each decision free of contradiction — behaviour,
refusals, priorities, where time comes from, invariants that nothing could
check; then narrow each doubt to one history or defect with a basis you can
show. This layer decides requirements and accepted decisions: do not ask for
contracts or implementation that later states write.

Answer with JSON only:
{{"open_points":[{{ ...the fields asked above..., "basis":[{{"key":"<section key or identifier you read>","quote":"<verbatim text of that section>"}}]}}],
 "complete":true|false, "unresolved":["<what you could not settle, and why>"],
 "read":["<keys you read>"]}}
Every point needs a basis quoted verbatim from a section you read; quotes are
checked against this snapshot. Say "complete": false, and list what is
unresolved, when you could not finish — an unfinished review is never clean."""


def instruction_note(workspace: dict[str, Any], state: int) -> str:
    methodology = "\n".join(f"  - {name}: {why}" for name, why in workspace["methodology"]) or "  - (none)"
    return EXPLORE.format(snapshot=workspace["snapshot"], state=state, methodology=methodology)


def _parse(answer: str) -> dict[str, Any] | None:
    start, end = answer.find("{"), answer.rfind("}")
    try:
        found = json.loads(answer[start:end + 1]) if start >= 0 else None
    except ValueError:
        return None
    return found if isinstance(found, dict) else None


def review(provider: Any, instruction: str, text: str, root: Path, snapshot: str) -> dict[str, Any]:
    """One exploring review: the provider explores the workspace; tools check what it brings back."""
    import design_navigate

    answer, usage, trace = provider.explore(instruction, text, root)
    found = _parse(answer)
    result: dict[str, Any] = {"snapshot": snapshot, "trace": trace, "usage": usage, "raw": answer}
    if found is None:
        return {**result, "open_points": [], "not_checked": "the review's answer is not readable JSON"}
    nav = design_navigate.Snapshot(root)
    points = []
    for point in found.get("open_points") or []:
        if not isinstance(point, dict):
            continue
        basis = [b for b in point.get("basis") or [] if isinstance(b, dict)]
        checked = [{**b, "verified": nav.verify_quote(str(b.get("key", "")), str(b.get("quote", "")), snapshot)}
                   for b in basis]
        points.append({**point, "basis": checked,
                       "basis_verified": bool(checked) and all(b["verified"] for b in checked)})
    result.update(open_points=points, read=list(found.get("read") or []),
                  unresolved=[str(u) for u in found.get("unresolved") or []])
    if found.get("complete") is not True or result["unresolved"]:
        result["not_checked"] = ("the review did not finish its exploration: "
                                 + ("; ".join(result["unresolved"]) or "it did not say it was complete"))
    return result
