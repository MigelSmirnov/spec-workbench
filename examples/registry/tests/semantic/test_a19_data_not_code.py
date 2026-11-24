"""Witness tests for accepted decision A19 (02_rules_installation.md).

Every stored value is data, never code: the owner interface renders every
stored value as text escaped for its place, sends no script and forbids any
by its content security policy; a value a caller gives only fills a value
place of a query whose structure the release fixes, and a value choosing
among fixed alternatives is checked against its closed list first; the
import file is read as data, under a limit of IMPORT_FILE_MAX_BYTES counted
over the bytes received. Each test carries the witness name its Required test
declares; Required test 4, untagged, runs as an ordinary test.

The Factory project ``registry`` supplies the ``semantic_runtime`` pytest
fixture (``RUNTIME_SURFACE.md``). Each test gets a fresh instance: an empty
store, both listeners, the clock at 2026-01-05T09:00:00Z.

Fixture surface used here:

- ``owner(action, target=None, stated_version=None, confirm=True,
  **values)`` -> answer (``create_project``, ``read_project``,
  ``add_room``, ``record_customer``, ``read_customer``, ``list_sessions``,
  ``answer_access_request``, ``show_import_mapping``, ``confirm_import``,
  ``list_pointers``);
- ``owner_upload(content, declared_length=...)`` -> answer;
- ``owner_http(method, path, query=None, form=None, cookie=...)`` ->
  ``(status, html, headers)``; ``owner_session()`` (its CSRF value);
- ``service(name, operation, inputs=None, kernel_session=None)`` -> answer;
- ``new_request_id()``; ``export_file(projects=..., rooms=..., pointers=...)``
  -> bytes, each record a dict of its ``ExportProject`` / ``ExportRoom`` /
  ``ExportPointer`` fields but ``position`` (State 6, "The import file");
- ``store_rows(table)``.
"""

import hashlib
import json
from html.parser import HTMLParser
from urllib.parse import parse_qs, urlsplit

KERNEL = "cabinet_kernel"

# Data provider constants (70_data_provider_closure.json).
IMPORT_FILE_MAX_BYTES = 52428800  # A19 rule 4: 50 × 1024 × 1024
OWNER_TARGET_PARAMETER = "target"
OWNER_CSRF_FIELD = "csrf"
OWNER_PATHS = {  # OWNER_ACTIONS: every row's path
    "/sign_in", "/sign_out", "/", "/read_project", "/create_project",
    "/correct_project", "/archive_project", "/erase_project", "/add_room",
    "/list_pointers", "/publish_pointer", "/withdraw_pointer",
    "/list_customers", "/read_customer", "/record_customer",
    "/correct_customer", "/mark_customer", "/erase_customer",
    "/list_sessions", "/read_session", "/answer_access_request",
    "/grant_project", "/set_active_project", "/revoke_project",
    "/end_session", "/read_audit", "/erase_audit_entries", "/upload_import",
    "/show_import_mapping", "/show_confirmation", "/confirm_import",
    "/newest_backup",
}

# State 6, "The store's rows": the eight tables.
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

# A value that is not text in the text it is shown as: it holds `<`, `>`,
# `&`, `"` and `'` (A19 Required test 5), and is an element with an attribute
# of a name no page has, so an element or an attribute made from it is seen.
# 18 characters: within ALIAS_MAX_CHARACTERS (40), so it fits every field.
HOSTILE = "<zq zq='1'>&\"</zq>"
HOSTILE_TAG = "zq"
# The same, holding also `?`, `#`, `/`, `=`, `+`, `%` and a space, for a value
# in a link's query (A19 Required test 5). An agent session's identity is
# recorded as Kernel gives it (R0-53, State 5 register_session) and is the
# target of the session's links (OWNER_TARGET_PARAMETER).
HOSTILE_QUERY = HOSTILE + "?#/=+% x"
# A session identity with nothing to escape, the control of HOSTILE_QUERY.
PLAIN_SESSION = "a19-plain-session"


# --- pages ------------------------------------------------------------------


class _Page(HTMLParser):
    """A page as a browser reads it: elements, attributes (character
    references decoded), text nodes, and the URLs of links and forms."""

    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.tags = []
        self.attributes = []  # (tag, name, value)
        self.texts = []
        self.urls = []  # (tag, url)
        self.feed(html)
        self.close()

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        for name, value in attrs:
            self.attributes.append((tag, name, value))
            if (tag, name) in (("a", "href"), ("form", "action")) and value is not None:
                self.urls.append((tag, value))

    handle_startendtag = handle_starttag

    def handle_data(self, data):
        self.texts.append(data)

    def text(self):
        return "\x00".join(self.texts)

    def attribute_values(self):
        return [v for _, _, v in self.attributes if v is not None]


def _csp_forbids_script(headers):
    """The response's content security policy forbids every script (A19
    rule 2): `script-src 'none'`, or no `script-src` and `default-src 'none'`."""
    values = [v for k, v in _header_items(headers) if k.lower() == "content-security-policy"]
    assert values, "a page without a Content-Security-Policy header field"
    directives = {}
    for value in values:
        for part in value.split(";"):
            words = part.split()
            if words:
                directives.setdefault(words[0].lower(), words[1:])
    source = directives.get("script-src", directives.get("default-src"))
    return source is not None and [w.lower() for w in source] == ["'none'"]


def _header_items(headers):
    return headers.items() if hasattr(headers, "items") else headers


def _assert_page_safe(status, html, headers):
    """Every page: its CSP forbids scripts, it holds no script of its own and
    no element or attribute made from HOSTILE (A19 rules 1, 2)."""
    assert _csp_forbids_script(headers)
    page = _Page(html)
    assert "script" not in page.tags
    assert HOSTILE_TAG not in page.tags
    for _, name, value in page.attributes:
        assert name != HOSTILE_TAG
        assert not name.startswith("on")  # no event handler: no script
        assert not (value or "").strip().lower().startswith("javascript:")
    return page


def _get(rt, path, query=None):
    status, html, headers = rt.owner_http("GET", path, query=query)
    page = _assert_page_safe(status, html, headers)
    return status, page, html


def _csrf(rt):
    return rt.owner_session().csrf


def _targets(page):
    """The target of every link and form that carries one, and its URL's
    other parts."""
    found = []
    for _, url in page.urls:
        parts = urlsplit(url)
        query = parse_qs(parts.query, keep_blank_values=True)
        if OWNER_TARGET_PARAMETER in query:
            found.append((parts, query))
    return found


# --- records ----------------------------------------------------------------


def _create_project(rt, display_name, address="Calle Mayor 1", alias=None):
    project = {"display_name": display_name, "address": address}
    if alias is not None:
        project["alias"] = alias
    answer = rt.owner("create_project", request_id=rt.new_request_id(), project=project)
    assert answer["answer_kind"] == "project_card"
    return answer["card"]


def _grant_session(rt, session, project_id, request_text="Need the project"):
    """Kernel registers `session` and asks; the owner grants `project_id` and
    makes it active (A10–A12)."""
    registered = rt.service(KERNEL, "register_agent_session", kernel_session=session)
    assert registered["answer_kind"] != "refused"
    asked = rt.service(
        KERNEL, "request_project_access", {"request_text": request_text},
        kernel_session=session,
    )
    assert asked["answer_kind"] == "request_pending"
    access = rt.service(KERNEL, "read_session_access", kernel_session=session)["access"]
    answer = rt.owner(
        "answer_access_request",
        target=session,
        stated_version=access["access_version"],
        access_answer={"answer_kind": "grant", "project_id": project_id, "make_active": True},
    )
    assert answer["answer_kind"] != "refused"


def _json(value):
    return json.loads(value) if isinstance(value, (str, bytes)) else value


def _store(rt):
    return {table: rt.store_rows(table) for table in TABLES}


def _refusal(answer, code, stage, kinds):
    assert answer["answer_kind"] == "refused"
    assert answer["code"] == code
    assert answer["stage"] == stage
    assert sorted(f["kind"] for f in answer["failures"]) == sorted(kinds)


def _export_project(project_id, name, address, customer_ref=None):
    return {
        "project_id": project_id,
        "name": name,
        "address": address,
        "status": "active",
        "customer_ref": customer_ref,
        "created_at": "2025-03-01T10:00:00+00:00",
        "updated_at": "2025-03-02T10:00:00+00:00",
        "archived_at": None,
    }


def _export_room(room_id, project_id, name):
    return {
        "room_id": room_id,
        "project_id": project_id,
        "name": name,
        "created_at": "2025-03-01T11:00:00+00:00",
    }


def _sized_export(rt, size):
    """An export file of exactly `size` bytes: one valid project, padded with
    JSON whitespace after the object, which the format reads as nothing (one
    UTF-8 JSON object, State 6 "The import file")."""
    content = rt.export_file(
        projects=[_export_project("v1-size-project", "Casa Limite", "Calle Limite 1")],
        rooms=[],
        pointers=[],
    )
    assert len(content) < size
    return content + b" " * (size - len(content))


# --- tests ------------------------------------------------------------------


SCRIPT_ROOM = "<script>alert(1)</script>"


def test_script_room_name_shown_as_text(semantic_runtime):
    """A room the agent named `<script>alert(1)</script>` is shown in the
    owner interface as that text, never as an element (A19 rule 1, A19-1)."""
    rt = semantic_runtime
    card = _create_project(rt, "Casa Script")
    project_id = card["project_id"]
    session = "a19-room-session"
    _grant_session(rt, session, project_id)
    added = rt.service(
        KERNEL,
        "add_room",
        {"project_id": project_id, "room_name": SCRIPT_ROOM, "request_id": rt.new_request_id()},
        kernel_session=session,
    )
    assert added["answer_kind"] == "room"
    assert added["room"]["name"] == SCRIPT_ROOM  # stored as given
    # Control: a plain room beside it.
    rt.owner("add_room", target=project_id, request_id=rt.new_request_id(), room_name="Cocina")

    names = sorted(r["name"] for r in rt.owner("read_project", target=project_id)["card"]["rooms"])
    assert names == sorted(["Cocina", SCRIPT_ROOM])

    status, page, html = _get(rt, "/read_project", {OWNER_TARGET_PARAMETER: project_id})
    assert status == 200  # SERVICE_ANSWER_STATUS
    assert "<script" not in html.lower()  # no script element, the value's included
    assert SCRIPT_ROOM in page.text()  # shown as that text
    assert "Cocina" in page.text()


ACCESS_MARKUP = "<img src=x onerror=alert(1)><zb>urgent</zb> & \"now\" 'please'"


def test_access_request_markup_shown_as_text(semantic_runtime):
    """An access request text holding markup is shown as text on the pages
    that show it (A19 rule 1, A19-1; M08)."""
    rt = semantic_runtime
    session = "a19-request-session"
    assert rt.service(KERNEL, "register_agent_session", kernel_session=session)[
        "answer_kind"
    ] != "refused"
    asked = rt.service(
        KERNEL, "request_project_access", {"request_text": ACCESS_MARKUP},
        kernel_session=session,
    )
    assert asked["answer_kind"] == "request_pending"
    items = rt.owner("list_sessions")["items"]
    assert [i["request_text"] for i in items] == [ACCESS_MARKUP]  # stored as given

    # The session list shows the request text (SessionListItem.request_text):
    # whole, as text, and no element or attribute came from it.
    status, page, html = _get(rt, "/list_sessions")
    assert status == 200  # SERVICE_ANSWER_STATUS
    assert ACCESS_MARKUP in page.text()
    assert "img" not in page.tags and "zb" not in page.tags
    assert all(name not in ("onerror", "src") for _, name, _ in page.attributes)
    assert "<img" not in html.lower()


QUOTE_SEMICOLON = "O'Brien \"Casa\"; Calle 5"


def test_quote_semicolon_name_round_trips(semantic_runtime):
    """A display name with a quote and a semicolon is stored and read back
    unchanged (A19 rule 3, A19-2)."""
    rt = semantic_runtime
    card = _create_project(rt, QUOTE_SEMICOLON, address="Calle 'Uno'; 2")
    project_id = card["project_id"]
    assert card["display_name"] == QUOTE_SEMICOLON
    read = rt.owner("read_project", target=project_id)["card"]
    assert read["display_name"] == QUOTE_SEMICOLON
    assert read["object_facts"]["address"] == "Calle 'Uno'; 2"
    # The same value through the service API (cabinet's read_project_context).
    # On the wire `context` is the nested view alone (State 6, "The service
    # API's wire format", R0-04).
    context = rt.service("cabinet", "read_project_context", {"project_id": project_id})
    assert context["display_name"] == QUOTE_SEMICOLON
    listed = rt.service("cabinet", "list_projects", {})
    assert [i["display_name"] for i in listed["items"]] == [QUOTE_SEMICOLON]


def test_import_file_size_limit_counted_over_received_bytes(semantic_runtime):
    """An import file of exactly 50 MiB, sent by the upload form with its CSRF
    field first, is read. One byte more is refused `file_too_large` with no
    mapping when no length is declared, when the true one is, and when the
    file part's declared length is one byte short — the body then ends inside
    the closing delimiter, every byte of the file arriving. A declared length
    so short that the body ends inside the file's own bytes is refused
    `file_unreadable`: the file ends before its delimiter and the limit is
    never passed (State 5 `serve_owner_request`, `read_upload_head`). Either
    way the file the session kept stays kept (A19 rule 4; Required test
    4)."""
    rt = semantic_runtime
    exact = _sized_export(rt, IMPORT_FILE_MAX_BYTES)
    over = _sized_export(rt, IMPORT_FILE_MAX_BYTES + 1)

    accepted = rt.owner_upload(exact, declared_length=len(exact))
    assert accepted["answer_kind"] == "import_upload"
    # The digest of exactly the bytes received (State 5 read_import_mapping).
    assert accepted["file_digest"] == hashlib.sha256(exact).hexdigest()
    assert [p["project_id"] for p in accepted["projects"]] == ["v1-size-project"]
    rows_before = _store(rt)

    # A byte over the limit: refused at stage (4), invalid_request,
    # file_too_large (State 5, "Closed set of refusal codes"), with the true
    # declared length, one byte smaller — a shortfall within the closing
    # delimiter, so more than the limit is still read — or none at all. A
    # refusal carries no mapping and no digest.
    for declared in (len(over), len(over) - 1, None):
        refused = rt.owner_upload(over, declared_length=declared)
        _refusal(refused, "invalid_request", 4, ["file_too_large"])
        assert "mapping" not in refused and "file_digest" not in refused

    # A shortfall longer than any closing delimiter (a boundary is at most
    # 70 characters, RFC 2046): the body ends inside the file's own bytes,
    # at most the limit of them arrive, and the file part ends before its
    # delimiter — file_unreadable, not file_too_large (State 5).
    short = len(over) - 1024
    assert short <= IMPORT_FILE_MAX_BYTES
    refused = rt.owner_upload(over, declared_length=short)
    _refusal(refused, "invalid_request", 4, ["file_unreadable"])
    assert "mapping" not in refused and "file_digest" not in refused

    # The kept file stays kept: its mapping is still shown, by its digest
    # (A19 rule 4: "replaces no file the session kept"; A16 rule 2).
    mapping = rt.owner(
        "show_import_mapping",
        import_choices={"picks": [{"project_id": "v1-size-project"}], "customers": []},
    )
    assert mapping["answer_kind"] == "import_mapping"
    assert mapping["file_digest"] == accepted["file_digest"]
    # Nothing was written by any of it (A16 rule 1).
    assert _store(rt) == rows_before


def test_every_shown_value_escaped_csp_forbids_script(semantic_runtime):
    """Every stored value a page shows, in each kind of place — an element's
    content, an attribute's value, a value of a link's query — is shown as
    that text; the page holds no element and no attribute made from it; a
    value in a link's query reads back whole; every page forbids every script
    (A19 rules 1, 2; A19-1, A19-2)."""
    rt = semantic_runtime

    # Values written by the owner, by Kernel and by the import.
    customer = rt.owner(
        "record_customer",
        request_id=rt.new_request_id(),
        customer={"name": HOSTILE, "customer_kind": "person"},
    )
    assert customer["answer_kind"] == "customer"
    customer_ref = customer["customer"]["customer_ref"]
    card = rt.owner(
        "create_project",
        request_id=rt.new_request_id(),
        project={"display_name": HOSTILE, "alias": HOSTILE, "address": HOSTILE,
                 "customer_ref": customer_ref},
    )["card"]
    project_id = card["project_id"]
    rt.owner("add_room", target=project_id, request_id=rt.new_request_id(), room_name=HOSTILE)
    _grant_session(rt, HOSTILE_QUERY, project_id, request_text=HOSTILE)
    # A plain session beside it, granted the same project: its links are the
    # control the hostile session's links are compared with (origin, path,
    # parameters), so "unchanged" is measured, not assumed.
    _grant_session(rt, PLAIN_SESSION, project_id)

    # Element content: every page showing a stored value shows it as text.
    pages = [
        ("/", None),
        ("/read_project", {OWNER_TARGET_PARAMETER: project_id}),
        ("/list_customers", None),
        ("/read_customer", {OWNER_TARGET_PARAMETER: customer_ref}),
        ("/list_sessions", None),
        ("/read_session", {OWNER_TARGET_PARAMETER: HOSTILE_QUERY}),
    ]
    for path, query in pages:
        status, page, _ = _get(rt, path, query)
        assert status == 200, path
        assert HOSTILE in page.text(), path

    # A value of a link's query: the session's identity, the target of the
    # session's links and forms (OWNER_TARGET_PARAMETER), reads back from
    # each as that one whole value, path and other parameters unchanged.
    def shape(links):
        # A link's origin, path and parameter names: what the value must not
        # change (A19 Required test 5).
        return sorted(
            (parts.scheme, parts.netloc, parts.path, parts.fragment, tuple(sorted(q)))
            for parts, q in links
        )

    for path, hostile_query, plain_query in (
        ("/list_sessions", None, None),
        ("/read_session", {OWNER_TARGET_PARAMETER: HOSTILE_QUERY},
         {OWNER_TARGET_PARAMETER: PLAIN_SESSION}),
    ):
        _, page, _ = _get(rt, path, hostile_query)
        assert HOSTILE_QUERY in page.text()
        targets = _targets(page)
        session_links = [
            (parts, q) for parts, q in targets
            if q[OWNER_TARGET_PARAMETER] not in ([project_id], [PLAIN_SESSION])
        ]
        assert session_links, f"{path}: no link or form names the session"
        for parts, q in session_links:
            assert q == {OWNER_TARGET_PARAMETER: [HOSTILE_QUERY]}, (path, parts)
            assert parts.path in OWNER_PATHS
            assert parts.fragment == ""
            assert parts.scheme in ("", "http", "https")
        # Control: the plain session's links, on the same page for the list
        # and on its own page for the card, have the very same origins, paths
        # and parameters — the hostile value changed none of them.
        if plain_query is None:
            plain_links = [(p_, q) for p_, q in targets
                           if q[OWNER_TARGET_PARAMETER] == [PLAIN_SESSION]]
        else:
            _, plain_page, _ = _get(rt, path, plain_query)
            plain_links = [(p_, q) for p_, q in _targets(plain_page)
                           if q[OWNER_TARGET_PARAMETER] == [PLAIN_SESSION]]
        assert plain_links, f"{path}: no link or form names the plain session"
        assert shape(session_links) == shape(plain_links), path

    # An attribute's value: the import's confirmation step carries its picks
    # as form fields (owner_interface: "a confirmation step's form MUST carry
    # the step's inputs as the fields of OwnerValues").
    content = rt.export_file(
        projects=[_export_project("v1-hostile", HOSTILE, HOSTILE)],
        rooms=[_export_room("v1-hostile-room", "v1-hostile", HOSTILE)],
        pointers=[],
    )
    uploaded = rt.owner_upload(content, declared_length=len(content))
    assert uploaded["answer_kind"] == "import_upload"
    pick = {
        "import_choices.picks.0.project_id": "v1-hostile",
        "import_choices.picks.0.display_name": HOSTILE,
        "import_choices.picks.0.alias": HOSTILE,
    }
    status, page, _ = _get(rt, "/show_import_mapping", pick)
    assert status == 200
    assert HOSTILE in page.text()
    status, html, headers = rt.owner_http(
        "POST",
        "/show_confirmation",
        form={
            OWNER_CSRF_FIELD: _csrf(rt),
            "confirm_action": "confirm_import",
            "upload_number": str(uploaded["upload_number"]),
            "file_digest": uploaded["file_digest"],
            **pick,
        },
    )
    assert status == 200
    page = _assert_page_safe(status, html, headers)
    assert HOSTILE in page.attribute_values()

    # Every page forbids every script: a refusal's page and the sign-in page
    # too (A19 rule 2, State 5 serve_owner_request Outputs).
    status, html, headers = rt.owner_http(
        "GET", "/read_project", query={OWNER_TARGET_PARAMETER: "no-such-project"}
    )
    assert status == 404  # not_found (REFUSAL_HTTP_STATUSES)
    _assert_page_safe(status, html, headers)
    status, html, headers = rt.owner_http("GET", "/", cookie=None)
    assert status == 422  # unauthenticated: the sign-in page
    _assert_page_safe(status, html, headers)


STATEMENT_NAME = "Robert'); DROP TABLE project_rows; -- \"x\" /* */ ;"
STATEMENT_ALIAS = "'; DELETE FROM room_rows; --"


def test_query_language_in_name_not_executed(semantic_runtime):
    """A display name holding a quote, a semicolon, a comment mark and a
    statement of the store's query language is stored and read back as given;
    the store holds afterwards what it held, and the records the create
    writes, nothing else; a value choosing among fixed alternatives is
    checked against its closed list first (A19 rule 3, A19-2)."""
    rt = semantic_runtime
    # Something for a statement to remove, were it run.
    earlier = _create_project(rt, "Casa Previa")["project_id"]
    rt.owner("add_room", target=earlier, request_id=rt.new_request_id(), room_name="Sala")
    before = _store(rt)
    assert len(before["project_rows"]) == 1 and len(before["room_rows"]) == 1

    card = _create_project(rt, STATEMENT_NAME, address=STATEMENT_NAME, alias=STATEMENT_ALIAS)
    project_id = card["project_id"]
    read = rt.owner("read_project", target=project_id)["card"]
    assert read["display_name"] == STATEMENT_NAME
    assert read["alias"] == STATEMENT_ALIAS
    assert read["object_facts"]["address"] == STATEMENT_NAME

    after = _store(rt)
    # Every table but the three the create writes is unchanged, row for row.
    for table in TABLES:
        if table not in ("project_rows", "audit_entry_rows", "audit_sequence_rows"):
            assert after[table] == before[table], table
    # The create wrote one Project, one entry, and moved the counter by one
    # (A14 rule 1, M12); every earlier row is as it was.
    for table in ("project_rows", "audit_entry_rows"):
        assert all(row in after[table] for row in before[table]), table
        assert len(after[table]) == len(before[table]) + 1, table
    new_project = [r for r in after["project_rows"] if r not in before["project_rows"]]
    assert [r["project_id"] for r in new_project] == [project_id]
    assert _json(new_project[0]["record"])["display_name"] == STATEMENT_NAME
    before_last = before["audit_sequence_rows"][0]["last_sequence_number"]
    assert after["audit_sequence_rows"][0]["last_sequence_number"] == before_last + 1

    # A value that selects among fixed alternatives is checked against its
    # closed list first (A19 rule 3; ProjectListChoice: `active`,
    # `with_archived`): refused at stage (4), outside_closed_list.
    refused = rt.service("cabinet", "list_projects", {"list_choice": "active' OR '1'='1"})
    _refusal(refused, "invalid_request", 4, ["outside_closed_list"])
    # Control: a member of the list is accepted.
    listed = rt.service("cabinet", "list_projects", {"list_choice": "with_archived"})
    assert sorted(i["project_id"] for i in listed["items"]) == sorted([earlier, project_id])
    assert _store(rt) == after


MARKUP = "<b onclick=\"x()\">Casa</b> & 'Hogar'"
STATEMENT = "'); DROP TABLE customer_rows; --"
PROGRAM = "__import__('os').system('id')"
TEMPLATE = "{{7*7}} ${7*7} =7*7"


def test_import_values_read_as_text_not_evaluated(semantic_runtime):
    """An import file whose values hold markup, a statement of the store's
    query language and text written as program code is read into those same
    values as text, unchanged; nothing in it is executed or evaluated (A19
    rule 4, A19-2)."""
    rt = semantic_runtime
    # Records a statement could remove, were it run.
    rt.owner(
        "record_customer",
        request_id=rt.new_request_id(),
        customer={"name": "Cliente Previo", "customer_kind": "person"},
    )
    earlier = _create_project(rt, "Casa Previa")["project_id"]
    rt.owner("add_room", target=earlier, request_id=rt.new_request_id(), room_name="Sala")
    content = rt.export_file(
        projects=[_export_project("v1-p1", MARKUP, STATEMENT, customer_ref=STATEMENT)],
        rooms=[
            _export_room("v1-r1", "v1-p1", PROGRAM),
            _export_room("v1-r2", "v1-p1", TEMPLATE),
        ],
        pointers=[
            {
                "pointer_id": "v1-ptr1",
                "project_id": "v1-p1",
                "artifact_type": "estimate",  # ARTIFACT_TYPE_OWNERS
                "owner_service": "presupro",
                "version": "1",
                "status": "published",
                "uri": "https://example.invalid/" + PROGRAM,
                "payload_ref": TEMPLATE,
                "content_digest": None,
                "created_at": "2025-03-01T12:00:00+00:00",
                "superseded_at": None,
            }
        ],
    )
    before = _store(rt)
    uploaded = rt.owner_upload(content, declared_length=len(content))
    assert uploaded["answer_kind"] == "import_upload"
    assert [p["project_id"] for p in uploaded["projects"]] == ["v1-p1"]

    choices = {
        "picks": [{"project_id": "v1-p1"}],  # arrives under its v1 name (A16 rule 1)
        "customers": [
            {"v1_value": STATEMENT, "name": "Cliente Importado",
             "customer_kind": "company", "is_tax_id": False}
        ],
    }
    mapped = rt.owner("show_import_mapping", import_choices=choices)
    assert mapped["answer_kind"] == "import_mapping"
    mapping = mapped["mapping"]
    assert mapping["clean"] is True
    [project] = mapping["projects"]
    assert project["display_name"] == MARKUP
    assert sorted(r["name"] for r in project["rooms"]) == sorted([PROGRAM, TEMPLATE])
    assert [(p["uri"], p["payload_ref"]) for p in project["pointers"]] == [
        ("https://example.invalid/" + PROGRAM, TEMPLATE)
    ]
    assert [c["v1_value"] for c in mapping["customers"]] == [STATEMENT]
    assert _store(rt) == before  # the mapping changes nothing (A16 rule 1)

    accepted = rt.owner(
        "confirm_import",
        upload_number=uploaded["upload_number"],
        file_digest=uploaded["file_digest"],
        import_choices=choices,
    )
    assert accepted["answer_kind"] == "import_accepted"
    assert [c["v1_value"] for c in accepted["customers"]] == [STATEMENT]

    # Read back as the same text: nothing evaluated (49 never appears).
    card = rt.owner("read_project", target="v1-p1")["card"]
    assert card["display_name"] == MARKUP
    assert card["object_facts"]["address"] == STATEMENT
    assert sorted(r["name"] for r in card["rooms"]) == sorted([PROGRAM, TEMPLATE])
    pointers = rt.owner("list_pointers", target="v1-p1")["pointers"]
    assert [(p["uri"], p["payload_ref"]) for p in pointers] == [
        ("https://example.invalid/" + PROGRAM, TEMPLATE)
    ]
    # Nothing executed: every table is still there, the statement removed no
    # Customer — the one the import made is stored — and every earlier row
    # stands.
    after = _store(rt)
    assert len(after["customer_rows"]) == len(before["customer_rows"]) + 1
    for table in TABLES:
        if table != "audit_sequence_rows":  # the counter moves (M12)
            assert all(row in after[table] for row in before[table]), table
    imported_rooms = sorted(r["name"] for r in after["room_rows"] if r["project_id"] == "v1-p1")
    assert imported_rooms == sorted([PROGRAM, TEMPLATE])
