"""Witnesses derived from A3, 02_rules.md; see review/SEMANTIC_HANDOFF.md."""
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
    Image.new("RGB", (3000, 1500), color).save(out, "JPEG", exif=Image.Exif() if exif is None else exif, **metadata)
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





def test_deliverer_a03_a_repeated_placement_writes_no_durable_state(semantic_runtime):
    r = semantic_runtime
    sid = seed(r)
    first = place(r, sid)
    before = r.durable_snapshot()
    r.source.remove("a.jpg")
    again = place(r, sid)
    assert again["status"] == "replayed" and again["placement"] == first["placement"]
    assert r.durable_snapshot() == before
    assert r.record_count("ledger", PROJECT, sid) == 1
    another = seed(r, "retry.jpg", jpeg(color=(90, 10, 20)))
    with r.fail_next_placement_write():
        assert place(r, another, "retry.jpg")["status"] == "failed"
    assert r.record_count("ledger", PROJECT, another) == 0
    assert place(r, another, "retry.jpg")["status"] == "placed"



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

