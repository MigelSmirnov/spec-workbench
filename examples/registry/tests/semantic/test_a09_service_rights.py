"""Witness tests for accepted decision A09 (02_rules_access.md).

Each service token names one service; the release — not the configuration —
says which operations that service may call and the highest disclosure class
it may receive (A09 rules 1, 2). An operation outside the token's row is
refused whatever the request holds (rule 3). An answer whose class is above the
token's highest is refused whole, never answered in part (rule 4); Cabinet
Kernel's highest class is `business_confidential` (R0-74). Each witness test
carries the name its Required test declares; Required tests 3, 7 and 8,
untagged, have tests named by what they show.

The Factory project `registry` supplies the ``semantic_runtime`` fixture
(``tests/semantic/RUNTIME_SURFACE.md``): a fresh instance per test, driven
over its two real listeners. Expected values come from State 2 (A09, A10,
A17 rule 7), State 5 (`50_public_apis_5_surfaces.md`:
`operations.perform_service_operation`, `service_api.serve_service_request`;
`50_public_apis_1_foundation.md`: `service_access.identify_service`,
`service_access.service_may_call`, `service_access.highest_class_of_service`;
`50_public_apis_3_records.md`: `projects.read_project_context`,
`projects.validate_project_reference`, `projects.read_agent_view`,
`customers.read_billing_data`, `artifact_pointers.publish_pointer`,
`artifact_pointers.list_pointers`; "Closed set of refusal codes" in
`50_public_apis_0_conventions.md`) and State 6 (`ServiceRequest`,
`ServiceInputs`, `ContextAnswer`/`ProjectContext`, `BillingAnswer`,
`ValidationAnswer`, `AgentProjectionAnswer`/`AgentProject`, `PointerAnswer`,
`PointersAnswer`, `RefusedAnswer`; the wire format of `60_contracts.md`; the
constants `SERVICE_RIGHTS`, `SERVICE_HIGHEST_CLASSES`, `PERSONAL_DATA_FIELDS`,
`ARTIFACT_TYPE_OWNERS`, `REFUSAL_HTTP_STATUSES` of
`70_data_provider_closure.json`).

Fixture surface used here:

- ``service(name, operation, inputs=None, kernel_session=None, token=…)``
  -> answer (``validate`` and ``context`` as the bare view, R0-04);
  ``service_raw(body, headers)`` -> (status, body, headers);
- ``owner(action, target=None, stated_version=None, **values)`` -> answer,
  for `create_project`, `record_customer`, `read_session`, `grant_project`;
- ``new_request_id()``; ``store_rows(table)`` for `pointer_rows`,
  `project_rows`, `customer_rows`, `agent_session_rows`, `audit_entry_rows`;
- ``stop()``, ``start()``, ``sign_in()`` and
  ``configure_release(**constants)``: after ``stop()`` and before
  ``start()``, the instance runs on a test release whose named data-provider
  constants hold the values given. A09 rule 6: a row of the rights
  changes only by a release; no Kernel-reachable answer of release v1 holds a
  `PERSONAL_DATA_FIELDS` field and every other service's highest class is
  `personal_data`, so rule 4 can only be observed on a release that differs
  in one row (tests 5 and 6, as A09 rule 4 states); rules 1 and 6 on a
  release whose `SERVICE_RIGHTS` differs in one row (test 7).
"""

import json
import secrets
import uuid

# Stage numbers of A04 rule 6 (70_data_provider_closure.json):
# REFUSAL_STAGE_AUTHENTICATION = 1, REFUSAL_STAGE_EXISTENCE = 3.
STAGE_AUTHENTICATION = 1
STAGE_EXISTENCE = 3

# State 6 ServiceName values.
PRESUPRO = "presupro"
CLIENT_PORTAL = "client_portal"
CABINET = "cabinet"
KERNEL = "cabinet_kernel"

# REFUSAL_HTTP_STATUSES (70_data_provider_closure.json; 60_contracts.md "The
# service API's wire format"): every code but not_found and internal_error
# answers 422.
UNAUTHENTICATED_HTTP_STATUS = 422

# ARTIFACT_TYPE_OWNERS (70_data_provider_closure.json): the one declared type.
ESTIMATE = "estimate"

# The keys of a refused answer as the fixture gives it (RUNTIME_SURFACE.md,
# "Refusals are answers"): nothing of the refused answer beside them.
REFUSAL_KEYS = {"answer_kind", "code", "stage", "failures"}

# The release v1 values of the two class tables
# (70_data_provider_closure.json), from which the test releases of tests 5
# and 6 differ in one row each.
# The release v1 rights table (70_data_provider_closure.json SERVICE_RIGHTS,
# A09 rule 2), from which the test release of Required test 7 differs in
# one row.
SERVICE_RIGHTS_V1 = [
    {"service": "presupro", "operation": "validate_project_reference"},
    {"service": "presupro", "operation": "read_project_context"},
    {"service": "presupro", "operation": "read_customer_billing"},
    {"service": "presupro", "operation": "list_artifacts"},
    {"service": "presupro", "operation": "read_latest_artifact"},
    {"service": "client_portal", "operation": "validate_project_reference"},
    {"service": "client_portal", "operation": "read_project_context"},
    {"service": "client_portal", "operation": "read_project"},
    {"service": "client_portal", "operation": "list_rooms"},
    {"service": "client_portal", "operation": "list_artifacts"},
    {"service": "client_portal", "operation": "read_latest_artifact"},
    {"service": "cabinet", "operation": "list_projects"},
    {"service": "cabinet", "operation": "read_project_context"},
    {"service": "cabinet", "operation": "validate_project_reference"},
    {"service": "cabinet_kernel", "operation": "register_agent_session"},
    {"service": "cabinet_kernel", "operation": "end_agent_session"},
    {"service": "cabinet_kernel", "operation": "read_session_access"},
    {"service": "cabinet_kernel", "operation": "request_project_access"},
    {"service": "cabinet_kernel", "operation": "validate_project_reference"},
    {"service": "cabinet_kernel", "operation": "read_agent_projection"},
    {"service": "cabinet_kernel", "operation": "list_rooms"},
    {"service": "cabinet_kernel", "operation": "add_room"},
    {"service": "cabinet_kernel", "operation": "list_artifacts"},
    {"service": "cabinet_kernel", "operation": "read_latest_artifact"},
    {"service": "cabinet_kernel", "operation": "publish_artifact_pointer"},
    {"service": "cabinet_kernel", "operation": "withdraw_artifact_pointer"},
]
SERVICE_HIGHEST_CLASSES_V1 = [
    {"service": "presupro", "highest_class": "personal_data"},
    {"service": "client_portal", "highest_class": "personal_data"},
    {"service": "cabinet", "highest_class": "personal_data"},
    {"service": "cabinet_kernel", "highest_class": "business_confidential"},
]
PERSONAL_DATA_FIELDS_V1 = [
    {"answer_model": "ProjectCard", "field": "display_name"},
    {"answer_model": "ProjectContext", "field": "display_name"},
    {"answer_model": "ProjectContext", "field": "address"},
    {"answer_model": "ProjectListItem", "field": "display_name"},
    {"answer_model": "ImportedProjectResult", "field": "display_name"},
    {"answer_model": "ImportPick", "field": "display_name"},
    {"answer_model": "MappedProject", "field": "display_name"},
    {"answer_model": "Object", "field": "address"},
    {"answer_model": "Object", "field": "object_kind"},
    {"answer_model": "Object", "field": "floor_area_m2"},
    {"answer_model": "Object", "field": "rooms_count"},
    {"answer_model": "Object", "field": "floor"},
    {"answer_model": "CustomerDetail", "field": "name"},
    {"answer_model": "CustomerDetail", "field": "phone"},
    {"answer_model": "CustomerDetail", "field": "email"},
    {"answer_model": "CustomerDetail", "field": "language"},
    {"answer_model": "CustomerDetail", "field": "tax_id"},
    {"answer_model": "CustomerDetail", "field": "legal_name"},
    {"answer_model": "ListedCustomer", "field": "name"},
    {"answer_model": "BillingAnswer", "field": "tax_id"},
    {"answer_model": "BillingAnswer", "field": "legal_name"},
    {"answer_model": "ImportCustomerValue", "field": "name"},
    {"answer_model": "ImportCustomerValue", "field": "v1_value"},
    {"answer_model": "MappedCustomer", "field": "name"},
    {"answer_model": "MappedCustomer", "field": "v1_value"},
    {"answer_model": "MadeCustomer", "field": "v1_value"},
]

ADDRESS = "Calle de la Paz 7, Valencia"
DISPLAY_NAME = "Casa Ferrer"
TAX_ID = "B98765432"
LEGAL_NAME = "Reformas Ferrer SL"


# --- helpers -----------------------------------------------------------------


def _answered(answer, kind):
    assert answer["answer_kind"] == kind, answer
    return answer


def _refused(answer, code, stage, kinds):
    """A refusal of the closed set (State 5): code, stage, the failing kinds."""
    assert answer["answer_kind"] == "refused", answer
    assert answer["code"] == code, answer
    assert answer["stage"] == stage, answer
    assert sorted(f["kind"] for f in answer["failures"]) == sorted(kinds), answer
    return answer


def _view(answer, name):
    """`validate` and `context` are the bare view on the wire (R0-04,
    State 5 `serve_service_request`; RUNTIME_SURFACE.md "Answers are the wire
    answers"): the view's fields at the top level, not nested under `name`."""
    assert not isinstance(answer.get(name), dict), answer
    return answer


def _create_project(rt, display_name=DISPLAY_NAME, address=ADDRESS, alias=None):
    project = {"display_name": display_name, "address": address}
    if alias is not None:
        project["alias"] = alias
    answer = rt.owner(
        "create_project", request_id=rt.new_request_id(), project=project
    )
    return _answered(answer, "project_card")["card"]["project_id"]


def _record_customer(rt, **facts):
    answer = rt.owner(
        "record_customer", request_id=rt.new_request_id(), customer=facts
    )
    return _answered(answer, "customer")["customer"]["customer_ref"]


def _kernel_session_with(rt, project_id):
    """A registered agent session holding `project_id` in its set (A10)."""
    session_id = f"a09-{uuid.uuid4().hex}"
    _answered(
        rt.service(KERNEL, "register_agent_session", kernel_session=session_id),
        "session_access",
    )
    version = _answered(
        rt.owner("read_session", target=session_id), "session_access"
    )["access"]["access_version"]
    _answered(
        rt.owner(
            "grant_project",
            target=session_id,
            stated_version=version,
            project_id=project_id,
            make_active=False,
        ),
        "session_access",
    )
    return session_id


def _restart_on_release(rt, **constants):
    """Run the instance on a test release differing in the rows given."""
    rt.stop()
    rt.configure_release(**constants)
    assert rt.start() is None
    rt.sign_in()


# --- Required test 1 ----------------------------------------------------------


def test_cabinet_billing_read_refused(semantic_runtime):
    """Cabinet calling 'read a customer's billing data' is refused (A09-1)."""
    rt = semantic_runtime
    customer_ref = _record_customer(
        rt,
        name="Ferrer",
        customer_kind="company",
        tax_id=TAX_ID,
        legal_name=LEGAL_NAME,
    )

    # Control: PresuPro's row holds the operation (A09 rule 2), so the same
    # request with PresuPro's token is answered with the billing data
    # (customers.read_billing_data Outputs).
    billing = _answered(
        rt.service(PRESUPRO, "read_customer_billing", {"customer_ref": customer_ref}),
        "billing",
    )
    assert billing["customer_kind"] == "company"
    assert billing["tax_id"] == TAX_ID
    assert billing["legal_name"] == LEGAL_NAME

    # Cabinet's row lacks it: not_permitted / outside_service_rights at stage
    # (1) (A09 rule 3; State 5 closed set), and nothing of the answer is in it.
    refused = rt.service(CABINET, "read_customer_billing", {"customer_ref": customer_ref})
    _refused(refused, "not_permitted", STAGE_AUTHENTICATION, ["outside_service_rights"])
    assert set(refused) == REFUSAL_KEYS
    assert TAX_ID not in json.dumps(refused)
    assert LEGAL_NAME not in json.dumps(refused)

    # "Whatever the request holds" (rule 3): an unknown Customer is the same
    # stage (1) refusal for Cabinet — the rights are checked before the record
    # (A04 rule 6) — while PresuPro reaches stage (3) with it.
    missing = str(uuid.uuid4())
    _refused(
        rt.service(CABINET, "read_customer_billing", {"customer_ref": missing}),
        "not_permitted",
        STAGE_AUTHENTICATION,
        ["outside_service_rights"],
    )
    _refused(
        rt.service(PRESUPRO, "read_customer_billing", {"customer_ref": missing}),
        "not_found",
        STAGE_EXISTENCE,
        ["unknown_customer"],
    )

    # Cabinet's own operations are answered with its token (row: list
    # projects, read a project context, validate a project reference).
    _answered(rt.service(CABINET, "list_projects", {}), "project_list")


# --- Required test 2 ----------------------------------------------------------


def test_context_portal_answered_kernel_refused(semantic_runtime):
    """Client Portal reading `context` receives the address; Kernel calling
    `context` is refused (A09-1)."""
    rt = semantic_runtime
    project_id = _create_project(rt)

    # Client Portal's row holds 'read a project context' (A09 rule 2); the
    # answer is v1's `context` field for field, address included (R0-04,
    # projects.read_project_context Outputs).
    context = _view(
        _answered(
            rt.service(CLIENT_PORTAL, "read_project_context", {"project_id": project_id}),
            "context",
        ),
        "context",
    )
    assert context["project_id"] == project_id
    assert context["address"] == ADDRESS
    assert context["display_name"] == DISPLAY_NAME
    assert context["status"] == "active"

    # Kernel's row has no 'read a project context'. The call is made with
    # everything else right — a registered session holding the project — so
    # only the row refuses it: not_permitted / outside_service_rights, stage
    # (1) (A09 rule 3), before the session's check of stage (2).
    session_id = _kernel_session_with(rt, project_id)
    refused = rt.service(
        KERNEL,
        "read_project_context",
        {"project_id": project_id},
        kernel_session=session_id,
    )
    _refused(refused, "not_permitted", STAGE_AUTHENTICATION, ["outside_service_rights"])
    assert set(refused) == REFUSAL_KEYS
    assert ADDRESS not in json.dumps(refused)
    assert DISPLAY_NAME not in json.dumps(refused)

    # Control for Kernel: an operation of its row on the same project and
    # session is answered (A09 rule 2, A10 rule 1).
    projection = _answered(
        rt.service(
            KERNEL,
            "read_agent_projection",
            {"project_id": project_id},
            kernel_session=session_id,
        ),
        "agent_projection",
    )
    assert projection["view"]["project_id"] == project_id


# --- Required test 3 (untagged) ----------------------------------------------


def test_unknown_token_refused_like_wrong_one(semantic_runtime):
    """A token not in the configuration is refused like a wrong one (R0-23,
    A17 rule 7): `unauthenticated` / `no_valid_token`, one answer for a
    missing, unknown or wrong token (State 5 closed set)."""
    rt = semantic_runtime
    project_id = _create_project(rt)
    inputs = {"project_id": project_id}

    # Control: the configured token is answered.
    _answered(rt.service(CABINET, "validate_project_reference", inputs), "validation")

    unknown = rt.service(
        CABINET, "validate_project_reference", inputs, token=secrets.token_urlsafe(48)
    )
    missing = rt.service(CABINET, "validate_project_reference", inputs, token=None)
    empty = rt.service(CABINET, "validate_project_reference", inputs, token="")
    for answer in (unknown, missing, empty):
        _refused(answer, "unauthenticated", STAGE_AUTHENTICATION, ["no_valid_token"])
    # One answer: nothing tells an unknown token from a wrong or a missing one.
    assert unknown == missing == empty

    # The same on the wire, byte for byte of its JSON, with the status of
    # REFUSAL_HTTP_STATUSES (422 for unauthenticated).
    body = json.dumps(
        {"operation": "validate_project_reference", "inputs": inputs}
    ).encode()
    content_type = {"Content-Type": "application/json"}
    raw_unknown = rt.service_raw(
        body,
        {**content_type, "Authorization": f"Bearer {secrets.token_urlsafe(48)}"},
    )
    raw_missing = rt.service_raw(body, dict(content_type))
    assert raw_unknown[0] == raw_missing[0] == UNAUTHENTICATED_HTTP_STATUS
    assert json.loads(raw_unknown[1]) == json.loads(raw_missing[1])

    # Refused each time without a limit (A17 rule 7): after many unknown
    # tokens the configured one is still answered.
    for _ in range(25):
        _refused(
            rt.service(
                CABINET,
                "validate_project_reference",
                inputs,
                token=secrets.token_urlsafe(48),
            ),
            "unauthenticated",
            STAGE_AUTHENTICATION,
            ["no_valid_token"],
        )
    validation = _view(
        _answered(rt.service(CABINET, "validate_project_reference", inputs), "validation"),
        "validation",
    )
    assert validation["exists"] is True


# --- Required test 4 ----------------------------------------------------------


def test_presupro_publish_pointer_refused(semantic_runtime):
    """PresuPro calling 'publish an artifact pointer' is refused (A09-1,
    R0-88)."""
    rt = semantic_runtime
    project_id = _create_project(rt)
    pointer = {
        "artifact_type": ESTIMATE,
        "uri": "https://presupro.example/estimates/1",
        "payload_ref": None,
        "content_digest": None,
    }
    inputs = {
        "project_id": project_id,
        "request_id": rt.new_request_id(),
        "pointer": pointer,
    }

    # PresuPro owns the type (ARTIFACT_TYPE_OWNERS), yet its row has no
    # 'publish': not_permitted / outside_service_rights at stage (1) (A09
    # rules 2, 3; service_access.service_may_call: no token but Kernel's may
    # publish).
    refused = rt.service(PRESUPRO, "publish_artifact_pointer", inputs)
    _refused(refused, "not_permitted", STAGE_AUTHENTICATION, ["outside_service_rights"])

    # Nothing was written: the pointer list PresuPro may read is empty, and so
    # is the store's pointer table.
    listed = _answered(
        rt.service(PRESUPRO, "list_artifacts", {"project_id": project_id}), "pointers"
    )
    assert listed["pointers"] == []
    assert rt.store_rows("pointer_rows") == []

    # Control: Kernel's row holds 'publish' (A09 rule 2); with a session
    # holding the project the same request is accepted and the pointer is
    # listed, version 1, owned by the type's owner service.
    session_id = _kernel_session_with(rt, project_id)
    published = _answered(
        rt.service(
            KERNEL, "publish_artifact_pointer", inputs, kernel_session=session_id
        ),
        "pointer",
    )
    assert published["pointer"]["project_id"] == project_id
    listed = _answered(
        rt.service(PRESUPRO, "list_artifacts", {"project_id": project_id}), "pointers"
    )
    assert [p["pointer_id"] for p in listed["pointers"]] == [
        published["pointer"]["pointer_id"]
    ]
    assert listed["pointers"][0]["owner_service"] == PRESUPRO
    assert listed["pointers"][0]["version"] == 1


# --- Required test 5 ----------------------------------------------------------


def test_answer_above_class_refused_whole(semantic_runtime):
    """An answer that would carry a class above the calling token's highest is
    refused whole: no field of it is disclosed (A09-2, rule 4).

    Release v1 gives every service but Kernel `personal_data`, the highest
    class, so the case exists only on a release whose PresuPro row says
    `business_confidential` (A09 rule 6: a row changes by a release)."""
    rt = semantic_runtime
    _restart_on_release(
        rt,
        SERVICE_HIGHEST_CLASSES=[
            row
            if row["service"] != PRESUPRO
            else {"service": PRESUPRO, "highest_class": "business_confidential"}
            for row in SERVICE_HIGHEST_CLASSES_V1
        ],
    )
    project_id = _create_project(rt)
    company = _record_customer(
        rt, name="Ferrer", customer_kind="company", tax_id=TAX_ID, legal_name=LEGAL_NAME
    )
    person = _record_customer(rt, name="Lola Ferrer", customer_kind="person")

    # `context` holds `display_name` and `address`, both PERSONAL_DATA_FIELDS
    # rows: its class is personal_data, above PresuPro's highest here.
    # Refused not_permitted / answer_above_class at stage (1) (State 5 closed
    # set), whole: the answer is the refusal and nothing else.
    refused = rt.service(PRESUPRO, "read_project_context", {"project_id": project_id})
    _refused(refused, "not_permitted", STAGE_AUTHENTICATION, ["answer_above_class"])
    assert set(refused) == REFUSAL_KEYS
    text = json.dumps(refused)
    assert ADDRESS not in text and DISPLAY_NAME not in text

    # The billing read of a company with fiscal data holds `tax_id` and
    # `legal_name` values: refused whole, its kind (not personal) withheld too.
    refused = rt.service(PRESUPRO, "read_customer_billing", {"customer_ref": company})
    _refused(refused, "not_permitted", STAGE_AUTHENTICATION, ["answer_above_class"])
    assert set(refused) == REFUSAL_KEYS
    text = json.dumps(refused)
    assert TAX_ID not in text and LEGAL_NAME not in text and "company" not in text

    # Controls. The class is the answer's, not the operation's: a billing read
    # whose personal fields hold no value is business_confidential
    # (perform_service_operation Enforces: "when one of the fields ... holds a
    # value in it") and answered, the absent values marked absent (R0-83).
    billing = _answered(
        rt.service(PRESUPRO, "read_customer_billing", {"customer_ref": person}),
        "billing",
    )
    assert billing["customer_kind"] == "person"
    assert billing["tax_id"] is None and billing["legal_name"] is None

    # An answer with no PERSONAL_DATA_FIELDS field is answered to PresuPro.
    validation = _view(
        _answered(
            rt.service(PRESUPRO, "validate_project_reference", {"project_id": project_id}),
            "validation",
        ),
        "validation",
    )
    assert validation["exists"] is True

    # The service whose row still says personal_data receives the same context
    # in full: the refusal is the class's, not the operation's.
    context = _view(
        _answered(
            rt.service(CLIENT_PORTAL, "read_project_context", {"project_id": project_id}),
            "context",
        ),
        "context",
    )
    assert context["address"] == ADDRESS


# --- Required test 6 ----------------------------------------------------------


def test_kernel_highest_class_business_confidential(semantic_runtime):
    """An answer to Cabinet Kernel carrying `business_confidential` is
    answered; one that would carry a `personal_data` field is refused whole
    (A09-3, A09-2).

    Kernel's row is release v1's (`business_confidential`, R0-74). No answer
    of Kernel's operations holds a PERSONAL_DATA_FIELDS field in release v1, so
    the test release adds one row, (`AgentProject`, `alias`), and leaves the
    rights and the highest classes as v1 has them."""
    rt = semantic_runtime
    _restart_on_release(
        rt,
        PERSONAL_DATA_FIELDS=PERSONAL_DATA_FIELDS_V1
        + [{"answer_model": "AgentProject", "field": "alias"}],
    )
    plain = _create_project(rt, display_name="Casa Ruiz")
    aliased = _create_project(rt, display_name="Casa Soler", alias="Soler-bano")
    session_id = _kernel_session_with(rt, plain)
    version = _answered(
        rt.owner("read_session", target=session_id), "session_access"
    )["access"]["access_version"]
    _answered(
        rt.owner(
            "grant_project",
            target=session_id,
            stated_version=version,
            project_id=aliased,
            make_active=False,
        ),
        "session_access",
    )

    # business_confidential answers are answered to Kernel: its highest class
    # is not `open` (every answer is at least business_confidential, State 5
    # perform_service_operation).
    projection = _answered(
        rt.service(
            KERNEL, "read_agent_projection", {"project_id": plain}, kernel_session=session_id
        ),
        "agent_projection",
    )
    assert projection["view"]["project_id"] == plain
    assert projection["view"]["alias"] is None
    access = _answered(
        rt.service(KERNEL, "read_session_access", kernel_session=session_id),
        "session_access",
    )
    assert sorted(access["access"]["granted_project_ids"]) == sorted([plain, aliased])

    # The projection whose `alias` holds a value is personal_data on this
    # release: above Kernel's highest, refused whole — Kernel's highest is not
    # `personal_data` (A09-3), and nothing of the projection is answered
    # (A09-2).
    refused = rt.service(
        KERNEL, "read_agent_projection", {"project_id": aliased}, kernel_session=session_id
    )
    _refused(refused, "not_permitted", STAGE_AUTHENTICATION, ["answer_above_class"])
    assert set(refused) == REFUSAL_KEYS
    assert "Soler-bano" not in json.dumps(refused)

    # Kernel's other read of the same project carries no listed field and is
    # still answered: the refusal is the answer's class, not the project's.
    rooms = _answered(
        rt.service(KERNEL, "list_rooms", {"project_id": aliased}, kernel_session=session_id),
        "rooms",
    )
    assert rooms["answer_kind"] == "rooms"


# --- Required test 7 (untagged) -----------------------------------------------


def test_rights_come_from_the_release_not_the_configuration(semantic_runtime):
    """A09 Required test 7: Cabinet's 'read a customer's billing data',
    refused on the first release, is answered on a test release whose
    rights table adds it to Cabinet's row, the configuration — the same
    tokens — unchanged; the first release again refuses it (A09 rules 1, 6:
    the configuration holds the tokens, the release their rights)."""
    rt = semantic_runtime
    customer_ref = _record_customer(
        rt, name="Ferrer", customer_kind="company", tax_id=TAX_ID, legal_name=LEGAL_NAME
    )

    def cabinet_billing():
        return rt.service(CABINET, "read_customer_billing", {"customer_ref": customer_ref})

    refused = cabinet_billing()
    _refused(refused, "not_permitted", STAGE_AUTHENTICATION, ["outside_service_rights"])
    assert TAX_ID not in json.dumps(refused)

    # The same instance, store and configuration on a release whose Cabinet
    # row holds the operation: the token now carries the right.
    _restart_on_release(
        rt,
        SERVICE_RIGHTS=SERVICE_RIGHTS_V1
        + [{"service": CABINET, "operation": "read_customer_billing"}],
    )
    billing = _answered(cabinet_billing(), "billing")
    assert billing["tax_id"] == TAX_ID
    assert billing["legal_name"] == LEGAL_NAME

    # Back on the first release's table: refused again.
    _restart_on_release(rt, SERVICE_RIGHTS=SERVICE_RIGHTS_V1)
    _refused(cabinet_billing(), "not_permitted", STAGE_AUTHENTICATION, ["outside_service_rights"])


# --- Required test 8 (untagged) -----------------------------------------------


def test_no_service_token_reaches_an_owner_action(semantic_runtime):
    """A09 Required test 8: each of the four tokens asking for an owner
    action — creating a project, recording a customer, archiving a project,
    granting a project to a session, erasing audit entries — is refused as
    outside its rights, and nothing changes (A09 rule 5: no token carries the
    owner's rights; State 5 `serve_service_request`: a name that is no
    `ServiceOperation` of the token's row is refused as outside its
    rights)."""
    rt = semantic_runtime
    project_id = _create_project(rt)
    session_id = _kernel_session_with(rt, project_id)
    tables = ("project_rows", "customer_rows", "agent_session_rows", "audit_entry_rows")
    before = {table: rt.store_rows(table) for table in tables}

    owner_actions = (
        ("create_project", {"request_id": rt.new_request_id(),
                            "project": {"display_name": "Por token", "address": ADDRESS}}),
        ("record_customer", {"request_id": rt.new_request_id(),
                             "customer": {"name": "Por token", "customer_kind": "person"}}),
        ("archive_project", {"project_id": project_id}),
        ("grant_project", {"project_id": project_id}),
        ("erase_audit_entries", {"erase_before": "2026-01-01"}),
    )
    for name in (PRESUPRO, CLIENT_PORTAL, CABINET, KERNEL):
        session = session_id if name == KERNEL else None
        for operation, inputs in owner_actions:
            refused = rt.service(name, operation, inputs, kernel_session=session)
            _refused(refused, "not_permitted", STAGE_AUTHENTICATION, ["outside_service_rights"])
            assert set(refused) == REFUSAL_KEYS, (name, operation)

    assert {table: rt.store_rows(table) for table in tables} == before
    # Control: the owner, in an owner session, archives the same project.
    card = _answered(rt.owner("read_project", target=project_id), "project_card")["card"]
    archived = _answered(
        rt.owner("archive_project", target=project_id, stated_version=card["revision"]),
        "project_card",
    )
    assert archived["card"]["status"] == "archived"
