"""Witnesses derived from A6, 02_rules.md; see review/SEMANTIC_HANDOFF.md."""
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

