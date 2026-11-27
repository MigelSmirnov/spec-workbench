"""Find single-key enum lookups for a note in the current case projection."""
import argparse
import json
from pathlib import Path

from spec_projection_workbench import projected_spec


def find_enum_lookup(case: Path, source: str, target: str) -> dict:
    spec = projected_spec(case)
    models = spec["models"]
    for name in (source, target):
        if models.get(name, {}).get("kind") != "enum":
            raise ValueError(f"{name!r} is not a declared enum; check its name in the current case.")
    provider = spec.get("rules", {}).get("data_provider_backend", {})
    matches = []
    for symbol, table in sorted(provider.get("constants", {}).items()):
        key = table.get("key")
        if table.get("value_type") != "record_tuple" or not isinstance(key, list) or len(key) != 1:
            continue
        fields = models.get(table["row_model"], {}).get("fields", {})
        if fields.get(key[0]) != source:
            continue
        for field, enum in fields.items():
            if field != key[0] and enum == target:
                matches.append({"constant": symbol, "row_model": table["row_model"], "select_by": key[0],
                                "read_field": field, "total": table.get("total") is True})
    guidance = ("Choose the matching table and result field from the design. Check the consumer imports the "
                "constant. Name it and the selection field in the note; read the result field from that row.")
    if not matches:
        guidance = ("No single-key typed table for this direction in this projection. If the design requires "
                    "this mapping, open an enum mapping structure request.")
    return {"source": source, "target": target, "matches": matches, "guidance": guidance}


def main(argv=None):
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("case", type=Path)
    cli.add_argument("source", help="enum used to select a row")
    cli.add_argument("target", help="enum the consumer needs")
    args = cli.parse_args(argv)
    try:
        report = find_enum_lookup(args.case, args.source, args.target)
    except (ValueError, OSError) as exc:
        cli.exit(2, f"Cannot search this case: {exc}\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
