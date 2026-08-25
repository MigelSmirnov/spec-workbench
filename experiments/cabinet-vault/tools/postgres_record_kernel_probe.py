#!/usr/bin/env python3
"""Execute the postgres_record_kernel verification packet against a real PostgreSQL runtime."""
from __future__ import annotations

import argparse
import json
import os
import threading
import time
import uuid
from dataclasses import asdict, dataclass
from typing import Callable

from postgres_record_kernel import PostgresRecordKernel


PROBE_SCHEMA_VERSION = "spec_workbench_postgres_record_kernel_probe.v0"
ENV_DSN = "SPEC_WORKBENCH_TEST_POSTGRES_DSN"


@dataclass(frozen=True)
class ProbeResult:
    probe_id: str
    status: str
    message: str


@dataclass(frozen=True)
class ProbeReport:
    schema_version: str
    provider_id: str
    status: str
    probe_schema: str
    results: tuple[ProbeResult, ...]


def _result(probe_id: str, status: str, message: str) -> ProbeResult:
    return ProbeResult(probe_id, status, message)


def _probe_import() -> ProbeResult:
    try:
        import psycopg  # noqa: F401
    except Exception as exc:  # pragma: no cover - runtime evidence
        return _result("RECORD-PROBE-001", "FAIL", f"psycopg import failed: {type(exc).__name__}")
    return _result("RECORD-PROBE-001", "PASS", "psycopg imported in the selected runtime")


def _probe_atomic_commit_rollback(kernel: PostgresRecordKernel) -> ProbeResult:
    try:
        with kernel.transaction() as tx:
            tx.lock_resource("probe", "atomic")
            tx.put_record("probe", "atomic", {"state": "committed"})

        try:
            with kernel.transaction() as tx:
                tx.lock_resource("probe", "atomic")
                tx.put_record(
                    "probe",
                    "atomic",
                    {"state": "must_rollback"},
                    expected_version=1,
                )
                raise RuntimeError("intentional probe rollback")
        except RuntimeError as exc:
            if str(exc) != "intentional probe rollback":
                raise

        record = kernel.read_record("probe", "atomic")
        if record is None or record.version != 1 or record.payload != {"state": "committed"}:
            return _result(
                "RECORD-PROBE-002",
                "FAIL",
                "rolled-back transaction changed committed record state",
            )
    except Exception as exc:  # pragma: no cover - runtime evidence
        return _result("RECORD-PROBE-002", "FAIL", f"transaction probe failed: {type(exc).__name__}: {exc}")
    return _result(
        "RECORD-PROBE-002",
        "PASS",
        "committed transaction persisted and intentional failure rolled back",
    )


def _probe_exact_resource_lock(kernel: PostgresRecordKernel) -> ProbeResult:
    holder_ready = threading.Event()
    release_holder = threading.Event()
    contender_started = threading.Event()
    contender_acquired = threading.Event()
    errors: list[str] = []

    def holder() -> None:
        try:
            with kernel.transaction() as tx:
                tx.lock_resource("probe", "locked-resource")
                holder_ready.set()
                if not release_holder.wait(5):
                    raise RuntimeError("holder timed out waiting for release")
        except Exception as exc:  # pragma: no cover - runtime evidence
            errors.append(f"holder:{type(exc).__name__}:{exc}")
            holder_ready.set()
            release_holder.set()

    def contender() -> None:
        try:
            if not holder_ready.wait(5):
                raise RuntimeError("contender did not observe holder")
            with kernel.transaction() as tx:
                contender_started.set()
                tx.lock_resource("probe", "locked-resource")
                contender_acquired.set()
        except Exception as exc:  # pragma: no cover - runtime evidence
            errors.append(f"contender:{type(exc).__name__}:{exc}")
            contender_started.set()

    holder_thread = threading.Thread(target=holder, name="record-kernel-holder")
    contender_thread = threading.Thread(target=contender, name="record-kernel-contender")
    holder_thread.start()
    if not holder_ready.wait(5):
        release_holder.set()
        holder_thread.join(timeout=5)
        return _result("RECORD-PROBE-003", "FAIL", "holder did not acquire resource lock")

    contender_thread.start()
    if not contender_started.wait(5):
        release_holder.set()
        holder_thread.join(timeout=5)
        contender_thread.join(timeout=5)
        return _result("RECORD-PROBE-003", "FAIL", "contender did not reach lock attempt")

    time.sleep(0.25)
    same_resource_blocked = not contender_acquired.is_set()

    different_resource_acquired = False
    try:
        with kernel.transaction() as tx:
            tx.lock_resource("probe", "different-resource")
            different_resource_acquired = True
    except Exception as exc:  # pragma: no cover - runtime evidence
        errors.append(f"different:{type(exc).__name__}:{exc}")

    release_holder.set()
    holder_thread.join(timeout=5)
    contender_thread.join(timeout=5)

    if holder_thread.is_alive() or contender_thread.is_alive():
        return _result("RECORD-PROBE-003", "FAIL", "lock probe threads did not terminate")
    if errors:
        return _result("RECORD-PROBE-003", "FAIL", "; ".join(errors))
    if not same_resource_blocked:
        return _result("RECORD-PROBE-003", "FAIL", "conflicting exact-resource lock did not block")
    if not different_resource_acquired:
        return _result("RECORD-PROBE-003", "FAIL", "unrelated resource lock was unnecessarily blocked")
    if not contender_acquired.is_set():
        return _result("RECORD-PROBE-003", "FAIL", "contender never acquired lock after release")
    return _result(
        "RECORD-PROBE-003",
        "PASS",
        "same resource serialized while unrelated resource remained independently lockable",
    )


def _probe_no_partial_state(kernel: PostgresRecordKernel) -> ProbeResult:
    event_id = f"partial-{uuid.uuid4().hex}"
    try:
        try:
            with kernel.transaction() as tx:
                tx.lock_resource("probe", "partial")
                tx.put_record("probe", "partial", {"state": "must_not_publish"})
                tx.append_audit(event_id, "probe.partial", "probe:partial", {"state": "pending"})
                raise RuntimeError("intentional partial-state failure")
        except RuntimeError as exc:
            if str(exc) != "intentional partial-state failure":
                raise

        record = kernel.read_record("probe", "partial")
        audit_ids = {item.event_id for item in kernel.read_audit()}
        if record is not None or event_id in audit_ids:
            return _result(
                "RECORD-PROBE-004",
                "FAIL",
                "failed transaction exposed partial record or audit state",
            )
    except Exception as exc:  # pragma: no cover - runtime evidence
        return _result("RECORD-PROBE-004", "FAIL", f"partial-state probe failed: {type(exc).__name__}: {exc}")
    return _result(
        "RECORD-PROBE-004",
        "PASS",
        "failed transaction exposed neither record nor audit state",
    )


def _probe_append_only_audit(kernel: PostgresRecordKernel) -> ProbeResult:
    event_id = f"append-only-{uuid.uuid4().hex}"
    try:
        import psycopg  # type: ignore
        from psycopg import sql  # type: ignore

        with kernel.transaction() as tx:
            tx.append_audit(event_id, "probe.append_only", "probe:audit", {"original": True})

        update_blocked = False
        try:
            with kernel.connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        sql.SQL("UPDATE {}.audit_events SET subject = %s WHERE event_id = %s").format(
                            sql.Identifier(kernel.schema)
                        ),
                        ("changed", event_id),
                    )
        except psycopg.Error:
            update_blocked = True

        delete_blocked = False
        try:
            with kernel.connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        sql.SQL("DELETE FROM {}.audit_events WHERE event_id = %s").format(
                            sql.Identifier(kernel.schema)
                        ),
                        (event_id,),
                    )
        except psycopg.Error:
            delete_blocked = True

        events = [item for item in kernel.read_audit() if item.event_id == event_id]
        unchanged = (
            len(events) == 1
            and events[0].subject == "probe:audit"
            and events[0].payload == {"original": True}
        )
        if not (update_blocked and delete_blocked and unchanged):
            return _result(
                "RECORD-PROBE-005",
                "FAIL",
                "audit row was mutable, deletable, duplicated, or changed",
            )
    except Exception as exc:  # pragma: no cover - runtime evidence
        return _result("RECORD-PROBE-005", "FAIL", f"append-only probe failed: {type(exc).__name__}: {exc}")
    return _result(
        "RECORD-PROBE-005",
        "PASS",
        "audit insert persisted while direct UPDATE and DELETE were rejected",
    )


def run_probe(dsn: str | None, *, keep_schema: bool = False) -> ProbeReport:
    import_result = _probe_import()
    schema = f"spec_workbench_probe_{uuid.uuid4().hex[:12]}"
    results: list[ProbeResult] = [import_result]

    if import_result.status != "PASS":
        results.extend(
            _result(probe_id, "UNVERIFIED", "provider probe blocked by psycopg import failure")
            for probe_id in (
                "RECORD-PROBE-002",
                "RECORD-PROBE-003",
                "RECORD-PROBE-004",
                "RECORD-PROBE-005",
            )
        )
        return ProbeReport(PROBE_SCHEMA_VERSION, "postgres_record_kernel", "block", schema, tuple(results))

    if not dsn:
        results.extend(
            _result(probe_id, "UNVERIFIED", f"set {ENV_DSN} or pass --dsn to execute runtime probe")
            for probe_id in (
                "RECORD-PROBE-002",
                "RECORD-PROBE-003",
                "RECORD-PROBE-004",
                "RECORD-PROBE-005",
            )
        )
        return ProbeReport(PROBE_SCHEMA_VERSION, "postgres_record_kernel", "block", schema, tuple(results))

    kernel = PostgresRecordKernel(dsn, schema=schema)
    try:
        kernel.initialize()
    except Exception as exc:  # pragma: no cover - runtime evidence
        results.extend(
            _result(probe_id, "UNVERIFIED", f"provider initialization failed: {type(exc).__name__}: {exc}")
            for probe_id in (
                "RECORD-PROBE-002",
                "RECORD-PROBE-003",
                "RECORD-PROBE-004",
                "RECORD-PROBE-005",
            )
        )
        return ProbeReport(PROBE_SCHEMA_VERSION, "postgres_record_kernel", "block", schema, tuple(results))

    probes: tuple[Callable[[PostgresRecordKernel], ProbeResult], ...] = (
        _probe_atomic_commit_rollback,
        _probe_exact_resource_lock,
        _probe_no_partial_state,
        _probe_append_only_audit,
    )
    try:
        results.extend(probe(kernel) for probe in probes)
    finally:
        if not keep_schema:
            try:
                kernel.drop_probe_schema()
            except Exception as exc:  # pragma: no cover - runtime evidence
                results.append(
                    _result("PROBE-CLEANUP", "FAIL", f"probe schema cleanup failed: {type(exc).__name__}: {exc}")
                )

    status = "pass" if all(item.status == "PASS" for item in results) else "block"
    return ProbeReport(PROBE_SCHEMA_VERSION, "postgres_record_kernel", status, schema, tuple(results))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dsn", default=os.environ.get(ENV_DSN))
    parser.add_argument("--keep-schema", action="store_true")
    args = parser.parse_args(argv)

    report = run_probe(args.dsn, keep_schema=args.keep_schema)
    print(json.dumps(asdict(report), indent=2, sort_keys=True))
    return 0 if report.status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
