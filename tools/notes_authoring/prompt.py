"""The writing agent's task for one module (tools/DATA_CLOSURE_WORKBENCH.md §3).

The task is navigation, not content. It names the module, where the rules
are and which tool answers which question, and the form of the answer. The
rules of writing are SPEC_STANDARD's own text, read with `spec_standard`; the
module, its notes, its design and its data come from the other tools while
the agent writes (decision Q4). Nothing here restates a rule, so nothing here
can drift from the standard.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from notes_authoring import request

RESULT_SCHEMA = "spec_workbench_notes_author_result.v1"


def build(project: Path, module: str, spec: dict[str, Any]) -> str:
    """The task text for ``module``; ``spec`` is the in-memory projection."""
    case = project.name
    version = spec.get("standard_version")
    return f"""You write the State 7 notes of module `{module}` of the Spec Workbench case `{case}`
(standard_version {version}). Notes are the generator's requirements for this module's code:
the generator receives the specification and nothing else.

# Where the rules are

The rules are SPEC_STANDARD, and only SPEC_STANDARD. This task states none. Read the
standard with `spec_standard`: call it without a section for the index and the table
of contents, then read the sections the index sends you to for notes. These are at
least §2 (notes) and §15 (data: what is data, where it lives, how a note names it).
Read any other section you need. When a sentence you are about to write is not
clearly allowed by a section you have read, read further before you write it.

# Route

1. `module_slice(project, module)`: the module's callables and signatures, the
   models those signatures name, what the design says the module does, and its
   open structure requests.
2. `module_notes(project, module)`: the module's current notes. You rewrite them; you
   do not add notes beside them. Keep every requirement they state unless the standard
   forbids how it is stated.
3. `design_provenance(project, name)`, `design_context(project, location)`: the accepted
   decisions behind a name, and the design text around a location. The generator does
   not receive these texts, so a note never points to them.
4. For data: `find_value_homes(project, value)` gives where a literal is declared,
   `resolve_data_address(project, address)` gives the Factory's verdict on one
   address, and `find_absence(project, terms)` gives where terms occur, with the
   namespace digests.
5. `check_note_draft(project, note)`: run it on every note before you hand the note in.
   It runs the State 7 gate's checks of one note and a mechanical lint. It is required
   but it is not the measure. A note it passes must still meet the standard. Never
   reword a sentence only so that the check stops seeing it.

If a requirement of this module needs a value the specification does not hold, you
write no notes for the module. You answer with structure requests instead (form
below), with the `absence` that `find_absence` gave you.

# Answer

One JSON object and nothing else. Either the notes, each one line
`<scope>: [NOTE_CLASS] prose`:

{{"schema_version": "{RESULT_SCHEMA}", "module": "{module}", "notes": ["<scope>: [CLASS] prose", "..."]}}

or, if a value has no home, the structure requests and no notes:

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
"""
