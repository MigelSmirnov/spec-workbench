"""Witness tests for accepted decision A15 (02_rules_audit.md).

The audit log is append-only: no action changes an entry, and only the
owner's 'erase audit entries before a date' removes any — every entry whose
instant is before 00:00 UTC of that date, a date not later than today. The
erasure's own entry is written after the removal, in the same transaction,
with the current instant, so it is never removed by the erasure that wrote
it, and it is written even when nothing was removed. Only the owner reads the
log. Sequence numbers are never reused: each entry takes the number after the
last the store's history ever wrote, kept apart from the entries (M12
AuditSequence), in the order the changes were applied, which is the order of
their commits. Each tagged test carries the witness name its Required test
declares.

The Factory project `registry` supplies the ``semantic_runtime`` fixture
(``tests/semantic/RUNTIME_SURFACE.md``): a fresh instance per test, driven
over its two real listeners. Expected values come from State 1 (M09, M12),
State 2 (A15, A14 rules 5, 6, A09 rule 2), State 5
(`50_public_apis_1_foundation.md`: `audit_log.append_audit_entry`,
`audit_log.erase_audit_entries_before`, `audit_log.read_audit_entries`;
`50_public_apis_5_surfaces.md`: `operations.perform_owner_operation`,
`operations.perform_service_operation`, `service_api.serve_service_request`;
"Conventions" — "The action's instant and today" — and "Closed set of
refusal codes" in `50_public_apis_0_conventions.md`), State 6 (`AuditEntry`,
`NoSubject`, `AuditViewAnswer`, `AuditErasedAnswer`,
`ConfirmationStepAnswer`, `AuditErasureInputs`, `OwnerValues.erase_before`;
the tables `audit_entry_rows` and `audit_sequence_rows` of
`70_persistence_closure.json`) and the constants of
`70_data_provider_closure.json` (`SERVICE_RIGHTS`).

Fixture surface used here:

- ``owner(action, target=None, stated_version=None, confirm=True,
  **values)`` -> answer, for `read_audit`, `erase_audit_entries` (confirmed
  by the fixture; ``confirm=False`` returns the step), `create_project`,
  `correct_project`; ``owner_confirm(step)``; ``sign_in()``,
  ``owner_session()``, ``use_owner_session(s)``;
- ``service(name, operation, inputs, kernel_session=…)`` -> answer;
- ``new_request_id()``; ``clock.set``, ``clock.advance``;
- ``store_rows(table)`` for `audit_entry_rows` and `audit_sequence_rows`
  (a row of the latter read by its column `last_sequence_number`);
- ``faults.fail_store_call("insert_audit_entry_row")``: the next insertion
  of an audit entry (`StoreRepository`, ``70_persistence_closure.json``)
  raises, failing its transaction — the last store call of an audited
  action, after the raised counter was written (State 7
  `append_audit_entry`);
- calls from two threads at once (RUNTIME_SURFACE.md "Concurrency"), and
  ``owner_confirm(step)`` submitting in the session the step was shown in;
- ``sign_in()`` after each move of the clock past the 30 idle minutes (A13
  rule 2; RUNTIME_SURFACE.md "The owner's session").
"""

import threading
from datetime import date, datetime, timezone

# 70_data_provider_closure.json
STAGE_AUTHENTICATION = 1  # REFUSAL_STAGE_AUTHENTICATION
STAGE_VALUES = 4  # REFUSAL_STAGE_VALUES
STAGE_VERSION = 5  # REFUSAL_STAGE_VERSION

# The fixture's default start instant (RUNTIME_SURFACE.md, "Time").
DAY_0 = date(2026, 1, 5)
DAY_1 = date(2026, 1, 6)
DAY_2 = date(2026, 1, 7)

ADDRESS = "Calle Mayor 1, Valencia"
SERVICES = ("presupro", "client_portal", "cabinet", "cabinet_kernel")  # ServiceName


def _refusal(answer):
    """(code, stage, kinds) of a refused answer (State 5 closed set)."""
    assert answer["answer_kind"] == "refused", answer
    return (
        answer["code"],
        answer["stage"],
        [f["kind"] for f in answer["failures"]],
    )


def _instant(text):
    """An answer's instant: ISO text in UTC ending in `Z` (RUNTIME_SURFACE)."""
    assert text.endswith("Z"), text
    return datetime.fromisoformat(text[:-1] + "+00:00")


def _start_of(day):
    return datetime(day.year, day.month, day.day, tzinfo=timezone.utc)


def _ok(answer, kind):
    assert answer["answer_kind"] == kind, answer
    return answer


def _log(rt):
    return _ok(rt.owner("read_audit"), "audit_view")["entries"]


def _numbers(entries):
    return [e["sequence_number"] for e in entries]


def _last_sequence_number(rt):
    """M12 AuditSequence as the store holds it: exactly one row."""
    rows = rt.store_rows("audit_sequence_rows")
    assert len(rows) == 1, rows
    return rows[0]["last_sequence_number"]


def _project_facts(display_name):
    return {
        "display_name": display_name,
        "alias": None,
        "customer_ref": None,
        "address": ADDRESS,
        "object_kind": None,
        "floor_area": None,
        "rooms_count": None,
        "floor": None,
    }


def _create_project(rt, display_name="Casa Lopez"):
    answer = rt.owner(
        "create_project",
        request_id=rt.new_request_id(),
        project=_project_facts(display_name),
    )
    return _ok(answer, "project_card")["card"]


def _correct(rt, card, display_name):
    answer = rt.owner(
        "correct_project",
        target=card["project_id"],
        stated_version=card["revision"],
        project=_project_facts(display_name),
    )
    return _ok(answer, "project_card")["card"]


def _erase_before(rt, day):
    return rt.owner("erase_audit_entries", erase_before=day.isoformat())


def _assert_erasure_entry(entry, day):
    # M09: an erasure of old entries names the owner's date, its subject is
    # none, it carries its confirmation id (A15 rule 6, A14 rule 5).
    assert entry["action"] == "audit_entries_erased"
    assert entry["subject"] == {"subject_kind": "none"}
    assert entry["erased_before"] == day.isoformat()
    assert entry["outcome"] == "accepted"
    assert isinstance(entry["confirmation_id"], str) and entry["confirmation_id"]


# --- Required test 1 -------------------------------------------------------


def test_erase_before_today_leaves_only_own_entry(semantic_runtime):
    """A15 rules 3, 4, A15-2: in a log whose entries are all older than
    today, erasing before today removes every one of them and leaves exactly
    the erasure's own entry."""
    rt = semantic_runtime
    card = _create_project(rt)
    card = _correct(rt, card, "Casa Lopez, segunda")
    _correct(rt, card, "Casa Lopez, tercera")
    old = _log(rt)
    assert len(old) == 3
    assert {_instant(e["recorded_at"]).date() for e in old} == {DAY_0}

    rt.clock.advance(days=1)
    rt.sign_in()
    erased = _ok(_erase_before(rt, DAY_1), "audit_erased")
    assert erased["removed"] == 3

    log = _log(rt)
    assert len(log) == 1
    _assert_erasure_entry(log[0], DAY_1)
    assert _instant(log[0]["recorded_at"]).date() == DAY_1
    assert log[0]["sequence_number"] == old[-1]["sequence_number"] + 1
    assert len(rt.store_rows("audit_entry_rows")) == 1


# --- Required test 2 (untagged) --------------------------------------------


def test_erase_before_older_date_removes_nothing_writes_own_entry(semantic_runtime):
    """A15 rule 6, A14 rule 5: erasing before a date older than every entry
    removes none and still writes its own entry with a confirmation id."""
    rt = semantic_runtime
    card = _create_project(rt)
    _correct(rt, card, "Casa Lopez, segunda")
    old = _log(rt)

    erased = _ok(_erase_before(rt, date(2026, 1, 1)), "audit_erased")
    assert erased["removed"] == 0

    log = _log(rt)
    assert log[:2] == old
    assert len(log) == 3
    _assert_erasure_entry(log[-1], date(2026, 1, 1))
    assert log[-1]["sequence_number"] == old[-1]["sequence_number"] + 1


# --- Required test 8 -------------------------------------------------------


def test_erase_at_midnight_keeps_own_entry_boundary(semantic_runtime):
    """A15 rules 3, 4, A15-2, A15-3: at 00:00:00 UTC of today, erasing before
    today removes an entry made a microsecond before and keeps an entry made
    at that instant — the erasure's own, and one written just before it."""
    rt = semantic_runtime
    card = _create_project(rt)  # 2026-01-05T09:00:00Z

    rt.clock.set("2026-01-05T23:59:59.999999Z")
    rt.sign_in()
    card = _correct(rt, card, "Casa Lopez, un microsegundo antes")

    rt.clock.set("2026-01-06T00:00:00Z")
    _correct(rt, card, "Casa Lopez, a medianoche")
    before = _log(rt)
    assert [_instant(e["recorded_at"]) for e in before] == [
        datetime(2026, 1, 5, 9, 0, tzinfo=timezone.utc),
        datetime(2026, 1, 5, 23, 59, 59, 999999, tzinfo=timezone.utc),
        _start_of(DAY_1),
    ]

    erased = _ok(_erase_before(rt, DAY_1), "audit_erased")
    assert erased["removed"] == 2

    log = _log(rt)
    assert log[0] == before[2]  # at 00:00:00, not before it: kept
    assert len(log) == 2
    own = log[1]
    _assert_erasure_entry(own, DAY_1)
    assert _instant(own["recorded_at"]) == _start_of(DAY_1)  # A15-3: >= start
    assert own["sequence_number"] == before[2]["sequence_number"] + 1


# --- Required test 3 (untagged) --------------------------------------------


def test_erase_date_after_today_refused(semantic_runtime):
    """A15 rule 3: a date later than today (the UTC date of the action's
    instant) is refused `invalid_request` (`date_after_today`) and nothing
    is removed or written; today itself is accepted."""
    rt = semantic_runtime
    _create_project(rt)
    rt.clock.set("2026-01-05T23:59:59.999999Z")  # still DAY_0 in UTC
    rt.sign_in()
    log = _log(rt)
    rows = rt.store_rows("audit_entry_rows")
    last = _last_sequence_number(rt)

    refused = _erase_before(rt, DAY_1)
    assert _refusal(refused) == ("invalid_request", STAGE_VALUES, ["date_after_today"])
    assert _log(rt) == log
    assert rt.store_rows("audit_entry_rows") == rows
    assert _last_sequence_number(rt) == last

    # Control: today is not later than today.
    erased = _ok(_erase_before(rt, DAY_0), "audit_erased")
    assert erased["removed"] == 0  # the entry is of DAY_0, not before it
    assert len(_log(rt)) == len(log) + 1


# --- Required test 4 -------------------------------------------------------


def test_next_sequence_follows_erasure_entry(semantic_runtime):
    """A15 rule 5, A15-1: after an erasure the next entry takes the number
    after the erasure entry's; after an erasure that removed every entry,
    the next number still follows the last the history wrote."""
    rt = semantic_runtime
    card = _create_project(rt)
    card = _correct(rt, card, "Casa Lopez, segunda")
    assert _numbers(_log(rt)) == [1, 2]

    rt.clock.advance(days=1)
    rt.sign_in()
    _ok(_erase_before(rt, DAY_1), "audit_erased")
    card = _correct(rt, card, "Casa Lopez, tercera")
    log = _log(rt)
    assert _numbers(log) == [3, 4]
    assert log[0]["action"] == "audit_entries_erased"
    assert log[1]["sequence_number"] == log[0]["sequence_number"] + 1
    assert _last_sequence_number(rt) == 4

    # A later erasure removes the earlier erasure's entry and every other:
    # its own entry is numbered after the last ever written, not after the
    # entries that remain (none) and not by their count.
    rt.clock.advance(days=1)
    rt.sign_in()
    erased = _ok(_erase_before(rt, DAY_2), "audit_erased")
    assert erased["removed"] == 2
    log = _log(rt)
    assert _numbers(log) == [5]
    _assert_erasure_entry(log[0], DAY_2)
    _correct(rt, card, "Casa Lopez, cuarta")
    assert _numbers(_log(rt)) == [5, 6]
    assert _last_sequence_number(rt) == 6


# --- Required test 5 (untagged) --------------------------------------------


def test_no_service_operation_reads_log(semantic_runtime):
    """A15 rule 2, A09 rules 2, 3: no service token has a right to the log:
    asking for it under any of the four tokens is refused at stage (1) as
    outside the service's rights; each token's own reads are answered."""
    rt = semantic_runtime
    card = _create_project(rt)
    pid = card["project_id"]
    _ok(
        rt.service("cabinet_kernel", "register_agent_session", kernel_session="a15-session"),
        "session_access",
    )
    log = _log(rt)

    outside = ("not_permitted", STAGE_AUTHENTICATION, ["outside_service_rights"])
    for name in SERVICES:
        session = "a15-session" if name == "cabinet_kernel" else None
        # The owner action's name and the audit module's operation: neither
        # is a ServiceOperation of SERVICE_RIGHTS (State 5
        # serve_service_request: an unknown name is refused as outside the
        # service's rights).
        for operation in ("read_audit", "read_audit_entries"):
            answer = rt.service(name, operation, {}, kernel_session=session)
            assert _refusal(answer) == outside, (name, operation)
            assert "entries" not in answer
        # Control: a read in the token's own row is answered. For the other
        # services validate_project_reference (in every row of A09 rule 2);
        # Cabinet Kernel acts for its agent session, which holds no project
        # here, so its control is the session's own access (A10).
        if name == "cabinet_kernel":
            control = rt.service(name, "read_session_access", {}, kernel_session=session)
        else:
            control = rt.service(name, "validate_project_reference", {"project_id": pid})
        assert control["answer_kind"] != "refused", (name, control)

    # Only the owner reads it, and no read wrote an entry (A14 rule 4).
    assert _log(rt) == log


# --- Required test 6 -------------------------------------------------------


def test_sequential_and_concurrent_changes_number_in_order(semantic_runtime):
    """A15 rule 5, A15-1: two changes in turn are numbered n and n + 1 and
    the audit sequence holds n + 1; concurrent changes take distinct
    consecutive numbers; of two concurrent erasures the one applied first —
    told by what it removed — holds the lower number."""
    rt = semantic_runtime

    # In turn.
    card = _create_project(rt, "Primera")
    n = _log(rt)[-1]["sequence_number"]
    card = _correct(rt, card, "Primera, corregida")
    log = _log(rt)
    assert _numbers(log)[-2:] == [n, n + 1]
    assert _last_sequence_number(rt) == n + 1

    # Concurrent creations in one session.
    before = len(log)
    answers = []

    def create(i):
        answers.append(_create_project(rt, f"Concurrente {i}"))

    threads = [threading.Thread(target=create, args=(i,)) for i in range(6)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert len(answers) == 6
    log = _log(rt)
    new = log[before:]
    assert _numbers(new) == list(range(n + 2, n + 8))
    assert sorted(e["subject"]["project_id"] for e in new) == sorted(
        a["project_id"] for a in answers
    )
    assert _last_sequence_number(rt) == n + 7

    # Two concurrent erasures whose order shows in what they remove. Entries
    # of DAY_0 exist (above); make entries of DAY_1; erase on DAY_2, one
    # session before DAY_2, the other before DAY_1.
    on_day_0 = len(log)
    rt.clock.advance(days=1)
    rt.sign_in()
    card = _correct(rt, card, "Primera, dia uno")
    _correct(rt, card, "Primera, dia uno bis")
    on_day_1 = 2
    rt.clock.advance(days=1)
    rt.sign_in()
    wide_session = rt.owner_session()
    wide = _ok(
        rt.owner("erase_audit_entries", erase_before=DAY_2.isoformat(), confirm=False),
        "confirmation_step",
    )
    rt.sign_in()
    narrow = _ok(
        rt.owner("erase_audit_entries", erase_before=DAY_1.isoformat(), confirm=False),
        "confirmation_step",
    )
    last = _last_sequence_number(rt)
    results = {}

    def submit(label, step):
        results[label] = rt.owner_confirm(step)

    pair = [
        threading.Thread(target=submit, args=("wide", wide)),
        threading.Thread(target=submit, args=("narrow", narrow)),
    ]
    for thread in pair:
        thread.start()
    for thread in pair:
        thread.join()
    removed_wide = _ok(results["wide"], "audit_erased")["removed"]
    removed_narrow = _ok(results["narrow"], "audit_erased")["removed"]

    rt.use_owner_session(wide_session)
    log = _log(rt)
    assert len(log) == 2
    by_date = {e["erased_before"]: e for e in log}
    wide_entry = by_date[DAY_2.isoformat()]
    narrow_entry = by_date[DAY_1.isoformat()]
    assert sorted(_numbers(log)) == [last + 1, last + 2]
    assert _last_sequence_number(rt) == last + 2
    if removed_narrow == 0:
        # The wide erasure was applied first: it removed every old entry.
        assert removed_wide == on_day_0 + on_day_1
        assert wide_entry["sequence_number"] < narrow_entry["sequence_number"]
    else:
        # The narrow one first: it removed DAY_0's, the wide one DAY_1's.
        assert (removed_narrow, removed_wide) == (on_day_0, on_day_1)
        assert narrow_entry["sequence_number"] < wide_entry["sequence_number"]


# --- Required test 7 -------------------------------------------------------


def test_failed_change_leaves_sequence_unchanged(semantic_runtime):
    """A15 rule 5, A15-1: a change whose transaction fails writes no entry
    and leaves the audit sequence; the next accepted change takes the number
    after the last written."""
    rt = semantic_runtime
    card = _create_project(rt)
    log = _log(rt)
    last = _last_sequence_number(rt)
    assert last == log[-1]["sequence_number"]

    # The transaction fails at its last store call, after
    # upsert_audit_sequence_row wrote the raised counter: the counter must be
    # rolled back with it.
    rt.faults.fail_store_call("insert_audit_entry_row")
    failed = rt.owner(
        "correct_project",
        target=card["project_id"],
        stated_version=card["revision"],
        project=_project_facts("Casa Lopez, fallida"),
    )
    assert _refusal(failed) == ("internal_error", None, ["transaction_failed"])
    assert _log(rt) == log
    assert _last_sequence_number(rt) == last

    _correct(rt, card, "Casa Lopez, segunda")
    log_after = _log(rt)
    assert log_after[:-1] == log
    assert log_after[-1]["sequence_number"] == last + 1
    assert _last_sequence_number(rt) == last + 1


def test_no_action_changes_an_entry(semantic_runtime):
    """A15 rule 1: entries are never changed — after further changes of the
    same record and an erasure that removes none, every earlier entry reads
    back as it was written."""
    rt = semantic_runtime
    card = _create_project(rt)
    first = _log(rt)
    card = _correct(rt, card, "Casa Lopez, segunda")
    rt.clock.advance(hours=1)
    rt.sign_in()
    _correct(rt, card, "Casa Lopez, tercera")
    _ok(_erase_before(rt, date(2026, 1, 1)), "audit_erased")
    log = _log(rt)
    assert log[: len(first)] == first
    assert len(log) == len(first) + 3
