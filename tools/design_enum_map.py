#!/usr/bin/env python3
"""Author a State 7 enum-to-enum lookup in its provider and model closures (§6.10)."""
import argparse
import difflib
import hashlib
import json
import keyword
import re
import subprocess
import sys
from pathlib import Path

from design_stage6_data import DATA_PROVIDER_CLOSURE
from notes_authoring.index import enum_member_names


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
    source, target = members(models[src]), members(models[dst])
    fields = {key: src, value: dst}
    if row in models and models[row].get("fields") != fields:
        raise ValueError(f"{row} already exists with another declaration")
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
    digest = hashlib.sha256()
    for p, raw in originals.items():
        digest.update(p.name.encode() + b"\0" + hashlib.sha256(raw).digest())
    form = {**op, "revision": digest.hexdigest(), "target_members": list(target.values()), "rows": cells}
    return form, originals, docs, owners[src], backend, source, target, fields


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
    op = {k: form[k] for k in ("symbol", "source", "target", "row_model", "total")}
    current, originals, docs, owner, backend, source, target, fields = context(case, op)
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
    if not any(row in doc.get("models", {}) for doc in docs.values()):
        docs[owner]["models"][row] = {"fields": fields}
    constant = {"value_type": "record_tuple", "row_model": row, "key": [key]}
    if op["total"]:
        constant["total"] = True
    backend["schema_version"] = 2
    backend["constants"][op["symbol"]] = {**constant, "value": records}
    root = Path(subprocess.check_output(["git", "-C", str(case), "rev-parse", "--show-toplevel"], text=True).strip())
    diff = []
    for path, raw in originals.items():
        before = raw.decode("utf-8")
        if json.loads(before) == docs[path]:
            continue
        if path.is_symlink():
            raise ValueError(f"refusing to replace symlink {path}")
        rel = path.relative_to(root).as_posix()
        after = render_edit(before, json.loads(before), docs[path])
        for line in difflib.unified_diff(before.splitlines(True), after.splitlines(True), f"a/{rel}", f"b/{rel}"):
            diff.append(line if line.endswith("\n") else line + "\n\\ No newline at end of file\n")
    if not diff:
        print("Already matches the requested mapping.")
        return
    if form["revision"] != current["revision"]:
        raise ValueError("stale form: generate a fresh template from the current closures")
    patch = "".join(diff)
    print(patch, end="")
    if args.command == "apply":
        subprocess.run(["git", "apply", "--whitespace=nowarn", "-"], cwd=root, input=patch.encode(), check=True)
        print(f"Applied. Consumer note: name the imported {op['symbol']} constant and its selection field {key}.")


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
