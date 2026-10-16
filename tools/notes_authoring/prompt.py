"""The writing agent's task for one module (tools/DATA_CLOSURE_WORKBENCH.md §3).

The input is the contract's §3: the module's design slice (responsibility,
capabilities, flows, public operations, obligations — what the notes must
say), its callables with their signatures, the models those signatures name
(fields and members are names a note may write as words), the module's
current notes (to rewrite, not to add beside) and the standard's sections in
their own words. Data is not in the prompt: the agent asks the Workbench MCP
for it while it writes (decision Q4), so it reaches a value only through its
home.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from notes_authoring import binding, request
from notes_authoring.index import SpecIndex

RESULT_SCHEMA = "spec_workbench_notes_author_result.v1"
STANDARD = Path(__file__).resolve().parents[2] / "skills" / "spec-authoring" / "SPEC_STANDARD.md"
# §3 of the contract: the rules of writing, in the standard's words.
SECTIONS = ("## 2.", "### 15.1 ", "### 15.2 ", "### 15.3 ", "### 15.4 ", "### 15.9 ", "### 15.11 ")
_TYPE_NAME_RE = re.compile(r"\b[A-Z][A-Za-z0-9_]*\b")


def standard_sections(path: Path = STANDARD) -> str:
    lines = path.read_text(encoding="utf-8").splitlines()
    out: list[str] = []
    for heading in SECTIONS:
        start = next((i for i, line in enumerate(lines) if line.startswith(heading)), None)
        if start is None:
            raise ValueError(f"SPEC_STANDARD.md has no section {heading.strip()!r}")
        level = heading.split(" ", 1)[0]
        end = next(
            (j for j in range(start + 1, len(lines))
             if lines[j].startswith("#") and len(lines[j].split(" ", 1)[0]) <= len(level)
             and lines[j].split(" ", 1)[0].strip("#") == ""),
            len(lines),
        )
        out.append("\n".join(lines[start:end]).rstrip())
    return "\n\n".join(out)


def _models_named(signatures: dict[str, str], index: SpecIndex) -> dict[str, Any]:
    named = sorted({n for s in signatures.values() for n in _TYPE_NAME_RE.findall(s)}
                   & (set(index.fields) | set(index.enums)))
    return {
        name: ({"enum_members": list(index.enums[name])} if name in index.enums
               else {"fields": sorted(index.fields[name])})
        for name in named
    }


def build(project: Path, module: str, spec: dict[str, Any], slice_payload: dict[str, Any],
          notes: list[dict[str, Any]]) -> str:
    """The task text. ``spec`` is the in-memory projection, ``slice_payload``
    the module's design slice, ``notes`` the case's authored notes."""
    index = SpecIndex.build(spec)
    callables = list((spec.get("module_functions") or {}).get(module) or [])
    contracts = spec.get("contracts") or {}
    signatures = {name: contracts[name] for name in callables if isinstance(contracts.get(name), str)}
    by_module, _ = binding.bind(notes, spec)
    current = [f"{n['scope']}: [{n['class']}] {n['text']}" for n in by_module.get(module, [])]
    design = {key: slice_payload.get(key) for key in
              ("responsibility", "capabilities", "flows", "public_operations", "obligations")}
    case = project.name
    version = spec.get("standard_version")
    return f"""You write the State 7 notes of module `{module}` of the Spec Workbench case `{case}`
(standard_version {version}). Notes are the generator's requirements for this module's
code. Write them so that no data is in prose: SPEC_STANDARD §15.

# Rules

1. One value, one home. A value the code needs — a threshold, a path, a rate, a code, a
   closed list, a mapping, an order — is written as its home: `= models.X` for an
   enumeration or model schema, `the imported X constant` for a data-provider constant,
   the field of the settings object for a runtime setting. Ask before you write it:
   `find_value_homes` for a value, `resolve_data_address` for an address.
2. No home: stop. Do not write the value, do not describe it, do not invent a home.
   Return a structure request instead (format below) with the `absence` that
   `find_absence` gave you. Every note the missing home holds back waits; this module is
   not written while a request is open.
3. What stays prose: a step of the algorithm over addressed data, a condition, a member
   of an enumeration chosen in one place next to its `= models.X`, an explanation, a
   field of a declared model named by its name, a sort order by declared fields.
4. Never restate the members of an enumeration next to its address, never list
   contract names as a registry, never copy another module's rule — name its function.
5. Never refer to design documents: no "State N", no `NN_*.md`, no handoff, no
   decision or rule numbers (`decision 20`, `A16 rules 4 and 6`). The generator never
   receives them.
6. No illustrative value ("for example 12.5"): it becomes a default in code.
7. Every callable below gets at least one note with a positive MUST, SHOULD or MAY.
   Notes are `<scope>: [NOTE_CLASS] prose`, scope a callable of this module or the
   module name, class from the registry of §2.
8. Before you hand a note in, run `check_note_draft` on it; hand in only notes it calls
   clean. The environment runs the same lint and refuses the module otherwise.

# Tools (Workbench MCP, project `{case}`)

- `find_value_homes(project, value)` — where a literal is declared; `homes_reaching_code`
  are the homes you may name.
- `resolve_data_address(project, address)` — the Factory's verdict on one address.
- `find_absence(project, terms)` — where terms occur, and the namespace digests.
- `module_notes(project, module)` — the current notes of a module.
- `design_provenance(project, name)`, `design_context(project, location)` — the
  accepted decisions behind a name, and the design text around a location.

# Callables of `{module}` and their signatures

{json.dumps(signatures, ensure_ascii=False, indent=2)}

# Models those signatures name (names you may write as words)

{json.dumps(_models_named(signatures, index), ensure_ascii=False, indent=2)}

# What the design says the module does

{json.dumps(design, ensure_ascii=False, indent=2)}

# Current notes of `{module}` (rewrite them; do not add beside them)

{chr(10).join(current) if current else "(none)"}

# Answer

One JSON object and nothing else, either the notes:

{{"schema_version": "{RESULT_SCHEMA}", "module": "{module}", "notes": ["<scope>: [CLASS] prose", "..."]}}

or, when a value has no home, the structure requests (no notes):

{{"schema_version": "{RESULT_SCHEMA}", "module": "{module}", "structure_requests": [{{
  "schema_version": "{request.SCHEMA}", "module": "{module}",
  "need": "<what the note must say, one sentence>",
  "value_kind": "{'|'.join(sorted(request.VALUE_KINDS))}",
  "candidate_values": ["<the value as you see it, and from which source>"],
  "sources": [{{"path": "<design file>", "line": 0, "quote": "<the words>"}}],
  "absence": {{"terms": ["..."], "namespaces": {{"models": "<sha256>", "rules": "<sha256>", "config": "<sha256>"}}}},
  "homes_considered": [{{"home": "<address>", "why_not": "..."}}],
  "route": "state6 (the home is clear, make it in State 6) | author (the value is not in the design texts) | owner (the home is ambiguous or a product decision)",
  "blocked_notes": ["<scope>: <class>"]
}}]}}

# SPEC_STANDARD, the sections you apply

{standard_sections()}
"""
