"""Accept what the writing agent hands in for one module (decisions Q12, Q15).

The agent writes no file. It hands in either the module's notes or its
structure requests, and this module decides:

- requests: each must be one (§5.2, with a proven `absence`); they are
  written to `notes_authoring/<module>/requests.json` and the notes stay as
  they are — a module is not written while its request is open;
- notes: each must be one line `<scope>: [CLASS] prose` with a scope of this
  module; each must pass the State 7 gate's checks of one note (from
  standard_version 3 the Factory's resolver, L1) and lint L2–L5 against the
  case's other notes, and every contract callable must keep a semantic note
  with a positive modal (the gate's coverage rule); then they replace the
  module's notes in `80_notes.md`, and the module's answered requests are
  removed. Text that fails never reaches the case branch.
"""

from __future__ import annotations

import unicodedata
from pathlib import Path
from typing import Any

from notes_authoring import binding, request
from notes_authoring.index import SpecIndex
from notes_authoring.lint import lint
from notes_authoring.prompt import RESULT_SCHEMA

NOTES_FILE = "80_notes.md"
AUTHOR_PATH = "<author>"
REPORT_SCHEMA = "spec_workbench_notes_author_acceptance.v1"


def _refused(module: str, reason: str, findings: list[dict[str, Any]] | None = None, **extra: Any) -> dict[str, Any]:
    return {"schema_version": REPORT_SCHEMA, "module": module, "status": "refused",
            "reason": reason, "findings": findings or [], **extra}


def _parse(notes: list[Any], module: str, spec: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    from notes_workbench.gate import NOTE_RE
    from notes_workbench.note_standard import NOTE_CLASSES

    owners = binding.owners(spec)
    parsed, errors = [], []
    for number, raw in enumerate(notes, start=1):
        # one note is one line: a line break or control character inside it
        # would come back from 80_notes.md as a second note no check has seen
        if not isinstance(raw, str) or len(raw.strip().splitlines()) != 1 or any(
            unicodedata.category(c) in ("Cc", "Zl", "Zp") for c in raw.strip()
        ):
            errors.append(f"note {number}: not one line of text")
            continue
        match = NOTE_RE.fullmatch(raw.strip())
        if not match:
            errors.append(f"note {number}: not '<scope>: [NOTE_CLASS] prose'")
            continue
        scope, note_class = match.group("scope"), match.group("class")
        if note_class not in NOTE_CLASSES:
            errors.append(f"note {number}: unknown class [{note_class}]")
        owner = owners.get(scope) or owners.get(scope.split(".", 1)[0])
        if owner != module:
            errors.append(f"note {number}: scope {scope!r} belongs to {owner or 'no module'}, not {module}")
        parsed.append({"path": AUTHOR_PATH, "line": number, "scope": scope, "class": note_class,
                       "text": match.group("text").strip()})
    return parsed, errors


def _gate(project: Path, notes: list[dict[str, Any]], factory_root: Path | None) -> list[dict[str, Any]]:
    """What the State 7 gate says of each note on its own: its per-note checks
    and, from standard_version 3, the Factory's resolver (L1)."""
    from notes_workbench import factory_addresses, gate

    context = gate.note_context(project)
    found = [f for note in notes for f in gate.note_findings(note, context)]
    if context["factory_judged"]:
        found += factory_addresses.findings(project, notes, factory_root)
    for item in found:
        item.setdefault("rule", "gate")
        item["path"] = AUTHOR_PATH
    return found


def _uncovered(module: str, notes: list[dict[str, Any]], spec: dict[str, Any]) -> list[dict[str, Any]]:
    """The gate's coverage rule (language.factory_coverage) on the module's new
    notes: every contract callable has a semantic note with a positive modal."""
    from notes_workbench import language

    return language.factory_coverage({
        "module_functions": {module: list((spec.get("module_functions") or {}).get(module) or [])},
        "contracts": spec.get("contracts") or {},
        "notes": [f"{n['scope']}: [{n['class']}] {n['text']}" for n in notes],
    })


def _continuation(raw: str) -> bool:
    stripped = raw.strip()
    return bool(stripped) and raw.startswith((" ", "\t")) and not stripped.startswith(("-", "#"))


def _rewrite(project: Path, module: str, notes: list[dict[str, Any]], existing: list[dict[str, Any]]) -> None:
    """Replace the module's notes in 80_notes.md by ``notes`` under its
    `## <module>` heading, creating the heading at the end when it is absent.
    A list-shaped note goes with its continuation lines; every other line,
    the file's line endings and its final newline stay as they were."""
    path = project / NOTES_FILE
    text = ""
    if path.is_file():
        with path.open(encoding="utf-8", newline="") as handle:
            text = handle.read()
    # the same line numbering as language.authored_notes (str.splitlines)
    lines = text.splitlines(keepends=True)
    newline = "\r\n" if "\r\n" in text else "\n"
    drop: set[int] = set()
    for note in existing:
        if note["path"] != NOTES_FILE:
            continue
        index = note["line"] - 1
        drop.add(index)
        if lines[index].lstrip().startswith("-"):
            index += 1
            while index < len(lines) and _continuation(lines[index].rstrip("\r\n")):
                drop.add(index)
                index += 1
    kept = [line for index, line in enumerate(lines) if index not in drop]
    rendered = [f"{n['scope']}: [{n['class']}] {n['text']}{newline}" for n in notes]
    bare = [line.rstrip("\r\n") for line in kept]
    heading = f"## {module}"
    if heading in bare:
        at = bare.index(heading) + 1
        if at == len(kept) or kept[at - 1] == kept[at - 1].rstrip("\r\n"):
            kept[at - 1] = bare[at - 1] + newline  # the heading was the last line
        end = at
        while end < len(kept) and not bare[end].strip():
            end += 1
        # heading, one blank line, the notes, one blank line before what follows
        kept[at:end] = [newline, *rendered] + ([newline] if end < len(kept) else [])
    else:
        if kept and not kept[-1].endswith(("\n", "\r")):
            kept[-1] += newline
        if kept and kept[-1].strip():
            kept.append(newline)
        kept += [heading + newline, newline, *rendered]
    out = "".join(kept)
    if text and not text.endswith(("\n", "\r")):
        out = out.rstrip("\r\n")  # the file had no final newline; it keeps none
    path.write_text(out, encoding="utf-8", newline="")


def accept(project: Path, module: str, result: Any, *, spec: dict[str, Any] | None = None,
           factory_root: Path | None = None, write: bool = True) -> dict[str, Any]:
    from notes_workbench import language

    if not isinstance(result, dict) or result.get("schema_version") != RESULT_SCHEMA:
        return _refused(module, f"the result is not a {RESULT_SCHEMA} object")
    if result.get("module") != module:
        return _refused(module, f"the result is for {result.get('module')!r}, not {module!r}")
    if spec is None:
        from spec_projection_workbench import projected_spec

        spec = projected_spec(project)
    index = SpecIndex.build(spec)
    authored = language.authored_notes(project)
    by_module, _ = binding.bind(authored, spec)
    if module not in by_module:
        return _refused(module, f"{module!r} is not a module of the case")
    requests = result.get("structure_requests")
    notes = result.get("notes")
    if requests:
        if notes:
            return _refused(module, "notes and structure requests together: a module with a request is not written")
        errors = [f"request {i}: {e}" for i, r in enumerate(requests, start=1) for e in request.validate(r, module)]
        if errors:
            return _refused(module, "invalid structure request", errors=errors)
        stale = [i for i, r in enumerate(requests, start=1) if request.stale(r, index)]
        if stale:
            return _refused(module, f"requests {stale} carry absence digests of other namespaces than the current ones")
        if write:
            request.write(project, module, requests)
        return {"schema_version": REPORT_SCHEMA, "module": module, "status": "requested",
                "requests": len(requests), "written": write}
    if not isinstance(notes, list) or not notes:
        return _refused(module, "the result holds neither notes nor structure requests")
    open_requests = [r for r in request.load(project, module) if not request.stale(r, index)]
    if open_requests:
        return _refused(module, f"{len(open_requests)} structure request(s) of {module} are open: "
                                "the source that answers them has not changed")
    elsewhere = [n for n in by_module[module] if n["path"] != NOTES_FILE]
    if elsewhere:
        return _refused(module, f"the module has notes in {sorted({n['path'] for n in elsewhere})}; "
                                f"the environment writes only {NOTES_FILE}")
    parsed, errors = _parse(notes, module, spec)
    if errors:
        return _refused(module, "notes do not parse or bind to the module", errors=errors)
    others = [n for n in authored if n not in by_module[module]]
    findings = _gate(project, parsed, factory_root) + [
        f for f in lint(others + parsed, spec)["findings"] if f["path"] == AUTHOR_PATH
    ]
    blocks = [f for f in findings if f["severity"] == "block"]
    if blocks:
        return _refused(module, f"{len(blocks)} blocking finding(s) of the gate or the lint", findings)
    uncovered = _uncovered(module, parsed, spec)
    if uncovered:
        return _refused(module, "callables without a note", uncovered,
                        callables_without_note=[f["scope"] for f in uncovered])
    if write:
        _rewrite(project, module, parsed, by_module[module])
        request.clear(project, module)
    return {"schema_version": REPORT_SCHEMA, "module": module, "status": "written",
            "notes": len(parsed), "replaced": len(by_module[module]), "written": write,
            "reports": findings}
