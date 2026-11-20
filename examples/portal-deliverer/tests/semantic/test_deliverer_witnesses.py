"""State 2 witnesses; Factory supplies semantic_runtime (see RUNTIME_SURFACE.md)."""
import hashlib
from datetime import datetime, timezone
from io import BytesIO

import pytest
from PIL import Image

PROJECT = "b13c5547-fe49-439d-a7d8-0a02b2c19a7b"
PHOTO = "7c9e6679-7425-40de-944b-e07fc1f90ae7"
OTHER = "52b132d7-0a94-44e7-9aab-63a77ca770f2"
MODIFIED = datetime(2026, 11, 18, 11, tzinfo=timezone.utc).timestamp()


def jpeg(color=(200, 30, 30), exif=None, **metadata):
    out = BytesIO()
    Image.new("RGB", (3000, 1500), color).save(out, "JPEG", exif=exif or Image.Exif(), **metadata)
    return out.getvalue()


def seed(r, name="a.jpg", content=None):
    content = jpeg() if content is None else content
    r.source.put(name, content, mtime=MODIFIED)
    return hashlib.sha256(content).hexdigest()


def place(r, sid, name="a.jpg"):
    return r.deliver_project_photo(PROJECT, name, sid)


def mark(r, sid, photo=PHOTO):
    return r.mark_photo_published(PROJECT, sid, photo)


def scan(r):
    return {x["name"]: x for x in r.scan_project_photos(PROJECT)["items"]}


def refused(action, code):
    with pytest.raises(Exception) as error:
        action()
    assert error.value.code == code


def test_deliverer_a01_no_operation_changes_the_source_folder(semantic_runtime):
    r = semantic_runtime
    sid = seed(r)
    seed(r, "sub/notes.txt", b"notes")
    before = r.source.snapshot()
    scan(r)
    place(r, sid)
    place(r, sid)
    mark(r, sid)
    assert r.source.snapshot() == before


def test_deliverer_a01_a_name_a_scan_would_not_report_is_not_delivered(semantic_runtime):
    r = semantic_runtime
    sid = seed(r)
    seed(r, "sub/a.jpg")
    r.source.symlink("linked.jpg", "a.jpg")
    r.source.symlink("linked_folder", "sub")
    for name in ["", "/etc/passwd", "../a.jpg", "sub/../a.jpg", "./a.jpg", "sub//a.jpg", "sub/", ".hidden.jpg", ".stversions/a.jpg", "a.jpg.tmp", "linked.jpg", "linked_folder/a.jpg", "sub", "nul\0.jpg"]:
        before = r.durable_snapshot()
        with r.trace_source_opens() as trace:
            answer = place(r, sid, name)
        assert (answer["status"], answer["reason"]) == ("failed", "not_ready_or_absent")
        assert trace == []
        assert r.durable_snapshot() == before


def test_deliverer_a01_a_syncthing_conflict_copy_is_neither_offered_nor_placed(semantic_runtime):
    r = semantic_runtime
    seed(r)
    for prefix in ["", "sub/"]:
        for flag in ["sync-conflict", "SYNC-CONFLICT", "SyNc-CoNfLiCt"]:
            seed(r, prefix + "a." + flag + "-20261118-120000-ABCDEF1.jpg")
    assert set(scan(r)) == {"a.jpg"}


def test_deliverer_a02_a_placed_photo_keeps_no_metadata_and_the_source_is_untouched(semantic_runtime):
    r = semantic_runtime
    exif = Image.Exif()
    exif[0x0112] = 6
    exif.get_ifd(0x8825)[1] = "N"
    raw = jpeg(exif=exif, comment=b"secret-comment", xmp=b"secret-xmp")
    sid = seed(r, content=raw)
    before = r.source.snapshot()
    result = place(r, sid)["placement"]
    stored = r.read_binary(result["file_ref"])
    assert b"Exif" not in stored and b"secret-comment" not in stored and b"secret-xmp" not in stored
    with Image.open(BytesIO(stored)) as image:
        assert image.format == "JPEG" and image.size == (1000, 2000)
        assert not image.getexif() and "comment" not in image.info
    assert result["sha256"] == hashlib.sha256(stored).hexdigest()
    assert r.source.snapshot() == before


def test_deliverer_a02_the_photo_date_is_naive_utc(semantic_runtime):
    r = semantic_runtime
    cases = [("2026:11:04 00:02:25", "+01:00", "2026-11-03T23:02:25"), ("2026:07:04 12:00:00", None, "2026-07-04T10:00:00"), ("2026:07:04 12:00:00", "+25:00", "2026-07-04T10:00:00"), ("1980:01:01 00:00:00", None, "2026-11-18T11:00:00"), (None, None, "2026-11-18T11:00:00")]
    for i, (date, offset, expected) in enumerate(cases):
        exif = Image.Exif()
        detail = exif.get_ifd(0x8769)
        if date is not None:
            detail[0x9003] = date
        if offset is not None:
            detail[0x9011] = offset
        name = f"{i}.jpg"
        sid = seed(r, name, jpeg(exif=exif))
        assert place(r, sid, name)["placement"]["publication"]["photo_date"] == expected


def test_deliverer_a02_publication_body_is_not_client_visible(semantic_runtime):
    r = semantic_runtime
    publication = place(r, seed(r))["placement"]["publication"]
    assert publication["client_visible"] is False
    assert publication["caption"] is None and publication["section_id"] is None
    photo_id = r.portal.publish(PROJECT, publication)
    assert photo_id not in r.portal.client_photo_ids(PROJECT)
    r.portal.set_visible(PROJECT, photo_id, True)
    assert photo_id in r.portal.client_photo_ids(PROJECT)


def test_deliverer_a03_a_repeated_placement_writes_no_durable_state(semantic_runtime):
    r = semantic_runtime
    sid = seed(r)
    first = place(r, sid)
    before = r.durable_snapshot()
    r.source.remove("a.jpg")
    again = place(r, sid)
    assert again["status"] == "replayed" and again["placement"] == first["placement"]
    assert r.durable_snapshot() == before


def test_deliverer_a03_a_replaced_file_is_a_new_photo_and_the_first_delivery_stays(semantic_runtime):
    r = semantic_runtime
    sid = seed(r)
    first = place(r, sid)
    mark(r, sid)
    before = r.durable_snapshot()
    new = seed(r, content=jpeg(color=(10, 20, 30)))
    assert new != sid
    assert (scan(r)["a.jpg"]["status"], scan(r)["a.jpg"]["source_id"]) == ("ready", new)
    assert r.durable_snapshot() == before
    r.source.remove("a.jpg")
    assert scan(r) == {}
    assert place(r, sid)["placement"] == first["placement"]
    assert place(r, sid)["photo_id"] == PHOTO
    assert r.durable_snapshot() == before


def test_deliverer_a03_a_syncthing_conflict_copy_is_neither_offered_nor_placed(semantic_runtime):
    r = semantic_runtime
    name = "a.sync-conflict-20261118-120000-ABCDEF1.jpg"
    sid = seed(r, name)
    before = r.durable_snapshot()
    answer = place(r, sid, name)
    assert (answer["status"], answer["reason"]) == ("failed", "not_ready_or_absent")
    assert r.durable_snapshot() == before
    seed(r)
    first = place(r, sid)
    r.source.remove("a.jpg")
    before = r.durable_snapshot()
    assert place(r, sid, name)["placement"] == first["placement"]
    assert r.durable_snapshot() == before


def test_deliverer_a04_marking_again_changes_nothing_and_another_photo_is_refused(semantic_runtime):
    r = semantic_runtime
    sid = seed(r)
    place(r, sid)
    first = mark(r, sid)
    before = r.durable_snapshot()
    r.clock.set("2026-11-20T13:00:00")
    again = mark(r, sid)
    assert again["status"] == "replayed" and again["marked_at"] == first["marked_at"]
    refused(lambda: mark(r, sid, OTHER), "publication_conflict")
    assert r.durable_snapshot() == before


def test_deliverer_a05_every_route_except_health_requires_the_token(semantic_runtime):
    r = semantic_runtime
    routes = [("GET", f"/v1/projects/{PROJECT}/photos"), ("POST", f"/v1/projects/{PROJECT}/photos/deliver"), ("POST", f"/v1/projects/{PROJECT}/photos/{'0'*64}/published")]
    for method, path in routes:
        for token in [None, "wrong"]:
            assert r.request(method, path, body={}, token=token).status_code == 401
    assert r.request("GET", "/v1/projects/not-a-uuid/photos", token=None).status_code == 401
    assert r.request("GET", "/health", token=None).status_code == 200


def test_deliverer_a05_an_unconfirmed_connection_delivers_nothing(semantic_runtime):
    r = semantic_runtime
    sid = seed(r)
    r.connection.set_confirmed(False)
    before = r.durable_snapshot()
    for action in [lambda: scan(r), lambda: place(r, sid), lambda: mark(r, sid)]:
        refused(action, "connection_not_confirmed")
    assert r.durable_snapshot() == before


def test_deliverer_a05_the_api_scans_and_places_without_showing_server_paths(semantic_runtime):
    r = semantic_runtime
    sid = seed(r)
    paths = [("GET", f"/v1/projects/{PROJECT}/photos", None), ("POST", f"/v1/projects/{PROJECT}/photos/deliver", {"name":"a.jpg", "source_id":sid}), ("POST", f"/v1/projects/{PROJECT}/photos/{sid}/published", {"photo_id":PHOTO}), ("POST", f"/v1/projects/{PROJECT}/photos/{'1'*64}/published", {"photo_id":PHOTO})]
    with r.trap_outbound_connections() as attempts:
        for method, path, body in paths:
            response = r.request(method, path, body=body)
            assert response.status_code == (409 if '1'*64 in path else 200)
            for private in r.private_paths:
                assert private not in response.text
    assert attempts == []


def test_deliverer_a06_separate_processes_leave_one_placement(semantic_runtime):
    r = semantic_runtime
    sid = seed(r)
    answers = r.concurrent_deliver(PROJECT, "a.jpg", sid, workers=4, separate_processes=True)
    assert sorted(x["status"] for x in answers) == ["placed", "replayed", "replayed", "replayed"]
    assert all(x["placement"] == answers[0]["placement"] for x in answers)
    assert r.record_count("ledger", PROJECT, sid) == 1
    assert r.binary_count() == 1
    answers = r.concurrent_mark(PROJECT, sid, [PHOTO, PHOTO, OTHER, OTHER], separate_processes=True)
    assert sum(x.get("status") == "marked" for x in answers) == 1
    winner = next(x["photo_id"] for x in answers if x.get("status") == "marked")
    assert sum(x.get("status") == "replayed" for x in answers) == 1
    assert sum(x.get("code") == "publication_conflict" for x in answers) == 2
    assert r.read_record("published", PROJECT, sid)["photo_id"] == winner
    assert r.record_count("published", PROJECT, sid) == 1


def test_deliverer_a06_a_damaged_record_refuses_and_is_never_taken_for_an_absent_one(semantic_runtime):
    r = semantic_runtime
    sid = seed(r)
    place(r, sid)
    mark(r, sid)
    for kind in ["ledger", "published"]:
        original = r.record_bytes(kind, PROJECT, sid)
        for broken in [b"{broken", b"[]", b"\xff\xfe", b"{}"]:
            r.write_record_bytes(kind, PROJECT, sid, broken)
            before = r.durable_snapshot()
            for action in [lambda: scan(r), lambda: place(r, sid), lambda: mark(r, sid)]:
                refused(action, "state_unavailable")
            assert r.durable_snapshot() == before
        r.write_record_bytes(kind, PROJECT, sid, original)


def test_deliverer_a07_only_the_mark_reads_the_clock(semantic_runtime):
    r = semantic_runtime
    sid = seed(r)
    r.clock.set("2026-11-20T12:00:00")
    for action in [lambda: scan(r), lambda: place(r, sid), lambda: r.request("GET", "/health", token=None)]:
        r.clock.reset_reads()
        action()
        assert r.clock.reads == 0
    r.clock.reset_reads()
    assert mark(r, sid)["marked_at"] == "2026-11-20T12:00:00"
    assert r.clock.reads == 1


def test_deliverer_a08_an_image_above_the_portal_read_limit_is_not_stored(semantic_runtime):
    r = semantic_runtime
    sid = seed(r)
    # Controlled constant binding, not a replacement for the encoder or its result.
    r.bind_constant("MAX_OUTPUT_BYTES", 10)
    before = r.durable_snapshot()
    answer = place(r, sid)
    assert (answer["status"], answer["reason"]) == ("failed", "too_large")
    assert r.durable_snapshot() == before
    assert r.binary_count() == 0


def test_deliverer_a09_deployment_refuses_a_vulnerable_image(semantic_runtime):
    r = semantic_runtime
    for outcome, allowed in [("vulnerable", False), ("unavailable", False), ("clean", True)]:
        # The actual deployment route runs; only its OSV data source is controlled.
        result = r.deployment.check(osv_outcome=outcome)
        assert result["allowed"] is allowed
        assert result["deployment_started"] is False


def test_deliverer_a11_an_offset_date_is_detected_before_delivery(semantic_runtime):
    r = semantic_runtime
    sid = seed(r)
    for date, allowed in [("2026-11-01T12:00:00+01:00", False), ("2026-11-01T11:00:00", True)]:
        r.portal.replace_staff_photo_dates(PROJECT, [date])
        with r.trace_delivery_calls() as calls:
            result = r.calling_flow.deliver(PROJECT)
        assert result["allowed"] is allowed
        assert bool(calls) is allowed
        if allowed:
            assert scan(r)["a.jpg"]["source_id"] == sid
            assert scan(r)["a.jpg"]["status"] == "published"
