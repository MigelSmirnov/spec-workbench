#!/usr/bin/env python3
"""
semantic_lint.py — experimental semantic authoring diagnostic for global_spec.json.

Status: experimental authoring tool, NOT a canonical factory validator.
Factory validators check admissibility and structural coherence of a finished
spec. This tool looks for signs of engineering decisions that were never made:
symbols the factory would have to invent, notes that a trivial implementation
would satisfy, references that resolve to nothing.

Checks:
  S1  type universe closure      — every contract type has an explicit owner
                                   (models / imports.stdlib / third_party / internal)
  S2  exception ownership        — every exception demanded by notes is declared
  S3  reference resolution       — config.* / rules.* / models.* in notes resolve
                                   (limited grammar: a.b, a.rows[*].c, a["key"], a[0])
  S4  vague language             — properly / correctly / as needed / handle errors
  S5  name-restating notes       — note body adds nothing beyond the target name
  S6  generic types              — dict / Any / object as postponed decisions
  S7  semantic coverage hints    — verb-based behavioral profile gaps (advisory)
  S8  trivial-implementation     — normalize_*/validate_*/build_*/resolve_* notes
      resistance                   must name concrete evidence that forbids an
                                   identity / empty implementation
  S9  Factory model path profile — generated models map to core/models for the
                                   current target Factory (advisory)
  S10 invariant landing coverage — State 2 ledger entries resolve to one
                                   function-owned rules/note/property landing

Global notes ("[CLASS] body" without a target) are parsed and checked by
S2/S3/S4; they do not participate in S5/S7/S8.

Usage:
    python3 semantic_lint.py global_spec.json [--invariants invariant_ledger.json]
                             [--matrix] [--strict] [--format json]

Exit codes:
    default (advisory): 1 if errors, else 0 (warnings do not fail)
    --strict:           1 if errors OR warnings, else 0
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

VAGUE_RE = re.compile(
    r"\b(properly|correctly|appropriately|as needed|as required|reasonable|"
    r"best|efficiently|handle errors|if necessary|when necessary)\b",
    re.IGNORECASE)
EXCEPTION_RE = re.compile(r"\b([A-Z][A-Za-z]*(?:Error|Exception))\b")
CAMEL_RE = re.compile(r"\b([A-Z][A-Za-z0-9_]+)\b")
TARGETED_NOTE_RE = re.compile(
    r"^([A-Za-z_][A-Za-z0-9_.]*):\s*(?:\[([A-Z_]+)\]\s*)?(.+)$", re.DOTALL)
GLOBAL_NOTE_RE = re.compile(r"^\[([A-Z_]+)\]\s*(.+)$", re.DOTALL)
GENERIC_RE = re.compile(r"\bAny\b|\bobject\b|\bdict\b(?!\[)|dict\[str,\s*(Any|object)\]")
REF_TOKEN_RE = re.compile(r'([A-Za-z0-9_]+)((?:\[[^\]]*\])*)$')

PY_KNOWN = {
    "None", "True", "False", "Optional", "Union", "Literal", "Annotated",
    "Protocol", "Callable", "Iterable", "Iterator", "Mapping", "Sequence",
    "Decimal", "Enum", "BaseModel", "Path",
    "BaseException", "Exception",
}

MUTATION_VERBS = ("create", "commit", "save", "delete", "update", "apply",
                  "transition", "change", "write", "append", "register")
PRODUCER_VERBS = ("build", "assemble", "collect", "resolve", "serialize",
                  "deserialize", "normalize", "analyze", "get", "list")

# S8: verb -> [(evidence regex over combined note bodies, message)]
CONCRETE_TOKEN = r"(\{[^}]+\}|\b\d+\b|\b[a-z][a-z0-9]*_[a-z0-9_]+\b|[A-Z][A-Za-z]+\.[a-z_]+)"
TRIVIALITY_RULES: dict[str, list[tuple[str, str]]] = {
    "normalize": [
        (CONCRETE_TOKEN,
         "no concrete field or value set named — identity implementation "
         "would satisfy the notes"),
        (r"\b(preserve|unchanged|identical|MUST NOT)\b",
         "no preserved/forbidden property stated — nothing pins what "
         "normalization must NOT change"),
    ],
    "validate": [
        (r"\b(raise|reject|error|issue|invalid|missing|report|severity)\b",
         "no failure or result semantics stated — an always-empty report "
         "would satisfy the notes"),
    ],
    "build": [
        (CONCRETE_TOKEN,
         "no shape or mandatory stage pinned — an empty artifact would "
         "satisfy the notes"),
    ],
    "assemble": [
        (CONCRETE_TOKEN,
         "no shape or mandatory stage pinned — an empty artifact would "
         "satisfy the notes"),
    ],
    "resolve": [
        (r"\b(raise|error|sorted|order|precedence|source|exact|fail)\b",
         "no precedence, source, or failure semantics — silently returning "
         "nothing would satisfy the notes"),
    ],
}


# ---------------------------------------------------------------- helpers

def imported_symbols(spec: dict) -> set[str]:
    """Names importable per imports.stdlib / third_party / internal."""
    out: set[str] = set()
    imports = spec.get("imports", {}) or {}
    for section in ("stdlib", "third_party"):
        for line in imports.get(section, []) or []:
            m = re.match(r"from\s+\S+\s+import\s+(.+)", line)
            if m:
                out.update(n.strip().split(" as ")[-1]
                           for n in m.group(1).split(","))
                continue
            m = re.match(r"import\s+(\S+)", line)
            if m:
                out.add(m.group(1).split(".")[0])
    internal = imports.get("internal", {}) or {}
    if isinstance(internal, dict):
        for names in internal.values():
            out.update(names or [])
    elif isinstance(internal, list):  # tolerate flat-list variants
        out.update(internal)
    return out


def resolve_ref(root: object, dotted: str) -> bool:
    """Resolve limited reference grammar: a.b, a.rows[*].c, a["key"], a[0]."""
    cur = root
    for raw in dotted.split("."):
        m = REF_TOKEN_RE.match(raw)
        if not m:
            return False
        name, brackets = m.groups()
        if not isinstance(cur, dict) or name not in cur:
            return False
        cur = cur[name]
        for idx in re.findall(r"\[([^\]]*)\]", brackets or ""):
            key = idx.strip("\"' ")
            if isinstance(cur, list):
                if not cur:
                    return True  # empty collection: path shape is plausible
                cur = cur[0]
            elif isinstance(cur, dict):
                if key == "*":
                    vals = list(cur.values())
                    if not vals:
                        return True
                    cur = vals[0]
                elif key in cur:
                    cur = cur[key]
                else:
                    return False
            else:
                return False
    return True


def tokens(name: str) -> set[str]:
    return {t.lower() for t in re.split(r"[^A-Za-z0-9]+", name) if len(t) > 2}


# ---------------------------------------------------------------- core

def lint(spec: dict, invariant_ledger: dict | None = None) -> dict:
    errors: list[str] = []
    warnings: list[str] = []

    contracts: dict[str, str] = spec.get("contracts", {}) or {}
    notes: list[str] = spec.get("notes", []) or []
    models: dict = spec.get("models", {}) or {}

    known = set(models) | imported_symbols(spec) | PY_KNOWN
    known |= {n.split(".")[0] for n in contracts if "." in n}

    # ---- parse notes: targeted and global ----
    targeted = []   # (target, cls, body, idx)
    global_notes = []  # (cls, body, idx)
    for idx, note in enumerate(notes):
        m = TARGETED_NOTE_RE.match(note)
        if m:
            targeted.append((m.group(1), m.group(2) or "", m.group(3), idx))
            continue
        g = GLOBAL_NOTE_RE.match(note)
        if g:
            global_notes.append((g.group(1), g.group(2), idx))
        # anything else is a format concern -> factory territory, skip

    all_bodies = ([(t, b, i) for t, _, b, i in targeted]
                  + [(None, b, i) for _, b, i in global_notes])

    # ---- S1: type universe closure ----
    unknown: dict[str, list[str]] = {}
    for fname, sig in contracts.items():
        for tok in CAMEL_RE.findall(sig):
            if tok not in known and not tok.isupper():
                unknown.setdefault(tok, []).append(fname)
    for tok, users in sorted(unknown.items()):
        more = f" +{len(users)-1} more" if len(users) > 1 else ""
        errors.append(f"S1 undefined type {tok!r} in contracts of {users[0]}{more} "
                      f"— no explicit owner; the factory will invent its shape")

    # ---- S2: exception ownership (targeted + global notes) ----
    declared_exc = {t for t in known if t.endswith(("Error", "Exception"))}
    for target, body, idx in all_bodies:
        where = f"note #{idx}" + (f" ({target})" if target else " (global)")
        for exc in EXCEPTION_RE.findall(body):
            if exc not in declared_exc:
                errors.append(f"S2 {where} demands {exc!r} but nothing declares "
                              f"it — no owner")
                declared_exc.add(exc)

    # ---- S3: reference resolution (targeted + global notes) ----
    for target, body, idx in all_bodies:
        where = f"note #{idx}" + (f" ({target})" if target else " (global)")
        for section in ("config", "rules", "models"):
            for ref in re.findall(rf'{section}\.([A-Za-z0-9_.\[\]"\'*]+)', body):
                ref = ref.rstrip(".")
                if not resolve_ref(spec.get(section, {}) or {}, ref):
                    errors.append(f"S3 {where}: {section}.{ref} does not resolve")

    # ---- S4: vague language (targeted + global notes) ----
    for target, body, idx in all_bodies:
        m = VAGUE_RE.search(body)
        if m:
            where = f"note #{idx}" + (f" ({target})" if target else " (global)")
            warnings.append(f"S4 {where}: vague {m.group(0)!r} — cannot "
                            f"distinguish implementation from stub")

    # ---- S5: name-restating notes (targeted only) ----
    for target, cls, body, idx in targeted:
        body_tok = tokens(re.sub(r"MUST( NOT)?", "", body))
        name_tok = tokens(target)
        if name_tok and body_tok and body_tok <= name_tok | {
                "the", "and", "value", "values", "data"}:
            warnings.append(f"S5 note #{idx} ({target}): note adds nothing "
                            f"beyond the function name")

    # ---- S6: generic types ----
    for fname, sig in contracts.items():
        if GENERIC_RE.search(sig):
            warnings.append(f"S6 contract {fname}: generic type in signature — "
                            f"justified external boundary, or hidden decision?")
    for mname, mdef in models.items():
        for fld, ftype in ((mdef or {}).get("fields", {}) or {}).items():
            if isinstance(ftype, str) and GENERIC_RE.search(ftype):
                warnings.append(f"S6 model {mname}.{fld}: generic type {ftype!r}")

    # ---- coverage map (feeds S7 and --matrix) ----
    coverage: dict[str, set[str]] = {f: set() for f in contracts}
    notes_by_fn: dict[str, list[str]] = {f: [] for f in contracts}
    for target, cls, body, _ in targeted:
        matched = [f for f in coverage
                   if f == target or f.split(".")[0] == target.split(".")[0]]
        for f in matched:
            if cls:
                coverage[f].add(cls)
            notes_by_fn[f].append(body)

    # ---- S7: verb-profile hints (advisory) ----
    for fname, classes in coverage.items():
        verb = fname.split(".")[-1].split("_")[0].lower()
        if not classes and not notes_by_fn[fname]:
            warnings.append(f"S7 {fname}: no notes at all — passes the "
                            f"'return None' test?")
            continue
        if verb in MUTATION_VERBS and not classes & {
                "ORCHESTRATION", "FIELD_ASSIGNMENT", "SECURITY_BOUNDARY",
                "RULE_REFERENCE", "FORBIDDEN_ACTION", "BEHAVIOR",
                "CONFIG_REFERENCE"}:
            warnings.append(f"S7 hint {fname}: mutating verb but no note about "
                            f"effects, rules, or boundaries")
        if verb in PRODUCER_VERBS and not classes & {
                "RETURN_SHAPE", "FIELD_PROJECTION", "FIELD_ASSIGNMENT",
                "DETERMINISM_OR_ORDERING", "SCHEMA_CONSTRAINT", "BEHAVIOR",
                "ORCHESTRATION", "VALIDATION_ERROR"}:
            warnings.append(f"S7 hint {fname}: producer verb but nothing pins "
                            f"the shape of what it produces")

    # ---- S8: trivial-implementation resistance ----
    for fname in contracts:
        verb = fname.split(".")[-1].split("_")[0].lower()
        rules = TRIVIALITY_RULES.get(verb)
        if not rules:
            continue
        combined = " ".join(notes_by_fn[fname])
        if not combined:
            continue  # already reported by S7
        for pattern, message in rules:
            if not re.search(pattern, combined):
                warnings.append(f"S8 {fname}: {message}")

    # ---- S9: current Factory deterministic model-path profile ----
    module_functions = spec.get("module_functions", {}) or {}
    if models or "models" in module_functions:
        model_path = (spec.get("module_paths", {}) or {}).get("models")
        if model_path != "core/models":
            actual = repr(model_path) if model_path is not None else "missing"
            warnings.append(
                "S9 models generation unit path is "
                f"{actual}; current Factory profile requires 'core/models' "
                "for deterministic generation and runtime imports")

    # ---- S10: State 2 invariant landing coverage ----
    invariant_coverage: dict[str, dict[str, str | None]] = {}
    if invariant_ledger is not None:
        entries = invariant_ledger.get("invariants") if isinstance(invariant_ledger, dict) else None
        schema_version = invariant_ledger.get("schema_version") if isinstance(invariant_ledger, dict) else None
        if schema_version != 1:
            warnings.append(
                f"S10 invariant ledger schema_version must be 1, got {schema_version!r}")
        if not isinstance(entries, list):
            warnings.append(
                "S10 invariant ledger must be an object with an 'invariants' list")
            entries = []

        seen_ids: set[str] = set()
        properties = spec.get("properties", {}) or {}
        for index, entry in enumerate(entries):
            if not isinstance(entry, dict):
                warnings.append(f"S10 invariant #{index}: entry must be an object")
                continue

            invariant_id = entry.get("id")
            display_id = invariant_id if isinstance(invariant_id, str) and invariant_id else f"#{index}"
            owner = entry.get("owner_function")
            landing = entry.get("landing")
            kind = landing.get("kind") if isinstance(landing, dict) else None
            status = "covered"

            if not isinstance(invariant_id, str) or not invariant_id.strip():
                warnings.append(f"S10 invariant #{index}: missing stable id")
                status = "invalid"
            elif invariant_id in seen_ids:
                warnings.append(f"S10 invariant {invariant_id}: duplicate id")
                status = "invalid"
            else:
                seen_ids.add(invariant_id)

            statement = entry.get("statement")
            if not isinstance(statement, str) or not statement.strip():
                warnings.append(f"S10 invariant {display_id}: missing statement")
                status = "invalid"

            if not isinstance(owner, str) or owner not in contracts:
                warnings.append(
                    f"S10 invariant {display_id}: owner_function {owner!r} "
                    "does not resolve to a contract")
                status = "uncovered"

            if not isinstance(landing, dict):
                warnings.append(
                    f"S10 invariant {display_id}: no landing; choose rules, note, or property")
                status = "uncovered"
            elif kind == "rules":
                path = landing.get("path")
                if not isinstance(path, str) or not resolve_ref(spec.get("rules", {}) or {}, path):
                    warnings.append(
                        f"S10 invariant {display_id}: rules landing {path!r} does not resolve")
                    status = "uncovered"
            elif kind == "note":
                text = landing.get("text")
                owner_prefix = f"{owner}:" if isinstance(owner, str) else None
                if not isinstance(text, str) or text not in notes:
                    warnings.append(
                        f"S10 invariant {display_id}: note landing is absent from notes")
                    status = "uncovered"
                elif owner_prefix and not text.startswith(owner_prefix):
                    warnings.append(
                        f"S10 invariant {display_id}: note landing is not owned by {owner!r}")
                    status = "uncovered"
            elif kind == "property":
                expression = landing.get("expression")
                owner_properties = properties.get(owner, []) if isinstance(properties, dict) else []
                if not isinstance(expression, str) or expression not in owner_properties:
                    warnings.append(
                        f"S10 invariant {display_id}: property landing is absent from "
                        f"properties.{owner}")
                    status = "uncovered"
            else:
                warnings.append(
                    f"S10 invariant {display_id}: landing kind must be rules, note, or property")
                status = "uncovered"

            invariant_coverage[str(display_id)] = {
                "owner_function": owner if isinstance(owner, str) else None,
                "landing_kind": kind if isinstance(kind, str) else None,
                "status": status,
            }

    return {
        "errors": errors,
        "warnings": warnings,
        "coverage": {f: sorted(c) for f, c in coverage.items()},
        "invariant_coverage": invariant_coverage,
    }


# ---------------------------------------------------------------- cli

def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec", type=Path)
    ap.add_argument(
        "--invariants", type=Path,
        help="State 2 invariant_ledger.json used for S10 landing coverage")
    ap.add_argument("--matrix", action="store_true",
                    help="print per-function semantic coverage matrix")
    ap.add_argument("--strict", action="store_true",
                    help="warnings also fail (exit 1)")
    ap.add_argument("--format", choices=("text", "json"), default="text")
    args = ap.parse_args()

    try:
        spec = json.loads(args.spec.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR   cannot load spec: {exc}", file=sys.stderr)
        return 1

    invariant_ledger = None
    if args.invariants is not None:
        try:
            invariant_ledger = json.loads(args.invariants.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"ERROR   cannot load invariant ledger: {exc}", file=sys.stderr)
            return 1

    result = lint(spec, invariant_ledger)

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=1))
    else:
        for e in result["errors"]:
            print(f"ERROR   {e}")
        for w in result["warnings"]:
            print(f"WARNING {w}")
        if args.matrix:
            print("\n--- semantic coverage matrix ---")
            cov = result["coverage"]
            width = max((len(f) for f in cov), default=0)
            for fname, classes in cov.items():
                print(f"{fname:<{width}}  {', '.join(classes) or '—'}")
            if result["invariant_coverage"]:
                print("\n--- State 2 invariant landing coverage ---")
                for invariant_id, item in result["invariant_coverage"].items():
                    print(
                        f"{invariant_id}  {item['status']}  "
                        f"{item['owner_function'] or '—'}  {item['landing_kind'] or '—'}")
        print(f"\n{len(result['errors'])} error(s), "
              f"{len(result['warnings'])} warning(s)")

    if result["errors"]:
        return 1
    if args.strict and result["warnings"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
