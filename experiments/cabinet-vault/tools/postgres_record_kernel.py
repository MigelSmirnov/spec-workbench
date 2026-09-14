#!/usr/bin/env python3
"""Generic PostgreSQL record/transaction/locking/audit provider for the Cabinet host experiment."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import json
from typing import Any, Iterator


class PostgresRecordKernelError(RuntimeError):
    pass


def _psycopg():
    try:
        import psycopg  # type: ignore
        from psycopg import sql  # type: ignore
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise PostgresRecordKernelError("psycopg is required for postgres_record_kernel") from exc
    return psycopg, sql


def _jsonb(value: dict[str, Any]):
    try:
        from psycopg.types.json import Jsonb  # type: ignore
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise PostgresRecordKernelError("psycopg JSONB support is required") from exc
    return Jsonb(value)


def _resource_lock_identity(namespace: str, resource_id: str) -> str:
    """Encode a composite resource identity as PostgreSQL-safe deterministic text."""
    return json.dumps([namespace, resource_id], ensure_ascii=True, separators=(",", ":"))


@dataclass(frozen=True)
class StoredRecord:
    namespace: str
    resource_id: str
    version: int
    payload: dict[str, Any]


@dataclass(frozen=True)
class AuditEvent:
    event_id: str
    event_type: str
    subject: str
    payload: dict[str, Any]


class RecordTransaction:
    def __init__(self, connection: Any, schema: str):
        self.connection = connection
        self.schema = schema
        self._locked: set[tuple[str, str]] = set()

    def lock_resource(self, namespace: str, resource_id: str) -> None:
        if not namespace or not resource_id:
            raise PostgresRecordKernelError("namespace and resource_id must be non-empty")
        lock_key = _resource_lock_identity(namespace, resource_id)
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))", (lock_key,))
        self._locked.add((namespace, resource_id))

    def get_record(self, namespace: str, resource_id: str) -> StoredRecord | None:
        _, sql = _psycopg()
        with self.connection.cursor() as cursor:
            cursor.execute(
                sql.SQL(
                    "SELECT namespace, resource_id, version, payload "
                    "FROM {}.records WHERE namespace = %s AND resource_id = %s"
                ).format(sql.Identifier(self.schema)),
                (namespace, resource_id),
            )
            row = cursor.fetchone()
        if row is None:
            return None
        return StoredRecord(
            namespace=str(row[0]),
            resource_id=str(row[1]),
            version=int(row[2]),
            payload=dict(row[3]),
        )

    def put_record(
        self,
        namespace: str,
        resource_id: str,
        payload: dict[str, Any],
        *,
        expected_version: int | None = None,
    ) -> StoredRecord:
        if (namespace, resource_id) not in self._locked:
            raise PostgresRecordKernelError("record mutation requires exact resource lock")
        if not isinstance(payload, dict):
            raise PostgresRecordKernelError("record payload must be a mapping")

        current = self.get_record(namespace, resource_id)
        current_version = None if current is None else current.version
        if expected_version is not None and current_version != expected_version:
            raise PostgresRecordKernelError(
                f"version conflict: expected {expected_version}, observed {current_version}"
            )
        next_version = 1 if current is None else current.version + 1

        _, sql = _psycopg()
        with self.connection.cursor() as cursor:
            cursor.execute(
                sql.SQL(
                    "INSERT INTO {}.records(namespace, resource_id, version, payload) "
                    "VALUES (%s, %s, %s, %s) "
                    "ON CONFLICT(namespace, resource_id) DO UPDATE SET "
                    "version = EXCLUDED.version, payload = EXCLUDED.payload, updated_at = now()"
                ).format(sql.Identifier(self.schema)),
                (namespace, resource_id, next_version, _jsonb(payload)),
            )
        return StoredRecord(namespace, resource_id, next_version, dict(payload))

    def append_audit(
        self,
        event_id: str,
        event_type: str,
        subject: str,
        payload: dict[str, Any],
    ) -> None:
        if not event_id or not event_type or not subject:
            raise PostgresRecordKernelError("audit identity, event_type, and subject must be non-empty")
        if not isinstance(payload, dict):
            raise PostgresRecordKernelError("audit payload must be a mapping")
        _, sql = _psycopg()
        with self.connection.cursor() as cursor:
            cursor.execute(
                sql.SQL(
                    "INSERT INTO {}.audit_events(event_id, event_type, subject, payload) "
                    "VALUES (%s, %s, %s, %s)"
                ).format(sql.Identifier(self.schema)),
                (event_id, event_type, subject, _jsonb(payload)),
            )


class PostgresRecordKernel:
    """Small generic provider for records, exact-resource locking, and append-only audit."""

    def __init__(self, dsn: str, *, schema: str):
        if not dsn:
            raise PostgresRecordKernelError("PostgreSQL DSN must be non-empty")
        if not schema or not schema.replace("_", "").isalnum():
            raise PostgresRecordKernelError("schema must contain only letters, digits, and underscores")
        self.dsn = dsn
        self.schema = schema

    def connect(self):
        psycopg, _ = _psycopg()
        return psycopg.connect(self.dsn)

    def initialize(self) -> None:
        _, sql = _psycopg()
        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(sql.Identifier(self.schema))
                )
                cursor.execute(
                    sql.SQL(
                        "CREATE TABLE IF NOT EXISTS {}.records ("
                        "namespace text NOT NULL, "
                        "resource_id text NOT NULL, "
                        "version bigint NOT NULL CHECK (version > 0), "
                        "payload jsonb NOT NULL, "
                        "updated_at timestamptz NOT NULL DEFAULT now(), "
                        "PRIMARY KEY(namespace, resource_id))"
                    ).format(sql.Identifier(self.schema))
                )
                cursor.execute(
                    sql.SQL(
                        "CREATE TABLE IF NOT EXISTS {}.audit_events ("
                        "sequence_id bigserial PRIMARY KEY, "
                        "event_id text NOT NULL UNIQUE, "
                        "event_type text NOT NULL, "
                        "subject text NOT NULL, "
                        "payload jsonb NOT NULL, "
                        "occurred_at timestamptz NOT NULL DEFAULT now())"
                    ).format(sql.Identifier(self.schema))
                )
                function_name = f"{self.schema}_reject_audit_mutation"
                cursor.execute(
                    sql.SQL(
                        "CREATE OR REPLACE FUNCTION {}.{}() RETURNS trigger "
                        "LANGUAGE plpgsql AS $$ BEGIN "
                        "RAISE EXCEPTION 'audit_events is append-only'; END; $$"
                    ).format(sql.Identifier(self.schema), sql.Identifier(function_name))
                )
                cursor.execute(
                    sql.SQL("DROP TRIGGER IF EXISTS reject_audit_mutation ON {}.audit_events").format(
                        sql.Identifier(self.schema)
                    )
                )
                cursor.execute(
                    sql.SQL(
                        "CREATE TRIGGER reject_audit_mutation "
                        "BEFORE UPDATE OR DELETE ON {}.audit_events "
                        "FOR EACH ROW EXECUTE FUNCTION {}.{}()"
                    ).format(
                        sql.Identifier(self.schema),
                        sql.Identifier(self.schema),
                        sql.Identifier(function_name),
                    )
                )

    @contextmanager
    def transaction(self) -> Iterator[RecordTransaction]:
        connection = self.connect()
        try:
            with connection.transaction():
                yield RecordTransaction(connection, self.schema)
        finally:
            connection.close()

    def read_record(self, namespace: str, resource_id: str) -> StoredRecord | None:
        connection = self.connect()
        try:
            return RecordTransaction(connection, self.schema).get_record(namespace, resource_id)
        finally:
            connection.close()

    def read_audit(self) -> tuple[AuditEvent, ...]:
        _, sql = _psycopg()
        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    sql.SQL(
                        "SELECT event_id, event_type, subject, payload "
                        "FROM {}.audit_events ORDER BY sequence_id"
                    ).format(sql.Identifier(self.schema))
                )
                rows = cursor.fetchall()
        return tuple(
            AuditEvent(str(row[0]), str(row[1]), str(row[2]), dict(row[3])) for row in rows
        )

    def drop_probe_schema(self) -> None:
        """Explicit test/probe cleanup; never called by normal host execution."""
        _, sql = _psycopg()
        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(self.schema))
                )
