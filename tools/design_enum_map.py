#!/usr/bin/env python3
"""Author a State 7 enum-to-enum lookup in its provider and model closures (§6.10)."""
import argparse
import difflib
import json
import keyword
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import authoring_form as forms
from design_stage6_data import DATA_PROVIDER_CLOSURE
from identity_workbench.service import state6_closure, verify
from identity_workbench.sources import load_state1
from imports_workbench import service as imports
from notes_authoring.index import enum_member_names

IDENTITIES = ("value", "entity")
# Everything the identity check reads; the trial copy holds exactly these.
IDENTITY_SOURCES = ("01_models*.md", "60_model_closure_*.json", "60_contracts.json",
                    DATA_PROVIDER_CLOSURE, "global_spec.json")
QUESTION = ("If this row were replaced by another row holding the same pair of values, would anything "
            "change for the product? No: value. Yes, the row itself is followed through changes: entity. "
            "Answer in row_identity and say why in row_identity_reason (SPEC_STANDARD §15.1.1).")
ENTITY_QUESTION = ("{row} is declared entity, yet a row of a constant table never changes state. Say in "
                   "row_identity_reason why this table may reuse it, or name another row model.")


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate key {key!r}")
        result[key] = value
    return result


def read(path):
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object)


def identifier(name):
    if not isinstance(name, str) or not name.isidentifier() or keyword.iskeyword(name):
        raise ValueError(f"invalid identifier: {name!r}")
    return name


def column(spec):
    if spec.count(".") != 1:
        raise ValueError(f"{spec!r}: write the column as Enum.field, the enum and the row field that holds it")
    enum, field = spec.split(".")
    return identifier(enum), identifier(field)


def members(model):
    if model.get("kind") != "enum":
        raise ValueError("both columns must name declared enums")
    if "values" not in model and isinstance(model.get("members"), dict):
        model = {**model, "values": list(model["members"].values())}
    names = enum_member_names(model)
    if not names or len(names) != len(model["values"]) or len(set(names.values())) != len(names):
        raise ValueError("enum has empty, duplicate or ambiguous members")
    return names


def context(case, op):
    src, key = column(op["source"])
    dst, value = column(op["target"])
    symbol, row = op["symbol"], identifier(op["row_model"])
    if not re.fullmatch(r"[A-Z][A-Z0-9_]*", symbol) or key == value or type(op["total"]) is not bool:
        raise ValueError("expected an UPPER_SNAKE symbol, distinct column names and boolean total")
    paths = sorted(case.glob("60_model_closure_*.json"))
    provider = case / DATA_PROVIDER_CLOSURE
    # Capture exactly the bytes used to construct the diff and its precondition.
    originals = {p: p.read_bytes() for p in [*paths, provider]}
    docs = {p: json.loads(raw, object_pairs_hook=unique_object) for p, raw in originals.items()}
    models = {}
    owners = {}
    for p in paths:
        doc = docs[p]
        if doc["schema_version"] != "spec_workbench_model_closure.v1":
            raise ValueError(f"unsupported model closure {p.name}")
        for name, model in doc["models"].items():
            if name in models and model != models[name]:
                raise ValueError(f"conflicting declarations for {name}")
            models[name], owners[name] = model, p
    for name in (src, dst):
        if name not in models:
            raise ValueError(f"{name} is not declared in {', '.join(p.name for p in paths) or 'any model closure'}; "
                             "name a declared enum as Enum.field")
    source, target = members(models[src]), members(models[dst])
    fields = {key: src, value: dst}
    if row in models and models[row].get("fields") != fields:
        raise ValueError(f"{row} is already declared in {owners[row].name} as "
                         f"{json.dumps(models[row], ensure_ascii=False)}; use its field names in "
                         "--source/--target or choose another --row-model")
    # Identity: State 1 decides it for a product concept; an existing record keeps
    # its own; for a model born here the author answers the question (§15.1.1).
    state1 = load_state1(case)[0].get(row)
    scoped = [p for p in paths if (docs[p].get("identity_scope") == "contract_only") != bool(state1)]
    row_info = {"state1": state1, "files": [p.name for p in scoped], "declared": None, "file": None}
    if row in models:
        row_info["declared"] = models[row].get("identity")
        row_info["file"] = owners[row].name
    elif owners[src] in scoped:
        row_info["file"] = owners[src].name
    elif len(scoped) == 1:
        row_info["file"] = scoped[0].name
    backend = docs[provider]["backend_ir"]
    if (docs[provider]["schema_version"] != "spec_workbench_data_provider_backend_closure.v1"
            or backend["kind"] != "data_provider_backend" or type(backend["schema_version"]) is not int
            or backend["schema_version"] not in (1, 2)):
        raise ValueError("expected a v1 or v2 data provider")
    old = backend["constants"].get(symbol)
    pairs = {}
    if old is not None:
        if old["value_type"] == "string_mapping":
            pairs = old["value"]
        elif old["value_type"] == "record_tuple" and old["row_model"] == row and old.get("key") == [key]:
            for entry in old["value"]:
                if set(entry) != {key, value} or entry[key] in pairs:
                    raise ValueError(f"invalid existing row in {symbol}")
                pairs[entry[key]] = entry[value]
        else:
            raise ValueError(f"{symbol} already exists with an incompatible shape")
    if set(pairs) - source.keys() or set(pairs.values()) - target.keys():
        raise ValueError(f"{symbol} contains values outside the selected enums; reconcile with the design first")
    cells = {member: target.get(pairs.get(raw)) for raw, member in source.items()}
    read = forms.read_set(case, [*originals, *case.glob("01_models*.md")])
    reopen = forms.command("design_enum_map.py", "template", case, symbol, "--source", op["source"], "--target",
                           op["target"], "--row-model", row, "--total" if op["total"] else "--partial")
    identity = row_info["declared"] or (state1.identity if state1 else None)
    form = {**op, "read_set": read, "revision": forms.revision(read),
            "return_to": forms.return_address(case, symbol, reopen)}
    if old and old.get("total") is True and not op["total"]:
        form["coverage_change"] = (f"{symbol} currently guarantees a result for every {src} member. "
                                   "Partial coverage allows existing or future members to have no result.")
        form["confirm_partial"] = False
    elif any(cells.values()):
        form["confirm_removed"] = []
    if row in models:
        form["row_model_declared"] = {"file": row_info["file"], **models[row]}
    else:
        form["row_model_file"] = row_info["file"]
        form["row_model_files"] = row_info["files"]
    if state1:
        form["row_model_state1"] = {"identity": state1.identity, "location": state1.location}
    form["row_identity"] = identity
    if identity == "entity":
        form["row_identity_question"] = ENTITY_QUESTION.format(row=row)
    elif identity is None:
        form["row_identity_question"] = QUESTION
    if identity != "value":
        form["row_identity_reason"] = None
    form.update({"target_members": list(target.values()), "rows": cells})
    return form, originals, docs, row_info, backend, source, target, fields


def row_declaration(form, row, info):
    """The author's identity answer, checked against what the project already decided."""
    identity, reason = form.get("row_identity"), form.get("row_identity_reason")
    if identity not in IDENTITIES:
        raise ValueError(f"row_identity: {row} needs identity value or entity before anything is written. {QUESTION}")
    for decided, where in ((info["declared"], info["file"]),
                           (info["state1"] and info["state1"].identity, info["state1"] and info["state1"].location)):
        if decided and identity != decided:
            raise ValueError(f"row_identity: {row} is {decided} in {where} and this form keeps it. To change the "
                             "identity, change that record first; to keep it, restore the value in the form")
    explained = isinstance(reason, str) and reason.strip()
    if identity == "entity" and not explained:
        raise ValueError("row_identity_reason: " + ENTITY_QUESTION.format(row=row))
    if not info["declared"] and not info["state1"] and not explained:
        raise ValueError(f"row_identity_reason: {row} is created by this form with no State 1 record, so the "
                         f"choice of {identity} has no other source. {QUESTION}")
    if info["declared"] or info["file"] is not None and form.get("row_model_file", info["file"]) == info["file"]:
        return identity, info["file"]
    target = form.get("row_model_file")
    kind = "without identity_scope contract_only" if info["state1"] else "with identity_scope contract_only"
    if not info["files"]:
        raise ValueError(f"row_model_file: {row} has " + ("a" if info["state1"] else "no") + " State 1 record, so it "
                         f"belongs in a model closure {kind}, and this project has none. Add that closure file"
                         + ("" if info["state1"] else f" or give {row} a State 1 model record") + " first")
    if target not in info["files"]:
        raise ValueError(f"row_model_file: choose where {row} is declared from {info['files']} (closure files {kind}: "
                         + ("it is a State 1 concept" if info["state1"] else "it has no State 1 record") + ")")
    return identity, target


def readers(case, backend, symbol):
    """Who is declared to read the constant, and which notes name it: what a changed row touches."""
    supplier = (backend.get("wiring") or {}).get("module")
    try:
        table = imports.load_table(case)
    except imports.ImportsError as exc:
        table, importers = None, f"unknown ({exc})"
    else:
        importers = (f"unknown: no {imports.table_path(case).name} in this project yet" if table is None else
                     ", ".join(m for m, edges in imports.derive(table).items() if symbol in edges.get(supplier, []))
                     or f"none declared in {imports.table_path(case).name}")
    lines = [f"Readers of {symbol}. Declared importers: {importers}."]
    files = sorted(case.glob("80_notes*.md"))
    found = [f"  {path.name}:{number}: {text.strip()[:220]}" for path in files
             for number, text in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
             if imports.named(symbol, text)]
    if not files:
        lines.append("Notes: this project has none yet, so what a reader does with a row is not written down.")
    else:
        lines.append(f"Notes naming it ({len(found)}); a note that reaches the table without naming it is not listed:")
        lines.extend(found)
    lines.append("Read these before deciding: the table does not say what a reader does when a row changes or is absent.")
    return lines


def identity_findings(project):
    reports = [state6_closure(project)]
    if (project / "global_spec.json").is_file():
        reports.append(verify(project))
    return {(f["code"], f.get("model"), f["message"]) for report in reports for f in report["findings"]}


def identity_trial(case, changed):
    """Run the identity check on the files it reads, with the patch applied to a copy."""
    with tempfile.TemporaryDirectory() as tmp:
        trial = Path(tmp) / case.name
        trial.mkdir()
        for pattern in IDENTITY_SOURCES:
            for path in case.glob(pattern):
                shutil.copyfile(path, trial / path.name)
        for path, text in changed.items():
            (trial / path.name).write_bytes(text.encode("utf-8"))
        return identity_findings(trial)


def render_edit(text, before, after):
    """Keep untouched JSON (including formatting) byte-for-byte in the patch."""
    decoder = json.JSONDecoder()

    def space(pos):
        while pos < len(text) and text[pos].isspace():
            pos += 1
        return pos

    def encode(value, pos):
        start = text.rfind("\n", 0, pos) + 1
        indent = re.match(r"[ \t]*", text[start:pos]).group()
        newline = "\r\n" if "\r\n" in text else "\n"
        return json.dumps(value, ensure_ascii=False, indent=2).replace("\n", newline + indent)

    def edits(pos, old, new):
        if old == new:
            return []
        if not isinstance(old, dict) or not isinstance(new, dict) or old.keys() != new.keys():
            # Append a new entry to an existing object without rewriting its siblings.
            if isinstance(old, dict) and old and isinstance(new, dict) and old.keys() < new.keys() and all(
                old[k] == new[k] for k in old
            ):
                cursor = space(pos + 1)
                for item in old:
                    key_pos = cursor
                    _, end = decoder.raw_decode(text, cursor)
                    _, end = decoder.raw_decode(text, space(space(end) + 1))
                    cursor = space(space(end) + 1)
                prefix = text[pos + 1 : space(pos + 1)]
                entries = [json.dumps(k) + ": " + encode(new[k], key_pos) for k in new if k not in old]
                return [(end, end, "," + prefix + ("," + prefix).join(entries))]
            _, end = decoder.raw_decode(text, pos)
            return [(pos, end, encode(new, pos))]
        result = []
        cursor = space(pos + 1)
        for key in old:
            _, end = decoder.raw_decode(text, cursor)
            start = space(space(end) + 1)
            result.extend(edits(start, old[key], new[key]))
            _, end = decoder.raw_decode(text, start)
            cursor = space(space(end) + 1)
        return result

    for start, end, replacement in reversed(edits(space(0), before, after)):
        text = text[:start] + replacement + text[end:]
    return text


def run(args):
    case = args.case.resolve()
    if args.command == "template":
        op = {k: getattr(args, k) for k in ("symbol", "source", "target", "row_model", "total")}
        print(json.dumps(context(case, op)[0], indent=2, ensure_ascii=False))
        return
    form = read(args.form)
    absent = [k for k in ("symbol", "source", "target", "row_model", "total", "revision", "rows") if k not in form]
    if absent:
        raise ValueError(f"form lacks {absent}; generate it with the template command")
    op = {k: form[k] for k in ("symbol", "source", "target", "row_model", "total")}
    current, originals, docs, row_info, backend, source, target, fields = context(case, op)
    key, value = fields
    rows = form["rows"]
    if not isinstance(rows, dict) or not rows or set(rows) - set(source.values()):
        raise ValueError("rows must contain at least one declared source member and no unknown members")
    if op["total"] and rows.keys() != current["rows"].keys():
        raise ValueError("total mapping must cover every source member")
    values = {name: raw for raw, name in target.items()}
    records = []
    for raw, name in source.items():
        if name in rows:
            if rows[name] not in values:
                raise ValueError(f"{name}: choose a target member from {list(values)}")
            records.append({key: raw, value: values[rows[name]]})
    row = op["row_model"]
    try:
        identity, home = row_declaration(form, row, row_info)
    except ValueError:
        forms.require_current(form.get("read_set"), current["read_set"], current["return_to"]["reopen"])
        raise
    owner = next(p for p in docs if p.name == home)
    if row not in docs[owner]["models"]:
        docs[owner]["models"][row] = {"identity": identity, "fields": fields}
    elif "identity" not in docs[owner]["models"][row]:
        docs[owner]["models"][row]["identity"] = identity
    constant = {"value_type": "record_tuple", "row_model": row, "key": [key]}
    if op["total"]:
        constant["total"] = True
    backend["schema_version"] = 2
    backend["constants"][op["symbol"]] = {**constant, "value": records}
    located = subprocess.run(["git", "-C", str(case), "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    if located.returncode:
        raise ValueError(f"{case} is not inside a git checkout; the patch is applied with git, so open the case "
                         "in its spec-workbench checkout")
    root = Path(located.stdout.strip())
    diff = []
    changed = {}
    for path, raw in originals.items():
        before = raw.decode("utf-8")
        if json.loads(before) == docs[path]:
            continue
        if path.is_symlink():
            raise ValueError(f"refusing to replace symlink {path}")
        rel = path.relative_to(root).as_posix()
        after = changed[path] = render_edit(before, json.loads(before), docs[path])
        for line in difflib.unified_diff(before.splitlines(True), after.splitlines(True), f"a/{rel}", f"b/{rel}"):
            diff.append(line if line.endswith("\n") else line + "\n\\ No newline at end of file\n")
    if not diff:
        print("Already matches the requested mapping.")
        return
    forms.require_current(form.get("read_set"), current["read_set"], current["return_to"]["reopen"])
    # The decision in the author's terms first; the diff below only shows how it is stored.
    before = current["rows"]
    removed = [name for name, was in before.items() if was is not None and name not in rows]
    summary = ([f"  + {name} -> {rows[name]}" for name in before if before[name] is None and name in rows]
               + [f"  ~ {name}: {before[name]} -> {rows[name]}" for name in before
                  if before[name] is not None and name in rows and rows[name] != before[name]]
               + [f"  - {name} -> {before[name]} ({name} will have no result)" for name in removed])
    if summary:
        print(f"Rows of {op['symbol']}:")
        print("\n".join(summary))
    blocked = None
    if "coverage_change" in current:
        print(current["coverage_change"])
        if removed:
            print("Members losing their result: " + ", ".join(removed))
        if form.get("confirm_partial") is not True:
            blocked = "Set confirm_partial to true if this change is intended, or regenerate with --total."
    elif removed and (not isinstance(form.get("confirm_removed"), list) or set(form["confirm_removed"]) != set(removed)):
        blocked = (f"Members losing their result: {', '.join(removed)}. Set confirm_removed to {json.dumps(removed)} "
                   "if this is intended, or keep their rows.")
    weakened = "coverage_change" in current or any(line[2] != "+" for line in summary)
    if weakened:
        print("\n".join(readers(case, backend, op["symbol"])))
    patch = "".join(diff)
    print(forms.will_write(case, {path.relative_to(case).as_posix():
                                  "enum table " + op["symbol"] if path.name == DATA_PROVIDER_CLOSURE
                                  else "row model " + row for path in changed}))
    print(patch, end="")
    known = identity_findings(case)
    added = sorted(identity_trial(case, changed) - known, key=str)
    if added:
        raise ValueError("this patch would add identity findings, so nothing was written:\n"
                         + "\n".join(f"  {code} [{model}] - {message}" for code, model, message in added))
    verdict = f"Identity check on the patched copy: no new findings ({len(known)} already present)."
    if args.command != "apply" or blocked:
        print(verdict)
        if blocked:
            raise ValueError(blocked + " Nothing was written.")
        return
    subprocess.run(["git", "apply", "--whitespace=nowarn", "-"], cwd=root, input=patch.encode(), check=True)
    left = sorted(identity_findings(case) - known, key=str)
    if left:
        raise ValueError(f"applied, but the identity check now reports {left}; inspect with design_identity_closure.py")
    print(verdict)
    print(f"Applied. {row}: identity {identity}"
          + (f" ({form['row_identity_reason'].strip()})" if isinstance(form.get("row_identity_reason"), str) else "")
          + f". Consumer note: name the imported {op['symbol']} constant and its selection field {key}."
          + (" Re-read the readers listed above: a row they relied on changed or may now be absent." if weakened else ""))
    print(forms.returning(current["return_to"]))


def main(argv=None):
    cli = argparse.ArgumentParser(description=__doc__)
    commands = cli.add_subparsers(dest="command", required=True)
    template = commands.add_parser("template", help="emit a JSON form; fill rows using target_members")
    template.add_argument("case", type=Path)
    template.add_argument("symbol")
    template.add_argument("--source", required=True, metavar="Enum.key_field")
    template.add_argument("--target", required=True, metavar="Enum.value_field")
    template.add_argument("--row-model", required=True)
    mode = template.add_mutually_exclusive_group(required=True)
    mode.add_argument("--total", dest="total", action="store_true")
    mode.add_argument("--partial", dest="total", action="store_false", help="remove unused rows from the form")
    for cmd in ("preview", "apply"):
        parser = commands.add_parser(cmd)
        parser.add_argument("case", type=Path)
        parser.add_argument("form", type=Path)
    try:
        run(cli.parse_args(argv))
    except (OSError, KeyError, ValueError, TypeError, AttributeError, subprocess.CalledProcessError) as exc:
        print(f"enum-map: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
