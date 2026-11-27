from pathlib import Path

import pytest

import find_enum_lookup as lookup


@pytest.fixture
def find(monkeypatch):
    models = {"Action": {"kind": "enum"}, "Status": {"kind": "enum"}, "Other": {"kind": "enum"},
              "Row": {"fields": {"action": "Action", "result": "Status"}}}
    row = {"value_type": "record_tuple", "row_model": "Row", "key": ["action"], "total": True}
    tables = {"B": row, "A": {**row, "total": False}, "COMPOSITE": {**row, "key": ["action", "result"]},
              "UNTYPED": {"value_type": "string_mapping", "value": {"x": "y"}}}
    spec = {"models": models, "rules": {"data_provider_backend": {"constants": tables}}}
    monkeypatch.setattr(lookup, "projected_spec", lambda case: spec)
    return lambda a, b: lookup.find_enum_lookup(Path("."), a, b)


def test_lists_all_candidates_without_guessing_or_copying_values(find):
    rows = find("Action", "Status")["matches"]
    assert rows == [{"constant": name, "row_model": "Row", "select_by": "action", "read_field": "result",
                     "total": total, "declared_importers": None,
                     "edit_form": f"python tools/design_enum_map.py template . {name} --source Action.action "
                                  f"--target Status.result --row-model Row {mode}"}
                    for name, total, mode in [("A", False, "--partial"), ("B", True, "--total")]]


def test_names_the_modules_that_declare_the_import(find, monkeypatch, tmp_path):
    lookup.projected_spec(None)["rules"]["data_provider_backend"]["wiring"] = {"module": "tables"}
    (tmp_path / "65_imports.json").write_text(
        '{"scopes": {"ui.show": {"uses": [{"provider": "tables", "symbol": "B"}]}}}')
    rows = {row["constant"]: row["declared_importers"]
            for row in lookup.find_enum_lookup(tmp_path, "Action", "Status")["matches"]}
    assert rows == {"A": [], "B": ["ui"]}


def test_direction_and_empty_result(find):
    assert find("Status", "Action")["matches"] == []
    assert "structure request" in find("Other", "Action")["guidance"]
    missing = find("Other", "Action")
    assert "string_mapping" in missing["guidance"]
    assert missing["create_form"].endswith("--source Other.KEY_FIELD --target Action.VALUE_FIELD --row-model RowModelName --total")
    assert "create_form" not in find("Action", "Status")
    with pytest.raises(ValueError, match="not a declared enum"):
        find("Missing", "Status")
