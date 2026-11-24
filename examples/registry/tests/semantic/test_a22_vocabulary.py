"""Witness tests for accepted decision A22 (02_rules_artifacts.md).

The first release declares one type, ``estimate``, owner service PresuPro
(rule 1). The declared types are part of the release: a running instance
reads them from its release, never from its configuration or its store (rule
2). A release that adds a type accepts it from then on (rule 3); one that
removes a type keeps every pointer of it as it was — 'list artifacts' and the
agent projection still carry them (rule 4) — while publishing it, reading its
latest and withdrawing a pointer of it are refused as an unknown type (rule
5). Formal invariants A22-1 to A22-3. Each tagged test carries the witness
name its Required test declares.

The Factory project supplies the ``semantic_runtime`` fixture
(``RUNTIME_SURFACE.md``); each test gets a fresh instance of the first
release at 2026-01-05T09:00:00Z. Surface used here:

- ``owner(...)`` — ``create_project``, ``grant_project``, ``read_session``,
  ``publish_pointer``, ``withdraw_pointer``, ``list_pointers``;
- ``service("cabinet_kernel", ...)`` — ``register_agent_session``,
  ``publish_artifact_pointer``, ``withdraw_artifact_pointer``,
  ``list_artifacts``, ``read_latest_artifact``, ``read_agent_projection``;
  ``service("presupro", ...)`` — ``read_latest_artifact``;
- ``store_rows("pointer_rows")``, ``new_request_id()``;
- ``stop()``, ``start()`` and ``configure_release(**constants)`` (RT2, RT3):
  after ``stop()`` and before ``start()``, the instance runs over the same
  store on a test release whose named data-provider constants hold the
  values given; here ``ARTIFACT_TYPE_OWNERS`` of a later release that removes
  ``estimate`` and adds ``quote`` (see ``review/A22.md``).

Expected values: the data provider's ``ARTIFACT_TYPE_OWNERS``
(``70_data_provider_closure.json``: ``[{"artifact_type": "estimate",
"owner_service": "presupro"}]``), State 5 (``50_public_apis_3_records.md``
publish_pointer, withdraw_pointer, list_pointers, latest_pointer_of_type,
published_pointers; Conventions, "Closed set of refusal codes":
``invalid_request`` (``unknown_artifact_type``), stage (4)), State 6
(``PointerView``, ``LatestPointerAnswer``, ``AgentProjectionAnswer``).
"""

KERNEL = "cabinet_kernel"
SESSION = "a22-session"

# 70_data_provider_closure.json: REFUSAL_STAGE_VALUES = 4.
STAGE_VALUES = 4

# ARTIFACT_TYPE_OWNERS of the first release (70_data_provider_closure.json).
FIRST_RELEASE = [{"artifact_type": "estimate", "owner_service": "presupro"}]
# A later release: `estimate` removed, a new type `quote` added (rules 3, 4,
# 6 — a removed name is never declared again, so the new type has a new name).
LATER_RELEASE = [{"artifact_type": "quote", "owner_service": "presupro"}]


def _accepted(answer, answer_kind):
    assert answer["answer_kind"] == answer_kind, answer
    return answer


def _assert_refused(answer, code, stage, kinds):
    # RUNTIME_SURFACE.md "Refusals are answers"; State 5 closed set.
    assert answer["answer_kind"] == "refused", answer
    assert answer["code"] == code, answer
    assert answer["stage"] == stage, answer
    assert [failure["kind"] for failure in answer["failures"]] == kinds, answer


def _assert_unknown_type(answer):
    _assert_refused(answer, "invalid_request", STAGE_VALUES, ["unknown_artifact_type"])


def _create_project(rt, name="A22 project"):
    answer = rt.owner(
        "create_project",
        request_id=rt.new_request_id(),
        project={"display_name": name, "address": "Calle Mayor 1"},
    )
    return _accepted(answer, "project_card")["card"]["project_id"]


def _kernel_with(rt, *project_ids):
    access = _accepted(
        rt.service(KERNEL, "register_agent_session", kernel_session=SESSION), "session_access"
    )["access"]
    version = access["access_version"]
    for project_id in project_ids:
        answer = rt.owner(
            "grant_project",
            target=SESSION,
            stated_version=version,
            project_id=project_id,
            make_active=False,
        )
        version = _accepted(answer, "session_access")["access"]["access_version"]


def _kernel_publish(rt, project_id, artifact_type, uri):
    return rt.service(
        KERNEL,
        "publish_artifact_pointer",
        {
            "project_id": project_id,
            "request_id": rt.new_request_id(),
            "pointer": {"artifact_type": artifact_type, "uri": uri},
        },
        kernel_session=SESSION,
    )


def _owner_publish(rt, project_id, artifact_type, uri):
    return rt.owner(
        "publish_pointer",
        target=project_id,
        request_id=rt.new_request_id(),
        pointer={"artifact_type": artifact_type, "uri": uri},
    )


def _kernel_list(rt, project_id):
    return _accepted(
        rt.service(KERNEL, "list_artifacts", {"project_id": project_id}, kernel_session=SESSION),
        "pointers",
    )["pointers"]


def _owner_list(rt, project_id):
    return _accepted(rt.owner("list_pointers", target=project_id), "pointers")["pointers"]


def _latest(rt, project_id, artifact_type):
    return rt.service(
        "presupro",
        "read_latest_artifact",
        {"project_id": project_id, "artifact_type": artifact_type},
    )


def _projection(rt, project_id):
    return _accepted(
        rt.service(
            KERNEL, "read_agent_projection", {"project_id": project_id}, kernel_session=SESSION
        ),
        "agent_projection",
    )


def _restart_on_later_release(rt):
    """A22 rules 2-4: the same store, served by a release whose
    ARTIFACT_TYPE_OWNERS no longer declares `estimate` and declares `quote`.
    A restart ends the owner's sessions (A13 rule 2); `owner` signs in again."""
    rt.stop()
    rt.configure_release(ARTIFACT_TYPE_OWNERS=LATER_RELEASE)
    assert rt.start() is None


def _history_with_every_status(rt):
    """Project A: estimate v1 superseded, v2 published; project B: v1 withdrawn."""
    project_a = _create_project(rt, "A22 history A")
    project_b = _create_project(rt, "A22 history B")
    _kernel_with(rt, project_a, project_b)
    _accepted(_kernel_publish(rt, project_a, "estimate", "https://presupro.example/a/1"), "pointer")
    published = _accepted(
        _kernel_publish(rt, project_a, "estimate", "https://presupro.example/a/2"), "pointer"
    )["pointer"]
    on_b = _accepted(
        _owner_publish(rt, project_b, "estimate", "https://presupro.example/b/1"), "pointer"
    )["pointer"]
    _accepted(rt.owner("withdraw_pointer", target=on_b["pointer_id"]), "pointer")
    return project_a, project_b, published


def test_undeclared_type_publish_refused(semantic_runtime):
    """RT1: publishing `wall_plan` is refused as an unknown type."""
    rt = semantic_runtime
    project_id = _create_project(rt)
    _kernel_with(rt, project_id)
    rows = rt.store_rows("pointer_rows")

    # A22-3: a type ARTIFACT_TYPE_OWNERS does not declare is unknown, stage
    # (4) `invalid_request` (`unknown_artifact_type`) — for Kernel and for the
    # owner alike (A08 rule 5).
    _assert_unknown_type(
        _kernel_publish(rt, project_id, "wall_plan", "https://walls.example/p/1")
    )
    _assert_unknown_type(_owner_publish(rt, project_id, "wall_plan", "https://walls.example/p/1"))
    # Its latest is refused the same way, never answered as none published.
    _assert_unknown_type(_latest(rt, project_id, "wall_plan"))
    assert _owner_list(rt, project_id) == []
    assert rt.store_rows("pointer_rows") == rows

    # Control: the declared type is accepted on the same project and session.
    published = _accepted(
        _kernel_publish(rt, project_id, "estimate", "https://presupro.example/e/1"), "pointer"
    )["pointer"]
    assert published["version"] == 1
    assert _owner_list(rt, project_id) == [published]


def test_removed_type_pointers_still_listed(semantic_runtime):
    """RT2: after a release without a type, its pointers are still listed by
    'list artifacts' with their statuses."""
    rt = semantic_runtime
    project_a, project_b, published = _history_with_every_status(rt)
    listed_a = _kernel_list(rt, project_a)
    listed_b = _owner_list(rt, project_b)
    assert [p["status"] for p in listed_a] == ["published", "superseded"]
    assert [p["status"] for p in listed_b] == ["withdrawn"]
    projection = _projection(rt, project_a)
    assert projection["pointers"] == [published]
    rows = rt.store_rows("pointer_rows")

    _restart_on_later_release(rt)

    # The release did change the vocabulary (control): `estimate` is now
    # unknown and `quote` is accepted from this release on (rules 3, 5).
    _assert_unknown_type(
        _kernel_publish(rt, project_a, "estimate", "https://presupro.example/a/3")
    )
    assert rt.store_rows("pointer_rows") == rows

    # A22-2, rule 4: every pointer of the removed type, as it was — status,
    # owner service, versions, instants, publisher, withdrawal — in 'list
    # artifacts' for Kernel and the owner, and the published one still in the
    # agent projection; the store's rows are not rewritten.
    assert _kernel_list(rt, project_a) == listed_a
    assert _owner_list(rt, project_a) == listed_a
    assert _owner_list(rt, project_b) == listed_b
    assert _projection(rt, project_a)["pointers"] == [published]
    assert rt.store_rows("pointer_rows") == rows

    # A new type's pointers join the history beside them; nothing old moves.
    quote = _accepted(
        _kernel_publish(rt, project_a, "quote", "https://presupro.example/q/1"), "pointer"
    )["pointer"]
    assert quote["version"] == 1
    assert quote["owner_service"] == "presupro"
    after = _kernel_list(rt, project_a)
    assert [p for p in after if p["artifact_type"] == "estimate"] == listed_a


def test_removed_type_latest_unknown_type(semantic_runtime):
    """RT3: 'read the latest artifact of a type' for a removed type is refused as
    an unknown type, not answered as none published."""
    rt = semantic_runtime
    project_a, project_b, published = _history_with_every_status(rt)
    never = _create_project(rt, "A22 never published")

    # Control, in the first release: a published latest, and "none is
    # published" for a project whose estimate was withdrawn or never made.
    assert _accepted(_latest(rt, project_a, "estimate"), "latest_pointer")["pointer"] == published
    assert _accepted(_latest(rt, project_b, "estimate"), "latest_pointer")["pointer"] is None
    assert _accepted(_latest(rt, never, "estimate"), "latest_pointer")["pointer"] is None
    rows = rt.store_rows("pointer_rows")

    _restart_on_later_release(rt)

    # A22-3, rule 5: refused as an unknown type — where a pointer is still
    # published, where none is, and where none ever was.
    for project_id in (project_a, project_b, never):
        _assert_unknown_type(_latest(rt, project_id, "estimate"))
    # Kernel, for the projects of its session's set, the same.
    for project_id in (project_a, project_b):
        _assert_unknown_type(
            rt.service(
                KERNEL,
                "read_latest_artifact",
                {"project_id": project_id, "artifact_type": "estimate"},
                kernel_session=SESSION,
            )
        )
    # The declared new type, never published, is answered as none published:
    # the two answers are told apart.
    assert _accepted(_latest(rt, never, "quote"), "latest_pointer")["pointer"] is None

    # Rule 5: publishing the removed type and withdrawing a pointer of it are
    # refused (State 5 withdraw_pointer: (4) a removed type refused), and the
    # published pointer stays published.
    _assert_unknown_type(_owner_publish(rt, project_a, "estimate", "https://presupro.example/a/3"))
    _assert_unknown_type(rt.owner("withdraw_pointer", target=published["pointer_id"]))
    _assert_unknown_type(
        rt.service(
            KERNEL,
            "withdraw_artifact_pointer",
            {"pointer_id": published["pointer_id"]},
            kernel_session=SESSION,
        )
    )
    assert rt.store_rows("pointer_rows") == rows
    [still] = [p for p in _owner_list(rt, project_a) if p["pointer_id"] == published["pointer_id"]]
    assert still == published


def test_first_release_declares_only_estimate(semantic_runtime):
    """RT4: in the first release publishing `estimate` is accepted and its
    pointer names PresuPro; `Estimate`, differing only in letter case, is
    refused as an unknown type."""
    rt = semantic_runtime
    project_id = _create_project(rt)
    _kernel_with(rt, project_id)

    # A22-1: declared_types(first release) = {estimate -> PresuPro}.
    by_kernel = _accepted(
        _kernel_publish(rt, project_id, "estimate", "https://presupro.example/e/1"), "pointer"
    )["pointer"]
    assert by_kernel["artifact_type"] == "estimate"
    assert by_kernel["owner_service"] == "presupro"
    by_owner = _accepted(
        _owner_publish(rt, project_id, "estimate", "https://presupro.example/e/2"), "pointer"
    )["pointer"]
    assert by_owner["owner_service"] == "presupro"
    assert by_owner["version"] == 2
    rows = rt.store_rows("pointer_rows")
    listed = _owner_list(rt, project_id)

    # Types compare as stored text (A06 rule 7), not case-folded: `Estimate`
    # is not declared, for publishing and for reading its latest; nor is the
    # name with a leading space, which Registry never trims (A02 rule 2).
    for undeclared in ("Estimate", "ESTIMATE", " estimate"):
        _assert_unknown_type(
            _kernel_publish(rt, project_id, undeclared, "https://presupro.example/e/x")
        )
        _assert_unknown_type(_owner_publish(rt, project_id, undeclared, "https://presupro.example/e/x"))
        _assert_unknown_type(_latest(rt, project_id, undeclared))
    assert _owner_list(rt, project_id) == listed
    assert rt.store_rows("pointer_rows") == rows
