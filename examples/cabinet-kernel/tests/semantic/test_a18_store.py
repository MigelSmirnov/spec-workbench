"""Witness tests for accepted decision A18 (02_rules_installation.md).

One process, one store, one writer: a second kernel on the same data
directory refuses to start; value bytes are published complete,
digest-checked and never overwritten; a failed store call writes no record;
a symbolic link in the data directory stops the start or fails the store call
that meets it; and only the store module opens the database or handles a
transaction. Each test carries the witness name its Required test declares.

The Factory project supplies the ``semantic_runtime`` pytest fixture. It binds
these scenarios to the generated public operations of State 5 — named here by
their operation names, with arguments shaped as the State 6 models — without
changing the assertions below. Each test gets a fresh, empty kernel store.

Fixture surface used here:

- ``issue_contract_version(slot_id, purpose, inputs, outputs)`` ->
  contract_version_id (acts as agent ``author``; bounds within the ceilings);
  ``read_contract_version(contract_version_id)`` -> ContractVersion;
- ``add_trial_case(contract_version_id, inputs, expected_outputs)`` ->
  ShownAddedTrialCase (acts as agent ``author``);
- ``compose_flow_version(flow_id, purpose, inputs, outputs, nodes, edges,
  constants)`` -> ComposedFlowVersion;
- ``page_records(record_type, record_filter, page_size)`` -> RecordPageAnswer;
- capabilities: ``restart()``, ``start_second_kernel()``, ``data_directory``,
  ``value_file(value_digest)`` (the path, relative to ``data_directory``, at
  which the store publishes the value bytes of that digest — requested here),
  ``faults.place_symlink``, ``kernel_sources()``.
"""

import ast
import hashlib
import re
from pathlib import PurePosixPath

import pytest

TEXT = '{"type":"string"}'

DATABASE_DRIVERS = ("sqlite3", "apsw", "sqlalchemy", "aiosqlite", "pysqlite2")
DATABASE_CALLS = (
    "execute",
    "executemany",
    "executescript",
    "cursor",
    "isolation_level",
    "in_transaction",
)
# A connection's `commit()` / `rollback()` take no argument; a call with one
# (a version-control `repo.commit(revision)`) is not a database transaction.
TRANSACTION_CALLS = ("commit", "rollback")
# A transaction statement is the whole SQL text, in upper case; a docstring
# that merely starts with "Begin ..." or "Commit ...", or a git object type
# "commit", is not one. (A module that sends SQL also needs `.execute`.)
TRANSACTION_SQL = re.compile(
    r"\s*(BEGIN(\s+(DEFERRED|IMMEDIATE|EXCLUSIVE))?(\s+TRANSACTION)?"
    r"|COMMIT(\s+TRANSACTION)?|END\s+TRANSACTION"
    r"|ROLLBACK(\s+TRANSACTION)?(\s+TO(\s+SAVEPOINT)?\s+\w+)?"
    r"|SAVEPOINT\s+\w+|RELEASE\s+SAVEPOINT\s+\w+)\s*;?\s*"
)


def _port(name, direction, schema, disclosure_class=None):
    return {
        "name": name,
        "direction": direction,
        "value_schema": schema,
        "carriage": "value",
        "media_type": None,
        "cardinality": "one",
        "disclosure_class": disclosure_class,
    }


def _function(semantic_runtime, slot_id):
    """A function of one text input `x` and one text output `y`."""
    return semantic_runtime.issue_contract_version(
        slot_id,
        purpose=f"A18 witness: {slot_id}",
        inputs=[_port("x", "input", TEXT, "open")],
        outputs=[_port("y", "output", TEXT)],
    )


def _node(node_id, contract_version_id):
    return {
        "node_id": node_id,
        "kind": "function",
        "contract_version_id": contract_version_id,
        "binding_id": None,
        "map_over": None,
    }


def _edge(from_node, from_port, to_node, to_port):
    return {
        "from_node": from_node,
        "from_port": from_port,
        "to_node": to_node,
        "to_port": to_port,
        "guard": None,
    }


def _text_value(text):
    """(json_text, canonical bytes, value_digest) of one ASCII JSON string.

    An ASCII string without quote, backslash or control characters is its own
    RFC 8785 form; the digest is the lowercase hex SHA-256 of the canonical
    bytes (State 1, M21 `value_digest`).
    """
    json_text = '"' + text + '"'
    canonical = json_text.encode("ascii")
    return json_text, canonical, hashlib.sha256(canonical).hexdigest()


def _case(semantic_runtime, contract_version_id, json_text, expected=None):
    return semantic_runtime.add_trial_case(
        contract_version_id,
        inputs=[{"payload_kind": "json", "port": "x", "json_text": json_text}],
        expected_outputs=(
            None
            if expected is None
            else [{"payload_kind": "json", "port": "y", "json_text": expected}]
        ),
    )


def _cases_of(semantic_runtime, contract_version_id):
    page = semantic_runtime.page_records(
        "trial_case",
        {
            "filter_kind": "equals",
            "field": "contract_version_id",
            "value": contract_version_id,
        },
        page_size=200,
    )
    return page.records.trial_cases


def _published(semantic_runtime, value_digest):
    return semantic_runtime.data_directory / semantic_runtime.value_file(value_digest)


def _is_store_module(module_path):
    parts = PurePosixPath(str(module_path).replace("\\", "/")).with_suffix("").parts
    return "store" in parts


def _database_uses(source):
    """Names, calls and SQL texts by which a module touches the database."""
    found = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] in DATABASE_DRIVERS:
                    found.append(f"import {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            if (node.module or "").split(".")[0] in DATABASE_DRIVERS:
                found.append(f"from {node.module} import")
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in TRANSACTION_CALLS and not node.args and not node.keywords:
                found.append(f".{node.func.attr}()")
        elif isinstance(node, ast.Attribute):
            if node.attr in DATABASE_CALLS or "transaction" in node.attr.lower():
                found.append(f".{node.attr}")
        elif isinstance(node, ast.Name):
            if "transaction" in node.id.lower():
                found.append(node.id)
        elif isinstance(node, ast.arg):
            if "transaction" in node.arg.lower():
                found.append(f"parameter {node.arg}")
        elif isinstance(node, ast.keyword):
            if node.arg and "transaction" in node.arg.lower():
                found.append(f"keyword {node.arg}")
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if "transaction" in node.name.lower():
                found.append(f"def {node.name}")
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            if TRANSACTION_SQL.fullmatch(node.value):
                found.append(f"sql {node.value.strip()[:20]!r}")
    return found


def test_single_process_lock(semantic_runtime):
    """[witness: verification:kernel_a18_single_process_lock]

    A18 Required test 1: a second kernel on the same data directory refuses to
    start.
    """
    contract_version_id = _function(semantic_runtime, "a18_lock")

    # A18 rule 1: the running kernel holds the exclusive lock.
    second = semantic_runtime.start_second_kernel()
    assert second.started is False
    assert second.exit_code not in (None, 0)

    # The first kernel keeps answering, its records untouched.
    kept = semantic_runtime.read_contract_version(contract_version_id)
    assert kept.contract_version_id == contract_version_id

    # Control: once the first process has stopped, a start on the same data
    # directory and configuration succeeds — the refusal came from the lock.
    assert semantic_runtime.restart().started is True
    again = semantic_runtime.read_contract_version(contract_version_id)
    assert again.contract_version_id == contract_version_id


def test_symlink_in_data_dir_refused(semantic_runtime, tmp_path):
    """[witness: verification:kernel_a18_symlink_in_data_dir_refused]

    A18 Required test 4: a symbolic link in the value area stops the start; one
    placed there after the start makes the store call that meets it fail with
    nothing written.
    """
    contract_version_id = _function(semantic_runtime, "a18_symlink")
    first_text, first_bytes, first_digest = _text_value("a18-symlink-first")
    _case(semantic_runtime, contract_version_id, first_text)
    assert _published(semantic_runtime, first_digest).read_bytes() == first_bytes

    # Control: before any link exists, this data directory starts.
    assert semantic_runtime.restart().started is True

    # A link placed after the start, at the path the next value is published
    # under, pointing outside the data directory.
    second_text, _, second_digest = _text_value("a18-symlink-second")
    outside = tmp_path / "outside_target"
    link = _published(semantic_runtime, second_digest)
    semantic_runtime.faults.place_symlink(
        semantic_runtime.value_file(second_digest), str(outside)
    )
    assert link.is_symlink()

    # A18 rule 2: the store call that meets it fails with nothing written
    # (State 5 `put_value_bytes`: a link is `internal_error`, nothing published).
    with pytest.raises(Exception) as exc:
        _case(semantic_runtime, contract_version_id, second_text)
    assert exc.value.code == "internal_error"
    # Nothing written through the link, and the link not replaced by a
    # published file. (80_notes.md `serve_kernel`: the process then ends, and
    # with the link in place no start can follow to read the records.)
    assert not outside.exists()
    assert link.is_symlink()
    assert _published(semantic_runtime, first_digest).read_bytes() == first_bytes

    # A18 rule 2: a link found at start stops the start.
    stopped = semantic_runtime.restart()
    assert stopped.started is False
    assert stopped.exit_code not in (None, 0)
    assert not outside.exists()
    assert link.is_symlink()


def test_store_module_sole_transaction_owner(semantic_runtime):
    """[witness: verification:kernel_a18_store_module_sole_transaction_owner]

    A18 Required test 6: no module other than the store module opens the
    database or opens, names or passes a transaction.
    """
    sources = semantic_runtime.kernel_sources()
    store_modules = [path for path in sources if _is_store_module(path)]
    assert store_modules, "the kernel has a store module"

    # A18 rule 3: only the store module opens the database; callers never open,
    # name or pass a transaction (K-17).
    offenders = {
        path: uses
        for path, source in sources.items()
        if not _is_store_module(path)
        for uses in [_database_uses(source)]
        if uses
    }
    assert offenders == {}

    # Control: the scan does see database access where it exists — in the
    # store module.
    assert any(_database_uses(sources[path]) for path in store_modules)
