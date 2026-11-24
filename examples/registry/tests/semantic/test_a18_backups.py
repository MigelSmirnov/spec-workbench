"""Witness tests for accepted decision A18 (02_rules_installation.md).

Daily encrypted backups, checked when made, kept 30 days: one run a date, at
the first look at or after 03:00 UTC of a date an earlier look of the same
process saw before 03:00; a backup is one snapshot of the store, as one read
transaction sees it, while writes go on; it holds every record but the agent
sessions; its first line is a record readable without the key — instant,
release, last audit sequence number, key digest; it is checked by decrypting
it and is kept only when the check passes; every run deletes the kept backups
made more than 720 hours before the instant its third step starts, compared
to the microsecond. Each test carries the witness name its Required test
declares; Required test 6, untagged, runs as an ordinary test.

The Factory project ``registry`` supplies the ``semantic_runtime`` pytest
fixture (``RUNTIME_SURFACE.md``). Each test gets a fresh instance: an empty
store, an empty backup location, both listeners, the clock at
2026-01-05T09:00:00Z. Passes run only when asked.

Fixture surface used here:

- ``owner(action, target=None, stated_version=None, **values)`` -> answer, in
  the held owner session (``create_project``, ``answer_access_request``,
  ``read_project``, ``list_sessions``, ``erase_audit_entries``); ``sign_in()``
  after each move of the clock past the 30 idle minutes (A13 rule 2;
  RUNTIME_SURFACE.md "The owner's session");
- ``service(name, operation, inputs=None, kernel_session=None)`` -> answer
  (Kernel's ``register_agent_session``, ``request_project_access``,
  ``read_session_access``);
- ``new_request_id()``;
- capabilities: ``configure(**settings)``, ``start()``, ``stop()``,
  ``clock.set``, ``run_backup_look()``, ``backup_files()``,
  ``backup_bytes(name)`` (the file's raw bytes), ``read_backup(name,
  key=None)`` -> ``{table: rows}`` (decrypted with the configured key or
  ``key=``), ``store_rows(table)``, ``diagnostics()`` (the lines the
  instance wrote to its standard error), ``restore(name)``,
  ``faults.fail_next_backup_check(kind)`` and
  ``faults.hold_backup_snapshot()`` (RUNTIME_SURFACE.md, "Capabilities").
"""

import hashlib
import json
import threading
from datetime import date, datetime, timedelta, timezone

UTC = timezone.utc

# Data provider constants (70_data_provider_closure.json), as the backup code
# imports them (A18 rules 4, 5; SPEC_STANDARD §15.3.1).
BACKUP_KEPT_PREFIX = "registry-backup-"
BACKUP_TEMPORARY_PREFIX = "registry-tmp-"
BACKUP_RETENTION_HOURS = 720
BACKUP_RECORD_VERSION = 1
BACKUP_KEY_DIGEST_DOMAIN = "registry-backup-key-digest-v1"
RELEASE_VERSION = "registry-2.0.0"

# State 6, "The store's rows" (70_persistence_closure.json): the eight tables.
TABLES = (
    "project_rows",
    "room_rows",
    "customer_rows",
    "pointer_rows",
    "agent_session_rows",
    "audit_entry_rows",
    "migration_closure_rows",
    "audit_sequence_rows",
)

# Two backup keys of more than the imported SECRET_MIN_BYTES (32) bytes
# (A17 rule 1, RuntimeSettings.backup_key).
KEY_ONE = "a18-backup-key-one-0123456789abcdefghijklmnop"
KEY_TWO = "a18-backup-key-two-0123456789abcdefghijklmnop"

KERNEL = "cabinet_kernel"
WAIT_SECONDS = 30


# --- time -----------------------------------------------------------------


def _iso(instant):
    """An instant as ISO text in UTC with `Z`, to the microsecond (L16)."""
    return instant.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _instant(text):
    return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(UTC)


def _at(day, hour, minute=0, second=0, microsecond=0):
    return datetime(day.year, day.month, day.day, hour, minute, second, microsecond, UTC)


def _arm_date(rt, day):
    """A look that sees `day` before 03:00 (A18 rule 1: a date's run needs an
    earlier look of the same process that saw that date before 03:00)."""
    rt.clock.set(_iso(_at(day, 2, 59)))
    rt.run_backup_look()


def _backup_at(rt, day, microsecond=0):
    """The run of `day`: a look at 02:59, then the first look at or after
    03:00 — BACKUP_DAILY_TIME_UTC "03:00" (A18 rule 1) — at 03:00 and
    `microsecond`. The fixture's clock does not move by itself, so the
    snapshot's instant and the third step's instant are both that look's.
    Returns the look's instant."""
    _arm_date(rt, day)
    instant = _at(day, 3, 0, 0, microsecond)
    rt.clock.set(_iso(instant))
    rt.run_backup_look()
    return instant


# --- the backup location ----------------------------------------------------


def _record(rt, name):
    """The record of a backup file: its first line, one JSON object readable
    without the key (State 6, "A backup file"; A18 rule 1)."""
    first_line = rt.backup_bytes(name).split(b"\n", 1)[0]
    return json.loads(first_line.decode("utf-8"))


def _kept(rt):
    """Kept backups by their recorded instant: files under the kept prefix
    whose record can be read (A18 rule 5)."""
    kept = {}
    for name in rt.backup_files():
        if name.startswith(BACKUP_KEPT_PREFIX):
            kept[_instant(_record(rt, name)["made_at"])] = name
    return kept


def _temporary(rt):
    return [n for n in rt.backup_files() if n.startswith(BACKUP_TEMPORARY_PREFIX)]


def _key_digest(key):
    # State 6, "A backup file": `sha256:` and the lowercase hex SHA-256 of
    # BACKUP_KEY_DIGEST_DOMAIN's bytes, a zero byte and the key's UTF-8 bytes.
    data = BACKUP_KEY_DIGEST_DOMAIN.encode("utf-8") + b"\x00" + key.encode("utf-8")
    return "sha256:" + hashlib.sha256(data).hexdigest()


# --- store rows -------------------------------------------------------------


def _json(value):
    return json.loads(value) if isinstance(value, (str, bytes)) else value


def _last_sequence(rows):
    """M12 AuditSequence's last number in a store's rows (one row)."""
    sequence_rows = rows["audit_sequence_rows"]
    assert len(sequence_rows) == 1  # M12: exactly one per store
    return sequence_rows[0]["last_sequence_number"]


def _store(rt):
    return {table: rt.store_rows(table) for table in TABLES}


def _project_ids(rows):
    return sorted(r["project_id"] for r in rows["project_rows"])


def _created_entries(rows):
    """Entries of `project_created` (OWNER_AUDIT_ACTIONS row of create_project)."""
    return [
        r for r in rows["audit_entry_rows"]
        if _json(r["record"])["action"] == "project_created"
    ]


def _assert_one_snapshot(rows, record):
    """A backup's rows hold no part of a transaction and its record names the
    snapshot (A18 rule 1, A18-2): every created project with its entry, every
    entry with its project, the counter at the highest entry, the record's
    number the counter's."""
    entries = _created_entries(rows)
    assert len(entries) == len(rows["project_rows"])
    numbers = [r["sequence_number"] for r in rows["audit_entry_rows"]]
    assert _last_sequence(rows) == (max(numbers) if numbers else 0)
    assert record["last_sequence_number"] == _last_sequence(rows)


# --- records ----------------------------------------------------------------


def _create_project(rt, name):
    """An owner create: one Project and its one `project_created` entry in one
    transaction (A04 rule 4, A14 rule 1, OWNER_AUDIT_ACTIONS)."""
    answer = rt.owner(
        "create_project",
        request_id=rt.new_request_id(),
        project={"display_name": name, "address": f"Calle {name} 1"},
    )
    assert answer["answer_kind"] == "project_card"
    return answer["card"]["project_id"]


def _in_thread(fn):
    result = {}

    def run():
        try:
            result["value"] = fn()
        except BaseException as error:  # handed to the test thread
            result["error"] = error

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    return thread, result


def _start_with_key(rt, key):
    """(Re)start the instance with a known backup key, store and backup
    location kept (RuntimeSettings.backup_key; A17 rule 1)."""
    rt.stop()
    rt.configure(backup_key=key)
    assert rt.start() is None


def _diagnostics(rt):
    return list(rt.diagnostics())


# --- tests ------------------------------------------------------------------


def test_backup_during_write_is_one_snapshot(semantic_runtime):
    """A backup taken during a write holds the store before or after it, never
    in between; the write is neither refused nor held by the copy (A18 rule 1,
    A18-2)."""
    rt = semantic_runtime
    first = _create_project(rt, "Uno")
    day = date(2026, 1, 6)
    _arm_date(rt, day)
    rt.sign_in()  # past the 30 idle minutes: a new owner session (A13 rule 2)

    gate = rt.faults.hold_backup_snapshot()
    try:
        rt.clock.set(_iso(_at(day, 3)))
        look, look_result = _in_thread(rt.run_backup_look)
        # The copy's first read — the audit counter — has fixed its snapshot.
        assert gate.wait_fixed(timeout=WAIT_SECONDS)

        # A write while the copy holds its snapshot completes: "No write is
        # refused or fails because a copy is being made" (A18 rule 1; State 6
        # "The journal": neither waits for the other).
        writer, written = _in_thread(lambda: _create_project(rt, "Dos"))
        writer.join(WAIT_SECONDS)
        assert not writer.is_alive(), "a write waited for the backup's copy"
        assert "error" not in written, written.get("error")
        second = written["value"]
    finally:
        gate.release()
    look.join(WAIT_SECONDS)
    assert not look.is_alive() and "error" not in look_result

    kept = _kept(rt)
    assert list(kept) == [_at(day, 3)]
    name = kept[_at(day, 3)]
    record = _record(rt, name)
    rows = rt.read_backup(name)

    # The snapshot was fixed before the write committed: the store as it was,
    # the record naming that snapshot's number (A18 rule 1: "a change committed
    # after it is not in this backup").
    assert _project_ids(rows) == [first]
    assert record["last_sequence_number"] == 1
    _assert_one_snapshot(rows, record)

    # Control: the write is in the store, and the next backup holds it.
    live = _store(rt)
    assert _project_ids(live) == sorted([first, second])
    assert _last_sequence(live) == 2
    next_day = date(2026, 1, 7)
    _backup_at(rt, next_day)
    later_name = _kept(rt)[_at(next_day, 3)]
    later_rows = rt.read_backup(later_name)
    assert _project_ids(later_rows) == sorted([first, second])
    _assert_one_snapshot(later_rows, _record(rt, later_name))

    # Writes running all through an ungated run: whichever moment the copy
    # takes, its rows are one snapshot.
    stop = threading.Event()

    def keep_writing():
        n = 0
        while not stop.is_set():
            n += 1
            _create_project(rt, f"Carga {n}")

    # The day is armed and the owner signed in before the writes start, so
    # the writer's session is not past its 30 idle minutes when the look
    # moves the clock from 02:59 to 03:00 (_backup_at's two steps).
    third_day = date(2026, 1, 8)
    _arm_date(rt, third_day)
    rt.sign_in()  # past the 30 idle minutes: a new owner session (A13 rule 2)
    loader, loaded = _in_thread(keep_writing)
    try:
        rt.clock.set(_iso(_at(third_day, 3)))
        rt.run_backup_look()
    finally:
        stop.set()
        loader.join(WAIT_SECONDS)
    assert "error" not in loaded, loaded.get("error")
    third_name = _kept(rt)[_at(third_day, 3)]
    _assert_one_snapshot(rt.read_backup(third_name), _record(rt, third_name))

    # The backup taken during the write restores to the store before it
    # (Required test 1: "restores either before or after it"): the owner puts
    # it in place of the store (outside Registry, R0-89) and Registry starts
    # over it (A18 rule 8). The restored store holds `first` with its entry
    # and the counter at 1 — not `second`, not a part of its transaction.
    assert rt.restore(name) is None
    restored = _store(rt)
    assert _project_ids(restored) == [first]
    assert _last_sequence(restored) == 1
    _assert_one_snapshot(restored, record)
    # Read back through the surface (a restart ended the owner's session, so
    # the next owner call signs in again): `first` is answered, `second` is
    # unknown — `not_found` / `unknown_project`, stage (3) (State 5, "Closed
    # set of refusal codes"; read_project_card Errors).
    assert rt.owner("read_project", target=first)["card"]["project_id"] == first
    missing = rt.owner("read_project", target=second)
    assert missing["answer_kind"] == "refused", missing
    assert missing["code"] == "not_found"
    assert missing["stage"] == 3
    assert [f["kind"] for f in missing["failures"]] == ["unknown_project"]


def test_failed_backup_still_deletes_old_backups(semantic_runtime):
    """A run whose backup fails its check still runs its third step: backups
    more than 720 hours old are deleted, younger ones kept (A18 rule 4,
    A18-1)."""
    rt = semantic_runtime
    _create_project(rt, "Uno")
    old_day, young_day, failed_day = date(2026, 1, 6), date(2026, 1, 20), date(2026, 2, 6)
    _backup_at(rt, old_day)
    _backup_at(rt, young_day)
    assert list(sorted(_kept(rt))) == [_at(old_day, 3), _at(young_day, 3)]
    before = len(_diagnostics(rt))

    _arm_date(rt, failed_day)
    rt.faults.fail_next_backup_check("integrity")
    rt.clock.set(_iso(_at(failed_day, 3)))
    rt.run_backup_look()

    # The run's own backup failed its check: deleted, not kept (A18 rule 4).
    kept = _kept(rt)
    assert _at(failed_day, 3) not in kept
    assert _temporary(rt) == []
    # Third step "whatever the second step did": cutoff 2026-02-06T03:00Z less
    # 720 h = 2026-01-07T03:00Z; the 2026-01-06 backup is older and deleted,
    # the 2026-01-20 one kept (A18 rule 4, BACKUP_RETENTION_HOURS).
    assert sorted(kept) == [_at(young_day, 3)]
    # The run failed: a diagnostic (A18 rule 5; Conventions, "Diagnostics").
    assert len(_diagnostics(rt)) > before


def test_retention_cutoff_exact_to_microsecond(semantic_runtime):
    """One cutoff, the third step's instant less exactly 720 h; a backup made
    exactly at the cutoff is kept, one a microsecond earlier deleted, the
    fraction of a second compared as it is (A18 rule 4, A18-1)."""
    rt = semantic_runtime
    _create_project(rt, "Uno")
    fraction = 250_000  # a non-zero fraction of a second
    first, second, third = date(2026, 1, 6), date(2026, 1, 7), date(2026, 1, 8)
    for day in (first, second, third):
        _backup_at(rt, day, microsecond=fraction)
    made = {day: _at(day, 3, 0, 0, fraction) for day in (first, second, third)}
    # The records hold the instant to the microsecond (A18 rule 4, L16).
    assert sorted(_kept(rt)) == sorted(made.values())

    # Run at 2026-02-05T03:00:00.250000Z: its cutoff is exactly the first
    # backup's instant — kept (A18 rule 4: "made exactly 30 × 24 hours before
    # it is kept"; "earlier than the cutoff is deleted").
    run_one = _backup_at(rt, date(2026, 2, 5), microsecond=fraction)
    assert run_one - timedelta(hours=BACKUP_RETENTION_HOURS) == made[first]
    kept = _kept(rt)
    assert made[first] in kept and made[second] in kept and made[third] in kept
    assert run_one in kept

    # Run at 2026-02-06T03:00:00.250001Z: cutoff 2026-01-07T03:00:00.250001Z.
    # The second backup is one microsecond earlier — deleted; the first too;
    # the third, a day younger, kept. Truncating either side to the second or
    # to the millisecond would keep the second backup.
    run_two = _backup_at(rt, date(2026, 2, 6), microsecond=fraction + 1)
    assert run_two - timedelta(hours=BACKUP_RETENTION_HOURS) - made[second] == timedelta(
        microseconds=1
    )
    kept = _kept(rt)
    assert made[first] not in kept
    assert made[second] not in kept
    assert made[third] in kept
    assert run_one in kept and run_two in kept


def test_record_matches_snapshot_mismatch_deleted(semantic_runtime):
    """The readable record holds the snapshot's instant, the release, the
    snapshot's last sequence number and the key's digest; a backup whose
    decrypted sequence differs from its record is deleted (A18 rules 1, 4;
    A18-1, A18-2)."""
    rt = semantic_runtime
    _start_with_key(rt, KEY_ONE)
    _create_project(rt, "Uno")
    _create_project(rt, "Dos")
    assert _last_sequence(_store(rt)) == 2  # one entry per create (A14, A15)

    day = date(2026, 1, 6)
    made = _backup_at(rt, day, microsecond=123_456)
    name = _kept(rt)[made]
    record = _record(rt, name)
    # State 6, "A backup file": exactly the five fields, readable without key.
    assert set(record) == {
        "record_version",
        "made_at",
        "release_version",
        "last_sequence_number",
        "key_digest",
    }
    assert record["record_version"] == BACKUP_RECORD_VERSION
    assert _instant(record["made_at"]) == made  # the snapshot's read instant
    assert record["release_version"] == RELEASE_VERSION
    assert record["last_sequence_number"] == 2
    assert record["key_digest"] == _key_digest(KEY_ONE)
    assert _last_sequence(rt.read_backup(name)) == 2

    # The record follows the snapshot, and it is the counter (M12), "whatever
    # the log now holds" (A18 rule 1): a third create (entry 3), then on
    # 2026-01-07 an erasure of every entry before that date, which removes 1–3
    # and writes its own entry 4 (A15 rules 3, 4, 6). The log holds one entry;
    # the next backup records 4.
    rt.sign_in()  # past the 30 idle minutes: a new owner session (A13 rule 2)
    _create_project(rt, "Tres")
    next_day = date(2026, 1, 7)
    rt.clock.set(_iso(_at(next_day, 1)))
    rt.sign_in()  # past the 30 idle minutes: a new owner session (A13 rule 2)
    erased = rt.owner("erase_audit_entries", erase_before=next_day.isoformat())
    assert erased["answer_kind"] != "refused"
    live = _store(rt)
    assert [r["sequence_number"] for r in live["audit_entry_rows"]] == [4]
    assert _last_sequence(live) == 4
    next_made = _backup_at(rt, next_day)
    next_record = _record(rt, _kept(rt)[next_made])
    assert next_record["last_sequence_number"] == 4
    assert _last_sequence(rt.read_backup(_kept(rt)[next_made])) == 4

    # Mismatch: the decrypted copy's counter differs from the record — the
    # check of step 2 fails, the backup is deleted and the run fails (A18
    # rule 4: "the last sequence number it keeps equals the recorded one").
    before = len(_diagnostics(rt))
    mismatch_day = date(2026, 1, 8)
    _arm_date(rt, mismatch_day)
    rt.faults.fail_next_backup_check("sequence_mismatch")
    rt.clock.set(_iso(_at(mismatch_day, 3)))
    rt.run_backup_look()
    kept = _kept(rt)
    assert _at(mismatch_day, 3) not in kept
    assert _temporary(rt) == []
    assert sorted(kept) == [made, next_made]  # the earlier ones stay
    assert len(_diagnostics(rt)) > before


def test_backup_unreadable_without_its_key(semantic_runtime):
    """A backup is encrypted with the key the configuration held at its
    making; it is read with that key and no other; a change of key leaves
    older backups under theirs (A18 rule 3, A18-2)."""
    rt = semantic_runtime
    _start_with_key(rt, KEY_ONE)
    project = _create_project(rt, "Casa Encriptada")
    first = _backup_at(rt, date(2026, 1, 6))
    first_name = _kept(rt)[first]

    # Control: with its key the backup reads, and holds the project.
    assert _project_ids(rt.read_backup(first_name, key=KEY_ONE)) == [project]
    # Without it, it does not read.
    try:
        rt.read_backup(first_name, key=KEY_TWO)
    except Exception:
        pass
    else:
        raise AssertionError("a backup was read with a key it was not made with")

    # Encrypted: the file shows neither the store's plain database header, a
    # stored value, nor the key (State 6, "A backup file": AES-256-GCM; the
    # record holds a digest of the key, "never the key", A18 rule 1).
    raw = rt.backup_bytes(first_name)
    assert b"SQLite format 3" not in raw
    assert b"Casa Encriptada" not in raw
    assert KEY_ONE.encode("utf-8") not in raw
    assert _record(rt, first_name)["key_digest"] == _key_digest(KEY_ONE)

    # The owner changes the key: older backups stay under the key they were
    # made with, named by their digest (A18 rule 3).
    _start_with_key(rt, KEY_TWO)
    second = _backup_at(rt, date(2026, 1, 7))
    kept = _kept(rt)
    assert sorted(kept) == [first, second]
    second_name = kept[second]
    assert _record(rt, second_name)["key_digest"] == _key_digest(KEY_TWO)
    assert _record(rt, first_name)["key_digest"] == _key_digest(KEY_ONE)
    assert _project_ids(rt.read_backup(second_name, key=KEY_TWO)) == [project]
    try:
        rt.read_backup(second_name, key=KEY_ONE)
    except Exception:
        pass
    else:
        raise AssertionError("a backup was read with the key of an older one")
    assert _project_ids(rt.read_backup(first_name, key=KEY_ONE)) == [project]


def test_integrity_failure_deleted_and_reported(semantic_runtime):
    """A backup whose integrity check fails is deleted, never kept, and the
    run writes a diagnostic naming no value; Registry keeps serving and the
    next 03:00 tries again (A18 rules 4, 5; A18-1, A18-2)."""
    rt = semantic_runtime
    _start_with_key(rt, KEY_ONE)
    project = _create_project(rt, "Integridad")

    # Control: an unfaulted run keeps its backup and reports nothing.
    good = _backup_at(rt, date(2026, 1, 6))
    assert list(_kept(rt)) == [good]
    before = _diagnostics(rt)

    bad_day = date(2026, 1, 7)
    _arm_date(rt, bad_day)
    rt.faults.fail_next_backup_check("integrity")
    rt.clock.set(_iso(_at(bad_day, 3)))
    rt.run_backup_look()

    kept = _kept(rt)
    assert _at(bad_day, 3) not in kept  # deleted, not kept
    assert sorted(kept) == [good]
    assert _temporary(rt) == []  # its decrypted copy and itself removed
    reported = _diagnostics(rt)[len(before):]
    assert len(reported) >= 1
    # A diagnostic names the failure and never a value (A17 rule 2, A18 rule 5).
    for line in reported:
        assert KEY_ONE not in line
        assert "Integridad" not in line
        assert project not in line

    # Registry keeps serving, and the next 03:00 tries again (A18 rule 5).
    rt.sign_in()  # past the 30 idle minutes: a new owner session (A13 rule 2)
    assert rt.owner("read_project", target=project)["answer_kind"] == "project_card"
    retry = _backup_at(rt, date(2026, 1, 8))
    assert sorted(_kept(rt)) == [good, retry]


def test_restored_store_holds_no_agent_session(semantic_runtime):
    """A backup holds every record but the agent sessions; a store restored
    from it has no session, so a grant does not come back (A18 rule 2,
    A18-2)."""
    rt = semantic_runtime
    project = _create_project(rt, "Restaurada")
    session = "a18-kernel-session"
    registered = rt.service(KERNEL, "register_agent_session", kernel_session=session)
    assert registered["answer_kind"] != "refused"
    assert rt.service(
        KERNEL, "request_project_access", {"request_text": "Need the project"},
        kernel_session=session,
    )["answer_kind"] == "request_pending"
    access = rt.service(KERNEL, "read_session_access", kernel_session=session)["access"]
    rt.owner(
        "answer_access_request",
        target=session,
        stated_version=access["access_version"],
        access_answer={"answer_kind": "grant", "project_id": project, "make_active": True},
    )
    granted = rt.service(KERNEL, "read_session_access", kernel_session=session)
    assert granted["access"]["granted_project_ids"] == [project]
    # Control: the live store holds the session.
    assert [r["session_id"] for r in rt.store_rows("agent_session_rows")] == [session]

    made = _backup_at(rt, date(2026, 1, 6))
    name = _kept(rt)[made]
    rows = rt.read_backup(name)
    # "A backup holds every record but the agent sessions" (A18 rule 2).
    assert rows["agent_session_rows"] == []
    assert _project_ids(rows) == [project]
    # The grant's entry stays: only sessions are removed from the copy.
    assert len(rows["audit_entry_rows"]) == len(rt.store_rows("audit_entry_rows"))

    # The owner puts the backup in place of the store (outside Registry,
    # R0-89); the restored store starts as any store (A18 rule 8, A17 rule 5).
    assert rt.restore(name) is None
    assert rt.store_rows("agent_session_rows") == []
    refused = rt.service(KERNEL, "read_session_access", kernel_session=session)
    assert refused["answer_kind"] == "refused"
    # An unregistered session: not_found, agent_call_refused, stage (2)
    # (State 5, "Closed set of refusal codes"; A10 rule 3).
    assert refused["code"] == "not_found"
    assert refused["stage"] == 2
    assert [f["kind"] for f in refused["failures"]] == ["agent_call_refused"]
    assert rt.owner("list_sessions")["items"] == []
    # Control: the project came back.
    assert rt.owner("read_project", target=project)["card"]["project_id"] == project
    # Kernel registers again; the owner must grant again (A18 rule 2).
    again = rt.service(KERNEL, "register_agent_session", kernel_session=session)
    assert again["access"]["granted_project_ids"] == []
    assert again["access"]["active_project_id"] is None


def test_missed_backup_while_stopped_not_made_up(semantic_runtime):
    """A 03:00 missed while Registry was stopped makes no backup at the next
    start, nor later in its place; the next one is made at the following
    03:00 (A18 rule 1, Required test 6)."""
    rt = semantic_runtime
    _create_project(rt, "Parada")
    missed = date(2026, 1, 6)
    _arm_date(rt, missed)  # this process saw the date before 03:00
    rt.stop()
    rt.clock.set(_iso(_at(missed, 5)))
    assert rt.start() is None
    rt.run_backup_look()
    rt.clock.set(_iso(_at(missed, 5, 1)))
    rt.run_backup_look()
    rt.clock.set(_iso(_at(missed, 23, 59)))
    rt.run_backup_look()
    # A new process saw no look of that date before 03:00 (A18 rule 1).
    assert _kept(rt) == {}
    assert _temporary(rt) == []

    # Control: the following 03:00 makes the next one, exactly one.
    following = date(2026, 1, 7)
    rt.clock.set(_iso(_at(following, 2, 59)))
    rt.run_backup_look()
    rt.clock.set(_iso(_at(following, 3)))
    rt.run_backup_look()
    rt.clock.set(_iso(_at(following, 3, 1)))
    rt.run_backup_look()
    assert list(_kept(rt)) == [_at(following, 3)]
