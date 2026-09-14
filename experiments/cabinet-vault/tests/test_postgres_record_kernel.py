from __future__ import annotations

import pytest

from postgres_record_kernel import (
    PostgresRecordKernel,
    PostgresRecordKernelError,
    RecordTransaction,
    _resource_lock_identity,
)
from postgres_record_kernel_probe import run_probe


def test_provider_rejects_unsafe_schema_identifier_before_connecting():
    with pytest.raises(PostgresRecordKernelError, match="schema"):
        PostgresRecordKernel("postgresql://unused", schema="unsafe-schema")


def test_record_mutation_requires_exact_resource_lock_before_database_access():
    tx = RecordTransaction(connection=None, schema="unused")

    with pytest.raises(PostgresRecordKernelError, match="exact resource lock"):
        tx.put_record("namespace", "resource", {"value": 1})


def test_resource_lock_identity_is_postgresql_text_safe_and_composite_unambiguous():
    key = _resource_lock_identity("namespace\x00with-control", "resource\x00with-control")

    assert "\x00" not in key
    assert "\\u0000" in key
    assert _resource_lock_identity("ab", "c") != _resource_lock_identity("a", "bc")
    assert _resource_lock_identity("a:b", "c") != _resource_lock_identity("a", "b:c")


def test_runtime_probe_without_dsn_fails_closed_instead_of_skipping_to_pass():
    report = run_probe(None)
    by_id = {item.probe_id: item for item in report.results}

    assert report.status == "block"
    assert set(by_id) == {
        "RECORD-PROBE-001",
        "RECORD-PROBE-002",
        "RECORD-PROBE-003",
        "RECORD-PROBE-004",
        "RECORD-PROBE-005",
    }
    assert by_id["RECORD-PROBE-001"].status in {"PASS", "FAIL"}
    assert {
        by_id[probe_id].status
        for probe_id in (
            "RECORD-PROBE-002",
            "RECORD-PROBE-003",
            "RECORD-PROBE-004",
            "RECORD-PROBE-005",
        )
    } == {"UNVERIFIED"}
