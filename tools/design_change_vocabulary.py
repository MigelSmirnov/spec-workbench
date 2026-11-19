#!/usr/bin/env python3
"""What a change of a state's rules added that the earlier states do not name.

    python tools/design_change_vocabulary.py examples/<case> --state 2 --since <ref>

State 2 decides required results in the words States 0 and 1 already hold:
their actors, models, statuses, refusals and promises. A fix that answers a
question of a round should close a fork in those words. One that brings in a
function, a call, a file mode or a procedure has decided how, which is the
work of a later state (skills/spec-authoring/QUESTIONS.md, "A State 2 gap
breaks a requirement").

For each section of the state's documents changed since `--since`, this
reports what its added lines introduce:

- identifiers: names in code marks that occur neither in the earlier states'
  texts nor in the state's own text at `--since` (test names apart: a
  Required tests item may name its test);
- mechanism words: words of an implementation (MECHANISM) that the earlier
  states' texts do not use. A product whose State 0 speaks of folders or locks
  may speak of them here; the word is reported only when it is new.

It is a report for the author and for the round on the change, not a gate: a
decided value has its own path to code (SPEC_STANDARD 15.3.1) and is named
here by right. Measured on the 30 fix commits of Portal Deliverer State 2
(docs/STATE2_REQUIRED_RESULTS_20261120.md). Exit 0; with --strict, 1 when
anything is reported.
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from questions_workbench import documents  # noqa: E402

IDENTIFIER = re.compile(r"`([A-Za-z_][\w.]*(?:_|\.)[\w.]*)`")
# Words that say how a result is reached. Each is matched as a whole word, in
# any of the listed forms, and reported only when States 0..N-1 do not use it.
MECHANISM = {
    "temporary": r"temporar(?:y|ily)",
    "rename": r"renam(?:e|es|ed|ing)",
    "synchronise": r"sync(?:s|ed|ing)?|synchroni[sz](?:e|es|ed|ing|ation)|fsync",
    "durable": r"durabl[ey]|durability",
    "atomic": r"atomic(?:ally)?",
    "lock": r"lock(?:s|ed|ing)?|lock file",
    "mode": r"modes?|permissions?|umask",
    "open": r"open(?:s|ed|ing)?",
    "descriptor": r"descriptors?|handles?",
    "system call": r"system calls?|syscalls?",
    "retry": r"retr(?:y|ies|ied|ying)",
    "suffix": r"suffix(?:es)?|prefix(?:es)?",
    "exclusive": r"exclusive(?:ly)?",
    "flush": r"flush(?:es|ed|ing)?",
    "buffer": r"buffer(?:s|ed|ing)?",
    "thread": r"threads?|process(?:es)?",
    "cache": r"cach(?:e|es|ed|ing)",
    "library": r"librar(?:y|ies)",
}
HEADING = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")


def _git(case: Path, *args: str) -> str | None:
    done = subprocess.run(["git", "-C", str(case), *args], capture_output=True, text=True)
    return done.stdout if done.returncode == 0 else None


def _at(case: Path, name: str, ref: str) -> str:
    """The document as it was at `ref`; "" when it did not exist there."""
    prefix = (_git(case, "rev-parse", "--show-prefix") or "").strip()
    return _git(case, "show", f"{ref}:{prefix}{name}") or ""


def _sections(text: str) -> list[tuple[str, int]]:
    """(level-2 heading or "(preamble)", line number) for every line."""
    current, rows = "(preamble)", []
    for number, line in enumerate(text.splitlines(), 1):
        match = HEADING.match(line)
        if match and len(match.group(1)) <= 2:
            current = match.group(2)
        rows.append((current, number))
    return rows


def _added(old: str, new: str) -> dict[str, list[str]]:
    """The lines `new` adds over `old`, by the section of `new` they stand in."""
    sections = _sections(new)
    new_lines, added = new.splitlines(), {}
    matcher = difflib.SequenceMatcher(None, old.splitlines(), new_lines, autojunk=False)
    for tag, _, _, start, end in matcher.get_opcodes():
        if tag in ("insert", "replace"):
            for index in range(start, end):
                added.setdefault(sections[index][0], []).append(new_lines[index])
    return added


def _words(pattern: str, text: str) -> list[str]:
    return re.findall(rf"(?<![\w-])(?:{pattern})(?![\w-])", text, re.IGNORECASE)


def report(case: Path, state: int, since: str | None) -> dict:
    """What the changes of State `state` since `since` introduce, by document
    and section. Without `since` the whole current text counts as added."""
    docs = documents.design_documents(case, state)
    own = [(s, path) for s, path in docs if s == state]
    if not own:
        raise ValueError(f"{case.name} has no State {state} document")
    earlier = "\n".join(path.read_text(encoding="utf-8") for s, path in docs if s < state)
    earlier_low = earlier.lower()
    rows = []
    for _, path in own:
        new = path.read_text(encoding="utf-8")
        old = _at(case, path.name, since) if since else ""
        known = set(IDENTIFIER.findall(earlier)) | set(IDENTIFIER.findall(old))
        for section, lines in _added(old, new).items():
            text = "\n".join(lines)
            names = sorted(set(IDENTIFIER.findall(text)) - known)
            identifiers = [n for n in names if not n.startswith("test_") and n not in earlier]
            tests = [n for n in names if n.startswith("test_")]
            words = {}
            for word, pattern in MECHANISM.items():
                if _words(pattern, earlier_low):
                    continue
                found = _words(pattern, text)
                if found:
                    words[word] = len(found)
            if identifiers or words:
                rows.append({"document": path.name, "section": section, "added_lines": len(lines),
                             "identifiers": identifiers, "mechanism_words": words, "test_names": tests})
    return {"case": case.name, "state": state, "since": since, "sections": rows,
            "identifiers": sum(len(r["identifiers"]) for r in rows),
            "mechanism_words": sum(sum(r["mechanism_words"].values()) for r in rows)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("case", type=Path)
    parser.add_argument("--state", type=int, default=2)
    parser.add_argument("--since", help="git ref the change is measured from (default: the whole text)")
    parser.add_argument("--strict", action="store_true", help="exit 1 when anything is reported")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = report(args.case, args.state, args.since)
    except ValueError as exc:
        print(f"design_change_vocabulary: error: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"State {result['state']} of {result['case']} since {result['since'] or 'the beginning'}: "
              f"{result['identifiers']} new identifier(s), {result['mechanism_words']} mechanism word(s) "
              f"the earlier states do not use")
        for row in result["sections"]:
            words = ", ".join(f"{w}×{n}" for w, n in row["mechanism_words"].items())
            print(f"  {row['document']} / {row['section']}")
            if row["identifiers"]:
                print(f"    identifiers: {', '.join(row['identifiers'])}")
            if words:
                print(f"    mechanism words: {words}")
        if result["sections"]:
            print("  Each is a question for the author: does a requirement need this named here, or does it say how "
                  "and belong to a later state (dispose --carried, with --keeps)?")
    return 1 if args.strict and result["sections"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
