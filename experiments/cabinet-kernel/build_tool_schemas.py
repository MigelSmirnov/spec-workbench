#!/usr/bin/env python3
"""The tools/list schemas of the MCP entrance, as data_provider constants (decision 58).

Reads the catalogue order from State 5 (50_public_apis.md) and each operation's
request model from the accepted specification (contracts and models); writes
MCP_CATALOGUE_OPERATIONS and MCP_TOOL_INPUT_SCHEMAS into 70_data_provider_closure.json.
With --check it writes nothing and fails when the closure differs.

The rule, the only one: a model is {"type": "object", "properties": its fields in
declared order, "required": its fields not typed X | None, "additionalProperties":
false}; str is {"type": "string"}, int {"type": "integer"}, X | None {"anyOf": [the
schema of X, {"type": "null"}]}, tuple[X, ...] {"type": "array", "items": the schema
of X}, an enumeration {"type": "string", "enum": its members in declared order}, a
Literal tag {"const": the tag}, a discriminated union {"anyOf": the schemas of its
variants in declared order}. No other keyword is added.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

CASE = Path(__file__).resolve().parents[2] / "examples" / "cabinet-kernel"
CLOSURE = CASE / "70_data_provider_closure.json"
OPERATION_ROW = re.compile(r"^\| `([a-z_]+)` \|")
REQUEST = re.compile(r"\brequest: *([A-Z]\w*)")
LITERAL = re.compile(r"^Literal\[['\"]([^'\"]+)['\"]\]$")


def catalogue_operations() -> list[str]:
    lines = (CASE / "50_public_apis.md").read_text(encoding="utf-8").splitlines()
    start = lines.index("## MCP surface catalogue")
    header = next(i for i in range(start, len(lines)) if lines[i].startswith("| MCP operation"))
    operations = []
    for line in lines[header + 2:]:
        match = OPERATION_ROW.match(line)
        if match is None:
            break
        operations.append(match.group(1))
    return operations


def annotation_schema(text: str, models: dict, stack: tuple[str, ...]) -> dict:
    text = text.strip()
    if text.endswith("| None"):
        return {"anyOf": [annotation_schema(text[: -len("| None")], models, stack), {"type": "null"}]}
    if text == "str":
        return {"type": "string"}
    if text == "int":
        return {"type": "integer"}
    literal = LITERAL.match(text)
    if literal:
        return {"const": literal.group(1)}
    if text.startswith("tuple[") and text.endswith(", ...]"):
        return {"type": "array", "items": annotation_schema(text[len("tuple["): -len(", ...]")], models, stack)}
    return model_schema(text, models, stack)


def model_schema(name: str, models: dict, stack: tuple[str, ...]) -> dict:
    if name in stack:
        raise SystemExit(f"a request model is recursive through {name}: the rule has no form for it")
    declaration = models.get(name)
    if not isinstance(declaration, dict):
        raise SystemExit(f"the rule has no form for the annotation {name!r}")
    kind = declaration.get("kind")
    if kind == "enum":
        return {"type": "string", "enum": list(declaration["values"])}
    if kind == "discriminated_union":
        return {"anyOf": [model_schema(variant, models, stack + (name,)) for variant in declaration["variants"]]}
    fields = declaration["fields"]
    return {
        "type": "object",
        "properties": {field: annotation_schema(annotation, models, stack + (name,))
                       for field, annotation in fields.items()},
        "required": [field for field, annotation in fields.items() if not annotation.strip().endswith("| None")],
        "additionalProperties": False,
    }


def constants(spec: dict) -> dict:
    operations = catalogue_operations()
    schemas = {}
    for operation in operations:
        match = REQUEST.search(spec["contracts"][f"handle_{operation}"])
        if match is None:
            raise SystemExit(f"handle_{operation} names no request model")
        schemas[operation] = json.dumps(model_schema(match.group(1), spec["models"], ()),
                                        ensure_ascii=False, separators=(",", ":"))
    return {
        "MCP_CATALOGUE_OPERATIONS": {"value_type": "string_tuple", "value": operations},
        "MCP_TOOL_INPUT_SCHEMAS": {"value_type": "string_mapping", "value": schemas},
    }


def main() -> int:
    spec = json.loads((CASE / "global_spec.json").read_text(encoding="utf-8"))
    closure = json.loads(CLOSURE.read_text(encoding="utf-8"))
    wanted = constants(spec)
    current = closure["backend_ir"]["constants"]
    if "--check" in sys.argv[1:]:
        stale = [name for name, row in wanted.items() if current.get(name) != row]
        print("stale: " + ", ".join(stale) if stale else "in step")
        return 1 if stale else 0
    current.update(wanted)
    CLOSURE.write_text(json.dumps(closure, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{len(wanted['MCP_CATALOGUE_OPERATIONS']['value'])} operations written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
