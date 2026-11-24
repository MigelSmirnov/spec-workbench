"""Witness tests for accepted decision A07 (02_rules_artifacts.md).

Publishing a pointer assigns its version, marks the type's published pointer
``superseded`` with its instant and stores the new one ``published``, all in
one transaction or none of it (rule 1). Publishes and withdrawals on one
project's pointers are serialised (rule 2). A project has at most one
``published`` pointer of a type (rule 3); a withdrawal never makes an earlier
version ``published`` (rule 4); publishing and withdrawing on an archived
project are refused, reading stays open (rule 5). Formal invariants A07-1 to
A07-4. Each tagged test carries the witness name its Required test declares.

The Factory project supplies the ``semantic_runtime`` fixture
(``RUNTIME_SURFACE.md``); each test gets a fresh instance at
2026-01-05T09:00:00Z. Surface used here:

- ``owner(...)`` — ``create_project``, ``archive_project``, ``grant_project``,
  ``publish_pointer``, ``withdraw_pointer``, ``list_pointers``;
- ``service("cabinet_kernel", ...)`` — ``register_agent_session``,
  ``publish_artifact_pointer``, ``withdraw_artifact_pointer``,
  ``list_artifacts``, ``read_latest_artifact``; ``service("presupro", ...)``
  — ``read_latest_artifact``, ``list_artifacts``;
- ``store_rows("pointer_rows")``, ``new_request_id()``, ``clock.advance``;
- calls of ``service`` from several threads at once (RT1, RT4;
  RUNTIME_SURFACE.md "Concurrency") and ``faults.fail_store_call(method)``
  (RT2): the next call of the named ``StoreRepository`` method (State 6,
  ``70_persistence_closure.json``) raises once. Not
  ``faults.fail_next_commit()``: failing a transaction at its commit cannot
  tell L07's two commits from one, since the first commit fails and nothing
  is left either way; failing the second write inside the publish can.

Expected values: State 5 (``50_public_apis_3_records.md`` publish_pointer,
withdraw_pointer, latest_pointer_of_type; Conventions, "Closed set of refusal
codes"), State 6 (``PointerView``, ``PointerAnswer``,
``LatestPointerAnswer``; "The store's rows": a repository failure is
``internal_error`` / ``transaction_failed``, nothing changed).
"""

import threading
from datetime import datetime

KERNEL = "cabinet_kernel"
SESSION = "a07-session"

# 70_data_provider_closure.json: REFUSAL_STAGE_LIFECYCLE = 6.
STAGE_LIFECYCLE = 6

ROUNDS = 10


def _instant(text):
    # State 6 wire format: instants are ISO 8601 text in UTC ending in `Z`.
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def _accepted(answer, answer_kind):
    assert answer["answer_kind"] == answer_kind, answer
    return answer


def _assert_refused(answer, code, stage, kinds):
    # RUNTIME_SURFACE.md "Refusals are answers"; State 5 closed set.
    assert answer["answer_kind"] == "refused", answer
    assert answer["code"] == code, answer
    assert answer["stage"] == stage, answer
    assert [failure["kind"] for failure in answer["failures"]] == kinds, answer


def _create_project(rt, name="A07 project"):
    answer = rt.owner(
        "create_project",
        request_id=rt.new_request_id(),
        project={"display_name": name, "address": "Calle Mayor 1"},
    )
    return _accepted(answer, "project_card")["card"]["project_id"]


def _kernel_with(rt, *project_ids, session=SESSION):
    access = _accepted(
        rt.service(KERNEL, "register_agent_session", kernel_session=session), "session_access"
    )["access"]
    version = access["access_version"]
    for project_id in project_ids:
        answer = rt.owner(
            "grant_project",
            target=session,
            stated_version=version,
            project_id=project_id,
            make_active=False,
        )
        version = _accepted(answer, "session_access")["access"]["access_version"]


def _kernel_publish(rt, project_id, uri, request_id=None, session=SESSION):
    return rt.service(
        KERNEL,
        "publish_artifact_pointer",
        {
            "project_id": project_id,
            "request_id": request_id or rt.new_request_id(),
            "pointer": {"artifact_type": "estimate", "uri": uri},
        },
        kernel_session=session,
    )


def _kernel_withdraw(rt, pointer_id, session=SESSION):
    return rt.service(
        KERNEL, "withdraw_artifact_pointer", {"pointer_id": pointer_id}, kernel_session=session
    )


def _owner_publish(rt, project_id, uri):
    return rt.owner(
        "publish_pointer",
        target=project_id,
        request_id=rt.new_request_id(),
        pointer={"artifact_type": "estimate", "uri": uri},
    )


def _list(rt, project_id):
    return _accepted(
        rt.service("presupro", "list_artifacts", {"project_id": project_id}), "pointers"
    )["pointers"]


def _latest(rt, project_id):
    return _accepted(
        rt.service(
            "presupro",
            "read_latest_artifact",
            {"project_id": project_id, "artifact_type": "estimate"},
        ),
        "latest_pointer",
    )["pointer"]


def _assert_history_invariants(pointers):
    # A07-1: at most one published; A07-2: versions 1..n without gaps or
    # repeats; A07-4: every superseded pointer carries its instant.
    versions = sorted(p["version"] for p in pointers)
    assert versions == list(range(1, len(pointers) + 1))
    assert sum(1 for p in pointers if p["status"] == "published") <= 1
    for pointer in pointers:
        if pointer["status"] == "superseded":
            assert pointer["superseded_at"] is not None
            assert pointer["withdrawn_at"] is None
        if pointer["status"] == "withdrawn":
            assert pointer["withdrawn_at"] is not None
            assert pointer["superseded_at"] is None
        if pointer["status"] == "published":
            assert pointer["superseded_at"] is None
            assert pointer["withdrawn_at"] is None


def _concurrently(*calls):
    """Run each call in its own thread, released together by a barrier."""
    barrier = threading.Barrier(len(calls))
    results = [None] * len(calls)
    errors = []

    def run(index, call):
        try:
            barrier.wait()
            results[index] = call()
        except BaseException as error:  # reported below, never swallowed
            errors.append(error)

    threads = [threading.Thread(target=run, args=(i, c)) for i, c in enumerate(calls)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert not errors, errors
    return results


def test_first_publish_makes_version_one(semantic_runtime):
    """RT0: the first publish of a type on a project makes version 1, published."""
    rt = semantic_runtime
    first_project = _create_project(rt, "A07 first")
    second_project = _create_project(rt, "A07 second")
    _kernel_with(rt, first_project, second_project)

    answer = _accepted(
        _kernel_publish(rt, first_project, "https://presupro.example/e/1"), "pointer"
    )
    pointer = answer["pointer"]
    # A07-3: max(version) + 1, or 1 for the first; State 5 publish_pointer.
    assert pointer["version"] == 1
    assert pointer["status"] == "published"
    assert pointer["project_id"] == first_project
    assert pointer["artifact_type"] == "estimate"
    assert pointer["superseded_at"] is None
    assert pointer["withdrawn_by"] is None
    assert pointer["withdrawn_at"] is None
    assert answer["changed"] is True  # a create, not a repeat (State 5 "Repeats")

    # Read back: the history holds it alone; it is the latest (R0-17).
    assert _list(rt, first_project) == [pointer]
    assert _latest(rt, first_project) == pointer

    # Versions are per project and type (A07-2): a second project's first
    # publish, after the first project's, is version 1 too — and by the owner.
    owner_first = _accepted(
        _owner_publish(rt, second_project, "https://presupro.example/e/b1"), "pointer"
    )["pointer"]
    assert owner_first["version"] == 1
    assert owner_first["status"] == "published"
    # And the next publish on the first project is version 2 (A07-3).
    second = _accepted(
        _kernel_publish(rt, first_project, "https://presupro.example/e/2"), "pointer"
    )["pointer"]
    assert second["version"] == 2
    _assert_history_invariants(_list(rt, first_project))


def test_concurrent_publishes_consecutive_versions(semantic_runtime):
    """RT1: two concurrent publishes make n+1 and n+2; never an internal error."""
    rt = semantic_runtime
    project_id = _create_project(rt)
    _kernel_with(rt, project_id)
    _accepted(_kernel_publish(rt, project_id, "https://presupro.example/e/0"), "pointer")
    n = 1

    # The race is repeated: any one round may happen to run one after the
    # other, which A07 rule 2 makes indistinguishable; a Registry that loses
    # the race (L07: 500, or a duplicate version) fails some round.
    for round_number in range(ROUNDS):
        answers = _concurrently(
            lambda: _kernel_publish(rt, project_id, f"https://presupro.example/r{round_number}/a"),
            lambda: _kernel_publish(rt, project_id, f"https://presupro.example/r{round_number}/b"),
        )
        # Neither refused nor an internal error (A07 rule 2: "both accepted").
        for answer in answers:
            _accepted(answer, "pointer")
            assert answer["changed"] is True
        versions = sorted(a["pointer"]["version"] for a in answers)
        assert versions == [n + 1, n + 2]

        by_version = {p["version"]: p for p in _list(rt, project_id)}
        # The first (lower version) is superseded by the second, which is the
        # one published (A07-1, A07-4); the earlier one is superseded too.
        assert by_version[n]["status"] == "superseded"
        assert by_version[n + 1]["status"] == "superseded"
        assert by_version[n + 2]["status"] == "published"
        assert _latest(rt, project_id)["version"] == n + 2
        _assert_history_invariants(list(by_version.values()))
        n += 2


def test_failed_publish_leaves_nothing(semantic_runtime):
    """RT2: a failure after the version is assigned leaves no superseded pointer
    and no new one.

    The store is made to fail once at each of the publish's two writes — the
    new pointer's insertion and the previous one's supersession — so either
    order of the two writes is caught.
    """
    rt = semantic_runtime
    project_id = _create_project(rt)
    _kernel_with(rt, project_id)
    first = _accepted(
        _kernel_publish(rt, project_id, "https://presupro.example/e/1"), "pointer"
    )["pointer"]
    listed = _list(rt, project_id)
    rows = rt.store_rows("pointer_rows")

    request_id = rt.new_request_id()
    for method in ("insert_pointer_row", "update_pointer_row"):
        # 70_persistence_closure.json / State 6 StoreRepository: the two
        # pointer writes. A repository failure is raised to `store`, which
        # rolls back and answers internal_error (transaction_failed), nothing
        # changed (State 6 "Failures", A04 rule 4).
        rt.faults.fail_store_call(method)
        answer = _kernel_publish(rt, project_id, "https://presupro.example/e/2", request_id)
        _assert_refused(answer, "internal_error", None, ["transaction_failed"])
        # Nothing of the attempt remains: v1 still published, not superseded.
        assert _list(rt, project_id) == listed
        assert _latest(rt, project_id) == first
        assert rt.store_rows("pointer_rows") == rows

    # Control: the same publish, request id included, is now a new create (no
    # row of the failed attempt holds its request id, A01 rule 4), and takes
    # version 2: the failed attempts consumed no version (A07-2).
    retried = _accepted(
        _kernel_publish(rt, project_id, "https://presupro.example/e/2", request_id), "pointer"
    )
    assert retried["changed"] is True
    assert retried["pointer"]["version"] == 2
    by_version = {p["version"]: p for p in _list(rt, project_id)}
    assert by_version[1]["status"] == "superseded"
    assert by_version[2]["status"] == "published"


def test_withdrawn_latest_answers_none_published(semantic_runtime):
    """RT3 (untagged): after withdrawing the published pointer, 'read the latest
    artifact of a type' answers that none is published."""
    rt = semantic_runtime
    project_id = _create_project(rt)
    _kernel_with(rt, project_id)
    _accepted(_kernel_publish(rt, project_id, "https://presupro.example/e/1"), "pointer")
    second = _accepted(
        _kernel_publish(rt, project_id, "https://presupro.example/e/2"), "pointer"
    )["pointer"]
    # Control: the latest is the published v2.
    assert _latest(rt, project_id) == second

    withdrawn = _accepted(_kernel_withdraw(rt, second["pointer_id"]), "pointer")["pointer"]
    assert withdrawn["status"] == "withdrawn"
    # State 5 latest_pointer_of_type: "that none is published — also after a
    # withdrawal, which never falls back (R0-14)"; A07 rule 4.
    assert _latest(rt, project_id) is None
    kernel_latest = _accepted(
        rt.service(
            KERNEL,
            "read_latest_artifact",
            {"project_id": project_id, "artifact_type": "estimate"},
            kernel_session=SESSION,
        ),
        "latest_pointer",
    )
    assert kernel_latest["pointer"] is None
    by_version = {p["version"]: p for p in _list(rt, project_id)}
    assert by_version[1]["status"] == "superseded"  # not made published again
    assert by_version[2]["status"] == "withdrawn"
    _assert_history_invariants(list(by_version.values()))


def test_withdrawal_racing_publish_never_both(semantic_runtime):
    """RT4 (untagged): a withdrawal racing a publish of the same type either
    withdraws the old pointer before it is superseded, or is refused because it
    was superseded; never both."""
    rt = semantic_runtime
    project_id = _create_project(rt)
    _kernel_with(rt, project_id)
    current = _accepted(
        _kernel_publish(rt, project_id, "https://presupro.example/e/0"), "pointer"
    )["pointer"]

    for round_number in range(ROUNDS):
        withdrawal, publish = _concurrently(
            lambda: _kernel_withdraw(rt, current["pointer_id"]),
            lambda: _kernel_publish(rt, project_id, f"https://presupro.example/r{round_number}"),
        )
        # The publish is accepted either way, with the next version,
        # `published` (A07 rule 2: "a publish that runs after a withdrawal
        # makes the next version published").
        new = _accepted(publish, "pointer")["pointer"]
        assert new["version"] == current["version"] + 1
        by_version = {p["version"]: p for p in _list(rt, project_id)}
        old = by_version[current["version"]]
        assert by_version[new["version"]]["status"] == "published"

        if withdrawal["answer_kind"] == "pointer":
            # Withdrawn first: the old pointer is withdrawn, never superseded.
            assert withdrawal["pointer"]["status"] == "withdrawn"
            assert old["status"] == "withdrawn"
            assert old["superseded_at"] is None
            assert old["withdrawn_by"]["session_id"] == SESSION
        else:
            # Superseded first: refused as withdrawing a superseded pointer
            # (State 5 withdraw_pointer, `refused` (`superseded`), stage 6),
            # and the pointer carries no withdrawal.
            _assert_refused(withdrawal, "refused", STAGE_LIFECYCLE, ["superseded"])
            assert old["status"] == "superseded"
            assert old["withdrawn_at"] is None
            assert old["withdrawn_by"] is None
        _assert_history_invariants(list(by_version.values()))
        current = new


def test_publish_on_archived_project_refused(semantic_runtime):
    """RT5 (untagged): publishing on an archived project is refused (rule 5).

    Withdrawing there is refused too; reading stays open.
    """
    rt = semantic_runtime
    project_id = _create_project(rt)
    _kernel_with(rt, project_id)
    # Control: before archiving, both principals publish.
    _accepted(_kernel_publish(rt, project_id, "https://presupro.example/e/1"), "pointer")
    published = _accepted(
        _owner_publish(rt, project_id, "https://presupro.example/e/2"), "pointer"
    )["pointer"]

    _accepted(
        rt.owner("archive_project", target=project_id, stated_version=1), "project_card"
    )
    listed = _list(rt, project_id)  # reading stays open (rule 5)
    rows = rt.store_rows("pointer_rows")

    # State 5 publish_pointer / withdraw_pointer: (6) an archived project,
    # `refused` (`archived`). Kernel's project is still in its set (R0-70),
    # so stage (2) passes and stage (6) answers (A10 rule 4).
    rt.clock.advance(minutes=1)
    _assert_refused(
        _kernel_publish(rt, project_id, "https://presupro.example/e/3"),
        "refused",
        STAGE_LIFECYCLE,
        ["archived"],
    )
    _assert_refused(
        _owner_publish(rt, project_id, "https://presupro.example/e/3"),
        "refused",
        STAGE_LIFECYCLE,
        ["archived"],
    )
    _assert_refused(
        rt.owner("withdraw_pointer", target=published["pointer_id"]),
        "refused",
        STAGE_LIFECYCLE,
        ["archived"],
    )
    _assert_refused(
        _kernel_withdraw(rt, published["pointer_id"]),
        "refused",
        STAGE_LIFECYCLE,
        ["archived"],
    )
    # Nothing changed, and reads are answered.
    assert _list(rt, project_id) == listed
    assert _latest(rt, project_id) == published
    assert rt.store_rows("pointer_rows") == rows
