"""Post-State-5 readers take operations from a State 5 split by module."""
from __future__ import annotations

import design_closure_gaps
import design_stage5
from notes_workbench import slice_builder

OPERATION = """## `public_op:{module}.{name}`

### Inputs

None.

### State impact

{impact}
"""


def _write(project, name, *operations):
    (project / name).write_text("# State 5 — public operations\n\n" + "\n".join(operations), encoding="utf-8")


def test_split_documents_are_read_when_the_canonical_one_is_absent(tmp_path):
    _write(tmp_path, "50_public_apis_clock.md", OPERATION.format(module="clock", name="now", impact="None."))
    _write(tmp_path, "50_public_apis_store.md", OPERATION.format(module="store", name="put", impact="Writes one value."))

    assert [path.name for path in design_stage5.public_api_documents(tmp_path)] == [
        "50_public_apis_clock.md", "50_public_apis_store.md"]
    details = slice_builder._public_op_details(tmp_path, "store")
    assert [item["key"] for item in details] == ["public_op:store.put"]
    assert details[0]["source"]["path"] == "50_public_apis_store.md"
    impacts = design_closure_gaps.parse_state_impacts(tmp_path)
    assert {name: row["module"] for name, row in impacts.items()} == {"now": "clock", "put": "store"}
    assert impacts["put"]["impact"] == "Writes one value."


def test_an_empty_impact_does_not_borrow_the_next_document_heading_text(tmp_path):
    _write(tmp_path, "50_public_apis_clock.md", OPERATION.format(module="clock", name="now", impact=""))
    _write(tmp_path, "50_public_apis_store.md", OPERATION.format(module="store", name="put", impact="Writes one value."))

    assert design_closure_gaps.parse_state_impacts(tmp_path)["now"]["impact"] == ""


def test_the_canonical_document_is_read_alone_so_recorded_slices_do_not_move(tmp_path):
    _write(tmp_path, "50_public_apis.md", OPERATION.format(module="store", name="put", impact="Writes one value."))
    _write(tmp_path, "50_public_apis_store_repair.md", OPERATION.format(module="store", name="repair", impact="None."))

    assert [path.name for path in design_stage5.public_api_documents(tmp_path)] == ["50_public_apis.md"]
    assert [item["key"] for item in slice_builder._public_op_details(tmp_path, "store")] == ["public_op:store.put"]
    assert sorted(design_closure_gaps.parse_state_impacts(tmp_path)) == ["put"]


def test_a_case_without_state5_documents_has_no_operations(tmp_path):
    assert design_stage5.public_api_documents(tmp_path) == []
    assert slice_builder._public_op_details(tmp_path, "store") == []
    assert design_closure_gaps.parse_state_impacts(tmp_path) == {}
