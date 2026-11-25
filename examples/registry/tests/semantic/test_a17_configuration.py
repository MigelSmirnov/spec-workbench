"""Witness tests for accepted decision A17 (02_rules_installation.md).

Configuration and secrets are checked before Registry serves: the start reads
exactly the `REGISTRY_` items of rule 1, checks them in rule 2's order and
serves nothing until every check passed; a failed check stops the start with
one diagnostic naming the item and never its value; the four service tokens
and the service API's address go all five or none, none being an owner-only
start; secrets are at least `SECRET_MIN_BYTES` UTF-8 bytes and pairwise
distinct; addresses are `host:port` in the strict text form of rule 1, on
different ports, bound exclusively; a start that fails after making a new
store removes it. Each witness test carries the name its Required test
declares; the untagged Required tests 4 and 6 are here too.

Expected values come from the design: A17's rules; State 5
(`50_public_apis_0_conventions.md` "Diagnostics": one line naming the failure,
never a value); State 6 `RuntimeSettings` / `config.runtime_environment_variables`
(`global_spec.json`: `REGISTRY_STORE_PATH` … `REGISTRY_SERVICE_LISTEN`, one
per field); the data closure (`SECRET_MIN_BYTES` = 32, `LISTEN_PORT_MIN` = 1,
`LISTEN_PORT_MAX` = 65535, `STORE_TEMPORARY_SUFFIX` = ".new"); State 7
(`80_notes.md` `load_configuration`: the diagnostic names the failed item "by
its RuntimeSettings field name and never its value", items in the order
store_path, backup_dir, backup_key, owner_credential, owner_listen,
token_presupro, token_client_portal, token_cabinet, token_cabinet_kernel,
service_listen; `start_instance`: a listener failure names the surface,
never its address).

The Factory project supplies the ``semantic_runtime`` pytest fixture
(`RUNTIME_SURFACE.md`). These tests are about the configuration, so each one
configures and starts the instance itself.

Fixture surface used here:

- capabilities ``configure(**settings)`` (State 6 `RuntimeSettings` field
  names; a setting given as ``None`` is unset — its variable absent),
  ``start()`` -> ``None`` or the diagnostic line, ``stop()``;
- ``configure_environment(variables)``: the instance's next start sees exactly these environment variables beside
  the host's own non-`REGISTRY_` ones, the fixture's configuration not
  applied; reaches ``configuration.load_runtime_settings`` (State 6
  `config.runtime_environment_variables`);
- ``owner(...)``, ``sign_in()``, ``new_request_id()`` and ``service(...)``,
  which, when no service API listener is open, raises ``OSError`` — the
  connection failing, with no answer (rule 1);
- ``store_rows(table)``.

Listeners are probed from the test with plain sockets at the addresses the
test configured: whether an endpoint accepts a connection or can be bound is
the observable of rules 1 and 2. The store and backup directories are the
test's own temporary directories, set up before Registry starts, as a host's
administration sets them up.
"""

import itertools
import re
import socket
import sqlite3
from contextlib import contextmanager

SECRET_MIN_BYTES = 32  # data closure SECRET_MIN_BYTES (SPEC_STANDARD §15.3.1)
STORE_TEMPORARY_SUFFIX = ".new"  # data closure STORE_TEMPORARY_SUFFIX
STORE_VERSION = 1  # data closure STORE_VERSION

TOKEN_ITEMS = (
    "token_presupro",
    "token_client_portal",
    "token_cabinet",
    "token_cabinet_kernel",
)
SECRET_ITEMS = ("backup_key", "owner_credential") + TOKEN_ITEMS

# global_spec.json `config.variables`: one environment variable per item.
VARIABLE = {
    "store_path": "REGISTRY_STORE_PATH",
    "backup_dir": "REGISTRY_BACKUP_DIR",
    "backup_key": "REGISTRY_BACKUP_KEY",
    "owner_credential": "REGISTRY_OWNER_CREDENTIAL",
    "owner_listen": "REGISTRY_OWNER_LISTEN",
    "token_presupro": "REGISTRY_CREDENTIAL_PRESUPRO",
    "token_client_portal": "REGISTRY_CREDENTIAL_CLIENT_PORTAL",
    "token_cabinet": "REGISTRY_CREDENTIAL_CABINET",
    "token_cabinet_kernel": "REGISTRY_CREDENTIAL_CABINET_KERNEL",
    "service_listen": "REGISTRY_SERVICE_LISTEN",
}

# global_spec.json "persistence": every table of the store.
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

# Distinct secrets of more than SECRET_MIN_BYTES ASCII bytes.
SECRETS = {
    "backup_key": "a17-backup-key-0f3e9c1d7b2a5e8f6c4d1a0b9e",
    "owner_credential": "a17-owner-credential-8d2b6f0a4c9e1b3d7f5a",
    "token_presupro": "a17-token-presupro-1c7e3a9f5b0d2e8c4a6f",
    "token_client_portal": "a17-token-client-portal-6b4d0f2e8a1c9e7b",
    "token_cabinet": "a17-token-cabinet-3e5a7c9b1d0f2e4a6c8b",
    "token_cabinet_kernel": "a17-token-cabinet-kernel-9a7c5e3b1f0d2c4e",
}


def _free_port(family=socket.AF_INET, host="127.0.0.1"):
    with socket.socket(family, socket.SOCK_STREAM) as probe:
        probe.bind((host, 0))
        return probe.getsockname()[1]


def _settings(tmp_path, **override):
    """A complete configuration (rule 1), with `override` replacing items."""
    (tmp_path / "store").mkdir(exist_ok=True)
    (tmp_path / "backups").mkdir(exist_ok=True)
    owner_port = _free_port()
    service_port = _free_port()
    while service_port == owner_port:
        service_port = _free_port()
    settings = {
        "store_path": str(tmp_path / "store" / "registry.sqlite"),
        "backup_dir": str(tmp_path / "backups"),
        "owner_listen": f"127.0.0.1:{owner_port}",
        "service_listen": f"127.0.0.1:{service_port}",
        **SECRETS,
    }
    settings.update(override)
    return settings


def _owner_only(settings):
    return {**settings, **{item: None for item in TOKEN_ITEMS}, "service_listen": None}


def _endpoint(address):
    """(host, port) of an address of rule 1's form."""
    host, _, port = address.rpartition(":")
    return host.strip("[]"), int(port)


def _accepts(address):
    """True when something accepts a TCP connection at `address`; an address
    that is not of rule 1's form names no endpoint and accepts nothing."""
    try:
        host, port = _endpoint(address)
        socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except (ValueError, OverflowError, OSError):
        return False
    family = socket.AF_INET6 if ":" in host else socket.AF_INET
    with socket.socket(family, socket.SOCK_STREAM) as client:
        client.settimeout(2)
        try:
            client.connect((host, port))
        except OSError:
            return False
        return True


@contextmanager
def _occupied(address):
    """Hold the endpoint with a listening socket of the test's own."""
    host, port = _endpoint(address)
    family = socket.AF_INET6 if ":" in host else socket.AF_INET
    blocker = socket.socket(family, socket.SOCK_STREAM)
    try:
        blocker.bind((host, port))
        blocker.listen(1)
        yield
    finally:
        blocker.close()


def _names(diagnostic, item):
    """The diagnostic names `item` by its RuntimeSettings field name, as a
    whole word (`token_cabinet` is not named by `token_cabinet_kernel`)."""
    return re.search(rf"(?<![A-Za-z0-9_]){re.escape(item)}(?![A-Za-z0-9_])", diagnostic) is not None


def _assert_no_value(diagnostic, settings):
    """Rule 2, rule 6, R0-37: a diagnostic never holds a configured value."""
    assert "\n" not in diagnostic.rstrip("\n")  # one line (State 5 "Diagnostics")
    for value in settings.values():
        if value:
            assert value not in diagnostic, diagnostic


def _start(rt, settings):
    rt.configure(**settings)
    return rt.start()


def _starts(rt, settings):
    """The start passes, serves (control), and is stopped again."""
    diagnostic = _start(rt, settings)
    assert diagnostic is None, diagnostic
    assert _accepts(settings["owner_listen"])
    rt.stop()


def _stops(rt, settings, item):
    """The start fails naming `item`, no value, and serves nothing (A17-1)."""
    diagnostic = _start(rt, settings)
    assert diagnostic is not None, f"start passed; expected it to name {item}"
    assert _names(diagnostic, item), (item, diagnostic)
    _assert_no_value(diagnostic, settings)
    for listen in ("owner_listen", "service_listen"):
        if settings.get(listen):
            assert not _accepts(settings[listen]), listen
    return diagnostic


def _assert_no_service_listener(rt):
    try:
        answer = rt.service("presupro", "list_projects", {"list_choice": "active"})
    except OSError:
        return
    raise AssertionError(f"an owner-only start answered a service call: {answer}")


# --------------------------------------------------------------------------


def test_missing_token_stops_start_none_owner_only(semantic_runtime, tmp_path):
    """Required test 1 (A17-1): some service tokens without Client Portal's
    stop the start naming that item; none of the four and no service API
    address is an owner-only start (rules 1, 2)."""
    rt = semantic_runtime
    full = _settings(tmp_path)
    _stops(rt, {**full, "token_client_portal": None}, "token_client_portal")

    # Not just "a token is missing": the first missing one in rule 1's order.
    diagnostic = _stops(
        rt, {**full, "token_client_portal": None, "token_cabinet": None},
        "token_client_portal",
    )
    assert not _names(diagnostic, "token_cabinet"), diagnostic
    assert not _names(diagnostic, "token_presupro"), diagnostic

    # None of the five: an owner-only start, the owner interface served.
    owner_only = _owner_only(full)
    assert _start(rt, owner_only) is None
    assert rt.sign_in()["answer_kind"] == "signed_in"
    _assert_no_service_listener(rt)
    assert not _accepts(full["service_listen"])
    rt.stop()

    # Control: the complete configuration serves both surfaces.
    assert _start(rt, full) is None
    assert _accepts(full["service_listen"])
    rt.stop()


def test_equal_secrets_stop_start(semantic_runtime, tmp_path):
    """Required test 2 (A17-2): two services with one token stop the start,
    and so does each other pair of equal secrets (rule 4)."""
    rt = semantic_runtime
    full = _settings(tmp_path)
    shared = "a17-shared-secret-5d3b1f9e7c2a4086e1b3d5f7"
    # A17-2 quantifies over every pair of the six secrets: all fifteen pairs
    # of the four tokens, the owner credential and the backup key.
    pairs = list(itertools.combinations(SECRET_ITEMS, 2))
    assert len(pairs) == 15
    for first, second in pairs:
        settings = {**full, first: shared, second: shared}
        diagnostic = _start(rt, settings)
        assert diagnostic is not None, (first, second)
        # The failed item is one of the pair (rule 2); never the value.
        assert _names(diagnostic, first) or _names(diagnostic, second), diagnostic
        _assert_no_value(diagnostic, settings)
        assert not _accepts(full["owner_listen"])

    # Control: all distinct, the same shared value in one item only.
    _starts(rt, {**full, "owner_credential": shared})


def test_secret_length_counted_in_utf8_bytes(semantic_runtime, tmp_path):
    """Required test 3 (A17-3): a 16-byte token stops the start; for each kind
    of secret one byte short of SECRET_MIN_BYTES stops it, exactly
    SECRET_MIN_BYTES passes; the length is UTF-8 bytes, not characters."""
    rt = semantic_runtime
    full = _settings(tmp_path)

    _stops(rt, {**full, "token_presupro": "t" * 16}, "token_presupro")

    # Every secret of the configuration, each token among them (A17-3).
    for item in SECRET_ITEMS:
        short = (item[:6] + "-" + "x" * SECRET_MIN_BYTES)[: SECRET_MIN_BYTES - 1]
        exact = (item[:6] + "-" + "y" * SECRET_MIN_BYTES)[:SECRET_MIN_BYTES]
        assert len(short.encode("utf-8")) == SECRET_MIN_BYTES - 1
        assert len(exact.encode("utf-8")) == SECRET_MIN_BYTES
        _stops(rt, {**full, item: short}, item)
        _starts(rt, {**full, item: exact})

    # 16 two-byte characters: 16 characters, 32 bytes — accepted.
    two_byte = "é" * 16
    assert len(two_byte) == 16 and len(two_byte.encode("utf-8")) == 32
    _starts(rt, {**full, "token_client_portal": two_byte})
    # 15 two-byte characters and one one-byte character: 31 bytes — stops.
    thirty_one = "ü" * 15 + "a"
    assert len(thirty_one.encode("utf-8")) == 31
    _stops(rt, {**full, "token_client_portal": thirty_one}, "token_client_portal")


def test_start_diagnostic_never_holds_a_secret(semantic_runtime, tmp_path):
    """Required test 4: no start diagnostic contains a secret's value
    (rules 2, 6; R0-37) — for each check that can fail on a secret and for
    failures of other items while the secrets are set."""
    rt = semantic_runtime
    full = _settings(tmp_path)
    failing = [
        {**full, "token_cabinet": "short-token"},  # length
        {**full, "owner_credential": full["backup_key"]},  # distinctness
        {**full, "token_cabinet": None},  # all-or-none
        {**full, "owner_listen": "localhost:1"},  # form, secrets set
        {**full, "backup_dir": str(tmp_path / "no-such-dir")},  # probe
    ]
    for settings in failing:
        diagnostic = _start(rt, settings)
        assert diagnostic is not None, settings
        for item in SECRET_ITEMS:
            value = settings.get(item)
            if value:
                assert value not in diagnostic, (item, diagnostic)
                # nor a recognisable part of it
                assert value[-SECRET_MIN_BYTES // 2 :] not in diagnostic
    _starts(rt, full)


def test_listener_failure_serves_nothing_keeps_store(semantic_runtime, tmp_path):
    """Required test 5 (A17-4): a start that made its store new and then
    cannot open a listener — the owner interface's, or the service API's
    after the owner interface's was opened, which is closed again — serves
    nothing and removes that store; over an existing store it leaves the
    store's records as they were (rule 2). A removal that fails, leaving an
    empty store, cannot be made to happen here without failing the store's
    making too: carried. The owner-only start's missing service listener is
    Required test 1's."""
    rt = semantic_runtime
    full = _settings(tmp_path)
    store = tmp_path / "store" / "registry.sqlite"
    temporary = tmp_path / "store" / ("registry.sqlite" + STORE_TEMPORARY_SUFFIX)

    # New store, owner interface's endpoint taken: stops, removes the store.
    # Its directory is the test's and writable, so the removal cannot fail
    # and the "left as an empty store" branch does not apply.
    assert not store.exists()
    with _occupied(full["owner_listen"]):
        diagnostic = _start(rt, full)
    assert diagnostic is not None
    host, port = _endpoint(full["owner_listen"])
    assert full["owner_listen"] not in diagnostic and str(port) not in diagnostic
    assert not store.exists() and not temporary.exists()
    assert not _accepts(full["service_listen"])

    # New store, service API's endpoint taken after the owner's was opened:
    # the owner's is closed, nothing served, the store removed.
    with _occupied(full["service_listen"]):
        assert _start(rt, full) is not None
        assert not _accepts(full["owner_listen"])
    assert not store.exists() and not temporary.exists()

    # Existing store: made by a passing start, holding a project.
    assert _start(rt, full) is None
    created = rt.owner(
        "create_project",
        request_id=rt.new_request_id(),
        project={
            "display_name": "Obra A17",
            "alias": None,
            "customer_ref": None,
            "address": "Calle Real 1, Valencia",
            "object_kind": None,
            "floor_area": None,
            "rooms_count": None,
            "floor": None,
        },
    )
    project_id = created["card"]["project_id"]
    rt.stop()
    before = {table: rt.store_rows(table) for table in TABLES}
    assert [r["project_id"] for r in before["project_rows"]] == [project_id]

    for taken in ("owner_listen", "service_listen"):
        with _occupied(full[taken]):
            assert _start(rt, full) is not None
            assert not _accepts(full["owner_listen"])
        assert store.exists()
        assert {table: rt.store_rows(table) for table in TABLES} == before

    # Control: with both endpoints free the same store starts and answers.
    assert _start(rt, full) is None
    card = rt.owner("read_project", target=project_id)
    assert card["answer_kind"] == "project_card"
    rt.stop()


def test_new_store_holds_only_audit_sequence_at_zero(semantic_runtime, tmp_path):
    """Required test 6: a store made new holds exactly one audit sequence
    (M12), at 0, and no other record; a file of the store's temporary name
    left by an interrupted start is removed by the next start, which makes a
    new store with one sequence at 0 (rule 5)."""
    rt = semantic_runtime
    full = _settings(tmp_path)
    store = tmp_path / "store" / "registry.sqlite"
    temporary = tmp_path / "store" / ("registry.sqlite" + STORE_TEMPORARY_SUFFIX)
    # What an interrupted start leaves: the temporary file, no store.
    temporary.write_bytes(b"left by an interrupted start")
    assert not store.exists()

    assert _start(rt, full) is None
    rt.stop()
    assert store.exists() and not temporary.exists()
    rows = {table: rt.store_rows(table) for table in TABLES}
    (sequence,) = rows.pop("audit_sequence_rows")
    assert sequence["last_sequence_number"] == 0
    assert sequence["sequence"] == "audit"  # AuditSequenceName.audit
    assert all(found == [] for found in rows.values()), rows

    # Rule 5: the store carries the running release's version — a store of
    # another version fails the start, so the next start over it passes.
    assert _start(rt, full) is None
    rt.stop()
    assert {table: rt.store_rows(table) for table in TABLES}["audit_sequence_rows"] == [
        sequence
    ]


def test_unknown_variables_ignored_misspelt_item_missing(semantic_runtime, tmp_path):
    """Required test 7 (A17-1): variables that name no item are neither read
    nor checked; a misspelt name leaves its item unset (rule 1)."""
    rt = semantic_runtime
    full = _settings(tmp_path)
    environment = {VARIABLE[item]: value for item, value in full.items()}
    extra = {
        "REGISTRY_EXTRA": "a17-extra-value-not-an-item",
        "REGISTRY_": "a17-bare-prefix-value",
        "A17_UNPREFIXED": "a17-unprefixed-value",
    }

    rt.configure_environment({**environment, **extra})
    assert rt.start() is None
    assert _accepts(full["owner_listen"]) and _accepts(full["service_listen"])
    rt.stop()

    # The backup key misspelt: stops, naming the backup key as missing; no
    # extra variable's name or value in the diagnostic.
    misspelt_key = {k: v for k, v in environment.items() if k != "REGISTRY_BACKUP_KEY"}
    misspelt_key["REGISTRY_BACKUP_KEYY"] = full["backup_key"]
    rt.configure_environment({**misspelt_key, **extra})
    diagnostic = rt.start()
    assert diagnostic is not None and _names(diagnostic, "backup_key"), diagnostic
    for name, value in {**extra, "REGISTRY_BACKUP_KEYY": full["backup_key"]}.items():
        assert value not in diagnostic
        assert name not in diagnostic or name == "REGISTRY_", diagnostic
    assert "REGISTRY_EXTRA" not in diagnostic and "KEYY" not in diagnostic
    assert not _accepts(full["owner_listen"])

    # Three tokens and the fourth misspelt: stops naming that token.
    three = {k: v for k, v in environment.items() if k != "REGISTRY_CREDENTIAL_CABINET"}
    three["REGISTRY_CREDENTIAL_CABINE"] = full["token_cabinet"]
    rt.configure_environment(three)
    diagnostic = rt.start()
    assert diagnostic is not None and _names(diagnostic, "token_cabinet"), diagnostic
    assert not _accepts(full["owner_listen"])

    # Only a misspelt token, no other token and no service address: owner-only.
    owner_only = {
        k: v
        for k, v in environment.items()
        if k not in {VARIABLE[i] for i in TOKEN_ITEMS} | {"REGISTRY_SERVICE_LISTEN"}
    }
    owner_only["REGISTRY_CREDENTIAL_PRESUPROO"] = full["token_presupro"]
    rt.configure_environment(owner_only)
    assert rt.start() is None
    assert _accepts(full["owner_listen"])
    _assert_no_service_listener(rt)
    assert not _accepts(full["service_listen"])
    rt.stop()


def test_service_address_with_tokens_and_wellformed(semantic_runtime, tmp_path):
    """Required test 8 (A17-1): the service API's address goes with the four
    tokens; addresses are `host:port` with an IP host and a port of 1–65535;
    the two ports differ (rules 1, 2)."""
    rt = semantic_runtime
    full = _settings(tmp_path)
    _stops(rt, {**full, "service_listen": None}, "service_listen")
    diagnostic = _stops(
        rt, {**full, **{item: None for item in TOKEN_ITEMS}}, "token_presupro"
    )
    assert not _names(diagnostic, "service_listen"), diagnostic

    # Accepted forms (controls), each actually listening.
    port = _endpoint(full["service_listen"])[1]
    for address in (f"127.0.0.1:{port}", f"[::1]:{_free_port(socket.AF_INET6, '::1')}"):
        settings = {**full, "service_listen": address}
        assert _start(rt, settings) is None, address
        assert _accepts(address)
        rt.stop()

    # Refused forms, each naming the item and not echoing the value.
    for address in (
        f"localhost:{port}",
        "127.0.0.1",
        "127.0.0.1:0",  # below LISTEN_PORT_MIN
        "127.0.0.1:65536",  # above LISTEN_PORT_MAX
    ):
        _stops(rt, {**full, "service_listen": address}, "service_listen")

    # One port for both addresses: named as the service API's address.
    # (The Required test's 8781 replaced by a port free on the test host, so
    # that a listener of another program cannot pass for Registry's.)
    one = _endpoint(full["owner_listen"])[1]
    same_port = {**full, "owner_listen": f"127.0.0.1:{one}", "service_listen": f"0.0.0.0:{one}"}
    diagnostic = _stops(rt, same_port, "service_listen")
    assert not _names(diagnostic, "owner_listen"), diagnostic


def test_address_text_form_and_exclusive_bind(semantic_runtime, tmp_path):
    """Required test 9 (A17-1): a zone identifier, an IPv4-mapped IPv6 host,
    a leading zero in an IPv4 number or in the port each stop the start; a
    running listener is bound exclusively, and an IPv6 listener takes no IPv4
    connection (rule 1)."""
    rt = semantic_runtime
    full = _settings(tmp_path)
    port = _endpoint(full["service_listen"])[1]
    for address in (
        f"[fe80::1%eth0]:{port}",
        f"[::ffff:127.0.0.1]:{port}",
        f"127.0.0.01:{port}",
        f"127.0.0.1:0{port}",
    ):
        _stops(rt, {**full, "service_listen": address}, "service_listen")

    # Exclusive bind: while Registry runs, a second socket — even one asking
    # for address and port reuse — cannot bind the service API's endpoint.
    assert _start(rt, full) is None
    attempts = [(), (socket.SO_REUSEADDR,)]
    if hasattr(socket, "SO_REUSEPORT"):
        attempts.append((socket.SO_REUSEADDR, socket.SO_REUSEPORT))
    for options in attempts:
        second = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            for option in options:
                second.setsockopt(socket.SOL_SOCKET, option, 1)
            try:
                second.bind(("127.0.0.1", port))
            except OSError:
                pass
            else:
                raise AssertionError(f"second bind succeeded with {options}")
        finally:
            second.close()
    assert _accepts(full["service_listen"])
    rt.stop()

    # An IPv6 listener on the unspecified address accepts IPv6 alone.
    v6_port = _free_port(socket.AF_INET6, "::")
    v6 = {**full, "service_listen": f"[::]:{v6_port}"}
    assert _start(rt, v6) is None
    assert _accepts(f"[::1]:{v6_port}")  # control: IPv6 is served
    assert not _accepts(f"127.0.0.1:{v6_port}")  # no IPv4-mapped connection
    rt.stop()


def test_failed_check_stops_before_any_listener(semantic_runtime, tmp_path):
    """Required test 10 (A17-1): each check made before the listeners — a
    configuration item, a backup location that cannot be written, an existing
    store failing its check or of another version, a new store that cannot be
    made — stops the start before any listener is opened; when the service
    API's listener cannot be opened after the owner interface's, the owner's
    is closed and nothing is served (rule 2)."""
    rt = semantic_runtime
    full = _settings(tmp_path)

    # Inputs the host could hand Registry, made before it starts: a file that
    # is no SQLite database; a SQLite database of another store version
    # (rule 5: "a store of another version … fails the start"); a regular
    # file where the backup directory should be (the probe cannot create a
    # file in it, A18 rule 5); a directory under the store's temporary name,
    # which the start cannot remove as a file while the store is absent
    # (rule 5, so no new store can be made).
    garbage = tmp_path / "garbage.sqlite"
    garbage.write_bytes(b"not a database " * 64)
    other_version = tmp_path / "other.sqlite"
    connection = sqlite3.connect(other_version)
    connection.execute("CREATE TABLE unrelated (x INTEGER)")
    connection.execute(f"PRAGMA user_version = {STORE_VERSION + 1}")
    connection.commit()
    connection.close()
    not_a_directory = tmp_path / "backups-file"
    not_a_directory.write_bytes(b"")
    blocked = tmp_path / "blocked"
    blocked.mkdir()
    (blocked / ("registry.sqlite" + STORE_TEMPORARY_SUFFIX)).mkdir()
    inputs_before = {
        garbage: garbage.read_bytes(),
        other_version: other_version.read_bytes(),
    }

    cases = {
        "configuration item": ({**full, "owner_credential": "too-short"}, "owner_credential"),
        "backup location not writable": (
            {**full, "backup_dir": str(not_a_directory)},
            "backup_dir",
        ),
        "store does not open": ({**full, "store_path": str(garbage)}, None),
        "store of another version": ({**full, "store_path": str(other_version)}, None),
        "new store cannot be made": (
            {**full, "store_path": str(blocked / "registry.sqlite")},
            None,
        ),
    }
    for case, (settings, item) in cases.items():
        # With both endpoints free: stops, serves nothing.
        free = _start(rt, settings)
        assert free is not None, case
        assert not _accepts(settings["owner_listen"]), case
        assert not _accepts(settings["service_listen"]), case
        if item is not None:
            assert _names(free, item), (case, free)
        # With the owner interface's endpoint taken: the same diagnostic —
        # a start that opened a listener first would fail on the listener.
        with _occupied(settings["owner_listen"]):
            taken = _start(rt, settings)
        assert taken == free, (case, free, taken)

    # Existing stores were left as they were (rule 5: a start never brings a
    # store to another version), and no store was made beside the blocked one.
    for path, content in inputs_before.items():
        assert path.read_bytes() == content, path
    assert not (blocked / "registry.sqlite").exists()

    # The service API's endpoint taken: the owner interface's was opened and
    # is closed again; nothing served on either.
    with _occupied(full["service_listen"]):
        assert _start(rt, full) is not None
        assert not _accepts(full["owner_listen"])

    # Control: the complete configuration starts and serves both.
    assert _start(rt, full) is None
    assert _accepts(full["owner_listen"]) and _accepts(full["service_listen"])
    rt.stop()
